"""
PyNext Live Query Change Detection.

Monitors the database for changes and notifies subscribers.

Detection Strategies (in priority order):
1. Supabase Realtime - Instant, uses Supabase's built-in realtime
2. PostgreSQL LISTEN/NOTIFY - Instant, uses PostgreSQL triggers
3. Polling - Fallback, configurable interval

Usage:
    # Auto-detection (recommended)
    from pynext.db.live import DetectorRegistry
    
    registry = get_detector_registry()
    detector = await registry.get_detector("users")  # Best available
    
    # Manual selection
    from pynext.db.live.detection import PostgresNotifyDetector
    
    detector = PostgresNotifyDetector()
    await detector.start("users", callback)
"""

from pynext.db.live.detection.base import (
    ChangeDetector,
    ChangeEvent,
    ChangeType,
)

from pynext.db.live.detection.registry import (
    DetectorRegistry,
    get_detector_registry,
)

__all__ = [
    "ChangeDetector",
    "ChangeEvent",
    "ChangeType",
    "DetectorRegistry",
    "get_detector_registry",
]

