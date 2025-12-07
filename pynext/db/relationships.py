"""
PyNext Database Relationships.

Automatic relationship detection and management with bidirectional sync support.

Design Philosophy:
- Just name your field `author_id` and we figure out the rest
- Add `backref="author"` to enable automatic bidirectional sync
- Or use `back_populates="posts"` for explicit bidirectional linking
- Fine-grained updates: only affected objects sync (SolidJS principle)
- AI-friendly: explicit, traceable behavior

Usage:
    # Option 1: Automatic backref (creates reverse relationship)
    class User(Table):
        posts: List["Post"] = has_many("Post", backref="author")
        # Automatically creates Post.author
    
    # Option 2: Explicit bidirectional linking
    class User(Table):
        posts: List["Post"] = has_many("Post", back_populates="author")
    
    class Post(Table):
        author_id: int
        author: "User" = belongs_to("User", back_populates="posts")
    
    # Both sync automatically:
    user.posts.append(post)  # Also sets post.author = user
    post.author = other_user  # Removes from old user.posts, adds to new
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
        backref: Name of auto-created reverse relationship
        back_populates: Name of existing reverse relationship to sync with
    """
    
    def __init__(
        self,
        name: str,
        rel_type: str,
        model: Union[Type["Table"], str],
        foreign_key: Optional[str] = None,
        through: Optional[str] = None,
        backref: Optional[str] = None,
        back_populates: Optional[str] = None,
    ):
        self.name = name
        self.type = rel_type
        self.model = model
        self.foreign_key = foreign_key
        self.through = through
        self.backref = backref
        self.back_populates = back_populates
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for storage."""
        return {
            "name": self.name,
            "type": self.type,
            "model": self.model,
            "foreign_key": self.foreign_key,
            "through": self.through,
            "backref": self.backref,
            "back_populates": self.back_populates,
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
    
    Provides lazy loading of related models with optional bidirectional sync.
    
    Usage:
        class Post(Table):
            author_id: int
            # Auto-detected:
            # author: BelongsTo[User]
            
            # Or explicit with backref:
            author: User = belongs_to(User, "author_id", back_populates="posts")
    
    When `back_populates` or `backref` is set:
        post.author = user  # Also adds post to user.posts
        post.author = None  # Also removes post from old user.posts
    """
    
    def __init__(
        self,
        rel_name: str,
        model: Union[Type[T], str],
        foreign_key: str,
        backref: Optional[str] = None,
        back_populates: Optional[str] = None,
    ):
        """
        Initialize BelongsTo descriptor.
        
        Args:
            rel_name: Name of this relationship (e.g., "author")
            model: Related model class or string name
            foreign_key: FK field name (e.g., "author_id")
            backref: Name for auto-created reverse relationship
            back_populates: Name of existing reverse relationship to sync
        """
        self.rel_name = rel_name
        self._model = model
        self.foreign_key = foreign_key
        self.backref = backref
        self.back_populates = back_populates
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
        """
        Set the related model instance.
        
        If backref/back_populates is configured, also updates the reverse side:
        - Removes obj from old_value's collection
        - Adds obj to new_value's collection
        """
        # Get old value for sync
        old_value = getattr(obj, self._cache_attr, None)
        
        # Set the new value
        setattr(obj, self._cache_attr, value)
        
        # Update FK field
        if self.foreign_key and hasattr(obj, self.foreign_key):
            fk_value = value.id if value is not None and hasattr(value, 'id') else None
            setattr(obj, self.foreign_key, fk_value)
        
        # Sync with reverse relationship if configured
        if self.backref or self.back_populates:
            from pynext.db.relationships.backref import get_sync_manager
            get_sync_manager().sync_belongs_to_set(
                obj, self.rel_name, old_value, value
            )


class HasMany(Generic[T]):
    """
    Descriptor for has_many relationships.
    
    Provides lazy loading of related models with optional bidirectional sync.
    Returns a SyncedList when backref is enabled.
    
    Usage:
        class User(Table):
            # Auto-detected:
            # posts: HasMany[Post]
            
            # Or explicit with backref:
            posts: List[Post] = has_many(Post, "author_id", backref="author")
    
    When `backref` is set:
        user.posts.append(post)  # Also sets post.author = user
        user.posts.remove(post)  # Also sets post.author = None
    """
    
    def __init__(
        self,
        rel_name: str,
        model: Union[Type[T], str],
        foreign_key: str,
        backref: Optional[str] = None,
        back_populates: Optional[str] = None,
    ):
        """
        Initialize HasMany descriptor.
        
        Args:
            rel_name: Name of this relationship (e.g., "posts")
            model: Related model class or string name
            foreign_key: FK field name on related model (e.g., "author_id")
            backref: Name for auto-created reverse belongs_to
            back_populates: Name of existing reverse relationship to sync
        """
        self.rel_name = rel_name
        self._model = model
        self.foreign_key = foreign_key
        self.backref = backref
        self.back_populates = back_populates
        self._cache_attr = f"_cached_{rel_name}"
    
    @property
    def model(self) -> Type[T]:
        """Get the related model (resolving lazy string if needed)."""
        if isinstance(self._model, str):
            from pynext.db.table import _model_registry
            self._model = _model_registry.get(self._model)
        return self._model
    
    def __get__(self, obj: Optional["Table"], objtype: Type["Table"] = None) -> List[T]:
        """
        Get the related model instances.
        
        Returns a SyncedList if backref is enabled, for automatic sync.
        Returns cached value if already loaded.
        Returns empty list/SyncedList otherwise.
        """
        if obj is None:
            return self
        
        # Check cache
        cached = getattr(obj, self._cache_attr, None)
        if cached is not None:
            return cached
        
        # Create appropriate collection based on backref setting
        if self.backref or self.back_populates:
            # Return SyncedList for automatic bidirectional sync
            from pynext.db.relationships.collections import SyncedList
            synced_list = SyncedList(obj, self.rel_name, [])
            setattr(obj, self._cache_attr, synced_list)
            return synced_list
        else:
            # Return regular empty list (no sync needed)
            return []
    
    def __set__(self, obj: "Table", value: List[T]) -> None:
        """
        Set the related model instances.
        
        If backref is enabled, wraps in SyncedList.
        """
        if self.backref or self.back_populates:
            from pynext.db.relationships.collections import SyncedList
            if isinstance(value, SyncedList):
                setattr(obj, self._cache_attr, value)
            else:
                # Wrap in SyncedList
                synced_list = SyncedList(obj, self.rel_name, value)
                setattr(obj, self._cache_attr, synced_list)
        else:
            setattr(obj, self._cache_attr, value)


class HasOne(Generic[T]):
    """
    Descriptor for has_one relationships.
    
    Like has_many but returns a single instance.
    
    Usage:
        class User(Table):
            # Explicitly defined:
            profile: Profile = has_one(Profile, "user_id", backref="user")
    
    When `backref` is set:
        user.profile = profile  # Also sets profile.user = user
        user.profile = None     # Also sets old profile.user = None
    """
    
    def __init__(
        self,
        rel_name: str,
        model: Union[Type[T], str],
        foreign_key: str,
        backref: Optional[str] = None,
        back_populates: Optional[str] = None,
    ):
        """
        Initialize HasOne descriptor.
        
        Args:
            rel_name: Name of this relationship (e.g., "profile")
            model: Related model class or string name
            foreign_key: FK field name on related model (e.g., "user_id")
            backref: Name for auto-created reverse belongs_to
            back_populates: Name of existing reverse relationship to sync
        """
        self.rel_name = rel_name
        self._model = model
        self.foreign_key = foreign_key
        self.backref = backref
        self.back_populates = back_populates
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
        """
        Set the related model instance.
        
        If backref/back_populates is configured, also updates the reverse side.
        """
        # Get old value for sync
        old_value = getattr(obj, self._cache_attr, None)
        
        # Set the new value
        setattr(obj, self._cache_attr, value)
        
        # Sync with reverse relationship if configured
        if self.backref or self.back_populates:
            from pynext.db.relationships.backref import get_sync_manager
            get_sync_manager().sync_has_one_set(
                obj, self.rel_name, old_value, value
            )


# =============================================================================
# Convenience Functions for Explicit Relationship Definition
# =============================================================================

def belongs_to(
    model: Union[Type[T], str],
    foreign_key: Optional[str] = None,
    backref: Optional[str] = None,
    back_populates: Optional[str] = None,
) -> BelongsTo[T]:
    """
    Define a belongs_to relationship explicitly.
    
    Usually auto-detected from `*_id` fields, but use this for:
    - Custom foreign keys
    - Bidirectional sync with backref/back_populates
    
    Args:
        model: Related model class or string name
        foreign_key: FK field name (auto-detected if not provided)
        backref: Name for auto-created reverse has_many relationship
        back_populates: Name of existing reverse relationship to sync
    
    Examples:
        # Simple explicit definition
        class Post(Table):
            author_id: int
            author: User = belongs_to(User, "author_id")
        
        # With bidirectional sync (explicit)
        class Post(Table):
            author_id: int
            author: User = belongs_to(User, "author_id", back_populates="posts")
        
        # Auto-create reverse (backref)
        class Comment(Table):
            post_id: int
            post: Post = belongs_to(Post, backref="comments")
    
    Returns:
        BelongsTo descriptor
    """
    return BelongsTo(
        rel_name="",  # Will be set by metaclass
        model=model,
        foreign_key=foreign_key or "",
        backref=backref,
        back_populates=back_populates,
    )


def has_many(
    model: Union[Type[T], str],
    foreign_key: Optional[str] = None,
    backref: Optional[str] = None,
    back_populates: Optional[str] = None,
) -> HasMany[T]:
    """
    Define a has_many relationship explicitly.
    
    Usually auto-detected, but use this for:
    - Custom foreign keys
    - Bidirectional sync with backref/back_populates
    
    Args:
        model: Related model class or string name
        foreign_key: FK field name on related model
        backref: Name for auto-created reverse belongs_to relationship
        back_populates: Name of existing reverse relationship to sync
    
    Examples:
        # Simple explicit definition
        class User(Table):
            posts: List[Post] = has_many(Post, "author_id")
        
        # With auto-created backref (most common)
        class User(Table):
            posts: List[Post] = has_many(Post, backref="author")
            # Automatically creates Post.author as BelongsTo
        
        # With explicit bidirectional (both sides defined)
        class User(Table):
            posts: List[Post] = has_many(Post, back_populates="author")
        
        class Post(Table):
            author_id: int
            author: User = belongs_to(User, back_populates="posts")
    
    Returns:
        HasMany descriptor
    """
    return HasMany(
        rel_name="",  # Will be set by metaclass
        model=model,
        foreign_key=foreign_key or "",
        backref=backref,
        back_populates=back_populates,
    )


def has_one(
    model: Union[Type[T], str],
    foreign_key: Optional[str] = None,
    backref: Optional[str] = None,
    back_populates: Optional[str] = None,
) -> HasOne[T]:
    """
    Define a has_one relationship explicitly.
    
    Args:
        model: Related model class or string name
        foreign_key: FK field name on related model
        backref: Name for auto-created reverse belongs_to relationship
        back_populates: Name of existing reverse relationship to sync
    
    Examples:
        # Simple explicit definition
        class User(Table):
            profile: Profile = has_one(Profile, "user_id")
        
        # With auto-created backref
        class User(Table):
            profile: Profile = has_one(Profile, backref="user")
            # Automatically creates Profile.user as BelongsTo
    
    Returns:
        HasOne descriptor
    """
    return HasOne(
        rel_name="",  # Will be set by metaclass
        model=model,
        foreign_key=foreign_key or "",
        backref=backref,
        back_populates=back_populates,
    )


# =============================================================================
# Relationship Setup Functions
# =============================================================================

def setup_relationships(model: Type["Table"], registry: Dict[str, Type["Table"]]) -> None:
    """
    Set up all relationships for a model.
    
    Called after all models are registered.
    
    This function:
    1. Detects belongs_to from *_id fields
    2. Detects has_many from other models' FKs
    3. Creates descriptors for detected relationships
    4. Does NOT process backrefs (that's done by process_backrefs)
    
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
    
    # Create descriptors for belongs_to (if not already defined)
    for name, rel in belongs_to_rels.items():
        if not hasattr(model, name):
            descriptor = BelongsTo(name, rel.model, rel.foreign_key)
            setattr(model, name, descriptor)
    
    # Create descriptors for has_many (if not already defined)
    for name, rel in has_many_rels.items():
        if not hasattr(model, name):
            descriptor = HasMany(name, rel.model, rel.foreign_key)
            setattr(model, name, descriptor)


def process_backrefs(model: Type["Table"], registry: Dict[str, Type["Table"]]) -> None:
    """
    Process backref definitions on a model.
    
    For each relationship with `backref` set:
    1. Creates the reverse relationship on the target model
    2. Registers the bidirectional pair in BackrefRegistry
    
    For each relationship with `back_populates` set:
    1. Registers the bidirectional pair in BackrefRegistry
    
    Args:
        model: The model class
        registry: Registry of all model classes
    """
    from pynext.db.relationships.backref import (
        BackrefConfig,
        get_backref_registry,
    )
    
    backref_registry = get_backref_registry()
    
    # Scan class attributes for relationship descriptors
    for attr_name in dir(model):
        if attr_name.startswith("_"):
            continue
        
        try:
            attr = getattr(model, attr_name, None)
        except Exception:
            continue
        
        if not isinstance(attr, (BelongsTo, HasMany, HasOne)):
            continue
        
        # Process backref (auto-create reverse relationship)
        if attr.backref:
            _create_backref(model, attr_name, attr, registry, backref_registry)
        
        # Process back_populates (register bidirectional pair)
        if attr.back_populates:
            _register_back_populates(model, attr_name, attr, registry, backref_registry)


def _create_backref(
    source_model: Type["Table"],
    source_attr: str,
    descriptor: Union[BelongsTo, HasMany, HasOne],
    registry: Dict[str, Type["Table"]],
    backref_registry: "BackrefRegistry",
) -> None:
    """
    Create a reverse relationship from a backref definition.
    
    Args:
        source_model: The model that defines the backref
        source_attr: The attribute name on source model
        descriptor: The relationship descriptor
        registry: Model registry
        backref_registry: Backref registry
    """
    from pynext.db.relationships.backref import BackrefConfig
    
    # Get target model
    target_model = descriptor.model
    if isinstance(target_model, str):
        # Try to resolve from registry
        target_model = registry.get(target_model)
        if target_model is None:
            # Defer to later
            backref_registry.add_pending(
                descriptor._model,  # target table name
                BackrefConfig(
                    name=descriptor.backref,
                    source_model=source_model,
                    source_attr=source_attr,
                    target_model=descriptor._model,
                    target_attr=descriptor.backref,
                    foreign_key=descriptor.foreign_key,
                )
            )
            return
    
    # Determine what kind of reverse to create
    target_attr = descriptor.backref
    
    if isinstance(descriptor, HasMany):
        # has_many.backref creates belongs_to on target
        if not hasattr(target_model, target_attr):
            # Create belongs_to on target
            reverse_descriptor = BelongsTo(
                rel_name=target_attr,
                model=source_model,
                foreign_key=descriptor.foreign_key,
                back_populates=source_attr,
            )
            setattr(target_model, target_attr, reverse_descriptor)
            
            # Update target's relationships dict
            if hasattr(target_model, "_relationships"):
                target_model._relationships[target_attr] = {
                    "name": target_attr,
                    "type": RelationshipType.BELONGS_TO,
                    "model": source_model,
                    "foreign_key": descriptor.foreign_key,
                    "back_populates": source_attr,
                }
    
    elif isinstance(descriptor, HasOne):
        # has_one.backref creates belongs_to on target
        if not hasattr(target_model, target_attr):
            reverse_descriptor = BelongsTo(
                rel_name=target_attr,
                model=source_model,
                foreign_key=descriptor.foreign_key,
                back_populates=source_attr,
            )
            setattr(target_model, target_attr, reverse_descriptor)
            
            if hasattr(target_model, "_relationships"):
                target_model._relationships[target_attr] = {
                    "name": target_attr,
                    "type": RelationshipType.BELONGS_TO,
                    "model": source_model,
                    "foreign_key": descriptor.foreign_key,
                    "back_populates": source_attr,
                }
    
    elif isinstance(descriptor, BelongsTo):
        # belongs_to.backref creates has_many on target
        if not hasattr(target_model, target_attr):
            reverse_descriptor = HasMany(
                rel_name=target_attr,
                model=source_model,
                foreign_key=descriptor.foreign_key,
                back_populates=source_attr,
            )
            setattr(target_model, target_attr, reverse_descriptor)
            
            if hasattr(target_model, "_relationships"):
                target_model._relationships[target_attr] = {
                    "name": target_attr,
                    "type": RelationshipType.HAS_MANY,
                    "model": source_model,
                    "foreign_key": descriptor.foreign_key,
                    "back_populates": source_attr,
                }
    
    # Update source descriptor to know its back_populates
    descriptor.back_populates = target_attr
    
    # Register in backref registry
    source_table = source_model.__table_name__
    target_table = target_model.__table_name__
    
    config = BackrefConfig(
        name=target_attr,
        source_model=source_model,
        source_attr=source_attr,
        target_model=target_model,
        target_attr=target_attr,
        foreign_key=descriptor.foreign_key,
    )
    backref_registry.register(config)


def _register_back_populates(
    source_model: Type["Table"],
    source_attr: str,
    descriptor: Union[BelongsTo, HasMany, HasOne],
    registry: Dict[str, Type["Table"]],
    backref_registry: "BackrefRegistry",
) -> None:
    """
    Register a back_populates relationship pair.
    
    Unlike backref, back_populates assumes both sides are explicitly defined.
    We just register them in the registry so sync knows about them.
    
    Args:
        source_model: The model with back_populates
        source_attr: The attribute name
        descriptor: The relationship descriptor
        registry: Model registry
        backref_registry: Backref registry
    """
    from pynext.db.relationships.backref import BackrefConfig
    
    # Get target model
    target_model = descriptor.model
    if isinstance(target_model, str):
        target_model = registry.get(target_model)
        if target_model is None:
            # Defer registration
            return
    
    target_attr = descriptor.back_populates
    
    # Check if already registered
    if backref_registry.has_backref(source_model, source_attr):
        return
    
    # Register the pair
    config = BackrefConfig(
        name=target_attr,
        source_model=source_model,
        source_attr=source_attr,
        target_model=target_model,
        target_attr=target_attr,
        foreign_key=descriptor.foreign_key,
    )
    backref_registry.register(config)
