// ── Engine Status Banner ───────────────────────────────

import { useEngineHealth } from '../hooks/use-engine-health';

export function EngineStatusBanner() {
  const status = useEngineHealth();

  if (status === 'ready' || status === 'starting') return null;

  return (
    <div className="flex items-center justify-center gap-2 bg-yellow-900/30 px-4 py-1.5 text-sm text-yellow-200 border-b border-yellow-800/50">
      <div className="h-2 w-2 rounded-full bg-yellow-500 animate-pulse-dot" />
      {status === 'degraded'
        ? 'Engine reconnecting...'
        : 'Engine offline — Check logs or restart'}
    </div>
  );
}
