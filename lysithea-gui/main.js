// main.js — Lysithea Electron entry point
// Bootstraps the window and registers IPC modules.

const { app, BrowserWindow } = require('electron');
const path = require('path');

// ── Hot reload ────────────────────────────────────────────────────────────────
const electronBin = require('electron');
require('electron-reload')(__dirname, {
  electron: typeof electronBin === 'string' ? electronBin : process.execPath,
  hardResetMethod: 'exit',
  watched: [
    path.join(__dirname, 'main.js'),
    path.join(__dirname, 'ipc'),
    path.join(__dirname, 'src'),
  ]
});

// ── IPC modules ───────────────────────────────────────────────────────────────
const registry   = require('./ipc/registry');
const filesystem = require('./ipc/filesystem');
const generation = require('./ipc/generation');
const tools      = require('./ipc/tools');

// ── Window ────────────────────────────────────────────────────────────────────
let mainWindow = null;
const getWindow = () => mainWindow;

function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 820,
    minWidth: 900,
    minHeight: 600,
    backgroundColor: '#0a0e1a',
    titleBarStyle: 'hidden',
    titleBarOverlay: {
      color: '#0a0e1a',
      symbolColor: '#60a5fa',
      height: 40
    },
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
    show: false,
  });

  mainWindow.loadFile(path.join(__dirname, 'src', 'index.html'));
  mainWindow.once('ready-to-show', () => mainWindow.show());
  mainWindow.on('closed', () => { mainWindow = null; });
}

// ── Register IPC handlers ─────────────────────────────────────────────────────
registry.register(getWindow);
filesystem.register(getWindow);
generation.register(getWindow);
tools.register(getWindow);

// ── App lifecycle ─────────────────────────────────────────────────────────────
app.whenReady().then(() => {
  createMainWindow();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createMainWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});