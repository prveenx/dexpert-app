// ── Error Types ────────────────────────────────────────

export enum ErrorCode {
  // General
  UNKNOWN = 'UNKNOWN',
  INTERNAL = 'INTERNAL',
  VALIDATION = 'VALIDATION',
  NOT_FOUND = 'NOT_FOUND',
  UNAUTHORIZED = 'UNAUTHORIZED',

  // Engine
  ENGINE_NOT_READY = 'ENGINE_NOT_READY',
  ENGINE_TIMEOUT = 'ENGINE_TIMEOUT',
  ENGINE_CRASHED = 'ENGINE_CRASHED',

  // Agent
  AGENT_DISABLED = 'AGENT_DISABLED',
  AGENT_TIMEOUT = 'AGENT_TIMEOUT',
  AGENT_ERROR = 'AGENT_ERROR',

  // Task
  TASK_CANCELLED = 'TASK_CANCELLED',
  TASK_FAILED = 'TASK_FAILED',

  // LLM
  LLM_API_ERROR = 'LLM_API_ERROR',
  LLM_RATE_LIMIT = 'LLM_RATE_LIMIT',
  LLM_CONTEXT_OVERFLOW = 'LLM_CONTEXT_OVERFLOW',

  // Tool
  TOOL_NOT_FOUND = 'TOOL_NOT_FOUND',
  TOOL_EXECUTION_ERROR = 'TOOL_EXECUTION_ERROR',

  // Auth
  AUTH_EXPIRED = 'AUTH_EXPIRED',
  AUTH_INVALID = 'AUTH_INVALID',

  // MCP / Extensions
  MCP_CONNECTION_FAILED = 'MCP_CONNECTION_FAILED',
  MCP_SERVER_ERROR = 'MCP_SERVER_ERROR',
  PLUGIN_LOAD_ERROR = 'PLUGIN_LOAD_ERROR',
  PLUGIN_EXECUTION_ERROR = 'PLUGIN_EXECUTION_ERROR',
}

export interface DexpertError {
  code: ErrorCode;
  message: string;
  details?: Record<string, unknown>;
  timestamp: string;
}

export interface ErrorPayload {
  error: DexpertError;
  recoverable: boolean;
  suggestion?: string;
}
