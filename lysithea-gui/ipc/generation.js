// ipc/generation.js
// Handles spawning and managing the Python orchestrator process.

const { ipcMain } = require('electron');
const path  = require('path');
const fs    = require('fs');
const { spawn } = require('child_process');

const activeProcs = new Map();

function register(getWindow) {

  // Run the Python orchestrator
  ipcMain.on('run-generation', (_e, { projectPath, projectId, prompt }) => {
    // Kill any existing process for this project
    if (activeProcs.has(projectId)) {
      activeProcs.get(projectId).kill();
      activeProcs.delete(projectId);
    }

    // lysithea-gui/ is one level up from __dirname (ipc/),
    // repo root is one more level up, Python package is inside Lysithea/
    const repoRoot = path.resolve(__dirname, '..', '..');
    const pkgDir   = path.join(repoRoot, 'Lysithea');

    console.log(`[generation] __dirname: ${__dirname}`);
    console.log(`[generation] repoRoot:  ${repoRoot}`);
    console.log(`[generation] pkgDir:    ${pkgDir}`);

    // Write prompt.md into the Python package dir so orchestrator finds it
    const promptContent = prompt || '';
    console.log(`[generation] Writing prompt.md (${promptContent.length} chars) to ${pkgDir}`);
    fs.writeFileSync(path.join(pkgDir, 'prompt.md'), promptContent, 'utf8');

    const proc = spawn('python', ['orchestrator.py'], {
      cwd: pkgDir,
      shell: false,
      env: {
        ...process.env,
        PYTHONUTF8: '1',
        PYTHONIOENCODING: 'utf-8',
        LYSITHEA_PROJECT_PATH: projectPath,
      }
    });

    activeProcs.set(projectId, proc);

    const send = (type, data) => {
      const win = getWindow();
      if (win) win.webContents.send('generation-log', { projectId, type, data });
    };

    proc.stdout.on('data', (data) => send('stdout', data.toString()));
    proc.stderr.on('data', (data) => send('stderr', data.toString()));

    proc.on('close', (code) => {
      activeProcs.delete(projectId);
      const win = getWindow();
      if (win) win.webContents.send('generation-complete', { projectId, exitCode: code });
    });
  });

  // Kill a running generation
  ipcMain.on('kill-generation', (_e, { projectId }) => {
    if (activeProcs.has(projectId)) {
      activeProcs.get(projectId).kill();
      activeProcs.delete(projectId);
    }
  });

}

module.exports = { register };