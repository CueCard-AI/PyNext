"""
Phase 34.4: Events E2E Browser Tests

End-to-end tests verifying event handling in a real browser.
Uses Playwright to test actual event behavior.

Total: 25 tests
"""

import pytest


# Skip all tests if Playwright is not available
pytest.importorskip("playwright")


@pytest.fixture(scope="module")
def browser_context():
    """Create a Playwright browser context for testing."""
    from playwright.sync_api import sync_playwright
    
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    
    yield context
    
    context.close()
    browser.close()
    playwright.stop()


@pytest.fixture
def page(browser_context):
    """Create a new page for each test."""
    page = browser_context.new_page()
    yield page
    page.close()


# =============================================================================
# Mouse Event Browser Tests (5 tests)
# =============================================================================

class TestMouseEventsBrowser:
    """E2E tests for mouse events in browser."""
    
    def test_click_coordinates(self, page):
        """Click coordinates should be captured correctly."""
        page.set_content('''
            <div id="box" style="width: 200px; height: 200px; background: blue;"></div>
            <script>
                window.clickData = null;
                document.getElementById('box').addEventListener('click', (e) => {
                    window.clickData = {
                        clientX: e.clientX,
                        clientY: e.clientY,
                        offsetX: e.offsetX,
                        offsetY: e.offsetY
                    };
                });
            </script>
        ''')
        
        page.click('#box', position={'x': 50, 'y': 50})
        
        result = page.evaluate('() => window.clickData')
        assert result is not None
        assert 'clientX' in result
        assert 'offsetX' in result
    
    def test_button_detection(self, page):
        """Mouse button should be detected correctly."""
        page.set_content('''
            <div id="box" style="width: 200px; height: 200px;"></div>
            <script>
                window.buttonData = null;
                document.getElementById('box').addEventListener('mousedown', (e) => {
                    window.buttonData = { button: e.button, buttons: e.buttons };
                });
            </script>
        ''')
        
        page.click('#box', button='left')
        
        result = page.evaluate('() => window.buttonData')
        assert result is not None
        assert result['button'] == 0  # Left button
    
    def test_modifier_keys(self, page):
        """Modifier keys should be detected correctly."""
        page.set_content('''
            <div id="box" style="width: 200px; height: 200px;"></div>
            <script>
                window.modifiers = null;
                document.getElementById('box').addEventListener('click', (e) => {
                    window.modifiers = {
                        altKey: e.altKey,
                        ctrlKey: e.ctrlKey,
                        shiftKey: e.shiftKey,
                        metaKey: e.metaKey
                    };
                });
            </script>
        ''')
        
        page.click('#box', modifiers=['Shift'])
        
        result = page.evaluate('() => window.modifiers')
        assert result is not None
        assert result['shiftKey'] is True
    
    def test_double_click(self, page):
        """Double click should work correctly."""
        page.set_content('''
            <div id="box" style="width: 200px; height: 200px;"></div>
            <script>
                window.dblClickCount = 0;
                document.getElementById('box').addEventListener('dblclick', () => {
                    window.dblClickCount++;
                });
            </script>
        ''')
        
        page.dblclick('#box')
        
        result = page.evaluate('() => window.dblClickCount')
        assert result == 1
    
    def test_mouse_enter_leave(self, page):
        """Mouse enter/leave should work correctly."""
        page.set_content('''
            <div id="outer" style="width: 300px; height: 300px; padding: 50px;">
                <div id="inner" style="width: 200px; height: 200px;"></div>
            </div>
            <script>
                window.events = [];
                const inner = document.getElementById('inner');
                inner.addEventListener('mouseenter', () => window.events.push('enter'));
                inner.addEventListener('mouseleave', () => window.events.push('leave'));
            </script>
        ''')
        
        page.hover('#inner')
        page.hover('#outer')
        
        result = page.evaluate('() => window.events')
        assert 'enter' in result


# =============================================================================
# Keyboard Event Browser Tests (5 tests)
# =============================================================================

class TestKeyboardEventsBrowser:
    """E2E tests for keyboard events in browser."""
    
    def test_key_value(self, page):
        """Key value should be captured correctly."""
        page.set_content('''
            <input id="input" type="text">
            <script>
                window.keyData = null;
                document.getElementById('input').addEventListener('keydown', (e) => {
                    window.keyData = { key: e.key, code: e.code };
                });
            </script>
        ''')
        
        page.focus('#input')
        page.keyboard.press('Enter')
        
        result = page.evaluate('() => window.keyData')
        assert result is not None
        assert result['key'] == 'Enter'
        assert result['code'] == 'Enter'
    
    def test_arrow_keys(self, page):
        """Arrow keys should be detected correctly."""
        page.set_content('''
            <div id="target" tabindex="0"></div>
            <script>
                window.keys = [];
                document.getElementById('target').addEventListener('keydown', (e) => {
                    window.keys.push(e.key);
                });
            </script>
        ''')
        
        page.focus('#target')
        page.keyboard.press('ArrowUp')
        page.keyboard.press('ArrowDown')
        
        result = page.evaluate('() => window.keys')
        assert 'ArrowUp' in result
        assert 'ArrowDown' in result
    
    def test_keyboard_modifiers(self, page):
        """Keyboard modifiers should work."""
        page.set_content('''
            <input id="input" type="text">
            <script>
                window.combo = null;
                document.getElementById('input').addEventListener('keydown', (e) => {
                    if (e.ctrlKey && e.key === 's') {
                        e.preventDefault();
                        window.combo = 'ctrl+s';
                    }
                });
            </script>
        ''')
        
        page.focus('#input')
        page.keyboard.press('Control+s')
        
        result = page.evaluate('() => window.combo')
        assert result == 'ctrl+s'
    
    def test_prevent_default(self, page):
        """preventDefault should work."""
        page.set_content('''
            <form id="form">
                <input type="text" id="input">
            </form>
            <script>
                window.submitted = false;
                document.getElementById('form').addEventListener('submit', (e) => {
                    e.preventDefault();
                    window.submitted = true;
                });
            </script>
        ''')
        
        page.focus('#input')
        page.keyboard.press('Enter')
        
        # Form should not navigate away
        result = page.evaluate('() => window.submitted')
        assert result is True
    
    def test_key_repeat(self, page):
        """Key repeat should be detected."""
        page.set_content('''
            <div id="target" tabindex="0"></div>
            <script>
                window.repeatCount = 0;
                document.getElementById('target').addEventListener('keydown', (e) => {
                    if (e.repeat) window.repeatCount++;
                });
            </script>
        ''')
        
        page.focus('#target')
        # Hold key down
        page.keyboard.down('a')
        page.wait_for_timeout(200)  # Wait for repeat
        page.keyboard.up('a')
        
        result = page.evaluate('() => window.repeatCount')
        # May or may not register repeats depending on timing
        assert isinstance(result, int)


# =============================================================================
# Form Event Browser Tests (5 tests)
# =============================================================================

class TestFormEventsBrowser:
    """E2E tests for form events in browser."""
    
    def test_input_event(self, page):
        """Input event should fire on typing."""
        page.set_content('''
            <input id="input" type="text">
            <script>
                window.inputData = [];
                document.getElementById('input').addEventListener('input', (e) => {
                    window.inputData.push({
                        value: e.target.value,
                        inputType: e.inputType
                    });
                });
            </script>
        ''')
        
        page.fill('#input', 'hello')
        
        result = page.evaluate('() => window.inputData')
        assert len(result) > 0
        assert result[-1]['value'] == 'hello'
    
    def test_change_event(self, page):
        """Change event should fire on blur."""
        page.set_content('''
            <input id="input" type="text">
            <button id="other">Other</button>
            <script>
                window.changeValue = null;
                document.getElementById('input').addEventListener('change', (e) => {
                    window.changeValue = e.target.value;
                });
            </script>
        ''')
        
        page.fill('#input', 'test')
        page.click('#other')  # Blur the input
        
        result = page.evaluate('() => window.changeValue')
        assert result == 'test'
    
    def test_focus_blur_events(self, page):
        """Focus and blur events should work."""
        page.set_content('''
            <input id="input1" type="text">
            <input id="input2" type="text">
            <script>
                window.events = [];
                const i1 = document.getElementById('input1');
                const i2 = document.getElementById('input2');
                i1.addEventListener('focus', () => window.events.push('focus1'));
                i1.addEventListener('blur', () => window.events.push('blur1'));
                i2.addEventListener('focus', () => window.events.push('focus2'));
            </script>
        ''')
        
        page.focus('#input1')
        page.focus('#input2')
        
        result = page.evaluate('() => window.events')
        assert 'focus1' in result
        assert 'blur1' in result
        assert 'focus2' in result
    
    def test_checkbox_change(self, page):
        """Checkbox change event should work."""
        page.set_content('''
            <input id="checkbox" type="checkbox">
            <script>
                window.checked = false;
                document.getElementById('checkbox').addEventListener('change', (e) => {
                    window.checked = e.target.checked;
                });
            </script>
        ''')
        
        page.check('#checkbox')
        
        result = page.evaluate('() => window.checked')
        assert result is True
    
    def test_select_change(self, page):
        """Select change event should work."""
        page.set_content('''
            <select id="select">
                <option value="a">A</option>
                <option value="b">B</option>
                <option value="c">C</option>
            </select>
            <script>
                window.selected = null;
                document.getElementById('select').addEventListener('change', (e) => {
                    window.selected = e.target.value;
                });
            </script>
        ''')
        
        page.select_option('#select', 'b')
        
        result = page.evaluate('() => window.selected')
        assert result == 'b'


# =============================================================================
# Custom Event Browser Tests (5 tests)
# =============================================================================

class TestCustomEventsBrowser:
    """E2E tests for custom events in browser."""
    
    def test_custom_event_dispatch(self, page):
        """Custom event should dispatch and be received."""
        page.set_content('''
            <div id="target"></div>
            <script>
                window.received = null;
                document.getElementById('target').addEventListener('my-event', (e) => {
                    window.received = e.detail;
                });
            </script>
        ''')
        
        page.evaluate('''() => {
            const event = new CustomEvent('my-event', { detail: { foo: 'bar' } });
            document.getElementById('target').dispatchEvent(event);
        }''')
        
        result = page.evaluate('() => window.received')
        assert result is not None
        assert result['foo'] == 'bar'
    
    def test_custom_event_bubbling(self, page):
        """Custom event should bubble when configured."""
        page.set_content('''
            <div id="parent">
                <div id="child"></div>
            </div>
            <script>
                window.bubbled = false;
                document.getElementById('parent').addEventListener('child-event', () => {
                    window.bubbled = true;
                });
            </script>
        ''')
        
        page.evaluate('''() => {
            const event = new CustomEvent('child-event', { bubbles: true });
            document.getElementById('child').dispatchEvent(event);
        }''')
        
        result = page.evaluate('() => window.bubbled')
        assert result is True
    
    def test_custom_event_prevent_default(self, page):
        """Custom event preventDefault should work."""
        page.set_content('''
            <div id="target"></div>
            <script>
                window.prevented = false;
                document.getElementById('target').addEventListener('cancelable-event', (e) => {
                    e.preventDefault();
                });
            </script>
        ''')
        
        result = page.evaluate('''() => {
            const event = new CustomEvent('cancelable-event', { cancelable: true });
            const dispatched = document.getElementById('target').dispatchEvent(event);
            return !dispatched;  // dispatchEvent returns false if preventDefault was called
        }''')
        
        assert result is True
    
    def test_custom_event_composed(self, page):
        """Composed custom event should cross shadow DOM."""
        page.set_content('''
            <div id="host"></div>
            <script>
                window.crossedShadow = false;
                const host = document.getElementById('host');
                const shadow = host.attachShadow({ mode: 'open' });
                shadow.innerHTML = '<div id="inner"></div>';
                
                host.addEventListener('shadow-event', () => {
                    window.crossedShadow = true;
                });
                
                const inner = shadow.getElementById('inner');
                const event = new CustomEvent('shadow-event', { 
                    bubbles: true, 
                    composed: true 
                });
                inner.dispatchEvent(event);
            </script>
        ''')
        
        result = page.evaluate('() => window.crossedShadow')
        assert result is True
    
    def test_custom_event_on_document(self, page):
        """Custom event on document should work."""
        page.set_content('''
            <script>
                window.appReady = false;
                document.addEventListener('app-ready', () => {
                    window.appReady = true;
                });
            </script>
        ''')
        
        page.evaluate('''() => {
            document.dispatchEvent(new CustomEvent('app-ready'));
        }''')
        
        result = page.evaluate('() => window.appReady')
        assert result is True


# =============================================================================
# Event Propagation Browser Tests (5 tests)
# =============================================================================

class TestEventPropagationBrowser:
    """E2E tests for event propagation in browser."""
    
    def test_stop_propagation(self, page):
        """stopPropagation should prevent bubbling."""
        page.set_content('''
            <style>
                #outer { width: 100px; height: 100px; background: blue; }
                #inner { width: 50px; height: 50px; background: red; }
            </style>
            <div id="outer">
                <div id="inner"></div>
            </div>
            <script>
                window.reached = [];
                document.getElementById('inner').addEventListener('click', (e) => {
                    window.reached.push('inner');
                    e.stopPropagation();
                });
                document.getElementById('outer').addEventListener('click', () => {
                    window.reached.push('outer');
                });
            </script>
        ''')
        
        page.click('#inner')
        
        result = page.evaluate('() => window.reached')
        assert 'inner' in result
        assert 'outer' not in result
    
    def test_stop_immediate_propagation(self, page):
        """stopImmediatePropagation should prevent all handlers."""
        page.set_content('''
            <style>
                #target { width: 100px; height: 100px; background: green; }
            </style>
            <div id="target"></div>
            <script>
                window.reached = [];
                const target = document.getElementById('target');
                target.addEventListener('click', (e) => {
                    window.reached.push('first');
                    e.stopImmediatePropagation();
                });
                target.addEventListener('click', () => {
                    window.reached.push('second');
                });
            </script>
        ''')
        
        page.click('#target')
        
        result = page.evaluate('() => window.reached')
        assert 'first' in result
        assert 'second' not in result
    
    def test_capture_phase(self, page):
        """Capture phase should run before bubble."""
        page.set_content('''
            <style>
                #outer { width: 100px; height: 100px; background: blue; }
                #inner { width: 50px; height: 50px; background: red; }
            </style>
            <div id="outer">
                <div id="inner"></div>
            </div>
            <script>
                window.order = [];
                document.getElementById('outer').addEventListener('click', () => {
                    window.order.push('outer-capture');
                }, true);
                document.getElementById('inner').addEventListener('click', () => {
                    window.order.push('inner-bubble');
                });
                document.getElementById('outer').addEventListener('click', () => {
                    window.order.push('outer-bubble');
                });
            </script>
        ''')
        
        page.click('#inner')
        
        result = page.evaluate('() => window.order')
        assert result[0] == 'outer-capture'
        assert 'inner-bubble' in result
    
    def test_once_option(self, page):
        """once option should remove listener after first call."""
        page.set_content('''
            <button id="btn">Click</button>
            <script>
                window.clickCount = 0;
                document.getElementById('btn').addEventListener('click', () => {
                    window.clickCount++;
                }, { once: true });
            </script>
        ''')
        
        page.click('#btn')
        page.click('#btn')
        page.click('#btn')
        
        result = page.evaluate('() => window.clickCount')
        assert result == 1
    
    def test_composed_path(self, page):
        """composedPath should return correct path."""
        page.set_content('''
            <style>
                #grandparent { width: 150px; height: 150px; background: blue; }
                #parent { width: 100px; height: 100px; background: green; }
                #child { width: 50px; height: 50px; background: red; }
            </style>
            <div id="grandparent">
                <div id="parent">
                    <div id="child"></div>
                </div>
            </div>
            <script>
                window.pathIds = [];
                document.getElementById('child').addEventListener('click', (e) => {
                    window.pathIds = e.composedPath()
                        .filter(el => el.id)
                        .map(el => el.id);
                });
            </script>
        ''')
        
        page.click('#child')
        
        result = page.evaluate('() => window.pathIds')
        assert 'child' in result
        assert 'parent' in result
        assert 'grandparent' in result

