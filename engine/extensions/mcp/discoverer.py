import json
import logging
import os
import subprocess
from typing import List
from pydantic import BaseModel, ConfigDict

log = logging.getLogger(__name__)

class McpServerConfig(BaseModel):
    id: str
    command: str
    args: List[str]
    model_config = ConfigDict(extra="ignore")

class McpDiscoverer:
    """Discover installed MCP servers."""

    @classmethod
    def discover_npm_global(cls) -> List[McpServerConfig]:
        configs = []
        try:
            res = subprocess.run(["npm", "ls", "-g", "--json", "--depth=0"], capture_output=True, text=True, check=True)
            data = json.loads(res.stdout)
            deps = data.get("dependencies", {})
            for pkg, info in deps.items():
                if pkg.startswith("@modelcontextprotocol/") or "mcp-" in pkg:
                    # simplistic assumption
                    bin_name = "npx"
                    configs.append(McpServerConfig(id=pkg, command=bin_name, args=["-y", pkg]))
        except Exception as e:
            log.warning(f"Error discovering npm mcp servers: {e}")
        return configs

    @classmethod
    def discover_uvx(cls) -> List[McpServerConfig]:
        configs = []
        try:
            res = subprocess.run(["uv", "tool", "list"], capture_output=True, text=True)
            if res.returncode == 0:
                for line in res.stdout.splitlines():
                    if "mcp" in line.lower():
                        pkg = line.split(" ")[0].strip()
                        if pkg:
                            configs.append(McpServerConfig(id=pkg, command="uvx", args=[pkg]))
        except Exception:
            pass
        return configs

    @classmethod
    def discover_all(cls) -> List[McpServerConfig]:
        configs = []
        configs.extend(cls.discover_npm_global())
        configs.extend(cls.discover_uvx())
        return configs
