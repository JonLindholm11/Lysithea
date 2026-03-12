// js/render.js — Main render loop and sidebar

const PROJECT_NAV = [
  {
    id: 'config', label: 'Configure',
    svg: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
      <path d="M12 2L2 7l10 5 10-5-10-5z"/>
      <path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
    </svg>`
  },
  {
    id: 'logs', label: 'Logs',
    svg: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
    </svg>`
  },
  {
    id: 'patterns', label: 'Patterns',
    svg: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
      <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
      <rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
    </svg>`
  },
  {
    id: 'fix', label: 'Fix Agent',
    svg: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
      <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
    </svg>`
  },
];

function renderSidebar() {
  const sidebar = $('#sidebar-nav');
  const isHome  = state.activeProjectId === null;
  const icons   = isHome ? [] : PROJECT_NAV;
  const active  = isHome ? null : (state.projectNav[state.activeProjectId] || 'config');

  const homeBtn = !isHome ? `
    <button class="sidebar-icon-btn sidebar-home-btn" id="btn-sidebar-home" title="All Projects">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M3 9.5L12 3l9 6.5V20a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V9.5z"/>
        <path d="M9 21V12h6v9"/>
      </svg>
      <span class="tooltip">All Projects</span>
    </button>
    <div class="sidebar-divider"></div>
  ` : '';

  sidebar.innerHTML = homeBtn + icons.map(nav => `
    <button class="sidebar-icon-btn ${nav.id === active ? 'active' : ''}" data-nav="${nav.id}" title="${nav.label}">
      ${nav.svg}
      <span class="tooltip">${nav.label}</span>
    </button>
  `).join('');

  $('#btn-sidebar-home')?.addEventListener('click', () => goHome());

  sidebar.querySelectorAll('[data-nav]').forEach(btn => {
    btn.addEventListener('click', () => {
      if (state.activeProjectId) {
        state.projectNav[state.activeProjectId] = btn.dataset.nav;
        renderWorkspace();
        renderSidebar();
      }
    });
  });
}

function renderContent() {
  if (state.activeProjectId === null) renderProjectsHome();
  else renderWorkspace();
}

function render() {
  renderSidebar();
  renderContent();
  renderRightPanel();
}