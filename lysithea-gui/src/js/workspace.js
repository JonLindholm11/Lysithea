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

  const features = (c.features && c.features.length)
    ? c.features
    : [{ name: '', ops: [], pages: [], fields: [] }];

  const featureRows = features.map((f, i) => {
    const fields = f.fields || [];

    const fieldTags = fields.map((fld, fi) => `
      <span class="field-tag" data-field-index="${fi}">
        <span class="field-tag-name">by ${escapeHtml(fld)}</span>
        <button class="field-tag-remove" data-row="${i}" data-field="${fi}" title="Remove">×</button>
      </span>
    `).join('');

    return `
      <div class="feature-row" data-index="${i}">
        <div class="feature-row-top">
          <input class="form-input feature-name" placeholder="Resource name (e.g. posts)"
            value="${escapeAttr(f.name || '')}" />
          <button class="btn-icon remove-feature" title="Remove">×</button>
        </div>
        <div class="feature-row-body">
          <div class="feature-row-label">Operations</div>
          <div class="feature-ops">
            ${['crud','list','create','read','update','delete','get by id'].map(op => `
              <label class="op-chip ${f.ops?.includes(op) ? 'active' : ''}">
                <input type="checkbox" value="${op}" ${f.ops?.includes(op) ? 'checked' : ''} />
                ${op}
              </label>
            `).join('')}
          </div>
          <div class="feature-row-label">Get By Field
            <span class="field-label-hint">— add fields this resource needs filtering by</span>
          </div>
          <div class="feature-fields" data-row="${i}">
            ${fieldTags}
            <div class="field-add-wrap">
              <input class="field-add-input" placeholder="field name (e.g. price)" data-row="${i}" />
              <button class="field-add-btn" data-row="${i}">+ Add</button>
            </div>
          </div>
          <div class="feature-row-label">Frontend Pages</div>
          <div class="feature-pages">
            ${['dashboard','form'].map(pg => `
              <label class="op-chip page-chip ${f.pages?.includes(pg) ? 'active' : ''}">
                <input type="checkbox" value="${pg}" ${f.pages?.includes(pg) ? 'checked' : ''} />
                ${pg}
              </label>
            `).join('')}
          </div>
        </div>
      </div>
    `;
  }).join('');

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
  $('#add-feature')?.addEventListener('click', () => {
    saveProjectConfig(project);
    project = state.projects.find(p => p.id === project.id);
    const c = project.config || {};
    c.features = [...(c.features || []), { name: '', ops: [], pages: [], fields: [] }];
    state.projects = state.projects.map(p => p.id === project.id ? { ...p, config: c } : p);
    render();
  });

  document.querySelectorAll('.remove-feature').forEach(btn => {
    btn.addEventListener('click', () => {
      const i = parseInt(btn.closest('.feature-row').dataset.index);
      saveProjectConfig(project);
      project = state.projects.find(p => p.id === project.id);
      const c = project.config || {};
      c.features = (c.features || []).filter((_, fi) => fi !== i);
      if (!c.features.length) c.features = [{ name: '', ops: [], pages: [], fields: [] }];
      state.projects = state.projects.map(p => p.id === project.id ? { ...p, config: c } : p);
      render();
    });
  });

  document.querySelectorAll('.op-chip input').forEach(cb => {
    cb.addEventListener('change', () => {
      cb.closest('.op-chip').classList.toggle('active', cb.checked);
    });
  });

  document.querySelectorAll('.field-add-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const rowIndex = parseInt(btn.dataset.row);
      const input = document.querySelector(`.field-add-input[data-row="${rowIndex}"]`);
      const fieldName = input?.value?.trim().toLowerCase().replace(/\s+/g, '_');
      if (!fieldName) return;
      saveProjectConfig(project);
      project = state.projects.find(p => p.id === project.id);
      const c = project.config || {};
      const feature = c.features[rowIndex];
      if (!feature) return;
      if (!feature.fields) feature.fields = [];
      if (!feature.fields.includes(fieldName)) feature.fields.push(fieldName);
      state.projects = state.projects.map(p => p.id === project.id ? { ...p, config: c } : p);
      render();
    });
  });

  document.querySelectorAll('.field-add-input').forEach(input => {
    input.addEventListener('keydown', e => {
      if (e.key === 'Enter') {
        const rowIndex = parseInt(input.dataset.row);
        const fieldName = input.value?.trim().toLowerCase().replace(/\s+/g, '_');
        if (!fieldName) return;
        saveProjectConfig(project);
        project = state.projects.find(p => p.id === project.id);
        const c = project.config || {};
        const feature = c.features[rowIndex];
        if (!feature) return;
        if (!feature.fields) feature.fields = [];
        if (!feature.fields.includes(fieldName)) feature.fields.push(fieldName);
        state.projects = state.projects.map(p => p.id === project.id ? { ...p, config: c } : p);
        render();
      }
    });
  });

  document.querySelectorAll('.field-tag-remove').forEach(btn => {
    btn.addEventListener('click', () => {
      const rowIndex   = parseInt(btn.dataset.row);
      const fieldIndex = parseInt(btn.dataset.field);
      saveProjectConfig(project);
      project = state.projects.find(p => p.id === project.id);
      const c = project.config || {};
      const feature = c.features[rowIndex];
      if (!feature?.fields) return;
      feature.fields = feature.fields.filter((_, i) => i !== fieldIndex);
      state.projects = state.projects.map(p => p.id === project.id ? { ...p, config: c } : p);
      render();
    });
  });
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

  const features = [];
  document.querySelectorAll('.feature-row').forEach((row, i) => {
    const name  = row.querySelector('.feature-name')?.value?.trim();
    const ops   = [...row.querySelectorAll('.feature-ops input:checked')].map(cb => cb.value);
    const pages = [...row.querySelectorAll('.feature-pages input:checked')].map(cb => cb.value);
    const stateFeature = (project.config?.features || [])[i];
    const fields = stateFeature?.fields || [];
    if (name) features.push({ name, ops, pages, fields });
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

  const features     = config.features || [];
  const featureLines = features.map(f => {
    const allOps = [...(f.ops || [])];
    (f.fields || []).forEach(fld => allOps.push(`get-by-field:${fld}`));
    return `- ${f.name}: ${allOps.join(', ') || 'crud'}`;
  }).join('\n');

  const frontendReqs = features
    .filter(f => f.pages?.length)
    .map(f => `- ${f.name}: ${f.pages.join(', ')}`)
    .join('\n');

  let md = `# Project Name\n${projectName}\n`;
  md += `\n# Stack\nFrontend: ${frontendLabel}\nBackend: ${backendLabel}\nDatabase: ${dbLabel}\n`;

  if (featureLines) md += `\n# Features\n${featureLines}\n`;

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

// ─── Patterns view ────────────────────────────────────────────────────────────

// Tracks which folder paths are open: Set of path strings e.g. 'Javascript/Express'
if (!window._patternOpenFolders) window._patternOpenFolders = new Set();

function renderPatternsView() {
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
  const listEl  = document.getElementById('patterns-list');
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

  // Build a nested folder tree from the flat pattern list.
  // Each pattern's category is e.g. 'Javascript / Express / routes'
  // Split on ' / ' to get path segments and build a tree.
  const tree = {};
  for (const p of patterns) {
    const parts = p.category.split(' / ').map(s => s.trim()).filter(Boolean);
    let node = tree;
    for (const part of parts) {
      if (!node[part]) node[part] = { __files__: [] };
      node = node[part];
    }
    node.__files__ = node.__files__ || [];
    node.__files__.push(p);
  }

  renderPatternTree(listEl, tree, '', patterns, countEl);
}

/**
 * Render the collapsible folder tree into listEl.
 * tree:     the nested folder object
 * basePath: dot-separated path string used as a stable open/close key
 * allPatterns / countEl: needed for search rebind
 */
function renderPatternTree(listEl, tree, basePath, allPatterns, countEl) {
  listEl.innerHTML = buildTreeHtml(tree, '', 0);
  bindTreeEvents(listEl, tree, allPatterns, countEl);

  // Wire search — when the user types, rebuild with filtered files visible
  const searchEl = document.getElementById('pattern-search');
  if (searchEl) {
    // Remove old listener by cloning
    const fresh = searchEl.cloneNode(true);
    searchEl.parentNode.replaceChild(fresh, searchEl);
    fresh.addEventListener('input', () => {
      const q = fresh.value.toLowerCase().trim();
      if (!q) {
        listEl.innerHTML = buildTreeHtml(tree, '', 0);
        if (countEl) countEl.textContent = `${allPatterns.length} pattern${allPatterns.length !== 1 ? 's' : ''}`;
      } else {
        // Filter: collect matching files, force all folders open
        const matching = allPatterns.filter(p =>
          p.name.toLowerCase().includes(q) || p.category.toLowerCase().includes(q)
        );
        if (countEl) countEl.textContent = `${matching.length} of ${allPatterns.length}`;
        listEl.innerHTML = buildFilteredHtml(matching);
      }
      bindTreeEvents(listEl, tree, allPatterns, countEl);
    });
  }
}

/** Build the full collapsible tree HTML. depth controls indent level. */
function buildTreeHtml(node, path, depth) {
  let html = '';

  // Folders first (keys that are not __files__)
  const folders = Object.keys(node).filter(k => k !== '__files__').sort();
  for (const folder of folders) {
    const folderPath = path ? `${path}/${folder}` : folder;
    const isOpen     = window._patternOpenFolders.has(folderPath);
    const fileCount  = countFiles(node[folder]);

    html += `
      <div class="ptree-folder" data-path="${escapeAttr(folderPath)}">
        <div class="ptree-folder-row depth-${depth}" data-path="${escapeAttr(folderPath)}">
          <span class="ptree-arrow">${isOpen ? '▾' : '▸'}</span>
          <span class="ptree-folder-icon">${depth === 0 ? '◫' : '◧'}</span>
          <span class="ptree-folder-name">${escapeHtml(folder)}</span>
          <span class="ptree-folder-count">${fileCount}</span>
        </div>
        <div class="ptree-children" style="display:${isOpen ? 'block' : 'none'}">
          ${buildTreeHtml(node[folder], folderPath, depth + 1)}
        </div>
      </div>
    `;
  }

  // Files inside this node
  const files = node.__files__ || [];
  for (const p of files) {
    html += `
      <div class="ptree-file depth-${depth}" data-path="${escapeAttr(p.path)}" data-name="${escapeAttr(p.name)}">
        <span class="ptree-file-icon">⬡</span>
        <span class="ptree-file-name">${escapeHtml(p.name)}</span>
        <span class="ptree-file-lines" id="lines-${escapeAttr(p.name)}"></span>
      </div>
    `;
  }

  return html;
}

/** When search is active, flatten all matching files with their folder path as a label. */
function buildFilteredHtml(patterns) {
  // Group by category for display
  const byCategory = {};
  for (const p of patterns) {
    if (!byCategory[p.category]) byCategory[p.category] = [];
    byCategory[p.category].push(p);
  }

  return Object.entries(byCategory).map(([cat, files]) => `
    <div class="ptree-search-group">
      <div class="ptree-search-group-label">${escapeHtml(cat)}</div>
      ${files.map(p => `
        <div class="ptree-file depth-1" data-path="${escapeAttr(p.path)}" data-name="${escapeAttr(p.name)}">
          <span class="ptree-file-icon">⬡</span>
          <span class="ptree-file-name">${escapeHtml(p.name)}</span>
          <span class="ptree-file-lines" id="lines-${escapeAttr(p.name)}"></span>
        </div>
      `).join('')}
    </div>
  `).join('');
}

/** Bind folder toggle + file click events after any tree render. */
function bindTreeEvents(listEl, tree, allPatterns, countEl) {
  // Folder row toggle
  listEl.querySelectorAll('.ptree-folder-row').forEach(row => {
    row.addEventListener('click', () => {
      const folderPath = row.dataset.path;
      const children   = row.nextElementSibling; // .ptree-children
      const arrow      = row.querySelector('.ptree-arrow');

      if (window._patternOpenFolders.has(folderPath)) {
        window._patternOpenFolders.delete(folderPath);
        if (children) children.style.display = 'none';
        if (arrow)    arrow.textContent = '▸';
      } else {
        window._patternOpenFolders.add(folderPath);
        if (children) children.style.display = 'block';
        if (arrow)    arrow.textContent = '▾';
      }
    });
  });

  // File click → preview
  listEl.querySelectorAll('.ptree-file').forEach(item => {
    item.addEventListener('click', () => {
      listEl.querySelectorAll('.ptree-file').forEach(i => i.classList.remove('active'));
      item.classList.add('active');
      openPatternPreview(item.dataset.path, item.dataset.name);
    });
  });
}

/** Count all leaf files under a tree node recursively. */
function countFiles(node) {
  let count = (node.__files__ || []).length;
  for (const key of Object.keys(node)) {
    if (key !== '__files__') count += countFiles(node[key]);
  }
  return count;
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

  const linesEl = document.getElementById(`lines-${escapeAttr(fileName)}`);
  if (linesEl) linesEl.textContent = `${lines.length}L`;

  previewEl.innerHTML = `
    <div class="file-preview fade-in">
      <div class="file-preview-header">
        <span class="file-preview-path">${escapeHtml(fileName)}</span>
        <span class="file-preview-lines">${lines.length} lines</span>
      </div>
      <div class="file-preview-body">
        <div class="line-numbers">${lines.map((_, i) => `<span>${i + 1}</span>`).join('')}</div>
        <pre class="file-preview-code"><code>${escapeHtml(result.content)}</code></pre>
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