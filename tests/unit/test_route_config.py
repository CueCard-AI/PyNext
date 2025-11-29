"""
Unit tests for Route Segment Configuration.

Tests cover:
- RouteConfig dataclass
- Enum types (Dynamic, Cache, Runtime)
- @route_config decorator
- Convenience shortcuts
- Router and server integration
- Edge cases
"""

import pytest
from typing import Optional


# ============================================
# RouteConfig Dataclass Tests (15 tests)
# ============================================

class TestRouteConfigDataclass:
    """Tests for RouteConfig dataclass."""
    
    def test_default_values(self):
        """Test default configuration values."""
        from pynext.core.route_config import RouteConfig, Dynamic, Cache, Runtime
        
        config = RouteConfig()
        
        assert config.dynamic == Dynamic.AUTO
        assert config.dynamic_params is True
        assert config.revalidate is False
        assert config.cache == Cache.AUTO
        assert config.tags == []
        assert config.runtime == Runtime.PYTHON
        assert config.max_duration == 60
        assert config.preferred_region == "auto"
    
    def test_string_to_enum_conversion(self):
        """Test automatic string to enum conversion."""
        from pynext.core.route_config import RouteConfig, Dynamic, Cache, Runtime
        
        config = RouteConfig(
            dynamic="force",
            cache="no-store",
            runtime="edge",
        )
        
        assert config.dynamic == Dynamic.FORCE
        assert config.cache == Cache.NO_STORE
        assert config.runtime == Runtime.EDGE
    
    def test_invalid_dynamic_raises(self):
        """Test invalid dynamic value raises ValueError."""
        from pynext.core.route_config import RouteConfig
        
        with pytest.raises(ValueError) as exc_info:
            RouteConfig(dynamic="invalid")
        
        assert "Invalid dynamic mode" in str(exc_info.value)
    
    def test_invalid_cache_raises(self):
        """Test invalid cache value raises ValueError."""
        from pynext.core.route_config import RouteConfig
        
        with pytest.raises(ValueError) as exc_info:
            RouteConfig(cache="invalid")
        
        assert "Invalid cache mode" in str(exc_info.value)
    
    def test_invalid_runtime_raises(self):
        """Test invalid runtime value raises ValueError."""
        from pynext.core.route_config import RouteConfig
        
        with pytest.raises(ValueError) as exc_info:
            RouteConfig(runtime="invalid")
        
        assert "Invalid runtime" in str(exc_info.value)
    
    def test_negative_max_duration_raises(self):
        """Test negative max_duration raises ValueError."""
        from pynext.core.route_config import RouteConfig
        
        with pytest.raises(ValueError) as exc_info:
            RouteConfig(max_duration=-1)
        
        assert "max_duration must be positive" in str(exc_info.value)
    
    def test_negative_revalidate_raises(self):
        """Test negative revalidate raises ValueError."""
        from pynext.core.route_config import RouteConfig
        
        with pytest.raises(ValueError) as exc_info:
            RouteConfig(revalidate=-1)
        
        assert "revalidate must be >= 0" in str(exc_info.value)
    
    def test_should_cache_no_store(self):
        """Test should_cache with NO_STORE cache."""
        from pynext.core.route_config import RouteConfig, Cache
        
        config = RouteConfig(cache=Cache.NO_STORE)
        
        assert config.should_cache() is False
    
    def test_should_cache_force(self):
        """Test should_cache with FORCE cache."""
        from pynext.core.route_config import RouteConfig, Cache
        
        config = RouteConfig(cache=Cache.FORCE)
        
        assert config.should_cache() is True
    
    def test_should_cache_dynamic_force(self):
        """Test should_cache with FORCE dynamic."""
        from pynext.core.route_config import RouteConfig, Dynamic
        
        config = RouteConfig(dynamic=Dynamic.FORCE)
        
        assert config.should_cache() is False
    
    def test_should_cache_with_revalidate(self):
        """Test should_cache with revalidate set."""
        from pynext.core.route_config import RouteConfig
        
        config = RouteConfig(revalidate=60)
        
        assert config.should_cache() is True
    
    def test_get_cache_seconds(self):
        """Test get_cache_seconds returns int."""
        from pynext.core.route_config import RouteConfig
        
        config = RouteConfig(revalidate=60)
        
        assert config.get_cache_seconds() == 60
    
    def test_get_cache_seconds_false(self):
        """Test get_cache_seconds returns None when False."""
        from pynext.core.route_config import RouteConfig
        
        config = RouteConfig(revalidate=False)
        
        assert config.get_cache_seconds() is None
    
    def test_is_static(self):
        """Test is_static check."""
        from pynext.core.route_config import RouteConfig, Dynamic
        
        assert RouteConfig(dynamic=Dynamic.STATIC).is_static() is True
        assert RouteConfig(dynamic=Dynamic.ERROR).is_static() is True
        assert RouteConfig(dynamic=Dynamic.FORCE).is_static() is False
        assert RouteConfig(dynamic=Dynamic.AUTO).is_static() is False
    
    def test_is_edge(self):
        """Test is_edge check."""
        from pynext.core.route_config import RouteConfig, Runtime
        
        assert RouteConfig(runtime=Runtime.EDGE).is_edge() is True
        assert RouteConfig(runtime=Runtime.PYTHON).is_edge() is False


# ============================================
# HTTP Headers Tests (8 tests)
# ============================================

class TestRouteConfigHeaders:
    """Tests for HTTP header generation."""
    
    def test_to_headers_no_store(self):
        """Test headers for no-store cache."""
        from pynext.core.route_config import RouteConfig, Cache
        
        config = RouteConfig(cache=Cache.NO_STORE)
        headers = config.to_headers()
        
        assert headers["Cache-Control"] == "no-store, must-revalidate"
    
    def test_to_headers_with_revalidate(self):
        """Test headers with revalidate seconds."""
        from pynext.core.route_config import RouteConfig
        
        config = RouteConfig(revalidate=60)
        headers = config.to_headers()
        
        assert "s-maxage=60" in headers["Cache-Control"]
        assert "stale-while-revalidate" in headers["Cache-Control"]
    
    def test_to_headers_revalidate_zero(self):
        """Test headers with revalidate=0."""
        from pynext.core.route_config import RouteConfig
        
        config = RouteConfig(revalidate=0)
        headers = config.to_headers()
        
        assert headers["Cache-Control"] == "no-cache, must-revalidate"
    
    def test_to_headers_force_cache(self):
        """Test headers with force cache."""
        from pynext.core.route_config import RouteConfig, Cache
        
        config = RouteConfig(cache=Cache.FORCE)
        headers = config.to_headers()
        
        assert "immutable" in headers["Cache-Control"]
    
    def test_to_headers_with_tags(self):
        """Test X-Cache-Tags header."""
        from pynext.core.route_config import RouteConfig
        
        config = RouteConfig(tags=["products", "featured"])
        headers = config.to_headers()
        
        assert headers["X-Cache-Tags"] == "products,featured"
    
    def test_to_headers_empty_tags(self):
        """Test no X-Cache-Tags with empty tags."""
        from pynext.core.route_config import RouteConfig
        
        config = RouteConfig(tags=[])
        headers = config.to_headers()
        
        assert "X-Cache-Tags" not in headers
    
    def test_to_headers_default(self):
        """Test default config has no cache headers."""
        from pynext.core.route_config import RouteConfig
        
        config = RouteConfig()
        headers = config.to_headers()
        
        assert "Cache-Control" not in headers
    
    def test_to_headers_multiple_tags(self):
        """Test multiple cache tags joined correctly."""
        from pynext.core.route_config import RouteConfig
        
        config = RouteConfig(tags=["a", "b", "c"])
        headers = config.to_headers()
        
        assert headers["X-Cache-Tags"] == "a,b,c"


# ============================================
# Dynamic Enum Tests (8 tests)
# ============================================

class TestDynamicEnum:
    """Tests for Dynamic enum."""
    
    def test_all_values_exist(self):
        """Test all expected values exist."""
        from pynext.core.route_config import Dynamic
        
        assert hasattr(Dynamic, "AUTO")
        assert hasattr(Dynamic, "FORCE")
        assert hasattr(Dynamic, "ERROR")
        assert hasattr(Dynamic, "STATIC")
    
    def test_values_are_strings(self):
        """Test enum values are strings."""
        from pynext.core.route_config import Dynamic
        
        assert Dynamic.AUTO.value == "auto"
        assert Dynamic.FORCE.value == "force"
        assert Dynamic.ERROR.value == "error"
        assert Dynamic.STATIC.value == "static"
    
    def test_string_comparison(self):
        """Test string comparison works."""
        from pynext.core.route_config import Dynamic
        
        assert Dynamic.AUTO == "auto"
        assert Dynamic.FORCE == "force"
    
    def test_from_string(self):
        """Test creating from string."""
        from pynext.core.route_config import Dynamic
        
        assert Dynamic("auto") == Dynamic.AUTO
        assert Dynamic("force") == Dynamic.FORCE
    
    def test_invalid_string_raises(self):
        """Test invalid string raises ValueError."""
        from pynext.core.route_config import Dynamic
        
        with pytest.raises(ValueError):
            Dynamic("invalid")
    
    def test_is_dynamic_method(self):
        """Test is_dynamic method on RouteConfig."""
        from pynext.core.route_config import RouteConfig, Dynamic
        
        assert RouteConfig(dynamic=Dynamic.FORCE).is_dynamic() is True
        assert RouteConfig(dynamic=Dynamic.AUTO).is_dynamic() is False
    
    def test_enum_in_dataclass(self):
        """Test enum works in dataclass field."""
        from pynext.core.route_config import RouteConfig, Dynamic
        
        config = RouteConfig(dynamic=Dynamic.FORCE)
        
        assert config.dynamic == Dynamic.FORCE
        assert isinstance(config.dynamic, Dynamic)
    
    def test_enum_serialization(self):
        """Test enum serializes to string."""
        from pynext.core.route_config import RouteConfig, Dynamic
        
        config = RouteConfig(dynamic=Dynamic.FORCE)
        data = config.to_dict()
        
        assert data["dynamic"] == "force"


# ============================================
# Cache Enum Tests (6 tests)
# ============================================

class TestCacheEnum:
    """Tests for Cache enum."""
    
    def test_all_values_exist(self):
        """Test all expected values exist."""
        from pynext.core.route_config import Cache
        
        assert hasattr(Cache, "AUTO")
        assert hasattr(Cache, "FORCE")
        assert hasattr(Cache, "NO_STORE")
    
    def test_values_are_strings(self):
        """Test enum values are strings."""
        from pynext.core.route_config import Cache
        
        assert Cache.AUTO.value == "auto"
        assert Cache.FORCE.value == "force"
        assert Cache.NO_STORE.value == "no-store"
    
    def test_string_comparison(self):
        """Test string comparison works."""
        from pynext.core.route_config import Cache
        
        assert Cache.NO_STORE == "no-store"
    
    def test_from_string(self):
        """Test creating from string."""
        from pynext.core.route_config import Cache
        
        assert Cache("no-store") == Cache.NO_STORE
    
    def test_enum_in_dataclass(self):
        """Test enum works in dataclass field."""
        from pynext.core.route_config import RouteConfig, Cache
        
        config = RouteConfig(cache=Cache.NO_STORE)
        
        assert config.cache == Cache.NO_STORE
    
    def test_enum_serialization(self):
        """Test enum serializes to string."""
        from pynext.core.route_config import RouteConfig, Cache
        
        config = RouteConfig(cache=Cache.NO_STORE)
        data = config.to_dict()
        
        assert data["cache"] == "no-store"


# ============================================
# Runtime Enum Tests (4 tests)
# ============================================

class TestRuntimeEnum:
    """Tests for Runtime enum."""
    
    def test_all_values_exist(self):
        """Test all expected values exist."""
        from pynext.core.route_config import Runtime
        
        assert hasattr(Runtime, "PYTHON")
        assert hasattr(Runtime, "EDGE")
    
    def test_values_are_strings(self):
        """Test enum values are strings."""
        from pynext.core.route_config import Runtime
        
        assert Runtime.PYTHON.value == "python"
        assert Runtime.EDGE.value == "edge"
    
    def test_from_string(self):
        """Test creating from string."""
        from pynext.core.route_config import Runtime
        
        assert Runtime("edge") == Runtime.EDGE
    
    def test_enum_serialization(self):
        """Test enum serializes to string."""
        from pynext.core.route_config import RouteConfig, Runtime
        
        config = RouteConfig(runtime=Runtime.EDGE)
        data = config.to_dict()
        
        assert data["runtime"] == "edge"


# ============================================
# Decorator Tests (12 tests)
# ============================================

class TestRouteConfigDecorator:
    """Tests for @route_config decorator."""
    
    def setup_method(self):
        """Clear global registry before each test."""
        from pynext.core.route_config import clear_configs
        clear_configs()
    
    def test_basic_decorator(self):
        """Test basic decorator application."""
        from pynext.core.route_config import route_config, get_route_config
        
        @route_config(dynamic="force")
        def my_page():
            return "Hello"
        
        config = get_route_config(my_page)
        
        assert config is not None
        assert config.dynamic.value == "force"
    
    def test_decorator_with_all_params(self):
        """Test decorator with all parameters."""
        from pynext.core.route_config import route_config, get_route_config
        
        @route_config(
            dynamic="static",
            revalidate=60,
            cache="force",
            tags=["test"],
            runtime="edge",
            max_duration=30,
            dynamic_params=False,
            preferred_region=["us-east-1"],
        )
        def my_page():
            return "Hello"
        
        config = get_route_config(my_page)
        
        assert config.dynamic.value == "static"
        assert config.revalidate == 60
        assert config.cache.value == "force"
        assert config.tags == ["test"]
        assert config.runtime.value == "edge"
        assert config.max_duration == 30
        assert config.dynamic_params is False
        assert config.preferred_region == ["us-east-1"]
    
    def test_decorator_preserves_function(self):
        """Test decorator preserves function attributes."""
        from pynext.core.route_config import route_config
        
        @route_config()
        def my_page():
            """My docstring."""
            return "Hello"
        
        assert my_page.__name__ == "my_page"
        assert my_page.__doc__ == "My docstring."
    
    def test_decorator_function_still_callable(self):
        """Test decorated function is still callable."""
        from pynext.core.route_config import route_config
        
        @route_config()
        def my_page():
            return "Hello"
        
        result = my_page()
        
        assert result == "Hello"
    
    def test_has_route_config(self):
        """Test has_route_config helper."""
        from pynext.core.route_config import route_config, has_route_config
        
        @route_config()
        def with_config():
            pass
        
        def without_config():
            pass
        
        assert has_route_config(with_config) is True
        assert has_route_config(without_config) is False
    
    def test_get_route_config_none(self):
        """Test get_route_config returns None for undecorated."""
        from pynext.core.route_config import get_route_config
        
        def my_page():
            pass
        
        assert get_route_config(my_page) is None
    
    def test_decorator_stacking(self):
        """Test decorator works with other decorators."""
        from pynext.core.route_config import route_config, get_route_config
        
        def other_decorator(fn):
            fn.other_attr = True
            return fn
        
        @other_decorator
        @route_config(dynamic="force")
        def my_page():
            return "Hello"
        
        config = get_route_config(my_page)
        
        assert config is not None
        assert hasattr(my_page, "other_attr")
    
    def test_global_registry(self):
        """Test configs are registered globally."""
        from pynext.core.route_config import route_config, get_all_configs
        
        @route_config(dynamic="force")
        def page_a():
            pass
        
        @route_config(dynamic="static")
        def page_b():
            pass
        
        configs = get_all_configs()
        
        assert len(configs) >= 2
    
    def test_decorator_with_enums(self):
        """Test decorator with enum values directly."""
        from pynext.core.route_config import route_config, get_route_config, Dynamic, Cache, Runtime
        
        @route_config(
            dynamic=Dynamic.FORCE,
            cache=Cache.NO_STORE,
            runtime=Runtime.EDGE,
        )
        def my_page():
            return "Hello"
        
        config = get_route_config(my_page)
        
        assert config.dynamic == Dynamic.FORCE
        assert config.cache == Cache.NO_STORE
        assert config.runtime == Runtime.EDGE
    
    def test_decorator_default_tags(self):
        """Test decorator with None tags defaults to empty list."""
        from pynext.core.route_config import route_config, get_route_config
        
        @route_config()
        def my_page():
            pass
        
        config = get_route_config(my_page)
        
        assert config.tags == []
    
    def test_get_effective_config_decorated(self):
        """Test get_effective_config on decorated function."""
        from pynext.core.route_config import route_config, get_effective_config, Dynamic
        
        @route_config(dynamic="force")
        def my_page():
            pass
        
        config = get_effective_config(my_page)
        
        assert config.dynamic == Dynamic.FORCE
    
    def test_get_effective_config_undecorated(self):
        """Test get_effective_config returns default for undecorated."""
        from pynext.core.route_config import get_effective_config, Dynamic
        
        def my_page():
            pass
        
        config = get_effective_config(my_page)
        
        assert config.dynamic == Dynamic.AUTO


# ============================================
# Shortcuts Tests (8 tests)
# ============================================

class TestRouteConfigShortcuts:
    """Tests for convenience shortcut functions."""
    
    def setup_method(self):
        """Clear global registry before each test."""
        from pynext.core.route_config import clear_configs
        clear_configs()
    
    def test_static_route(self):
        """Test static_route shortcut."""
        from pynext.core.route_config import static_route, get_route_config, Dynamic
        
        @static_route(revalidate=3600)
        def my_page():
            pass
        
        config = get_route_config(my_page)
        
        assert config.dynamic == Dynamic.STATIC
        assert config.revalidate == 3600
    
    def test_static_route_with_tags(self):
        """Test static_route with tags."""
        from pynext.core.route_config import static_route, get_route_config
        
        @static_route(revalidate=60, tags=["products"])
        def my_page():
            pass
        
        config = get_route_config(my_page)
        
        assert config.tags == ["products"]
    
    def test_dynamic_route(self):
        """Test dynamic_route shortcut."""
        from pynext.core.route_config import dynamic_route, get_route_config, Dynamic, Cache
        
        @dynamic_route()
        def my_page():
            pass
        
        config = get_route_config(my_page)
        
        assert config.dynamic == Dynamic.FORCE
        assert config.cache == Cache.NO_STORE
    
    def test_dynamic_route_with_cache(self):
        """Test dynamic_route with cache enabled."""
        from pynext.core.route_config import dynamic_route, get_route_config, Cache
        
        @dynamic_route(cache=True)
        def my_page():
            pass
        
        config = get_route_config(my_page)
        
        assert config.cache == Cache.AUTO
    
    def test_edge_route(self):
        """Test edge_route shortcut."""
        from pynext.core.route_config import edge_route, get_route_config, Runtime
        
        @edge_route(max_duration=10)
        def my_page():
            pass
        
        config = get_route_config(my_page)
        
        assert config.runtime == Runtime.EDGE
        assert config.max_duration == 10
    
    def test_edge_route_with_region(self):
        """Test edge_route with preferred region."""
        from pynext.core.route_config import edge_route, get_route_config
        
        @edge_route(preferred_region="us-east-1")
        def my_page():
            pass
        
        config = get_route_config(my_page)
        
        assert config.preferred_region == "us-east-1"
    
    def test_cached_route(self):
        """Test cached_route shortcut."""
        from pynext.core.route_config import cached_route, get_route_config
        
        @cached_route(300, tags=["data"])
        def my_page():
            pass
        
        config = get_route_config(my_page)
        
        assert config.revalidate == 300
        assert config.tags == ["data"]
    
    def test_no_cache_route(self):
        """Test no_cache_route shortcut."""
        from pynext.core.route_config import no_cache_route, get_route_config, Cache
        
        @no_cache_route()
        def my_page():
            pass
        
        config = get_route_config(my_page)
        
        assert config.cache == Cache.NO_STORE


# ============================================
# Serialization Tests (6 tests)
# ============================================

class TestRouteConfigSerialization:
    """Tests for serialization/deserialization."""
    
    def test_to_dict(self):
        """Test to_dict serialization."""
        from pynext.core.route_config import RouteConfig
        
        config = RouteConfig(
            dynamic="force",
            revalidate=60,
            tags=["test"],
        )
        
        data = config.to_dict()
        
        assert data["dynamic"] == "force"
        assert data["revalidate"] == 60
        assert data["tags"] == ["test"]
    
    def test_from_dict(self):
        """Test from_dict deserialization."""
        from pynext.core.route_config import RouteConfig, Dynamic
        
        data = {
            "dynamic": "force",
            "revalidate": 60,
            "tags": ["test"],
        }
        
        config = RouteConfig.from_dict(data)
        
        assert config.dynamic == Dynamic.FORCE
        assert config.revalidate == 60
        assert config.tags == ["test"]
    
    def test_from_dict_missing_fields(self):
        """Test from_dict with missing fields uses defaults."""
        from pynext.core.route_config import RouteConfig, Dynamic
        
        data = {"dynamic": "static"}
        
        config = RouteConfig.from_dict(data)
        
        assert config.dynamic == Dynamic.STATIC
        assert config.revalidate is False
        assert config.max_duration == 60
    
    def test_roundtrip(self):
        """Test serialization roundtrip."""
        from pynext.core.route_config import RouteConfig
        
        original = RouteConfig(
            dynamic="force",
            revalidate=120,
            cache="no-store",
            tags=["a", "b"],
            runtime="edge",
            max_duration=30,
        )
        
        data = original.to_dict()
        restored = RouteConfig.from_dict(data)
        
        assert restored.dynamic == original.dynamic
        assert restored.revalidate == original.revalidate
        assert restored.cache == original.cache
        assert restored.tags == original.tags
        assert restored.runtime == original.runtime
        assert restored.max_duration == original.max_duration
    
    def test_merge_with(self):
        """Test merge_with method."""
        from pynext.core.route_config import RouteConfig, Dynamic
        
        base = RouteConfig(
            dynamic="static",
            revalidate=60,
            tags=["base"],
        )
        
        override = RouteConfig(
            dynamic="force",
            tags=["override"],
        )
        
        merged = base.merge_with(override)
        
        assert merged.dynamic == Dynamic.FORCE
        assert merged.revalidate == 60  # From base (override is False)
        assert set(merged.tags) == {"base", "override"}
    
    def test_merge_with_auto_values(self):
        """Test merge_with preserves base when override is auto."""
        from pynext.core.route_config import RouteConfig, Dynamic
        
        base = RouteConfig(dynamic="static")
        override = RouteConfig(dynamic="auto")  # AUTO doesn't override
        
        merged = base.merge_with(override)
        
        assert merged.dynamic == Dynamic.STATIC


# ============================================
# Integration Tests (10 tests)
# ============================================

class TestRouteConfigIntegration:
    """Integration tests with router and server."""
    
    def setup_method(self):
        """Clear global registry before each test."""
        from pynext.core.route_config import clear_configs
        clear_configs()
    
    def test_path_config_registry(self):
        """Test path config registration."""
        from pynext.core.route_config import register_path_config, get_config_by_path, RouteConfig
        
        config = RouteConfig(revalidate=60)
        register_path_config("/products/[id]", config)
        
        result = get_config_by_path("/products/[id]")
        
        assert result is config
    
    def test_path_config_not_found(self):
        """Test get_config_by_path returns None for unknown path."""
        from pynext.core.route_config import get_config_by_path
        
        result = get_config_by_path("/unknown")
        
        assert result is None
    
    def test_config_on_page_component(self):
        """Test config extraction from page component."""
        from pynext.core.route_config import route_config, get_route_config
        from pynext.core.component import page
        
        @route_config(dynamic="force")
        @page
        def MyPage():
            return "Hello"
        
        config = get_route_config(MyPage)
        
        assert config is not None
    
    def test_config_headers_applied(self):
        """Test headers are correctly generated."""
        from pynext.core.route_config import RouteConfig
        
        config = RouteConfig(
            revalidate=300,
            tags=["products", "featured"],
        )
        
        headers = config.to_headers()
        
        assert "s-maxage=300" in headers["Cache-Control"]
        assert headers["X-Cache-Tags"] == "products,featured"
    
    def test_clear_configs(self):
        """Test clear_configs clears all registries."""
        from pynext.core.route_config import (
            route_config, register_path_config, RouteConfig,
            get_all_configs, get_config_by_path, clear_configs
        )
        
        @route_config(dynamic="force")
        def my_page():
            pass
        
        register_path_config("/test", RouteConfig())
        
        clear_configs()
        
        assert len(get_all_configs()) == 0
        assert get_config_by_path("/test") is None
    
    def test_multiple_pages_independent_configs(self):
        """Test multiple pages have independent configs."""
        from pynext.core.route_config import route_config, get_route_config
        
        @route_config(dynamic="force")
        def page_a():
            pass
        
        @route_config(dynamic="static")
        def page_b():
            pass
        
        config_a = get_route_config(page_a)
        config_b = get_route_config(page_b)
        
        assert config_a.dynamic.value == "force"
        assert config_b.dynamic.value == "static"
    
    def test_config_with_isr_integration(self):
        """Test config works with ISR settings."""
        from pynext.core.route_config import RouteConfig
        
        config = RouteConfig(
            revalidate=60,
            tags=["blog", "posts"],
        )
        
        assert config.should_cache() is True
        assert config.get_cache_seconds() == 60
        assert config.tags == ["blog", "posts"]
    
    def test_edge_config_constraints(self):
        """Test edge runtime config constraints."""
        from pynext.core.route_config import RouteConfig, Runtime
        
        config = RouteConfig(
            runtime=Runtime.EDGE,
            max_duration=30,
            preferred_region=["us-east-1", "eu-west-1"],
        )
        
        assert config.is_edge() is True
        assert config.max_duration == 30
        assert config.preferred_region == ["us-east-1", "eu-west-1"]
    
    def test_config_repr(self):
        """Test RouteConfig has readable repr."""
        from pynext.core.route_config import RouteConfig
        
        config = RouteConfig(dynamic="force", revalidate=60)
        
        repr_str = repr(config)
        
        assert "RouteConfig" in repr_str
        assert "FORCE" in repr_str or "force" in repr_str
    
    def test_exports_from_pynext(self):
        """Test all exports are available from pynext."""
        from pynext import (
            RouteConfig,
            Dynamic,
            Cache,
            Runtime,
            route_config,
            get_route_config,
            has_route_config,
            static_route,
            dynamic_route,
            edge_route,
            cached_route,
            no_cache_route,
        )
        
        # All imports should work
        assert RouteConfig is not None
        assert Dynamic is not None
        assert Cache is not None
        assert Runtime is not None


# ============================================
# Edge Cases Tests (7 tests)
# ============================================

class TestRouteConfigEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_zero_revalidate(self):
        """Test revalidate=0 (every request)."""
        from pynext.core.route_config import RouteConfig
        
        config = RouteConfig(revalidate=0)
        
        assert config.should_cache() is True  # Still caches, just validates every time
        assert config.get_cache_seconds() == 0
    
    def test_very_large_revalidate(self):
        """Test very large revalidate value."""
        from pynext.core.route_config import RouteConfig
        
        config = RouteConfig(revalidate=31536000)  # 1 year
        
        assert config.get_cache_seconds() == 31536000
    
    def test_empty_tags_list(self):
        """Test empty tags list."""
        from pynext.core.route_config import RouteConfig
        
        config = RouteConfig(tags=[])
        
        headers = config.to_headers()
        
        assert "X-Cache-Tags" not in headers
    
    def test_single_tag(self):
        """Test single tag."""
        from pynext.core.route_config import RouteConfig
        
        config = RouteConfig(tags=["single"])
        
        headers = config.to_headers()
        
        assert headers["X-Cache-Tags"] == "single"
    
    def test_preferred_region_list(self):
        """Test preferred_region as list."""
        from pynext.core.route_config import RouteConfig
        
        config = RouteConfig(preferred_region=["us-east-1", "eu-west-1"])
        
        assert config.preferred_region == ["us-east-1", "eu-west-1"]
    
    def test_preferred_region_string(self):
        """Test preferred_region as string."""
        from pynext.core.route_config import RouteConfig
        
        config = RouteConfig(preferred_region="global")
        
        assert config.preferred_region == "global"
    
    def test_conflicting_settings(self):
        """Test behavior with conflicting settings."""
        from pynext.core.route_config import RouteConfig, Dynamic, Cache
        
        # Force dynamic but also force cache - dynamic wins for should_cache
        config = RouteConfig(
            dynamic=Dynamic.FORCE,
            cache=Cache.FORCE,
        )
        
        # Cache.FORCE takes precedence in should_cache
        assert config.should_cache() is True

