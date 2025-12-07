"""
PyNext Hook Executor.

Provides a clean interface for executing hooks from collections
and relationship descriptors.

Design Philosophy:
- Synchronous execution for maximum speed
- Zero overhead when no hooks are registered
- Error handling that doesn't break the main operation
- Easy to trace and debug

Usage:
    from pynext.db.relationships.hook_executor import HookExecutor
    
    executor = HookExecutor()
    
    # In collection append
    executor.on_append(owner, "posts", new_post)
    
    # In collection remove
    executor.on_remove(owner, "posts", removed_post)
    
    # In scalar relationship setter
    executor.on_set(owner, "profile", old_profile, new_profile)
    
    # Before cascade delete
    executor.before_delete(instance)
"""

from __future__ import annotations

from typing import Any, Optional, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from pynext.db.table import Table

from pynext.db.relationships.hooks import (
    HookType,
    get_hook_registry,
    fire_hooks,
)


class HookExecutor:
    """
    Executor for relationship hooks.
    
    Provides a clean, simple interface for firing hooks.
    All execution is synchronous for maximum performance.
    
    Usage:
        executor = HookExecutor()
        
        # Fire on_append hook
        executor.on_append(user, "posts", new_post)
        
        # Fire on_remove hook  
        executor.on_remove(user, "posts", removed_post)
        
        # Fire on_set hook
        executor.on_set(user, "profile", old_profile, new_profile)
        
        # Fire before_delete hook
        executor.before_delete(user)
    """
    
    def __init__(self, suppress_errors: bool = False):
        """
        Initialize the hook executor.
        
        Args:
            suppress_errors: If True, catch and log errors instead of raising.
                           Default is False (errors propagate).
        """
        self._suppress_errors = suppress_errors
    
    def on_append(self, instance: "Table", relationship: str, item: Any) -> None:
        """
        Execute on_append hooks for a collection.
        
        Called when an item is added to a collection (append, extend, insert, etc.)
        
        Args:
            instance: The model instance that owns the collection
            relationship: The relationship name (e.g., "posts")
            item: The item being added
        """
        self._execute(
            instance,
            HookType.ON_APPEND,
            relationship=relationship,
            item=item,
        )
    
    def on_remove(self, instance: "Table", relationship: str, item: Any) -> None:
        """
        Execute on_remove hooks for a collection.
        
        Called when an item is removed from a collection (remove, pop, clear, del)
        
        Args:
            instance: The model instance that owns the collection
            relationship: The relationship name (e.g., "posts")
            item: The item being removed
        """
        self._execute(
            instance,
            HookType.ON_REMOVE,
            relationship=relationship,
            item=item,
        )
    
    def on_set(
        self, 
        instance: "Table", 
        relationship: str, 
        old_value: Any, 
        new_value: Any
    ) -> None:
        """
        Execute on_set hooks for a scalar relationship.
        
        Called when a scalar relationship (has_one, belongs_to) is set.
        
        Args:
            instance: The model instance
            relationship: The relationship name (e.g., "profile")
            old_value: The previous value (may be None)
            new_value: The new value (may be None)
        """
        self._execute(
            instance,
            HookType.ON_SET,
            relationship=relationship,
            old_value=old_value,
            new_value=new_value,
        )
    
    def before_delete(self, instance: "Table") -> None:
        """
        Execute before_delete hooks.
        
        Called before cascade delete starts.
        
        Args:
            instance: The model instance being deleted
        """
        self._execute(instance, HookType.BEFORE_DELETE)
    
    def _execute(
        self,
        instance: "Table",
        hook_type: HookType,
        relationship: Optional[str] = None,
        item: Any = None,
        old_value: Any = None,
        new_value: Any = None,
    ) -> None:
        """
        Internal method to execute hooks.
        
        Args:
            instance: The model instance
            hook_type: Type of hook to execute
            relationship: Relationship name (for collection/scalar hooks)
            item: Item being added/removed (for collection hooks)
            old_value: Previous value (for on_set)
            new_value: New value (for on_set)
        """
        try:
            fire_hooks(
                instance=instance,
                hook_type=hook_type,
                relationship=relationship,
                item=item,
                old_value=old_value,
                new_value=new_value,
            )
        except Exception as e:
            if not self._suppress_errors:
                raise
            # If suppressing, just log (could add proper logging here)
            pass


# Global executor instance for convenience
_executor: Optional[HookExecutor] = None


def get_hook_executor() -> HookExecutor:
    """
    Get the global hook executor.
    
    Returns:
        The global HookExecutor instance
    """
    global _executor
    if _executor is None:
        _executor = HookExecutor()
    return _executor


def reset_hook_executor() -> None:
    """Reset the global hook executor. Used for testing."""
    global _executor
    _executor = None


def set_hook_executor(executor: HookExecutor) -> None:
    """
    Set the global hook executor.
    
    Useful for testing or custom error handling.
    
    Args:
        executor: The HookExecutor to use
    """
    global _executor
    _executor = executor


# =============================================================================
# Convenience Functions
# =============================================================================

def fire_on_append(instance: "Table", relationship: str, item: Any) -> None:
    """
    Fire on_append hooks for a relationship.
    
    Convenience function that uses the global executor.
    
    Args:
        instance: The model instance
        relationship: The relationship name
        item: The item being appended
    """
    get_hook_executor().on_append(instance, relationship, item)


def fire_on_remove(instance: "Table", relationship: str, item: Any) -> None:
    """
    Fire on_remove hooks for a relationship.
    
    Convenience function that uses the global executor.
    
    Args:
        instance: The model instance
        relationship: The relationship name
        item: The item being removed
    """
    get_hook_executor().on_remove(instance, relationship, item)


def fire_on_set(
    instance: "Table", 
    relationship: str, 
    old_value: Any, 
    new_value: Any
) -> None:
    """
    Fire on_set hooks for a relationship.
    
    Convenience function that uses the global executor.
    
    Args:
        instance: The model instance
        relationship: The relationship name
        old_value: The previous value
        new_value: The new value
    """
    get_hook_executor().on_set(instance, relationship, old_value, new_value)


def fire_before_delete(instance: "Table") -> None:
    """
    Fire before_delete hooks.
    
    Convenience function that uses the global executor.
    
    Args:
        instance: The model instance being deleted
    """
    get_hook_executor().before_delete(instance)

