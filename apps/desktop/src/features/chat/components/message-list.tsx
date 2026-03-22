// ── Message List ───────────────────────────────────────
// Scrollable message list with auto-scroll to bottom.
// ───────────────────────────────────────────────────────

import React, { useRef, useEffect, useCallback } from 'react';
import type { ConversationTurn } from '@dexpert/types';
import { MessageItem } from './message-item';

interface MessageListProps {
  messages: ConversationTurn[];
  streamingMessageId?: string | null;
}

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  streamingMessageId,
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  // Auto-scroll on new messages or streaming updates
  useEffect(() => {
    scrollToBottom();
  }, [
    messages.length,
    messages[messages.length - 1]?.content,
    scrollToBottom,
  ]);

  return (
    <div
      ref={containerRef}
      className="flex-1 overflow-y-auto px-4 sm:px-8 lg:px-16 py-6 custom-scrollbar"
    >
      <div className="max-w-3xl mx-auto">
        {messages.map((msg, idx) => {
          const isLastMessage = idx === messages.length - 1;
          const isStreaming = isLastMessage && msg.id === streamingMessageId;

          return (
            <MessageItem
              key={msg.id}
              message={msg}
              isStreaming={isStreaming}
              isFinalStreamMessage={isLastMessage && !isStreaming}
            />
          );
        })}
        <div ref={bottomRef} className="h-4" />
      </div>
    </div>
  );
};
