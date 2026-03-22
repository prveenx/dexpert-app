// ── User Bubble ────────────────────────────────────────
// User message — right-aligned, rounded bubble.
// ───────────────────────────────────────────────────────

import React from 'react';
import { MarkdownRenderer } from './markdown-renderer';

interface UserBubbleProps {
  content: string;
  timestamp: string;
}

export const UserBubble: React.FC<UserBubbleProps> = ({ content, timestamp }) => {
  return (
    <div className="flex justify-end mb-6 animate-in fade-in slide-in-from-bottom-2 group/msg">
      <div className="flex flex-col items-end max-w-[85%] sm:max-w-[75%]">
        <div className="bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 rounded-2xl rounded-tr-md px-5 py-3 text-[15px] shadow-sm border border-zinc-200/50 dark:border-zinc-700/50">
          <MarkdownRenderer content={content} />
        </div>
        <span className="text-[10px] text-zinc-400 font-medium mt-1 mr-2 opacity-0 group-hover/msg:opacity-100 transition-opacity">
          {new Date(timestamp).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </span>
      </div>
    </div>
  );
};
