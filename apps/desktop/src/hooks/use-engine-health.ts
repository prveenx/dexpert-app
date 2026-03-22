// ── useEngineHealth Hook ───────────────────────────────

import { useEngineStore, type ConnectionStatus } from '../stores/engine.store';

export function useEngineHealth(): ConnectionStatus {
  return useEngineStore((s) => s.connectionStatus);
}
