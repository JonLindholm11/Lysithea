// app.js — Entry point. Loads state, wires IPC, kicks off render loop.

document.addEventListener('DOMContentLoaded', async () => {
  loadSettings();

  try {
    await loadProjects();
  } catch (err) {
    console.error('[Lysithea] loadProjects failed:', err);
  }

  render();
  setupIPC();
  checkOllama();
  setInterval(checkOllama, 10000);

  document.getElementById('btn-settings')?.addEventListener('click', showSettingsPanel);
});