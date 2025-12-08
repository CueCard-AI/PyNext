"""
Context API - Dependency Injection for Components

Context provides a way to pass data through the component tree
without explicitly passing props at every level.

Similar to React Context or Vue provide/inject.
"""

from __future__ import annotations

from typing import Any, Callable, Generic, Optional, TypeVar
from dataclasses import dataclass

from pynext.reactive.context import get_current_owner

T = TypeVar("T")


class Context(Generic[T]):
    """
    A Context holds a value that can be provided and consumed
    anywhere in the component tree.
    
    Usage:
        # Create context with default value
        ThemeContext = createContext("light")
        
        # Provide value to children
        ThemeContext.Provider(value="dark")[
            App()
        ]
        
        # Consume value in any descendant
        def Button():
            theme = useContext(ThemeContext)
            return button(class_=theme())["Click me"]
    """
    
    def __init__(self, default_value: T, name: Optional[str] = None):
        self._default_value = default_value
        self._name = name or f"Context_{id(self)}"
        self._id = f"ctx_{id(self)}"
    
    @property
    def id(self) -> str:
        return self._id
    
    @property
    def default_value(self) -> T:
        return self._default_value
    
    def Provider(self, value: T) -> "ContextProvider[T]":
        """
        Create a provider for this context.
        
        Args:
            value: The value to provide to descendants
            
        Returns:
            ContextProvider that can wrap children
        """
        return ContextProvider(self, value)
    
    def __repr__(self) -> str:
        return f"Context({self._name!r}, default={self._default_value!r})"


class ContextProvider(Generic[T]):
    """
    A provider component that supplies context value to children.
    """
    
    def __init__(self, context: Context[T], value: T):
        self._context = context
        self._value = value
        self._children: Any = None
    
    def __getitem__(self, children: Any) -> "ContextProvider[T]":
        """Set children."""
        self._children = children
        return self
    
    def __call__(self, children: Any) -> "ContextProvider[T]":
        """Alternative syntax for setting children."""
        self._children = children
        return self
    
    def render(self) -> str:
        """Render children with context value injected."""
        # Store context value in current owner
        owner = get_current_owner()
        if owner:
            owner.context[self._context.id] = self._value
        
        # Render children
        if self._children is None:
            return ""
        
        if hasattr(self._children, "render"):
            return self._children.render()
        
        if callable(self._children):
            result = self._children()
            if hasattr(result, "render"):
                return result.render()
            return str(result) if result else ""
        
        return str(self._children)
    
    def __str__(self) -> str:
        return self.render()


def createContext(default_value: T, name: Optional[str] = None) -> Context[T]:
    """
    Create a new Context.
    
    Usage:
        ThemeContext = createContext("light")
        UserContext = createContext(None, name="UserContext")
    
    Args:
        default_value: Value used when no provider is found
        name: Optional name for debugging
        
    Returns:
        Context object with Provider method
    """
    return Context(default_value, name)


def useContext(context: Context[T]) -> T:
    """
    Consume a context value.
    
    Looks up the component tree for a Provider of this context.
    If none found, returns the default value.
    
    Usage:
        def MyComponent():
            theme = useContext(ThemeContext)
            return div(class_=theme)["Content"]
    
    Args:
        context: The Context to consume
        
    Returns:
        The context value from nearest Provider or default
    """
    # Walk up the owner tree looking for context value
    owner = get_current_owner()
    
    while owner is not None:
        if context.id in owner.context:
            return owner.context[context.id]
        owner = owner.parent
    
    # No provider found, return default
    return context.default_value


def getContext(context: Context[T]) -> Optional[T]:
    """
    Get context value or None if not provided.
    
    Unlike useContext, this returns None instead of default
    when no provider is found.
    """
    owner = get_current_owner()
    
    while owner is not None:
        if context.id in owner.context:
            return owner.context[context.id]
        owner = owner.parent
    
    return None


def hasContext(context: Context[T]) -> bool:
    """Check if a context is provided in the current tree."""
    owner = get_current_owner()
    
    while owner is not None:
        if context.id in owner.context:
            return True
        owner = owner.parent
    
    return False

