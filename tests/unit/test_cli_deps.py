"""
Tests for PyNext CLI dependency commands.

Tests the `pynext deps` subcommands (install, check, init).
"""

import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


class TestDepsCommand:
    """Tests for the deps CLI command."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def run_cli(self, *args, cwd=None):
        """Run the pynext CLI with given arguments."""
        cmd = [sys.executable, "-m", "pynext.cli"] + list(args)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd
        )
        return result
    
    def test_deps_check_no_files(self, temp_project):
        """Test deps check when no dependency files exist."""
        result = self.run_cli("deps", "check", "--dir", str(temp_project))
        # Should succeed with no dependencies to check
        assert result.returncode == 0
        assert "All dependencies installed" in result.stdout
    
    def test_deps_check_missing_python(self, temp_project):
        """Test deps check reports missing Python packages."""
        # Create requirements with a fake package
        req_file = temp_project / "pynext.requirements.txt"
        req_file.write_text("nonexistent-fake-package>=1.0.0\n")
        
        result = self.run_cli("deps", "check", "--dir", str(temp_project))
        
        assert result.returncode == 1
        assert "Missing Python packages" in result.stdout
        assert "nonexistent-fake-package" in result.stdout
    
    def test_deps_check_missing_npm(self, temp_project):
        """Test deps check reports missing NPM packages."""
        # Create npm file with a package
        npm_file = temp_project / "pynext.npm.txt"
        npm_file.write_text("fake-npm-package@^1.0.0\n")
        
        result = self.run_cli("deps", "check", "--dir", str(temp_project))
        
        assert result.returncode == 1
        assert "Missing NPM packages" in result.stdout
        assert "fake-npm-package" in result.stdout
    
    def test_deps_init_creates_files(self, temp_project):
        """Test deps init creates template files."""
        result = self.run_cli("deps", "init", "--dir", str(temp_project))
        
        assert result.returncode == 0
        assert (temp_project / "pynext.requirements.txt").exists()
        assert (temp_project / "pynext.npm.txt").exists()
        
        # Check content has examples
        python_content = (temp_project / "pynext.requirements.txt").read_text()
        assert "pandas" in python_content
        
        npm_content = (temp_project / "pynext.npm.txt").read_text()
        assert "chart.js" in npm_content
    
    def test_deps_install_no_deps(self, temp_project):
        """Test deps install when no dependency files exist."""
        result = self.run_cli("deps", "install", "--dir", str(temp_project))
        
        # Should succeed with nothing to install
        assert result.returncode == 0


class TestDepsInstallPython:
    """Tests for Python dependency installation."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def run_cli(self, *args, cwd=None):
        """Run the pynext CLI with given arguments."""
        cmd = [sys.executable, "-m", "pynext.cli"] + list(args)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd
        )
        return result
    
    def test_deps_install_python_only_flag(self, temp_project):
        """Test --python flag only installs Python deps."""
        # Create both files
        (temp_project / "pynext.requirements.txt").write_text("")
        (temp_project / "pynext.npm.txt").write_text("lodash@^4.0.0\n")
        
        result = self.run_cli("deps", "install", "--python", "--dir", str(temp_project))
        
        assert result.returncode == 0
        assert "Python dependencies installed" in result.stdout
        # NPM should not be mentioned as installed
        assert "NPM dependencies installed" not in result.stdout


class TestDepsInstallNPM:
    """Tests for NPM dependency installation."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def run_cli(self, *args, cwd=None):
        """Run the pynext CLI with given arguments."""
        cmd = [sys.executable, "-m", "pynext.cli"] + list(args)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd
        )
        return result
    
    def test_deps_install_npm_only_flag(self, temp_project):
        """Test --npm flag only installs NPM deps."""
        # Create both files
        (temp_project / "pynext.requirements.txt").write_text("fake-pkg>=1.0.0\n")
        (temp_project / "pynext.npm.txt").write_text("")
        
        result = self.run_cli("deps", "install", "--npm", "--dir", str(temp_project))
        
        assert result.returncode == 0
        assert "NPM dependencies installed" in result.stdout
        # Python should not be mentioned as installed
        assert "Python dependencies installed" not in result.stdout

