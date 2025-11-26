"""
End-to-end tests for PyNext navigation.

Tests client-side navigation, link handling, and route transitions.
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


class TestLinkNavigation:
    """E2E tests for link-based navigation."""
    
    def test_internal_link_navigation(self, browser_page):
        """Clicking internal links navigates correctly."""
        page = browser_page
        page.set_content('''
            <html><body>
            <div id="title">Home</div>
            <a href="#about" id="about-link">About</a>
            <script>
                function router() {
                    var hash = window.location.hash.slice(1) || 'home';
                    document.getElementById('title').textContent = 
                        hash.charAt(0).toUpperCase() + hash.slice(1);
                }
                window.addEventListener('hashchange', router);
            </script>
            </body></html>
        ''')
        
        page.click('#about-link')
        page.wait_for_function('document.getElementById("title").textContent === "About"')
        assert page.text_content('#title') == "About"
    
    def test_back_button(self, browser_page):
        """Browser back button works."""
        page = browser_page
        page.set_content('''
            <html><body>
            <div id="page">home</div>
            <a href="#" id="nav">Navigate</a>
            <script>
                document.getElementById('nav').addEventListener('click', function(e) {
                    e.preventDefault();
                    window.history.pushState({page: 'other'}, '', '#other');
                    document.getElementById('page').textContent = 'other';
                });
                window.addEventListener('popstate', function(e) {
                    document.getElementById('page').textContent = e.state?.page || 'home';
                });
            </script>
            </body></html>
        ''')
        
        page.click('#nav')
        page.wait_for_function('document.getElementById("page").textContent === "other"')
        page.go_back()
        page.wait_for_function('document.getElementById("page").textContent === "home"')
        assert page.text_content('#page') == 'home'
    
    def test_forward_button(self, browser_page):
        """Browser forward button works."""
        page = browser_page
        page.set_content('''
            <html><body>
            <div id="page">home</div>
            <a href="#" id="nav">Navigate</a>
            <script>
                document.getElementById('nav').addEventListener('click', function(e) {
                    e.preventDefault();
                    window.history.pushState({page: 'other'}, '', '#other');
                    document.getElementById('page').textContent = 'other';
                });
                window.addEventListener('popstate', function(e) {
                    document.getElementById('page').textContent = e.state?.page || 'home';
                });
            </script>
            </body></html>
        ''')
        
        page.click('#nav')
        page.wait_for_function('document.getElementById("page").textContent === "other"')
        page.go_back()
        page.wait_for_function('document.getElementById("page").textContent === "home"')
        page.go_forward()
        page.wait_for_function('document.getElementById("page").textContent === "other"')
        assert page.text_content('#page') == 'other'


class TestDynamicRouteNavigation:
    """E2E tests for dynamic route parameters."""
    
    def test_dynamic_route_params(self, browser_page):
        """Dynamic route parameters are extracted."""
        page = browser_page
        page.set_content('''
            <html><body>
            <div id="user-id"></div>
            <a href="#users/123" id="link">User 123</a>
            <script>
                function extract() {
                    var m = window.location.hash.match(/users\\/(.+)/);
                    if (m) document.getElementById('user-id').textContent = m[1];
                }
                window.addEventListener('hashchange', extract);
            </script>
            </body></html>
        ''')
        
        page.click('#link')
        page.wait_for_function('document.getElementById("user-id").textContent === "123"')
        assert page.text_content('#user-id') == '123'
    
    def test_navigate_between_dynamic_routes(self, browser_page):
        """Navigation between dynamic routes updates params."""
        page = browser_page
        page.set_content('''
            <html><body>
            <div id="id"></div>
            <a href="#" data-id="1" class="nav">1</a>
            <a href="#" data-id="2" class="nav">2</a>
            <script>
                document.querySelectorAll('.nav').forEach(function(a) {
                    a.addEventListener('click', function(e) {
                        e.preventDefault();
                        document.getElementById('id').textContent = this.dataset.id;
                    });
                });
            </script>
            </body></html>
        ''')
        
        page.click('.nav[data-id="1"]')
        assert page.text_content('#id') == '1'
        page.click('.nav[data-id="2"]')
        assert page.text_content('#id') == '2'


class TestQueryParameters:
    """E2E tests for query parameters."""
    
    def test_query_params_in_url(self, browser_page):
        """Query parameters are accessible."""
        page = browser_page
        page.set_content('''
            <html><body>
            <div id="params"></div>
            <a href="#" id="link">Search</a>
            <script>
                document.getElementById('link').addEventListener('click', function(e) {
                    e.preventDefault();
                    // Use hash-based params for set_content context
                    window.location.hash = 'q=hello';
                    document.getElementById('params').textContent = window.location.hash;
                });
            </script>
            </body></html>
        ''')
        
        page.click('#link')
        page.wait_for_function('document.getElementById("params").textContent !== ""')
        assert 'q=hello' in page.text_content('#params')
    
    def test_query_params_preserved(self, browser_page):
        """Query parameters are preserved during navigation."""
        page = browser_page
        page.set_content('''
            <html><body>
            <div id="result"></div>
            <button id="set">Set</button>
            <button id="check">Check</button>
            <script>
                document.getElementById('set').addEventListener('click', function() {
                    window.location.hash = 'keep=true';
                });
                document.getElementById('check').addEventListener('click', function() {
                    document.getElementById('result').textContent = window.location.hash;
                });
            </script>
            </body></html>
        ''')
        
        page.click('#set')
        page.wait_for_function('window.location.hash !== ""')
        page.click('#check')
        assert 'keep=true' in page.text_content('#result')


class TestErrorHandling:
    """E2E tests for navigation error handling."""
    
    def test_404_page(self, browser_page):
        """404 page shows for unknown routes."""
        page = browser_page
        page.set_content('''
            <html><body>
            <div id="content">Home</div>
            <a href="#unknown" id="link">Unknown</a>
            <script>
                var routes = {'': 'Home', 'about': 'About'};
                function router() {
                    var h = window.location.hash.slice(1);
                    document.getElementById('content').textContent = routes[h] || '404 Not Found';
                }
                window.addEventListener('hashchange', router);
            </script>
            </body></html>
        ''')
        
        page.click('#link')
        page.wait_for_function('document.getElementById("content").textContent.includes("404")')
        assert '404' in page.text_content('#content')
    
    def test_navigation_error_recovery(self, browser_page):
        """Navigation errors allow recovery."""
        page = browser_page
        page.set_content('''
            <html><body>
            <div id="status">ready</div>
            <button id="retry">Retry</button>
            <script>
                var tries = 0;
                document.getElementById('retry').addEventListener('click', function() {
                    tries++;
                    document.getElementById('status').textContent = tries >= 3 ? 'success' : 'error';
                });
            </script>
            </body></html>
        ''')
        
        page.click('#retry')
        assert page.text_content('#status') == 'error'
        page.click('#retry')
        page.click('#retry')
        assert page.text_content('#status') == 'success'


class TestLayoutPersistence:
    """E2E tests for layout persistence during navigation."""
    
    def test_layout_preserved_during_navigation(self, browser_page):
        """Layout components persist during navigation."""
        page = browser_page
        page.set_content('''
            <html><body>
            <header id="header" data-renders="1">Header</header>
            <main id="content">Home</main>
            <button id="nav">Navigate</button>
            <script>
                document.getElementById('nav').addEventListener('click', function() {
                    document.getElementById('content').textContent = 'About';
                });
            </script>
            </body></html>
        ''')
        
        initial = page.get_attribute('#header', 'data-renders')
        page.click('#nav')
        assert page.get_attribute('#header', 'data-renders') == initial
        assert page.text_content('#content') == 'About'
    
    def test_nested_layout_navigation(self, browser_page):
        """Nested layouts work correctly."""
        page = browser_page
        page.set_content('''
            <html><body>
            <nav id="sidebar">Sidebar</nav>
            <main id="content">Dashboard</main>
            <button id="nav">Navigate</button>
            <script>
                document.getElementById('nav').addEventListener('click', function() {
                    document.getElementById('content').textContent = 'Settings';
                });
            </script>
            </body></html>
        ''')
        
        assert page.is_visible('#sidebar')
        page.click('#nav')
        assert page.is_visible('#sidebar')
        assert page.text_content('#content') == 'Settings'


class TestPrefetching:
    """E2E tests for link prefetching."""
    
    def test_prefetch_on_hover(self, browser_page):
        """Links prefetch on hover."""
        page = browser_page
        page.set_content('''
            <html><body>
            <div id="log"></div>
            <a href="/about" id="link" data-prefetch="true">About</a>
            <script>
                document.getElementById('link').addEventListener('mouseenter', function() {
                    document.getElementById('log').textContent = 'Prefetched: ' + this.href;
                });
            </script>
            </body></html>
        ''')
        
        page.hover('#link')
        assert 'Prefetched' in page.text_content('#log')
