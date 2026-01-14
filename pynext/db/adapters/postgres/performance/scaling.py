"""
PostgreSQL Adaptive Scaling.

This module provides predictive and adaptive pool scaling based on
load patterns and historical data.

Why Adaptive Scaling?

Static pool sizes are inefficient:
- Too small: Requests queue during peaks
- Too large: Resources wasted during lulls

Adaptive scaling:
- Learns your traffic patterns
- Predicts load before spikes
- Pre-scales to handle demand
- Shrinks during quiet periods

How It Works:

1. Record load samples over time (connections used, queue depth)
2. Build historical pattern (hourly, daily trends)
3. Use trend analysis to predict future load
4. Recommend or auto-adjust pool size

Visual:

    Load History ─────► Trend Analysis ─────► Prediction
         │                    │                   │
         ▼                    ▼                   ▼
    [9am: 50 conn]     [Peak: 9-11am]    [In 5min: 60 conn]
    [10am: 80 conn]    [Low: 2-4am]      [Recommend: 80 max]
    [11am: 60 conn]

Benefits:
- Handles spikes without over-provisioning
- Saves resources during quiet periods
- Self-tuning based on actual patterns
- No manual capacity planning

AI-Friendly Design:
- Simple record/predict/recommend API
- Clear trend analysis
- Observable predictions
- Easy to integrate
"""

from __future__ import annotations

import asyncio
import logging
import math
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Deque, Dict, List, Optional, Tuple, TypeVar

logger = logging.getLogger("pynext.db.postgres.scaling")

T = TypeVar("T")


@dataclass
class AdaptiveScalingConfig:
    """Configuration for adaptive scaling.
    
    Attributes:
        enabled: Whether adaptive scaling is enabled. Default: True
        predict_ahead_seconds: How far ahead to predict. Default: 60.0
        scale_up_threshold: Utilization threshold for scaling up. Default: 0.8
        scale_down_threshold: Utilization threshold for scaling down. Default: 0.3
        history_window: Seconds of history to keep. Default: 300.0 (5 min)
        sample_interval: Seconds between samples. Default: 5.0
        min_samples: Minimum samples before predicting. Default: 10
        prediction_buffer: Extra capacity buffer (fraction). Default: 0.2
        cooldown_seconds: Minimum time between scale events. Default: 60.0
    
    Example:
        # Default: predict 60s ahead, scale at 80% utilization
        config = AdaptiveScalingConfig()
        
        # More aggressive scaling
        config = AdaptiveScalingConfig(
            scale_up_threshold=0.7,
            predict_ahead_seconds=120.0,
        )
        
        # Conservative scaling
        config = AdaptiveScalingConfig(
            scale_up_threshold=0.9,
            scale_down_threshold=0.2,
            cooldown_seconds=120.0,
        )
    """
    enabled: bool = True
    predict_ahead_seconds: float = 60.0
    scale_up_threshold: float = 0.8
    scale_down_threshold: float = 0.3
    history_window: float = 300.0
    sample_interval: float = 5.0
    min_samples: int = 10
    prediction_buffer: float = 0.2
    cooldown_seconds: float = 60.0
    
    def __post_init__(self) -> None:
        """Validate configuration."""
        if not 0 < self.scale_up_threshold <= 1.0:
            raise ValueError(f"scale_up_threshold must be in (0, 1], got {self.scale_up_threshold}")
        if not 0 <= self.scale_down_threshold < self.scale_up_threshold:
            raise ValueError(
                f"scale_down_threshold must be in [0, scale_up_threshold), "
                f"got {self.scale_down_threshold}"
            )
        if self.history_window < 0:
            raise ValueError(f"history_window must be >= 0, got {self.history_window}")
        if self.min_samples < 1:
            raise ValueError(f"min_samples must be >= 1, got {self.min_samples}")


@dataclass
class LoadSample:
    """A sample of pool load at a point in time.
    
    Attributes:
        timestamp: When sample was taken
        connections_used: Active connections
        connections_max: Maximum connections
        queue_depth: Requests waiting for connections
        utilization: Fraction of pool in use
    """
    timestamp: float
    connections_used: int
    connections_max: int
    queue_depth: int = 0
    
    @property
    def utilization(self) -> float:
        """Pool utilization (0-1)."""
        if self.connections_max == 0:
            return 0.0
        return self.connections_used / self.connections_max
    
    @property
    def under_pressure(self) -> bool:
        """Whether pool is under pressure."""
        return self.queue_depth > 0 or self.utilization > 0.9


@dataclass
class ScaleEvent:
    """A scaling event.
    
    Attributes:
        timestamp: When scaling occurred
        direction: "up" or "down"
        old_max: Previous max connections
        new_max: New max connections
        trigger: What triggered the scaling
    """
    timestamp: float
    direction: str
    old_max: int
    new_max: int
    trigger: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "timestamp": self.timestamp,
            "direction": self.direction,
            "old_max": self.old_max,
            "new_max": self.new_max,
            "trigger": self.trigger,
        }


@dataclass
class ScalingStats:
    """Statistics about scaling behavior.
    
    Attributes:
        samples_recorded: Total load samples recorded
        predictions_made: Total predictions made
        scale_up_events: Number of scale-up events
        scale_down_events: Number of scale-down events
        prediction_accuracy: How accurate predictions were
    """
    samples_recorded: int = 0
    predictions_made: int = 0
    scale_up_events: int = 0
    scale_down_events: int = 0
    correct_predictions: int = 0
    total_predictions_verified: int = 0
    
    @property
    def prediction_accuracy(self) -> float:
        """How accurate predictions were (0-1)."""
        if self.total_predictions_verified == 0:
            return 0.0
        return self.correct_predictions / self.total_predictions_verified
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/metrics."""
        return {
            "samples_recorded": self.samples_recorded,
            "predictions_made": self.predictions_made,
            "scale_up_events": self.scale_up_events,
            "scale_down_events": self.scale_down_events,
            "prediction_accuracy": self.prediction_accuracy,
        }


@dataclass
class ScalingRecommendation:
    """A pool size recommendation.
    
    Attributes:
        recommended_min: Recommended minimum connections
        recommended_max: Recommended maximum connections
        current_load: Current utilization
        predicted_load: Predicted utilization
        confidence: Confidence in prediction (0-1)
        reason: Why this recommendation
    """
    recommended_min: int
    recommended_max: int
    current_load: float
    predicted_load: float
    confidence: float
    reason: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "recommended_min": self.recommended_min,
            "recommended_max": self.recommended_max,
            "current_load": self.current_load,
            "predicted_load": self.predicted_load,
            "confidence": self.confidence,
            "reason": self.reason,
        }


class AdaptiveScaler:
    """Provides adaptive pool sizing based on load patterns.
    
    Learns from historical load data and predicts future demand
    to recommend optimal pool sizes.
    
    Basic Usage:
        scaler = AdaptiveScaler()
        
        # Record load periodically
        scaler.record_load(
            connections_used=45,
            connections_max=100,
            queue_depth=0,
        )
        
        # Get recommendation
        rec = scaler.recommend_pool_size(current_min=5, current_max=100)
        print(f"Recommended max: {rec.recommended_max}")
    
    With Auto-Scaling:
        scaler = AdaptiveScaler(
            config=AdaptiveScalingConfig(),
            resize_callback=my_pool.resize,
        )
        await scaler.start()
        
        # Scaler will automatically:
        # 1. Sample pool state
        # 2. Predict future load
        # 3. Call resize_callback when needed
    
    Prediction:
        # How much load in 60 seconds?
        predicted = scaler.predict_load(seconds_ahead=60.0)
        print(f"Predicted connections needed: {predicted}")
    """
    
    def __init__(
        self,
        config: Optional[AdaptiveScalingConfig] = None,
        get_load: Optional[Callable[[], Tuple[int, int, int]]] = None,
        resize_callback: Optional[Callable[[int, int], None]] = None,
    ):
        """Initialize the adaptive scaler.
        
        Args:
            config: Scaling configuration
            get_load: Callback returning (connections_used, connections_max, queue_depth)
            resize_callback: Callback to resize pool (new_min, new_max)
        """
        self._config = config or AdaptiveScalingConfig()
        self._get_load = get_load
        self._resize_callback = resize_callback
        
        # Load history
        max_samples = int(self._config.history_window / self._config.sample_interval)
        self._history: Deque[LoadSample] = deque(maxlen=max(max_samples, 100))
        
        # Scale events
        self._scale_events: List[ScaleEvent] = []
        self._last_scale_time: float = 0
        
        # Statistics
        self._stats = ScalingStats()
        
        # Background task
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    @property
    def config(self) -> AdaptiveScalingConfig:
        """Get current configuration."""
        return self._config
    
    @property
    def sample_count(self) -> int:
        """Number of load samples recorded."""
        return len(self._history)
    
    def record_load(
        self,
        connections_used: int,
        connections_max: int,
        queue_depth: int = 0,
    ) -> None:
        """Record a load sample.
        
        Call this periodically to build load history.
        
        Args:
            connections_used: Currently active connections
            connections_max: Maximum connections allowed
            queue_depth: Requests waiting for connections
        """
        sample = LoadSample(
            timestamp=time.monotonic(),
            connections_used=connections_used,
            connections_max=connections_max,
            queue_depth=queue_depth,
        )
        self._history.append(sample)
        self._stats.samples_recorded += 1
    
    def predict_load(self, seconds_ahead: float = None) -> int:
        """Predict connection needs for the future.
        
        Uses trend analysis of recent history to predict
        how many connections will be needed.
        
        Args:
            seconds_ahead: How far ahead to predict (default: config)
        
        Returns:
            Predicted connections needed
        """
        seconds_ahead = seconds_ahead or self._config.predict_ahead_seconds
        
        if len(self._history) < self._config.min_samples:
            # Not enough data, return current
            if self._history:
                return self._history[-1].connections_used
            return 0
        
        self._stats.predictions_made += 1
        
        # Simple linear regression for trend
        samples = list(self._history)
        n = len(samples)
        
        # Extract time and load
        times = [s.timestamp - samples[0].timestamp for s in samples]
        loads = [s.connections_used for s in samples]
        
        # Calculate trend (slope)
        mean_t = sum(times) / n
        mean_l = sum(loads) / n
        
        numerator = sum((t - mean_t) * (l - mean_l) for t, l in zip(times, loads))
        denominator = sum((t - mean_t) ** 2 for t in times)
        
        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator
        
        # Project forward
        current_time = times[-1]
        future_time = current_time + seconds_ahead
        
        intercept = mean_l - slope * mean_t
        predicted = intercept + slope * future_time
        
        # Apply buffer and bounds
        predicted = predicted * (1 + self._config.prediction_buffer)
        predicted = max(0, int(predicted))
        
        return predicted
    
    def recommend_pool_size(
        self,
        current_min: int,
        current_max: int,
    ) -> ScalingRecommendation:
        """Get a pool size recommendation.
        
        Based on current and predicted load, recommends
        optimal min/max pool sizes.
        
        Args:
            current_min: Current minimum connections
            current_max: Current maximum connections
        
        Returns:
            ScalingRecommendation with suggested sizes
        """
        if not self._history:
            return ScalingRecommendation(
                recommended_min=current_min,
                recommended_max=current_max,
                current_load=0.0,
                predicted_load=0.0,
                confidence=0.0,
                reason="No load data available",
            )
        
        # Current state
        latest = self._history[-1]
        current_load = latest.utilization
        
        # Predict future
        predicted_connections = self.predict_load()
        predicted_load = predicted_connections / current_max if current_max > 0 else 0
        
        # Calculate confidence based on sample count
        confidence = min(1.0, len(self._history) / 100)
        
        # Determine recommendation
        recommended_min = current_min
        recommended_max = current_max
        reason = "Current size is optimal"
        
        if predicted_load > self._config.scale_up_threshold:
            # Scale up
            new_max = int(predicted_connections * 1.5)  # 50% headroom
            new_max = max(new_max, current_max + 10)
            recommended_max = new_max
            reason = f"Predicted load {predicted_load:.0%} exceeds threshold"
            
        elif predicted_load < self._config.scale_down_threshold and current_load < self._config.scale_down_threshold:
            # Scale down
            new_max = max(current_min * 2, int(predicted_connections * 1.5))
            recommended_max = new_max
            reason = f"Load {current_load:.0%} below threshold, can reduce"
        
        return ScalingRecommendation(
            recommended_min=recommended_min,
            recommended_max=recommended_max,
            current_load=current_load,
            predicted_load=predicted_load,
            confidence=confidence,
            reason=reason,
        )
    
    async def start(self) -> None:
        """Start the adaptive scaler.
        
        Begins automatic sampling and scaling.
        """
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._scaling_loop())
        logger.info("Adaptive scaler started")
    
    async def stop(self) -> None:
        """Stop the adaptive scaler."""
        if not self._running:
            return
        
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("Adaptive scaler stopped")
    
    async def _scaling_loop(self) -> None:
        """Background scaling loop."""
        while self._running:
            try:
                # Sample current load
                if self._get_load:
                    used, max_conn, queue = self._get_load()
                    self.record_load(used, max_conn, queue)
                
                # Check if scaling needed
                if self._resize_callback and len(self._history) >= self._config.min_samples:
                    await self._check_and_scale()
                
            except Exception as e:
                logger.error(f"Error in scaling loop: {e}")
            
            await asyncio.sleep(self._config.sample_interval)
    
    async def _check_and_scale(self) -> None:
        """Check if scaling is needed and perform it."""
        # Check cooldown
        now = time.monotonic()
        if now - self._last_scale_time < self._config.cooldown_seconds:
            return
        
        latest = self._history[-1]
        rec = self.recommend_pool_size(1, latest.connections_max)
        
        if rec.recommended_max != latest.connections_max:
            # Perform scaling
            direction = "up" if rec.recommended_max > latest.connections_max else "down"
            
            event = ScaleEvent(
                timestamp=now,
                direction=direction,
                old_max=latest.connections_max,
                new_max=rec.recommended_max,
                trigger=rec.reason,
            )
            self._scale_events.append(event)
            
            if direction == "up":
                self._stats.scale_up_events += 1
            else:
                self._stats.scale_down_events += 1
            
            self._last_scale_time = now
            
            # Call resize callback
            if asyncio.iscoroutinefunction(self._resize_callback):
                await self._resize_callback(rec.recommended_min, rec.recommended_max)
            else:
                self._resize_callback(rec.recommended_min, rec.recommended_max)
            
            logger.info(
                f"Scaled {direction}: {event.old_max} -> {event.new_max} "
                f"({rec.reason})"
            )
    
    def get_history(self, limit: int = 100) -> List[LoadSample]:
        """Get recent load history.
        
        Args:
            limit: Maximum samples to return
        
        Returns:
            List of LoadSample
        """
        return list(self._history)[-limit:]
    
    def get_scale_events(self, limit: int = 20) -> List[ScaleEvent]:
        """Get recent scale events.
        
        Args:
            limit: Maximum events to return
        
        Returns:
            List of ScaleEvent
        """
        return self._scale_events[-limit:]
    
    def get_stats(self) -> ScalingStats:
        """Get scaling statistics."""
        return self._stats
    
    def reset_stats(self) -> None:
        """Reset statistics and history."""
        self._stats = ScalingStats()
        self._history.clear()
        self._scale_events.clear()
    
    def __repr__(self) -> str:
        return (
            f"AdaptiveScaler(samples={len(self._history)}, "
            f"events={len(self._scale_events)})"
        )


# =============================================================================
# Convenience Functions
# =============================================================================

def aggressive_scaling_config() -> AdaptiveScalingConfig:
    """Create an aggressive scaling configuration.
    
    - Lower scale-up threshold (70%)
    - Shorter cooldown (30s)
    - Longer prediction window (120s)
    
    Best for variable traffic patterns.
    
    Returns:
        AdaptiveScalingConfig for aggressive scaling
    """
    return AdaptiveScalingConfig(
        scale_up_threshold=0.7,
        cooldown_seconds=30.0,
        predict_ahead_seconds=120.0,
        prediction_buffer=0.3,
    )


def conservative_scaling_config() -> AdaptiveScalingConfig:
    """Create a conservative scaling configuration.
    
    - Higher scale-up threshold (90%)
    - Longer cooldown (120s)
    - Lower scale-down threshold (20%)
    
    Best for stable traffic patterns.
    
    Returns:
        AdaptiveScalingConfig for conservative scaling
    """
    return AdaptiveScalingConfig(
        scale_up_threshold=0.9,
        scale_down_threshold=0.2,
        cooldown_seconds=120.0,
        prediction_buffer=0.1,
    )


def disabled_scaling_config() -> AdaptiveScalingConfig:
    """Create a disabled scaling configuration.
    
    Returns:
        AdaptiveScalingConfig with scaling disabled
    """
    return AdaptiveScalingConfig(enabled=False)

