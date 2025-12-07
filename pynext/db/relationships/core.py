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
    from pynext.db.relationships.cascade import CascadeOptions

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
        is_self_referential: True if model references itself (tree structure)
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
        is_self_referential: bool = False,
    ):
        self.name = name
        self.type = rel_type
        self.model = model
        self.foreign_key = foreign_key
        self.through = through
        self.backref = backref
        self.back_populates = back_populates
        self.is_self_referential = is_self_referential
    
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
        `parent_id: int` on Category -> self-referential belongs_to
    
    Self-Referential Detection:
        When a field like `parent_id` exists and the model name matches
        common self-referential patterns (parent, category, etc.), we
        detect it as a self-referential relationship.
    
    Args:
        model: The model class
        fields: Field definitions
        registry: Registry of all model classes by table name
    
    Returns:
        Dict of relationship name -> RelationshipInfo
    """
    relationships: Dict[str, RelationshipInfo] = {}
    model_table_name = getattr(model, '__table_name__', model.__name__.lower() + 's')
    
    for name, field in fields.items():
        # Check for *_id pattern
        if name.endswith("_id"):
            # author_id -> author
            rel_name = name[:-3]
            
            # author -> authors (table name)
            table_name = rel_name + "s"
            
            # Check for self-referential relationship
            is_self_ref = _is_self_referential_field(name, model, model_table_name)
            
            if is_self_ref:
                # Self-referential: parent_id on Category -> Category
                relationships[rel_name] = RelationshipInfo(
                    name=rel_name,
                    rel_type=RelationshipType.BELONGS_TO,
                    model=model,  # References self
                    foreign_key=name,
                    is_self_referential=True,
                )
            else:
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


def _is_self_referential_field(
    field_name: str,
    model: Type["Table"],
    model_table_name: str,
) -> bool:
    """
    Detect if a field represents a self-referential relationship.
    
    Common patterns:
        - parent_id on any model (tree hierarchy)
        - category_id on Category model
        - comment_id on Comment model (replies)
        - node_id on Node model
    
    Args:
        field_name: The field name (e.g., "parent_id")
        model: The model class
        model_table_name: The model's table name
    
    Returns:
        True if this is a self-referential field
    """
    # Common self-ref field names that always indicate tree hierarchy
    self_ref_patterns = {'parent_id', 'parent', 'reply_to_id', 'reports_to_id'}
    
    if field_name in self_ref_patterns:
        return True
    
    # Check if field references the same model
    # e.g., category_id on Category, comment_id on Comment
    rel_name = field_name[:-3] if field_name.endswith("_id") else field_name
    expected_table = rel_name + "s"
    
    # Check various model name formats
    model_name_lower = model.__name__.lower()
    
    # category_id on Category -> categories == categories
    if expected_table == model_table_name:
        return True
    
    # category_id on Category -> category == category
    if rel_name == model_name_lower:
        return True
    
    return False


def detect_reverse_relationships(
    model: Type["Table"],
    registry: Dict[str, Type["Table"]],
) -> Dict[str, RelationshipInfo]:
    """
    Auto-detect reverse relationships (has_many, has_one).
    
    For each model that has a FK to this model, create a reverse relationship.
    Also detects self-referential reverse (children for parent_id).
    
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
    
    # Check for self-referential (children relationship)
    model_fields = getattr(model, "_fields", {})
    if "parent_id" in model_fields:
        # This model has parent_id -> add "children" relationship
        relationships["children"] = RelationshipInfo(
            name="children",
            rel_type=RelationshipType.HAS_MANY,
            model=model,  # References self
            foreign_key="parent_id",
            is_self_referential=True,
        )
    
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
            
            # With loading strategy:
            author: User = belongs_to(User, lazy="joined")  # Eager load with JOIN
            
            # With filter (only active authors):
            active_author: User = belongs_to(User, filter=[eq("is_active", True)])
    
    When `back_populates` or `backref` is set:
        post.author = user  # Also adds post to user.posts
        post.author = None  # Also removes post from old user.posts
    
    Loading strategies:
        select   - Lazy load on access (default)
        joined   - LEFT JOIN in same query
        raise    - Raise error on access (N+1 prevention)
    
    Filter syntax:
        filter=[eq("field", value)]        # Condition functions
        filter=[("field", "=", value)]     # Tuple syntax
    """
    
    def __init__(
        self,
        rel_name: str,
        model: Union[Type[T], str],
        foreign_key: str,
        backref: Optional[str] = None,
        back_populates: Optional[str] = None,
        lazy: str = "select",
        filter: Optional[List] = None,
    ):
        """
        Initialize BelongsTo descriptor.
        
        Args:
            rel_name: Name of this relationship (e.g., "author")
            model: Related model class or string name
            foreign_key: FK field name (e.g., "author_id")
            backref: Name for auto-created reverse relationship
            back_populates: Name of existing reverse relationship to sync
            lazy: Loading strategy (select, joined, raise)
            filter: List of filter conditions (Condition objects or tuples)
        
        Filter Examples:
            filter=[eq("is_active", True)]
            filter=[("is_active", "=", True)]
        """
        self.rel_name = rel_name
        self._model = model
        self.foreign_key = foreign_key
        self.backref = backref
        self.back_populates = back_populates
        self.lazy = lazy
        self._cache_attr = f"_cached_{rel_name}"
        
        # Parse filter conditions (Phase 7.5)
        self._filter_input = filter
        self._filter = None  # Lazy parsed
    
    @property
    def model(self) -> Type[T]:
        """Get the related model (resolving lazy string if needed)."""
        if isinstance(self._model, str):
            from pynext.db.table import _model_registry
            self._model = _model_registry.get(self._model)
        return self._model
    
    @property
    def filter(self):
        """Get the parsed filter (lazy initialization)."""
        if self._filter is None and self._filter_input is not None:
            from pynext.db.relationships.filter import parse_filter
            self._filter = parse_filter(self._filter_input)
        return self._filter
    
    def __get__(self, obj: Optional["Table"], objtype: Type["Table"] = None) -> Optional[T]:
        """Get the related model instance (cached)."""
        if obj is None:
            return self
        
        # Check if marked to raise on access
        if getattr(obj, f"_raise_on_{self.rel_name}", False):
            from pynext.db.relationships.loading import LazyLoadError
            raise LazyLoadError(
                self.rel_name,
                model=type(obj).__name__,
            )
        
        # Check if lazy="raise" at descriptor level
        if self.lazy == "raise":
            # Only raise if not already loaded
            cached = getattr(obj, self._cache_attr, None)
            if cached is None:
                from pynext.db.relationships.loading import LazyLoadError
                raise LazyLoadError(
                    self.rel_name,
                    model=type(obj).__name__,
                )
            return cached
        
        # Check cache
        cached = getattr(obj, self._cache_attr, None)
        if cached is not None:
            return cached
        
        # Return None - actual loading happens in query.with_related() or options()
        return None
    
    def __set__(self, obj: "Table", value: Optional[T]) -> None:
        """
        Set the related model instance.
        
        If backref/back_populates is configured, also updates the reverse side:
        - Removes obj from old_value's collection
        - Adds obj to new_value's collection
        
        Fires on_set hooks.
        """
        from pynext.db.relationships.hook_executor import fire_on_set
        
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
        
        # Fire on_set hooks
        fire_on_set(obj, self.rel_name, old_value, value)


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
            
            # With loading strategy:
            posts: List[Post] = has_many(Post, lazy="selectin")  # Batch load
            audit_logs: List[Log] = has_many(Log, lazy="dynamic")  # Query builder
            
            # With filter (only load active posts):
            active_posts: List[Post] = has_many(Post, filter=[eq("is_active", True)])
    
    When `backref` is set:
        user.posts.append(post)  # Also sets post.author = user
        user.posts.remove(post)  # Also sets post.author = None
    
    Loading strategies:
        select   - Lazy load on access (default)
        selectin - SELECT WHERE id IN (...) - best for batches
        subquery - Subquery for IN clause
        raise    - Raise error on access (N+1 prevention)
        dynamic  - Return query builder instead of results
    
    Filter syntax:
        filter=[eq("field", value)]        # Condition functions
        filter=[("field", "=", value)]     # Tuple syntax
    """
    
    def __init__(
        self,
        rel_name: str,
        model: Union[Type[T], str],
        foreign_key: str,
        backref: Optional[str] = None,
        back_populates: Optional[str] = None,
        lazy: str = "select",
        on_delete: str = "none",
        cascade: Optional["CascadeOptions"] = None,
        filter: Optional[List] = None,
        order_by: Optional[Union[str, List[str]]] = None,
    ):
        """
        Initialize HasMany descriptor.
        
        Args:
            rel_name: Name of this relationship (e.g., "posts")
            model: Related model class or string name
            foreign_key: FK field name on related model (e.g., "author_id")
            backref: Name for auto-created reverse belongs_to
            back_populates: Name of existing reverse relationship to sync
            lazy: Loading strategy (select, selectin, subquery, raise, dynamic)
            on_delete: Simple cascade preset ("cascade", "nullify", "protect", "none")
            cascade: Fine-grained CascadeOptions for advanced control
            filter: List of filter conditions (Condition objects or tuples)
            order_by: Default ordering (string or list of strings)
        
        Cascade Options:
            on_delete="cascade"  - Delete related when parent deleted
            on_delete="nullify"  - Set FK to NULL when parent deleted
            on_delete="protect"  - Raise error if trying to delete with related
            on_delete="none"     - Do nothing (default, let DB handle it)
        
        Filter Examples:
            filter=[eq("is_active", True)]
            filter=[("is_active", "=", True), ("views", ">=", 100)]
        
        Order By Examples:
            order_by="created_at desc"
            order_by=["pinned desc", "created_at desc"]
        """
        self.rel_name = rel_name
        self._model = model
        self.foreign_key = foreign_key
        self.backref = backref
        self.back_populates = back_populates
        self.lazy = lazy
        self.on_delete = on_delete
        self.cascade = cascade
        self._cache_attr = f"_cached_{rel_name}"
        
        # Parse filter conditions (Phase 7.5)
        self._filter_input = filter
        self._filter = None  # Lazy parsed
        
        # Parse ordering (Phase 7.10)
        self._order_by_input = order_by
        self._ordering = None  # Lazy parsed
    
    @property
    def model(self) -> Type[T]:
        """Get the related model (resolving lazy string if needed)."""
        if isinstance(self._model, str):
            from pynext.db.table import _model_registry
            self._model = _model_registry.get(self._model)
        return self._model
    
    @property
    def filter(self):
        """Get the parsed filter (lazy initialization)."""
        if self._filter is None and self._filter_input is not None:
            from pynext.db.relationships.filter import parse_filter
            self._filter = parse_filter(self._filter_input)
        return self._filter
    
    @property
    def ordering(self):
        """Get the parsed ordering config (lazy initialization)."""
        if self._ordering is None and self._order_by_input is not None:
            from pynext.db.relationships.ordering import OrderingConfig
            self._ordering = OrderingConfig.from_order_by(self._order_by_input)
        return self._ordering
    
    @property
    def order_by(self):
        """Get raw order_by value for compatibility."""
        return self._order_by_input
    
    def __get__(self, obj: Optional["Table"], objtype: Type["Table"] = None) -> List[T]:
        """
        Get the related model instances.
        
        Returns a SyncedList if backref is enabled, for automatic sync.
        Returns cached value if already loaded.
        Returns DynamicRelationship if lazy="dynamic".
        Returns empty list/SyncedList otherwise.
        """
        if obj is None:
            return self
        
        # Check if marked to raise on access
        if getattr(obj, f"_raise_on_{self.rel_name}", False):
            from pynext.db.relationships.loading import LazyLoadError
            raise LazyLoadError(
                self.rel_name,
                model=type(obj).__name__,
            )
        
        # Handle lazy="raise" at descriptor level
        if self.lazy == "raise":
            cached = getattr(obj, self._cache_attr, None)
            if cached is None:
                from pynext.db.relationships.loading import LazyLoadError
                raise LazyLoadError(
                    self.rel_name,
                    model=type(obj).__name__,
                )
            return cached
        
        # Handle lazy="dynamic" - return query builder with filter applied
        if self.lazy == "dynamic":
            from pynext.db.relationships.dynamic import DynamicRelationship
            model = self.model
            if model is None:
                raise RuntimeError(
                    f"Could not resolve model for dynamic relationship '{self.rel_name}'"
                )
            return DynamicRelationship(
                owner=obj,
                model=model,
                fk_field=self.foreign_key,
                rel_name=self.rel_name,
                filter=self.filter,  # Pass filter to dynamic relationship
            )
        
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
            
            # With loading strategy:
            profile: Profile = has_one(Profile, lazy="joined")  # Eager with JOIN
            
            # With filter (only active profile):
            active_profile: Profile = has_one(Profile, filter=[eq("is_active", True)])
    
    When `backref` is set:
        user.profile = profile  # Also sets profile.user = user
        user.profile = None     # Also sets old profile.user = None
    
    Loading strategies:
        select   - Lazy load on access (default)
        joined   - LEFT JOIN in same query
        selectin - SELECT WHERE id IN (...)
        raise    - Raise error on access (N+1 prevention)
    
    Filter syntax:
        filter=[eq("field", value)]        # Condition functions
        filter=[("field", "=", value)]     # Tuple syntax
    """
    
    def __init__(
        self,
        rel_name: str,
        model: Union[Type[T], str],
        foreign_key: str,
        backref: Optional[str] = None,
        back_populates: Optional[str] = None,
        lazy: str = "select",
        on_delete: str = "none",
        cascade: Optional["CascadeOptions"] = None,
        filter: Optional[List] = None,
    ):
        """
        Initialize HasOne descriptor.
        
        Args:
            rel_name: Name of this relationship (e.g., "profile")
            model: Related model class or string name
            foreign_key: FK field name on related model (e.g., "user_id")
            backref: Name for auto-created reverse belongs_to
            back_populates: Name of existing reverse relationship to sync
            lazy: Loading strategy (select, joined, selectin, raise)
            on_delete: Simple cascade preset ("cascade", "nullify", "protect", "none")
            cascade: Fine-grained CascadeOptions for advanced control
            filter: List of filter conditions (Condition objects or tuples)
        
        Filter Examples:
            filter=[eq("is_active", True)]
            filter=[("is_active", "=", True)]
        """
        self.rel_name = rel_name
        self._model = model
        self.foreign_key = foreign_key
        self.backref = backref
        self.back_populates = back_populates
        self.lazy = lazy
        self.on_delete = on_delete
        self.cascade = cascade
        self._cache_attr = f"_cached_{rel_name}"
        
        # Parse filter conditions (Phase 7.5)
        self._filter_input = filter
        self._filter = None  # Lazy parsed
    
    @property
    def model(self) -> Type[T]:
        """Get the related model (resolving lazy string if needed)."""
        if isinstance(self._model, str):
            from pynext.db.table import _model_registry
            self._model = _model_registry.get(self._model)
        return self._model
    
    @property
    def filter(self):
        """Get the parsed filter (lazy initialization)."""
        if self._filter is None and self._filter_input is not None:
            from pynext.db.relationships.filter import parse_filter
            self._filter = parse_filter(self._filter_input)
        return self._filter
    
    def __get__(self, obj: Optional["Table"], objtype: Type["Table"] = None) -> Optional[T]:
        """Get the related model instance (cached)."""
        if obj is None:
            return self
        
        # Check if marked to raise on access
        if getattr(obj, f"_raise_on_{self.rel_name}", False):
            from pynext.db.relationships.loading import LazyLoadError
            raise LazyLoadError(
                self.rel_name,
                model=type(obj).__name__,
            )
        
        # Handle lazy="raise" at descriptor level
        if self.lazy == "raise":
            cached = getattr(obj, self._cache_attr, None)
            if cached is None:
                from pynext.db.relationships.loading import LazyLoadError
                raise LazyLoadError(
                    self.rel_name,
                    model=type(obj).__name__,
                )
            return cached
        
        # Check cache
        cached = getattr(obj, self._cache_attr, None)
        if cached is not None:
            return cached
        
        # Return None - actual loading happens in query.with_related() or options()
        return None
    
    def __set__(self, obj: "Table", value: Optional[T]) -> None:
        """
        Set the related model instance.
        
        If backref/back_populates is configured, also updates the reverse side.
        Fires on_set hooks.
        """
        from pynext.db.relationships.hook_executor import fire_on_set
        
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
        
        # Fire on_set hooks
        fire_on_set(obj, self.rel_name, old_value, value)


# =============================================================================
# Convenience Functions for Explicit Relationship Definition
# =============================================================================

def belongs_to(
    model: Union[Type[T], str],
    foreign_key: Optional[str] = None,
    backref: Optional[str] = None,
    back_populates: Optional[str] = None,
    lazy: str = "select",
    filter: Optional[List] = None,
) -> BelongsTo[T]:
    """
    Define a belongs_to relationship explicitly.
    
    Usually auto-detected from `*_id` fields, but use this for:
    - Custom foreign keys
    - Bidirectional sync with backref/back_populates
    - Custom loading strategy
    - Filtered relationships
    
    Args:
        model: Related model class or string name
        foreign_key: FK field name (auto-detected if not provided)
        backref: Name for auto-created reverse has_many relationship
        back_populates: Name of existing reverse relationship to sync
        lazy: Loading strategy (select, joined, raise). Default: "select"
        filter: List of conditions to filter related records
    
    Loading Strategies:
        select  - Lazy load on access (default, may cause N+1)
        joined  - LEFT JOIN in same query (eager, single query)
        raise   - Raise error on access (prevents N+1)
    
    Filter Syntax:
        filter=[eq("is_active", True)]           # Condition functions
        filter=[("is_active", "=", True)]        # Tuple syntax
    
    Examples:
        # Simple explicit definition
        class Post(Table):
            author_id: int
            author: User = belongs_to(User, "author_id")
        
        # With eager loading (always JOIN)
        class Post(Table):
            author_id: int
            author: User = belongs_to(User, lazy="joined")
        
        # With filter (only active authors)
        class Post(Table):
            author_id: int
            active_author: User = belongs_to(User, filter=[eq("is_active", True)])
        
        # Prevent N+1 - must use options() to load
        class Post(Table):
            author_id: int
            author: User = belongs_to(User, lazy="raise")
        
        # With bidirectional sync
        class Post(Table):
            author_id: int
            author: User = belongs_to(User, backref="posts")
    
    Returns:
        BelongsTo descriptor
    """
    return BelongsTo(
        rel_name="",  # Will be set by metaclass
        model=model,
        foreign_key=foreign_key or "",
        backref=backref,
        back_populates=back_populates,
        lazy=lazy,
        filter=filter,
    )


def has_many(
    model: Union[Type[T], str],
    foreign_key: Optional[str] = None,
    backref: Optional[str] = None,
    back_populates: Optional[str] = None,
    lazy: str = "select",
    on_delete: str = "none",
    cascade: Optional["CascadeOptions"] = None,
    filter: Optional[List] = None,
    order_by: Optional[Union[str, List[str]]] = None,
) -> HasMany[T]:
    """
    Define a has_many relationship explicitly.
    
    Usually auto-detected, but use this for:
    - Custom foreign keys
    - Bidirectional sync with backref/back_populates
    - Custom loading strategy
    - Cascade behavior
    - Filtered relationships
    - Default ordering
    
    Args:
        model: Related model class or string name
        foreign_key: FK field name on related model
        backref: Name for auto-created reverse belongs_to relationship
        back_populates: Name of existing reverse relationship to sync
        lazy: Loading strategy (select, selectin, subquery, raise, dynamic)
        on_delete: Simple cascade preset for deletion behavior
        cascade: Fine-grained CascadeOptions for advanced control
        filter: List of conditions to filter related records
        order_by: Default ordering (e.g., "created_at desc" or ["pinned desc", "name"])
    
    Loading Strategies:
        select   - Lazy load on access (default, may cause N+1)
        selectin - SELECT WHERE id IN (...) - best for batches
        subquery - Subquery for IN clause - good for deep nesting
        raise    - Raise error on access (prevents N+1)
        dynamic  - Return query builder instead of loading
    
    Cascade Options (on_delete):
        "cascade" - Delete all related when parent deleted
        "nullify" - Set FK to NULL when parent deleted
        "protect" - Raise error if trying to delete with related
        "none"    - Do nothing (default, let DB handle it)
    
    Filter Syntax:
        filter=[eq("is_active", True)]           # Condition functions
        filter=[("is_active", "=", True)]        # Tuple syntax
    
    Order By Syntax:
        order_by="created_at desc"               # Single column, descending
        order_by="name"                          # Single column, ascending (default)
        order_by=["pinned desc", "created_at"]   # Multiple columns
        order_by="due_date nulls last"           # With NULLS handling
    
    Examples:
        # Simple explicit definition
        class User(Table):
            posts: List[Post] = has_many(Post, "author_id")
        
        # With batch loading (most common for has_many)
        class User(Table):
            posts: List[Post] = has_many(Post, lazy="selectin")
        
        # With ordering - latest posts first
        class User(Table):
            posts: List[Post] = has_many(Post, order_by="created_at desc")
        
        # Multiple order columns
        class User(Table):
            comments: List[Comment] = has_many(
                Comment,
                order_by=["pinned desc", "created_at desc"]
            )
        
        # With cascade delete
        class User(Table):
            posts: List[Post] = has_many(Post, on_delete="cascade")
            # user.delete() will also delete all posts
        
        # Protect from deletion
        class User(Table):
            orders: List[Order] = has_many(Order, on_delete="protect")
            # user.delete() raises error if user has orders
        
        # Fine-grained control
        class User(Table):
            logs: List[Log] = has_many(Log, cascade=CascadeOptions(
                on_save=True,    # Save logs when user saved
                on_delete=True,  # Delete logs when user deleted
                on_orphan=True,  # Delete log when removed from collection
            ))
        
        # With bidirectional sync
        class User(Table):
            posts: List[Post] = has_many(Post, backref="author")
    
    Returns:
        HasMany descriptor
    """
    return HasMany(
        rel_name="",  # Will be set by metaclass
        model=model,
        foreign_key=foreign_key or "",
        backref=backref,
        back_populates=back_populates,
        lazy=lazy,
        on_delete=on_delete,
        cascade=cascade,
        filter=filter,
        order_by=order_by,
    )


def has_one(
    model: Union[Type[T], str],
    foreign_key: Optional[str] = None,
    backref: Optional[str] = None,
    back_populates: Optional[str] = None,
    lazy: str = "select",
    on_delete: str = "none",
    cascade: Optional["CascadeOptions"] = None,
    filter: Optional[List] = None,
) -> HasOne[T]:
    """
    Define a has_one relationship explicitly.
    
    Args:
        model: Related model class or string name
        foreign_key: FK field name on related model
        backref: Name for auto-created reverse belongs_to relationship
        back_populates: Name of existing reverse relationship to sync
        lazy: Loading strategy (select, joined, selectin, raise)
        on_delete: Simple cascade preset for deletion behavior
        cascade: Fine-grained CascadeOptions for advanced control
        filter: List of conditions to filter related records
    
    Loading Strategies:
        select   - Lazy load on access (default, may cause N+1)
        joined   - LEFT JOIN in same query - best for has_one
        selectin - SELECT WHERE id IN (...) - good for batches
        raise    - Raise error on access (prevents N+1)
    
    Cascade Options (on_delete):
        "cascade" - Delete related when parent deleted
        "nullify" - Set FK to NULL when parent deleted  
        "protect" - Raise error if related exists
        "none"    - Do nothing (default, let DB handle it)
    
    Filter Syntax:
        filter=[eq("is_active", True)]           # Condition functions
        filter=[("is_active", "=", True)]        # Tuple syntax
    
    Examples:
        # Simple explicit definition
        class User(Table):
            profile: Profile = has_one(Profile, "user_id")
        
        # With eager loading (recommended for has_one)
        class User(Table):
            profile: Profile = has_one(Profile, lazy="joined")
        
        # With filter (only active profile)
        class User(Table):
            active_profile: Profile = has_one(Profile, filter=[eq("is_active", True)])
        
        # With cascade delete
        class User(Table):
            profile: Profile = has_one(Profile, on_delete="cascade")
            # user.delete() will also delete the profile
        
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
        lazy=lazy,
        on_delete=on_delete,
        cascade=cascade,
        filter=filter,
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
    
    # Get target model - use _model to avoid property resolution issues
    model_ref = descriptor._model
    
    if isinstance(model_ref, str):
        model_name = model_ref
        target_model = None
        
        # Try to resolve from registry by table name
        target_model = registry.get(model_name)
        
        # Also try lowercase + 's' (class name to table name convention)
        if target_model is None:
            table_name = model_name.lower() + "s"
            target_model = registry.get(table_name)
        
        # Also try exact match by iterating (in case of non-standard names)
        if target_model is None:
            for tbl_name, model_cls in registry.items():
                if model_cls.__name__ == model_name:
                    target_model = model_cls
                    break
        
        if target_model is None:
            # Defer to later - use both class name and expected table name
            pending_key = model_name.lower() + "s"  # Use table name convention
            backref_registry.add_pending(
                pending_key,
                BackrefConfig(
                    name=descriptor.backref,
                    source_model=source_model,
                    source_attr=source_attr,
                    target_model=model_name,
                    target_attr=descriptor.backref,
                    foreign_key=descriptor.foreign_key,
                )
            )
            return
    else:
        # model_ref is already a class
        target_model = model_ref
    
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
    
    # Get target model - use _model to avoid property resolution issues
    model_ref = descriptor._model
    
    if isinstance(model_ref, str):
        model_name = model_ref
        target_model = None
        
        # Try to resolve from registry by table name
        target_model = registry.get(model_name)
        
        # Also try lowercase + 's' (class name to table name convention)
        if target_model is None:
            table_name = model_name.lower() + "s"
            target_model = registry.get(table_name)
        
        # Also try exact match by iterating
        if target_model is None:
            for tbl_name, model_cls in registry.items():
                if model_cls.__name__ == model_name:
                    target_model = model_cls
                    break
        
        if target_model is None:
            # Defer registration until target model is defined
            return
    else:
        target_model = model_ref
    
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


# =============================================================================
# Many-to-Many Relationship
# =============================================================================

class ManyToMany(Generic[T]):
    """
    Descriptor for many-to-many relationships.
    
    The simplest way to define M2M relationships. Automatically handles:
    - Junction table creation (or uses explicit through=)
    - Bidirectional sync with backref
    - Loading strategies (select, selectin, subquery, raise, dynamic)
    - Extra column support on junction table
    
    SQLAlchemy Comparison:
        SQLAlchemy (verbose - 15+ lines):
            association_table = Table('students_courses', Base.metadata,
                Column('student_id', Integer, ForeignKey('students.id')),
                Column('course_id', Integer, ForeignKey('courses.id'))
            )
            class Student(Base):
                __tablename__ = 'students'
                courses = relationship('Course', secondary=association_table,
                                      back_populates='students')
            class Course(Base):
                __tablename__ = 'courses'
                students = relationship('Student', secondary=association_table,
                                       back_populates='courses')
        
        PyNext (simple - 2 lines):
            class Student(Table):
                courses: List[Course] = many_to_many(Course, backref="students")
            # That's it! Junction table auto-created, both sides sync!
    
    Usage:
        # Simple - auto-create junction table
        class Student(Table):
            courses: List[Course] = many_to_many(Course, backref="students")
        
        # With explicit junction table (for extra columns)
        class Enrollment(Table):
            student_id: int
            course_id: int
            grade: str
            enrolled_at: datetime
        
        class Student(Table):
            courses: List[Course] = many_to_many(
                Course, 
                through=Enrollment, 
                backref="students"
            )
        
        # Usage
        student.courses.append(course)           # Auto-creates junction row
        student.courses.add(course, grade="A")   # With extra data
        student.courses.remove(course)           # Deletes junction row
        course.students                          # Access from other side
    
    Loading strategies:
        select   - Lazy load on access (default)
        selectin - SELECT WHERE id IN (...) - best for batches
        subquery - Subquery for IN clause
        raise    - Raise error on access (N+1 prevention)
        dynamic  - Return query builder
    """
    
    def __init__(
        self,
        rel_name: str,
        model: Union[Type[T], str],
        through: Optional[Union[Type["Table"], str]] = None,
        backref: Optional[Union[str, bool]] = None,
        back_populates: Optional[str] = None,
        lazy: str = "select",
        extra: Optional[Dict[str, Any]] = None,
        on_delete: str = "none",
        cascade: Optional["CascadeOptions"] = None,
        filter: Optional[List] = None,
        order_by: Optional[Union[str, List[str]]] = None,
    ):
        """
        Initialize ManyToMany descriptor.
        
        Args:
            rel_name: Name of this relationship (e.g., "courses")
            model: Related model class or string name
            through: Junction table model (auto-created if None)
            backref: Name for auto-created reverse relationship.
                     - None: Auto-generate from owner class name (e.g., Student → "students")
                     - str: Use provided name
                     - False: Explicitly disable backref (no reverse relationship)
            back_populates: Name of existing reverse relationship to sync
            lazy: Loading strategy (select, selectin, subquery, raise, dynamic)
            extra: Extra columns for the junction table (alternative to through=)
                   e.g., {"grade": Optional[str], "enrolled_at": datetime}
            on_delete: Simple cascade preset ("cascade", "nullify", "none")
                       For M2M, "cascade" deletes junction rows, "nullify" is same as "none"
            cascade: Fine-grained CascadeOptions for advanced control
            filter: List of filter conditions for related items
            order_by: Default ordering (e.g., "name" or ["position", "name desc"])
        
        Filter Examples:
            filter=[eq("is_active", True)]
            filter=[("is_active", "=", True)]
        """
        self.rel_name = rel_name
        self._model = model
        self.through = through
        self._backref_raw = backref  # Store raw value for auto-generation
        self.backref = backref if backref is not False else None
        self._backref_disabled = backref is False
        self.back_populates = back_populates
        self.lazy = lazy
        self.extra = extra or {}
        self.on_delete = on_delete
        self.cascade = cascade
        self._cache_attr = f"_cached_{rel_name}"
        self._config: Optional["JunctionConfig"] = None
        self._owner_class: Optional[Type["Table"]] = None
        self._auto_backref_generated = False
        
        # Parse filter conditions (Phase 7.5)
        self._filter_input = filter
        self._filter = None  # Lazy parsed
        
        # Parse ordering (Phase 7.10)
        self._order_by_input = order_by
        self._ordering = None  # Lazy parsed
    
    @property
    def model(self) -> Type[T]:
        """Get the related model (resolving lazy string if needed)."""
        if isinstance(self._model, str):
            from pynext.db.table import _model_registry
            resolved = _model_registry.get(self._model)
            if resolved is None:
                # Try lowercase + s convention
                table_name = self._model.lower() + "s"
                resolved = _model_registry.get(table_name)
            if resolved is not None:
                self._model = resolved
        return self._model
    
    @property
    def filter(self):
        """Get the parsed filter (lazy initialization)."""
        if self._filter is None and self._filter_input is not None:
            from pynext.db.relationships.filter import parse_filter
            self._filter = parse_filter(self._filter_input)
        return self._filter
    
    @property
    def ordering(self):
        """Get the parsed ordering config (lazy initialization)."""
        if self._ordering is None and self._order_by_input is not None:
            from pynext.db.relationships.ordering import OrderingConfig
            self._ordering = OrderingConfig.from_order_by(self._order_by_input)
        return self._ordering
    
    @property
    def order_by(self):
        """Get raw order_by value for compatibility."""
        return self._order_by_input
    
    def _get_junction_config(self, owner_class: Type["Table"]) -> "JunctionConfig":
        """Get or create junction configuration."""
        if self._config is not None:
            return self._config
        
        from pynext.db.relationships.junction import (
            create_junction_config,
            create_junction_with_extra,
        )
        
        # If extra columns defined, create inline junction table
        through_model = self.through
        if self.extra and not self.through:
            through_model = create_junction_with_extra(
                source_model=owner_class,
                target_model=self._model,
                extra_columns=self.extra,
            )
        
        self._config = create_junction_config(
            source_model=owner_class,
            target_model=self._model,
            through=through_model,
            source_attr=self.rel_name,
            target_attr=self.backref or self.back_populates or "",
        )
        return self._config
    
    def __set_name__(self, owner: Type["Table"], name: str) -> None:
        """Called when descriptor is assigned to class attribute."""
        self.rel_name = name
        self._cache_attr = f"_cached_{name}"
        self._owner_class = owner
        
        # Auto-generate backref if:
        # - backref was not explicitly provided (None)
        # - backref was not explicitly disabled (False)
        # - back_populates was not used (which means explicit linking)
        if (self._backref_raw is None 
            and not self._backref_disabled 
            and not self.back_populates):
            # Generate backref from owner class name: Student → "students"
            self.backref = self._pluralize(owner.__name__)
            self._auto_backref_generated = True
    
    @staticmethod
    def _pluralize(name: str) -> str:
        """
        Simple pluralization for auto-backref.
        
        Converts class names to plural lowercase:
        - Student → students
        - Person → persons (simple rule)
        - Category → categorys (simple rule, good enough for most cases)
        
        For complex pluralization, use explicit backref="people".
        """
        # Simple lowercase + 's' pluralization
        return name.lower() + "s"
    
    def __get__(
        self, 
        obj: Optional["Table"], 
        objtype: Type["Table"] = None,
    ) -> Union["ManyToMany[T]", "ManyToManyCollection[T]"]:
        """
        Get the M2M collection for an instance.
        
        Returns the descriptor itself when accessed on the class.
        Returns a ManyToManyCollection when accessed on an instance.
        """
        if obj is None:
            return self
        
        # Check if marked to raise on access
        if getattr(obj, f"_raise_on_{self.rel_name}", False):
            from pynext.db.relationships.loading import LazyLoadError
            raise LazyLoadError(
                self.rel_name,
                model=type(obj).__name__,
            )
        
        # Handle lazy="raise" at descriptor level
        if self.lazy == "raise":
            cached = getattr(obj, self._cache_attr, None)
            if cached is None:
                from pynext.db.relationships.loading import LazyLoadError
                raise LazyLoadError(
                    self.rel_name,
                    model=type(obj).__name__,
                )
            return cached
        
        # Handle lazy="dynamic" - return query builder
        if self.lazy == "dynamic":
            from pynext.db.relationships.m2m_dynamic import DynamicManyToMany
            config = self._get_junction_config(type(obj))
            return DynamicManyToMany(
                owner=obj,
                target_model=self.model,
                config=config,
            )
        
        # Check cache
        cached = getattr(obj, self._cache_attr, None)
        if cached is not None:
            return cached
        
        # Create collection
        from pynext.db.relationships.m2m_collection import ManyToManyCollection
        
        config = self._get_junction_config(type(obj))
        collection = ManyToManyCollection(
            owner=obj,
            attr_name=self.rel_name,
            config=config,
            items=None,
            reverse_attr=self.backref or self.back_populates,
        )
        
        setattr(obj, self._cache_attr, collection)
        return collection
    
    def __set__(
        self, 
        obj: "Table", 
        value: List[T],
    ) -> None:
        """
        Set the M2M collection.
        
        Replaces all items in the collection.
        """
        from pynext.db.relationships.m2m_collection import ManyToManyCollection
        
        config = self._get_junction_config(type(obj))
        
        if isinstance(value, ManyToManyCollection):
            setattr(obj, self._cache_attr, value)
        else:
            collection = ManyToManyCollection(
                owner=obj,
                attr_name=self.rel_name,
                config=config,
                items=value,
                reverse_attr=self.backref or self.back_populates,
            )
            setattr(obj, self._cache_attr, collection)


def many_to_many(
    model: Union[Type[T], str],
    through: Optional[Union[Type["Table"], str]] = None,
    backref: Optional[Union[str, bool]] = None,
    back_populates: Optional[str] = None,
    lazy: str = "select",
    extra: Optional[Dict[str, Any]] = None,
    on_delete: str = "none",
    cascade: Optional["CascadeOptions"] = None,
    filter: Optional[List] = None,
    order_by: Optional[Union[str, List[str]]] = None,
) -> ManyToMany[T]:
    """
    Define a many-to-many relationship.
    
    The simplest way to create M2M relationships in Python.
    
    Args:
        model: Target model class or string name
        through: Junction table (auto-created if not provided)
        backref: Name for auto-created reverse relationship.
                 - None (default): Auto-generate from owner class name
                   (e.g., on Student class → backref="students")
                 - str: Use provided name
                 - False: Explicitly disable backref (no reverse relationship)
        back_populates: Name of existing reverse relationship to sync
        lazy: Loading strategy (select, selectin, subquery, raise, dynamic)
        extra: Extra columns for junction table (alternative to through=).
               Dict of {column_name: type}, e.g., {"grade": Optional[str]}
        on_delete: Cascade preset for deletion. For M2M, "cascade" deletes
                   junction rows (not the related items themselves)
        cascade: Fine-grained CascadeOptions for advanced control
        filter: List of conditions to filter related records
        order_by: Default ordering (e.g., "name" or ["position", "name desc"])
    
    Loading Strategies:
        select   - Lazy load on access (default, may cause N+1)
        selectin - SELECT WHERE id IN (...) - best for batches
        subquery - Subquery for IN clause - good for complex queries
        raise    - Raise error on access (prevents N+1)
        dynamic  - Return query builder instead of loading
    
    Cascade Options (on_delete):
        "cascade" - Delete junction rows when parent deleted
        "none"    - Do nothing (default, let DB handle it)
    
    Filter Syntax:
        filter=[eq("is_active", True)]           # Condition functions
        filter=[("is_active", "=", True)]        # Tuple syntax
    
    Order By Syntax:
        order_by="name"                          # Single column, ascending
        order_by="created_at desc"               # Single column, descending
        order_by=["position", "name"]            # Multiple columns
    
    Examples:
        # Simplest - auto-backref as "students"
        class Student(Table):
            courses: List[Course] = many_to_many(Course)
        
        # With ordering
        class Student(Table):
            courses: List[Course] = many_to_many(Course, order_by="name")
        
        # Explicit backref name
        class Student(Table):
            courses: List[Course] = many_to_many(Course, backref="enrolled_students")
        
        # No backref (one-way relationship)
        class Student(Table):
            courses: List[Course] = many_to_many(Course, backref=False)
        
        # With inline extra columns (no separate model needed!)
        class Student(Table):
            courses: List[Course] = many_to_many(Course, extra={
                "grade": Optional[str],
                "enrolled_at": datetime,
            })
        
        # With cascade delete (removes junction rows)
        class Student(Table):
            courses: List[Course] = many_to_many(Course, on_delete="cascade")
        
        # With explicit junction table (for complex cases)
        class Enrollment(Table):
            student_id: int
            course_id: int
            grade: Optional[str]
        
        class Student(Table):
            courses: List[Course] = many_to_many(Course, through=Enrollment)
        
        # With loading strategy
        class Student(Table):
            courses: List[Course] = many_to_many(Course, lazy="selectin")
    
    Returns:
        ManyToMany descriptor
    """
    return ManyToMany(
        rel_name="",  # Will be set by __set_name__
        model=model,
        through=through,
        backref=backref,
        back_populates=back_populates,
        lazy=lazy,
        extra=extra,
        on_delete=on_delete,
        cascade=cascade,
        filter=filter,
        order_by=order_by,
    )
