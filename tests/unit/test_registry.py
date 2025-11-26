"""
Tests for PyNext Component Registry System.

Tests the three-tier component system:
- Tier 1: Native libraries (imports)
- Tier 2: Official UI components (pynext ui)
- Tier 3: Custom registries (pynext registry)
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest


class TestTier1NativeLibraries:
    """Test that native libraries can be imported directly."""
    
    def test_import_tw_utilities(self):
        """Test importing Tailwind utilities."""
        from pynext.tw import tw, cn
        
        assert callable(cn)
        assert hasattr(tw, 'flex')
    
    def test_import_shadcn_components(self):
        """Test importing ShadCN components."""
        from pynext.shadcn import Button, Card, Dialog, Input, Tabs
        
        assert Button is not None
        assert Card is not None
        assert Dialog is not None
        assert Input is not None
        assert Tabs is not None
    
    def test_button_render(self):
        """Test that Button component renders HTML."""
        from pynext.shadcn import Button
        
        btn = Button()["Click me"]
        html = btn.render()
        
        assert "<button" in html
        assert "Click me" in html


class TestTier2ComponentRegistry:
    """Test the pynext ui component management."""
    
    def test_list_available_components(self):
        """Test listing all available components."""
        from pynext.registry import list_available_components, AVAILABLE_COMPONENTS
        
        components = list_available_components()
        
        assert len(components) > 0
        assert len(components) == len(AVAILABLE_COMPONENTS)
    
    def test_list_components_by_category(self):
        """Test filtering components by category."""
        from pynext.registry import list_available_components
        
        basic = list_available_components(category="basic")
        form = list_available_components(category="form")
        
        assert len(basic) > 0
        assert len(form) > 0
        assert all(c.category == "basic" for c in basic)
        assert all(c.category == "form" for c in form)
    
    def test_component_info_structure(self):
        """Test that component info has correct structure."""
        from pynext.registry import list_available_components
        
        components = list_available_components()
        button = next(c for c in components if c.name == "button")
        
        assert button.name == "button"
        assert button.module == "pynext.shadcn.button"
        assert "Button" in button.exports
        assert button.category == "basic"
        assert len(button.description) > 0
    
    def test_get_component_source(self):
        """Test getting component source code."""
        from pynext.registry import get_component_source
        
        source = get_component_source("button")
        
        assert source is not None
        assert "Button" in source
        assert "def " in source or "class " in source
    
    def test_get_component_source_not_found(self):
        """Test getting source for non-existent component."""
        from pynext.registry import get_component_source
        
        source = get_component_source("nonexistent-component")
        
        assert source is None
    
    def test_copy_component_to_project(self):
        """Test copying a component to project directory."""
        from pynext.registry import copy_component_to_project
        
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            
            result = copy_component_to_project("button", project_dir)
            
            assert result is not None
            assert result.exists()
            assert result.name == "button.py"
            
            # Check content was modified
            content = result.read_text()
            assert "Copied from pynext.shadcn" in content
    
    def test_copy_component_creates_init(self):
        """Test that copying creates __init__.py."""
        from pynext.registry import copy_component_to_project
        
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            
            copy_component_to_project("button", project_dir)
            
            init_path = project_dir / "components" / "ui" / "__init__.py"
            assert init_path.exists()
            
            content = init_path.read_text()
            assert "from .button import Button" in content
    
    def test_copy_multiple_components(self):
        """Test copying multiple components."""
        from pynext.registry.components import copy_all_components
        
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            
            copied = copy_all_components(project_dir)
            
            assert len(copied) > 10  # We have 16+ components
            
            # Check all files exist
            for path in copied:
                assert path.exists()


class TestTier3CustomRegistries:
    """Test custom registry management."""
    
    def test_registry_manager_init(self):
        """Test initializing registry manager."""
        from pynext.registry import RegistryManager
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = RegistryManager(tmpdir)
            
            assert manager.project_dir == Path(tmpdir).resolve()
            assert len(manager.list_registries()) == 0
    
    def test_add_registry(self):
        """Test adding a custom registry."""
        from pynext.registry import RegistryManager
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = RegistryManager(tmpdir)
            
            registry = manager.add_registry("acme-ui", "https://ui.acme.com")
            
            assert registry.name == "acme-ui"
            assert registry.url == "https://ui.acme.com"
            assert len(manager.list_registries()) == 1
    
    def test_add_github_registry(self):
        """Test adding a GitHub registry."""
        from pynext.registry import RegistryManager
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = RegistryManager(tmpdir)
            
            registry = manager.add_registry("my-lib", "github:user/repo")
            
            assert registry.url == "github:user/repo"
    
    def test_remove_registry(self):
        """Test removing a registry."""
        from pynext.registry import RegistryManager
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = RegistryManager(tmpdir)
            manager.add_registry("acme-ui", "https://ui.acme.com")
            
            assert manager.remove_registry("acme-ui") is True
            assert len(manager.list_registries()) == 0
    
    def test_remove_nonexistent_registry(self):
        """Test removing a non-existent registry."""
        from pynext.registry import RegistryManager
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = RegistryManager(tmpdir)
            
            assert manager.remove_registry("nonexistent") is False
    
    def test_registry_persistence(self):
        """Test that registries persist to disk."""
        from pynext.registry import RegistryManager
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Add registry with first manager
            manager1 = RegistryManager(tmpdir)
            manager1.add_registry("acme-ui", "https://ui.acme.com")
            
            # Create new manager, should load from disk
            manager2 = RegistryManager(tmpdir)
            registries = manager2.list_registries()
            
            assert len(registries) == 1
            assert registries[0].name == "acme-ui"
    
    def test_registry_config_file_format(self):
        """Test the config file JSON format."""
        from pynext.registry import RegistryManager
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = RegistryManager(tmpdir)
            manager.add_registry("acme-ui", "https://ui.acme.com")
            
            config_path = Path(tmpdir) / ".pynext" / "registries.json"
            assert config_path.exists()
            
            data = json.loads(config_path.read_text())
            assert "registries" in data
            assert "acme-ui" in data["registries"]
            assert data["registries"]["acme-ui"]["url"] == "https://ui.acme.com"
    
    def test_get_registry(self):
        """Test getting a specific registry."""
        from pynext.registry import RegistryManager
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = RegistryManager(tmpdir)
            manager.add_registry("acme-ui", "https://ui.acme.com")
            
            registry = manager.get_registry("acme-ui")
            
            assert registry is not None
            assert registry.name == "acme-ui"
    
    def test_get_nonexistent_registry(self):
        """Test getting a non-existent registry."""
        from pynext.registry import RegistryManager
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = RegistryManager(tmpdir)
            
            registry = manager.get_registry("nonexistent")
            
            assert registry is None


class TestRegistryFromJSON:
    """Test Registry.from_json parsing."""
    
    def test_parse_full_registry(self):
        """Test parsing a complete registry JSON."""
        from pynext.registry import Registry
        
        data = {
            "name": "acme-ui",
            "version": "1.0.0",
            "description": "Acme Corp Design System",
            "author": "Acme Team",
            "base_styles": "styles/theme.css",
            "components": {
                "data-table": {
                    "name": "DataTable",
                    "description": "Sortable data table",
                    "files": ["data_table.py"],
                    "styles": "data_table.css",
                    "dependencies": {
                        "pynext": ["pynext.shadcn.table"],
                        "npm": ["@tanstack/table-core"]
                    }
                }
            }
        }
        
        registry = Registry.from_json(data)
        
        assert registry.name == "acme-ui"
        assert registry.version == "1.0.0"
        assert registry.description == "Acme Corp Design System"
        assert registry.author == "Acme Team"
        assert registry.base_styles == "styles/theme.css"
        
        assert "data-table" in registry.components
        comp = registry.components["data-table"]
        assert comp.name == "DataTable"
        assert comp.files == ["data_table.py"]
        assert "pynext" in comp.dependencies
    
    def test_parse_minimal_registry(self):
        """Test parsing a minimal registry JSON."""
        from pynext.registry import Registry
        
        data = {
            "name": "minimal",
            "components": {}
        }
        
        registry = Registry.from_json(data)
        
        assert registry.name == "minimal"
        assert registry.version == "1.0.0"  # default
        assert len(registry.components) == 0


class TestRegistryTemplate:
    """Test registry template creation."""
    
    def test_create_template(self):
        """Test creating a registry template file."""
        from pynext.registry.manager import create_registry_template
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "pynext-registry.json"
            
            create_registry_template(output_path)
            
            assert output_path.exists()
            
            data = json.loads(output_path.read_text())
            assert "name" in data
            assert "version" in data
            assert "components" in data
            assert "example-card" in data["components"]


class TestCLIIntegration:
    """Test CLI command integration."""
    
    def test_ui_list_command(self):
        """Test pynext ui list works without errors."""
        import subprocess
        import sys
        
        result = subprocess.run(
            [sys.executable, "-m", "pynext.cli", "ui", "list"],
            capture_output=True,
            text=True,
        )
        
        assert result.returncode == 0
        assert "Available UI Components" in result.stdout
        assert "button" in result.stdout.lower()
    
    def test_registry_list_command(self):
        """Test pynext registry list works without errors."""
        import subprocess
        import sys
        
        result = subprocess.run(
            [sys.executable, "-m", "pynext.cli", "registry", "list"],
            capture_output=True,
            text=True,
        )
        
        assert result.returncode == 0
    
    def test_ui_add_command(self):
        """Test pynext ui add command."""
        import subprocess
        import sys
        
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [sys.executable, "-m", "pynext.cli", "ui", "add", "button"],
                capture_output=True,
                text=True,
                cwd=tmpdir,
            )
            
            assert result.returncode == 0
            assert "button" in result.stdout
            
            # Check file was created
            button_path = Path(tmpdir) / "components" / "ui" / "button.py"
            assert button_path.exists()
    
    def test_ui_add_all_command(self):
        """Test pynext ui add --all command."""
        import subprocess
        import sys
        
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [sys.executable, "-m", "pynext.cli", "ui", "add", "--all"],
                capture_output=True,
                text=True,
                cwd=tmpdir,
            )
            
            assert result.returncode == 0
            assert "Copied" in result.stdout
            
            # Check multiple files were created
            ui_dir = Path(tmpdir) / "components" / "ui"
            assert ui_dir.exists()
            assert len(list(ui_dir.glob("*.py"))) > 10
    
    def test_registry_add_remove_cycle(self):
        """Test adding and removing a registry."""
        import subprocess
        import sys
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Add registry
            add_result = subprocess.run(
                [sys.executable, "-m", "pynext.cli", "registry", "add", 
                 "test-ui", "--url=https://test.com"],
                capture_output=True,
                text=True,
                cwd=tmpdir,
            )
            assert add_result.returncode == 0
            assert "Added test-ui" in add_result.stdout
            
            # List should show it
            list_result = subprocess.run(
                [sys.executable, "-m", "pynext.cli", "registry", "list"],
                capture_output=True,
                text=True,
                cwd=tmpdir,
            )
            assert "test-ui" in list_result.stdout
            
            # Remove registry
            remove_result = subprocess.run(
                [sys.executable, "-m", "pynext.cli", "registry", "remove", "test-ui"],
                capture_output=True,
                text=True,
                cwd=tmpdir,
            )
            assert remove_result.returncode == 0
            assert "Removed" in remove_result.stdout

