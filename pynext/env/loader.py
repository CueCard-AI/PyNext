"""
Environment file loader.

Load order (later files override earlier):
1. .env                 - Base defaults (commit to git)
2. .env.local           - Local overrides (gitignored)
3. .env.{mode}          - Mode-specific (development/production/test)
4. .env.{mode}.local    - Mode-specific local (gitignored)
5. OS environment       - Always highest priority

SolidJS Principle: Single load, immutable result
AI-Friendly: Predictable priority, no surprises

Example:
    from pynext.env.loader import load_env_files
    
    # Load for development mode
    vars = load_env_files(Path.cwd(), "development")
    
    # Load for production
    vars = load_env_files(Path.cwd(), "production")
"""

from pathlib import Path
from typing import Dict, List, Optional
import os
import re


def load_env_files(root: Path, mode: str = "development") -> Dict[str, str]:
    """
    Load and merge env files in priority order.
    
    Args:
        root: Project root directory
        mode: Current mode (development/production/test)
    
    Returns:
        Merged dict of all environment variables
    
    Example:
        vars = load_env_files(Path("/my/project"), "production")
        print(vars.get("DATABASE_URL"))
    
    Load order (later overrides earlier):
        1. .env
        2. .env.local
        3. .env.{mode}
        4. .env.{mode}.local
        5. OS environment
    """
    result: Dict[str, str] = {}
    
    # Load files in order (later overrides earlier)
    files = [
        root / ".env",
        root / ".env.local",
        root / f".env.{mode}",
        root / f".env.{mode}.local",
    ]
    
    for file in files:
        if file.exists():
            file_vars = parse_env_file(file)
            result.update(file_vars)
    
    # OS environment always wins
    result.update(os.environ)
    
    # Expand variable references
    result = expand_variables(result)
    
    return result


def parse_env_file(path: Path) -> Dict[str, str]:
    """
    Parse a .env file into a dictionary.
    
    Supports:
    - KEY=value
    - KEY="quoted value"
    - KEY='single quoted'
    - # comments
    - Empty lines
    - Multiline with quotes
    - Variable expansion ${VAR}
    
    Args:
        path: Path to .env file
    
    Returns:
        Dict of parsed key-value pairs
    
    Example:
        # Given .env file:
        # DATABASE_URL=postgres://localhost/db
        # DEBUG=true
        # API_KEY="secret-key"
        
        vars = parse_env_file(Path(".env"))
        # Returns: {"DATABASE_URL": "postgres://localhost/db", "DEBUG": "true", "API_KEY": "secret-key"}
    """
    result: Dict[str, str] = {}
    content = path.read_text(encoding="utf-8")
    
    # Process line by line for better handling
    lines = content.splitlines()
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines and comments
        if not line or line.startswith('#'):
            continue
        
        # Must have = sign
        if '=' not in line:
            continue
        
        # Split on first = only
        key, _, value = line.partition('=')
        key = key.strip()
        value = value.strip()
        
        # Validate key format
        if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', key):
            continue
        
        # Skip if value is just a comment
        if value.startswith('#'):
            result[key] = ""
            continue
        
        # Handle quoted values
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]
        # Handle inline comments (unquoted values only)
        elif '#' in value:
            # Find the comment that's not inside quotes
            value = value.split('#')[0].strip()
        
        # Handle escape sequences in double-quoted values
        if value.startswith('"'):
            value = value.replace('\\n', '\n')
            value = value.replace('\\t', '\t')
            value = value.replace('\\"', '"')
        
        result[key] = value
    
    return result


def expand_variables(vars: Dict[str, str]) -> Dict[str, str]:
    """
    Expand ${VAR} references in values.
    
    Example:
        BASE_URL=http://localhost
        API_URL=${BASE_URL}/api
        # API_URL becomes http://localhost/api
    
    Args:
        vars: Dict of environment variables
    
    Returns:
        Dict with all ${VAR} references expanded
    
    Note:
        Supports up to 10 levels of nested references.
        Unresolved references are left as-is.
    """
    result = dict(vars)
    pattern = re.compile(r'\$\{([A-Za-z_][A-Za-z0-9_]*)\}')
    
    # Multiple passes to handle nested references
    for _ in range(10):  # Max 10 levels of nesting
        changed = False
        for key, value in result.items():
            if not isinstance(value, str):
                continue
            new_value = pattern.sub(
                lambda m: result.get(m.group(1), m.group(0)),
                value
            )
            if new_value != value:
                result[key] = new_value
                changed = True
        if not changed:
            break
    
    return result


def get_env_files_info(root: Path, mode: str = "development") -> List[Dict]:
    """
    Get info about env files for debugging/CLI.
    
    Args:
        root: Project root directory
        mode: Current mode
    
    Returns:
        List of dicts with file info:
        - name: File name
        - path: Full path
        - exists: Whether file exists
        - vars: Number of variables (if exists)
    
    Example:
        info = get_env_files_info(Path.cwd(), "development")
        for f in info:
            print(f"{f['name']}: {'✓' if f['exists'] else '✗'}")
    """
    files = [
        (".env", root / ".env"),
        (".env.local", root / ".env.local"),
        (f".env.{mode}", root / f".env.{mode}"),
        (f".env.{mode}.local", root / f".env.{mode}.local"),
    ]
    
    result = []
    for name, path in files:
        info = {
            "name": name,
            "path": str(path),
            "exists": path.exists(),
            "vars": 0,
        }
        if path.exists():
            info["vars"] = len(parse_env_file(path))
        result.append(info)
    
    return result


def get_load_order_diagram() -> str:
    """
    Return ASCII diagram of load order for documentation.
    
    Returns:
        String with ASCII diagram
    """
    return """
    Environment Variable Load Order
    ================================
    
    Priority (lowest to highest):
    
    ┌─────────────────────────────┐
    │  1. .env                    │  Base defaults (commit to git)
    └─────────────┬───────────────┘
                  │ overrides
    ┌─────────────▼───────────────┐
    │  2. .env.local              │  Local overrides (gitignored)
    └─────────────┬───────────────┘
                  │ overrides
    ┌─────────────▼───────────────┐
    │  3. .env.{mode}             │  Mode-specific (dev/prod/test)
    └─────────────┬───────────────┘
                  │ overrides
    ┌─────────────▼───────────────┐
    │  4. .env.{mode}.local       │  Mode + local (gitignored)
    └─────────────┬───────────────┘
                  │ overrides
    ┌─────────────▼───────────────┐
    │  5. OS Environment          │  Always highest priority
    └─────────────────────────────┘
    
    Example:
        .env:                  PORT=3000
        .env.development:      PORT=8000
        OS: PORT=9000
        
        Result: PORT=9000 (OS wins)
    """

