"""
PyNext Synced Collections.

Collections that automatically sync backref relationships when modified.

When you call user.posts.append(post), SyncedList:
1. Adds post to its internal list
2. Calls RelationshipSyncManager to set post.author = user
3. Fires on_append hooks registered on the model

This provides the "magic" of bidirectional sync while keeping
the implementation explicit and debuggable.

Design:
- SyncedList extends MutableSequence for full list compatibility
- Every mutation method triggers the appropriate sync
- Every mutation method fires registered hooks
- The sync manager handles loop prevention
- Works with any Table subclass
"""

from __future__ import annotations

from collections.abc import MutableSequence
from typing import (
    Any,
    Generic,
    Iterable,
    Iterator,
    List,
    Optional,
    TypeVar,
    Union,
    TYPE_CHECKING,
    overload,
)

if TYPE_CHECKING:
    from pynext.db.table import Table

T = TypeVar("T", bound="Table")


class SyncedList(MutableSequence, Generic[T]):
    """
    A list that syncs backref relationships on modifications.
    
    This behaves like a normal Python list, but when you add or remove
    items, it automatically updates the reverse relationship.
    
    Usage:
        # Normally created automatically by HasMany descriptor
        user.posts  # Returns SyncedList
        
        # All list operations work:
        user.posts.append(post)      # Also sets post.author = user
        user.posts.remove(post)      # Also sets post.author = None
        user.posts.extend([p1, p2])  # Sets author on all
        user.posts.clear()           # Clears all author references
        user.posts[0] = new_post     # Updates both old and new
        del user.posts[0]            # Clears author on deleted
        user.posts.insert(0, post)   # Sets author
        user.posts.pop()             # Clears author on popped
    
    Attributes:
        _owner: The Table instance that owns this collection
        _attr_name: The attribute name on the owner (e.g., "posts")
        _items: The underlying list of items
    """
    
    def __init__(
        self,
        owner: "Table",
        attr_name: str,
        items: Optional[Iterable[T]] = None,
    ):
        """
        Initialize a synced list.
        
        Args:
            owner: The Table instance that owns this collection
            attr_name: The attribute name (e.g., "posts")
            items: Initial items (optional)
        """
        self._owner = owner
        self._attr_name = attr_name
        self._items: List[T] = list(items) if items else []
    
    # =========================================================================
    # Core MutableSequence Methods
    # =========================================================================
    
    def __getitem__(self, index: Union[int, slice]) -> Union[T, List[T]]:
        """Get item(s) by index or slice."""
        return self._items[index]
    
    @overload
    def __setitem__(self, index: int, value: T) -> None: ...
    
    @overload
    def __setitem__(self, index: slice, value: Iterable[T]) -> None: ...
    
    def __setitem__(self, index, value):
        """
        Set item(s) by index or slice.
        
        Syncs:
        - Removes old item(s) from relationship
        - Adds new item(s) to relationship
        
        Hooks:
        - Fires on_remove for old item(s)
        - Fires on_append for new item(s)
        """
        from pynext.db.relationships.backref import get_sync_manager
        from pynext.db.relationships.hook_executor import fire_on_append, fire_on_remove
        sync_manager = get_sync_manager()
        
        if isinstance(index, slice):
            # Get old items to unsync
            old_items = self._items[index]
            for old_item in old_items:
                sync_manager.sync_has_many_remove(self._owner, self._attr_name, old_item)
                fire_on_remove(self._owner, self._attr_name, old_item)
            
            # Set new items
            new_items = list(value)
            self._items[index] = new_items
            
            # Sync new items
            for new_item in new_items:
                sync_manager.sync_has_many_append(self._owner, self._attr_name, new_item)
                fire_on_append(self._owner, self._attr_name, new_item)
        else:
            # Single item
            old_item = self._items[index]
            sync_manager.sync_has_many_remove(self._owner, self._attr_name, old_item)
            fire_on_remove(self._owner, self._attr_name, old_item)
            
            self._items[index] = value
            sync_manager.sync_has_many_append(self._owner, self._attr_name, value)
            fire_on_append(self._owner, self._attr_name, value)
    
    def __delitem__(self, index: Union[int, slice]) -> None:
        """
        Delete item(s) by index or slice.
        
        Syncs: Removes deleted item(s) from relationship.
        Hooks: Fires on_remove for deleted item(s).
        """
        from pynext.db.relationships.backref import get_sync_manager
        from pynext.db.relationships.hook_executor import fire_on_remove
        sync_manager = get_sync_manager()
        
        if isinstance(index, slice):
            items_to_remove = self._items[index]
            for item in items_to_remove:
                sync_manager.sync_has_many_remove(self._owner, self._attr_name, item)
                fire_on_remove(self._owner, self._attr_name, item)
            del self._items[index]
        else:
            item = self._items[index]
            sync_manager.sync_has_many_remove(self._owner, self._attr_name, item)
            fire_on_remove(self._owner, self._attr_name, item)
            del self._items[index]
    
    def __len__(self) -> int:
        """Return the number of items."""
        return len(self._items)
    
    def __iter__(self) -> Iterator[T]:
        """Iterate over items."""
        return iter(self._items)
    
    def __contains__(self, item: Any) -> bool:
        """Check if item is in the list."""
        return item in self._items
    
    def __reversed__(self) -> Iterator[T]:
        """Iterate in reverse order."""
        return reversed(self._items)
    
    # =========================================================================
    # Mutation Methods (all sync)
    # =========================================================================
    
    def insert(self, index: int, value: T) -> None:
        """
        Insert an item at a specific index.
        
        Syncs: Sets reverse relationship on inserted item.
        Hooks: Fires on_append hooks.
        
        Args:
            index: Position to insert at
            value: Item to insert
        """
        from pynext.db.relationships.backref import get_sync_manager
        from pynext.db.relationships.hook_executor import fire_on_append
        
        self._items.insert(index, value)
        get_sync_manager().sync_has_many_append(self._owner, self._attr_name, value)
        
        # Fire on_append hooks
        fire_on_append(self._owner, self._attr_name, value)
    
    def append(self, value: T) -> None:
        """
        Append an item to the end.
        
        Syncs: Sets reverse relationship on appended item.
        Hooks: Fires on_append hooks.
        
        Args:
            value: Item to append
        
        Example:
            user.posts.append(post)
            # Now post.author == user
            # Plus any @on_append("posts") hooks are called
        """
        from pynext.db.relationships.backref import get_sync_manager
        from pynext.db.relationships.hook_executor import fire_on_append
        
        self._items.append(value)
        get_sync_manager().sync_has_many_append(self._owner, self._attr_name, value)
        
        # Fire on_append hooks
        fire_on_append(self._owner, self._attr_name, value)
    
    def extend(self, values: Iterable[T]) -> None:
        """
        Extend list with multiple items.
        
        Syncs: Sets reverse relationship on all items.
        Hooks: Fires on_append hooks for each item.
        
        Args:
            values: Items to add
        
        Example:
            user.posts.extend([post1, post2, post3])
            # All posts now have author == user
            # @on_append("posts") hooks called for each
        """
        from pynext.db.relationships.backref import get_sync_manager
        from pynext.db.relationships.hook_executor import fire_on_append
        sync_manager = get_sync_manager()
        
        items_list = list(values)
        self._items.extend(items_list)
        
        for item in items_list:
            sync_manager.sync_has_many_append(self._owner, self._attr_name, item)
            # Fire on_append hooks for each item
            fire_on_append(self._owner, self._attr_name, item)
    
    def remove(self, value: T) -> None:
        """
        Remove first occurrence of an item.
        
        Syncs: Clears reverse relationship on removed item.
        Hooks: Fires on_remove hooks.
        If cascade.on_orphan=True, schedules the item for deletion.
        
        Args:
            value: Item to remove
        
        Raises:
            ValueError: If item not in list
        
        Example:
            user.posts.remove(post)
            # Now post.author == None
            # @on_remove("posts") hooks called
            # If on_orphan=True, post is scheduled for deletion
        """
        from pynext.db.relationships.backref import get_sync_manager
        from pynext.db.relationships.hook_executor import fire_on_remove
        
        self._items.remove(value)
        get_sync_manager().sync_has_many_remove(self._owner, self._attr_name, value)
        
        # Fire on_remove hooks
        fire_on_remove(self._owner, self._attr_name, value)
        
        # Handle orphan deletion if configured
        self._handle_orphan(value)
    
    def pop(self, index: int = -1) -> T:
        """
        Remove and return item at index.
        
        Syncs: Clears reverse relationship on popped item.
        Hooks: Fires on_remove hooks.
        If cascade.on_orphan=True, schedules the item for deletion.
        
        Args:
            index: Index to pop (default: -1, last item)
        
        Returns:
            The removed item
        
        Example:
            post = user.posts.pop()
            # Now post.author == None
            # @on_remove("posts") hooks called
            # If on_orphan=True, post is scheduled for deletion
        """
        from pynext.db.relationships.backref import get_sync_manager
        from pynext.db.relationships.hook_executor import fire_on_remove
        
        item = self._items.pop(index)
        get_sync_manager().sync_has_many_remove(self._owner, self._attr_name, item)
        
        # Fire on_remove hooks
        fire_on_remove(self._owner, self._attr_name, item)
        
        # Handle orphan deletion if configured
        self._handle_orphan(item)
        
        return item
    
    def clear(self) -> None:
        """
        Remove all items.
        
        Syncs: Clears reverse relationship on all items.
        Hooks: Fires on_remove hooks for each item.
        If cascade.on_orphan=True, schedules all items for deletion.
        
        Example:
            user.posts.clear()
            # All posts now have author == None
            # @on_remove("posts") hooks called for each
            # If on_orphan=True, all posts are scheduled for deletion
        """
        from pynext.db.relationships.backref import get_sync_manager
        from pynext.db.relationships.hook_executor import fire_on_remove
        sync_manager = get_sync_manager()
        
        # Copy list since we're modifying it
        items_to_clear = list(self._items)
        self._items.clear()
        
        for item in items_to_clear:
            sync_manager.sync_has_many_remove(self._owner, self._attr_name, item)
            # Fire on_remove hooks
            fire_on_remove(self._owner, self._attr_name, item)
            # Handle orphan deletion if configured
            self._handle_orphan(item)
    
    def _handle_orphan(self, item: T) -> None:
        """
        Handle orphan deletion if cascade.on_orphan=True.
        
        This schedules the item for deletion when it's removed from
        the collection. The actual deletion happens when the cascade
        manager is invoked.
        
        Args:
            item: The item being removed from the collection
        """
        # Get the relationship descriptor to check cascade config
        descriptor = getattr(type(self._owner), self._attr_name, None)
        if descriptor is None:
            return
        
        # Check for on_orphan in cascade options
        cascade = getattr(descriptor, "cascade", None)
        if cascade and getattr(cascade, "on_orphan", False):
            from pynext.db.relationships.cascade import get_cascade_manager
            manager = get_cascade_manager()
            manager.schedule_orphan_delete(item, self._owner, self._attr_name)
    
    # =========================================================================
    # Non-mutating Methods
    # =========================================================================
    
    def index(self, value: T, start: int = 0, stop: Optional[int] = None) -> int:
        """Return index of first occurrence of value."""
        if stop is None:
            return self._items.index(value, start)
        return self._items.index(value, start, stop)
    
    def count(self, value: T) -> int:
        """Return number of occurrences of value."""
        return self._items.count(value)
    
    def copy(self) -> List[T]:
        """Return a shallow copy as a regular list."""
        return self._items.copy()
    
    # =========================================================================
    # Special Methods
    # =========================================================================
    
    def __repr__(self) -> str:
        """Return string representation."""
        owner_type = type(self._owner).__name__
        return f"SyncedList({owner_type}.{self._attr_name}, {self._items!r})"
    
    def __str__(self) -> str:
        """Return string representation of items."""
        return str(self._items)
    
    def __eq__(self, other: Any) -> bool:
        """Check equality with another list or SyncedList."""
        if isinstance(other, SyncedList):
            return self._items == other._items
        if isinstance(other, list):
            return self._items == other
        return NotImplemented
    
    def __ne__(self, other: Any) -> bool:
        """Check inequality."""
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result
    
    def __add__(self, other: List[T]) -> List[T]:
        """Concatenate with another list (returns new regular list)."""
        return self._items + list(other)
    
    def __radd__(self, other: List[T]) -> List[T]:
        """Reverse concatenation (returns new regular list)."""
        return list(other) + self._items
    
    def __iadd__(self, other: Iterable[T]) -> "SyncedList[T]":
        """In-place addition (extend)."""
        self.extend(other)
        return self
    
    def __mul__(self, n: int) -> List[T]:
        """Repeat list (returns new regular list)."""
        return self._items * n
    
    def __rmul__(self, n: int) -> List[T]:
        """Reverse repeat (returns new regular list)."""
        return n * self._items
    
    def __bool__(self) -> bool:
        """Return True if list is not empty."""
        return bool(self._items)
    
    # =========================================================================
    # Sorting Methods (no sync needed)
    # =========================================================================
    
    def sort(self, *, key=None, reverse: bool = False) -> None:
        """Sort the list in place."""
        self._items.sort(key=key, reverse=reverse)
    
    def reverse(self) -> None:
        """Reverse the list in place."""
        self._items.reverse()
    
    # =========================================================================
    # Utility Methods
    # =========================================================================
    
    def to_list(self) -> List[T]:
        """Convert to a regular Python list."""
        return list(self._items)
    
    @property
    def owner(self) -> "Table":
        """Get the owner of this collection."""
        return self._owner
    
    @property
    def attr_name(self) -> str:
        """Get the attribute name."""
        return self._attr_name
    
    def _set_items_without_sync(self, items: List[T]) -> None:
        """
        Set items directly without triggering sync.
        
        Used internally by eager loading and sync manager.
        
        Args:
            items: New list of items
        """
        self._items = list(items)
    
    def _append_without_sync(self, item: T) -> None:
        """
        Append item without triggering sync.
        
        Used internally by sync manager to prevent recursion.
        
        Args:
            item: Item to append
        """
        self._items.append(item)
    
    def _remove_without_sync(self, item: T) -> None:
        """
        Remove item without triggering sync.
        
        Used internally by sync manager to prevent recursion.
        
        Args:
            item: Item to remove
        """
        if item in self._items:
            self._items.remove(item)

