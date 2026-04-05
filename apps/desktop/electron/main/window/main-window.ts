// ── Main Window Factory ────────────────────────────────

import { BrowserWindow, shell, screen } from 'electron';
import { join } from 'path';
import { is } from '@electron-toolkit/utils';
import { WindowStateManager } from './window-state';

export function createMainWindow(port: number): BrowserWindow {
  const state = WindowStateManager.getInitialBounds('main');
  const windowManager = new WindowStateManager('main');

  const mainWindow = new BrowserWindow({
    // ... existing props ...
    width: state.width || 1280,
    height: state.height || 800,
    x: state.x,
    y: state.y,
    minWidth: 900,
    minHeight: 600,
    frame: false,
    titleBarStyle: 'hidden',
    titleBarOverlay: process.platform === 'win32' ? {
      color: '#00000000',
      symbolColor: '#ffffff',
      height: 36,
    } : undefined,
    show: false,
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: true,
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  windowManager.manage(mainWindow);

  mainWindow.on('ready-to-show', () => {
    mainWindow.show();
  });

  // Open external links in default browser
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  // Load renderer
  const urlParams = `?port=${port}`;
  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'] + urlParams);
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'), { query: { port: port.toString() } });
  }

  return mainWindow;
}
