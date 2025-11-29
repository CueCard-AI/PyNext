"""
PyNext Linting - Runner

Execute linting on files and projects.
Combines ruff with PyNext-specific rules.

Usage:
    from pynext.lint import lint, lint_project, fix
    
    # Lint a single file
    result = lint_file("pages/page.py")
    
    # Lint entire project
    result = lint_project(".")
    
    # Auto-fix issues
    result = fix("pages/page.py")
"""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Set

from pynext.lint.config import PyNextLintConfig, load_config, generate_ruff_args
from pynext.lint.rules import run_rules, LintError
from pynext.lint.rules.base import LintResult


# =============================================================================
# Main Linting Functions
# =============================================================================

def lint(
    target: str = ".",
    config: Optional[PyNextLintConfig] = None,
) -> LintResult:
    """
    Lint a file or directory.
    
    Runs both ruff and PyNext-specific rules.
    
    Args:
        target: File or directory to lint
        config: Linting configuration (auto-loaded if None)
        
    Returns:
        LintResult with all errors
        
    Example:
        result = lint("pages/")
        if result.has_errors:
            print(result.summary())
            for error in result.errors:
                print(error)
    """
    target_path = Path(target)
    
    if not target_path.exists():
        return LintResult(errors=[LintError(
            rule="PNX000",
            message=f"Target not found: {target}",
            line=0,
            column=0,
            severity="error",
        )])
    
    # Load config
    if config is None:
        project_root = _find_project_root(target_path)
        config = load_config(project_root)
    
    all_errors: List[LintError] = []
    files_checked = 0
    
    # Collect files to lint
    if target_path.is_file():
        files = [target_path]
    else:
        files = _collect_python_files(target_path, config)
    
    # Run ruff first (if available)
    ruff_errors = _run_ruff(target, config)
    all_errors.extend(ruff_errors)
    
    # Run PyNext-specific rules
    for file_path in files:
        try:
            source = file_path.read_text()
            errors = run_rules(source, str(file_path), config.enabled_rules)
            all_errors.extend(errors)
            files_checked += 1
        except Exception as e:
            all_errors.append(LintError(
                rule="PNX000",
                message=f"Error reading {file_path}: {e}",
                line=0,
                column=0,
                severity="error",
            ))
    
    return LintResult(errors=all_errors, files_checked=files_checked)


def lint_file(
    file_path: str,
    config: Optional[PyNextLintConfig] = None,
) -> LintResult:
    """
    Lint a single file.
    
    Args:
        file_path: Path to Python file
        config: Linting configuration
        
    Returns:
        LintResult with errors from this file
    """
    return lint(file_path, config)


def lint_project(
    project_path: str = ".",
    config: Optional[PyNextLintConfig] = None,
) -> LintResult:
    """
    Lint an entire project.
    
    Args:
        project_path: Path to project root
        config: Linting configuration
        
    Returns:
        LintResult with all errors
    """
    return lint(project_path, config)


def fix(
    target: str = ".",
    config: Optional[PyNextLintConfig] = None,
    unsafe: bool = False,
) -> LintResult:
    """
    Lint and auto-fix issues.
    
    Args:
        target: File or directory to fix
        config: Linting configuration
        unsafe: Include unsafe fixes
        
    Returns:
        LintResult with remaining unfixed errors
    """
    if config is None:
        project_root = _find_project_root(Path(target))
        config = load_config(project_root)
    
    # Enable auto-fix
    config.auto_fix = True
    config.unsafe_fixes = unsafe
    
    # Run ruff fix first
    _run_ruff_fix(target, config)
    
    # Then lint again to get remaining issues
    return lint(target, config)


# =============================================================================
# Ruff Integration
# =============================================================================

def _run_ruff(target: str, config: PyNextLintConfig) -> List[LintError]:
    """Run ruff linter and convert output to LintError."""
    errors = []
    
    try:
        args = ["ruff", "check", target, "--output-format=json"]
        args.extend(generate_ruff_args(config))
        
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
        )
        
        if result.stdout:
            import json
            try:
                ruff_errors = json.loads(result.stdout)
                for error in ruff_errors:
                    errors.append(LintError(
                        rule=error.get("code", "E000"),
                        message=error.get("message", "Unknown error"),
                        line=error.get("location", {}).get("row", 0),
                        column=error.get("location", {}).get("column", 0),
                        severity="error" if error.get("code", "").startswith("E") else "warning",
                    ))
            except json.JSONDecodeError:
                pass  # Ignore parse errors
                
    except FileNotFoundError:
        # ruff not installed, skip
        pass
    except Exception:
        # Ignore other errors
        pass
    
    return errors


def _run_ruff_fix(target: str, config: PyNextLintConfig) -> None:
    """Run ruff with --fix."""
    try:
        args = ["ruff", "check", target, "--fix"]
        if config.unsafe_fixes:
            args.append("--unsafe-fixes")
        args.extend(generate_ruff_args(config))
        
        subprocess.run(args, capture_output=True)
    except FileNotFoundError:
        pass  # ruff not installed


# =============================================================================
# File Collection
# =============================================================================

def _collect_python_files(
    directory: Path,
    config: PyNextLintConfig,
) -> List[Path]:
    """Collect Python files to lint."""
    files = []
    
    for pattern in config.include:
        files.extend(directory.rglob(pattern))
    
    # Filter excluded patterns
    exclude_patterns = set(config.exclude)
    
    filtered = []
    for f in files:
        # Check if any part of the path matches exclude patterns
        path_parts = f.parts
        excluded = False
        
        for pattern in exclude_patterns:
            if pattern.startswith("*"):
                # Glob pattern
                if f.match(pattern):
                    excluded = True
                    break
            else:
                # Directory name
                if pattern in path_parts:
                    excluded = True
                    break
        
        if not excluded:
            filtered.append(f)
    
    return filtered


def _find_project_root(path: Path) -> Path:
    """Find project root by looking for pyproject.toml or .git."""
    current = path.absolute()
    
    if current.is_file():
        current = current.parent
    
    while current != current.parent:
        if (current / "pyproject.toml").exists():
            return current
        if (current / ".git").exists():
            return current
        if (current / "pynext.config.py").exists():
            return current
        current = current.parent
    
    return path.absolute()


# =============================================================================
# Output Formatting
# =============================================================================

def format_errors(
    result: LintResult,
    format: str = "text",
    show_source: bool = False,
) -> str:
    """
    Format lint errors for display.
    
    Args:
        result: LintResult to format
        format: Output format ("text", "json", "github")
        show_source: Include source code context
        
    Returns:
        Formatted string
    """
    if format == "json":
        import json
        return json.dumps([e.to_dict() for e in result.errors], indent=2)
    
    elif format == "github":
        # GitHub Actions annotation format
        lines = []
        for error in result.errors:
            level = "error" if error.severity == "error" else "warning"
            lines.append(
                f"::{level} file={error.line},"
                f"line={error.line},col={error.column}::"
                f"{error.rule}: {error.message}"
            )
        return "\n".join(lines)
    
    else:  # text
        lines = []
        
        # Group by file
        by_file: dict = {}
        for error in result.errors:
            file_key = getattr(error, "file", "<unknown>")
            if file_key not in by_file:
                by_file[file_key] = []
            by_file[file_key].append(error)
        
        for file_path, errors in by_file.items():
            if file_path != "<unknown>":
                lines.append(f"\n{file_path}")
                lines.append("-" * len(file_path))
            
            for error in sorted(errors, key=lambda e: e.line):
                lines.append(str(error))
                if error.fix_description:
                    lines.append(f"  💡 {error.fix_description}")
        
        lines.append("")
        lines.append(result.summary())
        
        return "\n".join(lines)

