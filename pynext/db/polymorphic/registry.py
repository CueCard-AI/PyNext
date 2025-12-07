"""
PyNext Polymorphic Type Registry.

Manages the mapping between discriminator values and Python classes
for polymorphic inheritance patterns.

Design Philosophy:
- Global registry for type lookups
- Thread-safe operations
- Fast O(1) lookups by discriminator value
- Support for multiple inheritance hierarchies

Usage:
    from pynext.db.polymorphic.registry import PolymorphicRegistry
    
    registry = get_polymorphic_registry()
    registry.register(Content, "article", Article)
    
    # Later, when loading from DB
    cls = registry.get_class(Content, "article")
    # Returns: Article
"""

from __future__ import annotations

from typing import (
    Any,
    Dict,
    Optional,
    Type,
    TypeVar,
    Set,
    List,
    Tuple,
    TYPE_CHECKING,
)
from enum import Enum
import threading

if TYPE_CHECKING:
    from pynext.db.table import Table

T = TypeVar("T", bound="Table")


class InheritanceStrategy(Enum):
    """
    Polymorphic inheritance strategy.
    
    SINGLE_TABLE (STI):
        All types in one table with discriminator column.
        Pros: Simple queries, no JOINs
        Cons: Nullable columns for type-specific fields
    
    JOINED:
        Base table + separate table per subtype.
        Pros: Normalized, no nulls
        Cons: Requires JOINs for queries
    
    CONCRETE:
        Each type has its own complete table.
        Pros: Most isolated, fastest single-type queries
        Cons: No shared table, UNION for cross-type queries
    """
    SINGLE_TABLE = "single_table"
    JOINED = "joined"
    CONCRETE = "concrete"


class PolymorphicConfig:
    """
    Configuration for a polymorphic base class.
    
    Attributes:
        base_class: The base polymorphic class
        discriminator: Column name for type discrimination
        strategy: Inheritance strategy (STI, Joined, Concrete)
        subtypes: Dict mapping discriminator values to subtype classes
        identity: Discriminator value for this class (if subtype)
    """
    
    def __init__(
        self,
        base_class: Type[T],
        discriminator: str = "type",
        strategy: InheritanceStrategy = InheritanceStrategy.SINGLE_TABLE,
        identity: Optional[str] = None,
    ):
        self.base_class = base_class
        self.discriminator = discriminator
        self.strategy = strategy
        self.identity = identity
        self.subtypes: Dict[str, Type[T]] = {}
        self._parent_config: Optional[PolymorphicConfig] = None
    
    def register_subtype(self, identity: str, cls: Type[T]) -> None:
        """Register a subtype class."""
        self.subtypes[identity] = cls
    
    def get_subtype(self, identity: str) -> Optional[Type[T]]:
        """Get subtype class by identity."""
        return self.subtypes.get(identity)
    
    def get_all_subtypes(self) -> List[Type[T]]:
        """Get all registered subtype classes."""
        return list(self.subtypes.values())
    
    def get_identity_for_class(self, cls: Type[T]) -> Optional[str]:
        """Get discriminator value for a class."""
        for identity, subtype in self.subtypes.items():
            if subtype == cls:
                return identity
        return None


class PolymorphicRegistry:
    """
    Global registry for polymorphic type mappings.
    
    Thread-safe singleton that tracks all polymorphic hierarchies
    in the application.
    
    Example:
        registry = get_polymorphic_registry()
        
        # Register a base class
        config = registry.register_base(
            Content, 
            discriminator="type",
            strategy=InheritanceStrategy.SINGLE_TABLE
        )
        
        # Register subtypes
        registry.register_subtype(Content, "article", Article)
        registry.register_subtype(Content, "video", Video)
        
        # Lookup
        cls = registry.get_class(Content, "article")  # Returns Article
    """
    
    _instance: Optional["PolymorphicRegistry"] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> "PolymorphicRegistry":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._configs: Dict[Type, PolymorphicConfig] = {}
                    cls._instance._class_to_base: Dict[Type, Type] = {}
        return cls._instance
    
    def register_base(
        self,
        cls: Type[T],
        discriminator: str = "type",
        strategy: InheritanceStrategy = InheritanceStrategy.SINGLE_TABLE,
        identity: Optional[str] = None,
    ) -> PolymorphicConfig:
        """
        Register a base polymorphic class.
        
        Args:
            cls: The base class
            discriminator: Column name for type discrimination
            strategy: Inheritance strategy
            identity: Optional discriminator value for base class itself
        
        Returns:
            PolymorphicConfig for this class
        """
        config = PolymorphicConfig(
            base_class=cls,
            discriminator=discriminator,
            strategy=strategy,
            identity=identity,
        )
        self._configs[cls] = config
        self._class_to_base[cls] = cls
        
        # If base has identity, register it as a subtype too
        if identity:
            config.register_subtype(identity, cls)
        
        return config
    
    def register_subtype(
        self,
        base_class: Type[T],
        identity: str,
        subtype_class: Type[T],
    ) -> None:
        """
        Register a subtype of a polymorphic base.
        
        Args:
            base_class: The polymorphic base class
            identity: Discriminator value for this subtype
            subtype_class: The subtype class
        """
        if base_class not in self._configs:
            raise ValueError(
                f"Base class {base_class.__name__} is not registered as polymorphic. "
                f"Use @polymorphic decorator on the base class first."
            )
        
        config = self._configs[base_class]
        config.register_subtype(identity, subtype_class)
        self._class_to_base[subtype_class] = base_class
        
        # Create config for subtype pointing to parent
        subtype_config = PolymorphicConfig(
            base_class=base_class,
            discriminator=config.discriminator,
            strategy=config.strategy,
            identity=identity,
        )
        subtype_config._parent_config = config
        self._configs[subtype_class] = subtype_config
    
    def get_config(self, cls: Type[T]) -> Optional[PolymorphicConfig]:
        """Get polymorphic config for a class."""
        return self._configs.get(cls)
    
    def get_base_config(self, cls: Type[T]) -> Optional[PolymorphicConfig]:
        """Get the base polymorphic config for a class (or itself if base)."""
        base = self._class_to_base.get(cls)
        if base:
            return self._configs.get(base)
        return self._configs.get(cls)
    
    def get_class(
        self,
        base_class: Type[T],
        identity: str,
    ) -> Optional[Type[T]]:
        """
        Get subtype class by discriminator value.
        
        Args:
            base_class: The polymorphic base class
            identity: Discriminator value
        
        Returns:
            The subtype class, or None if not found
        """
        config = self._configs.get(base_class)
        if config:
            return config.get_subtype(identity)
        return None
    
    def get_identity(self, cls: Type[T]) -> Optional[str]:
        """Get discriminator value for a class."""
        config = self._configs.get(cls)
        if config:
            return config.identity
        return None
    
    def get_base_class(self, cls: Type[T]) -> Optional[Type[T]]:
        """Get the base polymorphic class for a subtype."""
        return self._class_to_base.get(cls)
    
    def is_polymorphic(self, cls: Type[T]) -> bool:
        """Check if a class is part of a polymorphic hierarchy."""
        return cls in self._configs or cls in self._class_to_base
    
    def is_base_class(self, cls: Type[T]) -> bool:
        """Check if a class is a polymorphic base."""
        config = self._configs.get(cls)
        return config is not None and config.base_class == cls
    
    def is_subtype(self, cls: Type[T]) -> bool:
        """Check if a class is a polymorphic subtype."""
        return cls in self._class_to_base and self._class_to_base[cls] != cls
    
    def get_all_subtypes(self, base_class: Type[T]) -> List[Type[T]]:
        """Get all registered subtypes for a base class."""
        config = self._configs.get(base_class)
        if config:
            return config.get_all_subtypes()
        return []
    
    def get_discriminator(self, cls: Type[T]) -> Optional[str]:
        """Get discriminator column name for a polymorphic class."""
        config = self.get_base_config(cls)
        if config:
            return config.discriminator
        return None
    
    def get_strategy(self, cls: Type[T]) -> Optional[InheritanceStrategy]:
        """Get inheritance strategy for a polymorphic class."""
        config = self.get_base_config(cls)
        if config:
            return config.strategy
        return None
    
    def clear(self) -> None:
        """Clear all registrations (for testing)."""
        self._configs.clear()
        self._class_to_base.clear()


# Global registry instance
_registry: Optional[PolymorphicRegistry] = None


def get_polymorphic_registry() -> PolymorphicRegistry:
    """Get the global polymorphic registry."""
    global _registry
    if _registry is None:
        _registry = PolymorphicRegistry()
    return _registry


def reset_polymorphic_registry() -> None:
    """Reset the global registry (for testing)."""
    global _registry
    if _registry:
        _registry.clear()
    _registry = None


__all__ = [
    "InheritanceStrategy",
    "PolymorphicConfig",
    "PolymorphicRegistry",
    "get_polymorphic_registry",
    "reset_polymorphic_registry",
]

