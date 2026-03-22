// ── Task Types ─────────────────────────────────────────

import type { AgentId } from './agent';

export interface TaskPayload {
  taskId: string;
  sessionId: string;
  goal: string;
  context?: string;
  targetAgent?: AgentId;
  parentTaskId?: string;
}

export interface SubTask {
  id: string;
  parentTaskId: string;
  assignedAgent: AgentId;
  description: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  dependencies: string[];
  result?: string;
  error?: string;
}

export interface PlannerOutput {
  plan: SubTask[];
  reasoning: string;
  estimatedSteps: number;
}

export interface TaskResult {
  taskId: string;
  success: boolean;
  result?: string;
  error?: string;
  duration: number;
  tokenUsage?: {
    input: number;
    output: number;
    cost: number;
  };
}
