"""
PyNext Many-to-Many Collection.

A collection that manages M2M relationships via junction tables.
All operations automatically create/delete junction rows.

Design Philosophy:
- Looks and feels like a normal Python list
- Junction table management is automatic and invisible
- Bidirectional sync with reverse relationship
- Support for extra columns via add() method
- Fires @on_append and @on_remove hooks for collection changes

SQLAlchemy Comparison:
    SQLAlchemy:
        parent.children.append(child)  # Works but no extra data
        # For extra data, must manually create association object
        assoc = Association(parent=parent, child=child, extra="value")
        session.add(assoc)
    
    PyNext:
        parent.children.append(child)           # Simple add
        parent.children.add(child, extra="A")   # With extra data - easy!
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
    from pynext.db.relationships.junction import JunctionConfig, JunctionManager

T = TypeVar("T", bound="Table")


class ManyToManyCollection(MutableSequence, Generic[T]):
    """
    Collection that manages M2M relationships via junction table.
    
    Operations automatically create/delete junction rows.
    Provides bidirectional sync with the reverse relationship.
    
    Usage:
        # Access collection
        courses = student.courses  # Returns ManyToManyCollection
        
        # Basic operations (auto-manage junction)
        student.courses.append(course)      # Creates junction row
        student.courses.remove(course)      # Deletes junction row
        student.courses.extend([c1, c2])    # Creates multiple junction rows
        student.courses.clear()             # Deletes all junction rows
        
        # With extra data (for explicit junction tables)
        student.courses.add(course, grade="A")  # Creates with extra data
        junction = await student.courses.get_junction(course)  # Get junction row
        
        # Standard list operations
        len(student.courses)
        course in student.courses
        for course in student.courses: ...
        student.courses[0]
        student.courses[1:3]
    
    Attributes:
        _owner: The Table instance that owns this collection
        _attr_name: The attribute name on the owner (e.g., "courses")
        _config: Junction table configuration
        _items: The underlying list of related items
        _reverse_attr: Attribute name on related items for bidirectional sync
    """
    
    def __init__(
        self,
        owner: "Table",
        attr_name: str,
        config: "JunctionConfig",
        items: Optional[Iterable[T]] = None,
        reverse_attr: Optional[str] = None,
    ):
        """
        Initialize a many-to-many collection.
        
        Args:
            owner: The Table instance that owns this collection
            attr_name: The attribute name (e.g., "courses")
            config: Junction table configuration
            items: Initial items (optional)
            reverse_attr: Attribute name on related items for sync
        """
        self._owner = owner
        self._attr_name = attr_name
        self._config = config
        self._items: List[T] = list(items) if items else []
        self._reverse_attr = reverse_attr
        self._pending_additions: List[tuple[T, dict]] = []  # (item, extra_data)
        self._pending_removals: List[T] = []
    
    # =========================================================================
    # Core MutableSequence Methods
    # =========================================================================
    
    def __getitem__(self, index: Union[int, slice, T]) -> Union[T, List[T], Optional["Table"]]:
        """
        Get item(s) by index, slice, or get junction row by related item.
        
        Usage:
            # By index (returns related item)
            course = student.courses[0]
            
            # By slice (returns list of related items)
            some_courses = student.courses[1:3]
            
            # By related item (returns junction row for accessing extra data!)
            enrollment = student.courses[math_course]
            print(enrollment.grade)  # Access extra column
            enrollment.grade = "A+"  # Modify extra column
        
        Args:
            index: Integer index, slice, or related Table instance
        
        Returns:
            - int/slice: The related item(s)
            - Table instance: The junction row (for accessing extra columns)
        """
        # Check if it's an integer or slice (standard access)
        if isinstance(index, (int, slice)):
            return self._items[index]
        
        # If it's a Table instance, return the junction row for that relationship
        # Check for _fields attribute which all Table subclasses have
        if hasattr(index, "_fields") and hasattr(index, "__table_name__"):
            # It's a Table instance - find junction row
            return self._get_junction_row_cached(index)
        
        # Fallback: try standard list access (will raise TypeError if invalid)
        return self._items[index]
    
    def _get_junction_row_cached(self, item: T) -> Optional["Table"]:
        """
        Get cached junction row for an item (sync access).
        
        For async access with database lookup, use get_junction(item).
        This returns cached data if available, None otherwise.
        """
        # Check if we have cached junction data
        cache_key = f"_junction_cache_{id(item)}"
        if hasattr(self, cache_key):
            return getattr(self, cache_key)
        
        # Return None if not cached - user should use async get_junction()
        # for guaranteed access
        return None
    
    @overload
    def __setitem__(self, index: int, value: T) -> None: ...
    
    @overload
    def __setitem__(self, index: slice, value: Iterable[T]) -> None: ...
    
    def __setitem__(self, index, value):
        """
        Set item(s) by index or slice.
        
        Fires on_remove for old items and on_append for new items.
        
        Note: This replaces items in the collection. Junction rows for
        removed items will be deleted, and new ones created for added items.
        """
        from pynext.db.relationships.hook_executor import fire_on_append, fire_on_remove
        
        if isinstance(index, slice):
            old_items = self._items[index]
            new_items = list(value)
            
            # Track removals
            for old_item in old_items:
                if old_item not in new_items:
                    self._pending_removals.append(old_item)
                    self._remove_from_reverse(old_item)
                    fire_on_remove(self._owner, self._attr_name, old_item)
            
            # Track additions
            for new_item in new_items:
                if new_item not in old_items:
                    self._pending_additions.append((new_item, {}))
                    self._add_to_reverse(new_item)
                    fire_on_append(self._owner, self._attr_name, new_item)
            
            self._items[index] = new_items
        else:
            old_item = self._items[index]
            
            if old_item != value:
                self._pending_removals.append(old_item)
                self._remove_from_reverse(old_item)
                fire_on_remove(self._owner, self._attr_name, old_item)
                
                self._pending_additions.append((value, {}))
                self._add_to_reverse(value)
                fire_on_append(self._owner, self._attr_name, value)
            
            self._items[index] = value
    
    def __delitem__(self, index: Union[int, slice]) -> None:
        """Delete item(s) by index or slice. Fires on_remove hooks."""
        from pynext.db.relationships.hook_executor import fire_on_remove
        
        if isinstance(index, slice):
            items_to_remove = self._items[index]
            for item in items_to_remove:
                self._pending_removals.append(item)
                self._remove_from_reverse(item)
                fire_on_remove(self._owner, self._attr_name, item)
            del self._items[index]
        else:
            item = self._items[index]
            self._pending_removals.append(item)
            self._remove_from_reverse(item)
            fire_on_remove(self._owner, self._attr_name, item)
            del self._items[index]
    
    def __len__(self) -> int:
        """Return the number of items."""
        return len(self._items)
    
    def __iter__(self) -> Iterator[T]:
        """Iterate over items."""
        return iter(self._items)
    
    def __contains__(self, item: Any) -> bool:
        """Check if item is in the collection."""
        return item in self._items
    
    def __reversed__(self) -> Iterator[T]:
        """Iterate in reverse order."""
        return reversed(self._items)
    
    # =========================================================================
    # Mutation Methods (all manage junction table)
    # =========================================================================
    
    def insert(self, index: int, value: T) -> None:
        """
        Insert an item at a specific index.
        
        Creates junction row and syncs reverse relationship.
        Fires on_append hooks.
        
        Args:
            index: Position to insert at
            value: Item to insert
        """
        from pynext.db.relationships.hook_executor import fire_on_append
        
        if value not in self._items:
            self._pending_additions.append((value, {}))
            self._add_to_reverse(value)
        
        self._items.insert(index, value)
        
        # Fire on_append hooks
        fire_on_append(self._owner, self._attr_name, value)
    
    def append(self, value: Union[T, tuple[T, dict]]) -> None:
        """
        Add an item to the collection.
        
        Creates junction row and syncs reverse relationship.
        Fires on_append hooks.
        
        Supports two syntaxes:
        1. Simple: append(item)
        2. With data: append((item, {"grade": "A"}))
        
        Args:
            value: Item to add, or tuple of (item, extra_data_dict)
        
        Example:
            # Simple append
            student.courses.append(course)
            # Creates junction row: (student_id, course_id)
            # @on_append("courses") hooks called
            
            # Append with extra data (tuple syntax)
            student.courses.append((course, {"grade": "A", "enrolled_at": now}))
            # Creates junction row with extra columns
            
            # Syncs: course.students now includes student
        """
        from pynext.db.relationships.hook_executor import fire_on_append
        
        # Handle tuple syntax: (item, data_dict)
        extra_data = {}
        if isinstance(value, tuple) and len(value) == 2:
            actual_item, extra_data = value
            if isinstance(extra_data, dict):
                value = actual_item
            else:
                # Not our tuple syntax, treat as regular value
                extra_data = {}
        
        if value not in self._items:
            self._pending_additions.append((value, extra_data))
            self._add_to_reverse(value)
            self._items.append(value)
            
            # Fire on_append hooks
            fire_on_append(self._owner, self._attr_name, value)
    
    def add(self, value: T, **extra: Any) -> None:
        """
        Add an item with extra junction data.
        
        Use this when your junction table has extra columns.
        Fires on_append hooks.
        
        Args:
            value: Item to add
            **extra: Extra column values for junction row
        
        Example:
            student.courses.add(course, grade="A", enrolled_at=datetime.now())
            # Creates junction row with extra data
            # @on_append("courses") hooks called
        """
        from pynext.db.relationships.hook_executor import fire_on_append
        
        if value not in self._items:
            self._pending_additions.append((value, extra))
            self._add_to_reverse(value)
            self._items.append(value)
            
            # Fire on_append hooks
            fire_on_append(self._owner, self._attr_name, value)
    
    def extend(self, values: Iterable[Union[T, tuple[T, dict]]]) -> None:
        """
        Add multiple items to the collection.
        
        Supports two syntaxes:
        1. Simple: extend([item1, item2])
        2. With data: extend([(item1, {"grade": "A"}), (item2, {"grade": "B"})])
        3. Mixed: extend([item1, (item2, {"grade": "B"})])
        
        Args:
            values: Items to add (or tuples of item + extra data)
        
        Example:
            # Simple extend
            student.courses.extend([math, science, english])
            
            # Extend with extra data
            student.courses.extend([
                (math, {"grade": "A"}),
                (science, {"grade": "B+"}),
                (english, {"grade": "A-"}),
            ])
            
            # Mixed (some with data, some without)
            student.courses.extend([
                math,  # No extra data
                (science, {"grade": "B+"}),  # With data
            ])
        """
        for value in values:
            self.append(value)
    
    def remove(self, value: T) -> None:
        """
        Remove an item from the collection.
        
        Deletes junction row and syncs reverse relationship.
        Fires on_remove hooks.
        If cascade.on_orphan=True on the M2M, the related item is NOT deleted
        (only the junction row is removed - this is different from has_many orphan).
        
        Args:
            value: Item to remove
        
        Raises:
            ValueError: If item not in collection
        
        Example:
            student.courses.remove(course)
            # Deletes junction row
            # @on_remove("courses") hooks called
            # Syncs: course.students no longer includes student
        """
        from pynext.db.relationships.hook_executor import fire_on_remove
        
        self._items.remove(value)
        self._pending_removals.append(value)
        self._remove_from_reverse(value)
        
        # Fire on_remove hooks
        fire_on_remove(self._owner, self._attr_name, value)
        
        # Note: For M2M, orphan handling is different from has_many
        # Removing from M2M collection only removes the junction row
        # It does NOT delete the related item itself
        # This is the expected behavior for M2M relationships
    
    def pop(self, index: int = -1) -> T:
        """
        Remove and return item at index.
        
        Fires on_remove hooks.
        
        Args:
            index: Index to pop (default: -1, last item)
        
        Returns:
            The removed item
        """
        from pynext.db.relationships.hook_executor import fire_on_remove
        
        item = self._items.pop(index)
        self._pending_removals.append(item)
        self._remove_from_reverse(item)
        
        # Fire on_remove hooks
        fire_on_remove(self._owner, self._attr_name, item)
        
        return item
    
    def clear(self) -> None:
        """
        Remove all items from the collection.
        
        Deletes all junction rows and syncs reverse relationships.
        Fires on_remove hooks for each item.
        """
        from pynext.db.relationships.hook_executor import fire_on_remove
        
        items_to_remove = list(self._items)
        self._items.clear()
        
        for item in items_to_remove:
            self._pending_removals.append(item)
            self._remove_from_reverse(item)
            # Fire on_remove hooks
            fire_on_remove(self._owner, self._attr_name, item)
    
    def discard(self, value: T) -> None:
        """
        Remove an item if present (no error if not found).
        
        Args:
            value: Item to remove
        """
        if value in self._items:
            self.remove(value)
    
    # =========================================================================
    # Junction Table Access
    # =========================================================================
    
    async def get_junction(self, value: T) -> Optional["Table"]:
        """
        Get the junction row for an item.
        
        Use this to access extra columns on the junction table.
        
        Args:
            value: Related item
        
        Returns:
            Junction row instance if found, None otherwise
        
        Example:
            junction = await student.courses.get_junction(math)
            if junction:
                print(f"Grade: {junction.grade}")
        """
        from pynext.db.relationships.junction import JunctionManager
        
        manager = JunctionManager(self._config)
        return await manager.get_row(self._owner, value)
    
    async def update_junction(self, value: T, **updates: Any) -> Optional["Table"]:
        """
        Update extra columns on a junction row.
        
        Args:
            value: Related item
            **updates: Column values to update
        
        Returns:
            Updated junction row if found, None otherwise
        
        Example:
            await student.courses.update_junction(math, grade="A+")
        """
        from pynext.db.relationships.junction import JunctionManager
        
        manager = JunctionManager(self._config)
        return await manager.update_row(self._owner, value, **updates)
    
    async def sync_junction_rows(self) -> None:
        """
        Synchronize pending junction row changes to the database.
        
        This is called automatically when the owner is saved,
        but can be called manually if needed.
        """
        from pynext.db.relationships.junction import JunctionManager
        
        manager = JunctionManager(self._config)
        
        # Process removals first
        for item in self._pending_removals:
            await manager.delete_row(self._owner, item)
        self._pending_removals.clear()
        
        # Then additions
        for item, extra in self._pending_additions:
            # Check if junction already exists
            exists = await manager.exists(self._owner, item)
            if not exists:
                await manager.create_row(self._owner, item, **extra)
        self._pending_additions.clear()
    
    # =========================================================================
    # Bidirectional Sync Helpers
    # =========================================================================
    
    def _add_to_reverse(self, item: T) -> None:
        """Add owner to item's reverse collection without recursion."""
        if not self._reverse_attr:
            return
        
        reverse_collection = getattr(item, f"_cached_{self._reverse_attr}", None)
        if reverse_collection is None:
            return
        
        if isinstance(reverse_collection, ManyToManyCollection):
            if self._owner not in reverse_collection._items:
                reverse_collection._items.append(self._owner)
    
    def _remove_from_reverse(self, item: T) -> None:
        """Remove owner from item's reverse collection without recursion."""
        if not self._reverse_attr:
            return
        
        reverse_collection = getattr(item, f"_cached_{self._reverse_attr}", None)
        if reverse_collection is None:
            return
        
        if isinstance(reverse_collection, ManyToManyCollection):
            if self._owner in reverse_collection._items:
                reverse_collection._items.remove(self._owner)
    
    def _append_without_sync(self, item: T) -> None:
        """
        Append item without triggering sync.
        
        Used internally by sync system to prevent recursion.
        """
        if item not in self._items:
            self._items.append(item)
    
    def _remove_without_sync(self, item: T) -> None:
        """
        Remove item without triggering sync.
        
        Used internally by sync system to prevent recursion.
        """
        if item in self._items:
            self._items.remove(item)
    
    def _set_items_without_sync(self, items: List[T]) -> None:
        """
        Set items directly without triggering sync.
        
        Used internally by eager loading.
        """
        self._items = list(items)
    
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
        return f"ManyToManyCollection({owner_type}.{self._attr_name}, {self._items!r})"
    
    def __str__(self) -> str:
        """Return string representation of items."""
        return str(self._items)
    
    def __eq__(self, other: Any) -> bool:
        """Check equality with another collection or list."""
        if isinstance(other, ManyToManyCollection):
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
    
    def __iadd__(self, other: Iterable[T]) -> "ManyToManyCollection[T]":
        """In-place addition (extend)."""
        self.extend(other)
        return self
    
    def __bool__(self) -> bool:
        """Return True if collection is not empty."""
        return bool(self._items)
    
    # =========================================================================
    # Sorting Methods
    # =========================================================================
    
    def sort(self, *, key=None, reverse: bool = False) -> None:
        """Sort the collection in place."""
        self._items.sort(key=key, reverse=reverse)
    
    def reverse(self) -> None:
        """Reverse the collection in place."""
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
    
    @property
    def config(self) -> "JunctionConfig":
        """Get the junction configuration."""
        return self._config
    
    @property
    def has_pending_changes(self) -> bool:
        """Check if there are pending junction row changes."""
        return bool(self._pending_additions) or bool(self._pending_removals)
    
    def get_pending_additions(self) -> List[tuple[T, dict]]:
        """Get list of pending additions (item, extra_data)."""
        return list(self._pending_additions)
    
    def get_pending_removals(self) -> List[T]:
        """Get list of pending removals."""
        return list(self._pending_removals)

