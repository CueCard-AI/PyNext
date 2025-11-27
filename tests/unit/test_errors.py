"""
Comprehensive tests for Error Types and Pages.

Tests:
- PyNextError base class
- UnauthorizedError (401)
- ForbiddenError (403)
- NotFoundError (404)
- ServerError (500)
- BadRequestError (400)
- Convenience functions (unauthorized, forbidden, etc.)
- Error page decorators (@unauthorized_page, @forbidden_page, etc.)
- Default error page rendering
"""

import pytest
from pynext.core.errors import (
    # Error classes
    PyNextError,
    UnauthorizedError,
    ForbiddenError,
    NotFoundError,
    ServerError,
    BadRequestError,
    # Convenience functions
    unauthorized,
    forbidden,
    not_found as raise_not_found,  # Renamed in __init__ to avoid conflict
    bad_request,
    server_error,
    # Page decorators
    ErrorPage,
    UnauthorizedPage,
    ForbiddenPage,
    NotFoundPage,
    ServerErrorPage,
    unauthorized_page,
    forbidden_page,
    not_found_page,
    server_error_page,
    # Utilities
    get_default_error_html,
)


# =============================================================================
# PyNextError Base Class Tests
# =============================================================================

class TestPyNextError:
    """Tests for PyNextError base class."""
    
    def test_default_message(self):
        """Has default message."""
        error = PyNextError()
        assert error.message == "Internal Server Error"
    
    def test_custom_message(self):
        """Accepts custom message."""
        error = PyNextError("Custom error")
        assert error.message == "Custom error"
    
    def test_status_code(self):
        """Has default status code 500."""
        error = PyNextError()
        assert error.status_code == 500
    
    def test_to_dict(self):
        """Converts to dictionary."""
        error = PyNextError("Test error")
        result = error.to_dict()
        
        assert result["error"] == "PyNextError"
        assert result["status_code"] == 500
        assert result["message"] == "Test error"
    
    def test_is_exception(self):
        """Is a proper exception."""
        error = PyNextError("Test")
        
        with pytest.raises(PyNextError):
            raise error


# =============================================================================
# UnauthorizedError (401) Tests
# =============================================================================

class TestUnauthorizedError:
    """Tests for UnauthorizedError (401)."""
    
    def test_status_code(self):
        """Has status code 401."""
        error = UnauthorizedError()
        assert error.status_code == 401
    
    def test_default_message(self):
        """Has default message."""
        error = UnauthorizedError()
        assert error.message == "Please sign in to continue"
    
    def test_custom_message(self):
        """Accepts custom message."""
        error = UnauthorizedError("Must be logged in")
        assert error.message == "Must be logged in"
    
    def test_default_redirect(self):
        """Default redirect is /login."""
        error = UnauthorizedError()
        assert error.redirect_to == "/login"
    
    def test_custom_redirect(self):
        """Accepts custom redirect."""
        error = UnauthorizedError(redirect_to="/auth/signin")
        assert error.redirect_to == "/auth/signin"
    
    def test_return_to_url(self):
        """Accepts return_to URL."""
        error = UnauthorizedError(return_to="/dashboard")
        assert error.return_to == "/dashboard"
    
    def test_get_login_url_simple(self):
        """get_login_url returns redirect without return path."""
        error = UnauthorizedError(redirect_to="/login")
        assert error.get_login_url() == "/login"
    
    def test_get_login_url_with_return(self):
        """get_login_url includes return_to parameter."""
        error = UnauthorizedError(redirect_to="/login", return_to="/dashboard")
        assert error.get_login_url() == "/login?return_to=/dashboard"
    
    def test_to_dict(self):
        """Converts to dictionary."""
        error = UnauthorizedError("Please sign in")
        result = error.to_dict()
        
        assert result["error"] == "UnauthorizedError"
        assert result["status_code"] == 401


# =============================================================================
# ForbiddenError (403) Tests
# =============================================================================

class TestForbiddenError:
    """Tests for ForbiddenError (403)."""
    
    def test_status_code(self):
        """Has status code 403."""
        error = ForbiddenError()
        assert error.status_code == 403
    
    def test_default_message(self):
        """Has default message."""
        error = ForbiddenError()
        assert "permission" in error.message.lower()
    
    def test_custom_message(self):
        """Accepts custom message."""
        error = ForbiddenError("Admin only")
        assert error.message == "Admin only"
    
    def test_required_role(self):
        """Accepts required_role."""
        error = ForbiddenError("Admin only", required_role="admin")
        assert error.required_role == "admin"
    
    def test_to_dict(self):
        """Converts to dictionary."""
        error = ForbiddenError()
        result = error.to_dict()
        
        assert result["error"] == "ForbiddenError"
        assert result["status_code"] == 403


# =============================================================================
# NotFoundError (404) Tests
# =============================================================================

class TestNotFoundError:
    """Tests for NotFoundError (404)."""
    
    def test_status_code(self):
        """Has status code 404."""
        error = NotFoundError()
        assert error.status_code == 404
    
    def test_default_message(self):
        """Has default message."""
        error = NotFoundError()
        assert "doesn't exist" in error.message or "not found" in error.message.lower()
    
    def test_custom_message(self):
        """Accepts custom message."""
        error = NotFoundError("Post not found")
        assert error.message == "Post not found"


# =============================================================================
# ServerError (500) Tests
# =============================================================================

class TestServerError:
    """Tests for ServerError (500)."""
    
    def test_status_code(self):
        """Has status code 500."""
        error = ServerError()
        assert error.status_code == 500
    
    def test_default_message(self):
        """Has default message."""
        error = ServerError()
        assert "wrong" in error.message.lower()


# =============================================================================
# BadRequestError (400) Tests
# =============================================================================

class TestBadRequestError:
    """Tests for BadRequestError (400)."""
    
    def test_status_code(self):
        """Has status code 400."""
        error = BadRequestError()
        assert error.status_code == 400
    
    def test_default_message(self):
        """Has default message."""
        error = BadRequestError()
        assert "could not be processed" in error.message or "request" in error.message.lower()


# =============================================================================
# Convenience Function Tests
# =============================================================================

class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    def test_unauthorized_raises(self):
        """unauthorized() raises UnauthorizedError."""
        with pytest.raises(UnauthorizedError):
            unauthorized()
    
    def test_unauthorized_with_message(self):
        """unauthorized() passes message."""
        try:
            unauthorized("Members only")
        except UnauthorizedError as e:
            assert e.message == "Members only"
    
    def test_unauthorized_with_redirect(self):
        """unauthorized() passes redirect_to."""
        try:
            unauthorized(redirect_to="/auth")
        except UnauthorizedError as e:
            assert e.redirect_to == "/auth"
    
    def test_forbidden_raises(self):
        """forbidden() raises ForbiddenError."""
        with pytest.raises(ForbiddenError):
            forbidden()
    
    def test_forbidden_with_role(self):
        """forbidden() passes required_role."""
        try:
            forbidden("Admin only", required_role="admin")
        except ForbiddenError as e:
            assert e.required_role == "admin"
    
    def test_not_found_raises(self):
        """raise_not_found() raises NotFoundError."""
        with pytest.raises(NotFoundError):
            raise_not_found()
    
    def test_bad_request_raises(self):
        """bad_request() raises BadRequestError."""
        with pytest.raises(BadRequestError):
            bad_request()
    
    def test_server_error_raises(self):
        """server_error() raises ServerError."""
        with pytest.raises(ServerError):
            server_error()


# =============================================================================
# Error Page Decorator Tests
# =============================================================================

class TestErrorPageDecorators:
    """Tests for error page decorators."""
    
    def test_unauthorized_page_decorator(self):
        """@unauthorized_page creates UnauthorizedPage."""
        @unauthorized_page
        def custom_401():
            return "<h1>Please Sign In</h1>"
        
        assert isinstance(custom_401, UnauthorizedPage)
        assert custom_401.status_code == 401
    
    def test_forbidden_page_decorator(self):
        """@forbidden_page creates ForbiddenPage."""
        @forbidden_page
        def custom_403():
            return "<h1>Access Denied</h1>"
        
        assert isinstance(custom_403, ForbiddenPage)
        assert custom_403.status_code == 403
    
    def test_not_found_page_decorator(self):
        """@not_found_page creates NotFoundPage."""
        @not_found_page
        def custom_404():
            return "<h1>Not Found</h1>"
        
        assert isinstance(custom_404, NotFoundPage)
        assert custom_404.status_code == 404
    
    def test_server_error_page_decorator(self):
        """@server_error_page creates ServerErrorPage."""
        @server_error_page
        def custom_500():
            return "<h1>Server Error</h1>"
        
        assert isinstance(custom_500, ServerErrorPage)
        assert custom_500.status_code == 500
    
    def test_preserves_function_name(self):
        """Decorator preserves function name."""
        @unauthorized_page
        def my_custom_page():
            return "<h1>Test</h1>"
        
        assert my_custom_page.__name__ == "my_custom_page"


# =============================================================================
# ErrorPage Rendering Tests
# =============================================================================

class TestErrorPageRendering:
    """Tests for ErrorPage.render() and render_full_page()."""
    
    def test_render_basic(self):
        """Renders basic content."""
        @unauthorized_page
        def my_page():
            return "<h1>Sign In</h1>"
        
        html = my_page.render()
        assert "<h1>Sign In</h1>" in html
    
    def test_render_with_error_param(self):
        """Passes error to function."""
        @unauthorized_page
        def my_page(error=None):
            return f"<h1>{error.message if error else 'Default'}</h1>"
        
        error = UnauthorizedError("Custom message")
        html = my_page.render(error)
        assert "Custom message" in html
    
    def test_render_without_error_param(self):
        """Works when function doesn't accept error."""
        @unauthorized_page
        def my_page():
            return "<h1>Static</h1>"
        
        error = UnauthorizedError("Ignored")
        html = my_page.render(error)
        assert "<h1>Static</h1>" in html
    
    def test_render_full_page(self):
        """Renders full HTML document."""
        @unauthorized_page
        def my_page():
            return "<h1>Sign In</h1>"
        
        html = my_page.render_full_page()
        
        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "</html>" in html
        assert '<meta charset="UTF-8">' in html
        assert "noindex" in html  # SEO noindex for error pages
    
    def test_render_full_page_custom_title(self):
        """Allows custom page title."""
        @unauthorized_page
        def my_page():
            return "<h1>Sign In</h1>"
        
        html = my_page.render_full_page(title="Custom Title")
        assert "Custom Title" in html
    
    def test_render_with_component(self):
        """Handles components with render() method."""
        class MockComponent:
            def render(self):
                return "<div>Component</div>"
        
        @unauthorized_page
        def my_page():
            return MockComponent()
        
        html = my_page.render()
        assert "<div>Component</div>" in html
    
    def test_render_full_page_has_fallback_styles(self):
        """Full page has fallback CSS."""
        @forbidden_page
        def my_page():
            return "<h1>Denied</h1>"
        
        html = my_page.render_full_page()
        assert "font-family" in html
        assert "error-container" in html


# =============================================================================
# Default Error HTML Tests
# =============================================================================

class TestDefaultErrorHTML:
    """Tests for get_default_error_html() function."""
    
    def test_401_default_html(self):
        """Generates 401 default page."""
        html = get_default_error_html(401)
        
        assert "401" in html
        assert "Sign In" in html or "sign in" in html.lower()
        assert "<!DOCTYPE html>" in html
    
    def test_401_with_error(self):
        """Includes error message in 401 page."""
        error = UnauthorizedError("Custom message")
        html = get_default_error_html(401, error)
        
        assert "Custom message" in html
    
    def test_403_default_html(self):
        """Generates 403 default page."""
        html = get_default_error_html(403)
        
        assert "403" in html
        assert "Denied" in html or "Forbidden" in html
    
    def test_404_default_html(self):
        """Generates 404 default page."""
        html = get_default_error_html(404)
        
        assert "404" in html
        assert "Not Found" in html or "not found" in html.lower()
    
    def test_500_default_html(self):
        """Generates 500 default page."""
        html = get_default_error_html(500)
        
        assert "500" in html
        assert "Wrong" in html or "Error" in html
    
    def test_unknown_status_code(self):
        """Unknown status code falls back to 500 template."""
        html = get_default_error_html(418)  # I'm a teapot
        
        # Should still render something
        assert "<!DOCTYPE html>" in html
    
    def test_default_html_includes_home_link(self):
        """Default pages include link to home."""
        for status_code in [401, 403, 404, 500]:
            html = get_default_error_html(status_code)
            assert 'href="/' in html or 'href=\\"/' in html


# =============================================================================
# Exception Hierarchy Tests
# =============================================================================

class TestExceptionHierarchy:
    """Tests for exception inheritance."""
    
    def test_all_errors_inherit_from_pynext_error(self):
        """All error classes inherit from PyNextError."""
        errors = [
            UnauthorizedError(),
            ForbiddenError(),
            NotFoundError(),
            ServerError(),
            BadRequestError(),
        ]
        
        for error in errors:
            assert isinstance(error, PyNextError)
    
    def test_all_errors_are_exceptions(self):
        """All error classes are proper exceptions."""
        errors = [
            UnauthorizedError(),
            ForbiddenError(),
            NotFoundError(),
            ServerError(),
            BadRequestError(),
        ]
        
        for error in errors:
            assert isinstance(error, Exception)
    
    def test_catch_pynext_error_catches_all(self):
        """Can catch all PyNext errors with base class."""
        errors_to_raise = [
            lambda: unauthorized(),
            lambda: forbidden(),
            lambda: raise_not_found(),
            lambda: bad_request(),
            lambda: server_error(),
        ]
        
        for raise_error in errors_to_raise:
            try:
                raise_error()
            except PyNextError as e:
                # Should catch all
                assert e.status_code is not None


# =============================================================================
# Edge Cases
# =============================================================================

class TestErrorEdgeCases:
    """Tests for edge cases."""
    
    def test_empty_message(self):
        """Empty message uses default (empty string is falsy)."""
        error = UnauthorizedError("")
        # Empty string is falsy, so default is used
        assert error.message == "Please sign in to continue"
    
    def test_none_message(self):
        """None message uses default."""
        error = ForbiddenError(None)
        assert error.message is not None
    
    def test_unicode_message(self):
        """Handles unicode in messages."""
        error = NotFoundError("Page 不存在")
        assert error.message == "Page 不存在"
    
    def test_long_message(self):
        """Handles very long messages."""
        long_message = "Error: " + "x" * 10000
        error = ServerError(long_message)
        assert len(error.message) > 10000
    
    def test_html_in_message_is_present_in_default(self):
        """HTML in message is included (escaping is caller's responsibility)."""
        error = ForbiddenError("<script>alert('xss')</script>")
        html = get_default_error_html(403, error)
        # Default error pages include the message as-is
        # For user-facing apps, callers should sanitize user input before raising errors
        assert "script" in html.lower()

