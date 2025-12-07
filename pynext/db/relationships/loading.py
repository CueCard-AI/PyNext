"""
PyNext Database Loading Strategies.

Control how and when related models are loaded with simple, explicit strategies.

Design Philosophy:
- One parameter (`lazy=`) controls everything at the relationship level
- Query-level override with `.options()` takes precedence
- N+1 prevention with `lazy="raise"` catches accidental lazy loads
- AI-friendly: explicit strategy names, clear execution paths

Strategies:
    select   - Lazy load on access (default, causes N+1 if not careful)
    joined   - LEFT JOIN in same query (best for single objects)
    subquery - Subquery with IN clause (best for collections with deep nesting)
    selectin - SELECT WHERE id IN (...) (best for batches)
    raise    - Raise error on access (prevents N+1 in production)
    dynamic  - Return query builder (best for large collections)

Usage:
    # At relationship definition
    class User(Table):
        posts: List[Post] = has_many(Post, lazy="selectin")
        profile: Profile = has_one(Profile, lazy="joined")
    
    # At query time (overrides relationship default)
    users = await User.select().options(
        joinedload("profile"),
        selectinload("posts"),
    )
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any,
    Dict,
    Generic,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    TYPE_CHECKING,
    Union,
)

if TYPE_CHECKING:
    from pynext.db.table import Table
    from pynext.db.query import Query
    from pynext.db.adapters.base import Adapter


T = TypeVar("T", bound="Table")


class LoadStrategy(Enum):
    """
    Loading strategies for relationships.
    
    Each strategy has different performance characteristics:
    
    SELECT (default):
        - Loads on first access
        - Simple but causes N+1 queries
        - Use for rarely accessed relations
    
    JOINED:
        - Uses LEFT JOIN in same query
        - Single query, but can return duplicate rows
        - Best for belongs_to and has_one
    
    SUBQUERY:
        - Uses subquery to get IDs, then loads
        - Good for collections with deep nesting
        - Avoids cartesian product issues
    
    SELECTIN:
        - Collects IDs, then SELECT WHERE id IN (...)
        - Best for batches of objects
        - Most common eager loading choice
    
    RAISE:
        - Raises LazyLoadError on access
        - Use to prevent N+1 in production
        - Forces explicit loading
    
    DYNAMIC:
        - Returns query builder instead of results
        - Best for large collections needing filtering
        - Doesn't load all at once
    """
    SELECT = "select"
    JOINED = "joined"
    SUBQUERY = "subquery"
    SELECTIN = "selectin"
    RAISE = "raise"
    DYNAMIC = "dynamic"
    
    @classmethod
    def from_string(cls, value: str) -> "LoadStrategy":
        """
        Convert string to LoadStrategy.
        
        Args:
            value: Strategy name (case-insensitive)
            
        Returns:
            LoadStrategy enum value
            
        Raises:
            ValueError: If invalid strategy name
        """
        value_lower = value.lower()
        for strategy in cls:
            if strategy.value == value_lower:
                return strategy
        
        valid = ", ".join(s.value for s in cls)
        raise ValueError(
            f"Invalid loading strategy: '{value}'. "
            f"Valid strategies: {valid}"
        )


class LazyLoadError(Exception):
    """
    Raised when accessing a relationship with lazy="raise".
    
    This error indicates an attempt to lazy load a relationship
    that was configured to prevent N+1 queries.
    
    To fix:
        1. Use .options(selectinload("relation")) in your query
        2. Use .with_related("relation") to eager load
        3. Change the relationship's lazy strategy
    
    Example:
        class User(Table):
            posts: List[Post] = has_many(Post, lazy="raise")
        
        user = await User.get(1)
        user.posts  # Raises LazyLoadError!
        
        # Fix: eager load
        user = await User.select().options(selectinload("posts")).where(id=1).first()
        user.posts  # Works!
    """
    
    def __init__(
        self,
        relationship: str,
        model: Optional[str] = None,
        message: Optional[str] = None,
    ):
        self.relationship = relationship
        self.model = model
        
        if message:
            super().__init__(message)
        else:
            model_part = f" on {model}" if model else ""
            super().__init__(
                f"Accessing '{relationship}'{model_part} would trigger a lazy load. "
                f"This relationship has lazy='raise' to prevent N+1 queries. "
                f"Use .options(selectinload('{relationship}')) or "
                f".with_related('{relationship}') to eager load."
            )


@dataclass
class LoadOption:
    """
    Configuration for a loading option.
    
    LoadOptions specify how a relationship should be loaded at query time.
    They can be nested to load relationships of relationships.
    
    Attributes:
        relationship: Name of the relationship (e.g., "posts" or "author")
        strategy: How to load (joined, selectin, subquery, etc.)
        inner_options: Nested loading options for related model's relationships
    
    Example:
        # Simple option
        opt = LoadOption("posts", LoadStrategy.SELECTIN)
        
        # Nested options
        opt = LoadOption("posts", LoadStrategy.SELECTIN, [
            LoadOption("author", LoadStrategy.JOINED),
            LoadOption("comments", LoadStrategy.SELECTIN),
        ])
    """
    relationship: str
    strategy: LoadStrategy
    inner_options: List["LoadOption"] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate the load option."""
        if not self.relationship:
            raise ValueError("Relationship name cannot be empty")
        
        # Convert string strategy to enum if needed
        if isinstance(self.strategy, str):
            self.strategy = LoadStrategy.from_string(self.strategy)
    
    def add_inner(self, option: "LoadOption") -> "LoadOption":
        """
        Add a nested loading option.
        
        Returns self for chaining:
            selectinload("posts").add_inner(joinedload("author"))
        
        Args:
            option: The inner option to add
            
        Returns:
            Self for chaining
        """
        self.inner_options.append(option)
        return self
    
    def joinedload(self, relationship: str) -> "LoadOption":
        """
        Chain a joined load for a nested relationship.
        
        Example:
            selectinload("posts").joinedload("author")
            # Loads posts with SELECT IN, then joins author
        """
        inner = LoadOption(relationship, LoadStrategy.JOINED)
        self.inner_options.append(inner)
        return inner
    
    def selectinload(self, relationship: str) -> "LoadOption":
        """
        Chain a selectin load for a nested relationship.
        
        Example:
            joinedload("author").selectinload("posts")
        """
        inner = LoadOption(relationship, LoadStrategy.SELECTIN)
        self.inner_options.append(inner)
        return inner
    
    def subqueryload(self, relationship: str) -> "LoadOption":
        """
        Chain a subquery load for a nested relationship.
        
        Example:
            selectinload("posts").subqueryload("comments")
        """
        inner = LoadOption(relationship, LoadStrategy.SUBQUERY)
        self.inner_options.append(inner)
        return inner
    
    def raiseload(self, relationship: str) -> "LoadOption":
        """
        Chain a raise load for a nested relationship.
        
        Example:
            selectinload("posts").raiseload("audit_logs")
        """
        inner = LoadOption(relationship, LoadStrategy.RAISE)
        self.inner_options.append(inner)
        return inner
    
    def noload(self, relationship: str) -> "LoadOption":
        """
        Chain a noload for a nested relationship.
        
        Example:
            selectinload("posts").noload("metadata")
        """
        inner = LoadOption(relationship, LoadStrategy.SELECT)
        self.inner_options.append(inner)
        return inner
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for debugging/serialization."""
        return {
            "relationship": self.relationship,
            "strategy": self.strategy.value,
            "inner_options": [opt.to_dict() for opt in self.inner_options],
        }
    
    def __repr__(self) -> str:
        inner = f", inner={self.inner_options}" if self.inner_options else ""
        return f"LoadOption({self.relationship!r}, {self.strategy.value!r}{inner})"


class RelationshipLoader:
    """
    Executes loading strategies for relationships.
    
    This class handles the actual loading of related models based on
    the configured strategy. It's used internally by Query.
    
    Design:
        - Each strategy has its own method for clarity
        - Methods are async to support database operations
        - Batch operations minimize queries
        - Nested loading is recursive
    
    Usage (internal):
        loader = RelationshipLoader(adapter)
        await loader.load(instances, options, model)
    """
    
    def __init__(self, adapter: "Adapter"):
        """
        Initialize the loader.
        
        Args:
            adapter: Database adapter for executing queries
        """
        self._adapter = adapter
    
    async def load(
        self,
        instances: List["Table"],
        options: List[LoadOption],
        model: Type["Table"],
    ) -> None:
        """
        Load relationships for instances based on options.
        
        Args:
            instances: Model instances to load relationships for
            options: Loading options specifying what and how to load
            model: The model class of the instances
        """
        if not instances or not options:
            return
        
        for option in options:
            await self._load_option(instances, option, model)
    
    async def _load_option(
        self,
        instances: List["Table"],
        option: LoadOption,
        model: Type["Table"],
    ) -> None:
        """Load a single option for instances."""
        strategy = option.strategy
        relationship = option.relationship
        
        # Get relationship info
        relationships = getattr(model, "_relationships", {})
        rel_info = relationships.get(relationship)
        
        if rel_info is None:
            from pynext.db.exceptions import RelationshipError
            raise RelationshipError(
                f"Unknown relationship: {relationship}",
                relation=relationship,
                model=model.__name__,
            )
        
        # Dispatch to appropriate strategy
        if strategy == LoadStrategy.JOINED:
            # Joined loading is handled at query build time
            # This is called for post-processing only
            pass
        elif strategy == LoadStrategy.SELECTIN:
            await self._load_selectin(instances, option, rel_info, model)
        elif strategy == LoadStrategy.SUBQUERY:
            await self._load_subquery(instances, option, rel_info, model)
        elif strategy == LoadStrategy.RAISE:
            # Mark instances to raise on access
            self._mark_raise(instances, relationship)
        elif strategy == LoadStrategy.SELECT:
            # Default lazy loading - nothing to do here
            pass
        elif strategy == LoadStrategy.DYNAMIC:
            # Dynamic returns query builder - nothing to preload
            pass
    
    async def _load_selectin(
        self,
        instances: List["Table"],
        option: LoadOption,
        rel_info: Dict[str, Any],
        model: Type["Table"],
    ) -> None:
        """
        Load relationship using SELECT WHERE id IN (...).
        
        This is the most common eager loading strategy:
        1. Collect all IDs from instances
        2. Execute single SELECT with IN clause
        3. Map results back to instances
        
        Args:
            instances: Parent instances
            option: Load option with nested options
            rel_info: Relationship metadata
            model: Parent model class
        """
        rel_type = rel_info["type"]
        related_model = rel_info["model"]
        foreign_key = rel_info.get("foreign_key")
        relationship = option.relationship
        
        # Resolve string model reference
        if isinstance(related_model, str):
            from pynext.db.table import _model_registry
            related_model = _model_registry.get(related_model)
            if related_model is None:
                return
        
        if rel_type == "belongs_to":
            await self._load_selectin_belongs_to(
                instances, relationship, related_model, foreign_key, option
            )
        elif rel_type == "has_many":
            await self._load_selectin_has_many(
                instances, relationship, related_model, foreign_key, model, option
            )
        elif rel_type == "has_one":
            await self._load_selectin_has_one(
                instances, relationship, related_model, foreign_key, model, option
            )
    
    async def _load_selectin_belongs_to(
        self,
        instances: List["Table"],
        relationship: str,
        related_model: Type["Table"],
        foreign_key: Optional[str],
        option: LoadOption,
    ) -> None:
        """Load belongs_to with SELECT IN."""
        # Determine FK field
        fk_field = foreign_key or f"{relationship}_id"
        
        # Collect unique FK values
        fk_values: Set[int] = set()
        for inst in instances:
            fk_value = getattr(inst, fk_field, None)
            if fk_value is not None:
                fk_values.add(fk_value)
        
        if not fk_values:
            # No FKs to load - set all to None
            for inst in instances:
                setattr(inst, f"_cached_{relationship}", None)
            return
        
        # Load related models
        related_query = related_model.select().where_in(id=list(fk_values))
        related_instances = await related_query
        
        # Load nested relationships if specified
        if option.inner_options and related_instances:
            await self.load(related_instances, option.inner_options, related_model)
        
        # Map by id
        related_map = {inst.id: inst for inst in related_instances}
        
        # Assign to instances
        for inst in instances:
            fk_value = getattr(inst, fk_field, None)
            related = related_map.get(fk_value) if fk_value else None
            setattr(inst, f"_cached_{relationship}", related)
    
    async def _load_selectin_has_many(
        self,
        instances: List["Table"],
        relationship: str,
        related_model: Type["Table"],
        foreign_key: Optional[str],
        parent_model: Type["Table"],
        option: LoadOption,
    ) -> None:
        """Load has_many with SELECT IN."""
        # Determine FK field on related model
        table_name = parent_model.__table_name__
        fk_field = foreign_key or (table_name[:-1] + "_id" if table_name.endswith("s") else table_name + "_id")
        
        # Collect parent IDs
        parent_ids = [inst.id for inst in instances if getattr(inst, "id", None) is not None]
        
        if not parent_ids:
            # No parent IDs - set empty lists
            for inst in instances:
                self._set_has_many_cache(inst, relationship, [])
            return
        
        # Load related models
        related_query = related_model.select().where_in(**{fk_field: parent_ids})
        related_instances = await related_query
        
        # Load nested relationships if specified
        if option.inner_options and related_instances:
            await self.load(related_instances, option.inner_options, related_model)
        
        # Group by FK
        related_map: Dict[int, List] = {}
        for related in related_instances:
            fk_value = getattr(related, fk_field, None)
            if fk_value is not None:
                if fk_value not in related_map:
                    related_map[fk_value] = []
                related_map[fk_value].append(related)
        
        # Assign to instances
        for inst in instances:
            inst_id = getattr(inst, "id", None)
            related_list = related_map.get(inst_id, [])
            self._set_has_many_cache(inst, relationship, related_list)
    
    async def _load_selectin_has_one(
        self,
        instances: List["Table"],
        relationship: str,
        related_model: Type["Table"],
        foreign_key: Optional[str],
        parent_model: Type["Table"],
        option: LoadOption,
    ) -> None:
        """Load has_one with SELECT IN."""
        # Determine FK field on related model
        table_name = parent_model.__table_name__
        fk_field = foreign_key or (table_name[:-1] + "_id" if table_name.endswith("s") else table_name + "_id")
        
        # Collect parent IDs
        parent_ids = [inst.id for inst in instances if getattr(inst, "id", None) is not None]
        
        if not parent_ids:
            for inst in instances:
                setattr(inst, f"_cached_{relationship}", None)
            return
        
        # Load related models
        related_query = related_model.select().where_in(**{fk_field: parent_ids})
        related_instances = await related_query
        
        # Load nested if specified
        if option.inner_options and related_instances:
            await self.load(related_instances, option.inner_options, related_model)
        
        # Map by FK
        related_map = {getattr(inst, fk_field): inst for inst in related_instances}
        
        # Assign to instances
        for inst in instances:
            inst_id = getattr(inst, "id", None)
            related = related_map.get(inst_id)
            setattr(inst, f"_cached_{relationship}", related)
    
    async def _load_subquery(
        self,
        instances: List["Table"],
        option: LoadOption,
        rel_info: Dict[str, Any],
        model: Type["Table"],
    ) -> None:
        """
        Load relationship using subquery strategy.
        
        Similar to selectin but uses a subquery to get IDs.
        Better for very deep nesting where IDs would be duplicated.
        
        For now, this delegates to selectin as the implementation
        is similar for most use cases.
        """
        # Subquery strategy uses similar logic to selectin
        # The main difference is in how the query is built
        # For simplicity, we use the same implementation
        await self._load_selectin(instances, option, rel_info, model)
    
    def _mark_raise(
        self,
        instances: List["Table"],
        relationship: str,
    ) -> None:
        """
        Mark instances to raise on relationship access.
        
        This sets a special marker that the descriptor checks.
        """
        marker_attr = f"_raise_on_{relationship}"
        for inst in instances:
            setattr(inst, marker_attr, True)
    
    def _set_has_many_cache(
        self,
        instance: "Table",
        relationship: str,
        items: List["Table"],
    ) -> None:
        """Set the has_many cache, using SyncedList if backref is configured."""
        from pynext.db.relationships.collections import SyncedList
        
        # Check if this relationship has backref configured
        cache_attr = f"_cached_{relationship}"
        
        # Get the descriptor to check for backref
        descriptor = getattr(type(instance), relationship, None)
        has_backref = (
            descriptor is not None and 
            hasattr(descriptor, "backref") and 
            (descriptor.backref or getattr(descriptor, "back_populates", None))
        )
        
        if has_backref:
            synced_list = SyncedList(instance, relationship, items)
            setattr(instance, cache_attr, synced_list)
        else:
            setattr(instance, cache_attr, items)


class JoinBuilder:
    """
    Builds JOIN clauses for eager loading.
    
    Used when strategy is JOINED to construct the SQL query
    with appropriate LEFT JOINs.
    
    Usage (internal):
        builder = JoinBuilder(model)
        builder.add_join("author", LoadStrategy.JOINED)
        sql, params = builder.build()
    """
    
    def __init__(self, model: Type["Table"]):
        """
        Initialize join builder.
        
        Args:
            model: The primary model being queried
        """
        self._model = model
        self._joins: List[Tuple[str, str, str, str]] = []  # (rel_name, table, on_left, on_right)
        self._select_columns: List[str] = []
    
    def add_join(
        self,
        relationship: str,
        rel_info: Dict[str, Any],
    ) -> None:
        """
        Add a JOIN for a relationship.
        
        Args:
            relationship: Relationship name
            rel_info: Relationship metadata
        """
        rel_type = rel_info["type"]
        related_model = rel_info["model"]
        foreign_key = rel_info.get("foreign_key")
        
        # Resolve string model
        if isinstance(related_model, str):
            from pynext.db.table import _model_registry
            related_model = _model_registry.get(related_model)
            if related_model is None:
                return
        
        table_name = related_model.__table_name__
        parent_table = self._model.__table_name__
        
        if rel_type == "belongs_to":
            # JOIN related ON parent.fk = related.id
            fk_field = foreign_key or f"{relationship}_id"
            self._joins.append((
                relationship,
                table_name,
                f"{parent_table}.{fk_field}",
                f"{table_name}.id",
            ))
        elif rel_type in ("has_many", "has_one"):
            # JOIN related ON related.fk = parent.id
            fk_field = foreign_key or (parent_table[:-1] + "_id" if parent_table.endswith("s") else parent_table + "_id")
            self._joins.append((
                relationship,
                table_name,
                f"{parent_table}.id",
                f"{table_name}.{fk_field}",
            ))
    
    def get_joins(self) -> List[Tuple[str, str, str, str]]:
        """Get the list of joins to add."""
        return self._joins
    
    def build_join_sql(self) -> str:
        """Build JOIN SQL clauses."""
        if not self._joins:
            return ""
        
        clauses = []
        for rel_name, table, on_left, on_right in self._joins:
            alias = f"{rel_name}_joined"
            clauses.append(
                f"LEFT JOIN {table} AS {alias} ON {on_left} = {on_right}"
            )
        
        return " ".join(clauses)


# Singleton loader instance
_loader: Optional[RelationshipLoader] = None


def get_loader(adapter: "Adapter") -> RelationshipLoader:
    """
    Get a relationship loader instance.
    
    Args:
        adapter: Database adapter
        
    Returns:
        RelationshipLoader instance
    """
    global _loader
    if _loader is None or _loader._adapter != adapter:
        _loader = RelationshipLoader(adapter)
    return _loader


def reset_loader() -> None:
    """Reset the global loader (for testing)."""
    global _loader
    _loader = None

