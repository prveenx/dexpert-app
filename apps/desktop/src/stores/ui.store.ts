// ── UI Store ───────────────────────────────────────────

import { create } from 'zustand';

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

export const useUIStore = create<UIStoreState & UIStoreActions>((set) => ({
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
}));
