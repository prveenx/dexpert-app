# FILE: core/llm/tokenizer.py
"""
Token tracking and cost calculation.

Moved here from utils/ per archetecture.md.
Tracks token usage per-agent, per-model for cost reporting.
"""

import json
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field

log = logging.getLogger(__name__)

RUNTIME_DIR = "runtime"
TOKEN_LOG_PATH = os.path.join(RUNTIME_DIR, "logs", "token_tracker.jsonl")

# Approximate cost per 1M tokens (input/output) for common models
MODEL_COSTS: Dict[str, Dict[str, float]] = {
    "gemini-2.0-flash": {"input": 0.075, "output": 0.30},
    "gemini-2.5-flash-preview-05-20": {"input": 0.15, "output": 0.60},
    "gemini-2.5-pro-preview-05-06": {"input": 1.25, "output": 10.00},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
    "claude-3-5-haiku-20241022": {"input": 0.80, "output": 4.00},
}


@dataclass
class UsageRecord:
    """Single token usage record."""
    agent_name: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    latency_ms: float
    timestamp: str


class TokenTracker:
    """Tracks token usage and costs across the session."""

    _records: list = field(default_factory=list) if False else []
    _session_totals: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def track_request(
        cls,
        agent_name: str,
        model: str,
        response: Any,
        latency: float,
        session_id: Optional[str] = None,
    ) -> Optional[UsageRecord]:
        """Track a completed LLM request."""
        try:
            usage = getattr(response, "usage", None)
            if not usage:
                return None

            prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
            completion_tokens = getattr(usage, "completion_tokens", 0) or 0
            total_tokens = prompt_tokens + completion_tokens

            # Calculate cost
            model_key = model.split("/")[-1] if "/" in model else model
            costs = MODEL_COSTS.get(model_key, {"input": 0.0, "output": 0.0})
            cost_usd = (
                (prompt_tokens * costs["input"] / 1_000_000)
                + (completion_tokens * costs["output"] / 1_000_000)
            )

            record = UsageRecord(
                agent_name=agent_name,
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cost_usd=round(cost_usd, 6),
                latency_ms=round(latency * 1000, 1),
                timestamp=datetime.now().isoformat(),
            )

            cls._records.append(record)

            # Update session totals
            if session_id:
                if session_id not in cls._session_totals:
                    cls._session_totals[session_id] = {
                        "total_tokens": 0,
                        "total_cost": 0.0,
                        "requests": 0,
                    }
                totals = cls._session_totals[session_id]
                totals["total_tokens"] += total_tokens
                totals["total_cost"] += cost_usd
                totals["requests"] += 1

            # Append to JSONL log
            cls._append_to_log(record)

            return record

        except Exception as e:
            log.error(f"Token tracking failed: {e}")
            return None

    @classmethod
    def _append_to_log(cls, record: UsageRecord) -> None:
        """Append record to the JSONL log file."""
        try:
            os.makedirs(os.path.dirname(TOKEN_LOG_PATH), exist_ok=True)
            with open(TOKEN_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(
                    json.dumps(
                        {
                            "agent": record.agent_name,
                            "model": record.model,
                            "prompt_tokens": record.prompt_tokens,
                            "completion_tokens": record.completion_tokens,
                            "cost_usd": record.cost_usd,
                            "latency_ms": record.latency_ms,
                            "ts": record.timestamp,
                        }
                    )
                    + "\n"
                )
        except Exception as e:
            log.debug(f"Failed to write token log: {e}")

    @classmethod
    def get_session_totals(cls, session_id: str) -> Dict[str, Any]:
        return cls._session_totals.get(
            session_id, {"total_tokens": 0, "total_cost": 0.0, "requests": 0}
        )

    @classmethod
    def get_recent_records(cls, limit: int = 20) -> list:
        return cls._records[-limit:]
