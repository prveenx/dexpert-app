// ── Session Types ──────────────────────────────────────

export interface Session {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  isActive: boolean;
  messageCount: number;
  lastMessage?: string;
}

export interface SessionMeta {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  tags?: string[];
}

export interface Checkpoint {
  sessionId: string;
  timestamp: string;
  state: Record<string, unknown>;
  completedTasks: string[];
  pendingTasks: string[];
}

export interface ConversationTurn {
  id: string;
  sessionId: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  agentId?: string;
  metadata?: Record<string, unknown>;
}
