// ── IPC Handlers ───────────────────────────────────────
// Registers all ipcMain.handle() calls.
// ───────────────────────────────────────────────────────

import { ipcMain, shell, app, BrowserWindow } from 'electron';
import { IPC } from './channels';
import { TokenStore } from '../auth/token-store';

export function registerIpcHandlers(): void {
  // ── Window Controls ────────────────────────────────
  ipcMain.on(IPC.WINDOW_MINIMIZE, (event) => {
    BrowserWindow.fromWebContents(event.sender)?.minimize();
  });

  ipcMain.on(IPC.WINDOW_MAXIMIZE, (event) => {
    const win = BrowserWindow.fromWebContents(event.sender);
    if (win) {
      win.isMaximized() ? win.unmaximize() : win.maximize();
    }
  });

  ipcMain.on(IPC.WINDOW_CLOSE, (event) => {
    BrowserWindow.fromWebContents(event.sender)?.close();
  });

  ipcMain.handle(IPC.WINDOW_IS_MAXIMIZED, (event) => {
    return BrowserWindow.fromWebContents(event.sender)?.isMaximized() ?? false;
  });

  // ── Shell ──────────────────────────────────────────
  ipcMain.on(IPC.SHELL_OPEN_EXTERNAL, (_event, url: string) => {
    shell.openExternal(url);
  });

  // ── App ────────────────────────────────────────────
  ipcMain.handle(IPC.APP_VERSION, () => {
    return app.getVersion();
  });

  ipcMain.handle(IPC.APP_PLATFORM, () => {
    return process.platform;
  });

  // ── Auth ───────────────────────────────────────────

  ipcMain.handle(IPC.AUTH_GET_TOKEN, () => {
    return TokenStore.get();
  });

  ipcMain.handle(IPC.AUTH_SET_TOKEN, (_event, token: string) => {
    TokenStore.save(token);
    app.emit('auth-success');
    return true;
  });

  ipcMain.handle(IPC.AUTH_CLEAR, () => {
    TokenStore.clear();
    return;
  });
}
