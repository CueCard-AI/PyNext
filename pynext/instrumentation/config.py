"""
Instrumentation Configuration

Define observability settings using decorators.
Auto-discovered from instrumentation.py.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union
from functools import wraps
from enum import Enum


class Exporter(str, Enum):
    """Supported telemetry exporters."""
    CONSOLE = "console"
    OTLP = "otlp"
    JAEGER = "jaeger"
    ZIPKIN = "zipkin"
    PROMETHEUS = "prometheus"


@dataclass
class InstrumentConfig:
    """
    Instrumentation configuration.
    
    Attributes:
        service_name: Name of the service for tracing
        service_version: Version string
        environment: Environment (development, staging, production)
        traces: Enable tracing
        metrics: Enable metrics
        logs: Enable structured logging
        exporter: Default exporter
        endpoint: Exporter endpoint URL
        sample_rate: Trace sampling rate (0.0 to 1.0)
        batch_size: Batch size for exports
        export_interval: Export interval in seconds
    """
    service_name: str = "pynext-app"
    service_version: str = "1.0.0"
    environment: str = "development"
    traces: bool = True
    metrics: bool = True
    logs: bool = True
    exporter: Exporter = Exporter.CONSOLE
    endpoint: Optional[str] = None
    sample_rate: float = 1.0
    batch_size: int = 512
    export_interval: int = 5
    
    # Additional attributes
    attributes: Dict[str, str] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InstrumentConfig":
        """Create config from dictionary."""
        # Handle exporter conversion
        if "exporter" in data and isinstance(data["exporter"], str):
            data["exporter"] = Exporter(data["exporter"])
        
        # Filter to known fields
        known_fields = {
            f.name for f in cls.__dataclass_fields__.values()
        }
        filtered = {k: v for k, v in data.items() if k in known_fields}
        
        return cls(**filtered)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "service_name": self.service_name,
            "service_version": self.service_version,
            "environment": self.environment,
            "traces": self.traces,
            "metrics": self.metrics,
            "logs": self.logs,
            "exporter": self.exporter.value,
            "endpoint": self.endpoint,
            "sample_rate": self.sample_rate,
            "attributes": self.attributes,
        }


# Global configuration
_config: Optional[InstrumentConfig] = None
_configured = False


def get_config() -> InstrumentConfig:
    """Get the current instrumentation configuration."""
    global _config
    if _config is None:
        _config = InstrumentConfig()
    return _config


def configure_instrumentation(config: InstrumentConfig):
    """Set the instrumentation configuration."""
    global _config, _configured
    _config = config
    _configured = True
    
    # Apply configuration
    _apply_config(config)


def _apply_config(config: InstrumentConfig):
    """Apply configuration to instrumentation systems."""
    from .traces import configure_tracer
    from .metrics import configure_metrics
    from .logs import configure_logging
    
    if config.traces:
        configure_tracer(config)
    
    if config.metrics:
        configure_metrics(config)
    
    if config.logs:
        configure_logging(config)


def instrument(
    traces: bool = True,
    metrics: bool = True,
    logs: bool = True,
) -> Callable:
    """
    Decorator to configure instrumentation.
    
    Apply to a function that returns configuration dict.
    The function is called once at startup.
    
    Args:
        traces: Enable tracing
        metrics: Enable metrics
        logs: Enable structured logging
        
    Returns:
        Decorator function
        
    Example:
        @instrument(traces=True, metrics=True, logs=True)
        def configure():
            return {
                "service_name": "my-app",
                "service_version": "1.0.0",
                "exporter": "otlp",
                "endpoint": "http://localhost:4317",
            }
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get config from function
            result = func(*args, **kwargs)
            
            if isinstance(result, dict):
                config = InstrumentConfig.from_dict({
                    **result,
                    "traces": traces,
                    "metrics": metrics,
                    "logs": logs,
                })
            elif isinstance(result, InstrumentConfig):
                config = result
                config.traces = traces
                config.metrics = metrics
                config.logs = logs
            else:
                config = InstrumentConfig(
                    traces=traces,
                    metrics=metrics,
                    logs=logs,
                )
            
            configure_instrumentation(config)
            return config
        
        # Store reference for auto-discovery
        wrapper._is_instrument_config = True
        wrapper._traces = traces
        wrapper._metrics = metrics
        wrapper._logs = logs
        
        return wrapper
    
    return decorator


def load_instrumentation(
    path: Optional[Path] = None,
    app_dir: Optional[Path] = None,
) -> Optional[InstrumentConfig]:
    """
    Load instrumentation from instrumentation.py.
    
    Discovers and calls the @instrument decorated function.
    
    Args:
        path: Direct path to instrumentation.py
        app_dir: App directory to search
        
    Returns:
        InstrumentConfig if found and loaded
    """
    import importlib.util
    
    # Find instrumentation.py
    if path is None:
        if app_dir is None:
            app_dir = Path.cwd()
        
        for loc in ["instrumentation.py", "app/instrumentation.py"]:
            candidate = app_dir / loc
            if candidate.exists():
                path = candidate
                break
    
    if path is None or not path.exists():
        return None
    
    # Import and find @instrument function
    spec = importlib.util.spec_from_file_location("instrumentation", path)
    if not spec or not spec.loader:
        return None
    
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # Find and call the instrument function
    for name in dir(module):
        obj = getattr(module, name)
        if callable(obj) and getattr(obj, "_is_instrument_config", False):
            return obj()
    
    return None


def auto_configure():
    """Auto-configure instrumentation from environment."""
    global _configured
    
    if _configured:
        return
    
    # Try loading from file
    config = load_instrumentation()
    if config:
        return
    
    # Use environment variables
    config = InstrumentConfig(
        service_name=os.environ.get("PYNEXT_SERVICE_NAME", "pynext-app"),
        service_version=os.environ.get("PYNEXT_SERVICE_VERSION", "1.0.0"),
        environment=os.environ.get("PYNEXT_ENV", "development"),
        exporter=Exporter(os.environ.get("PYNEXT_EXPORTER", "console")),
        endpoint=os.environ.get("PYNEXT_EXPORTER_ENDPOINT"),
    )
    
    configure_instrumentation(config)

