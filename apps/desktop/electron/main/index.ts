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
import { createTray } from './tray';
import { setupAppMenu } from './app-menu';
import { EngineHealthMonitor } from './engine/engine-health';

// Prevent multiple instances
const gotTheLock = app.requestSingleInstanceLock();
if (!gotTheLock) {
  app.quit();
}

// Engine manager singleton
let engineManager: EngineManager | null = null;
let engineClient: EngineClient | null = null;
let healthMonitor: EngineHealthMonitor | null = null;
let mainWindow: BrowserWindow | null = null;
let authWindow: BrowserWindow | null = null;
let tray: any = null;

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

      healthMonitor = new EngineHealthMonitor(port);
      if (mainWindow) healthMonitor.registerWindow(mainWindow);
      if (authWindow) healthMonitor.registerWindow(authWindow);
      healthMonitor.start();
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
    mainWindow = createMainWindow(engineManager.getPort());
    tray = createTray(mainWindow);
    setupAppMenu(mainWindow);
    if (healthMonitor) healthMonitor.registerWindow(mainWindow);
  } else {
    authWindow = createAuthWindow();
    if (healthMonitor) healthMonitor.registerWindow(authWindow);
  }

  // Handle second instance (deep links on Windows)
  app.on('second-instance', (_event, argv) => {
    const activeWindow = mainWindow || authWindow;
    if (activeWindow) {
      if (activeWindow.isMinimized()) activeWindow.restore();
      activeWindow.show();
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
        mainWindow = createMainWindow(engineManager!.getPort());
        tray = createTray(mainWindow);
        setupAppMenu(mainWindow);
        if (healthMonitor) healthMonitor.registerWindow(mainWindow);
      }
    }
  });

  // Handle internal auth completion
  // Handle internal auth completion
  app.on('auth-success' as any, () => {
    const token = TokenStore.get();
    if (token && engineClient) {
      engineClient.setToken(token);
    }

    if (authWindow) {
      authWindow.close();
      authWindow = null;
      mainWindow = createMainWindow(engineManager!.getPort());
      tray = createTray(mainWindow);
      setupAppMenu(mainWindow);
      if (healthMonitor) healthMonitor.registerWindow(mainWindow);
    }
  });

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
    const activeWindow = mainWindow || authWindow;
    handleDeepLink(url, activeWindow);
    if (url.startsWith('dexpert://token') && authWindow) {
      // Swap windows
      authWindow.close();
      authWindow = null;
      mainWindow = createMainWindow(engineManager!.getPort());
      tray = createTray(mainWindow);
      setupAppMenu(mainWindow);
      if (healthMonitor) healthMonitor.registerWindow(mainWindow);
    }
  });
}

app.whenReady().then(bootstrap);

// Setup app lifecycle handlers
setupAppLifecycle(() => engineManager);
