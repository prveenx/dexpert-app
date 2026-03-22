# FILE: /browser/core/memory.py
"""
Browser-specific persistent memory.

Stores site-specific knowledge that helps the agent across sessions:
  - Selector patterns that worked for a site
  - Login flow observations (e.g., "amazon.com uses 2FA")
  - Cookie consent button locations
  - Known captcha-protected pages

This is a thin JSON file adapter — for heavier persistence, use the
central StateManager (memory/state_manager.py).
"""
import json
import os
import logging
from typing import Dict, Any, Optional

log = logging.getLogger(__name__)


class BrowserMemory:
    """
    Persistent JSON-backed memory for the Browser Agent.

    Saves to ``data/browser_memory.json`` and is loaded on agent init.
    Only stores site-level observations — task-level state lives in
    the Scratchpad.
    """

    def __init__(self, storage_path: str = "data/browser_memory.json"):
        self.storage_path = storage_path
        self.data: Dict[str, Any] = {
            "sites": {},      # domain → {key: value}
            "knowledge": {},  # general facts
        }
        self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
                log.debug(f"BrowserMemory: Loaded from {self.storage_path}")
            except Exception as e:
                log.error(f"BrowserMemory: Failed to load: {e}")

    def save(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.storage_path) or ".", exist_ok=True)
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            log.error(f"BrowserMemory: Failed to save: {e}")

    # ------------------------------------------------------------------
    # Site Knowledge
    # ------------------------------------------------------------------

    def update_site_info(self, domain: str, key: str, value: Any) -> None:
        """Store a site-specific observation (e.g., selector patterns, 2FA status)."""
        if domain not in self.data["sites"]:
            self.data["sites"][domain] = {}
        self.data["sites"][domain][key] = value
        self.save()

    def get_site_info(self, domain: str) -> Dict[str, Any]:
        """Retrieve all stored info for a domain."""
        return self.data["sites"].get(domain, {})

    def get_site_hint(self, domain: str, key: str) -> Optional[Any]:
        """Retrieve a specific hint for a domain."""
        return self.data["sites"].get(domain, {}).get(key)

    # ------------------------------------------------------------------
    # General Knowledge
    # ------------------------------------------------------------------

    def learn_fact(self, key: str, fact: Any) -> None:
        """Store a general fact."""
        self.data["knowledge"][key] = fact
        self.save()

    def get_fact(self, key: str) -> Optional[Any]:
        """Retrieve a stored fact."""
        return self.data["knowledge"].get(key)

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def known_domains(self) -> list:
        """List all domains with stored knowledge."""
        return list(self.data["sites"].keys())

    def clear(self) -> None:
        """Wipe all browser memory."""
        self.data = {"sites": {}, "knowledge": {}}
        self.save()
