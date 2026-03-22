// ── Agent Response ─────────────────────────────────────
// Agent response — markdown-rendered, with agent badge.
// Includes copy/TTS actions on hover.
// ───────────────────────────────────────────────────────

import React, { useState } from 'react';
import { Bot, Copy, Check, Volume2 } from 'lucide-react';
import { MarkdownRenderer } from './markdown-renderer';

interface AgentResponseProps {
  content: string;
  agentId?: string;
  timestamp: string;
  isStreaming?: boolean;
}

const AgentBadge: React.FC<{ agentId: string }> = ({ agentId }) => {
  const config: Record<string, { label: string; color: string }> = {
    planner: { label: 'Dexpert', color: 'text-violet-600 dark:text-violet-400' },
    browser: { label: 'Browser', color: 'text-teal-600 dark:text-teal-400' },
    os: { label: 'OS Agent', color: 'text-amber-600 dark:text-amber-400' },
  };

  const { label, color } = config[agentId] || { label: 'Agent', color: 'text-zinc-600' };

  return (
    <div className="flex items-center gap-2 mb-2">
      <div className="p-1.5 bg-violet-100 dark:bg-violet-900/20 rounded-lg">
        <Bot className="w-4 h-4 text-violet-600 dark:text-violet-400" />
      </div>
      <span className={`text-sm font-bold ${color}`}>{label}</span>
    </div>
  );
};

const MessageActions: React.FC<{ text: string }> = ({ text }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex items-center gap-1 mt-2 opacity-0 group-hover/msg:opacity-100 transition-opacity">
      <button
        onClick={handleCopy}
        className="p-1.5 text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200 rounded-md hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
        title="Copy"
      >
        {copied ? (
          <Check className="w-3.5 h-3.5 text-green-500" />
        ) : (
          <Copy className="w-3.5 h-3.5" />
        )}
      </button>
    </div>
  );
};

export const AgentResponse: React.FC<AgentResponseProps> = ({
  content,
  agentId = 'planner',
  timestamp,
  isStreaming = false,
}) => {
  return (
    <div className="flex gap-4 w-full max-w-full animate-in fade-in duration-300 group/msg mb-6">
      <div className="flex-1 min-w-0 space-y-1">
        <AgentBadge agentId={agentId} />

        <div className="text-[15px] leading-relaxed">
          <MarkdownRenderer content={content} />

          {/* Streaming cursor */}
          {isStreaming && (
            <span className="inline-block w-2 h-4 bg-violet-500/50 ml-1 animate-pulse align-middle rounded-sm" />
          )}

          {/* Actions (shown on hover) */}
          {!isStreaming && content.length > 0 && (
            <MessageActions text={content} />
          )}
        </div>
      </div>
    </div>
  );
};
