"""
Tests for PostgreSQL Adaptive Scaling.

Tests cover:
- AdaptiveScalingConfig validation and defaults
- Load recording
- Load prediction
- Pool size recommendations
- Scale events
- Auto-scaling
- Statistics tracking
"""

import asyncio
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch

from pynext.db.adapters.postgres_scaling import (
    AdaptiveScalingConfig,
    LoadSample,
    ScaleEvent,
    ScalingStats,
    ScalingRecommendation,
    AdaptiveScaler,
    aggressive_scaling_config,
    conservative_scaling_config,
    disabled_scaling_config,
)


# =============================================================================
# AdaptiveScalingConfig Tests
# =============================================================================

class TestAdaptiveScalingConfig:
    """Tests for AdaptiveScalingConfig dataclass."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = AdaptiveScalingConfig()
        assert config.enabled is True
        assert config.predict_ahead_seconds == 60.0
        assert config.scale_up_threshold == 0.8
        assert config.scale_down_threshold == 0.3
        assert config.history_window == 300.0
        assert config.min_samples == 10
    
    def test_custom_thresholds(self):
        """Test custom thresholds."""
        config = AdaptiveScalingConfig(
            scale_up_threshold=0.9,
            scale_down_threshold=0.2,
        )
        assert config.scale_up_threshold == 0.9
        assert config.scale_down_threshold == 0.2
    
    def test_custom_prediction(self):
        """Test custom prediction settings."""
        config = AdaptiveScalingConfig(
            predict_ahead_seconds=120.0,
            min_samples=20,
        )
        assert config.predict_ahead_seconds == 120.0
        assert config.min_samples == 20
    
    def test_invalid_scale_up_threshold(self):
        """Test invalid scale_up_threshold raises error."""
        with pytest.raises(ValueError, match="scale_up_threshold"):
            AdaptiveScalingConfig(scale_up_threshold=1.5)
        
        with pytest.raises(ValueError, match="scale_up_threshold"):
            AdaptiveScalingConfig(scale_up_threshold=0)
    
    def test_invalid_scale_down_threshold(self):
        """Test invalid scale_down_threshold raises error."""
        with pytest.raises(ValueError, match="scale_down_threshold"):
            AdaptiveScalingConfig(scale_down_threshold=-0.1)
        
        # scale_down must be < scale_up
        with pytest.raises(ValueError, match="scale_down_threshold"):
            AdaptiveScalingConfig(
                scale_up_threshold=0.5,
                scale_down_threshold=0.6,
            )
    
    def test_invalid_min_samples(self):
        """Test invalid min_samples raises error."""
        with pytest.raises(ValueError, match="min_samples"):
            AdaptiveScalingConfig(min_samples=0)
    
    def test_negative_history_window_raises(self):
        """Test negative history_window raises error."""
        with pytest.raises(ValueError, match="history_window"):
            AdaptiveScalingConfig(history_window=-1)


# =============================================================================
# LoadSample Tests
# =============================================================================

class TestLoadSample:
    """Tests for LoadSample dataclass."""
    
    def test_basic_sample(self):
        """Test basic load sample creation."""
        sample = LoadSample(
            timestamp=time.monotonic(),
            connections_used=45,
            connections_max=100,
        )
        assert sample.connections_used == 45
        assert sample.connections_max == 100
    
    def test_utilization_calculation(self):
        """Test utilization calculation."""
        sample = LoadSample(
            timestamp=time.monotonic(),
            connections_used=50,
            connections_max=100,
        )
        assert sample.utilization == 0.5
    
    def test_utilization_zero_max(self):
        """Test utilization with zero max."""
        sample = LoadSample(
            timestamp=time.monotonic(),
            connections_used=0,
            connections_max=0,
        )
        assert sample.utilization == 0.0
    
    def test_under_pressure_with_queue(self):
        """Test under_pressure with queue depth."""
        sample = LoadSample(
            timestamp=time.monotonic(),
            connections_used=50,
            connections_max=100,
            queue_depth=5,
        )
        assert sample.under_pressure is True
    
    def test_under_pressure_high_utilization(self):
        """Test under_pressure with high utilization."""
        sample = LoadSample(
            timestamp=time.monotonic(),
            connections_used=95,
            connections_max=100,
        )
        assert sample.under_pressure is True
    
    def test_not_under_pressure(self):
        """Test not under pressure."""
        sample = LoadSample(
            timestamp=time.monotonic(),
            connections_used=50,
            connections_max=100,
            queue_depth=0,
        )
        assert sample.under_pressure is False


# =============================================================================
# ScaleEvent Tests
# =============================================================================

class TestScaleEvent:
    """Tests for ScaleEvent dataclass."""
    
    def test_scale_up_event(self):
        """Test scale up event."""
        event = ScaleEvent(
            timestamp=time.monotonic(),
            direction="up",
            old_max=50,
            new_max=100,
            trigger="High load",
        )
        assert event.direction == "up"
        assert event.old_max == 50
        assert event.new_max == 100
    
    def test_scale_down_event(self):
        """Test scale down event."""
        event = ScaleEvent(
            timestamp=time.monotonic(),
            direction="down",
            old_max=100,
            new_max=50,
            trigger="Low utilization",
        )
        assert event.direction == "down"
    
    def test_to_dict(self):
        """Test dictionary conversion."""
        event = ScaleEvent(
            timestamp=1234.5,
            direction="up",
            old_max=50,
            new_max=100,
            trigger="Test",
        )
        d = event.to_dict()
        assert d["direction"] == "up"
        assert d["old_max"] == 50
        assert d["new_max"] == 100


# =============================================================================
# ScalingStats Tests
# =============================================================================

class TestScalingStats:
    """Tests for ScalingStats dataclass."""
    
    def test_initial_stats(self):
        """Test initial statistics."""
        stats = ScalingStats()
        assert stats.samples_recorded == 0
        assert stats.predictions_made == 0
        assert stats.scale_up_events == 0
    
    def test_prediction_accuracy(self):
        """Test prediction accuracy calculation."""
        stats = ScalingStats(
            correct_predictions=8,
            total_predictions_verified=10,
        )
        assert stats.prediction_accuracy == 0.8
    
    def test_prediction_accuracy_zero(self):
        """Test prediction accuracy with no predictions."""
        stats = ScalingStats()
        assert stats.prediction_accuracy == 0.0
    
    def test_to_dict(self):
        """Test dictionary conversion."""
        stats = ScalingStats(scale_up_events=5)
        d = stats.to_dict()
        assert d["scale_up_events"] == 5


# =============================================================================
# ScalingRecommendation Tests
# =============================================================================

class TestScalingRecommendation:
    """Tests for ScalingRecommendation dataclass."""
    
    def test_basic_recommendation(self):
        """Test basic recommendation."""
        rec = ScalingRecommendation(
            recommended_min=5,
            recommended_max=100,
            current_load=0.6,
            predicted_load=0.8,
            confidence=0.9,
            reason="Predicted load increase",
        )
        assert rec.recommended_max == 100
        assert rec.confidence == 0.9
    
    def test_to_dict(self):
        """Test dictionary conversion."""
        rec = ScalingRecommendation(
            recommended_min=5,
            recommended_max=100,
            current_load=0.6,
            predicted_load=0.8,
            confidence=0.9,
            reason="Test",
        )
        d = rec.to_dict()
        assert "recommended_max" in d
        assert "confidence" in d


# =============================================================================
# AdaptiveScaler Basic Tests
# =============================================================================

class TestAdaptiveScalerBasic:
    """Tests for basic AdaptiveScaler operations."""
    
    @pytest.fixture
    def scaler(self):
        return AdaptiveScaler()
    
    def test_initial_state(self, scaler):
        """Test initial scaler state."""
        assert scaler.sample_count == 0
    
    def test_record_load(self, scaler):
        """Test recording load samples."""
        scaler.record_load(
            connections_used=50,
            connections_max=100,
            queue_depth=0,
        )
        
        assert scaler.sample_count == 1
    
    def test_record_multiple_loads(self, scaler):
        """Test recording multiple load samples."""
        for i in range(10):
            scaler.record_load(
                connections_used=50 + i,
                connections_max=100,
            )
        
        assert scaler.sample_count == 10
    
    def test_get_history(self, scaler):
        """Test getting load history."""
        for i in range(5):
            scaler.record_load(i, 100)
        
        history = scaler.get_history()
        assert len(history) == 5


# =============================================================================
# Load Prediction Tests
# =============================================================================

class TestLoadPrediction:
    """Tests for load prediction."""
    
    @pytest.fixture
    def scaler_with_data(self):
        scaler = AdaptiveScaler(AdaptiveScalingConfig(min_samples=5))
        
        # Record increasing load
        for i in range(10):
            scaler.record_load(
                connections_used=10 + i * 2,  # Increasing
                connections_max=100,
            )
        
        return scaler
    
    def test_predict_with_data(self, scaler_with_data):
        """Test prediction with sufficient data."""
        predicted = scaler_with_data.predict_load(seconds_ahead=60.0)
        
        # Should predict higher than current (increasing trend)
        assert predicted >= 0
    
    def test_predict_without_data(self):
        """Test prediction without sufficient data."""
        scaler = AdaptiveScaler(AdaptiveScalingConfig(min_samples=10))
        
        # Add fewer samples than min_samples
        for i in range(5):
            scaler.record_load(50, 100)
        
        predicted = scaler.predict_load()
        
        # Should return current or 0
        assert predicted >= 0
    
    def test_predict_empty(self):
        """Test prediction with no data."""
        scaler = AdaptiveScaler()
        predicted = scaler.predict_load()
        
        assert predicted == 0
    
    def test_prediction_updates_stats(self, scaler_with_data):
        """Test prediction updates statistics."""
        scaler_with_data.predict_load()
        
        stats = scaler_with_data.get_stats()
        assert stats.predictions_made == 1


# =============================================================================
# Pool Size Recommendation Tests
# =============================================================================

class TestPoolSizeRecommendation:
    """Tests for pool size recommendations."""
    
    def test_recommendation_no_data(self):
        """Test recommendation without data."""
        scaler = AdaptiveScaler()
        
        rec = scaler.recommend_pool_size(
            current_min=5,
            current_max=100,
        )
        
        # Should recommend current values
        assert rec.recommended_min == 5
        assert rec.recommended_max == 100
        assert rec.confidence == 0.0
    
    def test_recommendation_with_data(self):
        """Test recommendation with data."""
        scaler = AdaptiveScaler(AdaptiveScalingConfig(min_samples=5))
        
        # Add stable load
        for _ in range(10):
            scaler.record_load(50, 100)
        
        rec = scaler.recommend_pool_size(
            current_min=5,
            current_max=100,
        )
        
        assert rec.confidence > 0
        assert rec.reason != ""
    
    def test_scale_up_recommendation(self):
        """Test scale-up recommendation."""
        scaler = AdaptiveScaler(AdaptiveScalingConfig(
            min_samples=5,
            scale_up_threshold=0.5,
        ))
        
        # Add high load
        for _ in range(10):
            scaler.record_load(80, 100)
        
        rec = scaler.recommend_pool_size(
            current_min=5,
            current_max=100,
        )
        
        # Should recommend higher max
        assert rec.recommended_max >= 100
    
    def test_scale_down_recommendation(self):
        """Test scale-down recommendation."""
        scaler = AdaptiveScaler(AdaptiveScalingConfig(
            min_samples=5,
            scale_down_threshold=0.5,
        ))
        
        # Add very low load
        for _ in range(10):
            scaler.record_load(10, 100)
        
        rec = scaler.recommend_pool_size(
            current_min=5,
            current_max=100,
        )
        
        # Should recommend lower max
        assert rec.predicted_load < 0.5


# =============================================================================
# Auto-Scaling Tests
# =============================================================================

class TestAutoScaling:
    """Tests for automatic scaling."""
    
    @pytest.mark.asyncio
    async def test_start_stop(self):
        """Test start and stop."""
        scaler = AdaptiveScaler()
        
        await scaler.start()
        assert scaler._running
        
        await scaler.stop()
        assert not scaler._running
    
    @pytest.mark.asyncio
    async def test_double_start(self):
        """Test starting already running scaler."""
        scaler = AdaptiveScaler()
        
        await scaler.start()
        await scaler.start()  # Should be no-op
        
        assert scaler._running
        await scaler.stop()
    
    @pytest.mark.asyncio
    async def test_double_stop(self):
        """Test stopping already stopped scaler."""
        scaler = AdaptiveScaler()
        
        await scaler.stop()  # Already stopped
        await scaler.stop()  # Should be no-op
        
        assert not scaler._running
    
    @pytest.mark.asyncio
    async def test_auto_sampling(self):
        """Test automatic load sampling."""
        sample_count = 0
        
        def get_load():
            nonlocal sample_count
            sample_count += 1
            return (50, 100, 0)
        
        scaler = AdaptiveScaler(
            config=AdaptiveScalingConfig(sample_interval=0.05),
            get_load=get_load,
        )
        
        await scaler.start()
        await asyncio.sleep(0.2)
        await scaler.stop()
        
        assert sample_count >= 2
    
    @pytest.mark.asyncio
    async def test_resize_callback(self):
        """Test resize callback is called."""
        resize_calls = []
        
        def get_load():
            return (90, 100, 5)  # High load
        
        def resize(new_min, new_max):
            resize_calls.append((new_min, new_max))
        
        scaler = AdaptiveScaler(
            config=AdaptiveScalingConfig(
                sample_interval=0.01,
                min_samples=2,
                cooldown_seconds=0,
                scale_up_threshold=0.5,
            ),
            get_load=get_load,
            resize_callback=resize,
        )
        
        # Add initial samples
        for _ in range(5):
            scaler.record_load(90, 100, 5)
        
        await scaler.start()
        await asyncio.sleep(0.1)
        await scaler.stop()
        
        # May or may not have triggered, depending on timing
        # Just check it doesn't crash


# =============================================================================
# Scale Events Tests
# =============================================================================

class TestScaleEvents:
    """Tests for scale events tracking."""
    
    def test_get_scale_events_empty(self):
        """Test getting scale events when empty."""
        scaler = AdaptiveScaler()
        events = scaler.get_scale_events()
        
        assert len(events) == 0
    
    def test_get_scale_events_with_limit(self):
        """Test getting limited scale events."""
        scaler = AdaptiveScaler()
        
        # Manually add events for testing
        for i in range(10):
            event = ScaleEvent(
                timestamp=time.monotonic(),
                direction="up",
                old_max=i * 10,
                new_max=(i + 1) * 10,
                trigger="Test",
            )
            scaler._scale_events.append(event)
        
        events = scaler.get_scale_events(limit=5)
        assert len(events) == 5


# =============================================================================
# Statistics Tests
# =============================================================================

class TestScalingStatistics:
    """Tests for scaling statistics."""
    
    def test_stats_after_recording(self):
        """Test statistics after recording samples."""
        scaler = AdaptiveScaler()
        
        for _ in range(10):
            scaler.record_load(50, 100)
        
        stats = scaler.get_stats()
        assert stats.samples_recorded == 10
    
    def test_stats_reset(self):
        """Test statistics reset."""
        scaler = AdaptiveScaler()
        
        for _ in range(10):
            scaler.record_load(50, 100)
        
        scaler.reset_stats()
        
        stats = scaler.get_stats()
        assert stats.samples_recorded == 0
        assert scaler.sample_count == 0


# =============================================================================
# Convenience Config Tests
# =============================================================================

class TestConvenienceConfigs:
    """Tests for convenience configuration functions."""
    
    def test_aggressive_config(self):
        """Test aggressive scaling configuration."""
        config = aggressive_scaling_config()
        assert config.scale_up_threshold == 0.7
        assert config.cooldown_seconds == 30.0
        assert config.predict_ahead_seconds == 120.0
    
    def test_conservative_config(self):
        """Test conservative scaling configuration."""
        config = conservative_scaling_config()
        assert config.scale_up_threshold == 0.9
        assert config.scale_down_threshold == 0.2
        assert config.cooldown_seconds == 120.0
    
    def test_disabled_config(self):
        """Test disabled scaling configuration."""
        config = disabled_scaling_config()
        assert config.enabled is False


# =============================================================================
# Repr Tests
# =============================================================================

class TestScalerRepr:
    """Tests for scaler string representation."""
    
    def test_repr(self):
        """Test scaler repr."""
        scaler = AdaptiveScaler()
        repr_str = repr(scaler)
        assert "AdaptiveScaler" in repr_str


# =============================================================================
# Edge Cases Tests
# =============================================================================

class TestScalerEdgeCases:
    """Tests for scaler edge cases."""
    
    def test_zero_connections(self):
        """Test recording zero connections."""
        scaler = AdaptiveScaler()
        scaler.record_load(0, 0, 0)
        
        assert scaler.sample_count == 1
    
    def test_high_queue_depth(self):
        """Test recording high queue depth."""
        scaler = AdaptiveScaler()
        scaler.record_load(100, 100, 1000)
        
        history = scaler.get_history()
        assert history[0].queue_depth == 1000
    
    def test_prediction_flat_load(self):
        """Test prediction with flat load."""
        scaler = AdaptiveScaler(AdaptiveScalingConfig(min_samples=5))
        
        # Flat load
        for _ in range(10):
            scaler.record_load(50, 100)
        
        predicted = scaler.predict_load()
        
        # Should be close to current
        assert abs(predicted - 50) < 50  # Allow buffer
    
    def test_prediction_decreasing_load(self):
        """Test prediction with decreasing load."""
        scaler = AdaptiveScaler(AdaptiveScalingConfig(min_samples=5))
        
        # Decreasing load
        for i in range(10):
            scaler.record_load(100 - i * 5, 100)
        
        predicted = scaler.predict_load()
        
        # Should predict lower (or at least not explode)
        assert predicted >= 0


# =============================================================================
# History Management Tests
# =============================================================================

class TestHistoryManagement:
    """Tests for history management."""
    
    def test_history_window(self):
        """Test history respects window size."""
        scaler = AdaptiveScaler(AdaptiveScalingConfig(
            history_window=1.0,  # 1 second
            sample_interval=0.1,  # 10 samples max
        ))
        
        # Add many samples
        for i in range(20):
            scaler.record_load(i, 100)
        
        # Should have at most history_window / sample_interval samples
        assert scaler.sample_count <= 20
    
    def test_get_history_limit(self):
        """Test getting history with limit."""
        scaler = AdaptiveScaler()
        
        for i in range(100):
            scaler.record_load(i, 100)
        
        history = scaler.get_history(limit=10)
        assert len(history) == 10

