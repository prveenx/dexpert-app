# FILE: /browser/manager.py
import os
import asyncio
import logging
import time
import uuid
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any

from playwright.async_api import async_playwright, Playwright, BrowserContext, Page
from .browser.config.config import BrowserAgentSettings

log = logging.getLogger(__name__)

_SYSTEM_DOWNLOADS = Path(os.path.expanduser('~/Downloads')).resolve()


class BrowserManager:
    """
    Infrastructure Layer for the Browser Agent.
    
    Uses CDP (Chrome DevTools Protocol) to override Playwright's download
    interception, allowing background downloads with real progress tracking
    and actual filenames/extensions.
    """
    def __init__(self, config: BrowserAgentSettings):
        self.config = config
        self.playwright: Optional[Playwright] = None
        self.context: Optional[BrowserContext] = None
        self.active_page: Optional[Page] = None
        self._is_running = False
        
        # Download tracking (CDP-based)
        self.active_downloads: Dict[str, dict] = {}
        self.completed_downloads: List[dict] = []
        self._cdp_sessions: List[Any] =[]
        
        # Download event coordination
        self._download_event: asyncio.Event = asyncio.Event()
        self._last_captured_download: Optional[dict] = None

    async def initialize(self):
        if self._is_running: return
        log.info(f"Initializing Browser Engine (Mode: {self.config.engine.mode})...")
        self.playwright = await async_playwright().start()

        if self.config.engine.mode == "launch":
            await self._launch_persistent_browser()
        elif self.config.engine.mode == "connect_cdp":
            await self._connect_over_cdp()
        else:
            raise ValueError(f"Unknown engine mode: {self.config.engine.mode}")

        # Override Playwright's download handling with native Chrome downloads
        await self._setup_native_downloads()

        self._is_running = True
        if self.config.debug.save_traces and self.context:
            await self.context.tracing.start(screenshots=True, snapshots=True, sources=True)

    async def _launch_persistent_browser(self):
        user_data_dir = self.config.engine.user_data_dir
        if user_data_dir and not os.path.exists(user_data_dir):
            os.makedirs(user_data_dir, exist_ok=True)

        args = self.config.engine.args.copy()
        width = self.config.engine.window_size.get("width", 1280)
        height = self.config.engine.window_size.get("height", 720)
        args.append(f"--window-size={width},{height}")
        viewport = {"width": width, "height": height}

        try:
            self.context = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=user_data_dir or "./.pcagent_browser_profile",
                headless=self.config.engine.headless,
                channel=self.config.engine.channel,
                args=args,
                viewport=viewport,
                ignore_default_args=["--enable-automation"],
                # IMPORTANT: Must be False to stop Playwright from deleting our files
                accept_downloads=False, 
                bypass_csp=True, 
                ignore_https_errors=True
            )
            
            if len(self.context.pages) > 0: self.active_page = self.context.pages[0]
            else: self.active_page = await self.context.new_page()

            if self.active_page.url == "about:blank" and self.config.engine.homepage:
                await self.active_page.goto(self.config.engine.homepage, wait_until="domcontentloaded")
        except Exception as e:
            raise e

    async def _connect_over_cdp(self):
        cdp_url = self.config.engine.cdp_url
        try:
            browser = await self.playwright.chromium.connect_over_cdp(cdp_url)
            if not browser.contexts: self.context = await browser.new_context()
            else: self.context = browser.contexts[0]
            if self.context.pages: self.active_page = self.context.pages[0]
            else: self.active_page = await self.context.new_page()
        except Exception as e:
            raise ConnectionError(f"CDP Connection failed: {e}")

    # ------------------------------------------------------------------
    # CDP Native Downloads Setup
    # ------------------------------------------------------------------

    async def _setup_native_downloads(self):
        _SYSTEM_DOWNLOADS.mkdir(parents=True, exist_ok=True)
        dl_path = str(_SYSTEM_DOWNLOADS)

        try:
            await self._apply_cdp_download_override(self.active_page, dl_path)
            
            # Auto-override for any NEW pages/tabs that open
            self.context.on("page", lambda page: asyncio.create_task(
                self._apply_cdp_download_override(page, dl_path)
            ))
            
            log.info(f"Native CDP downloads configured: {dl_path}")
        except Exception as e:
            log.error(f"CDP download setup failed: {e}")

    async def _apply_cdp_download_override(self, page: Page, dl_path: str):
        try:
            cdp = await self.context.new_cdp_session(page)
            self._cdp_sessions.append(cdp)
            
            # FIX: Use "allow" instead of "allowAndName" so it doesn't freeze in headless mode
            await cdp.send("Browser.setDownloadBehavior", {
                "behavior": "allow",
                "downloadPath": dl_path,
                "eventsEnabled": True
            })
            
            cdp.on("Browser.downloadWillBegin", lambda p: self._on_cdp_download_begin(p))
            cdp.on("Browser.downloadProgress", lambda p: self._on_cdp_download_progress(p))
            
            log.debug(f"CDP download override applied for page: {page.url[:50]}")
        except Exception as e:
            log.warning(f"CDP override failed for page: {e}")

    def _get_unique_path(self, base_path: Path) -> Path:
        """Helper to act like a human OS: appends (1), (2) if file exists."""
        if not base_path.exists():
            return base_path
        directory = base_path.parent
        name = base_path.stem
        ext = base_path.suffix
        counter = 1
        while True:
            new_path = directory / f"{name} ({counter}){ext}"
            if not new_path.exists():
                return new_path
            counter += 1

    def _on_cdp_download_begin(self, params: dict):
        guid = params.get("guid", str(uuid.uuid4()))
        filename = params.get("suggestedFilename", "unknown_file")
        
        task_id = guid[:8]
        
        for d in self.active_downloads.values():
            if d.get("guid") == guid:
                return
        
        # 🚀 SOTA: Rich ETA & Progress Tracking Fields Added
        state = {
            "id": task_id,
            "guid": guid,
            "filename": filename,
            "status": "downloading",
            "downloaded_mb": 0.0,
            "total_mb": 0.0,
            "percent": 0.0,
            "speed_mb_s": 0.0,
            "eta_seconds": -1,
            "start_time": time.time(),
            "elapsed_seconds": 0,
            "final_path": None,
            "error": None
        }
        self.active_downloads[task_id] = state
        
        self._last_captured_download = state
        self._download_event.set()
        
        log.info(f"CDP Download started: {filename} (task: {task_id})")

    def _on_cdp_download_progress(self, params: dict):
        guid = params.get("guid", "")
        cdp_state = params.get("state", "")
        received = params.get("receivedBytes", 0)
        total = params.get("totalBytes", 0)
        
        task_id = None
        for tid, d in list(self.active_downloads.items()):
            if d.get("guid") == guid:
                task_id = tid
                break
        
        if not task_id: return
        dl = self.active_downloads[task_id]
        
        # 🚀 SOTA: Calculate exact ETA, Speed, and Percentage
        dl["downloaded_mb"] = received / (1024 * 1024)
        dl["total_mb"] = total / (1024 * 1024) if total > 0 else 0.0
        
        if dl["total_mb"] > 0:
            dl["percent"] = (dl["downloaded_mb"] / dl["total_mb"]) * 100.0
        
        elapsed = time.time() - dl["start_time"]
        dl["elapsed_seconds"] = int(elapsed)
        
        if elapsed > 0:
            dl["speed_mb_s"] = dl["downloaded_mb"] / elapsed
            
        if dl["speed_mb_s"] > 0 and dl["total_mb"] > 0:
            remaining_mb = dl["total_mb"] - dl["downloaded_mb"]
            dl["eta_seconds"] = int(remaining_mb / dl["speed_mb_s"])
        
        # --- THE FIX: RENAME GUID TO REAL FILENAME UPON COMPLETION ---
        if cdp_state == "completed":
            dl["status"] = "completed"
            dl["percent"] = 100.0
            dl["eta_seconds"] = 0
            
            # CDP downloads the file named as its GUID
            temp_file_path = _SYSTEM_DOWNLOADS / dl["guid"]
            intended_file_path = _SYSTEM_DOWNLOADS / dl["filename"]
            
            # Prevent overwriting existing files like a human OS
            final_file_path = self._get_unique_path(intended_file_path)
            
            try:
                if temp_file_path.exists():
                    # Rename/Move the file to have its correct extension and name
                    shutil.move(str(temp_file_path), str(final_file_path))
                    dl["final_path"] = str(final_file_path)
                    dl["downloaded_mb"] = final_file_path.stat().st_size / (1024 * 1024)
                    log.info(f"CDP Download completed and renamed: {final_file_path.name} ({dl['downloaded_mb']:.1f}MB)")
                else:
                    dl["final_path"] = str(final_file_path)
                    log.warning(f"CDP raw GUID file not found. File may have been moved by external process.")
            except Exception as e:
                dl["status"] = "failed"
                dl["error"] = f"Failed to rename file: {str(e)}"
                log.error(dl["error"])
                
            self.completed_downloads.append(dl.copy())
            del self.active_downloads[task_id]
            
        elif cdp_state == "canceled":
            dl["status"] = "cancelled"
            dl["error"] = "Download was cancelled by the browser."
            self.completed_downloads.append(dl.copy())
            del self.active_downloads[task_id]
            log.info(f"CDP Download cancelled: {dl['filename']}")

    # ------------------------------------------------------------------
    # Download Query / Control
    # ------------------------------------------------------------------

    def _resolve_task_id(self, identifier: str) -> Optional[str]:
        if not identifier: return None
        if identifier in self.active_downloads: return identifier
        for d in self.completed_downloads:
            if d["id"] == identifier: return identifier
        
        il = identifier.lower().strip()
        for tid, d in self.active_downloads.items():
            if d.get("filename", "").lower() == il: return tid
        for d in self.completed_downloads:
            if d.get("filename", "").lower() == il: return d["id"]
        
        all_ids = list(self.active_downloads.keys()) +[d["id"] for d in self.completed_downloads]
        if len(all_ids) == 1: return all_ids[0]
        return None

    async def cancel_download(self, task_id: str) -> bool:
        resolved = self._resolve_task_id(task_id)
        if resolved and resolved in self.active_downloads:
            self.active_downloads[resolved]["status"] = "cancelled"
            self.completed_downloads.append(self.active_downloads[resolved].copy())
            del self.active_downloads[resolved]
            return True
        return False

    def get_all_downloads(self) -> List[dict]:
        for d in self.active_downloads.values():
            d["elapsed_seconds"] = int(time.time() - d["start_time"])
        return list(self.active_downloads.values()) + self.completed_downloads

    def clear_completed_downloads(self):
        self.completed_downloads.clear()

    # ------------------------------------------------------------------
    # Page / Lifecycle
    # ------------------------------------------------------------------

    async def get_page(self) -> Page:
        if not self._is_running: await self.initialize()
        if not self.active_page or self.active_page.is_closed():
             self.active_page = await self.context.new_page()
        return self.active_page

    async def close(self, force: bool = False):
        if not self._is_running: return
        if self.config.engine.keep_alive and not force: return
        for cdp in self._cdp_sessions:
            try: await cdp.detach()
            except: pass
        self._cdp_sessions.clear()
        if self.context: await self.context.close()
        if self.playwright: await self.playwright.stop()
        self.playwright = None
        self.context = None
        self._is_running = False
        self.active_downloads = {}
        self.completed_downloads =[]