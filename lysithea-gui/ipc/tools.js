// ipc/tools.js
// Handles opening external tools — editors, terminal, file explorer, context menus.

const { ipcMain, shell, Menu } = require('electron');
const { spawn } = require('child_process');

function register(getWindow) {

  // Native right-click context menu for project cards
  ipcMain.handle('show-context-menu', async (_e, { project, settings }) => {
    const win       = getWindow();
    const hasFolder = !!project.projectPath;
    const editor    = settings?.editor || 'vscode';
    const editorLabel = { vscode: 'VS Code', cursor: 'Cursor', zed: 'Zed', webstorm: 'WebStorm' }[editor] || 'Editor';

    return new Promise((resolve) => {
      const menu = Menu.buildFromTemplate([
        {
          label: `Open ${project.name}`,
          click: () => resolve({ action: 'open' }),
        },
        { type: 'separator' },
        {
          label: `Open in ${editorLabel}`,
          enabled: hasFolder,
          click: () => resolve({ action: 'editor', editor }),
        },
        {
          label: 'Open in Terminal',
          enabled: hasFolder,
          click: () => resolve({ action: 'terminal' }),
        },
        {
          label: 'Show in Explorer',
          enabled: hasFolder,
          click: () => resolve({ action: 'explorer' }),
        },
        { type: 'separator' },
        {
          label: 'Rename',
          click: () => resolve({ action: 'rename' }),
        },
        { type: 'separator' },
        {
          label: 'Remove from Lysithea',
          click: () => resolve({ action: 'delete' }),
        },
      ]);

      menu.popup({ window: win });

      // If user clicks away without selecting anything
      menu.once('menu-will-close', () => {
        setTimeout(() => resolve({ action: null }), 100);
      });
    });
  });

  // Open in external code editor
  ipcMain.on('open-in-editor', (_e, { outputPath, editor }) => {
    const commands = {
      vscode:   'code',
      cursor:   'cursor',
      zed:      'zed',
      webstorm: 'webstorm',
    };
    const cmd = commands[editor] || 'code';
    // shell:true required on Windows so PATH-registered commands (code, cursor) resolve
    spawn(cmd, [outputPath], { shell: true, detached: true, stdio: 'ignore' });
  });

  // Open terminal at project output path
  ipcMain.on('open-in-terminal', (_e, { outputPath }) => {
    if (process.platform === 'darwin') {
      spawn('open', ['-a', 'Terminal', outputPath], { shell: false, detached: true, stdio: 'ignore' });
    } else if (process.platform === 'linux') {
      spawn('x-terminal-emulator', ['--working-directory', outputPath], { shell: false, detached: true, stdio: 'ignore' });
    } else {
      // Windows — open a new cmd window cd'd to the output path
      spawn('cmd', ['/c', `start cmd /k "cd /d "${outputPath}""`], { shell: true, detached: true, stdio: 'ignore' });
    }
  });

  // Open in system file explorer
  ipcMain.on('open-in-explorer', (_e, { outputPath }) => {
    shell.openPath(outputPath);
  });

}

module.exports = { register };