"""
Integration tests for PyNext layouts.

Tests nested layouts, layout resolution, and layout rendering.
"""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from pynext.server.app import create_app


class TestLayoutRendering:
    """Tests for layout rendering in pages."""
    
    @pytest.fixture
    def app_with_layouts(self, temp_pages_dir: Path):
        """Create app with layouts."""
        # Root layout
        (temp_pages_dir / "layout.py").write_text('''
from pynext import layout, div

@layout
def root_layout(children):
    return div(class_="root-layout")[
        div(class_="header")["Header"],
        div(class_="main")[children],
        div(class_="footer")["Footer"]
    ]
''')
        
        # Index page
        (temp_pages_dir / "index.py").write_text('''
from pynext import page, div, h1

@page(title="Home")
def index():
    return div()[h1()["Welcome Home"]]
''')
        
        # Dashboard section with nested layout
        dashboard_dir = temp_pages_dir / "dashboard"
        dashboard_dir.mkdir()
        
        (dashboard_dir / "layout.py").write_text('''
from pynext import layout, div

@layout
def dashboard_layout(children):
    return div(class_="dashboard-layout")[
        div(class_="sidebar")["Sidebar"],
        div(class_="content")[children]
    ]
''')
        
        (dashboard_dir / "index.py").write_text('''
from pynext import page, div, h1

@page(title="Dashboard")
def dashboard():
    return div()[h1()["Dashboard"]]
''')
        
        (dashboard_dir / "settings.py").write_text('''
from pynext import page, div, h1

@page(title="Settings")
def settings():
    return div()[h1()["Settings"]]
''')
        
        return create_app(
            pages_dir=str(temp_pages_dir),
            static_dir=str(temp_pages_dir.parent / "public"),
            debug=True,
        )
    
    @pytest.fixture
    def client_with_layouts(self, app_with_layouts):
        """Create test client with layouts."""
        return TestClient(app_with_layouts.app)
    
    def test_root_layout_applied(self, client_with_layouts):
        """Root layout is applied to index page."""
        response = client_with_layouts.get("/")
        
        assert response.status_code == 200
        assert "root-layout" in response.text
        assert "Header" in response.text
        assert "Footer" in response.text
        assert "Welcome Home" in response.text
    
    def test_nested_layout_applied(self, client_with_layouts):
        """Nested layout is applied to dashboard pages."""
        response = client_with_layouts.get("/dashboard")
        
        assert response.status_code == 200
        # Both layouts should be applied
        assert "root-layout" in response.text
        assert "dashboard-layout" in response.text
        assert "Sidebar" in response.text
        assert "Dashboard" in response.text
    
    def test_layout_order(self, client_with_layouts):
        """Layouts are applied in correct order (outer to inner)."""
        response = client_with_layouts.get("/dashboard/settings")
        
        assert response.status_code == 200
        
        # Root layout should wrap dashboard layout
        text = response.text
        root_pos = text.find("root-layout")
        dashboard_pos = text.find("dashboard-layout")
        
        assert root_pos < dashboard_pos  # Root comes before dashboard
    
    def test_page_without_nested_layout(self, client_with_layouts):
        """Page outside dashboard only gets root layout."""
        response = client_with_layouts.get("/")
        
        assert response.status_code == 200
        assert "root-layout" in response.text
        assert "dashboard-layout" not in response.text


class TestLayoutWithSpecialFiles:
    """Tests for layouts with loading/error components."""
    
    @pytest.fixture
    def app_with_special_files(self, temp_pages_dir: Path):
        """Create app with layouts and special files."""
        # Root layout
        (temp_pages_dir / "layout.py").write_text('''
from pynext import layout, div

@layout
def root_layout(children):
    return div(class_="root")[children]
''')
        
        # Loading component
        (temp_pages_dir / "loading.py").write_text('''
from pynext import loading, div

@loading
def global_loading():
    return div(class_="loading-spinner")["Loading..."]
''')
        
        # Error component
        (temp_pages_dir / "error.py").write_text('''
from pynext import error, div, h1, button

@error
def global_error(error, reset):
    return div(class_="error-boundary")[
        h1()["Error"],
        div()[str(error)]
    ]
''')
        
        # Not found component
        (temp_pages_dir / "not-found.py").write_text('''
from pynext import not_found, div, h1

@not_found
def custom_404():
    return div(class_="custom-404")[
        h1()["Page Not Found"]
    ]
''')
        
        # Index page
        (temp_pages_dir / "index.py").write_text('''
from pynext import page, div

@page
def index():
    return div()["Home"]
''')
        
        return create_app(
            pages_dir=str(temp_pages_dir),
            static_dir=str(temp_pages_dir.parent / "public"),
            debug=True,
        )
    
    @pytest.fixture
    def client_special(self, app_with_special_files):
        return TestClient(app_with_special_files.app)
    
    def test_custom_404_page(self, client_special):
        """Custom 404 page is used."""
        response = client_special.get("/nonexistent")
        
        assert response.status_code == 404
        assert "custom-404" in response.text
        assert "Page Not Found" in response.text


class TestLayoutMetadata:
    """Tests for metadata in layouts."""
    
    @pytest.fixture
    def app_with_metadata(self, temp_pages_dir: Path):
        """Create app with metadata."""
        (temp_pages_dir / "index.py").write_text('''
from pynext import page, div, Metadata

@page(metadata=Metadata(
    title="My Site - Home",
    description="Welcome to my site",
))
def index():
    return div()["Home"]
''')
        
        (temp_pages_dir / "about.py").write_text('''
from pynext import page, div, Metadata, OpenGraph

@page(metadata=Metadata(
    title="About Us",
    description="Learn about us",
    openGraph=OpenGraph(
        title="About - My Site",
        image="/og-about.png"
    )
))
def about():
    return div()["About"]
''')
        
        return create_app(
            pages_dir=str(temp_pages_dir),
            static_dir=str(temp_pages_dir.parent / "public"),
            debug=True,
        )
    
    @pytest.fixture
    def client_meta(self, app_with_metadata):
        return TestClient(app_with_metadata.app)
    
    def test_page_title(self, client_meta):
        """Page title is set from metadata."""
        response = client_meta.get("/")
        
        assert response.status_code == 200
        assert "<title>My Site - Home</title>" in response.text
    
    def test_page_description(self, client_meta):
        """Page description meta tag is set."""
        response = client_meta.get("/")
        
        assert response.status_code == 200
        assert 'name="description"' in response.text
        assert "Welcome to my site" in response.text
    
    def test_opengraph_meta(self, client_meta):
        """OpenGraph meta tags are set."""
        response = client_meta.get("/about")
        
        assert response.status_code == 200
        assert 'property="og:title"' in response.text
        assert 'property="og:image"' in response.text

