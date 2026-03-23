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
import { useEffect, useRef } from 'react';

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
  const currentSessionId = useSessionStore((s) => s.currentSessionId);
  const allMessages = useSessionStore((s) => s.messages);
  
  const messages = React.useMemo(
    () => allMessages.filter(m => m.sessionId === currentSessionId),
    [allMessages, currentSessionId]
  );

  const { sendTask } = useSendTask();
  const [streamingMessageId, setStreamingMessageId] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const handleSend = useCallback(
    (content: string) => {
      sendTask(content);
    },
    [sendTask],
  );

  const hasMessages = messages.length > 0;
  const plannerStatus = useAgentsStore((s) => s.agentStatuses.planner);
  const isTyping = (plannerStatus === 'running') && 
                   (messages.length === 0 || messages[messages.length - 1].role === 'user');

  // Autoscroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  const handleStop = useCallback(() => {
    if (window.dexpert?.engine?.send && currentSessionId) {
      (window.dexpert.engine.send as any)({
        type: 'cancel',
        sessionId: currentSessionId,
      });
    }
  }, [currentSessionId]);

  return (
    <div className="flex h-full flex-col bg-white dark:bg-zinc-950 relative overflow-hidden">
      {/* Search Header */}
      <div className="flex-shrink-0 z-50">
        <ChatHeader />
      </div>

      <div className="flex-1 overflow-hidden relative flex flex-col">
        {hasMessages ? (
          <div 
            ref={scrollRef}
            className="flex-1 overflow-y-auto custom-scrollbar scroll-smooth px-4 sm:px-8 lg:px-16 pt-8"
          >
            <div className="max-w-3xl mx-auto">
              <MessageList
                messages={messages}
                streamingMessageId={streamingMessageId}
              />
              {isTyping && (
                <div className="mt-6">
                  <TypingIndicator />
                </div>
              )}
            </div>
            {/* Safe area at bottom of scrollable content */}
            <div className="h-24" />
          </div>
        ) : (
          <EmptyState onSuggestion={handleSend} />
        )}
      </div>

      {/* Input Bar — Stunning blurred gradient transition */}
      <div className="flex-shrink-0 relative z-40 px-4 sm:px-8 lg:px-16 pt-16 pb-2">
        {/* The glassmorphic fog effect */}
        <div className="absolute inset-0 bg-gradient-to-t from-white via-white/95 to-transparent dark:from-zinc-950 dark:via-zinc-950/95 dark:to-transparent backdrop-blur-xl pointer-events-none" />
        
        <div className="max-w-3xl mx-auto relative z-10">
          <ChatInput 
            onSend={handleSend} 
            onStop={handleStop}
            isWorking={plannerStatus === 'running'}
          />
        </div>
      </div>
    </div>
  );
};
