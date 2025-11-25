"""
PyNext Internationalization (i18n) Module.

Provides signal-based i18n with:
- Reactive locale switching (text-only updates, no full re-render)
- Lazy locale loading
- Build-time string extraction
- Automatic locale detection

SolidJS Principles Applied:
- Fine-grained reactivity (only text nodes update on locale change)
- Lazy loading (load translations on demand)
- Compile-time optimization (extract strings at build time)
"""

from pynext.i18n.locale import (
    Locale,
    LocaleConfig,
    LocaleSignal,
    t,
    use_locale,
    get_locale,
    set_locale,
    create_locale_signal,
    LocaleProvider,
    format_number,
    format_date,
    format_currency,
    format_relative_time,
)

from pynext.i18n.translations import (
    Translation,
    TranslationLoader,
    load_translations,
    get_translation,
    register_translations,
)

from pynext.i18n.middleware import (
    LocaleMiddleware,
    detect_locale,
    add_locale_middleware,
)

__all__ = [
    # Locale
    "Locale",
    "LocaleConfig",
    "LocaleSignal",
    "t",
    "use_locale",
    "get_locale",
    "set_locale",
    "create_locale_signal",
    "LocaleProvider",
    # Formatting
    "format_number",
    "format_date",
    "format_currency",
    "format_relative_time",
    # Translations
    "Translation",
    "TranslationLoader",
    "load_translations",
    "get_translation",
    "register_translations",
    # Middleware
    "LocaleMiddleware",
    "detect_locale",
    "add_locale_middleware",
]

