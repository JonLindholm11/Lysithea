// ipc/fix.js
// Spawns the Python fix agent, streams structured output back to the renderer,
// and handles the apply-fix confirmation write.

const { ipcMain } = require('electron');
const path  = require('path');
const fs    = require('fs');
const { spawn } = require('child_process');

function register(getWindow) {

  // ── Run the fix agent ─────────────────────────────────────────────────────
  // Spawns fix_runner.py which wraps fix_agent.run_fix_agent() and outputs
  // a single JSON result to stdout when analysis is complete.
  ipcMain.on('run-fix-agent', (_e, { projectPath, prompt }) => {
    const win = getWindow();

    const repoRoot = path.resolve(__dirname, '..', '..');
    const pkgDir   = path.join(repoRoot, 'Lysithea');
    const runner   = path.join(pkgDir, 'audit', 'fix_runner.py');

    const send = (type, data) => {
      if (win) win.webContents.send('fix-agent-log', { type, data });
    };

    send('status', 'Analysing...');

    const proc = spawn('python', [runner, '--prompt', prompt, '--path', projectPath], {
      cwd: pkgDir,
      shell: false,
      env: {
        ...process.env,
        PYTHONUTF8: '1',
        PYTHONIOENCODING: 'utf-8',
        LYSITHEA_PROJECT_PATH: projectPath,
      },
    });

    let jsonBuffer = '';
    let capturing  = false;

    proc.stdout.on('data', (chunk) => {
      const text = chunk.toString();

      // Stream human-readable lines to the log
      for (const line of text.split('\n')) {
        const trimmed = line.trim();
        if (!trimmed) continue;

        // The runner wraps the final JSON result in sentinel markers
        if (trimmed === '<<<LYSITHEA_FIX_RESULT_START>>>') {
          capturing = true;
          continue;
        }
        if (trimmed === '<<<LYSITHEA_FIX_RESULT_END>>>') {
          capturing = false;
          try {
            const result = JSON.parse(jsonBuffer);
            if (win) win.webContents.send('fix-agent-result', { ok: true, result });
          } catch (e) {
            if (win) win.webContents.send('fix-agent-result', {
              ok: false, error: 'Failed to parse agent result'
            });
          }
          continue;
        }

        if (capturing) {
          jsonBuffer += trimmed;
        } else {
          send('log', trimmed);
        }
      }
    });

    proc.stderr.on('data', (chunk) => {
      send('error', chunk.toString());
    });

    proc.on('close', (code) => {
      if (code !== 0 && !jsonBuffer) {
        if (win) win.webContents.send('fix-agent-result', {
          ok: false, error: `Agent exited with code ${code}`
        });
      }
      send('status', 'done');
    });
  });


  // ── Apply the confirmed fix ───────────────────────────────────────────────
  // Called when the user clicks "Apply Fix" in the GUI.
  // Writes the fix directly by calling fix_runner.py in apply mode,
  // OR we can do the write directly in Node since we have the data.
  ipcMain.handle('apply-fix', async (_e, { filePath, startLine, endLine, fixedBlock }) => {
    try {
      const content = fs.readFileSync(filePath, 'utf8');
      const lines   = content.split('\n');

      // lines are 0-indexed, startLine/endLine are 1-based from Python
      const before = lines.slice(0, startLine - 1);
      const after  = lines.slice(endLine);
      const fixed  = fixedBlock.split('\n');

      const newContent = [...before, ...fixed, ...after].join('\n');
      fs.writeFileSync(filePath, newContent, 'utf8');

      return { ok: true };
    } catch (err) {
      return { ok: false, error: err.message };
    }
  });

}

module.exports = { register };