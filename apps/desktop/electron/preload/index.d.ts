// ── Preload Type Declarations ──────────────────────────
// TypeScript declarations for window.dexpert
// ───────────────────────────────────────────────────────

import type { ClientMessage, EngineEvent } from '@dexpert/types';

export interface DexpertAPI {
  engine: {
    send(msg: ClientMessage): void;
    onEvent(callback: (event: EngineEvent) => void): () => void;
    getStatus(): Promise<string>;
  };
  auth: {
    getToken(): Promise<string | null>;
    clearToken(): Promise<void>;
  };
  window: {
    minimize(): void;
    maximize(): void;
    close(): void;
    isMaximized(): Promise<boolean>;
  };
  shell: {
    openExternal(url: string): void;
  };
  app: {
    version(): Promise<string>;
    platform(): Promise<string>;
  };
}

declare global {
  interface Window {
    dexpert: DexpertAPI;
  }
}
