// ── Session Store ──────────────────────────────────────

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
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
  togglePinSession: (id: string) => void;
  createSession: (id: string, title: string) => void;
}

export const useSessionStore = create<SessionStoreState & SessionStoreActions>()(
  persist(
    (set) => ({
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
      renameSession: (id: string, title: string) => set((state) => ({
        sessions: state.sessions.map((s) => (s.id === id ? { ...s, title } : s)),
      })),
      deleteSession: (id: string) => set((state) => ({
        sessions: state.sessions.filter((s) => s.id !== id),
        currentSessionId: state.currentSessionId === id ? null : state.currentSessionId,
        messages: state.currentSessionId === id ? [] : state.messages,
      })),
      togglePinSession: (id: string) => set((state) => ({
        sessions: state.sessions.map((s) => (s.id === id ? { ...s, pinned: !s.pinned } : s)),
      })),
      createSession: (id: string, title: string) => set((state) => ({
        sessions: [{
          id,
          title,
          userId: 'default',
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          isActive: true,
          messageCount: 1,
          pinned: false
        }, ...state.sessions],
        currentSessionId: id
      })),
    }),
    {
      name: 'dexpert-session-storage',
      storage: {
        getItem: async (name: string) => {
          const data = await (window as any).dexpert.storage.getSessions();
          return { state: data };
        },
        setItem: async (name: string, value: any) => {
          // value is already the wrapped state from zustand
          await (window as any).dexpert.storage.setSessions(value.state);
        },
        removeItem: async (name: string) => {
          // Optional: handle removal
        },
      } as any,
    }
  )
);
