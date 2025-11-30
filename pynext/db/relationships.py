"""
PyNext Database Relationships.

Automatic relationship detection and management.
Relationships are inferred from field naming conventions.

Design: Just name your field `author_id` and we figure out the rest.
"""

from __future__ import annotations

from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Type,
    TypeVar,
    TYPE_CHECKING,
    Union,
)

if TYPE_CHECKING:
    from pynext.db.table import Table
    from pynext.db.fields import FieldInfo

T = TypeVar("T", bound="Table")


class RelationshipType:
    """Types of relationships between models."""
    BELONGS_TO = "belongs_to"
    HAS_ONE = "has_one"
    HAS_MANY = "has_many"
    MANY_TO_MANY = "many_to_many"


class RelationshipInfo:
    """
    Information about a relationship between models.
    
    Attributes:
        name: Relationship name (e.g., "author")
        type: Relationship type (belongs_to, has_one, has_many)
        model: Related model class (or string name for lazy loading)
        foreign_key: Foreign key field name
        through: Junction table for many-to-many
    """
    
    def __init__(
        self,
        name: str,
        rel_type: str,
        model: Union[Type["Table"], str],
        foreign_key: Optional[str] = None,
        through: Optional[str] = None,
    ):
        self.name = name
        self.type = rel_type
        self.model = model
        self.foreign_key = foreign_key
        self.through = through
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for storage."""
        return {
            "name": self.name,
            "type": self.type,
            "model": self.model,
            "foreign_key": self.foreign_key,
            "through": self.through,
        }


def detect_relationships(
    model: Type["Table"],
    fields: Dict[str, "FieldInfo"],
    registry: Dict[str, Type["Table"]],
) -> Dict[str, RelationshipInfo]:
    """
    Auto-detect relationships from field naming conventions.
    
    Convention:
        `author_id: int` -> belongs_to Author (accessed via `.author`)
    
    Args:
        model: The model class
        fields: Field definitions
        registry: Registry of all model classes by table name
    
    Returns:
        Dict of relationship name -> RelationshipInfo
    """
    relationships: Dict[str, RelationshipInfo] = {}
    
    for name, field in fields.items():
        # Check for *_id pattern
        if name.endswith("_id"):
            # author_id -> author
            rel_name = name[:-3]
            
            # author -> authors (table name)
            table_name = rel_name + "s"
            
            # Find the related model
            related_model = registry.get(table_name)
            
            if related_model:
                relationships[rel_name] = RelationshipInfo(
                    name=rel_name,
                    rel_type=RelationshipType.BELONGS_TO,
                    model=related_model,
                    foreign_key=name,
                )
            else:
                # Store as string for lazy resolution
                relationships[rel_name] = RelationshipInfo(
                    name=rel_name,
                    rel_type=RelationshipType.BELONGS_TO,
                    model=table_name,  # Will be resolved later
                    foreign_key=name,
                )
    
    return relationships


def detect_reverse_relationships(
    model: Type["Table"],
    registry: Dict[str, Type["Table"]],
) -> Dict[str, RelationshipInfo]:
    """
    Auto-detect reverse relationships (has_many, has_one).
    
    For each model that has a FK to this model, create a reverse relationship.
    
    Args:
        model: The model class
        registry: Registry of all model classes
    
    Returns:
        Dict of relationship name -> RelationshipInfo
    """
    relationships: Dict[str, RelationshipInfo] = {}
    table_name = model.__table_name__
    
    # user -> user_id (the FK that other models would have)
    expected_fk = table_name[:-1] + "_id" if table_name.endswith("s") else table_name + "_id"
    
    for other_table, other_model in registry.items():
        if other_model == model:
            continue
        
        # Check if other model has a FK to this model
        other_fields = getattr(other_model, "_fields", {})
        
        if expected_fk in other_fields:
            # posts -> Post model has user_id -> User.posts
            relationships[other_table] = RelationshipInfo(
                name=other_table,
                rel_type=RelationshipType.HAS_MANY,
                model=other_model,
                foreign_key=expected_fk,
            )
    
    return relationships


class BelongsTo(Generic[T]):
    """
    Descriptor for belongs_to relationships.
    
    Provides lazy loading of related models.
    
    Usage:
        class Post(Table):
            author_id: int
            # Automatically gets:
            # author: BelongsTo[User]
    """
    
    def __init__(
        self,
        rel_name: str,
        model: Union[Type[T], str],
        foreign_key: str,
    ):
        self.rel_name = rel_name
        self._model = model
        self.foreign_key = foreign_key
        self._cache_attr = f"_cached_{rel_name}"
    
    @property
    def model(self) -> Type[T]:
        """Get the related model (resolving lazy string if needed)."""
        if isinstance(self._model, str):
            from pynext.db.table import _model_registry
            self._model = _model_registry.get(self._model)
        return self._model
    
    def __get__(self, obj: Optional["Table"], objtype: Type["Table"] = None) -> Optional[T]:
        """Get the related model instance (cached)."""
        if obj is None:
            return self
        
        # Check cache
        cached = getattr(obj, self._cache_attr, None)
        if cached is not None:
            return cached
        
        # Return None - actual loading happens in query.with_related()
        return None
    
    def __set__(self, obj: "Table", value: Optional[T]) -> None:
        """Set the related model instance (cache)."""
        setattr(obj, self._cache_attr, value)


class HasMany(Generic[T]):
    """
    Descriptor for has_many relationships.
    
    Provides lazy loading of related models.
    
    Usage:
        class User(Table):
            # Automatically gets:
            # posts: HasMany[Post]
    """
    
    def __init__(
        self,
        rel_name: str,
        model: Union[Type[T], str],
        foreign_key: str,
    ):
        self.rel_name = rel_name
        self._model = model
        self.foreign_key = foreign_key
        self._cache_attr = f"_cached_{rel_name}"
    
    @property
    def model(self) -> Type[T]:
        """Get the related model (resolving lazy string if needed)."""
        if isinstance(self._model, str):
            from pynext.db.table import _model_registry
            self._model = _model_registry.get(self._model)
        return self._model
    
    def __get__(self, obj: Optional["Table"], objtype: Type["Table"] = None) -> List[T]:
        """Get the related model instances (cached)."""
        if obj is None:
            return self
        
        # Check cache
        cached = getattr(obj, self._cache_attr, None)
        if cached is not None:
            return cached
        
        # Return empty list - actual loading happens in query.with_related()
        return []
    
    def __set__(self, obj: "Table", value: List[T]) -> None:
        """Set the related model instances (cache)."""
        setattr(obj, self._cache_attr, value)


class HasOne(Generic[T]):
    """
    Descriptor for has_one relationships.
    
    Like has_many but returns a single instance.
    
    Usage:
        class User(Table):
            # Explicitly defined:
            profile: HasOne[Profile] = has_one(Profile, "user_id")
    """
    
    def __init__(
        self,
        rel_name: str,
        model: Union[Type[T], str],
        foreign_key: str,
    ):
        self.rel_name = rel_name
        self._model = model
        self.foreign_key = foreign_key
        self._cache_attr = f"_cached_{rel_name}"
    
    @property
    def model(self) -> Type[T]:
        """Get the related model (resolving lazy string if needed)."""
        if isinstance(self._model, str):
            from pynext.db.table import _model_registry
            self._model = _model_registry.get(self._model)
        return self._model
    
    def __get__(self, obj: Optional["Table"], objtype: Type["Table"] = None) -> Optional[T]:
        """Get the related model instance (cached)."""
        if obj is None:
            return self
        
        # Check cache
        cached = getattr(obj, self._cache_attr, None)
        if cached is not None:
            return cached
        
        # Return None - actual loading happens in query.with_related()
        return None
    
    def __set__(self, obj: "Table", value: Optional[T]) -> None:
        """Set the related model instance (cache)."""
        setattr(obj, self._cache_attr, value)


# Convenience functions for explicit relationship definition

def belongs_to(
    model: Union[Type[T], str],
    foreign_key: Optional[str] = None,
) -> BelongsTo[T]:
    """
    Define a belongs_to relationship explicitly.
    
    Usually auto-detected, but use this for custom foreign keys.
    
    Examples:
        class Post(Table):
            author_id: int
            author: User = belongs_to(User, "author_id")
    """
    return BelongsTo(
        rel_name="",  # Will be set by metaclass
        model=model,
        foreign_key=foreign_key or "",
    )


def has_many(
    model: Union[Type[T], str],
    foreign_key: Optional[str] = None,
) -> HasMany[T]:
    """
    Define a has_many relationship explicitly.
    
    Usually auto-detected, but use this for custom foreign keys.
    
    Examples:
        class User(Table):
            posts: List[Post] = has_many(Post, "author_id")
    """
    return HasMany(
        rel_name="",  # Will be set by metaclass
        model=model,
        foreign_key=foreign_key or "",
    )


def has_one(
    model: Union[Type[T], str],
    foreign_key: Optional[str] = None,
) -> HasOne[T]:
    """
    Define a has_one relationship explicitly.
    
    Examples:
        class User(Table):
            profile: Profile = has_one(Profile, "user_id")
    """
    return HasOne(
        rel_name="",  # Will be set by metaclass
        model=model,
        foreign_key=foreign_key or "",
    )


def setup_relationships(model: Type["Table"], registry: Dict[str, Type["Table"]]) -> None:
    """
    Set up all relationships for a model.
    
    Called after all models are registered.
    
    Args:
        model: The model class
        registry: Registry of all model classes
    """
    fields = getattr(model, "_fields", {})
    
    # Detect belongs_to from *_id fields
    belongs_to_rels = detect_relationships(model, fields, registry)
    
    # Detect has_many from other models' FKs
    has_many_rels = detect_reverse_relationships(model, registry)
    
    # Combine all relationships
    all_relationships: Dict[str, Dict] = {}
    
    for name, rel in belongs_to_rels.items():
        all_relationships[name] = rel.to_dict()
    
    for name, rel in has_many_rels.items():
        all_relationships[name] = rel.to_dict()
    
    # Store on model
    model._relationships = all_relationships
    
    # Create descriptors for belongs_to
    for name, rel in belongs_to_rels.items():
        if not hasattr(model, name):
            descriptor = BelongsTo(name, rel.model, rel.foreign_key)
            setattr(model, name, descriptor)
    
    # Create descriptors for has_many
    for name, rel in has_many_rels.items():
        if not hasattr(model, name):
            descriptor = HasMany(name, rel.model, rel.foreign_key)
            setattr(model, name, descriptor)

