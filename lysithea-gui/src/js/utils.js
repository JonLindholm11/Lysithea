// js/utils.js — Shared helpers, toast, ollama status

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

function timestamp() {
  return new Date().toLocaleTimeString('en-US', {
    hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit'
  });
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric'
  });
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function escapeAttr(str) {
  return String(str).replace(/"/g, '&quot;');
}

function showToast(message, type = 'info') {
  const existing = $('#toast');
  if (existing) existing.remove();

  const colors = {
    success: { bg: 'var(--success-dim)', border: 'var(--success)', text: 'var(--success)' },
    error:   { bg: 'var(--error-dim)',   border: 'var(--error)',   text: 'var(--error)'   },
    info:    { bg: 'var(--accent-glow)', border: 'var(--accent)',  text: 'var(--accent-bright)' },
  };
  const c = colors[type] || colors.info;

  const toast = document.createElement('div');
  toast.id = 'toast';
  toast.style.cssText = `
    position:fixed;bottom:24px;left:50%;transform:translateX(-50%);
    background:${c.bg};border:1px solid ${c.border};color:${c.text};
    padding:10px 20px;border-radius:var(--r-md);font-size:13px;
    box-shadow:var(--shadow-md);z-index:9999;
    animation:fadeIn 0.2s ease;white-space:nowrap;
  `;
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3500);
}

async function checkOllama() {
  try {
    const res = await fetch('http://localhost:11434/api/tags', {
      signal: AbortSignal.timeout(2000)
    });
    state.ollamaOnline = res.ok;
  } catch {
    state.ollamaOnline = false;
  }
  const dot = $('#ollama-dot');
  if (dot) {
    dot.className = `ollama-dot ${state.ollamaOnline ? 'online' : 'offline'}`;
    const btn = $('#btn-ollama-status');
    if (btn) btn.title = state.ollamaOnline ? 'Ollama: Online' : 'Ollama: Offline';
  }
}