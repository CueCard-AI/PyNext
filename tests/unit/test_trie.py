"""
Unit tests for PyNext radix trie router.

Tests route insertion, matching, and performance characteristics.
"""

import pytest
from pynext.router.trie import RouteTrie, LayoutCache, SpecialFilesCache


class TestRouteTrie:
    """Tests for the RouteTrie class."""
    
    def test_insert_and_match_static(self):
        """Insert and match static routes."""
        trie = RouteTrie()
        trie.insert("/", "root")
        trie.insert("/about", "about")
        trie.insert("/users", "users_list")
        trie.insert("/users/settings", "user_settings")
        
        assert trie.match("/") == ("root", {})
        assert trie.match("/about") == ("about", {})
        assert trie.match("/users") == ("users_list", {})
        assert trie.match("/users/settings") == ("user_settings", {})
    
    def test_match_not_found(self):
        """Non-existent routes return None."""
        trie = RouteTrie()
        trie.insert("/about", "about")
        
        route, params = trie.match("/contact")
        assert route is None
        assert params == {}
    
    def test_dynamic_routes(self):
        """Dynamic routes match and extract params."""
        trie = RouteTrie()
        trie.insert("/users/:id", "user_profile")
        trie.insert("/posts/:id/comments/:commentId", "comment")
        
        route, params = trie.match("/users/123")
        assert route == "user_profile"
        assert params == {"id": "123"}
        
        route, params = trie.match("/posts/42/comments/99")
        assert route == "comment"
        assert params == {"id": "42", "commentId": "99"}
    
    def test_static_over_dynamic_priority(self):
        """Static routes take priority over dynamic."""
        trie = RouteTrie()
        trie.insert("/users/:id", "dynamic")
        trie.insert("/users/me", "static")
        
        route, params = trie.match("/users/me")
        assert route == "static"
        assert params == {}
        
        route, params = trie.match("/users/123")
        assert route == "dynamic"
        assert params == {"id": "123"}
    
    def test_catch_all_routes(self):
        """Catch-all routes match remaining path."""
        trie = RouteTrie()
        trie.insert("/docs/*slug", "docs")
        
        route, params = trie.match("/docs/api")
        assert route == "docs"
        assert params == {"slug": "api"}
        
        route, params = trie.match("/docs/api/reference/signals")
        assert route == "docs"
        assert params == {"slug": "api/reference/signals"}
    
    def test_optional_catch_all(self):
        """Optional catch-all matches with or without remainder."""
        trie = RouteTrie()
        trie.insert("/docs/*slug?", "docs")
        
        route, params = trie.match("/docs")
        assert route == "docs"
        assert params == {"slug": ""}
        
        route, params = trie.match("/docs/getting-started")
        assert route == "docs"
        assert params == {"slug": "getting-started"}
    
    def test_dynamic_over_catch_all_priority(self):
        """Dynamic routes take priority over catch-all."""
        trie = RouteTrie()
        trie.insert("/files/*path", "catch_all")
        trie.insert("/files/:id", "dynamic")
        
        # For single segment, dynamic should match
        route, params = trie.match("/files/123")
        assert route == "dynamic"
        assert params == {"id": "123"}
        
        # For multiple segments, catch-all should match
        route, params = trie.match("/files/a/b/c")
        assert route == "catch_all"
        assert params == {"path": "a/b/c"}
    
    def test_empty_path(self):
        """Root path matches correctly."""
        trie = RouteTrie()
        trie.insert("/", "home")
        
        route, params = trie.match("/")
        assert route == "home"
        assert params == {}
    
    def test_trailing_slash_normalization(self):
        """Trailing slashes are normalized."""
        trie = RouteTrie()
        trie.insert("/about/", "about")
        
        route, params = trie.match("/about")
        assert route == "about"
    
    def test_length(self):
        """Length returns route count."""
        trie = RouteTrie()
        assert len(trie) == 0
        
        trie.insert("/a", "a")
        assert len(trie) == 1
        
        trie.insert("/b", "b")
        trie.insert("/c/:id", "c")
        assert len(trie) == 3
    
    def test_get_all_routes(self):
        """Get all routes for debugging."""
        trie = RouteTrie()
        trie.insert("/", "root")
        trie.insert("/users", "users")
        trie.insert("/users/:id", "user")
        
        routes = trie.get_all_routes()
        
        assert len(routes) == 3
        paths = [path for path, _ in routes]
        assert "/" in paths
        assert "/users" in paths
        assert "/users/:id" in paths


class TestLayoutCache:
    """Tests for the LayoutCache class."""
    
    def test_single_layout(self):
        """Single root layout."""
        cache = LayoutCache()
        cache.add_layout("", "root_layout")
        
        chain = cache.get_chain("")
        assert chain == ["root_layout"]
        
        chain = cache.get_chain("users")
        assert chain == ["root_layout"]
    
    def test_nested_layouts(self):
        """Nested layouts are returned in order."""
        cache = LayoutCache()
        cache.add_layout("", "root")
        cache.add_layout("dashboard", "dashboard")
        cache.add_layout("dashboard/settings", "settings")
        
        chain = cache.get_chain("")
        assert chain == ["root"]
        
        chain = cache.get_chain("dashboard")
        assert chain == ["root", "dashboard"]
        
        chain = cache.get_chain("dashboard/settings")
        assert chain == ["root", "dashboard", "settings"]
        
        chain = cache.get_chain("dashboard/settings/profile")
        assert chain == ["root", "dashboard", "settings"]
    
    def test_skip_missing_intermediate(self):
        """Skip directories without layouts."""
        cache = LayoutCache()
        cache.add_layout("", "root")
        cache.add_layout("a/b/c", "deep")
        
        chain = cache.get_chain("a/b/c")
        assert chain == ["root", "deep"]
        
        chain = cache.get_chain("a/b")
        assert chain == ["root"]
    
    def test_caching(self):
        """Results are cached."""
        cache = LayoutCache()
        cache.add_layout("", "root")
        
        chain1 = cache.get_chain("users")
        chain2 = cache.get_chain("users")
        
        # Should be same object (cached)
        assert chain1 is chain2
    
    def test_clear(self):
        """Clear removes all layouts."""
        cache = LayoutCache()
        cache.add_layout("", "root")
        
        cache.clear()
        
        chain = cache.get_chain("")
        assert chain == []


class TestSpecialFilesCache:
    """Tests for the SpecialFilesCache class."""
    
    def test_direct_match(self):
        """Direct handler match."""
        cache = SpecialFilesCache()
        cache.add("users", "users_loading")
        
        handler = cache.get("users")
        assert handler == "users_loading"
    
    def test_inheritance(self):
        """Handlers are inherited from parent directories."""
        cache = SpecialFilesCache()
        cache.add("", "root_loading")
        
        handler = cache.get("users")
        assert handler == "root_loading"
        
        handler = cache.get("users/profile")
        assert handler == "root_loading"
    
    def test_closest_wins(self):
        """Closest handler wins."""
        cache = SpecialFilesCache()
        cache.add("", "root")
        cache.add("dashboard", "dashboard")
        
        handler = cache.get("dashboard")
        assert handler == "dashboard"
        
        handler = cache.get("dashboard/settings")
        assert handler == "dashboard"
        
        handler = cache.get("users")
        assert handler == "root"
    
    def test_no_handler(self):
        """Return None if no handler found."""
        cache = SpecialFilesCache()
        
        handler = cache.get("users")
        assert handler is None
    
    def test_caching(self):
        """Resolved handlers are cached."""
        cache = SpecialFilesCache()
        cache.add("", "root")
        
        handler1 = cache.get("users")
        handler2 = cache.get("users")
        
        assert handler1 == handler2


class TestTriePerformance:
    """Performance tests for the trie."""
    
    def test_many_static_routes(self):
        """Trie handles many static routes."""
        trie = RouteTrie()
        
        # Insert 1000 routes
        for i in range(1000):
            trie.insert(f"/page{i}", f"handler_{i}")
        
        assert len(trie) == 1000
        
        # All should match
        route, _ = trie.match("/page500")
        assert route == "handler_500"
        
        route, _ = trie.match("/page999")
        assert route == "handler_999"
    
    def test_many_dynamic_routes(self):
        """Trie handles many dynamic routes."""
        trie = RouteTrie()
        
        for i in range(100):
            trie.insert(f"/section{i}/:id", f"handler_{i}")
        
        assert len(trie) == 100
        
        route, params = trie.match("/section50/123")
        assert route == "handler_50"
        assert params == {"id": "123"}
    
    def test_deep_nesting(self):
        """Trie handles deep nesting."""
        trie = RouteTrie()
        
        # Create a very deep route
        trie.insert("/a/b/c/d/e/f/g/h/i/j", "deep")
        trie.insert("/a/b/c/d/e/f/g/h/i/:id", "dynamic")
        
        route, _ = trie.match("/a/b/c/d/e/f/g/h/i/j")
        assert route == "deep"
        
        route, params = trie.match("/a/b/c/d/e/f/g/h/i/123")
        assert route == "dynamic"
        assert params == {"id": "123"}


class TestTrieEdgeCases:
    """Edge cases for the trie."""
    
    def test_similar_static_routes(self):
        """Similar static routes are distinct."""
        trie = RouteTrie()
        trie.insert("/user", "user")
        trie.insert("/users", "users")
        trie.insert("/users/list", "users_list")
        
        assert trie.match("/user")[0] == "user"
        assert trie.match("/users")[0] == "users"
        assert trie.match("/users/list")[0] == "users_list"
    
    def test_multiple_dynamic_segments(self):
        """Multiple dynamic segments work."""
        trie = RouteTrie()
        trie.insert("/:a/:b/:c/:d", "four_params")
        
        route, params = trie.match("/1/2/3/4")
        assert route == "four_params"
        assert params == {"a": "1", "b": "2", "c": "3", "d": "4"}
    
    def test_mixed_static_dynamic(self):
        """Mixed static and dynamic segments."""
        trie = RouteTrie()
        trie.insert("/api/:version/users/:id/posts", "user_posts")
        
        route, params = trie.match("/api/v1/users/123/posts")
        assert route == "user_posts"
        assert params == {"version": "v1", "id": "123"}

