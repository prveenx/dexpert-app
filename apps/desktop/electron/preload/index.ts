// ── Preload Bridge ─────────────────────────────────────
// contextBridge.exposeInMainWorld('dexpert', {...})
// ───────────────────────────────────────────────────────

import { contextBridge, ipcRenderer } from 'electron';
import { IPC } from '../main/ipc/channels';

const api = {
  engine: {
    send: (msg: unknown): void => {
      ipcRenderer.send(IPC.ENGINE_SEND, msg);
    },
    onEvent: (callback: (event: unknown) => void): (() => void) => {
      const handler = (_event: unknown, data: unknown) => callback(data);
      ipcRenderer.on(IPC.ENGINE_EVENTS, handler);
      return () => ipcRenderer.removeListener(IPC.ENGINE_EVENTS, handler);
    },
    getStatus: (): Promise<string> => {
      return ipcRenderer.invoke(IPC.ENGINE_STATUS);
    },
  },
  auth: {
    getToken: (): Promise<string | null> => {
      return ipcRenderer.invoke(IPC.AUTH_GET_TOKEN);
    },
    setToken: (token: string): Promise<void> => {
      return ipcRenderer.invoke(IPC.AUTH_SET_TOKEN, token);
    },
    clearToken: (): Promise<void> => {
      return ipcRenderer.invoke(IPC.AUTH_CLEAR);
    },
  },
  window: {
    minimize: (): void => ipcRenderer.send(IPC.WINDOW_MINIMIZE),
    maximize: (): void => ipcRenderer.send(IPC.WINDOW_MAXIMIZE),
    close: (): void => ipcRenderer.send(IPC.WINDOW_CLOSE),
    isMaximized: (): Promise<boolean> => ipcRenderer.invoke(IPC.WINDOW_IS_MAXIMIZED),
  },
  shell: {
    openExternal: (url: string): void => {
      ipcRenderer.send(IPC.SHELL_OPEN_EXTERNAL, url);
    },
  },
  app: {
    version: (): Promise<string> => ipcRenderer.invoke(IPC.APP_VERSION),
    platform: (): Promise<string> => ipcRenderer.invoke(IPC.APP_PLATFORM),
  },
  storage: {
    getSessions: (): Promise<any> => ipcRenderer.invoke(IPC.STORAGE_GET_SESSIONS),
    setSessions: (data: any): Promise<boolean> => ipcRenderer.invoke(IPC.STORAGE_SET_SESSIONS, data),
  },
};

contextBridge.exposeInMainWorld('dexpert', api);

export type DexpertAPI = typeof api;
