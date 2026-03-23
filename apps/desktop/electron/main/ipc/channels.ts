// ── IPC Channel Constants ──────────────────────────────
// Never use raw strings for IPC channels.
// ───────────────────────────────────────────────────────

export const IPC = {
  // Engine
  ENGINE_SEND: 'engine:send',
  ENGINE_EVENTS: 'engine:events',
  ENGINE_STATUS: 'engine:status',

  // Auth
  AUTH_GET_TOKEN: 'auth:get-token',
  AUTH_SET_TOKEN: 'auth:set-token',
  AUTH_CLEAR: 'auth:clear',
  AUTH_SUCCESS: 'auth:success',

  // Window
  WINDOW_MINIMIZE: 'window:minimize',
  WINDOW_MAXIMIZE: 'window:maximize',
  WINDOW_CLOSE: 'window:close',
  WINDOW_IS_MAXIMIZED: 'window:is-maximized',

  // Shell
  SHELL_OPEN_EXTERNAL: 'shell:open-external',

  // App
  APP_VERSION: 'app:version',
  APP_PLATFORM: 'app:platform',
} as const;

export type IpcChannel = (typeof IPC)[keyof typeof IPC];
