"""
PyNext Generic Foreign Keys.

Implements Union-type foreign keys that can reference multiple tables.
Much simpler than Django's ContentType framework or SQLAlchemy's 
workarounds.

Design Philosophy:
- Use Python's Union type hints for type safety
- Auto-generate target_type and target_id columns
- Lazy loading of referenced objects
- IDE support through proper type hints

Usage:
    from pynext.db import Table, generic_fk
    from typing import Union
    
    class Comment(Table):
        content: str
        author_id: int
        
        # Can be attached to Article, Video, or Photo
        target: Union[Article, Video, Photo] = generic_fk()
    
    # Creating
    comment = await Comment.create(
        content="Great!",
        author_id=1,
        target=article  # Pass actual object
    )
    
    # Loading
    comment = await Comment.get(1)
    target = await comment.target  # Returns Article, Video, or Photo

SQLAlchemy Comparison:
    SQLAlchemy has no built-in generic FK support.
    You need third-party packages or complex workarounds.
    
    Django uses ContentType which requires a separate table
    and is confusing to understand.
    
    PyNext: Just use Union[A, B, C] = generic_fk()
"""

from __future__ import annotations

from typing import (
    Any,
    Dict,
    Generic,
    get_origin,
    get_args,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
    TYPE_CHECKING,
)
from dataclasses import dataclass
import inspect

if TYPE_CHECKING:
    from pynext.db.table import Table

T = TypeVar("T", bound="Table")


@dataclass
class GenericFKConfig:
    """
    Configuration for a generic foreign key.
    
    Attributes:
        field_name: Name of the generic FK field
        type_column: Column storing the target type (default: {field}_type)
        id_column: Column storing the target ID (default: {field}_id)
        allowed_types: List of allowed target types from Union
    """
    field_name: str
    type_column: str
    id_column: str
    allowed_types: List[Type["Table"]]
    
    def validate_target(self, target: Any) -> bool:
        """Check if a target is an allowed type."""
        if target is None:
            return True
        return type(target) in self.allowed_types or any(
            isinstance(target, t) for t in self.allowed_types
        )
    
    def get_type_name(self, target: Any) -> Optional[str]:
        """Get the type identifier for a target."""
        if target is None:
            return None
        
        target_type = type(target)
        
        # Use table name as type identifier
        if hasattr(target_type, '__tablename__'):
            return target_type.__tablename__
        if hasattr(target_type, '_table_name'):
            return target_type._table_name
        
        return target_type.__name__.lower()
    
    def get_target_id(self, target: Any) -> Optional[int]:
        """Get the ID of a target."""
        if target is None:
            return None
        return getattr(target, 'id', None)
    
    def get_type_class(self, type_name: str) -> Optional[Type["Table"]]:
        """Get the class for a type name."""
        for cls in self.allowed_types:
            table_name = None
            if hasattr(cls, '__tablename__'):
                table_name = cls.__tablename__
            elif hasattr(cls, '_table_name'):
                table_name = cls._table_name
            else:
                table_name = cls.__name__.lower()
            
            if table_name == type_name:
                return cls
        
        return None


class GenericForeignKey(Generic[T]):
    """
    Descriptor for generic foreign keys.
    
    Creates two database columns:
    - {name}_type: Stores the target table name
    - {name}_id: Stores the target row ID
    
    Provides lazy loading and type-safe access.
    
    Example:
        class Comment(Table):
            target: Union[Article, Video] = generic_fk()
        
        # Setting (sync, just stores values)
        comment.target = article
        
        # Getting (async, loads from DB)
        target = await comment.target
    """
    
    def __init__(
        self,
        type_column: Optional[str] = None,
        id_column: Optional[str] = None,
    ):
        """
        Initialize generic foreign key.
        
        Args:
            type_column: Custom column name for type (default: {field}_type)
            id_column: Custom column name for ID (default: {field}_id)
        """
        self._type_column = type_column
        self._id_column = id_column
        self._field_name: Optional[str] = None
        self._config: Optional[GenericFKConfig] = None
        self._allowed_types: List[Type] = []
    
    def __set_name__(self, owner: Type, name: str) -> None:
        """Called when descriptor is assigned to a class attribute."""
        self._field_name = name
        self._owner = owner
        
        # Get allowed types from type annotation
        self._allowed_types = self._extract_union_types(owner, name)
        
        # Create config
        type_col = self._type_column or f"{name}_type"
        id_col = self._id_column or f"{name}_id"
        
        self._config = GenericFKConfig(
            field_name=name,
            type_column=type_col,
            id_column=id_col,
            allowed_types=self._allowed_types,
        )
        
        # Add columns to owner's annotations
        self._add_columns_to_owner(owner, type_col, id_col)
        
        # Register config on owner
        if not hasattr(owner, '_generic_fk_configs'):
            owner._generic_fk_configs = {}
        owner._generic_fk_configs[name] = self._config
    
    def _extract_union_types(self, owner: Type, name: str) -> List[Type]:
        """Extract types from Union annotation."""
        annotations = getattr(owner, '__annotations__', {})
        
        if name not in annotations:
            return []
        
        type_hint = annotations[name]
        
        # Handle Union types
        origin = get_origin(type_hint)
        if origin is Union:
            args = get_args(type_hint)
            # Filter out NoneType
            return [t for t in args if t is not type(None)]
        
        return []
    
    def _add_columns_to_owner(
        self,
        owner: Type,
        type_col: str,
        id_col: str,
    ) -> None:
        """Add the type and ID columns to the owner class."""
        if not hasattr(owner, '__annotations__'):
            owner.__annotations__ = {}
        
        # Add type column (string)
        owner.__annotations__[type_col] = Optional[str]
        if not hasattr(owner, type_col):
            setattr(owner, type_col, None)
        
        # Add ID column (int)
        owner.__annotations__[id_col] = Optional[int]
        if not hasattr(owner, id_col):
            setattr(owner, id_col, None)
    
    def __get__(
        self,
        obj: Optional[T],
        objtype: Optional[Type[T]] = None,
    ) -> Union["GenericForeignKey[T]", "GenericFKLoader[T]"]:
        """
        Get the generic FK value.
        
        Returns a loader that can be awaited to get the actual target.
        """
        if obj is None:
            return self
        
        # Return a loader that can be awaited
        return GenericFKLoader(obj, self._config)
    
    def __set__(self, obj: T, value: Any) -> None:
        """
        Set the generic FK value.
        
        Accepts either:
        - A model instance (extracts type and ID)
        - None (clears the reference)
        - A dict with 'type' and 'id' keys
        """
        if value is None:
            setattr(obj, self._config.type_column, None)
            setattr(obj, self._config.id_column, None)
            return
        
        if isinstance(value, dict):
            # Dict with type and id
            setattr(obj, self._config.type_column, value.get('type'))
            setattr(obj, self._config.id_column, value.get('id'))
            return
        
        # Model instance
        if not self._config.validate_target(value):
            allowed = [t.__name__ for t in self._config.allowed_types]
            raise TypeError(
                f"Invalid target type {type(value).__name__}. "
                f"Allowed types: {allowed}"
            )
        
        type_name = self._config.get_type_name(value)
        target_id = self._config.get_target_id(value)
        
        setattr(obj, self._config.type_column, type_name)
        setattr(obj, self._config.id_column, target_id)


class GenericFKLoader(Generic[T]):
    """
    Async loader for generic FK targets.
    
    Returned by GenericForeignKey.__get__ to allow async loading.
    
    Usage:
        target = await comment.target
    """
    
    def __init__(self, obj: T, config: GenericFKConfig):
        self._obj = obj
        self._config = config
        self._cached_target: Optional[Any] = None
        self._loaded = False
    
    def __await__(self):
        """Allow awaiting to load the target."""
        return self._load().__await__()
    
    async def _load(self) -> Optional[Any]:
        """Load the target from database."""
        if self._loaded:
            return self._cached_target
        
        type_name = getattr(self._obj, self._config.type_column, None)
        target_id = getattr(self._obj, self._config.id_column, None)
        
        if type_name is None or target_id is None:
            self._loaded = True
            self._cached_target = None
            return None
        
        # Get the target class
        target_class = self._config.get_type_class(type_name)
        
        if target_class is None:
            self._loaded = True
            self._cached_target = None
            return None
        
        # Load the target
        if hasattr(target_class, 'get'):
            self._cached_target = await target_class.get(target_id)
        else:
            self._cached_target = None
        
        self._loaded = True
        return self._cached_target
    
    @property
    def target_type(self) -> Optional[str]:
        """Get the target type name."""
        return getattr(self._obj, self._config.type_column, None)
    
    @property
    def target_id(self) -> Optional[int]:
        """Get the target ID."""
        return getattr(self._obj, self._config.id_column, None)
    
    @property
    def is_set(self) -> bool:
        """Check if the generic FK is set."""
        return (
            getattr(self._obj, self._config.type_column, None) is not None and
            getattr(self._obj, self._config.id_column, None) is not None
        )


def generic_fk(
    type_column: Optional[str] = None,
    id_column: Optional[str] = None,
) -> GenericForeignKey:
    """
    Create a generic foreign key descriptor.
    
    Args:
        type_column: Custom column name for type (default: {field}_type)
        id_column: Custom column name for ID (default: {field}_id)
    
    Returns:
        GenericForeignKey descriptor
    
    Example:
        class Comment(Table):
            content: str
            
            # Default column names: target_type, target_id
            target: Union[Article, Video] = generic_fk()
            
            # Custom column names
            parent: Union[Post, Comment] = generic_fk(
                type_column="parent_kind",
                id_column="parent_ref"
            )
    """
    return GenericForeignKey(type_column=type_column, id_column=id_column)


def get_generic_fk_config(
    cls: Type["Table"],
    field_name: str,
) -> Optional[GenericFKConfig]:
    """Get the generic FK config for a field."""
    configs = getattr(cls, '_generic_fk_configs', {})
    return configs.get(field_name)


def get_all_generic_fk_configs(
    cls: Type["Table"],
) -> Dict[str, GenericFKConfig]:
    """Get all generic FK configs for a class."""
    return getattr(cls, '_generic_fk_configs', {})


__all__ = [
    "GenericForeignKey",
    "GenericFKConfig",
    "GenericFKLoader",
    "generic_fk",
    "get_generic_fk_config",
    "get_all_generic_fk_configs",
]

