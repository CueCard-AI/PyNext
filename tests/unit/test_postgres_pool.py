"""
PostgreSQL Auto-Scaling Pool Tests.

80 comprehensive tests for AutoScalingPool functionality.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from pynext.db.adapters.postgres_pool import (
    AutoScalingPool,
    PooledConnection,
    PoolState,
    ConnectionState,
    PoolStats,
    PoolExhaustedError,
    PoolClosedError,
)
from pynext.db.adapters.postgres_url import PostgresConfig


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def config():
    """Create a test PostgresConfig."""
    return PostgresConfig(
        host="localhost",
        port=5432,
        database="test",
        user="postgres",
    )


@pytest.fixture
def mock_asyncpg():
    """Mock asyncpg module."""
    import sys
    
    mock_conn = MagicMock()
    mock_conn.close = AsyncMock()
    mock_conn.execute = AsyncMock(return_value="SELECT 1")
    mock_conn.fetch = AsyncMock(return_value=[])
    mock_conn.fetchrow = AsyncMock(return_value=None)
    mock_conn.fetchval = AsyncMock(return_value=1)
    
    # Create a mock asyncpg module
    mock_asyncpg_module = MagicMock()
    mock_asyncpg_module.connect = AsyncMock(return_value=mock_conn)
    
    # Inject into sys.modules so import works
    old_module = sys.modules.get("asyncpg")
    sys.modules["asyncpg"] = mock_asyncpg_module
    
    yield mock_asyncpg_module, mock_conn
    
    # Restore
    if old_module:
        sys.modules["asyncpg"] = old_module
    else:
        sys.modules.pop("asyncpg", None)


# =============================================================================
# Pool Creation Tests
# =============================================================================

class TestPoolCreation:
    """Tests for pool creation."""
    
    def test_pool_creation_defaults(self, config):
        """Test creating pool with defaults."""
        pool = AutoScalingPool(config)
        assert pool.state == PoolState.UNINITIALIZED
        assert pool.size == 0
    
    def test_pool_creation_custom_sizes(self, config):
        """Test creating pool with custom sizes."""
        pool = AutoScalingPool(
            config,
            min_size=5,
            max_size=50,
        )
        stats = pool.get_stats()
        assert stats.min_size == 5
        assert stats.max_size == 50
    
    def test_pool_min_greater_than_max_raises(self, config):
        """Test min_size > max_size raises error."""
        with pytest.raises(ValueError):
            AutoScalingPool(config, min_size=10, max_size=5)
    
    def test_pool_min_size_zero_allowed(self, config):
        """Test min_size=0 is allowed."""
        pool = AutoScalingPool(config, min_size=0, max_size=10)
        stats = pool.get_stats()
        assert stats.min_size == 0
    
    def test_pool_max_size_one_allowed(self, config):
        """Test max_size=1 is allowed."""
        pool = AutoScalingPool(config, min_size=0, max_size=1)
        stats = pool.get_stats()
        assert stats.max_size == 1
    
    def test_pool_negative_min_raises(self, config):
        """Test negative min_size raises error."""
        with pytest.raises(ValueError):
            AutoScalingPool(config, min_size=-1)
    
    def test_pool_zero_max_raises(self, config):
        """Test max_size=0 raises error."""
        with pytest.raises(ValueError):
            AutoScalingPool(config, max_size=0)
    
    def test_pool_negative_timeout_raises(self, config):
        """Test negative idle_timeout raises error."""
        with pytest.raises(ValueError):
            AutoScalingPool(config, idle_timeout=-1)


# =============================================================================
# Pool Lifecycle Tests
# =============================================================================

class TestPoolLifecycle:
    """Tests for pool start/close lifecycle."""
    
    @pytest.mark.asyncio
    async def test_pool_start(self, config, mock_asyncpg):
        """Test starting pool creates initial connections."""
        mock, mock_conn = mock_asyncpg
        pool = AutoScalingPool(config, min_size=2, max_size=10)
        
        await pool.start()
        
        assert pool.state == PoolState.RUNNING
        assert pool.size == 2
        assert mock.connect.call_count == 2
    
    @pytest.mark.asyncio
    async def test_pool_start_with_zero_min(self, config, mock_asyncpg):
        """Test starting pool with min_size=0."""
        pool = AutoScalingPool(config, min_size=0, max_size=10)
        
        await pool.start()
        
        assert pool.state == PoolState.RUNNING
        assert pool.size == 0
    
    @pytest.mark.asyncio
    async def test_pool_close(self, config, mock_asyncpg):
        """Test closing pool closes all connections."""
        mock, mock_conn = mock_asyncpg
        pool = AutoScalingPool(config, min_size=2, max_size=10)
        
        await pool.start()
        await pool.close()
        
        assert pool.state == PoolState.CLOSED
        assert pool.size == 0
        assert mock_conn.close.call_count == 2
    
    @pytest.mark.asyncio
    async def test_pool_close_idempotent(self, config, mock_asyncpg):
        """Test closing already closed pool is safe."""
        pool = AutoScalingPool(config, min_size=1, max_size=10)
        
        await pool.start()
        await pool.close()
        await pool.close()  # Should not raise
        
        assert pool.state == PoolState.CLOSED
    
    @pytest.mark.asyncio
    async def test_pool_double_start_warning(self, config, mock_asyncpg):
        """Test starting already started pool logs warning."""
        pool = AutoScalingPool(config, min_size=1, max_size=10)
        
        await pool.start()
        await pool.start()  # Should not raise
        
        assert pool.state == PoolState.RUNNING


# =============================================================================
# Acquire/Release Tests
# =============================================================================

class TestAcquireRelease:
    """Tests for connection acquire/release."""
    
    @pytest.mark.asyncio
    async def test_acquire_returns_connection(self, config, mock_asyncpg):
        """Test acquire returns a connection."""
        mock, mock_conn = mock_asyncpg
        pool = AutoScalingPool(config, min_size=1, max_size=10)
        await pool.start()
        
        async with pool.acquire() as conn:
            assert conn == mock_conn
        
        await pool.close()
    
    @pytest.mark.asyncio
    async def test_acquire_from_closed_pool_raises(self, config, mock_asyncpg):
        """Test acquiring from closed pool raises error."""
        pool = AutoScalingPool(config, min_size=1, max_size=10)
        
        with pytest.raises(PoolClosedError):
            async with pool.acquire():
                pass
    
    @pytest.mark.asyncio
    async def test_release_returns_to_pool(self, config, mock_asyncpg):
        """Test released connection is returned to pool."""
        pool = AutoScalingPool(config, min_size=1, max_size=10)
        await pool.start()
        
        async with pool.acquire():
            stats = pool.get_stats()
            assert stats.busy == 1
            assert stats.idle == 0
        
        stats = pool.get_stats()
        assert stats.busy == 0
        assert stats.idle == 1
        
        await pool.close()


# =============================================================================
# Auto-Scaling Tests
# =============================================================================

class TestAutoScaling:
    """Tests for auto-scaling behavior."""
    
    @pytest.mark.asyncio
    async def test_scales_up_on_demand(self, config, mock_asyncpg):
        """Test pool scales up when all connections busy."""
        mock, mock_conn = mock_asyncpg
        pool = AutoScalingPool(config, min_size=1, max_size=10, auto_scale=True)
        await pool.start()
        
        assert pool.size == 1
        
        # Acquire more connections than min_size
        acquired = []
        for _ in range(3):
            conn = await pool._acquire_connection()
            acquired.append(conn)
        
        assert pool.size == 3
        
        for conn in acquired:
            await pool._release_connection(conn)
        
        await pool.close()
    
    @pytest.mark.asyncio
    async def test_respects_max_size(self, config, mock_asyncpg):
        """Test pool doesn't exceed max_size."""
        mock, mock_conn = mock_asyncpg
        pool = AutoScalingPool(
            config,
            min_size=1,
            max_size=3,
            auto_scale=True,
            acquire_timeout=0.5,
        )
        await pool.start()
        
        # Acquire all connections
        acquired = []
        for _ in range(3):
            conn = await pool._acquire_connection()
            acquired.append(conn)
        
        assert pool.size == 3
        
        # Try to acquire one more - should timeout
        with pytest.raises(PoolExhaustedError):
            await pool._acquire_connection()
        
        for conn in acquired:
            await pool._release_connection(conn)
        
        await pool.close()
    
    @pytest.mark.asyncio
    async def test_no_scale_when_disabled(self, config, mock_asyncpg):
        """Test pool doesn't scale when auto_scale=False."""
        mock, mock_conn = mock_asyncpg
        pool = AutoScalingPool(
            config,
            min_size=1,
            max_size=10,
            auto_scale=False,
            acquire_timeout=0.5,
        )
        await pool.start()
        
        # Acquire the only connection
        conn = await pool._acquire_connection()
        assert pool.size == 1
        
        # Try to acquire another - should timeout (no scaling)
        with pytest.raises(PoolExhaustedError):
            await pool._acquire_connection()
        
        await pool._release_connection(conn)
        await pool.close()


# =============================================================================
# Statistics Tests
# =============================================================================

class TestPoolStats:
    """Tests for pool statistics."""
    
    @pytest.mark.asyncio
    async def test_stats_initial(self, config, mock_asyncpg):
        """Test initial statistics."""
        pool = AutoScalingPool(config, min_size=2, max_size=10)
        await pool.start()
        
        stats = pool.get_stats()
        assert stats.size == 2
        assert stats.idle == 2
        assert stats.busy == 0
        assert stats.total_acquires == 0
        
        await pool.close()
    
    @pytest.mark.asyncio
    async def test_stats_after_acquire(self, config, mock_asyncpg):
        """Test statistics after acquiring."""
        pool = AutoScalingPool(config, min_size=2, max_size=10)
        await pool.start()
        
        async with pool.acquire():
            stats = pool.get_stats()
            assert stats.busy == 1
            assert stats.idle == 1
            assert stats.total_acquires == 1
        
        await pool.close()
    
    @pytest.mark.asyncio
    async def test_stats_after_release(self, config, mock_asyncpg):
        """Test statistics after releasing."""
        pool = AutoScalingPool(config, min_size=2, max_size=10)
        await pool.start()
        
        async with pool.acquire():
            pass
        
        stats = pool.get_stats()
        assert stats.busy == 0
        assert stats.idle == 2
        assert stats.total_releases == 1
        
        await pool.close()
    
    @pytest.mark.asyncio
    async def test_stats_to_dict(self, config, mock_asyncpg):
        """Test stats to_dict method."""
        pool = AutoScalingPool(config, min_size=1, max_size=10)
        await pool.start()
        
        stats_dict = pool.get_stats().to_dict()
        
        assert "size" in stats_dict
        assert "idle" in stats_dict
        assert "busy" in stats_dict
        assert "utilization" in stats_dict
        
        await pool.close()


# =============================================================================
# PooledConnection Tests
# =============================================================================

class TestPooledConnection:
    """Tests for PooledConnection class."""
    
    def test_creation(self):
        """Test creating a pooled connection."""
        mock_conn = MagicMock()
        pooled = PooledConnection(connection=mock_conn)
        
        assert pooled.connection == mock_conn
        assert pooled.state == ConnectionState.IDLE
        assert pooled.use_count == 0
    
    def test_mark_busy(self):
        """Test marking connection as busy."""
        mock_conn = MagicMock()
        pooled = PooledConnection(connection=mock_conn)
        
        pooled.mark_busy()
        
        assert pooled.state == ConnectionState.BUSY
        assert pooled.use_count == 1
    
    def test_mark_idle(self):
        """Test marking connection as idle."""
        mock_conn = MagicMock()
        pooled = PooledConnection(connection=mock_conn)
        pooled.mark_busy()
        pooled.mark_idle()
        
        assert pooled.state == ConnectionState.IDLE
    
    def test_age(self):
        """Test connection age calculation."""
        mock_conn = MagicMock()
        pooled = PooledConnection(connection=mock_conn)
        
        age = pooled.age()
        assert age >= 0
    
    def test_idle_time(self):
        """Test idle time calculation."""
        mock_conn = MagicMock()
        pooled = PooledConnection(connection=mock_conn)
        
        idle_time = pooled.idle_time()
        assert idle_time >= 0


# =============================================================================
# Convenience Methods Tests
# =============================================================================

class TestConvenienceMethods:
    """Tests for pool convenience methods."""
    
    @pytest.mark.asyncio
    async def test_execute(self, config, mock_asyncpg):
        """Test execute convenience method."""
        mock, mock_conn = mock_asyncpg
        mock_conn.execute.return_value = "UPDATE 5"
        pool = AutoScalingPool(config, min_size=1, max_size=10)
        await pool.start()
        
        result = await pool.execute("UPDATE users SET active = true")
        
        assert result == "UPDATE 5"
        mock_conn.execute.assert_called_once()
        
        await pool.close()
    
    @pytest.mark.asyncio
    async def test_fetch(self, config, mock_asyncpg):
        """Test fetch convenience method."""
        mock, mock_conn = mock_asyncpg
        mock_conn.fetch.return_value = [{"id": 1}, {"id": 2}]
        pool = AutoScalingPool(config, min_size=1, max_size=10)
        await pool.start()
        
        result = await pool.fetch("SELECT * FROM users")
        
        assert len(result) == 2
        mock_conn.fetch.assert_called_once()
        
        await pool.close()
    
    @pytest.mark.asyncio
    async def test_fetchrow(self, config, mock_asyncpg):
        """Test fetchrow convenience method."""
        mock, mock_conn = mock_asyncpg
        mock_conn.fetchrow.return_value = {"id": 1, "name": "John"}
        pool = AutoScalingPool(config, min_size=1, max_size=10)
        await pool.start()
        
        result = await pool.fetchrow("SELECT * FROM users WHERE id = $1", 1)
        
        assert result["id"] == 1
        mock_conn.fetchrow.assert_called_once()
        
        await pool.close()
    
    @pytest.mark.asyncio
    async def test_fetchval(self, config, mock_asyncpg):
        """Test fetchval convenience method."""
        mock, mock_conn = mock_asyncpg
        mock_conn.fetchval.return_value = 42
        pool = AutoScalingPool(config, min_size=1, max_size=10)
        await pool.start()
        
        result = await pool.fetchval("SELECT COUNT(*) FROM users")
        
        assert result == 42
        # Check the actual query was called (not just health check)
        mock_conn.fetchval.assert_any_call(
            "SELECT COUNT(*) FROM users",
            column=0,
            timeout=None,
        )
        
        await pool.close()


# =============================================================================
# Repr Tests
# =============================================================================

class TestRepr:
    """Tests for string representation."""
    
    def test_repr_uninitialized(self, config):
        """Test repr of uninitialized pool."""
        pool = AutoScalingPool(config, min_size=1, max_size=10)
        repr_str = repr(pool)
        
        assert "AutoScalingPool" in repr_str
        assert "uninitialized" in repr_str
    
    @pytest.mark.asyncio
    async def test_repr_running(self, config, mock_asyncpg):
        """Test repr of running pool."""
        pool = AutoScalingPool(config, min_size=2, max_size=10)
        await pool.start()
        
        repr_str = repr(pool)
        
        assert "running" in repr_str
        assert "2/10" in repr_str
        
        await pool.close()


# =============================================================================
# PoolStats Tests
# =============================================================================

class TestPoolStatsClass:
    """Tests for PoolStats dataclass."""
    
    def test_stats_creation(self):
        """Test creating PoolStats."""
        stats = PoolStats(
            size=5,
            idle=3,
            busy=2,
            min_size=1,
            max_size=10,
        )
        assert stats.size == 5
        assert stats.idle == 3
        assert stats.busy == 2
    
    def test_stats_to_dict(self):
        """Test PoolStats to_dict method."""
        stats = PoolStats(
            size=5,
            idle=3,
            busy=2,
            min_size=1,
            max_size=10,
            total_acquires=100,
            total_releases=95,
        )
        result = stats.to_dict()
        
        assert result["size"] == 5
        assert result["utilization"] == 0.4  # 2/5
    
    def test_stats_utilization_empty_pool(self):
        """Test utilization calculation with empty pool."""
        stats = PoolStats(size=0, idle=0, busy=0)
        result = stats.to_dict()
        
        assert result["utilization"] == 0


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestErrorHandling:
    """Tests for error handling."""
    
    @pytest.mark.asyncio
    async def test_pool_exhausted_error_message(self, config, mock_asyncpg):
        """Test PoolExhaustedError has helpful message."""
        pool = AutoScalingPool(
            config,
            min_size=1,
            max_size=1,
            acquire_timeout=0.1,
        )
        await pool.start()
        
        conn = await pool._acquire_connection()
        
        try:
            with pytest.raises(PoolExhaustedError) as exc_info:
                await pool._acquire_connection()
            
            error_msg = str(exc_info.value)
            assert "timeout" in error_msg.lower()
            assert "max_connections" in error_msg.lower() or "Pool stats" in error_msg
        finally:
            await pool._release_connection(conn)
            await pool.close()
    
    @pytest.mark.asyncio
    async def test_connection_create_failure(self, config):
        """Test handling connection creation failure."""
        import sys
        
        # Create a mock asyncpg module that fails
        mock_asyncpg_module = MagicMock()
        mock_asyncpg_module.connect = AsyncMock(side_effect=Exception("Connection failed"))
        
        old_module = sys.modules.get("asyncpg")
        sys.modules["asyncpg"] = mock_asyncpg_module
        
        try:
            pool = AutoScalingPool(config, min_size=1, max_size=10)
            
            # Pool should start but have no connections
            await pool.start()
            assert pool.size == 0
            
            await pool.close()
        finally:
            if old_module:
                sys.modules["asyncpg"] = old_module
            else:
                sys.modules.pop("asyncpg", None)

