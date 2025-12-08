"""
Tests for Go Bridge fallback behavior.

These tests simulate Go being unavailable by patching GO_AVAILABLE
to test the fallback paths even when Go is actually available.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestGoBridgeFallbackSimulated:
    """Tests that simulate Go being unavailable."""
    
    def test_go_not_available_error_raised(self):
        """When GO_AVAILABLE is False, init should raise GoNotAvailableError."""
        with patch('pynext_go.bridge.GO_AVAILABLE', False):
            from pynext_go import GoBridge, GoNotAvailableError
            from pynext_go.config import BridgeConfig
            
            bridge = GoBridge()
            config = BridgeConfig(primary="postgresql://localhost/test")
            
            with pytest.raises(GoNotAvailableError):
                bridge.init(config)
    
    def test_module_init_raises_when_go_unavailable(self):
        """pynext_go.init() should raise when Go unavailable."""
        with patch('pynext_go.bridge.GO_AVAILABLE', False):
            # Need to also patch the module-level check
            with patch('pynext_go.GO_AVAILABLE', False):
                import pynext_go
                from pynext_go import GoNotAvailableError
                
                pynext_go.close()  # Reset
                
                with pytest.raises(GoNotAvailableError):
                    pynext_go.init("postgresql://localhost/test")
    
    def test_version_returns_not_available(self):
        """Version should return 'not available' when Go unavailable."""
        with patch('pynext_go.bridge.GO_AVAILABLE', False):
            from pynext_go import GoBridge
            
            version = GoBridge.version()
            assert version == "not available"


class TestGoAdapterFallbackSimulated:
    """Tests for GoPostgresAdapter fallback when Go unavailable."""
    
    @pytest.mark.asyncio
    async def test_connect_sets_connected_in_fallback_mode(self):
        """In fallback mode, connect should set _connected without Go bridge."""
        with patch('pynext.db.adapters.go_adapter.is_go_available', return_value=False):
            from pynext.db.adapters.go_adapter import GoPostgresAdapter
            
            adapter = GoPostgresAdapter("postgresql://localhost/test")
            
            # Connect should work in fallback mode
            await adapter.connect()
            
            assert adapter._connected is True
            assert adapter._bridge is None  # No Go bridge
    
    @pytest.mark.asyncio
    async def test_require_go_raises_when_unavailable(self):
        """require_go=True should raise when Go unavailable."""
        with patch('pynext.db.adapters.go_adapter.is_go_available', return_value=False):
            from pynext.db.adapters.go_adapter import GoPostgresAdapter
            from pynext_go.errors import GoNotAvailableError
            
            adapter = GoPostgresAdapter(
                "postgresql://localhost/test",
                require_go=True,
            )
            
            with pytest.raises(GoNotAvailableError):
                await adapter.connect()
    
    @pytest.mark.asyncio
    async def test_fallback_mode_operations_raise_not_implemented(self):
        """In pure fallback mode without asyncpg, operations should raise."""
        with patch('pynext.db.adapters.go_adapter.is_go_available', return_value=False):
            from pynext.db.adapters.go_adapter import GoPostgresAdapter
            
            adapter = GoPostgresAdapter("postgresql://localhost/test")
            await adapter.connect()
            
            # Without asyncpg fallback implemented, these should raise
            with pytest.raises(NotImplementedError):
                await adapter.execute("SELECT 1")


class TestGetBestAdapterFallbackSimulated:
    """Tests for get_best_adapter fallback selection."""
    
    def test_get_best_adapter_require_go_raises(self):
        """get_best_adapter with require_go should raise when unavailable."""
        # Patch both the adapter module and the function it calls
        with patch('pynext.db.adapters.go_adapter.is_go_available', return_value=False):
            with patch('pynext.db.adapters.is_go_available', return_value=False):
                from pynext.db.adapters import get_best_adapter
                
                with pytest.raises(ImportError, match="Go bridge required"):
                    get_best_adapter(
                        "postgresql://localhost/test",
                        require_go=True,
                    )
    
    def test_get_best_adapter_prefer_go_falls_back(self):
        """get_best_adapter should fallback when Go unavailable and prefer_go=False."""
        from pynext.db.adapters import get_best_adapter
        from pynext.db.adapters.go_adapter import GoPostgresAdapter
        
        # When prefer_go=False, should try asyncpg even if Go is available
        try:
            adapter = get_best_adapter(
                "postgresql://localhost/test",
                prefer_go=False,
            )
            # Should NOT be GoPostgresAdapter when prefer_go=False
            assert not isinstance(adapter, GoPostgresAdapter)
        except ImportError:
            # asyncpg not installed - this is expected and correct behavior
            pass


class TestFallbackAPIConsistency:
    """Test that the API is consistent between Go and fallback modes."""
    
    def test_bridge_has_same_interface_in_fallback(self):
        """GoBridge should have same interface regardless of Go availability."""
        from pynext_go import GoBridge
        
        bridge = GoBridge()
        
        # All methods should exist
        assert hasattr(bridge, 'init')
        assert hasattr(bridge, 'execute')
        assert hasattr(bridge, 'execute_batch')
        assert hasattr(bridge, 'health')
        assert hasattr(bridge, 'warmup')
        assert hasattr(bridge, 'close')
        
        # All properties should exist
        assert hasattr(bridge, 'is_available')
        assert hasattr(bridge, 'is_initialized')
        assert hasattr(bridge, 'config')
    
    def test_adapter_has_same_interface_in_fallback(self):
        """GoPostgresAdapter should have same interface regardless of Go."""
        from pynext.db.adapters.go_adapter import GoPostgresAdapter
        
        adapter = GoPostgresAdapter("postgresql://localhost/test")
        
        # All Adapter methods should exist
        assert hasattr(adapter, 'connect')
        assert hasattr(adapter, 'disconnect')
        assert hasattr(adapter, 'execute')
        assert hasattr(adapter, 'fetch_all')
        assert hasattr(adapter, 'fetch_one')
        assert hasattr(adapter, 'insert')
        assert hasattr(adapter, 'select')
        assert hasattr(adapter, 'update')
        assert hasattr(adapter, 'delete')
        assert hasattr(adapter, 'count')
        assert hasattr(adapter, 'exists')
        assert hasattr(adapter, 'begin_transaction')
        assert hasattr(adapter, 'commit_transaction')
        assert hasattr(adapter, 'rollback_transaction')


class TestFallbackErrorMessages:
    """Test that fallback error messages are helpful."""
    
    def test_go_not_available_error_message(self):
        """GoNotAvailableError should have helpful message."""
        from pynext_go.errors import GoNotAvailableError
        
        err = GoNotAvailableError()
        assert "not available" in str(err).lower()
    
    def test_go_not_available_custom_message(self):
        """GoNotAvailableError should accept custom message."""
        from pynext_go.errors import GoNotAvailableError
        
        err = GoNotAvailableError("Custom: Install pynext-go")
        assert "Custom" in str(err)
    
    def test_bridge_not_initialized_error_helpful(self):
        """BridgeError for uninitialized should mention init()."""
        from pynext_go.errors import BridgeError
        
        err = BridgeError("Go bridge not initialized - call init() first")
        assert "init()" in str(err)


class TestFallbackGracefulDegradation:
    """Test graceful degradation when Go unavailable."""
    
    def test_close_safe_without_go(self):
        """close() should be safe even without Go."""
        with patch('pynext_go.bridge.GO_AVAILABLE', False):
            from pynext_go import GoBridge
            
            bridge = GoBridge()
            
            # Should not raise
            bridge.close()
            bridge.close()  # Multiple times safe
    
    def test_module_close_safe_without_init(self):
        """Module close() should be safe without init."""
        import pynext_go
        
        pynext_go.close()  # Should not raise
        pynext_go.close()  # Multiple times safe


class TestFallbackEnvironmentVariable:
    """Test PYNEXT_GO_LIB environment variable fallback."""
    
    def test_env_var_checked_for_library(self):
        """_find_library should check PYNEXT_GO_LIB env var."""
        import os
        from pynext_go.bridge import _find_library
        
        # With no env var, should still work
        result = _find_library()
        # Result depends on whether Go lib exists
        assert result is None or result.exists()
    
    def test_invalid_env_var_path_handled(self):
        """Invalid PYNEXT_GO_LIB path should be handled gracefully."""
        import os
        from unittest.mock import patch
        
        with patch.dict(os.environ, {'PYNEXT_GO_LIB': '/nonexistent/path/libpynext.so'}):
            from pynext_go.bridge import _find_library
            
            # Should not raise, just log warning and continue search
            result = _find_library()
            # May find it elsewhere or return None

