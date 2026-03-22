// ── Session Store ──────────────────────────────────────

import { create } from 'zustand';
import type { Session, ConversationTurn } from '@dexpert/types';

interface SessionStoreState {
  sessions: Session[];
  currentSessionId: string | null;
  messages: ConversationTurn[];
}

interface SessionStoreActions {
  setSessions: (sessions: Session[]) => void;
  setActive: (sessionId: string) => void;
  addMessage: (message: ConversationTurn) => void;
  updateMessage: (id: string, content: string | ((prev: string) => string)) => void;
  clearMessages: () => void;
  renameSession: (id: string, title: string) => void;
  deleteSession: (id: string) => void;
}

export const useSessionStore = create<SessionStoreState & SessionStoreActions>((set) => ({
  sessions: [],
  currentSessionId: null,
  messages: [],

  setSessions: (sessions) => set({ sessions }),
  setActive: (sessionId) => set({ currentSessionId: sessionId }),
  addMessage: (message) => set((state) => ({
    messages: [...state.messages, message],
  })),
  updateMessage: (id, content) => set((state) => ({
    messages: state.messages.map((m) => {
      if (m.id !== id) return m;
      const newContent = typeof content === 'function' ? content(m.content) : content;
      return { ...m, content: newContent };
    }),
  })),
  clearMessages: () => set({ messages: [] }),
  renameSession: (id, title) => set((state) => ({
    sessions: state.sessions.map((s) => (s.id === id ? { ...s, title } : s)),
  })),
  deleteSession: (id) => set((state) => ({
    sessions: state.sessions.filter((s) => s.id !== id),
    currentSessionId: state.currentSessionId === id ? null : state.currentSessionId,
    messages: state.currentSessionId === id ? [] : state.messages,
  })),
}));
