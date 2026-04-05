// ── Message Item (v2) ──────────────────────────────────
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
import { FileCard } from './file-card';
import { TerminalBlock } from './terminal-block';
import { DiffView } from './diff-view';
import { AgentHandoff } from './agent-handoff';

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
      // Handle specialty typed blocks from metadata
      const type = metadata?.type as string | undefined;

      switch (type) {
        case 'thinking':
          return (
            <ThinkingBlock
              content={metadata?.thinking as string}
              isStreaming={isStreaming}
            />
          );

        case 'tool_call':
          return (
            <ToolCallBlock
              toolName={metadata?.toolName as string}
              args={metadata?.args as Record<string, unknown>}
              isRunning={metadata?.isRunning as boolean}
              callId={metadata?.callId as string}
            />
          );

        case 'tool_result':
          return (
            <ToolCallBlock
              toolName={metadata?.toolName as string}
              result={metadata?.result as string}
              success={metadata?.success as boolean}
              callId={metadata?.callId as string}
            />
          );

        case 'file_created':
          return (
            <FileCard
              filePath={metadata?.filePath as string}
              language={metadata?.language as string}
              contentPreview={metadata?.contentPreview as string}
              agentId={agentId}
            />
          );

        case 'file_modified':
          return (
            <DiffView
              filePath={metadata?.filePath as string}
              diff={metadata?.diff as string}
              agentId={agentId}
            />
          );

        case 'terminal_output':
          return (
            <TerminalBlock
              command={metadata?.command as string}
              output={metadata?.output as string}
              exitCode={metadata?.exitCode as number}
              isError={metadata?.isError as boolean}
              agentId={agentId}
            />
          );

        case 'agent_handoff':
          return (
            <AgentHandoff
              fromAgent={metadata?.fromAgent as string}
              toAgent={metadata?.toAgent as string}
              taskSummary={metadata?.taskSummary as string}
            />
          );

        default:
          // Fallback to standard agent response
          if (isStreaming && !content) return <TypingIndicator />;
          return (
            <AgentResponse
              content={content}
              agentId={agentId}
              timestamp={timestamp}
              isStreaming={isStreaming}
            />
          );
      }
    }

    return null;
  },
  (prev, next) => {
    return (
      prev.message.id === next.message.id &&
      prev.message.content === next.message.content &&
      prev.isStreaming === next.isStreaming &&
      prev.isFinalStreamMessage === next.isFinalStreamMessage
    );
  }
);

MessageItem.displayName = 'MessageItem';
