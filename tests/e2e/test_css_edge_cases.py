"""
Phase 34.2: CSS Edge Cases E2E Tests

Browser-based tests for edge case CSS behaviors:
- Empty string removes style property
- classList deduplication
- Detached element computed styles
- Animation cancellation
- Style property removal
- getPropertyPriority for !important
- Transition/animation events
- Multiple animations
- Invalid CSS value handling
- CSS keyword values

Total: 19 tests
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
# Empty String Style Removal Tests (2 tests)
# =============================================================================

class TestEmptyStringRemoval:
    """Tests for removing styles by setting empty string."""
    
    def test_empty_string_removes_inline_style(self, browser_page):
        """Setting style to empty string should remove the property."""
        html = """
        <div id="box" style="display: flex;">Box</div>
        <script>
            const box = document.getElementById('box');
            // Initially has display: flex
            window.before = box.style.display;
            // Set to empty to remove
            box.style.display = '';
            window.after = box.style.display;
        </script>
        """
        load_test_html(browser_page, html)
        before = browser_page.evaluate("window.before")
        after = browser_page.evaluate("window.after")
        
        assert before == "flex"
        assert after == "", f"Expected empty string, got '{after}'"
    
    def test_remove_property_removes_style(self, browser_page):
        """removeProperty should remove the style."""
        html = """
        <div id="box" style="color: red; background: blue;">Box</div>
        <script>
            const box = document.getElementById('box');
            window.before = box.style.color;
            box.style.removeProperty('color');
            window.after = box.style.color;
            // Background should still be there
            window.bg = box.style.backgroundColor;
        </script>
        """
        load_test_html(browser_page, html)
        before = browser_page.evaluate("window.before")
        after = browser_page.evaluate("window.after")
        bg = browser_page.evaluate("window.bg")
        
        assert before == "red"
        assert after == ""
        assert bg == "blue"


# =============================================================================
# classList Deduplication Tests (2 tests)
# =============================================================================

class TestClassListDeduplication:
    """Tests for classList handling of duplicate classes."""
    
    def test_add_existing_class_no_duplicate(self, browser_page):
        """Adding an existing class should not create duplicates."""
        html = """
        <div id="box" class="card active">Box</div>
        <script>
            const box = document.getElementById('box');
            window.before = box.classList.length;
            box.classList.add('active');  // Already exists
            window.after = box.classList.length;
            window.className = box.className;
        </script>
        """
        load_test_html(browser_page, html)
        before = browser_page.evaluate("window.before")
        after = browser_page.evaluate("window.after")
        class_name = browser_page.evaluate("window.className")
        
        assert before == 2
        assert after == 2  # Should not increase
        assert class_name.count("active") == 1
    
    def test_remove_nonexistent_class_no_error(self, browser_page):
        """Removing a class that doesn't exist should not error."""
        html = """
        <div id="box" class="card">Box</div>
        <script>
            const box = document.getElementById('box');
            window.error = null;
            try {
                box.classList.remove('nonexistent');
                window.success = true;
            } catch (e) {
                window.error = e.message;
                window.success = false;
            }
            window.className = box.className;
        </script>
        """
        load_test_html(browser_page, html)
        success = browser_page.evaluate("window.success")
        class_name = browser_page.evaluate("window.className")
        
        assert success is True
        assert class_name == "card"


# =============================================================================
# getPropertyPriority Tests (2 tests)
# =============================================================================

class TestPropertyPriority:
    """Tests for !important priority handling."""
    
    def test_set_property_with_important(self, browser_page):
        """setProperty with 'important' priority should work."""
        html = """
        <div id="box">Box</div>
        <script>
            const box = document.getElementById('box');
            box.style.setProperty('color', 'red', 'important');
            window.priority = box.style.getPropertyPriority('color');
            window.value = box.style.getPropertyValue('color');
        </script>
        """
        load_test_html(browser_page, html)
        priority = browser_page.evaluate("window.priority")
        value = browser_page.evaluate("window.value")
        
        assert priority == "important"
        assert value == "red"
    
    def test_csstext_includes_important(self, browser_page):
        """cssText should include !important when set."""
        html = """
        <div id="box">Box</div>
        <script>
            const box = document.getElementById('box');
            box.style.setProperty('display', 'flex', 'important');
            window.cssText = box.style.cssText;
        </script>
        """
        load_test_html(browser_page, html)
        css_text = browser_page.evaluate("window.cssText")
        
        assert "important" in css_text.lower()
        assert "display" in css_text.lower()


# =============================================================================
# Detached Element Tests (2 tests)
# =============================================================================

class TestDetachedElements:
    """Tests for style operations on detached elements."""
    
    def test_style_on_created_element(self, browser_page):
        """Can set styles on element before adding to DOM."""
        html = """
        <script>
            const box = document.createElement('div');
            box.style.display = 'flex';
            box.style.backgroundColor = 'blue';
            window.display = box.style.display;
            window.bg = box.style.backgroundColor;
        </script>
        """
        load_test_html(browser_page, html)
        display = browser_page.evaluate("window.display")
        bg = browser_page.evaluate("window.bg")
        
        assert display == "flex"
        assert bg == "blue"
    
    def test_computed_style_on_detached(self, browser_page):
        """getComputedStyle on detached element should work (returns defaults)."""
        html = """
        <script>
            const box = document.createElement('div');
            box.style.width = '100px';
            const computed = window.getComputedStyle(box);
            // Detached elements may have limited computed styles
            window.hasComputed = computed !== null;
            window.display = computed.display;  // Default is usually 'block' or ''
        </script>
        """
        load_test_html(browser_page, html)
        has_computed = browser_page.evaluate("window.hasComputed")
        
        assert has_computed is True


# =============================================================================
# Animation Cancellation Tests (2 tests)
# =============================================================================

class TestAnimationCancellation:
    """Tests for animation control and cancellation."""
    
    def test_animation_cancel(self, browser_page):
        """Canceling animation should stop it."""
        html = """
        <div id="box" style="width: 100px; height: 100px; background: red;">Box</div>
        <script>
            const box = document.getElementById('box');
            const anim = box.animate([
                { opacity: 1 },
                { opacity: 0 }
            ], { duration: 1000 });
            
            window.stateBeforeCancel = anim.playState;
            anim.cancel();
            window.stateAfterCancel = anim.playState;
        </script>
        """
        load_test_html(browser_page, html)
        before = browser_page.evaluate("window.stateBeforeCancel")
        after = browser_page.evaluate("window.stateAfterCancel")
        
        assert before in ("running", "pending")
        assert after == "idle"
    
    def test_animation_pause_resume(self, browser_page):
        """Animation can be paused and resumed."""
        html = """
        <div id="box" style="width: 100px; height: 100px; background: red;">Box</div>
        <script>
            const box = document.getElementById('box');
            const anim = box.animate([
                { transform: 'translateX(0)' },
                { transform: 'translateX(100px)' }
            ], { duration: 1000 });
            
            window.stateRunning = anim.playState;
            anim.pause();
            window.statePaused = anim.playState;
            anim.play();
            window.stateResumed = anim.playState;
        </script>
        """
        load_test_html(browser_page, html)
        running = browser_page.evaluate("window.stateRunning")
        paused = browser_page.evaluate("window.statePaused")
        resumed = browser_page.evaluate("window.stateResumed")
        
        assert running in ("running", "pending")
        assert paused == "paused"
        assert resumed in ("running", "pending")


# =============================================================================
# Transition Event Tests (2 tests)
# =============================================================================

class TestTransitionEvents:
    """Tests for CSS transition events."""
    
    def test_transitionend_fires(self, browser_page):
        """transitionend event should fire after transition completes."""
        html = """
        <style>
            #box {
                width: 100px;
                height: 100px;
                background: red;
                transition: width 0.1s ease;
            }
        </style>
        <div id="box">Box</div>
        <script>
            const box = document.getElementById('box');
            window.transitionEnded = false;
            box.addEventListener('transitionend', () => {
                window.transitionEnded = true;
            });
            // Force reflow before triggering transition
            box.offsetHeight;
            // Trigger transition
            box.style.width = '200px';
        </script>
        """
        load_test_html(browser_page, html)
        # Wait for transition to complete (100ms transition + buffer)
        browser_page.wait_for_timeout(300)
        result = browser_page.evaluate("window.transitionEnded")
        assert result is True
    
    def test_transitionend_event_properties(self, browser_page):
        """transitionend event should have correct properties."""
        html = """
        <style>
            #box {
                width: 100px;
                transition: width 0.1s;
            }
        </style>
        <div id="box">Box</div>
        <script>
            const box = document.getElementById('box');
            window.eventProps = {};
            box.addEventListener('transitionend', (e) => {
                window.eventProps = {
                    propertyName: e.propertyName,
                    elapsedTime: e.elapsedTime
                };
            });
            // Force reflow
            box.offsetHeight;
            box.style.width = '200px';
        </script>
        """
        load_test_html(browser_page, html)
        browser_page.wait_for_timeout(300)
        props = browser_page.evaluate("window.eventProps")
        assert props.get("propertyName") == "width"
        assert props.get("elapsedTime") >= 0.1


# =============================================================================
# Multiple Animations Tests (3 tests)
# =============================================================================

class TestMultipleAnimations:
    """Tests for multiple animations on same element."""
    
    def test_two_animations_simultaneously(self, browser_page):
        """Two animations can run on same element."""
        html = """
        <div id="box" style="width: 100px; height: 100px; background: red;">Box</div>
        <script>
            const box = document.getElementById('box');
            const anim1 = box.animate([
                { opacity: 1 },
                { opacity: 0.5 }
            ], { duration: 200 });
            const anim2 = box.animate([
                { transform: 'scale(1)' },
                { transform: 'scale(1.5)' }
            ], { duration: 200 });
            
            window.anim1State = anim1.playState;
            window.anim2State = anim2.playState;
        </script>
        """
        load_test_html(browser_page, html)
        state1 = browser_page.evaluate("window.anim1State")
        state2 = browser_page.evaluate("window.anim2State")
        
        assert state1 in ("running", "pending")
        assert state2 in ("running", "pending")
    
    def test_get_animations_returns_all(self, browser_page):
        """getAnimations() should return all running animations."""
        html = """
        <div id="box" style="width: 100px; height: 100px;">Box</div>
        <script>
            const box = document.getElementById('box');
            box.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 1000 });
            box.animate([{ transform: 'rotate(0)' }, { transform: 'rotate(360deg)' }], { duration: 1000 });
            box.animate([{ backgroundColor: 'red' }, { backgroundColor: 'blue' }], { duration: 1000 });
            
            window.animCount = box.getAnimations().length;
        </script>
        """
        load_test_html(browser_page, html)
        count = browser_page.evaluate("window.animCount")
        assert count == 3
    
    def test_cancel_one_keep_others(self, browser_page):
        """Canceling one animation should not affect others."""
        html = """
        <div id="box" style="width: 100px; height: 100px;">Box</div>
        <script>
            const box = document.getElementById('box');
            const anim1 = box.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 1000 });
            const anim2 = box.animate([{ transform: 'scale(1)' }, { transform: 'scale(2)' }], { duration: 1000 });
            
            window.beforeCancel = box.getAnimations().length;
            anim1.cancel();
            window.afterCancel = box.getAnimations().length;
            window.anim2State = anim2.playState;
        </script>
        """
        load_test_html(browser_page, html)
        before = browser_page.evaluate("window.beforeCancel")
        after = browser_page.evaluate("window.afterCancel")
        state2 = browser_page.evaluate("window.anim2State")
        
        assert before == 2
        assert after == 1
        assert state2 in ("running", "pending")


# =============================================================================
# Invalid CSS Value Tests (2 tests)
# =============================================================================

class TestInvalidCSSValues:
    """Tests for browser handling of invalid CSS values."""
    
    def test_invalid_value_ignored(self, browser_page):
        """Browser should ignore invalid CSS values."""
        html = """
        <div id="box" style="width: 100px;">Box</div>
        <script>
            const box = document.getElementById('box');
            window.before = box.style.width;
            box.style.width = 'banana';  // Invalid
            window.after = box.style.width;
        </script>
        """
        load_test_html(browser_page, html)
        before = browser_page.evaluate("window.before")
        after = browser_page.evaluate("window.after")
        
        assert before == "100px"
        # Invalid value is ignored, original value remains
        assert after == "100px"
    
    def test_valid_after_invalid(self, browser_page):
        """Valid value after invalid should still work."""
        html = """
        <div id="box" style="width: 100px;">Box</div>
        <script>
            const box = document.getElementById('box');
            box.style.width = 'invalid';
            box.style.width = '200px';
            window.finalWidth = box.style.width;
        </script>
        """
        load_test_html(browser_page, html)
        width = browser_page.evaluate("window.finalWidth")
        assert width == "200px"


# =============================================================================
# CSS Keyword Values Tests (2 tests)
# =============================================================================

class TestCSSKeywordValues:
    """Tests for CSS keyword values in browser."""
    
    def test_inherit_applies(self, browser_page):
        """inherit keyword should inherit from parent."""
        html = """
        <div id="parent" style="color: blue;">
            <div id="child" style="color: red;">Child</div>
        </div>
        <script>
            const child = document.getElementById('child');
            window.before = window.getComputedStyle(child).color;
            child.style.color = 'inherit';
            window.after = window.getComputedStyle(child).color;
        </script>
        """
        load_test_html(browser_page, html)
        before = browser_page.evaluate("window.before")
        after = browser_page.evaluate("window.after")
        
        # Before: red, After: blue (inherited from parent)
        # Normalize by removing all spaces for comparison
        before_normalized = before.replace(" ", "")
        after_normalized = after.replace(" ", "")
        assert "255,0,0" in before_normalized  # red
        assert "0,0,255" in after_normalized   # blue
    
    def test_initial_resets(self, browser_page):
        """initial keyword should reset to initial value."""
        html = """
        <div id="box" style="display: flex;">Box</div>
        <script>
            const box = document.getElementById('box');
            window.before = box.style.display;
            box.style.display = 'initial';
            window.after = window.getComputedStyle(box).display;
        </script>
        """
        load_test_html(browser_page, html)
        before = browser_page.evaluate("window.before")
        after = browser_page.evaluate("window.after")
        
        assert before == "flex"
        # initial for display is 'inline'
        assert after == "inline"


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

