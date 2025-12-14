"""
Comprehensive tests for nested routes.

Tests cover:
1. Outlet component
2. Nested route matching
3. Layout patterns
4. Nested params
"""

import pytest
from unittest.mock import Mock, patch

from pynext.reactive.router import (
    Router,
    Route,
    Outlet,
    _create_router_context,
    useParams,
)


# =============================================================================
# SECTION 1: OUTLET COMPONENT
# =============================================================================

class TestOutlet:
    """Test Outlet component."""
    
    def test_outlet_creates(self):
        """Outlet creates successfully."""
        outlet = Outlet()
        
        assert outlet is not None
    
    def test_outlet_renders(self):
        """Outlet renders to HTML."""
        outlet = Outlet()
        
        result = str(outlet)
        
        assert "<div" in result
        assert "data-pynext-outlet" in result
    
    def test_outlet_has_marker(self):
        """Outlet has identification marker."""
        outlet = Outlet()
        
        result = str(outlet)
        
        assert 'data-pynext-outlet="true"' in result


# =============================================================================
# SECTION 2: NESTED ROUTE DEFINITIONS
# =============================================================================

class TestNestedRouteDefinitions:
    """Test defining nested routes."""
    
    def test_parent_with_child_routes(self):
        """Parent route with child routes."""
        def Layout():
            from pynext.core.html import div
            return div()[
                "Layout",
                Outlet(),
            ]
        
        def Child1():
            from pynext.core.html import div
            return div()["Child 1"]
        
        def Child2():
            from pynext.core.html import div
            return div()["Child 2"]
        
        # Routes can be defined hierarchically
        routes = [
            Route("/", component=Layout),
            Route("/child1", component=Child1),
            Route("/child2", component=Child2),
        ]
        
        assert len(routes) == 3
    
    def test_nested_param_routes(self):
        """Nested routes with params at multiple levels."""
        routes = [
            Route("/users/:userId", component=lambda: None),
            Route("/users/:userId/posts/:postId", component=lambda: None),
        ]
        
        # Child route has both params
        assert routes[1].param_names == ["userId", "postId"]


# =============================================================================
# SECTION 3: LAYOUT PATTERNS
# =============================================================================

class TestLayoutPatterns:
    """Test common layout patterns."""
    
    def test_shared_layout(self):
        """Shared layout with outlet."""
        def Layout():
            from pynext.core.html import div, header, main, footer
            return div()[
                header()["Header"],
                main()[str(Outlet())],  # Convert Outlet to string
                footer()["Footer"],
            ]
        
        result = str(Layout())
        
        assert "Header" in result
        assert "Footer" in result
        assert "data-pynext-outlet" in result
    
    def test_admin_layout(self):
        """Admin section with sidebar layout."""
        def AdminLayout():
            from pynext.core.html import div, nav, main
            return div()[
                nav()["Sidebar"],
                main()[str(Outlet())],  # Convert Outlet to string
            ]
        
        result = str(AdminLayout())
        
        assert "Sidebar" in result
        assert "data-pynext-outlet" in result
    
    def test_nested_layouts(self):
        """Nested layouts (admin > dashboard)."""
        def AdminLayout():
            from pynext.core.html import div
            return div(id="admin")[
                "Admin Layout",
                str(Outlet()),  # Convert Outlet to string
            ]
        
        def DashboardLayout():
            from pynext.core.html import div
            return div(id="dashboard")[
                "Dashboard Layout",
                str(Outlet()),  # Convert Outlet to string
            ]
        
        # Both layouts render outlets
        admin = str(AdminLayout())
        dashboard = str(DashboardLayout())
        
        assert 'id="admin"' in admin
        assert 'id="dashboard"' in dashboard


# =============================================================================
# SECTION 4: NESTED PARAM ACCESS
# =============================================================================

class TestNestedParamAccess:
    """Test accessing params in nested routes."""
    
    def test_parent_param_in_child(self):
        """Child can access parent params."""
        ctx = _create_router_context("/users/1/posts/2")
        ctx.params.set({"userId": "1", "postId": "2"})
        
        params = useParams()
        
        assert params["userId"] == "1"
        assert params["postId"] == "2"
    
    def test_deeply_nested_params(self):
        """Deeply nested params."""
        ctx = _create_router_context("/org/acme/team/dev/member/john")
        ctx.params.set({
            "orgId": "acme",
            "teamId": "dev",
            "memberId": "john",
        })
        
        params = useParams()
        
        assert params["orgId"] == "acme"
        assert params["teamId"] == "dev"
        assert params["memberId"] == "john"


# =============================================================================
# SECTION 5: ROUTE MATCHING PRIORITY
# =============================================================================

class TestNestedRoutePriority:
    """Test route matching priority for nested routes."""
    
    def test_more_specific_wins(self):
        """More specific route should be defined first."""
        router = Router()[
            Route("/users/new", component=lambda: "New User"),
            Route("/users/:id", component=lambda: "User Detail"),
        ]
        
        matched, params = router._find_matching_route("/users/new")
        
        # First matching route wins
        assert matched.path == "/users/new"
    
    def test_order_matters(self):
        """Route order matters for matching."""
        # Dynamic first - will match "new" as id
        router1 = Router()[
            Route("/users/:id", component=lambda: "Dynamic"),
            Route("/users/new", component=lambda: "Static"),
        ]
        
        matched1, params1 = router1._find_matching_route("/users/new")
        assert params1 == {"id": "new"}  # Dynamic matched first
        
        # Static first - will match exactly
        router2 = Router()[
            Route("/users/new", component=lambda: "Static"),
            Route("/users/:id", component=lambda: "Dynamic"),
        ]
        
        matched2, params2 = router2._find_matching_route("/users/new")
        assert params2 == {}  # Static matched first


# =============================================================================
# SECTION 6: OUTLET RENDERING CONTEXT
# =============================================================================

class TestOutletRenderingContext:
    """Test Outlet rendering in different contexts."""
    
    def test_outlet_in_function_component(self):
        """Outlet renders in function component."""
        def MyLayout():
            from pynext.core.html import div
            return div()[
                str(Outlet()),  # Convert to string
            ]
        
        result = str(MyLayout())
        assert "data-pynext-outlet" in result
    
    def test_multiple_outlets(self):
        """Multiple outlets in same layout."""
        def MultiOutletLayout():
            from pynext.core.html import div
            return div()[
                div(id="main")[str(Outlet())],  # Convert to string
                div(id="sidebar")[str(Outlet())],  # Convert to string
            ]
        
        result = str(MultiOutletLayout())
        
        # Both outlets rendered
        assert result.count("data-pynext-outlet") == 2


# =============================================================================
# SECTION 7: EDGE CASES
# =============================================================================

class TestNestedRouteEdgeCases:
    """Test edge cases for nested routes."""
    
    def test_empty_outlet(self):
        """Outlet with no matched child."""
        outlet = Outlet()
        result = str(outlet)
        
        # Should render empty outlet container
        assert "<div" in result
    
    def test_outlet_repr(self):
        """Outlet has string representation."""
        outlet = Outlet()
        result = str(outlet)
        
        assert result  # Non-empty
    
    def test_deeply_nested_path(self):
        """Very deeply nested path matching."""
        path = "/a/:a/b/:b/c/:c/d/:d/e/:e"
        route = Route(path, component=lambda: None)
        
        params = route.match("/a/1/b/2/c/3/d/4/e/5")
        
        assert params == {"a": "1", "b": "2", "c": "3", "d": "4", "e": "5"}

