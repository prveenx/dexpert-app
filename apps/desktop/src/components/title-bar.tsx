// ── Title Bar ──────────────────────────────────────────
// Custom frameless window chrome with traffic lights (macOS) / min+max+close (Windows)
// ───────────────────────────────────────────────────────

import { useEngineHealth } from '../hooks/use-engine-health';

const statusColors: Record<string, string> = {
  ready: 'bg-green-500',
  starting: 'bg-yellow-500 animate-pulse-dot',
  degraded: 'bg-yellow-500',
  offline: 'bg-red-500',
};

export function TitleBar() {
  const status = useEngineHealth();

  return (
    <div className="titlebar-drag flex h-9 items-center justify-between border-b border-gray-800 bg-gray-950 px-4">
      <div className="flex items-center gap-2">
        <span className="text-sm font-semibold text-gray-300">Dexpert</span>
        <div className={`h-2 w-2 rounded-full ${statusColors[status] || 'bg-gray-500'}`} />
        <span className="text-xs text-gray-500 capitalize">{status}</span>
      </div>

      <div className="titlebar-no-drag flex items-center gap-1">
        {/* Native window buttons are handled by Electron titleBarOverlay/traffic lights */}
      </div>
    </div>
  );
}
