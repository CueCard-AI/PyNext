"""
PyNext Association Proxy.

Provides direct access to related objects through a junction table.

Design Philosophy:
- Access related objects directly without navigating through junction
- Works with both implicit and explicit junction tables
- Full query builder support for filtering, counting, etc.
- AI-friendly: clear, explicit behavior

SQLAlchemy Comparison:
    SQLAlchemy requires association_proxy from sqlalchemy.ext:
        from sqlalchemy.ext.associationproxy import association_proxy
        
        class User(Base):
            keywords = association_proxy('user_keywords', 'keyword')
    
    PyNext - built in and simpler:
        class User(Table):
            tags: List[Tag] = many_to_many(Tag, through=UserTag, backref="users")
            # Direct access to tags without extra imports or configuration!

Usage:
    # Instead of navigating through junction:
    #   student.enrollments -> [Enrollment] -> enrollment.course
    
    # Direct access:
    student.courses  # Returns list of Course objects
    
    # With filtering via proxy:
    await student.courses.filter(active=True)
    await student.courses.count()
"""

from __future__ import annotations

from typing import (
    Any,
    Generic,
    Iterator,
    List,
    Optional,
    Type,
    TypeVar,
    TYPE_CHECKING,
    Union,
)

if TYPE_CHECKING:
    from pynext.db.table import Table
    from pynext.db.query import Query
    from pynext.db.relationships.junction import JunctionConfig

T = TypeVar("T", bound="Table")


class AssociationProxy(Generic[T]):
    """
    Provides direct access to related objects through a junction.
    
    Instead of:
        student.enrollments -> [Enrollment] -> enrollment.course
    
    Access directly:
        student.courses -> [Course]
    
    The proxy handles the junction table navigation automatically.
    
    Attributes:
        _owner: The Table instance that owns the proxy
        _target_model: The model class being accessed (e.g., Course)
        _through_attr: Attribute name for junction collection (e.g., "enrollments")
        _target_attr: Attribute name on junction for target (e.g., "course")
        _config: Junction table configuration
    
    Usage:
        # Get all courses for a student
        courses = student.courses  # Returns AssociationProxy
        
        # Iterate
        for course in student.courses:
            print(course.name)
        
        # Check membership
        math in student.courses
        
        # Count (async)
        count = await student.courses.count()
        
        # Filter (async)
        active_courses = await student.courses.filter(active=True)
    """
    
    def __init__(
        self,
        owner: "Table",
        target_model: Union[Type[T], str],
        config: "JunctionConfig",
        through_attr: Optional[str] = None,
        target_attr: Optional[str] = None,
    ):
        """
        Initialize an association proxy.
        
        Args:
            owner: The Table instance that owns the proxy
            target_model: The related model class
            config: Junction table configuration
            through_attr: Attribute name for junction collection
            target_attr: Attribute name on junction for target
        """
        self._owner = owner
        self._target_model = target_model
        self._config = config
        self._through_attr = through_attr
        self._target_attr = target_attr or config.target_fk.replace("_id", "")
        self._cached_items: Optional[List[T]] = None
    
    @property
    def target_model(self) -> Type[T]:
        """Get the target model class (resolve string if needed)."""
        if isinstance(self._target_model, str):
            from pynext.db.table import _model_registry
            model = _model_registry.get(self._target_model)
            if model is None:
                # Try lowercase + s convention
                table_name = self._target_model.lower() + "s"
                model = _model_registry.get(table_name)
            if model is None:
                raise ValueError(f"Could not resolve target model: {self._target_model}")
            self._target_model = model
        return self._target_model
    
    # =========================================================================
    # Iteration and Access
    # =========================================================================
    
    def __iter__(self) -> Iterator[T]:
        """
        Iterate through target objects.
        
        If through_attr is set, navigates through junction objects.
        Otherwise, uses cached items from eager loading.
        """
        if self._cached_items is not None:
            yield from self._cached_items
            return
        
        if self._through_attr:
            # Navigate through junction objects
            junction_items = getattr(self._owner, self._through_attr, [])
            for junction in junction_items:
                target = getattr(junction, self._target_attr, None)
                if target is not None:
                    yield target
    
    def __len__(self) -> int:
        """Return the number of related items."""
        # Don't use list(self) - it calls __len__ causing recursion
        count = 0
        for _ in self.__iter__():
            count += 1
        return count
    
    def __contains__(self, item: Any) -> bool:
        """Check if item is in the collection."""
        return any(i == item or (hasattr(i, 'id') and hasattr(item, 'id') and i.id == item.id) 
                   for i in self)
    
    def __bool__(self) -> bool:
        """Return True if there are any related items."""
        return any(True for _ in self)
    
    def __getitem__(self, index: int) -> T:
        """Get item by index."""
        # Don't use list(self) - build list manually to avoid __len__
        items = [item for item in self.__iter__()]
        return items[index]
    
    # =========================================================================
    # Async Query Methods
    # =========================================================================
    
    async def all(self) -> List[T]:
        """
        Get all related items.
        
        Returns:
            List of related model instances
        
        Example:
            courses = await student.courses.all()
        """
        return list(self)
    
    async def count(self) -> int:
        """
        Count related items efficiently.
        
        Uses COUNT query on junction table for efficiency.
        
        Returns:
            Number of related items
        
        Example:
            num_courses = await student.courses.count()
        """
        from pynext.db.relationships.junction import JunctionManager, get_junction_factory
        
        factory = get_junction_factory()
        junction_class = factory.get_or_create(self._config)
        
        owner_id = getattr(self._owner, "id", None)
        if owner_id is None:
            return 0
        
        return await junction_class.select().where(**{
            self._config.source_fk: owner_id,
        }).count()
    
    async def exists(self) -> bool:
        """
        Check if any related items exist.
        
        Returns:
            True if at least one related item exists
        
        Example:
            has_courses = await student.courses.exists()
        """
        count = await self.count()
        return count > 0
    
    async def filter(self, **kwargs: Any) -> List[T]:
        """
        Filter related items.
        
        Args:
            **kwargs: Filter conditions for target model
        
        Returns:
            Filtered list of related items
        
        Example:
            active_courses = await student.courses.filter(active=True)
        """
        all_items = list(self)
        
        result = []
        for item in all_items:
            match = True
            for key, value in kwargs.items():
                if getattr(item, key, None) != value:
                    match = False
                    break
            if match:
                result.append(item)
        
        return result
    
    async def first(self) -> Optional[T]:
        """
        Get the first related item.
        
        Returns:
            First item or None if empty
        
        Example:
            first_course = await student.courses.first()
        """
        for item in self:
            return item
        return None
    
    async def get_ids(self) -> List[int]:
        """
        Get IDs of all related items.
        
        Efficient query that doesn't load full objects.
        
        Returns:
            List of target model IDs
        """
        from pynext.db.relationships.junction import get_junction_factory
        
        factory = get_junction_factory()
        junction_class = factory.get_or_create(self._config)
        
        owner_id = getattr(self._owner, "id", None)
        if owner_id is None:
            return []
        
        rows = await junction_class.select().where(**{
            self._config.source_fk: owner_id,
        }).all()
        
        return [getattr(row, self._config.target_fk) for row in rows]
    
    # =========================================================================
    # Cache Management
    # =========================================================================
    
    def _set_cached_items(self, items: List[T]) -> None:
        """
        Set cached items from eager loading.
        
        Used internally by RelationshipLoader.
        """
        self._cached_items = list(items)
    
    def _clear_cache(self) -> None:
        """Clear cached items."""
        self._cached_items = None
    
    @property
    def is_loaded(self) -> bool:
        """Check if items have been loaded/cached."""
        return self._cached_items is not None
    
    # =========================================================================
    # Special Methods
    # =========================================================================
    
    def __repr__(self) -> str:
        """Return string representation."""
        owner_type = type(self._owner).__name__
        target_name = (
            self._target_model.__name__ 
            if hasattr(self._target_model, "__name__") 
            else str(self._target_model)
        )
        return f"AssociationProxy({owner_type} -> {target_name})"
    
    def __str__(self) -> str:
        """Return string representation of items."""
        # Don't use list(self) - build list manually to avoid __len__
        return str([item for item in self.__iter__()])
    
    def to_list(self) -> List[T]:
        """Convert to a regular Python list."""
        # Don't use list(self) - build list manually to avoid __len__
        return [item for item in self.__iter__()]
    
    # =========================================================================
    # Async Await Support
    # =========================================================================
    
    def __await__(self):
        """Allow awaiting the proxy to get all items."""
        return self.all().__await__()


class AssociationProxyDescriptor(Generic[T]):
    """
    Descriptor that creates AssociationProxy instances on access.
    
    Used internally by many_to_many relationships to provide
    transparent proxy access.
    
    Usage (internal):
        class Student(Table):
            _courses_proxy = AssociationProxyDescriptor(
                target_model=Course,
                config=junction_config,
            )
    """
    
    def __init__(
        self,
        target_model: Union[Type[T], str],
        config: "JunctionConfig",
        through_attr: Optional[str] = None,
        target_attr: Optional[str] = None,
    ):
        """
        Initialize the descriptor.
        
        Args:
            target_model: The related model class
            config: Junction table configuration
            through_attr: Attribute name for junction collection
            target_attr: Attribute name on junction for target
        """
        self._target_model = target_model
        self._config = config
        self._through_attr = through_attr
        self._target_attr = target_attr
        self._cache_attr: Optional[str] = None
    
    def __set_name__(self, owner: Type["Table"], name: str) -> None:
        """Called when descriptor is assigned to a class attribute."""
        self._cache_attr = f"_proxy_{name}"
    
    def __get__(
        self, 
        obj: Optional["Table"], 
        objtype: Type["Table"] = None,
    ) -> Union["AssociationProxyDescriptor[T]", AssociationProxy[T]]:
        """
        Get the association proxy for an instance.
        
        Returns the descriptor itself when accessed on the class.
        Returns an AssociationProxy when accessed on an instance.
        """
        if obj is None:
            return self
        
        # Check cache
        if self._cache_attr:
            cached = getattr(obj, self._cache_attr, None)
            if cached is not None:
                return cached
        
        # Create proxy
        proxy = AssociationProxy(
            owner=obj,
            target_model=self._target_model,
            config=self._config,
            through_attr=self._through_attr,
            target_attr=self._target_attr,
        )
        
        # Cache it
        if self._cache_attr:
            setattr(obj, self._cache_attr, proxy)
        
        return proxy

