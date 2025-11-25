"""
Unit tests for PyNext file-based router.

Tests route matching, dynamic routes, and layout resolution.
"""

import pytest
from pathlib import Path
from pynext.router.file_router import FileRouter, Route, get_params, get_query
from pynext.router.dynamic import (
    RoutePattern,
    file_path_to_route,
    match_route,
    parse_dynamic_segment,
)


class TestRoutePattern:
    """Tests for RoutePattern creation."""
    
    def test_static_route(self):
        """Static route pattern."""
        pattern = file_path_to_route("about.py")
        
        assert pattern.url_pattern == "/about"
        assert len(pattern.params) == 0  # No params = static
        assert not pattern.is_catch_all
    
    def test_index_route(self):
        """Index route becomes root path."""
        pattern = file_path_to_route("index.py")
        
        assert pattern.url_pattern == "/"
    
    def test_nested_static_route(self):
        """Nested static route."""
        pattern = file_path_to_route("blog/posts.py")
        
        assert pattern.url_pattern == "/blog/posts"
    
    def test_dynamic_route(self):
        """Dynamic route with [param]."""
        pattern = file_path_to_route("users/[id].py")
        
        assert pattern.url_pattern == "/users/:id"
        assert len(pattern.params) > 0  # Has params = dynamic
        assert "id" in pattern.params
    
    def test_catch_all_route(self):
        """Catch-all route with [...slug]."""
        pattern = file_path_to_route("docs/[...slug].py")
        
        assert pattern.is_catch_all
        assert "slug" in pattern.params
    
    def test_optional_catch_all(self):
        """Optional catch-all with [[...slug]]."""
        pattern = file_path_to_route("docs/[[...slug]].py")
        
        assert pattern.is_optional_catch_all
    
    def test_multiple_dynamic_segments(self):
        """Route with multiple dynamic segments."""
        pattern = file_path_to_route("users/[userId]/posts/[postId].py")
        
        assert len(pattern.params) > 0  # Has params
        assert "userId" in pattern.params
        assert "postId" in pattern.params


class TestRouteMatching:
    """Tests for route matching."""
    
    def test_match_static_route(self):
        """Match static route."""
        pattern = file_path_to_route("about.py")
        
        result = match_route("/about", pattern)
        assert result is not None
        assert result == {}
    
    def test_no_match_static_route(self):
        """No match for different path."""
        pattern = file_path_to_route("about.py")
        
        result = match_route("/contact", pattern)
        assert result is None
    
    def test_match_dynamic_route(self):
        """Match dynamic route extracts params."""
        pattern = file_path_to_route("users/[id].py")
        
        result = match_route("/users/123", pattern)
        assert result is not None
        assert result["id"] == "123"
    
    def test_match_multiple_params(self):
        """Match route with multiple params."""
        pattern = file_path_to_route("users/[userId]/posts/[postId].py")
        
        result = match_route("/users/42/posts/99", pattern)
        assert result is not None
        assert result["userId"] == "42"
        assert result["postId"] == "99"
    
    def test_match_catch_all(self):
        """Match catch-all route."""
        pattern = file_path_to_route("docs/[...slug].py")
        
        result = match_route("/docs/api/reference/signals", pattern)
        assert result is not None
        assert result["slug"] == "api/reference/signals"
    
    def test_match_index(self):
        """Match index route."""
        pattern = file_path_to_route("index.py")
        
        result = match_route("/", pattern)
        assert result is not None


class TestFileRouter:
    """Tests for FileRouter."""
    
    def test_create_router(self, temp_pages_dir):
        """Create a FileRouter."""
        router = FileRouter(str(temp_pages_dir))
        # Compare resolved paths (handles /private vs /var symlink on macOS)
        assert router.pages_dir.resolve() == temp_pages_dir.resolve()
    
    def test_scan_empty_directory(self, empty_router):
        """Scanning empty directory returns no routes."""
        empty_router.scan()
        assert len(empty_router.routes) == 0
    
    def test_scan_finds_pages(self, router):
        """Scanning finds page files."""
        assert len(router.routes) > 0
    
    def test_match_route(self, router):
        """Router matches routes correctly."""
        route, params = router.match("/")
        assert route is not None
    
    def test_match_dynamic_route(self, router):
        """Router matches dynamic routes and extracts params."""
        route, params = router.match("/users/123")
        
        assert route is not None
        assert params.get("id") == "123"
    
    def test_no_match_returns_none(self, router):
        """Router returns None for unmatched paths."""
        route, params = router.match("/nonexistent/path")
        assert route is None
    
    def test_match_api_route(self, router):
        """Router matches API routes."""
        route, params = router.match_api("/api/health")
        assert route is not None
    
    def test_get_routes_info(self, router):
        """Router provides route information."""
        info = router.get_routes_info()
        
        assert isinstance(info, list)
        assert len(info) > 0
        
        for route_info in info:
            assert "type" in route_info
            assert "pattern" in route_info


class TestLayoutResolution:
    """Tests for layout chain resolution."""
    
    def test_root_layout(self, temp_pages_dir):
        """Root layout applies to all routes."""
        # Create root layout
        (temp_pages_dir / "layout.py").write_text('''
from pynext import layout, div

@layout
def root_layout(children):
    return div(class_="root")[children]
''')
        
        # Create page
        (temp_pages_dir / "index.py").write_text('''
from pynext import page, div

@page
def index():
    return div()["Home"]
''')
        
        router = FileRouter(str(temp_pages_dir))
        router.scan()
        
        route, _ = router.match("/")
        assert route is not None
        assert len(route.layouts) == 1
    
    def test_nested_layout(self, temp_pages_dir):
        """Nested layouts are applied in order."""
        # Create root layout
        (temp_pages_dir / "layout.py").write_text('''
from pynext import layout, div

@layout
def root_layout(children):
    return div(class_="root")[children]
''')
        
        # Create dashboard directory with layout
        dashboard_dir = temp_pages_dir / "dashboard"
        dashboard_dir.mkdir()
        
        (dashboard_dir / "layout.py").write_text('''
from pynext import layout, div

@layout
def dashboard_layout(children):
    return div(class_="dashboard")[children]
''')
        
        (dashboard_dir / "index.py").write_text('''
from pynext import page, div

@page
def dashboard():
    return div()["Dashboard"]
''')
        
        router = FileRouter(str(temp_pages_dir))
        router.scan()
        
        route, _ = router.match("/dashboard")
        assert route is not None
        assert len(route.layouts) == 2  # root + dashboard


class TestSpecialFiles:
    """Tests for special file handling (loading, error, not-found)."""
    
    def test_loading_file(self, temp_pages_dir):
        """Loading file is registered."""
        (temp_pages_dir / "loading.py").write_text('''
from pynext import loading, div

@loading
def global_loading():
    return div()["Loading..."]
''')
        
        (temp_pages_dir / "index.py").write_text('''
from pynext import page, div

@page
def index():
    return div()["Home"]
''')
        
        router = FileRouter(str(temp_pages_dir))
        router.scan()
        
        route, _ = router.match("/")
        assert route is not None
        assert route.loading is not None
    
    def test_error_file(self, temp_pages_dir):
        """Error file is registered."""
        (temp_pages_dir / "error.py").write_text('''
from pynext import error, div

@error
def global_error(error, reset):
    return div()[str(error)]
''')
        
        (temp_pages_dir / "index.py").write_text('''
from pynext import page, div

@page
def index():
    return div()["Home"]
''')
        
        router = FileRouter(str(temp_pages_dir))
        router.scan()
        
        route, _ = router.match("/")
        assert route is not None
        assert route.error is not None
    
    def test_not_found_file(self, temp_pages_dir):
        """Not-found file is registered."""
        (temp_pages_dir / "not-found.py").write_text('''
from pynext import not_found, div

@not_found
def custom_404():
    return div()["Not Found"]
''')
        
        (temp_pages_dir / "index.py").write_text('''
from pynext import page, div

@page
def index():
    return div()["Home"]
''')
        
        router = FileRouter(str(temp_pages_dir))
        router.scan()
        
        assert router.get_not_found() is not None


class TestContextVars:
    """Tests for get_params and get_query context variables."""
    
    def test_get_params_default(self):
        """get_params returns empty dict by default."""
        params = get_params()
        assert params == {}
    
    def test_get_query_default(self):
        """get_query returns empty dict by default."""
        query = get_query()
        assert query == {}


class TestRouteReload:
    """Tests for hot reload functionality."""
    
    def test_reload_single_file(self, temp_pages_dir):
        """Router can reload a single file."""
        # Create initial page
        page_path = temp_pages_dir / "test.py"
        page_path.write_text('''
from pynext import page, div

@page
def test():
    return div()["Version 1"]
''')
        
        router = FileRouter(str(temp_pages_dir))
        router.scan()
        
        initial_count = len(router.routes)
        
        # Modify the file
        page_path.write_text('''
from pynext import page, div

@page
def test():
    return div()["Version 2"]
''')
        
        # Reload just this file
        router.reload(str(page_path))
        
        # Should still have same number of routes
        assert len(router.routes) == initial_count
    
    def test_full_rescan(self, temp_pages_dir):
        """Router can do a full rescan."""
        (temp_pages_dir / "page1.py").write_text('''
from pynext import page, div

@page
def page1():
    return div()["Page 1"]
''')
        
        router = FileRouter(str(temp_pages_dir))
        router.scan()
        
        initial_count = len(router.routes)
        
        # Add new page
        (temp_pages_dir / "page2.py").write_text('''
from pynext import page, div

@page
def page2():
    return div()["Page 2"]
''')
        
        # Full rescan
        router.reload()
        
        assert len(router.routes) == initial_count + 1

