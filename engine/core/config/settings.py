"""
Dexpert Engine Settings — Pydantic-powered configuration.

Provides:
  - DexpertSettings: Global engine configuration
  - AgentConfig: Per-agent model/execution settings
  - resolve_model() / resolve_vision_model(): Model resolution helpers
"""

import os
from typing import Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class AgentConfig(BaseModel):
    """Configuration for a single agent."""
    enabled: bool = True
    model: str = "gemini/gemini-2.0-flash"
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 120
    max_retries: int = 3


class DexpertSettings(BaseSettings):
    """Engine-wide settings."""

    # Server
    engine_port: int = 48765
    engine_host: str = "127.0.0.1"
    log_level: str = "info"

    # Storage
    runtime_dir: str = "runtime"
    db_path: str = "runtime/memory.db"
    log_dir: str = "runtime/logs"
    session_dir: str = "runtime/sessions"

    # LLM API Keys
    google_ai_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    nvidia_nim_api_key: Optional[str] = None

    # Default model
    default_model: str = "gemini/gemini-2.0-flash"
    default_temperature: float = 0.7
    default_max_tokens: int = 4096

    # Global model override (if set, all agents use this)
    global_model_override: Optional[str] = None

    # Agent configs
    planner: AgentConfig = AgentConfig(model="gemini/gemini-2.0-flash", temperature=0.7)
    browser: AgentConfig = AgentConfig(model="gemini/gemini-2.0-flash", temperature=0.5)
    os_agent: AgentConfig = AgentConfig(model="gemini/gemini-2.0-flash", temperature=0.3)

    # Memory & Personalization
    enable_personalization: bool = True
    # Auth
    auth_secret: str = Field(default="supersecretbetterauthsecret", validation_alias="BETTER_AUTH_SECRET")

    model_config = {
        "env_prefix": "DEXPERT_",
        "env_file": ".env",
        "extra": "ignore"
    }


# ── Global singleton ──────────────────────────────────────

_settings: Optional[DexpertSettings] = None


def get_settings() -> DexpertSettings:
    """Get or create the global settings singleton."""
    global _settings
    if _settings is None:
        _settings = DexpertSettings()
    assert _settings is not None
    return _settings


def reload_settings() -> DexpertSettings:
    """Force reload settings from environment."""
    global _settings
    _settings = DexpertSettings()
    return _settings


# ── Model Resolution Helpers ──────────────────────────────

def resolve_model(local_model: str) -> str:
    """
    Resolve which model to use, respecting global override.
    
    Priority:
      1. Global override (DexpertSettings.global_model_override)
      2. Agent's local model setting
    """
    settings = get_settings()
    if settings.global_model_override:
        return str(settings.global_model_override)
    
    # Ensure the model string has a provider prefix for LiteLLM
    if "/" not in local_model:
        # Default to gemini provider if no prefix
        return f"gemini/{local_model}"
    return local_model


def resolve_vision_model(
    local_main_model: str,
    local_vision_model: Optional[str] = None,
) -> str:
    """
    Resolve which vision model to use.

    Falls back to main model if no dedicated vision model is set.
    """
    if local_vision_model and local_vision_model.strip():
        return resolve_model(local_vision_model)
    return resolve_model(local_main_model)
