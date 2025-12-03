"""
PyNext Live Query - Detector Registry.

Manages available change detectors and selects the best one for each table.

Priority Order:
1. Supabase Realtime (priority 100) - If using Supabase
2. PostgreSQL LISTEN/NOTIFY (priority 50) - Direct PostgreSQL
3. Polling (priority 10) - Fallback for any database

Usage:
    registry = get_detector_registry()
    
    # Auto-select best detector for a table
    detector = await registry.get_detector("users")
    
    # Or use a specific detector type
    detector = await registry.get_detector("users", detection=DetectionStrategy.POSTGRES)
"""

from __future__ import annotations

import asyncio
import logging
from typing import Dict, List, Optional, Type, TYPE_CHECKING

from pynext.db.live.detection.base import ChangeDetector, ChangeCallback
from pynext.db.live.detection.postgres import PostgresNotifyDetector
from pynext.db.live.detection.supabase import SupabaseRealtimeDetector
from pynext.db.live.detection.polling import PollingDetector
from pynext.db.live.config import DetectionStrategy

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class DetectorRegistry:
    """
    Registry of available change detectors.
    
    Manages detector lifecycle and auto-selects the best detector
    based on availability and priority.
    
    This is a singleton - use get_detector_registry() to access.
    """
    
    def __init__(self):
        # All registered detector classes
        self._detector_classes: List[Type[ChangeDetector]] = [
            SupabaseRealtimeDetector,
            PostgresNotifyDetector,
            PollingDetector,
        ]
        
        # Active detector instances
        self._detectors: Dict[str, ChangeDetector] = {}  # name -> instance
        
        # Table -> detector mapping
        self._table_detectors: Dict[str, ChangeDetector] = {}
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
        
        # Availability cache
        self._availability_cache: Dict[str, bool] = {}
        self._cache_valid = False
    
    async def get_detector(
        self,
        table: str,
        detection: DetectionStrategy = DetectionStrategy.AUTO,
    ) -> ChangeDetector:
        """
        Get the best detector for a table.
        
        Args:
            table: Table name
            detection: Detection strategy (default: AUTO)
        
        Returns:
            The selected detector instance
        """
        async with self._lock:
            # Check if we already have a detector for this table
            if table in self._table_detectors:
                return self._table_detectors[table]
            
            # Select detector based on strategy
            if detection == DetectionStrategy.AUTO:
                detector = await self._auto_select_detector()
            elif detection == DetectionStrategy.SUPABASE:
                detector = await self._get_or_create(SupabaseRealtimeDetector)
            elif detection == DetectionStrategy.POSTGRES:
                detector = await self._get_or_create(PostgresNotifyDetector)
            else:  # POLLING
                detector = await self._get_or_create(PollingDetector)
            
            # Start if not running
            if not detector.is_running:
                await detector.start()
            
            # Register table
            self._table_detectors[table] = detector
            
            return detector
    
    async def _auto_select_detector(self) -> ChangeDetector:
        """
        Auto-select the best available detector.
        
        Checks availability in priority order and returns the first available.
        """
        # Refresh availability cache if needed
        if not self._cache_valid:
            await self._refresh_availability()
        
        # Sort by priority (highest first)
        for detector_class in sorted(
            self._detector_classes,
            key=lambda c: c.__new__(c).priority if hasattr(c.__new__(c), "priority") else 0,
            reverse=True,
        ):
            name = detector_class.__name__
            
            if self._availability_cache.get(name, False):
                return await self._get_or_create(detector_class)
        
        # Fallback to polling (always available)
        return await self._get_or_create(PollingDetector)
    
    async def _get_or_create(
        self,
        detector_class: Type[ChangeDetector],
    ) -> ChangeDetector:
        """Get an existing detector or create a new one."""
        name = detector_class.__name__
        
        if name not in self._detectors:
            self._detectors[name] = detector_class()
            logger.debug(f"Created detector: {name}")
        
        return self._detectors[name]
    
    async def _refresh_availability(self) -> None:
        """Check availability of all detectors."""
        self._availability_cache.clear()
        
        for detector_class in self._detector_classes:
            try:
                detector = detector_class()
                available = await detector.is_available()
                self._availability_cache[detector_class.__name__] = available
                
                logger.debug(
                    f"Detector {detector_class.__name__}: "
                    f"{'available' if available else 'not available'}"
                )
            except Exception as e:
                self._availability_cache[detector_class.__name__] = False
                logger.debug(f"Detector {detector_class.__name__} check failed: {e}")
        
        self._cache_valid = True
    
    def invalidate_cache(self) -> None:
        """Invalidate the availability cache."""
        self._cache_valid = False
    
    async def stop_all(self) -> None:
        """Stop all running detectors."""
        async with self._lock:
            for detector in self._detectors.values():
                if detector.is_running:
                    await detector.stop()
            
            self._detectors.clear()
            self._table_detectors.clear()
            self._cache_valid = False
    
    def get_detector_for_table(self, table: str) -> Optional[ChangeDetector]:
        """Get the detector currently assigned to a table."""
        return self._table_detectors.get(table)
    
    def get_all_detectors(self) -> Dict[str, ChangeDetector]:
        """Get all active detector instances."""
        return dict(self._detectors)
    
    def get_table_assignments(self) -> Dict[str, str]:
        """Get table -> detector name mapping."""
        return {
            table: detector.__class__.__name__
            for table, detector in self._table_detectors.items()
        }


# Global registry instance
_registry: Optional[DetectorRegistry] = None


def get_detector_registry() -> DetectorRegistry:
    """
    Get the global detector registry.
    
    Creates it if it doesn't exist.
    """
    global _registry
    if _registry is None:
        _registry = DetectorRegistry()
    return _registry


async def reset_detector_registry() -> None:
    """
    Reset the global detector registry.
    
    Stops all detectors and creates a fresh registry.
    Mainly for testing.
    """
    global _registry
    if _registry is not None:
        await _registry.stop_all()
    _registry = None

