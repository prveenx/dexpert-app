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
        <button
          onClick={() => window.dexpert?.window?.minimize()}
          className="flex h-7 w-7 items-center justify-center rounded hover:bg-gray-800"
          aria-label="Minimize"
        >
          <svg width="10" height="1" viewBox="0 0 10 1" fill="currentColor" className="text-gray-400">
            <rect width="10" height="1" />
          </svg>
        </button>
        <button
          onClick={() => window.dexpert?.window?.maximize()}
          className="flex h-7 w-7 items-center justify-center rounded hover:bg-gray-800"
          aria-label="Maximize"
        >
          <svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="currentColor" strokeWidth="1" className="text-gray-400">
            <rect x="0.5" y="0.5" width="9" height="9" />
          </svg>
        </button>
        <button
          onClick={() => window.dexpert?.window?.close()}
          className="flex h-7 w-7 items-center justify-center rounded hover:bg-red-600"
          aria-label="Close"
        >
          <svg width="10" height="10" viewBox="0 0 10 10" fill="currentColor" className="text-gray-400">
            <path d="M1 1L9 9M9 1L1 9" stroke="currentColor" strokeWidth="1.2" />
          </svg>
        </button>
      </div>
    </div>
  );
}
