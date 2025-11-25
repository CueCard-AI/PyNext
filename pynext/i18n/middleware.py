"""
PyNext i18n Middleware - Locale Detection and Routing.

Handles:
- Automatic locale detection from headers/cookies
- Locale prefix routing (/en/about, /fr/about)
- Locale persistence
"""

from typing import Callable, List, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, RedirectResponse
from starlette.types import ASGIApp

from pynext.i18n.locale import (
    LocaleConfig,
    get_config,
    set_locale,
    configure_i18n,
)
from pynext.i18n.translations import load_translations


class LocaleMiddleware(BaseHTTPMiddleware):
    """
    Middleware for locale detection and routing.
    
    Features:
    - Detects locale from URL prefix, cookie, or Accept-Language header
    - Sets locale for the request
    - Redirects to localized URL if needed
    - Loads translations for the locale
    """
    
    def __init__(
        self,
        app: ASGIApp,
        config: Optional[LocaleConfig] = None,
        default_namespace: str = "common"
    ):
        super().__init__(app)
        self.config = config or get_config()
        self.default_namespace = default_namespace
        
        # Apply config globally
        configure_i18n(self.config)
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """Process request with locale handling."""
        path = request.url.path
        
        # Skip static files and API routes
        if self._should_skip(path):
            return await call_next(request)
        
        # Detect locale from URL prefix
        locale, clean_path = self._extract_locale_from_path(path)
        
        if locale is None:
            # Detect from cookie or headers
            locale = self._detect_locale(request)
            
            # Redirect to localized URL if detection is enabled
            if self.config.locale_detection and self.config.strategy == "prefix":
                localized_path = f"/{locale}{path}"
                return RedirectResponse(
                    url=localized_path,
                    status_code=307
                )
        
        # Set locale for this request
        set_locale(locale)
        
        # Load translations
        load_translations(locale, self.default_namespace)
        
        # Store locale in request state
        request.state.locale = locale
        request.state.locale_path = clean_path
        
        # Process request
        response = await call_next(request)
        
        # Set locale cookie if configured
        if self.config.persist_cookie:
            response.set_cookie(
                key=self.config.cookie_name,
                value=locale,
                max_age=31536000,  # 1 year
                path="/",
                httponly=False,  # Allow JS access for client-side
            )
        
        # Set Content-Language header
        response.headers["Content-Language"] = locale
        
        return response
    
    def _should_skip(self, path: str) -> bool:
        """Check if path should skip locale handling."""
        skip_prefixes = [
            "/_next/",
            "/api/",
            "/static/",
            "/__pynext__/",
        ]
        skip_extensions = [
            ".js", ".css", ".png", ".jpg", ".jpeg", ".gif",
            ".ico", ".svg", ".woff", ".woff2", ".ttf",
        ]
        
        for prefix in skip_prefixes:
            if path.startswith(prefix):
                return True
        
        for ext in skip_extensions:
            if path.endswith(ext):
                return True
        
        return False
    
    def _extract_locale_from_path(self, path: str) -> tuple:
        """
        Extract locale from URL path prefix.
        
        Returns (locale, clean_path) or (None, path) if no locale found.
        """
        parts = path.split("/")
        
        if len(parts) > 1 and parts[1] in self.config.locales:
            locale = parts[1]
            clean_path = "/" + "/".join(parts[2:])
            if not clean_path:
                clean_path = "/"
            return locale, clean_path
        
        return None, path
    
    def _detect_locale(self, request: Request) -> str:
        """
        Detect locale from request.
        
        Priority:
        1. Cookie
        2. Accept-Language header
        3. Default locale
        """
        # Check cookie
        cookie_locale = request.cookies.get(self.config.cookie_name)
        if cookie_locale and cookie_locale in self.config.locales:
            return cookie_locale
        
        # Parse Accept-Language header
        accept_language = request.headers.get("accept-language", "")
        detected = detect_locale(
            accept_language,
            self.config.locales,
            self.config.default_locale
        )
        
        return detected


def detect_locale(
    accept_language: str,
    available_locales: List[str],
    default: str
) -> str:
    """
    Parse Accept-Language header and find best match.
    
    Example:
        detect_locale("en-US,en;q=0.9,fr;q=0.8", ["en", "fr", "de"], "en")
        # Returns "en"
    """
    if not accept_language:
        return default
    
    # Parse header: "en-US,en;q=0.9,fr;q=0.8"
    locales_with_quality = []
    
    for part in accept_language.split(","):
        part = part.strip()
        if not part:
            continue
        
        if ";q=" in part:
            locale, _, q = part.partition(";q=")
            try:
                quality = float(q)
            except ValueError:
                quality = 1.0
        else:
            locale = part
            quality = 1.0
        
        # Normalize locale (en-US -> en)
        locale = locale.split("-")[0].lower()
        locales_with_quality.append((locale, quality))
    
    # Sort by quality
    locales_with_quality.sort(key=lambda x: -x[1])
    
    # Find best match
    for locale, _ in locales_with_quality:
        if locale in available_locales:
            return locale
    
    return default


def add_locale_middleware(
    app: "FastAPI",
    config: Optional[LocaleConfig] = None,
    preload_locales: bool = True
) -> None:
    """
    Add i18n middleware to a FastAPI app.
    
    Args:
        app: FastAPI application
        config: Locale configuration
        preload_locales: Whether to preload all translations at startup
    """
    from fastapi import FastAPI
    
    if config:
        configure_i18n(config)
    
    config = config or get_config()
    
    # Add middleware
    app.add_middleware(LocaleMiddleware, config=config)
    
    # Preload translations
    if preload_locales:
        @app.on_event("startup")
        async def preload():
            from pynext.i18n.translations import get_loader
            loader = get_loader()
            loader.preload_locales(config.locales)
    
    # Add locale switching API
    @app.post("/api/locale")
    async def set_locale_api(request: Request):
        """API endpoint to switch locale."""
        body = await request.json()
        new_locale = body.get("locale")
        
        if new_locale not in config.locales:
            from fastapi import HTTPException
            raise HTTPException(400, f"Invalid locale: {new_locale}")
        
        return {"locale": new_locale}

