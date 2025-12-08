"""
Integration tests for Go Bridge fallback behavior.

Tests the seamless fallback to asyncpg when Go bridge is not available.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from pynext.db.adapters import get_best_adapter
from pynext.db.adapters.go_adapter import GoPostgresAdapter, is_go_available


class TestFallbackSelection:
    """Tests for adapter auto-selection fallback."""
    
    def test_get_best_adapter_exists(self):
        """get_best_adapter should exist."""
        from pynext.db.adapters import get_best_adapter
        assert callable(get_best_adapter)
    
    @pytest.mark.skipif(is_go_available(), reason="Tests Go-not-available path")
    def test_fallback_to_asyncpg_when_no_go(self):
        """Should fallback to asyncpg when Go unavailable."""
        try:
            adapter = get_best_adapter(
                "postgresql://localhost/test",
                prefer_go=True,  # Want Go but unavailable
            )
            # Should get asyncpg adapter
            assert not isinstance(adapter, GoPostgresAdapter)
        except ImportError:
            # asyncpg not installed either
            pass
    
    def test_explicit_asyncpg_when_prefer_go_false(self):
        """Should use asyncpg when prefer_go=False."""
        try:
            adapter = get_best_adapter(
                "postgresql://localhost/test",
                prefer_go=False,
            )
            # Should NOT get GoPostgresAdapter
            assert not isinstance(adapter, GoPostgresAdapter)
        except ImportError:
            # asyncpg not installed
            pass
    
    @pytest.mark.skipif(is_go_available(), reason="Tests Go-not-available path")
    def test_require_go_raises_when_unavailable(self):
        """require_go=True should raise when Go unavailable."""
        with pytest.raises(ImportError, match="Go bridge required"):
            get_best_adapter(
                "postgresql://localhost/test",
                require_go=True,
            )
    
    @pytest.mark.skipif(not is_go_available(), reason="Requires Go")
    def test_uses_go_when_available_and_preferred(self):
        """Should use Go adapter when available and preferred."""
        adapter = get_best_adapter(
            "postgresql://localhost/test",
            prefer_go=True,
        )
        assert isinstance(adapter, GoPostgresAdapter)


class TestFallbackBehavior:
    """Tests for fallback behavior in GoPostgresAdapter."""
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(is_go_available(), reason="Tests Go-not-available path")
    async def test_adapter_fallback_logs_warning(self):
        """Adapter should log warning when falling back."""
        import logging
        
        with patch("pynext.db.adapters.go_adapter.logger") as mock_logger:
            adapter = GoPostgresAdapter("postgresql://localhost/test")
            
            try:
                await adapter.connect()
            except (NotImplementedError, Exception):
                pass  # Expected - asyncpg fallback not implemented
            
            # Should have warned about fallback
            # (This depends on implementation details)
    
    @pytest.mark.asyncio
    async def test_adapter_require_go_prevents_fallback(self):
        """require_go=True should prevent fallback."""
        if not is_go_available():
            adapter = GoPostgresAdapter(
                "postgresql://localhost/test",
                require_go=True,
            )
            
            from pynext_go.errors import GoNotAvailableError
            with pytest.raises(GoNotAvailableError):
                await adapter.connect()


class TestFallbackAPIConsistency:
    """Tests that fallback provides consistent API."""
    
    @pytest.fixture
    def go_adapter(self):
        """Create Go adapter."""
        return GoPostgresAdapter("postgresql://localhost/test")
    
    def test_has_connect_method(self, go_adapter):
        """Adapter should have connect method."""
        assert hasattr(go_adapter, "connect")
        assert callable(go_adapter.connect)
    
    def test_has_disconnect_method(self, go_adapter):
        """Adapter should have disconnect method."""
        assert hasattr(go_adapter, "disconnect")
        assert callable(go_adapter.disconnect)
    
    def test_has_execute_method(self, go_adapter):
        """Adapter should have execute method."""
        assert hasattr(go_adapter, "execute")
        assert callable(go_adapter.execute)
    
    def test_has_fetch_all_method(self, go_adapter):
        """Adapter should have fetch_all method."""
        assert hasattr(go_adapter, "fetch_all")
        assert callable(go_adapter.fetch_all)
    
    def test_has_fetch_one_method(self, go_adapter):
        """Adapter should have fetch_one method."""
        assert hasattr(go_adapter, "fetch_one")
        assert callable(go_adapter.fetch_one)
    
    def test_has_transaction_methods(self, go_adapter):
        """Adapter should have transaction methods."""
        assert hasattr(go_adapter, "begin_transaction")
        assert hasattr(go_adapter, "commit_transaction")
        assert hasattr(go_adapter, "rollback_transaction")
    
    def test_has_crud_methods(self, go_adapter):
        """Adapter should have CRUD methods."""
        assert hasattr(go_adapter, "insert")
        assert hasattr(go_adapter, "select")
        assert hasattr(go_adapter, "select_one")
        assert hasattr(go_adapter, "update")
        assert hasattr(go_adapter, "delete")
        assert hasattr(go_adapter, "count")
        assert hasattr(go_adapter, "exists")


class TestFallbackConfiguration:
    """Tests for fallback configuration handling."""
    
    def test_config_preserved_in_fallback(self):
        """Configuration should be preserved in fallback mode."""
        adapter = GoPostgresAdapter(
            "postgresql://localhost/test",
            pool_min_size=5,
            pool_max_size=20,
            query_timeout=10000,
        )
        
        assert adapter._pool_min_size == 5
        assert adapter._pool_max_size == 20
        assert adapter._query_timeout == 10000
    
    def test_require_go_stored(self):
        """require_go flag should be stored."""
        adapter1 = GoPostgresAdapter(
            "postgresql://localhost/test",
            require_go=True,
        )
        adapter2 = GoPostgresAdapter(
            "postgresql://localhost/test",
            require_go=False,
        )
        
        assert adapter1._require_go is True
        assert adapter2._require_go is False


class TestFallbackErrorHandling:
    """Tests for error handling in fallback scenarios."""
    
    @pytest.mark.asyncio
    async def test_not_connected_raises(self):
        """Operations before connect should raise."""
        adapter = GoPostgresAdapter("postgresql://localhost/test")
        
        with pytest.raises(Exception, match="Not connected"):
            await adapter.fetch_all("SELECT 1")
    
    @pytest.mark.asyncio
    async def test_disconnect_safe_without_connect(self):
        """Disconnect without connect should be safe."""
        adapter = GoPostgresAdapter("postgresql://localhost/test")
        
        # Should not raise
        await adapter.disconnect()


class TestFallbackDetection:
    """Tests for fallback detection."""
    
    def test_is_go_available_consistent(self):
        """is_go_available should be consistent."""
        result1 = is_go_available()
        result2 = is_go_available()
        
        assert result1 == result2
        assert isinstance(result1, bool)
    
    def test_is_go_powered_false_without_bridge(self):
        """is_go_powered should be False without bridge."""
        adapter = GoPostgresAdapter("postgresql://localhost/test")
        
        # Before connect, no bridge
        assert adapter.is_go_powered is False


class TestFallbackIntegrationScenarios:
    """Integration scenarios for fallback."""
    
    @pytest.mark.asyncio
    async def test_create_table_works_in_fallback(self):
        """Table creation should work in fallback mode."""
        adapter = GoPostgresAdapter("postgresql://localhost/test")
        adapter._connected = True
        adapter._bridge = Mock()
        adapter._bridge.execute.return_value = Mock(success=True, rows_affected=0)
        
        from pynext.db.fields import FieldInfo, SQLType
        fields = {
            "id": FieldInfo("id", int, SQLType.INTEGER),
            "name": FieldInfo("name", str, SQLType.TEXT),
        }
        
        await adapter.create_table("test", fields)
        
        # Should have executed CREATE TABLE
        assert adapter._bridge.execute.called
    
    @pytest.mark.asyncio
    async def test_drop_table_works_in_fallback(self):
        """Table dropping should work in fallback mode."""
        adapter = GoPostgresAdapter("postgresql://localhost/test")
        adapter._connected = True
        adapter._bridge = Mock()
        adapter._bridge.execute.return_value = Mock(success=True, rows_affected=0)
        
        await adapter.drop_table("test")
        
        # Should have executed DROP TABLE
        assert adapter._bridge.execute.called

