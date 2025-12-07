"""
PyNext Dynamic Relationships.

Return a query builder instead of loading all results.

Design Philosophy:
- Perfect for large collections you don't want to load entirely
- Allows filtering, pagination, counting without loading
- Explicit: you get a query, not data
- AI-friendly: methods match Query API

Usage:
    class User(Table):
        # Don't load all audit logs - there could be thousands!
        audit_logs: List[AuditLog] = has_many(AuditLog, lazy="dynamic")
    
    user = await User.get(1)
    
    # user.audit_logs is a DynamicRelationship, not a list
    recent_logs = await user.audit_logs.filter(
        action="login"
    ).order_by("-created_at").limit(10)
    
    # Count without loading
    total = await user.audit_logs.count()
"""

from __future__ import annotations

from typing import (
    Any,
    Generic,
    List,
    Optional,
    Type,
    TypeVar,
    TYPE_CHECKING,
)

if TYPE_CHECKING:
    from pynext.db.table import Table
    from pynext.db.query import Query
    from pynext.db.relationships.filter import RelationshipFilter

T = TypeVar("T", bound="Table")


class DynamicRelationship(Generic[T]):
    """
    A query builder for relationships instead of loading results.
    
    When a relationship has lazy="dynamic", accessing it returns
    a DynamicRelationship instead of a list of models.
    
    This is ideal for:
        - Large collections (thousands of items)
        - Relationships that need filtering
        - Counting without loading
        - Paginated access
    
    Attributes:
        _owner: The parent model instance
        _model: The related model class
        _fk_field: Foreign key field name on related model
        _rel_name: Name of this relationship
    
    Example:
        class User(Table):
            audit_logs: List[AuditLog] = has_many(AuditLog, lazy="dynamic")
        
        user = await User.get(1)
        
        # Get recent logs (doesn't load all)
        recent = await user.audit_logs.order_by("-created_at").limit(10)
        
        # Count total
        total = await user.audit_logs.count()
        
        # Filter
        logins = await user.audit_logs.filter(action="login")
    """
    
    def __init__(
        self,
        owner: "Table",
        model: Type[T],
        fk_field: str,
        rel_name: str,
        filter: Optional["RelationshipFilter"] = None,
    ):
        """
        Initialize the dynamic relationship.
        
        Args:
            owner: Parent model instance (e.g., user)
            model: Related model class (e.g., AuditLog)
            fk_field: FK field name on related model (e.g., "user_id")
            rel_name: Name of this relationship (e.g., "audit_logs")
            filter: Optional RelationshipFilter to apply to base query
        """
        self._owner = owner
        self._model = model
        self._fk_field = fk_field
        self._rel_name = rel_name
        self._filter = filter
    
    def _base_query(self) -> "Query[T]":
        """
        Create the base query filtered by owner.
        
        Returns:
            Query filtered to only this owner's related items,
            with any relationship filter conditions applied.
        """
        owner_id = getattr(self._owner, "id", None)
        if owner_id is None:
            # Owner hasn't been saved - return empty query
            return self._model.select().where(id=-1)  # Will match nothing
        
        query = self._model.select().where(**{self._fk_field: owner_id})
        
        # Apply relationship filter if defined
        if self._filter is not None:
            query = self._filter.apply_to_query(query)
        
        return query
    
    def all(self) -> "Query[T]":
        """
        Get query for all related items.
        
        Returns:
            Query that will return all related items when awaited
        
        Example:
            all_logs = await user.audit_logs.all()
        """
        return self._base_query()
    
    def filter(self, **kwargs: Any) -> "Query[T]":
        """
        Add filters to the relationship query.
        
        Args:
            **kwargs: Field filters (same as Query.where)
            
        Returns:
            Filtered query
        
        Example:
            login_logs = await user.audit_logs.filter(action="login")
            recent_errors = await user.audit_logs.filter(level="error")
        """
        return self._base_query().where(**kwargs)
    
    def where(self, **kwargs: Any) -> "Query[T]":
        """
        Alias for filter() - add where conditions.
        
        Args:
            **kwargs: Field filters
            
        Returns:
            Filtered query
        """
        return self.filter(**kwargs)
    
    def where_in(self, **kwargs: List[Any]) -> "Query[T]":
        """
        Filter with IN clause.
        
        Args:
            **kwargs: Field to list of values
            
        Returns:
            Filtered query
            
        Example:
            logs = await user.audit_logs.where_in(action=["login", "logout"])
        """
        return self._base_query().where_in(**kwargs)
    
    def where_not(self, **kwargs: Any) -> "Query[T]":
        """
        Filter with NOT EQUAL.
        
        Args:
            **kwargs: Field to value
            
        Returns:
            Filtered query
        """
        return self._base_query().where_not(**kwargs)
    
    def order_by(self, *fields: str) -> "Query[T]":
        """
        Order the results.
        
        Use "-field" for descending order.
        
        Args:
            *fields: Field names to order by
            
        Returns:
            Ordered query
            
        Example:
            recent = await user.audit_logs.order_by("-created_at").limit(10)
        """
        return self._base_query().order_by(*fields)
    
    def limit(self, n: int) -> "Query[T]":
        """
        Limit number of results.
        
        Args:
            n: Maximum number of results
            
        Returns:
            Limited query
        """
        return self._base_query().limit(n)
    
    def offset(self, n: int) -> "Query[T]":
        """
        Skip first n results.
        
        Args:
            n: Number of results to skip
            
        Returns:
            Query with offset
        """
        return self._base_query().offset(n)
    
    async def count(self) -> int:
        """
        Count related items without loading them.
        
        Returns:
            Number of related items
            
        Example:
            total_logs = await user.audit_logs.count()
        """
        return await self._base_query().count()
    
    async def exists(self) -> bool:
        """
        Check if any related items exist.
        
        Returns:
            True if at least one related item exists
            
        Example:
            has_errors = await user.audit_logs.filter(level="error").exists()
        """
        return await self._base_query().exists()
    
    async def first(self) -> Optional[T]:
        """
        Get first related item.
        
        Returns:
            First item or None
            
        Example:
            latest = await user.audit_logs.order_by("-created_at").first()
        """
        return await self._base_query().first()
    
    async def one(self) -> T:
        """
        Get exactly one related item.
        
        Raises:
            NotFoundError: If no items found
            
        Returns:
            The single item
        """
        return await self._base_query().one()
    
    def __await__(self):
        """
        Allow awaiting directly to get all items.
        
        Example:
            logs = await user.audit_logs  # Same as await user.audit_logs.all()
        """
        return self.all().__await__()
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        owner_id = getattr(self._owner, "id", None)
        return (
            f"DynamicRelationship({self._model.__name__}, "
            f"owner_id={owner_id}, fk={self._fk_field})"
        )
    
    def __bool__(self) -> bool:
        """
        Dynamic relationships are always truthy.
        
        Use .count() or .exists() to check for items.
        """
        return True
    
    async def __aiter__(self):
        """
        Async iteration over items.
        
        Example:
            async for log in user.audit_logs:
                print(log.action)
        """
        items = await self.all()
        for item in items:
            yield item


class DynamicHasManyDescriptor(Generic[T]):
    """
    Descriptor that returns DynamicRelationship on access.
    
    This is used internally when lazy="dynamic" is set.
    """
    
    def __init__(
        self,
        rel_name: str,
        model: Type[T],
        foreign_key: str,
    ):
        self.rel_name = rel_name
        self._model_ref = model
        self.foreign_key = foreign_key
    
    @property
    def model(self) -> Type[T]:
        """Resolve string model reference."""
        if isinstance(self._model_ref, str):
            from pynext.db.table import _model_registry
            resolved = _model_registry.get(self._model_ref)
            if resolved:
                self._model_ref = resolved
            return resolved
        return self._model_ref
    
    def __get__(
        self,
        obj: Optional["Table"],
        objtype: Type["Table"] = None,
    ) -> DynamicRelationship[T]:
        """Return DynamicRelationship when accessed."""
        if obj is None:
            return self
        
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
        )
    
    def __set__(self, obj: "Table", value: Any) -> None:
        """Prevent setting dynamic relationships."""
        raise AttributeError(
            f"Cannot set dynamic relationship '{self.rel_name}'. "
            f"Dynamic relationships return a query builder, not a list. "
            f"Use the query methods to add/remove items."
        )


__all__ = [
    "DynamicRelationship",
    "DynamicHasManyDescriptor",
]

