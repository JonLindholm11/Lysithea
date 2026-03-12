// js/workspace/logs.js
// Logs view — renders the streaming generation log.

function renderLogsView(project) {
  const logs  = state.projectLogs[project.id] || [];
  const lines = logs.length === 0
    ? `<div class="log-empty">No logs yet. Run generation to see output here.</div>`
    : logs.map(log => `
        <div class="log-line">
          <span class="log-time">${log.time}</span>
          <span class="log-agent ${log.agent}">${log.agent}</span>
          <span class="log-msg ${log.type === 'stderr' ? 'error' : ''}">${escapeHtml(log.msg)}</span>
        </div>
      `).join('');

  return `<div class="logs-view"><div class="log-stream" id="log-stream">${lines}</div></div>`;
}