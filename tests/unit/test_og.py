"""
Unit tests for OG Image generation.

Tests cover:
- OGCanvas and elements
- OGTemplate and presets
- @og_image decorator
- OGRenderer
- Integration tests
"""

import pytest
from pathlib import Path
import tempfile


# ============================================
# OGCanvas Tests (12 tests)
# ============================================

class TestOGCanvas:
    """Tests for OGCanvas."""
    
    def test_create_default_canvas(self):
        """Test creating canvas with defaults."""
        from pynext.og import OGCanvas
        
        canvas = OGCanvas()
        
        assert canvas.width == 1200
        assert canvas.height == 630
        assert canvas.background == "#ffffff"
        assert canvas.quality == 90
    
    def test_create_custom_canvas(self):
        """Test creating canvas with custom values."""
        from pynext.og import OGCanvas
        
        canvas = OGCanvas(
            width=800,
            height=400,
            background="#000000",
            quality=85,
        )
        
        assert canvas.width == 800
        assert canvas.height == 400
        assert canvas.background == "#000000"
        assert canvas.quality == 85
    
    def test_invalid_dimensions_raises(self):
        """Test invalid dimensions raise error."""
        from pynext.og import OGCanvas
        
        with pytest.raises(ValueError):
            OGCanvas(width=0, height=630)
        
        with pytest.raises(ValueError):
            OGCanvas(width=1200, height=-1)
    
    def test_invalid_quality_raises(self):
        """Test invalid quality raises error."""
        from pynext.og import OGCanvas
        
        with pytest.raises(ValueError):
            OGCanvas(quality=0)
        
        with pytest.raises(ValueError):
            OGCanvas(quality=101)
    
    def test_add_text(self):
        """Test adding text element."""
        from pynext.og import OGCanvas
        
        canvas = OGCanvas()
        result = canvas.add_text("Hello", x=60, y=200, font_size=48)
        
        assert result is canvas  # Chainable
        assert len(canvas.elements) == 1
        assert canvas.elements[0].text == "Hello"
        assert canvas.elements[0].x == 60
        assert canvas.elements[0].y == 200
    
    def test_add_image(self):
        """Test adding image element."""
        from pynext.og import OGCanvas
        
        canvas = OGCanvas()
        canvas.add_image("avatar.png", x=60, y=400, width=80, height=80)
        
        assert len(canvas.elements) == 1
        assert canvas.elements[0].src == "avatar.png"
        assert canvas.elements[0].width == 80
    
    def test_add_rect(self):
        """Test adding rectangle element."""
        from pynext.og import OGCanvas
        
        canvas = OGCanvas()
        canvas.add_rect(x=0, y=500, width=1200, height=130, color="#000000")
        
        assert len(canvas.elements) == 1
        assert canvas.elements[0].width == 1200
        assert canvas.elements[0].color == "#000000"
    
    def test_chaining(self):
        """Test method chaining."""
        from pynext.og import OGCanvas
        
        canvas = (
            OGCanvas(background="gradient:blue")
            .add_text("Title", x=60, y=200)
            .add_text("Subtitle", x=60, y=280)
            .add_rect(x=0, y=500, width=1200, height=130)
        )
        
        assert len(canvas.elements) == 3
    
    def test_clear(self):
        """Test clearing elements."""
        from pynext.og import OGCanvas
        
        canvas = OGCanvas().add_text("Hello", x=0, y=0)
        assert len(canvas.elements) == 1
        
        canvas.clear()
        assert len(canvas.elements) == 0
    
    def test_to_dict(self):
        """Test converting to dictionary."""
        from pynext.og import OGCanvas
        
        canvas = OGCanvas().add_text("Hello", x=60, y=200)
        d = canvas.to_dict()
        
        assert d["width"] == 1200
        assert d["height"] == 630
        assert len(d["elements"]) == 1
        assert d["elements"][0]["type"] == "text"
    
    def test_clone(self):
        """Test cloning canvas."""
        from pynext.og import OGCanvas
        
        original = OGCanvas(background="#ff0000").add_text("Hello", x=0, y=0)
        clone = original.clone()
        
        assert clone.background == original.background
        assert len(clone.elements) == len(original.elements)
        assert clone is not original
    
    def test_gradient_background(self):
        """Test gradient background."""
        from pynext.og import OGCanvas
        
        canvas = OGCanvas(background="gradient:blue")
        
        assert canvas.background == "gradient:blue"


# ============================================
# Element Tests (8 tests)
# ============================================

class TestElements:
    """Tests for element types."""
    
    def test_text_element_defaults(self):
        """Test TextElement defaults."""
        from pynext.og.canvas import TextElement
        
        el = TextElement(text="Hello", x=0, y=0)
        
        assert el.font_size == 32
        assert el.font_weight == "normal"
        assert el.color == "#000000"
        assert el.align == "left"
    
    def test_text_element_to_dict(self):
        """Test TextElement to_dict."""
        from pynext.og.canvas import TextElement
        
        el = TextElement(text="Hello", x=60, y=200, font_size=48, font_weight="bold")
        d = el.to_dict()
        
        assert d["type"] == "text"
        assert d["text"] == "Hello"
        assert d["font_size"] == 48
        assert d["font_weight"] == "bold"
    
    def test_image_element_defaults(self):
        """Test ImageElement defaults."""
        from pynext.og.canvas import ImageElement
        
        el = ImageElement(src="img.png", x=0, y=0, width=100, height=100)
        
        assert el.border_radius == 0
        assert el.object_fit == "cover"
    
    def test_image_element_to_dict(self):
        """Test ImageElement to_dict."""
        from pynext.og.canvas import ImageElement
        
        el = ImageElement(src="img.png", x=60, y=400, width=80, height=80, border_radius=40)
        d = el.to_dict()
        
        assert d["type"] == "image"
        assert d["src"] == "img.png"
        assert d["border_radius"] == 40
    
    def test_rect_element_defaults(self):
        """Test RectElement defaults."""
        from pynext.og.canvas import RectElement
        
        el = RectElement(x=0, y=0, width=100, height=100)
        
        assert el.color == "#000000"
        assert el.opacity == 1.0
    
    def test_rect_element_to_dict(self):
        """Test RectElement to_dict."""
        from pynext.og.canvas import RectElement
        
        el = RectElement(x=0, y=500, width=1200, height=130, color="#ffffff", opacity=0.5)
        d = el.to_dict()
        
        assert d["type"] == "rect"
        assert d["opacity"] == 0.5
    
    def test_text_element_max_width(self):
        """Test TextElement with max_width."""
        from pynext.og.canvas import TextElement
        
        el = TextElement(text="Long text", x=0, y=0, max_width=500)
        
        assert el.max_width == 500
    
    def test_image_element_object_fit(self):
        """Test ImageElement object_fit options."""
        from pynext.og.canvas import ImageElement
        
        for fit in ["cover", "contain", "fill"]:
            el = ImageElement(src="img.png", x=0, y=0, width=100, height=100, object_fit=fit)
            assert el.object_fit == fit


# ============================================
# OGTemplate Tests (10 tests)
# ============================================

class TestOGTemplate:
    """Tests for OGTemplate."""
    
    def test_default_template(self):
        """Test default template."""
        from pynext.og import OGTemplate
        
        template = OGTemplate()
        
        assert template.title == "{{title}}"
        assert template.background == "gradient:slate"
    
    def test_template_with_subtitle(self):
        """Test template with subtitle."""
        from pynext.og import OGTemplate
        
        template = OGTemplate(
            title="{{title}}",
            subtitle="{{date}} · {{category}}",
        )
        
        assert template.subtitle == "{{date}} · {{category}}"
    
    def test_interpolate_simple(self):
        """Test simple placeholder interpolation."""
        from pynext.og import OGTemplate
        
        template = OGTemplate(title="{{title}}")
        result = template._interpolate("Hello {{name}}", {"name": "World"})
        
        assert result == "Hello World"
    
    def test_interpolate_missing_key(self):
        """Test missing placeholder key."""
        from pynext.og import OGTemplate
        
        template = OGTemplate()
        result = template._interpolate("Hello {{name}}", {})
        
        assert result == "Hello {{name}}"
    
    def test_render_basic(self):
        """Test basic template rendering."""
        from pynext.og import OGTemplate
        
        template = OGTemplate(title="{{title}}")
        canvas = template.render({"title": "My Post"})
        
        assert len(canvas.elements) >= 1
        assert canvas.elements[0].text == "My Post"
    
    def test_render_with_subtitle(self):
        """Test rendering with subtitle."""
        from pynext.og import OGTemplate
        
        template = OGTemplate(
            title="{{title}}",
            subtitle="{{date}}",
        )
        canvas = template.render({"title": "Post", "date": "Jan 1"})
        
        assert len(canvas.elements) == 2
    
    def test_with_logo(self):
        """Test creating template with logo."""
        from pynext.og import OGTemplate
        
        template = OGTemplate().with_logo("logo.png")
        
        assert template.logo == "logo.png"
    
    def test_with_background(self):
        """Test creating template with different background."""
        from pynext.og import OGTemplate
        
        template = OGTemplate().with_background("gradient:blue")
        
        assert template.background == "gradient:blue"
    
    def test_resolve_gradient(self):
        """Test gradient resolution."""
        from pynext.og import OGTemplate
        
        template = OGTemplate(background="gradient:blue")
        resolved = template._resolve_background(template.background)
        
        assert "linear-gradient" in resolved
        assert "#3b82f6" in resolved
    
    def test_prebuilt_templates(self):
        """Test pre-built templates exist."""
        from pynext.og import templates
        
        assert templates.blog_post is not None
        assert templates.product is not None
        assert templates.profile is not None
        assert templates.minimal is not None


# ============================================
# Decorator Tests (8 tests)
# ============================================

class TestOGImageDecorator:
    """Tests for @og_image decorator."""
    
    def test_basic_decorator(self):
        """Test basic decorator usage."""
        from pynext import og_image
        
        @og_image()
        def page():
            pass
        
        assert hasattr(page, "_og_config")
    
    def test_decorator_with_template(self):
        """Test decorator with template."""
        from pynext import og_image, OGTemplate
        
        template = OGTemplate(title="Custom")
        
        @og_image(template=template)
        def page():
            pass
        
        assert page._og_config.template.title == "Custom"
    
    def test_decorator_with_cache(self):
        """Test decorator with cache settings."""
        from pynext import og_image
        
        @og_image(cache=86400)
        def page():
            pass
        
        assert page._og_config.cache == 86400
        assert page._og_config.cache_seconds == 86400
    
    def test_decorator_cache_disabled(self):
        """Test decorator with cache disabled."""
        from pynext import og_image
        
        @og_image(cache=False)
        def page():
            pass
        
        assert page._og_config.cache_seconds == 0
    
    def test_decorator_format(self):
        """Test decorator with format."""
        from pynext import og_image
        
        @og_image(format="jpeg", quality=85)
        def page():
            pass
        
        assert page._og_config.format == "jpeg"
        assert page._og_config.quality == 85
        assert page._og_config.media_type == "image/jpeg"
    
    def test_custom_og_handler(self):
        """Test custom OG handler."""
        from pynext import og_image, OGCanvas
        
        @og_image()
        def page():
            pass
        
        @page.og
        def custom_og():
            return OGCanvas()
        
        assert page._og_handler is custom_og
    
    def test_has_og_config(self):
        """Test has_og_config utility."""
        from pynext import og_image
        from pynext.og.decorator import has_og_config
        
        @og_image()
        def with_og():
            pass
        
        def without_og():
            pass
        
        assert has_og_config(with_og) is True
        assert has_og_config(without_og) is False
    
    def test_get_og_config(self):
        """Test get_og_config utility."""
        from pynext import og_image
        from pynext.og.decorator import get_og_config
        
        @og_image(cache=3600)
        def page():
            pass
        
        config = get_og_config(page)
        
        assert config is not None
        assert config.cache == 3600


# ============================================
# Renderer Tests (12 tests)
# ============================================

class TestOGRenderer:
    """Tests for OGRenderer."""
    
    @pytest.fixture
    def skip_if_no_pillow(self):
        """Skip test if Pillow not installed."""
        try:
            import PIL
        except ImportError:
            pytest.skip("Pillow not installed")
    
    def test_render_basic(self, skip_if_no_pillow):
        """Test basic rendering."""
        from pynext.og import OGCanvas, OGRenderer
        
        canvas = OGCanvas(background="#ffffff")
        renderer = OGRenderer()
        
        image_bytes = renderer.render(canvas)
        
        assert isinstance(image_bytes, bytes)
        assert len(image_bytes) > 0
        # PNG magic bytes
        assert image_bytes[:4] == b'\x89PNG'
    
    def test_render_with_text(self, skip_if_no_pillow):
        """Test rendering with text."""
        from pynext.og import OGCanvas, OGRenderer
        
        canvas = OGCanvas().add_text("Hello", x=60, y=200)
        renderer = OGRenderer()
        
        image_bytes = renderer.render(canvas)
        
        assert len(image_bytes) > 0
    
    def test_render_jpeg(self, skip_if_no_pillow):
        """Test rendering as JPEG."""
        from pynext.og import OGCanvas, OGRenderer
        
        canvas = OGCanvas()
        renderer = OGRenderer()
        
        image_bytes = renderer.render(canvas, format="jpeg")
        
        # JPEG magic bytes
        assert image_bytes[:2] == b'\xff\xd8'
    
    def test_render_gradient(self, skip_if_no_pillow):
        """Test rendering with gradient background."""
        from pynext.og import OGCanvas, OGRenderer
        
        canvas = OGCanvas(background="gradient:blue")
        renderer = OGRenderer()
        
        image_bytes = renderer.render(canvas)
        
        assert len(image_bytes) > 0
    
    def test_render_rect(self, skip_if_no_pillow):
        """Test rendering rectangles."""
        from pynext.og import OGCanvas, OGRenderer
        
        canvas = OGCanvas().add_rect(x=100, y=100, width=200, height=100, color="#ff0000")
        renderer = OGRenderer()
        
        image_bytes = renderer.render(canvas)
        
        assert len(image_bytes) > 0
    
    def test_render_multiple_elements(self, skip_if_no_pillow):
        """Test rendering multiple elements."""
        from pynext.og import OGCanvas, OGRenderer
        
        canvas = (
            OGCanvas(background="#1e293b")
            .add_text("Title", x=60, y=200, font_size=64, color="#ffffff")
            .add_text("Subtitle", x=60, y=300, color="#94a3b8")
            .add_rect(x=0, y=500, width=1200, height=130, color="#000000", opacity=0.5)
        )
        renderer = OGRenderer()
        
        image_bytes = renderer.render(canvas)
        
        assert len(image_bytes) > 0
    
    def test_parse_hex_color(self, skip_if_no_pillow):
        """Test hex color parsing."""
        from pynext.og.renderer import parse_color
        
        assert parse_color("#ffffff") == (255, 255, 255, 255)
        assert parse_color("#000000") == (0, 0, 0, 255)
        assert parse_color("#ff0000") == (255, 0, 0, 255)
        assert parse_color("#fff") == (255, 255, 255, 255)
    
    def test_parse_rgba_color(self, skip_if_no_pillow):
        """Test rgba color parsing."""
        from pynext.og.renderer import parse_color
        
        assert parse_color("rgba(255, 0, 0, 0.5)") == (255, 0, 0, 127)
        assert parse_color("rgb(128, 128, 128)") == (128, 128, 128, 255)
    
    def test_parse_named_color(self, skip_if_no_pillow):
        """Test named color parsing."""
        from pynext.og.renderer import parse_color
        
        assert parse_color("white") == (255, 255, 255, 255)
        assert parse_color("black") == (0, 0, 0, 255)
    
    def test_render_convenience(self, skip_if_no_pillow):
        """Test render_canvas convenience function."""
        from pynext.og import OGCanvas
        from pynext.og.renderer import render_canvas
        
        canvas = OGCanvas()
        image_bytes = render_canvas(canvas)
        
        assert len(image_bytes) > 0
    
    def test_save_canvas(self, skip_if_no_pillow):
        """Test save_canvas convenience function."""
        from pynext.og import OGCanvas
        from pynext.og.renderer import save_canvas
        
        with tempfile.TemporaryDirectory() as tmpdir:
            canvas = OGCanvas()
            path = Path(tmpdir) / "test.png"
            save_canvas(canvas, path)
            
            assert path.exists()
            assert path.stat().st_size > 0
    
    def test_text_wrapping(self, skip_if_no_pillow):
        """Test text wrapping."""
        from pynext.og import OGCanvas, OGRenderer
        
        long_text = "This is a very long title that should wrap to multiple lines when rendered"
        canvas = OGCanvas().add_text(long_text, x=60, y=200, max_width=500)
        renderer = OGRenderer()
        
        image_bytes = renderer.render(canvas)
        
        assert len(image_bytes) > 0


# ============================================
# Template Presets Tests (6 tests)
# ============================================

class TestTemplatePresets:
    """Tests for pre-built templates."""
    
    def test_blog_post_template(self):
        """Test blog_post template."""
        from pynext.og import templates
        
        canvas = templates.blog_post.render({
            "title": "My Blog Post",
            "date": "Jan 1, 2025",
            "category": "Tech",
        })
        
        assert len(canvas.elements) >= 1
    
    def test_product_template(self):
        """Test product template."""
        from pynext.og import templates
        
        canvas = templates.product.render({
            "name": "Product Name",
            "price": "$99.99",
        })
        
        assert len(canvas.elements) >= 1
    
    def test_profile_template(self):
        """Test profile template."""
        from pynext.og import templates
        
        canvas = templates.profile.render({
            "name": "John Doe",
            "bio": "Software Developer",
        })
        
        assert len(canvas.elements) >= 1
    
    def test_minimal_template(self):
        """Test minimal template."""
        from pynext.og import templates
        
        canvas = templates.minimal.render({
            "title": "Simple Title",
        })
        
        assert len(canvas.elements) == 1
    
    def test_create_template(self):
        """Test create_template factory."""
        from pynext.og.templates import create_template
        
        template = create_template(
            title="{{product}}",
            subtitle="Only {{price}}!",
            background="gradient:green",
        )
        
        assert template.title == "{{product}}"
        assert template.background == "gradient:green"
    
    def test_list_gradients(self):
        """Test listing available gradients."""
        from pynext.og.templates import list_gradients, get_gradient
        
        gradients = list_gradients()
        
        assert "blue" in gradients
        assert "slate" in gradients
        assert "purple" in gradients
        
        blue = get_gradient("blue")
        assert "linear-gradient" in blue


# ============================================
# Meta Tag Tests (4 tests)
# ============================================

class TestMetaTags:
    """Tests for OG meta tag generation."""
    
    def test_generate_og_meta_tags(self):
        """Test generating OG meta tags."""
        from pynext.og.decorator import generate_og_meta_tags
        
        tags = generate_og_meta_tags("/blog/my-post", "https://example.com")
        
        assert 'property="og:image"' in tags
        assert 'https://example.com/og/blog/my-post.png' in tags
    
    def test_meta_tags_twitter(self):
        """Test Twitter card meta tags."""
        from pynext.og.decorator import generate_og_meta_tags
        
        tags = generate_og_meta_tags("/blog/post", "https://example.com")
        
        assert 'twitter:card' in tags
        assert 'twitter:image' in tags
    
    def test_meta_tags_dimensions(self):
        """Test image dimension meta tags."""
        from pynext.og.decorator import generate_og_meta_tags
        
        tags = generate_og_meta_tags("/", "https://example.com")
        
        assert 'og:image:width' in tags
        assert '1200' in tags
        assert 'og:image:height' in tags
        assert '630' in tags
    
    def test_meta_tags_path_normalization(self):
        """Test path normalization in meta tags."""
        from pynext.og.decorator import generate_og_meta_tags
        
        tags = generate_og_meta_tags("blog/post", "https://example.com")
        
        # Should normalize path
        assert "/og/blog/post.png" in tags


# ============================================
# Integration Tests (4 tests)
# ============================================

class TestIntegration:
    """Integration tests for OG image generation."""
    
    def test_exports_from_pynext(self):
        """Test all exports are available from pynext."""
        from pynext import (
            OGCanvas,
            OGTemplate,
            og_image,
            OGConfig,
            OGRenderer,
        )
        
        assert OGCanvas is not None
        assert og_image is not None
    
    def test_exports_from_og_module(self):
        """Test exports from og submodule."""
        from pynext.og import (
            OGCanvas,
            OGTemplate,
            templates,
            og_image,
        )
        
        assert OGCanvas is not None
        assert templates.blog_post is not None
    
    def test_full_flow(self):
        """Test complete OG image flow."""
        from pynext import og_image, OGCanvas
        from pynext.og import templates
        
        # Decorator usage
        @og_image(template=templates.blog_post)
        def BlogPost(slug: str):
            pass
        
        # Custom handler
        @og_image()
        def ProductPage(id: str):
            pass
        
        @ProductPage.og
        def product_og(id: str):
            return OGCanvas(background="gradient:blue").add_text(f"Product {id}", x=60, y=200)
        
        # Verify configs
        assert BlogPost._og_config is not None
        assert ProductPage._og_handler is not None
    
    @pytest.fixture
    def skip_if_no_pillow(self):
        """Skip test if Pillow not installed."""
        try:
            import PIL
        except ImportError:
            pytest.skip("Pillow not installed")
    
    def test_full_render_flow(self, skip_if_no_pillow):
        """Test complete render flow."""
        from pynext import og_image, OGCanvas, OGRenderer
        from pynext.og import templates
        
        # Create template-based canvas
        template = templates.blog_post
        canvas = template.render({
            "title": "Integration Test",
            "date": "Jan 2025",
            "category": "Testing",
        })
        
        # Render
        renderer = OGRenderer()
        image_bytes = renderer.render(canvas)
        
        assert len(image_bytes) > 0
        assert image_bytes[:4] == b'\x89PNG'

