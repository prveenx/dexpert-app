"""
Dexpert Engine Settings — Pydantic-powered configuration.
"""

from typing import Optional
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class AgentConfig(BaseModel):
    """Configuration for a single agent."""
    enabled: bool = True
    model: str = "gemini-2.0-flash"
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

    # LLM Security
    google_ai_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    nvidia_nim_api_key: Optional[str] = None

    # Default model
    default_model: str = "gemini/gemini-2.0-flash"
    default_temperature: float = 0.7
    default_max_tokens: int = 4096

    # Agent configs
    planner: AgentConfig = AgentConfig(model="gemini-2.0-flash", temperature=0.7)
    browser: AgentConfig = AgentConfig(model="gemini-2.0-flash", temperature=0.5)
    os_agent: AgentConfig = AgentConfig(model="gemini-2.0-flash", temperature=0.3)

    # Memory & Personalization
    enable_personalization: bool = True
    memory_max_facts: int = 50

    model_config = {
        "env_prefix": "DEXPERT_",
        "env_file": ".env",
        "extra": "ignore"
    }
