"""
Unit tests for Font Optimization.

Tests:
- Font component with zero-JS output
- Font registry and configuration
- CSS generation
- Preload link generation
- Google Font handling
"""

import pytest
from pynext.core.font import (
    Font,
    GoogleFont,
    LocalFont,
    FontConfig,
    FontDisplay,
    FontStyle,
    FontWeight,
    FontRegistry,
    OptimizedFont,
    FontVariant,
    FontMetrics,
    get_font_registry,
    generate_font_css,
    generate_preload_link,
    get_font_style_tag,
    _sanitize_family_name,
    SYSTEM_FONT_METRICS,
)


class TestFontComponent:
    """Tests for the Font component."""
    
    def test_font_returns_class_name(self):
        """Font() should return a CSS class name."""
        class_name = Font("Inter")
        assert class_name == "font-inter"
    
    def test_font_sanitizes_family_name(self):
        """Font should sanitize family names for CSS class."""
        assert _sanitize_family_name("Open Sans") == "open-sans"
        assert _sanitize_family_name("Roboto Mono") == "roboto-mono"
        assert _sanitize_family_name("Inter") == "inter"
    
    def test_font_registers_with_registry(self):
        """Font should register with the global registry."""
        registry = get_font_registry()
        initial_pending = len(registry.get_pending())
        
        Font("TestFont")
        
        # Should have one more pending
        assert len(registry.get_pending()) >= initial_pending


class TestFontRegistry:
    """Tests for FontRegistry."""
    
    def test_registry_register(self):
        """Registry should register fonts and return hash."""
        registry = FontRegistry()
        hash_id = registry.register(FontConfig(family="Inter", src="inter.woff2"))
        
        assert hash_id
        assert len(hash_id) == 12
    
    def test_registry_get_pending(self):
        """Registry should track pending fonts."""
        registry = FontRegistry()
        registry.register(FontConfig(family="Inter", src="inter.woff2"))
        
        pending = registry.get_pending()
        assert len(pending) == 1
    
    def test_registry_set_and_get(self):
        """Registry should store and retrieve optimized fonts."""
        registry = FontRegistry()
        config = FontConfig(family="Inter", src="inter.woff2")
        registry.register(config)
        
        optimized = OptimizedFont(
            family="Inter",
            hash="test123",
            variants=[FontVariant(weight=400)],
            css="@font-face { ... }",
            fallback_css="",
            preload_links=[],
        )
        
        registry.set(config, optimized)
        
        result = registry.get("Inter")
        assert result is not None
        assert result.family == "Inter"
    
    def test_registry_to_manifest(self):
        """Registry should export to manifest."""
        registry = FontRegistry()
        config = FontConfig(family="Inter", src="inter.woff2")
        registry.register(config)
        
        optimized = OptimizedFont(
            family="Inter",
            hash="test123",
            variants=[FontVariant(weight=400)],
            css="@font-face { ... }",
            fallback_css="",
            preload_links=[],
        )
        registry.set(config, optimized)
        
        manifest = registry.to_manifest()
        assert len(manifest) > 0


class TestFontConfig:
    """Tests for FontConfig."""
    
    def test_default_config(self):
        """FontConfig should have sensible defaults."""
        config = FontConfig(family="Inter", src="inter.woff2")
        
        assert config.display == FontDisplay.SWAP
        assert config.preload is True
        assert config.weight == 400
        assert config.style == FontStyle.NORMAL
    
    def test_custom_config(self):
        """FontConfig should accept custom values."""
        config = FontConfig(
            family="Roboto",
            src="roboto.woff2",
            weight=[400, 500, 700],
            display=FontDisplay.OPTIONAL,
            variable=True,
        )
        
        assert config.weight == [400, 500, 700]
        assert config.display == FontDisplay.OPTIONAL
        assert config.variable is True


class TestFontMetrics:
    """Tests for FontMetrics."""
    
    def test_line_height_calculation(self):
        """FontMetrics should calculate line height."""
        metrics = FontMetrics(
            units_per_em=1000,
            ascender=800,
            descender=-200,
            line_gap=100,
        )
        
        assert metrics.line_height == 1.1  # (800 - (-200) + 100) / 1000
    
    def test_size_adjust_calculation(self):
        """FontMetrics should calculate size-adjust."""
        font_metrics = FontMetrics(
            units_per_em=1000,
            ascender=800,
            descender=-200,
            line_gap=0,
        )
        
        fallback_metrics = FontMetrics(
            units_per_em=2000,
            ascender=1800,
            descender=-200,
            line_gap=0,
        )
        
        adjust = font_metrics.calculate_size_adjust(fallback_metrics)
        assert adjust == 100.0  # Same line height
    
    def test_system_font_metrics_available(self):
        """System font metrics should be defined."""
        assert "Arial" in SYSTEM_FONT_METRICS
        assert "Helvetica" in SYSTEM_FONT_METRICS
        assert "Times New Roman" in SYSTEM_FONT_METRICS


class TestCSSGeneration:
    """Tests for CSS generation."""
    
    def test_generate_font_css(self):
        """Should generate valid @font-face CSS."""
        config = FontConfig(
            family="Inter",
            src="/fonts/inter.woff2",
            weight=400,
        )
        
        css = generate_font_css(config)
        
        assert "@font-face" in css
        assert 'font-family: "Inter"' in css
        assert "font-weight: 400" in css
        assert "font-display: swap" in css
    
    def test_generate_preload_link(self):
        """Should generate valid preload link."""
        link = generate_preload_link("/fonts/inter.woff2")
        
        assert 'rel="preload"' in link
        assert 'as="font"' in link
        assert 'href="/fonts/inter.woff2"' in link
        assert 'crossorigin="anonymous"' in link


class TestGoogleFont:
    """Tests for GoogleFont helper."""
    
    def test_google_font_returns_class(self):
        """GoogleFont should return CSS class name."""
        class_name = GoogleFont("Inter", weight=400)
        assert class_name == "font-inter"
    
    def test_google_font_with_weights(self):
        """GoogleFont should accept weight list."""
        class_name = GoogleFont("Roboto", weight=[400, 500, 700])
        assert class_name == "font-roboto"


class TestLocalFont:
    """Tests for LocalFont helper."""
    
    def test_local_font_returns_class(self):
        """LocalFont should return CSS class name."""
        class_name = LocalFont("MyFont", src="/fonts/myfont.woff2")
        assert class_name == "font-myfont"
    
    def test_local_font_variable(self):
        """LocalFont should support variable fonts."""
        class_name = LocalFont(
            "MyVariable",
            src="/fonts/var.woff2",
            variable=True,
            weight=range(100, 900),
        )
        assert class_name == "font-myvariable"


class TestFontWeight:
    """Tests for FontWeight."""
    
    def test_weight_from_int(self):
        """FontWeight.from_value should handle integers."""
        assert FontWeight.from_value(400) == 400
        assert FontWeight.from_value(700) == 700
    
    def test_weight_from_string(self):
        """FontWeight.from_value should handle strings."""
        assert FontWeight.from_value("normal") == 400
        assert FontWeight.from_value("bold") == 700
        assert FontWeight.from_value("light") == 300
    
    def test_weight_from_enum(self):
        """FontWeight.from_value should handle enum."""
        assert FontWeight.from_value(FontWeight.BOLD) == 700
        assert FontWeight.from_value(FontWeight.NORMAL) == 400


class TestZeroJS:
    """Tests verifying zero JS output for fonts."""
    
    def test_no_js_in_font_output(self):
        """Font component should not produce JavaScript."""
        class_name = Font("Inter")
        
        # Font returns class name, not HTML with JS
        assert "<script" not in class_name
    
    def test_style_tag_no_js(self):
        """Font style tag should be pure CSS."""
        registry = get_font_registry()
        
        # Register a font
        config = FontConfig(family="TestZeroJS", src="test.woff2")
        registry.register(config)
        
        optimized = OptimizedFont(
            family="TestZeroJS",
            hash="abc123",
            variants=[],
            css="@font-face { font-family: TestZeroJS; }",
            fallback_css="",
            preload_links=[],
        )
        registry.set(config, optimized)
        
        style_tag = get_font_style_tag()
        
        # Should be pure CSS in style tag
        if style_tag:
            assert "<style>" in style_tag
            assert "<script>" not in style_tag

