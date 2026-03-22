// ── Engine Store ───────────────────────────────────────

import { create } from 'zustand';

export type ConnectionStatus = 'starting' | 'ready' | 'degraded' | 'offline';

interface EngineStoreState {
  connectionStatus: ConnectionStatus;
  engineVersion: string | null;
  lastHealthCheck: string | null;
}

interface EngineStoreActions {
  setStatus: (status: ConnectionStatus) => void;
  setVersion: (version: string) => void;
  setLastHealthCheck: (timestamp: string) => void;
}

export const useEngineStore = create<EngineStoreState & EngineStoreActions>((set) => ({
  connectionStatus: 'starting',
  engineVersion: null,
  lastHealthCheck: null,

  setStatus: (status) => set({ connectionStatus: status }),
  setVersion: (version) => set({ engineVersion: version }),
  setLastHealthCheck: (timestamp) => set({ lastHealthCheck: timestamp }),
}));
