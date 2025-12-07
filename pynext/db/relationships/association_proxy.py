"""
PyNext Association Proxy.

Access attributes through relationships with simple, Pythonic syntax.

Design Philosophy:
- Stupid simple: `association_proxy("enrollments", "course.name")` 
- Auto-detect scalar vs collection based on source relationship
- Dot-notation for nested path traversal
- Zero configuration for common cases
- AI-friendly: clear patterns LLMs can understand

SQLAlchemy Comparison:
    # SQLAlchemy - Requires import, confusing parameters
    from sqlalchemy.ext.associationproxy import association_proxy
    
    class User(Base):
        keywords = association_proxy('user_keywords', 'keyword')
        keyword_names = association_proxy('user_keywords', 'keyword', 
                                          attr='name')  # What's attr?
    
    # PyNext - Built-in, intuitive dot notation
    class User(Table):
        keywords: List[Keyword] = association_proxy("user_keywords", "keyword")
        keyword_names: List[str] = association_proxy("user_keywords", "keyword.name")

Usage:
    from pynext.db import Table, has_many, belongs_to, association_proxy
    
    class User(Table):
        enrollments: List[Enrollment] = has_many(Enrollment)
        
        # Access course objects through enrollments
        courses: List[Course] = association_proxy("enrollments", "course")
        
        # Access course names with dot notation
        course_names: List[str] = association_proxy("enrollments", "course.name")
    
    class Post(Table):
        author: User = belongs_to(User, "author_id")
        
        # Scalar proxy - returns single value, not list
        author_name: str = association_proxy("author", "name")
    
    # Usage is dead simple:
    user.course_names    # ["Math", "Physics", "Chemistry"]
    post.author_name     # "Alice" (not ["Alice"]!)
"""

from __future__ import annotations

from collections.abc import MutableSequence
from typing import (
    Any,
    Callable,
    Generic,
    Iterable,
    Iterator,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
    TYPE_CHECKING,
    overload,
)

if TYPE_CHECKING:
    from pynext.db.table import Table

T = TypeVar("T")


# =============================================================================
# Main Function: association_proxy()
# =============================================================================

def association_proxy(
    target_collection: str,
    attr: str,
    *,
    creator: Optional[Callable[[Any], Any]] = None,
    scalar: Optional[bool] = None,
    flatten: bool = False,
) -> "AttributeProxyDescriptor":
    """
    Create a proxy to access attributes through relationships.
    
    This is THE function you use for association proxies. It creates a
    descriptor that traverses relationships and extracts attributes.
    
    Args:
        target_collection: Name of the relationship to traverse (e.g., "enrollments")
        attr: Attribute or dot-path to access (e.g., "course" or "course.name")
        creator: Optional function to create junction objects when appending
        scalar: Force scalar mode (None = auto-detect from relationship type)
        flatten: If True, flatten nested lists (e.g., for permissions lists)
    
    Returns:
        A descriptor that provides proxy access to the attribute
    
    Examples:
        # Collection proxy - returns list
        class User(Table):
            enrollments: List[Enrollment] = has_many(Enrollment)
            courses: List[Course] = association_proxy("enrollments", "course")
            course_names: List[str] = association_proxy("enrollments", "course.name")
        
        # Scalar proxy - returns single value
        class Post(Table):
            author: User = belongs_to(User, "author_id")
            author_name: str = association_proxy("author", "name")
        
        # With creator for append support
        class Product(Table):
            product_tags: List[ProductTag] = has_many(ProductTag)
            tags: List[Tag] = association_proxy(
                "product_tags", 
                "tag",
                creator=lambda tag: ProductTag(tag=tag)
            )
        
        # Usage:
        user.course_names    # ["Math", "Physics"]
        post.author_name     # "Alice"
        product.tags.append(new_tag)  # Creates ProductTag automatically
    """
    return AttributeProxyDescriptor(
        target_collection=target_collection,
        attr=attr,
        creator=creator,
        scalar=scalar,
        flatten=flatten,
    )


# =============================================================================
# AttributeProxyDescriptor
# =============================================================================

class AttributeProxyDescriptor(Generic[T]):
    """
    Descriptor that provides proxy access to attributes through relationships.
    
    Created by association_proxy() function. Handles:
    - Path traversal ("course.name" -> obj.course.name)
    - Scalar vs collection auto-detection
    - Lazy evaluation
    - Creator functions for append
    
    Attributes:
        target_collection: Name of the relationship to traverse
        attr: Attribute path (simple or dot-notation)
        creator: Optional function for creating items when appending
        _scalar: Force scalar mode (None = auto-detect)
        flatten: Whether to flatten nested lists
    """
    
    def __init__(
        self,
        target_collection: str,
        attr: str,
        creator: Optional[Callable[[Any], Any]] = None,
        scalar: Optional[bool] = None,
        flatten: bool = False,
    ):
        """
        Initialize the proxy descriptor.
        
        Args:
            target_collection: Name of relationship to traverse
            attr: Attribute path to access
            creator: Function to create junction objects
            scalar: Force scalar mode
            flatten: Flatten nested lists
        """
        self.target_collection = target_collection
        self.attr = attr
        self.creator = creator
        self._scalar = scalar
        self.flatten = flatten
        self._name: Optional[str] = None
        self._owner_class: Optional[Type] = None
    
    def __set_name__(self, owner: Type["Table"], name: str) -> None:
        """Called when descriptor is assigned to a class attribute."""
        self._name = name
        self._owner_class = owner
    
    def __get__(
        self, 
        obj: Optional["Table"], 
        objtype: Optional[Type["Table"]] = None,
    ) -> Union["AttributeProxyDescriptor[T]", T, List[T], "ProxyCollection[T]"]:
        """
        Get the proxied value(s).
        
        When accessed on the class, returns the descriptor itself.
        When accessed on an instance:
        - Returns single value if source is scalar (belongs_to, has_one)
        - Returns ProxyCollection if source is collection (has_many, m2m)
        """
        if obj is None:
            return self
        
        # Get the source relationship value
        source = getattr(obj, self.target_collection, None)
        
        # Determine if scalar or collection
        is_scalar = self._is_scalar(source, obj)
        
        if is_scalar:
            # Scalar: return single value
            return self._get_scalar_value(source)
        else:
            # Collection: return ProxyCollection for full list operations
            return ProxyCollection(
                owner=obj,
                target_collection=self.target_collection,
                attr=self.attr,
                creator=self.creator,
                flatten=self.flatten,
            )
    
    def __set__(self, obj: "Table", value: Any) -> None:
        """
        Set values through the proxy.
        
        For scalar proxies, this is not supported (set the relationship directly).
        For collection proxies with creator, replaces all items.
        """
        source = getattr(obj, self.target_collection, None)
        is_scalar = self._is_scalar(source, obj)
        
        if is_scalar:
            raise AttributeError(
                f"Cannot set scalar proxy '{self._name}' directly. "
                f"Set '{self.target_collection}' instead."
            )
        
        if self.creator is None:
            raise AttributeError(
                f"Cannot set proxy '{self._name}' without a creator function. "
                f"Add creator=lambda x: ... to association_proxy()."
            )
        
        # Clear existing and add new items
        source_collection = getattr(obj, self.target_collection)
        source_collection.clear()
        
        for item in value:
            new_junction = self.creator(item)
            source_collection.append(new_junction)
    
    def _is_scalar(self, source: Any, obj: "Table") -> bool:
        """
        Determine if this should return a scalar or collection.
        
        Args:
            source: The source relationship value
            obj: The owner instance
        
        Returns:
            True if scalar (single value), False if collection
        """
        # If explicitly set, use that
        if self._scalar is not None:
            return self._scalar
        
        # Check if source is None (could be unloaded scalar)
        if source is None:
            # Check the class-level descriptor to determine type
            descriptor = getattr(type(obj), self.target_collection, None)
            if descriptor is not None:
                # Check for BelongsTo or HasOne (scalar types)
                from pynext.db.relationships.core import BelongsTo, HasOne
                if isinstance(descriptor, (BelongsTo, HasOne)):
                    return True
            return False
        
        # If source is iterable (list, collection), it's not scalar
        if isinstance(source, (list, tuple)) or hasattr(source, '__iter__'):
            # But Table instances are also iterable, check for that
            if hasattr(source, '_fields') and hasattr(source, '__table_name__'):
                return True  # It's a single Table instance
            if hasattr(source, '_items'):  # SyncedList, ManyToManyCollection
                return False
            if isinstance(source, str):
                return True  # Strings are iterable but scalar
            return False
        
        return True  # Default to scalar for single objects
    
    def _get_scalar_value(self, source: Any) -> Any:
        """
        Get a single value by traversing the attribute path.
        
        Args:
            source: The source object to traverse from
        
        Returns:
            The value at the end of the path, or None
        """
        return _traverse_path(source, self.attr)
    
    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"AttributeProxyDescriptor("
            f"'{self.target_collection}', '{self.attr}'"
            f"{', creator=...' if self.creator else ''}"
            f")"
        )


# =============================================================================
# ProxyCollection
# =============================================================================

class ProxyCollection(MutableSequence, Generic[T]):
    """
    Collection returned by association_proxy for list-like access.
    
    This behaves like a list but extracts values through the relationship.
    Supports iteration, indexing, len(), and append() (with creator).
    
    Example:
        user.course_names  # Returns ProxyCollection
        
        # Iteration
        for name in user.course_names:
            print(name)
        
        # Indexing
        first = user.course_names[0]
        
        # Length
        count = len(user.course_names)
        
        # Append (with creator)
        user.tags.append(new_tag)  # Creates junction object
    """
    
    def __init__(
        self,
        owner: "Table",
        target_collection: str,
        attr: str,
        creator: Optional[Callable[[Any], Any]] = None,
        flatten: bool = False,
    ):
        """
        Initialize the proxy collection.
        
        Args:
            owner: The Table instance that owns this proxy
            target_collection: Name of the relationship to traverse
            attr: Attribute path to extract
            creator: Optional function to create junction objects
            flatten: Whether to flatten nested lists
        """
        self._owner = owner
        self._target_collection = target_collection
        self._attr = attr
        self._creator = creator
        self._flatten = flatten
        self._cached_values: Optional[List[T]] = None
    
    # =========================================================================
    # Core Collection Methods
    # =========================================================================
    
    def _get_values(self) -> List[T]:
        """
        Get all values by traversing the relationship.
        
        Returns:
            List of extracted values
        """
        source = getattr(self._owner, self._target_collection, None)
        if source is None:
            return []
        
        result: List[T] = []
        
        for item in source:
            value = _traverse_path(item, self._attr)
            if value is not None:
                if self._flatten and isinstance(value, (list, tuple)):
                    result.extend(value)
                else:
                    result.append(value)
        
        return result
    
    def __iter__(self) -> Iterator[T]:
        """Iterate through proxied values."""
        return iter(self._get_values())
    
    def __len__(self) -> int:
        """Return the number of proxied values."""
        return len(self._get_values())
    
    def __getitem__(self, index: Union[int, slice]) -> Union[T, List[T]]:
        """Get value(s) by index or slice."""
        values = self._get_values()
        return values[index]
    
    def __setitem__(self, index: int, value: T) -> None:
        """
        Set value at index.
        
        This is complex for proxies and generally not recommended.
        Raises an error to guide users to better patterns.
        """
        raise TypeError(
            f"Cannot set items on proxy collection '{self._target_collection}.{self._attr}'. "
            f"Modify the source collection directly."
        )
    
    def __delitem__(self, index: int) -> None:
        """
        Delete value at index.
        
        This is complex for proxies. Raises an error.
        """
        raise TypeError(
            f"Cannot delete items from proxy collection. "
            f"Use remove() on the source collection."
        )
    
    def __contains__(self, item: Any) -> bool:
        """Check if item is in the proxied values."""
        return item in self._get_values()
    
    def __bool__(self) -> bool:
        """Return True if there are any values."""
        return len(self) > 0
    
    def __eq__(self, other: Any) -> bool:
        """Check equality with another list or ProxyCollection."""
        if isinstance(other, ProxyCollection):
            return self._get_values() == other._get_values()
        if isinstance(other, list):
            return self._get_values() == other
        return NotImplemented
    
    # =========================================================================
    # Mutation Methods
    # =========================================================================
    
    def insert(self, index: int, value: T) -> None:
        """
        Insert a value at index.
        
        Requires a creator function to be set.
        Note: The index is for the proxied values, but insertion
        happens at the end of the source collection (order not guaranteed).
        """
        if self._creator is None:
            raise ValueError(
                f"Cannot insert into proxy without creator function. "
                f"Add creator=lambda x: ... to association_proxy()."
            )
        
        source = getattr(self._owner, self._target_collection)
        new_item = self._creator(value)
        source.append(new_item)  # Note: inserts at end, not at index
    
    def append(self, value: T) -> None:
        """
        Append a value through the proxy.
        
        Creates a junction object using the creator function and
        appends it to the source collection.
        
        Args:
            value: The value to append (e.g., a Tag object)
        
        Example:
            # With creator=lambda tag: ProductTag(tag=tag)
            product.tags.append(new_tag)
            # Creates ProductTag(tag=new_tag) and appends to product_tags
        """
        if self._creator is None:
            raise ValueError(
                f"Cannot append to proxy without creator function. "
                f"Add creator=lambda x: ... to association_proxy()."
            )
        
        source = getattr(self._owner, self._target_collection)
        new_item = self._creator(value)
        source.append(new_item)
    
    def extend(self, values: Iterable[T]) -> None:
        """
        Extend with multiple values.
        
        Args:
            values: Iterable of values to append
        """
        for value in values:
            self.append(value)
    
    def remove(self, value: T) -> None:
        """
        Remove a value from the proxy.
        
        Finds the source item that produces this value and removes it.
        
        Args:
            value: The value to remove
        
        Raises:
            ValueError: If value not found
        """
        source = getattr(self._owner, self._target_collection)
        
        # Find the source item that produces this value
        for item in list(source):
            item_value = _traverse_path(item, self._attr)
            if item_value == value:
                source.remove(item)
                return
        
        raise ValueError(f"{value!r} not in proxy collection")
    
    def pop(self, index: int = -1) -> T:
        """
        Remove and return value at index.
        
        Args:
            index: Index of value to pop (default: -1, last)
        
        Returns:
            The removed value
        """
        source = getattr(self._owner, self._target_collection)
        values = self._get_values()
        
        if not values:
            raise IndexError("pop from empty proxy collection")
        
        value = values[index]
        
        # Find and remove the source item
        for item in list(source):
            item_value = _traverse_path(item, self._attr)
            if item_value == value:
                source.remove(item)
                return value
        
        raise IndexError("pop index out of range")
    
    def clear(self) -> None:
        """Clear all items from the source collection."""
        source = getattr(self._owner, self._target_collection)
        source.clear()
    
    # =========================================================================
    # Query Methods
    # =========================================================================
    
    def index(self, value: T, start: int = 0, stop: Optional[int] = None) -> int:
        """Return index of first occurrence of value."""
        values = self._get_values()
        if stop is None:
            return values.index(value, start)
        return values.index(value, start, stop)
    
    def count(self, value: T) -> int:
        """Return number of occurrences of value."""
        return self._get_values().count(value)
    
    def copy(self) -> List[T]:
        """Return a shallow copy as a regular list."""
        return self._get_values().copy()
    
    # =========================================================================
    # Async Methods
    # =========================================================================
    
    async def all(self) -> List[T]:
        """
        Get all values asynchronously.
        
        Returns:
            List of all proxied values
        """
        return self._get_values()
    
    async def first(self) -> Optional[T]:
        """
        Get the first value asynchronously.
        
        Returns:
            First value or None if empty
        """
        values = self._get_values()
        return values[0] if values else None
    
    async def filter(self, **kwargs: Any) -> List[T]:
        """
        Filter values by attributes.
        
        Only works when proxied values are objects with attributes.
        
        Args:
            **kwargs: Attribute filters
        
        Returns:
            Filtered list of values
        """
        values = self._get_values()
        result = []
        
        for value in values:
            match = True
            for key, expected in kwargs.items():
                if not hasattr(value, key):
                    match = False
                    break
                if getattr(value, key) != expected:
                    match = False
                    break
            if match:
                result.append(value)
        
        return result
    
    # =========================================================================
    # Special Methods
    # =========================================================================
    
    def __repr__(self) -> str:
        """Return string representation."""
        return f"ProxyCollection({self._target_collection}.{self._attr}, {self._get_values()!r})"
    
    def __str__(self) -> str:
        """Return string representation of values."""
        return str(self._get_values())
    
    def to_list(self) -> List[T]:
        """Convert to a regular Python list."""
        return self._get_values()
    
    def __add__(self, other: List[T]) -> List[T]:
        """Concatenate with another list."""
        return self._get_values() + list(other)
    
    def __radd__(self, other: List[T]) -> List[T]:
        """Reverse concatenation."""
        return list(other) + self._get_values()


# =============================================================================
# Helper Functions
# =============================================================================

def _traverse_path(obj: Any, path: str) -> Any:
    """
    Traverse a dot-notation path on an object.
    
    Examples:
        _traverse_path(enrollment, "course.name")
        # Returns enrollment.course.name
        
        _traverse_path(user, "profile.bio")
        # Returns user.profile.bio
        
        _traverse_path(user, "")
        # Returns user (empty path returns object itself)
    
    Args:
        obj: The object to start traversal from
        path: Dot-separated attribute path
    
    Returns:
        The value at the end of the path, or None if any step fails
    """
    if obj is None:
        return None
    
    # Empty path returns the object itself
    if not path:
        return obj
    
    parts = path.split(".")
    current = obj
    
    for part in parts:
        if current is None:
            return None
        current = getattr(current, part, None)
    
    return current


def _is_collection_type(obj: Any) -> bool:
    """
    Check if an object is a collection type.
    
    Args:
        obj: Object to check
    
    Returns:
        True if it's a collection (list, tuple, SyncedList, etc.)
    """
    if obj is None:
        return False
    
    # Check for common collection types
    if isinstance(obj, (list, tuple, set, frozenset)):
        return True
    
    # Check for PyNext collection types
    if hasattr(obj, '_items'):  # SyncedList, ManyToManyCollection
        return True
    
    # Check for Table instances (not collections)
    if hasattr(obj, '_fields') and hasattr(obj, '__table_name__'):
        return False
    
    # Strings are iterable but not collections in this context
    if isinstance(obj, str):
        return False
    
    return False


# =============================================================================
# Convenience Aliases
# =============================================================================

# For users who prefer shorter names
proxy = association_proxy
attr_proxy = association_proxy

