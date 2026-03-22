"""Tools package."""

from typing import Any, Callable, Optional


class UnifiedToolRegistry:
    """
    Single source of truth for all available tools.
    Namespaced by source: native:*, plugin:*, mcp:*
    """

    def __init__(self):
        self._tools: dict[str, dict] = {}

    def register_native(self, tools: list[dict]) -> None:
        for tool in tools:
            name = f"native:{tool['name']}"
            self._tools[name] = {**tool, "source": "native", "qualified_name": name}

    def register_plugin(self, plugin_id: str, tools: list[dict]) -> None:
        for tool in tools:
            name = f"plugin:{plugin_id}:{tool['name']}"
            self._tools[name] = {**tool, "source": "plugin", "source_id": plugin_id, "qualified_name": name}

    def register_mcp(self, server_id: str, tools: list[dict]) -> None:
        for tool in tools:
            name = f"mcp:{server_id}:{tool['name']}"
            self._tools[name] = {**tool, "source": "mcp", "source_id": server_id, "qualified_name": name}

    def unregister_plugin(self, plugin_id: str) -> None:
        self._tools = {k: v for k, v in self._tools.items() if not k.startswith(f"plugin:{plugin_id}:")}

    def unregister_mcp(self, server_id: str) -> None:
        self._tools = {k: v for k, v in self._tools.items() if not k.startswith(f"mcp:{server_id}:")}

    def get_all(self) -> list[dict]:
        return list(self._tools.values())

    def find(self, name: str) -> Optional[dict]:
        return self._tools.get(name)
