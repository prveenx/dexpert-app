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
      handleDeepLink(url, authWindow); 
    }
  });

  authWindow.webContents.on('will-redirect', (event, url) => {
    if (url.startsWith('dexpert://')) {
      event.preventDefault();
      handleDeepLink(url, authWindow);
    }
  });

  // Handle load failure proactively
  authWindow.webContents.on('did-fail-load', (e, errorCode, errorDescription) => {
    console.error(`[AuthWindow] Failed to load auth URL: ${errorCode} - ${errorDescription}`);
    // If it's a connection refused, tell the user the web server isn't running
    if (errorCode === -102 || errorCode === -105) {
       authWindow.webContents.executeJavaScript(`
          document.body.innerHTML = \`
             <div style="background:#09090b; color:#fff; height:100vh; display:flex; flex-direction:column; align-items:center; justify-content:center; font-family: sans-serif; text-align:center; padding: 2rem;">
                <div style="padding: 1rem 1.5rem; background: #ef4444; color: white; border-radius: 1rem; font-weight: 800; font-size: 0.75rem; text-transform: uppercase; margin-bottom: 2rem;">Engine Connection Timeout</div>
                <h1 style="font-size: 2rem; font-weight: 900; margin-bottom: 1rem;">Web App Offline</h1>
                <p style="color: #a1a1aa; max-width: 400px; line-height: 1.6;">The authentication gateway is unreachable on port 3000. Please ensure "pnpm run dev" is running and checking for Next.js build errors.</p>
                <div style="margin-top: 3rem; font-family: monospace; color: #71717a; font-size: 0.8rem;">ERROR_CODE: ${errorCode}</div>
             </div>
          \`;
       `);
    }
  });

  // Load the external Web Application route for Auth
  const NEXT_APP_URL = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000';
  authWindow.loadURL(`${NEXT_APP_URL}/login?platform=desktop`);

  return authWindow;
}
