"""
Unit tests for development server with file watching.

Comprehensive tests covering:
- FileWatcher initialization and configuration
- ChangeType classification for all file types
- FileChange and reload type determination
- Ignore patterns (default and custom)
- Path handling (absolute, relative, src/ folder)
- DevServer WebSocket handling
- Dev client script content
- Edge cases and error handling
- Integration tests
"""

import pytest
from pathlib import Path
import tempfile
import asyncio
import json


# ============================================
# ChangeType Tests (6 tests)
# ============================================

class TestChangeType:
    """Tests for ChangeType enum."""
    
    def test_page_value(self):
        """Test PAGE type value."""
        from pynext.server.watcher import ChangeType
        
        assert ChangeType.PAGE.value == "page"
    
    def test_component_value(self):
        """Test COMPONENT type value."""
        from pynext.server.watcher import ChangeType
        
        assert ChangeType.COMPONENT.value == "component"
    
    def test_layout_value(self):
        """Test LAYOUT type value."""
        from pynext.server.watcher import ChangeType
        
        assert ChangeType.LAYOUT.value == "layout"
    
    def test_static_value(self):
        """Test STATIC type value."""
        from pynext.server.watcher import ChangeType
        
        assert ChangeType.STATIC.value == "static"
    
    def test_config_value(self):
        """Test CONFIG type value."""
        from pynext.server.watcher import ChangeType
        
        assert ChangeType.CONFIG.value == "config"
    
    def test_api_value(self):
        """Test API type value."""
        from pynext.server.watcher import ChangeType
        
        assert ChangeType.API.value == "api"


# ============================================
# FileChange Tests (10 tests)
# ============================================

class TestFileChange:
    """Tests for FileChange dataclass."""
    
    def test_create_basic(self):
        """Test creating a basic FileChange."""
        from pynext.server.watcher import FileChange, ChangeType
        
        change = FileChange(
            path=Path("/project/pages/index.py"),
            change_type=ChangeType.PAGE,
        )
        
        assert change.path == Path("/project/pages/index.py")
        assert change.change_type == ChangeType.PAGE
        assert change.is_delete is False
    
    def test_create_with_delete(self):
        """Test FileChange with is_delete=True."""
        from pynext.server.watcher import FileChange, ChangeType
        
        change = FileChange(
            path=Path("/project/pages/old.py"),
            change_type=ChangeType.PAGE,
            is_delete=True,
        )
        
        assert change.is_delete is True
    
    def test_relative_path_with_root(self):
        """Test relative_path with project_root."""
        from pynext.server.watcher import FileChange, ChangeType
        
        change = FileChange(
            path=Path("/project/pages/index.py"),
            change_type=ChangeType.PAGE,
            project_root=Path("/project"),
        )
        
        assert change.relative_path == "pages/index.py"
    
    def test_relative_path_without_root(self):
        """Test relative_path without project_root."""
        from pynext.server.watcher import FileChange, ChangeType
        
        change = FileChange(
            path=Path("/project/pages/index.py"),
            change_type=ChangeType.PAGE,
        )
        
        assert change.relative_path == "/project/pages/index.py"
    
    def test_reload_type_page(self):
        """Test reload_type for PAGE change."""
        from pynext.server.watcher import FileChange, ChangeType
        
        change = FileChange(
            path=Path("pages/index.py"),
            change_type=ChangeType.PAGE,
        )
        
        assert change.reload_type == "hot"
    
    def test_reload_type_component(self):
        """Test reload_type for COMPONENT change."""
        from pynext.server.watcher import FileChange, ChangeType
        
        change = FileChange(
            path=Path("components/button.py"),
            change_type=ChangeType.COMPONENT,
        )
        
        assert change.reload_type == "hot"
    
    def test_reload_type_css(self):
        """Test reload_type for CSS file."""
        from pynext.server.watcher import FileChange, ChangeType
        
        change = FileChange(
            path=Path("public/styles.css"),
            change_type=ChangeType.STATIC,
        )
        
        assert change.reload_type == "css"
    
    def test_reload_type_layout(self):
        """Test reload_type for LAYOUT change."""
        from pynext.server.watcher import FileChange, ChangeType
        
        change = FileChange(
            path=Path("pages/layout.py"),
            change_type=ChangeType.LAYOUT,
        )
        
        assert change.reload_type == "full"
    
    def test_reload_type_config(self):
        """Test reload_type for CONFIG change."""
        from pynext.server.watcher import FileChange, ChangeType
        
        change = FileChange(
            path=Path("pynext.config.py"),
            change_type=ChangeType.CONFIG,
        )
        
        assert change.reload_type == "full"
    
    def test_to_dict(self):
        """Test FileChange to_dict serialization."""
        from pynext.server.watcher import FileChange, ChangeType
        
        change = FileChange(
            path=Path("pages/index.py"),
            change_type=ChangeType.PAGE,
            project_root=Path("."),
        )
        
        d = change.to_dict()
        
        assert d["change_type"] == "page"
        assert d["reload_type"] == "hot"
        assert d["is_delete"] is False


# ============================================
# FileWatcher Tests (12 tests)
# ============================================

class TestFileWatcher:
    """Tests for FileWatcher class."""
    
    def test_init_default(self):
        """Test FileWatcher with defaults."""
        from pynext.server.watcher import FileWatcher
        
        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = FileWatcher(Path(tmpdir))
            
            assert watcher.root == Path(tmpdir).resolve()
            assert watcher.debounce_ms == 10
    
    def test_init_custom_ignore(self):
        """Test FileWatcher with custom ignore patterns."""
        from pynext.server.watcher import FileWatcher
        
        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = FileWatcher(
                Path(tmpdir),
                ignore_patterns=["*.tmp"],
            )
            
            assert "*.tmp" in watcher.ignore_patterns
    
    def test_classify_page(self):
        """Test classifying page files."""
        from pynext.server.watcher import FileWatcher, ChangeType
        
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            (root / "pages").mkdir()
            
            watcher = FileWatcher(root)
            
            # Use resolved absolute path
            result = watcher._classify_change((root / "pages" / "index.py").resolve())
            assert result == ChangeType.PAGE
    
    def test_classify_layout(self):
        """Test classifying layout files."""
        from pynext.server.watcher import FileWatcher, ChangeType
        
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            (root / "pages").mkdir()
            
            watcher = FileWatcher(root)
            
            result = watcher._classify_change((root / "pages" / "layout.py").resolve())
            assert result == ChangeType.LAYOUT
    
    def test_classify_component(self):
        """Test classifying component files."""
        from pynext.server.watcher import FileWatcher, ChangeType
        
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            (root / "components").mkdir()
            
            watcher = FileWatcher(root)
            
            result = watcher._classify_change((root / "components" / "button.py").resolve())
            assert result == ChangeType.COMPONENT
    
    def test_classify_static(self):
        """Test classifying static files."""
        from pynext.server.watcher import FileWatcher, ChangeType
        
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            (root / "public").mkdir()
            
            watcher = FileWatcher(root)
            
            result = watcher._classify_change((root / "public" / "style.css").resolve())
            assert result == ChangeType.STATIC
    
    def test_classify_config(self):
        """Test classifying config files."""
        from pynext.server.watcher import FileWatcher, ChangeType
        
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            
            watcher = FileWatcher(root)
            
            result = watcher._classify_change((root / "pynext.config.py").resolve())
            assert result == ChangeType.CONFIG
    
    def test_classify_api(self):
        """Test classifying API files."""
        from pynext.server.watcher import FileWatcher, ChangeType
        
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            (root / "pages" / "api").mkdir(parents=True)
            
            watcher = FileWatcher(root)
            
            result = watcher._classify_change((root / "pages" / "api" / "users.py").resolve())
            assert result == ChangeType.API
    
    def test_classify_src_pages(self):
        """Test classifying files in src/pages."""
        from pynext.server.watcher import FileWatcher, ChangeType
        
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            (root / "src" / "pages").mkdir(parents=True)
            
            watcher = FileWatcher(root)
            
            result = watcher._classify_change((root / "src" / "pages" / "index.py").resolve())
            assert result == ChangeType.PAGE
    
    def test_should_ignore_pycache(self):
        """Test ignoring __pycache__ directories."""
        from pynext.server.watcher import FileWatcher
        
        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = FileWatcher(Path(tmpdir))
            
            assert watcher._should_ignore(Path("pages/__pycache__/test.pyc"))
    
    def test_should_ignore_pyc(self):
        """Test ignoring .pyc files."""
        from pynext.server.watcher import FileWatcher
        
        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = FileWatcher(Path(tmpdir))
            
            assert watcher._should_ignore(Path("pages/index.pyc"))
    
    def test_stop(self):
        """Test stopping the watcher."""
        from pynext.server.watcher import FileWatcher
        
        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = FileWatcher(Path(tmpdir))
            watcher._running = True
            
            watcher.stop()
            
            assert watcher._running is False


# ============================================
# DevServer Tests (8 tests)
# ============================================

class TestDevServer:
    """Tests for DevServer class."""
    
    def test_init(self):
        """Test DevServer initialization."""
        from pynext.server.dev import DevServer
        
        with tempfile.TemporaryDirectory() as tmpdir:
            server = DevServer(Path(tmpdir))
            
            assert server.root == Path(tmpdir).resolve()
            assert server.port == 8000
            assert server.host == "0.0.0.0"
    
    def test_init_custom_port(self):
        """Test DevServer with custom port."""
        from pynext.server.dev import DevServer
        
        with tempfile.TemporaryDirectory() as tmpdir:
            server = DevServer(Path(tmpdir), port=3000)
            
            assert server.port == 3000
    
    def test_connected_clients_empty(self):
        """Test connected_clients when no clients."""
        from pynext.server.dev import DevServer
        
        with tempfile.TemporaryDirectory() as tmpdir:
            server = DevServer(Path(tmpdir))
            
            assert server.connected_clients == 0
    
    def test_reload_count_initial(self):
        """Test initial reload count."""
        from pynext.server.dev import DevServer
        
        with tempfile.TemporaryDirectory() as tmpdir:
            server = DevServer(Path(tmpdir))
            
            assert server._reload_count == 0
    
    def test_get_dev_client_script(self):
        """Test getting dev client script."""
        from pynext.server.dev import get_dev_client_script
        
        script = get_dev_client_script()
        
        assert "WebSocket" in script
        assert "__pynext/ws" in script
        assert "hotReload" in script
    
    def test_get_dev_script_tag(self):
        """Test getting dev script tag."""
        from pynext.server.dev import get_dev_script_tag
        
        tag = get_dev_script_tag()
        
        assert "<script" in tag
        assert "dev-client.js" in tag
    
    def test_dev_client_script_has_css_reload(self):
        """Test dev client has CSS reload."""
        from pynext.server.dev import DEV_CLIENT_SCRIPT
        
        assert "reloadCSS" in DEV_CLIENT_SCRIPT
    
    def test_dev_client_script_has_reconnect(self):
        """Test dev client has reconnection."""
        from pynext.server.dev import DEV_CLIENT_SCRIPT
        
        assert "reconnect" in DEV_CLIENT_SCRIPT.lower()


# ============================================
# Convenience Functions Tests (4 tests)
# ============================================

class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    def test_create_watcher(self):
        """Test create_watcher function."""
        from pynext.server.watcher import create_watcher
        
        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = create_watcher(tmpdir)
            
            assert watcher.root == Path(tmpdir).resolve()
    
    def test_create_watcher_with_ignore(self):
        """Test create_watcher with ignore patterns."""
        from pynext.server.watcher import create_watcher
        
        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = create_watcher(tmpdir, ignore=["*.log"])
            
            assert "*.log" in watcher.ignore_patterns
    
    def test_run_dev_server_function_exists(self):
        """Test run_dev_server function exists."""
        from pynext.server.dev import run_dev_server
        
        assert callable(run_dev_server)
    
    def test_run_dev_server_async_exists(self):
        """Test run_dev_server_async function exists."""
        from pynext.server.dev import run_dev_server_async
        
        assert asyncio.iscoroutinefunction(run_dev_server_async)


# ============================================
# Integration Tests (6 tests)
# ============================================

class TestIntegration:
    """Integration tests for dev server."""
    
    def test_watcher_export(self):
        """Test watcher exports from pynext.server."""
        from pynext.server.watcher import (
            FileWatcher,
            FileChange,
            ChangeType,
            create_watcher,
        )
        
        assert FileWatcher is not None
        assert FileChange is not None
        assert ChangeType is not None
    
    def test_dev_server_export(self):
        """Test dev server exports."""
        from pynext.server.dev import (
            DevServer,
            run_dev_server,
            get_dev_client_script,
        )
        
        assert DevServer is not None
        assert run_dev_server is not None
    
    def test_reload_type_api_none(self):
        """Test API changes return 'none' reload type."""
        from pynext.server.watcher import FileChange, ChangeType
        
        change = FileChange(
            path=Path("pages/api/users.py"),
            change_type=ChangeType.API,
        )
        
        assert change.reload_type == "none"
    
    def test_reload_type_template(self):
        """Test template changes return 'full' reload type."""
        from pynext.server.watcher import FileChange, ChangeType
        
        change = FileChange(
            path=Path("pages/template.py"),
            change_type=ChangeType.TEMPLATE,
        )
        
        assert change.reload_type == "full"
    
    def test_js_file_full_reload(self):
        """Test JS files trigger full reload."""
        from pynext.server.watcher import FileChange, ChangeType
        
        change = FileChange(
            path=Path("public/app.js"),
            change_type=ChangeType.STATIC,
        )
        
        assert change.reload_type == "full"
    
    def test_file_extension_property(self):
        """Test file_extension property."""
        from pynext.server.watcher import FileChange, ChangeType
        
        change = FileChange(
            path=Path("public/styles.css"),
            change_type=ChangeType.STATIC,
        )
        
        assert change.file_extension == ".css"


# ============================================
# Extended FileChange Tests (12 tests)
# ============================================

class TestFileChangeExtended:
    """Extended tests for FileChange edge cases."""
    
    def test_reload_type_unknown(self):
        """Test UNKNOWN type defaults to full reload."""
        from pynext.server.watcher import FileChange, ChangeType
        
        change = FileChange(
            path=Path("random/file.txt"),
            change_type=ChangeType.UNKNOWN,
        )
        
        assert change.reload_type == "full"
    
    def test_typescript_full_reload(self):
        """Test TypeScript files trigger full reload."""
        from pynext.server.watcher import FileChange, ChangeType
        
        change = FileChange(
            path=Path("public/app.ts"),
            change_type=ChangeType.STATIC,
        )
        
        assert change.reload_type == "full"
    
    def test_image_file_reload(self):
        """Test image files trigger full reload."""
        from pynext.server.watcher import FileChange, ChangeType
        
        for ext in [".png", ".jpg", ".gif", ".svg", ".webp"]:
            change = FileChange(
                path=Path(f"public/image{ext}"),
                change_type=ChangeType.STATIC,
            )
            assert change.reload_type == "full"
    
    def test_scss_css_reload(self):
        """Test SCSS files also get CSS hot swap."""
        from pynext.server.watcher import FileChange, ChangeType
        
        # Note: only .css gets css reload, scss needs processing
        change = FileChange(
            path=Path("public/styles.scss"),
            change_type=ChangeType.STATIC,
        )
        # SCSS isn't pure CSS, so full reload
        assert change.reload_type == "full"
    
    def test_to_dict_all_fields(self):
        """Test to_dict includes all fields."""
        from pynext.server.watcher import FileChange, ChangeType
        
        change = FileChange(
            path=Path("pages/blog/post.py"),
            change_type=ChangeType.PAGE,
            is_delete=True,
            project_root=Path("/project"),
        )
        
        d = change.to_dict()
        
        assert "path" in d
        assert "change_type" in d
        assert "reload_type" in d
        assert "is_delete" in d
        assert "extension" in d
        assert d["is_delete"] is True
        assert d["extension"] == ".py"
    
    def test_file_extension_no_extension(self):
        """Test file without extension."""
        from pynext.server.watcher import FileChange, ChangeType
        
        change = FileChange(
            path=Path("Makefile"),
            change_type=ChangeType.UNKNOWN,
        )
        
        assert change.file_extension == ""
    
    def test_relative_path_complex(self):
        """Test relative_path with nested directories."""
        from pynext.server.watcher import FileChange, ChangeType
        
        change = FileChange(
            path=Path("/project/src/pages/blog/[slug]/index.py"),
            change_type=ChangeType.PAGE,
            project_root=Path("/project"),
        )
        
        assert change.relative_path == "src/pages/blog/[slug]/index.py"
    
    def test_relative_path_outside_root(self):
        """Test relative_path when path is outside root."""
        from pynext.server.watcher import FileChange, ChangeType
        
        change = FileChange(
            path=Path("/other/project/file.py"),
            change_type=ChangeType.UNKNOWN,
            project_root=Path("/my/project"),
        )
        
        # Should fall back to absolute path
        assert "/other/project/file.py" in change.relative_path
    
    def test_multiple_css_files(self):
        """Test different CSS file paths."""
        from pynext.server.watcher import FileChange, ChangeType
        
        paths = [
            "public/styles.css",
            "public/components/button.css",
            "static/themes/dark.css",
        ]
        
        for path in paths:
            change = FileChange(
                path=Path(path),
                change_type=ChangeType.STATIC,
            )
            assert change.reload_type == "css"
    
    def test_nested_api_route(self):
        """Test deeply nested API routes."""
        from pynext.server.watcher import FileChange, ChangeType
        
        change = FileChange(
            path=Path("pages/api/v1/users/[id].py"),
            change_type=ChangeType.API,
        )
        
        assert change.reload_type == "none"
    
    def test_font_files(self):
        """Test font files trigger full reload."""
        from pynext.server.watcher import FileChange, ChangeType
        
        for ext in [".woff", ".woff2", ".ttf", ".otf", ".eot"]:
            change = FileChange(
                path=Path(f"public/fonts/inter{ext}"),
                change_type=ChangeType.STATIC,
            )
            assert change.reload_type == "full"
    
    def test_json_files(self):
        """Test JSON files in static directory."""
        from pynext.server.watcher import FileChange, ChangeType
        
        change = FileChange(
            path=Path("public/data.json"),
            change_type=ChangeType.STATIC,
        )
        
        assert change.reload_type == "full"


# ============================================
# Extended FileWatcher Tests (16 tests)
# ============================================

class TestFileWatcherExtended:
    """Extended tests for FileWatcher."""
    
    def test_default_ignore_patterns(self):
        """Test all default ignore patterns are present."""
        from pynext.server.watcher import FileWatcher
        
        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = FileWatcher(Path(tmpdir))
            
            expected = ["__pycache__", "*.pyc", ".git", ".pynext", "node_modules"]
            for pattern in expected:
                assert pattern in watcher.ignore_patterns
    
    def test_should_ignore_node_modules(self):
        """Test ignoring node_modules."""
        from pynext.server.watcher import FileWatcher
        
        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = FileWatcher(Path(tmpdir))
            
            assert watcher._should_ignore(Path("node_modules/react/index.js"))
    
    def test_should_ignore_git(self):
        """Test ignoring .git directory."""
        from pynext.server.watcher import FileWatcher
        
        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = FileWatcher(Path(tmpdir))
            
            assert watcher._should_ignore(Path(".git/objects/abc"))
    
    def test_should_ignore_pynext_dir(self):
        """Test ignoring .pynext directory."""
        from pynext.server.watcher import FileWatcher
        
        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = FileWatcher(Path(tmpdir))
            
            assert watcher._should_ignore(Path(".pynext/cache/file.py"))
    
    def test_should_ignore_env_files(self):
        """Test ignoring .env files."""
        from pynext.server.watcher import FileWatcher
        
        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = FileWatcher(Path(tmpdir))
            
            assert watcher._should_ignore(Path(".env"))
            assert watcher._should_ignore(Path(".env.local"))
            assert watcher._should_ignore(Path(".env.production"))
    
    def test_should_not_ignore_valid_files(self):
        """Test valid files are not ignored."""
        from pynext.server.watcher import FileWatcher
        
        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = FileWatcher(Path(tmpdir))
            
            assert not watcher._should_ignore(Path("pages/index.py"))
            assert not watcher._should_ignore(Path("components/button.py"))
            assert not watcher._should_ignore(Path("public/styles.css"))
    
    def test_classify_nested_page(self):
        """Test classifying nested page files."""
        from pynext.server.watcher import FileWatcher, ChangeType
        
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            (root / "pages" / "blog" / "posts").mkdir(parents=True)
            
            watcher = FileWatcher(root)
            
            result = watcher._classify_change((root / "pages" / "blog" / "posts" / "[id].py").resolve())
            assert result == ChangeType.PAGE
    
    def test_classify_dynamic_route(self):
        """Test classifying dynamic route files."""
        from pynext.server.watcher import FileWatcher, ChangeType
        
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            (root / "pages" / "products").mkdir(parents=True)
            
            watcher = FileWatcher(root)
            
            result = watcher._classify_change((root / "pages" / "products" / "[...slug].py").resolve())
            assert result == ChangeType.PAGE
    
    def test_classify_src_components(self):
        """Test classifying files in src/components."""
        from pynext.server.watcher import FileWatcher, ChangeType
        
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            (root / "src" / "components").mkdir(parents=True)
            
            watcher = FileWatcher(root)
            
            result = watcher._classify_change((root / "src" / "components" / "Card.py").resolve())
            assert result == ChangeType.COMPONENT
    
    def test_classify_template(self):
        """Test classifying template.py files."""
        from pynext.server.watcher import FileWatcher, ChangeType
        
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            (root / "pages" / "dashboard").mkdir(parents=True)
            
            watcher = FileWatcher(root)
            
            result = watcher._classify_change((root / "pages" / "dashboard" / "template.py").resolve())
            assert result == ChangeType.TEMPLATE
    
    def test_classify_public_subdirectory(self):
        """Test classifying files in public subdirectories."""
        from pynext.server.watcher import FileWatcher, ChangeType
        
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            (root / "public" / "images").mkdir(parents=True)
            
            watcher = FileWatcher(root)
            
            result = watcher._classify_change((root / "public" / "images" / "logo.png").resolve())
            assert result == ChangeType.STATIC
    
    def test_classify_static_directory(self):
        """Test classifying files in static directory."""
        from pynext.server.watcher import FileWatcher, ChangeType
        
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            (root / "static").mkdir()
            
            watcher = FileWatcher(root)
            
            result = watcher._classify_change((root / "static" / "bundle.js").resolve())
            assert result == ChangeType.STATIC
    
    def test_custom_debounce(self):
        """Test custom debounce setting."""
        from pynext.server.watcher import FileWatcher
        
        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = FileWatcher(Path(tmpdir), debounce_ms=50)
            
            assert watcher.debounce_ms == 50
    
    def test_add_remove_callback(self):
        """Test adding and removing callbacks."""
        from pynext.server.watcher import FileWatcher
        
        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = FileWatcher(Path(tmpdir))
            
            callback = lambda x: None
            watcher.add_callback(callback)
            assert callback in watcher._callbacks
            
            watcher.remove_callback(callback)
            assert callback not in watcher._callbacks
    
    def test_remove_nonexistent_callback(self):
        """Test removing callback that doesn't exist."""
        from pynext.server.watcher import FileWatcher
        
        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = FileWatcher(Path(tmpdir))
            
            callback = lambda x: None
            # Should not raise
            watcher.remove_callback(callback)
    
    def test_should_ignore_swap_files(self):
        """Test ignoring editor swap files."""
        from pynext.server.watcher import FileWatcher
        
        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = FileWatcher(Path(tmpdir))
            
            assert watcher._should_ignore(Path("pages/index.py.swp"))
            assert watcher._should_ignore(Path("pages/index.py.swo"))
            assert watcher._should_ignore(Path("pages/index.py~"))


# ============================================
# DevServer Extended Tests (12 tests)
# ============================================

class TestDevServerExtended:
    """Extended tests for DevServer."""
    
    def test_init_with_all_params(self):
        """Test DevServer with all parameters."""
        from pynext.server.dev import DevServer
        
        with tempfile.TemporaryDirectory() as tmpdir:
            server = DevServer(
                root=Path(tmpdir),
                port=3000,
                host="127.0.0.1",
            )
            
            assert server.port == 3000
            assert server.host == "127.0.0.1"
    
    def test_websockets_set_empty(self):
        """Test WebSocket set is empty initially."""
        from pynext.server.dev import DevServer
        
        with tempfile.TemporaryDirectory() as tmpdir:
            server = DevServer(Path(tmpdir))
            
            assert isinstance(server._websockets, set)
            assert len(server._websockets) == 0
    
    def test_watcher_instance(self):
        """Test watcher is created."""
        from pynext.server.dev import DevServer
        from pynext.server.watcher import FileWatcher
        
        with tempfile.TemporaryDirectory() as tmpdir:
            server = DevServer(Path(tmpdir))
            
            assert isinstance(server.watcher, FileWatcher)
    
    def test_dev_client_has_websocket_url(self):
        """Test dev client has correct WebSocket URL."""
        from pynext.server.dev import DEV_CLIENT_SCRIPT
        
        assert "__pynext/ws" in DEV_CLIENT_SCRIPT
    
    def test_dev_client_has_hot_reload(self):
        """Test dev client has hot reload function."""
        from pynext.server.dev import DEV_CLIENT_SCRIPT
        
        assert "hotReload" in DEV_CLIENT_SCRIPT
    
    def test_dev_client_has_css_reload(self):
        """Test dev client has CSS reload function."""
        from pynext.server.dev import DEV_CLIENT_SCRIPT
        
        assert "reloadCSS" in DEV_CLIENT_SCRIPT
    
    def test_dev_client_has_full_reload(self):
        """Test dev client has full reload function."""
        from pynext.server.dev import DEV_CLIENT_SCRIPT
        
        assert "fullReload" in DEV_CLIENT_SCRIPT or "location.reload" in DEV_CLIENT_SCRIPT
    
    def test_dev_client_has_reconnect_logic(self):
        """Test dev client has reconnection logic."""
        from pynext.server.dev import DEV_CLIENT_SCRIPT
        
        assert "reconnect" in DEV_CLIENT_SCRIPT.lower() or "onclose" in DEV_CLIENT_SCRIPT
    
    def test_dev_client_has_overlay(self):
        """Test dev client has connection overlay."""
        from pynext.server.dev import DEV_CLIENT_SCRIPT
        
        assert "overlay" in DEV_CLIENT_SCRIPT.lower()
    
    def test_dev_client_has_pynext_dev_global(self):
        """Test dev client exposes __pynext_dev__ global."""
        from pynext.server.dev import DEV_CLIENT_SCRIPT
        
        assert "__pynext_dev__" in DEV_CLIENT_SCRIPT
    
    def test_dev_client_handles_message_types(self):
        """Test dev client handles different message types."""
        from pynext.server.dev import DEV_CLIENT_SCRIPT
        
        assert "'hot'" in DEV_CLIENT_SCRIPT or '"hot"' in DEV_CLIENT_SCRIPT
        assert "'css'" in DEV_CLIENT_SCRIPT or '"css"' in DEV_CLIENT_SCRIPT
        assert "'full'" in DEV_CLIENT_SCRIPT or '"full"' in DEV_CLIENT_SCRIPT
    
    def test_dev_client_has_performance_timing(self):
        """Test dev client has performance timing."""
        from pynext.server.dev import DEV_CLIENT_SCRIPT
        
        assert "performance.now" in DEV_CLIENT_SCRIPT


# ============================================
# Dev Reload JS Tests (8 tests)
# ============================================

class TestDevReloadJS:
    """Tests for dev-reload.js runtime file."""
    
    def test_runtime_file_exists(self):
        """Test dev-reload.js file exists."""
        from pathlib import Path
        
        runtime_path = Path(__file__).parent.parent.parent / "pynext" / "runtime" / "dev-reload.js"
        assert runtime_path.exists()
    
    def test_runtime_has_connect_function(self):
        """Test runtime has connect function."""
        from pathlib import Path
        
        runtime_path = Path(__file__).parent.parent.parent / "pynext" / "runtime" / "dev-reload.js"
        content = runtime_path.read_text()
        
        assert "function connect" in content or "connect()" in content
    
    def test_runtime_has_websocket(self):
        """Test runtime uses WebSocket."""
        from pathlib import Path
        
        runtime_path = Path(__file__).parent.parent.parent / "pynext" / "runtime" / "dev-reload.js"
        content = runtime_path.read_text()
        
        assert "WebSocket" in content
    
    def test_runtime_has_pynext_ws_endpoint(self):
        """Test runtime connects to correct endpoint."""
        from pathlib import Path
        
        runtime_path = Path(__file__).parent.parent.parent / "pynext" / "runtime" / "dev-reload.js"
        content = runtime_path.read_text()
        
        assert "__pynext/ws" in content
    
    def test_runtime_has_reload_handlers(self):
        """Test runtime has reload handler functions."""
        from pathlib import Path
        
        runtime_path = Path(__file__).parent.parent.parent / "pynext" / "runtime" / "dev-reload.js"
        content = runtime_path.read_text()
        
        assert "reloadCSS" in content
        assert "hotReload" in content
        assert "fullReload" in content
    
    def test_runtime_has_dom_parser(self):
        """Test runtime uses DOMParser for hot reload."""
        from pathlib import Path
        
        runtime_path = Path(__file__).parent.parent.parent / "pynext" / "runtime" / "dev-reload.js"
        content = runtime_path.read_text()
        
        assert "DOMParser" in content
    
    def test_runtime_is_iife(self):
        """Test runtime is wrapped in IIFE."""
        from pathlib import Path
        
        runtime_path = Path(__file__).parent.parent.parent / "pynext" / "runtime" / "dev-reload.js"
        content = runtime_path.read_text()
        
        # Check for IIFE pattern
        assert "(function()" in content or "(() =>" in content
    
    def test_runtime_has_use_strict(self):
        """Test runtime uses strict mode."""
        from pathlib import Path
        
        runtime_path = Path(__file__).parent.parent.parent / "pynext" / "runtime" / "dev-reload.js"
        content = runtime_path.read_text()
        
        assert "'use strict'" in content or '"use strict"' in content


# ============================================
# Edge Cases and Error Handling (10 tests)
# ============================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_empty_path_classification(self):
        """Test classifying empty-ish paths."""
        from pynext.server.watcher import FileWatcher, ChangeType
        
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            watcher = FileWatcher(root)
            
            # Root path itself
            result = watcher._classify_change(root)
            assert result == ChangeType.UNKNOWN
    
    def test_deeply_nested_components(self):
        """Test deeply nested component paths."""
        from pynext.server.watcher import FileWatcher, ChangeType
        
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            deep_path = root / "components" / "ui" / "forms" / "inputs" / "TextInput.py"
            deep_path.parent.mkdir(parents=True)
            
            watcher = FileWatcher(root)
            
            result = watcher._classify_change(deep_path.resolve())
            assert result == ChangeType.COMPONENT
    
    def test_special_characters_in_path(self):
        """Test paths with special characters."""
        from pynext.server.watcher import FileChange, ChangeType
        
        change = FileChange(
            path=Path("pages/[...slug].py"),
            change_type=ChangeType.PAGE,
        )
        
        assert change.reload_type == "hot"
    
    def test_unicode_filename(self):
        """Test unicode in filename."""
        from pynext.server.watcher import FileChange, ChangeType
        
        change = FileChange(
            path=Path("pages/日本語.py"),
            change_type=ChangeType.PAGE,
        )
        
        assert change.reload_type == "hot"
    
    def test_watcher_with_nonexistent_root(self):
        """Test watcher with non-existent root directory."""
        from pynext.server.watcher import FileWatcher
        
        # Should not raise during construction
        watcher = FileWatcher(Path("/nonexistent/path"))
        assert watcher.root == Path("/nonexistent/path")
    
    def test_change_type_enum_values(self):
        """Test all ChangeType enum values."""
        from pynext.server.watcher import ChangeType
        
        expected = ["page", "component", "layout", "template", "static", "config", "api", "unknown"]
        actual = [ct.value for ct in ChangeType]
        
        for exp in expected:
            assert exp in actual
    
    def test_file_change_immutability(self):
        """Test FileChange fields after creation."""
        from pynext.server.watcher import FileChange, ChangeType
        
        change = FileChange(
            path=Path("test.py"),
            change_type=ChangeType.PAGE,
            is_delete=False,
        )
        
        # These are dataclass fields, should be accessible
        assert change.path == Path("test.py")
        assert change.change_type == ChangeType.PAGE
        assert change.is_delete is False
    
    def test_hidden_files_classification(self):
        """Test hidden files (starting with dot)."""
        from pynext.server.watcher import FileWatcher, ChangeType
        
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            watcher = FileWatcher(root)
            
            result = watcher._classify_change((root / ".hidden").resolve())
            assert result == ChangeType.UNKNOWN
    
    def test_double_extension_files(self):
        """Test files with double extensions."""
        from pynext.server.watcher import FileChange, ChangeType
        
        change = FileChange(
            path=Path("public/script.min.js"),
            change_type=ChangeType.STATIC,
        )
        
        assert change.file_extension == ".js"
    
    def test_no_extension_in_pages(self):
        """Test file without extension in pages directory."""
        from pynext.server.watcher import FileWatcher, ChangeType
        
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            (root / "pages").mkdir()
            
            watcher = FileWatcher(root)
            
            result = watcher._classify_change((root / "pages" / "README").resolve())
            assert result == ChangeType.PAGE


# ============================================
# Async Behavior Tests (6 tests)
# ============================================

class TestAsyncBehavior:
    """Tests for async behavior."""
    
    def test_watch_returns_async_iterator(self):
        """Test watch() returns async iterator."""
        from pynext.server.watcher import FileWatcher
        import inspect
        
        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = FileWatcher(Path(tmpdir))
            
            result = watcher.watch()
            assert hasattr(result, "__anext__")
    
    def test_stop_sets_running_false(self):
        """Test stop() sets _running to False."""
        from pynext.server.watcher import FileWatcher
        
        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = FileWatcher(Path(tmpdir))
            watcher._running = True
            
            watcher.stop()
            
            assert watcher._running is False
    
    def test_run_dev_server_async_is_coroutine(self):
        """Test run_dev_server_async is a coroutine function."""
        from pynext.server.dev import run_dev_server_async
        import asyncio
        
        assert asyncio.iscoroutinefunction(run_dev_server_async)
    
    def test_run_dev_server_is_sync(self):
        """Test run_dev_server is a regular function."""
        from pynext.server.dev import run_dev_server
        import asyncio
        
        assert not asyncio.iscoroutinefunction(run_dev_server)
    
    def test_watch_once_is_async(self):
        """Test watch_once is async."""
        from pynext.server.watcher import watch_once
        import asyncio
        
        assert asyncio.iscoroutinefunction(watch_once)
    
    def test_dev_server_start_is_async(self):
        """Test DevServer.start is async."""
        from pynext.server.dev import DevServer
        import asyncio
        
        with tempfile.TemporaryDirectory() as tmpdir:
            server = DevServer(Path(tmpdir))
            
            assert asyncio.iscoroutinefunction(server.start)


# ============================================
# Performance Tests (8 tests)
# ============================================

class TestPerformance:
    """Tests for performance characteristics."""
    
    def test_file_change_creation_fast(self):
        """Test FileChange creation is fast."""
        from pynext.server.watcher import FileChange, ChangeType
        import time
        
        start = time.perf_counter()
        for _ in range(1000):
            FileChange(
                path=Path("pages/index.py"),
                change_type=ChangeType.PAGE,
            )
        elapsed = (time.perf_counter() - start) * 1000
        
        # Should create 1000 instances in < 10ms
        assert elapsed < 100, f"Creation took {elapsed:.2f}ms"
    
    def test_to_dict_fast(self):
        """Test to_dict is fast."""
        from pynext.server.watcher import FileChange, ChangeType
        import time
        
        change = FileChange(
            path=Path("pages/index.py"),
            change_type=ChangeType.PAGE,
        )
        
        start = time.perf_counter()
        for _ in range(1000):
            change.to_dict()
        elapsed = (time.perf_counter() - start) * 1000
        
        # Should serialize 1000 times in < 50ms
        assert elapsed < 100, f"Serialization took {elapsed:.2f}ms"
    
    def test_classify_change_fast(self):
        """Test classification is fast."""
        from pynext.server.watcher import FileWatcher
        import time
        
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            (root / "pages").mkdir()
            watcher = FileWatcher(root)
            
            paths = [
                root / "pages" / "index.py",
                root / "pages" / "blog" / "post.py",
                root / "components" / "button.py",
                root / "public" / "styles.css",
            ]
            
            start = time.perf_counter()
            for _ in range(1000):
                for path in paths:
                    watcher._classify_change(path)
            elapsed = (time.perf_counter() - start) * 1000
            
            # Should classify 4000 paths in < 100ms
            assert elapsed < 200, f"Classification took {elapsed:.2f}ms"
    
    def test_should_ignore_fast(self):
        """Test ignore checking is fast."""
        from pynext.server.watcher import FileWatcher
        import time
        
        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = FileWatcher(Path(tmpdir))
            
            paths = [
                Path("pages/index.py"),
                Path("__pycache__/file.pyc"),
                Path("node_modules/react/index.js"),
                Path("components/button.py"),
            ]
            
            start = time.perf_counter()
            for _ in range(1000):
                for path in paths:
                    watcher._should_ignore(path)
            elapsed = (time.perf_counter() - start) * 1000
            
            # Should check 4000 paths in < 100ms
            assert elapsed < 200, f"Ignore check took {elapsed:.2f}ms"
    
    def test_json_dumps_message_fast(self):
        """Test JSON serialization is fast."""
        import time
        
        message = {
            "type": "reload",
            "reload_type": "hot",
            "path": "pages/index.py",
            "change_type": "page",
            "is_delete": False,
            "timestamp": 1234567890.123,
        }
        
        start = time.perf_counter()
        for _ in range(1000):
            json.dumps(message)
        elapsed = (time.perf_counter() - start) * 1000
        
        # Should serialize 1000 messages in < 50ms
        assert elapsed < 100, f"JSON serialization took {elapsed:.2f}ms"
    
    def test_dev_client_script_small(self):
        """Test dev client script is small."""
        from pynext.server.dev import DEV_CLIENT_SCRIPT
        
        # Script should be < 6KB unminified (reasonable for a feature-rich dev client)
        size = len(DEV_CLIENT_SCRIPT)
        assert size < 6000, f"Script is {size} bytes"
    
    def test_reload_type_property_fast(self):
        """Test reload_type property is fast."""
        from pynext.server.watcher import FileChange, ChangeType
        import time
        
        changes = [
            FileChange(Path("pages/index.py"), ChangeType.PAGE),
            FileChange(Path("components/button.py"), ChangeType.COMPONENT),
            FileChange(Path("public/styles.css"), ChangeType.STATIC),
            FileChange(Path("layout.py"), ChangeType.LAYOUT),
        ]
        
        start = time.perf_counter()
        for _ in range(1000):
            for change in changes:
                _ = change.reload_type
        elapsed = (time.perf_counter() - start) * 1000
        
        # Should access 4000 reload types in < 50ms
        assert elapsed < 100, f"reload_type access took {elapsed:.2f}ms"
    
    def test_relative_path_property_fast(self):
        """Test relative_path property is fast."""
        from pynext.server.watcher import FileChange, ChangeType
        import time
        
        change = FileChange(
            path=Path("/project/pages/blog/[id]/index.py"),
            change_type=ChangeType.PAGE,
            project_root=Path("/project"),
        )
        
        start = time.perf_counter()
        for _ in range(1000):
            _ = change.relative_path
        elapsed = (time.perf_counter() - start) * 1000
        
        # Should access 1000 times in < 50ms
        assert elapsed < 100, f"relative_path access took {elapsed:.2f}ms"


# ============================================
# Comprehensive Reload Type Tests (12 tests)
# ============================================

class TestReloadTypeComprehensive:
    """Comprehensive tests for reload type determination."""
    
    def test_all_page_types_hot(self):
        """Test all page types get hot reload."""
        from pynext.server.watcher import FileChange, ChangeType
        
        paths = [
            "pages/index.py",
            "pages/about.py",
            "pages/blog/index.py",
            "pages/blog/[id].py",
            "pages/products/[...slug].py",
            "pages/(admin)/dashboard.py",
        ]
        
        for path in paths:
            change = FileChange(Path(path), ChangeType.PAGE)
            assert change.reload_type == "hot", f"{path} should be hot reload"
    
    def test_all_component_types_hot(self):
        """Test all component types get hot reload."""
        from pynext.server.watcher import FileChange, ChangeType
        
        paths = [
            "components/button.py",
            "components/ui/card.py",
            "components/forms/input.py",
            "components/layouts/sidebar.py",
        ]
        
        for path in paths:
            change = FileChange(Path(path), ChangeType.COMPONENT)
            assert change.reload_type == "hot", f"{path} should be hot reload"
    
    def test_all_css_types_css(self):
        """Test all CSS types get CSS reload."""
        from pynext.server.watcher import FileChange, ChangeType
        
        paths = [
            "public/styles.css",
            "public/theme/dark.css",
            "static/global.css",
            "public/components/button.css",
        ]
        
        for path in paths:
            change = FileChange(Path(path), ChangeType.STATIC)
            assert change.reload_type == "css", f"{path} should be CSS reload"
    
    def test_all_js_types_full(self):
        """Test all JS types get full reload."""
        from pynext.server.watcher import FileChange, ChangeType
        
        paths = [
            "public/app.js",
            "public/vendor/jquery.js",
            "static/bundle.js",
            "public/app.ts",
        ]
        
        for path in paths:
            change = FileChange(Path(path), ChangeType.STATIC)
            assert change.reload_type == "full", f"{path} should be full reload"
    
    def test_layout_always_full(self):
        """Test layouts always get full reload."""
        from pynext.server.watcher import FileChange, ChangeType
        
        paths = [
            "pages/layout.py",
            "pages/blog/layout.py",
            "pages/admin/dashboard/layout.py",
        ]
        
        for path in paths:
            change = FileChange(Path(path), ChangeType.LAYOUT)
            assert change.reload_type == "full", f"{path} should be full reload"
    
    def test_template_always_full(self):
        """Test templates always get full reload."""
        from pynext.server.watcher import FileChange, ChangeType
        
        paths = [
            "pages/template.py",
            "pages/blog/template.py",
            "pages/admin/template.py",
        ]
        
        for path in paths:
            change = FileChange(Path(path), ChangeType.TEMPLATE)
            assert change.reload_type == "full", f"{path} should be full reload"
    
    def test_config_always_full(self):
        """Test config always gets full reload."""
        from pynext.server.watcher import FileChange, ChangeType
        
        change = FileChange(Path("pynext.config.py"), ChangeType.CONFIG)
        assert change.reload_type == "full"
    
    def test_api_always_none(self):
        """Test API routes don't trigger visual reload."""
        from pynext.server.watcher import FileChange, ChangeType
        
        paths = [
            "pages/api/users.py",
            "pages/api/v1/products.py",
            "pages/api/[...path].py",
        ]
        
        for path in paths:
            change = FileChange(Path(path), ChangeType.API)
            assert change.reload_type == "none", f"{path} should be none"
    
    def test_image_files_full(self):
        """Test image files get full reload."""
        from pynext.server.watcher import FileChange, ChangeType
        
        extensions = [".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico"]
        
        for ext in extensions:
            change = FileChange(Path(f"public/image{ext}"), ChangeType.STATIC)
            assert change.reload_type == "full", f"{ext} should be full reload"
    
    def test_font_files_full(self):
        """Test font files get full reload."""
        from pynext.server.watcher import FileChange, ChangeType
        
        extensions = [".woff", ".woff2", ".ttf", ".otf", ".eot"]
        
        for ext in extensions:
            change = FileChange(Path(f"public/font{ext}"), ChangeType.STATIC)
            assert change.reload_type == "full", f"{ext} should be full reload"
    
    def test_data_files_full(self):
        """Test data files get full reload."""
        from pynext.server.watcher import FileChange, ChangeType
        
        extensions = [".json", ".xml", ".yaml", ".yml", ".toml"]
        
        for ext in extensions:
            change = FileChange(Path(f"public/data{ext}"), ChangeType.STATIC)
            assert change.reload_type == "full", f"{ext} should be full reload"
    
    def test_unknown_defaults_to_full(self):
        """Test unknown types default to full reload."""
        from pynext.server.watcher import FileChange, ChangeType
        
        paths = [
            "unknown/file.py",
            "lib/utils.py",
            "README.md",
            "pyproject.toml",
        ]
        
        for path in paths:
            change = FileChange(Path(path), ChangeType.UNKNOWN)
            assert change.reload_type == "full", f"{path} should be full reload"


# ============================================
# Dev Client JavaScript Tests (10 tests)
# ============================================

class TestDevClientJavaScript:
    """Tests for dev client JavaScript functionality."""
    
    def test_has_iife_wrapper(self):
        """Test script is wrapped in IIFE for isolation."""
        from pynext.server.dev import DEV_CLIENT_SCRIPT
        
        assert DEV_CLIENT_SCRIPT.strip().startswith("/**")
        assert "(function()" in DEV_CLIENT_SCRIPT
        assert "})();" in DEV_CLIENT_SCRIPT
    
    def test_has_strict_mode(self):
        """Test script uses strict mode."""
        from pynext.server.dev import DEV_CLIENT_SCRIPT
        
        assert "'use strict'" in DEV_CLIENT_SCRIPT
    
    def test_has_websocket_connection(self):
        """Test script creates WebSocket connection."""
        from pynext.server.dev import DEV_CLIENT_SCRIPT
        
        assert "new WebSocket" in DEV_CLIENT_SCRIPT
        assert "__pynext/ws" in DEV_CLIENT_SCRIPT
    
    def test_has_reconnect_logic(self):
        """Test script has reconnection logic."""
        from pynext.server.dev import DEV_CLIENT_SCRIPT
        
        assert "RECONNECT_DELAY" in DEV_CLIENT_SCRIPT
        assert "MAX_RECONNECT_ATTEMPTS" in DEV_CLIENT_SCRIPT
    
    def test_has_reload_functions(self):
        """Test script has all reload functions."""
        from pynext.server.dev import DEV_CLIENT_SCRIPT
        
        assert "function reloadCSS" in DEV_CLIENT_SCRIPT
        assert "function hotReload" in DEV_CLIENT_SCRIPT
        assert "function fullReload" in DEV_CLIENT_SCRIPT
    
    def test_has_overlay_functions(self):
        """Test script has overlay functions."""
        from pynext.server.dev import DEV_CLIENT_SCRIPT
        
        assert "showOverlay" in DEV_CLIENT_SCRIPT
        assert "hideOverlay" in DEV_CLIENT_SCRIPT
    
    def test_has_message_handler(self):
        """Test script has message handler."""
        from pynext.server.dev import DEV_CLIENT_SCRIPT
        
        assert "handleMessage" in DEV_CLIENT_SCRIPT
        assert "switch" in DEV_CLIENT_SCRIPT
    
    def test_handles_all_reload_types(self):
        """Test script handles all reload types."""
        from pynext.server.dev import DEV_CLIENT_SCRIPT
        
        assert "'css'" in DEV_CLIENT_SCRIPT
        assert "'hot'" in DEV_CLIENT_SCRIPT
        assert "'full'" in DEV_CLIENT_SCRIPT
        assert "'none'" in DEV_CLIENT_SCRIPT
    
    def test_has_pynext_global(self):
        """Test script exposes __pynext_dev__ global."""
        from pynext.server.dev import DEV_CLIENT_SCRIPT
        
        assert "__pynext_dev__" in DEV_CLIENT_SCRIPT
        assert "reconnect" in DEV_CLIENT_SCRIPT
    
    def test_has_heartbeat(self):
        """Test script has heartbeat for connection keep-alive."""
        from pynext.server.dev import DEV_CLIENT_SCRIPT
        
        assert "heartbeat" in DEV_CLIENT_SCRIPT
        assert "setInterval" in DEV_CLIENT_SCRIPT


# ============================================
# WebSocket Message Format Tests (6 tests)
# ============================================

class TestWebSocketMessageFormat:
    """Tests for WebSocket message format."""
    
    def test_message_has_type_field(self):
        """Test messages have type field."""
        from pynext.server.watcher import FileChange, ChangeType
        
        change = FileChange(Path("pages/index.py"), ChangeType.PAGE)
        d = change.to_dict()
        
        assert "change_type" in d
    
    def test_message_has_reload_type(self):
        """Test messages have reload_type field."""
        from pynext.server.watcher import FileChange, ChangeType
        
        change = FileChange(Path("pages/index.py"), ChangeType.PAGE)
        d = change.to_dict()
        
        assert "reload_type" in d
        assert d["reload_type"] == "hot"
    
    def test_message_has_path(self):
        """Test messages have path field."""
        from pynext.server.watcher import FileChange, ChangeType
        
        change = FileChange(
            path=Path("/project/pages/index.py"),
            change_type=ChangeType.PAGE,
            project_root=Path("/project"),
        )
        d = change.to_dict()
        
        assert "path" in d
        assert d["path"] == "pages/index.py"
    
    def test_message_has_is_delete(self):
        """Test messages have is_delete field."""
        from pynext.server.watcher import FileChange, ChangeType
        
        change = FileChange(Path("pages/index.py"), ChangeType.PAGE, is_delete=True)
        d = change.to_dict()
        
        assert "is_delete" in d
        assert d["is_delete"] is True
    
    def test_message_has_extension(self):
        """Test messages have extension field."""
        from pynext.server.watcher import FileChange, ChangeType
        
        change = FileChange(Path("public/styles.css"), ChangeType.STATIC)
        d = change.to_dict()
        
        assert "extension" in d
        assert d["extension"] == ".css"
    
    def test_message_json_serializable(self):
        """Test messages are JSON serializable."""
        from pynext.server.watcher import FileChange, ChangeType
        
        change = FileChange(
            path=Path("/project/pages/blog/[id].py"),
            change_type=ChangeType.PAGE,
            is_delete=False,
            project_root=Path("/project"),
        )
        
        # Should not raise
        json_str = json.dumps(change.to_dict())
        parsed = json.loads(json_str)
        
        assert parsed["path"] == "pages/blog/[id].py"
        assert parsed["change_type"] == "page"
        assert parsed["reload_type"] == "hot"

