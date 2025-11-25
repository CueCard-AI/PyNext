"""
Tests for PyNext Internationalization (i18n).
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
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
    configure_i18n,
)
from pynext.i18n.translations import (
    Translation,
    TranslationLoader,
    load_translations,
    register_translations,
    get_all_translations,
)
from pynext.i18n.middleware import detect_locale


class TestLocale:
    """Tests for Locale class."""
    
    def test_locale_creation(self):
        """Test locale object creation."""
        locale = Locale("en", "English", "ltr")
        
        assert locale.code == "en"
        assert locale.name == "English"
        assert locale.direction == "ltr"
    
    def test_locale_string(self):
        """Test locale string representation."""
        locale = Locale("fr", "French")
        
        assert str(locale) == "fr"
    
    def test_locale_equality(self):
        """Test locale equality comparisons."""
        locale = Locale("en")
        
        assert locale == "en"
        assert locale == Locale("en")
        assert locale != "fr"
    
    def test_locale_hash(self):
        """Test locale hashing for use in sets/dicts."""
        locales = {Locale("en"), Locale("fr"), Locale("en")}
        
        assert len(locales) == 2


class TestLocaleConfig:
    """Tests for LocaleConfig."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = LocaleConfig()
        
        assert "en" in config.locales
        assert config.default_locale == "en"
        assert config.locale_detection is True
        assert config.strategy == "prefix"
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = LocaleConfig(
            locales=["en", "fr", "de"],
            default_locale="fr",
            fallback_locale="en",
        )
        
        assert len(config.locales) == 3
        assert config.default_locale == "fr"
        assert config.fallback_locale == "en"


class TestLocaleSignal:
    """Tests for LocaleSignal."""
    
    def test_signal_creation(self):
        """Test locale signal creation."""
        config = LocaleConfig(locales=["en", "fr"])
        signal = LocaleSignal("en", config)
        
        assert signal.get() == "en"
    
    def test_set_locale(self):
        """Test setting locale."""
        config = LocaleConfig(locales=["en", "fr", "de"])
        signal = LocaleSignal("en", config)
        
        signal.set_locale("fr")
        assert signal.get() == "fr"
    
    def test_set_invalid_locale(self):
        """Test setting invalid locale falls back to default."""
        config = LocaleConfig(
            locales=["en", "fr"],
            default_locale="en",
            fallback_locale="en",
        )
        signal = LocaleSignal("en", config)
        
        signal.set_locale("invalid")
        # Should remain or fallback
        assert signal.get() in config.locales
    
    def test_load_translations(self):
        """Test loading translations into signal."""
        config = LocaleConfig(locales=["en", "fr"])
        signal = LocaleSignal("en", config)
        
        signal.load_translations("en", {"hello": "Hello", "goodbye": "Goodbye"})
        signal.load_translations("fr", {"hello": "Bonjour", "goodbye": "Au revoir"})
        
        assert signal.get_translation("hello") == "Hello"
        
        signal.set_locale("fr")
        assert signal.get_translation("hello") == "Bonjour"
    
    def test_translation_fallback(self):
        """Test translation fallback to another locale."""
        config = LocaleConfig(
            locales=["en", "fr"],
            default_locale="en",
            fallback_locale="en",
        )
        signal = LocaleSignal("fr", config)
        
        signal.load_translations("en", {"hello": "Hello", "only_en": "English only"})
        signal.load_translations("fr", {"hello": "Bonjour"})
        
        # French translation exists
        assert signal.get_translation("hello") == "Bonjour"
        
        # Falls back to English
        assert signal.get_translation("only_en") == "English only"
    
    def test_js_init(self):
        """Test JavaScript initialization code generation."""
        config = LocaleConfig(locales=["en", "fr"])
        signal = LocaleSignal("en", config)
        signal.load_translations("en", {"hello": "Hello"})
        
        js = signal.get_js_init()
        
        assert "__pynext__.locale" in js
        assert '"en"' in js
        assert "translations" in js


class TestTranslationFunction:
    """Tests for t() translation function."""
    
    def setup_method(self):
        """Set up translations for tests."""
        configure_i18n(LocaleConfig(locales=["en", "fr"], default_locale="en"))
        register_translations("en", {
            "hello": "Hello",
            "greeting": "Hello, {name}!",
            "items": "You have {count} items",
        })
        register_translations("fr", {
            "hello": "Bonjour",
            "greeting": "Bonjour, {name}!",
        })
        set_locale("en")
    
    def test_simple_translation(self):
        """Test simple translation."""
        result = t("hello")
        assert result == "Hello"
    
    def test_translation_with_params(self):
        """Test translation with parameters."""
        result = t("greeting", {"name": "Alice"})
        assert result == "Hello, Alice!"
    
    def test_missing_translation_returns_key(self):
        """Test missing translation returns key."""
        result = t("nonexistent")
        assert result == "nonexistent"
    
    def test_translation_with_default(self):
        """Test translation with default value."""
        result = t("nonexistent", default="Default text")
        assert result == "Default text"
    
    def test_translation_locale_switch(self):
        """Test translation after locale switch."""
        set_locale("en")
        assert t("hello") == "Hello"
        
        set_locale("fr")
        assert t("hello") == "Bonjour"


class TestFormatting:
    """Tests for formatting functions."""
    
    def test_format_number(self):
        """Test number formatting."""
        result = format_number(1234567.89)
        
        # Should have thousand separators
        assert "," in result or " " in result
    
    def test_format_number_percent(self):
        """Test percent formatting."""
        result = format_number(0.75, style="percent")
        
        assert "75" in result
        assert "%" in result
    
    def test_format_date(self):
        """Test date formatting."""
        date = datetime(2024, 11, 25)
        result = format_date(date)
        
        assert "Nov" in result or "11" in result
        assert "2024" in result
    
    def test_format_date_formats(self):
        """Test different date formats."""
        date = datetime(2024, 11, 25)
        
        short = format_date(date, format="short")
        medium = format_date(date, format="medium")
        long_fmt = format_date(date, format="long")
        
        # All should contain year info
        assert "24" in short or "2024" in short
        assert "2024" in medium
        assert "2024" in long_fmt
    
    def test_format_currency(self):
        """Test currency formatting."""
        result = format_currency(99.99, "USD")
        
        assert "$" in result
        assert "99.99" in result
    
    def test_format_currency_different_currencies(self):
        """Test different currencies."""
        usd = format_currency(100, "USD")
        eur = format_currency(100, "EUR")
        gbp = format_currency(100, "GBP")
        
        assert "$" in usd
        assert "€" in eur
        assert "£" in gbp
    
    def test_format_relative_time_just_now(self):
        """Test relative time for recent times."""
        now = datetime.now()
        result = format_relative_time(now - timedelta(seconds=30))
        
        assert "just now" in result.lower()
    
    def test_format_relative_time_minutes(self):
        """Test relative time for minutes ago."""
        now = datetime.now()
        result = format_relative_time(now - timedelta(minutes=5))
        
        assert "minute" in result.lower()
    
    def test_format_relative_time_hours(self):
        """Test relative time for hours ago."""
        now = datetime.now()
        result = format_relative_time(now - timedelta(hours=3))
        
        assert "hour" in result.lower()


class TestLocaleProvider:
    """Tests for LocaleProvider component."""
    
    def test_provider_renders_children(self):
        """Test provider renders children."""
        provider = LocaleProvider("en", "<div>Content</div>")
        html = provider.render()
        
        assert "<div>Content</div>" in html
    
    def test_provider_sets_lang_attribute(self):
        """Test provider sets lang attribute."""
        provider = LocaleProvider("fr", "<span>Test</span>")
        html = provider.render()
        
        assert 'lang="fr"' in html
        assert 'data-locale="fr"' in html


class TestTranslationLoader:
    """Tests for TranslationLoader."""
    
    def test_loader_creation(self, tmp_path):
        """Test loader creation."""
        loader = TranslationLoader(tmp_path)
        
        assert loader.base_path == tmp_path
    
    def test_load_json_file(self, tmp_path):
        """Test loading JSON translation file."""
        # Create translation file
        en_dir = tmp_path / "en"
        en_dir.mkdir()
        (en_dir / "common.json").write_text('{"hello": "Hello", "world": "World"}')
        
        loader = TranslationLoader(tmp_path)
        translations = loader.load_sync("en", "common")
        
        assert translations["hello"] == "Hello"
        assert translations["world"] == "World"
    
    def test_load_nested_keys(self, tmp_path):
        """Test loading nested translation keys."""
        en_dir = tmp_path / "en"
        en_dir.mkdir()
        (en_dir / "common.json").write_text('''
        {
            "buttons": {
                "submit": "Submit",
                "cancel": "Cancel"
            }
        }
        ''')
        
        loader = TranslationLoader(tmp_path)
        translations = loader.load_sync("en", "common")
        
        assert translations["buttons.submit"] == "Submit"
        assert translations["buttons.cancel"] == "Cancel"
    
    def test_caching(self, tmp_path):
        """Test translation caching."""
        en_dir = tmp_path / "en"
        en_dir.mkdir()
        (en_dir / "common.json").write_text('{"test": "Test"}')
        
        loader = TranslationLoader(tmp_path)
        
        # First load
        t1 = loader.load_sync("en", "common")
        
        # Second load (should be cached)
        t2 = loader.load_sync("en", "common")
        
        assert t1 == t2
    
    def test_preload_locales(self, tmp_path):
        """Test preloading multiple locales."""
        for locale in ["en", "fr"]:
            locale_dir = tmp_path / locale
            locale_dir.mkdir()
            (locale_dir / "common.json").write_text(f'{{"lang": "{locale}"}}')
        
        loader = TranslationLoader(tmp_path)
        loader.preload_locales(["en", "fr"])
        
        loaded = loader.get_loaded_locales()
        assert "en" in loaded
        assert "fr" in loaded


class TestLocaleDetection:
    """Tests for locale detection."""
    
    def test_detect_from_accept_language(self):
        """Test detecting locale from Accept-Language header."""
        result = detect_locale(
            "en-US,en;q=0.9,fr;q=0.8",
            ["en", "fr", "de"],
            "en"
        )
        
        assert result == "en"
    
    def test_detect_second_preference(self):
        """Test detecting second preference locale."""
        result = detect_locale(
            "de-DE,de;q=0.9,fr;q=0.8",
            ["en", "fr"],  # de not available
            "en"
        )
        
        assert result == "fr"
    
    def test_detect_fallback_to_default(self):
        """Test fallback to default when no match."""
        result = detect_locale(
            "zh-CN,zh;q=0.9",
            ["en", "fr"],
            "en"
        )
        
        assert result == "en"
    
    def test_detect_empty_header(self):
        """Test detection with empty header."""
        result = detect_locale("", ["en", "fr"], "fr")
        
        assert result == "fr"
    
    def test_detect_malformed_header(self):
        """Test detection with malformed header."""
        result = detect_locale(
            "en;q=abc,fr",
            ["en", "fr"],
            "en"
        )
        
        # Should still work
        assert result in ["en", "fr"]


class TestRegistration:
    """Tests for translation registration."""
    
    def test_register_translations(self):
        """Test direct translation registration."""
        configure_i18n(LocaleConfig(locales=["en"]))
        register_translations("en", {"test_key": "Test Value"})
        
        all_trans = get_all_translations()
        assert "en" in all_trans
        assert all_trans["en"]["test_key"] == "Test Value"

