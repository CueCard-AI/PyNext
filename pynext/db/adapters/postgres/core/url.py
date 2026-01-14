"""
PostgreSQL URL Parser and Configuration.

This module provides a simple way to configure PostgreSQL connections
using either a URL string or keyword arguments (or both).

Three ways to configure:

1. URL only:
   config = PostgresConfig.from_url("postgresql://user:pass@localhost/mydb")

2. Keywords only:
   config = PostgresConfig(host="localhost", database="mydb")

3. Mixed (URL + overrides):
   config = PostgresConfig.from_url(
       "postgresql://localhost/mydb",
       password="secret"  # Override from URL
   )

AI-Friendly Design:
- Each method has clear docstrings with examples
- Type hints on all parameters and return values
- Validation errors are descriptive and actionable
- No magic - everything is explicit
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, unquote, urlparse


class PostgresConfigError(Exception):
    """Error in PostgreSQL configuration.
    
    Raised when:
    - URL format is invalid
    - Required parameters are missing
    - Parameter values are invalid
    
    The error message always includes:
    - What went wrong
    - How to fix it
    - Example of correct usage
    """
    pass


@dataclass
class PostgresConfig:
    """PostgreSQL connection configuration.
    
    This is the single source of truth for connection settings.
    All other components (pool, adapter) use this config.
    
    Attributes:
        host: Database server hostname or IP (default: "localhost")
        port: Database server port (default: 5432)
        database: Database name (default: "postgres")
        user: Username for authentication (default: "postgres")
        password: Password for authentication (default: None)
        ssl: Enable SSL/TLS connection (default: False)
        ssl_mode: SSL mode: disable, allow, prefer, require, verify-ca, verify-full
        application_name: Name shown in pg_stat_activity (default: "pynext")
        options: Additional connection options
    
    Examples:
        # Minimal config (connects to localhost:5432/postgres as postgres)
        config = PostgresConfig()
        
        # Explicit config
        config = PostgresConfig(
            host="db.example.com",
            port=5432,
            database="myapp",
            user="myuser",
            password="secret123",
            ssl=True,
        )
        
        # From URL
        config = PostgresConfig.from_url("postgresql://user:pass@host:5432/db")
        
        # URL with overrides
        config = PostgresConfig.from_url(
            "postgresql://localhost/db",
            password="override_password"
        )
    """
    
    # Connection parameters
    host: str = "localhost"
    port: int = 5432
    database: str = "postgres"
    user: str = "postgres"
    password: Optional[str] = None
    
    # SSL settings
    ssl: bool = False
    ssl_mode: str = "prefer"
    
    # Application identification
    application_name: str = "pynext"
    
    # Additional options (passed to asyncpg)
    options: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        self._validate()
    
    def _validate(self) -> None:
        """Validate all configuration values.
        
        Raises:
            PostgresConfigError: If any value is invalid
        """
        # Validate host
        if not self.host or not isinstance(self.host, str):
            raise PostgresConfigError(
                "Invalid host: must be a non-empty string.\n"
                "Example: host='localhost' or host='db.example.com'"
            )
        
        # Validate port
        if not isinstance(self.port, int) or self.port < 1 or self.port > 65535:
            raise PostgresConfigError(
                f"Invalid port: {self.port}. Must be an integer between 1 and 65535.\n"
                "Example: port=5432"
            )
        
        # Validate database
        if not self.database or not isinstance(self.database, str):
            raise PostgresConfigError(
                "Invalid database: must be a non-empty string.\n"
                "Example: database='myapp'"
            )
        
        # Validate user
        if not self.user or not isinstance(self.user, str):
            raise PostgresConfigError(
                "Invalid user: must be a non-empty string.\n"
                "Example: user='postgres'"
            )
        
        # Validate ssl_mode
        valid_ssl_modes = {"disable", "allow", "prefer", "require", "verify-ca", "verify-full"}
        if self.ssl_mode not in valid_ssl_modes:
            raise PostgresConfigError(
                f"Invalid ssl_mode: '{self.ssl_mode}'.\n"
                f"Must be one of: {', '.join(sorted(valid_ssl_modes))}\n"
                "Example: ssl_mode='require'"
            )
    
    @classmethod
    def from_url(cls, url: str, **overrides: Any) -> "PostgresConfig":
        """Create config from a PostgreSQL URL.
        
        Parses a standard PostgreSQL connection URL and optionally
        applies overrides for any parameter.
        
        URL Format:
            postgresql://[user[:password]@][host][:port]/database[?options]
        
        Supported URL schemes:
            - postgresql://
            - postgres://
        
        Args:
            url: PostgreSQL connection URL
            **overrides: Override any parsed value (e.g., password="secret")
        
        Returns:
            PostgresConfig instance
        
        Raises:
            PostgresConfigError: If URL format is invalid
        
        Examples:
            # Basic URL
            config = PostgresConfig.from_url("postgresql://localhost/mydb")
            
            # Full URL
            config = PostgresConfig.from_url(
                "postgresql://user:pass@db.example.com:5432/mydb?sslmode=require"
            )
            
            # URL with password override (for security)
            config = PostgresConfig.from_url(
                "postgresql://user@localhost/mydb",
                password=os.environ["DB_PASSWORD"]
            )
        """
        # Parse the URL
        parsed = cls._parse_url(url)
        
        # Apply overrides
        parsed.update({k: v for k, v in overrides.items() if v is not None})
        
        # Create and return config
        return cls(**parsed)
    
    @classmethod
    def _parse_url(cls, url: str) -> Dict[str, Any]:
        """Parse a PostgreSQL URL into configuration dict.
        
        Args:
            url: PostgreSQL connection URL
        
        Returns:
            Dict of configuration values
        
        Raises:
            PostgresConfigError: If URL format is invalid
        """
        if not url:
            raise PostgresConfigError(
                "URL cannot be empty.\n"
                "Example: 'postgresql://localhost/mydb'"
            )
        
        # Check scheme
        if not url.startswith(("postgresql://", "postgres://")):
            raise PostgresConfigError(
                f"Invalid URL scheme. URL must start with 'postgresql://' or 'postgres://'.\n"
                f"Got: {url[:20]}...\n"
                "Example: 'postgresql://localhost/mydb'"
            )
        
        try:
            parsed = urlparse(url)
        except Exception as e:
            raise PostgresConfigError(
                f"Failed to parse URL: {e}\n"
                "Example: 'postgresql://user:pass@localhost:5432/mydb'"
            )
        
        config: Dict[str, Any] = {}
        
        # Extract host
        if parsed.hostname:
            config["host"] = parsed.hostname
        
        # Extract port
        if parsed.port:
            config["port"] = parsed.port
        
        # Extract database (path without leading /)
        if parsed.path and parsed.path != "/":
            config["database"] = parsed.path.lstrip("/")
        
        # Extract user
        if parsed.username:
            config["user"] = unquote(parsed.username)
        
        # Extract password
        if parsed.password:
            config["password"] = unquote(parsed.password)
        
        # Parse query string options
        if parsed.query:
            query_params = parse_qs(parsed.query)
            
            # Handle sslmode
            if "sslmode" in query_params:
                ssl_mode = query_params["sslmode"][0]
                config["ssl_mode"] = ssl_mode
                config["ssl"] = ssl_mode != "disable"
            
            # Handle application_name
            if "application_name" in query_params:
                config["application_name"] = query_params["application_name"][0]
            
            # Store other options
            known_params = {"sslmode", "application_name"}
            other_options = {
                k: v[0] if len(v) == 1 else v
                for k, v in query_params.items()
                if k not in known_params
            }
            if other_options:
                config["options"] = other_options
        
        return config
    
    def to_dsn(self) -> str:
        """Convert config to a DSN (Data Source Name) string.
        
        This is the format asyncpg expects for connection strings.
        
        Returns:
            DSN string like "postgresql://user:pass@host:port/database"
        
        Example:
            config = PostgresConfig(host="localhost", database="mydb")
            dsn = config.to_dsn()  # "postgresql://postgres@localhost:5432/mydb"
        """
        # Build auth part
        auth = self.user
        if self.password:
            # URL-encode password to handle special characters
            encoded_password = self.password.replace("@", "%40").replace(":", "%3A")
            auth = f"{self.user}:{encoded_password}"
        
        # Build base DSN
        dsn = f"postgresql://{auth}@{self.host}:{self.port}/{self.database}"
        
        # Add query parameters
        params = []
        if self.ssl_mode != "prefer":
            params.append(f"sslmode={self.ssl_mode}")
        if self.application_name != "pynext":
            params.append(f"application_name={self.application_name}")
        
        if params:
            dsn += "?" + "&".join(params)
        
        return dsn
    
    def to_asyncpg_kwargs(self) -> Dict[str, Any]:
        """Convert config to asyncpg.connect() keyword arguments.
        
        Returns:
            Dict of keyword arguments for asyncpg.connect()
        
        Example:
            config = PostgresConfig(host="localhost", database="mydb")
            kwargs = config.to_asyncpg_kwargs()
            conn = await asyncpg.connect(**kwargs)
        """
        kwargs: Dict[str, Any] = {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "user": self.user,
        }
        
        if self.password:
            kwargs["password"] = self.password
        
        # SSL configuration
        if self.ssl or self.ssl_mode != "disable":
            # asyncpg uses ssl=True or an ssl.SSLContext
            if self.ssl_mode in ("require", "verify-ca", "verify-full"):
                kwargs["ssl"] = True
            elif self.ssl_mode == "prefer":
                kwargs["ssl"] = "prefer"
        
        # Add any extra options
        if self.options:
            kwargs.update(self.options)
        
        return kwargs
    
    def __repr__(self) -> str:
        """Return string representation (password hidden)."""
        password_display = "***" if self.password else None
        return (
            f"PostgresConfig("
            f"host={self.host!r}, "
            f"port={self.port}, "
            f"database={self.database!r}, "
            f"user={self.user!r}, "
            f"password={password_display!r}, "
            f"ssl={self.ssl})"
        )


def parse_postgres_url(url: str) -> PostgresConfig:
    """Convenience function to parse a PostgreSQL URL.
    
    This is a simple wrapper around PostgresConfig.from_url() for those
    who prefer function-style API.
    
    Args:
        url: PostgreSQL connection URL
    
    Returns:
        PostgresConfig instance
    
    Example:
        config = parse_postgres_url("postgresql://localhost/mydb")
    """
    return PostgresConfig.from_url(url)

