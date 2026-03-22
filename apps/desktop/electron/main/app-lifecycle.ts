// ── App Lifecycle ──────────────────────────────────────
// Ensures engine subprocess is killed cleanly on quit.
// ───────────────────────────────────────────────────────

import { app } from 'electron';
import type { EngineManager } from './engine/engine-manager';

export function setupAppLifecycle(
  getEngineManager: () => EngineManager | null,
): void {
  app.on('window-all-closed', () => {
    // On macOS, keep the app running in the menu bar
    if (process.platform !== 'darwin') {
      app.quit();
    }
  });

  app.on('before-quit', async () => {
    const engineManager = getEngineManager();
    if (engineManager) {
      await engineManager.stop();
    }
  });

  app.on('activate', () => {
    // On macOS, re-create a window when the dock icon is clicked
    const { BrowserWindow } = require('electron');
    if (BrowserWindow.getAllWindows().length === 0) {
      const { createMainWindow } = require('./window/main-window');
      createMainWindow();
    }
  });
}
