"""
PyNext Translation Loading and Management.

Supports:
- JSON/YAML translation files
- Lazy loading per locale
- Namespace organization
- Plural forms
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union
import asyncio


@dataclass
class Translation:
    """Represents a single translation entry."""
    key: str
    value: str
    locale: str
    namespace: str = "common"
    
    # Plural forms
    plural_forms: Optional[Dict[str, str]] = None
    
    def get_value(self, count: Optional[int] = None) -> str:
        """Get value with optional plural form selection."""
        if count is not None and self.plural_forms:
            if count == 0 and "zero" in self.plural_forms:
                return self.plural_forms["zero"]
            elif count == 1 and "one" in self.plural_forms:
                return self.plural_forms["one"]
            elif count == 2 and "two" in self.plural_forms:
                return self.plural_forms["two"]
            elif "few" in self.plural_forms and 2 < count < 5:
                return self.plural_forms["few"]
            elif "many" in self.plural_forms:
                return self.plural_forms["many"]
            elif "other" in self.plural_forms:
                return self.plural_forms["other"]
        return self.value


class TranslationLoader:
    """
    Loads translations from files.
    
    Supports lazy loading to only load translations when needed.
    """
    
    def __init__(self, base_path: Union[str, Path]):
        self.base_path = Path(base_path)
        self._cache: Dict[str, Dict[str, str]] = {}
        self._loading: Dict[str, asyncio.Task] = {}
    
    def load_sync(self, locale: str, namespace: str = "common") -> Dict[str, str]:
        """Load translations synchronously."""
        cache_key = f"{locale}:{namespace}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Try different file formats
        for ext in [".json", ".yaml", ".yml"]:
            file_path = self.base_path / locale / f"{namespace}{ext}"
            if file_path.exists():
                translations = self._load_file(file_path)
                self._cache[cache_key] = translations
                return translations
        
        # Try single file per locale
        for ext in [".json", ".yaml", ".yml"]:
            file_path = self.base_path / f"{locale}{ext}"
            if file_path.exists():
                translations = self._load_file(file_path)
                self._cache[cache_key] = translations
                return translations
        
        return {}
    
    async def load_async(self, locale: str, namespace: str = "common") -> Dict[str, str]:
        """Load translations asynchronously (for lazy loading)."""
        cache_key = f"{locale}:{namespace}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        if cache_key in self._loading:
            return await self._loading[cache_key]
        
        # Start loading
        task = asyncio.create_task(self._load_async_impl(locale, namespace))
        self._loading[cache_key] = task
        
        try:
            return await task
        finally:
            del self._loading[cache_key]
    
    async def _load_async_impl(self, locale: str, namespace: str) -> Dict[str, str]:
        """Implementation of async loading."""
        # Run sync loading in executor
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.load_sync,
            locale,
            namespace
        )
    
    def _load_file(self, path: Path) -> Dict[str, str]:
        """Load translations from a file."""
        content = path.read_text(encoding="utf-8")
        
        if path.suffix == ".json":
            data = json.loads(content)
        elif path.suffix in (".yaml", ".yml"):
            try:
                import yaml
                data = yaml.safe_load(content)
            except ImportError:
                # Fallback to simple YAML parsing
                data = self._parse_simple_yaml(content)
        else:
            return {}
        
        # Flatten nested keys
        return self._flatten_dict(data)
    
    def _flatten_dict(
        self,
        data: Dict[str, Any],
        prefix: str = ""
    ) -> Dict[str, str]:
        """Flatten nested dictionary to dot-notation keys."""
        result = {}
        
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                # Check if it's plural forms
                if set(value.keys()) & {"zero", "one", "two", "few", "many", "other"}:
                    result[full_key] = value.get("other", value.get("one", str(value)))
                    # Store plural forms separately
                    result[f"{full_key}._plural"] = json.dumps(value)
                else:
                    result.update(self._flatten_dict(value, full_key))
            else:
                result[full_key] = str(value)
        
        return result
    
    def _parse_simple_yaml(self, content: str) -> Dict[str, Any]:
        """Simple YAML parser for basic translation files."""
        result = {}
        current_key = None
        current_indent = 0
        
        for line in content.split("\n"):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            
            indent = len(line) - len(line.lstrip())
            
            if ":" in stripped:
                key, _, value = stripped.partition(":")
                key = key.strip()
                value = value.strip().strip('"\'')
                
                if value:
                    result[key] = value
                else:
                    result[key] = {}
                    current_key = key
                    current_indent = indent
        
        return result
    
    def preload_locales(self, locales: List[str], namespaces: List[str] = None) -> None:
        """Preload multiple locales synchronously."""
        namespaces = namespaces or ["common"]
        
        for locale in locales:
            for namespace in namespaces:
                self.load_sync(locale, namespace)
    
    def get_loaded_locales(self) -> List[str]:
        """Get list of loaded locales."""
        locales = set()
        for key in self._cache:
            locale, _ = key.split(":", 1)
            locales.add(locale)
        return list(locales)
    
    def clear_cache(self) -> None:
        """Clear translation cache."""
        self._cache.clear()


# Global translation state
_loader: Optional[TranslationLoader] = None
_translations: Dict[str, Dict[str, str]] = {}


def init_translations(base_path: Union[str, Path]) -> TranslationLoader:
    """Initialize the translation loader."""
    global _loader
    _loader = TranslationLoader(base_path)
    return _loader


def get_loader() -> TranslationLoader:
    """Get the translation loader."""
    global _loader
    if _loader is None:
        _loader = TranslationLoader(Path("locales"))
    return _loader


def load_translations(
    locale: str,
    namespace: str = "common"
) -> Dict[str, str]:
    """Load translations for a locale."""
    loader = get_loader()
    translations = loader.load_sync(locale, namespace)
    
    # Register with locale signal
    from pynext.i18n.locale import create_locale_signal
    signal = create_locale_signal()
    
    # Merge with existing translations
    if locale not in _translations:
        _translations[locale] = {}
    _translations[locale].update(translations)
    
    signal.load_translations(locale, _translations[locale])
    
    return translations


async def load_translations_async(
    locale: str,
    namespace: str = "common"
) -> Dict[str, str]:
    """Load translations asynchronously."""
    loader = get_loader()
    translations = await loader.load_async(locale, namespace)
    
    from pynext.i18n.locale import create_locale_signal
    signal = create_locale_signal()
    
    if locale not in _translations:
        _translations[locale] = {}
    _translations[locale].update(translations)
    
    signal.load_translations(locale, _translations[locale])
    
    return translations


def get_translation(
    key: str,
    locale: Optional[str] = None,
    namespace: str = "common"
) -> Optional[str]:
    """Get a specific translation."""
    from pynext.i18n.locale import get_locale
    
    locale = locale or get_locale()
    
    if locale in _translations:
        return _translations[locale].get(key)
    
    # Try loading
    load_translations(locale, namespace)
    
    if locale in _translations:
        return _translations[locale].get(key)
    
    return None


def register_translations(locale: str, translations: Dict[str, str]) -> None:
    """Register translations directly (without loading from file)."""
    from pynext.i18n.locale import create_locale_signal
    
    if locale not in _translations:
        _translations[locale] = {}
    _translations[locale].update(translations)
    
    signal = create_locale_signal()
    signal.load_translations(locale, _translations[locale])


def get_all_translations() -> Dict[str, Dict[str, str]]:
    """Get all loaded translations."""
    return _translations.copy()

