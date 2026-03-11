// ipc/filesystem.js
// Handles all file system IPC — prompt.md, file tree, file content, folder picker.

const { ipcMain, dialog } = require('electron');
const path = require('path');
const fs   = require('fs');

function register(getWindow) {

  // Native folder picker
  ipcMain.handle('pick-folder', async () => {
    const result = await dialog.showOpenDialog(getWindow(), {
      properties: ['openDirectory', 'createDirectory'],
      title: 'Select Project Folder',
    });
    if (result.canceled || result.filePaths.length === 0) return null;
    return result.filePaths[0];
  });

  // Write prompt.md
  ipcMain.handle('write-prompt', async (_e, { projectPath, content }) => {
    try {
      if (!fs.existsSync(projectPath)) fs.mkdirSync(projectPath, { recursive: true });
      fs.writeFileSync(path.join(projectPath, 'prompt.md'), content, 'utf8');
      return { ok: true };
    } catch (err) {
      return { ok: false, error: err.message };
    }
  });

  // Read prompt.md
  ipcMain.handle('read-prompt', async (_e, { projectPath }) => {
    try {
      const filePath = path.join(projectPath, 'prompt.md');
      if (!fs.existsSync(filePath)) return { ok: true, content: '' };
      return { ok: true, content: fs.readFileSync(filePath, 'utf8') };
    } catch (err) {
      return { ok: false, error: err.message };
    }
  });

  // Read generated file tree (walks output/ directory)
  ipcMain.handle('read-file-tree', async (_e, { projectPath }) => {
    try {
      const outputPath = path.join(projectPath, 'output');
      if (!fs.existsSync(outputPath)) return { ok: true, files: [] };

      const walk = (dir, depth = 0) => {
        const entries = fs.readdirSync(dir, { withFileTypes: true });
        const results = [];
        for (const entry of entries) {
          const fullPath = path.join(dir, entry.name);
          const relPath  = path.relative(outputPath, fullPath);
          if (entry.isDirectory()) {
            results.push({ name: entry.name, path: relPath, type: 'dir', depth });
            results.push(...walk(fullPath, depth + 1));
          } else {
            results.push({ name: entry.name, path: relPath, type: 'file', depth });
          }
        }
        return results;
      };

      return { ok: true, files: walk(outputPath) };
    } catch (err) {
      return { ok: false, error: err.message };
    }
  });

  // Read individual file content for preview
  ipcMain.handle('read-file', async (_e, { projectPath, filePath }) => {
    try {
      const fullPath = path.join(projectPath, 'output', filePath);
      if (!fs.existsSync(fullPath)) return { ok: false, error: 'File not found' };
      const content = fs.readFileSync(fullPath, 'utf8');
      return { ok: true, content };
    } catch (err) {
      return { ok: false, error: err.message };
    }
  });

  // Read pattern files from repo Patterns/ directory
  ipcMain.handle('read-patterns', async () => {
    try {
      // __dirname is lysithea-gui/ipc/ — go up two levels to reach the repo root
      const repoRoot    = path.resolve(__dirname, '../..');
      const patternsDir = path.join(repoRoot, 'Patterns');

      if (!fs.existsSync(patternsDir)) {
        return { ok: false, error: `Patterns directory not found at ${patternsDir}` };
      }

      const patterns = [];

      const walk = (dir, category = '') => {
        const entries = fs.readdirSync(dir, { withFileTypes: true });
        for (const entry of entries) {
          const fullPath = path.join(dir, entry.name);
          if (entry.isDirectory()) {
            const subCategory = category ? `${category} / ${entry.name}` : entry.name;
            walk(fullPath, subCategory);
          } else if (entry.name.endsWith('.js') || entry.name.endsWith('.jsx')) {
            patterns.push({
              name:     entry.name,
              category: category || 'Uncategorised',
              path:     fullPath,
              relPath:  path.relative(patternsDir, fullPath),
            });
          }
        }
      };

      walk(patternsDir);
      return { ok: true, patterns };
    } catch (err) {
      return { ok: false, error: err.message };
    }
  });

  // Read a pattern file's content for preview
  ipcMain.handle('read-pattern-file', async (_e, { filePath }) => {
    try {
      if (!fs.existsSync(filePath)) return { ok: false, error: 'Pattern file not found' };
      const content = fs.readFileSync(filePath, 'utf8');
      return { ok: true, content };
    } catch (err) {
      return { ok: false, error: err.message };
    }
  });

}

module.exports = { register };