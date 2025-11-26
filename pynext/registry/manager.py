"""
Custom Registry Manager for PyNext.

Handles Tier 3: Custom component registries from URLs or GitHub.
"""

from __future__ import annotations

import json
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse


@dataclass
class RegistryComponent:
    """A component within a registry."""
    name: str
    description: str
    files: list[str]
    styles: Optional[str] = None
    dependencies: dict = field(default_factory=dict)


@dataclass
class Registry:
    """A custom component registry."""
    name: str
    url: str
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    base_styles: Optional[str] = None
    components: dict[str, RegistryComponent] = field(default_factory=dict)
    
    @classmethod
    def from_json(cls, data: dict) -> "Registry":
        """Create a Registry from JSON data."""
        components = {}
        for comp_name, comp_data in data.get("components", {}).items():
            components[comp_name] = RegistryComponent(
                name=comp_data.get("name", comp_name),
                description=comp_data.get("description", ""),
                files=comp_data.get("files", []),
                styles=comp_data.get("styles"),
                dependencies=comp_data.get("dependencies", {}),
            )
        
        return cls(
            name=data["name"],
            url=data.get("url", ""),
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            author=data.get("author", ""),
            base_styles=data.get("base_styles"),
            components=components,
        )
    
    def to_json(self) -> dict:
        """Convert registry to JSON-serializable dict."""
        return {
            "name": self.name,
            "url": self.url,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "base_styles": self.base_styles,
            "components": {
                name: {
                    "name": comp.name,
                    "description": comp.description,
                    "files": comp.files,
                    "styles": comp.styles,
                    "dependencies": comp.dependencies,
                }
                for name, comp in self.components.items()
            },
        }


class RegistryManager:
    """
    Manages custom component registries.
    
    Stores registry configuration in .pynext/registries.json
    """
    
    def __init__(self, project_dir: str | Path = "."):
        self.project_dir = Path(project_dir).resolve()
        self.config_dir = self.project_dir / ".pynext"
        self.config_file = self.config_dir / "registries.json"
        self._registries: dict[str, Registry] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load registry configuration from disk."""
        if self.config_file.exists():
            try:
                data = json.loads(self.config_file.read_text())
                for name, reg_data in data.get("registries", {}).items():
                    self._registries[name] = Registry.from_json(reg_data)
            except (json.JSONDecodeError, KeyError):
                self._registries = {}
    
    def _save_config(self) -> None:
        """Save registry configuration to disk."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        data = {
            "registries": {
                name: reg.to_json()
                for name, reg in self._registries.items()
            }
        }
        self.config_file.write_text(json.dumps(data, indent=2))
    
    def add_registry(self, name: str, url: str) -> Registry:
        """
        Add a custom registry.
        
        Args:
            name: Registry name (e.g., "acme-ui")
            url: Registry URL (https:// or github:owner/repo)
        
        Returns:
            The added Registry
        """
        # Fetch registry metadata
        registry = self._fetch_registry_metadata(name, url)
        self._registries[name] = registry
        self._save_config()
        return registry
    
    def remove_registry(self, name: str) -> bool:
        """
        Remove a custom registry.
        
        Args:
            name: Registry name to remove
        
        Returns:
            True if removed, False if not found
        """
        if name not in self._registries:
            return False
        
        del self._registries[name]
        self._save_config()
        return True
    
    def list_registries(self) -> list[Registry]:
        """List all registered custom registries."""
        return list(self._registries.values())
    
    def get_registry(self, name: str) -> Optional[Registry]:
        """Get a registry by name."""
        return self._registries.get(name)
    
    def install_component(
        self,
        registry_name: str,
        component_name: str,
        output_subdir: Optional[str] = None,
    ) -> list[Path]:
        """
        Install a component from a custom registry.
        
        Args:
            registry_name: Name of the registry
            component_name: Name of the component to install
            output_subdir: Custom output directory (default: components/{registry_name})
        
        Returns:
            List of installed file paths
        """
        registry = self._registries.get(registry_name)
        if not registry:
            raise ValueError(f"Registry not found: {registry_name}")
        
        component = registry.components.get(component_name)
        if not component:
            raise ValueError(f"Component not found: {component_name} in {registry_name}")
        
        # Determine output directory
        if output_subdir is None:
            output_subdir = f"components/{registry_name}"
        
        output_dir = self.project_dir / output_subdir
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Fetch and install component files
        installed = self._fetch_component_files(registry, component, output_dir)
        
        # Handle dependencies
        self._handle_dependencies(component.dependencies)
        
        return installed
    
    def _fetch_registry_metadata(self, name: str, url: str) -> Registry:
        """
        Fetch registry metadata from URL.
        
        Supports:
        - https://... URLs (expects pynext-registry.json)
        - github:owner/repo format
        """
        if url.startswith("github:"):
            # Convert github:owner/repo to raw URL
            repo_path = url[7:]  # Remove 'github:'
            raw_url = f"https://raw.githubusercontent.com/{repo_path}/main/pynext-registry.json"
        else:
            # Assume it's a direct URL
            raw_url = url.rstrip("/") + "/pynext-registry.json"
        
        # For now, create a placeholder registry
        # In production, this would fetch from the URL
        # TODO: Add actual HTTP fetching with httpx/requests
        return Registry(
            name=name,
            url=url,
            version="1.0.0",
            description=f"Custom registry: {name}",
            components={},
        )
    
    def _fetch_component_files(
        self,
        registry: Registry,
        component: RegistryComponent,
        output_dir: Path,
    ) -> list[Path]:
        """
        Fetch component files from registry.
        
        Returns list of installed file paths.
        """
        installed = []
        
        # Parse registry URL
        if registry.url.startswith("github:"):
            repo_path = registry.url[7:]
            base_url = f"https://raw.githubusercontent.com/{repo_path}/main/"
        else:
            base_url = registry.url.rstrip("/") + "/"
        
        # In production, fetch each file
        # For now, create placeholder files
        for file_name in component.files:
            file_path = output_dir / file_name
            
            # TODO: Fetch actual content
            # content = httpx.get(base_url + file_name).text
            content = f'''"""
{component.name} - {component.description}

Downloaded from: {registry.name} ({registry.url})

TODO: This is a placeholder. In production, this would be fetched from the registry.
"""

# Component implementation would go here
'''
            
            file_path.write_text(content)
            installed.append(file_path)
        
        # Handle styles
        if component.styles:
            styles_path = output_dir / component.styles
            styles_path.write_text(f"/* Styles for {component.name} */\n")
            installed.append(styles_path)
        
        return installed
    
    def _handle_dependencies(self, dependencies: dict) -> None:
        """
        Handle component dependencies.
        
        Updates pynext.requirements.txt and pynext.npm.txt as needed.
        """
        python_deps = dependencies.get("pynext", [])
        npm_deps = dependencies.get("npm", [])
        
        if python_deps:
            req_file = self.project_dir / "pynext.requirements.txt"
            if req_file.exists():
                existing = req_file.read_text()
                for dep in python_deps:
                    if dep not in existing:
                        with open(req_file, "a") as f:
                            f.write(f"\n{dep}")
        
        if npm_deps:
            npm_file = self.project_dir / "pynext.npm.txt"
            if npm_file.exists():
                existing = npm_file.read_text()
                for dep in npm_deps:
                    if dep not in existing:
                        with open(npm_file, "a") as f:
                            f.write(f"\n{dep}")


def create_registry_template(output_path: Path) -> None:
    """
    Create a template pynext-registry.json for publishing a component library.
    """
    template = {
        "name": "my-components",
        "version": "1.0.0",
        "description": "My custom PyNext component library",
        "author": "Your Name",
        "base_styles": "styles/theme.css",
        "components": {
            "example-card": {
                "name": "ExampleCard",
                "description": "An example card component",
                "files": ["example_card.py"],
                "styles": "example_card.css",
                "dependencies": {
                    "pynext": ["pynext.shadcn.card"],
                    "npm": []
                }
            }
        }
    }
    
    output_path.write_text(json.dumps(template, indent=2))

