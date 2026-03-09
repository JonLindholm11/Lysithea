// js/state.js — Global state and persistence

const state = {
  projects:        [],
  openProjects:    [],
  activeProjectId: null,
  projectNav:      {},
  projectLogs:     {},
  projectStatus:   {},
  switcherOpen:    false,
  ollamaOnline:    false,
  ollamaModels:    [],
  settings: {
    editor:           'vscode',
    ollamaModel:      'llama3.1:8b',
    defaultOutputPath: '',
  },
};

async function saveProjects() {
  if (!window.lysithea) {
    localStorage.setItem('lysithea-projects', JSON.stringify(state.projects));
    return;
  }
  for (const project of state.projects) {
    await window.lysithea.saveProject(project);
  }
}

async function saveProject(project) {
  if (!window.lysithea) return;
  await window.lysithea.saveProject(project);
}

async function loadProjects() {
  if (!window.lysithea) {
    state.projects = JSON.parse(localStorage.getItem('lysithea-projects') || '[]');
    return;
  }
  try {
    const result = await window.lysithea.loadProjects();
    if (result.ok) state.projects = result.projects;
  } catch (err) {
    console.error('[Lysithea] loadProjects IPC error:', err);
    state.projects = [];
  }
}

function loadSettings() {
  try {
    const saved = localStorage.getItem('lysithea-settings');
    if (saved) Object.assign(state.settings, JSON.parse(saved));
  } catch { /* use defaults */ }
}

function saveSettings() {
  localStorage.setItem('lysithea-settings', JSON.stringify(state.settings));
}