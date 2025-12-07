"""
PyNext Relationship Hooks.

Simple, decorator-based event hooks for relationship changes.

Design Philosophy:
- Decorators live IN the model class (not scattered elsewhere like SQLAlchemy)
- Simple callback signatures: (self, item) not (target, value, initiator)
- Synchronous execution for maximum speed (zero coroutine overhead)
- AI-friendly: Clear patterns that LLMs can understand and generate

SQLAlchemy Comparison:
    # SQLAlchemy - Verbose, disconnected from model
    @event.listens_for(User.posts, 'append')
    def on_post_append(target, value, initiator):
        pass  # What is initiator?
    
    # PyNext - Simple, in the model
    class User(Table):
        posts: List[Post] = has_many(Post)
        
        @on_append("posts")
        def on_post_added(self, post: Post):
            send_notification(f"New post by {self.name}")

Usage:
    from pynext.db import Table, has_many, on_append, on_remove, on_set, before_delete
    
    class User(Table):
        posts: List[Post] = has_many(Post)
        profile: Profile = has_one(Profile)
        
        @on_append("posts")
        def on_post_added(self, post: Post):
            '''Called when a post is added to user.posts.'''
            log_activity(f"New post by {self.name}")
        
        @on_remove("posts") 
        def on_post_removed(self, post: Post):
            '''Called when a post is removed.'''
            log_audit(f"Post {post.id} removed")
        
        @on_set("profile")
        def on_profile_changed(self, old: Profile, new: Profile):
            '''Called when profile is set or changed.'''
            if old and new:
                log_audit(f"Profile changed")
        
        @before_delete()
        def cleanup(self):
            '''Called before cascade delete.'''
            archive_user_data(self)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Type,
    TypeVar,
    TYPE_CHECKING,
)
from weakref import WeakKeyDictionary

if TYPE_CHECKING:
    from pynext.db.table import Table

T = TypeVar("T", bound="Table")


class HookType(str, Enum):
    """Types of relationship hooks."""
    ON_APPEND = "on_append"
    ON_REMOVE = "on_remove"
    ON_SET = "on_set"
    BEFORE_DELETE = "before_delete"


@dataclass
class HookConfig:
    """
    Configuration for a registered hook.
    
    Attributes:
        type: The hook type (ON_APPEND, ON_REMOVE, etc.)
        relationship: The relationship name this hook applies to (None for before_delete)
        priority: Execution priority (lower = earlier, default 0)
    """
    type: HookType
    relationship: Optional[str] = None
    priority: int = 0


@dataclass
class HookRegistry:
    """
    Registry of hooks for a single model class.
    
    Stores hooks by type and relationship name for fast lookup.
    Hooks are executed synchronously for maximum performance.
    
    Attributes:
        _on_append: Dict mapping relationship name to list of append hooks
        _on_remove: Dict mapping relationship name to list of remove hooks
        _on_set: Dict mapping relationship name to list of set hooks
        _before_delete: List of before_delete hooks
    """
    _on_append: Dict[str, List[Callable]] = field(default_factory=dict)
    _on_remove: Dict[str, List[Callable]] = field(default_factory=dict)
    _on_set: Dict[str, List[Callable]] = field(default_factory=dict)
    _before_delete: List[Callable] = field(default_factory=list)
    
    def register_on_append(self, relationship: str, hook: Callable) -> None:
        """
        Register an on_append hook for a relationship.
        
        Args:
            relationship: The relationship name (e.g., "posts")
            hook: The hook function (unbound method)
        """
        if relationship not in self._on_append:
            self._on_append[relationship] = []
        self._on_append[relationship].append(hook)
    
    def register_on_remove(self, relationship: str, hook: Callable) -> None:
        """
        Register an on_remove hook for a relationship.
        
        Args:
            relationship: The relationship name (e.g., "posts")
            hook: The hook function (unbound method)
        """
        if relationship not in self._on_remove:
            self._on_remove[relationship] = []
        self._on_remove[relationship].append(hook)
    
    def register_on_set(self, relationship: str, hook: Callable) -> None:
        """
        Register an on_set hook for a relationship.
        
        Args:
            relationship: The relationship name (e.g., "profile")
            hook: The hook function (unbound method)
        """
        if relationship not in self._on_set:
            self._on_set[relationship] = []
        self._on_set[relationship].append(hook)
    
    def register_before_delete(self, hook: Callable) -> None:
        """
        Register a before_delete hook.
        
        Args:
            hook: The hook function (unbound method)
        """
        self._before_delete.append(hook)
    
    def fire_on_append(self, instance: "Table", relationship: str, item: Any) -> None:
        """
        Fire all on_append hooks for a relationship.
        
        Synchronous execution - direct function calls for maximum speed.
        
        Args:
            instance: The model instance (owner of the collection)
            relationship: The relationship name
            item: The item being appended
        """
        hooks = self._on_append.get(relationship, [])
        for hook in hooks:
            hook(instance, item)
    
    def fire_on_remove(self, instance: "Table", relationship: str, item: Any) -> None:
        """
        Fire all on_remove hooks for a relationship.
        
        Synchronous execution - direct function calls for maximum speed.
        
        Args:
            instance: The model instance (owner of the collection)
            relationship: The relationship name
            item: The item being removed
        """
        hooks = self._on_remove.get(relationship, [])
        for hook in hooks:
            hook(instance, item)
    
    def fire_on_set(
        self, 
        instance: "Table", 
        relationship: str, 
        old_value: Any, 
        new_value: Any
    ) -> None:
        """
        Fire all on_set hooks for a relationship.
        
        Synchronous execution - direct function calls for maximum speed.
        
        Args:
            instance: The model instance
            relationship: The relationship name
            old_value: The previous value (may be None)
            new_value: The new value (may be None)
        """
        hooks = self._on_set.get(relationship, [])
        for hook in hooks:
            hook(instance, old_value, new_value)
    
    def fire_before_delete(self, instance: "Table") -> None:
        """
        Fire all before_delete hooks.
        
        Synchronous execution - direct function calls for maximum speed.
        
        Args:
            instance: The model instance being deleted
        """
        for hook in self._before_delete:
            hook(instance)
    
    def has_hooks_for(self, relationship: str) -> bool:
        """
        Check if any hooks are registered for a relationship.
        
        Args:
            relationship: The relationship name
            
        Returns:
            True if any hooks exist
        """
        return (
            relationship in self._on_append or
            relationship in self._on_remove or
            relationship in self._on_set
        )
    
    def get_hook_count(self) -> int:
        """Get total number of registered hooks."""
        count = len(self._before_delete)
        for hooks in self._on_append.values():
            count += len(hooks)
        for hooks in self._on_remove.values():
            count += len(hooks)
        for hooks in self._on_set.values():
            count += len(hooks)
        return count
    
    def merge_from(self, other: "HookRegistry") -> None:
        """
        Merge hooks from another registry (for inheritance).
        
        Args:
            other: Another HookRegistry to merge from
        """
        for rel, hooks in other._on_append.items():
            if rel not in self._on_append:
                self._on_append[rel] = []
            self._on_append[rel].extend(hooks)
        
        for rel, hooks in other._on_remove.items():
            if rel not in self._on_remove:
                self._on_remove[rel] = []
            self._on_remove[rel].extend(hooks)
        
        for rel, hooks in other._on_set.items():
            if rel not in self._on_set:
                self._on_set[rel] = []
            self._on_set[rel].extend(hooks)
        
        self._before_delete.extend(other._before_delete)


# Global registry: maps model classes to their HookRegistry
_hook_registries: Dict[Type["Table"], HookRegistry] = {}


def get_hook_registry(model_class: Type["Table"]) -> HookRegistry:
    """
    Get or create the hook registry for a model class.
    
    Also handles inheritance - merges parent hooks.
    
    Args:
        model_class: The model class
        
    Returns:
        The HookRegistry for this class
    """
    if model_class not in _hook_registries:
        registry = HookRegistry()
        
        # Merge hooks from parent classes (inheritance support)
        for base in model_class.__mro__[1:]:
            if base in _hook_registries:
                registry.merge_from(_hook_registries[base])
        
        _hook_registries[model_class] = registry
    
    return _hook_registries[model_class]


def reset_hook_registries() -> None:
    """Reset all hook registries. Used for testing."""
    global _hook_registries
    _hook_registries = {}


def discover_hooks(model_class: Type["Table"]) -> None:
    """
    Discover and register hooks defined on a model class.
    
    Scans the class for methods decorated with @on_append, @on_remove, etc.
    and registers them in the class's HookRegistry.
    
    Args:
        model_class: The model class to scan
    """
    registry = get_hook_registry(model_class)
    
    for name in dir(model_class):
        try:
            attr = getattr(model_class, name)
        except AttributeError:
            continue
        
        if not callable(attr):
            continue
        
        # Check for hook config
        hook_config = getattr(attr, "_pynext_hook", None)
        if hook_config is None:
            continue
        
        # Register based on hook type
        if hook_config.type == HookType.ON_APPEND:
            registry.register_on_append(hook_config.relationship, attr)
        elif hook_config.type == HookType.ON_REMOVE:
            registry.register_on_remove(hook_config.relationship, attr)
        elif hook_config.type == HookType.ON_SET:
            registry.register_on_set(hook_config.relationship, attr)
        elif hook_config.type == HookType.BEFORE_DELETE:
            registry.register_before_delete(attr)


# =============================================================================
# Decorator Functions
# =============================================================================

def on_append(relationship_name: str, *, priority: int = 0) -> Callable:
    """
    Decorator to register an on_append hook for a collection relationship.
    
    Called when an item is added to the collection via append(), extend(),
    insert(), or assignment.
    
    Args:
        relationship_name: The name of the relationship (e.g., "posts")
        priority: Execution priority (lower = earlier, default 0)
    
    Returns:
        Decorator function
    
    Example:
        class User(Table):
            posts: List[Post] = has_many(Post)
            
            @on_append("posts")
            def on_post_added(self, post: Post):
                send_notification(f"New post by {self.name}")
    """
    def decorator(func: Callable) -> Callable:
        func._pynext_hook = HookConfig(
            type=HookType.ON_APPEND,
            relationship=relationship_name,
            priority=priority,
        )
        return func
    return decorator


def on_remove(relationship_name: str, *, priority: int = 0) -> Callable:
    """
    Decorator to register an on_remove hook for a collection relationship.
    
    Called when an item is removed from the collection via remove(), pop(),
    clear(), or del.
    
    Args:
        relationship_name: The name of the relationship (e.g., "posts")
        priority: Execution priority (lower = earlier, default 0)
    
    Returns:
        Decorator function
    
    Example:
        class User(Table):
            posts: List[Post] = has_many(Post)
            
            @on_remove("posts")
            def on_post_removed(self, post: Post):
                log_audit(f"Post {post.id} removed from {self.name}")
    """
    def decorator(func: Callable) -> Callable:
        func._pynext_hook = HookConfig(
            type=HookType.ON_REMOVE,
            relationship=relationship_name,
            priority=priority,
        )
        return func
    return decorator


def on_set(relationship_name: str, *, priority: int = 0) -> Callable:
    """
    Decorator to register an on_set hook for a scalar relationship.
    
    Called when a scalar relationship (has_one, belongs_to) is set or changed.
    The callback receives both old and new values.
    
    Args:
        relationship_name: The name of the relationship (e.g., "profile")
        priority: Execution priority (lower = earlier, default 0)
    
    Returns:
        Decorator function
    
    Example:
        class User(Table):
            profile: Profile = has_one(Profile)
            
            @on_set("profile")
            def on_profile_changed(self, old_profile: Profile, new_profile: Profile):
                if old_profile and new_profile:
                    log_audit(f"Profile changed from {old_profile.id} to {new_profile.id}")
    """
    def decorator(func: Callable) -> Callable:
        func._pynext_hook = HookConfig(
            type=HookType.ON_SET,
            relationship=relationship_name,
            priority=priority,
        )
        return func
    return decorator


def before_delete(*, priority: int = 0) -> Callable:
    """
    Decorator to register a before_delete hook.
    
    Called before cascade delete starts on this instance.
    Use this to archive data, send notifications, or perform cleanup.
    
    Args:
        priority: Execution priority (lower = earlier, default 0)
    
    Returns:
        Decorator function
    
    Example:
        class User(Table):
            @before_delete()
            def cleanup_before_delete(self):
                archive_user_data(self)
                send_goodbye_email(self.email)
    """
    def decorator(func: Callable) -> Callable:
        func._pynext_hook = HookConfig(
            type=HookType.BEFORE_DELETE,
            relationship=None,
            priority=priority,
        )
        return func
    return decorator


# =============================================================================
# Helper Functions
# =============================================================================

def has_hooks(model_class: Type["Table"]) -> bool:
    """
    Check if a model class has any registered hooks.
    
    Args:
        model_class: The model class to check
        
    Returns:
        True if any hooks are registered
    """
    if model_class not in _hook_registries:
        return False
    return _hook_registries[model_class].get_hook_count() > 0


def get_hooks_for_relationship(
    model_class: Type["Table"], 
    relationship: str, 
    hook_type: HookType
) -> List[Callable]:
    """
    Get all hooks of a specific type for a relationship.
    
    Args:
        model_class: The model class
        relationship: The relationship name
        hook_type: The type of hooks to get
        
    Returns:
        List of hook functions
    """
    if model_class not in _hook_registries:
        return []
    
    registry = _hook_registries[model_class]
    
    if hook_type == HookType.ON_APPEND:
        return registry._on_append.get(relationship, [])
    elif hook_type == HookType.ON_REMOVE:
        return registry._on_remove.get(relationship, [])
    elif hook_type == HookType.ON_SET:
        return registry._on_set.get(relationship, [])
    elif hook_type == HookType.BEFORE_DELETE:
        return registry._before_delete
    
    return []


def fire_hooks(
    instance: "Table",
    hook_type: HookType,
    relationship: Optional[str] = None,
    item: Any = None,
    old_value: Any = None,
    new_value: Any = None,
) -> None:
    """
    Fire hooks of a specific type.
    
    This is the main entry point for firing hooks from collections
    and relationship descriptors.
    
    Args:
        instance: The model instance
        hook_type: The type of hooks to fire
        relationship: The relationship name (required for append/remove/set)
        item: The item being added/removed (for append/remove)
        old_value: The previous value (for on_set)
        new_value: The new value (for on_set)
    """
    model_class = type(instance)
    
    if model_class not in _hook_registries:
        return
    
    registry = _hook_registries[model_class]
    
    if hook_type == HookType.ON_APPEND and relationship:
        registry.fire_on_append(instance, relationship, item)
    elif hook_type == HookType.ON_REMOVE and relationship:
        registry.fire_on_remove(instance, relationship, item)
    elif hook_type == HookType.ON_SET and relationship:
        registry.fire_on_set(instance, relationship, old_value, new_value)
    elif hook_type == HookType.BEFORE_DELETE:
        registry.fire_before_delete(instance)

