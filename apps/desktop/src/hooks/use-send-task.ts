// FILE: apps/desktop/src/hooks/use-send-task.ts
import { useCallback } from 'react';
import { useSessionStore } from '../stores/session.store';
import type { ClientMessage } from '@dexpert/types';

export function useSendTask() {
  const addMessage = useSessionStore((s) => s.addMessage);
  const currentSessionId = useSessionStore((s) => s.currentSessionId);
  const createSession = useSessionStore((s) => s.createSession);

  const sendTask = useCallback(
    (content: string, options?: any) => {
      let sessionId = currentSessionId;
      
      // If no active session, create a new one
      if (!sessionId) {
        sessionId = crypto.randomUUID();
        const title = content.length > 30 ? content.substring(0, 30) + '...' : content;
        createSession(sessionId, title);
      }

      // Optimistic user message
      addMessage({
        id: crypto.randomUUID(),
        sessionId,
        role: 'user',
        content,
        timestamp: new Date().toISOString(),
      });

      // Send to engine, passing down the chosen model to the backend
      const msg: any = {
        type: 'chat',
        sessionId,
        content,
        model: options?.model, // Plumb the UI model to the backend
      };

      if (window.dexpert?.engine?.send) {
        window.dexpert.engine.send(msg);
      }
    },
    [addMessage, currentSessionId, createSession],
  );

  return { sendTask };
}