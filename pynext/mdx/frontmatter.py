"""
Frontmatter - YAML Metadata in MDX

Extracts and parses YAML frontmatter from MDX content.

Frontmatter is metadata at the top of a file:

    ---
    title: My Post
    date: 2024-01-15
    tags: [python, web]
    ---
    
    # My Post Content

Usage:
    from pynext.mdx import extract_frontmatter
    
    fm, content = extract_frontmatter(mdx_string)
    print(fm.title)  # "My Post"
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union


@dataclass
class Frontmatter:
    """
    Parsed frontmatter metadata.
    
    Provides typed access to common fields and dict-like
    access to custom fields.
    
    Attributes:
        title: Page/post title
        description: Meta description
        date: Publication date
        updated: Last update date
        author: Author name
        tags: List of tags
        draft: Whether this is a draft
        layout: Layout to use
        image: Featured image
        data: All raw frontmatter data
    """
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[datetime] = None
    updated: Optional[datetime] = None
    author: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    draft: bool = False
    layout: Optional[str] = None
    image: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    
    def __getitem__(self, key: str) -> Any:
        """Access frontmatter data by key."""
        return self.data.get(key)
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists."""
        return key in self.data
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value with default."""
        return self.data.get(key, default)
    
    def keys(self):
        """Get all keys."""
        return self.data.keys()
    
    def values(self):
        """Get all values."""
        return self.data.values()
    
    def items(self):
        """Get all items."""
        return self.data.items()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.data.copy()
    
    def to_meta_tags(self) -> str:
        """
        Generate HTML meta tags from frontmatter.
        
        Returns:
            HTML string with meta tags
        """
        tags = []
        
        if self.title:
            tags.append(f'<title>{self.title}</title>')
            tags.append(f'<meta property="og:title" content="{self.title}" />')
        
        if self.description:
            tags.append(f'<meta name="description" content="{self.description}" />')
            tags.append(f'<meta property="og:description" content="{self.description}" />')
        
        if self.author:
            tags.append(f'<meta name="author" content="{self.author}" />')
        
        if self.image:
            tags.append(f'<meta property="og:image" content="{self.image}" />')
        
        if self.date:
            tags.append(f'<meta property="article:published_time" content="{self.date.isoformat()}" />')
        
        if self.updated:
            tags.append(f'<meta property="article:modified_time" content="{self.updated.isoformat()}" />')
        
        for tag in self.tags:
            tags.append(f'<meta property="article:tag" content="{tag}" />')
        
        return "\n".join(tags)


def extract_frontmatter(content: str) -> Tuple[Frontmatter, str]:
    """
    Extract frontmatter from MDX content.
    
    Args:
        content: Full MDX string with optional frontmatter
        
    Returns:
        Tuple of (Frontmatter, remaining_content)
        
    Example:
        >>> fm, body = extract_frontmatter('''
        ... ---
        ... title: Hello World
        ... date: 2024-01-15
        ... ---
        ... 
        ... # Hello
        ... ''')
        >>> fm.title
        'Hello World'
        >>> body.strip()
        '# Hello'
    """
    # Check for frontmatter
    pattern = re.compile(r"^---\n(.*?)\n---\n?", re.DOTALL)
    match = pattern.match(content)
    
    if not match:
        return Frontmatter(), content
    
    yaml_content = match.group(1)
    remaining = content[match.end():]
    
    # Parse YAML (simple parser - no external deps)
    data = _parse_yaml(yaml_content)
    
    # Create Frontmatter object
    fm = Frontmatter(
        title=data.get("title"),
        description=data.get("description"),
        date=_parse_date(data.get("date")),
        updated=_parse_date(data.get("updated")),
        author=data.get("author"),
        tags=_ensure_list(data.get("tags", [])),
        draft=bool(data.get("draft", False)),
        layout=data.get("layout"),
        image=data.get("image"),
        data=data,
    )
    
    return fm, remaining


def _parse_yaml(yaml_str: str) -> Dict[str, Any]:
    """
    Simple YAML parser for frontmatter.
    
    Handles common cases without external dependencies:
    - key: value
    - key: [item1, item2]
    - key: "quoted value"
    - key: 123
    - key: true/false
    - Nested keys (one level)
    """
    data: Dict[str, Any] = {}
    current_key: Optional[str] = None
    current_list: Optional[List] = None
    
    for line in yaml_str.split("\n"):
        # Skip empty lines and comments
        if not line.strip() or line.strip().startswith("#"):
            continue
        
        # Check for list continuation
        if line.startswith("  - ") and current_list is not None:
            value = line.strip()[2:]  # Remove "- "
            current_list.append(_parse_value(value))
            continue
        
        # Parse key: value
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            
            if not value:
                # Might be start of a list
                current_key = key
                current_list = []
                data[key] = current_list
            elif value.startswith("[") and value.endswith("]"):
                # Inline list
                items = value[1:-1].split(",")
                data[key] = [_parse_value(item.strip()) for item in items if item.strip()]
                current_list = None
            else:
                data[key] = _parse_value(value)
                current_list = None
    
    return data


def _parse_value(value: str) -> Any:
    """Parse a YAML value into Python type."""
    # Remove quotes
    if (value.startswith('"') and value.endswith('"')) or \
       (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    
    # Boolean
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    
    # None
    if value.lower() in ("null", "~", ""):
        return None
    
    # Number
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        pass
    
    return value


def _parse_date(value: Any) -> Optional[datetime]:
    """Parse various date formats."""
    if value is None:
        return None
    
    if isinstance(value, datetime):
        return value
    
    value = str(value)
    
    # Try common formats
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
        "%B %d, %Y",
        "%b %d, %Y",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    
    return None


def _ensure_list(value: Any) -> List[str]:
    """Ensure value is a list of strings."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


class FrontmatterSchema:
    """
    Schema for validating frontmatter.
    
    Define required fields and types for validation.
    """
    
    def __init__(
        self,
        required: Optional[List[str]] = None,
        optional: Optional[Dict[str, type]] = None,
    ):
        self.required = required or []
        self.optional = optional or {}
    
    def validate(self, fm: Frontmatter) -> List[str]:
        """
        Validate frontmatter against schema.
        
        Returns list of error messages (empty if valid).
        """
        errors = []
        
        # Check required fields
        for field in self.required:
            if field not in fm.data or fm.data[field] is None:
                errors.append(f"Missing required field: {field}")
        
        # Check types for optional fields
        for field, expected_type in self.optional.items():
            if field in fm.data and fm.data[field] is not None:
                if not isinstance(fm.data[field], expected_type):
                    errors.append(
                        f"Field '{field}' should be {expected_type.__name__}, "
                        f"got {type(fm.data[field]).__name__}"
                    )
        
        return errors


# Common schemas
BlogPostSchema = FrontmatterSchema(
    required=["title", "date"],
    optional={
        "description": str,
        "author": str,
        "tags": list,
        "draft": bool,
    },
)

DocsPageSchema = FrontmatterSchema(
    required=["title"],
    optional={
        "description": str,
        "sidebar_position": int,
        "sidebar_label": str,
    },
)

