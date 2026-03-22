import { BrowserWindow, shell } from 'electron';
import { join } from 'path';
import { is } from '@electron-toolkit/utils';

export function createAuthWindow(): BrowserWindow {
  const authWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    frame: false,
    resizable: true,
    center: true,
    show: false,
    autoHideMenuBar: true,
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: true,
      contextIsolation: true,
      nodeIntegration: false,
      devTools: true,
    },
  });

  // Enable full screen / maximized if needed
  authWindow.maximize();

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
