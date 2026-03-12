// js/workspace/shell.js
// Workspace shell — top bar, nav routing, generate bar, navigation helpers.
// Depends on: config.js, logs.js, patterns.js, fix.js (all in same folder)

function renderWorkspace() {
  const content = $('#content');
  const project = state.projects.find(p => p.id === state.activeProjectId);
  if (!project) return;

  const nav    = state.projectNav[state.activeProjectId] || 'config';
  const status = state.projectStatus[state.activeProjectId] || 'idle';
  const labels = { config: 'Configure', logs: 'Logs', patterns: 'Patterns', fix: 'Fix Agent' };

  content.innerHTML = `
    <div class="workspace fade-in">
      <div class="workspace-center">
        <div class="workspace-topbar">
          <span class="workspace-topbar-title">${project.name}</span>
          <span class="workspace-topbar-sep">›</span>
          <span class="workspace-topbar-section">${labels[nav] || nav}</span>
        </div>
        <div class="workspace-body" id="workspace-body">
          ${renderNavView(nav, project)}
        </div>
        <div class="generate-bar">
          <button class="btn-generate ${status === 'running' ? 'generating' : status === 'done' ? 'done' : ''}" id="btn-generate">
            ${status === 'running' ? '● Generating...' : status === 'done' ? '✓ Done — Regenerate' : '⚡ Generate'}
          </button>
          <span class="generate-status" id="generate-status">
            ${status === 'running' ? 'Running orchestrator...' : status === 'done' ? 'Output ready in file tree →' : 'Ready to generate'}
          </span>
        </div>
      </div>
    </div>
  `;

  $('#btn-generate')?.addEventListener('click', () => {
    if (status !== 'running') startGeneration(project);
  });
}

function renderNavView(nav, project) {
  if (nav === 'config') {
    setTimeout(() => bindConfigView(project), 0);
    return renderConfigView(project);
  }
  if (nav === 'logs')     return renderLogsView(project);
  if (nav === 'patterns') return renderPatternsView(project);
  if (nav === 'fix')      return renderFixView(project);
  return '';
}

// ─── Navigation helpers ───────────────────────────────────────────────────────

function openProject(projectId) {
  if (!state.openProjects.includes(projectId)) state.openProjects.push(projectId);
  state.activeProjectId = projectId;
  if (!state.projectNav[projectId]) state.projectNav[projectId] = 'config';
  state.switcherOpen = false;
  render();

  const project = state.projects.find(p => p.id === projectId);
  if (project?.outputPath && window.lysithea) {
    window.lysithea.readFileTree(project.outputPath).then(result => {
      if (!result.ok) return;
      state.projects = state.projects.map(p =>
        p.id === projectId ? { ...p, files: result.files } : p
      );
      const tree = document.getElementById('file-tree');
      if (tree) {
        const updated = state.projects.find(p => p.id === projectId);
        tree.innerHTML = renderFileTree(updated);
        bindFileTree(updated);
      }
    });
  }
}

function switchToProject(projectId) {
  state.activeProjectId = projectId;
  state.switcherOpen = false;
  render();
}

function goHome() {
  if (state.activeProjectId) {
    stopFileTreePoll(state.activeProjectId);
    state.projects = state.projects.map(p =>
      p.id === state.activeProjectId ? { ...p, files: [] } : p
    );
  }
  state.activeProjectId = null;
  state.switcherOpen = false;
  render();
}