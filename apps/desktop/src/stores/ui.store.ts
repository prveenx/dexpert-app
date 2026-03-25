// ── UI Store ───────────────────────────────────────────

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface UIStoreState {
  sidebarWidth: number;
  agentsPanelWidth: number;
  terminalHeight: number;
  terminalOpen: boolean;
  settingsOpen: boolean;
  settingsSection: string | null;
  theme: 'light' | 'dark' | 'system';
  commandPaletteOpen: boolean;
}

interface UIStoreActions {
  setSidebarWidth: (width: number) => void;
  setAgentsPanelWidth: (width: number) => void;
  setTerminalHeight: (height: number) => void;
  setTerminalOpen: (open: boolean) => void;
  toggleTerminal: () => void;
  setSettingsOpen: (open: boolean) => void;
  setSettingsSection: (section: string | null) => void;
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
  setCommandPaletteOpen: (open: boolean) => void;
  toggleCommandPalette: () => void;
}

export const useUIStore = create<UIStoreState & UIStoreActions>()(
  persist(
    (set) => ({
      sidebarWidth: 260,
      agentsPanelWidth: 320,
      terminalHeight: 200,
      terminalOpen: false,
      settingsOpen: false,
      settingsSection: null,
      theme: 'dark',
      commandPaletteOpen: false,

      setSidebarWidth: (width) => set({ sidebarWidth: width }),
      setAgentsPanelWidth: (width) => set({ agentsPanelWidth: width }),
      setTerminalHeight: (height) => set({ terminalHeight: height }),
      setTerminalOpen: (open) => set({ terminalOpen: open }),
      toggleTerminal: () => set((s) => ({ terminalOpen: !s.terminalOpen })),
      setSettingsOpen: (open) => set({ settingsOpen: open }),
      setSettingsSection: (section) => set({ settingsSection: section }),
      setTheme: (theme) => set({ theme }),
      setCommandPaletteOpen: (open) => set({ commandPaletteOpen: open }),
      toggleCommandPalette: () => set((s) => ({ commandPaletteOpen: !s.commandPaletteOpen })),
    }),
    {
      name: 'dexpert-ui-storage',
      storage: {
        getItem: async (name: string) => {
          // Note: We currently share sessions with a single vault file for simplicity.
          // In a "No Compromises" future, we might split files.
          const data = await (window as any).dexpert.storage.getSessions();
          return { state: data?.ui || {} };
        },
        setItem: async (name: string, value: any) => {
          const sessionsData = await (window as any).dexpert.storage.getSessions();
          await (window as any).dexpert.storage.setSessions({
            ...sessionsData,
            ui: value.state,
          });
        },
      } as any,
    }
  )
);
