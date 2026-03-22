// ── System Notice ──────────────────────────────────────
// System messages: "Session resumed from checkpoint"
// ───────────────────────────────────────────────────────

import React from 'react';
import { Info } from 'lucide-react';

interface SystemNoticeProps {
  content: string;
}

export const SystemNotice: React.FC<SystemNoticeProps> = ({ content }) => {
  return (
    <div className="flex justify-center my-4 animate-in fade-in duration-300">
      <div className="flex items-center gap-2 px-4 py-2 bg-zinc-100 dark:bg-zinc-800/50 rounded-full border border-zinc-200 dark:border-zinc-700">
        <Info className="w-3.5 h-3.5 text-zinc-400" />
        <span className="text-xs text-zinc-500 dark:text-zinc-400 font-medium">
          {content}
        </span>
      </div>
    </div>
  );
};
