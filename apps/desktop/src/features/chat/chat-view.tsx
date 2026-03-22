// ── Chat View ──────────────────────────────────────────
// Top-level chat layout: <MessageList> + <ChatInput>
// Subscribes to session.store + engine events.
// ───────────────────────────────────────────────────────

import React, { useState, useCallback } from 'react';
import { useSessionStore } from '../../stores/session.store';
import { useEngineStore } from '../../stores/engine.store';
import { useAgentsStore } from '../../stores/agents.store';
import { useSendTask } from '../../hooks/use-send-task';
import { MessageList, TypingIndicator } from './components';
import { ChatInput } from './chat-input';
import { Bot, Sparkles, ArrowRight } from 'lucide-react';

// ── Empty State ───────────────────────────────────────

const EmptyState: React.FC<{ onSuggestion: (text: string) => void }> = ({
  onSuggestion,
}) => {
  const suggestions = [
    { icon: '✨', text: 'Create a Python script to organize my Downloads folder' },
    { icon: '🔍', text: 'Search the web for the latest AI research papers' },
    { icon: '📂', text: 'Help me clean up duplicate files on my Desktop' },
    { icon: '💡', text: 'Explain how transformers work in simple terms' },
  ];

  return (
    <div className="flex-1 flex items-center justify-center px-4">
      <div className="max-w-2xl w-full space-y-8 text-center">
        {/* Logo */}
        <div className="flex flex-col items-center gap-4">
          <div className="relative">
            <div className="w-16 h-16 bg-gradient-to-br from-violet-500 to-indigo-600 rounded-2xl flex items-center justify-center shadow-lg shadow-violet-500/20">
              <Bot className="w-8 h-8 text-white" />
            </div>
            <div className="absolute -top-1 -right-1 w-6 h-6 bg-gradient-to-br from-amber-400 to-orange-500 rounded-full flex items-center justify-center shadow-md">
              <Sparkles className="w-3 h-3 text-white" />
            </div>
          </div>
          <div>
            <h1 className="text-2xl font-bold text-zinc-100">
              How can I help you today?
            </h1>
            <p className="text-sm text-zinc-500 mt-1">
              I can browse the web, manage files, run commands, and more.
            </p>
          </div>
        </div>

        {/* Suggestions */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {suggestions.map((s, i) => (
            <button
              key={i}
              onClick={() => onSuggestion(s.text)}
              className="group flex items-center gap-3 p-4 text-left rounded-xl border border-zinc-800 bg-zinc-900/50 hover:bg-zinc-800/80 hover:border-zinc-700 transition-all duration-200"
            >
              <span className="text-lg">{s.icon}</span>
              <span className="text-sm text-zinc-400 group-hover:text-zinc-200 transition-colors flex-1">
                {s.text}
              </span>
              <ArrowRight className="w-4 h-4 text-zinc-600 group-hover:text-violet-400 transition-colors opacity-0 group-hover:opacity-100" />
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

// ── Chat Header ───────────────────────────────────────

const ChatHeader: React.FC = () => {
  const plannerStatus = useAgentsStore((s) => s.agentStatuses.planner);

  return (
    <div className="flex items-center justify-between px-6 py-3 border-b border-zinc-800/50 bg-zinc-950/80 backdrop-blur-sm">
      <div className="flex items-center gap-2">
        <span className="text-sm font-medium text-zinc-300">Chat</span>
        {plannerStatus === 'running' && (
          <span className="text-[10px] px-2 py-0.5 bg-violet-500/10 text-violet-400 rounded-full font-medium animate-pulse">
            Processing...
          </span>
        )}
      </div>
    </div>
  );
};

// ── Main Chat View ────────────────────────────────────

export const ChatView: React.FC = () => {
  const messages = useSessionStore((s) => s.messages);
  const { sendTask } = useSendTask();
  const [streamingMessageId, setStreamingMessageId] = useState<string | null>(null);

  const handleSend = useCallback(
    (content: string) => {
      sendTask(content);
    },
    [sendTask],
  );

  const hasMessages = messages.length > 0;

  return (
    <div className="flex flex-col h-full bg-zinc-950">
      <ChatHeader />

      {hasMessages ? (
        <MessageList
          messages={messages}
          streamingMessageId={streamingMessageId}
        />
      ) : (
        <EmptyState onSuggestion={handleSend} />
      )}

      {/* Input Bar — always at bottom */}
      <div className="border-t border-zinc-800/50 bg-zinc-950/80 backdrop-blur-sm px-4 sm:px-8 lg:px-16 py-4">
        <div className="max-w-3xl mx-auto">
          <ChatInput onSend={handleSend} />
        </div>
      </div>
    </div>
  );
};
