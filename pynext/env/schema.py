"""
Optional schema validation for environment variables.

Use in production to fail fast if required vars are missing
or have invalid values.

Example:
    # env.schema.py (in project root)
    from pynext.env import EnvSchema, Var
    
    schema = EnvSchema(
        DATABASE_URL=Var(str, required=True),
        PORT=Var(int, default=8000),
        DEBUG=Var(bool, default=False),
        ALLOWED_HOSTS=Var(list, default=["localhost"]),
        API_KEY=Var(str, required=True, secret=True),
    )

SolidJS Principle: Fail at startup, not at runtime
AI-Friendly: Declarative schema, clear error messages
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Type, Union
from pathlib import Path
import importlib.util


@dataclass
class Var:
    """
    Schema definition for a single environment variable.
    
    Args:
        type: Expected type (str, int, bool, float, list)
        required: If True, startup fails if missing
        default: Default value if not set
        description: Human-readable description
        secret: If True, value is masked in logs/CLI
        validator: Optional custom validation function
        choices: Optional list of allowed values
    
    Examples:
        # Required string
        Var(str, required=True)
        
        # Optional int with default
        Var(int, default=8000)
        
        # Boolean with description
        Var(bool, default=False, description="Enable debug mode")
        
        # String with choices
        Var(str, choices=["development", "production", "test"])
        
        # Custom validation
        Var(str, validator=lambda x: x.startswith("http"))
        
        # Secret value (masked in output)
        Var(str, required=True, secret=True)
    """
    type: Type
    required: bool = False
    default: Any = None
    description: str = ""
    secret: bool = False
    validator: Optional[Callable[[Any], bool]] = None
    choices: Optional[List[Any]] = None


@dataclass
class ValidationError:
    """
    A single validation error.
    
    Attributes:
        key: Environment variable name
        message: Human-readable error message
        value: The invalid value (masked if secret)
    """
    key: str
    message: str
    value: Optional[str] = None
    
    def __str__(self) -> str:
        if self.value:
            return f"{self.key}: {self.message} (got: {self.value})"
        return f"{self.key}: {self.message}"


@dataclass
class ValidationResult:
    """
    Result of schema validation.
    
    Attributes:
        valid: True if all validations passed
        errors: List of validation errors
        warnings: List of non-fatal warnings
    """
    valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def raise_if_invalid(self) -> None:
        """
        Raise exception if validation failed.
        
        Raises:
            EnvironmentError: With details of all validation errors
        """
        if not self.valid:
            error_msg = "Environment validation failed:\n\n"
            for err in self.errors:
                error_msg += f"  {err.key}: {err.message}\n"
            error_msg += "\nFix these issues in your .env file or environment."
            raise EnvironmentError(error_msg)
    
    def __str__(self) -> str:
        if self.valid:
            return "Validation passed"
        return f"Validation failed with {len(self.errors)} error(s)"


class EnvSchema:
    """
    Schema for validating environment variables.
    
    Define your schema once, validate everywhere.
    
    Usage:
        # Define schema
        schema = EnvSchema(
            DATABASE_URL=Var(str, required=True),
            PORT=Var(int, default=8000),
            DEBUG=Var(bool, default=False),
        )
        
        # Validate against current env
        result = schema.validate(env_vars)
        result.raise_if_invalid()
        
        # Or get typed values
        config = schema.load(env_vars)
        print(config.DATABASE_URL)  # typed access
        print(config.PORT)          # int, not str
    
    Benefits:
        - Fail fast: Know immediately if config is wrong
        - Type safety: Get proper types, not just strings
        - Documentation: Schema serves as config documentation
        - Templates: Auto-generate .env.example files
    """
    
    def __init__(self, **vars: Var):
        """
        Create schema from variable definitions.
        
        Args:
            **vars: Variable name to Var definition mapping
        """
        self.vars = vars
    
    def validate(self, env_vars: Dict[str, str]) -> ValidationResult:
        """
        Validate env vars against schema.
        
        Args:
            env_vars: Dict of environment variables
        
        Returns:
            ValidationResult with errors and warnings
        
        Example:
            result = schema.validate({"PORT": "8000", "DEBUG": "true"})
            if not result.valid:
                for err in result.errors:
                    print(f"Error: {err}")
        """
        errors: List[ValidationError] = []
        warnings: List[str] = []
        
        for key, var in self.vars.items():
            value = env_vars.get(key)
            
            # Check required
            if var.required and value is None:
                desc = f" {var.description}" if var.description else ""
                errors.append(ValidationError(
                    key=key,
                    message=f"Required but not set.{desc}",
                ))
                continue
            
            # Skip if not set and not required
            if value is None:
                continue
            
            # Type conversion and validation
            try:
                typed_value = self._convert(value, var.type)
            except (ValueError, TypeError) as e:
                display_value = "***" if var.secret else value
                errors.append(ValidationError(
                    key=key,
                    message=f"Invalid type. Expected {var.type.__name__}, got '{display_value}'",
                    value=display_value,
                ))
                continue
            
            # Check choices
            if var.choices and typed_value not in var.choices:
                errors.append(ValidationError(
                    key=key,
                    message=f"Invalid value. Must be one of: {var.choices}",
                    value=value if not var.secret else "***",
                ))
                continue
            
            # Custom validator
            if var.validator:
                try:
                    if not var.validator(typed_value):
                        errors.append(ValidationError(
                            key=key,
                            message="Custom validation failed",
                            value=value if not var.secret else "***",
                        ))
                except Exception as e:
                    errors.append(ValidationError(
                        key=key,
                        message=f"Validation error: {e}",
                    ))
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )
    
    def load(self, env_vars: Dict[str, str]) -> 'EnvConfig':
        """
        Load and validate env vars, returning typed config object.
        
        Args:
            env_vars: Dict of environment variables
        
        Returns:
            EnvConfig with typed attribute access
        
        Raises:
            EnvironmentError: If validation fails
        
        Example:
            config = schema.load(os.environ)
            port: int = config.PORT  # Already converted to int
        """
        result = self.validate(env_vars)
        result.raise_if_invalid()
        
        # Build typed config
        config_dict = {}
        for key, var in self.vars.items():
            value = env_vars.get(key)
            if value is not None:
                config_dict[key] = self._convert(value, var.type)
            elif var.default is not None:
                config_dict[key] = var.default
        
        return EnvConfig(config_dict)
    
    def _convert(self, value: str, target_type: Type) -> Any:
        """Convert string value to target type."""
        if target_type == str:
            return value
        elif target_type == int:
            return int(value)
        elif target_type == float:
            return float(value)
        elif target_type == bool:
            return value.lower() in ("true", "1", "yes", "on")
        elif target_type == list:
            return [v.strip() for v in value.split(",") if v.strip()]
        else:
            raise TypeError(f"Unsupported type: {target_type}")
    
    def generate_template(self) -> str:
        """
        Generate a .env.example template from schema.
        
        Returns:
            String content for .env.example file
        
        Example:
            template = schema.generate_template()
            Path(".env.example").write_text(template)
        """
        lines = [
            "# Environment Variables",
            "# Generated from env.schema.py",
            "#",
            "# Copy this file to .env and fill in your values:",
            "#   cp .env.example .env",
            "",
        ]
        
        # Group by required/optional
        required_vars = [(k, v) for k, v in self.vars.items() if v.required]
        optional_vars = [(k, v) for k, v in self.vars.items() if not v.required]
        
        if required_vars:
            lines.append("# ===================")
            lines.append("# Required Variables")
            lines.append("# ===================")
            lines.append("")
            
            for key, var in required_vars:
                lines.extend(self._var_to_template_lines(key, var))
        
        if optional_vars:
            lines.append("# ===================")
            lines.append("# Optional Variables")
            lines.append("# ===================")
            lines.append("")
            
            for key, var in optional_vars:
                lines.extend(self._var_to_template_lines(key, var))
        
        return "\n".join(lines)
    
    def _var_to_template_lines(self, key: str, var: Var) -> List[str]:
        """Generate template lines for a single variable."""
        lines = []
        
        # Add description comment
        if var.description:
            lines.append(f"# {var.description}")
        
        # Add type hint
        type_hint = var.type.__name__
        if var.choices:
            type_hint = f"one of: {', '.join(str(c) for c in var.choices)}"
        
        required = "(required)" if var.required else "(optional)"
        lines.append(f"# Type: {type_hint} {required}")
        
        # Add example value
        if var.secret:
            example = "your_secret_here"
        elif var.default is not None:
            if isinstance(var.default, list):
                example = ",".join(str(v) for v in var.default)
            else:
                example = str(var.default)
        elif var.choices:
            example = str(var.choices[0])
        else:
            example = ""
        
        lines.append(f"{key}={example}")
        lines.append("")
        
        return lines
    
    def get_required_vars(self) -> List[str]:
        """Get list of required variable names."""
        return [k for k, v in self.vars.items() if v.required]
    
    def get_optional_vars(self) -> List[str]:
        """Get list of optional variable names."""
        return [k for k, v in self.vars.items() if not v.required]
    
    def get_secret_vars(self) -> List[str]:
        """Get list of secret variable names."""
        return [k for k, v in self.vars.items() if v.secret]


class EnvConfig:
    """
    Typed configuration object from validated schema.
    
    Provides attribute access to validated env vars with proper types.
    
    Usage:
        config = schema.load(env_vars)
        
        # Attribute access
        config.DATABASE_URL  # str
        config.PORT          # int (already converted)
        config.DEBUG         # bool
        
        # Dict access
        config.to_dict()     # {"DATABASE_URL": "...", "PORT": 8000, ...}
    """
    
    def __init__(self, values: Dict[str, Any]):
        self._values = values
    
    def __getattr__(self, name: str) -> Any:
        if name.startswith('_'):
            raise AttributeError(name)
        if name not in self._values:
            raise AttributeError(
                f"Config has no attribute '{name}'. "
                f"Available: {list(self._values.keys())}"
            )
        return self._values[name]
    
    def __contains__(self, key: str) -> bool:
        return key in self._values
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get config value with optional default."""
        return self._values.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return dict(self._values)
    
    def __repr__(self) -> str:
        return f"EnvConfig({list(self._values.keys())})"


def load_schema(root: Path) -> Optional[EnvSchema]:
    """
    Load env.schema.py from project root if it exists.
    
    Args:
        root: Project root directory
    
    Returns:
        EnvSchema if env.schema.py exists and has 'schema' variable,
        None otherwise
    
    Example:
        schema = load_schema(Path.cwd())
        if schema:
            result = schema.validate(env_vars)
    """
    schema_path = root / "env.schema.py"
    if not schema_path.exists():
        return None
    
    try:
        spec = importlib.util.spec_from_file_location("env_schema", schema_path)
        if not spec or not spec.loader:
            return None
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        if hasattr(module, "schema"):
            return module.schema
        
        # Also check for Schema (capitalized)
        if hasattr(module, "Schema"):
            return module.Schema
        
        return None
    except Exception as e:
        print(f"[PyNext] Warning: Error loading env.schema.py: {e}")
        return None

