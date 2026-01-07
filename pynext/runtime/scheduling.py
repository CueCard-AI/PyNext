"""
PyNext Runtime - Scheduling APIs (Python implementation)

This module provides scheduling APIs for Python async code.
The JavaScript equivalent is in scheduling.js.

These utilities simulate browser scheduling APIs in Python.
"""

import asyncio
import time
from typing import Any, Callable, Dict, Optional
from dataclasses import dataclass


# Global state for tracking scheduled callbacks
_next_handle = 1
_pending_callbacks: Dict[int, asyncio.Task] = {}


@dataclass
class IdleDeadline:
    """Represents the deadline for an idle callback."""
    
    _start_time: float
    _timeout: float
    didTimeout: bool = False
    
    def timeRemaining(self) -> float:
        """Returns milliseconds remaining in the idle period."""
        elapsed = (time.time() - self._start_time) * 1000
        remaining = self._timeout - elapsed
        return max(0, remaining)


def queueMicrotask(callback: Callable[[], None]) -> None:
    """
    Schedule a callback to run as a microtask.
    
    In Python, this uses asyncio to schedule the callback
    to run after the current task completes.
    """
    try:
        loop = asyncio.get_running_loop()
        loop.call_soon(callback)
    except RuntimeError:
        # No running loop, run immediately
        callback()


def requestIdleCallback(
    callback: Callable[[IdleDeadline], None],
    options: Optional[Dict[str, Any]] = None
) -> int:
    """
    Schedule a callback to run during idle time.
    
    Returns a handle that can be used to cancel the callback.
    """
    global _next_handle
    
    options = options or {}
    timeout = options.get('timeout', 5000)  # Default 5 second timeout
    
    handle = _next_handle
    _next_handle += 1
    
    async def run_callback():
        start_time = time.time()
        deadline = IdleDeadline(
            _start_time=start_time,
            _timeout=timeout,
            didTimeout=False
        )
        
        # Simulate idle time by yielding control
        await asyncio.sleep(0)
        
        if handle in _pending_callbacks:
            try:
                callback(deadline)
            finally:
                _pending_callbacks.pop(handle, None)
    
    try:
        loop = asyncio.get_running_loop()
        task = loop.create_task(run_callback())
        _pending_callbacks[handle] = task
    except RuntimeError:
        # No running loop, run synchronously after delay
        deadline = IdleDeadline(
            _start_time=time.time(),
            _timeout=timeout,
            didTimeout=True
        )
        callback(deadline)
    
    return handle


def cancelIdleCallback(handle: int) -> None:
    """
    Cancel a scheduled idle callback.
    """
    task = _pending_callbacks.pop(handle, None)
    if task and not task.done():
        task.cancel()


def requestAnimationFrame(callback: Callable[[float], None]) -> int:
    """
    Schedule a callback to run before the next repaint.
    
    In Python, this simulates ~60fps timing (16.67ms).
    Returns a handle that can be used to cancel the callback.
    """
    global _next_handle
    
    handle = _next_handle
    _next_handle += 1
    
    async def run_callback():
        # Simulate frame timing
        await asyncio.sleep(0.016)  # ~60fps
        
        if handle in _pending_callbacks:
            try:
                timestamp = time.time() * 1000  # DOMHighResTimeStamp (ms)
                callback(timestamp)
            finally:
                _pending_callbacks.pop(handle, None)
    
    try:
        loop = asyncio.get_running_loop()
        task = loop.create_task(run_callback())
        _pending_callbacks[handle] = task
    except RuntimeError:
        # No running loop, run synchronously
        timestamp = time.time() * 1000
        callback(timestamp)
    
    return handle


def cancelAnimationFrame(handle: int) -> None:
    """
    Cancel a scheduled animation frame callback.
    """
    task = _pending_callbacks.pop(handle, None)
    if task and not task.done():
        task.cancel()


__all__ = [
    'queueMicrotask',
    'requestIdleCallback',
    'cancelIdleCallback',
    'requestAnimationFrame',
    'cancelAnimationFrame',
    'IdleDeadline',
]

