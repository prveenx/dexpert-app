// ── useEngine Hook ─────────────────────────────────────
// Manages WebSocket event subscription and dispatches to stores.
//
// Handles streaming by accumulating response chunks into a single
// assistant message, then finalizing when 'done' is received.
// ───────────────────────────────────────────────────────

import { useEffect, useRef } from 'react';
import { useEngineStore } from '../stores/engine.store';
import { useAgentsStore } from '../stores/agents.store';
import { useSessionStore } from '../stores/session.store';
import type { EngineEvent } from '@dexpert/types';

export function useEngine(): void {
  const setStatus = useEngineStore((s) => s.setStatus);
  const setAgentStatus = useAgentsStore((s) => s.setAgentStatus);
  const addToolCall = useAgentsStore((s) => s.addToolCall);
  const addMessage = useSessionStore((s) => s.addMessage);
  const updateMessage = useSessionStore((s) => s.updateMessage);

  // Track the current streaming message ID per session
  const streamingMessageRef = useRef<Record<string, string>>({});

  useEffect(() => {
    if (!window.dexpert?.engine?.onEvent) {
      // Engine API not available (running outside Electron / dev mode)
      setStatus('ready');
      return;
    }

    const unsubscribe = window.dexpert.engine.onEvent((event: EngineEvent) => {
      switch (event.type) {
        case 'agent_status':
          setAgentStatus(event.agentId, event.status, event.action);
          break;

        case 'tool_call':
          addToolCall(event.toolCall);
          break;

        case 'thinking':
          // For now, we could display thinking as a system message or
          // accumulate in metadata. Keeping it simple — log only.
          break;

        case 'response': {
          const { sessionId, content, isStreaming, agentId } = event;

          if (isStreaming) {
            // Streaming chunk — append to existing or create new message
            const existingId = streamingMessageRef.current[sessionId];

            if (existingId) {
              // Accumulate: append chunk to existing message
              updateMessage(existingId, (prev: string) => prev + content);
            } else {
              // First chunk — create new assistant message
              const msgId = crypto.randomUUID();
              streamingMessageRef.current[sessionId] = msgId;
              addMessage({
                id: msgId,
                sessionId,
                role: 'assistant',
                content,
                timestamp: new Date().toISOString(),
                agentId,
              });
            }
          } else {
            // Final (non-streaming) response — replace full content
            const existingId = streamingMessageRef.current[sessionId];
            if (existingId) {
              updateMessage(existingId, content);
              delete streamingMessageRef.current[sessionId];
            } else {
              // Single non-streaming response
              addMessage({
                id: crypto.randomUUID(),
                sessionId,
                role: 'assistant',
                content,
                timestamp: new Date().toISOString(),
                agentId,
              });
            }
          }
          break;
        }

        case 'done':
          // Clean up streaming state
          if (event.sessionId && streamingMessageRef.current[event.sessionId]) {
            delete streamingMessageRef.current[event.sessionId];
          }
          setStatus('ready');
          break;

        case 'error':
          console.error('[Engine Event] Error:', event.message);
          // Clean up streaming state on error
          if (event.sessionId && streamingMessageRef.current[event.sessionId]) {
            delete streamingMessageRef.current[event.sessionId];
          }
          break;

        case 'pong':
          // Health check response
          break;
      }
    });

    // Mark engine as ready (in dev mode without engine, we simulate)
    setTimeout(() => setStatus('ready'), 1000);

    return unsubscribe;
  }, [setStatus, setAgentStatus, addToolCall, addMessage, updateMessage]);
}
