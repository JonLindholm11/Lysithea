// js/workspace/config.js
// Config view — stack selectors, feature rows, op chips, field tags, save logic.

// ─── Render ───────────────────────────────────────────────────────────────────

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
          <input class="form-input feature-name"
            placeholder="Resource name (e.g. posts)"
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
                <option value="none"    ${s.frontend === 'none'    ? 'selected' : ''}>None</option>
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
                <option value="none"    ${s.auth === 'none'    ? 'selected' : ''}>None</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <div class="config-section">
        <div class="config-section-header">
          <div class="config-section-title">Features / Resources</div>
        </div>
        <div class="config-section-body">
          <div id="feature-rows">${featureRows}</div>
          <button class="btn-add-feature" id="add-feature">+ Add Resource</button>
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
              <label>Input Validation</label>
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
          <textarea class="prompt-editor" id="db-notes"
            placeholder="Describe any specific schema requirements, relationships, or constraints..."
            rows="4"
            spellcheck="false"
          >${escapeHtml(c.dbNotes || '')}</textarea>
        </div>
      </div>

      <div class="config-section">
        <div class="config-section-header">
          <div class="config-section-title">Extra Notes</div>
        </div>
        <div class="config-section-body">
          <textarea class="prompt-editor" id="extra-notes"
            placeholder="Any additional instructions for the generator. e.g. Use async/await throughout. Style: corporate."
            spellcheck="false"
          >${escapeHtml(c.extraNotes || '')}</textarea>
        </div>
      </div>

    </div>
  `;
}

// ─── Bind ─────────────────────────────────────────────────────────────────────

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
      const rowIndex  = parseInt(btn.dataset.row);
      const input     = document.querySelector(`.field-add-input[data-row="${rowIndex}"]`);
      const fieldName = input?.value?.trim().toLowerCase().replace(/\s+/g, '_');
      if (!fieldName) return;
      saveProjectConfig(project);
      project = state.projects.find(p => p.id === project.id);
      const c       = project.config || {};
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
      if (e.key !== 'Enter') return;
      const rowIndex  = parseInt(input.dataset.row);
      const fieldName = input.value?.trim().toLowerCase().replace(/\s+/g, '_');
      if (!fieldName) return;
      saveProjectConfig(project);
      project = state.projects.find(p => p.id === project.id);
      const c       = project.config || {};
      const feature = c.features[rowIndex];
      if (!feature) return;
      if (!feature.fields) feature.fields = [];
      if (!feature.fields.includes(fieldName)) feature.fields.push(fieldName);
      state.projects = state.projects.map(p => p.id === project.id ? { ...p, config: c } : p);
      render();
    });
  });

  document.querySelectorAll('.field-tag-remove').forEach(btn => {
    btn.addEventListener('click', () => {
      const rowIndex   = parseInt(btn.dataset.row);
      const fieldIndex = parseInt(btn.dataset.field);
      saveProjectConfig(project);
      project = state.projects.find(p => p.id === project.id);
      const c       = project.config || {};
      const feature = c.features[rowIndex];
      if (!feature?.fields) return;
      feature.fields = feature.fields.filter((_, i) => i !== fieldIndex);
      state.projects = state.projects.map(p => p.id === project.id ? { ...p, config: c } : p);
      render();
    });
  });
}

// ─── Save ─────────────────────────────────────────────────────────────────────

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

// ─── prompt.md builder ───────────────────────────────────────────────────────

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