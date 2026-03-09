// js/projects.js — Projects home, cards, new project modal

function renderProjectsHome() {
  const content = $('#content');
  content.innerHTML = `
    <div class="projects-home fade-in">
      <div class="projects-home-header">
        <div style="display:flex;align-items:center;justify-content:space-between;">
          <div>
            <h1>Projects</h1>
            <p>Select a project to open it, or create a new one.</p>
          </div>
          <button id="btn-import-project" class="btn-secondary">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
            Import Existing
          </button>
        </div>
      </div>
      <div class="projects-grid" id="projects-grid">
        ${state.projects.map(p => renderProjectCard(p)).join('')}
        <div class="project-card new-card" id="btn-new-project">
          <div class="new-card-icon">＋</div>
          <div class="new-card-label">New Project</div>
        </div>
      </div>
    </div>
  `;

  bindProjectCards();

  $('#btn-new-project').addEventListener('click', showNewProjectModal);

  $('#btn-import-project')?.addEventListener('click', async () => {
    if (!window.lysithea) return;
    const result = await window.lysithea.importProject();
    if (result.ok) {
      state.projects.push(result.project);
      showToast(`Imported "${result.project.name}" successfully.`, 'success');
      render();
    } else if (result.error) {
      showToast(result.error, 'error');
    }
  });
}

function renderProjectCard(project) {
  const status    = state.projectStatus[project.id] || 'idle';
  const isMissing = project.status === 'missing';
  const dotClass  = isMissing ? 'error' : ({ idle: 'idle', running: 'running', done: 'fresh', error: 'error' }[status] || 'idle');
  const badges    = [project.stack?.backend, project.stack?.frontend, project.stack?.database].filter(Boolean);

  return `
    <div class="project-card fade-in ${isMissing ? 'missing' : ''}"
      data-project-id="${project.id}"
      ${isMissing ? `title="Folder not found: ${project.projectPath}"` : ''}
    >
      <div class="project-card-header">
        <div class="project-card-name">${project.name}</div>
        <button class="btn-card-delete" data-delete-id="${project.id}" title="Remove project">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>
      ${isMissing
        ? `<div class="project-card-missing">⚠ Folder not found</div>`
        : `<div class="project-card-stack">${badges.map(b => `<span class="stack-badge">${b}</span>`).join('')}</div>`
      }
      <div class="project-card-meta">
        <span class="project-card-date">${project.updatedAt ? formatDate(project.updatedAt) : 'Never generated'}</span>
        <div class="project-status-dot ${dotClass}"></div>
      </div>
    </div>
  `;
}

function bindProjectCards() {
  // Open project on card click (but not delete button)
  document.querySelectorAll('[data-project-id]').forEach(card => {
    card.addEventListener('click', (e) => {
      if (e.target.closest('[data-delete-id]')) return;
      const project = state.projects.find(p => p.id === card.dataset.projectId);
      if (project?.status === 'missing') {
        showToast('Project folder not found. Update the path in settings.', 'error');
        return;
      }
      openProject(card.dataset.projectId);
    });

    // Right-click context menu
    card.addEventListener('contextmenu', async (e) => {
      e.preventDefault();
      if (!window.lysithea) return;

      const project = state.projects.find(p => p.id === card.dataset.projectId);
      if (!project) return;

      const result = await window.lysithea.showContextMenu(project, state.settings);
      if (!result?.action) return;

      switch (result.action) {
        case 'open':
          if (project.status !== 'missing') openProject(project.id);
          else showToast('Project folder not found.', 'error');
          break;
        case 'editor':
          if (project.outputPath) window.lysithea.openInEditor(project.outputPath, result.editor);
          else showToast('No output path set for this project.', 'error');
          break;
        case 'terminal':
          if (project.projectPath) window.lysithea.openInTerminal(project.projectPath);
          else showToast('No project folder set.', 'error');
          break;
        case 'explorer':
          if (project.projectPath) window.lysithea.openInExplorer(project.projectPath);
          else showToast('No project folder set.', 'error');
          break;
        case 'rename':
          showRenameModal(project);
          break;
        case 'delete':
          showDeleteConfirm(project.id);
          break;
      }
    });
  });

  // Delete buttons
  document.querySelectorAll('[data-delete-id]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      showDeleteConfirm(btn.dataset.deleteId);
    });
  });
}

function showDeleteConfirm(projectId) {
  const project = state.projects.find(p => p.id === projectId);
  if (!project) return;

  const modal = document.createElement('div');
  modal.id = 'modal-overlay';
  modal.innerHTML = `
    <div class="modal fade-in">
      <div class="modal-title">Remove Project</div>
      <div class="modal-subtitle">
        This removes <strong style="color:var(--text-primary)">${project.name}</strong> from Lysithea.<br/>
        Your files on disk will not be deleted.
      </div>
      <div class="modal-actions">
        <button id="modal-cancel" class="btn-secondary">Cancel</button>
        <button id="modal-confirm-delete" class="btn-danger">Remove</button>
      </div>
    </div>
  `;

  document.body.appendChild(modal);
  modal.querySelector('#modal-cancel').addEventListener('click', () => modal.remove());
  modal.addEventListener('click', e => { if (e.target === modal) modal.remove(); });

  modal.querySelector('#modal-confirm-delete').addEventListener('click', async () => {
    modal.remove();
    await deleteProject(projectId);
  });
}

async function deleteProject(projectId) {
  state.openProjects = state.openProjects.filter(id => id !== projectId);
  if (state.activeProjectId === projectId) state.activeProjectId = null;
  state.projects = state.projects.filter(p => p.id !== projectId);
  if (window.lysithea) await window.lysithea.deleteProject(projectId);
  showToast('Project removed.', 'info');
  render();
}

function showRenameModal(project) {
  const modal = document.createElement('div');
  modal.id = 'modal-overlay';
  modal.innerHTML = `
    <div class="modal fade-in">
      <div class="modal-title">Rename Project</div>
      <div class="modal-subtitle">Choose a new name for <strong style="color:var(--text-primary)">${project.name}</strong></div>
      <div class="modal-fields">
        <div class="modal-field">
          <label>Project Name</label>
          <input id="rename-input" type="text" class="modal-input" value="${project.name}" />
        </div>
      </div>
      <div class="modal-actions">
        <button id="modal-cancel" class="btn-secondary">Cancel</button>
        <button id="modal-confirm-rename" class="btn-primary">Rename</button>
      </div>
    </div>
  `;

  document.body.appendChild(modal);

  const input = modal.querySelector('#rename-input');
  input.focus();
  input.select();

  modal.querySelector('#modal-cancel').addEventListener('click', () => modal.remove());
  modal.addEventListener('click', e => { if (e.target === modal) modal.remove(); });

  const doRename = async () => {
    const newName = input.value.trim();
    if (!newName || newName === project.name) { modal.remove(); return; }

    state.projects = state.projects.map(p =>
      p.id === project.id ? { ...p, name: newName } : p
    );
    const updated = state.projects.find(p => p.id === project.id);
    if (window.lysithea) await window.lysithea.saveProject(updated);
    modal.remove();
    showToast(`Renamed to "${newName}".`, 'success');
    render();
  };

  modal.querySelector('#modal-confirm-rename').addEventListener('click', doRename);
  input.addEventListener('keydown', e => { if (e.key === 'Enter') doRename(); });
}

function showNewProjectModal() {
  const modal = document.createElement('div');
  modal.id = 'modal-overlay';
  modal.innerHTML = `
    <div class="modal fade-in">
      <div class="modal-title">New Project</div>
      <div class="modal-subtitle">Set up a new Lysithea project</div>

      <div class="modal-fields">
        <div class="modal-field">
          <label>Project Name</label>
          <input id="new-project-name" type="text" placeholder="e.g. MyShopApp" class="modal-input"/>
        </div>
        <div class="modal-field">
          <label>Project Folder</label>
          <div class="modal-path-row">
            <input id="new-project-path" type="text" placeholder="Select a folder..." readonly class="modal-input mono"/>
            <button id="btn-pick-folder" class="btn-browse">Browse...</button>
          </div>
          <div class="modal-hint">Lysithea will write prompt.md and generate output here.</div>
        </div>
      </div>

      <div class="modal-actions">
        <button id="modal-cancel" class="btn-secondary">Cancel</button>
        <button id="modal-create" class="btn-primary">Create Project</button>
      </div>
    </div>
  `;

  document.body.appendChild(modal);

  modal.querySelector('#modal-cancel').addEventListener('click', () => modal.remove());
  modal.addEventListener('click', e => { if (e.target === modal) modal.remove(); });

  modal.querySelector('#btn-pick-folder').addEventListener('click', async () => {
    if (!window.lysithea) return;
    const folder = await window.lysithea.pickFolder();
    if (folder) {
      modal.querySelector('#new-project-path').value = folder;
      const nameInput = modal.querySelector('#new-project-name');
      if (!nameInput.value.trim()) {
        nameInput.value = folder.replace(/\\/g, '/').split('/').pop() || '';
      }
    }
  });

  modal.querySelector('#modal-create').addEventListener('click', async () => {
    const name       = modal.querySelector('#new-project-name').value.trim();
    const folderPath = modal.querySelector('#new-project-path').value.trim();
    if (!name) {
      modal.querySelector('#new-project-name').style.borderColor = 'var(--error)';
      return;
    }

    const project = {
      id:          crypto.randomUUID(),
      name,
      projectPath: folderPath || null,
      outputPath:  folderPath ? folderPath + '/output' : null,
      prompt:      '',
      stack:       { backend: 'express', frontend: 'react', database: 'postgresql', auth: 'jwt' },
      createdAt:   new Date().toISOString(),
      updatedAt:   null,
      files:       [],
      status:      'ok',
    };

    state.projects.push(project);
    await saveProject(project);
    modal.remove();
    openProject(project.id);
  });

  modal.querySelector('#new-project-name').focus();
}