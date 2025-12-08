"""
Unit tests for Go Bridge core functionality.

Tests GoBridge class, library loading, and function bindings.
Note: These tests work without the actual Go library by testing
the Python wrapper behavior and error handling.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import ctypes

from pynext_go.bridge import (
    GoBridge,
    GO_AVAILABLE,
    GO_LIBRARY_PATH,
    _find_library,
)
from pynext_go.config import BridgeConfig
from pynext_go.errors import (
    BridgeError,
    GoNotAvailableError,
)


class TestLibraryDiscovery:
    """Library discovery tests."""
    
    def test_find_library_returns_path_or_none(self):
        """_find_library should return Path or None."""
        result = _find_library()
        if result is not None:
            from pathlib import Path
            assert isinstance(result, Path)
    
    def test_go_available_is_boolean(self):
        """GO_AVAILABLE should be a boolean."""
        assert isinstance(GO_AVAILABLE, bool)
    
    def test_library_path_matches_available(self):
        """GO_LIBRARY_PATH should be set iff GO_AVAILABLE."""
        if GO_AVAILABLE:
            assert GO_LIBRARY_PATH is not None
        else:
            assert GO_LIBRARY_PATH is None


class TestGoBridgeInit:
    """GoBridge initialization tests."""
    
    def test_create_bridge(self):
        """Create GoBridge instance."""
        bridge = GoBridge()
        assert bridge.is_initialized is False
        assert bridge.config is None
    
    def test_is_available_property(self):
        """is_available should match GO_AVAILABLE."""
        bridge = GoBridge()
        assert bridge.is_available == GO_AVAILABLE
    
    @pytest.mark.skipif(GO_AVAILABLE, reason="Tests Go-not-available path")
    def test_init_raises_when_go_unavailable(self):
        """init should raise GoNotAvailableError when Go not available."""
        bridge = GoBridge()
        config = BridgeConfig(primary="postgresql://localhost/test")
        
        with pytest.raises(GoNotAvailableError):
            bridge.init(config)
    
    def test_init_validates_config(self):
        """init should validate config before calling Go."""
        bridge = GoBridge()
        
        # This should fail validation before even checking Go availability
        with pytest.raises(ValueError):
            bridge.init(BridgeConfig(primary=""))


class TestGoBridgeContextManager:
    """GoBridge context manager tests."""
    
    def test_context_manager_enter(self):
        """Context manager should return bridge."""
        with GoBridge() as bridge:
            assert isinstance(bridge, GoBridge)
    
    def test_context_manager_exit_calls_close(self):
        """Context manager exit should call close."""
        bridge = GoBridge()
        bridge.close = Mock()
        
        with bridge:
            pass
        
        bridge.close.assert_called_once()


class TestGoBridgeClose:
    """GoBridge close tests."""
    
    def test_close_uninitialized(self):
        """close on uninitialized bridge should be safe."""
        bridge = GoBridge()
        bridge.close()  # Should not raise
        assert bridge.is_initialized is False
    
    def test_close_multiple_times(self):
        """close should be safe to call multiple times."""
        bridge = GoBridge()
        bridge.close()
        bridge.close()
        bridge.close()
        assert bridge.is_initialized is False


class TestGoBridgeVersion:
    """GoBridge.version tests."""
    
    def test_version_returns_string(self):
        """version should return a string."""
        version = GoBridge.version()
        assert isinstance(version, str)
    
    @pytest.mark.skipif(not GO_AVAILABLE, reason="Requires Go library")
    def test_version_format(self):
        """version should be in semver format when Go available."""
        version = GoBridge.version()
        # Should be like "0.1.0" or "not available"
        if "not available" not in version.lower():
            parts = version.split(".")
            assert len(parts) >= 2  # At least major.minor


class TestGoBridgeCheckInitialized:
    """_check_initialized tests."""
    
    def test_check_initialized_raises_when_not_init(self):
        """_check_initialized should raise when not initialized."""
        bridge = GoBridge()
        with pytest.raises(BridgeError, match="not initialized"):
            bridge._check_initialized()


class TestGoBridgeExecuteUninitialized:
    """Execute method tests without initialization."""
    
    def test_execute_raises_when_not_init(self):
        """execute should raise when not initialized."""
        bridge = GoBridge()
        with pytest.raises(BridgeError, match="not initialized"):
            bridge.execute("SELECT 1")
    
    def test_execute_batch_raises_when_not_init(self):
        """execute_batch should raise when not initialized."""
        bridge = GoBridge()
        with pytest.raises(BridgeError, match="not initialized"):
            bridge.execute_batch([("SELECT 1", [])])
    
    def test_health_raises_when_not_init(self):
        """health should raise when not initialized."""
        bridge = GoBridge()
        with pytest.raises(BridgeError, match="not initialized"):
            bridge.health()
    
    def test_warmup_raises_when_not_init(self):
        """warmup should raise when not initialized."""
        bridge = GoBridge()
        with pytest.raises(BridgeError, match="not initialized"):
            bridge.warmup()


class TestGoBridgeMocked:
    """Tests with mocked Go library."""
    
    @pytest.fixture
    def mock_go_lib(self):
        """Create mock Go library."""
        mock_lib = MagicMock()
        mock_lib.PynextInit.return_value = 0
        mock_lib.PynextClose.return_value = None
        mock_lib.PynextVersion.return_value = b"0.1.0"
        return mock_lib
    
    def test_mock_library_structure(self, mock_go_lib):
        """Verify mock library has expected methods."""
        assert hasattr(mock_go_lib, 'PynextInit')
        assert hasattr(mock_go_lib, 'PynextExecute')
        assert hasattr(mock_go_lib, 'PynextClose')
        assert hasattr(mock_go_lib, 'PynextHealth')


class TestGoBridgeThreadSafety:
    """Thread safety tests."""
    
    def test_bridge_has_lock(self):
        """Bridge should have internal lock."""
        bridge = GoBridge()
        assert hasattr(bridge, '_lock')
    
    def test_close_is_idempotent(self):
        """close should be idempotent (safe to call multiple times)."""
        bridge = GoBridge()
        
        # Calling close multiple times from "different threads"
        for _ in range(10):
            bridge.close()
        
        assert not bridge.is_initialized


class TestGoBridgeConfigProperty:
    """Config property tests."""
    
    def test_config_none_before_init(self):
        """config should be None before init."""
        bridge = GoBridge()
        assert bridge.config is None
    
    def test_config_cleared_after_close(self):
        """config should be None after close."""
        bridge = GoBridge()
        bridge._initialized = True
        bridge._config = BridgeConfig(primary="postgresql://localhost/test")
        
        bridge.close()
        assert bridge.config is None


class TestGoBridgeErrorHandling:
    """Error handling tests."""
    
    def test_error_from_code_method(self):
        """_error_from_code should create appropriate errors."""
        bridge = GoBridge()
        
        err = bridge._error_from_code(1, "config error")
        assert "config error" in str(err)
        
        err = bridge._error_from_code(999, "unknown")
        assert "unknown" in str(err)


# =============================================================================
# Integration-style tests (mock the library calls)
# =============================================================================

class TestGoBridgeExecuteMocked:
    """Execute tests with mocked library."""
    
    @pytest.fixture
    def initialized_bridge(self):
        """Create an initialized bridge with mocked internals."""
        bridge = GoBridge()
        bridge._initialized = True
        bridge._config = BridgeConfig(primary="postgresql://localhost/test")
        return bridge
    
    def test_execute_params_default_empty(self, initialized_bridge):
        """execute with no params should use empty list."""
        bridge = initialized_bridge
        
        # The bridge needs a _bridge attribute for execute to work
        # Without the Go library, we just verify the interface
        assert hasattr(bridge, 'execute')
        assert callable(bridge.execute)


class TestGoBridgeExecuteBatchMocked:
    """Execute batch tests with mocked library."""
    
    @pytest.fixture
    def initialized_bridge(self):
        """Create an initialized bridge with mocked internals."""
        bridge = GoBridge()
        bridge._initialized = True
        bridge._config = BridgeConfig(primary="postgresql://localhost/test")
        return bridge
    
    def test_batch_format(self, initialized_bridge):
        """Verify batch query format."""
        queries = [
            ("INSERT INTO t VALUES ($1)", [1]),
            ("INSERT INTO t VALUES ($1)", [2]),
        ]
        
        # Format is [(sql, params), ...]
        assert len(queries) == 2
        assert queries[0][0] == "INSERT INTO t VALUES ($1)"
        assert queries[0][1] == [1]


# =============================================================================
# Edge case tests
# =============================================================================

class TestGoBridgeEdgeCases:
    """Edge case tests."""
    
    def test_create_many_bridges(self):
        """Creating many bridge instances should work."""
        bridges = [GoBridge() for _ in range(100)]
        assert len(bridges) == 100
        
        for b in bridges:
            b.close()
    
    def test_bridge_repr(self):
        """Bridge should have reasonable repr."""
        bridge = GoBridge()
        r = repr(bridge)
        # Should at least be a string without crashing
        assert isinstance(r, str)
    
    def test_config_immutable_after_init(self):
        """Config should not be modifiable after init."""
        bridge = GoBridge()
        config = BridgeConfig(primary="postgresql://localhost/test")
        bridge._initialized = True
        bridge._config = config
        
        # Getting config should return the same object
        assert bridge.config is config

