"""
Error Types and Pages for PyNext.

Provides custom error pages for common HTTP errors:
- 401 Unauthorized (not logged in)
- 403 Forbidden (logged in but no permission)
- 404 Not Found (already exists in routing)

Example:
    # Raise in your page
    @page
    async def admin():
        user = get_user()
        if not user:
            raise UnauthorizedError("Please log in")
        if not user.is_admin:
            raise ForbiddenError("Admin access required")
        return AdminDashboard()
    
    # Custom error page
    # pages/forbidden.py
    @forbidden_page
    def custom_403(error=None):
        return div()[
            h1()["Access Denied"],
            p()[error.message if error else "No permission"],
        ]

SolidJS Principle: Zero JS for static error pages
AI-Friendly: Raise exception → render page (that simple)
"""

from typing import Optional, Dict, Any, Callable
import inspect


# =============================================================================
# Error Classes - Simple, Clear, Typed
# =============================================================================

class PyNextError(Exception):
    """
    Base error with status code.
    
    All PyNext errors inherit from this, making them easy to catch
    and handle uniformly.
    """
    status_code: int = 500
    default_message: str = "Internal Server Error"
    
    def __init__(self, message: Optional[str] = None):
        self.message = message or self.default_message
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for JSON responses."""
        return {
            "error": self.__class__.__name__,
            "status_code": self.status_code,
            "message": self.message,
        }


class UnauthorizedError(PyNextError):
    """
    401 - User is not authenticated.
    
    Use when: User needs to log in to access this resource.
    
    Example:
        if not session.user:
            raise UnauthorizedError("Please sign in to continue")
    
    Attributes:
        redirect_to: Where to redirect after successful login
    """
    status_code = 401
    default_message = "Please sign in to continue"
    
    def __init__(
        self, 
        message: Optional[str] = None, 
        redirect_to: str = "/login",
        return_to: Optional[str] = None,
    ):
        super().__init__(message)
        self.redirect_to = redirect_to
        self.return_to = return_to  # URL to return to after login
    
    def get_login_url(self) -> str:
        """Get login URL with return path."""
        if self.return_to:
            return f"{self.redirect_to}?return_to={self.return_to}"
        return self.redirect_to


class ForbiddenError(PyNextError):
    """
    403 - User is authenticated but lacks permission.
    
    Use when: User is logged in but can't access this resource.
    
    Example:
        if not user.is_admin:
            raise ForbiddenError("Admin access required")
    
    Attributes:
        required_role: The role needed to access (for display)
    """
    status_code = 403
    default_message = "You don't have permission to access this"
    
    def __init__(
        self, 
        message: Optional[str] = None,
        required_role: Optional[str] = None,
    ):
        super().__init__(message)
        self.required_role = required_role


class NotFoundError(PyNextError):
    """
    404 - Resource not found.
    
    Use when: The requested item doesn't exist.
    
    Example:
        post = get_post(slug)
        if not post:
            raise NotFoundError(f"Post '{slug}' not found")
    """
    status_code = 404
    default_message = "The page you're looking for doesn't exist"


class ServerError(PyNextError):
    """
    500 - Internal server error.
    
    Use when: Something unexpected went wrong.
    
    Example:
        try:
            result = external_api.call()
        except APIError as e:
            raise ServerError(f"External service failed: {e}")
    """
    status_code = 500
    default_message = "Something went wrong on our end"


class BadRequestError(PyNextError):
    """
    400 - Bad request.
    
    Use when: The request is malformed or has invalid data.
    
    Example:
        if not is_valid_email(email):
            raise BadRequestError("Invalid email format")
    """
    status_code = 400
    default_message = "The request could not be processed"


# =============================================================================
# Convenience Functions - AI-Friendly One-Liners
# =============================================================================

def unauthorized(
    message: str = "Please sign in", 
    redirect_to: str = "/login",
    return_to: Optional[str] = None,
) -> None:
    """
    Raise UnauthorizedError (one-liner).
    
    Example:
        if not user:
            unauthorized("Members only")
    """
    raise UnauthorizedError(message, redirect_to, return_to)


def forbidden(
    message: str = "Access denied",
    required_role: Optional[str] = None,
) -> None:
    """
    Raise ForbiddenError (one-liner).
    
    Example:
        if not user.is_admin:
            forbidden("Admin access required", required_role="admin")
    """
    raise ForbiddenError(message, required_role)


def not_found(message: str = "Not found") -> None:
    """
    Raise NotFoundError (one-liner).
    
    Example:
        if not post:
            not_found("Post doesn't exist")
    """
    raise NotFoundError(message)


def bad_request(message: str = "Invalid request") -> None:
    """
    Raise BadRequestError (one-liner).
    
    Example:
        if not data.get('email'):
            bad_request("Email is required")
    """
    raise BadRequestError(message)


def server_error(message: str = "Server error") -> None:
    """
    Raise ServerError (one-liner).
    
    Example:
        if not database.connected:
            server_error("Database unavailable")
    """
    raise ServerError(message)


# =============================================================================
# Error Page Decorators
# =============================================================================

class ErrorPage:
    """
    Base class for custom error pages.
    
    Error pages are rendered with zero JavaScript by default
    for maximum performance and reliability.
    """
    status_code: int
    
    def __init__(self, fn: Callable):
        self.fn = fn
        self.name = fn.__name__
        self.__name__ = fn.__name__
        self.__doc__ = fn.__doc__
    
    def render(self, error: Optional[PyNextError] = None) -> str:
        """Render the error page content."""
        # Check if function accepts error param
        sig = inspect.signature(self.fn)
        
        if 'error' in sig.parameters:
            result = self.fn(error=error)
        else:
            result = self.fn()
        
        if hasattr(result, 'render'):
            return result.render()
        return str(result) if result else ""
    
    def render_full_page(
        self, 
        error: Optional[PyNextError] = None,
        title: Optional[str] = None,
        stylesheet: str = "/_pynext/styles.css",
    ) -> str:
        """
        Render as complete HTML document (zero JS).
        
        Args:
            error: The error that triggered this page
            title: Custom page title
            stylesheet: Path to stylesheet
        
        Returns:
            Complete HTML document string
        """
        content = self.render(error)
        page_title = title or f"{self.status_code} Error"
        
        # No hydration script - pure HTML for reliability
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="robots" content="noindex, nofollow">
    <title>{page_title}</title>
    <link rel="stylesheet" href="{stylesheet}">
    <style>
        /* Fallback styles if CSS fails to load */
        body {{
            font-family: system-ui, -apple-system, sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
            background: #f5f5f5;
        }}
        .error-container {{
            text-align: center;
            padding: 2rem;
        }}
    </style>
</head>
<body>
    <div id="__pynext" class="error-container">
        {content}
    </div>
</body>
</html>'''


class UnauthorizedPage(ErrorPage):
    """
    Custom 401 page.
    
    Rendered when UnauthorizedError is raised.
    """
    status_code = 401


class ForbiddenPage(ErrorPage):
    """
    Custom 403 page.
    
    Rendered when ForbiddenError is raised.
    """
    status_code = 403


class NotFoundPage(ErrorPage):
    """
    Custom 404 page.
    
    Rendered when NotFoundError is raised or route not found.
    """
    status_code = 404


class ServerErrorPage(ErrorPage):
    """
    Custom 500 page.
    
    Rendered when ServerError or unhandled exception occurs.
    """
    status_code = 500


def unauthorized_page(fn: Callable) -> UnauthorizedPage:
    """
    Decorator for custom 401 page.
    
    The decorated function receives an optional `error` parameter
    containing the UnauthorizedError that was raised.
    
    Example:
        # pages/unauthorized.py
        @unauthorized_page
        def custom_401(error=None):
            return div(class_="error-page")[
                h1()["Sign In Required"],
                p()[error.message if error else "Please log in"],
                a(href="/login")["Go to Login"],
            ]
    """
    return UnauthorizedPage(fn)


def forbidden_page(fn: Callable) -> ForbiddenPage:
    """
    Decorator for custom 403 page.
    
    The decorated function receives an optional `error` parameter
    containing the ForbiddenError that was raised.
    
    Example:
        # pages/forbidden.py
        @forbidden_page
        def custom_403(error=None):
            return div(class_="error-page")[
                h1()["Access Denied"],
                p()[error.message if error else "No permission"],
                a(href="/")["Go Home"],
            ]
    """
    return ForbiddenPage(fn)


def not_found_page(fn: Callable) -> NotFoundPage:
    """
    Decorator for custom 404 page.
    
    Example:
        # pages/not-found.py
        @not_found_page
        def custom_404(error=None):
            return div(class_="error-page")[
                h1()["Page Not Found"],
                p()["The page you're looking for doesn't exist."],
                a(href="/")["Go Home"],
            ]
    """
    return NotFoundPage(fn)


def server_error_page(fn: Callable) -> ServerErrorPage:
    """
    Decorator for custom 500 page.
    
    Example:
        # pages/error.py
        @server_error_page
        def custom_500(error=None):
            return div(class_="error-page")[
                h1()["Something Went Wrong"],
                p()["We're working on it."],
                a(href="/")["Go Home"],
            ]
    """
    return ServerErrorPage(fn)


# =============================================================================
# Default Error Pages
# =============================================================================

def _default_unauthorized_content(error: Optional[UnauthorizedError] = None) -> str:
    """Default 401 page content."""
    message = error.message if error else "Please sign in to continue"
    login_url = error.get_login_url() if error else "/login"
    
    return f'''
<div style="text-align: center; padding: 50px;">
    <h1 style="font-size: 72px; margin: 0; color: #666;">401</h1>
    <h2 style="margin: 10px 0;">Sign In Required</h2>
    <p style="color: #666; margin: 20px 0;">{message}</p>
    <a href="{login_url}" style="
        display: inline-block;
        padding: 12px 24px;
        background: #0070f3;
        color: white;
        text-decoration: none;
        border-radius: 6px;
        font-weight: 500;
    ">Sign In</a>
</div>
'''


def _default_forbidden_content(error: Optional[ForbiddenError] = None) -> str:
    """Default 403 page content."""
    message = error.message if error else "You don't have permission to access this"
    
    return f'''
<div style="text-align: center; padding: 50px;">
    <h1 style="font-size: 72px; margin: 0; color: #666;">403</h1>
    <h2 style="margin: 10px 0;">Access Denied</h2>
    <p style="color: #666; margin: 20px 0;">{message}</p>
    <a href="/" style="
        display: inline-block;
        padding: 12px 24px;
        background: #0070f3;
        color: white;
        text-decoration: none;
        border-radius: 6px;
        font-weight: 500;
    ">Go Home</a>
</div>
'''


def _default_not_found_content(error: Optional[NotFoundError] = None) -> str:
    """Default 404 page content."""
    message = error.message if error else "The page you're looking for doesn't exist"
    
    return f'''
<div style="text-align: center; padding: 50px;">
    <h1 style="font-size: 72px; margin: 0; color: #666;">404</h1>
    <h2 style="margin: 10px 0;">Page Not Found</h2>
    <p style="color: #666; margin: 20px 0;">{message}</p>
    <a href="/" style="
        display: inline-block;
        padding: 12px 24px;
        background: #0070f3;
        color: white;
        text-decoration: none;
        border-radius: 6px;
        font-weight: 500;
    ">Go Home</a>
</div>
'''


def _default_server_error_content(error: Optional[ServerError] = None) -> str:
    """Default 500 page content."""
    return '''
<div style="text-align: center; padding: 50px;">
    <h1 style="font-size: 72px; margin: 0; color: #666;">500</h1>
    <h2 style="margin: 10px 0;">Something Went Wrong</h2>
    <p style="color: #666; margin: 20px 0;">We're working on fixing this.</p>
    <a href="/" style="
        display: inline-block;
        padding: 12px 24px;
        background: #0070f3;
        color: white;
        text-decoration: none;
        border-radius: 6px;
        font-weight: 500;
    ">Go Home</a>
</div>
'''


def get_default_error_html(
    status_code: int, 
    error: Optional[PyNextError] = None,
) -> str:
    """
    Get default error page HTML for a status code.
    
    Args:
        status_code: HTTP status code
        error: Optional error with details
    
    Returns:
        Complete HTML document
    """
    content_fn = {
        401: _default_unauthorized_content,
        403: _default_forbidden_content,
        404: _default_not_found_content,
        500: _default_server_error_content,
    }.get(status_code, _default_server_error_content)
    
    content = content_fn(error)
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="robots" content="noindex, nofollow">
    <title>{status_code} Error</title>
</head>
<body style="font-family: system-ui, -apple-system, sans-serif; margin: 0; display: flex; align-items: center; justify-content: center; min-height: 100vh; background: #fafafa;">
    {content}
</body>
</html>'''

