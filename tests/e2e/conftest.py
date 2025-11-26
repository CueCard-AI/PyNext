"""
E2E Test Configuration and Fixtures.

Provides Playwright browser fixtures and test server management.
"""

import pytest
import subprocess
import time
import socket
import os
import sys

# Check if playwright is available
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


def is_port_in_use(port: int) -> bool:
    """Check if a port is in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


@pytest.fixture(scope="session")
def example_app_url():
    """URL of the test server."""
    return "http://localhost:3333"


@pytest.fixture(scope="session")
def test_server(example_app_url):
    """
    Start a PyNext test server for E2E tests.
    
    The server runs the example app on port 3333.
    """
    port = 3333
    
    # Check if server is already running
    if is_port_in_use(port):
        print(f"Server already running on port {port}")
        yield example_app_url
        return
    
    # Start the server
    example_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'example')
    
    server_process = subprocess.Popen(
        [sys.executable, '-m', 'pynext', 'dev', '--port', str(port)],
        cwd=example_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, 'PYNEXT_ENV': 'test'}
    )
    
    # Wait for server to start
    max_wait = 10
    start_time = time.time()
    while time.time() - start_time < max_wait:
        if is_port_in_use(port):
            break
        time.sleep(0.5)
    else:
        server_process.kill()
        pytest.skip("Could not start test server")
    
    yield example_app_url
    
    # Cleanup
    server_process.terminate()
    try:
        server_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        server_process.kill()


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


@pytest.fixture(scope="function")
def page(browser_page, test_server):
    """
    Provide a page with access to the test server.
    
    This fixture combines browser_page and test_server.
    """
    return browser_page

