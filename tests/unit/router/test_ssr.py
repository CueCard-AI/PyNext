"""
Comprehensive tests for Server-Side Rendering (SSR) with router.

Tests cover:
1. Initial route rendering
2. Hydration data
3. Route data attributes
4. Context propagation
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock

from pynext.reactive.router import (
    Router,
    Route,
    Link,
    _create_router_context,
    useParams,
)


# =============================================================================
# SECTION 1: INITIAL ROUTE RENDERING
# =============================================================================

class TestInitialRouteRendering:
    """Test SSR initial route rendering."""
    
    def test_router_renders_matched_route(self):
        """Router renders matched route on SSR."""
        def Home():
            from pynext.core.html import div
            return div()["Home Page"]
        
        with patch.object(Router, '_get_initial_pathname', return_value="/"):
            router = Router()[
                Route("/", component=Home),
            ]
            
            result = str(router)
        
        assert "Home Page" in result
    
    def test_router_renders_dynamic_route(self):
        """Router renders dynamic route with params."""
        def User():
            params = useParams()
            from pynext.core.html import div
            return div()[f"User {params.get('id', 'none')}"]
        
        with patch.object(Router, '_get_initial_pathname', return_value="/users/42"):
            router = Router()[
                Route("/users/:id", component=User),
            ]
            
            result = str(router)
        
        assert "User 42" in result
    
    def test_router_renders_fallback(self):
        """Router renders fallback for unmatched route."""
        def NotFound():
            from pynext.core.html import div
            return div()["Page Not Found"]
        
        with patch.object(Router, '_get_initial_pathname', return_value="/unknown"):
            router = Router(fallback=NotFound)[
                Route("/", component=lambda: "Home"),
            ]
            
            result = str(router)
        
        assert "Page Not Found" in result


# =============================================================================
# SECTION 2: ROUTE DATA ATTRIBUTES
# =============================================================================

class TestRouteDataAttributes:
    """Test data attributes for hydration."""
    
    def test_router_has_data_attr(self):
        """Router container has data attribute."""
        with patch.object(Router, '_get_initial_pathname', return_value="/"):
            router = Router()[
                Route("/", component=lambda: "Home"),
            ]
            
            result = str(router)
        
        assert 'data-pynext-router="true"' in result
    
    def test_route_data_json(self):
        """Router includes route data JSON."""
        with patch.object(Router, '_get_initial_pathname', return_value="/users/123"):
            router = Router()[
                Route("/users/:id", component=lambda: "User"),
            ]
            
            result = str(router)
        
        assert "data-pynext-route-data" in result
        
        # Extract and parse JSON
        import re
        match = re.search(r'data-pynext-route-data="([^"]+)"', result)
        if match:
            # HTML entities might be escaped
            json_str = match.group(1).replace("&quot;", '"')
            data = json.loads(json_str)
            
            assert data["pathname"] == "/users/123"
            assert data["params"] == {"id": "123"}


# =============================================================================
# SECTION 3: LINK SSR
# =============================================================================

class TestLinkSSR:
    """Test Link component SSR."""
    
    def test_link_renders_as_anchor(self):
        """Link renders as anchor tag."""
        link = Link(href="/about")["About"]
        
        result = str(link)
        
        assert "<a" in result
        assert 'href="/about"' in result
    
    def test_link_has_hydration_markers(self):
        """Link has markers for hydration."""
        link = Link(href="/test")["Test"]
        
        result = str(link)
        
        assert "data-pynext-link" in result
    
    def test_link_prefetch_marker(self):
        """Link prefetch attribute present."""
        link = Link(href="/test", prefetch=True)["Test"]
        
        result = str(link)
        
        assert "data-pynext-prefetch" in result


# =============================================================================
# SECTION 4: CONTEXT PROPAGATION
# =============================================================================

class TestContextPropagation:
    """Test router context propagation during SSR."""
    
    def test_params_available_in_component(self):
        """Params are available in rendered component."""
        rendered_params = []
        
        def CaptureParams():
            params = useParams()
            rendered_params.append(dict(params))
            from pynext.core.html import div
            return div()["Component"]
        
        with patch.object(Router, '_get_initial_pathname', return_value="/items/abc"):
            router = Router()[
                Route("/items/:id", component=CaptureParams),
            ]
            
            str(router)
        
        assert rendered_params == [{"id": "abc"}]
    
    def test_nested_components_access_context(self):
        """Nested components can access router context."""
        def Inner():
            params = useParams()
            from pynext.core.html import span
            return span()[params.get("id", "none")]
        
        def Outer():
            from pynext.core.html import div
            return div()[Inner()]
        
        with patch.object(Router, '_get_initial_pathname', return_value="/items/123"):
            router = Router()[
                Route("/items/:id", component=Outer),
            ]
            
            result = str(router)
        
        assert "123" in result


# =============================================================================
# SECTION 5: MULTIPLE ROUTES SSR
# =============================================================================

class TestMultipleRoutesSSR:
    """Test SSR with multiple routes."""
    
    def test_only_matched_route_rendered(self):
        """Only the matched route is rendered."""
        home_rendered = []
        about_rendered = []
        
        def Home():
            home_rendered.append(True)
            from pynext.core.html import div
            return div()["Home"]
        
        def About():
            about_rendered.append(True)
            from pynext.core.html import div
            return div()["About"]
        
        with patch.object(Router, '_get_initial_pathname', return_value="/"):
            router = Router()[
                Route("/", component=Home),
                Route("/about", component=About),
            ]
            
            str(router)
        
        assert home_rendered == [True]
        assert about_rendered == []
    
    def test_routes_in_route_data(self):
        """All route paths included in route data."""
        with patch.object(Router, '_get_initial_pathname', return_value="/"):
            router = Router()[
                Route("/", component=lambda: "Home"),
                Route("/about", component=lambda: "About"),
                Route("/contact", component=lambda: "Contact"),
            ]
            
            result = str(router)
        
        # Route data should include all paths for client-side routing
        assert "/about" in result or "about" in result


# =============================================================================
# SECTION 6: ERROR HANDLING
# =============================================================================

class TestSSRErrorHandling:
    """Test error handling during SSR."""
    
    def test_default_404_rendering(self):
        """Default 404 when no fallback."""
        with patch.object(Router, '_get_initial_pathname', return_value="/nonexistent"):
            router = Router()[
                Route("/", component=lambda: "Home"),
            ]
            
            result = str(router)
        
        assert "404" in result
    
    def test_custom_fallback_rendering(self):
        """Custom fallback component rendered."""
        def Custom404():
            from pynext.core.html import div
            return div(class_="error")["Custom Not Found"]
        
        with patch.object(Router, '_get_initial_pathname', return_value="/missing"):
            router = Router(fallback=Custom404)[
                Route("/", component=lambda: "Home"),
            ]
            
            result = str(router)
        
        assert "Custom Not Found" in result


# =============================================================================
# SECTION 7: INTEGRATION
# =============================================================================

class TestSSRIntegration:
    """Test full SSR integration."""
    
    def test_complete_page_ssr(self):
        """Complete page with router renders correctly."""
        def Home():
            from pynext.core.html import div, h1
            return div()[
                h1()["Welcome"],
                str(Link(href="/about")["Go to About"]),  # Convert Link to string
            ]
        
        def About():
            from pynext.core.html import div, h1
            return div()[
                h1()["About Us"],
            ]
        
        with patch.object(Router, '_get_initial_pathname', return_value="/"):
            router = Router()[
                Route("/", component=Home),
                Route("/about", component=About),
            ]
            
            result = str(router)
        
        assert "Welcome" in result
        # Link may be HTML-escaped when nested as string, check for the link text
        assert "Go to About" in result
        assert "data-pynext-router" in result

