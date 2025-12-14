"""
Integration tests for the router system.

Tests cover end-to-end scenarios combining multiple router features.
"""

import pytest
from unittest.mock import Mock, patch

from pynext.reactive.router import (
    Router,
    Route,
    Link,
    Outlet,
    useNavigate,
    useParams,
    useSearchParams,
    useLocation,
    useMatch,
    Redirect,
    createRouteGuard,
    _create_router_context,
)


# =============================================================================
# SECTION 1: FULL NAVIGATION FLOW
# =============================================================================

class TestFullNavigationFlow:
    """Test complete navigation flows."""
    
    def test_home_to_about_navigation(self):
        """Navigate from home to about."""
        ctx = _create_router_context("/")
        ctx.routes = [
            Route("/", component=lambda: "Home").to_compiled(),
            Route("/about", component=lambda: "About").to_compiled(),
        ]
        
        # Start at home
        assert ctx.pathname() == "/"
        
        # Navigate
        navigate = useNavigate()
        navigate("/about")
        
        # Verify
        assert ctx.pathname() == "/about"
    
    def test_navigate_to_dynamic_and_back(self):
        """Navigate to dynamic route and back."""
        ctx = _create_router_context("/users")
        ctx.routes = [
            Route("/users", component=lambda: "List").to_compiled(),
            Route("/users/:id", component=lambda: "Detail").to_compiled(),
        ]
        
        navigate = useNavigate()
        
        # Go to detail
        navigate("/users/123")
        assert ctx.pathname() == "/users/123"
        assert useParams() == {"id": "123"}
        
        # Go back to list
        navigate("/users")
        assert ctx.pathname() == "/users"
        assert useParams() == {}
    
    def test_multi_step_navigation(self):
        """Navigate through multiple pages."""
        ctx = _create_router_context("/")
        ctx.routes = [
            Route("/", component=lambda: "Home").to_compiled(),
            Route("/a", component=lambda: "A").to_compiled(),
            Route("/b", component=lambda: "B").to_compiled(),
            Route("/c", component=lambda: "C").to_compiled(),
        ]
        
        navigate = useNavigate()
        
        navigate("/a")
        assert ctx.pathname() == "/a"
        
        navigate("/b")
        assert ctx.pathname() == "/b"
        
        navigate("/c")
        assert ctx.pathname() == "/c"


# =============================================================================
# SECTION 2: QUERY STRING INTEGRATION
# =============================================================================

class TestQueryStringIntegration:
    """Test query string handling in navigation."""
    
    def test_navigate_with_preserve_query(self):
        """Navigate while manipulating query."""
        ctx = _create_router_context("/search")
        ctx.query.set({"q": "test"})
        
        navigate = useNavigate()
        
        # Add more query params
        navigate("/search?q=test&page=2")
        
        query = ctx.query()
        assert query["q"] == "test"
        assert query["page"] == "2"
    
    def test_search_params_update(self):
        """Update search params without changing path."""
        ctx = _create_router_context("/search")
        ctx.query.set({"q": "initial"})
        
        params, setParams = useSearchParams()
        
        setParams({"q": "updated", "filter": "active"})
        
        new_params, _ = useSearchParams()
        assert new_params["q"] == "updated"
        assert new_params["filter"] == "active"
    
    def test_paginated_list_navigation(self):
        """Navigate through paginated list."""
        ctx = _create_router_context("/items")
        ctx.routes = [Route("/items", component=lambda: "Items").to_compiled()]
        
        navigate = useNavigate()
        
        # Page 1
        navigate("/items?page=1")
        assert ctx.query()["page"] == "1"
        
        # Page 2
        navigate("/items?page=2")
        assert ctx.query()["page"] == "2"
        
        # With filter
        navigate("/items?page=1&status=active")
        query = ctx.query()
        assert query["page"] == "1"
        assert query["status"] == "active"


# =============================================================================
# SECTION 3: GUARDS INTEGRATION
# =============================================================================

class TestGuardsIntegration:
    """Test route guards in realistic scenarios."""
    
    def test_protected_route_redirect(self):
        """Protected route redirects unauthenticated users."""
        is_authenticated = [False]
        
        def auth_guard():
            if not is_authenticated[0]:
                return Redirect("/login")
            return None
        
        guard = createRouteGuard(auth_guard)
        
        # Not authenticated - should redirect
        result = guard()
        assert isinstance(result, Redirect)
        assert result.to == "/login"
    
    def test_role_based_access(self):
        """Role-based route access."""
        user_role = ["user"]
        
        def admin_guard():
            if user_role[0] != "admin":
                return Redirect("/unauthorized")
            return None
        
        guard = createRouteGuard(admin_guard)
        
        # Regular user
        assert isinstance(guard(), Redirect)
        
        # Admin user
        user_role[0] = "admin"
        assert guard() is None


# =============================================================================
# SECTION 4: LINK INTEGRATION
# =============================================================================

class TestLinkIntegration:
    """Test Link component in realistic scenarios."""
    
    def test_navigation_menu(self):
        """Navigation menu with multiple links."""
        ctx = _create_router_context("/")
        
        links = [
            Link(href="/")["Home"],
            Link(href="/about")["About"],
            Link(href="/contact")["Contact"],
        ]
        
        for link in links:
            result = str(link)
            assert "data-pynext-link" in result
    
    def test_active_nav_item(self):
        """Active navigation item styling."""
        ctx = _create_router_context("/about")
        
        home_link = Link(href="/", exact=True)["Home"]
        about_link = Link(href="/about", exact=True)["About"]
        
        assert home_link._is_active("/about") is False
        assert about_link._is_active("/about") is True
    
    def test_breadcrumb_links(self):
        """Breadcrumb navigation links."""
        ctx = _create_router_context("/users/1/posts/2")
        
        breadcrumbs = [
            Link(href="/")["Home"],
            Link(href="/users")["Users"],
            Link(href="/users/1")["User 1"],
            Link(href="/users/1/posts")["Posts"],
            Link(href="/users/1/posts/2")["Post 2"],
        ]
        
        for link in breadcrumbs:
            result = str(link)
            assert "<a" in result


# =============================================================================
# SECTION 5: PARAMS INTEGRATION
# =============================================================================

class TestParamsIntegration:
    """Test params in realistic scenarios."""
    
    def test_user_profile_page(self):
        """User profile page with user ID."""
        ctx = _create_router_context("/users/john-doe")
        ctx.params.set({"username": "john-doe"})
        
        params = useParams()
        
        assert params["username"] == "john-doe"
    
    def test_product_detail_page(self):
        """Product detail with category and product ID."""
        ctx = _create_router_context("/shop/electronics/product-123")
        ctx.params.set({"category": "electronics", "productId": "product-123"})
        
        params = useParams()
        
        assert params["category"] == "electronics"
        assert params["productId"] == "product-123"
    
    def test_nested_resource_params(self):
        """Nested resource with multiple params."""
        ctx = _create_router_context("/orgs/acme/teams/dev/members/jane")
        ctx.params.set({
            "orgId": "acme",
            "teamId": "dev",
            "memberId": "jane",
        })
        
        params = useParams()
        
        assert params["orgId"] == "acme"
        assert params["teamId"] == "dev"
        assert params["memberId"] == "jane"


# =============================================================================
# SECTION 6: LOCATION INTEGRATION
# =============================================================================

class TestLocationIntegration:
    """Test useLocation in realistic scenarios."""
    
    def test_breadcrumb_from_location(self):
        """Build breadcrumb from location."""
        ctx = _create_router_context("/users/123/posts")
        
        location = useLocation()
        segments = location.pathname.split("/")[1:]  # Remove empty first
        
        assert segments == ["users", "123", "posts"]
    
    def test_share_current_url(self):
        """Get current URL for sharing."""
        ctx = _create_router_context("/article/my-article")
        ctx.query.set({"ref": "twitter"})
        
        location = useLocation()
        
        assert location.pathname == "/article/my-article"
        assert "ref=twitter" in location.search
    
    def test_scroll_to_anchor(self):
        """Detect anchor for scrolling."""
        ctx = _create_router_context("/docs/api")
        ctx.hash_.set("authentication")
        
        location = useLocation()
        
        assert location.hash == "#authentication"


# =============================================================================
# SECTION 7: MATCH INTEGRATION
# =============================================================================

class TestMatchIntegration:
    """Test useMatch in realistic scenarios."""
    
    def test_conditional_sidebar(self):
        """Show sidebar only on certain routes."""
        ctx = _create_router_context("/dashboard/analytics")
        
        # Sidebar shown on dashboard routes
        match = useMatch("/dashboard/*")
        show_sidebar = match is not None
        
        assert show_sidebar is True
    
    def test_highlight_current_section(self):
        """Highlight current documentation section."""
        ctx = _create_router_context("/docs/getting-started")
        
        sections = [
            ("/docs/getting-started", "Getting Started"),
            ("/docs/api", "API"),
            ("/docs/examples", "Examples"),
        ]
        
        for path, name in sections:
            match = useMatch(path)
            is_current = match is not None
            
            if path == "/docs/getting-started":
                assert is_current is True
            else:
                assert is_current is False
    
    def test_detect_edit_mode(self):
        """Detect if on edit page."""
        ctx = _create_router_context("/posts/123/edit")
        
        edit_match = useMatch("/posts/:id/edit")
        view_match = useMatch("/posts/:id")
        
        # Edit match should work for /posts/123/edit
        assert edit_match == {"id": "123"}


# =============================================================================
# SECTION 8: ROUTER SSR INTEGRATION
# =============================================================================

class TestRouterSSRIntegration:
    """Test Router SSR in realistic scenarios."""
    
    def test_blog_post_ssr(self):
        """SSR blog post page."""
        def BlogPost():
            params = useParams()
            from pynext.core.html import article, h1
            return article()[
                h1()[f"Post: {params.get('slug', 'unknown')}"],
            ]
        
        with patch.object(Router, '_get_initial_pathname', return_value="/blog/my-post"):
            router = Router()[
                Route("/blog/:slug", component=BlogPost),
            ]
            
            result = str(router)
        
        assert "Post: my-post" in result
    
    def test_product_catalog_ssr(self):
        """SSR product catalog page."""
        def ProductList():
            from pynext.core.html import div, h1
            return div()[h1()["Products"]]
        
        def ProductDetail():
            params = useParams()
            from pynext.core.html import div, h1
            return div()[h1()[f"Product {params.get('id', '?')}"]]
        
        with patch.object(Router, '_get_initial_pathname', return_value="/products/abc-123"):
            router = Router()[
                Route("/products", component=ProductList),
                Route("/products/:id", component=ProductDetail),
            ]
            
            result = str(router)
        
        assert "Product abc-123" in result
    
    def test_404_page_ssr(self):
        """SSR 404 page."""
        def NotFound():
            from pynext.core.html import div, h1
            return div()[h1()["Page Not Found"]]
        
        with patch.object(Router, '_get_initial_pathname', return_value="/nonexistent"):
            router = Router(fallback=NotFound)[
                Route("/", component=lambda: "Home"),
            ]
            
            result = str(router)
        
        assert "Page Not Found" in result


# =============================================================================
# SECTION 9: COMPLEX SCENARIOS
# =============================================================================

class TestComplexScenarios:
    """Test complex real-world scenarios."""
    
    def test_ecommerce_navigation(self):
        """E-commerce site navigation flow."""
        ctx = _create_router_context("/")
        ctx.routes = [
            Route("/", component=lambda: "Home").to_compiled(),
            Route("/products", component=lambda: "Products").to_compiled(),
            Route("/products/:id", component=lambda: "Product").to_compiled(),
            Route("/cart", component=lambda: "Cart").to_compiled(),
            Route("/checkout", component=lambda: "Checkout").to_compiled(),
        ]
        
        navigate = useNavigate()
        
        # Browse products
        navigate("/products")
        assert ctx.pathname() == "/products"
        
        # View product
        navigate("/products/shoe-123")
        assert useParams() == {"id": "shoe-123"}
        
        # Add to cart
        navigate("/cart")
        assert ctx.pathname() == "/cart"
        
        # Checkout
        navigate("/checkout")
        assert ctx.pathname() == "/checkout"
    
    def test_dashboard_tabs(self):
        """Dashboard with tabbed navigation."""
        ctx = _create_router_context("/dashboard/overview")
        ctx.routes = [
            Route("/dashboard/overview", component=lambda: "Overview").to_compiled(),
            Route("/dashboard/analytics", component=lambda: "Analytics").to_compiled(),
            Route("/dashboard/settings", component=lambda: "Settings").to_compiled(),
        ]
        
        navigate = useNavigate()
        
        tabs = ["/dashboard/overview", "/dashboard/analytics", "/dashboard/settings"]
        
        for tab in tabs:
            navigate(tab)
            assert ctx.pathname() == tab
    
    def test_search_with_filters(self):
        """Search page with filters in query."""
        ctx = _create_router_context("/search")
        ctx.routes = [Route("/search", component=lambda: "Search").to_compiled()]
        
        navigate = useNavigate()
        
        # Initial search
        navigate("/search?q=laptop")
        assert ctx.query()["q"] == "laptop"
        
        # Add filter
        navigate("/search?q=laptop&brand=apple&min_price=500")
        query = ctx.query()
        assert query["q"] == "laptop"
        assert query["brand"] == "apple"
        assert query["min_price"] == "500"
        
        # Change query
        navigate("/search?q=tablet")
        query = ctx.query()
        assert query["q"] == "tablet"
        assert "brand" not in query

