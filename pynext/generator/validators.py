"""
Name and path validation for generators.

Simple validation rules:
- Names must be valid Python identifiers
- Paths must be valid file system paths
- Reserved names are blocked

Why validate?
    Bad names cause subtle bugs and confusing errors.
    Better to catch them early with clear messages.
"""

import keyword
import re
from pathlib import Path
from typing import Optional

# Reserved component names
RESERVED_NAMES = {
    # Python reserved
    "class", "def", "return", "import", "from", "if", "else", "elif",
    "for", "while", "try", "except", "finally", "with", "as", "pass",
    "break", "continue", "raise", "yield", "lambda", "and", "or", "not",
    "in", "is", "None", "True", "False", "global", "nonlocal", "assert",
    "del", "async", "await",
    
    # PyNext reserved
    "page", "layout", "template", "loading", "error", "not_found",
    "middleware", "route", "api",
    
    # Common conflicts
    "app", "main", "index", "test", "config", "settings", "utils",
}

# Valid name pattern: starts with letter/underscore, contains alphanumeric/underscore
NAME_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')

# Valid path pattern: alphanumeric, underscore, hyphen, brackets for dynamic routes
PATH_PATTERN = re.compile(r'^[a-zA-Z0-9_\-\[\]\.\/]+$')


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


def validate_name(name: str, generator_type: str) -> str:
    """
    Validate a component name.
    
    Args:
        name: Component name to validate
        generator_type: Type of generator (page, component, etc.)
    
    Returns:
        Normalized name (PascalCase for components, snake_case for others)
    
    Raises:
        ValidationError: If name is invalid
    
    Example:
        >>> validate_name("UserProfile", "component")
        'UserProfile'
        
        >>> validate_name("blog-post", "page")
        'blog_post'
        
        >>> validate_name("class", "page")
        ValidationError: 'class' is a reserved name
    """
    if not name:
        raise ValidationError("Name cannot be empty")
    
    # Convert hyphens to underscores for Python compatibility
    normalized = name.replace("-", "_")
    
    # Check if it matches valid pattern
    if not NAME_PATTERN.match(normalized):
        raise ValidationError(
            f"Invalid name '{name}'. Names must:\n"
            f"  - Start with a letter or underscore\n"
            f"  - Contain only letters, numbers, and underscores\n"
            f"  - Example: 'UserProfile', 'blog_post', 'api_v2'"
        )
    
    # Check reserved names
    if normalized.lower() in RESERVED_NAMES or keyword.iskeyword(normalized):
        raise ValidationError(
            f"'{name}' is a reserved name. Please choose a different name.\n"
            f"  Try: '{name}_page', 'my_{name}', '{name}_component'"
        )
    
    # Apply case convention based on type
    if generator_type in ("component", "island"):
        # PascalCase for components
        return to_pascal_case(normalized)
    else:
        # snake_case for pages, api, etc.
        return to_snake_case(normalized)


def validate_path(path: str, generator_type: str) -> Path:
    """
    Validate a file path.
    
    Args:
        path: Path to validate (can include directories)
        generator_type: Type of generator
    
    Returns:
        Validated Path object
    
    Raises:
        ValidationError: If path is invalid
    
    Example:
        >>> validate_path("blog/posts", "page")
        Path('blog/posts')
        
        >>> validate_path("products/[id]", "page")
        Path('products/[id]')
    """
    if not path:
        raise ValidationError("Path cannot be empty")
    
    # Check for invalid characters
    if not PATH_PATTERN.match(path):
        raise ValidationError(
            f"Invalid path '{path}'. Paths can only contain:\n"
            f"  - Letters, numbers, underscores, hyphens\n"
            f"  - Forward slashes for directories\n"
            f"  - Brackets for dynamic routes [id], [...slug]"
        )
    
    # Check for path traversal attempts
    # Allow [...slug] pattern but not standalone ..
    if path.startswith("/"):
        raise ValidationError(
            f"Invalid path '{path}'. Paths cannot start with '/'"
        )
    
    # Check for ".." but not "[...slug]"
    path_without_brackets = path
    # Temporarily remove bracket contents
    import re
    path_without_brackets = re.sub(r'\[[^\]]+\]', '', path)
    if ".." in path_without_brackets:
        raise ValidationError(
            f"Invalid path '{path}'. Paths cannot contain '..'"
        )
    
    # Validate dynamic route brackets are balanced
    bracket_count = path.count("[") - path.count("]")
    if bracket_count != 0:
        raise ValidationError(
            f"Invalid dynamic route in '{path}'. Brackets must be balanced.\n"
            f"  Valid: '[id]', '[...slug]', '[[...optional]]'\n"
            f"  Invalid: '[id', 'slug]'"
        )
    
    return Path(path)


def to_pascal_case(name: str) -> str:
    """
    Convert name to PascalCase.
    
    Example:
        >>> to_pascal_case("user_profile")
        'UserProfile'
        
        >>> to_pascal_case("button")
        'Button'
    """
    parts = name.split("_")
    return "".join(part.capitalize() for part in parts)


def to_snake_case(name: str) -> str:
    """
    Convert name to snake_case.
    
    Example:
        >>> to_snake_case("UserProfile")
        'user_profile'
        
        >>> to_snake_case("Button")
        'button'
    """
    # Insert underscore before uppercase letters
    result = re.sub(r'([A-Z])', r'_\1', name)
    # Remove leading underscore and convert to lowercase
    return result.lstrip("_").lower()


def to_title_case(name: str) -> str:
    """
    Convert name to Title Case for display.
    
    Example:
        >>> to_title_case("user_profile")
        'User Profile'
        
        >>> to_title_case("UserProfile")
        'User Profile'
    """
    # First convert to snake_case, then title
    snake = to_snake_case(name)
    return " ".join(part.capitalize() for part in snake.split("_"))


def get_function_name(name: str, generator_type: str) -> str:
    """
    Get the function name for a component.
    
    Args:
        name: Component name
        generator_type: Type of generator
    
    Returns:
        Valid Python function name
    
    Example:
        >>> get_function_name("blog_post", "page")
        'blog_post'
        
        >>> get_function_name("UserCard", "component")
        'UserCard'
    """
    return validate_name(name, generator_type)


def get_route_path(name: str) -> str:
    """
    Convert a name to a URL route path.
    
    Example:
        >>> get_route_path("blog_post")
        'blog-post'
        
        >>> get_route_path("UserProfile")
        'user-profile'
    """
    snake = to_snake_case(name)
    return snake.replace("_", "-")

