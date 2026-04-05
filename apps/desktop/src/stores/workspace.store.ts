// ── Workspace Store ────────────────────────────────────
// Manages the dynamic workspace panel state, files created
// by agents, editor tabs, and file tree.
// ───────────────────────────────────────────────────────

import { create } from 'zustand';

// ── Types ────────────────────────────────────────────

export interface WorkspaceFile {
  path: string;
  name: string;
  content: string;
  language: string;
  status: 'new' | 'modified' | 'deleted' | 'unchanged';
  diff?: string;
  originalContent?: string;
  lastModified: number;
}

export interface FileTreeNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  language?: string;
  status?: 'new' | 'modified' | 'deleted' | 'unchanged';
  children?: FileTreeNode[];
  isExpanded?: boolean;
}

export interface TerminalEntry {
  id: string;
  command: string;
  output: string;
  exitCode?: number;
  isError: boolean;
  timestamp: number;
  agentId: string;
}

// ── Store ────────────────────────────────────────────

interface WorkspaceStoreState {
  isOpen: boolean;
  panelWidth: number;
  activeTab: 'files' | 'preview' | 'terminal';
  files: Record<string, WorkspaceFile>;
  fileTree: FileTreeNode[];
  openEditorTabs: string[];
  activeEditorTab: string | null;
  editorViewMode: 'code' | 'diff' | 'preview';
  terminalHistory: TerminalEntry[];
  rootPath: string | null;
  previewUrl: string | null;
}

interface WorkspaceStoreActions {
  // Panel
  openPanel: () => void;
  closePanel: () => void;
  togglePanel: () => void;
  setPanelWidth: (width: number) => void;
  setActiveTab: (tab: 'files' | 'preview' | 'terminal') => void;

  // Files
  addFile: (path: string, content: string, language: string) => void;
  updateFile: (path: string, diff: string, newContent: string) => void;
  removeFile: (path: string) => void;
  setFileTree: (tree: FileTreeNode[], rootPath: string) => void;
  toggleTreeNode: (path: string) => void;

  // Editor
  openEditorTab: (path: string) => void;
  closeEditorTab: (path: string) => void;
  setActiveEditor: (path: string) => void;
  setEditorViewMode: (mode: 'code' | 'diff' | 'preview') => void;

  // Terminal
  addTerminalEntry: (entry: Omit<TerminalEntry, 'id' | 'timestamp'>) => void;
  clearTerminal: () => void;

  // Preview
  setPreviewUrl: (url: string | null) => void;

  // Reset
  resetWorkspace: () => void;
}

// ── Helpers ──────────────────────────────────────────

function inferLanguage(filepath: string): string {
  const ext = filepath.split('.').pop()?.toLowerCase() || '';
  const langMap: Record<string, string> = {
    ts: 'typescript', tsx: 'typescript', js: 'javascript', jsx: 'javascript',
    py: 'python', rs: 'rust', go: 'go', rb: 'ruby', java: 'java',
    cpp: 'cpp', c: 'c', h: 'c', hpp: 'cpp', cs: 'csharp',
    html: 'html', css: 'css', scss: 'scss', less: 'less',
    json: 'json', yaml: 'yaml', yml: 'yaml', toml: 'toml',
    md: 'markdown', mdx: 'markdown', txt: 'text',
    sh: 'bash', bash: 'bash', zsh: 'bash', fish: 'fish',
    sql: 'sql', graphql: 'graphql', xml: 'xml', svg: 'xml',
    dockerfile: 'dockerfile', makefile: 'makefile',
    kt: 'kotlin', swift: 'swift', dart: 'dart', lua: 'lua',
    r: 'r', php: 'php', pl: 'perl', ex: 'elixir', erl: 'erlang',
    zig: 'zig', nim: 'nim', v: 'v', wasm: 'wasm',
  };
  return langMap[ext] || 'text';
}

function buildFileTree(files: Record<string, WorkspaceFile>): FileTreeNode[] {
  const root: Record<string, FileTreeNode> = {};

  Object.values(files).forEach(file => {
    const parts = file.path.replace(/\\/g, '/').split('/');
    let current = root;

    parts.forEach((part, idx) => {
      const isFile = idx === parts.length - 1;
      const currentPath = parts.slice(0, idx + 1).join('/');

      if (!current[part]) {
        current[part] = {
          name: part,
          path: currentPath,
          type: isFile ? 'file' : 'directory',
          language: isFile ? file.language : undefined,
          status: isFile ? file.status : undefined,
          children: isFile ? undefined : [],
          isExpanded: true,
        };
      }

      if (!isFile) {
        if (!current[part].children) current[part].children = [];
        const childMap: Record<string, FileTreeNode> = {};
        current[part].children!.forEach(c => { childMap[c.name] = c; });
        current = childMap;
      }
    });
  });

  return Object.values(root);
}

function getFileName(path: string): string {
  return path.replace(/\\/g, '/').split('/').pop() || path;
}

// ── Store Implementation ─────────────────────────────

const initialState: WorkspaceStoreState = {
  isOpen: false,
  panelWidth: 50,
  activeTab: 'files',
  files: {},
  fileTree: [],
  openEditorTabs: [],
  activeEditorTab: null,
  editorViewMode: 'code',
  terminalHistory: [],
  rootPath: null,
  previewUrl: null,
};

export const useWorkspaceStore = create<WorkspaceStoreState & WorkspaceStoreActions>((set, get) => ({
  ...initialState,

  // ── Panel Actions ────────────────────────────────
  openPanel: () => set({ isOpen: true }),
  closePanel: () => set({ isOpen: false }),
  togglePanel: () => set(s => ({ isOpen: !s.isOpen })),
  setPanelWidth: (width) => set({ panelWidth: Math.max(30, Math.min(70, width)) }),
  setActiveTab: (tab) => set({ activeTab: tab }),

  // ── File Actions ─────────────────────────────────
  addFile: (path, content, language) => {
    set(state => {
      const lang = language || inferLanguage(path);
      const newFiles = {
        ...state.files,
        [path]: {
          path,
          name: getFileName(path),
          content,
          language: lang,
          status: 'new' as const,
          lastModified: Date.now(),
        },
      };
      
      const newTabs = state.openEditorTabs.includes(path)
        ? state.openEditorTabs
        : [...state.openEditorTabs, path];

      return {
        files: newFiles,
        fileTree: buildFileTree(newFiles),
        openEditorTabs: newTabs,
        activeEditorTab: path,
        isOpen: true,
        activeTab: 'files',
      };
    });
  },

  updateFile: (path, diff, newContent) => {
    set(state => {
      const existing = state.files[path];
      const newFiles = {
        ...state.files,
        [path]: {
          ...(existing || {
            path,
            name: getFileName(path),
            language: inferLanguage(path),
            lastModified: Date.now(),
          }),
          content: newContent || existing?.content || '',
          originalContent: existing?.content,
          diff,
          status: 'modified' as const,
          lastModified: Date.now(),
        },
      };

      const newTabs = state.openEditorTabs.includes(path)
        ? state.openEditorTabs
        : [...state.openEditorTabs, path];

      return {
        files: newFiles,
        fileTree: buildFileTree(newFiles),
        openEditorTabs: newTabs,
        activeEditorTab: path,
        editorViewMode: 'diff',
      };
    });
  },

  removeFile: (path) => {
    set(state => {
      const { [path]: _, ...remaining } = state.files;
      const newTabs = state.openEditorTabs.filter(t => t !== path);
      return {
        files: remaining,
        fileTree: buildFileTree(remaining),
        openEditorTabs: newTabs,
        activeEditorTab: newTabs.length > 0 ? newTabs[newTabs.length - 1] : null,
      };
    });
  },

  setFileTree: (tree, rootPath) => set({ fileTree: tree, rootPath }),

  toggleTreeNode: (path) => {
    set(state => {
      const toggle = (nodes: FileTreeNode[]): FileTreeNode[] =>
        nodes.map(n => {
          if (n.path === path) return { ...n, isExpanded: !n.isExpanded };
          if (n.children) return { ...n, children: toggle(n.children) };
          return n;
        });
      return { fileTree: toggle(state.fileTree) };
    });
  },

  // ── Editor Actions ───────────────────────────────
  openEditorTab: (path) => {
    set(state => ({
      openEditorTabs: state.openEditorTabs.includes(path)
        ? state.openEditorTabs
        : [...state.openEditorTabs, path],
      activeEditorTab: path,
    }));
  },

  closeEditorTab: (path) => {
    set(state => {
      const newTabs = state.openEditorTabs.filter(t => t !== path);
      const wasActive = state.activeEditorTab === path;
      return {
        openEditorTabs: newTabs,
        activeEditorTab: wasActive
          ? (newTabs.length > 0 ? newTabs[newTabs.length - 1] : null)
          : state.activeEditorTab,
      };
    });
  },

  setActiveEditor: (path) => set({ activeEditorTab: path }),
  setEditorViewMode: (mode) => set({ editorViewMode: mode }),

  // ── Terminal Actions ─────────────────────────────
  addTerminalEntry: (entry) => {
    set(state => ({
      terminalHistory: [
        ...state.terminalHistory,
        {
          ...entry,
          id: crypto.randomUUID(),
          timestamp: Date.now(),
        },
      ],
    }));
  },

  clearTerminal: () => set({ terminalHistory: [] }),

  // ── Preview ──────────────────────────────────────
  setPreviewUrl: (url) => set({ previewUrl: url }),

  // ── Reset ────────────────────────────────────────
  resetWorkspace: () => set(initialState),
}));
