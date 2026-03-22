// ── Electron Bridge Types ────────────────────────────────
// Defines the window.dexpert API provided by the preload script.
// ───────────────────────────────────────────────────────

import type { ClientMessage, EngineEvent } from '@dexpert/types';

declare global {
  interface Window {
    dexpert: {
      engine: {
        /**
         * Send a message to the Dexpert Engine via WebSocket.
         */
        send: (message: ClientMessage) => void;

        /**
         * Subscribe to Engine events.
         * Returns an unsubscribe function.
         */
        onEvent: (callback: (event: EngineEvent) => void) => () => void;
      };
      rpc?: {
        invoke: (channel: string, ...args: any[]) => Promise<any>;
        on: (channel: string, callback: (...args: any[]) => void) => () => void;
      };
    };
  }
}

export {};
