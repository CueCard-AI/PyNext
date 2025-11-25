"""
Tests for PyNext Image Optimization.
"""

import pytest
from pathlib import Path
from pynext.core.image import (
    Image,
    ImageConfig,
    ImageLayout,
    ImageLoading,
    ImageFormat,
    ImageRegistry,
    OptimizedImage,
    ResponsiveImage,
    FillImage,
    PriorityImage,
    Avatar,
    get_image_config,
    get_image_registry,
    configure_images,
    get_image_js_runtime,
    needs_image_runtime,
)


class TestImageConfig:
    """Tests for ImageConfig."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = ImageConfig()
        
        assert ImageFormat.AVIF in config.formats
        assert ImageFormat.WEBP in config.formats
        assert len(config.sizes) > 0
        assert config.quality[ImageFormat.AVIF] == 75
        assert config.build_time_optimization is True
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = ImageConfig(
            formats=[ImageFormat.WEBP, ImageFormat.JPEG],
            quality={ImageFormat.WEBP: 90, ImageFormat.JPEG: 80},
            blur_hash_size=8,
        )
        
        assert len(config.formats) == 2
        assert ImageFormat.AVIF not in config.formats
        assert config.quality[ImageFormat.WEBP] == 90
        assert config.blur_hash_size == 8


class TestImageRegistry:
    """Tests for ImageRegistry."""
    
    def test_register_image(self):
        """Test image registration."""
        registry = ImageRegistry()
        hash_id = registry.register("/images/hero.jpg")
        
        assert len(hash_id) == 12
        assert "/images/hero.jpg" in registry.get_pending()
    
    def test_duplicate_registration(self):
        """Test that duplicate registration uses same hash."""
        registry = ImageRegistry()
        hash1 = registry.register("/images/hero.jpg")
        hash2 = registry.register("/images/hero.jpg")
        
        assert hash1 == hash2
        # Should only be in pending once
        assert registry.get_pending().count("/images/hero.jpg") == 1
    
    def test_set_optimized_image(self):
        """Test setting optimized image data."""
        registry = ImageRegistry()
        registry.register("/images/hero.jpg")
        
        optimized = OptimizedImage(
            original_src="/images/hero.jpg",
            hash="abc123",
            width=1920,
            height=1080,
            variants={
                "webp": {"640w": "/_next/image/abc123_640w.webp"},
            },
            blur_data_url="data:image/webp;base64,..."
        )
        
        registry.set("/images/hero.jpg", optimized)
        
        result = registry.get("/images/hero.jpg")
        assert result is not None
        assert result.width == 1920
        assert "/images/hero.jpg" not in registry.get_pending()
    
    def test_manifest_export(self):
        """Test exporting registry as manifest."""
        import hashlib
        registry = ImageRegistry()
        src = "/images/test.jpg"
        optimized = OptimizedImage(
            original_src=src,
            hash="test123",
            width=800,
            height=600,
        )
        registry.set(src, optimized)
        
        manifest = registry.to_manifest()
        
        # The manifest key is md5(src)[:12], not optimized.hash
        expected_key = hashlib.md5(src.encode()).hexdigest()[:12]
        assert expected_key in manifest
        assert manifest[expected_key]["width"] == 800


class TestOptimizedImage:
    """Tests for OptimizedImage."""
    
    def test_srcset_generation(self):
        """Test srcset string generation."""
        optimized = OptimizedImage(
            original_src="/test.jpg",
            hash="abc",
            width=1920,
            height=1080,
            variants={
                "webp": {
                    "640w": "/_next/image/abc_640w.webp",
                    "1080w": "/_next/image/abc_1080w.webp",
                },
            },
        )
        
        srcset = optimized.get_srcset(ImageFormat.WEBP)
        
        assert "640w" in srcset
        assert "1080w" in srcset
        assert "abc_640w.webp" in srcset
    
    def test_serialization(self):
        """Test to_dict serialization."""
        optimized = OptimizedImage(
            original_src="/test.jpg",
            hash="abc",
            width=800,
            height=600,
            blur_hash="LHFC*L~qWB%M",
            dominant_color="#336699",
        )
        
        data = optimized.to_dict()
        
        assert data["original"] == "/test.jpg"
        assert data["width"] == 800
        assert data["blurHash"] == "LHFC*L~qWB%M"
        assert data["dominantColor"] == "#336699"


class TestImageComponent:
    """Tests for Image component rendering."""
    
    def test_basic_image(self):
        """Test basic image rendering."""
        html = Image(
            src="/images/hero.jpg",
            alt="Hero image",
            width=1920,
            height=1080,
        )
        
        assert "<img" in html
        assert 'alt="Hero image"' in html
        assert 'width="1920"' in html
        assert 'loading="lazy"' in html
    
    def test_eager_loading(self):
        """Test eager loading."""
        html = Image(
            src="/images/hero.jpg",
            alt="Hero",
            loading=ImageLoading.EAGER,
        )
        
        assert 'loading="eager"' in html
    
    def test_priority_image(self):
        """Test priority image with preload."""
        html = Image(
            src="/images/hero.jpg",
            alt="Hero",
            priority=True,
        )
        
        assert '<link rel="preload"' in html
        assert 'loading="eager"' in html
    
    def test_fill_layout(self):
        """Test fill layout styles."""
        html = Image(
            src="/images/bg.jpg",
            alt="Background",
            layout=ImageLayout.FILL,
        )
        
        assert "position: absolute" in html
        assert "object-fit: cover" in html
    
    def test_responsive_layout(self):
        """Test responsive layout styles."""
        html = Image(
            src="/images/content.jpg",
            alt="Content",
            layout=ImageLayout.RESPONSIVE,
        )
        
        assert "width: 100%" in html
        assert "height: auto" in html
    
    def test_svg_passthrough(self):
        """Test SVG images are not processed."""
        html = Image(
            src="/images/logo.svg",
            alt="Logo",
            width=100,
            height=100,
        )
        
        assert 'src="/images/logo.svg"' in html
        # No picture element for SVG
        assert "<picture>" not in html
    
    def test_custom_classname(self):
        """Test custom className."""
        html = Image(
            src="/images/test.jpg",
            alt="Test",
            className="hero-image custom-class",
        )
        
        assert 'class="hero-image custom-class"' in html
    
    def test_custom_style(self):
        """Test custom inline styles."""
        html = Image(
            src="/images/test.jpg",
            alt="Test",
            style={"border-radius": "8px", "box-shadow": "0 2px 4px rgba(0,0,0,0.1)"},
        )
        
        assert "border-radius: 8px" in html
        assert "box-shadow:" in html
    
    def test_data_attributes(self):
        """Test data-* attributes."""
        html = Image(
            src="/images/test.jpg",
            alt="Test",
            data_testid="hero-img",
            data_index="0",
        )
        
        assert 'data-testid="hero-img"' in html
        assert 'data-index="0"' in html


class TestConvenienceComponents:
    """Tests for convenience image components."""
    
    def test_responsive_image(self):
        """Test ResponsiveImage wrapper."""
        html = ResponsiveImage(
            src="/images/content.jpg",
            alt="Content",
        )
        
        assert "width: 100%" in html
    
    def test_fill_image(self):
        """Test FillImage wrapper."""
        html = FillImage(
            src="/images/bg.jpg",
            alt="Background",
        )
        
        assert "position: absolute" in html
    
    def test_priority_image_wrapper(self):
        """Test PriorityImage wrapper."""
        html = PriorityImage(
            src="/images/hero.jpg",
            alt="Hero",
        )
        
        assert 'loading="eager"' in html
        assert '<link rel="preload"' in html
    
    def test_avatar(self):
        """Test Avatar component."""
        html = Avatar(
            src="/images/user.jpg",
            alt="User avatar",
            size=48,
        )
        
        assert 'width="48"' in html
        assert 'height="48"' in html
        assert "border-radius: 50%" in html


class TestImageJSRuntime:
    """Tests for image JS runtime."""
    
    def test_runtime_content(self):
        """Test JS runtime contains necessary code."""
        js = get_image_js_runtime()
        
        assert "data-pynext-image" in js
        assert "querySelectorAll" in js
        assert "subscribe" in js
    
    def test_needs_runtime_default_false(self):
        """Test that by default no runtime is needed."""
        # Fresh registry should not need runtime
        assert needs_image_runtime() is False


class TestImageWithOptimizedData:
    """Tests for Image with pre-optimized data."""
    
    def test_picture_element_rendering(self):
        """Test picture element with sources."""
        registry = get_image_registry()
        
        optimized = OptimizedImage(
            original_src="/images/test.jpg",
            hash="opt123",
            width=1920,
            height=1080,
            variants={
                "avif": {
                    "640w_sm": "/_next/image/opt123_640w_sm.avif",
                    "1080w_lg": "/_next/image/opt123_1080w_lg.avif",
                },
                "webp": {
                    "640w_sm": "/_next/image/opt123_640w_sm.webp",
                    "1080w_lg": "/_next/image/opt123_1080w_lg.webp",
                },
            },
            blur_data_url="data:image/webp;base64,abc123",
        )
        registry.set("/images/test.jpg", optimized)
        
        html = Image(
            src="/images/test.jpg",
            alt="Test",
        )
        
        assert "<picture>" in html
        assert "</picture>" in html
        assert '<source type="image/avif"' in html
        assert '<source type="image/webp"' in html
        assert "srcset=" in html
    
    def test_blur_placeholder(self):
        """Test blur placeholder styling."""
        registry = get_image_registry()
        
        optimized = OptimizedImage(
            original_src="/images/blur-test.jpg",
            hash="blur123",
            width=800,
            height=600,
            variants={"webp": {"640w": "/_next/image/blur123_640w.webp"}},
            blur_data_url="data:image/webp;base64,testblur",
        )
        registry.set("/images/blur-test.jpg", optimized)
        
        html = Image(
            src="/images/blur-test.jpg",
            alt="Blur test",
            placeholder="blur",
        )
        
        assert "background-image: url(data:image/webp;base64,testblur)" in html

