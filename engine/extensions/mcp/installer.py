import logging
import asyncio
import subprocess
from typing import Optional
from enum import Enum

from .discoverer import McpServerConfig

log = logging.getLogger(__name__)

class PackageManager(str, Enum):
    NPM = "npm"
    UV = "uv"
    CARGO = "cargo"

class McpInstaller:
    """Installs MCP servers via standard package managers."""

    @classmethod
    async def install(cls, package_id: str, manager: PackageManager) -> Optional[McpServerConfig]:
        """Installs the given package using the specified package manager."""
        log.info(f"Attempting MCP install: {manager.value} -> {package_id}")

        try:
            if manager == PackageManager.NPM:
                # Assuming npx -y will fetch it on first run, we don't necessarily need global install, 
                # but if we want to install globally: npm install -g <package>
                proc = await asyncio.create_subprocess_shell(
                    f"npm install -g {package_id}",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                _, _ = await proc.communicate()
                if proc.returncode == 0:
                    return McpServerConfig(id=package_id, command="npx", args=["-y", package_id])
            
            elif manager == PackageManager.UV:
                proc = await asyncio.create_subprocess_shell(
                    f"uv tool install {package_id}",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                _, _ = await proc.communicate()
                if proc.returncode == 0:
                    return McpServerConfig(id=package_id, command="uvx", args=[package_id])

            elif manager == PackageManager.CARGO:
                proc = await asyncio.create_subprocess_shell(
                    f"cargo install {package_id}",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                _, _ = await proc.communicate()
                if proc.returncode == 0:
                    return McpServerConfig(id=package_id, command=package_id, args=[])

        except Exception as e:
            log.error(f"Failed to install {package_id} via {manager.value}: {e}")

        return None
