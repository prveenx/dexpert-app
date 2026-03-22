// ── Typing Indicator ───────────────────────────────────
// Three-dot pulse animation while agent is streaming.
// ───────────────────────────────────────────────────────

import React from 'react';

export const TypingIndicator: React.FC<{ label?: string }> = ({
  label = 'Thinking...',
}) => {
  return (
    <div className="flex items-center gap-3 py-2 px-1 animate-in fade-in duration-300">
      <div className="flex space-x-1.5">
        <div className="w-1.5 h-1.5 bg-violet-500 rounded-full animate-bounce [animation-delay:-0.3s]" />
        <div className="w-1.5 h-1.5 bg-violet-500 rounded-full animate-bounce [animation-delay:-0.15s]" />
        <div className="w-1.5 h-1.5 bg-violet-500 rounded-full animate-bounce" />
      </div>
      <span className="text-sm font-medium text-zinc-400 dark:text-zinc-500 animate-pulse">
        {label}
      </span>
    </div>
  );
};
