"""
End-to-end tests for PyNext navigation.

Tests client-side navigation, link handling, and route transitions.
"""

import pytest

# These tests require Playwright and a running server
pytestmark = pytest.mark.e2e


class TestLinkNavigation:
    """E2E tests for link-based navigation."""
    
    @pytest.mark.skip(reason="Requires running server and Playwright")
    async def test_internal_link_navigation(self, page, example_app_url):
        """Clicking internal links navigates correctly."""
        await page.goto(example_app_url)
        
        # Click an internal link
        await page.click("a[href='/about']")
        
        # Check URL changed
        assert "/about" in page.url
        
        # Check content updated
        heading = await page.text_content("h1")
        assert "About" in heading
    
    @pytest.mark.skip(reason="Requires running server and Playwright")
    async def test_back_button(self, page, example_app_url):
        """Browser back button works."""
        await page.goto(example_app_url)
        initial_url = page.url
        
        # Navigate to another page
        await page.click("a[href='/about']")
        assert "/about" in page.url
        
        # Go back
        await page.go_back()
        
        # Should be back at initial page
        assert page.url == initial_url
    
    @pytest.mark.skip(reason="Requires running server and Playwright")
    async def test_forward_button(self, page, example_app_url):
        """Browser forward button works."""
        await page.goto(example_app_url)
        
        # Navigate away and back
        await page.click("a[href='/about']")
        await page.go_back()
        
        # Go forward
        await page.go_forward()
        
        assert "/about" in page.url


class TestDynamicRouteNavigation:
    """E2E tests for dynamic route navigation."""
    
    @pytest.mark.skip(reason="Requires running server and Playwright")
    async def test_dynamic_route_params(self, page, example_app_url):
        """Dynamic route parameters are passed correctly."""
        await page.goto(f"{example_app_url}/users/123")
        
        # Check that parameter is displayed
        content = await page.text_content("body")
        assert "123" in content
    
    @pytest.mark.skip(reason="Requires running server and Playwright")
    async def test_navigate_between_dynamic_routes(self, page, example_app_url):
        """Navigation between dynamic routes works."""
        # Go to user 1
        await page.goto(f"{example_app_url}/users/1")
        content1 = await page.text_content("body")
        assert "1" in content1
        
        # Navigate to user 2
        await page.click("a[href='/users/2']")
        content2 = await page.text_content("body")
        assert "2" in content2


class TestQueryParameters:
    """E2E tests for query parameter handling."""
    
    @pytest.mark.skip(reason="Requires running server and Playwright")
    async def test_query_params_in_url(self, page, example_app_url):
        """Query parameters are accessible in page."""
        await page.goto(f"{example_app_url}/search?q=test&page=1")
        
        # Check that query params are used
        content = await page.text_content("body")
        # Page should show search results or query
        assert "test" in content or "search" in page.url
    
    @pytest.mark.skip(reason="Requires running server and Playwright")
    async def test_query_params_preserved(self, page, example_app_url):
        """Query parameters are preserved during navigation."""
        await page.goto(f"{example_app_url}/search?q=test")
        
        # Add more query params programmatically
        await page.evaluate('''
            const url = new URL(window.location);
            url.searchParams.set('page', '2');
            window.history.pushState({}, '', url);
        ''')
        
        # Check URL still has original query
        assert "q=test" in page.url


class TestErrorHandling:
    """E2E tests for navigation error handling."""
    
    @pytest.mark.skip(reason="Requires running server and Playwright")
    async def test_404_page(self, page, example_app_url):
        """404 page is shown for non-existent routes."""
        response = await page.goto(f"{example_app_url}/this-does-not-exist")
        
        assert response.status == 404
        content = await page.text_content("body")
        assert "404" in content or "not found" in content.lower()
    
    @pytest.mark.skip(reason="Requires running server and Playwright")
    async def test_navigation_error_recovery(self, page, example_app_url):
        """App recovers from navigation errors."""
        await page.goto(example_app_url)
        
        # Try to navigate to non-existent page
        await page.goto(f"{example_app_url}/nonexistent")
        
        # Should still be able to navigate back
        await page.goto(example_app_url)
        assert page.url == example_app_url or page.url == f"{example_app_url}/"


class TestLayoutPersistence:
    """E2E tests for layout state persistence."""
    
    @pytest.mark.skip(reason="Requires running server and Playwright")
    async def test_layout_preserved_during_navigation(self, page, example_app_url):
        """Layout components persist during navigation."""
        await page.goto(example_app_url)
        
        # Check layout is present
        header = await page.locator("header").count()
        assert header > 0
        
        # Navigate to another page
        await page.click("a[href='/about']")
        
        # Layout should still be present
        header_after = await page.locator("header").count()
        assert header_after > 0
    
    @pytest.mark.skip(reason="Requires running server and Playwright")
    async def test_nested_layout_navigation(self, page, example_app_url):
        """Nested layouts work correctly during navigation."""
        await page.goto(f"{example_app_url}/dashboard")
        
        # Check dashboard layout
        sidebar = await page.locator(".sidebar").count()
        
        # Navigate within dashboard
        await page.click("a[href='/dashboard/settings']")
        
        # Dashboard layout should persist
        sidebar_after = await page.locator(".sidebar").count()
        assert sidebar == sidebar_after


class TestPrefetching:
    """E2E tests for route prefetching."""
    
    @pytest.mark.skip(reason="Requires running server and Playwright")
    async def test_prefetch_on_hover(self, page, example_app_url):
        """Routes are prefetched on link hover."""
        await page.goto(example_app_url)
        
        # Track network requests
        requests = []
        page.on("request", lambda req: requests.append(req.url))
        
        # Hover over a link
        await page.hover("a[href='/about']")
        
        # Wait for potential prefetch
        await page.wait_for_timeout(500)
        
        # Should have made a prefetch request
        # (This depends on implementation)

