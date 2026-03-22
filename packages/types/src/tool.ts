// ── Tool Types ─────────────────────────────────────────
import { AgentId } from './agent';

export interface ToolDefinition {
  name: string;
  description: string;
  inputSchema: Record<string, unknown>;
  source: 'native' | 'plugin' | 'mcp';
  sourceId?: string;
  agentRestrictions?: string[];
}

export interface ToolCall {
  id: string;
  name: string;
  agentId?: AgentId;
  arguments: Record<string, unknown>;
  timestamp: string;
}

export interface ToolResult {
  callId: string;
  success: boolean;
  output?: string;
  error?: string;
  duration: number;
}
