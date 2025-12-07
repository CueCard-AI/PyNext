"""
PyNext Database Query Builder.

Chainable, lazy-evaluated query builder.
Nothing executes until you await the query.

Design: Build queries naturally, execute when ready.
"""

from __future__ import annotations

from copy import deepcopy
from typing import (
    Any,
    Awaitable,
    Dict,
    Generic,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    TYPE_CHECKING,
    Union,
)

if TYPE_CHECKING:
    from pynext.db.table import Table
    from pynext.db.adapters.base import Adapter
    from pynext.db.fields import FieldInfo

T = TypeVar("T", bound="Table")


class Query(Generic[T]):
    """
    Chainable query builder for database operations.
    
    Builds a query step by step, then executes when awaited.
    
    Usage:
        # Build query (nothing executes)
        query = User.select().where(role="admin").order_by("-created_at").limit(10)
        
        # Execute when awaited
        users = await query
        
    Chainable methods:
        .where(field=value)      - Equality filter
        .where_not(field=value)  - Not equal filter
        .where_in(field=[...])   - IN filter
        .where_like(field="%...%") - LIKE filter
        .where_gt(field=value)   - Greater than
        .where_gte(field=value)  - Greater than or equal
        .where_lt(field=value)   - Less than
        .where_lte(field=value)  - Less than or equal
        .where_null(field)       - IS NULL
        .where_not_null(field)   - IS NOT NULL
        .order_by(field)         - Order ascending
        .order_by("-field")      - Order descending
        .limit(n)                - Limit results
        .offset(n)               - Skip results
        .with_related("rel")     - Eager load relation
    """
    
    def __init__(
        self,
        model: Type[T],
        adapter: "Adapter",
        fields: Dict[str, "FieldInfo"],
    ):
        self._model = model
        self._adapter = adapter
        self._fields = fields
        self._table = model.__table_name__
        
        # Query state
        self._where: Dict[str, Any] = {}
        self._where_not: Dict[str, Any] = {}
        self._where_in: Dict[str, List[Any]] = {}
        self._where_like: Dict[str, str] = {}
        self._where_gt: Dict[str, Any] = {}
        self._where_gte: Dict[str, Any] = {}
        self._where_lt: Dict[str, Any] = {}
        self._where_lte: Dict[str, Any] = {}
        self._where_null: List[str] = []
        self._where_not_null: List[str] = []
        self._order_by: List[str] = []
        self._limit: Optional[int] = None
        self._offset: Optional[int] = None
        self._with_related: List[str] = []
        self._select_columns: Optional[List[str]] = None
        self._load_options: List[Any] = []  # LoadOption objects for eager loading
    
    def _clone(self) -> "Query[T]":
        """Create a copy of this query."""
        clone = Query(self._model, self._adapter, self._fields)
        clone._where = deepcopy(self._where)
        clone._where_not = deepcopy(self._where_not)
        clone._where_in = deepcopy(self._where_in)
        clone._where_like = deepcopy(self._where_like)
        clone._where_gt = deepcopy(self._where_gt)
        clone._where_gte = deepcopy(self._where_gte)
        clone._where_lt = deepcopy(self._where_lt)
        clone._where_lte = deepcopy(self._where_lte)
        clone._where_null = list(self._where_null)
        clone._where_not_null = list(self._where_not_null)
        clone._order_by = list(self._order_by)
        clone._limit = self._limit
        clone._offset = self._offset
        clone._with_related = list(self._with_related)
        clone._select_columns = list(self._select_columns) if self._select_columns else None
        clone._load_options = list(self._load_options)
        return clone
    
    # Filter methods
    
    def where(self, **kwargs: Any) -> "Query[T]":
        """
        Add equality filter(s).
        
        Examples:
            .where(role="admin")
            .where(role="admin", active=True)
        """
        clone = self._clone()
        clone._where.update(kwargs)
        return clone
    
    def where_not(self, **kwargs: Any) -> "Query[T]":
        """
        Add not-equal filter(s).
        
        Examples:
            .where_not(role="admin")
        """
        clone = self._clone()
        clone._where_not.update(kwargs)
        return clone
    
    def where_in(self, **kwargs: List[Any]) -> "Query[T]":
        """
        Add IN filter(s).
        
        Examples:
            .where_in(id=[1, 2, 3])
            .where_in(role=["admin", "moderator"])
        """
        clone = self._clone()
        clone._where_in.update(kwargs)
        return clone
    
    def where_like(self, **kwargs: str) -> "Query[T]":
        """
        Add LIKE filter(s).
        
        Examples:
            .where_like(name="%john%")
            .where_like(email="%@gmail.com")
        """
        clone = self._clone()
        clone._where_like.update(kwargs)
        return clone
    
    def where_gt(self, **kwargs: Any) -> "Query[T]":
        """
        Add greater-than filter(s).
        
        Examples:
            .where_gt(age=18)
            .where_gt(created_at=yesterday)
        """
        clone = self._clone()
        clone._where_gt.update(kwargs)
        return clone
    
    def where_gte(self, **kwargs: Any) -> "Query[T]":
        """
        Add greater-than-or-equal filter(s).
        
        Examples:
            .where_gte(age=18)
        """
        clone = self._clone()
        clone._where_gte.update(kwargs)
        return clone
    
    def where_lt(self, **kwargs: Any) -> "Query[T]":
        """
        Add less-than filter(s).
        
        Examples:
            .where_lt(age=65)
        """
        clone = self._clone()
        clone._where_lt.update(kwargs)
        return clone
    
    def where_lte(self, **kwargs: Any) -> "Query[T]":
        """
        Add less-than-or-equal filter(s).
        
        Examples:
            .where_lte(age=65)
        """
        clone = self._clone()
        clone._where_lte.update(kwargs)
        return clone
    
    def where_null(self, *fields: str) -> "Query[T]":
        """
        Add IS NULL filter(s).
        
        Examples:
            .where_null("deleted_at")
        """
        clone = self._clone()
        clone._where_null.extend(fields)
        return clone
    
    def where_not_null(self, *fields: str) -> "Query[T]":
        """
        Add IS NOT NULL filter(s).
        
        Examples:
            .where_not_null("email")
        """
        clone = self._clone()
        clone._where_not_null.extend(fields)
        return clone
    
    # Ordering
    
    def order_by(self, *fields: str) -> "Query[T]":
        """
        Add ordering.
        
        Use "-field" for descending order.
        
        Examples:
            .order_by("name")           # ASC
            .order_by("-created_at")    # DESC
            .order_by("role", "-name")  # Multiple
        """
        clone = self._clone()
        clone._order_by.extend(fields)
        return clone
    
    # Pagination
    
    def limit(self, n: int) -> "Query[T]":
        """
        Limit number of results.
        
        Examples:
            .limit(10)
        """
        clone = self._clone()
        clone._limit = n
        return clone
    
    def offset(self, n: int) -> "Query[T]":
        """
        Skip n results.
        
        Examples:
            .offset(20)
        """
        clone = self._clone()
        clone._offset = n
        return clone
    
    def page(self, page: int, per_page: int = 20) -> "Query[T]":
        """
        Paginate results.
        
        Examples:
            .page(1, 20)  # First 20 results
            .page(2, 20)  # Results 21-40
        """
        return self.limit(per_page).offset((page - 1) * per_page)
    
    # Relationships
    
    def with_related(self, *relations: str) -> "Query[T]":
        """
        Eager load related models.
        
        Use "__" for nested relations.
        
        Examples:
            .with_related("author")
            .with_related("author", "comments")
            .with_related("author__profile")
        
        Note: Consider using .options() with loading functions for more control:
            .options(selectinload("author"), joinedload("profile"))
        """
        clone = self._clone()
        clone._with_related.extend(relations)
        return clone
    
    def options(self, *load_options) -> "Query[T]":
        """
        Apply loading options to control how relationships are loaded.
        
        This provides fine-grained control over relationship loading strategies,
        overriding any model-level defaults.
        
        Args:
            *load_options: LoadOption objects from joinedload(), selectinload(), etc.
        
        Examples:
            # Basic eager loading
            users = await User.select().options(
                selectinload("posts"),      # Use SELECT IN for posts
                joinedload("profile"),      # Use JOIN for profile
            )
            
            # Nested loading
            users = await User.select().options(
                selectinload("posts").joinedload("author"),
            )
            
            # Prevent N+1 errors
            users = await User.select().options(
                raiseload("audit_logs"),  # Will raise if accessed
            )
        
        Returns:
            Query with loading options applied
        """
        clone = self._clone()
        clone._load_options.extend(load_options)
        return clone
    
    # Column selection
    
    def only(self, *columns: str) -> "Query[T]":
        """
        Select only specific columns.
        
        Examples:
            .only("id", "name", "email")
        """
        clone = self._clone()
        clone._select_columns = list(columns)
        return clone
    
    # Execution methods
    
    async def all(self) -> List[T]:
        """
        Execute query and return all matching rows.
        
        Examples:
            users = await User.select().where(role="admin").all()
            users = await User.select().options(selectinload("posts")).all()
        """
        rows = await self._adapter.select(self._table, self, self._fields)
        instances = [self._model._from_row(row) for row in rows]
        
        # Apply loading options (new API)
        if self._load_options:
            await self._apply_load_options(instances)
        
        # Load related models (legacy API)
        if self._with_related:
            await self._load_related(instances)
        
        return instances
    
    async def _apply_load_options(self, instances: List[T]) -> None:
        """
        Apply loading options to instances.
        
        Uses RelationshipLoader to load relationships based on the
        specified strategies.
        """
        if not instances or not self._load_options:
            return
        
        from pynext.db.relationships.loading import get_loader
        
        loader = get_loader(self._adapter)
        await loader.load(instances, self._load_options, self._model)
    
    async def first(self) -> Optional[T]:
        """
        Execute query and return first matching row.
        
        Examples:
            user = await User.select().where(email="john@example.com").first()
        """
        clone = self.limit(1)
        results = await clone.all()
        return results[0] if results else None
    
    async def one(self) -> T:
        """
        Execute query and return exactly one row.
        
        Raises NotFoundError if no rows match.
        
        Examples:
            user = await User.select().where(id=1).one()
        """
        from pynext.db.exceptions import NotFoundError
        
        result = await self.first()
        if result is None:
            raise NotFoundError(self._table)
        return result
    
    async def first_or_raise(self) -> T:
        """
        Execute query and return first matching row.
        
        Raises NotFoundError if no rows match.
        Alias for one() for more explicit naming.
        
        Examples:
            user = await User.select().where(role="admin").first_or_raise()
        """
        return await self.one()
    
    async def last(self) -> Optional[T]:
        """
        Execute query and return last matching row.
        
        Requires an order_by clause to be meaningful.
        
        Examples:
            latest = await User.select().order_by("-created_at").last()
        """
        # Get all results and return last
        results = await self.all()
        return results[-1] if results else None
    
    async def values(self, *fields: str) -> List[Dict[str, Any]]:
        """
        Return only specified fields as dicts.
        
        More efficient than loading full model instances.
        
        Examples:
            emails = await User.select().values("id", "email")
            # Returns: [{"id": 1, "email": "a@test.com"}, ...]
        """
        rows = await self._adapter.select(self._table, self, self._fields)
        return [{f: row.get(f) for f in fields} for row in rows]
    
    async def values_list(self, *fields: str, flat: bool = False) -> List[Any]:
        """
        Return only specified fields as tuples or flat list.
        
        Examples:
            # Get tuples
            data = await User.select().values_list("id", "email")
            # Returns: [(1, "a@test.com"), (2, "b@test.com")]
            
            # Get flat list (single field)
            emails = await User.select().values_list("email", flat=True)
            # Returns: ["a@test.com", "b@test.com"]
        """
        rows = await self._adapter.select(self._table, self, self._fields)
        
        if flat and len(fields) == 1:
            return [row.get(fields[0]) for row in rows]
        
        return [tuple(row.get(f) for f in fields) for row in rows]
    
    async def distinct(self, field: str) -> List[Any]:
        """
        Return distinct values for a field.
        
        Examples:
            roles = await User.select().distinct("role")
            # Returns: ["admin", "user", "guest"]
        """
        rows = await self._adapter.select(self._table, self, self._fields)
        seen = set()
        result = []
        for row in rows:
            value = row.get(field)
            if value not in seen:
                seen.add(value)
                result.append(value)
        return result
    
    async def sum(self, field: str) -> float:
        """
        Sum a numeric field.
        
        Examples:
            total_age = await User.select().sum("age")
        """
        rows = await self._adapter.select(self._table, self, self._fields)
        return sum(row.get(field, 0) or 0 for row in rows)
    
    async def avg(self, field: str) -> Optional[float]:
        """
        Average a numeric field.
        
        Examples:
            avg_age = await User.select().avg("age")
        """
        rows = await self._adapter.select(self._table, self, self._fields)
        if not rows:
            return None
        values = [row.get(field, 0) or 0 for row in rows]
        return sum(values) / len(values)
    
    async def min(self, field: str) -> Optional[Any]:
        """
        Get minimum value of a field.
        
        Examples:
            min_age = await User.select().min("age")
        """
        rows = await self._adapter.select(self._table, self, self._fields)
        if not rows:
            return None
        values = [row.get(field) for row in rows if row.get(field) is not None]
        return min(values) if values else None
    
    async def max(self, field: str) -> Optional[Any]:
        """
        Get maximum value of a field.
        
        Examples:
            max_age = await User.select().max("age")
        """
        rows = await self._adapter.select(self._table, self, self._fields)
        if not rows:
            return None
        values = [row.get(field) for row in rows if row.get(field) is not None]
        return max(values) if values else None
    
    async def count(self) -> int:
        """
        Count matching rows.
        
        Examples:
            admin_count = await User.select().where(role="admin").count()
        """
        return await self._adapter.count(self._table, self)
    
    async def exists(self) -> bool:
        """
        Check if any rows match.
        
        Examples:
            has_admins = await User.select().where(role="admin").exists()
        """
        return await self._adapter.exists(self._table, self)
    
    async def delete(self) -> int:
        """
        Delete all matching rows.
        
        Returns the number of deleted rows.
        
        Examples:
            deleted = await User.select().where(active=False).delete()
        """
        # Get all matching IDs first
        rows = await self._adapter.select(self._table, self, self._fields)
        count = 0
        for row in rows:
            if await self._adapter.delete(self._table, row["id"]):
                count += 1
        return count
    
    async def update(self, **data: Any) -> int:
        """
        Update all matching rows.
        
        Returns the number of updated rows.
        
        Examples:
            updated = await User.select().where(role="user").update(role="member")
        """
        # Get all matching IDs first
        rows = await self._adapter.select(self._table, self, self._fields)
        count = 0
        for row in rows:
            await self._adapter.update(self._table, row["id"], data, self._fields)
            count += 1
        return count
    
    # Magic methods
    
    def __await__(self):
        """Allow awaiting the query directly."""
        return self.all().__await__()
    
    async def __aiter__(self):
        """Allow async iteration over results."""
        results = await self.all()
        for item in results:
            yield item
    
    # Private methods
    
    async def _load_related(self, instances: List[T]) -> None:
        """Load related models for instances."""
        if not instances:
            return
        
        for relation in self._with_related:
            await self._load_relation(instances, relation)
    
    async def _load_relation(self, instances: List[T], relation: str) -> None:
        """Load a single relation for instances."""
        # Handle nested relations (e.g., "author__profile")
        parts = relation.split("__")
        rel_name = parts[0]
        nested = "__".join(parts[1:]) if len(parts) > 1 else None
        
        # Get relationship info from model
        relationships = getattr(self._model, "_relationships", {})
        rel_info = relationships.get(rel_name)
        
        if rel_info is None:
            from pynext.db.exceptions import RelationshipError
            raise RelationshipError(f"Unknown relation: {rel_name}", relation=rel_name, model=self._model.__name__)
        
        rel_type = rel_info["type"]
        related_model = rel_info["model"]
        foreign_key = rel_info.get("foreign_key")
        
        if rel_type == "belongs_to":
            # e.g., post.author - load by author_id
            fk_field = foreign_key or f"{rel_name}_id"
            fk_values = [getattr(inst, fk_field) for inst in instances if getattr(inst, fk_field, None) is not None]
            
            if fk_values:
                # Load related models
                related_query = related_model.select().where_in(id=fk_values)
                if nested:
                    related_query = related_query.with_related(nested)
                related_instances = await related_query
                
                # Map by id
                related_map = {inst.id: inst for inst in related_instances}
                
                # Assign to instances
                for inst in instances:
                    fk_value = getattr(inst, fk_field, None)
                    if fk_value is not None:
                        setattr(inst, rel_name, related_map.get(fk_value))
        
        elif rel_type == "has_many":
            # e.g., user.posts - load by user_id
            fk_field = foreign_key or f"{self._model.__table_name__[:-1]}_id"  # users -> user_id
            ids = [inst.id for inst in instances]
            
            if ids:
                # Load related models
                related_query = related_model.select().where_in(**{fk_field: ids})
                if nested:
                    related_query = related_query.with_related(nested)
                related_instances = await related_query
                
                # Group by foreign key
                related_map: Dict[int, List] = {}
                for related in related_instances:
                    fk_value = getattr(related, fk_field, None)
                    if fk_value is not None:
                        if fk_value not in related_map:
                            related_map[fk_value] = []
                        related_map[fk_value].append(related)
                
                # Assign to instances
                for inst in instances:
                    setattr(inst, rel_name, related_map.get(inst.id, []))
        
        elif rel_type == "has_one":
            # e.g., user.profile - load single by user_id
            fk_field = foreign_key or f"{self._model.__table_name__[:-1]}_id"
            ids = [inst.id for inst in instances]
            
            if ids:
                related_query = related_model.select().where_in(**{fk_field: ids})
                if nested:
                    related_query = related_query.with_related(nested)
                related_instances = await related_query
                
                # Map by foreign key
                related_map = {getattr(inst, fk_field): inst for inst in related_instances}
                
                # Assign to instances
                for inst in instances:
                    setattr(inst, rel_name, related_map.get(inst.id))
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        parts = [f"Query({self._model.__name__})"]
        
        if self._where:
            parts.append(f".where({self._where})")
        if self._where_not:
            parts.append(f".where_not({self._where_not})")
        if self._where_in:
            parts.append(f".where_in({self._where_in})")
        if self._order_by:
            parts.append(f".order_by({self._order_by})")
        if self._limit:
            parts.append(f".limit({self._limit})")
        if self._offset:
            parts.append(f".offset({self._offset})")
        if self._with_related:
            parts.append(f".with_related({self._with_related})")
        
        return "".join(parts)

