// ── useSendTask Hook ───────────────────────────────────

import { useCallback } from 'react';
import { useSessionStore } from '../stores/session.store';
import type { ClientMessage } from '@dexpert/types';

export function useSendTask() {
  const addMessage = useSessionStore((s) => s.addMessage);
  const currentSessionId = useSessionStore((s) => s.currentSessionId);
  const createSession = useSessionStore((s) => s.createSession);

  const sendTask = useCallback(
    (content: string) => {
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

      // Send to engine
      const msg: ClientMessage = {
        type: 'chat',
        sessionId,
        content,
      };

      if (window.dexpert?.engine?.send) {
        window.dexpert.engine.send(msg);
      }
    },
    [addMessage, currentSessionId, createSession],
  );

  return { sendTask };
}
