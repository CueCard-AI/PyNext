"""
End-to-end tests for PyNext reactivity in the browser.

Tests signal updates, effects, and DOM synchronization.
"""

import pytest

# These tests require Playwright and a running server
# Mark them to skip if Playwright is not available
pytestmark = pytest.mark.e2e


@pytest.fixture
def example_app_url():
    """URL of the running example app."""
    return "http://localhost:3000"


class TestSignalReactivity:
    """E2E tests for signal reactivity."""
    
    @pytest.mark.skip(reason="Requires running server and Playwright")
    async def test_counter_increment(self, page, example_app_url):
        """Counter increments when button is clicked."""
        await page.goto(example_app_url)
        
        # Find counter display
        counter = page.locator("[data-testid='counter']")
        initial_value = await counter.text_content()
        
        # Click increment button
        await page.click("[data-testid='increment']")
        
        # Check value updated
        new_value = await counter.text_content()
        assert int(new_value) == int(initial_value) + 1
    
    @pytest.mark.skip(reason="Requires running server and Playwright")
    async def test_input_binding(self, page, example_app_url):
        """Input value syncs with signal."""
        await page.goto(example_app_url)
        
        # Type in input
        await page.fill("[data-testid='name-input']", "Alice")
        
        # Check display updated
        display = page.locator("[data-testid='greeting']")
        assert "Alice" in await display.text_content()


class TestHydration:
    """E2E tests for hydration."""
    
    @pytest.mark.skip(reason="Requires running server and Playwright")
    async def test_page_hydrates(self, page, example_app_url):
        """Page hydrates correctly."""
        await page.goto(example_app_url)
        
        # Wait for hydration
        await page.wait_for_function("window.__pynext__ !== undefined")
        
        # Check signals exist
        signals_exist = await page.evaluate("Object.keys(window.__pynext__.signals).length > 0")
        assert signals_exist


class TestNavigation:
    """E2E tests for navigation."""
    
    @pytest.mark.skip(reason="Requires running server and Playwright")
    async def test_link_navigation(self, page, example_app_url):
        """Clicking links navigates correctly."""
        await page.goto(example_app_url)
        
        # Click about link
        await page.click("a[href='/about']")
        
        # Check URL changed
        assert "/about" in page.url
        
        # Check content updated
        assert "About" in await page.text_content("h1")

