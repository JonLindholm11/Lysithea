// js/rightpanel.js — Right panel: project switcher, file tree, file preview

function renderRightPanel() {
  if (state.activeProjectId === null) renderRightHome();
  else renderProjectSwitcher();
}

function renderRightHome() {
  const rightPanel = $('#right-panel');
  rightPanel.innerHTML = `
    <div class="right-home">
      <div class="right-home-title">Open Projects</div>
      <div class="right-empty">
        <div class="right-empty-icon">◈</div>
        <p>No projects open yet.<br/>Select a project card<br/>to get started.</p>
      </div>
    </div>
  `;
}

function renderProjectSwitcher() {
  const rightPanel    = $('#right-panel');
  const activeProject = state.projects.find(p => p.id === state.activeProjectId);
  if (!activeProject) return;

  const statusText = {
    idle: 'Ready to generate', running: '● Generating...',
    done: '✓ Generation complete', error: '✗ Generation failed',
  };
  const status = state.projectStatus[state.activeProjectId] || 'idle';

  rightPanel.innerHTML = `
    <div class="project-switcher">

      <div class="switcher-current" id="switcher-toggle">
        <div class="switcher-current-info">
          <div class="switcher-current-name">${activeProject.name}</div>
          <div class="switcher-current-status">${statusText[status] || 'Ready'}</div>
        </div>
        <svg class="switcher-chevron ${state.switcherOpen ? 'open' : ''}" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="6 9 12 15 18 9"/>
        </svg>
      </div>

      <div class="switcher-dropdown ${state.switcherOpen ? 'open' : ''}" id="switcher-dropdown">
        ${state.openProjects.map(pid => {
          const proj = state.projects.find(p => p.id === pid);
          if (!proj) return '';
          const s = state.projectStatus[pid] || 'idle';
          const dotColors = { idle: '#475569', running: '#a78bfa', done: '#22d3ee', error: '#f87171' };
          return `
            <div class="switcher-project-item ${pid === state.activeProjectId ? 'active' : ''}" data-pid="${pid}">
              <div class="switcher-item-dot" style="background:${dotColors[s]};box-shadow:${s === 'running' ? '0 0 6px #a78bfa' : 'none'}"></div>
              <div class="switcher-item-name">${proj.name}</div>
            </div>
          `;
        }).join('')}
        <div class="switcher-divider"></div>
        <div class="switcher-action" id="switcher-new">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          New Project
        </div>
        <div class="switcher-action" id="switcher-all">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>
          All Projects
        </div>
      </div>

      <div class="file-tree-label" title="${activeProject.outputPath || ''}">
        ${activeProject.outputPath
          ? activeProject.outputPath.replace(/\\/g, '/').split('/').slice(-2).join('/')
          : 'Output Files'}
      </div>
      <div class="file-tree" id="file-tree">
        ${renderFileTree(activeProject)}
      </div>

      <div class="action-bar">
        <div class="action-bar-title">Open With</div>
        <button class="btn-action" data-action="vscode">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M16.5 3L6 13.5l-3-3L1.5 12 6 16.5l12-12L16.5 3z"/><path d="M1.5 12L6 16.5 18 4.5"/></svg>
          VS Code
        </button>
        <button class="btn-action" data-action="cursor">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><path d="M8 12l8 0M12 8l0 8"/></svg>
          Cursor
        </button>
        <button class="btn-action" data-action="terminal">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>
          Terminal
        </button>
        <button class="btn-action" data-action="explorer">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
          Show in Explorer
        </button>
      </div>
    </div>
  `;

  // Switcher toggle
  $('#switcher-toggle')?.addEventListener('click', () => {
    state.switcherOpen = !state.switcherOpen;
    renderProjectSwitcher();
  });

  // Switch to another open project
  rightPanel.querySelectorAll('[data-pid]').forEach(item => {
    item.addEventListener('click', () => switchToProject(item.dataset.pid));
  });

  $('#switcher-new')?.addEventListener('click', () => {
    state.switcherOpen = false;
    showNewProjectModal();
  });

  $('#switcher-all')?.addEventListener('click', () => {
    state.switcherOpen = false;
    goHome();
  });

  // Action bar buttons
  rightPanel.querySelectorAll('[data-action]').forEach(btn => {
    btn.addEventListener('click', () => {
      const action = btn.dataset.action;
      const proj   = state.projects.find(p => p.id === state.activeProjectId);
      if (!proj?.outputPath) return;
      if (action === 'terminal')  window.lysithea?.openInTerminal(proj.outputPath);
      else if (action === 'explorer') window.lysithea?.openInExplorer(proj.outputPath);
      else window.lysithea?.openInEditor(proj.outputPath, action);
    });
  });

  bindFileTree(activeProject);
}

// ─── File tree ────────────────────────────────────────────────────────────────

const treeState = {};

function getTreeState(projectId) {
  if (!treeState[projectId]) treeState[projectId] = { collapsed: new Set(), selectedFile: null };
  return treeState[projectId];
}

function renderFileTree(project) {
  if (!project.files || project.files.length === 0) {
    return `<div class="file-tree-empty">Generate your project to see output files here.</div>`;
  }

  const ts = getTreeState(project.id);

  return project.files.map(file => {
    const isDir       = file.type === 'dir';
    const isCollapsed = ts.collapsed.has(file.path);
    const isSelected  = ts.selectedFile === file.path;
    const indent      = file.depth * 12;
    const icon        = isDir ? (isCollapsed ? '▶' : '▾') : getFileIcon(file.name);
    const color       = isDir ? 'var(--accent-bright)' : getFileColor(file.name);

    return `
      <div class="file-node ${isSelected ? 'active' : ''}"
        data-file="${escapeAttr(file.path)}"
        data-type="${file.type}"
        style="padding-left:${8 + indent}px"
      >
        <span class="file-node-icon" style="color:${color}">${icon}</span>
        <span class="file-node-name">${file.name}</span>
      </div>
    `;
  }).join('');
}

function bindFileTree(project) {
  const tree = document.getElementById('file-tree');
  if (!tree) return;

  tree.querySelectorAll('.file-node').forEach(node => {
    node.addEventListener('click', () => {
      const filePath = node.dataset.file;
      const fileType = node.dataset.type;
      const ts       = getTreeState(project.id);

      if (fileType === 'dir') {
        if (ts.collapsed.has(filePath)) ts.collapsed.delete(filePath);
        else ts.collapsed.add(filePath);
        tree.innerHTML = renderFileTree(project);
        bindFileTree(project);
      } else {
        ts.selectedFile = filePath;
        tree.querySelectorAll('.file-node').forEach(n => n.classList.remove('active'));
        node.classList.add('active');
        openFilePreview(project, filePath);
      }
    });
  });
}

// ─── File preview ─────────────────────────────────────────────────────────────

async function openFilePreview(project, filePath) {
  if (!window.lysithea || !project.outputPath) return;

  const result = await window.lysithea.readFile(project.outputPath, filePath);
  if (!result.ok) { showToast(`Could not read file: ${result.error}`, 'error'); return; }

  const body = document.getElementById('workspace-body');
  if (!body) return;

  const lines = result.content.split('\n');

  body.innerHTML = `
    <div class="file-preview fade-in">
      <div class="file-preview-header">
        <span class="file-preview-path">${filePath.replace(/\\/g, '/')}</span>
        <span class="file-preview-lines">${lines.length} lines</span>
      </div>
      <div class="file-preview-body">
        <div class="line-numbers">${lines.map((_, i) => `<span>${i + 1}</span>`).join('')}</div>
        <pre class="file-preview-code"><code>${escapeHtml(result.content)}</code></pre>
      </div>
    </div>
  `;
}

// ─── File type helpers ────────────────────────────────────────────────────────

function getFileIcon(name) {
  const ext = name.split('.').pop().toLowerCase();
  return { js:'⬡', jsx:'⬡', ts:'⬡', tsx:'⬡', py:'🐍', json:'{}', md:'📄', sql:'🗃', css:'🎨', html:'🌐', env:'⚙', sh:'⚙', gitignore:'⊘', lock:'🔒' }[ext] || '·';
}

function getFileColor(name) {
  const ext = name.split('.').pop().toLowerCase();
  return { js:'#f7df1e', jsx:'#61dafb', ts:'#3178c6', tsx:'#61dafb', py:'#3572a5', json:'#fbbf24', md:'#94a3b8', sql:'#22d3ee', css:'#a78bfa', html:'#e44d26' }[ext] || 'var(--text-muted)';
}