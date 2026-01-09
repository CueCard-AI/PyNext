"""
Phase 34.3: CSS Typed OM E2E Browser Tests

End-to-end tests that verify CSS Typed OM works correctly in a real browser.
These tests use Playwright to test actual browser behavior.

Total: 25 tests
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


# =============================================================================
# CSS Factory Browser Tests (5 tests)
# =============================================================================

@pytest.mark.e2e
class TestCSSFactoryBrowser:
    """E2E tests for CSS factory methods in browser."""
    
    def test_css_px_creates_unit_value(self, browser_page):
        """CSS.px(100) should create a CSSUnitValue in browser."""
        browser_page.goto("about:blank")
        
        result = browser_page.evaluate('''() => {
            const val = CSS.px(100);
            return {
                value: val.value,
                unit: val.unit,
                toString: val.toString()
            };
        }''')
        
        assert result["value"] == 100
        assert result["unit"] == "px"
        assert result["toString"] == "100px"
    
    def test_css_percent_creates_unit_value(self, browser_page):
        """CSS.percent(50) should create a CSSUnitValue."""
        browser_page.goto("about:blank")
        
        result = browser_page.evaluate('''() => {
            const val = CSS.percent(50);
            return {
                value: val.value,
                unit: val.unit
            };
        }''')
        
        assert result["value"] == 50
        assert result["unit"] == "percent"
    
    def test_css_deg_creates_angle(self, browser_page):
        """CSS.deg(45) should create an angle CSSUnitValue."""
        browser_page.goto("about:blank")
        
        result = browser_page.evaluate('''() => {
            const val = CSS.deg(45);
            return {
                value: val.value,
                unit: val.unit
            };
        }''')
        
        assert result["value"] == 45
        assert result["unit"] == "deg"
    
    def test_css_rem_creates_length(self, browser_page):
        """CSS.rem(2) should create a rem CSSUnitValue."""
        browser_page.goto("about:blank")
        
        result = browser_page.evaluate('''() => {
            const val = CSS.rem(2);
            return {
                value: val.value,
                unit: val.unit
            };
        }''')
        
        assert result["value"] == 2
        assert result["unit"] == "rem"
    
    def test_css_keyword_creates_keyword_value(self, browser_page):
        """CSS.keyword should create CSSKeywordValue (if supported)."""
        browser_page.goto("about:blank")
        
        # Note: CSS.keyword may not be in all browsers
        result = browser_page.evaluate('''() => {
            try {
                // Try creating a CSSKeywordValue directly if CSS.keyword not available
                const kw = new CSSKeywordValue("auto");
                return { value: kw.value, supported: true };
            } catch (e) {
                return { supported: false, error: e.message };
            }
        }''')
        
        if result.get("supported"):
            assert result["value"] == "auto"


# =============================================================================
# CSSUnitValue Arithmetic Browser Tests (5 tests)
# =============================================================================

@pytest.mark.e2e
class TestArithmeticBrowser:
    """E2E tests for CSSUnitValue arithmetic in browser."""
    
    def test_add_same_unit(self, browser_page):
        """Adding values with same unit should work."""
        browser_page.goto("about:blank")
        
        result = browser_page.evaluate('''() => {
            const a = CSS.px(100);
            const b = CSS.px(50);
            const sum = a.add(b);
            return { value: sum.value, unit: sum.unit };
        }''')
        
        assert result["value"] == 150
        assert result["unit"] == "px"
    
    def test_mul_scalar(self, browser_page):
        """Multiplying by scalar should work."""
        browser_page.goto("about:blank")
        
        result = browser_page.evaluate('''() => {
            const val = CSS.px(100);
            const doubled = val.mul(2);
            return { value: doubled.value, unit: doubled.unit };
        }''')
        
        assert result["value"] == 200
        assert result["unit"] == "px"
    
    def test_div_scalar(self, browser_page):
        """Dividing by scalar should work."""
        browser_page.goto("about:blank")
        
        result = browser_page.evaluate('''() => {
            const val = CSS.px(100);
            const half = val.div(2);
            return { value: half.value, unit: half.unit };
        }''')
        
        assert result["value"] == 50
        assert result["unit"] == "px"
    
    def test_sub_same_unit(self, browser_page):
        """Subtracting values with same unit should work."""
        browser_page.goto("about:blank")
        
        result = browser_page.evaluate('''() => {
            const a = CSS.px(100);
            const b = CSS.px(30);
            const diff = a.sub(b);
            return { value: diff.value, unit: diff.unit };
        }''')
        
        assert result["value"] == 70
        assert result["unit"] == "px"
    
    def test_equals_same_value(self, browser_page):
        """Comparing equal values should return true."""
        browser_page.goto("about:blank")
        
        result = browser_page.evaluate('''() => {
            const a = CSS.px(100);
            const b = CSS.px(100);
            return a.equals(b);
        }''')
        
        assert result is True


# =============================================================================
# StylePropertyMap Browser Tests (8 tests)
# =============================================================================

@pytest.mark.e2e
class TestStylePropertyMapBrowser:
    """E2E tests for StylePropertyMap in browser."""
    
    def test_set_and_get_width(self, browser_page):
        """Setting and getting width with typed value should work."""
        browser_page.goto("about:blank")
        
        result = browser_page.evaluate('''() => {
            const el = document.createElement("div");
            document.body.appendChild(el);
            
            el.attributeStyleMap.set("width", CSS.px(200));
            const width = el.attributeStyleMap.get("width");
            
            return { value: width.value, unit: width.unit };
        }''')
        
        assert result["value"] == 200
        assert result["unit"] == "px"
    
    def test_delete_property(self, browser_page):
        """Deleting a property should work."""
        browser_page.goto("about:blank")
        
        result = browser_page.evaluate('''() => {
            const el = document.createElement("div");
            document.body.appendChild(el);
            
            el.attributeStyleMap.set("width", CSS.px(200));
            el.attributeStyleMap.delete("width");
            
            return el.attributeStyleMap.has("width");
        }''')
        
        assert result is False
    
    def test_clear_all_properties(self, browser_page):
        """Clearing all properties should work."""
        browser_page.goto("about:blank")
        
        result = browser_page.evaluate('''() => {
            const el = document.createElement("div");
            document.body.appendChild(el);
            
            el.attributeStyleMap.set("width", CSS.px(200));
            el.attributeStyleMap.set("height", CSS.px(100));
            el.attributeStyleMap.clear();
            
            return el.attributeStyleMap.size;
        }''')
        
        assert result == 0
    
    def test_has_property(self, browser_page):
        """Checking if property exists should work."""
        browser_page.goto("about:blank")
        
        result = browser_page.evaluate('''() => {
            const el = document.createElement("div");
            document.body.appendChild(el);
            
            el.attributeStyleMap.set("width", CSS.px(200));
            
            return {
                hasWidth: el.attributeStyleMap.has("width"),
                hasHeight: el.attributeStyleMap.has("height")
            };
        }''')
        
        assert result["hasWidth"] is True
        assert result["hasHeight"] is False
    
    def test_size_property(self, browser_page):
        """Size should reflect number of properties."""
        browser_page.goto("about:blank")
        
        result = browser_page.evaluate('''() => {
            const el = document.createElement("div");
            document.body.appendChild(el);
            
            const before = el.attributeStyleMap.size;
            el.attributeStyleMap.set("width", CSS.px(200));
            el.attributeStyleMap.set("height", CSS.px(100));
            const after = el.attributeStyleMap.size;
            
            return { before, after };
        }''')
        
        assert result["before"] == 0
        assert result["after"] == 2
    
    def test_set_transform(self, browser_page):
        """Setting transform with CSSTransformValue should work."""
        browser_page.goto("about:blank")
        
        result = browser_page.evaluate('''() => {
            const el = document.createElement("div");
            document.body.appendChild(el);
            
            const transform = new CSSTransformValue([
                new CSSTranslate(CSS.px(100), CSS.px(50))
            ]);
            el.attributeStyleMap.set("transform", transform);
            
            const got = el.attributeStyleMap.get("transform");
            return got instanceof CSSTransformValue;
        }''')
        
        assert result is True
    
    def test_iterate_keys(self, browser_page):
        """Iterating keys should work."""
        browser_page.goto("about:blank")
        
        result = browser_page.evaluate('''() => {
            const el = document.createElement("div");
            document.body.appendChild(el);
            
            el.attributeStyleMap.set("width", CSS.px(200));
            el.attributeStyleMap.set("height", CSS.px(100));
            
            const keys = [...el.attributeStyleMap.keys()];
            return keys;
        }''')
        
        assert "width" in result
        assert "height" in result
    
    def test_rendered_element_has_correct_style(self, browser_page):
        """Setting style via attributeStyleMap should affect rendering."""
        browser_page.goto("about:blank")
        
        browser_page.evaluate('''() => {
            const el = document.createElement("div");
            el.id = "test-box";
            document.body.appendChild(el);
            
            el.attributeStyleMap.set("width", CSS.px(200));
            el.attributeStyleMap.set("height", CSS.px(100));
        }''')
        
        box = browser_page.locator("#test-box")
        width = box.evaluate("el => window.getComputedStyle(el).width")
        height = box.evaluate("el => window.getComputedStyle(el).height")
        
        assert width == "200px"
        assert height == "100px"


# =============================================================================
# ComputedStyleMap Browser Tests (4 tests)
# =============================================================================

@pytest.mark.e2e
class TestComputedStyleMapBrowser:
    """E2E tests for computedStyleMap in browser."""
    
    def test_computed_width(self, browser_page):
        """Getting computed width should return resolved value."""
        browser_page.goto("about:blank")
        
        result = browser_page.evaluate('''() => {
            const el = document.createElement("div");
            el.style.width = "200px";
            document.body.appendChild(el);
            
            const computed = el.computedStyleMap();
            const width = computed.get("width");
            
            return { value: width.value, unit: width.unit };
        }''')
        
        assert result["value"] == 200
        assert result["unit"] == "px"
    
    def test_computed_resolves_percentage(self, browser_page):
        """Computed styles should resolve percentages to pixels."""
        browser_page.goto("about:blank")
        
        result = browser_page.evaluate('''() => {
            const container = document.createElement("div");
            container.style.width = "400px";
            container.style.display = "block";
            container.style.position = "relative";
            document.body.appendChild(container);
            
            const child = document.createElement("div");
            child.style.width = "50%";
            child.style.display = "block";
            container.appendChild(child);
            
            // Force layout
            container.offsetHeight;
            child.offsetHeight;
            
            const computed = child.computedStyleMap();
            const width = computed.get("width");
            
            return { value: width.value, unit: width.unit };
        }''')
        
        # 50% of 400px = 200px (computed styles resolve to pixels)
        # But computedStyleMap might return the percentage depending on browser
        assert result["unit"] == "px" or result["unit"] == "percent"
        if result["unit"] == "px":
            assert result["value"] == 200
        else:
            # If returned as percentage, value should be 50
            assert result["value"] == 50
    
    def test_computed_has_many_properties(self, browser_page):
        """Computed style map should have many properties."""
        browser_page.goto("about:blank")
        
        result = browser_page.evaluate('''() => {
            const el = document.createElement("div");
            document.body.appendChild(el);
            
            const computed = el.computedStyleMap();
            return computed.size;
        }''')
        
        # Should have many computed properties
        assert result > 100
    
    def test_computed_is_read_only(self, browser_page):
        """Computed style map should be read-only."""
        browser_page.goto("about:blank")
        
        result = browser_page.evaluate('''() => {
            const el = document.createElement("div");
            document.body.appendChild(el);
            
            const computed = el.computedStyleMap();
            
            try {
                computed.set("width", CSS.px(200));
                return { error: null };
            } catch (e) {
                return { error: e.name };
            }
        }''')
        
        # Should throw an error as computed styles are read-only
        assert result["error"] is not None


# =============================================================================
# Transform Browser Tests (3 tests)
# =============================================================================

@pytest.mark.e2e
class TestTransformBrowser:
    """E2E tests for CSS transforms in browser."""
    
    def test_translate_transform(self, browser_page):
        """CSSTranslate should translate element."""
        browser_page.goto("about:blank")
        
        result = browser_page.evaluate('''() => {
            const el = document.createElement("div");
            el.style.width = "100px";
            el.style.height = "100px";
            el.style.position = "absolute";
            el.style.top = "0";
            el.style.left = "0";
            document.body.appendChild(el);
            
            const transform = new CSSTransformValue([
                new CSSTranslate(CSS.px(50), CSS.px(25))
            ]);
            el.attributeStyleMap.set("transform", transform);
            
            const rect = el.getBoundingClientRect();
            return { left: rect.left, top: rect.top };
        }''')
        
        assert result["left"] == 50
        assert result["top"] == 25
    
    def test_rotate_transform(self, browser_page):
        """CSSRotate should rotate element."""
        browser_page.goto("about:blank")
        
        result = browser_page.evaluate('''() => {
            const el = document.createElement("div");
            document.body.appendChild(el);
            
            const transform = new CSSTransformValue([
                new CSSRotate(CSS.deg(45))
            ]);
            el.attributeStyleMap.set("transform", transform);
            
            const got = el.attributeStyleMap.get("transform");
            return got.length;
        }''')
        
        assert result == 1
    
    def test_combined_transforms(self, browser_page):
        """Multiple transforms should combine correctly."""
        browser_page.goto("about:blank")
        
        result = browser_page.evaluate('''() => {
            const el = document.createElement("div");
            document.body.appendChild(el);
            
            const transform = new CSSTransformValue([
                new CSSTranslate(CSS.px(100), CSS.px(50)),
                new CSSRotate(CSS.deg(45)),
                new CSSScale(2, 2)
            ]);
            el.attributeStyleMap.set("transform", transform);
            
            const got = el.attributeStyleMap.get("transform");
            return {
                length: got.length,
                is2D: got.is2D
            };
        }''')
        
        assert result["length"] == 3
        assert result["is2D"] is True
