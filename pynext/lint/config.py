"""
PyNext Linting - Configuration

Default configuration for PyNext linting.
Sensible defaults that work out of the box.

Example:
    # Get default config
    config = get_default_config()
    
    # Create .ruff.toml
    create_config_file(project_path)
    
    # Load existing config
    config = load_config(project_path)

Configuration Hierarchy:
    1. CLI arguments (highest priority)
    2. pyproject.toml [tool.pynext.lint]
    3. .ruff.toml
    4. Default config (lowest priority)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import tomllib


# =============================================================================
# Configuration Data Structure
# =============================================================================

@dataclass
class PyNextLintConfig:
    """
    PyNext linting configuration.
    
    Controls which rules run and how errors are reported.
    """
    
    # Enabled rule sets
    enabled_rules: Set[str] = field(default_factory=lambda: {
        "PNX001", "PNX002", "PNX003", "PNX004", "PNX005",
        "PNX006", "PNX007", "PNX008", "PNX009", "PNX010",
    })
    
    # Disabled rules (overrides enabled)
    disabled_rules: Set[str] = field(default_factory=set)
    
    # Files/directories to ignore
    exclude: List[str] = field(default_factory=lambda: [
        "__pycache__",
        ".git",
        ".venv",
        "venv",
        "node_modules",
        ".pytest_cache",
        "*.pyc",
        "__snapshots__",
    ])
    
    # Include only these file patterns
    include: List[str] = field(default_factory=lambda: ["*.py"])
    
    # Target directories (relative to project root)
    target_dirs: List[str] = field(default_factory=lambda: [
        "pages",
        "components",
        "app",
        "src",
    ])
    
    # Auto-fix settings
    auto_fix: bool = False
    unsafe_fixes: bool = False
    
    # Output format
    output_format: str = "text"  # text, json, github
    
    # Show codes in output
    show_codes: bool = True
    
    # Maximum line length (for some rules)
    line_length: int = 88
    
    # Ruff settings to merge
    ruff_extend: Dict[str, Any] = field(default_factory=dict)
    
    def is_rule_enabled(self, rule_id: str) -> bool:
        """Check if a rule is enabled."""
        if rule_id in self.disabled_rules:
            return False
        return rule_id in self.enabled_rules
    
    def enable_rule(self, rule_id: str) -> None:
        """Enable a rule."""
        self.enabled_rules.add(rule_id)
        self.disabled_rules.discard(rule_id)
    
    def disable_rule(self, rule_id: str) -> None:
        """Disable a rule."""
        self.disabled_rules.add(rule_id)


# =============================================================================
# Default Configuration
# =============================================================================

def get_default_config() -> PyNextLintConfig:
    """
    Get the default PyNext linting configuration.
    
    Returns:
        PyNextLintConfig with sensible defaults
    """
    return PyNextLintConfig()


# =============================================================================
# Configuration Loading
# =============================================================================

def load_config(project_path: Path) -> PyNextLintConfig:
    """
    Load linting configuration from project.
    
    Looks for configuration in:
    1. pyproject.toml [tool.pynext.lint]
    2. .ruff.toml
    
    Args:
        project_path: Path to project root
        
    Returns:
        Merged configuration
    """
    config = get_default_config()
    
    # Try pyproject.toml first
    pyproject = project_path / "pyproject.toml"
    if pyproject.exists():
        try:
            with open(pyproject, "rb") as f:
                data = tomllib.load(f)
            
            pynext_lint = data.get("tool", {}).get("pynext", {}).get("lint", {})
            _merge_config(config, pynext_lint)
        except Exception:
            pass  # Ignore parse errors
    
    # Check for .ruff.toml to extend
    ruff_toml = project_path / ".ruff.toml"
    if ruff_toml.exists():
        try:
            with open(ruff_toml, "rb") as f:
                ruff_data = tomllib.load(f)
            
            config.ruff_extend = ruff_data
        except Exception:
            pass
    
    return config


def _merge_config(config: PyNextLintConfig, data: Dict[str, Any]) -> None:
    """Merge configuration data into config object."""
    if "enabled_rules" in data:
        config.enabled_rules = set(data["enabled_rules"])
    
    if "disabled_rules" in data:
        config.disabled_rules = set(data["disabled_rules"])
    
    if "exclude" in data:
        config.exclude = data["exclude"]
    
    if "include" in data:
        config.include = data["include"]
    
    if "target_dirs" in data:
        config.target_dirs = data["target_dirs"]
    
    if "auto_fix" in data:
        config.auto_fix = data["auto_fix"]
    
    if "unsafe_fixes" in data:
        config.unsafe_fixes = data["unsafe_fixes"]
    
    if "output_format" in data:
        config.output_format = data["output_format"]
    
    if "line_length" in data:
        config.line_length = data["line_length"]


# =============================================================================
# Configuration File Creation
# =============================================================================

def create_config_file(
    project_path: Path,
    format: str = "ruff",
) -> Path:
    """
    Create a linting configuration file.
    
    Args:
        project_path: Path to project root
        format: Config format ("ruff" or "pyproject")
        
    Returns:
        Path to created config file
    """
    if format == "ruff":
        return _create_ruff_config(project_path)
    else:
        return _create_pyproject_config(project_path)


def _create_ruff_config(project_path: Path) -> Path:
    """Create .ruff.toml with PyNext settings."""
    config_path = project_path / ".ruff.toml"
    
    content = '''# PyNext Linting Configuration
# Generated by: pynext lint init
# Docs: https://docs.pynext.dev/linting

# Ruff settings
line-length = 88
target-version = "py310"

[lint]
# Enable standard rules
select = [
    "E",      # pycodestyle errors
    "F",      # Pyflakes
    "I",      # isort
    "B",      # flake8-bugbear
    "C4",     # flake8-comprehensions
    "UP",     # pyupgrade
]

# Ignore rules that conflict with PyNext patterns
ignore = [
    "E501",   # Line too long (handled by formatter)
]

# Per-file ignores
[lint.per-file-ignores]
"__init__.py" = ["F401"]  # Allow unused imports in __init__
"tests/*" = ["B011"]       # Allow assert in tests

[format]
# Use double quotes for strings
quote-style = "double"

# Use 4 spaces for indentation
indent-style = "space"

# Unix-style line endings
line-ending = "lf"
'''
    
    config_path.write_text(content)
    return config_path


def _create_pyproject_config(project_path: Path) -> Path:
    """Add PyNext lint config to pyproject.toml."""
    pyproject_path = project_path / "pyproject.toml"
    
    section = '''
[tool.pynext.lint]
# PyNext-specific rules
enabled_rules = [
    "PNX001",  # Unused Signal
    "PNX002",  # Signal in loop
    "PNX003",  # Missing component return
    "PNX004",  # Invalid prop type for island
    "PNX005",  # Server import in island
    "PNX006",  # Invalid route name
    "PNX007",  # Missing page export
    "PNX008",  # Untracked effect
    "PNX009",  # Direct signal mutation
    "PNX010",  # Missing metadata
]

# Output format: "text", "json", "github"
output_format = "text"

# Directories to lint
target_dirs = ["pages", "components", "app", "src"]
'''
    
    if pyproject_path.exists():
        existing = pyproject_path.read_text()
        if "[tool.pynext.lint]" not in existing:
            pyproject_path.write_text(existing + section)
    else:
        pyproject_path.write_text(section)
    
    return pyproject_path


# =============================================================================
# Ruff Configuration Generation
# =============================================================================

def generate_ruff_args(config: PyNextLintConfig) -> List[str]:
    """
    Generate ruff CLI arguments from config.
    
    Args:
        config: PyNext lint configuration
        
    Returns:
        List of CLI arguments for ruff
    """
    args = []
    
    # Line length
    args.extend(["--line-length", str(config.line_length)])
    
    # Exclude patterns
    for pattern in config.exclude:
        args.extend(["--exclude", pattern])
    
    # Output format
    if config.output_format == "json":
        args.append("--output-format=json")
    elif config.output_format == "github":
        args.append("--output-format=github")
    
    # Auto-fix
    if config.auto_fix:
        args.append("--fix")
        if config.unsafe_fixes:
            args.append("--unsafe-fixes")
    
    return args


# =============================================================================
# VS Code Settings Generation
# =============================================================================

def generate_vscode_settings(project_path: Path) -> Dict[str, Any]:
    """
    Generate VS Code settings for PyNext linting.
    
    Args:
        project_path: Path to project root
        
    Returns:
        Settings dictionary for .vscode/settings.json
    """
    return {
        "python.linting.enabled": True,
        "python.linting.ruffEnabled": True,
        "ruff.configurationPreference": "filesystemFirst",
        "[python]": {
            "editor.formatOnSave": True,
            "editor.codeActionsOnSave": {
                "source.fixAll.ruff": "explicit",
                "source.organizeImports.ruff": "explicit",
            },
            "editor.defaultFormatter": "charliermarsh.ruff",
        },
        "pynext.lint.enabled": True,
    }


def create_vscode_config(project_path: Path) -> Path:
    """
    Create VS Code configuration for PyNext linting.
    
    Args:
        project_path: Path to project root
        
    Returns:
        Path to created .vscode/settings.json
    """
    import json
    
    vscode_dir = project_path / ".vscode"
    vscode_dir.mkdir(exist_ok=True)
    
    settings_path = vscode_dir / "settings.json"
    
    # Load existing settings if present
    if settings_path.exists():
        try:
            existing = json.loads(settings_path.read_text())
        except json.JSONDecodeError:
            existing = {}
    else:
        existing = {}
    
    # Merge with PyNext settings
    pynext_settings = generate_vscode_settings(project_path)
    existing.update(pynext_settings)
    
    # Write back
    settings_path.write_text(json.dumps(existing, indent=2))
    
    # Also create extensions.json
    extensions_path = vscode_dir / "extensions.json"
    extensions = {
        "recommendations": [
            "charliermarsh.ruff",
            "ms-python.python",
        ]
    }
    extensions_path.write_text(json.dumps(extensions, indent=2))
    
    return settings_path

