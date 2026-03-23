// ── Agents Store ───────────────────────────────────────

import { create } from 'zustand';
import type { AgentId, AgentStatus, ToolCall } from '@dexpert/types';

interface AgentStoreState {
  agentStatuses: Record<AgentId, AgentStatus>;
  toolCallLog: ToolCall[];
  currentTasks: Record<AgentId, string | null>;
}

interface AgentStoreActions {
  setAgentStatus: (agentId: AgentId, status: AgentStatus, task?: string | null) => void;
  addToolCall: (toolCall: ToolCall) => void;
  setCurrentTask: (agentId: AgentId, task: string | null) => void;
}

export const useAgentsStore = create<AgentStoreState & AgentStoreActions>((set) => ({
  agentStatuses: {
    planner: 'idle',
    browser: 'idle',
    os: 'idle',
  },
  toolCallLog: [],
  currentTasks: {
    planner: null,
    browser: null,
    os: null,
  },

  setAgentStatus: (agentId, status, task = null) => set((state) => ({
    agentStatuses: { ...state.agentStatuses, [agentId]: status },
    currentTasks: { ...state.currentTasks, [agentId]: task || state.currentTasks[agentId] },
  })),
  addToolCall: (toolCall) => set((state) => ({
    toolCallLog: [...state.toolCallLog, toolCall],
  })),
  setCurrentTask: (agentId, task) => set((state) => ({
    currentTasks: { ...state.currentTasks, [agentId]: task },
  })),
}));
