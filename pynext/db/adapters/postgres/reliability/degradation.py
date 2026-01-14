"""
PostgreSQL Graceful Degradation.

This module provides intelligent degradation when the database is under stress,
implementing load shedding, automatic recovery, and observable state.

Why Graceful Degradation?

When a database is struggling, continuing normal operation can:
1. Make the problem worse (pile on more load)
2. Cause cascade failures (everything times out)
3. Create inconsistent user experience

Graceful degradation:
1. Detects stress early (before failure)
2. Sheds non-critical load
3. Protects critical operations
4. Recovers automatically

Degradation Levels:

    ┌──────────────────────────────────────────────────────────────┐
    │                    DEGRADATION LEVELS                         │
    │                                                               │
    │  NORMAL      │ All systems operational                       │
    │              │ No restrictions                               │
    │              ▼                                                │
    │  DEGRADED    │ Stress detected                               │
    │              │ Non-critical operations may be delayed        │
    │              ▼                                                │
    │  CRITICAL    │ Significant stress                            │
    │              │ Only essential operations proceed             │
    │              ▼                                                │
    │  EMERGENCY   │ System is failing                             │
    │              │ Reject all non-critical operations            │
    │                                                               │
    └──────────────────────────────────────────────────────────────┘

Triggers:

1. QUEUE_DEPTH: Too many requests waiting for connections
2. ERROR_RATE: Too many operations failing
3. LATENCY_P95: 95th percentile response time too high
4. CONNECTION_HEALTH: Too many unhealthy connections
5. REPLICA_LAG: Read replicas too far behind

Actions per Level:

- DEGRADED: Enable request queuing, extend timeouts
- CRITICAL: Reject BATCH priority, enable aggressive caching
- EMERGENCY: Reject LOW/BATCH priority, return 503 for reads

AI-Friendly Design:
- Clear trigger definitions
- Observable state and metrics
- Automatic recovery
- Easy to configure
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any, Callable, Dict, List, Optional, Set, TYPE_CHECKING

logger = logging.getLogger("pynext.db.postgres.degradation")


class DegradationLevel(IntEnum):
    """Degradation severity levels.
    
    Higher values = more severe degradation.
    """
    NORMAL = 0      # All systems go
    DEGRADED = 1    # Some stress detected
    CRITICAL = 2    # Significant problems
    EMERGENCY = 3   # System failing


class DegradationMetric(Enum):
    """Metrics that can trigger degradation.
    
    QUEUE_DEPTH: Requests waiting for connections
    ERROR_RATE: Fraction of operations failing
    LATENCY_P95: 95th percentile latency in ms
    LATENCY_P99: 99th percentile latency in ms
    CONNECTION_HEALTH: Fraction of healthy connections
    REPLICA_LAG: Maximum replica lag in seconds
    POOL_UTILIZATION: Pool capacity in use (0-1)
    """
    QUEUE_DEPTH = "queue_depth"
    ERROR_RATE = "error_rate"
    LATENCY_P95 = "latency_p95"
    LATENCY_P99 = "latency_p99"
    CONNECTION_HEALTH = "connection_health"
    REPLICA_LAG = "replica_lag"
    POOL_UTILIZATION = "pool_utilization"


class DegradationAction(Enum):
    """Actions to take at different degradation levels.
    
    LOG_WARNING: Log a warning message
    REJECT_BATCH: Reject BATCH priority requests
    REJECT_LOW: Reject LOW and BATCH priority requests
    REJECT_NORMAL: Reject NORMAL, LOW, BATCH (only CRITICAL/HIGH proceed)
    EXTEND_TIMEOUTS: Increase query timeouts
    REDUCE_POOL: Reduce pool size to conserve resources
    CIRCUIT_OPEN: Open the circuit breaker
    NOTIFY: Send notification (callback)
    """
    LOG_WARNING = "log_warning"
    REJECT_BATCH = "reject_batch"
    REJECT_LOW = "reject_low"
    REJECT_NORMAL = "reject_normal"
    EXTEND_TIMEOUTS = "extend_timeouts"
    REDUCE_POOL = "reduce_pool"
    CIRCUIT_OPEN = "circuit_open"
    NOTIFY = "notify"


@dataclass
class DegradationTrigger:
    """A trigger that can escalate degradation level.
    
    Attributes:
        metric: Which metric to monitor
        threshold: Value that triggers this level
        level: Degradation level to activate
        comparison: How to compare ("gt", "lt", "gte", "lte")
                   gt = greater than (trigger if metric > threshold)
                   lt = less than (trigger if metric < threshold)
    
    Example:
        # Trigger DEGRADED when queue > 100
        trigger = DegradationTrigger(
            metric=DegradationMetric.QUEUE_DEPTH,
            threshold=100,
            level=DegradationLevel.DEGRADED,
        )
        
        # Trigger CRITICAL when error rate > 10%
        trigger = DegradationTrigger(
            metric=DegradationMetric.ERROR_RATE,
            threshold=0.1,
            level=DegradationLevel.CRITICAL,
        )
    """
    metric: DegradationMetric
    threshold: float
    level: DegradationLevel
    comparison: str = "gt"  # "gt", "lt", "gte", "lte"
    
    def __post_init__(self) -> None:
        """Validate trigger."""
        if self.comparison not in ("gt", "lt", "gte", "lte"):
            raise ValueError(f"comparison must be gt/lt/gte/lte, got {self.comparison}")
    
    def is_triggered(self, value: float) -> bool:
        """Check if this trigger is activated.
        
        Args:
            value: Current metric value
        
        Returns:
            True if trigger condition is met
        """
        if self.comparison == "gt":
            return value > self.threshold
        elif self.comparison == "lt":
            return value < self.threshold
        elif self.comparison == "gte":
            return value >= self.threshold
        elif self.comparison == "lte":
            return value <= self.threshold
        return False


@dataclass
class DegradationConfig:
    """Configuration for graceful degradation.
    
    Attributes:
        triggers: List of triggers that escalate degradation
        actions: Actions to take at each level
        auto_recovery: Whether to automatically recover when metrics improve
        recovery_check_interval: Seconds between recovery checks
        recovery_delay: Seconds to wait before recovering (debounce)
        min_samples: Minimum samples before triggering
        notify_callback: Function to call on degradation changes
    
    Example:
        config = DegradationConfig(
            triggers=[
                DegradationTrigger(DegradationMetric.QUEUE_DEPTH, 100, DegradationLevel.DEGRADED),
                DegradationTrigger(DegradationMetric.QUEUE_DEPTH, 500, DegradationLevel.CRITICAL),
                DegradationTrigger(DegradationMetric.ERROR_RATE, 0.1, DegradationLevel.DEGRADED),
                DegradationTrigger(DegradationMetric.ERROR_RATE, 0.25, DegradationLevel.CRITICAL),
            ],
            actions={
                DegradationLevel.DEGRADED: [DegradationAction.LOG_WARNING],
                DegradationLevel.CRITICAL: [
                    DegradationAction.LOG_WARNING,
                    DegradationAction.REJECT_BATCH,
                ],
                DegradationLevel.EMERGENCY: [
                    DegradationAction.LOG_WARNING,
                    DegradationAction.REJECT_LOW,
                    DegradationAction.NOTIFY,
                ],
            },
        )
    """
    triggers: Optional[List[DegradationTrigger]] = None
    actions: Optional[Dict[DegradationLevel, List[DegradationAction]]] = None
    auto_recovery: bool = True
    recovery_check_interval: float = 10.0
    recovery_delay: float = 30.0
    min_samples: int = 5
    notify_callback: Optional[Callable[[DegradationLevel, DegradationLevel], None]] = None
    
    def __post_init__(self) -> None:
        """Set default triggers and actions if not provided."""
        # Only set defaults if None (not provided), not if empty list (explicit)
        if self.triggers is None:
            self.triggers = default_triggers()
        if self.actions is None:
            self.actions = default_actions()


@dataclass
class DegradationStats:
    """Statistics for degradation monitoring.
    
    Tracks level changes, time in each level, and trigger activations.
    """
    current_level: DegradationLevel = DegradationLevel.NORMAL
    level_changes: int = 0
    time_in_level: Dict[DegradationLevel, float] = field(default_factory=dict)
    last_level_change: float = 0.0
    triggered_by: Dict[str, int] = field(default_factory=dict)
    recovery_count: int = 0
    load_shed_count: int = 0
    
    # Current metrics
    current_metrics: Dict[str, float] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Initialize time tracking."""
        for level in DegradationLevel:
            if level not in self.time_in_level:
                self.time_in_level[level] = 0.0
        self.last_level_change = time.monotonic()
    
    def record_level_change(
        self,
        old_level: DegradationLevel,
        new_level: DegradationLevel,
    ) -> None:
        """Record a level transition."""
        now = time.monotonic()
        
        # Update time in old level
        self.time_in_level[old_level] += now - self.last_level_change
        
        self.current_level = new_level
        self.level_changes += 1
        self.last_level_change = now
        
        if new_level < old_level:
            self.recovery_count += 1
    
    def record_trigger(self, trigger: DegradationTrigger) -> None:
        """Record which trigger was activated."""
        key = f"{trigger.metric.value}:{trigger.level.name}"
        self.triggered_by[key] = self.triggered_by.get(key, 0) + 1
    
    def record_load_shed(self) -> None:
        """Record a load shedding event."""
        self.load_shed_count += 1
    
    def record_metric(self, metric: DegradationMetric, value: float) -> None:
        """Record current metric value."""
        self.current_metrics[metric.value] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/metrics."""
        return {
            "current_level": self.current_level.name,
            "level_changes": self.level_changes,
            "recovery_count": self.recovery_count,
            "load_shed_count": self.load_shed_count,
            "time_in_level": {
                level.name: seconds
                for level, seconds in self.time_in_level.items()
            },
            "triggered_by": self.triggered_by,
            "current_metrics": self.current_metrics,
        }


class DegradationError(Exception):
    """Raised when an operation is rejected due to degradation.
    
    Attributes:
        level: Current degradation level
        retry_after: Suggested seconds to wait before retrying
    """
    
    def __init__(
        self,
        message: str,
        level: DegradationLevel,
        retry_after: int,
    ):
        super().__init__(message)
        self.level = level
        self.retry_after = retry_after
    
    def __str__(self) -> str:
        return (
            f"DegradationError: {self.args[0]} "
            f"(level={self.level.name}, retry_after={self.retry_after}s)"
        )


class DegradationManager:
    """Manages graceful degradation for database operations.
    
    This class:
    - Monitors metrics from the pool/adapter
    - Evaluates triggers to determine degradation level
    - Executes actions based on current level
    - Handles automatic recovery
    
    Usage:
        manager = DegradationManager(config)
        await manager.start(get_metrics_callback)
        
        # Check before operations
        if manager.should_reject("batch"):
            raise DegradationError(...)
        
        # Get current state
        level = manager.current_level
        stats = manager.stats
    """
    
    def __init__(
        self,
        config: Optional[DegradationConfig] = None,
    ):
        """Initialize the degradation manager.
        
        Args:
            config: Degradation configuration
        """
        self._config = config or DegradationConfig()
        self._stats = DegradationStats()
        self._current_level = DegradationLevel.NORMAL
        self._last_normal_time = time.monotonic()
        self._running = False
        self._monitoring_task: Optional[asyncio.Task] = None
        self._get_metrics: Optional[Callable[[], Dict[str, float]]] = None
        
        # Track when recovery started
        self._recovery_started: Optional[float] = None
    
    @property
    def current_level(self) -> DegradationLevel:
        """Get the current degradation level."""
        return self._current_level
    
    @property
    def stats(self) -> DegradationStats:
        """Get degradation statistics."""
        return self._stats
    
    @property
    def is_degraded(self) -> bool:
        """Check if system is in any degraded state."""
        return self._current_level != DegradationLevel.NORMAL
    
    @property
    def is_critical(self) -> bool:
        """Check if system is in critical or emergency state."""
        return self._current_level >= DegradationLevel.CRITICAL
    
    @property
    def is_emergency(self) -> bool:
        """Check if system is in emergency state."""
        return self._current_level == DegradationLevel.EMERGENCY
    
    async def start(
        self,
        get_metrics: Callable[[], Dict[str, float]],
    ) -> None:
        """Start degradation monitoring.
        
        Args:
            get_metrics: Callback that returns current metrics.
                        Should return dict with keys like:
                        - queue_depth: int
                        - error_rate: float (0-1)
                        - latency_p95: float (ms)
                        - connection_health: float (0-1)
                        - replica_lag: float (seconds)
                        - pool_utilization: float (0-1)
        """
        if self._running:
            return
        
        self._get_metrics = get_metrics
        self._running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info("Degradation monitoring started")
    
    async def stop(self) -> None:
        """Stop degradation monitoring."""
        if not self._running:
            return
        
        self._running = False
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Degradation monitoring stopped")
    
    async def _monitoring_loop(self) -> None:
        """Background task that checks metrics and updates level."""
        while self._running:
            try:
                await self._check_and_update()
            except Exception as e:
                logger.error(f"Error in degradation monitoring: {e}")
            
            await asyncio.sleep(self._config.recovery_check_interval)
    
    async def _check_and_update(self) -> None:
        """Check current metrics and update degradation level."""
        if not self._get_metrics:
            return
        
        # Get current metrics
        metrics = self._get_metrics()
        
        # Record metrics
        for metric_name, value in metrics.items():
            try:
                metric = DegradationMetric(metric_name)
                self._stats.record_metric(metric, value)
            except ValueError:
                pass  # Unknown metric, ignore
        
        # Evaluate triggers
        new_level = self._evaluate_triggers(metrics)
        
        # Handle level change
        if new_level != self._current_level:
            await self._transition_to(new_level, metrics)
    
    def _evaluate_triggers(self, metrics: Dict[str, float]) -> DegradationLevel:
        """Evaluate triggers and determine degradation level.
        
        Args:
            metrics: Current metric values
        
        Returns:
            The appropriate degradation level
        """
        highest_level = DegradationLevel.NORMAL
        
        for trigger in self._config.triggers:
            metric_name = trigger.metric.value
            
            if metric_name not in metrics:
                continue
            
            value = metrics[metric_name]
            
            if trigger.is_triggered(value):
                if trigger.level > highest_level:
                    highest_level = trigger.level
                    self._stats.record_trigger(trigger)
        
        return highest_level
    
    async def _transition_to(
        self,
        new_level: DegradationLevel,
        metrics: Dict[str, float],
    ) -> None:
        """Transition to a new degradation level.
        
        Args:
            new_level: Target degradation level
            metrics: Current metrics (for logging)
        """
        old_level = self._current_level
        
        # Check recovery delay
        if new_level < old_level:
            # Recovery - check if we should delay
            if self._config.auto_recovery:
                if self._recovery_started is None:
                    self._recovery_started = time.monotonic()
                    logger.info(
                        f"Recovery possible: {old_level.name} → {new_level.name} "
                        f"(waiting {self._config.recovery_delay}s)"
                    )
                    return
                
                elapsed = time.monotonic() - self._recovery_started
                if elapsed < self._config.recovery_delay:
                    # Still waiting
                    return
            
            # Recovery confirmed
            self._recovery_started = None
            logger.info(
                f"Recovering from {old_level.name} to {new_level.name}"
            )
        else:
            # Escalating - no delay
            self._recovery_started = None
            logger.warning(
                f"Degradation: {old_level.name} → {new_level.name} "
                f"(metrics: {metrics})"
            )
        
        # Update level
        self._current_level = new_level
        self._stats.record_level_change(old_level, new_level)
        
        if new_level == DegradationLevel.NORMAL:
            self._last_normal_time = time.monotonic()
        
        # Execute actions for new level
        await self._execute_actions(new_level)
        
        # Notify callback
        if self._config.notify_callback:
            try:
                self._config.notify_callback(old_level, new_level)
            except Exception as e:
                logger.error(f"Notification callback failed: {e}")
    
    async def _execute_actions(self, level: DegradationLevel) -> None:
        """Execute actions for a degradation level.
        
        Args:
            level: Current degradation level
        """
        actions = self._config.actions.get(level, [])
        
        for action in actions:
            try:
                if action == DegradationAction.LOG_WARNING:
                    logger.warning(f"Degradation level: {level.name}")
                elif action == DegradationAction.NOTIFY:
                    # Notification handled via callback
                    pass
                # Other actions would be implemented by the adapter
            except Exception as e:
                logger.error(f"Action {action.value} failed: {e}")
    
    def should_shed_load(self, priority: str = "normal") -> bool:
        """Check if a request should be rejected.
        
        Args:
            priority: Request priority (critical, high, normal, low, batch)
        
        Returns:
            True if request should be rejected
        """
        level = self._current_level
        
        if level == DegradationLevel.NORMAL:
            return False
        
        actions = self._config.actions.get(level, [])
        
        if DegradationAction.REJECT_NORMAL in actions:
            if priority in ("normal", "low", "batch"):
                self._stats.record_load_shed()
                return True
        
        if DegradationAction.REJECT_LOW in actions:
            if priority in ("low", "batch"):
                self._stats.record_load_shed()
                return True
        
        if DegradationAction.REJECT_BATCH in actions:
            if priority == "batch":
                self._stats.record_load_shed()
                return True
        
        return False
    
    def get_retry_after(self) -> int:
        """Get suggested retry delay in seconds.
        
        Returns different values based on degradation level.
        """
        level = self._current_level
        
        if level == DegradationLevel.NORMAL:
            return 0
        elif level == DegradationLevel.DEGRADED:
            return 5
        elif level == DegradationLevel.CRITICAL:
            return 15
        else:  # EMERGENCY
            return 30
    
    def check_and_reject(self, priority: str = "normal") -> None:
        """Check if request should be rejected, raise if so.
        
        Args:
            priority: Request priority
        
        Raises:
            DegradationError: If request should be rejected
        """
        if self.should_shed_load(priority):
            raise DegradationError(
                f"Request rejected due to {self._current_level.name} degradation",
                level=self._current_level,
                retry_after=self.get_retry_after(),
            )
    
    def force_level(self, level: DegradationLevel) -> None:
        """Force a specific degradation level.
        
        Useful for testing or manual intervention.
        """
        old_level = self._current_level
        self._current_level = level
        self._stats.record_level_change(old_level, level)
        logger.warning(f"Degradation level forced: {old_level.name} → {level.name}")
        
        # Call notify callback if configured
        if self._config.notify_callback is not None and old_level != level:
            self._config.notify_callback(old_level, level)
    
    def reset(self) -> None:
        """Reset to NORMAL level."""
        if self._current_level != DegradationLevel.NORMAL:
            old_level = self._current_level
            self._current_level = DegradationLevel.NORMAL
            self._stats.record_level_change(old_level, DegradationLevel.NORMAL)
            self._last_normal_time = time.monotonic()
            logger.info(f"Degradation reset: {old_level.name} → NORMAL")


# Default configurations

def default_triggers() -> List[DegradationTrigger]:
    """Get sensible default triggers.
    
    Returns:
        List of default triggers for each level
    """
    return [
        # Queue depth triggers
        DegradationTrigger(DegradationMetric.QUEUE_DEPTH, 100, DegradationLevel.DEGRADED),
        DegradationTrigger(DegradationMetric.QUEUE_DEPTH, 500, DegradationLevel.CRITICAL),
        DegradationTrigger(DegradationMetric.QUEUE_DEPTH, 1000, DegradationLevel.EMERGENCY),
        
        # Error rate triggers
        DegradationTrigger(DegradationMetric.ERROR_RATE, 0.05, DegradationLevel.DEGRADED),
        DegradationTrigger(DegradationMetric.ERROR_RATE, 0.15, DegradationLevel.CRITICAL),
        DegradationTrigger(DegradationMetric.ERROR_RATE, 0.30, DegradationLevel.EMERGENCY),
        
        # Latency triggers (p95 in ms)
        DegradationTrigger(DegradationMetric.LATENCY_P95, 1000, DegradationLevel.DEGRADED),
        DegradationTrigger(DegradationMetric.LATENCY_P95, 5000, DegradationLevel.CRITICAL),
        DegradationTrigger(DegradationMetric.LATENCY_P95, 10000, DegradationLevel.EMERGENCY),
        
        # Pool utilization triggers
        DegradationTrigger(DegradationMetric.POOL_UTILIZATION, 0.8, DegradationLevel.DEGRADED),
        DegradationTrigger(DegradationMetric.POOL_UTILIZATION, 0.95, DegradationLevel.CRITICAL),
    ]


def default_actions() -> Dict[DegradationLevel, List[DegradationAction]]:
    """Get sensible default actions for each level.
    
    Returns:
        Dict mapping levels to actions
    """
    return {
        DegradationLevel.DEGRADED: [
            DegradationAction.LOG_WARNING,
        ],
        DegradationLevel.CRITICAL: [
            DegradationAction.LOG_WARNING,
            DegradationAction.REJECT_BATCH,
        ],
        DegradationLevel.EMERGENCY: [
            DegradationAction.LOG_WARNING,
            DegradationAction.REJECT_LOW,
            DegradationAction.NOTIFY,
        ],
    }


def strict_config() -> DegradationConfig:
    """Create a strict degradation config (triggers quickly).
    
    Good for critical production systems.
    """
    return DegradationConfig(
        triggers=[
            DegradationTrigger(DegradationMetric.QUEUE_DEPTH, 50, DegradationLevel.DEGRADED),
            DegradationTrigger(DegradationMetric.QUEUE_DEPTH, 200, DegradationLevel.CRITICAL),
            DegradationTrigger(DegradationMetric.ERROR_RATE, 0.02, DegradationLevel.DEGRADED),
            DegradationTrigger(DegradationMetric.ERROR_RATE, 0.10, DegradationLevel.CRITICAL),
        ],
        recovery_delay=60.0,  # Longer recovery delay
    )


def lenient_config() -> DegradationConfig:
    """Create a lenient degradation config (triggers slowly).
    
    Good for development or tolerant systems.
    """
    return DegradationConfig(
        triggers=[
            DegradationTrigger(DegradationMetric.QUEUE_DEPTH, 500, DegradationLevel.DEGRADED),
            DegradationTrigger(DegradationMetric.QUEUE_DEPTH, 2000, DegradationLevel.CRITICAL),
            DegradationTrigger(DegradationMetric.ERROR_RATE, 0.20, DegradationLevel.DEGRADED),
            DegradationTrigger(DegradationMetric.ERROR_RATE, 0.50, DegradationLevel.CRITICAL),
        ],
        recovery_delay=10.0,  # Faster recovery
    )


def disabled_config() -> DegradationConfig:
    """Create a disabled degradation config.
    
    No degradation, no load shedding.
    """
    return DegradationConfig(
        triggers=[],
        actions={},
        auto_recovery=False,
    )

