// ── useEngine Hook ─────────────────────────────────────
// Manages WebSocket event subscription and dispatches to stores.
//
// v2: Uses StreamManager for batched token rendering,
// handles workspace events (file/terminal/handoff),
// and provides granular event routing to all stores.
// ───────────────────────────────────────────────────────

import { useEffect, useRef, useCallback } from 'react';
import { useEngineStore } from '../stores/engine.store';
import { useAgentsStore } from '../stores/agents.store';
import { useSessionStore } from '../stores/session.store';
import { useWorkspaceStore } from '../stores/workspace.store';
import { StreamManager } from '../lib/stream-accumulator';
import type { EngineEvent } from '@dexpert/types';

export function useEngine(): void {
  const setStatus = useEngineStore((s) => s.setStatus);
  const setAgentStatus = useAgentsStore((s) => s.setAgentStatus);
  const addToolCall = useAgentsStore((s) => s.addToolCall);
  const addMessage = useSessionStore((s) => s.addMessage);
  const updateMessage = useSessionStore((s) => s.updateMessage);

  // Workspace actions
  const addFile = useWorkspaceStore((s) => s.addFile);
  const updateFile = useWorkspaceStore((s) => s.updateFile);
  const addTerminalEntry = useWorkspaceStore((s) => s.addTerminalEntry);
  const setFileTree = useWorkspaceStore((s) => s.setFileTree);
  const openPanel = useWorkspaceStore((s) => s.openPanel);

  // Track the current streaming message ID per session
  const streamingMessageRef = useRef<Record<string, string>>({});

  // Stream manager for batched token rendering
  const streamManagerRef = useRef<StreamManager | null>(null);

  // Initialize stream manager with flush handler
  const getStreamManager = useCallback(() => {
    if (!streamManagerRef.current) {
      streamManagerRef.current = new StreamManager((sessionId, batchedContent) => {
        const existingId = streamingMessageRef.current[sessionId];
        if (existingId) {
          // Append batched tokens to existing streaming message
          updateMessage(existingId, (prev) => ({ content: prev.content + batchedContent }));
        }
      });
    }
    return streamManagerRef.current;
  }, [updateMessage]);

  useEffect(() => {
    if (!window.dexpert?.engine?.onEvent) {
      // Engine API not available (running outside Electron / dev mode)
      setStatus('ready');
      return;
    }

    const sm = getStreamManager();

    const unsubscribe = window.dexpert.engine.onEvent((event: EngineEvent) => {
      switch (event.type) {
        // ── Agent Status ────────────────────────────
        case 'agent_status':
          setAgentStatus(event.agentId as any, event.status, event.action);
          break;

        // ── Tool Call ───────────────────────────────
        case 'tool_call':
          addToolCall({
            id: (event as any).callId || crypto.randomUUID(),
            name: (event as any).toolName,
            agentId: event.agentId as any,
            arguments: (event as any).args,
            timestamp: new Date().toISOString(),
          });
          // Also inject into chat as a tool_call message
          if ((event as any).sessionId) {
            addMessage({
              id: crypto.randomUUID(),
              sessionId: (event as any).sessionId,
              role: 'assistant',
              content: '',
              timestamp: new Date().toISOString(),
              agentId: event.agentId,
              metadata: {
                type: 'tool_call',
                toolName: (event as any).toolName,
                args: (event as any).args,
                callId: (event as any).callId,
                isRunning: true,
              },
            });
          }
          break;

        // ── Tool Result ─────────────────────────────
        case 'tool_result': {
          const tr = event as any;
          if (tr.sessionId) {
            addMessage({
              id: crypto.randomUUID(),
              sessionId: tr.sessionId,
              role: 'assistant',
              content: '',
              timestamp: new Date().toISOString(),
              agentId: tr.agentId,
              metadata: {
                type: 'tool_result',
                toolName: tr.toolName,
                result: tr.result,
                success: tr.success,
                callId: tr.callId,
              },
            });
          }
          break;
        }

        // ── Thinking ────────────────────────────────
        case 'thinking': {
          const tk = event as any;
          if (tk.sessionId) {
            addMessage({
              id: crypto.randomUUID(),
              sessionId: tk.sessionId,
              role: 'assistant',
              content: '',
              timestamp: new Date().toISOString(),
              agentId: tk.agentId,
              metadata: {
                type: 'thinking',
                thinking: tk.content,
              },
            });
          }
          break;
        }

        // ── Response (Streaming) ────────────────────
        case 'response': {
          const { sessionId, content, isStreaming, agentId } = event as any;

          if (isStreaming) {
            const existingId = streamingMessageRef.current[sessionId];

            if (existingId) {
              // Push token into stream manager for batched updates
              sm.push(sessionId, content);
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
                metadata: { type: 'response', isStreaming: true },
              });
            }
          } else {
            // Final (non-streaming) response — finalize stream
            sm.finalize(sessionId);
            const existingId = streamingMessageRef.current[sessionId];
            if (existingId) {
              // Update the streaming message with complete content
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
                metadata: { type: 'response', isStreaming: false },
              });
            }
          }
          break;
        }

        // ── Workspace: File Created ─────────────────
        case 'file_created': {
          const fc = event as any;
          addFile(fc.filePath, fc.content, fc.language);
          // Inject file creation card into chat
          if (fc.sessionId) {
            addMessage({
              id: crypto.randomUUID(),
              sessionId: fc.sessionId,
              role: 'assistant',
              content: '',
              timestamp: new Date().toISOString(),
              agentId: fc.agentId,
              metadata: {
                type: 'file_created',
                filePath: fc.filePath,
                language: fc.language,
                contentPreview: fc.content.slice(0, 500),
              },
            });
          }
          break;
        }

        // ── Workspace: File Modified ────────────────
        case 'file_modified': {
          const fm = event as any;
          updateFile(fm.filePath, fm.diff, fm.newContent);
          if (fm.sessionId) {
            addMessage({
              id: crypto.randomUUID(),
              sessionId: fm.sessionId,
              role: 'assistant',
              content: '',
              timestamp: new Date().toISOString(),
              agentId: fm.agentId,
              metadata: {
                type: 'file_modified',
                filePath: fm.filePath,
                diff: fm.diff,
              },
            });
          }
          break;
        }

        // ── Workspace: Terminal Output ──────────────
        case 'terminal_output': {
          const to = event as any;
          addTerminalEntry({
            command: to.command,
            output: to.output,
            exitCode: to.exitCode,
            isError: to.isError,
            agentId: to.agentId,
          });
          if (to.sessionId) {
            addMessage({
              id: crypto.randomUUID(),
              sessionId: to.sessionId,
              role: 'assistant',
              content: '',
              timestamp: new Date().toISOString(),
              agentId: to.agentId,
              metadata: {
                type: 'terminal_output',
                command: to.command,
                output: to.output,
                exitCode: to.exitCode,
                isError: to.isError,
              },
            });
          }
          break;
        }

        // ── Workspace: File Tree Update ─────────────
        case 'workspace_update': {
          const wu = event as any;
          setFileTree(wu.fileTree, wu.rootPath);
          openPanel();
          break;
        }

        // ── Agent Handoff ───────────────────────────
        case 'agent_handoff': {
          const ah = event as any;
          if (ah.sessionId) {
            addMessage({
              id: crypto.randomUUID(),
              sessionId: ah.sessionId,
              role: 'assistant',
              content: '',
              timestamp: new Date().toISOString(),
              agentId: ah.fromAgent,
              metadata: {
                type: 'agent_handoff',
                fromAgent: ah.fromAgent,
                toAgent: ah.toAgent,
                taskSummary: ah.taskSummary,
              },
            });
          }
          break;
        }

        // ── Done ────────────────────────────────────
        case 'done': {
          const de = event as any;
          // Clean up streaming state
          if (de.sessionId && streamingMessageRef.current[de.sessionId]) {
            sm.finalize(de.sessionId);
            delete streamingMessageRef.current[de.sessionId];
          }
          setStatus('ready');
          break;
        }

        // ── Error ───────────────────────────────────
        case 'error': {
          const ee = event as any;
          console.error('[Engine Event] Error:', ee.message);
          if (ee.sessionId && streamingMessageRef.current[ee.sessionId]) {
            sm.finalize(ee.sessionId);
            delete streamingMessageRef.current[ee.sessionId];
          }
          // Add error message to chat
          if (ee.sessionId) {
            addMessage({
              id: crypto.randomUUID(),
              sessionId: ee.sessionId,
              role: 'system',
              content: ee.message,
              timestamp: new Date().toISOString(),
              metadata: { type: 'error', code: ee.code },
            });
          }
          break;
        }

        // ── Pong ────────────────────────────────────
        case 'pong':
          break;

        // ── Token Usage ─────────────────────────────
        case 'token_usage':
          // Store token usage for status bar display
          break;
      }
    });

    // Mark engine as ready
    setTimeout(() => setStatus('ready'), 1000);

    return () => {
      unsubscribe();
      sm.resetAll();
    };
  }, [
    setStatus, setAgentStatus, addToolCall, addMessage, updateMessage,
    addFile, updateFile, addTerminalEntry, setFileTree, openPanel,
    getStreamManager,
  ]);
}
