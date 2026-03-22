// ── Thinking Block ─────────────────────────────────────
// Collapsible: agent's inner reasoning (italic, muted).
// Adapted from ThinkingProcess in original chat-view.tsx.
// ───────────────────────────────────────────────────────

import React, { useState, useRef, useEffect } from 'react';
import { ChevronRight, Brain, Loader2 } from 'lucide-react';

interface ThinkingBlockProps {
  content: string;
  isStreaming?: boolean;
}

export const ThinkingBlock: React.FC<ThinkingBlockProps> = ({
  content,
  isStreaming = false,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isExpanded && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [content, isExpanded]);

  if (!content) return null;

  const tokenEstimate = Math.round(content.length / 4);

  return (
    <div className="w-full my-3 animate-in fade-in slide-in-from-top-1 duration-300 border border-zinc-200 dark:border-zinc-800 rounded-xl overflow-hidden bg-white dark:bg-zinc-900/50">
      {/* Toggle Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="group flex items-center justify-between w-full p-3 bg-zinc-50 dark:bg-zinc-900 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
      >
        <div className="flex items-center gap-2.5">
          <div
            className={`p-1 rounded-md bg-zinc-200 dark:bg-zinc-800 text-zinc-500 transition-transform duration-200 ${
              isExpanded ? 'rotate-90' : ''
            }`}
          >
            <ChevronRight className="w-4 h-4" />
          </div>
          <Brain className="w-4 h-4 text-zinc-500" />
          <span className="text-xs font-semibold text-zinc-700 dark:text-zinc-300">
            Thought Process
          </span>
          <span className="text-[10px] text-zinc-400">{tokenEstimate} tokens</span>
        </div>
        {isStreaming && (
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-zinc-500 font-medium animate-pulse">
              Thinking
            </span>
            <Loader2 className="w-3.5 h-3.5 text-zinc-500 animate-spin" />
          </div>
        )}
      </button>

      {/* Expandable Content */}
      {isExpanded && (
        <div
          ref={scrollRef}
          className="max-h-64 overflow-y-auto p-4 text-xs custom-scrollbar bg-white dark:bg-zinc-950 text-zinc-600 dark:text-zinc-400 italic leading-relaxed whitespace-pre-wrap"
        >
          {content}
        </div>
      )}
    </div>
  );
};
