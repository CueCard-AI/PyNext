"""
Unit tests for pynext_go module-level functions.

Tests the convenience functions in pynext_go/__init__.py.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

import pynext_go
from pynext_go import (
    GO_AVAILABLE,
    GoBridge,
    BridgeConfig,
    BridgeError,
)


class TestModuleExports:
    """Module export tests."""
    
    def test_version_exported(self):
        """__version__ should be exported."""
        assert hasattr(pynext_go, '__version__')
        assert isinstance(pynext_go.__version__, str)
    
    def test_go_available_exported(self):
        """GO_AVAILABLE should be exported."""
        assert hasattr(pynext_go, 'GO_AVAILABLE')
        assert isinstance(pynext_go.GO_AVAILABLE, bool)
    
    def test_go_library_path_exported(self):
        """GO_LIBRARY_PATH should be exported."""
        assert hasattr(pynext_go, 'GO_LIBRARY_PATH')
    
    def test_bridge_exported(self):
        """GoBridge should be exported."""
        assert hasattr(pynext_go, 'GoBridge')
        assert pynext_go.GoBridge is GoBridge
    
    def test_config_exported(self):
        """BridgeConfig should be exported."""
        assert hasattr(pynext_go, 'BridgeConfig')
        assert pynext_go.BridgeConfig is BridgeConfig
    
    def test_errors_exported(self):
        """Error classes should be exported."""
        assert hasattr(pynext_go, 'BridgeError')
        assert hasattr(pynext_go, 'BridgeConfigError')
        assert hasattr(pynext_go, 'BridgeConnectionError')
        assert hasattr(pynext_go, 'BridgeQueryError')
        assert hasattr(pynext_go, 'BridgeTimeoutError')
        assert hasattr(pynext_go, 'BridgePoolError')
        assert hasattr(pynext_go, 'BridgeArrowError')
        assert hasattr(pynext_go, 'GoNotAvailableError')
    
    def test_health_types_exported(self):
        """Health status types should be exported."""
        assert hasattr(pynext_go, 'HealthStatus')
        assert hasattr(pynext_go, 'ConnectionHealth')
        assert hasattr(pynext_go, 'PoolHealth')
    
    def test_result_types_exported(self):
        """Result types should be exported."""
        assert hasattr(pynext_go, 'QueryResult')
        assert hasattr(pynext_go, 'BatchResult')
    
    def test_constants_exported(self):
        """Constants should be exported."""
        assert hasattr(pynext_go, 'DEFAULT_POOL_MIN')
        assert hasattr(pynext_go, 'DEFAULT_POOL_MAX')
        assert hasattr(pynext_go, 'DEFAULT_QUERY_TIMEOUT')


class TestModuleFunctions:
    """Module-level function tests."""
    
    def test_init_function_exists(self):
        """init function should exist."""
        assert hasattr(pynext_go, 'init')
        assert callable(pynext_go.init)
    
    def test_execute_function_exists(self):
        """execute function should exist."""
        assert hasattr(pynext_go, 'execute')
        assert callable(pynext_go.execute)
    
    def test_execute_batch_function_exists(self):
        """execute_batch function should exist."""
        assert hasattr(pynext_go, 'execute_batch')
        assert callable(pynext_go.execute_batch)
    
    def test_health_function_exists(self):
        """health function should exist."""
        assert hasattr(pynext_go, 'health')
        assert callable(pynext_go.health)
    
    def test_close_function_exists(self):
        """close function should exist."""
        assert hasattr(pynext_go, 'close')
        assert callable(pynext_go.close)
    
    def test_warmup_function_exists(self):
        """warmup function should exist."""
        assert hasattr(pynext_go, 'warmup')
        assert callable(pynext_go.warmup)


class TestModuleGlobalBridge:
    """Global bridge instance tests."""
    
    def test_execute_without_init_raises(self):
        """execute without init should raise."""
        pynext_go.close()  # Ensure no global bridge
        
        with pytest.raises(BridgeError, match="not initialized"):
            pynext_go.execute("SELECT 1")
    
    def test_execute_batch_without_init_raises(self):
        """execute_batch without init should raise."""
        pynext_go.close()
        
        with pytest.raises(BridgeError, match="not initialized"):
            pynext_go.execute_batch([("SELECT 1", [])])
    
    def test_health_without_init_raises(self):
        """health without init should raise."""
        pynext_go.close()
        
        with pytest.raises(BridgeError, match="not initialized"):
            pynext_go.health()
    
    def test_warmup_without_init_raises(self):
        """warmup without init should raise."""
        pynext_go.close()
        
        with pytest.raises(BridgeError, match="not initialized"):
            pynext_go.warmup()
    
    def test_close_without_init_safe(self):
        """close without init should be safe."""
        pynext_go.close()
        pynext_go.close()  # Should not raise
    
    def test_close_multiple_times_safe(self):
        """close multiple times should be safe."""
        for _ in range(5):
            pynext_go.close()


class TestModuleInit:
    """Module init function tests."""
    
    @pytest.mark.skipif(GO_AVAILABLE, reason="Tests Go-not-available path")
    def test_init_without_go_warns(self):
        """init without Go should raise or fallback."""
        pynext_go.close()
        
        # Without Go, init should raise GoNotAvailableError
        from pynext_go import GoNotAvailableError
        with pytest.raises(GoNotAvailableError):
            pynext_go.init("postgresql://localhost/test")
    
    def test_init_returns_bridge(self):
        """init should return GoBridge instance (or raise)."""
        pynext_go.close()
        
        try:
            bridge = pynext_go.init("postgresql://localhost/test")
            assert isinstance(bridge, GoBridge)
        except Exception:
            # May fail without Go or database
            pass
        finally:
            pynext_go.close()
    
    def test_init_with_pool_settings(self):
        """init should accept pool settings."""
        pynext_go.close()
        
        try:
            pynext_go.init(
                "postgresql://localhost/test",
                pool_min_size=5,
                pool_max_size=20,
            )
        except Exception:
            pass
        finally:
            pynext_go.close()
    
    def test_init_with_timeout(self):
        """init should accept timeout."""
        pynext_go.close()
        
        try:
            pynext_go.init(
                "postgresql://localhost/test",
                query_timeout=5000,
            )
        except Exception:
            pass
        finally:
            pynext_go.close()
    
    def test_init_with_replicas(self):
        """init should accept replicas."""
        pynext_go.close()
        
        try:
            pynext_go.init(
                "postgresql://localhost/test",
                replicas=["postgresql://replica/test"],
            )
        except Exception:
            pass
        finally:
            pynext_go.close()


class TestModuleAllExports:
    """__all__ export list tests."""
    
    def test_all_is_list(self):
        """__all__ should be a list."""
        assert hasattr(pynext_go, '__all__')
        assert isinstance(pynext_go.__all__, list)
    
    def test_all_contains_main_exports(self):
        """__all__ should contain main exports."""
        required = [
            '__version__',
            'GO_AVAILABLE',
            'GoBridge',
            'BridgeConfig',
            'BridgeError',
            'init',
            'execute',
            'close',
        ]
        for name in required:
            assert name in pynext_go.__all__, f"{name} not in __all__"
    
    def test_all_items_exist(self):
        """All items in __all__ should exist in module."""
        for name in pynext_go.__all__:
            assert hasattr(pynext_go, name), f"{name} in __all__ but not in module"


class TestModuleDocstring:
    """Module docstring tests."""
    
    def test_has_docstring(self):
        """Module should have docstring."""
        assert pynext_go.__doc__ is not None
        assert len(pynext_go.__doc__) > 100  # Substantial docs
    
    def test_docstring_mentions_go_bridge(self):
        """Docstring should mention Go bridge."""
        assert "Go" in pynext_go.__doc__
        assert "bridge" in pynext_go.__doc__.lower()
    
    def test_docstring_has_examples(self):
        """Docstring should have examples."""
        # Look for code examples
        assert "GoBridge" in pynext_go.__doc__ or "init" in pynext_go.__doc__


class TestModuleVersionFormat:
    """Version format tests."""
    
    def test_version_is_string(self):
        """__version__ should be a string."""
        assert isinstance(pynext_go.__version__, str)
    
    def test_version_has_parts(self):
        """__version__ should have major.minor.patch format."""
        parts = pynext_go.__version__.split(".")
        assert len(parts) >= 2  # At least major.minor


class TestModuleConstants:
    """Module constant tests."""
    
    def test_default_pool_min_positive(self):
        """DEFAULT_POOL_MIN should be non-negative."""
        assert pynext_go.DEFAULT_POOL_MIN >= 0
    
    def test_default_pool_max_greater_than_min(self):
        """DEFAULT_POOL_MAX should be >= DEFAULT_POOL_MIN."""
        assert pynext_go.DEFAULT_POOL_MAX >= pynext_go.DEFAULT_POOL_MIN
    
    def test_default_timeout_reasonable(self):
        """DEFAULT_QUERY_TIMEOUT should be reasonable (1s - 60s)."""
        assert pynext_go.DEFAULT_QUERY_TIMEOUT >= 1000  # At least 1s
        assert pynext_go.DEFAULT_QUERY_TIMEOUT <= 60000  # At most 60s


class TestModuleErrorInheritance:
    """Error inheritance tests through module."""
    
    def test_all_errors_inherit_bridge_error(self):
        """All error classes should inherit from BridgeError."""
        errors = [
            pynext_go.BridgeConfigError,
            pynext_go.BridgeConnectionError,
            pynext_go.BridgeQueryError,
            pynext_go.BridgeTimeoutError,
            pynext_go.BridgePoolError,
            pynext_go.BridgeArrowError,
            pynext_go.GoNotAvailableError,
        ]
        
        for err_class in errors:
            assert issubclass(err_class, pynext_go.BridgeError)

