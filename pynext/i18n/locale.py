"""
PyNext Locale Signal - Fine-Grained i18n Reactivity.

Unlike Next.js which re-renders the entire tree on locale change,
PyNext uses signal-based reactivity to only update text nodes.

This results in:
- No component re-renders
- Direct DOM text updates
- Instant locale switching
- Minimal JavaScript
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Union
import json


@dataclass
class LocaleConfig:
    """Configuration for i18n."""
    # Available locales
    locales: List[str] = field(default_factory=lambda: ["en"])
    
    # Default locale
    default_locale: str = "en"
    
    # Enable automatic locale detection
    locale_detection: bool = True
    
    # Path to translations directory
    translations_path: str = "locales"
    
    # Fallback locale when translation missing
    fallback_locale: Optional[str] = None
    
    # URL strategy: "prefix" (/en/about) or "domain" (en.example.com)
    strategy: str = "prefix"
    
    # Persist locale in cookie
    persist_cookie: bool = True
    cookie_name: str = "PYNEXT_LOCALE"
    
    # Default number/date formats per locale
    formats: Dict[str, Dict[str, str]] = field(default_factory=dict)


class Locale:
    """
    Represents a locale with its configuration.
    """
    
    def __init__(self, code: str, name: str = "", direction: str = "ltr"):
        self.code = code
        self.name = name or code
        self.direction = direction  # ltr or rtl
    
    def __str__(self) -> str:
        return self.code
    
    def __eq__(self, other) -> bool:
        if isinstance(other, str):
            return self.code == other
        if isinstance(other, Locale):
            return self.code == other.code
        return False
    
    def __hash__(self) -> int:
        return hash(self.code)


class LocaleSignal:
    """
    Signal for the current locale.
    
    When this signal changes, only subscribed text nodes update,
    not entire components. This is the key to efficient i18n.
    """
    
    def __init__(self, initial: str, config: LocaleConfig):
        self._value = initial
        self.config = config
        self._translations: Dict[str, Dict[str, str]] = {}
        self._subscribers: List[Callable] = []
    
    def get(self) -> str:
        """Get current locale."""
        return self._value
    
    def set(self, value: str) -> None:
        """Set locale and notify subscribers."""
        if value != self._value:
            old = self._value
            self._value = value
            for sub in self._subscribers:
                sub(value, old)
    
    def subscribe(self, fn: Callable) -> Callable:
        """Subscribe to locale changes."""
        self._subscribers.append(fn)
        return lambda: self._subscribers.remove(fn)
    
    def set_locale(self, locale: str) -> None:
        """Change the current locale."""
        if locale not in self.config.locales:
            locale = self.config.fallback_locale or self.config.default_locale
        self.set(locale)
    
    def load_translations(self, locale: str, translations: Dict[str, str]) -> None:
        """Load translations for a locale."""
        self._translations[locale] = translations
    
    def get_translation(self, key: str, default: Optional[str] = None) -> str:
        """Get translation for current locale."""
        current = self.get()
        
        if current in self._translations:
            value = self._translations[current].get(key)
            if value is not None:
                return value
        
        # Try fallback
        if self.config.fallback_locale and self.config.fallback_locale in self._translations:
            value = self._translations[self.config.fallback_locale].get(key)
            if value is not None:
                return value
        
        return default or key
    
    def get_js_init(self) -> str:
        """Generate JavaScript initialization for client-side."""
        return f"""
__pynext__.locale = {{
    current: "{self.get()}",
    available: {json.dumps(self.config.locales)},
    translations: {json.dumps(self._translations)},
    
    get: function() {{
        return this.current;
    }},
    
    set: function(locale) {{
        if (!this.available.includes(locale)) return;
        this.current = locale;
        this._updateDOM();
        
        // Persist to cookie
        document.cookie = "{self.config.cookie_name}=" + locale + "; path=/; max-age=31536000";
    }},
    
    t: function(key, params) {{
        let value = this.translations[this.current]?.[key] 
                 || this.translations["{self.config.fallback_locale or self.config.default_locale}"]?.[key] 
                 || key;
        
        if (params) {{
            for (const [k, v] of Object.entries(params)) {{
                value = value.replace(new RegExp('{{' + k + '}}', 'g'), v);
            }}
        }}
        return value;
    }},
    
    _updateDOM: function() {{
        // Find all elements with data-i18n attribute
        document.querySelectorAll('[data-i18n]').forEach(el => {{
            const key = el.dataset.i18n;
            const params = el.dataset.i18nParams ? JSON.parse(el.dataset.i18nParams) : null;
            el.textContent = this.t(key, params);
        }});
        
        // Update html lang attribute
        document.documentElement.lang = this.current;
        
        // Dispatch event for custom handlers
        window.dispatchEvent(new CustomEvent('locale-change', {{ detail: this.current }}));
    }}
}};
"""


# Global locale signal
_locale_signal: Optional[LocaleSignal] = None
_config: Optional[LocaleConfig] = None


def configure_i18n(config: LocaleConfig) -> None:
    """Configure i18n globally."""
    global _config, _locale_signal
    _config = config
    _locale_signal = LocaleSignal(config.default_locale, config)


def get_config() -> LocaleConfig:
    """Get current i18n config."""
    global _config
    if _config is None:
        _config = LocaleConfig()
    return _config


def create_locale_signal(initial: Optional[str] = None) -> LocaleSignal:
    """Create or get the locale signal."""
    global _locale_signal, _config
    
    if _config is None:
        _config = LocaleConfig()
    
    if _locale_signal is None:
        _locale_signal = LocaleSignal(
            initial or _config.default_locale,
            _config
        )
    elif initial is not None:
        _locale_signal.set(initial)
    
    return _locale_signal


def use_locale() -> LocaleSignal:
    """
    Get the locale signal for reactive locale access.
    
    Example:
        locale = use_locale()
        
        # In a component
        return div(
            h1(t("welcome")),
            button(
                t("switch_language"),
                onclick=lambda: locale.set_locale("fr")
            )
        )
    """
    return create_locale_signal()


def get_locale() -> str:
    """Get the current locale code."""
    return create_locale_signal().get()


def set_locale(locale: str) -> None:
    """Set the current locale."""
    create_locale_signal().set_locale(locale)


def t(
    key: str,
    params: Optional[Dict[str, Any]] = None,
    default: Optional[str] = None
) -> str:
    """
    Translate a key to the current locale.
    
    Args:
        key: Translation key
        params: Optional parameters for interpolation
        default: Default value if key not found
    
    Example:
        # Simple
        t("hello")  # "Hello"
        
        # With parameters
        t("greeting", {"name": "Alice"})  # "Hello, Alice!"
        
        # With default
        t("unknown", default="Fallback")
    """
    signal = create_locale_signal()
    value = signal.get_translation(key, default)
    
    if params:
        for param_key, param_value in params.items():
            value = value.replace(f"{{{param_key}}}", str(param_value))
    
    return value


def t_element(
    key: str,
    params: Optional[Dict[str, Any]] = None,
    tag: str = "span"
) -> str:
    """
    Create a reactive translation element.
    
    Unlike t(), this creates an element with data-i18n attribute
    that will automatically update when locale changes.
    
    Example:
        t_element("welcome")  # <span data-i18n="welcome">Welcome</span>
    """
    value = t(key, params)
    
    attrs = f'data-i18n="{key}"'
    if params:
        attrs += f" data-i18n-params='{json.dumps(params)}'"
    
    return f'<{tag} {attrs}>{value}</{tag}>'


class LocaleProvider:
    """
    Context provider for locale in component trees.
    
    Wraps content with locale context for SSR.
    """
    
    def __init__(self, locale: str, children: Any):
        self.locale = locale
        self.children = children
        
        # Set locale for this render
        set_locale(locale)
    
    def render(self) -> str:
        """Render with locale context."""
        content = self.children
        if callable(content):
            content = content()
        if hasattr(content, "render"):
            content = content.render()
        
        return f'<div data-locale="{self.locale}" lang="{self.locale}">{content}</div>'


# Formatting functions

def format_number(
    value: Union[int, float],
    locale: Optional[str] = None,
    style: str = "decimal",
    **options
) -> str:
    """
    Format a number according to locale.
    
    Example:
        format_number(1234.56)  # "1,234.56" (en) or "1 234,56" (fr)
    """
    locale = locale or get_locale()
    
    # Simple formatting (use babel for full support)
    if style == "percent":
        return f"{value * 100:.0f}%"
    elif style == "currency":
        currency = options.get("currency", "USD")
        return f"{currency} {value:,.2f}"
    else:
        return f"{value:,}"


def format_date(
    value: datetime,
    locale: Optional[str] = None,
    format: str = "medium",
    **options
) -> str:
    """
    Format a date according to locale.
    
    Example:
        format_date(datetime.now())  # "Nov 25, 2024" (en)
    """
    locale = locale or get_locale()
    
    formats = {
        "short": "%m/%d/%y",
        "medium": "%b %d, %Y",
        "long": "%B %d, %Y",
        "full": "%A, %B %d, %Y",
    }
    
    fmt = formats.get(format, format)
    return value.strftime(fmt)


def format_currency(
    value: Union[int, float],
    currency: str = "USD",
    locale: Optional[str] = None,
    **options
) -> str:
    """
    Format a currency value.
    
    Example:
        format_currency(99.99)  # "$99.99"
    """
    symbols = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "JPY": "¥",
    }
    
    symbol = symbols.get(currency, currency)
    return f"{symbol}{value:,.2f}"


def format_relative_time(
    value: datetime,
    locale: Optional[str] = None,
    **options
) -> str:
    """
    Format relative time (e.g., "2 hours ago").
    
    Example:
        format_relative_time(datetime.now() - timedelta(hours=2))  # "2 hours ago"
    """
    from datetime import datetime as dt
    
    now = dt.now()
    diff = now - value
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"{days} day{'s' if days > 1 else ''} ago"
    else:
        return format_date(value, locale)

