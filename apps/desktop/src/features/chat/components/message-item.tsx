// ── Message Item ───────────────────────────────────────
// Polymorphic renderer that dispatches to the correct component
// based on message role and metadata.
// ───────────────────────────────────────────────────────

import React, { memo } from 'react';
import type { ConversationTurn } from '@dexpert/types';
import { UserBubble } from './user-bubble';
import { AgentResponse } from './agent-response';
import { SystemNotice } from './system-notice';
import { ThinkingBlock } from './thinking-block';
import { ToolCallBlock } from './tool-call-block';
import { TypingIndicator } from './typing-indicator';

export interface MessageItemProps {
  message: ConversationTurn;
  isStreaming?: boolean;
  isFinalStreamMessage?: boolean;
}

export const MessageItem = memo<MessageItemProps>(
  ({ message, isStreaming = false, isFinalStreamMessage = false }) => {
    const { role, content, agentId, timestamp, metadata } = message;

    // System messages
    if (role === 'system') {
      return <SystemNotice content={content} />;
    }

    // User messages
    if (role === 'user') {
      return <UserBubble content={content} timestamp={timestamp} />;
    }

    // Assistant messages
    if (role === 'assistant') {
      // If this is a streaming message with no content yet, show typing
      if (isStreaming && !content) {
        return <TypingIndicator />;
      }

      // Check metadata for thinking/tool calls
      const thinking = metadata?.thinking as string | undefined;
      const toolCalls = metadata?.toolCalls as Array<{
        name: string;
        args?: Record<string, unknown>;
        result?: string;
        isRunning?: boolean;
        success?: boolean;
      }> | undefined;

      return (
        <div className="space-y-2">
          {/* Thinking Block */}
          {thinking && (
            <ThinkingBlock
              content={thinking}
              isStreaming={isStreaming && !content}
            />
          )}

          {/* Tool Call Blocks */}
          {toolCalls?.map((tc, idx) => (
            <ToolCallBlock
              key={`${message.id}-tc-${idx}`}
              toolName={tc.name}
              args={tc.args}
              result={tc.result}
              isRunning={tc.isRunning}
              success={tc.success}
            />
          ))}

          {/* Agent Response */}
          {content && (
            <AgentResponse
              content={content}
              agentId={agentId}
              timestamp={timestamp}
              isStreaming={isStreaming}
            />
          )}
        </div>
      );
    }

    return null;
  },
  (prev, next) => {
    // Only re-render when relevant props change
    return (
      prev.message.id === next.message.id &&
      prev.message.content === next.message.content &&
      prev.isStreaming === next.isStreaming &&
      prev.isFinalStreamMessage === next.isFinalStreamMessage
    );
  }
);

MessageItem.displayName = 'MessageItem';
