# FILE: engine/agents/os/middleware/vfs_router.py
import os
import logging
from pathlib import Path
from typing import Optional, Tuple

log = logging.getLogger(__name__)

class VFSRouter:
    """
    Virtual File System Router & Dynamic CWD Manager.
    Solves path hallucinations, auto-detects Python VENVs, 
    and routes 'mcp://' resource URIs seamlessly.
    """
    def __init__(self, mcp_manager=None):
        self.cwd: Path = Path(os.path.expanduser("~")).resolve()
        self.mcp_manager = mcp_manager

    def change_directory(self, target_path: str) -> str:
        """Updates the agent's spatial awareness."""
        try:
            target = self.resolve_path(target_path)
            if target.exists() and target.is_dir():
                self.cwd = target
                return f"Success: Changed directory to {self.cwd}"
            return f"Error: Directory '{target}' does not exist."
        except Exception as e:
            return f"Error resolving path: {e}"

    def resolve_path(self, raw_path: str) -> Path:
        """
        Normalizes paths natively.
        If absolute (C:/ or /var), uses it.
        If relative (src/main.py), resolves against self.cwd.
        """
        p = Path(raw_path).expanduser()
        if p.is_absolute():
            return p.resolve()
        return (self.cwd / p).resolve()

    def detect_venv(self) -> Optional[Path]:
        """
        Scans current CWD for Python virtual environments.
        Used by the execution middleware to prevent 'pip not found' errors.
        """
        venv_names = [".venv", "venv", "env"]
        for name in venv_names:
            candidate = self.cwd / name
            if candidate.exists() and candidate.is_dir():
                # Detect binary path based on OS
                if os.name == 'nt':
                    bin_dir = candidate / "Scripts"
                else:
                    bin_dir = candidate / "bin"
                
                if bin_dir.exists():
                    return bin_dir
        return None

    async def fetch_resource(self, uri: str) -> Tuple[bool, str]:
        """
        The magic router.
        If uri starts with 'mcp://' or 'postgres://', routes to MCP.
        Otherwise, treats as local file.
        Returns: (is_mcp, content_or_error)
        """
        if uri.startswith("mcp://") or uri.startswith("postgres://") or uri.startswith("github://"):
            if not self.mcp_manager:
                return True, f"Error: Cannot resolve MCP resource '{uri}'. MCP Manager offline."
            
            try:
                log.info(f"VFS Router: Intercepted remote resource request: {uri}")
                content = await self.mcp_manager.read_resource(uri)
                return True, content
            except Exception as e:
                return True, f"MCP Resource Error: {e}"
        
        # Local File Resolution
        return False, ""