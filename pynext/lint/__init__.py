"""
PyNext Linting - Code Quality Made Easy

Zero-config linting with PyNext-specific rules.
Just run `pynext lint` and you're done.

Quick Start:
    # Lint your project
    pynext lint
    
    # Auto-fix issues
    pynext lint --fix
    
    # Check specific directory
    pynext lint pages/

Features:
    - Built on ruff (Rust-powered, blazing fast)
    - 10 PyNext-specific rules (PNX001-010)
    - VS Code integration
    - LSP support for any editor
    - Auto-fix for many issues

Why PyNext Linting:
    - 100x faster than ESLint
    - Catches PyNext-specific issues
    - AI-friendly error messages
    - Zero config to start
"""

from pynext.lint.runner import (
    lint,
    lint_file,
    lint_project,
    fix,
    LintResult,
    LintError,
)

from pynext.lint.config import (
    get_default_config,
    create_config_file,
    load_config,
    PyNextLintConfig,
)

from pynext.lint.rules import (
    # Rule registry
    get_all_rules,
    get_rule,
    run_rules,
    
    # Individual linters
    SignalLinter,
    ComponentLinter,
    IslandLinter,
    RouteLinter,
)

from pynext.lint.lsp import (
    start_lsp_server,
    LSPServer,
)


__all__ = [
    # Runner
    "lint",
    "lint_file",
    "lint_project",
    "fix",
    "LintResult",
    "LintError",
    
    # Config
    "get_default_config",
    "create_config_file",
    "load_config",
    "PyNextLintConfig",
    
    # Rules
    "get_all_rules",
    "get_rule",
    "run_rules",
    "SignalLinter",
    "ComponentLinter",
    "IslandLinter",
    "RouteLinter",
    
    # LSP
    "start_lsp_server",
    "LSPServer",
]

