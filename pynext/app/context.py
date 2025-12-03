"""
Context Analyzer - Analyzes existing PyNext projects.

Builds understanding of project structure, models, pages,
components to enable intelligent feature additions.

Example:
    analyzer = ContextAnalyzer()
    context = await analyzer.analyze(Path("./my-project"))
    
    print(context.pages)
    print(context.models)
    print(context.components)
"""

import ast
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import logging

logger = logging.getLogger(__name__)


@dataclass
class ProjectContext:
    """
    Understanding of an existing project.
    
    Attributes:
        root: Project root path
        structure: File tree structure
        models: Database model names
        pages: Page file paths
        components: Component file paths
        islands: Island component paths
        apis: API route paths
        dependencies: Package dependencies
        config: Project configuration
    """
    root: Path
    structure: Dict[str, Any] = field(default_factory=dict)
    models: List[str] = field(default_factory=list)
    pages: List[str] = field(default_factory=list)
    components: List[str] = field(default_factory=list)
    islands: List[str] = field(default_factory=list)
    apis: List[str] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    middlewares: List[str] = field(default_factory=list)
    dependencies: Dict[str, str] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "root": str(self.root),
            "structure": self.structure,
            "models": self.models,
            "pages": self.pages,
            "components": self.components,
            "islands": self.islands,
            "apis": self.apis,
            "actions": self.actions,
            "middlewares": self.middlewares,
            "dependencies": self.dependencies,
            "config": self.config,
        }
    
    def get_summary(self) -> str:
        """Get a summary of the project."""
        lines = [
            f"Project: {self.root.name}",
            f"Pages: {len(self.pages)}",
            f"Components: {len(self.components)}",
            f"Islands: {len(self.islands)}",
            f"Models: {len(self.models)}",
            f"APIs: {len(self.apis)}",
        ]
        return "\n".join(lines)


class ContextAnalyzer:
    """
    Analyzes existing PyNext projects.
    
    Scans project structure, identifies components,
    parses code to understand the codebase.
    """
    
    def __init__(self):
        """Initialize analyzer."""
        pass
    
    async def analyze(self, project_path: Path) -> ProjectContext:
        """
        Analyze a PyNext project.
        
        Args:
            project_path: Path to project root
        
        Returns:
            ProjectContext with full analysis
        """
        project_path = Path(project_path).resolve()
        
        if not project_path.exists():
            raise ValueError(f"Project path does not exist: {project_path}")
        
        context = ProjectContext(root=project_path)
        
        # Build file structure
        context.structure = self._scan_structure(project_path)
        
        # Find pages
        pages_dir = project_path / "pages"
        if pages_dir.exists():
            context.pages = self._find_files(pages_dir, ".py")
        
        # Find components
        components_dir = project_path / "components"
        if components_dir.exists():
            context.components = self._find_files(components_dir, ".py")
        
        # Find islands
        islands_dir = project_path / "islands"
        if islands_dir.exists():
            context.islands = self._find_files(islands_dir, ".py")
        
        # Find models
        models_dir = project_path / "models"
        if models_dir.exists():
            context.models = self._find_files(models_dir, ".py")
            # Also extract model class names
            context.models = await self._extract_model_names(models_dir)
        
        # Find APIs
        api_dir = project_path / "api"
        if api_dir.exists():
            context.apis = self._find_files(api_dir, ".py")
        
        # Find actions
        actions_dir = project_path / "actions"
        if actions_dir.exists():
            context.actions = self._find_files(actions_dir, ".py")
        
        # Find middleware
        middleware_dir = project_path / "middleware"
        if middleware_dir.exists():
            context.middlewares = self._find_files(middleware_dir, ".py")
        
        # Load dependencies
        context.dependencies = self._load_dependencies(project_path)
        
        # Load config
        context.config = self._load_config(project_path)
        
        return context
    
    def _scan_structure(self, path: Path, max_depth: int = 4) -> Dict[str, Any]:
        """Scan directory structure."""
        structure = {}
        
        try:
            for item in path.iterdir():
                if item.name.startswith(".") or item.name == "__pycache__":
                    continue
                
                if item.is_dir() and max_depth > 0:
                    structure[item.name] = self._scan_structure(item, max_depth - 1)
                elif item.is_file():
                    structure[item.name] = "file"
        except PermissionError:
            pass
        
        return structure
    
    def _find_files(self, directory: Path, extension: str) -> List[str]:
        """Find files with given extension."""
        files = []
        
        try:
            for item in directory.rglob(f"*{extension}"):
                if "__pycache__" not in str(item):
                    rel_path = item.relative_to(directory.parent)
                    files.append(str(rel_path))
        except Exception as e:
            logger.warning(f"Error scanning {directory}: {e}")
        
        return files
    
    async def _extract_model_names(self, models_dir: Path) -> List[str]:
        """Extract model class names from files."""
        model_names = []
        
        for py_file in models_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            
            try:
                content = py_file.read_text(encoding="utf-8")
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # Check if it inherits from Table
                        for base in node.bases:
                            if isinstance(base, ast.Name) and base.id == "Table":
                                model_names.append(node.name)
                                break
            except Exception as e:
                logger.warning(f"Error parsing {py_file}: {e}")
        
        return model_names
    
    def _load_dependencies(self, project_path: Path) -> Dict[str, str]:
        """Load project dependencies."""
        deps = {}
        
        # Check requirements.txt
        req_file = project_path / "requirements.txt"
        if req_file.exists():
            try:
                content = req_file.read_text(encoding="utf-8")
                for line in content.split("\n"):
                    line = line.strip()
                    if line and not line.startswith("#"):
                        # Parse package==version or package
                        if "==" in line:
                            pkg, version = line.split("==", 1)
                            deps[pkg.strip()] = version.strip()
                        else:
                            deps[line] = "*"
            except Exception:
                pass
        
        # Check pyproject.toml
        pyproject = project_path / "pyproject.toml"
        if pyproject.exists():
            try:
                import tomllib
                content = pyproject.read_bytes()
                data = tomllib.loads(content.decode("utf-8"))
                
                # Look for dependencies
                if "project" in data and "dependencies" in data["project"]:
                    for dep in data["project"]["dependencies"]:
                        if "==" in dep:
                            pkg, version = dep.split("==", 1)
                            deps[pkg.strip()] = version.strip()
                        else:
                            deps[dep.split("[")[0].split(">=")[0].strip()] = "*"
            except Exception:
                pass
        
        return deps
    
    def _load_config(self, project_path: Path) -> Dict[str, Any]:
        """Load project configuration."""
        config = {}
        
        # Check pynext.toml
        pynext_config = project_path / "pynext.toml"
        if pynext_config.exists():
            try:
                import tomllib
                content = pynext_config.read_bytes()
                config = tomllib.loads(content.decode("utf-8"))
            except Exception:
                pass
        
        return config
    
    def get_relevant_files(
        self,
        context: ProjectContext,
        feature: str,
    ) -> List[Path]:
        """
        Find files relevant to a feature request.
        
        Args:
            context: Project context
            feature: Feature description
        
        Returns:
            List of relevant file paths
        """
        relevant = []
        feature_lower = feature.lower()
        
        # Keywords to file types
        if any(w in feature_lower for w in ["page", "route", "view"]):
            relevant.extend([context.root / p for p in context.pages])
        
        if any(w in feature_lower for w in ["component", "ui", "element"]):
            relevant.extend([context.root / p for p in context.components])
        
        if any(w in feature_lower for w in ["interactive", "client", "island"]):
            relevant.extend([context.root / p for p in context.islands])
        
        if any(w in feature_lower for w in ["database", "model", "table"]):
            # Get model files
            models_dir = context.root / "models"
            if models_dir.exists():
                relevant.extend(list(models_dir.glob("*.py")))
        
        if any(w in feature_lower for w in ["api", "endpoint"]):
            relevant.extend([context.root / p for p in context.apis])
        
        if any(w in feature_lower for w in ["auth", "login", "middleware"]):
            relevant.extend([context.root / p for p in context.middlewares])
        
        # Filter to existing files
        return [f for f in relevant if f.exists()]
    
    def get_imports_for_file(
        self,
        context: ProjectContext,
        file_type: str,
    ) -> List[str]:
        """
        Get suggested imports for a file type.
        
        Args:
            context: Project context
            file_type: Type of file (page, component, etc.)
        
        Returns:
            List of import statements
        """
        imports = ["from pynext import div, h1, p"]
        
        if file_type in ("island", "interactive"):
            imports.append("from pynext import Signal")
            imports.append("from pynext.islands import island")
        
        if file_type == "api":
            imports.append("from pynext.api import api, Request, Response")
        
        if file_type == "action":
            imports.append("from pynext.actions import action, ActionError")
        
        if file_type == "model":
            imports.append("from pynext.db import Table, Column, types")
        
        if file_type == "middleware":
            imports.append("from pynext.middleware import middleware, redirect")
        
        # Add model imports if models exist
        if context.models and file_type in ("page", "api", "action"):
            for model in context.models[:3]:
                imports.append(f"from models.{model.lower()} import {model}")
        
        return imports

