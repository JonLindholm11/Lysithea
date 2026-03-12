// js/workspace/fix.js
// Fix Agent view — prompt input, agent log stream, structured result panel, apply/discard.

// Pending fix result — persists across re-renders within session
if (!window._fixAgentPending) window._fixAgentPending = null;

// ─── Render ───────────────────────────────────────────────────────────────────

function renderFixView(project) {
  setTimeout(() => bindFixView(project), 0);

  return `
    <div class="fix-view" id="fix-view">

      <!-- ── Input bar ── -->
      <div class="fix-input-section">
        <div class="fix-input-label">
          <span class="fix-input-label-icon">⚙</span>
          Describe the bug or paste an error / stack trace
        </div>
        <div class="fix-input-row">
          <textarea
            id="fix-prompt-input"
            class="fix-prompt-input"
            placeholder="e.g. &quot;the getUsers route is returning 500 errors&quot; or paste a full stack trace..."
            rows="4"
          ></textarea>
        </div>
        <div class="fix-input-actions">
          <button class="btn-fix-analyse" id="btn-fix-analyse">
            <span id="fix-btn-label">⚡ Analyse</span>
          </button>
          <span class="fix-path-hint" id="fix-path-hint">
            ${project.outputPath
              ? `Searching: ${project.outputPath}`
              : 'No output path — set one in Configure'}
          </span>
        </div>
      </div>

      <!-- ── Agent log stream ── -->
      <div class="fix-log-section" id="fix-log-section">
        <div class="fix-log-header">Agent Log</div>
        <div class="fix-log-stream" id="fix-log-stream">
          <div class="fix-log-empty">Run an analysis to see agent output here.</div>
        </div>
      </div>

      <!-- ── Result panel (hidden until result arrives) ── -->
      <div class="fix-result-panel" id="fix-result-panel" style="display:none;">

        <div class="fix-result-meta" id="fix-result-meta"></div>

        <div class="fix-result-blocks">
          <div class="fix-result-col">
            <div class="fix-result-col-label">Original</div>
            <div class="fix-code-block" id="fix-original-block"></div>
          </div>
          <div class="fix-result-arrow">→</div>
          <div class="fix-result-col">
            <div class="fix-result-col-label">Proposed Fix</div>
            <div class="fix-code-block fix-code-block--new" id="fix-proposed-block"></div>
          </div>
        </div>

        <div class="fix-result-actions">
          <button class="btn-fix-apply"   id="btn-fix-apply">✓ Apply Fix</button>
          <button class="btn-fix-discard" id="btn-fix-discard">✕ Discard</button>
        </div>

        <div class="fix-applied-msg" id="fix-applied-msg" style="display:none;"></div>
      </div>

    </div>
  `;
}

// ─── Bind ─────────────────────────────────────────────────────────────────────

function bindFixView(project) {
  const analyseBtn  = document.getElementById('btn-fix-analyse');
  const applyBtn    = document.getElementById('btn-fix-apply');
  const discardBtn  = document.getElementById('btn-fix-discard');
  const promptInput = document.getElementById('fix-prompt-input');

  if (!analyseBtn) return;

  // Remove stale IPC listeners before re-binding
  window.lysithea.removeAllListeners('fix-agent-log');
  window.lysithea.removeAllListeners('fix-agent-result');

  // ── Analyse ──────────────────────────────────────────────────────────────
  analyseBtn.addEventListener('click', () => {
    const prompt = promptInput?.value?.trim();
    if (!prompt) {
      _fixLog('error', 'Please enter a prompt before analysing.');
      return;
    }
    if (!project.outputPath) {
      _fixLog('error', 'No project output path set. Configure one first.');
      return;
    }

    window._fixAgentPending = null;
    _showFixResult(false);
    _setFixBusy(true);
    _clearFixLog();
    _fixLog('log', `Starting fix agent for: "${prompt.slice(0, 80)}${prompt.length > 80 ? '...' : ''}"`);

    window.lysithea.runFixAgent(project.outputPath, prompt);
  });

  // ── IPC log stream ────────────────────────────────────────────────────────
  window.lysithea.onFixAgentLog((data) => {
    if (data.type === 'log')   _fixLog('log',   data.data);
    if (data.type === 'error') _fixLog('error', data.data);
    if (data.type === 'status' && data.data === 'done') _setFixBusy(false);
  });

  // ── IPC result ────────────────────────────────────────────────────────────
  window.lysithea.onFixAgentResult((data) => {
    _setFixBusy(false);

    if (!data.ok) {
      _fixLog('error', `Agent error: ${data.error || 'Unknown failure'}`);
      return;
    }

    // ── No bug found ─────────────────────────────────────────────────────────
    if (data.result.no_bug) {
      _fixLog('log', `✅ No issue found — ${data.result.diagnosis}`);
      _renderNoBug(data.result);
      _showFixResult(true);
      return;
    }

    // ── Needs more info ───────────────────────────────────────────────────────
    if (data.result.needs_more_info) {
      _fixLog('log', `ℹ️ ${data.result.reason}`);
      _renderNeedsMoreInfo(data.result);
      _showFixResult(true);
      return;
    }

    window._fixAgentPending = data.result;
    _renderFixResult(data.result);
    _showFixResult(true);
  });

  // ── Apply ─────────────────────────────────────────────────────────────────
  if (applyBtn) {
    applyBtn.addEventListener('click', async () => {
      const pending = window._fixAgentPending;
      if (!pending) return;

      applyBtn.disabled    = true;
      discardBtn.disabled  = true;
      applyBtn.textContent = 'Applying...';

      const result = await window.lysithea.applyFix({
        filePath:   pending.file,
        startLine:  pending.start_line,
        endLine:    pending.end_line,
        fixedBlock: pending.fixed_block,
      });

      const msgEl = document.getElementById('fix-applied-msg');
      if (result.ok) {
        if (msgEl) {
          msgEl.textContent   = `✅ Fix applied to ${pending.file}`;
          msgEl.className     = 'fix-applied-msg fix-applied-msg--ok';
          msgEl.style.display = 'block';
        }
        _fixLog('log', `✅ Fix written to ${pending.file} (lines ${pending.start_line}–${pending.end_line})`);
        window._fixAgentPending = null;
      } else {
        if (msgEl) {
          msgEl.textContent   = `❌ Write failed: ${result.error}`;
          msgEl.className     = 'fix-applied-msg fix-applied-msg--err';
          msgEl.style.display = 'block';
        }
        applyBtn.disabled    = false;
        discardBtn.disabled  = false;
        applyBtn.textContent = '✓ Apply Fix';
      }
    });
  }

  // ── Discard ───────────────────────────────────────────────────────────────
  if (discardBtn) {
    discardBtn.addEventListener('click', () => {
      window._fixAgentPending = null;
      _showFixResult(false);
      _fixLog('log', 'Fix discarded. No files changed.');
    });
  }
}

// ─── Result renderer ──────────────────────────────────────────────────────────

function _renderNoBug(result) {
  // Repurpose the result panel to show a clean "no issue" state.
  // Hide the code diff blocks and action buttons — nothing to apply.
  const metaEl     = document.getElementById('fix-result-meta');
  const blocksEl   = document.querySelector('.fix-result-blocks');
  const actionsEl  = document.querySelector('.fix-result-actions');
  const msgEl      = document.getElementById('fix-applied-msg');

  if (blocksEl)  blocksEl.style.display  = 'none';
  if (actionsEl) actionsEl.style.display = 'none';
  if (msgEl)     msgEl.style.display     = 'none';

  if (metaEl) {
    metaEl.innerHTML = `
      <div class="fix-meta-row">
        <span class="fix-meta-key">File</span>
        <span class="fix-meta-val fix-meta-val--file">${escapeHtml(result.file || '')}</span>
      </div>
      <div class="fix-meta-row">
        <span class="fix-meta-key">Lines</span>
        <span class="fix-meta-val">${result.start_line || '?'}–${result.end_line || '?'}</span>
      </div>
      <div class="fix-no-bug">
        <span class="fix-no-bug-icon">✅</span>
        <span>${escapeHtml(result.diagnosis)}</span>
      </div>
    `;
  }
}

function _renderNeedsMoreInfo(result) {
  const metaEl    = document.getElementById('fix-result-meta');
  const blocksEl  = document.querySelector('.fix-result-blocks');
  const actionsEl = document.querySelector('.fix-result-actions');
  const msgEl     = document.getElementById('fix-applied-msg');

  if (blocksEl)  blocksEl.style.display  = 'none';
  if (actionsEl) actionsEl.style.display = 'none';
  if (msgEl)     msgEl.style.display     = 'none';

  const candidateList = (result.candidates || [])
    .map(f => `<div class="fix-candidate-file">${escapeHtml(f)}</div>`)
    .join('');

  if (metaEl) {
    metaEl.innerHTML = `
      <div class="fix-needs-info">
        <span class="fix-needs-info-icon">ℹ️</span>
        <div class="fix-needs-info-body">
          <div class="fix-needs-info-reason">${escapeHtml(result.reason)}</div>
          ${candidateList ? `
            <div class="fix-needs-info-label">Possible matches:</div>
            <div class="fix-candidate-list">${candidateList}</div>
          ` : ''}
        </div>
      </div>
    `;
  }
}


function _renderFixResult(result) {
  // Restore blocks + actions in case a previous run was a no-bug result
  const blocksEl  = document.querySelector('.fix-result-blocks');
  const actionsEl = document.querySelector('.fix-result-actions');
  if (blocksEl)  blocksEl.style.display  = 'flex';
  if (actionsEl) actionsEl.style.display = 'flex';

  const metaEl     = document.getElementById('fix-result-meta');
  const originalEl = document.getElementById('fix-original-block');
  const proposedEl = document.getElementById('fix-proposed-block');
  const msgEl      = document.getElementById('fix-applied-msg');
  const applyBtn   = document.getElementById('btn-fix-apply');
  const discardBtn = document.getElementById('btn-fix-discard');

  if (msgEl)      msgEl.style.display = 'none';
  if (applyBtn)   { applyBtn.disabled   = false; applyBtn.textContent   = '✓ Apply Fix'; }
  if (discardBtn) { discardBtn.disabled = false; }

  if (metaEl) {
    metaEl.innerHTML = `
      <div class="fix-meta-row">
        <span class="fix-meta-key">Pattern</span>
        <span class="fix-meta-val fix-meta-val--pattern">${escapeHtml(result.pattern_name || 'none matched')}</span>
      </div>
      ${result.pattern_logic ? `
      <div class="fix-meta-row">
        <span class="fix-meta-key">Logic</span>
        <span class="fix-meta-val">${escapeHtml(result.pattern_logic)}</span>
      </div>` : ''}
      <div class="fix-meta-row">
        <span class="fix-meta-key">File</span>
        <span class="fix-meta-val fix-meta-val--file">${escapeHtml(result.file || '')}</span>
      </div>
      <div class="fix-meta-row">
        <span class="fix-meta-key">Lines</span>
        <span class="fix-meta-val">${result.start_line || '?'}–${result.end_line || '?'}</span>
      </div>
      <div class="fix-diagnosis">
        <span class="fix-diagnosis-icon">⚠</span>
        <span>${escapeHtml(result.diagnosis || 'No diagnosis provided')}</span>
      </div>
    `;
  }

  if (originalEl) originalEl.innerHTML = _renderCodeBlock((result.original_block || '').split('\n'));
  if (proposedEl) proposedEl.innerHTML = _renderCodeBlock((result.fixed_block    || '').split('\n'));
}

function _renderCodeBlock(lines) {
  return `
    <div class="fix-code-inner">
      <div class="fix-line-numbers">${lines.map((_, i) => `<span>${i + 1}</span>`).join('')}</div>
      <pre class="fix-code-pre"><code>${escapeHtml(lines.join('\n'))}</code></pre>
    </div>
  `;
}

// ─── Log helpers ──────────────────────────────────────────────────────────────

function _fixLog(type, msg) {
  const stream = document.getElementById('fix-log-stream');
  if (!stream) return;

  const empty = stream.querySelector('.fix-log-empty');
  if (empty) empty.remove();

  const time = new Date().toLocaleTimeString('en-GB', { hour12: false });
  const line = document.createElement('div');
  line.className = `fix-log-line fix-log-line--${type}`;
  line.innerHTML = `
    <span class="fix-log-time">${time}</span>
    <span class="fix-log-msg">${escapeHtml(msg)}</span>
  `;
  stream.appendChild(line);
  stream.scrollTop = stream.scrollHeight;
}

function _clearFixLog() {
  const stream = document.getElementById('fix-log-stream');
  if (stream) stream.innerHTML = '';
}

function _setFixBusy(busy) {
  const btn   = document.getElementById('btn-fix-analyse');
  const label = document.getElementById('fix-btn-label');
  if (!btn) return;
  btn.disabled = busy;
  if (label) label.textContent = busy ? '◈ Analysing...' : '⚡ Analyse';
  btn.classList.toggle('busy', busy);
}

function _showFixResult(show) {
  const panel = document.getElementById('fix-result-panel');
  if (panel) panel.style.display = show ? 'flex' : 'none';
}