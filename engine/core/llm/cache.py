# FILE: core/llm/cache.py
"""
Native Prompt Caching Manager.

Manages LiteLLM's automatic caching for supported providers:
  - Google Gemini: Context Caching API
  - Anthropic: Prompt Caching headers
  - OpenAI: No native caching (uses local dedup)

For Phase 2 — currently a pass-through skeleton.
"""

import logging
from typing import Optional, Dict, Any

log = logging.getLogger(__name__)


class PromptCache:
    """Prompt caching manager for LLM providers."""

    def __init__(self):
        self._cache_hits = 0
        self._cache_misses = 0

    def should_cache(self, model: str) -> bool:
        """Determine if caching is supported for this model."""
        cacheable_prefixes = ["gemini/", "anthropic/", "claude-"]
        return any(model.startswith(p) for p in cacheable_prefixes)

    def get_cache_params(self, model: str) -> Dict[str, Any]:
        """Get cache-specific parameters for the LLM call."""
        if not self.should_cache(model):
            return {}

        return {
            "caching": True,
            "cache_control": {"type": "ephemeral"},
        }

    @property
    def stats(self) -> Dict[str, int]:
        return {
            "hits": self._cache_hits,
            "misses": self._cache_misses,
        }
