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
  if (nav === 'config') {
    setTimeout(() => bindConfigView(project), 0);
    return renderConfigView(project);
  }
  if (nav === 'logs')     return renderLogsView(project);
  if (nav === 'patterns') return renderPatternsView(project);
  return '';
}

// ─── Config view ──────────────────────────────────────────────────────────────

function renderConfigView(project) {
  const c = project.config || {};
  const s = project.stack  || {};

  // Features rows
  const features = (c.features && c.features.length)
    ? c.features
    : [{ name: '', ops: [] }];

  const featureRows = features.map((f, i) => `
    <div class="feature-row" data-index="${i}">
      <input class="form-input feature-name" placeholder="Resource name (e.g. posts)"
        value="${escapeAttr(f.name || '')}" />
      <div class="feature-ops">
        ${['crud','list','create','read','update','delete'].map(op => `
          <label class="op-chip ${f.ops?.includes(op) ? 'active' : ''}">
            <input type="checkbox" value="${op}" ${f.ops?.includes(op) ? 'checked' : ''} />
            ${op}
          </label>
        `).join('')}
      </div>
      <button class="btn-icon remove-feature" title="Remove">×</button>
    </div>
  `).join('');

  return `
    <div class="config-view structured">

      <div class="config-section">
        <div class="config-section-header">
          <div class="config-section-title">Stack</div>
        </div>
        <div class="config-section-body">
          <div class="stack-grid">
            <div class="stack-field">
              <label>Backend</label>
              <select class="stack-select" id="stack-backend">
                <option value="express"  ${s.backend === 'express'  ? 'selected' : ''}>Express.js</option>
                <option value="fastapi"  ${s.backend === 'fastapi'  ? 'selected' : ''}>FastAPI</option>
                <option value="django"   ${s.backend === 'django'   ? 'selected' : ''}>Django</option>
              </select>
            </div>
            <div class="stack-field">
              <label>Frontend</label>
              <select class="stack-select" id="stack-frontend">
                <option value="react"   ${s.frontend === 'react'   ? 'selected' : ''}>React 18 + Tailwind</option>
                <option value="vue"     ${s.frontend === 'vue'     ? 'selected' : ''}>Vue</option>
                <option value="svelte"  ${s.frontend === 'svelte'  ? 'selected' : ''}>Svelte</option>
                <option value="none"    ${s.frontend === 'none'    ? 'selected' : ''}>None (API only)</option>
              </select>
            </div>
            <div class="stack-field">
              <label>Database</label>
              <select class="stack-select" id="stack-database">
                <option value="postgresql" ${s.database === 'postgresql' ? 'selected' : ''}>PostgreSQL</option>
                <option value="mysql"      ${s.database === 'mysql'      ? 'selected' : ''}>MySQL</option>
                <option value="mongodb"    ${s.database === 'mongodb'    ? 'selected' : ''}>MongoDB</option>
              </select>
            </div>
            <div class="stack-field">
              <label>Auth</label>
              <select class="stack-select" id="stack-auth">
                <option value="jwt"     ${s.auth === 'jwt'     ? 'selected' : ''}>JWT</option>
                <option value="session" ${s.auth === 'session' ? 'selected' : ''}>Session</option>
                <option value="oauth"   ${s.auth === 'oauth'   ? 'selected' : ''}>OAuth</option>
                <option value="none"    ${s.auth === 'none'    ? 'selected' : ''}>None</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <div class="config-section">
        <div class="config-section-header">
          <div class="config-section-title">Features</div>
          <button class="btn-secondary btn-sm" id="add-feature">+ Add Resource</button>
        </div>
        <div class="config-section-body">
          <div id="features-list">${featureRows}</div>
        </div>
      </div>

      <div class="config-section">
        <div class="config-section-header">
          <div class="config-section-title">API Requirements</div>
        </div>
        <div class="config-section-body">
          <div class="form-row-2">
            <div class="form-field">
              <label>Endpoint Style</label>
              <select class="stack-select" id="api-style">
                <option value="RESTful"  ${c.apiStyle === 'RESTful'  ? 'selected' : ''}>RESTful</option>
                <option value="GraphQL"  ${c.apiStyle === 'GraphQL'  ? 'selected' : ''}>GraphQL</option>
                <option value="tRPC"     ${c.apiStyle === 'tRPC'     ? 'selected' : ''}>tRPC</option>
              </select>
            </div>
            <div class="form-field">
              <label>Validation</label>
              <select class="stack-select" id="api-validation">
                <option value="true"  ${c.apiValidation !== false ? 'selected' : ''}>Enabled</option>
                <option value="false" ${c.apiValidation === false  ? 'selected' : ''}>Disabled</option>
              </select>
            </div>
            <div class="form-field">
              <label>Rate Limiting</label>
              <select class="stack-select" id="api-ratelimit">
                <option value="false" ${!c.apiRateLimit ? 'selected' : ''}>Disabled</option>
                <option value="true"  ${c.apiRateLimit  ? 'selected' : ''}>Enabled</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <div class="config-section">
        <div class="config-section-header">
          <div class="config-section-title">Database / Schema Notes</div>
        </div>
        <div class="config-section-body">
          <textarea class="form-textarea" id="db-notes"
            placeholder="e.g.&#10;- Tables:&#10;  - users: email, username, password_hash&#10;  - posts: title, content, user_id&#10;- Relationships:&#10;  - posts belongs to users"
            spellcheck="false"
          >${escapeHtml(c.dbNotes || '')}</textarea>
        </div>
      </div>

      <div class="config-section">
        <div class="config-section-header">
          <div class="config-section-title">Extra Notes</div>
        </div>
        <div class="config-section-body">
          <textarea class="form-textarea short" id="extra-notes"
            placeholder="e.g. Use async/await throughout. Style: corporate."
            spellcheck="false"
          >${escapeHtml(c.extraNotes || '')}</textarea>
        </div>
      </div>

    </div>
  `;
}

function bindConfigView(project) {
  // Add feature row
  $('#add-feature')?.addEventListener('click', () => {
    saveProjectConfig(project);
    project = state.projects.find(p => p.id === project.id);
    const c = project.config || {};
    c.features = [...(c.features || []), { name: '', ops: [] }];
    state.projects = state.projects.map(p => p.id === project.id ? { ...p, config: c } : p);
    render();
  });

  // Remove feature row
  document.querySelectorAll('.remove-feature').forEach(btn => {
    btn.addEventListener('click', () => {
      const i = parseInt(btn.closest('.feature-row').dataset.index);
      saveProjectConfig(project);
      project = state.projects.find(p => p.id === project.id);
      const c = project.config || {};
      c.features = (c.features || []).filter((_, fi) => fi !== i);
      if (!c.features.length) c.features = [{ name: '', ops: [] }];
      state.projects = state.projects.map(p => p.id === project.id ? { ...p, config: c } : p);
      render();
    });
  });

  // Op chip toggles
  document.querySelectorAll('.op-chip input').forEach(cb => {
    cb.addEventListener('change', () => {
      cb.closest('.op-chip').classList.toggle('active', cb.checked);
    });
  });
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
  const backend    = $('#stack-backend')?.value;
  const frontend   = $('#stack-frontend')?.value;
  const database   = $('#stack-database')?.value;
  const auth       = $('#stack-auth')?.value;
  const apiStyle   = $('#api-style')?.value;
  const validation = $('#api-validation')?.value;
  const rateLimit  = $('#api-ratelimit')?.value;
  const dbNotes    = $('#db-notes')?.value;
  const extraNotes = $('#extra-notes')?.value;

  // Collect feature rows
  const features = [];
  document.querySelectorAll('.feature-row').forEach(row => {
    const name = row.querySelector('.feature-name')?.value?.trim();
    const ops  = [...row.querySelectorAll('.feature-ops input:checked')].map(cb => cb.value);
    if (name) features.push({ name, ops });
  });

  const config = {
    features,
    apiStyle:      apiStyle   ?? project.config?.apiStyle,
    apiValidation: validation === 'true',
    apiRateLimit:  rateLimit  === 'true',
    dbNotes:       dbNotes    ?? project.config?.dbNotes,
    extraNotes:    extraNotes ?? project.config?.extraNotes,
  };

  const stack = {
    backend:  backend  ?? project.stack?.backend,
    frontend: frontend ?? project.stack?.frontend,
    database: database ?? project.stack?.database,
    auth:     auth     ?? project.stack?.auth,
  };

  // Build prompt.md from structured fields
  const prompt = buildPromptMd(project.name, stack, config);

  state.projects = state.projects.map(p => p.id !== project.id ? p : {
    ...p, config, stack, prompt,
  });

  saveProject(state.projects.find(p => p.id === project.id));
}

function buildPromptMd(projectName, stack, config) {
  const frontendLabel = {
    react:  'React 18 + Tailwind',
    vue:    'Vue',
    svelte: 'Svelte',
    none:   'None',
  }[stack.frontend] || stack.frontend;

  const backendLabel = {
    express: 'Express.js + Node 20',
    fastapi: 'FastAPI + Python',
    django:  'Django + Python',
  }[stack.backend] || stack.backend;

  const dbLabel = {
    postgresql: 'PostgreSQL',
    mysql:      'MySQL',
    mongodb:    'MongoDB',
  }[stack.database] || stack.database;

  const features   = config.features || [];
  const featureLines = features.map(f =>
    `- ${f.name}: ${f.ops.join(', ') || 'crud'}`
  ).join('\n');

  const frontendReqs = features
    .filter(f => f.ops.includes('crud') || f.ops.includes('list') || f.ops.includes('create'))
    .map(f => `- ${f.name}: dashboard${f.ops.includes('create') || f.ops.includes('crud') ? ', form' : ''}`)
    .join('\n');

  let md = `# Project Name\n${projectName}\n`;
  md += `\n# Stack\nFrontend: ${frontendLabel}\nBackend: ${backendLabel}\nDatabase: ${dbLabel}\n`;

  if (featureLines) {
    md += `\n# Features\n${featureLines}\n`;
  }

  md += `\n# API Requirements\n`;
  md += `- Security: ${stack.auth?.toUpperCase() || 'JWT'}\n`;
  md += `- Endpoint style: ${config.apiStyle || 'RESTful'}\n`;
  md += `- Validation: ${config.apiValidation !== false ? 'true' : 'false'}\n`;
  md += `- Rate limiting: ${config.apiRateLimit ? 'true' : 'false'}\n`;

  if (frontendReqs && stack.frontend !== 'none') {
    md += `\n# Frontend Requirements\n${frontendReqs}\n`;
  }

  if (config.dbNotes?.trim()) {
    const dbNotes = config.dbNotes.trim().replace(/^#\s*Database\s*\/?\s*Schema\s*Notes\s*\n?/i, '').trim();
    if (dbNotes) md += `\n# Database / Schema Notes\n${dbNotes}\n`;
  }

  if (config.extraNotes?.trim()) {
    const extraNotes = config.extraNotes.trim().replace(/^#\s*Extra\s*Notes\s*\n?/i, '').trim();
    if (extraNotes) md += `\n# Extra Notes\n${extraNotes}\n`;
  }

  return md;
}

// ─── Navigation helpers ───────────────────────────────────────────────────────

function openProject(projectId) {
  if (!state.openProjects.includes(projectId)) state.openProjects.push(projectId);
  state.activeProjectId = projectId;
  if (!state.projectNav[projectId]) state.projectNav[projectId] = 'config';
  state.switcherOpen = false;
  render();

  // Load file tree from disk so it's always populated on entry
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
  // Clear files for the project being left so the tree doesn't persist stale state
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