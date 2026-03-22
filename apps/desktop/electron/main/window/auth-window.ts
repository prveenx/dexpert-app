import { BrowserWindow, shell } from 'electron';
import { join } from 'path';
import { is } from '@electron-toolkit/utils';

export function createAuthWindow(): BrowserWindow {
  const authWindow = new BrowserWindow({
    width: 800,
    height: 560,
    frame: false,
    resizable: false,
    center: true,
    show: false,
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: true,
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  authWindow.on('ready-to-show', () => {
    authWindow.show();
  });

  authWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  // Load the external Web Application route for Auth
  const NEXT_APP_URL = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000';
  authWindow.loadURL(`${NEXT_APP_URL}/login?platform=desktop`);

  return authWindow;
}
