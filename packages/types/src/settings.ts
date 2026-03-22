// ── Settings Types ─────────────────────────────────────

import type { AgentConfig } from './agent';
import type { ModelConfig, LLMProvider } from './llm';
import type { UserPreferences } from './user';

export interface EngineSettings {
  port: number;
  host: string;
  logLevel: 'debug' | 'info' | 'warn' | 'error';
  agents: Record<string, AgentConfig>;
  defaultModel: ModelConfig;
  apiKeys: Partial<Record<LLMProvider, string>>;
}

export interface DesktopSettings extends UserPreferences {
  windowBounds?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  sidebarWidth: number;
  agentsPanelWidth: number;
  terminalHeight: number;
  terminalOpen: boolean;
}

export interface AgentModelConfig {
  agentId: string;
  model: ModelConfig;
  overrideGlobal: boolean;
}
