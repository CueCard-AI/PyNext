"""
PyNext Environment Variables Module.

Re-exports all environment-related components for easy access.

Usage:
    from pynext.env import env, EnvSchema, Var
    
    # Simple access
    db_url = env.DATABASE_URL
    port = env.get_int("PORT", 8000)
    
    # Schema validation
    schema = EnvSchema(
        DATABASE_URL=Var(str, required=True),
        PORT=Var(int, default=8000),
    )
"""

from pynext.env.loader import (
    load_env_files,
    parse_env_file,
    expand_variables,
    get_env_files_info,
)

from pynext.env.schema import (
    Var,
    ValidationError,
    ValidationResult,
    EnvSchema,
    EnvConfig,
    load_schema,
)

from pynext.env.client import (
    get_public_vars,
    generate_inline_script,
    generate_runtime_script,
    inline_env_in_js,
    get_client_env_accessor,
)

__all__ = [
    # Loader
    "load_env_files",
    "parse_env_file",
    "expand_variables",
    "get_env_files_info",
    # Schema
    "Var",
    "ValidationError",
    "ValidationResult",
    "EnvSchema",
    "EnvConfig",
    "load_schema",
    # Client
    "get_public_vars",
    "generate_inline_script",
    "generate_runtime_script",
    "inline_env_in_js",
    "get_client_env_accessor",
]

