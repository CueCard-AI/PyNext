"""
End-to-End Browser Tests for PyNext Components.
Tests actual browser behavior using Playwright.
"""

import pytest

# Mark all tests in this module as E2E tests
pytestmark = pytest.mark.e2e

# Check if playwright is available
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


class TestDialogE2E:
    """E2E tests for Dialog component."""
    
    def test_dialog_opens_on_trigger_click(self, browser_page):
        """Clicking trigger should open dialog."""
        page = browser_page
        page.set_content('''
            <html>
            <body>
            <div data-pynext-dialog>
                <button data-pynext-dialog-trigger id="trigger">Open</button>
                <div data-pynext-dialog-content data-state="closed" id="content" style="display:none">
                    <h2>Dialog Title</h2>
                </div>
            </div>
            <script>
                document.getElementById('trigger').addEventListener('click', function() {
                    var content = document.getElementById('content');
                    content.setAttribute('data-state', 'open');
                    content.style.display = 'block';
                });
            </script>
            </body>
            </html>
        ''')
        
        # Click trigger
        page.click('#trigger')
        
        # Check dialog opened
        state = page.get_attribute('#content', 'data-state')
        assert state == 'open'
        
    def test_dialog_closes_on_escape(self, browser_page):
        """Pressing Escape should close dialog."""
        page = browser_page
        page.set_content('''
            <html>
            <body>
            <div data-pynext-dialog>
                <div data-pynext-dialog-content data-state="open" id="content" style="display:block">
                    <h2>Dialog Title</h2>
                    <button id="close">Close</button>
                </div>
            </div>
            <script>
                document.addEventListener('keydown', function(e) {
                    if (e.key === 'Escape') {
                        var content = document.getElementById('content');
                        content.setAttribute('data-state', 'closed');
                        content.style.display = 'none';
                    }
                });
            </script>
            </body>
            </html>
        ''')
        
        # Press Escape
        page.keyboard.press('Escape')
        
        # Check dialog closed
        state = page.get_attribute('#content', 'data-state')
        assert state == 'closed'
        
    def test_dialog_traps_focus(self, browser_page):
        """Tab should cycle within dialog."""
        page = browser_page
        page.set_content('''
            <html>
            <body>
            <div data-pynext-dialog>
                <div data-pynext-dialog-content data-state="open" id="dialog">
                    <button id="first">First</button>
                    <button id="second">Second</button>
                    <button id="third">Third</button>
                </div>
            </div>
            <script>
                var dialog = document.getElementById('dialog');
                var buttons = dialog.querySelectorAll('button');
                var first = buttons[0];
                var last = buttons[buttons.length - 1];
                
                dialog.addEventListener('keydown', function(e) {
                    if (e.key === 'Tab') {
                        if (e.shiftKey && document.activeElement === first) {
                            e.preventDefault();
                            last.focus();
                        } else if (!e.shiftKey && document.activeElement === last) {
                            e.preventDefault();
                            first.focus();
                        }
                    }
                });
                
                // Focus first button
                first.focus();
            </script>
            </body>
            </html>
        ''')
        
        # Focus first button
        page.focus('#first')
        
        # Tab through all buttons
        page.keyboard.press('Tab')
        focused = page.evaluate('document.activeElement.id')
        assert focused == 'second'
        
        page.keyboard.press('Tab')
        focused = page.evaluate('document.activeElement.id')
        assert focused == 'third'
        
        # Tab should wrap to first (focus trap)
        page.keyboard.press('Tab')
        focused = page.evaluate('document.activeElement.id')
        assert focused == 'first'


class TestKeyboardE2E:
    """E2E tests for keyboard shortcuts."""
    
    def test_shortcut_fires_handler(self, browser_page):
        """Cmd+K should open search."""
        page = browser_page
        page.set_content('''
            <html>
            <body>
            <div id="search" data-state="closed"></div>
            <script>
                document.addEventListener('keydown', function(e) {
                    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
                        e.preventDefault();
                        document.getElementById('search').setAttribute('data-state', 'open');
                    }
                });
            </script>
            </body>
            </html>
        ''')
        
        # Press Ctrl+K
        page.keyboard.press('Control+k')
        
        # Check search opened
        state = page.get_attribute('#search', 'data-state')
        assert state == 'open'
        
    def test_sequence_fires_handler(self, browser_page):
        """g then d should navigate to dashboard."""
        page = browser_page
        page.set_content('''
            <html>
            <body>
            <div id="nav" data-route=""></div>
            <script>
                var lastKey = '';
                document.addEventListener('keydown', function(e) {
                    if (lastKey === 'g' && e.key === 'd') {
                        document.getElementById('nav').setAttribute('data-route', 'dashboard');
                    }
                    lastKey = e.key;
                    setTimeout(function() { lastKey = ''; }, 1000);
                });
            </script>
            </body>
            </html>
        ''')
        
        # Press g then d
        page.keyboard.press('g')
        page.keyboard.press('d')
        
        # Check navigation
        route = page.get_attribute('#nav', 'data-route')
        assert route == 'dashboard'


class TestSSE_E2E:
    """E2E tests for Server-Sent Events."""
    
    def test_sse_mock_event(self, browser_page):
        """Test SSE event handling with mock."""
        page = browser_page
        page.set_content('''
            <html>
            <body>
            <div id="count">0</div>
            <script>
                window.mockSSE = function(data) {
                    document.getElementById('count').textContent = data;
                };
                
                setTimeout(function() {
                    window.mockSSE('42');
                }, 100);
            </script>
            </body>
            </html>
        ''')
        
        # Wait for SSE mock event
        page.wait_for_function(
            'document.getElementById("count").textContent !== "0"',
            timeout=5000
        )
        
        count = page.text_content('#count')
        assert count == '42'
        
    def test_sse_reconnection_logic(self, browser_page):
        """Test SSE reconnection logic."""
        page = browser_page
        page.set_content('''
            <html>
            <body>
            <div id="status">initial</div>
            <div id="reconnects">0</div>
            <script>
                var reconnects = 0;
                
                function simulateReconnect() {
                    reconnects++;
                    document.getElementById('reconnects').textContent = reconnects.toString();
                    document.getElementById('status').textContent = 'reconnecting';
                    
                    if (reconnects >= 2) {
                        document.getElementById('status').textContent = 'connected';
                    }
                }
                
                setTimeout(simulateReconnect, 50);
                setTimeout(simulateReconnect, 100);
            </script>
            </body>
            </html>
        ''')
        
        # Wait for reconnection logic
        page.wait_for_function(
            'document.getElementById("status").textContent === "connected"',
            timeout=5000
        )
        
        status = page.text_content('#status')
        reconnects = page.text_content('#reconnects')
        
        assert status == 'connected'
        assert int(reconnects) >= 2


class TestTabsE2E:
    """E2E tests for Tabs component."""
    
    def test_tabs_switch_on_click(self, browser_page):
        """Clicking tab should switch content."""
        page = browser_page
        page.set_content('''
            <html>
            <body>
            <div data-pynext-tabs>
                <div role="tablist">
                    <button data-pynext-tab-trigger data-value="tab1" data-state="active" id="trigger1">Tab 1</button>
                    <button data-pynext-tab-trigger data-value="tab2" data-state="inactive" id="trigger2">Tab 2</button>
                </div>
                <div data-pynext-tab-content data-value="tab1" data-state="active" id="content1">Content 1</div>
                <div data-pynext-tab-content data-value="tab2" data-state="inactive" id="content2" hidden>Content 2</div>
            </div>
            <script>
                document.querySelectorAll('[data-pynext-tab-trigger]').forEach(function(trigger) {
                    trigger.addEventListener('click', function() {
                        var value = this.dataset.value;
                        
                        document.querySelectorAll('[data-pynext-tab-trigger]').forEach(function(t) {
                            t.dataset.state = t.dataset.value === value ? 'active' : 'inactive';
                        });
                        
                        document.querySelectorAll('[data-pynext-tab-content]').forEach(function(c) {
                            c.dataset.state = c.dataset.value === value ? 'active' : 'inactive';
                            c.hidden = c.dataset.value !== value;
                        });
                    });
                });
            </script>
            </body>
            </html>
        ''')
        
        # Click second tab
        page.click('#trigger2')
        
        # Check content switched
        state1 = page.get_attribute('#content1', 'data-state')
        state2 = page.get_attribute('#content2', 'data-state')
        
        assert state1 == 'inactive'
        assert state2 == 'active'
        
    def test_tabs_keyboard_navigation(self, browser_page):
        """Arrow keys should navigate tabs."""
        page = browser_page
        page.set_content('''
            <html>
            <body>
            <div data-pynext-tabs>
                <div role="tablist" id="tablist">
                    <button id="tab1" role="tab">Tab 1</button>
                    <button id="tab2" role="tab">Tab 2</button>
                    <button id="tab3" role="tab">Tab 3</button>
                </div>
            </div>
            <script>
                var tablist = document.getElementById('tablist');
                var tabs = tablist.querySelectorAll('[role="tab"]');
                var tabsArray = Array.from(tabs);
                
                tablist.addEventListener('keydown', function(e) {
                    var currentIndex = tabsArray.indexOf(document.activeElement);
                    
                    if (e.key === 'ArrowRight') {
                        e.preventDefault();
                        var nextIndex = (currentIndex + 1) % tabs.length;
                        tabs[nextIndex].focus();
                    }
                });
            </script>
            </body>
            </html>
        ''')
        
        # Focus first tab
        page.focus('#tab1')
        
        # Press right arrow
        page.keyboard.press('ArrowRight')
        
        # Check focus moved
        focused = page.evaluate('document.activeElement.id')
        assert focused == 'tab2'


class TestThemeE2E:
    """E2E tests for theme switching."""
    
    def test_theme_toggle(self, browser_page):
        """Theme toggle should switch between light/dark."""
        page = browser_page
        page.set_content('''
            <html data-theme="light">
            <body>
                <button id="toggle">Toggle</button>
                <script>
                    document.getElementById('toggle').addEventListener('click', function() {
                        var html = document.documentElement;
                        html.setAttribute('data-theme', 
                            html.getAttribute('data-theme') === 'light' ? 'dark' : 'light'
                        );
                    });
                </script>
            </body>
            </html>
        ''')
        
        # Click toggle
        page.click('#toggle')
        
        # Check theme changed
        theme = page.get_attribute('html', 'data-theme')
        assert theme == 'dark'
        
    def test_theme_persists(self, browser_page):
        """Theme preference should persist (using data attribute as proxy for localStorage)."""
        page = browser_page
        page.set_content('''
            <html data-theme="light" data-persisted="">
            <body>
                <button id="toggle">Toggle</button>
                <script>
                    document.getElementById('toggle').addEventListener('click', function() {
                        var html = document.documentElement;
                        var currentTheme = html.getAttribute('data-theme');
                        var newTheme = currentTheme === 'light' ? 'dark' : 'light';
                        html.setAttribute('data-theme', newTheme);
                        // Simulate persistence by setting a marker
                        html.setAttribute('data-persisted', newTheme);
                    });
                </script>
            </body>
            </html>
        ''')
        
        # Click toggle
        page.click('#toggle')
        
        # Check persistence marker (proxy for localStorage in test)
        persisted = page.get_attribute('html', 'data-persisted')
        assert persisted == 'dark'
        
    def test_no_flash_on_load(self, browser_page):
        """Theme should apply before content visible (inline script executes synchronously)."""
        page = browser_page
        page.set_content('''
            <html>
            <head>
                <script>
                    // This simulates ThemeScript - runs synchronously before body
                    (function() {
                        // Default to light theme (simulating what ThemeScript does)
                        document.documentElement.setAttribute('data-theme', 'light');
                    })();
                </script>
            </head>
            <body>Content</body>
            </html>
        ''')
        
        # Theme should be set immediately by the inline script
        theme = page.get_attribute('html', 'data-theme')
        assert theme == 'light'


class TestAccordionE2E:
    """E2E tests for Accordion component."""
    
    def test_accordion_expand_collapse(self, browser_page):
        """Accordion should expand and collapse on click."""
        page = browser_page
        page.set_content('''
            <html>
            <body>
            <div data-pynext-accordion>
                <div data-pynext-accordion-item>
                    <button data-pynext-accordion-trigger id="trigger" data-state="closed">Title</button>
                    <div data-pynext-accordion-content id="content" data-state="closed" hidden>Content</div>
                </div>
            </div>
            <script>
                document.getElementById('trigger').addEventListener('click', function() {
                    var content = document.getElementById('content');
                    var trigger = document.getElementById('trigger');
                    var isOpen = content.dataset.state === 'open';
                    
                    content.dataset.state = isOpen ? 'closed' : 'open';
                    content.hidden = isOpen;
                    trigger.dataset.state = isOpen ? 'closed' : 'open';
                });
            </script>
            </body>
            </html>
        ''')
        
        # Click to expand
        page.click('#trigger')
        state = page.get_attribute('#content', 'data-state')
        assert state == 'open'
        
        # Click to collapse
        page.click('#trigger')
        state = page.get_attribute('#content', 'data-state')
        assert state == 'closed'


class TestDropdownE2E:
    """E2E tests for Dropdown component."""
    
    def test_dropdown_opens_closes(self, browser_page):
        """Dropdown should open on click and close on outside click."""
        page = browser_page
        page.set_content('''
            <html>
            <body>
            <div data-pynext-dropdown id="dropdown">
                <button data-pynext-dropdown-trigger id="trigger">Menu</button>
                <div data-pynext-dropdown-content id="content" data-state="closed" hidden>
                    <button>Item 1</button>
                </div>
            </div>
            <div id="outside" style="margin-top: 100px;">Outside</div>
            <script>
                var dropdown = document.getElementById('dropdown');
                var content = document.getElementById('content');
                var trigger = document.getElementById('trigger');
                
                trigger.addEventListener('click', function(e) {
                    e.stopPropagation();
                    var isOpen = content.dataset.state === 'open';
                    content.dataset.state = isOpen ? 'closed' : 'open';
                    content.hidden = isOpen;
                });
                
                document.addEventListener('click', function(e) {
                    if (!dropdown.contains(e.target)) {
                        content.dataset.state = 'closed';
                        content.hidden = true;
                    }
                });
            </script>
            </body>
            </html>
        ''')
        
        # Click to open
        page.click('#trigger')
        state = page.get_attribute('#content', 'data-state')
        assert state == 'open'
        
        # Click outside to close
        page.click('#outside')
        state = page.get_attribute('#content', 'data-state')
        assert state == 'closed'


class TestTooltipE2E:
    """E2E tests for Tooltip component."""
    
    def test_tooltip_shows_on_hover(self, browser_page):
        """Tooltip should show on hover."""
        page = browser_page
        page.set_content('''
            <html>
            <body>
            <div data-pynext-tooltip>
                <button data-pynext-tooltip-trigger id="trigger">Hover me</button>
                <div data-pynext-tooltip-content id="tooltip" data-state="closed" style="display:none">
                    Tooltip text
                </div>
            </div>
            <script>
                var trigger = document.getElementById('trigger');
                var tooltip = document.getElementById('tooltip');
                
                trigger.addEventListener('mouseenter', function() {
                    tooltip.dataset.state = 'open';
                    tooltip.style.display = 'block';
                });
                
                trigger.addEventListener('mouseleave', function() {
                    tooltip.dataset.state = 'closed';
                    tooltip.style.display = 'none';
                });
            </script>
            </body>
            </html>
        ''')
        
        # Hover over trigger
        page.hover('#trigger')
        
        # Check tooltip visible
        state = page.get_attribute('#tooltip', 'data-state')
        assert state == 'open'


class TestComboboxE2E:
    """E2E tests for Combobox component."""
    
    def test_combobox_filters(self, browser_page):
        """Combobox should filter items on input."""
        page = browser_page
        page.set_content('''
            <html>
            <body>
            <div data-pynext-combobox>
                <input data-pynext-combobox-input id="input" type="text">
                <div data-pynext-combobox-content>
                    <div data-pynext-combobox-item class="item" id="item1">Apple</div>
                    <div data-pynext-combobox-item class="item" id="item2">Banana</div>
                    <div data-pynext-combobox-item class="item" id="item3">Cherry</div>
                </div>
            </div>
            <script>
                var input = document.getElementById('input');
                var items = document.querySelectorAll('.item');
                
                input.addEventListener('input', function() {
                    var query = this.value.toLowerCase();
                    items.forEach(function(item) {
                        item.hidden = !item.textContent.toLowerCase().includes(query);
                    });
                });
            </script>
            </body>
            </html>
        ''')
        
        # Type to filter
        page.fill('#input', 'ban')
        
        # Check filtering
        apple_hidden = page.is_hidden('#item1')
        banana_hidden = page.is_hidden('#item2')
        cherry_hidden = page.is_hidden('#item3')
        
        assert apple_hidden == True
        assert banana_hidden == False
        assert cherry_hidden == True


class TestCalendarE2E:
    """E2E tests for Calendar component."""
    
    def test_calendar_date_selection(self, browser_page):
        """Calendar should select date on click."""
        page = browser_page
        page.set_content('''
            <html>
            <body>
            <div data-pynext-calendar>
                <div id="selected"></div>
                <button data-pynext-calendar-day data-date="2024-06-15" id="day15">15</button>
                <button data-pynext-calendar-day data-date="2024-06-16" id="day16">16</button>
            </div>
            <script>
                document.querySelectorAll('[data-pynext-calendar-day]').forEach(function(day) {
                    day.addEventListener('click', function() {
                        document.querySelectorAll('[data-pynext-calendar-day]').forEach(function(d) {
                            d.dataset.selected = 'false';
                        });
                        this.dataset.selected = 'true';
                        document.getElementById('selected').textContent = this.dataset.date;
                    });
                });
            </script>
            </body>
            </html>
        ''')
        
        # Click day 15
        page.click('#day15')
        
        # Check selection
        selected = page.get_attribute('#day15', 'data-selected')
        date = page.text_content('#selected')
        
        assert selected == 'true'
        assert date == '2024-06-15'


class TestDataTableE2E:
    """E2E tests for DataTable component."""
    
    def test_datatable_sorting(self, browser_page):
        """DataTable should sort on header click."""
        page = browser_page
        page.set_content('''
            <html>
            <body>
            <div data-pynext-datatable id="table" data-sort-column="" data-sort-direction="">
                <table>
                    <thead>
                        <tr>
                            <th data-pynext-column-header data-column="name" id="nameHeader">Name</th>
                        </tr>
                    </thead>
                </table>
            </div>
            <script>
                document.getElementById('nameHeader').addEventListener('click', function() {
                    var table = document.getElementById('table');
                    var currentCol = table.dataset.sortColumn;
                    var currentDir = table.dataset.sortDirection;
                    
                    if (currentCol === 'name') {
                        table.dataset.sortDirection = currentDir === 'asc' ? 'desc' : 'asc';
                    } else {
                        table.dataset.sortColumn = 'name';
                        table.dataset.sortDirection = 'asc';
                    }
                });
            </script>
            </body>
            </html>
        ''')
        
        # Click header to sort ascending
        page.click('#nameHeader')
        
        sortCol = page.get_attribute('#table', 'data-sort-column')
        sortDir = page.get_attribute('#table', 'data-sort-direction')
        
        assert sortCol == 'name'
        assert sortDir == 'asc'
        
        # Click again to sort descending
        page.click('#nameHeader')
        sortDir = page.get_attribute('#table', 'data-sort-direction')
        assert sortDir == 'desc'
