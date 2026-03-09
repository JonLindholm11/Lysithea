// js/workspace.js — Workspace shell, config/logs/patterns views, nav helpers

function renderWorkspace() {
  const content = $('#content');
  const project = state.projects.find(p => p.id === state.activeProjectId);
  if (!project) return;

  const nav    = state.projectNav[state.activeProjectId] || 'config';
  const status = state.projectStatus[state.activeProjectId] || 'idle';
  const labels = { config: 'Configure', logs: 'Logs', patterns: 'Patterns' };

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
  if (nav === 'config')   return renderConfigView(project);
  if (nav === 'logs')     return renderLogsView(project);
  if (nav === 'patterns') return renderPatternsView(project);
  return '';
}

// ─── Config view ──────────────────────────────────────────────────────────────

function renderConfigView(project) {
  return `
    <div class="config-view">
      <div class="config-section">
        <div class="config-section-header">
          <div class="config-section-title">prompt.md</div>
        </div>
        <div class="config-section-body">
          <textarea class="prompt-editor" id="prompt-editor"
            placeholder="Describe your project... Lysithea will plan and scaffold your full-stack app."
            spellcheck="false"
          >${project.prompt || ''}</textarea>
        </div>
      </div>

      <div class="config-section">
        <div class="config-section-header">
          <div class="config-section-title">Stack Configuration</div>
        </div>
        <div class="config-section-body">
          <div class="stack-grid">
            <div class="stack-field">
              <label>Backend</label>
              <select class="stack-select" id="stack-backend">
                <option value="express"  ${project.stack?.backend === 'express'  ? 'selected' : ''}>Express.js</option>
                <option value="fastapi"  ${project.stack?.backend === 'fastapi'  ? 'selected' : ''}>FastAPI</option>
                <option value="django"   ${project.stack?.backend === 'django'   ? 'selected' : ''}>Django</option>
              </select>
            </div>
            <div class="stack-field">
              <label>Frontend</label>
              <select class="stack-select" id="stack-frontend">
                <option value="react"   ${project.stack?.frontend === 'react'   ? 'selected' : ''}>React</option>
                <option value="vue"     ${project.stack?.frontend === 'vue'     ? 'selected' : ''}>Vue</option>
                <option value="svelte"  ${project.stack?.frontend === 'svelte'  ? 'selected' : ''}>Svelte</option>
              </select>
            </div>
            <div class="stack-field">
              <label>Database</label>
              <select class="stack-select" id="stack-database">
                <option value="postgresql" ${project.stack?.database === 'postgresql' ? 'selected' : ''}>PostgreSQL</option>
                <option value="mysql"      ${project.stack?.database === 'mysql'      ? 'selected' : ''}>MySQL</option>
                <option value="mongodb"    ${project.stack?.database === 'mongodb'    ? 'selected' : ''}>MongoDB</option>
              </select>
            </div>
            <div class="stack-field">
              <label>Auth</label>
              <select class="stack-select" id="stack-auth">
                <option value="jwt"     ${project.stack?.auth === 'jwt'     ? 'selected' : ''}>JWT</option>
                <option value="session" ${project.stack?.auth === 'session' ? 'selected' : ''}>Session</option>
                <option value="oauth"   ${project.stack?.auth === 'oauth'   ? 'selected' : ''}>OAuth</option>
              </select>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
}

// ─── Logs view ────────────────────────────────────────────────────────────────

function renderLogsView(project) {
  const logs  = state.projectLogs[project.id] || [];
  const lines = logs.length === 0
    ? `<div class="log-empty">No logs yet. Run generation to see output here.</div>`
    : logs.map(log => `
        <div class="log-line">
          <span class="log-time">${log.time}</span>
          <span class="log-agent ${log.agent}">${log.agent}</span>
          <span class="log-msg ${log.type === 'stderr' ? 'error' : ''}">${escapeHtml(log.msg)}</span>
        </div>
      `).join('');

  return `<div class="logs-view"><div class="log-stream" id="log-stream">${lines}</div></div>`;
}

// ─── Patterns view ────────────────────────────────────────────────────────────

function renderPatternsView() {
  // Render shell immediately, load patterns async
  setTimeout(() => loadAndRenderPatterns(), 0);

  return `
    <div class="patterns-view">
      <div class="patterns-toolbar">
        <div class="patterns-search-wrap">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input id="pattern-search" class="patterns-search" placeholder="Filter patterns..." />
        </div>
        <div id="patterns-count" class="patterns-count">Loading...</div>
      </div>
      <div class="patterns-layout">
        <div class="patterns-list" id="patterns-list">
          <div class="patterns-loading">
            <div class="patterns-loading-icon">◈</div>
            <div>Reading pattern files...</div>
          </div>
        </div>
        <div class="patterns-preview" id="patterns-preview">
          <div class="patterns-preview-empty">
            <div class="patterns-preview-empty-icon">{ }</div>
            <div>Select a pattern to preview</div>
          </div>
        </div>
      </div>
    </div>
  `;
}

async function loadAndRenderPatterns() {
  const listEl = document.getElementById('patterns-list');
  const countEl = document.getElementById('patterns-count');
  if (!listEl) return;

  if (!window.lysithea) {
    listEl.innerHTML = `<div class="patterns-error">Pattern reading requires Electron.</div>`;
    return;
  }

  const result = await window.lysithea.readPatterns();

  if (!result.ok) {
    listEl.innerHTML = `<div class="patterns-error">⚠ ${result.error}</div>`;
    if (countEl) countEl.textContent = 'Error';
    return;
  }

  const patterns = result.patterns;
  if (countEl) countEl.textContent = `${patterns.length} pattern${patterns.length !== 1 ? 's' : ''}`;

  // Group by category
  const grouped = {};
  for (const p of patterns) {
    if (!grouped[p.category]) grouped[p.category] = [];
    grouped[p.category].push(p);
  }

  renderPatternList(grouped, patterns);

  // Wire search
  const searchEl = document.getElementById('pattern-search');
  if (searchEl) {
    searchEl.addEventListener('input', () => {
      const q = searchEl.value.toLowerCase();
      const filtered = {};
      for (const [cat, items] of Object.entries(grouped)) {
        const matches = items.filter(p => p.name.toLowerCase().includes(q) || cat.toLowerCase().includes(q));
        if (matches.length) filtered[cat] = matches;
      }
      const total = Object.values(filtered).flat().length;
      if (countEl) countEl.textContent = `${total} of ${patterns.length}`;
      renderPatternList(filtered, patterns);
    });
  }
}

function renderPatternList(grouped, allPatterns) {
  const listEl = document.getElementById('patterns-list');
  if (!listEl) return;

  if (Object.keys(grouped).length === 0) {
    listEl.innerHTML = `<div class="patterns-error">No patterns match your search.</div>`;
    return;
  }

  listEl.innerHTML = Object.entries(grouped).map(([category, items]) => `
    <div class="pattern-group">
      <div class="pattern-group-label">${category}</div>
      ${items.map(p => `
        <div class="pattern-item" data-path="${escapeAttr(p.path)}" data-name="${escapeAttr(p.name)}">
          <span class="pattern-item-icon">⬡</span>
          <span class="pattern-item-name">${p.name}</span>
          <span class="pattern-item-lines" id="lines-${escapeAttr(p.name)}"></span>
        </div>
      `).join('')}
    </div>
  `).join('');

  // Bind clicks
  listEl.querySelectorAll('.pattern-item').forEach(item => {
    item.addEventListener('click', () => {
      listEl.querySelectorAll('.pattern-item').forEach(i => i.classList.remove('active'));
      item.classList.add('active');
      openPatternPreview(item.dataset.path, item.dataset.name);
    });
  });
}

async function openPatternPreview(filePath, fileName) {
  const previewEl = document.getElementById('patterns-preview');
  if (!previewEl) return;

  previewEl.innerHTML = `<div class="patterns-loading"><div class="patterns-loading-icon">◈</div><div>Loading...</div></div>`;

  const result = await window.lysithea.readPatternFile(filePath);
  if (!result.ok) {
    previewEl.innerHTML = `<div class="patterns-error">⚠ ${result.error}</div>`;
    return;
  }

  const lines = result.content.split('\n');

  // Update line count badge
  const linesEl = document.getElementById(`lines-${escapeAttr(fileName)}`);
  if (linesEl) linesEl.textContent = `${lines.length}L`;

  previewEl.innerHTML = `
    <div class="file-preview fade-in">
      <div class="file-preview-header">
        <span class="file-preview-path">${fileName}</span>
        <span class="file-preview-lines">${lines.length} lines</span>
      </div>
      <div class="file-preview-body">
        <div class="line-numbers">${lines.map((_, i) => `<span>${i + 1}</span>`).join('')}</div>
        <pre class="file-preview-code"><code>${escapeHtml(result.content)}</code></pre>
      </div>
    </div>
  `;
}

// ─── Save config ──────────────────────────────────────────────────────────────

function saveProjectConfig(project) {
  const prompt   = $('#prompt-editor')?.value;
  const backend  = $('#stack-backend')?.value;
  const frontend = $('#stack-frontend')?.value;
  const database = $('#stack-database')?.value;
  const auth     = $('#stack-auth')?.value;

  state.projects = state.projects.map(p => p.id !== project.id ? p : {
    ...p,
    prompt: prompt ?? p.prompt,
    stack: {
      backend:  backend  ?? p.stack?.backend,
      frontend: frontend ?? p.stack?.frontend,
      database: database ?? p.stack?.database,
      auth:     auth     ?? p.stack?.auth,
    }
  });

  saveProject(state.projects.find(p => p.id === project.id));
}

// ─── Navigation helpers ───────────────────────────────────────────────────────

function openProject(projectId) {
  if (!state.openProjects.includes(projectId)) state.openProjects.push(projectId);
  state.activeProjectId = projectId;
  if (!state.projectNav[projectId]) state.projectNav[projectId] = 'config';
  state.switcherOpen = false;
  render();
}

function switchToProject(projectId) {
  state.activeProjectId = projectId;
  state.switcherOpen = false;
  render();
}

function goHome() {
  state.activeProjectId = null;
  state.switcherOpen = false;
  render();
}