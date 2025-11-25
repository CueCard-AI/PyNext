"""
PyNext Test Configuration and Fixtures

Provides shared fixtures for unit, integration, and E2E tests.
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

# Add pynext to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pynext.server.app import PyNextApp, create_app
from pynext.core.signals import Signal, Computed, Effect, Store, batch
from pynext.core.component import component, page, layout, loading, error, not_found
from pynext.core.html import div, span, button, h1, p, ul, li, form, input_, a
from pynext.router.file_router import FileRouter


# =============================================================================
# Test App Fixtures
# =============================================================================

@pytest.fixture
def temp_pages_dir() -> Generator[Path, None, None]:
    """Create a temporary pages directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pages_dir = Path(tmpdir) / "pages"
        pages_dir.mkdir()
        yield pages_dir


@pytest.fixture
def temp_project_dir() -> Generator[Path, None, None]:
    """Create a complete temporary project directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        
        # Create directory structure
        (project_dir / "pages").mkdir()
        (project_dir / "pages" / "api").mkdir()
        (project_dir / "public").mkdir()
        (project_dir / "components").mkdir()
        
        yield project_dir


@pytest.fixture
def sample_pages(temp_pages_dir: Path) -> Path:
    """Create sample page files for testing routing."""
    # Index page
    (temp_pages_dir / "index.py").write_text('''
from pynext import page, div, h1

@page(title="Home")
def index():
    return div()[h1()["Welcome"]]
''')
    
    # About page
    (temp_pages_dir / "about.py").write_text('''
from pynext import page, div, h1

@page(title="About")
def about():
    return div()[h1()["About Us"]]
''')
    
    # Dynamic route
    users_dir = temp_pages_dir / "users"
    users_dir.mkdir()
    
    (users_dir / "index.py").write_text('''
from pynext import page, div, h1

@page(title="Users")
def users():
    return div()[h1()["All Users"]]
''')
    
    (users_dir / "[id].py").write_text('''
from pynext import page, div, h1
from pynext.router import get_params

@page(title="User Profile")
def user_profile():
    params = get_params()
    return div()[h1()[f"User {params.get('id')}"]]
''')
    
    # API route
    api_dir = temp_pages_dir / "api"
    api_dir.mkdir()
    
    health_dir = api_dir / "health"
    health_dir.mkdir()
    
    (health_dir / "route.py").write_text('''
from pynext import api_route

@api_route
async def GET(request):
    return {"status": "healthy"}
''')
    
    return temp_pages_dir


@pytest.fixture
def app(sample_pages: Path) -> PyNextApp:
    """Create a PyNextApp with sample pages."""
    return create_app(
        pages_dir=str(sample_pages),
        static_dir=str(sample_pages.parent / "public"),
        debug=True,
    )


@pytest.fixture
def client(app: PyNextApp) -> TestClient:
    """Create a synchronous test client."""
    return TestClient(app.app)


@pytest.fixture
async def async_client(app: PyNextApp) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    transport = ASGITransport(app=app.app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# =============================================================================
# Router Fixtures
# =============================================================================

@pytest.fixture
def router(sample_pages: Path) -> FileRouter:
    """Create a FileRouter with sample pages."""
    router = FileRouter(str(sample_pages))
    router.scan()
    return router


@pytest.fixture
def empty_router(temp_pages_dir: Path) -> FileRouter:
    """Create an empty FileRouter."""
    return FileRouter(str(temp_pages_dir))


# =============================================================================
# Signal Fixtures
# =============================================================================

@pytest.fixture
def signal() -> Signal[int]:
    """Create a test signal."""
    return Signal(0, name="test_signal")


@pytest.fixture
def string_signal() -> Signal[str]:
    """Create a string signal."""
    return Signal("hello", name="string_signal")


@pytest.fixture
def list_signal() -> Signal[list]:
    """Create a list signal."""
    return Signal([], name="list_signal")


@pytest.fixture
def store() -> Store:
    """Create a test store."""
    return Store({
        "count": 0,
        "user": {
            "name": "Alice",
            "age": 30,
        },
        "items": [],
    }, name="test_store")


# =============================================================================
# Component Fixtures
# =============================================================================

@pytest.fixture
def simple_component():
    """Create a simple test component."""
    @component
    def TestComponent():
        return div(class_="test")["Hello World"]
    return TestComponent


@pytest.fixture
def reactive_component():
    """Create a component with signals."""
    @component
    def ReactiveComponent():
        count = Signal(0)
        return div()[
            span(class_="count")[count],
            button(onclick=lambda: count.update(lambda x: x + 1))["Increment"]
        ]
    return ReactiveComponent


@pytest.fixture
def page_component():
    """Create a test page component."""
    @page(title="Test Page")
    def test_page():
        return div()[h1()["Test Page"]]
    return test_page


@pytest.fixture
def layout_component():
    """Create a test layout component."""
    @layout
    def test_layout(children):
        return div(class_="layout")[
            div(class_="header")["Header"],
            div(class_="content")[children],
            div(class_="footer")["Footer"],
        ]
    return test_layout


# =============================================================================
# Mock Fixtures
# =============================================================================

@pytest.fixture
def mock_request():
    """Create a mock request object."""
    request = MagicMock()
    request.url.path = "/"
    request.query_params = {}
    request.path_params = {}
    request.headers = {}
    request.method = "GET"
    return request


# =============================================================================
# Benchmark Fixtures
# =============================================================================

@pytest.fixture
def large_route_set(temp_pages_dir: Path) -> Path:
    """Create a large set of routes for benchmarking."""
    # Create 100 static routes
    for i in range(100):
        (temp_pages_dir / f"page{i}.py").write_text(f'''
from pynext import page, div

@page
def page{i}():
    return div()["Page {i}"]
''')
    
    # Create 20 dynamic routes
    for i in range(20):
        dir_path = temp_pages_dir / f"section{i}"
        dir_path.mkdir()
        (dir_path / "[id].py").write_text(f'''
from pynext import page, div
from pynext.router import get_params

@page
def dynamic{i}():
    params = get_params()
    return div()[f"Section {i}: {{params.get('id')}}"]
''')
    
    return temp_pages_dir


# =============================================================================
# Helpers
# =============================================================================

def create_test_page(pages_dir: Path, name: str, content: str) -> Path:
    """Helper to create a test page file."""
    file_path = pages_dir / f"{name}.py"
    file_path.write_text(content)
    return file_path


def create_test_layout(pages_dir: Path, path: str = "") -> Path:
    """Helper to create a layout file."""
    if path:
        layout_dir = pages_dir / path
        layout_dir.mkdir(parents=True, exist_ok=True)
        file_path = layout_dir / "layout.py"
    else:
        file_path = pages_dir / "layout.py"
    
    file_path.write_text('''
from pynext import layout, div

@layout
def test_layout(children):
    return div(class_="layout")[children]
''')
    return file_path


# =============================================================================
# Event Loop Configuration
# =============================================================================

@pytest.fixture(scope="session")
def event_loop_policy():
    """Use default event loop policy."""
    return asyncio.DefaultEventLoopPolicy()

