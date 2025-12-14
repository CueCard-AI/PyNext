"""
Chrome Launcher - Auto-launch Chrome with CDP Enabled.

This module finds and launches Chrome/Chromium with the remote debugging
port enabled, allowing CDP connections.

Why Auto-Launch?
    Manual setup (find Chrome, add flags, get WS URL) is tedious.
    Auto-launch provides a seamless developer experience - just run
    `pynext dev --ai-debug` and Chrome opens automatically.

How It Works:
    1. Find Chrome installation (varies by OS)
    2. Launch with --remote-debugging-port=9222
    3. Wait for Chrome to be ready
    4. Fetch WebSocket URL from http://localhost:9222/json
    5. Return WS URL for CDPBridge to connect

Platform Support:
    - macOS: /Applications/Google Chrome.app
    - Linux: google-chrome, chromium-browser, etc.
    - Windows: Chrome in Program Files

Example:
    launcher = ChromeLauncher()
    ws_url = await launcher.launch("http://localhost:3000")
    
    # Chrome is now open at localhost:3000 with debugging enabled
    # ws_url can be passed to CDPBridge.connect()
    
    # When done:
    launcher.shutdown()
"""

from __future__ import annotations

import asyncio
import json
import os
import platform
import shutil
import signal
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import urllib.request
import urllib.error


@dataclass
class ChromeInfo:
    """Information about a Chrome installation."""
    path: Path
    version: Optional[str] = None
    
    @property
    def exists(self) -> bool:
        """Check if Chrome executable exists."""
        return self.path.exists()


class ChromeLauncher:
    """
    Launches Chrome with CDP (remote debugging) enabled.
    
    This class handles:
    - Finding Chrome installation on the system
    - Creating a temporary profile directory
    - Launching with correct flags for CDP
    - Waiting for Chrome to be ready
    - Fetching the WebSocket URL
    - Graceful shutdown
    
    Attributes:
        debug_port: Port for CDP (default 9222)
        process: The Chrome subprocess
        profile_dir: Temporary profile directory
    
    Example:
        launcher = ChromeLauncher(debug_port=9222)
        
        # Launch and get WebSocket URL
        ws_url = await launcher.launch("http://localhost:3000")
        print(f"Connect to: {ws_url}")
        
        # Later, shut down Chrome
        launcher.shutdown()
    """
    
    # Common Chrome paths by platform
    CHROME_PATHS = {
        "Darwin": [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary",
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        ],
        "Linux": [
            "google-chrome",
            "google-chrome-stable",
            "chromium",
            "chromium-browser",
            "/usr/bin/google-chrome",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
            "/snap/bin/chromium",
        ],
        "Windows": [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"),
        ],
    }
    
    def __init__(self, debug_port: int = 9222):
        """
        Initialize the Chrome launcher.
        
        Args:
            debug_port: Port for CDP remote debugging (default 9222)
        """
        self.debug_port = debug_port
        self.process: Optional[subprocess.Popen] = None
        self.profile_dir: Optional[Path] = None
        self._chrome_path: Optional[Path] = None
    
    def find_chrome(self) -> Optional[ChromeInfo]:
        """
        Find Chrome installation on the system.
        
        Returns:
            ChromeInfo with path if found, None otherwise
        """
        system = platform.system()
        paths = self.CHROME_PATHS.get(system, [])
        
        for path_str in paths:
            # Try shutil.which for command names
            if not os.path.isabs(path_str):
                found = shutil.which(path_str)
                if found:
                    return ChromeInfo(path=Path(found))
            else:
                path = Path(path_str)
                if path.exists():
                    return ChromeInfo(path=path)
        
        return None
    
    async def launch(
        self,
        url: str = "about:blank",
        headless: bool = False,
        window_size: tuple[int, int] = (1280, 800),
    ) -> str:
        """
        Launch Chrome with CDP enabled and navigate to URL.
        
        Args:
            url: Initial URL to open
            headless: Run in headless mode (no visible window)
            window_size: Window dimensions (width, height)
        
        Returns:
            WebSocket URL for CDP connection
        
        Raises:
            RuntimeError: If Chrome not found or launch fails
        """
        # Find Chrome
        chrome_info = self.find_chrome()
        if not chrome_info:
            raise RuntimeError(
                "Chrome/Chromium not found. Please install Chrome or set CHROME_PATH.\n"
                "Download: https://www.google.com/chrome/"
            )
        
        self._chrome_path = chrome_info.path
        
        # Create temporary profile directory
        self.profile_dir = Path(tempfile.mkdtemp(prefix="pynext_debug_"))
        
        # Build Chrome arguments
        args = [
            str(self._chrome_path),
            f"--remote-debugging-port={self.debug_port}",
            f"--user-data-dir={self.profile_dir}",
            f"--window-size={window_size[0]},{window_size[1]}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-background-networking",
            "--disable-client-side-phishing-detection",
            "--disable-default-apps",
            "--disable-extensions",
            "--disable-hang-monitor",
            "--disable-popup-blocking",
            "--disable-prompt-on-repost",
            "--disable-sync",
            "--disable-translate",
            "--metrics-recording-only",
            "--safebrowsing-disable-auto-update",
            "--password-store=basic",
            "--use-mock-keychain",
        ]
        
        if headless:
            args.append("--headless=new")
        
        args.append(url)
        
        # Launch Chrome
        try:
            # Suppress Chrome output
            self.process = subprocess.Popen(
                args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to launch Chrome: {e}")
        
        # Wait for Chrome to be ready and get WebSocket URL
        ws_url = await self._wait_for_ready()
        
        return ws_url
    
    async def _wait_for_ready(
        self,
        timeout: float = 30.0,
        poll_interval: float = 0.1,
    ) -> str:
        """
        Wait for Chrome to be ready and return WebSocket URL.
        
        Args:
            timeout: Max seconds to wait
            poll_interval: Seconds between polls
        
        Returns:
            WebSocket URL for page
        
        Raises:
            TimeoutError: If Chrome doesn't respond in time
        """
        debug_url = f"http://localhost:{self.debug_port}/json"
        
        elapsed = 0.0
        while elapsed < timeout:
            try:
                with urllib.request.urlopen(debug_url, timeout=1) as response:
                    data = json.loads(response.read())
                    
                    # Find the first page target
                    for target in data:
                        if target.get("type") == "page":
                            ws_url = target.get("webSocketDebuggerUrl")
                            if ws_url:
                                return ws_url
                    
                    # No page target yet, wait
                    
            except (urllib.error.URLError, json.JSONDecodeError, OSError):
                pass  # Chrome not ready yet
            
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
        
        raise TimeoutError(
            f"Chrome did not start within {timeout} seconds. "
            f"Check if port {self.debug_port} is already in use."
        )
    
    def shutdown(self) -> None:
        """
        Shut down Chrome gracefully.
        
        Terminates the Chrome process and cleans up the temporary profile.
        """
        if self.process:
            try:
                # Try graceful termination first
                if platform.system() == "Windows":
                    self.process.terminate()
                else:
                    os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                
                # Wait briefly for graceful exit
                try:
                    self.process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    # Force kill
                    if platform.system() == "Windows":
                        self.process.kill()
                    else:
                        os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                
            except (ProcessLookupError, OSError):
                pass  # Process already gone
            
            self.process = None
        
        # Clean up profile directory
        if self.profile_dir and self.profile_dir.exists():
            try:
                import shutil
                shutil.rmtree(self.profile_dir, ignore_errors=True)
            except Exception:
                pass  # Best effort cleanup
            
            self.profile_dir = None
    
    @property
    def is_running(self) -> bool:
        """Check if Chrome is running."""
        if not self.process:
            return False
        return self.process.poll() is None
    
    async def get_all_pages(self) -> list[dict]:
        """
        Get information about all open pages.
        
        Returns:
            List of page info dicts with id, url, title, webSocketDebuggerUrl
        """
        debug_url = f"http://localhost:{self.debug_port}/json"
        
        try:
            with urllib.request.urlopen(debug_url, timeout=5) as response:
                data = json.loads(response.read())
                return [t for t in data if t.get("type") == "page"]
        except Exception:
            return []
    
    async def navigate_to(self, url: str) -> None:
        """
        Navigate the current page to a new URL.
        
        This uses CDP to navigate rather than opening a new tab.
        
        Args:
            url: URL to navigate to
        """
        # This requires an active CDP connection, so we provide it as a helper
        # The actual navigation should be done through CDPBridge
        raise NotImplementedError(
            "Use CDPBridge.send_command('Page.navigate', {'url': url}) instead"
        )


async def quick_launch(url: str, debug_port: int = 9222) -> tuple[ChromeLauncher, str]:
    """
    Convenience function to launch Chrome and get WebSocket URL.
    
    Args:
        url: URL to open
        debug_port: CDP port
    
    Returns:
        Tuple of (launcher, ws_url)
    
    Example:
        launcher, ws_url = await quick_launch("http://localhost:3000")
        # ... use ws_url ...
        launcher.shutdown()
    """
    launcher = ChromeLauncher(debug_port=debug_port)
    ws_url = await launcher.launch(url)
    return launcher, ws_url

