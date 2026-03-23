# FILE: agents/os/config/config.py
"""
OS agent configuration — Pydantic models and YAML loader.
"""

import yaml
import logging
from pathlib import Path
from pydantic import BaseModel, ValidationError

log = logging.getLogger(__name__)


class OSSettings(BaseModel):
    core: dict = {}
    model: dict = {}
    execution: dict = {}
    bridge: dict = {}
    skills: dict = {}
    vision: dict = {}

    @classmethod
    def load(cls) -> "OSSettings":
        """Load from setting.yaml or settings.yaml next to this file."""
        path = Path(__file__).parent / "setting.yaml"
        if not path.exists():
            path = Path(__file__).parent / "settings.yaml"

        if not path.exists():
            log.warning(f"OS settings not found at {path}, using defaults")
            return cls()

        try:
            with open(path, "r", encoding="utf-8") as f:
                return cls(**yaml.safe_load(f))
        except (ValidationError, Exception) as e:
            log.error(f"Failed to load OS settings: {e}")
            return cls()


class OSPrompts(BaseModel):
    system_prompt: str = "You are Dexpert OS Agent operating on {os_name}."

    @classmethod
    def load(cls) -> "OSPrompts":
        """Load from prompt.yaml next to this file."""
        path = Path(__file__).parent / "prompt.yaml"
        if not path.exists():
            log.warning(f"OS prompts not found at {path}, using defaults")
            return cls()
        try:
            with open(path, "r", encoding="utf-8") as f:
                return cls(**yaml.safe_load(f))
        except (ValidationError, Exception) as e:
            log.error(f"Failed to load OS prompts: {e}")
            return cls()
