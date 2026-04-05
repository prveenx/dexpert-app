# FILE: engine/core/config/settings.py
import os
import platform
import json
import logging
from typing import Optional
from pathlib import Path
from pydantic import BaseModel, Field, AliasChoices
from pydantic_settings import BaseSettings

log = logging.getLogger(__name__)

def get_appdata_dir() -> str:
    system = platform.system()
    if system == "Windows":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(base, "Dexpert")
    elif system == "Darwin":
        return os.path.expanduser("~/Library/Application Support/Dexpert")
    else:
        return os.path.expanduser("~/.config/dexpert")

APP_DIR = get_appdata_dir()

class AgentConfig(BaseModel):
    """Configuration for a single agent."""
    enabled: bool = True
    model: str = "gemini/gemini-3.1-flash-lite-preview"
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
    runtime_dir: str = APP_DIR
    db_path: str = os.path.join(APP_DIR, "memory.db")
    log_dir: str = os.path.join(APP_DIR, "logs")
    session_dir: str = os.path.join(APP_DIR, "sessions")

    # LLM API Keys
    google_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    nvidia_nim_api_key: Optional[str] = None

    # Default model
    default_model: str = "gemini/gemini-3.1-flash-lite-preview"
    default_temperature: float = 0.7
    default_max_tokens: int = 4096

    # Global model override (if set, all agents use this)
    global_model_override: Optional[str] = None

    # Agent configs
    planner: AgentConfig = AgentConfig(model="gemini/gemini-3.1-flash-lite-preview", temperature=0.7)
    browser: AgentConfig = AgentConfig(model="gemini/gemini-3.1-flash-lite-preview", temperature=0.5)
    os_agent: AgentConfig = AgentConfig(model="gemini/gemini-3.1-flash-lite-preview", temperature=0.3)

    # Memory & Personalization
    enable_personalization: bool = True
    # Auth
    better_auth_secret: str = "supersecretbetterauthsecret"

    model_config = {
        "env_prefix": "DEXPERT_",
        "env_file": [
            ".env",
            os.path.join(os.path.dirname(__file__), "../../../.env")
        ],
        "extra": "ignore"
    }

    def save_user_config(self):
        """Persist user-mutable settings to disk so they survive restarts."""
        os.makedirs(self.runtime_dir, exist_ok=True)
        config_path = os.path.join(self.runtime_dir, "user_config.json")
        try:
            data = {
                "google_api_key": self.google_api_key,
                "openai_api_key": self.openai_api_key,
                "anthropic_api_key": self.anthropic_api_key,
                "groq_api_key": self.groq_api_key,
                "default_model": self.default_model,
                "global_model_override": self.global_model_override,
                "log_level": self.log_level,
                "enable_personalization": self.enable_personalization,
            }
            with open(config_path, "w") as f:
                json.dump(data, f, indent=2)
            log.info("User configuration saved successfully.")
        except Exception as e:
            log.error(f"Failed to save user config: {e}")

    def apply_user_config(self):
        """Load user-mutable settings from disk."""
        config_path = os.path.join(self.runtime_dir, "user_config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    data = json.load(f)
                if data.get("google_api_key"): self.google_api_key = data["google_api_key"]
                if data.get("openai_api_key"): self.openai_api_key = data["openai_api_key"]
                if data.get("anthropic_api_key"): self.anthropic_api_key = data["anthropic_api_key"]
                if data.get("groq_api_key"): self.groq_api_key = data["groq_api_key"]
                if data.get("default_model"): self.default_model = data["default_model"]
                if data.get("global_model_override"): self.global_model_override = data["global_model_override"]
                if data.get("log_level"): self.log_level = data["log_level"]
                if "enable_personalization" in data: self.enable_personalization = data["enable_personalization"]
            except Exception as e:
                log.error(f"Failed to apply user config: {e}")


# ── Global singleton ──────────────────────────────────────

_settings: Optional[DexpertSettings] = None

def get_settings() -> DexpertSettings:
    """Get or create the global settings singleton."""
    global _settings
    if _settings is None:
        _settings = DexpertSettings()
        _settings.apply_user_config()
    assert _settings is not None
    return _settings

def reload_settings() -> DexpertSettings:
    """Force reload settings from environment and disk."""
    global _settings
    _settings = DexpertSettings()
    _settings.apply_user_config()
    return _settings

# ── Model Resolution Helpers ──────────────────────────────

def resolve_model(local_model: str) -> str:
    """
    Resolve which model to use, respecting global override and mapping aliases.
    """
    settings = get_settings()
    
    # Priority 1: Global override
    if settings.global_model_override:
        model = str(settings.global_model_override)
    else:
        model = local_model

    # Mapping common aliases to LiteLLM format
    model = model.lower()
    
    # ── Google Gemini ─────────────────────────────────────
    if "gemini-1.5-pro" in model: return "gemini/gemini-1.5-pro-latest"
    if "gemini-2.0-flash" in model: return "gemini/gemini-2.0-flash-exp"
    if "gemini-1.5-flash-8b" in model: return "gemini/gemini-1.5-flash-8b-latest"
    if "gemini-1.5-flash" in model: return "gemini/gemini-1.5-flash-latest"

    # ── OpenAI GPT ────────────────────────────────────────
    if "gpt-4o-mini" in model: return "openai/gpt-4o-mini"
    if "gpt-4o" in model: return "openai/gpt-4o"
    if "o1" in model: return "openai/o1-preview"

    # ── Anthropic Claude ──────────────────────────────────
    if "claude-3-5-sonnet" in model: return "anthropic/claude-3-5-sonnet-20241022"
    if "claude-3-5-haiku" in model: return "anthropic/claude-3-5-haiku-20241022"
    if "claude-3-opus" in model: return "anthropic/claude-3-opus-20240229"

    # ── Fallback ──────────────────────────────────────────
    if "/" not in model:
        if "gpt" in model: return f"openai/{model}"
        if "claude" in model: return f"anthropic/{model}"
        return f"gemini/{model}"
        
    return model

def resolve_vision_model(
    local_main_model: str,
    local_vision_model: Optional[str] = None,
) -> str:
    if local_vision_model and local_vision_model.strip():
        return resolve_model(local_vision_model)
    return resolve_model(local_main_model)