# FILE: agents/planner/config/config.py
"""
Planner agent configuration — Pydantic models and YAML loader.
"""

import yaml
import logging
from pathlib import Path
from pydantic import BaseModel, ValidationError

log = logging.getLogger(__name__)


class ModelConfig(BaseModel):
    provider: str = "google"
    model_name: str = "gemini-3.1-flash-lite-preview"
    temperature: float = 0.7
    max_tokens: int = 4096


class PlannerSettings(BaseModel):
    core: dict = {}
    model: ModelConfig = ModelConfig()
    execution: dict = {}

    @classmethod
    def load(cls) -> "PlannerSettings":
        """Load from settings.yaml next to this file."""
        path = Path(__file__).parent / "settings.yaml"
        if not path.exists():
            log.warning(f"Planner settings not found at {path}, using defaults")
            return cls()
        try:
            with open(path, "r", encoding="utf-8") as f:
                return cls(**yaml.safe_load(f))
        except (ValidationError, Exception) as e:
            log.error(f"Failed to load planner settings: {e}")
            return cls()


class PlannerPrompts(BaseModel):
    system_prompt: str = "You are Dexpert, an advanced AI assistant."

    @classmethod
    def load(cls) -> "PlannerPrompts":
        """Load from prompts.yaml next to this file."""
        path = Path(__file__).parent / "prompts.yaml"
        if not path.exists():
            log.warning(f"Planner prompts not found at {path}, using defaults")
            return cls()
        try:
            with open(path, "r", encoding="utf-8") as f:
                return cls(**yaml.safe_load(f))
        except (ValidationError, Exception) as e:
            log.error(f"Failed to load planner prompts: {e}")
            return cls()