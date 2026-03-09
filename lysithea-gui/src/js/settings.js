// js/settings.js — Settings panel (slide-in from sidebar)

function showSettingsPanel() {
  const existing = document.getElementById('settings-panel');
  if (existing) { existing.remove(); return; }

  const panel = document.createElement('div');
  panel.id = 'settings-panel';
  panel.innerHTML = `
    <div class="settings-overlay" id="settings-overlay"></div>
    <div class="settings-drawer fade-in">

      <div class="settings-header">
        <div class="settings-title">Settings</div>
        <button class="settings-close" id="settings-close">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>

      <div class="settings-body">

        <!-- Editor -->
        <div class="settings-section">
          <div class="settings-section-title">Editor</div>
          <div class="settings-field">
            <label>Default Editor</label>
            <div class="settings-hint">Used by the "Open With" buttons in the file panel.</div>
            <div class="editor-options">
              ${[
                { id: 'vscode',    label: 'VS Code',   icon: '⬡' },
                { id: 'cursor',    label: 'Cursor',    icon: '◎' },
                { id: 'zed',       label: 'Zed',       icon: '◈' },
                { id: 'webstorm',  label: 'WebStorm',  icon: '⬢' },
              ].map(e => `
                <button class="editor-option ${state.settings.editor === e.id ? 'active' : ''}" data-editor="${e.id}">
                  <span class="editor-option-icon">${e.icon}</span>
                  <span>${e.label}</span>
                </button>
              `).join('')}
            </div>
          </div>
        </div>

        <!-- Ollama -->
        <div class="settings-section">
          <div class="settings-section-title">Ollama / LLM</div>
          <div class="settings-field">
            <label>Active Model</label>
            <div class="settings-hint">Model used by the orchestrator for code generation.</div>
            <div class="settings-model-row">
              <select class="settings-select" id="settings-model">
                ${buildModelOptions()}
              </select>
              <button class="btn-refresh-models" id="btn-refresh-models" title="Refresh model list">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="23 4 23 10 17 10"/>
                  <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
                </svg>
              </button>
            </div>
            <div class="ollama-status-row">
              <span class="ollama-dot ${state.ollamaOnline ? 'online' : 'offline'}" style="position:static;width:8px;height:8px;border:none;"></span>
              <span style="font-size:11px;color:var(--text-muted)">
                ${state.ollamaOnline ? 'Ollama is running' : 'Ollama not detected — start it with: ollama serve'}
              </span>
            </div>
          </div>
        </div>

        <!-- Output -->
        <div class="settings-section">
          <div class="settings-section-title">Paths</div>
          <div class="settings-field">
            <label>Default Output Path</label>
            <div class="settings-hint">Optional fallback path when no project folder is set.</div>
            <div class="modal-path-row">
              <input id="settings-output-path" type="text"
                class="modal-input mono"
                placeholder="e.g. C:\Projects or ~/projects"
                value="${state.settings.defaultOutputPath || ''}"
              />
              <button class="btn-browse" id="btn-pick-default-path">Browse...</button>
            </div>
          </div>
        </div>

        <!-- About -->
        <div class="settings-section">
          <div class="settings-section-title">About</div>
          <div class="settings-about">
            <div class="settings-about-row">
              <span>Lysithea</span>
              <span class="settings-about-value">v0.1.0</span>
            </div>
            <div class="settings-about-row">
              <span>Part of</span>
              <span class="settings-about-value">Lunar Systems</span>
            </div>
            <div class="settings-about-row">
              <span>Model</span>
              <span class="settings-about-value">${state.settings.ollamaModel}</span>
            </div>
          </div>
        </div>

      </div>

      <div class="settings-footer">
        <button class="btn-primary" id="settings-save">Save Settings</button>
      </div>
    </div>
  `;

  document.body.appendChild(panel);

  // Close
  document.getElementById('settings-close').addEventListener('click', closeSettingsPanel);
  document.getElementById('settings-overlay').addEventListener('click', closeSettingsPanel);

  // Editor option toggle
  panel.querySelectorAll('[data-editor]').forEach(btn => {
    btn.addEventListener('click', () => {
      panel.querySelectorAll('[data-editor]').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    });
  });

  // Refresh Ollama models
  document.getElementById('btn-refresh-models').addEventListener('click', async () => {
    const btn = document.getElementById('btn-refresh-models');
    btn.style.opacity = '0.5';
    await fetchOllamaModels();
    document.getElementById('settings-model').innerHTML = buildModelOptions();
    btn.style.opacity = '1';
  });

  // Browse default output path
  document.getElementById('btn-pick-default-path').addEventListener('click', async () => {
    if (!window.lysithea) return;
    const folder = await window.lysithea.pickFolder();
    if (folder) document.getElementById('settings-output-path').value = folder;
  });

  // Save
  document.getElementById('settings-save').addEventListener('click', () => {
    const activeEditor = panel.querySelector('[data-editor].active');
    if (activeEditor) state.settings.editor = activeEditor.dataset.editor;
    state.settings.ollamaModel      = document.getElementById('settings-model').value;
    state.settings.defaultOutputPath = document.getElementById('settings-output-path').value.trim();
    saveSettings();
    showToast('Settings saved.', 'success');
    closeSettingsPanel();
  });

  // Fetch models on open if online
  if (state.ollamaOnline && state.ollamaModels.length === 0) {
    fetchOllamaModels().then(() => {
      const sel = document.getElementById('settings-model');
      if (sel) sel.innerHTML = buildModelOptions();
    });
  }
}

function closeSettingsPanel() {
  document.getElementById('settings-panel')?.remove();
}

function buildModelOptions() {
  const current = state.settings.ollamaModel;
  const models  = state.ollamaModels.length > 0
    ? state.ollamaModels
    : [current]; // fallback to current setting if no models fetched yet

  return models.map(m =>
    `<option value="${m}" ${m === current ? 'selected' : ''}>${m}</option>`
  ).join('');
}

async function fetchOllamaModels() {
  try {
    const res  = await fetch('http://localhost:11434/api/tags', { signal: AbortSignal.timeout(3000) });
    const data = await res.json();
    state.ollamaModels = (data.models || []).map(m => m.name).filter(Boolean);
  } catch {
    state.ollamaModels = [];
  }
}