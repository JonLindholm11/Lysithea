// js/workspace/patterns.js
// Patterns view — collapsible folder tree, file preview, search filter.

// Tracks which folder paths are open: Set of path strings e.g. 'Javascript/Express'
if (!window._patternOpenFolders) window._patternOpenFolders = new Set();

// ─── Render shell ─────────────────────────────────────────────────────────────

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

// ─── Load + render ────────────────────────────────────────────────────────────

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

  // Build nested folder tree from flat pattern list.
  // Each pattern's category is e.g. 'Javascript / Express / routes'
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

  // Wire up search filter
  const searchEl = document.getElementById('pattern-search');
  if (searchEl) {
    searchEl.addEventListener('input', () => {
      const q = searchEl.value.trim().toLowerCase();
      const filtered = q
        ? patterns.filter(p => p.name.toLowerCase().includes(q) || p.category.toLowerCase().includes(q))
        : patterns;

      if (countEl) countEl.textContent = `${filtered.length} pattern${filtered.length !== 1 ? 's' : ''}`;

      if (!q) {
        renderPatternTree(listEl, tree, '', patterns, countEl);
      } else {
        // Flat list for search results
        listEl.innerHTML = filtered.length === 0
          ? `<div class="patterns-error">No patterns match "${escapeHtml(q)}"</div>`
          : filtered.map(p => `
              <div class="ptree-file" data-path="${escapeAttr(p.path)}" data-name="${escapeAttr(p.name)}">
                <span class="ptree-file-icon">⬡</span>
                <span class="ptree-file-name">${escapeHtml(p.name)}</span>
                <span class="ptree-file-category">${escapeHtml(p.category)}</span>
              </div>
            `).join('');
        listEl.querySelectorAll('.ptree-file').forEach(item => {
          item.addEventListener('click', () => {
            listEl.querySelectorAll('.ptree-file').forEach(i => i.classList.remove('active'));
            item.classList.add('active');
            openPatternPreview(item.dataset.path, item.dataset.name);
          });
        });
      }
    });
  }
}

// ─── Tree renderer ────────────────────────────────────────────────────────────

function renderPatternTree(listEl, tree, pathPrefix, allPatterns, countEl) {
  listEl.innerHTML = _buildTreeHtml(tree, pathPrefix);
  bindTreeEvents(listEl, tree, allPatterns, countEl);
}

function _buildTreeHtml(node, pathPrefix) {
  let html = '';
  for (const key of Object.keys(node)) {
    if (key === '__files__') continue;
    const folderPath  = pathPrefix ? `${pathPrefix}/${key}` : key;
    const isOpen      = window._patternOpenFolders.has(folderPath);
    const childCount  = countFiles(node[key]);
    html += `
      <div class="ptree-folder-row" data-path="${escapeAttr(folderPath)}">
        <span class="ptree-arrow">${isOpen ? '▾' : '▸'}</span>
        <span class="ptree-folder-icon">◫</span>
        <span class="ptree-folder-name">${escapeHtml(key)}</span>
        <span class="ptree-folder-count">${childCount}</span>
      </div>
      <div class="ptree-children" style="display:${isOpen ? 'block' : 'none'}">
        ${_buildTreeHtml(node[key], folderPath)}
      </div>
    `;
  }
  for (const file of (node.__files__ || [])) {
    html += `
      <div class="ptree-file" data-path="${escapeAttr(file.path)}" data-name="${escapeAttr(file.name)}">
        <span class="ptree-file-icon">⬡</span>
        <span class="ptree-file-name">${escapeHtml(file.name)}</span>
        <span class="ptree-file-lines" id="lines-${escapeAttr(file.name)}"></span>
      </div>
    `;
  }
  return html;
}

function bindTreeEvents(listEl, tree, allPatterns, countEl) {
  listEl.querySelectorAll('.ptree-folder-row').forEach(row => {
    row.addEventListener('click', () => {
      const folderPath = row.dataset.path;
      const children   = row.nextElementSibling;
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

// ─── Pattern file preview ─────────────────────────────────────────────────────

async function openPatternPreview(filePath, fileName) {
  const previewEl = document.getElementById('patterns-preview');
  if (!previewEl) return;

  previewEl.innerHTML = `
    <div class="patterns-loading">
      <div class="patterns-loading-icon">◈</div>
      <div>Loading...</div>
    </div>
  `;

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