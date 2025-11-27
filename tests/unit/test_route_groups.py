"""
Comprehensive tests for Route Groups.

Tests:
- is_route_group() detection
- strip_groups() URL generation
- get_group_name() extraction
- get_groups_in_path() multiple groups
- RouteGroup dataclass
- GroupRegistry operations
- scan_groups() directory scanning
"""

import pytest
from pathlib import Path

from pynext.router.groups import (
    is_route_group,
    strip_groups,
    get_group_name,
    get_groups_in_path,
    RouteGroup,
    GroupRegistry,
    scan_groups,
)


# =============================================================================
# is_route_group() Tests
# =============================================================================

class TestIsRouteGroup:
    """Tests for is_route_group() function."""
    
    def test_valid_route_group_simple(self):
        """Simple parenthesized name is a route group."""
        assert is_route_group("(marketing)") is True
    
    def test_valid_route_group_with_dash(self):
        """Route group with dash is valid."""
        assert is_route_group("(app-v2)") is True
    
    def test_valid_route_group_with_underscore(self):
        """Route group with underscore is valid."""
        assert is_route_group("(user_area)") is True
    
    def test_valid_route_group_numbers(self):
        """Route group with numbers is valid."""
        assert is_route_group("(section1)") is True
    
    def test_invalid_no_parentheses(self):
        """Regular folder is not a route group."""
        assert is_route_group("marketing") is False
    
    def test_invalid_only_opening_paren(self):
        """Missing closing paren is not a route group."""
        assert is_route_group("(marketing") is False
    
    def test_invalid_only_closing_paren(self):
        """Missing opening paren is not a route group."""
        assert is_route_group("marketing)") is False
    
    def test_invalid_slot_convention(self):
        """@slot convention is not a route group."""
        assert is_route_group("@sidebar") is False
    
    def test_invalid_dynamic_route(self):
        """[id] dynamic route is not a route group."""
        assert is_route_group("[id]") is False
    
    def test_invalid_catch_all(self):
        """[...slug] catch-all is not a route group."""
        assert is_route_group("[...slug]") is False
    
    def test_invalid_empty_parens(self):
        """Empty parentheses are not a route group."""
        assert is_route_group("()") is False
    
    def test_invalid_nested_parens(self):
        """Nested parentheses are not a route group."""
        assert is_route_group("((nested))") is False
    
    def test_invalid_special_chars(self):
        """Special characters outside alphanumeric/dash/underscore are invalid."""
        assert is_route_group("(app.v2)") is False
        assert is_route_group("(app/v2)") is False


# =============================================================================
# get_group_name() Tests
# =============================================================================

class TestGetGroupName:
    """Tests for get_group_name() function."""
    
    def test_extracts_name_simple(self):
        """Extracts name from simple route group."""
        assert get_group_name("(marketing)") == "marketing"
    
    def test_extracts_name_with_dash(self):
        """Extracts name from route group with dash."""
        assert get_group_name("(app-v2)") == "app-v2"
    
    def test_returns_none_for_non_group(self):
        """Returns None for non-route-group folders."""
        assert get_group_name("dashboard") is None
    
    def test_returns_none_for_slot(self):
        """Returns None for @slot folders."""
        assert get_group_name("@sidebar") is None


# =============================================================================
# strip_groups() Tests
# =============================================================================

class TestStripGroups:
    """Tests for strip_groups() URL generation."""
    
    def test_strips_single_group(self):
        """Strips single route group from path."""
        assert strip_groups("pages/(marketing)/about/page.py") == "/about"
    
    def test_strips_multiple_groups(self):
        """Strips multiple route groups from path."""
        assert strip_groups("pages/(app)/(admin)/users/page.py") == "/users"
    
    def test_preserves_regular_folders(self):
        """Preserves non-group folders in URL."""
        assert strip_groups("pages/(app)/dashboard/settings/page.py") == "/dashboard/settings"
    
    def test_handles_dynamic_routes(self):
        """Preserves dynamic route segments."""
        assert strip_groups("pages/(app)/users/[id]/page.py") == "/users/[id]"
    
    def test_handles_catch_all_routes(self):
        """Preserves catch-all route segments."""
        assert strip_groups("pages/(docs)/[...slug]/page.py") == "/[...slug]"
    
    def test_handles_no_groups(self):
        """Works correctly when no groups present."""
        assert strip_groups("pages/blog/page.py") == "/blog"
    
    def test_handles_root_page(self):
        """Returns / for root page."""
        assert strip_groups("pages/page.py") == "/"
    
    def test_handles_index_file(self):
        """Strips index.py correctly."""
        assert strip_groups("pages/(marketing)/index.py") == "/"
    
    def test_strips_src_prefix(self):
        """Strips src/ prefix as well."""
        assert strip_groups("src/pages/(app)/dashboard/page.py") == "/dashboard"
    
    def test_group_at_root(self):
        """Group at root level works."""
        assert strip_groups("pages/(app)/page.py") == "/"


# =============================================================================
# get_groups_in_path() Tests
# =============================================================================

class TestGetGroupsInPath:
    """Tests for get_groups_in_path() function."""
    
    def test_single_group(self):
        """Finds single group in path."""
        groups = get_groups_in_path("pages/(marketing)/about/page.py")
        assert groups == ["marketing"]
    
    def test_multiple_groups(self):
        """Finds multiple groups in order."""
        groups = get_groups_in_path("pages/(app)/(admin)/users/page.py")
        assert groups == ["app", "admin"]
    
    def test_no_groups(self):
        """Returns empty list when no groups."""
        groups = get_groups_in_path("pages/blog/page.py")
        assert groups == []
    
    def test_preserves_order(self):
        """Groups are returned in path order."""
        groups = get_groups_in_path("pages/(first)/(second)/(third)/page.py")
        assert groups == ["first", "second", "third"]


# =============================================================================
# RouteGroup Tests
# =============================================================================

class TestRouteGroup:
    """Tests for RouteGroup dataclass."""
    
    def test_creation_minimal(self):
        """Creates with minimal required fields."""
        group = RouteGroup(name="marketing", path=Path("/pages/(marketing)"))
        assert group.name == "marketing"
        assert group.layout is None
        assert group.template is None
    
    def test_creation_with_all_fields(self):
        """Creates with all special files."""
        group = RouteGroup(
            name="app",
            path=Path("/pages/(app)"),
            layout=Path("/pages/(app)/layout.py"),
            template=Path("/pages/(app)/template.py"),
            loading=Path("/pages/(app)/loading.py"),
            error=Path("/pages/(app)/error.py"),
        )
        assert group.layout is not None
        assert group.template is not None


# =============================================================================
# GroupRegistry Tests
# =============================================================================

class TestGroupRegistry:
    """Tests for GroupRegistry class."""
    
    def test_empty_registry(self):
        """Empty registry returns None for lookups."""
        registry = GroupRegistry()
        assert registry.get_group("marketing") is None
        assert registry.get_groups_for_url("/about") == []
    
    def test_get_group(self):
        """Gets group by name."""
        registry = GroupRegistry()
        group = RouteGroup(name="marketing", path=Path("/pages/(marketing)"))
        registry.groups["marketing"] = group
        
        assert registry.get_group("marketing") == group
        assert registry.get_group("nonexistent") is None
    
    def test_get_groups_for_url(self):
        """Gets groups that apply to a URL."""
        registry = GroupRegistry()
        group = RouteGroup(name="app", path=Path("/pages/(app)"))
        registry.groups["app"] = group
        registry.url_to_groups["/dashboard"] = ["app"]
        
        groups = registry.get_groups_for_url("/dashboard")
        assert len(groups) == 1
        assert groups[0].name == "app"
    
    def test_get_layouts_empty(self):
        """Returns empty list when no layouts."""
        registry = GroupRegistry()
        layouts = registry.get_layouts("/about")
        assert layouts == []
    
    def test_get_layouts_with_root(self):
        """Returns root layout first."""
        registry = GroupRegistry()
        root_layout = Path("/pages/layout.py")
        registry.groups["root"] = RouteGroup(
            name="root",
            path=Path("/pages"),
            layout=root_layout,
        )
        
        layouts = registry.get_layouts("/about")
        assert layouts == [root_layout]
    
    def test_get_layouts_chain(self):
        """Returns layout chain in correct order."""
        registry = GroupRegistry()
        
        root_layout = Path("/pages/layout.py")
        app_layout = Path("/pages/(app)/layout.py")
        
        registry.groups["root"] = RouteGroup(
            name="root",
            path=Path("/pages"),
            layout=root_layout,
        )
        registry.groups["app"] = RouteGroup(
            name="app",
            path=Path("/pages/(app)"),
            layout=app_layout,
        )
        registry.url_to_groups["/dashboard"] = ["app"]
        
        layouts = registry.get_layouts("/dashboard")
        assert layouts == [root_layout, app_layout]
    
    def test_get_loading_most_specific(self):
        """Returns most specific loading file."""
        registry = GroupRegistry()
        
        root_loading = Path("/pages/loading.py")
        app_loading = Path("/pages/(app)/loading.py")
        
        registry.groups["root"] = RouteGroup(
            name="root",
            path=Path("/pages"),
            loading=root_loading,
        )
        registry.groups["app"] = RouteGroup(
            name="app",
            path=Path("/pages/(app)"),
            loading=app_loading,
        )
        registry.url_to_groups["/dashboard"] = ["app"]
        
        loading = registry.get_loading("/dashboard")
        assert loading == app_loading
    
    def test_get_loading_falls_back_to_root(self):
        """Falls back to root loading when group has none."""
        registry = GroupRegistry()
        
        root_loading = Path("/pages/loading.py")
        
        registry.groups["root"] = RouteGroup(
            name="root",
            path=Path("/pages"),
            loading=root_loading,
        )
        registry.groups["app"] = RouteGroup(
            name="app",
            path=Path("/pages/(app)"),
            # No loading
        )
        registry.url_to_groups["/dashboard"] = ["app"]
        
        loading = registry.get_loading("/dashboard")
        assert loading == root_loading


# =============================================================================
# scan_groups() Integration Tests
# =============================================================================

class TestScanGroups:
    """Integration tests for scan_groups() function."""
    
    def test_empty_directory(self, tmp_path):
        """Returns empty registry for empty directory."""
        pages_dir = tmp_path / "pages"
        pages_dir.mkdir()
        
        registry = scan_groups(pages_dir)
        assert len(registry.groups) == 0
    
    def test_nonexistent_directory(self, tmp_path):
        """Returns empty registry for nonexistent directory."""
        pages_dir = tmp_path / "nonexistent"
        
        registry = scan_groups(pages_dir)
        assert len(registry.groups) == 0
    
    def test_finds_root_layout(self, tmp_path):
        """Finds root layout.py."""
        pages_dir = tmp_path / "pages"
        pages_dir.mkdir()
        (pages_dir / "layout.py").write_text("# layout")
        
        registry = scan_groups(pages_dir)
        assert "root" in registry.groups
        assert registry.groups["root"].layout is not None
    
    def test_finds_route_groups(self, tmp_path):
        """Finds (folder) route groups."""
        pages_dir = tmp_path / "pages"
        pages_dir.mkdir()
        (pages_dir / "(marketing)").mkdir()
        (pages_dir / "(app)").mkdir()
        
        registry = scan_groups(pages_dir)
        assert "marketing" in registry.groups
        assert "app" in registry.groups
    
    def test_finds_group_special_files(self, tmp_path):
        """Finds special files within groups."""
        pages_dir = tmp_path / "pages"
        pages_dir.mkdir()
        
        app_dir = pages_dir / "(app)"
        app_dir.mkdir()
        (app_dir / "layout.py").write_text("# layout")
        (app_dir / "loading.py").write_text("# loading")
        (app_dir / "error.py").write_text("# error")
        
        registry = scan_groups(pages_dir)
        app_group = registry.groups["app"]
        
        assert app_group.layout is not None
        assert app_group.loading is not None
        assert app_group.error is not None
    
    def test_maps_pages_to_groups(self, tmp_path):
        """Maps page URLs to their groups."""
        pages_dir = tmp_path / "pages"
        pages_dir.mkdir()
        
        app_dir = pages_dir / "(app)"
        app_dir.mkdir()
        dashboard_dir = app_dir / "dashboard"
        dashboard_dir.mkdir()
        (dashboard_dir / "page.py").write_text("# page")
        
        registry = scan_groups(pages_dir)
        
        # The URL /dashboard should map to the "app" group
        assert "/dashboard" in registry.url_to_groups
        assert registry.url_to_groups["/dashboard"] == ["app"]
    
    def test_nested_groups(self, tmp_path):
        """Handles nested route groups."""
        pages_dir = tmp_path / "pages"
        pages_dir.mkdir()
        
        app_dir = pages_dir / "(app)"
        app_dir.mkdir()
        admin_dir = app_dir / "(admin)"
        admin_dir.mkdir()
        users_dir = admin_dir / "users"
        users_dir.mkdir()
        (users_dir / "page.py").write_text("# page")
        
        registry = scan_groups(pages_dir)
        
        assert "app" in registry.groups
        assert "admin" in registry.groups
        assert "/users" in registry.url_to_groups
        assert registry.url_to_groups["/users"] == ["app", "admin"]
    
    def test_ignores_non_groups(self, tmp_path):
        """Ignores regular folders."""
        pages_dir = tmp_path / "pages"
        pages_dir.mkdir()
        (pages_dir / "blog").mkdir()
        (pages_dir / "@sidebar").mkdir()
        
        registry = scan_groups(pages_dir)
        
        assert "blog" not in registry.groups
        assert "@sidebar" not in registry.groups
        assert "sidebar" not in registry.groups


# =============================================================================
# Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and unusual inputs."""
    
    def test_group_with_unicode(self):
        """Handles unicode in group names (valid - Python \w matches unicode)."""
        # Python's \w matches Unicode letters, so this is valid
        assert is_route_group("(café)") is True
    
    def test_very_long_group_name(self):
        """Handles very long group names."""
        long_name = "(a" + "b" * 100 + ")"
        assert is_route_group(long_name) is True
    
    def test_strip_groups_windows_path(self):
        """Handles Windows-style paths."""
        # Path library normalizes these
        result = strip_groups("pages\\(app)\\dashboard\\page.py")
        # Result depends on platform, but should work
        assert "dashboard" in result
    
    def test_strip_groups_double_slashes(self):
        """Handles paths with double slashes."""
        result = strip_groups("pages//(app)//dashboard//page.py")
        assert "dashboard" in result

