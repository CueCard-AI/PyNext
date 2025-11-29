"""
Environment Variables for PyNext.

Simple, typed access to environment variables with sensible defaults.

Example:
    from pynext import env
    
    # Direct access (raises KeyError if missing)
    db_url = env.DATABASE_URL
    
    # With default
    debug = env.get("DEBUG", False)
    
    # Typed getters
    port = env.get_int("PORT", 8000)
    debug = env.get_bool("DEBUG", False)
    hosts = env.get_list("ALLOWED_HOSTS", ["localhost"])

SolidJS Principle: Immutable after load - no runtime overhead
AI-Friendly: One import, attribute access, done
"""

from typing import Any, List, Optional, TypeVar, Union
from pathlib import Path
import os
import json

T = TypeVar('T')


class Env:
    """
    Environment variable container with typed access.
    
    Loads once at import, immutable thereafter.
    
    Usage:
        from pynext import env
        
        # Attribute access
        env.DATABASE_URL      # str, raises if missing
        env.DEBUG             # str, raises if missing
        
        # Safe access with defaults
        env.get("DEBUG", "false")            # str
        env.get_bool("DEBUG", False)         # bool
        env.get_int("PORT", 8000)            # int
        env.get_float("RATE", 1.5)           # float
        env.get_list("HOSTS", ["localhost"]) # List[str]
        
        # Utilities
        env.mode              # "development", "production", or "test"
        env.is_production     # True if production mode
        env.has("KEY")        # Check if var exists
        env.require("A", "B") # Require multiple vars
    """
    
    _instance: Optional['Env'] = None
    _loaded: bool = False
    _vars: dict = {}
    _mode: str = "development"
    
    def __new__(cls) -> 'Env':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not Env._loaded:
            self._load()
            Env._loaded = True
    
    def _load(self, root: Optional[Path] = None) -> None:
        """Load env files in priority order."""
        from pynext.env.loader import load_env_files
        
        root = root or Path.cwd()
        Env._mode = os.environ.get("PYNEXT_MODE", "development")
        Env._vars = load_env_files(root, Env._mode)
    
    def __getattr__(self, name: str) -> str:
        """
        Direct attribute access: env.DATABASE_URL
        
        Raises KeyError with helpful message if var is not set.
        """
        if name.startswith('_'):
            raise AttributeError(name)
        
        if name not in Env._vars:
            raise KeyError(
                f"Environment variable '{name}' is not set.\n"
                f"Add it to .env or .env.local:\n"
                f"  {name}=your_value\n"
                f"\n"
                f"Or set in your environment:\n"
                f"  export {name}=your_value"
            )
        return Env._vars[name]
    
    # === Simple Getters ===
    
    def get(self, key: str, default: T = None) -> Union[T, str]:
        """
        Get env var with optional default.
        
        Args:
            key: Variable name
            default: Default value if not set
        
        Returns:
            Variable value or default
        
        Example:
            api_url = env.get("API_URL", "http://localhost:3000")
        """
        return Env._vars.get(key, default)
    
    def get_str(self, key: str, default: str = "") -> str:
        """
        Get as string.
        
        Args:
            key: Variable name
            default: Default string value
        
        Returns:
            Variable value as string
        """
        return Env._vars.get(key, default)
    
    def get_int(self, key: str, default: int = 0) -> int:
        """
        Get as integer.
        
        Args:
            key: Variable name
            default: Default int value
        
        Returns:
            Variable value converted to int
        
        Raises:
            ValueError: If value cannot be converted to int
        
        Example:
            port = env.get_int("PORT", 8000)
        """
        val = Env._vars.get(key)
        if val is None:
            return default
        try:
            return int(val)
        except ValueError:
            raise ValueError(
                f"Environment variable '{key}' must be an integer.\n"
                f"Got: '{val}'\n"
                f"Expected: A number like 8000 or 3306"
            )
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """
        Get as boolean.
        
        Recognizes: true/false, 1/0, yes/no, on/off (case-insensitive)
        
        Args:
            key: Variable name
            default: Default bool value
        
        Returns:
            Variable value as boolean
        
        Example:
            debug = env.get_bool("DEBUG", False)
        """
        val = Env._vars.get(key)
        if val is None:
            return default
        return val.lower() in ("true", "1", "yes", "on")
    
    def get_float(self, key: str, default: float = 0.0) -> float:
        """
        Get as float.
        
        Args:
            key: Variable name
            default: Default float value
        
        Returns:
            Variable value converted to float
        
        Raises:
            ValueError: If value cannot be converted to float
        """
        val = Env._vars.get(key)
        if val is None:
            return default
        try:
            return float(val)
        except ValueError:
            raise ValueError(
                f"Environment variable '{key}' must be a number.\n"
                f"Got: '{val}'"
            )
    
    def get_list(
        self,
        key: str,
        default: Optional[List[str]] = None,
        separator: str = ","
    ) -> List[str]:
        """
        Get as list (comma-separated by default).
        
        Args:
            key: Variable name
            default: Default list value
            separator: Separator character (default: comma)
        
        Returns:
            List of string values
        
        Example:
            hosts = env.get_list("ALLOWED_HOSTS", ["localhost"])
            # ALLOWED_HOSTS=example.com,localhost -> ["example.com", "localhost"]
        """
        val = Env._vars.get(key)
        if val is None:
            return default or []
        return [item.strip() for item in val.split(separator) if item.strip()]
    
    def get_json(self, key: str, default: Any = None) -> Any:
        """
        Get as parsed JSON.
        
        Args:
            key: Variable name
            default: Default value if not set
        
        Returns:
            Parsed JSON value
        
        Raises:
            ValueError: If value is not valid JSON
        
        Example:
            config = env.get_json("APP_CONFIG", {"feature": True})
        """
        val = Env._vars.get(key)
        if val is None:
            return default
        try:
            return json.loads(val)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Environment variable '{key}' must be valid JSON.\n"
                f"Got: '{val}'\n"
                f"Error: {e}"
            )
    
    def get_bytes(self, key: str, default: bytes = b"") -> bytes:
        """
        Get as bytes (UTF-8 encoded).
        
        Args:
            key: Variable name
            default: Default bytes value
        
        Returns:
            Variable value encoded as bytes
        """
        val = Env._vars.get(key)
        if val is None:
            return default
        return val.encode("utf-8")
    
    # === Utilities ===
    
    @property
    def mode(self) -> str:
        """
        Current mode: development, production, or test.
        
        Set via PYNEXT_MODE environment variable.
        """
        return Env._mode
    
    @property
    def is_development(self) -> bool:
        """True if running in development mode."""
        return Env._mode == "development"
    
    @property
    def is_production(self) -> bool:
        """True if running in production mode."""
        return Env._mode == "production"
    
    @property
    def is_test(self) -> bool:
        """True if running in test mode."""
        return Env._mode == "test"
    
    def has(self, key: str) -> bool:
        """
        Check if env var exists.
        
        Args:
            key: Variable name
        
        Returns:
            True if variable is set
        """
        return key in Env._vars
    
    def require(self, *keys: str) -> None:
        """
        Require multiple vars exist, raise with all missing.
        
        Args:
            *keys: Variable names to require
        
        Raises:
            KeyError: With list of all missing variables
        
        Example:
            env.require("DATABASE_URL", "SECRET_KEY", "API_KEY")
        """
        missing = [k for k in keys if k not in Env._vars]
        if missing:
            raise KeyError(
                f"Required environment variables missing:\n" +
                "\n".join(f"  - {k}" for k in missing) +
                f"\n\nAdd them to .env or set in environment."
            )
    
    def get_public(self) -> dict:
        """
        Get all PYNEXT_PUBLIC_* vars for client.
        
        Returns:
            Dict of public vars with prefix stripped
        
        Example:
            # PYNEXT_PUBLIC_API_URL=https://api.example.com
            public = env.get_public()
            # {"API_URL": "https://api.example.com"}
        """
        return {
            k.replace("PYNEXT_PUBLIC_", ""): v
            for k, v in Env._vars.items()
            if k.startswith("PYNEXT_PUBLIC_")
        }
    
    def all(self) -> dict:
        """
        Get all loaded vars (for debugging).
        
        Returns:
            Dict of all environment variables
        """
        return dict(Env._vars)
    
    def reload(self, root: Optional[Path] = None) -> None:
        """
        Reload env files (for development hot reload).
        
        Args:
            root: Project root directory
        """
        Env._loaded = False
        self._load(root)
    
    def __contains__(self, key: str) -> bool:
        """Support 'in' operator: 'KEY' in env"""
        return key in Env._vars
    
    def __repr__(self) -> str:
        return f"Env(mode={Env._mode}, vars={len(Env._vars)})"


# Singleton instance - use this
env = Env()

