// ── Electron Main Process Entry Point ──────────────────
// Responsibilities:
// - app.whenReady()
// - Register protocol handler (dexpert://)
// - Start engine subprocess
// - Open MainWindow
// ───────────────────────────────────────────────────────

import { app, BrowserWindow, ipcMain } from 'electron';
import { join } from 'path';
import { createMainWindow } from './window/main-window';
import { createAuthWindow } from './window/auth-window';
import { registerIpcHandlers } from './ipc/handlers';
import { setupAppLifecycle } from './app-lifecycle';
import { EngineManager } from './engine/engine-manager';
import { EngineClient } from './engine/engine-client';
import { setupSecurity } from './security';
import { TokenStore } from './auth/token-store';
import { handleDeepLink } from './auth/protocol-handler';
import { IPC } from './ipc/channels';

// Prevent multiple instances
const gotTheLock = app.requestSingleInstanceLock();
if (!gotTheLock) {
  app.quit();
}

// Engine manager singleton
let engineManager: EngineManager | null = null;
let engineClient: EngineClient | null = null;
let mainWindow: BrowserWindow | null = null;
let authWindow: BrowserWindow | null = null;

async function bootstrap(): Promise<void> {
  // Security hardening
  setupSecurity();

  // Register IPC handlers before creating windows
  registerIpcHandlers();

  // Start engine subprocess
  engineManager = new EngineManager();
  
  engineManager.on('ready', (port) => {
    if (!engineClient) {
      const token = TokenStore.get();
      engineClient = new EngineClient(port, token);
      engineClient.connect();
      
      engineClient.on('event', (eventData) => {
         const activeWindow = mainWindow || authWindow;
         if (activeWindow) {
            activeWindow.webContents.send(IPC.ENGINE_EVENTS, eventData);
         }
      });
    }
  });

  await engineManager.start();

  // Engine IPC bindings
  ipcMain.on(IPC.ENGINE_SEND, (_event, msg) => {
    if (engineClient) {
      engineClient.send(msg);
    }
  });

  ipcMain.handle(IPC.ENGINE_STATUS, () => {
    return engineClient ? 'connected' : 'disconnected';
  });

  // Read keychain to decide window
  const token = TokenStore.get();
  
  if (token) {
    mainWindow = createMainWindow();
  } else {
    authWindow = createAuthWindow();
  }

  // Handle second instance (deep links on Windows)
  app.on('second-instance', (_event, argv) => {
    const activeWindow = mainWindow || authWindow;
    if (activeWindow) {
      if (activeWindow.isMinimized()) activeWindow.restore();
      activeWindow.focus();
    }
    // Handle deep link from argv (Windows)
    const deepLink = argv.find((arg) => arg.startsWith('dexpert://'));
    if (deepLink) {
      handleDeepLink(deepLink, activeWindow);
      if (deepLink.startsWith('dexpert://token') && authWindow) {
        // Swap windows
        authWindow.close();
        authWindow = null;
        mainWindow = createMainWindow();
      }
    }
  });

  // Handle internal auth completion
  app.on('auth-success' as any, () => {
    const token = TokenStore.get();
    if (token && engineClient) {
      engineClient.setToken(token);
    }

    if (authWindow) {
      authWindow.close();
      authWindow = null;
      mainWindow = createMainWindow();
    }
  });
}

app.whenReady().then(bootstrap);

// Setup app lifecycle handlers
setupAppLifecycle(() => engineManager);

// Register protocol for deep links
if (process.defaultApp) {
  if (process.argv.length >= 2) {
    app.setAsDefaultProtocolClient('dexpert', process.execPath, [
      join(__dirname, '..', '..'),
    ]);
  }
} else {
  app.setAsDefaultProtocolClient('dexpert');
}

// macOS open-url
app.on('open-url', (event, url) => {
  event.preventDefault();
  handleDeepLink(url, mainWindow || authWindow);
  if (url.startsWith('dexpert://token') && authWindow) {
    // Swap windows
    authWindow.close();
    authWindow = null;
    mainWindow = createMainWindow();
  }
});
