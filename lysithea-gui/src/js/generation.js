// js/generation.js — Generation lifecycle, IPC listeners, simulation mode

async function startGeneration(project) {
  saveProjectConfig(project);

  // Re-read from state so we have the freshly built prompt.md content
  project = state.projects.find(p => p.id === project.id);

  if (!project.projectPath) {
    showToast('No project folder set. Select a folder in project config first.', 'error');
    return;
  }

  state.projectStatus[project.id] = 'running';
  state.projectLogs[project.id]   = [];
  state.projectNav[project.id]    = 'logs';
  render();

  addLog(project.id, 'system', 'stdout', `Starting generation for "${project.name}"...`);
  addLog(project.id, 'system', 'stdout', `Project path: ${project.projectPath}`);

  if (window.lysithea) {
    window.lysithea.runGeneration(project.projectPath, project.id, project.prompt || '');
  } else {
    simulateGeneration(project.id);
  }
}

function addLog(projectId, agent, type, msg) {
  if (!state.projectLogs[projectId]) state.projectLogs[projectId] = [];
  state.projectLogs[projectId].push({ time: timestamp(), agent, type, msg });
}

function setupIPC() {
  if (!window.lysithea) return;

  window.lysithea.onGenerationLog(({ projectId, type, data }) => {
    const lower = data.toLowerCase();
    const agent = lower.includes('coordinator') ? 'coordinator'
                : lower.includes('planner')     ? 'planner'
                : lower.includes('generator')   ? 'generator'
                : type === 'stderr'             ? 'error'
                : 'system';

    addLog(projectId, agent, type, data.trim());

    if (state.activeProjectId === projectId && state.projectNav[projectId] === 'logs') {
      const stream = $('#log-stream');
      if (stream) {
        const line = document.createElement('div');
        line.className = 'log-line fade-in';
        line.innerHTML = `
          <span class="log-time">${timestamp()}</span>
          <span class="log-agent ${agent}">${agent}</span>
          <span class="log-msg ${type === 'stderr' ? 'error' : ''}">${escapeHtml(data.trim())}</span>
        `;
        stream.appendChild(line);
        stream.scrollTop = stream.scrollHeight;
      }
    }
  });

  window.lysithea.onGenerationComplete(async ({ projectId, exitCode }) => {
    state.projectStatus[projectId] = exitCode === 0 ? 'done' : 'error';

    const project = state.projects.find(p => p.id === projectId);
    if (project?.projectPath) {
      const result = await window.lysithea.readFileTree(project.projectPath);
      if (result.ok) {
        state.projects = state.projects.map(p =>
          p.id === projectId ? { ...p, files: result.files, updatedAt: new Date().toISOString() } : p
        );
      }
    } else {
      state.projects = state.projects.map(p =>
        p.id === projectId ? { ...p, updatedAt: new Date().toISOString() } : p
      );
    }

    saveProjects();
    showToast(exitCode === 0 ? 'Generation complete!' : 'Generation finished with errors. Check logs.', exitCode === 0 ? 'success' : 'error');
    if (state.activeProjectId === projectId) render();
  });
}

// ─── Dev mode simulation ──────────────────────────────────────────────────────

function simulateGeneration(projectId) {
  const steps = [
    ['coordinator', 'Reading prompt.md and planning resources...'],
    ['coordinator', 'Identified resources: users, products, orders'],
    ['planner',     'Extracting stack configuration...'],
    ['planner',     'Stack: Express.js + React + PostgreSQL'],
    ['generator',   'Generating schema...'],
    ['generator',   'Writing routes/users.js'],
    ['generator',   'Writing routes/products.js'],
    ['generator',   'Writing schema/schema.sql'],
    ['generator',   'Generating React frontend...'],
    ['generator',   'Writing src/pages/Dashboard.jsx'],
    ['system',      'Generation complete ✓'],
  ];

  let i = 0;
  const interval = setInterval(() => {
    if (i >= steps.length) {
      clearInterval(interval);
      state.projectStatus[projectId] = 'done';
      state.projects = state.projects.map(p =>
        p.id === projectId ? { ...p, updatedAt: new Date().toISOString() } : p
      );
      saveProjects();
      if (state.activeProjectId === projectId) render();
      return;
    }
    const [agent, msg] = steps[i++];
    addLog(projectId, agent, 'stdout', msg);
    if (state.activeProjectId === projectId && state.projectNav[projectId] === 'logs') {
      const stream = $('#log-stream');
      if (stream) {
        stream.innerHTML += `
          <div class="log-line fade-in">
            <span class="log-time">${timestamp()}</span>
            <span class="log-agent ${agent}">${agent}</span>
            <span class="log-msg">${escapeHtml(msg)}</span>
          </div>
        `;
        stream.scrollTop = stream.scrollHeight;
      }
    }
  }, 600);
}