"""
PyNext Polymorphic Decorators.

Provides the @polymorphic and @polymorphic.subtype decorators for
defining polymorphic inheritance hierarchies.

Design Philosophy:
- Decorators are more Pythonic than magic __mapper_args__ dicts
- Single decorator handles all inheritance strategies
- Type hints work correctly with subtypes
- Auto-detection of discriminator values when not specified

Usage:
    from pynext.db import Table, polymorphic
    
    # Single Table Inheritance (default)
    @polymorphic("type")
    class Content(Table):
        title: str
    
    @polymorphic.subtype("article")
    class Article(Content):
        body: str
    
    # Joined Table Inheritance
    @polymorphic("type", strategy="joined")
    class Employee(Table):
        name: str
    
    # Concrete Table Inheritance
    @polymorphic(strategy="concrete")
    class Vehicle(Table):
        make: str

SQLAlchemy Comparison:
    SQLAlchemy (confusing):
        __mapper_args__ = {
            'polymorphic_on': type,
            'polymorphic_identity': 'article'
        }
    
    PyNext (simple):
        @polymorphic("type")
        class Content(Table): ...
        
        @polymorphic.subtype("article")
        class Article(Content): ...
"""

from __future__ import annotations

from typing import (
    Any,
    Callable,
    Optional,
    Type,
    TypeVar,
    Union,
    overload,
    TYPE_CHECKING,
)
from functools import wraps

from pynext.db.polymorphic.registry import (
    InheritanceStrategy,
    PolymorphicConfig,
    get_polymorphic_registry,
)

if TYPE_CHECKING:
    from pynext.db.table import Table

T = TypeVar("T", bound="Table")


class PolymorphicDecorator:
    """
    Decorator for marking a class as polymorphic base.
    
    Can be used in multiple ways:
    
    1. With discriminator column:
        @polymorphic("type")
        class Content(Table): ...
    
    2. With strategy:
        @polymorphic("type", strategy="joined")
        class Employee(Table): ...
    
    3. Just strategy (for concrete, no discriminator needed):
        @polymorphic(strategy="concrete")
        class Vehicle(Table): ...
    
    4. As subtype decorator:
        @polymorphic.subtype("article")
        class Article(Content): ...
    """
    
    @overload
    def __call__(self, cls: Type[T]) -> Type[T]: ...
    
    @overload
    def __call__(
        self,
        discriminator: str,
        *,
        strategy: str = "single_table",
        identity: Optional[str] = None,
    ) -> Callable[[Type[T]], Type[T]]: ...
    
    def __call__(
        self,
        discriminator_or_cls: Union[str, Type[T], None] = None,
        *,
        strategy: str = "single_table",
        identity: Optional[str] = None,
    ) -> Union[Type[T], Callable[[Type[T]], Type[T]]]:
        """
        Mark a class as a polymorphic base.
        
        Args:
            discriminator_or_cls: Either the discriminator column name,
                or the class itself (when used without parentheses)
            strategy: "single_table" (default), "joined", or "concrete"
            identity: Optional discriminator value for base class
        
        Returns:
            Decorated class or decorator function
        """
        # Parse strategy
        strategy_enum = self._parse_strategy(strategy)
        
        # Case 1: @polymorphic used without parentheses (rare)
        if isinstance(discriminator_or_cls, type):
            return self._register_base(
                discriminator_or_cls,
                discriminator="type",  # Default
                strategy=strategy_enum,
                identity=identity,
            )
        
        # Case 2: @polymorphic("type") or @polymorphic(strategy="concrete")
        discriminator = discriminator_or_cls or "type"
        
        def decorator(cls: Type[T]) -> Type[T]:
            return self._register_base(
                cls,
                discriminator=discriminator,
                strategy=strategy_enum,
                identity=identity,
            )
        
        return decorator
    
    def _register_base(
        self,
        cls: Type[T],
        discriminator: str,
        strategy: InheritanceStrategy,
        identity: Optional[str],
    ) -> Type[T]:
        """Register a class as polymorphic base."""
        registry = get_polymorphic_registry()
        
        # Register with the global registry
        config = registry.register_base(
            cls,
            discriminator=discriminator,
            strategy=strategy,
            identity=identity,
        )
        
        # Attach config to class for easy access
        cls._polymorphic_config = config
        cls._is_polymorphic_base = True
        
        # Add discriminator column if STI or Joined
        if strategy in (InheritanceStrategy.SINGLE_TABLE, InheritanceStrategy.JOINED):
            self._ensure_discriminator_column(cls, discriminator)
        
        return cls
    
    def _ensure_discriminator_column(self, cls: Type[T], discriminator: str) -> None:
        """Ensure the discriminator column exists on the class."""
        # Check if discriminator is already defined
        if not hasattr(cls, '__annotations__'):
            cls.__annotations__ = {}
        
        if discriminator not in cls.__annotations__:
            # Add discriminator column
            cls.__annotations__[discriminator] = str
            setattr(cls, discriminator, None)
    
    def _parse_strategy(self, strategy: str) -> InheritanceStrategy:
        """Parse strategy string to enum."""
        strategy_map = {
            "single_table": InheritanceStrategy.SINGLE_TABLE,
            "sti": InheritanceStrategy.SINGLE_TABLE,
            "joined": InheritanceStrategy.JOINED,
            "concrete": InheritanceStrategy.CONCRETE,
        }
        
        normalized = strategy.lower().replace("-", "_")
        if normalized not in strategy_map:
            valid = list(strategy_map.keys())
            raise ValueError(
                f"Invalid strategy '{strategy}'. Valid options: {valid}"
            )
        
        return strategy_map[normalized]
    
    def subtype(
        self,
        identity: Optional[str] = None,
    ) -> Callable[[Type[T]], Type[T]]:
        """
        Mark a class as a polymorphic subtype.
        
        Args:
            identity: Discriminator value for this subtype.
                If not provided, uses lowercase class name.
        
        Returns:
            Decorator function
        
        Example:
            @polymorphic.subtype("article")
            class Article(Content):
                body: str
            
            # Auto-generated identity
            @polymorphic.subtype()
            class Video(Content):  # identity = "video"
                url: str
        """
        def decorator(cls: Type[T]) -> Type[T]:
            return self._register_subtype(cls, identity)
        
        return decorator
    
    def _register_subtype(
        self,
        cls: Type[T],
        identity: Optional[str],
    ) -> Type[T]:
        """Register a class as a polymorphic subtype."""
        # Find the polymorphic base class
        base_class = self._find_polymorphic_base(cls)
        
        if base_class is None:
            raise ValueError(
                f"Class {cls.__name__} must inherit from a @polymorphic base class. "
                f"Make sure the parent class is decorated with @polymorphic."
            )
        
        # Auto-generate identity if not provided
        if identity is None:
            identity = cls.__name__.lower()
        
        # Register with global registry
        registry = get_polymorphic_registry()
        registry.register_subtype(base_class, identity, cls)
        
        # Attach metadata to class
        cls._polymorphic_identity = identity
        cls._polymorphic_base = base_class
        cls._is_polymorphic_subtype = True
        
        return cls
    
    def _find_polymorphic_base(self, cls: Type[T]) -> Optional[Type[T]]:
        """Find the polymorphic base class in the inheritance chain."""
        for base in cls.__mro__[1:]:  # Skip self
            if hasattr(base, '_is_polymorphic_base') and base._is_polymorphic_base:
                return base
        return None


# Create the decorator instance
polymorphic = PolymorphicDecorator()


def is_polymorphic(cls: Type) -> bool:
    """Check if a class is part of a polymorphic hierarchy."""
    return hasattr(cls, '_polymorphic_config') or hasattr(cls, '_polymorphic_base')


def is_polymorphic_base(cls: Type) -> bool:
    """Check if a class is a polymorphic base (not a subtype)."""
    is_base = getattr(cls, '_is_polymorphic_base', False)
    is_subtype = getattr(cls, '_is_polymorphic_subtype', False)
    return is_base and not is_subtype


def is_polymorphic_subtype(cls: Type) -> bool:
    """Check if a class is a polymorphic subtype."""
    return getattr(cls, '_is_polymorphic_subtype', False)


def get_polymorphic_identity(cls: Type) -> Optional[str]:
    """Get the discriminator value for a polymorphic class."""
    if hasattr(cls, '_polymorphic_identity'):
        return cls._polymorphic_identity
    if hasattr(cls, '_polymorphic_config'):
        return cls._polymorphic_config.identity
    return None


def get_polymorphic_base(cls: Type) -> Optional[Type]:
    """Get the polymorphic base class for a subtype."""
    if hasattr(cls, '_polymorphic_base'):
        return cls._polymorphic_base
    if hasattr(cls, '_is_polymorphic_base') and cls._is_polymorphic_base:
        return cls
    return None


def get_discriminator_column(cls: Type) -> Optional[str]:
    """Get the discriminator column name for a polymorphic class."""
    registry = get_polymorphic_registry()
    return registry.get_discriminator(cls)


def get_inheritance_strategy(cls: Type) -> Optional[InheritanceStrategy]:
    """Get the inheritance strategy for a polymorphic class."""
    registry = get_polymorphic_registry()
    return registry.get_strategy(cls)


__all__ = [
    "polymorphic",
    "PolymorphicDecorator",
    "is_polymorphic",
    "is_polymorphic_base",
    "is_polymorphic_subtype",
    "get_polymorphic_identity",
    "get_polymorphic_base",
    "get_discriminator_column",
    "get_inheritance_strategy",
]

