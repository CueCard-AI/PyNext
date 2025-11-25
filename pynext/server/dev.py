"""
Development server for PyNext.

Provides hot reloading and development features.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

import uvicorn
from watchfiles import awatch

from pynext.server.app import PyNextApp


class DevServer:
    """
    Development server with hot reloading.
    
    Watches for file changes and automatically reloads routes.
    """
    
    def __init__(
        self,
        app: PyNextApp,
        host: str = "127.0.0.1",
        port: int = 3000,
    ):
        self.app = app
        self.host = host
        self.port = port
        self._watch_task: Optional[asyncio.Task] = None
    
    async def _watch_files(self) -> None:
        """Watch for file changes and reload."""
        pages_dir = self.app.pages_dir
        
        print(f"[PyNext] Watching for changes in {pages_dir}")
        
        try:
            async for changes in awatch(pages_dir):
                for change_type, path in changes:
                    if path.endswith(".py") and "__pycache__" not in path:
                        print(f"[PyNext] Detected change: {path}")
                        try:
                            self.app.reload_routes(path)
                            print(f"[PyNext] Reloaded routes")
                        except Exception as e:
                            print(f"[PyNext] Error reloading: {e}")
        except asyncio.CancelledError:
            pass
    
    def run(self) -> None:
        """Start the development server."""
        print(f"\n  PyNext Dev Server")
        print(f"  ─────────────────")
        print(f"  → Local:   http://{self.host}:{self.port}")
        print(f"  → Pages:   {self.app.pages_dir}")
        print(f"  → Static:  {self.app.static_dir}")
        print(f"\n  Press Ctrl+C to stop\n")
        
        # Create config for uvicorn
        config = uvicorn.Config(
            app=self.app,
            host=self.host,
            port=self.port,
            log_level="warning",
            access_log=False,
        )
        
        server = uvicorn.Server(config)
        
        # Run with file watching
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def run_all():
            # Start file watcher
            self._watch_task = asyncio.create_task(self._watch_files())
            
            # Start server
            await server.serve()
            
            # Cleanup
            if self._watch_task:
                self._watch_task.cancel()
                try:
                    await self._watch_task
                except asyncio.CancelledError:
                    pass
        
        try:
            loop.run_until_complete(run_all())
        except KeyboardInterrupt:
            pass
        finally:
            loop.close()


def run_dev_server(
    pages_dir: str = "pages",
    static_dir: str = "public",
    host: str = "127.0.0.1",
    port: int = 3000,
) -> None:
    """
    Run the PyNext development server.
    
    Args:
        pages_dir: Directory containing page components
        static_dir: Directory for static files
        host: Host to bind to
        port: Port to listen on
    """
    app = PyNextApp(pages_dir=pages_dir, static_dir=static_dir, debug=True)
    server = DevServer(app, host=host, port=port)
    server.run()

