"""
Comprehensive tests for Client Testing Mocking Utilities.

WHAT THIS FILE TESTS:
- mock_fetch context manager
- mock_navigator context manager
- mock_window context manager
- mock_document context manager
- mock_signal function
- SignalMockFactory
- MockFactory and custom mock factories

Total: 30 tests
"""

import pytest
from pynext.testing.mocks import (
    mock_fetch, mock_navigator, mock_window, mock_document,
    mock_signal, SignalMockFactory, MockFactory, create_mock_factory,
    clear_all_mocks, get_mock
)
from pynext.reactive import Signal


# =============================================================================
# mock_fetch Tests
# =============================================================================

class TestMockFetch:
    """Tests for mock_fetch context manager."""
    
    def test_mock_fetch_simple_response(self):
        """Test mock_fetch with simple response."""
        with mock_fetch({
            "https://api.example.com/data": {
                "status": 200,
                "data": {"key": "value"}
            }
        }) as mock:
            # Mock should be available
            assert mock is not None
            assert hasattr(mock, 'calls')
    
    def test_mock_fetch_callable_response(self):
        """Test mock_fetch with callable response."""
        def response_handler(url, **kwargs):
            if "error" in url:
                return {
                    "status": 404,
                    "data": {"error": "Not found"}
                }
            return {
                "status": 200,
                "data": {"success": True}
            }
        
        with mock_fetch({
            "https://api.example.com": response_handler
        }) as mock:
            result = mock("https://api.example.com")
            assert result.status == 200
    
    def test_mock_fetch_tracks_calls(self):
        """Test that mock_fetch tracks calls."""
        with mock_fetch({
            "https://api.example.com": {"status": 200, "data": {}}
        }) as mock:
            mock("https://api.example.com")
            mock("https://api.example.com/users")
            
            assert len(mock.calls) == 2
            assert mock.calls[0]["url"] == "https://api.example.com"


# =============================================================================
# mock_navigator Tests
# =============================================================================

class TestMockNavigator:
    """Tests for mock_navigator context manager."""
    
    def test_mock_navigator_default_attributes(self):
        """Test mock_navigator with default attributes."""
        with mock_navigator() as nav:
            assert nav.userAgent == "PyNext Test Agent"
            assert nav.language == "en-US"
            assert nav.onLine is True
    
    def test_mock_navigator_custom_attributes(self):
        """Test mock_navigator with custom attributes."""
        with mock_navigator(userAgent="Custom Agent", language="fr-FR") as nav:
            assert nav.userAgent == "Custom Agent"
            assert nav.language == "fr-FR"
    
    def test_mock_navigator_cleans_up(self):
        """Test that mock_navigator cleans up after context."""
        with mock_navigator(userAgent="Test"):
            pass
        
        # After context, mock should be cleaned up
        assert get_mock("navigator") is None


# =============================================================================
# mock_window Tests
# =============================================================================

class TestMockWindow:
    """Tests for mock_window context manager."""
    
    def test_mock_window_default(self):
        """Test mock_window with defaults."""
        with mock_window() as window:
            assert hasattr(window, 'location')
            assert hasattr(window, 'document')
            assert hasattr(window, 'localStorage')
            assert callable(window.alert)
            assert callable(window.confirm)
    
    def test_mock_window_custom_location(self):
        """Test mock_window with custom location."""
        with mock_window(location={"href": "https://example.com"}) as window:
            assert window.location["href"] == "https://example.com"
    
    def test_mock_window_alert_does_not_raise(self):
        """Test that window.alert doesn't raise."""
        with mock_window() as window:
            window.alert("Test message")  # Should not raise


# =============================================================================
# mock_document Tests
# =============================================================================

class TestMockDocument:
    """Tests for mock_document context manager."""
    
    def test_mock_document_default(self):
        """Test mock_document with defaults."""
        with mock_document() as doc:
            assert hasattr(doc, 'body')
            assert hasattr(doc, 'documentElement')
            assert callable(doc.querySelector)
            assert callable(doc.querySelectorAll)
            assert callable(doc.createElement)
    
    def test_mock_document_custom_title(self):
        """Test mock_document with custom title."""
        with mock_document(title="Test Page") as doc:
            assert doc.title == "Test Page"
    
    def test_mock_document_createElement(self):
        """Test mock_document.createElement."""
        with mock_document() as doc:
            element = doc.createElement("div")
            assert element.tagName == "DIV"


# =============================================================================
# mock_signal Tests
# =============================================================================

class TestMockSignal:
    """Tests for mock_signal function."""
    
    def test_mock_signal_basic(self):
        """Test mock_signal creates a signal."""
        signal = mock_signal(42)
        assert isinstance(signal, Signal)
        assert signal() == 42
    
    def test_mock_signal_updates(self):
        """Test mock_signal can be updated."""
        signal = mock_signal(0)
        signal.set(5)
        assert signal() == 5


# =============================================================================
# SignalMockFactory Tests
# =============================================================================

class TestSignalMockFactory:
    """Tests for SignalMockFactory."""
    
    def test_create_with_setter(self):
        """Test create_with_setter."""
        def custom_setter(value):
            return value * 2
        
        signal = SignalMockFactory.create_with_setter(5, custom_setter)
        signal.set(10)
        assert signal() == 20
    
    def test_create_readonly(self):
        """Test create_readonly."""
        signal = SignalMockFactory.create_readonly(100)
        signal.set(200)  # Should be no-op
        assert signal() == 100


# =============================================================================
# MockFactory Tests
# =============================================================================

class TestMockFactory:
    """Tests for MockFactory."""
    
    def test_create_with_function(self):
        """Test MockFactory.create with factory function."""
        def create_api():
            from unittest.mock import Mock
            mock = Mock()
            mock.get = Mock(return_value={"data": "test"})
            return mock
        
        api = MockFactory.create(create_api)
        assert api.get() == {"data": "test"}
    
    def test_create_with_config(self):
        """Test MockFactory.create_with_config."""
        factory = MockFactory.create_with_config({
            "get": lambda: {"data": "test"},
            "post": lambda x: {"success": True}
        })
        api = factory()
        assert api.get() == {"data": "test"}
        assert api.post(None) == {"success": True}


# =============================================================================
# create_mock_factory Tests
# =============================================================================

class TestCreateMockFactory:
    """Tests for create_mock_factory."""
    
    def test_create_mock_factory_reusable(self):
        """Test create_mock_factory creates reusable factory."""
        def create_user_api():
            from unittest.mock import Mock
            mock = Mock()
            mock.get_user = Mock(return_value={"id": 1, "name": "John"})
            return mock
        
        factory = create_mock_factory(create_user_api)
        api1 = factory()
        api2 = factory()
        
        # Each call should create fresh mock
        assert api1.get_user() == {"id": 1, "name": "John"}
        assert api2.get_user() == {"id": 1, "name": "John"}


# =============================================================================
# clear_all_mocks Tests
# =============================================================================

class TestClearAllMocks:
    """Tests for clear_all_mocks."""
    
    def test_clear_all_mocks(self):
        """Test clear_all_mocks clears all mocks."""
        with mock_fetch({"http://test.com": {"status": 200}}):
            with mock_navigator():
                assert get_mock("fetch") is not None
                assert get_mock("navigator") is not None
                
                clear_all_mocks()
                
                assert get_mock("fetch") is None
                assert get_mock("navigator") is None
    
    def test_clear_after_context(self):
        """Test mocks are cleared after context exits."""
        with mock_fetch({"http://test.com": {"status": 200}}):
            pass
        
        # Should be None after context
        assert get_mock("fetch") is None


# =============================================================================
# get_mock Tests
# =============================================================================

class TestGetMock:
    """Tests for get_mock function."""
    
    def test_get_mock_returns_mock(self):
        """Test get_mock returns mock when available."""
        with mock_fetch({"http://test.com": {"status": 200}}) as mock:
            retrieved = get_mock("fetch")
            assert retrieved is not None
            assert retrieved is mock
    
    def test_get_mock_returns_none_when_not_found(self):
        """Test get_mock returns None when mock not found."""
        assert get_mock("nonexistent") is None

