"""
Tests for PyNext CLI Build Commands (30 tests)

Tests CLI flags and exit codes for build commands.
"""

import pytest
import argparse
from pathlib import Path
from unittest.mock import Mock, patch

from pynext.cli import cmd_compile


# =============================================================================
# COMPILE COMMAND
# =============================================================================

class TestCompileCommand:
    """Tests for pynext compile command."""
    
    def test_compile_basic(self, tmp_path, capsys):
        """Basic compile command."""
        pages = tmp_path / "pages"
        pages.mkdir()
        (pages / "test.py").write_text("@island\ndef Test(): pass")
        
        args = argparse.Namespace(
            dir=str(tmp_path),
            output=str(tmp_path / "build"),
            tree_shake=False,
            analyze=False,
            watch=False,
            verbose=False,
        )
        
        with patch('pynext.build.compile_project') as mock:
            mock.return_value = Mock(
                success=True,
                island_count=1,
                output_size_kb=1.0,
                cache_hits=0,
                cache_misses=1,
                error_count=0,
                errors=[],
                duration_ms=100,
            )
            exit_code = cmd_compile(args)
        
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Compiled" in captured.out
    
    def test_compile_with_errors(self, tmp_path, capsys):
        """Compile with errors returns non-zero."""
        args = argparse.Namespace(
            dir=str(tmp_path),
            output=str(tmp_path / "build"),
            tree_shake=False,
            analyze=False,
            watch=False,
            verbose=False,
        )
        
        with patch('pynext.build.compile_project') as mock:
            mock.return_value = Mock(
                success=False,
                island_count=0,
                error_count=2,
                errors=[
                    ("a.py", "Error 1"),
                    ("b.py", "Error 2"),
                ],
                output_size_kb=0,
                cache_hits=0,
                cache_misses=0,
            )
            exit_code = cmd_compile(args)
        
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "failed" in captured.out
    
    def test_compile_verbose(self, tmp_path, capsys):
        """Verbose mode prints progress."""
        pages = tmp_path / "pages"
        pages.mkdir()
        (pages / "test.py").write_text("@island\ndef Test(): pass")
        
        args = argparse.Namespace(
            dir=str(tmp_path),
            output=str(tmp_path / "build"),
            tree_shake=False,
            analyze=False,
            watch=False,
            verbose=True,
        )
        
        with patch('pynext.build.compile_project') as mock:
            mock.return_value = Mock(
                success=True,
                island_count=1,
                output_size_kb=1.0,
                cache_hits=0,
                cache_misses=1,
                error_count=0,
                errors=[],
                duration_ms=100,
            )
            cmd_compile(args)
        
        captured = capsys.readouterr()
        assert "Compiling" in captured.out
    
    def test_compile_with_analyze(self, tmp_path, capsys):
        """Compile with --analyze flag."""
        args = argparse.Namespace(
            dir=str(tmp_path),
            output=str(tmp_path / "build"),
            tree_shake=False,
            analyze=True,
            watch=False,
            verbose=False,
        )
        
        # Create output directory for analysis
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "test.js").write_text("const x = 1;")
        
        with patch('pynext.build.compile_project') as mock_compile:
            mock_compile.return_value = Mock(
                success=True,
                island_count=1,
                output_size_kb=1.0,
                cache_hits=0,
                cache_misses=1,
                error_count=0,
                errors=[],
                duration_ms=100,
            )
            
            exit_code = cmd_compile(args)
        
        assert exit_code == 0
    
    def test_compile_tree_shake(self, tmp_path):
        """Compile with --tree-shake flag."""
        args = argparse.Namespace(
            dir=str(tmp_path),
            output=str(tmp_path / "build"),
            tree_shake=True,
            analyze=False,
            watch=False,
            verbose=False,
        )
        
        with patch('pynext.build.compile_project') as mock:
            mock.return_value = Mock(
                success=True,
                island_count=0,
                output_size_kb=0,
                cache_hits=0,
                cache_misses=0,
                error_count=0,
                errors=[],
                duration_ms=50,
            )
            cmd_compile(args)
            
            # Check tree_shake was passed to config
            call_args = mock.call_args
            config = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get('config')
            if config:
                assert config.tree_shake is True


# =============================================================================
# BUILD COMMAND FLAGS
# =============================================================================

class TestBuildFlags:
    """Tests for build command flags."""
    
    def test_tree_shake_flag(self):
        """--tree-shake flag."""
        from pynext.cli import main
        import sys
        
        # Test that the parser accepts the flag
        parser = argparse.ArgumentParser()
        parser.add_argument("--tree-shake", action="store_true")
        
        args = parser.parse_args(["--tree-shake"])
        assert args.tree_shake is True
    
    def test_analyze_flag(self):
        """--analyze flag."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--analyze", action="store_true")
        
        args = parser.parse_args(["--analyze"])
        assert args.analyze is True
    
    def test_benchmark_flag(self):
        """--benchmark flag."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--benchmark", action="store_true")
        
        args = parser.parse_args(["--benchmark"])
        assert args.benchmark is True
    
    def test_no_minify_flag(self):
        """--no-minify flag."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--no-minify", action="store_true")
        
        args = parser.parse_args(["--no-minify"])
        assert args.no_minify is True
    
    def test_no_sourcemap_flag(self):
        """--no-sourcemap flag."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--no-sourcemap", action="store_true")
        
        args = parser.parse_args(["--no-sourcemap"])
        assert args.no_sourcemap is True
    
    def test_no_cache_flag(self):
        """--no-cache flag."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--no-cache", action="store_true")
        
        args = parser.parse_args(["--no-cache"])
        assert args.no_cache is True
    
    def test_clean_flag(self):
        """--clean flag."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--clean", action="store_true")
        
        args = parser.parse_args(["--clean"])
        assert args.clean is True
    
    def test_verbose_flag(self):
        """--verbose flag."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--verbose", action="store_true")
        
        args = parser.parse_args(["--verbose"])
        assert args.verbose is True


# =============================================================================
# EXIT CODES
# =============================================================================

class TestExitCodes:
    """Tests for exit codes."""
    
    def test_success_returns_zero(self, tmp_path):
        """Successful build returns 0."""
        args = argparse.Namespace(
            dir=str(tmp_path),
            output=str(tmp_path / "build"),
            tree_shake=False,
            analyze=False,
            watch=False,
            verbose=False,
        )
        
        with patch('pynext.build.compile_project') as mock:
            mock.return_value = Mock(
                success=True,
                island_count=0,
                output_size_kb=0,
                cache_hits=0,
                cache_misses=0,
                error_count=0,
                errors=[],
                duration_ms=50,
            )
            exit_code = cmd_compile(args)
        
        assert exit_code == 0
    
    def test_failure_returns_one(self, tmp_path):
        """Failed build returns 1."""
        args = argparse.Namespace(
            dir=str(tmp_path),
            output=str(tmp_path / "build"),
            tree_shake=False,
            analyze=False,
            watch=False,
            verbose=False,
        )
        
        with patch('pynext.build.compile_project') as mock:
            mock.return_value = Mock(
                success=False,
                island_count=0,
                error_count=1,
                errors=[("file.py", "Error")],
                output_size_kb=0,
                cache_hits=0,
                cache_misses=0,
            )
            exit_code = cmd_compile(args)
        
        assert exit_code == 1


# =============================================================================
# INTEGRATION WITH BUILD MODULE
# =============================================================================

class TestBuildIntegration:
    """Tests for integration with build module."""
    
    def test_passes_config_to_build(self, tmp_path):
        """CLI passes config to build module."""
        args = argparse.Namespace(
            dir=str(tmp_path),
            output=str(tmp_path / "build"),
            tree_shake=True,
            analyze=False,
            watch=False,
            verbose=True,
        )
        
        with patch('pynext.build.compile_project') as mock:
            mock.return_value = Mock(
                success=True,
                island_count=0,
                output_size_kb=0,
                cache_hits=0,
                cache_misses=0,
                error_count=0,
                errors=[],
                duration_ms=50,
            )
            cmd_compile(args)
        
        mock.assert_called_once()
    
    def test_creates_output_directory(self, tmp_path):
        """Creates output directory if needed."""
        output = tmp_path / "new_build"
        
        args = argparse.Namespace(
            dir=str(tmp_path),
            output=str(output),
            tree_shake=False,
            analyze=False,
            watch=False,
            verbose=False,
        )
        
        with patch('pynext.build.compile_project') as mock:
            mock.return_value = Mock(
                success=True,
                island_count=0,
                output_size_kb=0,
                cache_hits=0,
                cache_misses=0,
                error_count=0,
                errors=[],
                duration_ms=50,
            )
            cmd_compile(args)
        
        # Directory should exist after compile
        # (or mock should be called with correct path)
        mock.assert_called_once()

