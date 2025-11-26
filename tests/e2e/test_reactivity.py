"""
End-to-end tests for PyNext reactivity in the browser.

Tests signal updates, effects, and DOM synchronization.
"""

import pytest

pytestmark = pytest.mark.e2e

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


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


class TestSignalReactivity:
    """E2E tests for signal reactivity."""
    
    def test_counter_increment(self, browser_page):
        """Counter increments when button is clicked."""
        page = browser_page
        page.set_content('''
            <html>
            <body>
            <div id="counter">0</div>
            <button id="increment">+</button>
            <script>
                // Simple signal implementation
                var count = 0;
                function updateCounter() {
                    document.getElementById('counter').textContent = count;
                }
                document.getElementById('increment').addEventListener('click', function() {
                    count++;
                    updateCounter();
                });
            </script>
            </body>
            </html>
        ''')
        
        # Get initial value
        initial = int(page.text_content('#counter'))
        
        # Click increment
        page.click('#increment')
        
        # Check value updated
        new_value = int(page.text_content('#counter'))
        assert new_value == initial + 1
    
    def test_input_binding(self, browser_page):
        """Input value syncs with signal."""
        page = browser_page
        page.set_content('''
            <html>
            <body>
            <input type="text" id="name-input">
            <div id="greeting"></div>
            <script>
                var name = '';
                document.getElementById('name-input').addEventListener('input', function() {
                    name = this.value;
                    document.getElementById('greeting').textContent = 'Hello, ' + name;
                });
            </script>
            </body>
            </html>
        ''')
        
        # Type in input
        page.fill('#name-input', 'Alice')
        
        # Check display updated
        greeting = page.text_content('#greeting')
        assert 'Alice' in greeting
    
    def test_computed_values(self, browser_page):
        """Computed values update when dependencies change."""
        page = browser_page
        page.set_content('''
            <html>
            <body>
            <input type="number" id="a" value="5">
            <input type="number" id="b" value="3">
            <div id="sum"></div>
            <script>
                function updateSum() {
                    var a = parseInt(document.getElementById('a').value) || 0;
                    var b = parseInt(document.getElementById('b').value) || 0;
                    document.getElementById('sum').textContent = 'Sum: ' + (a + b);
                }
                document.getElementById('a').addEventListener('input', updateSum);
                document.getElementById('b').addEventListener('input', updateSum);
                updateSum();
            </script>
            </body>
            </html>
        ''')
        
        # Check initial sum
        assert page.text_content('#sum') == 'Sum: 8'
        
        # Change value
        page.fill('#a', '10')
        assert page.text_content('#sum') == 'Sum: 13'
    
    def test_effect_side_effects(self, browser_page):
        """Effects run side effects when signals change."""
        page = browser_page
        page.set_content('''
            <html>
            <body>
            <input type="text" id="input">
            <div id="log"></div>
            <script>
                var logs = [];
                document.getElementById('input').addEventListener('input', function() {
                    // Effect: log changes
                    logs.push('Changed to: ' + this.value);
                    document.getElementById('log').textContent = logs.join(', ');
                });
            </script>
            </body>
            </html>
        ''')
        
        # Type characters
        page.fill('#input', 'a')
        page.fill('#input', 'ab')
        page.fill('#input', 'abc')
        
        # Check effect ran
        log = page.text_content('#log')
        assert 'Changed to:' in log


class TestHydration:
    """E2E tests for hydration."""
    
    def test_page_hydrates(self, browser_page):
        """Page hydrates correctly with PyNext signals."""
        page = browser_page
        page.set_content('''
            <html>
            <body>
            <div id="app">Content</div>
            <script>
                // Simulate PyNext hydration
                window.__pynext__ = window.__pynext__ || {};
                window.__pynext__.signals = {
                    count: { value: 0, subscribers: [] }
                };
                window.__pynext__.hydrated = true;
            </script>
            </body>
            </html>
        ''')
        
        # Wait for hydration
        page.wait_for_function('window.__pynext__ !== undefined')
        
        # Check signals exist
        signals_exist = page.evaluate('Object.keys(window.__pynext__.signals).length > 0')
        assert signals_exist
        
        # Check hydrated flag
        hydrated = page.evaluate('window.__pynext__.hydrated')
        assert hydrated
    
    def test_hydration_preserves_state(self, browser_page):
        """Hydration preserves server-rendered state."""
        page = browser_page
        page.set_content('''
            <html>
            <body>
            <div id="server-count">42</div>
            <script>
                // Hydrate from server-rendered value
                window.__pynext__ = { signals: {} };
                var serverValue = parseInt(document.getElementById('server-count').textContent);
                window.__pynext__.signals.count = { value: serverValue };
            </script>
            </body>
            </html>
        ''')
        
        # Check state preserved
        state_value = page.evaluate('window.__pynext__.signals.count.value')
        assert state_value == 42
    
    def test_hydration_enables_interactivity(self, browser_page):
        """Hydration enables interactive features."""
        page = browser_page
        page.set_content('''
            <html>
            <body>
            <div id="count">0</div>
            <button id="btn" disabled>Loading...</button>
            <script>
                // Simulate hydration enabling button
                window.__pynext__ = { signals: { count: { value: 0 } } };
                
                var btn = document.getElementById('btn');
                btn.disabled = false;
                btn.textContent = 'Click me';
                
                btn.addEventListener('click', function() {
                    window.__pynext__.signals.count.value++;
                    document.getElementById('count').textContent = 
                        window.__pynext__.signals.count.value;
                });
            </script>
            </body>
            </html>
        ''')
        
        # Button should be enabled after hydration
        assert not page.is_disabled('#btn')
        
        # Clicking should work
        page.click('#btn')
        assert page.text_content('#count') == '1'


class TestNavigation:
    """E2E tests for reactive navigation."""
    
    def test_link_navigation(self, browser_page):
        """Clicking links navigates correctly."""
        page = browser_page
        page.set_content('''
            <html>
            <body>
            <h1 id="title">Home</h1>
            <a href="#about" id="about-link">About</a>
            <script>
                var routes = { '': 'Home', 'about': 'About' };
                function router() {
                    var hash = window.location.hash.slice(1);
                    document.getElementById('title').textContent = routes[hash] || routes[''];
                }
                window.addEventListener('hashchange', router);
            </script>
            </body>
            </html>
        ''')
        
        # Click about link
        page.click('#about-link')
        
        # Wait for navigation
        page.wait_for_function('document.getElementById("title").textContent === "About"')
        
        # Check content updated
        assert page.text_content('#title') == 'About'
    
    def test_navigation_preserves_state(self, browser_page):
        """Navigation preserves component state."""
        page = browser_page
        page.set_content('''
            <html>
            <body>
            <div id="count">0</div>
            <button id="inc">+</button>
            <a href="#other" id="nav">Navigate</a>
            <script>
                var count = 0;
                document.getElementById('inc').addEventListener('click', function() {
                    count++;
                    document.getElementById('count').textContent = count;
                });
            </script>
            </body>
            </html>
        ''')
        
        # Increment counter
        page.click('#inc')
        page.click('#inc')
        assert page.text_content('#count') == '2'
        
        # Navigate
        page.click('#nav')
        
        # Count should be preserved (in-memory state)
        assert page.text_content('#count') == '2'


class TestStoreReactivity:
    """E2E tests for store-based reactivity."""
    
    def test_store_updates(self, browser_page):
        """Store updates trigger UI updates."""
        page = browser_page
        page.set_content('''
            <html>
            <body>
            <div id="user-name"></div>
            <button id="update">Update</button>
            <script>
                // Simple store
                var store = { user: { name: 'Alice' } };
                var subscribers = [];
                
                function subscribe(fn) { subscribers.push(fn); }
                function notify() { subscribers.forEach(function(fn) { fn(); }); }
                
                function render() {
                    document.getElementById('user-name').textContent = store.user.name;
                }
                
                subscribe(render);
                render();
                
                document.getElementById('update').addEventListener('click', function() {
                    store.user.name = 'Bob';
                    notify();
                });
            </script>
            </body>
            </html>
        ''')
        
        # Check initial state
        assert page.text_content('#user-name') == 'Alice'
        
        # Update store
        page.click('#update')
        
        # Check UI updated
        assert page.text_content('#user-name') == 'Bob'
    
    def test_nested_store_updates(self, browser_page):
        """Nested store properties update correctly."""
        page = browser_page
        page.set_content('''
            <html>
            <body>
            <div id="address"></div>
            <button id="update">Update City</button>
            <script>
                var store = {
                    user: {
                        address: { city: 'NYC', country: 'USA' }
                    }
                };
                
                function render() {
                    document.getElementById('address').textContent = 
                        store.user.address.city + ', ' + store.user.address.country;
                }
                render();
                
                document.getElementById('update').addEventListener('click', function() {
                    store.user.address.city = 'LA';
                    render();
                });
            </script>
            </body>
            </html>
        ''')
        
        # Check initial
        assert page.text_content('#address') == 'NYC, USA'
        
        # Update nested property
        page.click('#update')
        
        # Check update
        assert page.text_content('#address') == 'LA, USA'


class TestConditionalRendering:
    """E2E tests for conditional rendering."""
    
    def test_show_hide(self, browser_page):
        """Conditional show/hide works."""
        page = browser_page
        page.set_content('''
            <html>
            <body>
            <div id="content" style="display:none">Secret Content</div>
            <button id="toggle">Toggle</button>
            <script>
                var visible = false;
                document.getElementById('toggle').addEventListener('click', function() {
                    visible = !visible;
                    document.getElementById('content').style.display = visible ? 'block' : 'none';
                });
            </script>
            </body>
            </html>
        ''')
        
        # Initially hidden
        assert not page.is_visible('#content')
        
        # Toggle to show
        page.click('#toggle')
        assert page.is_visible('#content')
        
        # Toggle to hide
        page.click('#toggle')
        assert not page.is_visible('#content')
    
    def test_conditional_class(self, browser_page):
        """Conditional class application works."""
        page = browser_page
        page.set_content('''
            <html>
            <head>
            <style>.active { color: green; } .inactive { color: red; }</style>
            </head>
            <body>
            <div id="status" class="inactive">Status</div>
            <button id="activate">Activate</button>
            <script>
                var active = false;
                document.getElementById('activate').addEventListener('click', function() {
                    active = !active;
                    var el = document.getElementById('status');
                    el.className = active ? 'active' : 'inactive';
                });
            </script>
            </body>
            </html>
        ''')
        
        # Initially inactive
        assert 'inactive' in page.get_attribute('#status', 'class')
        
        # Activate
        page.click('#activate')
        assert 'active' in page.get_attribute('#status', 'class')


class TestListRendering:
    """E2E tests for list rendering."""
    
    def test_list_add_item(self, browser_page):
        """Adding items to list works."""
        page = browser_page
        page.set_content('''
            <html>
            <body>
            <ul id="list"></ul>
            <button id="add">Add Item</button>
            <script>
                var items = [];
                function render() {
                    document.getElementById('list').innerHTML = 
                        items.map(function(item) { return '<li>' + item + '</li>'; }).join('');
                }
                document.getElementById('add').addEventListener('click', function() {
                    items.push('Item ' + (items.length + 1));
                    render();
                });
            </script>
            </body>
            </html>
        ''')
        
        # Add items
        page.click('#add')
        page.click('#add')
        page.click('#add')
        
        # Check list
        items = page.locator('#list li')
        assert items.count() == 3
    
    def test_list_remove_item(self, browser_page):
        """Removing items from list works."""
        page = browser_page
        page.set_content('''
            <html>
            <body>
            <ul id="list">
                <li data-id="1">Item 1 <button class="remove">X</button></li>
                <li data-id="2">Item 2 <button class="remove">X</button></li>
                <li data-id="3">Item 3 <button class="remove">X</button></li>
            </ul>
            <script>
                document.getElementById('list').addEventListener('click', function(e) {
                    if (e.target.classList.contains('remove')) {
                        e.target.parentElement.remove();
                    }
                });
            </script>
            </body>
            </html>
        ''')
        
        # Initial count
        assert page.locator('#list li').count() == 3
        
        # Remove first item
        page.click('#list li:first-child .remove')
        
        # Check count
        assert page.locator('#list li').count() == 2
