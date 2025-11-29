"""
Unit tests for PWA (Icons & Manifest) features.

Tests cover:
- Icon dataclass
- AppIcons configuration
- IconDetector auto-detection
- ManifestIcon and Shortcut
- PWAManifest configuration
- ManifestGenerator
- Convenience functions
- Integration tests
"""

import pytest
from pathlib import Path
import tempfile
import json


# ============================================
# Icon Tests (8 tests)
# ============================================

class TestIcon:
    """Tests for Icon dataclass."""
    
    def test_create_basic_icon(self):
        """Test creating a basic icon."""
        from pynext.pwa.icons import Icon
        
        icon = Icon("icon.png")
        
        assert icon.path == "icon.png"
        assert icon.type == "image/png"
        assert icon.purpose == "any"
    
    def test_icon_with_size(self):
        """Test icon with explicit size."""
        from pynext.pwa.icons import Icon
        
        icon = Icon("icon.png", size=192)
        
        assert icon.size == 192
    
    def test_auto_detect_size_from_filename(self):
        """Test auto-detecting size from filename."""
        from pynext.pwa.icons import Icon
        
        icon = Icon("icon-192.png")
        assert icon.size == 192
        
        icon2 = Icon("icon-512.png")
        assert icon2.size == 512
        
        icon3 = Icon("icon_256.png")
        assert icon3.size == 256
    
    def test_auto_detect_mime_type(self):
        """Test auto-detecting MIME type."""
        from pynext.pwa.icons import Icon
        
        assert Icon("icon.png").type == "image/png"
        assert Icon("icon.svg").type == "image/svg+xml"
        assert Icon("favicon.ico").type == "image/x-icon"
        assert Icon("image.webp").type == "image/webp"
    
    def test_invalid_purpose_raises(self):
        """Test invalid purpose raises error."""
        from pynext.pwa.icons import Icon
        
        with pytest.raises(ValueError) as exc_info:
            Icon("icon.png", purpose="invalid")
        
        assert "purpose" in str(exc_info.value)
    
    def test_to_link_tag(self):
        """Test generating link tag."""
        from pynext.pwa.icons import Icon
        
        icon = Icon("icon-192.png", size=192)
        tag = icon.to_link_tag()
        
        assert 'rel="icon"' in tag
        assert 'sizes="192x192"' in tag
        assert 'href="/icon-192.png"' in tag
    
    def test_to_manifest_icon(self):
        """Test converting to manifest format."""
        from pynext.pwa.icons import Icon
        
        icon = Icon("icon-512.png", size=512, purpose="maskable")
        manifest = icon.to_manifest_icon()
        
        assert manifest["src"] == "/icon-512.png"
        assert manifest["sizes"] == "512x512"
        assert manifest["purpose"] == "maskable"
    
    def test_maskable_purpose(self):
        """Test maskable icon."""
        from pynext.pwa.icons import Icon
        
        icon = Icon("icon.png", size=512, purpose="maskable")
        
        assert icon.purpose == "maskable"


# ============================================
# AppIcons Tests (10 tests)
# ============================================

class TestAppIcons:
    """Tests for AppIcons configuration."""
    
    def test_default_values(self):
        """Test default AppIcons values."""
        from pynext.pwa.icons import AppIcons
        
        icons = AppIcons()
        
        assert icons.favicon is None
        assert icons.icons == []
        assert icons.apple_icon is None
        assert icons.og_image is None
    
    def test_with_all_fields(self):
        """Test AppIcons with all fields."""
        from pynext.pwa.icons import AppIcons, Icon
        
        icons = AppIcons(
            favicon="favicon.ico",
            icons=[Icon("icon-192.png", size=192)],
            apple_icon="apple-icon.png",
            og_image="og.png",
        )
        
        assert icons.favicon == "favicon.ico"
        assert len(icons.icons) == 1
        assert icons.apple_icon == "apple-icon.png"
        assert icons.og_image == "og.png"
    
    def test_to_head_tags_favicon(self):
        """Test head tags for favicon."""
        from pynext.pwa.icons import AppIcons
        
        icons = AppIcons(favicon="favicon.ico")
        tags = icons.to_head_tags()
        
        assert 'rel="icon"' in tags
        assert 'favicon.ico' in tags
    
    def test_to_head_tags_app_icons(self):
        """Test head tags for app icons."""
        from pynext.pwa.icons import AppIcons, Icon
        
        icons = AppIcons(icons=[
            Icon("icon-192.png", size=192),
            Icon("icon-512.png", size=512),
        ])
        tags = icons.to_head_tags()
        
        assert "icon-192.png" in tags
        assert "icon-512.png" in tags
        assert 'sizes="192x192"' in tags
    
    def test_to_head_tags_apple_icon(self):
        """Test head tags for Apple icon."""
        from pynext.pwa.icons import AppIcons
        
        icons = AppIcons(apple_icon="apple-icon.png")
        tags = icons.to_head_tags()
        
        assert 'rel="apple-touch-icon"' in tags
        assert "apple-icon.png" in tags
    
    def test_to_head_tags_og_image(self):
        """Test head tags for OG image."""
        from pynext.pwa.icons import AppIcons
        
        icons = AppIcons(og_image="og.png")
        tags = icons.to_head_tags(base_url="https://example.com")
        
        assert 'property="og:image"' in tags
        assert "example.com" in tags
    
    def test_get_manifest_icons(self):
        """Test getting icons for manifest."""
        from pynext.pwa.icons import AppIcons, Icon
        
        icons = AppIcons(icons=[
            Icon("icon-192.png", size=192),
            Icon("icon-512.png", size=512, purpose="maskable"),
        ])
        
        manifest_icons = icons.get_manifest_icons()
        
        assert len(manifest_icons) == 2
        assert manifest_icons[0]["sizes"] == "192x192"
        assert manifest_icons[1]["purpose"] == "maskable"
    
    def test_merge_with(self):
        """Test merging two AppIcons."""
        from pynext.pwa.icons import AppIcons, Icon
        
        base = AppIcons(favicon="old.ico", apple_icon="apple.png")
        override = AppIcons(favicon="new.ico")
        
        merged = base.merge_with(override)
        
        assert merged.favicon == "new.ico"
        assert merged.apple_icon == "apple.png"
    
    def test_empty_head_tags(self):
        """Test empty head tags."""
        from pynext.pwa.icons import AppIcons
        
        icons = AppIcons()
        tags = icons.to_head_tags()
        
        assert tags == ""
    
    def test_svg_favicon(self):
        """Test SVG favicon."""
        from pynext.pwa.icons import AppIcons
        
        icons = AppIcons(favicon="favicon.svg")
        tags = icons.to_head_tags()
        
        assert 'type="image/svg+xml"' in tags


# ============================================
# IconDetector Tests (12 tests)
# ============================================

class TestIconDetector:
    """Tests for IconDetector."""
    
    def test_detect_empty_directory(self):
        """Test detecting icons in empty directory."""
        from pynext.pwa.icons import IconDetector
        
        with tempfile.TemporaryDirectory() as tmpdir:
            detector = IconDetector(Path(tmpdir))
            icons = detector.detect()
            
            assert icons.favicon is None
            assert icons.icons == []
    
    def test_detect_favicon_ico(self):
        """Test detecting favicon.ico."""
        from pynext.pwa.icons import IconDetector
        
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "favicon.ico").touch()
            
            detector = IconDetector(Path(tmpdir))
            icons = detector.detect()
            
            assert icons.favicon == "favicon.ico"
    
    def test_detect_favicon_png(self):
        """Test detecting favicon.png."""
        from pynext.pwa.icons import IconDetector
        
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "favicon.png").touch()
            
            detector = IconDetector(Path(tmpdir))
            icons = detector.detect()
            
            assert icons.favicon == "favicon.png"
    
    def test_detect_sized_icons(self):
        """Test detecting sized icons."""
        from pynext.pwa.icons import IconDetector
        
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "icon-192.png").touch()
            (Path(tmpdir) / "icon-512.png").touch()
            
            detector = IconDetector(Path(tmpdir))
            icons = detector.detect()
            
            assert len(icons.icons) == 2
            sizes = {i.size for i in icons.icons}
            assert 192 in sizes
            assert 512 in sizes
    
    def test_detect_apple_icon(self):
        """Test detecting Apple icon."""
        from pynext.pwa.icons import IconDetector
        
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "apple-icon.png").touch()
            
            detector = IconDetector(Path(tmpdir))
            icons = detector.detect()
            
            assert icons.apple_icon == "apple-icon.png"
    
    def test_detect_og_image(self):
        """Test detecting OG image."""
        from pynext.pwa.icons import IconDetector
        
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "og-image.png").touch()
            
            detector = IconDetector(Path(tmpdir))
            icons = detector.detect()
            
            assert icons.og_image == "og-image.png"
    
    def test_detect_all_icons(self):
        """Test detecting all icons."""
        from pynext.pwa.icons import IconDetector
        
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "favicon.ico").touch()
            (Path(tmpdir) / "icon-192.png").touch()
            (Path(tmpdir) / "icon-512.png").touch()
            (Path(tmpdir) / "apple-icon.png").touch()
            (Path(tmpdir) / "og.png").touch()
            
            detector = IconDetector(Path(tmpdir))
            icons = detector.detect()
            
            assert icons.favicon == "favicon.ico"
            assert len(icons.icons) == 2
            assert icons.apple_icon == "apple-icon.png"
            assert icons.og_image == "og.png"
    
    def test_nonexistent_directory(self):
        """Test with nonexistent directory."""
        from pynext.pwa.icons import IconDetector
        
        detector = IconDetector(Path("/nonexistent"))
        icons = detector.detect()
        
        assert icons.favicon is None
    
    def test_get_missing_icons(self):
        """Test getting missing icons."""
        from pynext.pwa.icons import IconDetector
        
        with tempfile.TemporaryDirectory() as tmpdir:
            detector = IconDetector(Path(tmpdir))
            missing = detector.get_missing_icons()
            
            assert any("favicon" in m.lower() for m in missing)
            assert any("192" in m for m in missing)
            assert any("512" in m for m in missing)
    
    def test_validate_no_icons(self):
        """Test validation with no icons."""
        from pynext.pwa.icons import IconDetector
        
        with tempfile.TemporaryDirectory() as tmpdir:
            detector = IconDetector(Path(tmpdir))
            warnings = detector.validate()
            
            assert len(warnings) > 0
    
    def test_validate_complete_icons(self):
        """Test validation with complete icons."""
        from pynext.pwa.icons import IconDetector
        
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "favicon.ico").touch()
            (Path(tmpdir) / "icon-192.png").touch()
            (Path(tmpdir) / "icon-512.png").touch()
            
            detector = IconDetector(Path(tmpdir))
            warnings = detector.validate()
            
            # Should only have maskable warning
            assert len([w for w in warnings if "required" in w.lower()]) == 0
    
    def test_icons_sorted_by_size(self):
        """Test icons are sorted by size."""
        from pynext.pwa.icons import IconDetector
        
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "icon-512.png").touch()
            (Path(tmpdir) / "icon-192.png").touch()
            (Path(tmpdir) / "icon-72.png").touch()
            
            detector = IconDetector(Path(tmpdir))
            icons = detector.detect()
            
            sizes = [i.size for i in icons.icons]
            assert sizes == sorted(sizes)


# ============================================
# ManifestIcon Tests (6 tests)
# ============================================

class TestManifestIcon:
    """Tests for ManifestIcon dataclass."""
    
    def test_create_basic(self):
        """Test creating basic ManifestIcon."""
        from pynext.pwa.manifest import ManifestIcon
        
        icon = ManifestIcon("icon.png", sizes="192x192")
        
        assert icon.src == "/icon.png"
        assert icon.sizes == "192x192"
        assert icon.type == "image/png"
    
    def test_src_normalized(self):
        """Test src path is normalized."""
        from pynext.pwa.manifest import ManifestIcon
        
        icon = ManifestIcon("icon.png")
        assert icon.src.startswith("/")
        
        icon2 = ManifestIcon("/icon.png")
        assert icon2.src == "/icon.png"
    
    def test_invalid_purpose_raises(self):
        """Test invalid purpose raises error."""
        from pynext.pwa.manifest import ManifestIcon
        
        with pytest.raises(ValueError):
            ManifestIcon("icon.png", purpose="invalid")
    
    def test_to_dict(self):
        """Test converting to dict."""
        from pynext.pwa.manifest import ManifestIcon
        
        icon = ManifestIcon("icon.png", sizes="512x512", purpose="maskable")
        d = icon.to_dict()
        
        assert d["src"] == "/icon.png"
        assert d["sizes"] == "512x512"
        assert d["purpose"] == "maskable"
    
    def test_to_dict_no_purpose(self):
        """Test to_dict excludes 'any' purpose."""
        from pynext.pwa.manifest import ManifestIcon
        
        icon = ManifestIcon("icon.png", purpose="any")
        d = icon.to_dict()
        
        assert "purpose" not in d
    
    def test_maskable_icon(self):
        """Test maskable icon."""
        from pynext.pwa.manifest import ManifestIcon
        
        icon = ManifestIcon("icon.png", sizes="512x512", purpose="maskable")
        
        assert icon.purpose == "maskable"
        assert icon.to_dict()["purpose"] == "maskable"


# ============================================
# Shortcut Tests (6 tests)
# ============================================

class TestShortcut:
    """Tests for Shortcut dataclass."""
    
    def test_create_basic(self):
        """Test creating basic Shortcut."""
        from pynext.pwa.manifest import Shortcut
        
        shortcut = Shortcut("New Task", "/new")
        
        assert shortcut.name == "New Task"
        assert shortcut.url == "/new"
    
    def test_with_description(self):
        """Test Shortcut with description."""
        from pynext.pwa.manifest import Shortcut
        
        shortcut = Shortcut("New Task", "/new", description="Create a new task")
        
        assert shortcut.description == "Create a new task"
    
    def test_with_icon(self):
        """Test Shortcut with icon."""
        from pynext.pwa.manifest import Shortcut
        
        shortcut = Shortcut("New", "/new", icon="icon-add.png")
        
        assert shortcut.icon == "icon-add.png"
    
    def test_name_required(self):
        """Test name is required."""
        from pynext.pwa.manifest import Shortcut
        
        with pytest.raises(ValueError):
            Shortcut("", "/new")
    
    def test_url_required(self):
        """Test url is required."""
        from pynext.pwa.manifest import Shortcut
        
        with pytest.raises(ValueError):
            Shortcut("New", "")
    
    def test_to_dict(self):
        """Test converting to dict."""
        from pynext.pwa.manifest import Shortcut
        
        shortcut = Shortcut("New Task", "/new", description="Create task", icon="add.png")
        d = shortcut.to_dict()
        
        assert d["name"] == "New Task"
        assert d["url"] == "/new"
        assert d["description"] == "Create task"
        assert "icons" in d


# ============================================
# PWAManifest Tests (14 tests)
# ============================================

class TestPWAManifest:
    """Tests for PWAManifest dataclass."""
    
    def test_create_minimal(self):
        """Test creating minimal manifest."""
        from pynext.pwa.manifest import PWAManifest
        
        manifest = PWAManifest(name="My App")
        
        assert manifest.name == "My App"
        assert manifest.short_name == "My App"
        assert manifest.start_url == "/"
    
    def test_auto_short_name(self):
        """Test auto-generated short_name."""
        from pynext.pwa.manifest import PWAManifest
        
        manifest = PWAManifest(name="My Very Long App Name")
        
        assert len(manifest.short_name) <= 12
    
    def test_explicit_short_name(self):
        """Test explicit short_name."""
        from pynext.pwa.manifest import PWAManifest
        
        manifest = PWAManifest(name="My App", short_name="App")
        
        assert manifest.short_name == "App"
    
    def test_default_values(self):
        """Test default values."""
        from pynext.pwa.manifest import PWAManifest
        
        manifest = PWAManifest(name="App")
        
        assert manifest.display == "standalone"
        assert manifest.orientation == "any"
        assert manifest.background_color == "#ffffff"
        assert manifest.start_url == "/"
    
    def test_invalid_display_raises(self):
        """Test invalid display mode raises."""
        from pynext.pwa.manifest import PWAManifest
        
        with pytest.raises(ValueError):
            PWAManifest(name="App", display="invalid")
    
    def test_invalid_orientation_raises(self):
        """Test invalid orientation raises."""
        from pynext.pwa.manifest import PWAManifest
        
        with pytest.raises(ValueError):
            PWAManifest(name="App", orientation="invalid")
    
    def test_to_dict(self):
        """Test converting to dict."""
        from pynext.pwa.manifest import PWAManifest
        
        manifest = PWAManifest(
            name="My App",
            theme_color="#3b82f6",
        )
        d = manifest.to_dict()
        
        assert d["name"] == "My App"
        assert d["theme_color"] == "#3b82f6"
        assert d["display"] == "standalone"
    
    def test_to_json(self):
        """Test JSON output."""
        from pynext.pwa.manifest import PWAManifest
        
        manifest = PWAManifest(name="App")
        json_str = manifest.to_json()
        
        data = json.loads(json_str)
        assert data["name"] == "App"
    
    def test_to_link_tag(self):
        """Test link tag generation."""
        from pynext.pwa.manifest import PWAManifest
        
        manifest = PWAManifest(name="App")
        tag = manifest.to_link_tag()
        
        assert 'rel="manifest"' in tag
        assert 'href="/manifest.json"' in tag
    
    def test_to_meta_tags(self):
        """Test meta tags generation."""
        from pynext.pwa.manifest import PWAManifest
        
        manifest = PWAManifest(name="App", theme_color="#3b82f6")
        tags = manifest.to_meta_tags()
        
        assert 'theme-color' in tags
        assert "#3b82f6" in tags
        assert 'apple-mobile-web-app-capable' in tags
    
    def test_with_icons(self):
        """Test manifest with icons."""
        from pynext.pwa.manifest import PWAManifest, ManifestIcon
        
        manifest = PWAManifest(
            name="App",
            icons=[
                ManifestIcon("icon-192.png", sizes="192x192"),
            ],
        )
        d = manifest.to_dict()
        
        assert "icons" in d
        assert len(d["icons"]) == 1
    
    def test_with_shortcuts(self):
        """Test manifest with shortcuts."""
        from pynext.pwa.manifest import PWAManifest, Shortcut
        
        manifest = PWAManifest(
            name="App",
            shortcuts=[
                Shortcut("New", "/new"),
            ],
        )
        d = manifest.to_dict()
        
        assert "shortcuts" in d
        assert d["shortcuts"][0]["name"] == "New"
    
    def test_with_categories(self):
        """Test manifest with categories."""
        from pynext.pwa.manifest import PWAManifest
        
        manifest = PWAManifest(
            name="App",
            categories=["productivity", "utilities"],
        )
        d = manifest.to_dict()
        
        assert d["categories"] == ["productivity", "utilities"]
    
    def test_write_to_file(self):
        """Test writing manifest to file."""
        from pynext.pwa.manifest import PWAManifest
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = PWAManifest(name="App")
            path = manifest.write_to_file(Path(tmpdir) / "manifest.json")
            
            assert path.exists()
            data = json.loads(path.read_text())
            assert data["name"] == "App"


# ============================================
# ManifestGenerator Tests (6 tests)
# ============================================

class TestManifestGenerator:
    """Tests for ManifestGenerator."""
    
    def test_generate_basic(self):
        """Test basic generation."""
        from pynext.pwa.manifest import PWAManifest, ManifestGenerator
        from pynext.pwa.icons import AppIcons
        
        config = PWAManifest(name="App")
        icons = AppIcons()
        
        generator = ManifestGenerator(config, icons)
        content = generator.generate()
        
        data = json.loads(content)
        assert data["name"] == "App"
    
    def test_merge_icons(self):
        """Test merging detected icons."""
        from pynext.pwa.manifest import PWAManifest, ManifestGenerator
        from pynext.pwa.icons import AppIcons, Icon
        
        config = PWAManifest(name="App")
        icons = AppIcons(icons=[
            Icon("icon-192.png", size=192),
        ])
        
        generator = ManifestGenerator(config, icons)
        content = generator.generate()
        
        data = json.loads(content)
        assert "icons" in data
        assert len(data["icons"]) == 1
    
    def test_config_icons_priority(self):
        """Test config icons take priority."""
        from pynext.pwa.manifest import PWAManifest, ManifestGenerator, ManifestIcon
        from pynext.pwa.icons import AppIcons, Icon
        
        config = PWAManifest(
            name="App",
            icons=[ManifestIcon("custom.png", sizes="256x256")],
        )
        icons = AppIcons(icons=[Icon("detected.png", size=192)])
        
        generator = ManifestGenerator(config, icons)
        content = generator.generate()
        
        data = json.loads(content)
        assert data["icons"][0]["src"] == "/custom.png"
    
    def test_get_all_head_tags(self):
        """Test getting all head tags."""
        from pynext.pwa.manifest import PWAManifest, ManifestGenerator
        from pynext.pwa.icons import AppIcons
        
        config = PWAManifest(name="App", theme_color="#3b82f6")
        icons = AppIcons(favicon="favicon.ico")
        
        generator = ManifestGenerator(config, icons)
        tags = generator.get_all_head_tags()
        
        assert 'rel="manifest"' in tags
        assert 'theme-color' in tags
        assert 'favicon.ico' in tags
    
    def test_empty_icons(self):
        """Test with empty icons."""
        from pynext.pwa.manifest import PWAManifest, ManifestGenerator
        from pynext.pwa.icons import AppIcons
        
        config = PWAManifest(name="App")
        icons = AppIcons()
        
        generator = ManifestGenerator(config, icons)
        content = generator.generate()
        
        data = json.loads(content)
        assert "icons" not in data or data.get("icons") == []
    
    def test_full_generation(self):
        """Test full manifest generation."""
        from pynext.pwa.manifest import PWAManifest, ManifestGenerator, Shortcut
        from pynext.pwa.icons import AppIcons, Icon
        
        config = PWAManifest(
            name="Task Manager",
            short_name="Tasks",
            theme_color="#10b981",
            shortcuts=[Shortcut("New", "/new")],
        )
        icons = AppIcons(
            favicon="favicon.ico",
            icons=[Icon("icon-512.png", size=512)],
        )
        
        generator = ManifestGenerator(config, icons)
        content = generator.generate()
        
        data = json.loads(content)
        assert data["name"] == "Task Manager"
        assert len(data["shortcuts"]) == 1
        assert len(data["icons"]) == 1


# ============================================
# Convenience Functions Tests (6 tests)
# ============================================

class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    def test_pwa_minimal(self):
        """Test pwa_minimal function."""
        from pynext.pwa.manifest import pwa_minimal
        
        manifest = pwa_minimal("My App")
        
        assert manifest.name == "My App"
        assert manifest.display == "standalone"
    
    def test_pwa_minimal_with_theme(self):
        """Test pwa_minimal with theme color."""
        from pynext.pwa.manifest import pwa_minimal
        
        manifest = pwa_minimal("My App", theme_color="#3b82f6")
        
        assert manifest.theme_color == "#3b82f6"
    
    def test_pwa_full(self):
        """Test pwa_full function."""
        from pynext.pwa.manifest import pwa_full, Shortcut
        
        manifest = pwa_full(
            name="Task Manager",
            short_name="Tasks",
            theme_color="#10b981",
            shortcuts=[Shortcut("New", "/new")],
        )
        
        assert manifest.name == "Task Manager"
        assert manifest.short_name == "Tasks"
        assert len(manifest.shortcuts) == 1
    
    def test_generate_default_icons(self):
        """Test generate_default_icons function."""
        from pynext.pwa.manifest import generate_default_icons
        
        icons = generate_default_icons()
        
        assert len(icons) == 3
        sizes = {i.sizes for i in icons}
        assert "192x192" in sizes
        assert "512x512" in sizes
    
    def test_detect_icons(self):
        """Test detect_icons convenience function."""
        from pynext.pwa.icons import detect_icons
        
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "favicon.ico").touch()
            
            icons = detect_icons(tmpdir)
            
            assert icons.favicon == "favicon.ico"
    
    def test_create_icons(self):
        """Test create_icons convenience function."""
        from pynext.pwa.icons import create_icons
        
        icons = create_icons(
            favicon="favicon.ico",
            icon_192="icon-192.png",
            icon_512="icon-512.png",
            maskable_512=True,
        )
        
        assert icons.favicon == "favicon.ico"
        assert len(icons.icons) == 2
        assert icons.icons[1].purpose == "maskable"


# ============================================
# Integration Tests (6 tests)
# ============================================

class TestPWAIntegration:
    """Integration tests for PWA features."""
    
    def test_exports_from_pynext(self):
        """Test all exports are available from pynext."""
        from pynext import (
            Icon,
            AppIcons,
            IconDetector,
            ManifestIcon,
            Shortcut,
            PWAManifest,
            ManifestGenerator,
            pwa_minimal,
            pwa_full,
        )
        
        assert Icon is not None
        assert PWAManifest is not None
    
    def test_exports_from_pwa_module(self):
        """Test exports from pwa submodule."""
        from pynext.pwa import (
            Icon,
            AppIcons,
            ManifestIcon,
            PWAManifest,
        )
        
        assert Icon is not None
    
    def test_full_pwa_flow(self):
        """Test complete PWA setup flow."""
        from pynext.pwa.icons import IconDetector
        from pynext.pwa.manifest import PWAManifest, ManifestGenerator
        
        with tempfile.TemporaryDirectory() as tmpdir:
            public = Path(tmpdir)
            
            # Create icons
            (public / "favicon.ico").touch()
            (public / "icon-192.png").touch()
            (public / "icon-512.png").touch()
            
            # Detect icons
            detector = IconDetector(public)
            icons = detector.detect()
            
            # Create manifest
            manifest = PWAManifest(
                name="Test App",
                theme_color="#3b82f6",
            )
            
            # Generate
            generator = ManifestGenerator(manifest, icons)
            content = generator.generate()
            
            # Verify
            data = json.loads(content)
            assert data["name"] == "Test App"
            assert len(data["icons"]) == 2
    
    def test_head_tag_integration(self):
        """Test full head tag integration."""
        from pynext.pwa.icons import AppIcons, Icon
        from pynext.pwa.manifest import PWAManifest, ManifestGenerator
        
        icons = AppIcons(
            favicon="favicon.ico",
            icons=[Icon("icon-192.png", size=192)],
            apple_icon="apple-icon.png",
        )
        
        manifest = PWAManifest(
            name="App",
            theme_color="#3b82f6",
        )
        
        generator = ManifestGenerator(manifest, icons)
        tags = generator.get_all_head_tags()
        
        # All required tags present
        assert "favicon.ico" in tags
        assert "icon-192" in tags
        assert "apple-touch-icon" in tags
        assert "manifest" in tags
        assert "theme-color" in tags
    
    def test_manifest_file_write(self):
        """Test writing manifest to file."""
        from pynext.pwa.manifest import PWAManifest
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = PWAManifest(
                name="Test App",
                theme_color="#10b981",
            )
            
            path = manifest.write_to_file(Path(tmpdir) / "manifest.json")
            
            assert path.exists()
            
            data = json.loads(path.read_text())
            assert data["name"] == "Test App"
            assert data["theme_color"] == "#10b981"
    
    def test_pwa_validation_complete(self):
        """Test PWA is valid with all requirements."""
        from pynext.pwa.icons import IconDetector
        
        with tempfile.TemporaryDirectory() as tmpdir:
            public = Path(tmpdir)
            
            # Create all required icons
            (public / "favicon.ico").touch()
            (public / "icon-192.png").touch()
            (public / "icon-512.png").touch()
            
            detector = IconDetector(public)
            warnings = detector.validate()
            
            # Only optional warnings (no "required" warnings)
            required_warnings = [w for w in warnings if "required" in w.lower()]
            assert len(required_warnings) == 0

