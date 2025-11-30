"""
Structured Logging - JSON Logs with Context

Simple, structured logging that integrates with
traces and provides consistent output.
"""

from __future__ import annotations

import json
import logging
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TextIO, Union
from enum import Enum


class LogLevel(str, Enum):
    """Log levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class LogRecord:
    """
    A structured log record.
    
    Attributes:
        level: Log level
        message: Log message
        timestamp: Unix timestamp
        attributes: Additional key-value data
        trace_id: Associated trace ID
        span_id: Associated span ID
    """
    level: LogLevel
    message: str
    timestamp: float = field(default_factory=time.time)
    attributes: Dict[str, Any] = field(default_factory=dict)
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "level": self.level.value,
            "message": self.message,
            "timestamp": self.timestamp,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            **self.attributes,
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


class Logger:
    """
    Structured logger with context support.
    
    Example:
        log = Logger("my-app")
        log.info("User logged in", user_id=123, ip="1.2.3.4")
        
        # With context
        with log.context(request_id="abc123"):
            log.info("Processing request")
    """
    
    def __init__(
        self,
        name: str = "pynext",
        level: LogLevel = LogLevel.INFO,
        output: Optional[TextIO] = None,
    ):
        self.name = name
        self.level = level
        self.output = output or sys.stderr
        self._context: Dict[str, Any] = {}
        self._handlers: List[LogHandler] = []
        
        # Add default handler
        self._handlers.append(ConsoleHandler(output=self.output))
    
    def _should_log(self, level: LogLevel) -> bool:
        """Check if level should be logged."""
        levels = list(LogLevel)
        return levels.index(level) >= levels.index(self.level)
    
    def _create_record(
        self,
        level: LogLevel,
        message: str,
        **kwargs,
    ) -> LogRecord:
        """Create a log record."""
        # Get trace context
        from .traces import get_current_span
        
        span = get_current_span()
        trace_id = span.context.trace_id if span else None
        span_id = span.context.span_id if span else None
        
        # Merge context and kwargs
        attributes = {
            "logger": self.name,
            **self._context,
            **kwargs,
        }
        
        return LogRecord(
            level=level,
            message=message,
            attributes=attributes,
            trace_id=trace_id,
            span_id=span_id,
        )
    
    def _log(self, level: LogLevel, message: str, **kwargs):
        """Log a message."""
        if not self._should_log(level):
            return
        
        record = self._create_record(level, message, **kwargs)
        
        for handler in self._handlers:
            handler.emit(record)
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log(LogLevel.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._log(LogLevel.WARNING, message, **kwargs)
    
    def warn(self, message: str, **kwargs):
        """Alias for warning."""
        self.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self._log(LogLevel.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self._log(LogLevel.CRITICAL, message, **kwargs)
    
    def exception(self, message: str, exc: Optional[Exception] = None, **kwargs):
        """Log exception with traceback."""
        import traceback
        
        if exc:
            kwargs["exception"] = {
                "type": type(exc).__name__,
                "message": str(exc),
                "traceback": traceback.format_exc(),
            }
        
        self._log(LogLevel.ERROR, message, **kwargs)
    
    def context(self, **kwargs) -> "_LogContext":
        """
        Create a context with additional attributes.
        
        Returns:
            Context manager
        """
        return _LogContext(self, kwargs)
    
    def with_context(self, **kwargs) -> "Logger":
        """
        Create a new logger with additional context.
        
        Returns:
            New Logger instance with context
        """
        new_logger = Logger(
            name=self.name,
            level=self.level,
            output=self.output,
        )
        new_logger._context = {**self._context, **kwargs}
        new_logger._handlers = self._handlers
        return new_logger
    
    def add_handler(self, handler: "LogHandler"):
        """Add a log handler."""
        self._handlers.append(handler)


class _LogContext:
    """Context manager for temporary log context."""
    
    def __init__(self, logger: Logger, context: Dict[str, Any]):
        self.logger = logger
        self.context = context
        self._old_context: Dict[str, Any] = {}
    
    def __enter__(self):
        self._old_context = self.logger._context.copy()
        self.logger._context.update(self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger._context = self._old_context
        return False


class LogHandler:
    """Base class for log handlers."""
    
    def emit(self, record: LogRecord):
        """Emit a log record."""
        raise NotImplementedError


class ConsoleHandler(LogHandler):
    """Handler that writes to console."""
    
    COLORS = {
        LogLevel.DEBUG: "\033[36m",    # Cyan
        LogLevel.INFO: "\033[32m",     # Green
        LogLevel.WARNING: "\033[33m",  # Yellow
        LogLevel.ERROR: "\033[31m",    # Red
        LogLevel.CRITICAL: "\033[35m", # Magenta
    }
    RESET = "\033[0m"
    
    def __init__(
        self,
        output: Optional[TextIO] = None,
        json_format: bool = True,
        colors: bool = True,
    ):
        self.output = output or sys.stderr
        self.json_format = json_format
        self.colors = colors and hasattr(self.output, "isatty") and self.output.isatty()
    
    def emit(self, record: LogRecord):
        """Write log record to output."""
        if self.json_format:
            line = record.to_json()
        else:
            line = self._format_text(record)
        
        if self.colors:
            color = self.COLORS.get(record.level, "")
            line = f"{color}{line}{self.RESET}"
        
        print(line, file=self.output)
    
    def _format_text(self, record: LogRecord) -> str:
        """Format as human-readable text."""
        ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(record.timestamp))
        level = record.level.value.upper().ljust(8)
        
        attrs = " ".join(
            f"{k}={v}"
            for k, v in record.attributes.items()
            if k != "logger"
        )
        
        if attrs:
            return f"[{ts}] {level} {record.message} | {attrs}"
        return f"[{ts}] {level} {record.message}"


class FileHandler(LogHandler):
    """Handler that writes to a file."""
    
    def __init__(self, path: str):
        self.path = path
        self._file: Optional[TextIO] = None
    
    def emit(self, record: LogRecord):
        """Write log record to file."""
        if self._file is None:
            self._file = open(self.path, "a", encoding="utf-8")
        
        self._file.write(record.to_json() + "\n")
        self._file.flush()
    
    def close(self):
        """Close the file."""
        if self._file:
            self._file.close()
            self._file = None


# Global logger instance
_logger: Optional[Logger] = None


def get_logger(name: str = "pynext") -> Logger:
    """Get or create a logger."""
    global _logger
    if _logger is None:
        _logger = Logger(name)
    return _logger


# Convenience access to default logger methods
class _LogProxy:
    """Proxy object for convenient logging."""
    
    def __getattr__(self, name: str):
        logger = get_logger()
        return getattr(logger, name)


log = _LogProxy()


def configure_logging(config):
    """Configure logging with InstrumentConfig."""
    global _logger
    
    level = LogLevel.DEBUG if config.environment == "development" else LogLevel.INFO
    _logger = Logger(
        name=config.service_name,
        level=level,
    )

