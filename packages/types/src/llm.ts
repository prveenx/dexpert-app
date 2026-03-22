// ── LLM Types ──────────────────────────────────────────

export type LLMProvider =
  | 'google'
  | 'groq'
  | 'anthropic'
  | 'openai'
  | 'nvidia';

export interface ModelConfig {
  provider: LLMProvider;
  model: string;
  temperature: number;
  maxTokens: number;
  topP?: number;
  frequencyPenalty?: number;
  presencePenalty?: number;
}

export interface TokenUsage {
  inputTokens: number;
  outputTokens: number;
  totalTokens: number;
}

export interface CostRecord {
  provider: LLMProvider;
  model: string;
  tokenUsage: TokenUsage;
  cost: number;
  timestamp: string;
}
