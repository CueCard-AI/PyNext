"""
PyNext Testing - Mocking Utilities

WHAT THIS FILE DOES:
Provides mocking utilities for browser APIs (fetch, navigator, window, document)
and PyNext-specific mocks (Signal mocking, custom mock factories).

WHY THIS EXISTS:
Testing client components often requires mocking browser APIs.
This module provides simple, reusable mocks for common scenarios.

HOW IT WORKS:
- Stores mock implementations in global registry
- Provides context managers for automatic cleanup
- Supports custom mock factories for complex scenarios

WHO USES THIS:
- Tests that need to mock browser APIs
- Tests that need to mock Signals
- Tests that need custom mock implementations

WHEN TO USE:
- Testing fetch calls: mock_fetch
- Testing navigator APIs: mock_navigator
- Testing window/document: mock_window, mock_document
- Testing Signals: mock_signal
- Custom scenarios: create_mock_factory

EXAMPLES:
    from pynext.testing.mocks import mock_fetch, mock_signal
    
    with mock_fetch({"https://api.example.com": {"status": 200, "data": {...}}}):
        # fetch() is now mocked
        response = await fetch("https://api.example.com")
    
    signal = mock_signal(initial_value=0)
    assert signal() == 0
"""

from __future__ import annotations

import contextlib
from typing import Any, Callable, Dict, Optional, Union
from unittest.mock import Mock, MagicMock

from pynext.reactive import Signal


# =============================================================================
# Mock Registry
# =============================================================================

_mock_registry: Dict[str, Any] = {}


# =============================================================================
# Fetch Mocking
# =============================================================================

class FetchMock:
    """
    Mock implementation of fetch API.
    
    Supports URL-to-response mapping and custom response handlers.
    """
    
    def __init__(self, responses: Optional[Dict[str, Any]] = None):
        """
        Initialize fetch mock.
        
        Args:
            responses: Dict mapping URLs to responses
                       Response can be dict (status, data) or callable
        """
        self.responses = responses or {}
        self._calls = []
    
    def __call__(self, url: str, **kwargs) -> Any:
        """
        Mock fetch call.
        
        Args:
            url: URL to fetch
            **kwargs: Fetch options
            
        Returns:
            Mock response
        """
        self._calls.append({"url": url, "kwargs": kwargs})
        
        # Check if we have a response for this URL
        if url in self.responses:
            response = self.responses[url]
            
            # If response is a callable, call it
            if callable(response):
                result = response(url, **kwargs)
                # If result is a dict, wrap it in a mock response
                if isinstance(result, dict):
                    mock_response = MagicMock()
                    mock_response.status = result.get("status", 200)
                    mock_response.ok = 200 <= mock_response.status < 300
                    
                    async def json_async():
                        return result.get("data", {})
                    
                    async def text_async():
                        return result.get("text", "")
                    
                    mock_response.json = json_async
                    mock_response.text = text_async
                    return mock_response
                return result
            
            # If response is a dict, create a mock response
            if isinstance(response, dict):
                mock_response = MagicMock()
                mock_response.status = response.get("status", 200)
                mock_response.ok = 200 <= mock_response.status < 300
                mock_response.json.return_value = response.get("data", {})
                mock_response.text.return_value = response.get("text", "")
                
                # Make it awaitable
                async def json_async():
                    return response.get("data", {})
                
                async def text_async():
                    return response.get("text", "")
                
                mock_response.json = json_async
                mock_response.text = text_async
                
                return mock_response
        
        # Default: return 404
        mock_response = MagicMock()
        mock_response.status = 404
        mock_response.ok = False
        mock_response.json.return_value = {"error": "Not found"}
        mock_response.text.return_value = "Not found"
        
        async def json_async():
            return {"error": "Not found"}
        
        async def text_async():
            return "Not found"
        
        mock_response.json = json_async
        mock_response.text = text_async
        
        return mock_response
    
    @property
    def calls(self) -> list:
        """Get list of fetch calls made."""
        return self._calls


@contextlib.contextmanager
def mock_fetch(responses: Optional[Dict[str, Any]] = None):
    """
    Context manager for mocking fetch API.
    
    Args:
        responses: Dict mapping URLs to responses
        
    Example:
        with mock_fetch({
            "https://api.example.com/users": {
                "status": 200,
                "data": [{"id": 1, "name": "John"}]
            }
        }):
            response = await fetch("https://api.example.com/users")
    """
    fetch_mock = FetchMock(responses)
    _mock_registry["fetch"] = fetch_mock
    
    try:
        yield fetch_mock
    finally:
        if "fetch" in _mock_registry:
            del _mock_registry["fetch"]


# =============================================================================
# Navigator Mocking
# =============================================================================

class NavigatorMock:
    """
    Mock implementation of navigator API.
    """
    
    def __init__(self, **attrs):
        """
        Initialize navigator mock.
        
        Args:
            **attrs: Navigator attributes to set
        """
        self.userAgent = attrs.get("userAgent", "PyNext Test Agent")
        self.language = attrs.get("language", "en-US")
        self.languages = attrs.get("languages", ["en-US"])
        self.onLine = attrs.get("onLine", True)
        self.platform = attrs.get("platform", "Test Platform")
        
        # Add any additional attributes
        for key, value in attrs.items():
            if not hasattr(self, key):
                setattr(self, key, value)


@contextlib.contextmanager
def mock_navigator(**attrs):
    """
    Context manager for mocking navigator API.
    
    Args:
        **attrs: Navigator attributes to set
        
    Example:
        with mock_navigator(userAgent="Custom Agent", language="fr-FR"):
            # navigator is now mocked
            assert navigator.language == "fr-FR"
    """
    nav_mock = NavigatorMock(**attrs)
    _mock_registry["navigator"] = nav_mock
    
    try:
        yield nav_mock
    finally:
        if "navigator" in _mock_registry:
            del _mock_registry["navigator"]


# =============================================================================
# Window Mocking
# =============================================================================

class WindowMock:
    """
    Mock implementation of window API.
    """
    
    def __init__(self, **attrs):
        """
        Initialize window mock.
        
        Args:
            **attrs: Window attributes to set
        """
        self.location = attrs.get("location", Mock())
        self.document = attrs.get("document", Mock())
        self.localStorage = attrs.get("localStorage", {})
        self.sessionStorage = attrs.get("sessionStorage", {})
        
        # Add any additional attributes
        for key, value in attrs.items():
            if not hasattr(self, key):
                setattr(self, key, value)
    
    def alert(self, message: str) -> None:
        """Mock alert function."""
        pass
    
    def confirm(self, message: str) -> bool:
        """Mock confirm function."""
        return True
    
    def prompt(self, message: str, default: str = "") -> Optional[str]:
        """Mock prompt function."""
        return default


@contextlib.contextmanager
def mock_window(**attrs):
    """
    Context manager for mocking window API.
    
    Args:
        **attrs: Window attributes to set
        
    Example:
        with mock_window(location={"href": "https://example.com"}):
            # window is now mocked
            assert window.location.href == "https://example.com"
    """
    window_mock = WindowMock(**attrs)
    _mock_registry["window"] = window_mock
    
    try:
        yield window_mock
    finally:
        if "window" in _mock_registry:
            del _mock_registry["window"]


# =============================================================================
# Document Mocking
# =============================================================================

class DocumentMock:
    """
    Mock implementation of document API.
    """
    
    def __init__(self, **attrs):
        """
        Initialize document mock.
        
        Args:
            **attrs: Document attributes to set
        """
        self.body = attrs.get("body", Mock())
        self.documentElement = attrs.get("documentElement", Mock())
        self.cookie = attrs.get("cookie", "")
        self.title = attrs.get("title", "Test Document")
        
        # Mock querySelector
        self.querySelector = Mock(return_value=None)
        self.querySelectorAll = Mock(return_value=[])
        self.getElementById = Mock(return_value=None)
        self.getElementsByClassName = Mock(return_value=[])
        self.getElementsByTagName = Mock(return_value=[])
        
        # Add any additional attributes
        for key, value in attrs.items():
            if not hasattr(self, key):
                setattr(self, key, value)
    
    def createElement(self, tag: str) -> Mock:
        """Mock createElement."""
        element = Mock()
        element.tagName = tag.upper()
        return element


@contextlib.contextmanager
def mock_document(**attrs):
    """
    Context manager for mocking document API.
    
    Args:
        **attrs: Document attributes to set
        
    Example:
        with mock_document(title="Test Page"):
            # document is now mocked
            assert document.title == "Test Page"
    """
    doc_mock = DocumentMock(**attrs)
    _mock_registry["document"] = doc_mock
    
    try:
        yield doc_mock
    finally:
        if "document" in _mock_registry:
            del _mock_registry["document"]


# =============================================================================
# Signal Mocking
# =============================================================================

def mock_signal(initial_value: Any = None) -> Signal:
    """
    Create a mock Signal for testing.
    
    Args:
        initial_value: Initial value for the signal
        
    Returns:
        Signal instance
        
    Example:
        count = mock_signal(0)
        assert count() == 0
        count.set(5)
        assert count() == 5
    """
    return Signal(initial_value)


class SignalMockFactory:
    """
    Factory for creating mock Signals with custom behavior.
    """
    
    @staticmethod
    def create_with_setter(initial_value: Any, setter_fn: Callable[[Any], Any]) -> Signal:
        """
        Create a Signal with custom setter behavior.
        
        Args:
            initial_value: Initial value
            setter_fn: Function to call when set() is called
            
        Returns:
            Signal with custom setter
        """
        # Create a wrapper class that intercepts set calls
        class CustomSignal(Signal):
            def __init__(self, val, setter):
                super().__init__(val)
                self._custom_setter = setter
            
            def set(self, value):
                result = self._custom_setter(value)
                super().set(result)
        
        return CustomSignal(initial_value, setter_fn)
    
    @staticmethod
    def create_readonly(initial_value: Any) -> Signal:
        """
        Create a read-only Signal (set() does nothing).
        
        Args:
            initial_value: Initial value
            
        Returns:
            Read-only Signal
        """
        # Create a wrapper class that ignores set calls
        class ReadOnlySignal(Signal):
            def set(self, value):
                pass  # No-op - ignore set calls
        
        return ReadOnlySignal(initial_value)


# =============================================================================
# Custom Mock Factories
# =============================================================================

class MockFactory:
    """
    Factory for creating custom mocks.
    """
    
    @staticmethod
    def create(factory_fn: Callable[[], Any]) -> Any:
        """
        Create a mock using a factory function.
        
        Args:
            factory_fn: Function that returns a mock object
            
        Returns:
            Mock object
            
        Example:
            def create_api_mock():
                mock = Mock()
                mock.get = Mock(return_value={"data": "test"})
                return mock
            
            api = MockFactory.create(create_api_mock)
            assert api.get() == {"data": "test"}
        """
        return factory_fn()
    
    @staticmethod
    def create_with_config(config: Dict[str, Any]) -> Callable[[], Any]:
        """
        Create a factory function from a config dict.
        
        Args:
            config: Dict mapping attribute names to values/callables
            
        Returns:
            Factory function
            
        Example:
            factory = MockFactory.create_with_config({
                "get": lambda: {"data": "test"},
                "post": Mock(return_value={"success": True})
            })
            api = factory()
            assert api.get() == {"data": "test"}
        """
        def factory():
            mock = Mock()
            for key, value in config.items():
                if callable(value):
                    setattr(mock, key, value)
                else:
                    setattr(mock, key, value)
            return mock
        
        return factory


def create_mock_factory(factory_fn: Callable[[], Any]) -> Callable[[], Any]:
    """
    Create a reusable mock factory.
    
    Args:
        factory_fn: Function that returns a mock object
        
    Returns:
        Factory function
        
    Example:
        def create_user_api():
            mock = Mock()
            mock.get_user = Mock(return_value={"id": 1, "name": "John"})
            return mock
        
        user_api_factory = create_mock_factory(create_user_api)
        api1 = user_api_factory()
        api2 = user_api_factory()  # Fresh mock each time
    """
    return factory_fn


# =============================================================================
# Cleanup Utilities
# =============================================================================

def clear_all_mocks() -> None:
    """
    Clear all registered mocks.
    
    This is useful for cleanup between tests.
    """
    _mock_registry.clear()


def get_mock(name: str) -> Optional[Any]:
    """
    Get a registered mock by name.
    
    Args:
        name: Mock name (e.g., "fetch", "navigator")
        
    Returns:
        Mock object or None
    """
    return _mock_registry.get(name)

