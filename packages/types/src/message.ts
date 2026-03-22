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
  agentId: AgentId;
  content: string;
}

export interface ToolCallEvent {
  type: 'tool_call';
  sessionId: string;
  agentId: AgentId;
  toolCall: ToolCall;
}

export interface ToolResultEvent {
  type: 'tool_result';
  sessionId: string;
  agentId: AgentId;
  result: ToolResult;
}

export interface ResponseEvent {
  type: 'response';
  sessionId: string;
  agentId: AgentId;
  content: string;
  isStreaming: boolean;
}

export interface AgentStatusEvent {
  type: 'agent_status';
  agentId: AgentId;
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
  agentId: AgentId;
  provider: string;
  inputTokens: number;
  outputTokens: number;
  cost: number;
}

export interface ScreenshotEvent {
  type: 'screenshot';
  sessionId: string;
  data: string; // base64 JPEG
  width: number;
  height: number;
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
  | ScreenshotEvent;
