# FILE: /browser/config/config.py
"""
Pydantic configuration models for the Browser Agent.
Maps 1:1 to /browser/config/setting.yaml.
"""
import os
import yaml
import logging
from pathlib import Path
from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field, ValidationError

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Section Models
# ---------------------------------------------------------------------------

class CoreConfig(BaseModel):
    agent_id: str
    version: str
    description: str


class EngineConfig(BaseModel):
    browser_type: Literal["chromium", "firefox", "webkit"] = "chromium"
    headless: bool = False
    channel: str = "chrome"
    mode: Literal["launch", "connect_cdp"] = "launch"
    cdp_url: str = "http://localhost:9222"
    user_data_dir: Optional[str] = None
    profile_name: str = "Default"
    window_size: Dict[str, int] = Field(default_factory=lambda: {"width": 1280, "height": 720})
    homepage: str = "https://www.google.com"
    keep_alive: bool = True
    args: List[str] = Field(default_factory=list)


class ControllerConfig(BaseModel):
    action_delay: float = 0.5
    navigation_timeout: int = 30
    element_timeout: int = 5
    max_retries_per_action: int = 3
    interaction_mode: Literal["strict", "fuzzy"] = "strict"
    highlight_elements: bool = True
    allowed_domains: List[str] = Field(default_factory=list)
    blocked_resource_types: List[str] = Field(default_factory=list)


class PerceptionConfig(BaseModel):
    strategy: Literal["accessibility", "html"] = "accessibility"
    use_shadow_dom: bool = True
    generate_ax_ids: bool = True
    visual_mode: bool = False
    screenshot_quality: int = 60
    model_name: str = "" # To be resolved from settings
    vision_model: str = "" # To be resolved from settings


class CaptchaConfig(BaseModel):
    """Configuration for the automatic CAPTCHA detection & solving subsystem."""
    enabled: bool = True
    auto_solve: bool = True
    provider: str = "vision_llm"
    crop_padding: Dict[str, int] = Field(
        default_factory=lambda: {"width": 20, "height": 20}
    )
    crop_width: int = 300
    crop_height: int = 100
    max_attempts: int = 3


class DebugConfig(BaseModel):
    enabled: bool = True
    log_level: str = "INFO"
    save_traces: bool = True
    trace_dir: str = ".//browser/traces"
    save_screenshots_on_fail: bool = True
    screenshot_dir: str = ".//browser/screenshots"
    log_network_traffic: bool = False


# ---------------------------------------------------------------------------
# Root Settings
# ---------------------------------------------------------------------------

class BrowserAgentSettings(BaseModel):
    """Root settings object — mirrors the full setting.yaml structure."""
    core: CoreConfig
    engine: EngineConfig
    controller: ControllerConfig
    perception: PerceptionConfig
    captcha: CaptchaConfig = Field(default_factory=CaptchaConfig)
    debug: DebugConfig

    @classmethod
    def load_from_yaml(cls, path: str) -> "BrowserAgentSettings":
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"Browser settings not found at {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_data = yaml.safe_load(f)
            return cls(**raw_data)
        except ValidationError as e:
            log.critical(f"Invalid Browser Configuration at {path}: {e}")
            raise


class BrowserPrompts(BaseModel):
    """Prompt templates loaded from prompt.yaml."""
    system_prompt: str
    vision_system_prompt: str
    extraction_prompt: str
    error_recovery_prompt: str

    @classmethod
    def load_from_yaml(cls, path: str) -> "BrowserPrompts":
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"Browser prompts not found at {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_data = yaml.safe_load(f)
            return cls(**raw_data)
        except ValidationError as e:
            log.critical(f"Invalid Browser Prompts at {path}: {e}")
            raise