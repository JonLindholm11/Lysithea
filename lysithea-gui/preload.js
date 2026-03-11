const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('lysithea', {

  // ── Project registry ────────────────────────────────────────────────────────
  loadProjects:  ()          => ipcRenderer.invoke('load-projects'),
  saveProject:   (project)   => ipcRenderer.invoke('save-project',   { project }),
  deleteProject: (projectId) => ipcRenderer.invoke('delete-project', { projectId }),
  importProject: ()          => ipcRenderer.invoke('import-project'),

  // ── Folder picker ───────────────────────────────────────────────────────────
  pickFolder: () => ipcRenderer.invoke('pick-folder'),

  // ── File system ─────────────────────────────────────────────────────────────
  writePrompt:     (projectPath, content)  => ipcRenderer.invoke('write-prompt',      { projectPath, content }),
  readPrompt:      (projectPath)           => ipcRenderer.invoke('read-prompt',       { projectPath }),
  readFileTree:    (outputPath)            => ipcRenderer.invoke('read-file-tree',    { outputPath }),
  readFile:        (outputPath, filePath)  => ipcRenderer.invoke('read-file',         { projectPath: outputPath, filePath }),
  readPatterns:    ()                      => ipcRenderer.invoke('read-patterns'),
  readPatternFile: (filePath)              => ipcRenderer.invoke('read-pattern-file', { filePath }),

  // ── Generation ──────────────────────────────────────────────────────────────
  runGeneration:  (outputPath, projectId, prompt) => ipcRenderer.send('run-generation',  { projectPath: outputPath, projectId, prompt }),
  killGeneration: (projectId)              => ipcRenderer.send('kill-generation', { projectId }),

  // ── Context menu ────────────────────────────────────────────────────────────
  showContextMenu: (project, settings) => ipcRenderer.invoke('show-context-menu', { project, settings }),

  // ── External tools ──────────────────────────────────────────────────────────
  openInEditor:   (outputPath, editor) => ipcRenderer.send('open-in-editor',   { outputPath, editor }),
  openInTerminal: (outputPath)         => ipcRenderer.send('open-in-terminal', { outputPath }),
  openInExplorer: (outputPath)         => ipcRenderer.send('open-in-explorer', { outputPath }),

  // ── Listeners ───────────────────────────────────────────────────────────────
  onGenerationLog:      (cb) => ipcRenderer.on('generation-log',      (_e, data) => cb(data)),
  onGenerationComplete: (cb) => ipcRenderer.on('generation-complete', (_e, data) => cb(data)),

  // ── Cleanup ─────────────────────────────────────────────────────────────────
  removeAllListeners: (channel) => ipcRenderer.removeAllListeners(channel),
});