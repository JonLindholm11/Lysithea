// ipc/registry.js
// Manages the project registry (projects.json) and .lysithea metadata files.

const { app, ipcMain } = require('electron');
const path = require('path');
const fs   = require('fs');

// ── Registry file location ────────────────────────────────────────────────────
// Windows: %APPDATA%\Lysithea\projects.json
// Linux:   ~/.config/Lysithea/projects.json
// Mac:     ~/Library/Application Support/Lysithea/projects.json

function getRegistryPath() {
  const userDataPath = app.getPath('userData');
  if (!fs.existsSync(userDataPath)) fs.mkdirSync(userDataPath, { recursive: true });
  return path.join(userDataPath, 'projects.json');
}

function readRegistry() {
  try {
    const p = getRegistryPath();
    if (!fs.existsSync(p)) return [];
    return JSON.parse(fs.readFileSync(p, 'utf8'));
  } catch {
    return [];
  }
}

function writeRegistry(projects) {
  try {
    fs.writeFileSync(getRegistryPath(), JSON.stringify(projects, null, 2), 'utf8');
    return { ok: true };
  } catch (err) {
    return { ok: false, error: err.message };
  }
}

// ── .lysithea metadata ────────────────────────────────────────────────────────

function readProjectMeta(projectPath) {
  try {
    // Check new location first: projectPath/.lysithea/.lysithea
    const newMetaPath = path.join(projectPath, '.lysithea', '.lysithea');
    if (fs.existsSync(newMetaPath)) {
      return JSON.parse(fs.readFileSync(newMetaPath, 'utf8'));
    }
    // Fall back to old location for legacy projects
    const oldMetaPath = path.join(projectPath, '.lysithea');
    if (fs.existsSync(oldMetaPath) && !fs.statSync(oldMetaPath).isDirectory()) {
      return JSON.parse(fs.readFileSync(oldMetaPath, 'utf8'));
    }
    return null;
  } catch {
    return null;
  }
}

function writeProjectMeta(projectPath, meta) {
  try {
    const metaDir = path.join(projectPath, '.lysithea');
    if (!fs.existsSync(metaDir)) fs.mkdirSync(metaDir, { recursive: true });
    fs.writeFileSync(
      path.join(metaDir, '.lysithea'),
      JSON.stringify(meta, null, 2),
      'utf8'
    );
    return { ok: true };
  } catch (err) {
    return { ok: false, error: err.message };
  }
}

// ── IPC handlers ─────────────────────────────────────────────────────────────

function register(getWindow) {
  // Load all projects — verify folders still exist
  ipcMain.handle('load-projects', async () => {
    try {
      const registry = readRegistry();
      const projects = registry.map(entry => {
        const exists = entry.projectPath && fs.existsSync(entry.projectPath);
        if (!exists) return { ...entry, status: 'missing' };
        const meta = readProjectMeta(entry.projectPath);
        return {
          ...entry,
          ...(meta || {}),
          projectPath: entry.projectPath,
          status: 'ok',
        };
      });
      return { ok: true, projects };
    } catch (err) {
      return { ok: false, error: err.message };
    }
  });

  // Save project — writes registry + .lysithea
  ipcMain.handle('save-project', async (_e, { project }) => {
    try {
      const registry = readRegistry();
      const idx = registry.findIndex(p => p.id === project.id);
      const entry = {
        id:          project.id,
        name:        project.name,
        projectPath: project.projectPath,
        outputPath:  project.outputPath,
        updatedAt:   project.updatedAt,
        createdAt:   project.createdAt,
      };
      if (idx >= 0) registry[idx] = entry;
      else registry.push(entry);
      writeRegistry(registry);
      return { ok: true };
    } catch (err) {
      return { ok: false, error: err.message };
    }
  });

  // Delete project from registry only (does not delete files)
  ipcMain.handle('delete-project', async (_e, { projectId }) => {
    try {
      const registry = readRegistry().filter(p => p.id !== projectId);
      writeRegistry(registry);
      return { ok: true };
    } catch (err) {
      return { ok: false, error: err.message };
    }
  });

  // Import existing project folder that has a .lysithea file
  ipcMain.handle('import-project', async () => {
    const { dialog } = require('electron');
    const result = await dialog.showOpenDialog(getWindow(), {
      properties: ['openDirectory'],
      title: 'Import Existing Lysithea Project',
    });
    if (result.canceled || result.filePaths.length === 0) return { ok: false };

    const folderPath = result.filePaths[0];
    const meta = readProjectMeta(folderPath);

    if (!meta) {
      return { ok: false, error: 'No .lysithea file found. Is this a Lysithea project?' };
    }

    const registry = readRegistry();
    const existing = registry.find(p => p.id === meta.id || p.projectPath === folderPath);
    if (existing) {
      return { ok: false, error: 'This project is already in your registry.' };
    }

    const entry = {
      id:          meta.id || require('crypto').randomUUID(),
      name:        meta.name || path.basename(folderPath),
      projectPath: folderPath,
      outputPath:  path.join(folderPath, 'output'),
      createdAt:   meta.createdAt || new Date().toISOString(),
      updatedAt:   meta.updatedAt || null,
    };
    registry.push(entry);
    writeRegistry(registry);

    return { ok: true, project: { ...entry, ...meta, status: 'ok' } };
  });
}

module.exports = { register };