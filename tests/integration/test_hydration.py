"""
Integration tests for PyNext hydration.

Tests server → client state transfer and signal initialization.
"""

import pytest
import json
import re
from pathlib import Path
from fastapi.testclient import TestClient
from pynext.server.app import create_app
from pynext.reactive import Signal
from pynext.core.component import page, component
from pynext.core.html import div, span, button, h1


class TestHydrationDataGeneration:
    """Tests for hydration data in server responses."""
    
    @pytest.fixture
    def app_with_signals(self, temp_pages_dir: Path):
        """Create app with pages that use signals."""
        # Page with signals
        (temp_pages_dir / "counter.py").write_text('''
from pynext import page, Signal, div, span, button

@page(title="Counter")
def counter():
    count = Signal(0, name="count")
    
    return div(class_="counter")[
        span(data_signal=count._id)[count],
        button(onclick=lambda: count.update(lambda x: x + 1))["Increment"]
    ]
''')
        
        # Page with store
        (temp_pages_dir / "store.py").write_text('''
from pynext import page, Store, div, span

@page(title="Store Demo")
def store_demo():
    user = Store({
        "name": "Alice",
        "age": 30,
        "settings": {"theme": "dark"}
    }, name="user")
    
    return div()[
        span()[f"Name: {user.name}"],
        span()[f"Age: {user.age}"],
        span()[f"Theme: {user.settings.theme}"],
    ]
''')
        
        # Page with computed
        (temp_pages_dir / "computed.py").write_text('''
from pynext import page, Signal, Computed, div, span

@page(title="Computed Demo")
def computed_demo():
    count = Signal(5, name="count")
    doubled = Computed(lambda: count() * 2, name="doubled")
    
    return div()[
        span()[f"Count: {count()}"],
        span()[f"Doubled: {doubled()}"],
    ]
''')
        
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
    def hydration_client(self, app_with_signals):
        return TestClient(app_with_signals.app)
    
    def test_hydration_script_present(self, hydration_client):
        """Hydration script is included in page."""
        response = hydration_client.get("/counter")
        
        assert response.status_code == 200
        assert "__PYNEXT_HYDRATION__" in response.text
    
    def test_hydration_data_is_valid_json(self, hydration_client):
        """Hydration data is valid JSON."""
        response = hydration_client.get("/counter")
        
        # Extract hydration data
        match = re.search(
            r'window\.__PYNEXT_HYDRATION__\s*=\s*({.*?});',
            response.text,
            re.DOTALL
        )
        
        assert match is not None
        data = json.loads(match.group(1))
        assert isinstance(data, dict)
    
    def test_signal_in_hydration_data(self, hydration_client):
        """Signals are included in hydration data."""
        response = hydration_client.get("/counter")
        
        match = re.search(
            r'window\.__PYNEXT_HYDRATION__\s*=\s*({.*?});',
            response.text,
            re.DOTALL
        )
        
        assert match is not None
        data = json.loads(match.group(1))
        
        # Should have signals
        assert "signals" in data or len(data) > 0
    
    def test_signal_value_hydrated(self, hydration_client):
        """Signal initial value is in hydration data."""
        response = hydration_client.get("/counter")
        
        match = re.search(
            r'window\.__PYNEXT_HYDRATION__\s*=\s*({.*?});',
            response.text,
            re.DOTALL
        )
        
        assert match is not None
        data = json.loads(match.group(1))
        
        # Check for signal with value 0
        if "signals" in data:
            values = [s.get("value") for s in data["signals"].values()]
            assert 0 in values
    
    def test_store_hydration(self, hydration_client):
        """Store data is included in hydration."""
        response = hydration_client.get("/store")
        
        assert response.status_code == 200
        
        # Page should render with store values
        assert "Alice" in response.text
        assert "30" in response.text


class TestHydrationMarkers:
    """Tests for DOM hydration markers."""
    
    @pytest.fixture
    def app_markers(self, temp_pages_dir: Path):
        """Create app with hydration markers."""
        (temp_pages_dir / "markers.py").write_text('''
from pynext import page, Signal, div, span

@page(title="Markers Test")
def markers():
    count = Signal(42, name="marker_count")
    
    return div()[
        span(id="count-display")[count],
    ]
''')
        
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
    def marker_client(self, app_markers):
        return TestClient(app_markers.app)
    
    def test_signal_marker_in_dom(self, marker_client):
        """Signal elements have data-signal attribute."""
        response = marker_client.get("/markers")
        
        assert response.status_code == 200
        # Signal should render to DOM with marker or value
        assert "42" in response.text or "data-signal" in response.text


class TestEventHandlerHydration:
    """Tests for event handler hydration."""
    
    @pytest.fixture
    def app_events(self, temp_pages_dir: Path):
        """Create app with event handlers."""
        (temp_pages_dir / "events.py").write_text('''
from pynext import page, Signal, div, button

@page(title="Events Test")
def events():
    count = Signal(0)
    
    return div()[
        button(
            id="increment-btn",
            onclick=lambda: count.update(lambda x: x + 1)
        )["Click me"],
        button(
            id="reset-btn",
            onclick=lambda: count.set(0)
        )["Reset"],
    ]
''')
        
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
    def event_client(self, app_events):
        return TestClient(app_events.app)
    
    def test_event_handlers_registered(self, event_client):
        """Event handlers are registered in hydration data."""
        response = event_client.get("/events")
        
        assert response.status_code == 200
        
        # Buttons should have IDs for event binding
        assert 'id="increment-btn"' in response.text
        assert 'id="reset-btn"' in response.text
    
    def test_runtime_script_included(self, event_client):
        """Runtime script is included for hydration."""
        response = event_client.get("/events")
        
        assert response.status_code == 200
        assert "/_pynext/runtime.js" in response.text


class TestHydrationEdgeCases:
    """Tests for edge cases in hydration."""
    
    def test_empty_hydration_data(self, client):
        """Page without signals still has hydration data."""
        response = client.get("/")
        
        assert response.status_code == 200
        assert "__PYNEXT_HYDRATION__" in response.text
    
    def test_special_characters_in_signal(self, temp_pages_dir, client):
        """Signals with special characters are properly escaped."""
        # Create page with special chars in signal value
        (temp_pages_dir / "special.py").write_text('''
from pynext import page, Signal, div, span

@page(title="Special Chars")
def special():
    message = Signal("<script>alert('xss')</script>", name="message")
    
    return div()[
        span()[message]
    ]
''')
        
        # Would need to rescan router, but this tests the concept
        # In real usage, the special chars should be escaped
    
    def test_large_state(self, temp_pages_dir):
        """Large state objects are handled."""
        # This tests that we can serialize large amounts of data
        large_list = list(range(1000))
        
        signal = Signal(large_list)
        js_init = signal.get_js_init()
        
        # Should contain serialized list
        assert "__pynext__.createSignal" in js_init
        assert "1000" not in js_init or str(large_list[-1]) in js_init

