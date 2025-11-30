"""
CSS Scoper - Build-Time Class Name Hashing

Generates unique, deterministic class names to prevent style conflicts.
Uses content-based hashing for cache stability.

Example:
    Input:  .button { padding: 8px; }
    Output: .Button_button_x7f3d { padding: 8px; }
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from pathlib import Path


def generate_hash(content: str, length: int = 5) -> str:
    """
    Generate a short, deterministic hash from content.
    
    Uses MD5 for speed (not security) and base36 for shorter strings.
    
    Args:
        content: String to hash (typically CSS content + component name)
        length: Number of characters in output hash
        
    Returns:
        Short alphanumeric hash like "x7f3d"
        
    Example:
        >>> generate_hash(".button { padding: 8px; }")
        'a3b2c'
    """
    digest = hashlib.md5(content.encode()).hexdigest()
    # Convert hex to base36 for shorter string
    num = int(digest[:12], 16)  # Use first 12 hex chars
    chars = "0123456789abcdefghijklmnopqrstuvwxyz"
    result = []
    while num and len(result) < length:
        result.append(chars[num % 36])
        num //= 36
    return "".join(result) or "00000"[:length]


@dataclass
class ScopedClass:
    """
    Represents a scoped CSS class name.
    
    Attributes:
        original: Original class name (e.g., "button")
        scoped: Scoped class name (e.g., "Button_button_x7f3d")
        component: Component name used in scoping
        hash: The hash suffix
    """
    original: str
    scoped: str
    component: str
    hash: str
    
    def __str__(self) -> str:
        return self.scoped


@dataclass  
class ScopedCSS:
    """
    Result of CSS scoping operation.
    
    Attributes:
        css: The scoped CSS string
        classes: Mapping from original to scoped class names
        component: Component name
        hash: Hash used for scoping
    """
    css: str
    classes: Dict[str, ScopedClass]
    component: str
    hash: str
    
    def __getattr__(self, name: str) -> str:
        """
        Access scoped class names as attributes.
        
        Example:
            styles.button -> "Button_button_x7f3d"
        """
        if name.startswith("_"):
            raise AttributeError(name)
        if name in self.classes:
            return str(self.classes[name])
        raise AttributeError(f"CSS class '{name}' not defined")
    
    def __getitem__(self, name: str) -> str:
        """
        Access scoped class names as dict items.
        
        Example:
            styles["button"] -> "Button_button_x7f3d"
        """
        if name in self.classes:
            return str(self.classes[name])
        raise KeyError(f"CSS class '{name}' not defined")
    
    def get(self, name: str, default: str = "") -> str:
        """Get class name with optional default."""
        if name in self.classes:
            return str(self.classes[name])
        return default
    
    def has(self, name: str) -> bool:
        """Check if class exists."""
        return name in self.classes
    
    def all(self) -> Dict[str, str]:
        """Get all class mappings."""
        return {k: str(v) for k, v in self.classes.items()}


class CSSScoper:
    """
    Transforms CSS by scoping class names with unique hashes.
    
    The scoping algorithm:
    1. Parse CSS to find all class selectors
    2. Generate component-specific hash
    3. Replace class names with scoped versions
    4. Return scoped CSS and class mapping
    
    Example:
        >>> scoper = CSSScoper("Button")
        >>> result = scoper.scope(".button { color: blue; }")
        >>> print(result.css)
        .Button_button_x7f3d { color: blue; }
        >>> print(result.button)
        Button_button_x7f3d
    """
    
    # Regex to find class selectors in CSS
    CLASS_PATTERN = re.compile(r"\.([a-zA-Z_][a-zA-Z0-9_-]*)")
    
    # Regex to match complete CSS rules for parsing
    RULE_PATTERN = re.compile(r"([^{]+)\{([^}]*)\}", re.MULTILINE)
    
    def __init__(
        self,
        component: str,
        hash_length: int = 5,
        prefix_component: bool = True,
    ):
        """
        Initialize CSS scoper.
        
        Args:
            component: Component name for scoped class prefix
            hash_length: Length of hash suffix (default 5)
            prefix_component: Whether to include component name in scoped class
        """
        self.component = component
        self.hash_length = hash_length
        self.prefix_component = prefix_component
        self._classes: Dict[str, ScopedClass] = {}
        self._hash: Optional[str] = None
    
    def scope(self, css: str) -> ScopedCSS:
        """
        Scope all class names in CSS.
        
        Args:
            css: Raw CSS string
            
        Returns:
            ScopedCSS with scoped CSS and class mappings
            
        Example:
            >>> scoper = CSSScoper("Button")
            >>> result = scoper.scope('''
            ...     .button { padding: 8px; }
            ...     .button:hover { opacity: 0.8; }
            ...     .primary { background: blue; }
            ... ''')
            >>> print(result.button)
            Button_button_a3b2c
        """
        # Generate hash from CSS content + component name
        self._hash = generate_hash(f"{self.component}:{css}", self.hash_length)
        
        # Find all class names
        class_names = set(self.CLASS_PATTERN.findall(css))
        
        # Generate scoped names
        for class_name in class_names:
            scoped_name = self._generate_scoped_name(class_name)
            self._classes[class_name] = ScopedClass(
                original=class_name,
                scoped=scoped_name,
                component=self.component,
                hash=self._hash,
            )
        
        # Replace class names in CSS
        scoped_css = self._replace_classes(css)
        
        return ScopedCSS(
            css=scoped_css,
            classes=self._classes.copy(),
            component=self.component,
            hash=self._hash,
        )
    
    def _generate_scoped_name(self, class_name: str) -> str:
        """Generate scoped class name."""
        if self.prefix_component:
            return f"{self.component}_{class_name}_{self._hash}"
        return f"{class_name}_{self._hash}"
    
    def _replace_classes(self, css: str) -> str:
        """Replace all class references with scoped versions."""
        def replace_class(match: re.Match) -> str:
            class_name = match.group(1)
            if class_name in self._classes:
                return f".{self._classes[class_name].scoped}"
            return match.group(0)
        
        return self.CLASS_PATTERN.sub(replace_class, css)


class GlobalCSSScoper:
    """
    Manages CSS scoping across entire application.
    
    Collects all component styles and generates unique hashes
    that remain stable across builds (content-based hashing).
    """
    
    def __init__(self):
        self._components: Dict[str, ScopedCSS] = {}
        self._global_classes: Dict[str, str] = {}
    
    def register(self, component: str, css: str) -> ScopedCSS:
        """
        Register component CSS and return scoped result.
        
        Args:
            component: Component name
            css: Raw CSS string
            
        Returns:
            ScopedCSS for the component
        """
        if component in self._components:
            return self._components[component]
        
        scoper = CSSScoper(component)
        result = scoper.scope(css)
        
        self._components[component] = result
        
        # Track global class mapping for conflict detection
        for original, scoped in result.all().items():
            key = f"{component}.{original}"
            self._global_classes[key] = scoped
        
        return result
    
    def get_all_css(self) -> str:
        """Get combined CSS for all registered components."""
        return "\n\n".join(
            f"/* {name} */\n{scoped.css}"
            for name, scoped in self._components.items()
        )
    
    def get_class_map(self) -> Dict[str, Dict[str, str]]:
        """Get class mappings for all components."""
        return {
            name: scoped.all()
            for name, scoped in self._components.items()
        }
    
    def clear(self):
        """Clear all registered components."""
        self._components.clear()
        self._global_classes.clear()


# Global scoper instance
_global_scoper = GlobalCSSScoper()


def get_global_scoper() -> GlobalCSSScoper:
    """Get the global CSS scoper instance."""
    return _global_scoper

