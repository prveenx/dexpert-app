// ── Agent Types ────────────────────────────────────────

export type AgentId = 'planner' | 'browser' | 'os';

export type AgentStatus = 'idle' | 'running' | 'error' | 'disabled';

export interface AgentState {
  id: AgentId;
  status: AgentStatus;
  currentAction?: string;
  lastError?: string;
  taskCount: number;
}

export interface AgentConfig {
  id: AgentId;
  enabled: boolean;
  model: string;
  temperature: number;
  maxTokens: number;
  timeout: number;
  maxRetries: number;
}
