"""
Unit tests for Go Bridge health status types.

Tests HealthStatus, ConnectionHealth, and PoolHealth.
"""

import pytest
from datetime import datetime

from pynext_go.health import (
    ConnectionHealth,
    PoolHealth,
    HealthStatus,
)


class TestConnectionHealth:
    """ConnectionHealth tests."""
    
    def test_basic_creation(self):
        """Create basic ConnectionHealth."""
        health = ConnectionHealth(
            url="***",
            status="ok",
            latency_ms=1.5,
        )
        assert health.url == "***"
        assert health.status == "ok"
        assert health.latency_ms == 1.5
        assert health.error == ""
    
    def test_with_error(self):
        """ConnectionHealth with error."""
        health = ConnectionHealth(
            url="***",
            status="down",
            latency_ms=0.0,
            error="connection refused",
        )
        assert health.error == "connection refused"
    
    def test_is_ok_property(self):
        """is_ok should return True only for 'ok' status."""
        ok = ConnectionHealth(url="", status="ok", latency_ms=1.0)
        degraded = ConnectionHealth(url="", status="degraded", latency_ms=100.0)
        down = ConnectionHealth(url="", status="down", latency_ms=0.0)
        
        assert ok.is_ok is True
        assert degraded.is_ok is False
        assert down.is_ok is False
    
    def test_is_degraded_property(self):
        """is_degraded should return True only for 'degraded' status."""
        ok = ConnectionHealth(url="", status="ok", latency_ms=1.0)
        degraded = ConnectionHealth(url="", status="degraded", latency_ms=100.0)
        down = ConnectionHealth(url="", status="down", latency_ms=0.0)
        
        assert ok.is_degraded is False
        assert degraded.is_degraded is True
        assert down.is_degraded is False
    
    def test_is_down_property(self):
        """is_down should return True only for 'down' status."""
        ok = ConnectionHealth(url="", status="ok", latency_ms=1.0)
        degraded = ConnectionHealth(url="", status="degraded", latency_ms=100.0)
        down = ConnectionHealth(url="", status="down", latency_ms=0.0)
        
        assert ok.is_down is False
        assert degraded.is_down is False
        assert down.is_down is True
    
    def test_from_dict(self):
        """from_dict should create ConnectionHealth from dict."""
        d = {
            "url": "***",
            "status": "ok",
            "latency_ms": 2.5,
            "error": "",
        }
        health = ConnectionHealth.from_dict(d)
        
        assert health.url == "***"
        assert health.status == "ok"
        assert health.latency_ms == 2.5
    
    def test_from_dict_missing_fields(self):
        """from_dict should handle missing fields with defaults."""
        d = {}
        health = ConnectionHealth.from_dict(d)
        
        assert health.url == ""
        assert health.status == "unknown"
        assert health.latency_ms == 0.0
        assert health.error == ""


class TestPoolHealth:
    """PoolHealth tests."""
    
    def test_basic_creation(self):
        """Create basic PoolHealth."""
        health = PoolHealth(
            total_conns=10,
            idle_conns=5,
            active_conns=5,
        )
        assert health.total_conns == 10
        assert health.idle_conns == 5
        assert health.active_conns == 5
        assert health.waiting_reqs == 0
    
    def test_with_all_fields(self):
        """PoolHealth with all fields."""
        health = PoolHealth(
            total_conns=10,
            idle_conns=2,
            active_conns=8,
            waiting_reqs=3,
            avg_wait_ms=5.5,
            max_wait_ms=50.0,
        )
        assert health.waiting_reqs == 3
        assert health.avg_wait_ms == 5.5
        assert health.max_wait_ms == 50.0
    
    def test_utilization_property(self):
        """utilization should return percentage of active connections."""
        health = PoolHealth(total_conns=10, idle_conns=3, active_conns=7)
        assert health.utilization == 70.0
        
        health2 = PoolHealth(total_conns=20, idle_conns=20, active_conns=0)
        assert health2.utilization == 0.0
        
        health3 = PoolHealth(total_conns=5, idle_conns=0, active_conns=5)
        assert health3.utilization == 100.0
    
    def test_utilization_zero_total(self):
        """utilization with zero total should return 0."""
        health = PoolHealth(total_conns=0, idle_conns=0, active_conns=0)
        assert health.utilization == 0.0
    
    def test_is_exhausted_property(self):
        """is_exhausted should be True when no idle conns and waiters exist."""
        # Not exhausted - has idle connections
        health1 = PoolHealth(total_conns=10, idle_conns=2, active_conns=8, waiting_reqs=0)
        assert health1.is_exhausted is False
        
        # Not exhausted - no waiters
        health2 = PoolHealth(total_conns=10, idle_conns=0, active_conns=10, waiting_reqs=0)
        assert health2.is_exhausted is False
        
        # Exhausted - no idle and has waiters
        health3 = PoolHealth(total_conns=10, idle_conns=0, active_conns=10, waiting_reqs=5)
        assert health3.is_exhausted is True
    
    def test_from_dict(self):
        """from_dict should create PoolHealth from dict."""
        d = {
            "total_conns": 15,
            "idle_conns": 5,
            "active_conns": 10,
            "waiting_reqs": 2,
            "avg_wait_ms": 3.0,
            "max_wait_ms": 20.0,
        }
        health = PoolHealth.from_dict(d)
        
        assert health.total_conns == 15
        assert health.idle_conns == 5
        assert health.active_conns == 10
        assert health.waiting_reqs == 2
    
    def test_from_dict_missing_fields(self):
        """from_dict should handle missing fields with defaults."""
        d = {}
        health = PoolHealth.from_dict(d)
        
        assert health.total_conns == 0
        assert health.idle_conns == 0
        assert health.active_conns == 0


class TestHealthStatus:
    """HealthStatus tests."""
    
    def test_basic_creation(self):
        """Create basic HealthStatus."""
        now = datetime.now()
        health = HealthStatus(
            status="healthy",
            primary=ConnectionHealth(url="***", status="ok", latency_ms=1.0),
            replicas=[],
            pool=PoolHealth(total_conns=10, idle_conns=5, active_conns=5),
            timestamp=now,
        )
        assert health.status == "healthy"
        assert health.primary is not None
        assert health.primary.status == "ok"
        assert health.timestamp == now
    
    def test_is_healthy_property(self):
        """is_healthy should return True for 'healthy' status."""
        now = datetime.now()
        pool = PoolHealth(total_conns=5, idle_conns=2, active_conns=3)
        
        healthy = HealthStatus(status="healthy", primary=None, replicas=[], pool=pool, timestamp=now)
        degraded = HealthStatus(status="degraded", primary=None, replicas=[], pool=pool, timestamp=now)
        unhealthy = HealthStatus(status="unhealthy", primary=None, replicas=[], pool=pool, timestamp=now)
        
        assert healthy.is_healthy is True
        assert degraded.is_healthy is False
        assert unhealthy.is_healthy is False
    
    def test_is_degraded_property(self):
        """is_degraded should return True for 'degraded' status."""
        now = datetime.now()
        pool = PoolHealth(total_conns=5, idle_conns=2, active_conns=3)
        
        healthy = HealthStatus(status="healthy", primary=None, replicas=[], pool=pool, timestamp=now)
        degraded = HealthStatus(status="degraded", primary=None, replicas=[], pool=pool, timestamp=now)
        
        assert healthy.is_degraded is False
        assert degraded.is_degraded is True
    
    def test_is_unhealthy_property(self):
        """is_unhealthy should return True for 'unhealthy' status."""
        now = datetime.now()
        pool = PoolHealth(total_conns=5, idle_conns=2, active_conns=3)
        
        unhealthy = HealthStatus(status="unhealthy", primary=None, replicas=[], pool=pool, timestamp=now)
        healthy = HealthStatus(status="healthy", primary=None, replicas=[], pool=pool, timestamp=now)
        
        assert unhealthy.is_unhealthy is True
        assert healthy.is_unhealthy is False
    
    def test_has_replicas_property(self):
        """has_replicas should be True when replicas configured."""
        now = datetime.now()
        pool = PoolHealth(total_conns=5, idle_conns=2, active_conns=3)
        replica = ConnectionHealth(url="***", status="ok", latency_ms=2.0)
        
        no_replicas = HealthStatus(status="healthy", primary=None, replicas=[], pool=pool, timestamp=now)
        with_replicas = HealthStatus(status="healthy", primary=None, replicas=[replica], pool=pool, timestamp=now)
        
        assert no_replicas.has_replicas is False
        assert with_replicas.has_replicas is True
    
    def test_healthy_replicas_property(self):
        """healthy_replicas should filter to only ok replicas."""
        now = datetime.now()
        pool = PoolHealth(total_conns=5, idle_conns=2, active_conns=3)
        
        replicas = [
            ConnectionHealth(url="r1", status="ok", latency_ms=1.0),
            ConnectionHealth(url="r2", status="degraded", latency_ms=100.0),
            ConnectionHealth(url="r3", status="ok", latency_ms=2.0),
            ConnectionHealth(url="r4", status="down", latency_ms=0.0),
        ]
        
        health = HealthStatus(status="degraded", primary=None, replicas=replicas, pool=pool, timestamp=now)
        
        healthy = health.healthy_replicas
        assert len(healthy) == 2
        assert all(r.status == "ok" for r in healthy)
    
    def test_summary(self):
        """summary should return readable string."""
        now = datetime.now()
        pool = PoolHealth(total_conns=10, idle_conns=3, active_conns=7)
        primary = ConnectionHealth(url="***", status="ok", latency_ms=1.5)
        
        health = HealthStatus(status="healthy", primary=primary, replicas=[], pool=pool, timestamp=now)
        summary = health.summary()
        
        assert "healthy" in summary.lower()
        assert "Primary: ok" in summary
        assert "7/10 active" in summary
    
    def test_summary_with_replicas(self):
        """summary should include replica info when present."""
        now = datetime.now()
        pool = PoolHealth(total_conns=5, idle_conns=2, active_conns=3)
        replicas = [
            ConnectionHealth(url="r1", status="ok", latency_ms=1.0),
            ConnectionHealth(url="r2", status="down", latency_ms=0.0),
        ]
        
        health = HealthStatus(status="degraded", primary=None, replicas=replicas, pool=pool, timestamp=now)
        summary = health.summary()
        
        assert "Replicas: 1/2 healthy" in summary
    
    def test_from_dict_full(self):
        """from_dict should create full HealthStatus."""
        d = {
            "status": "healthy",
            "primary": {
                "url": "***",
                "status": "ok",
                "latency_ms": 1.0,
                "error": "",
            },
            "replicas": [
                {"url": "***", "status": "ok", "latency_ms": 2.0, "error": ""},
            ],
            "pool": {
                "total_conns": 10,
                "idle_conns": 5,
                "active_conns": 5,
                "waiting_reqs": 0,
                "avg_wait_ms": 1.0,
                "max_wait_ms": 5.0,
            },
            "timestamp": "2024-01-15T10:30:00Z",
        }
        
        health = HealthStatus.from_dict(d)
        
        assert health.status == "healthy"
        assert health.primary is not None
        assert health.primary.status == "ok"
        assert len(health.replicas) == 1
        assert health.pool.total_conns == 10
    
    def test_from_dict_minimal(self):
        """from_dict with minimal data should use defaults."""
        d = {"status": "unknown"}
        health = HealthStatus.from_dict(d)
        
        assert health.status == "unknown"
        assert health.primary is None
        assert health.replicas == []
    
    def test_to_dict(self):
        """to_dict should serialize HealthStatus."""
        now = datetime.now()
        pool = PoolHealth(total_conns=10, idle_conns=5, active_conns=5)
        primary = ConnectionHealth(url="***", status="ok", latency_ms=1.0)
        
        health = HealthStatus(status="healthy", primary=primary, replicas=[], pool=pool, timestamp=now)
        d = health.to_dict()
        
        assert d["status"] == "healthy"
        assert d["primary"]["status"] == "ok"
        assert d["pool"]["total_conns"] == 10
        assert "timestamp" in d
    
    def test_roundtrip(self):
        """HealthStatus should survive dict roundtrip."""
        now = datetime.now()
        pool = PoolHealth(total_conns=10, idle_conns=5, active_conns=5)
        primary = ConnectionHealth(url="***", status="ok", latency_ms=1.5)
        replica = ConnectionHealth(url="***", status="degraded", latency_ms=50.0, error="slow")
        
        original = HealthStatus(
            status="degraded",
            primary=primary,
            replicas=[replica],
            pool=pool,
            timestamp=now,
        )
        
        d = original.to_dict()
        restored = HealthStatus.from_dict(d)
        
        assert restored.status == original.status
        assert restored.primary.status == original.primary.status
        assert len(restored.replicas) == 1
        assert restored.replicas[0].error == "slow"


class TestHealthStatusEdgeCases:
    """Edge case tests for health status."""
    
    def test_no_primary(self):
        """HealthStatus without primary should work."""
        now = datetime.now()
        pool = PoolHealth(total_conns=0, idle_conns=0, active_conns=0)
        
        health = HealthStatus(
            status="unhealthy",
            primary=None,
            replicas=[],
            pool=pool,
            timestamp=now,
        )
        
        assert health.primary is None
        summary = health.summary()
        assert "Primary:" not in summary
    
    def test_many_replicas(self):
        """HealthStatus with many replicas."""
        now = datetime.now()
        pool = PoolHealth(total_conns=10, idle_conns=5, active_conns=5)
        
        replicas = [
            ConnectionHealth(url=f"r{i}", status="ok", latency_ms=float(i))
            for i in range(10)
        ]
        
        health = HealthStatus(status="healthy", primary=None, replicas=replicas, pool=pool, timestamp=now)
        
        assert health.has_replicas
        assert len(health.healthy_replicas) == 10
    
    def test_timestamp_parsing_variants(self):
        """from_dict should handle various timestamp formats."""
        pool = {"total_conns": 5, "idle_conns": 2, "active_conns": 3}
        
        # ISO format with Z
        d1 = {"status": "healthy", "pool": pool, "timestamp": "2024-01-15T10:30:00Z"}
        h1 = HealthStatus.from_dict(d1)
        assert h1.timestamp.year == 2024
        
        # ISO format with offset
        d2 = {"status": "healthy", "pool": pool, "timestamp": "2024-01-15T10:30:00+00:00"}
        h2 = HealthStatus.from_dict(d2)
        assert h2.timestamp.year == 2024
        
        # Invalid timestamp should fall back to now
        d3 = {"status": "healthy", "pool": pool, "timestamp": "invalid"}
        h3 = HealthStatus.from_dict(d3)
        assert isinstance(h3.timestamp, datetime)

