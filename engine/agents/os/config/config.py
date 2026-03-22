import os
import yaml
import logging
from pathlib import Path
from pydantic import BaseModel, ValidationError
from typing import List, Optional

log = logging.getLogger(__name__)

class OSSettings(BaseModel):
    core: dict
    model: dict
    execution: dict
    bridge: dict
    skills: dict
    vision: dict = {}

    @classmethod
    def load(cls) -> "OSSettings":
        path = Path(__file__).parent / "setting.yaml"
        if not path.exists():
            # Fallback if the user named it settings.yaml
            path = Path(__file__).parent / "settings.yaml"
        
        with open(path, "r", encoding="utf-8") as f:
            return cls(**yaml.safe_load(f))

class OSPrompts(BaseModel):
    system_prompt: str

    @classmethod
    def load(cls) -> "OSPrompts":
        path = Path(__file__).parent / "prompt.yaml"
        with open(path, "r", encoding="utf-8") as f:
            return cls(**yaml.safe_load(f))
