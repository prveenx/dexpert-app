import { useSessionStore } from '../stores/session.store';
import { useCallback } from 'react';

export function useSession() {
  const { 
    sessions, 
    currentSessionId, 
    messages, 
    setSessions, 
    setActive, 
    addMessage, 
    updateMessage, 
    clearMessages, 
    renameSession, 
    deleteSession, 
    togglePinSession, 
    createSession 
  } = useSessionStore();

  const createNewSession = useCallback((title: string = 'New Session') => {
    const id = crypto.randomUUID();
    createSession(id, title);
    return id;
  }, [createSession]);

  const selectSession = useCallback((id: string) => {
    setActive(id);
    // In a real app, you might want to fetch messages for this session
    // For now, we rely on the state persisted or managed elsewhere
  }, [setActive]);

  return {
    sessions,
    currentSessionId,
    messages,
    createSession: createNewSession,
    selectSession,
    renameSession,
    deleteSession,
    togglePinSession,
    addMessage,
    updateMessage,
    clearMessages,
    setSessions,
  };
}
