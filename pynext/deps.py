"""
PyNext Dependency Manager.

Manages Python and NPM dependencies for PyNext applications using simple
text-based formats similar to requirements.txt.

Files:
    - pynext.requirements.txt: Python dependencies (pip format)
    - pynext.npm.txt: NPM dependencies (package@version format)
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class PythonDependency:
    """Represents a Python package dependency."""
    name: str
    version_spec: str = ""  # e.g., ">=2.0.0", "==1.5.0", ""
    
    def __str__(self) -> str:
        return f"{self.name}{self.version_spec}" if self.version_spec else self.name
    
    @classmethod
    def parse(cls, line: str) -> Optional["PythonDependency"]:
        """Parse a requirements.txt line into a PythonDependency."""
        line = line.strip()
        if not line or line.startswith("#"):
            return None
        
        # Handle extras like package[extra]>=1.0.0
        # Match: package_name[extras]version_spec
        match = re.match(r'^([a-zA-Z0-9_-]+(?:\[[^\]]+\])?)(.*)?$', line)
        if match:
            name = match.group(1)
            version_spec = match.group(2) or ""
            return cls(name=name, version_spec=version_spec.strip())
        return None


@dataclass
class NPMDependency:
    """Represents an NPM package dependency."""
    name: str
    version: str = "latest"  # e.g., "^4.4.0", "~1.0.0", "latest"
    
    def __str__(self) -> str:
        return f"{self.name}@{self.version}" if self.version != "latest" else self.name
    
    @classmethod
    def parse(cls, line: str) -> Optional["NPMDependency"]:
        """Parse a pynext.npm.txt line into an NPMDependency."""
        line = line.strip()
        if not line or line.startswith("#"):
            return None
        
        # Handle scoped packages: @scope/package@version
        # and regular packages: package@version
        if line.startswith("@"):
            # Scoped package: @scope/name@version
            # Find the last @ that's not at the start
            at_positions = [i for i, c in enumerate(line) if c == "@"]
            if len(at_positions) >= 2:
                # Has version spec
                last_at = at_positions[-1]
                name = line[:last_at]
                version = line[last_at + 1:]
            else:
                # No version, just @scope/name
                name = line
                version = "latest"
        else:
            # Regular package: name@version or just name
            if "@" in line:
                name, version = line.rsplit("@", 1)
            else:
                name = line
                version = "latest"
        
        return cls(name=name, version=version)


class DependencyManager:
    """
    Manages Python and NPM dependencies for a PyNext application.
    
    Usage:
        deps = DependencyManager("/path/to/project")
        
        # Load dependencies
        python_deps = deps.load_python_requirements()
        npm_deps = deps.load_npm_packages()
        
        # Check what's missing
        missing_python = deps.check_python_deps()
        missing_npm = deps.check_npm_deps()
        
        # Install dependencies
        deps.install_python_deps()
        deps.install_npm_deps()
    """
    
    PYTHON_REQUIREMENTS_FILE = "pynext.requirements.txt"
    NPM_PACKAGES_FILE = "pynext.npm.txt"
    
    def __init__(self, project_dir: str = "."):
        self.project_dir = Path(project_dir).resolve()
        self.python_requirements_path = self.project_dir / self.PYTHON_REQUIREMENTS_FILE
        self.npm_packages_path = self.project_dir / self.NPM_PACKAGES_FILE
    
    # =========================================================================
    # Python Dependencies
    # =========================================================================
    
    def load_python_requirements(self) -> list[PythonDependency]:
        """
        Load Python dependencies from pynext.requirements.txt.
        
        Returns:
            List of PythonDependency objects
        """
        if not self.python_requirements_path.exists():
            return []
        
        deps = []
        for line in self.python_requirements_path.read_text().splitlines():
            dep = PythonDependency.parse(line)
            if dep:
                deps.append(dep)
        return deps
    
    def check_python_deps(self) -> list[PythonDependency]:
        """
        Check which Python dependencies are missing.
        
        Returns:
            List of missing PythonDependency objects
        """
        required = self.load_python_requirements()
        if not required:
            return []
        
        missing = []
        for dep in required:
            # Extract base package name (without extras)
            base_name = dep.name.split("[")[0]
            try:
                __import__(base_name.replace("-", "_"))
            except ImportError:
                # Try using pkg_resources or importlib.metadata
                try:
                    from importlib.metadata import distribution
                    distribution(base_name)
                except Exception:
                    missing.append(dep)
        
        return missing
    
    def install_python_deps(self, quiet: bool = False) -> bool:
        """
        Install Python dependencies using pip.
        
        Args:
            quiet: Suppress pip output
        
        Returns:
            True if successful, False otherwise
        """
        if not self.python_requirements_path.exists():
            return True  # Nothing to install
        
        cmd = ["pip", "install", "-r", str(self.python_requirements_path)]
        if quiet:
            cmd.append("-q")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_dir)
            )
            if result.returncode != 0 and not quiet:
                print(f"[PyNext] pip install error: {result.stderr}")
            return result.returncode == 0
        except Exception as e:
            if not quiet:
                print(f"[PyNext] Error installing Python deps: {e}")
            return False
    
    # =========================================================================
    # NPM Dependencies
    # =========================================================================
    
    def load_npm_packages(self) -> list[NPMDependency]:
        """
        Load NPM dependencies from pynext.npm.txt.
        
        Returns:
            List of NPMDependency objects
        """
        if not self.npm_packages_path.exists():
            return []
        
        deps = []
        for line in self.npm_packages_path.read_text().splitlines():
            dep = NPMDependency.parse(line)
            if dep:
                deps.append(dep)
        return deps
    
    def check_npm_deps(self) -> list[NPMDependency]:
        """
        Check which NPM dependencies are missing.
        
        Returns:
            List of missing NPMDependency objects
        """
        required = self.load_npm_packages()
        if not required:
            return []
        
        node_modules = self.project_dir / "node_modules"
        if not node_modules.exists():
            return required  # All missing
        
        missing = []
        for dep in required:
            # Check if package directory exists in node_modules
            pkg_path = node_modules / dep.name
            if not pkg_path.exists():
                missing.append(dep)
        
        return missing
    
    def install_npm_deps(self, quiet: bool = False) -> bool:
        """
        Install NPM dependencies.
        
        Creates/updates package.json and runs npm install.
        
        Args:
            quiet: Suppress npm output
        
        Returns:
            True if successful, False otherwise
        """
        packages = self.load_npm_packages()
        if not packages:
            return True  # Nothing to install
        
        # Check if npm is available
        if not shutil.which("npm"):
            if not quiet:
                print("[PyNext] npm not found. Please install Node.js.")
            return False
        
        # Create or update package.json
        package_json_path = self.project_dir / "package.json"
        if package_json_path.exists():
            package_json = json.loads(package_json_path.read_text())
        else:
            package_json = {
                "name": "pynext-app",
                "private": True,
                "type": "module",
                "dependencies": {}
            }
        
        # Add dependencies
        for pkg in packages:
            package_json.setdefault("dependencies", {})[pkg.name] = pkg.version
        
        # Write package.json
        package_json_path.write_text(json.dumps(package_json, indent=2))
        
        # Run npm install
        cmd = ["npm", "install"]
        if quiet:
            cmd.append("--silent")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_dir)
            )
            if result.returncode != 0 and not quiet:
                print(f"[PyNext] npm install error: {result.stderr}")
            return result.returncode == 0
        except Exception as e:
            if not quiet:
                print(f"[PyNext] Error installing NPM deps: {e}")
            return False
    
    # =========================================================================
    # Combined Operations
    # =========================================================================
    
    def install_all(self, quiet: bool = False) -> bool:
        """
        Install both Python and NPM dependencies.
        
        Returns:
            True if all installations successful
        """
        python_ok = self.install_python_deps(quiet=quiet)
        npm_ok = self.install_npm_deps(quiet=quiet)
        return python_ok and npm_ok
    
    def check_all(self) -> dict[str, list]:
        """
        Check all dependencies.
        
        Returns:
            Dict with 'python' and 'npm' keys containing missing deps
        """
        return {
            "python": self.check_python_deps(),
            "npm": self.check_npm_deps()
        }
    
    def has_dependencies(self) -> bool:
        """Check if any dependency files exist."""
        return (
            self.python_requirements_path.exists() or
            self.npm_packages_path.exists()
        )
    
    def print_status(self) -> None:
        """Print dependency status to console."""
        missing = self.check_all()
        
        if not missing["python"] and not missing["npm"]:
            print("[PyNext] All dependencies installed ✓")
            return
        
        if missing["python"]:
            print(f"[PyNext] Missing Python packages: {', '.join(str(d) for d in missing['python'])}")
        if missing["npm"]:
            print(f"[PyNext] Missing NPM packages: {', '.join(str(d) for d in missing['npm'])}")
        print("[PyNext] Run 'pynext deps install' to install missing dependencies")


# =============================================================================
# Template Generation
# =============================================================================

PYTHON_REQUIREMENTS_TEMPLATE = """\
# PyNext Python Dependencies
# 
# Add Python packages needed for your Server Actions here.
# Uses standard pip requirements.txt format.
#
# Examples:
#   pandas>=2.0.0
#   numpy>=1.24.0
#   scikit-learn>=1.3.0
#   sqlalchemy>=2.0.0
#   requests>=2.31.0

# Add your dependencies below:

"""

NPM_PACKAGES_TEMPLATE = """\
# PyNext NPM Dependencies
#
# Add NPM packages for client-side JavaScript here.
# Format: package@version or @scope/package@version
#
# Examples:
#   chart.js@^4.4.0
#   lodash@^4.17.0
#   d3@^7.0.0
#   @mui/material@^5.14.0
#
# React packages are auto-detected and use Preact (~4KB) under the hood.

# Add your dependencies below:

"""


def create_python_requirements_template(project_dir: str = ".") -> Path:
    """Create a template pynext.requirements.txt file."""
    path = Path(project_dir) / DependencyManager.PYTHON_REQUIREMENTS_FILE
    if not path.exists():
        path.write_text(PYTHON_REQUIREMENTS_TEMPLATE)
    return path


def create_npm_packages_template(project_dir: str = ".") -> Path:
    """Create a template pynext.npm.txt file."""
    path = Path(project_dir) / DependencyManager.NPM_PACKAGES_FILE
    if not path.exists():
        path.write_text(NPM_PACKAGES_TEMPLATE)
    return path


def create_dependency_templates(project_dir: str = ".") -> tuple[Path, Path]:
    """Create both dependency template files."""
    return (
        create_python_requirements_template(project_dir),
        create_npm_packages_template(project_dir)
    )


# =============================================================================
# Convenience Functions
# =============================================================================

_manager: Optional[DependencyManager] = None


def get_dependency_manager(project_dir: str = ".") -> DependencyManager:
    """Get the global dependency manager instance."""
    global _manager
    if _manager is None or str(_manager.project_dir) != str(Path(project_dir).resolve()):
        _manager = DependencyManager(project_dir)
    return _manager


def check_deps(project_dir: str = ".") -> dict[str, list]:
    """Quick check for missing dependencies."""
    return get_dependency_manager(project_dir).check_all()


def install_deps(project_dir: str = ".", quiet: bool = False) -> bool:
    """Quick install all dependencies."""
    return get_dependency_manager(project_dir).install_all(quiet=quiet)

