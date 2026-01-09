"""
Phase 34.2: CSS Browser Behavior E2E Tests

Tests that verify CSS features work correctly in a real browser:
- CSS variable inheritance (cascade)
- Computed style resolution (% → px, colors → rgb)
- getComputedStyle with pseudo-elements

These tests use Playwright to run in a real Chromium browser.

Total: 12 tests
"""

import pytest

# Check if playwright is available
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture(scope="function")
def browser_page():
    """Create a browser page for each test."""
    if not PLAYWRIGHT_AVAILABLE:
        pytest.skip("Playwright not installed")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        yield page
        page.close()
        browser.close()


def load_test_html(page, html_content: str):
    """Load HTML content directly into the browser page."""
    page.set_content(html_content)


# =============================================================================
# CSS Variable Inheritance Tests (4 tests)
# =============================================================================

class TestCSSVariableInheritance:
    """Tests for CSS variable cascading/inheritance behavior."""
    
    def test_variable_inherits_to_child(self, browser_page):
        """Child element should inherit CSS variable from parent."""
        html = """
        <div id="parent">
            <div id="child">Child</div>
        </div>
        <script>
            const parent = document.getElementById('parent');
            const child = document.getElementById('child');
            
            // Set variable on parent
            parent.style.setProperty('--color', 'blue');
            
            // Store result for assertion
            const computed = window.getComputedStyle(child);
            window.testResult = computed.getPropertyValue('--color').trim();
        </script>
        """
        load_test_html(browser_page, html)
        result = browser_page.evaluate("window.testResult")
        assert result == "blue", f"Expected 'blue', got '{result}'"
    
    def test_variable_inherits_deeply_nested(self, browser_page):
        """Deeply nested elements should inherit CSS variables from ancestors."""
        html = """
        <div id="root">
            <div id="level1">
                <div id="level2">
                    <div id="level3">Deep</div>
                </div>
            </div>
        </div>
        <script>
            const root = document.getElementById('root');
            const level3 = document.getElementById('level3');
            
            // Set on root
            root.style.setProperty('--theme', 'dark');
            
            // Should cascade to deeply nested element
            const computed = window.getComputedStyle(level3);
            window.testResult = computed.getPropertyValue('--theme').trim();
        </script>
        """
        load_test_html(browser_page, html)
        result = browser_page.evaluate("window.testResult")
        assert result == "dark"
    
    def test_variable_override_at_child_level(self, browser_page):
        """Child can override inherited CSS variable."""
        html = """
        <div id="parent">
            <div id="child">Child</div>
        </div>
        <script>
            const parent = document.getElementById('parent');
            const child = document.getElementById('child');
            
            // Set on parent
            parent.style.setProperty('--color', 'blue');
            // Override on child
            child.style.setProperty('--color', 'red');
            
            const parentComputed = window.getComputedStyle(parent);
            const childComputed = window.getComputedStyle(child);
            
            window.parentValue = parentComputed.getPropertyValue('--color').trim();
            window.childValue = childComputed.getPropertyValue('--color').trim();
        </script>
        """
        load_test_html(browser_page, html)
        parent_val = browser_page.evaluate("window.parentValue")
        child_val = browser_page.evaluate("window.childValue")
        
        assert parent_val == "blue", f"Parent should have 'blue', got '{parent_val}'"
        assert child_val == "red", f"Child should have 'red', got '{child_val}'"
    
    def test_root_variable_accessible_everywhere(self, browser_page):
        """Variable set on :root should be accessible on any element."""
        html = """
        <style>
            :root {
                --global-spacing: 16px;
            }
        </style>
        <div id="element">Element</div>
        <script>
            const el = document.getElementById('element');
            const computed = window.getComputedStyle(el);
            window.testResult = computed.getPropertyValue('--global-spacing').trim();
        </script>
        """
        load_test_html(browser_page, html)
        result = browser_page.evaluate("window.testResult")
        assert result == "16px"


# =============================================================================
# Computed Style Resolution Tests (5 tests)
# =============================================================================

class TestComputedStyleResolution:
    """Tests for computed style value resolution (%, em → px, etc.)."""
    
    def test_percentage_width_resolves_to_px(self, browser_page):
        """width: 50% should resolve to px in getComputedStyle."""
        html = """
        <div id="parent" style="width: 400px;">
            <div id="child" style="width: 50%;">Child</div>
        </div>
        <script>
            const child = document.getElementById('child');
            const computed = window.getComputedStyle(child);
            window.testResult = computed.width;
        </script>
        """
        load_test_html(browser_page, html)
        result = browser_page.evaluate("window.testResult")
        # Should be "200px" (50% of 400px)
        assert result == "200px", f"Expected '200px', got '{result}'"
    
    def test_em_font_size_resolves_to_px(self, browser_page):
        """font-size: 2em should resolve to px."""
        html = """
        <div id="parent" style="font-size: 16px;">
            <div id="child" style="font-size: 2em;">Child</div>
        </div>
        <script>
            const child = document.getElementById('child');
            const computed = window.getComputedStyle(child);
            window.testResult = computed.fontSize;
        </script>
        """
        load_test_html(browser_page, html)
        result = browser_page.evaluate("window.testResult")
        # Should be "32px" (2 * 16px)
        assert result == "32px", f"Expected '32px', got '{result}'"
    
    def test_color_name_resolves_to_rgb(self, browser_page):
        """color: red should resolve to rgb() in getComputedStyle."""
        html = """
        <div id="element" style="color: red;">Text</div>
        <script>
            const el = document.getElementById('element');
            const computed = window.getComputedStyle(el);
            window.testResult = computed.color;
        </script>
        """
        load_test_html(browser_page, html)
        result = browser_page.evaluate("window.testResult")
        # Should be "rgb(255, 0, 0)"
        assert "rgb(255, 0, 0)" in result or "rgb(255,0,0)" in result.replace(" ", "")
    
    def test_hex_color_resolves_to_rgb(self, browser_page):
        """color: #0000ff should resolve to rgb() in getComputedStyle."""
        html = """
        <div id="element" style="color: #0000ff;">Text</div>
        <script>
            const el = document.getElementById('element');
            const computed = window.getComputedStyle(el);
            window.testResult = computed.color;
        </script>
        """
        load_test_html(browser_page, html)
        result = browser_page.evaluate("window.testResult")
        # Should be "rgb(0, 0, 255)"
        assert "rgb(0, 0, 255)" in result or "rgb(0,0,255)" in result.replace(" ", "")
    
    def test_calc_resolves_to_px(self, browser_page):
        """width: calc(100px + 50px) should resolve to px."""
        html = """
        <div id="element" style="width: calc(100px + 50px);">Element</div>
        <script>
            const el = document.getElementById('element');
            const computed = window.getComputedStyle(el);
            window.testResult = computed.width;
        </script>
        """
        load_test_html(browser_page, html)
        result = browser_page.evaluate("window.testResult")
        # Should be "150px"
        assert result == "150px", f"Expected '150px', got '{result}'"


# =============================================================================
# Pseudo-Element Computed Styles Tests (3 tests)
# =============================================================================

class TestPseudoElementStyles:
    """Tests for getComputedStyle with ::before and ::after."""
    
    def test_before_pseudo_content(self, browser_page):
        """getComputedStyle(el, '::before') should return pseudo-element styles."""
        html = """
        <style>
            #element::before {
                content: "PREFIX";
                color: green;
            }
        </style>
        <div id="element">Text</div>
        <script>
            const el = document.getElementById('element');
            const before = window.getComputedStyle(el, '::before');
            window.testContent = before.content;
            window.testColor = before.color;
        </script>
        """
        load_test_html(browser_page, html)
        content = browser_page.evaluate("window.testContent")
        color = browser_page.evaluate("window.testColor")
        
        # Content should be "PREFIX" (with quotes in some browsers)
        assert "PREFIX" in content
        # Color should be green (rgb(0, 128, 0))
        assert "rgb(0, 128, 0)" in color or "rgb(0,128,0)" in color.replace(" ", "")
    
    def test_after_pseudo_content(self, browser_page):
        """getComputedStyle(el, '::after') should return pseudo-element styles."""
        html = """
        <style>
            #element::after {
                content: "SUFFIX";
                font-weight: bold;
            }
        </style>
        <div id="element">Text</div>
        <script>
            const el = document.getElementById('element');
            const after = window.getComputedStyle(el, '::after');
            window.testContent = after.content;
            window.testWeight = after.fontWeight;
        </script>
        """
        load_test_html(browser_page, html)
        content = browser_page.evaluate("window.testContent")
        weight = browser_page.evaluate("window.testWeight")
        
        assert "SUFFIX" in content
        # Bold is typically 700
        assert weight in ("700", "bold")
    
    def test_pseudo_inherits_from_element(self, browser_page):
        """Pseudo-elements should inherit CSS variables from parent element."""
        html = """
        <style>
            #element {
                --pseudo-color: purple;
            }
            #element::before {
                content: "•";
                color: var(--pseudo-color);
            }
        </style>
        <div id="element">Text</div>
        <script>
            const el = document.getElementById('element');
            const before = window.getComputedStyle(el, '::before');
            window.testColor = before.color;
        </script>
        """
        load_test_html(browser_page, html)
        color = browser_page.evaluate("window.testColor")
        
        # Purple is rgb(128, 0, 128)
        assert "rgb(128, 0, 128)" in color or "rgb(128,0,128)" in color.replace(" ", "")


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

