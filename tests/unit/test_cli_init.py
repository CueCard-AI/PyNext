"""
Tests for PyNext CLI init command.

Tests that `pynext init` creates the correct project structure including
the new dependency files.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


class TestInitCommand:
    """Tests for the init CLI command."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory."""
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
    
    def test_init_creates_project_directory(self, temp_dir):
        """Test that init creates the project directory."""
        project_name = "test-project"
        result = self.run_cli("init", project_name, cwd=str(temp_dir))
        
        assert result.returncode == 0
        project_dir = temp_dir / project_name
        assert project_dir.exists()
        assert project_dir.is_dir()
    
    def test_init_creates_pages_directory(self, temp_dir):
        """Test that init creates the pages directory with example pages."""
        project_name = "test-project"
        self.run_cli("init", project_name, cwd=str(temp_dir))
        
        project_dir = temp_dir / project_name
        pages_dir = project_dir / "pages"
        
        assert pages_dir.exists()
        assert (pages_dir / "index.py").exists()
        assert (pages_dir / "about.py").exists()
        assert (pages_dir / "users" / "[id].py").exists()
    
    def test_init_creates_public_directory(self, temp_dir):
        """Test that init creates the public directory."""
        project_name = "test-project"
        self.run_cli("init", project_name, cwd=str(temp_dir))
        
        project_dir = temp_dir / project_name
        public_dir = project_dir / "public"
        
        assert public_dir.exists()
        assert (public_dir / "styles.css").exists()
    
    def test_init_creates_components_directory(self, temp_dir):
        """Test that init creates the components directory."""
        project_name = "test-project"
        self.run_cli("init", project_name, cwd=str(temp_dir))
        
        project_dir = temp_dir / project_name
        assert (project_dir / "components").exists()
    
    def test_init_creates_config_file(self, temp_dir):
        """Test that init creates pynext.config.py."""
        project_name = "test-project"
        self.run_cli("init", project_name, cwd=str(temp_dir))
        
        project_dir = temp_dir / project_name
        config_file = project_dir / "pynext.config.py"
        
        assert config_file.exists()
        content = config_file.read_text()
        assert "PyNext Configuration" in content
    
    def test_init_creates_python_requirements(self, temp_dir):
        """Test that init creates pynext.requirements.txt."""
        project_name = "test-project"
        self.run_cli("init", project_name, cwd=str(temp_dir))
        
        project_dir = temp_dir / project_name
        req_file = project_dir / "pynext.requirements.txt"
        
        assert req_file.exists()
        content = req_file.read_text()
        assert "PyNext Python Dependencies" in content
        assert "pandas" in content  # Example in template
    
    def test_init_creates_npm_packages(self, temp_dir):
        """Test that init creates pynext.npm.txt."""
        project_name = "test-project"
        self.run_cli("init", project_name, cwd=str(temp_dir))
        
        project_dir = temp_dir / project_name
        npm_file = project_dir / "pynext.npm.txt"
        
        assert npm_file.exists()
        content = npm_file.read_text()
        assert "PyNext NPM Dependencies" in content
        assert "chart.js" in content  # Example in template
    
    def test_init_creates_gitignore(self, temp_dir):
        """Test that init creates .gitignore."""
        project_name = "test-project"
        self.run_cli("init", project_name, cwd=str(temp_dir))
        
        project_dir = temp_dir / project_name
        gitignore = project_dir / ".gitignore"
        
        assert gitignore.exists()
        content = gitignore.read_text()
        assert ".pynext/" in content
        assert "node_modules/" in content
    
    def test_init_fails_on_existing_nonempty_dir(self, temp_dir):
        """Test that init fails if directory exists and is not empty."""
        project_name = "test-project"
        project_dir = temp_dir / project_name
        project_dir.mkdir()
        (project_dir / "existing_file.txt").write_text("existing")
        
        result = self.run_cli("init", project_name, cwd=str(temp_dir))
        
        assert result.returncode == 1
        assert "already exists" in result.stdout or "already exists" in result.stderr
    
    def test_init_output_shows_next_steps(self, temp_dir):
        """Test that init output shows helpful next steps."""
        project_name = "test-project"
        result = self.run_cli("init", project_name, cwd=str(temp_dir))
        
        assert "Created PyNext project" in result.stdout
        assert f"cd {project_name}" in result.stdout
        assert "pynext dev" in result.stdout
    
    def test_init_output_shows_new_dependency_files(self, temp_dir):
        """Test that init output mentions dependency files."""
        project_name = "test-project"
        result = self.run_cli("init", project_name, cwd=str(temp_dir))
        
        assert "pynext.requirements.txt" in result.stdout
        assert "pynext.npm.txt" in result.stdout

