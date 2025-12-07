"""
PyNext Dynamic Many-to-Many Query Builder.

Provides a query builder interface for lazy="dynamic" many-to-many relationships.
Instead of loading all related items, returns a query builder for on-demand access.

Design Philosophy:
- Never load more data than needed
- Full query builder power for filtering, ordering, pagination
- Efficient COUNT and EXISTS without loading
- AI-friendly: clear, predictable behavior

Usage:
    class Student(Table):
        # Could have thousands of courses over their lifetime
        all_courses: List[Course] = many_to_many(Course, lazy="dynamic")
    
    student = await Student.get(1)
    
    # student.all_courses is a query builder, not a list!
    recent = await student.all_courses.order_by("-enrolled_at").limit(10)
    count = await student.all_courses.count()  # Efficient COUNT(*)
    has_math = await student.all_courses.filter(name="Math").exists()
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


class DynamicManyToMany(Generic[T]):
    """
    Query builder for dynamic many-to-many relationships.
    
    Instead of loading all related items into memory, this provides
    a query builder interface for on-demand access.
    
    Attributes:
        _owner: The Table instance that owns this relationship
        _target_model: The related model class
        _config: Junction table configuration
    
    Usage:
        # student.courses returns DynamicManyToMany when lazy="dynamic"
        
        # Get all (returns query, must await)
        all_courses = await student.courses.all()
        
        # Filter
        active = await student.courses.filter(active=True)
        
        # Order and limit
        recent = await student.courses.order_by("-created_at").limit(10)
        
        # Pagination
        page_2 = await student.courses.offset(20).limit(10)
        
        # Count (efficient - doesn't load items)
        total = await student.courses.count()
        
        # Exists check
        has_courses = await student.courses.exists()
        
        # First item
        first = await student.courses.first()
    """
    
    def __init__(
        self,
        owner: "Table",
        target_model: Union[Type[T], str],
        config: "JunctionConfig",
    ):
        """
        Initialize dynamic M2M query builder.
        
        Args:
            owner: The Table instance that owns this relationship
            target_model: The related model class
            config: Junction table configuration
        """
        self._owner = owner
        self._target_model = target_model
        self._config = config
        
        # Query state
        self._filters: dict = {}
        self._filter_in: dict = {}
        self._filter_not: dict = {}
        self._order: List[str] = []
        self._limit_val: Optional[int] = None
        self._offset_val: Optional[int] = None
    
    @property
    def target_model(self) -> Type[T]:
        """Get the target model class (resolve string if needed)."""
        if isinstance(self._target_model, str):
            from pynext.db.table import _model_registry
            model = _model_registry.get(self._target_model)
            if model is None:
                table_name = self._target_model.lower() + "s"
                model = _model_registry.get(table_name)
            if model is None:
                raise ValueError(f"Could not resolve target model: {self._target_model}")
            self._target_model = model
        return self._target_model
    
    def _clone(self) -> "DynamicManyToMany[T]":
        """Create a copy of this query builder."""
        clone = DynamicManyToMany(
            owner=self._owner,
            target_model=self._target_model,
            config=self._config,
        )
        clone._filters = dict(self._filters)
        clone._filter_in = dict(self._filter_in)
        clone._filter_not = dict(self._filter_not)
        clone._order = list(self._order)
        clone._limit_val = self._limit_val
        clone._offset_val = self._offset_val
        return clone
    
    # =========================================================================
    # Query Building Methods (return new DynamicManyToMany)
    # =========================================================================
    
    def filter(self, **kwargs: Any) -> "DynamicManyToMany[T]":
        """
        Add filter conditions.
        
        Args:
            **kwargs: Filter conditions (field=value)
        
        Returns:
            New DynamicManyToMany with filters applied
        
        Example:
            active_courses = student.courses.filter(active=True)
        """
        clone = self._clone()
        clone._filters.update(kwargs)
        return clone
    
    def where(self, **kwargs: Any) -> "DynamicManyToMany[T]":
        """Alias for filter()."""
        return self.filter(**kwargs)
    
    def where_in(self, **kwargs: Any) -> "DynamicManyToMany[T]":
        """
        Add IN clause filter.
        
        Args:
            **kwargs: Field=list pairs for IN conditions
        
        Returns:
            New DynamicManyToMany with filter applied
        
        Example:
            specific = student.courses.where_in(id=[1, 2, 3])
        """
        clone = self._clone()
        clone._filter_in.update(kwargs)
        return clone
    
    def where_not(self, **kwargs: Any) -> "DynamicManyToMany[T]":
        """
        Add NOT filter.
        
        Args:
            **kwargs: Filter conditions to negate
        
        Returns:
            New DynamicManyToMany with filter applied
        
        Example:
            not_archived = student.courses.where_not(archived=True)
        """
        clone = self._clone()
        clone._filter_not.update(kwargs)
        return clone
    
    def order_by(self, *fields: str) -> "DynamicManyToMany[T]":
        """
        Add ordering.
        
        Args:
            *fields: Field names (prefix with - for descending)
        
        Returns:
            New DynamicManyToMany with ordering applied
        
        Example:
            recent = student.courses.order_by("-created_at", "name")
        """
        clone = self._clone()
        clone._order.extend(fields)
        return clone
    
    def limit(self, n: int) -> "DynamicManyToMany[T]":
        """
        Limit number of results.
        
        Args:
            n: Maximum number of items
        
        Returns:
            New DynamicManyToMany with limit applied
        
        Example:
            top_10 = student.courses.limit(10)
        """
        clone = self._clone()
        clone._limit_val = n
        return clone
    
    def offset(self, n: int) -> "DynamicManyToMany[T]":
        """
        Skip results.
        
        Args:
            n: Number of items to skip
        
        Returns:
            New DynamicManyToMany with offset applied
        
        Example:
            page_2 = student.courses.offset(20).limit(10)
        """
        clone = self._clone()
        clone._offset_val = n
        return clone
    
    # =========================================================================
    # Async Execution Methods
    # =========================================================================
    
    async def _get_target_ids(self) -> List[int]:
        """Get target IDs from junction table."""
        from pynext.db.relationships.junction import get_junction_factory
        
        factory = get_junction_factory()
        junction_class = factory.get_or_create(self._config)
        
        owner_id = getattr(self._owner, "id", None)
        if owner_id is None:
            return []
        
        # Query junction table
        rows = await junction_class.select().where(**{
            self._config.source_fk: owner_id,
        }).all()
        
        return [getattr(row, self._config.target_fk) for row in rows]
    
    async def _build_query(self) -> "Query[T]":
        """Build the query for target model."""
        target_ids = await self._get_target_ids()
        
        if not target_ids:
            # Return empty query result
            query = self.target_model.select().where_in(id=[])
        else:
            query = self.target_model.select().where_in(id=target_ids)
        
        # Apply filters
        if self._filters:
            query = query.where(**self._filters)
        
        if self._filter_in:
            for field, values in self._filter_in.items():
                query = query.where_in(**{field: values})
        
        if self._filter_not:
            query = query.where_not(**self._filter_not)
        
        # Apply ordering
        if self._order:
            query = query.order_by(*self._order)
        
        # Apply limit/offset
        if self._limit_val is not None:
            query = query.limit(self._limit_val)
        
        if self._offset_val is not None:
            query = query.offset(self._offset_val)
        
        return query
    
    async def all(self) -> List[T]:
        """
        Execute query and return all results.
        
        Returns:
            List of related model instances
        
        Example:
            all_courses = await student.courses.all()
        """
        query = await self._build_query()
        return await query.all()
    
    async def count(self) -> int:
        """
        Count related items efficiently.
        
        Uses COUNT on junction table for efficiency when no filters.
        
        Returns:
            Number of related items
        
        Example:
            total = await student.courses.count()
        """
        # If no filters, count directly on junction
        if not self._filters and not self._filter_in and not self._filter_not:
            from pynext.db.relationships.junction import get_junction_factory
            
            factory = get_junction_factory()
            junction_class = factory.get_or_create(self._config)
            
            owner_id = getattr(self._owner, "id", None)
            if owner_id is None:
                return 0
            
            return await junction_class.select().where(**{
                self._config.source_fk: owner_id,
            }).count()
        
        # With filters, need to query target table
        query = await self._build_query()
        return await query.count()
    
    async def exists(self) -> bool:
        """
        Check if any related items exist.
        
        Returns:
            True if at least one item exists
        
        Example:
            has_courses = await student.courses.exists()
        """
        # Optimize: just check if any junction rows exist
        if not self._filters and not self._filter_in and not self._filter_not:
            count = await self.count()
            return count > 0
        
        query = await self._build_query()
        return await query.exists()
    
    async def first(self) -> Optional[T]:
        """
        Get the first result.
        
        Returns:
            First item or None if empty
        
        Example:
            first_course = await student.courses.first()
        """
        query = await self._build_query()
        return await query.first()
    
    async def one(self) -> T:
        """
        Get exactly one result.
        
        Raises:
            NoResultError: If no result found
            MultipleResultsError: If more than one result
        
        Returns:
            The single item
        """
        query = await self._build_query()
        return await query.one()
    
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
        return f"DynamicManyToMany({owner_type} -> {target_name})"
    
    def __bool__(self) -> bool:
        """Always returns True (query builder is truthy)."""
        return True
    
    def __await__(self):
        """Allow awaiting to get all items."""
        return self.all().__await__()
    
    async def __aiter__(self):
        """Async iteration over items."""
        items = await self.all()
        for item in items:
            yield item

