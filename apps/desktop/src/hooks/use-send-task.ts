// ── useSendTask Hook ───────────────────────────────────

import { useCallback } from 'react';
import { useSessionStore } from '../stores/session.store';
import type { ClientMessage } from '@dexpert/types';

export function useSendTask() {
  const addMessage = useSessionStore((s) => s.addMessage);
  const currentSessionId = useSessionStore((s) => s.currentSessionId);

  const sendTask = useCallback(
    (content: string) => {
      const sessionId = currentSessionId || crypto.randomUUID();

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
    [addMessage, currentSessionId],
  );

  return { sendTask };
}
