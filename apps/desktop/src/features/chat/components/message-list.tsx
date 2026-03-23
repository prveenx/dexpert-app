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
  return (
    <div className="flex flex-col gap-6">
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
    </div>
  );
};
