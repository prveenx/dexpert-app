import os
import yaml
from pathlib import Path
from pydantic import BaseModel

class ModelConfig(BaseModel):
    provider: str
    model_name: str
    temperature: float
    max_tokens: int

class PlannerSettings(BaseModel):
    core: dict
    model: ModelConfig
    execution: dict

    @classmethod
    def load(cls) -> "PlannerSettings":
        path = Path(__file__).parent / "settings.yaml"
        with open(path, "r") as f:
            return cls(**yaml.safe_load(f))

class PlannerPrompts(BaseModel):
    system_prompt: str

    @classmethod
    def load(cls) -> "PlannerPrompts":
        path = Path(__file__).parent / "prompts.yaml"
        with open(path, "r") as f:
            return cls(**yaml.safe_load(f))