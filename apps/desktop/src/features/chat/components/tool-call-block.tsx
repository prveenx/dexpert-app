// ── Tool Call Block ────────────────────────────────────
// Collapsible: tool name + input args + result preview.
// Adapted from ExecutionLogs in original chat-view.tsx.
// ───────────────────────────────────────────────────────

import React, { useState, useRef, useEffect } from 'react';
import { ChevronRight, Terminal, Globe, Loader2, Check, X } from 'lucide-react';

interface ToolCallBlockProps {
  toolName: string;
  args?: Record<string, unknown>;
  result?: string;
  isRunning?: boolean;
  success?: boolean;
  callId?: string;
}

export const ToolCallBlock: React.FC<ToolCallBlockProps> = ({
  toolName,
  args,
  result,
  isRunning = false,
  success = true,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const icon = toolName.toLowerCase().includes('browse') || toolName.toLowerCase().includes('navigate')
    ? <Globe className="w-3.5 h-3.5 text-blue-500" />
    : <Terminal className="w-3.5 h-3.5 text-purple-500" />;

  const statusIcon = isRunning
    ? <Loader2 className="w-3.5 h-3.5 text-violet-500 animate-spin" />
    : success
      ? <Check className="w-3.5 h-3.5 text-green-500" />
      : <X className="w-3.5 h-3.5 text-red-500" />;

  return (
    <div className="w-full my-2 animate-in fade-in duration-200 border border-zinc-200 dark:border-zinc-800 rounded-lg overflow-hidden bg-white dark:bg-zinc-900/50">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center justify-between w-full px-3 py-2.5 hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-colors"
      >
        <div className="flex items-center gap-2.5">
          <div
            className={`p-0.5 text-zinc-500 transition-transform duration-200 ${
              isExpanded ? 'rotate-90' : ''
            }`}
          >
            <ChevronRight className="w-3.5 h-3.5" />
          </div>
          {icon}
          <span className="text-xs font-semibold text-zinc-700 dark:text-zinc-300 uppercase tracking-wide">
            {toolName}
          </span>
        </div>
        {statusIcon}
      </button>

      {isExpanded && (
        <div className="border-t border-zinc-100 dark:border-zinc-800 p-3 font-mono text-xs space-y-2">
          {args && Object.keys(args).length > 0 && (
            <div>
              <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wide">
                Arguments
              </span>
              <pre className="mt-1 p-2 bg-zinc-50 dark:bg-zinc-950 rounded text-zinc-600 dark:text-zinc-400 whitespace-pre-wrap break-words max-h-32 overflow-auto custom-scrollbar">
                {JSON.stringify(args, null, 2)}
              </pre>
            </div>
          )}
          {result && (
            <div>
              <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wide">
                Result
              </span>
              <pre className="mt-1 p-2 bg-zinc-50 dark:bg-zinc-950 rounded text-zinc-600 dark:text-zinc-400 whitespace-pre-wrap break-words max-h-48 overflow-auto custom-scrollbar">
                {result}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
