import { BrowserWindow, shell } from 'electron';
import { join } from 'path';
import { is } from '@electron-toolkit/utils';

import { handleDeepLink } from '../auth/protocol-handler';
import { createMainWindow } from './main-window';

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

  // Intercept deep link navigation internally

  authWindow.webContents.on('will-navigate', (event, url) => {
    if (url.startsWith('dexpert://')) {
      event.preventDefault();
      handleDeepLink(url, null); // window is null here as we are about to close this one
      
      // Swap windows
      authWindow.close();
      createMainWindow();
    }
  });

  authWindow.webContents.on('will-redirect', (event, url) => {
    if (url.startsWith('dexpert://')) {
      event.preventDefault();
      handleDeepLink(url, null);
      
      // Swap windows
      authWindow.close();
      createMainWindow();
    }
  });

  // Load the external Web Application route for Auth
  const NEXT_APP_URL = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000';
  authWindow.loadURL(`${NEXT_APP_URL}/login?platform=desktop`);

  return authWindow;
}
