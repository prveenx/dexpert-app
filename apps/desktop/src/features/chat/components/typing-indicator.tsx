// ── Typing Indicator ───────────────────────────────────
// Premium thinking indicator with avatar and shimmer effect.
// ───────────────────────────────────────────────────────

import React from 'react';
import { Bot } from 'lucide-react';

export const TypingIndicator: React.FC<{ label?: string; agentId?: string }> = ({
  label = 'Dexpert is thinking...',
  agentId = 'planner',
}) => {
  return (
    <div className="flex gap-4 w-full max-w-full animate-in fade-in slide-in-from-bottom-2 duration-500 mb-6 px-1">
      <div className="flex-shrink-0">
        <div className="w-8 h-8 bg-gradient-to-br from-violet-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-violet-500/10 ring-1 ring-white/10">
          <Bot className="w-4.5 h-4.5 text-white animate-pulse" />
        </div>
      </div>

      <div className="flex-1 min-w-0 flex flex-col gap-2 pt-1">
        <div className="flex items-center gap-2">
          <span className="text-sm font-bold text-violet-400 uppercase tracking-widest text-[10px]">
            {agentId === 'planner' ? 'Dexpert' : agentId.toUpperCase()}
          </span>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex space-x-1.5 items-center">
            <div className="w-1.5 h-1.5 bg-violet-500 rounded-full animate-bounce [animation-delay:-0.3s]" />
            <div className="w-1.5 h-1.5 bg-violet-500 rounded-full animate-bounce [animation-delay:-0.15s]" />
            <div className="w-1.5 h-1.5 bg-violet-500 rounded-full animate-bounce" />
          </div>
          <span className="text-sm font-medium text-zinc-500 dark:text-zinc-500 animate-pulse bg-clip-text text-transparent bg-gradient-to-r from-zinc-500 via-zinc-300 to-zinc-500">
            {label}
          </span>
        </div>

        {/* Shimmer bar */}
        <div className="h-2 w-32 bg-zinc-800/50 rounded-full overflow-hidden relative border border-zinc-800/20">
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-violet-500/20 to-transparent -translate-x-full animate-shimmer" />
        </div>
      </div>
    </div>
  );
};
