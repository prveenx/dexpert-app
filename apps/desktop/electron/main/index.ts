// ── Electron Main Process Entry Point ──────────────────
// Responsibilities:
// - app.whenReady()
// - Register protocol handler (dexpert://)
// - Start engine subprocess
// - Open MainWindow
// ───────────────────────────────────────────────────────

import { app, BrowserWindow } from 'electron';
import { join } from 'path';
import { createMainWindow } from './window/main-window';
import { createAuthWindow } from './window/auth-window';
import { registerIpcHandlers } from './ipc/handlers';
import { setupAppLifecycle } from './app-lifecycle';
import { EngineManager } from './engine/engine-manager';
import { setupSecurity } from './security';
import { TokenStore } from './auth/token-store';
import { handleDeepLink } from './auth/protocol-handler';

// Prevent multiple instances
const gotTheLock = app.requestSingleInstanceLock();
if (!gotTheLock) {
  app.quit();
}

// Engine manager singleton
let engineManager: EngineManager | null = null;
let mainWindow: BrowserWindow | null = null;
let authWindow: BrowserWindow | null = null;

async function bootstrap(): Promise<void> {
  // Security hardening
  setupSecurity();

  // Register IPC handlers before creating windows
  registerIpcHandlers();

  // Start engine subprocess
  engineManager = new EngineManager();
  await engineManager.start();

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
