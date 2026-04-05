// ── WebSocket Protocol Messages ────────────────────────

import type { TaskPayload } from './task';
import type { AgentId, AgentStatus } from './agent';
import type { ToolCall, ToolResult } from './tool';

// ── Client → Engine ───────────────────────────────────

export interface TaskMsg {
  type: 'task';
  payload: TaskPayload;
}

export interface ChatMsg {
  type: 'chat';
  sessionId: string;
  content: string;
  targetAgent?: AgentId;
}

export interface CancelMsg {
  type: 'cancel';
  taskId: string;
}

export interface PingMsg {
  type: 'ping';
  timestamp: number;
}

export type ClientMessage = TaskMsg | ChatMsg | CancelMsg | PingMsg;

// ── Engine → Client ───────────────────────────────────

export interface ThinkingEvent {
  type: 'thinking';
  sessionId: string;
  agentId: string;
  content: string;
}

export interface ToolCallEvent {
  type: 'tool_call';
  sessionId: string;
  agentId: string;
  toolName: string;
  args: Record<string, unknown>;
  callId?: string;
}

export interface ToolResultEvent {
  type: 'tool_result';
  sessionId: string;
  agentId: string;
  toolName: string;
  result: string;
  success: boolean;
  callId?: string;
}

export interface ResponseEvent {
  type: 'response';
  sessionId: string;
  agentId: string;
  content: string;
  isStreaming: boolean;
}

export interface AgentStatusEvent {
  type: 'agent_status';
  agentId: string;
  status: AgentStatus;
  action?: string;
}

export interface DoneEvent {
  type: 'done';
  sessionId: string;
  taskId?: string;
  success: boolean;
}

export interface ErrorEvent {
  type: 'error';
  sessionId?: string;
  code: string;
  message: string;
}

export interface PongEvent {
  type: 'pong';
  timestamp: number;
}

export interface TokenUsageEvent {
  type: 'token_usage';
  sessionId: string;
  agentId: string;
  provider: string;
  inputTokens: number;
  outputTokens: number;
  cost: number;
}

export interface ScreenshotEvent {
  type: 'screenshot';
  sessionId: string;
  data: string;
  width: number;
  height: number;
}

// ── Workspace Events (New — v2) ──────────────────────

export interface FileCreatedEvent {
  type: 'file_created';
  sessionId: string;
  agentId: string;
  filePath: string;
  content: string;
  language: string;
}

export interface FileModifiedEvent {
  type: 'file_modified';
  sessionId: string;
  agentId: string;
  filePath: string;
  diff: string;
  newContent: string;
}

export interface TerminalOutputEvent {
  type: 'terminal_output';
  sessionId: string;
  agentId: string;
  command: string;
  output: string;
  exitCode?: number;
  isError: boolean;
}

export interface WorkspaceUpdateEvent {
  type: 'workspace_update';
  sessionId: string;
  agentId: string;
  rootPath: string;
  fileTree: WorkspaceFileNode[];
}

export interface WorkspaceFileNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  language?: string;
  status?: 'new' | 'modified' | 'deleted';
  children?: WorkspaceFileNode[];
}

export interface AgentHandoffEvent {
  type: 'agent_handoff';
  sessionId: string;
  fromAgent: string;
  toAgent: string;
  taskSummary: string;
}

export type EngineEvent =
  | ThinkingEvent
  | ToolCallEvent
  | ToolResultEvent
  | ResponseEvent
  | AgentStatusEvent
  | DoneEvent
  | ErrorEvent
  | PongEvent
  | TokenUsageEvent
  | ScreenshotEvent
  | FileCreatedEvent
  | FileModifiedEvent
  | TerminalOutputEvent
  | WorkspaceUpdateEvent
  | AgentHandoffEvent;
