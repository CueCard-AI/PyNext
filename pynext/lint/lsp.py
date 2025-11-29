"""
PyNext Linting - Language Server Protocol

LSP server for real-time linting in any editor.
Provides diagnostics, quick fixes, and hover information.

Usage:
    # Start the LSP server
    pynext lint lsp
    
    # Or from Python
    from pynext.lint.lsp import start_lsp_server
    start_lsp_server()

Editor Integration:
    - VS Code: Use the PyNext extension
    - Neovim: Configure with nvim-lspconfig
    - Sublime: Use LSP package
    - Emacs: Use lsp-mode
"""

from __future__ import annotations

import json
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from pynext.lint.runner import lint_file
from pynext.lint.rules import explain_rule, get_all_rules
from pynext.lint.config import load_config


# =============================================================================
# LSP Message Types
# =============================================================================

@dataclass
class LSPMessage:
    """A JSON-RPC message for LSP."""
    jsonrpc: str = "2.0"
    id: Optional[int] = None
    method: Optional[str] = None
    params: Optional[Dict] = None
    result: Optional[Any] = None
    error: Optional[Dict] = None


@dataclass
class LSPDiagnostic:
    """A diagnostic (lint error) in LSP format."""
    range: Dict
    message: str
    severity: int  # 1=Error, 2=Warning, 3=Info, 4=Hint
    code: str
    source: str = "pynext"
    
    def to_dict(self) -> Dict:
        return {
            "range": self.range,
            "message": self.message,
            "severity": self.severity,
            "code": self.code,
            "source": self.source,
        }


# =============================================================================
# LSP Server
# =============================================================================

class LSPServer:
    """
    PyNext Language Server.
    
    Provides:
    - Real-time diagnostics (linting)
    - Quick fixes for auto-fixable issues
    - Hover information for PyNext constructs
    - Code actions
    """
    
    def __init__(self):
        self.running = False
        self.documents: Dict[str, str] = {}  # uri -> content
        self.config = None
        self.handlers: Dict[str, Callable] = {
            "initialize": self._handle_initialize,
            "initialized": self._handle_initialized,
            "shutdown": self._handle_shutdown,
            "exit": self._handle_exit,
            "textDocument/didOpen": self._handle_did_open,
            "textDocument/didChange": self._handle_did_change,
            "textDocument/didSave": self._handle_did_save,
            "textDocument/didClose": self._handle_did_close,
            "textDocument/codeAction": self._handle_code_action,
            "textDocument/hover": self._handle_hover,
        }
    
    def start(self) -> None:
        """Start the LSP server."""
        self.running = True
        self._log("PyNext LSP server starting...")
        
        while self.running:
            try:
                message = self._read_message()
                if message:
                    response = self._handle_message(message)
                    if response:
                        self._write_message(response)
            except Exception as e:
                self._log(f"Error: {e}")
                break
    
    def stop(self) -> None:
        """Stop the LSP server."""
        self.running = False
    
    # -------------------------------------------------------------------------
    # Message I/O
    # -------------------------------------------------------------------------
    
    def _read_message(self) -> Optional[LSPMessage]:
        """Read a message from stdin."""
        # Read headers
        headers = {}
        while True:
            line = sys.stdin.readline()
            if not line or line == "\r\n":
                break
            
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip()] = value.strip()
        
        if "Content-Length" not in headers:
            return None
        
        # Read body
        length = int(headers["Content-Length"])
        body = sys.stdin.read(length)
        
        try:
            data = json.loads(body)
            return LSPMessage(
                jsonrpc=data.get("jsonrpc", "2.0"),
                id=data.get("id"),
                method=data.get("method"),
                params=data.get("params"),
            )
        except json.JSONDecodeError:
            return None
    
    def _write_message(self, message: LSPMessage) -> None:
        """Write a message to stdout."""
        body = json.dumps({
            "jsonrpc": message.jsonrpc,
            "id": message.id,
            "result": message.result,
            "error": message.error,
        })
        
        content = f"Content-Length: {len(body)}\r\n\r\n{body}"
        sys.stdout.write(content)
        sys.stdout.flush()
    
    def _send_notification(self, method: str, params: Dict) -> None:
        """Send a notification to the client."""
        body = json.dumps({
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        })
        
        content = f"Content-Length: {len(body)}\r\n\r\n{body}"
        sys.stdout.write(content)
        sys.stdout.flush()
    
    def _log(self, message: str) -> None:
        """Log a message to the client."""
        self._send_notification("window/logMessage", {
            "type": 3,  # Info
            "message": message,
        })
    
    # -------------------------------------------------------------------------
    # Message Handling
    # -------------------------------------------------------------------------
    
    def _handle_message(self, message: LSPMessage) -> Optional[LSPMessage]:
        """Handle an incoming message."""
        if message.method is None:
            return None
        
        handler = self.handlers.get(message.method)
        if handler:
            try:
                result = handler(message.params or {})
                if message.id is not None:
                    return LSPMessage(id=message.id, result=result)
            except Exception as e:
                if message.id is not None:
                    return LSPMessage(
                        id=message.id,
                        error={"code": -32603, "message": str(e)}
                    )
        
        return None
    
    def _handle_initialize(self, params: Dict) -> Dict:
        """Handle initialize request."""
        # Load config from workspace
        root_path = params.get("rootPath") or params.get("rootUri", "").replace("file://", "")
        if root_path:
            self.config = load_config(Path(root_path))
        
        return {
            "capabilities": {
                "textDocumentSync": {
                    "openClose": True,
                    "change": 1,  # Full sync
                    "save": {"includeText": True},
                },
                "codeActionProvider": True,
                "hoverProvider": True,
                "diagnosticProvider": {
                    "interFileDependencies": False,
                    "workspaceDiagnostics": False,
                },
            },
            "serverInfo": {
                "name": "pynext-lint",
                "version": "1.0.0",
            },
        }
    
    def _handle_initialized(self, params: Dict) -> None:
        """Handle initialized notification."""
        self._log("PyNext LSP server initialized")
    
    def _handle_shutdown(self, params: Dict) -> None:
        """Handle shutdown request."""
        return None
    
    def _handle_exit(self, params: Dict) -> None:
        """Handle exit notification."""
        self.running = False
    
    def _handle_did_open(self, params: Dict) -> None:
        """Handle document open."""
        doc = params.get("textDocument", {})
        uri = doc.get("uri", "")
        text = doc.get("text", "")
        
        self.documents[uri] = text
        self._publish_diagnostics(uri, text)
    
    def _handle_did_change(self, params: Dict) -> None:
        """Handle document change."""
        doc = params.get("textDocument", {})
        uri = doc.get("uri", "")
        changes = params.get("contentChanges", [])
        
        if changes:
            text = changes[0].get("text", "")
            self.documents[uri] = text
            self._publish_diagnostics(uri, text)
    
    def _handle_did_save(self, params: Dict) -> None:
        """Handle document save."""
        doc = params.get("textDocument", {})
        uri = doc.get("uri", "")
        text = params.get("text", self.documents.get(uri, ""))
        
        self._publish_diagnostics(uri, text)
    
    def _handle_did_close(self, params: Dict) -> None:
        """Handle document close."""
        doc = params.get("textDocument", {})
        uri = doc.get("uri", "")
        
        if uri in self.documents:
            del self.documents[uri]
        
        # Clear diagnostics
        self._send_notification("textDocument/publishDiagnostics", {
            "uri": uri,
            "diagnostics": [],
        })
    
    def _handle_code_action(self, params: Dict) -> List[Dict]:
        """Handle code action request (quick fixes)."""
        uri = params.get("textDocument", {}).get("uri", "")
        diagnostics = params.get("context", {}).get("diagnostics", [])
        
        actions = []
        for diag in diagnostics:
            code = diag.get("code", "")
            if code.startswith("PNX"):
                # Get rule info
                try:
                    rule_info = get_all_rules().get(code)
                    if rule_info and rule_info.get("auto_fix"):
                        actions.append({
                            "title": f"Fix {code}",
                            "kind": "quickfix",
                            "diagnostics": [diag],
                            "isPreferred": True,
                        })
                except:
                    pass
        
        return actions
    
    def _handle_hover(self, params: Dict) -> Optional[Dict]:
        """Handle hover request."""
        uri = params.get("textDocument", {}).get("uri", "")
        position = params.get("position", {})
        
        text = self.documents.get(uri, "")
        line_num = position.get("line", 0)
        
        lines = text.split("\n")
        if line_num < len(lines):
            line = lines[line_num]
            
            # Check for PyNext imports
            if "from pynext" in line or "import pynext" in line:
                return {
                    "contents": {
                        "kind": "markdown",
                        "value": "**PyNext Import**\n\nPyNext is a Python web framework with SolidJS-style reactivity."
                    }
                }
            
            # Check for Signal
            if "Signal(" in line:
                return {
                    "contents": {
                        "kind": "markdown",
                        "value": "**Signal**\n\nA reactive value that triggers updates when changed.\n\n```python\ncount = Signal(0)\nprint(count())  # Read: 0\ncount.set(5)    # Write\n```"
                    }
                }
        
        return None
    
    # -------------------------------------------------------------------------
    # Diagnostics
    # -------------------------------------------------------------------------
    
    def _publish_diagnostics(self, uri: str, text: str) -> None:
        """Publish diagnostics for a document."""
        file_path = uri.replace("file://", "")
        
        # Only lint Python files
        if not file_path.endswith(".py"):
            return
        
        # Run linting
        from pynext.lint.rules import run_rules
        enabled = self.config.enabled_rules if self.config else None
        errors = run_rules(text, file_path, enabled)
        
        # Convert to LSP diagnostics
        diagnostics = []
        for error in errors:
            severity = {
                "error": 1,
                "warning": 2,
                "info": 3,
            }.get(error.severity, 2)
            
            diagnostics.append({
                "range": {
                    "start": {"line": max(0, error.line - 1), "character": error.column},
                    "end": {"line": max(0, error.line - 1), "character": error.column + 10},
                },
                "message": error.message,
                "severity": severity,
                "code": error.rule,
                "source": "pynext",
            })
        
        self._send_notification("textDocument/publishDiagnostics", {
            "uri": uri,
            "diagnostics": diagnostics,
        })


# =============================================================================
# Entry Point
# =============================================================================

def start_lsp_server() -> None:
    """Start the PyNext LSP server."""
    server = LSPServer()
    server.start()


if __name__ == "__main__":
    start_lsp_server()

