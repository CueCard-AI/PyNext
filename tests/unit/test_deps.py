"""
Tests for PyNext dependency management.

Tests the parsing and checking of pynext.requirements.txt and pynext.npm.txt files.
"""

import tempfile
from pathlib import Path

import pytest

from pynext.deps import (
    DependencyManager,
    NPMDependency,
    PythonDependency,
    create_dependency_templates,
    create_npm_packages_template,
    create_python_requirements_template,
)


class TestPythonDependencyParsing:
    """Tests for parsing Python dependencies."""
    
    def test_parse_simple_package(self):
        """Test parsing a simple package name."""
        dep = PythonDependency.parse("pandas")
        assert dep is not None
        assert dep.name == "pandas"
        assert dep.version_spec == ""
        assert str(dep) == "pandas"
    
    def test_parse_package_with_version(self):
        """Test parsing package with version specifier."""
        dep = PythonDependency.parse("pandas>=2.0.0")
        assert dep is not None
        assert dep.name == "pandas"
        assert dep.version_spec == ">=2.0.0"
        assert str(dep) == "pandas>=2.0.0"
    
    def test_parse_package_with_exact_version(self):
        """Test parsing package with exact version."""
        dep = PythonDependency.parse("numpy==1.24.0")
        assert dep is not None
        assert dep.name == "numpy"
        assert dep.version_spec == "==1.24.0"
    
    def test_parse_package_with_extras(self):
        """Test parsing package with extras."""
        dep = PythonDependency.parse("uvicorn[standard]>=0.24.0")
        assert dep is not None
        assert dep.name == "uvicorn[standard]"
        assert dep.version_spec == ">=0.24.0"
    
    def test_parse_comment_line(self):
        """Test that comment lines return None."""
        dep = PythonDependency.parse("# This is a comment")
        assert dep is None
    
    def test_parse_empty_line(self):
        """Test that empty lines return None."""
        dep = PythonDependency.parse("")
        assert dep is None
        dep = PythonDependency.parse("   ")
        assert dep is None
    
    def test_parse_hyphenated_package(self):
        """Test parsing package with hyphens."""
        dep = PythonDependency.parse("scikit-learn>=1.3.0")
        assert dep is not None
        assert dep.name == "scikit-learn"
        assert dep.version_spec == ">=1.3.0"


class TestNPMDependencyParsing:
    """Tests for parsing NPM dependencies."""
    
    def test_parse_simple_package(self):
        """Test parsing a simple package name."""
        dep = NPMDependency.parse("lodash")
        assert dep is not None
        assert dep.name == "lodash"
        assert dep.version == "latest"
        assert str(dep) == "lodash"
    
    def test_parse_package_with_version(self):
        """Test parsing package with version."""
        dep = NPMDependency.parse("chart.js@^4.4.0")
        assert dep is not None
        assert dep.name == "chart.js"
        assert dep.version == "^4.4.0"
        assert str(dep) == "chart.js@^4.4.0"
    
    def test_parse_scoped_package(self):
        """Test parsing scoped package (@scope/name)."""
        dep = NPMDependency.parse("@mui/material")
        assert dep is not None
        assert dep.name == "@mui/material"
        assert dep.version == "latest"
    
    def test_parse_scoped_package_with_version(self):
        """Test parsing scoped package with version."""
        dep = NPMDependency.parse("@mui/material@^5.14.0")
        assert dep is not None
        assert dep.name == "@mui/material"
        assert dep.version == "^5.14.0"
        assert str(dep) == "@mui/material@^5.14.0"
    
    def test_parse_scoped_package_complex(self):
        """Test parsing complex scoped package."""
        dep = NPMDependency.parse("@emotion/react@^11.0.0")
        assert dep is not None
        assert dep.name == "@emotion/react"
        assert dep.version == "^11.0.0"
    
    def test_parse_comment_line(self):
        """Test that comment lines return None."""
        dep = NPMDependency.parse("# Charts")
        assert dep is None
    
    def test_parse_empty_line(self):
        """Test that empty lines return None."""
        dep = NPMDependency.parse("")
        assert dep is None


class TestDependencyManager:
    """Tests for the DependencyManager class."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_load_empty_python_requirements(self, temp_project):
        """Test loading when no requirements file exists."""
        manager = DependencyManager(str(temp_project))
        deps = manager.load_python_requirements()
        assert deps == []
    
    def test_load_python_requirements(self, temp_project):
        """Test loading Python requirements from file."""
        req_file = temp_project / "pynext.requirements.txt"
        req_file.write_text("""
# Data processing
pandas>=2.0.0
numpy>=1.24.0

# ML
scikit-learn>=1.3.0
""")
        
        manager = DependencyManager(str(temp_project))
        deps = manager.load_python_requirements()
        
        assert len(deps) == 3
        assert deps[0].name == "pandas"
        assert deps[0].version_spec == ">=2.0.0"
        assert deps[1].name == "numpy"
        assert deps[2].name == "scikit-learn"
    
    def test_load_empty_npm_packages(self, temp_project):
        """Test loading when no npm file exists."""
        manager = DependencyManager(str(temp_project))
        deps = manager.load_npm_packages()
        assert deps == []
    
    def test_load_npm_packages(self, temp_project):
        """Test loading NPM packages from file."""
        npm_file = temp_project / "pynext.npm.txt"
        npm_file.write_text("""
# Charts
chart.js@^4.4.0
d3@^7.0.0

# UI
@mui/material@^5.14.0
""")
        
        manager = DependencyManager(str(temp_project))
        deps = manager.load_npm_packages()
        
        assert len(deps) == 3
        assert deps[0].name == "chart.js"
        assert deps[0].version == "^4.4.0"
        assert deps[1].name == "d3"
        assert deps[2].name == "@mui/material"
        assert deps[2].version == "^5.14.0"
    
    def test_check_python_deps_all_installed(self, temp_project):
        """Test checking Python deps when all are installed."""
        req_file = temp_project / "pynext.requirements.txt"
        req_file.write_text("json\n")  # json is always available
        
        manager = DependencyManager(str(temp_project))
        missing = manager.check_python_deps()
        
        # json module is always installed, so should not be missing
        # (Note: the check looks for import, json is built-in)
        assert len(missing) == 0
    
    def test_check_python_deps_missing(self, temp_project):
        """Test checking Python deps when some are missing."""
        req_file = temp_project / "pynext.requirements.txt"
        req_file.write_text("nonexistent-fake-package>=1.0.0\n")
        
        manager = DependencyManager(str(temp_project))
        missing = manager.check_python_deps()
        
        assert len(missing) == 1
        assert missing[0].name == "nonexistent-fake-package"
    
    def test_check_npm_deps_no_node_modules(self, temp_project):
        """Test checking NPM deps when node_modules doesn't exist."""
        npm_file = temp_project / "pynext.npm.txt"
        npm_file.write_text("lodash@^4.17.0\n")
        
        manager = DependencyManager(str(temp_project))
        missing = manager.check_npm_deps()
        
        assert len(missing) == 1
        assert missing[0].name == "lodash"
    
    def test_check_npm_deps_with_node_modules(self, temp_project):
        """Test checking NPM deps when some are installed."""
        npm_file = temp_project / "pynext.npm.txt"
        npm_file.write_text("lodash@^4.17.0\nchart.js@^4.0.0\n")
        
        # Create node_modules with only lodash
        node_modules = temp_project / "node_modules"
        node_modules.mkdir()
        (node_modules / "lodash").mkdir()
        
        manager = DependencyManager(str(temp_project))
        missing = manager.check_npm_deps()
        
        assert len(missing) == 1
        assert missing[0].name == "chart.js"
    
    def test_check_all(self, temp_project):
        """Test checking all dependencies."""
        (temp_project / "pynext.requirements.txt").write_text("fake-pkg>=1.0.0\n")
        (temp_project / "pynext.npm.txt").write_text("fake-npm@^1.0.0\n")
        
        manager = DependencyManager(str(temp_project))
        missing = manager.check_all()
        
        assert "python" in missing
        assert "npm" in missing
        assert len(missing["python"]) == 1
        assert len(missing["npm"]) == 1
    
    def test_has_dependencies_false(self, temp_project):
        """Test has_dependencies when no files exist."""
        manager = DependencyManager(str(temp_project))
        assert manager.has_dependencies() is False
    
    def test_has_dependencies_true_python(self, temp_project):
        """Test has_dependencies when Python file exists."""
        (temp_project / "pynext.requirements.txt").write_text("")
        manager = DependencyManager(str(temp_project))
        assert manager.has_dependencies() is True
    
    def test_has_dependencies_true_npm(self, temp_project):
        """Test has_dependencies when NPM file exists."""
        (temp_project / "pynext.npm.txt").write_text("")
        manager = DependencyManager(str(temp_project))
        assert manager.has_dependencies() is True


class TestTemplateGeneration:
    """Tests for dependency template generation."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_create_python_requirements_template(self, temp_project):
        """Test creating Python requirements template."""
        path = create_python_requirements_template(str(temp_project))
        
        assert path.exists()
        assert path.name == "pynext.requirements.txt"
        content = path.read_text()
        assert "PyNext Python Dependencies" in content
        assert "pandas" in content  # Example in template
    
    def test_create_npm_packages_template(self, temp_project):
        """Test creating NPM packages template."""
        path = create_npm_packages_template(str(temp_project))
        
        assert path.exists()
        assert path.name == "pynext.npm.txt"
        content = path.read_text()
        assert "PyNext NPM Dependencies" in content
        assert "chart.js" in content  # Example in template
    
    def test_create_dependency_templates(self, temp_project):
        """Test creating both templates."""
        python_path, npm_path = create_dependency_templates(str(temp_project))
        
        assert python_path.exists()
        assert npm_path.exists()
        assert python_path.name == "pynext.requirements.txt"
        assert npm_path.name == "pynext.npm.txt"
    
    def test_template_not_overwritten(self, temp_project):
        """Test that existing files are not overwritten."""
        existing = temp_project / "pynext.requirements.txt"
        existing.write_text("existing content")
        
        path = create_python_requirements_template(str(temp_project))
        
        assert path.read_text() == "existing content"

