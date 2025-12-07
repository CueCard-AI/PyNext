"""
PyNext Backref - Bidirectional Relationship Sync.

Manages automatic synchronization between both sides of a relationship.
When you modify one side, the other side updates automatically.

Design:
- BackrefConfig: Configuration for a backref relationship
- BackrefRegistry: Tracks all bidirectional relationship pairs
- RelationshipSyncManager: Handles sync with infinite loop prevention

How it works:
1. User defines: has_many("Post", backref="author")
2. BackrefRegistry records: User.posts <-> Post.author
3. When user.posts.append(post) is called:
   - SyncedList calls sync_manager.sync_has_many_append()
   - Sync manager sets post.author = user (with guard to prevent loop)
4. When post.author = user is called:
   - BelongsTo.__set__ calls sync_manager.sync_belongs_to_set()
   - Sync manager adds post to user.posts (with guard to prevent loop)

The guard (ContextVar) prevents infinite loops:
- Before syncing, we check if this (object_id, attr) is in the guard set
- If yes, we're in a recursive call - skip the sync
- If no, add to guard, do sync, then remove from guard
"""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import (
    Any,
    Dict,
    Optional,
    Set,
    Tuple,
    Type,
    TYPE_CHECKING,
    Union,
)
from weakref import WeakValueDictionary

if TYPE_CHECKING:
    from pynext.db.table import Table

# Type alias for relationship pair key
RelationshipKey = Tuple[str, str]  # (table_name, attr_name)


@dataclass
class BackrefConfig:
    """
    Configuration for a backref relationship.
    
    Attributes:
        name: Name of the reverse relationship (e.g., "author" for Post.author)
        source_model: The model that defined the backref (e.g., User)
        source_attr: The attribute on source model (e.g., "posts")
        target_model: The model that gets the backref (e.g., Post)
        target_attr: The attribute on target model (e.g., "author")
        foreign_key: The FK field name (e.g., "author_id")
        cascade_add: Auto-add to reverse collection on set (default: True)
        cascade_remove: Auto-remove from reverse collection on unset (default: True)
    
    Example:
        # For: has_many("Post", backref="author")
        BackrefConfig(
            name="author",
            source_model=User,
            source_attr="posts",
            target_model=Post,
            target_attr="author",
            foreign_key="author_id",
        )
    """
    name: str
    source_model: Union[Type["Table"], str]
    source_attr: str
    target_model: Union[Type["Table"], str]
    target_attr: str
    foreign_key: Optional[str] = None
    cascade_add: bool = True
    cascade_remove: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization/debugging."""
        return {
            "name": self.name,
            "source_model": getattr(self.source_model, "__name__", str(self.source_model)),
            "source_attr": self.source_attr,
            "target_model": getattr(self.target_model, "__name__", str(self.target_model)),
            "target_attr": self.target_attr,
            "foreign_key": self.foreign_key,
            "cascade_add": self.cascade_add,
            "cascade_remove": self.cascade_remove,
        }


class BackrefRegistry:
    """
    Registry that tracks all bidirectional relationship pairs.
    
    This is a singleton that stores the mapping between:
    - Source side: (User, "posts") -> BackrefConfig
    - Target side: (Post, "author") -> BackrefConfig (with reversed perspective)
    
    Usage:
        registry = get_backref_registry()
        
        # Register a backref pair
        registry.register(config)
        
        # Look up backref for an attribute
        config = registry.get_backref("posts", Post)
        
        # Check if attribute has backref
        if registry.has_backref("users", Post, "posts"):
            # This attr syncs with another
    """
    
    def __init__(self):
        # Key: (table_name, attr_name) -> BackrefConfig
        self._source_to_config: Dict[RelationshipKey, BackrefConfig] = {}
        
        # Key: (table_name, attr_name) -> BackrefConfig (for reverse lookup)
        self._target_to_config: Dict[RelationshipKey, BackrefConfig] = {}
        
        # Pending backrefs (for forward references)
        # Key: target_table_name -> List of (config, callback)
        self._pending: Dict[str, list] = {}
    
    def register(self, config: BackrefConfig) -> None:
        """
        Register a bidirectional relationship pair.
        
        Args:
            config: The backref configuration
        
        Example:
            registry.register(BackrefConfig(
                name="author",
                source_model=User,
                source_attr="posts",
                target_model=Post,
                target_attr="author",
                foreign_key="author_id",
            ))
        """
        # Get table names
        source_table = self._get_table_name(config.source_model)
        target_table = self._get_table_name(config.target_model)
        
        # Register source -> config
        source_key = (source_table, config.source_attr)
        self._source_to_config[source_key] = config
        
        # Register target -> config (reverse lookup)
        target_key = (target_table, config.target_attr)
        self._target_to_config[target_key] = config
    
    def get_backref_for_source(
        self,
        model: Union[Type["Table"], str],
        attr: str,
    ) -> Optional[BackrefConfig]:
        """
        Get backref config for a source attribute.
        
        Args:
            model: The model class or table name
            attr: The attribute name (e.g., "posts")
        
        Returns:
            BackrefConfig if this attr has a backref, None otherwise
        """
        table_name = self._get_table_name(model)
        key = (table_name, attr)
        return self._source_to_config.get(key)
    
    def get_backref_for_target(
        self,
        model: Union[Type["Table"], str],
        attr: str,
    ) -> Optional[BackrefConfig]:
        """
        Get backref config for a target attribute (the auto-created side).
        
        Args:
            model: The model class or table name
            attr: The attribute name (e.g., "author")
        
        Returns:
            BackrefConfig if this attr is a backref target, None otherwise
        """
        table_name = self._get_table_name(model)
        key = (table_name, attr)
        return self._target_to_config.get(key)
    
    def has_backref(
        self,
        model: Union[Type["Table"], str],
        attr: str,
    ) -> bool:
        """
        Check if an attribute participates in a backref relationship.
        
        Args:
            model: The model class or table name
            attr: The attribute name
        
        Returns:
            True if this attr has bidirectional sync enabled
        """
        table_name = self._get_table_name(model)
        key = (table_name, attr)
        return key in self._source_to_config or key in self._target_to_config
    
    def get_reverse_attr(
        self,
        model: Union[Type["Table"], str],
        attr: str,
    ) -> Optional[Tuple[str, str]]:
        """
        Get the reverse attribute for a given relationship.
        
        Args:
            model: The model class or table name
            attr: The attribute name
        
        Returns:
            Tuple of (target_table, target_attr) or None
        """
        table_name = self._get_table_name(model)
        key = (table_name, attr)
        
        # Check if this is a source
        if key in self._source_to_config:
            config = self._source_to_config[key]
            target_table = self._get_table_name(config.target_model)
            return (target_table, config.target_attr)
        
        # Check if this is a target
        if key in self._target_to_config:
            config = self._target_to_config[key]
            source_table = self._get_table_name(config.source_model)
            return (source_table, config.source_attr)
        
        return None
    
    def add_pending(
        self,
        target_table: str,
        config: BackrefConfig,
    ) -> None:
        """
        Add a pending backref for forward reference resolution.
        
        When models reference each other (User -> Post -> User),
        we may need to defer backref setup until both models exist.
        
        Args:
            target_table: The table name we're waiting for
            config: The backref config to register when ready
        """
        if target_table not in self._pending:
            self._pending[target_table] = []
        self._pending[target_table].append(config)
    
    def resolve_pending(self, model: Type["Table"]) -> None:
        """
        Resolve any pending backrefs for a newly registered model.
        
        Called when a new Table subclass is created.
        
        Args:
            model: The newly created model class
        """
        table_name = model.__table_name__
        
        if table_name in self._pending:
            pending_configs = self._pending.pop(table_name)
            for config in pending_configs:
                # Update config with actual model reference
                if isinstance(config.target_model, str):
                    config.target_model = model
                if isinstance(config.source_model, str):
                    from pynext.db.table import _model_registry
                    source_name = config.source_model
                    # Try table name first
                    if source_name in _model_registry:
                        config.source_model = _model_registry[source_name]
                    else:
                        # Try class name to table name conversion
                        source_table = source_name.lower() + "s"
                        if source_table in _model_registry:
                            config.source_model = _model_registry[source_table]
                
                # Register the bidirectional pair
                self.register(config)
                
                # NOW actually create the descriptor on the target model!
                self._create_pending_descriptor(model, config)
    
    def clear(self) -> None:
        """Clear all registered backrefs. Useful for testing."""
        self._source_to_config.clear()
        self._target_to_config.clear()
        self._pending.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics for debugging."""
        return {
            "source_count": len(self._source_to_config),
            "target_count": len(self._target_to_config),
            "pending_count": sum(len(v) for v in self._pending.values()),
            "sources": list(self._source_to_config.keys()),
            "targets": list(self._target_to_config.keys()),
        }
    
    def _get_table_name(self, model: Union[Type["Table"], str]) -> str:
        """Get table name from model class or string."""
        if isinstance(model, str):
            return model
        return getattr(model, "__table_name__", model.__name__.lower() + "s")
    
    def _create_pending_descriptor(
        self,
        target_model: Type["Table"],
        config: BackrefConfig,
    ) -> None:
        """
        Create the descriptor on the target model for a pending backref.
        
        This is called when the target model is finally defined.
        
        Args:
            target_model: The newly created target model
            config: The backref configuration
        """
        from pynext.db.relationships.core import BelongsTo, HasMany, HasOne, RelationshipType
        
        target_attr = config.target_attr
        source_model = config.source_model
        source_attr = config.source_attr
        foreign_key = config.foreign_key
        
        # Skip if already has the attribute
        if hasattr(target_model, target_attr):
            existing = getattr(target_model, target_attr)
            if isinstance(existing, (BelongsTo, HasMany, HasOne)):
                return
        
        # Determine what type to create based on the source relationship type
        # If source is has_many, target gets belongs_to
        # If source is has_one, target gets belongs_to
        # If source is belongs_to, target gets has_many
        
        if isinstance(source_model, type):
            source_descriptor = getattr(source_model, source_attr, None)
            
            if isinstance(source_descriptor, HasMany):
                # Create belongs_to on target
                reverse_descriptor = BelongsTo(
                    rel_name=target_attr,
                    model=source_model,
                    foreign_key=foreign_key or "",
                    back_populates=source_attr,
                )
            elif isinstance(source_descriptor, HasOne):
                # Create belongs_to on target
                reverse_descriptor = BelongsTo(
                    rel_name=target_attr,
                    model=source_model,
                    foreign_key=foreign_key or "",
                    back_populates=source_attr,
                )
            elif isinstance(source_descriptor, BelongsTo):
                # Create has_many on target
                reverse_descriptor = HasMany(
                    rel_name=target_attr,
                    model=source_model,
                    foreign_key=foreign_key or "",
                    back_populates=source_attr,
                )
            else:
                # Default to belongs_to
                reverse_descriptor = BelongsTo(
                    rel_name=target_attr,
                    model=source_model,
                    foreign_key=foreign_key or "",
                    back_populates=source_attr,
                )
            
            setattr(target_model, target_attr, reverse_descriptor)
            
            # Update the source descriptor's back_populates
            if source_descriptor and hasattr(source_descriptor, 'back_populates'):
                source_descriptor.back_populates = target_attr
            
            # Update target's relationships dict
            if hasattr(target_model, "_relationships"):
                rel_type = RelationshipType.BELONGS_TO
                if isinstance(reverse_descriptor, HasMany):
                    rel_type = RelationshipType.HAS_MANY
                elif isinstance(reverse_descriptor, HasOne):
                    rel_type = RelationshipType.HAS_ONE
                
                target_model._relationships[target_attr] = {
                    "name": target_attr,
                    "type": rel_type,
                    "model": source_model,
                    "foreign_key": foreign_key,
                    "back_populates": source_attr,
                }


# Singleton instance
_backref_registry: Optional[BackrefRegistry] = None


def get_backref_registry() -> BackrefRegistry:
    """Get the global backref registry singleton."""
    global _backref_registry
    if _backref_registry is None:
        _backref_registry = BackrefRegistry()
    return _backref_registry


def reset_backref_registry() -> None:
    """Reset the backref registry. For testing only."""
    global _backref_registry
    if _backref_registry is not None:
        _backref_registry.clear()
    _backref_registry = None


class RelationshipSyncManager:
    """
    Manages bidirectional sync with infinite loop prevention.
    
    This is the core engine that synchronizes both sides of a relationship.
    It uses a context-variable-based guard to prevent infinite recursion.
    
    How the guard works:
    1. Before syncing, create a key: (id(object), attr_name)
    2. Check if key is in the guard set
    3. If yes: We're in a recursive call, skip sync
    4. If no: Add key to guard, do sync, remove key from guard
    
    Usage:
        manager = get_sync_manager()
        
        # When setting belongs_to
        manager.sync_belongs_to_set(post, "author", old_user, new_user)
        
        # When appending to has_many
        manager.sync_has_many_append(user, "posts", post)
        
        # When removing from has_many
        manager.sync_has_many_remove(user, "posts", post)
    """
    
    # Context variable for update guard (prevents infinite loops)
    # Stores set of (object_id, attr_name) currently being synced
    _update_guard: ContextVar[Set[Tuple[int, str]]] = ContextVar(
        "relationship_sync_guard",
        default=None,
    )
    
    def __init__(self, registry: Optional[BackrefRegistry] = None):
        """
        Initialize the sync manager.
        
        Args:
            registry: BackrefRegistry to use (defaults to global singleton)
        """
        self._registry = registry or get_backref_registry()
    
    def _get_guard(self) -> Set[Tuple[int, str]]:
        """Get or create the guard set for this context."""
        guard = self._update_guard.get()
        if guard is None:
            guard = set()
            self._update_guard.set(guard)
        return guard
    
    def _is_guarded(self, obj: Any, attr: str) -> bool:
        """Check if this (object, attr) is currently being synced."""
        guard = self._get_guard()
        return (id(obj), attr) in guard
    
    def _add_guard(self, obj: Any, attr: str) -> None:
        """Add (object, attr) to the sync guard."""
        guard = self._get_guard()
        guard.add((id(obj), attr))
    
    def _remove_guard(self, obj: Any, attr: str) -> None:
        """Remove (object, attr) from the sync guard."""
        guard = self._get_guard()
        guard.discard((id(obj), attr))
    
    def sync_belongs_to_set(
        self,
        instance: "Table",
        attr: str,
        old_value: Optional["Table"],
        new_value: Optional["Table"],
    ) -> None:
        """
        Sync when a belongs_to attribute is set.
        
        This handles:
        - Removing instance from old_value's has_many collection
        - Adding instance to new_value's has_many collection
        
        Args:
            instance: The object being modified (e.g., post)
            attr: The attribute name (e.g., "author")
            old_value: Previous value (e.g., old user)
            new_value: New value (e.g., new user)
        
        Example:
            post.author = new_user
            # This triggers:
            # 1. Remove post from old_user.posts (if old_user exists)
            # 2. Add post to new_user.posts (if new_user exists)
        """
        # Check if we're already syncing this (prevents infinite loop)
        if self._is_guarded(instance, attr):
            return
        
        # Get backref config
        model = type(instance)
        config = self._registry.get_backref_for_target(model, attr)
        
        if config is None:
            # Also check source side (for back_populates)
            config = self._registry.get_backref_for_source(model, attr)
        
        if config is None:
            # No backref configured for this attribute
            return
        
        # Add guard to prevent recursion
        self._add_guard(instance, attr)
        
        try:
            # Determine the reverse attribute
            if self._registry.get_backref_for_target(model, attr):
                # This is the target side (e.g., Post.author)
                reverse_attr = config.source_attr  # e.g., "posts"
            else:
                # This is the source side with back_populates
                reverse_attr = config.target_attr
            
            # Remove from old collection
            if old_value is not None and config.cascade_remove:
                self._remove_from_collection(old_value, reverse_attr, instance)
            
            # Add to new collection
            if new_value is not None and config.cascade_add:
                self._add_to_collection(new_value, reverse_attr, instance)
                
        finally:
            self._remove_guard(instance, attr)
    
    def sync_has_many_append(
        self,
        instance: "Table",
        attr: str,
        item: "Table",
    ) -> None:
        """
        Sync when an item is appended to a has_many collection.
        
        This sets the belongs_to attribute on the appended item.
        
        Args:
            instance: The owner of the collection (e.g., user)
            attr: The attribute name (e.g., "posts")
            item: The item being appended (e.g., post)
        
        Example:
            user.posts.append(post)
            # This triggers: post.author = user
        """
        # Skip None items - they can't have relationships set
        if item is None:
            return
        
        # Check if we're already syncing this
        if self._is_guarded(instance, attr):
            return
        
        # Get backref config
        model = type(instance)
        config = self._registry.get_backref_for_source(model, attr)
        
        if config is None:
            # Also check target side (for has_one backref)
            config = self._registry.get_backref_for_target(model, attr)
        
        if config is None or not config.cascade_add:
            return
        
        # Add guard
        self._add_guard(instance, attr)
        
        try:
            # Determine the reverse attribute
            if self._registry.get_backref_for_source(model, attr):
                # This is the source side (e.g., User.posts)
                reverse_attr = config.target_attr  # e.g., "author"
            else:
                # This is the target side with back_populates
                reverse_attr = config.source_attr
            
            # Set the belongs_to on the item
            self._set_belongs_to(item, reverse_attr, instance)
            
        finally:
            self._remove_guard(instance, attr)
    
    def sync_has_many_remove(
        self,
        instance: "Table",
        attr: str,
        item: "Table",
    ) -> None:
        """
        Sync when an item is removed from a has_many collection.
        
        This unsets the belongs_to attribute on the removed item.
        
        Args:
            instance: The owner of the collection (e.g., user)
            attr: The attribute name (e.g., "posts")
            item: The item being removed (e.g., post)
        
        Example:
            user.posts.remove(post)
            # This triggers: post.author = None
        """
        # Check if we're already syncing this
        if self._is_guarded(instance, attr):
            return
        
        # Get backref config
        model = type(instance)
        config = self._registry.get_backref_for_source(model, attr)
        
        if config is None:
            config = self._registry.get_backref_for_target(model, attr)
        
        if config is None or not config.cascade_remove:
            return
        
        # Add guard
        self._add_guard(instance, attr)
        
        try:
            # Determine the reverse attribute
            if self._registry.get_backref_for_source(model, attr):
                reverse_attr = config.target_attr
            else:
                reverse_attr = config.source_attr
            
            # Unset the belongs_to on the item
            self._set_belongs_to(item, reverse_attr, None)
            
        finally:
            self._remove_guard(instance, attr)
    
    def sync_has_one_set(
        self,
        instance: "Table",
        attr: str,
        old_value: Optional["Table"],
        new_value: Optional["Table"],
    ) -> None:
        """
        Sync when a has_one attribute is set.
        
        Similar to belongs_to sync but from the "one" side.
        
        Args:
            instance: The owner (e.g., user)
            attr: The attribute name (e.g., "profile")
            old_value: Previous value (e.g., old profile)
            new_value: New value (e.g., new profile)
        """
        # Check if we're already syncing this
        if self._is_guarded(instance, attr):
            return
        
        # Get backref config
        model = type(instance)
        config = self._registry.get_backref_for_source(model, attr)
        
        if config is None:
            config = self._registry.get_backref_for_target(model, attr)
        
        if config is None:
            return
        
        # Add guard
        self._add_guard(instance, attr)
        
        try:
            # Determine the reverse attribute
            if self._registry.get_backref_for_source(model, attr):
                reverse_attr = config.target_attr
            else:
                reverse_attr = config.source_attr
            
            # Unset old value's reverse
            if old_value is not None and config.cascade_remove:
                self._set_belongs_to(old_value, reverse_attr, None)
            
            # Set new value's reverse
            if new_value is not None and config.cascade_add:
                self._set_belongs_to(new_value, reverse_attr, instance)
                
        finally:
            self._remove_guard(instance, attr)
    
    def _add_to_collection(
        self,
        owner: "Table",
        attr: str,
        item: "Table",
    ) -> None:
        """Add item to owner's collection without triggering sync."""
        collection = getattr(owner, attr, None)
        
        if collection is None:
            # Initialize empty collection
            from pynext.db.relationships.collections import SyncedList
            collection = SyncedList(owner, attr, [])
            cache_attr = f"_cached_{attr}"
            setattr(owner, cache_attr, collection)
        
        # Add without sync (we're already in a sync operation)
        if hasattr(collection, '_items'):
            # It's a SyncedList - add directly to avoid recursion
            if item not in collection._items:
                collection._items.append(item)
        elif isinstance(collection, list):
            if item not in collection:
                collection.append(item)
    
    def _remove_from_collection(
        self,
        owner: "Table",
        attr: str,
        item: "Table",
    ) -> None:
        """Remove item from owner's collection without triggering sync."""
        collection = getattr(owner, attr, None)
        
        if collection is None:
            return
        
        # Remove without sync
        if hasattr(collection, '_items'):
            # It's a SyncedList - remove directly
            if item in collection._items:
                collection._items.remove(item)
        elif isinstance(collection, list):
            if item in collection:
                collection.remove(item)
    
    def _set_belongs_to(
        self,
        instance: "Table",
        attr: str,
        value: Optional["Table"],
    ) -> None:
        """Set a belongs_to attribute without triggering sync."""
        cache_attr = f"_cached_{attr}"
        setattr(instance, cache_attr, value)
        
        # Also update the FK field if we know it
        model = type(instance)
        config = self._registry.get_backref_for_target(model, attr)
        
        if config and config.foreign_key:
            # Get id safely - might not be set for unsaved objects
            fk_value = getattr(value, "id", None) if value is not None else None
            if hasattr(instance, config.foreign_key):
                setattr(instance, config.foreign_key, fk_value)


# Singleton instance
_sync_manager: Optional[RelationshipSyncManager] = None


def get_sync_manager() -> RelationshipSyncManager:
    """Get the global sync manager singleton."""
    global _sync_manager
    if _sync_manager is None:
        _sync_manager = RelationshipSyncManager()
    return _sync_manager


def reset_sync_manager() -> None:
    """Reset the sync manager. For testing only."""
    global _sync_manager
    _sync_manager = None

