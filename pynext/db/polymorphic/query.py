"""
PyNext Polymorphic Query Extensions.

Extends the query builder to handle polymorphic types:
- Automatic type inference from discriminator values
- without_polymorphism() for raw queries
- where_target_type() for generic FK filtering

Design Philosophy:
- Seamless integration with existing query builder
- Automatic type resolution by default
- Explicit control when needed
- Efficient SQL generation

Usage:
    # Automatic polymorphism (default)
    contents = await Content.all()
    # Returns: [Article(...), Video(...), ...]
    
    # Disable polymorphism
    contents = await Content.all().without_polymorphism()
    # Returns: [Content(...), Content(...), ...]
    
    # Filter by generic FK target type
    comments = await Comment.select().where_target_type(Article)
"""

from __future__ import annotations

from typing import (
    Any,
    Dict,
    Generic,
    List,
    Optional,
    Type,
    TypeVar,
    TYPE_CHECKING,
)

from pynext.db.polymorphic.registry import (
    InheritanceStrategy,
    get_polymorphic_registry,
)
from pynext.db.polymorphic.strategies import get_strategy
from pynext.db.polymorphic.generic_fk import (
    get_generic_fk_config,
    get_all_generic_fk_configs,
)

if TYPE_CHECKING:
    from pynext.db.table import Table

T = TypeVar("T", bound="Table")


class PolymorphicQueryMixin:
    """
    Mixin for query builders to support polymorphic operations.
    
    Add this to your query builder class to enable:
    - Automatic type instantiation
    - without_polymorphism()
    - where_target_type()
    """
    
    _use_polymorphism: bool = True
    _model_class: Type[T]
    
    def without_polymorphism(self) -> "PolymorphicQueryMixin":
        """
        Disable polymorphic type resolution.
        
        By default, queries on polymorphic base classes return
        instances of the correct subtype based on the discriminator.
        
        This method disables that behavior, returning all rows
        as instances of the queried class.
        
        Example:
            # Default: Returns Article, Video instances
            contents = await Content.all()
            
            # With this: Returns all as Content instances
            contents = await Content.all().without_polymorphism()
        
        Returns:
            Self for chaining
        """
        self._use_polymorphism = False
        return self
    
    def with_polymorphism(self) -> "PolymorphicQueryMixin":
        """
        Enable polymorphic type resolution (default).
        
        Returns:
            Self for chaining
        """
        self._use_polymorphism = True
        return self
    
    def where_target_type(
        self,
        target_type: Type["Table"],
        field_name: str = "target",
    ) -> "PolymorphicQueryMixin":
        """
        Filter by generic FK target type.
        
        Args:
            target_type: The target model class to filter by
            field_name: Name of the generic FK field (default: "target")
        
        Example:
            # Get comments on articles only
            comments = await Comment.select().where_target_type(Article)
            
            # For a different field name
            comments = await Comment.select().where_target_type(
                Video, 
                field_name="parent"
            )
        
        Returns:
            Self for chaining
        """
        config = get_generic_fk_config(self._model_class, field_name)
        
        if config is None:
            raise ValueError(
                f"Field '{field_name}' is not a generic foreign key on "
                f"{self._model_class.__name__}"
            )
        
        # Get type name for the target class
        type_name = None
        if hasattr(target_type, '__tablename__'):
            type_name = target_type.__tablename__
        elif hasattr(target_type, '_table_name'):
            type_name = target_type._table_name
        else:
            type_name = target_type.__name__.lower()
        
        # Add WHERE condition for type column
        return self.where(**{config.type_column: type_name})
    
    def where_target(
        self,
        target: "Table",
        field_name: str = "target",
    ) -> "PolymorphicQueryMixin":
        """
        Filter by specific generic FK target instance.
        
        Args:
            target: The target model instance
            field_name: Name of the generic FK field (default: "target")
        
        Example:
            article = await Article.get(1)
            comments = await Comment.select().where_target(article)
        
        Returns:
            Self for chaining
        """
        config = get_generic_fk_config(self._model_class, field_name)
        
        if config is None:
            raise ValueError(
                f"Field '{field_name}' is not a generic foreign key on "
                f"{self._model_class.__name__}"
            )
        
        # Get type name and ID
        type_name = config.get_type_name(target)
        target_id = config.get_target_id(target)
        
        # Add WHERE conditions for both columns
        return self.where(**{
            config.type_column: type_name,
            config.id_column: target_id,
        })
    
    def _instantiate_polymorphic(
        self,
        row: Dict[str, Any],
    ) -> T:
        """
        Instantiate a row as the correct polymorphic type.
        
        Args:
            row: Database row as dict
        
        Returns:
            Instance of correct subtype (or base if polymorphism disabled)
        """
        if not self._use_polymorphism:
            return self._model_class(**row)
        
        strategy = get_strategy(self._model_class)
        
        if strategy:
            return strategy.instantiate_from_row(row)
        
        return self._model_class(**row)
    
    def _get_polymorphic_select_query(self) -> tuple:
        """
        Get the SELECT query for polymorphic class.
        
        Handles strategy-specific query generation.
        
        Returns:
            Tuple of (query_string, parameters)
        """
        strategy = get_strategy(self._model_class)
        
        if strategy:
            return strategy.build_select_query(self._model_class)
        
        # Fallback to simple query
        table_name = self._get_table_name()
        return f"SELECT * FROM {table_name}", []
    
    def _get_table_name(self) -> str:
        """Get table name for the model."""
        if hasattr(self._model_class, '__tablename__'):
            return self._model_class.__tablename__
        if hasattr(self._model_class, '_table_name'):
            return self._model_class._table_name
        return self._model_class.__name__.lower() + 's'


class PolymorphicQueryBuilder(PolymorphicQueryMixin, Generic[T]):
    """
    Query builder with full polymorphic support.
    
    This is a standalone query builder that can be used
    when the main query builder doesn't have polymorphic support.
    
    Example:
        query = PolymorphicQueryBuilder(Content)
        contents = await query.all()
    """
    
    def __init__(self, model_class: Type[T]):
        self._model_class = model_class
        self._use_polymorphism = True
        self._conditions: List[tuple] = []
        self._order_by: Optional[str] = None
        self._limit_value: Optional[int] = None
        self._offset_value: Optional[int] = None
    
    def where(self, **conditions) -> "PolymorphicQueryBuilder[T]":
        """Add WHERE conditions."""
        for field, value in conditions.items():
            self._conditions.append((field, '=', value))
        return self
    
    def where_in(self, **conditions) -> "PolymorphicQueryBuilder[T]":
        """Add WHERE IN conditions."""
        for field, values in conditions.items():
            self._conditions.append((field, 'IN', values))
        return self
    
    def order_by(self, field: str, desc: bool = False) -> "PolymorphicQueryBuilder[T]":
        """Add ORDER BY."""
        direction = "DESC" if desc else "ASC"
        self._order_by = f"{field} {direction}"
        return self
    
    def limit(self, n: int) -> "PolymorphicQueryBuilder[T]":
        """Add LIMIT."""
        self._limit_value = n
        return self
    
    def offset(self, n: int) -> "PolymorphicQueryBuilder[T]":
        """Add OFFSET."""
        self._offset_value = n
        return self
    
    async def all(self) -> List[T]:
        """Execute query and return all results."""
        # This would integrate with your actual query execution
        # For now, returns empty list as placeholder
        return []
    
    async def first(self) -> Optional[T]:
        """Execute query and return first result."""
        results = await self.limit(1).all()
        return results[0] if results else None
    
    async def count(self) -> int:
        """Count matching rows."""
        return 0


def polymorphic_query(model_class: Type[T]) -> PolymorphicQueryBuilder[T]:
    """
    Create a polymorphic query builder.
    
    Args:
        model_class: The model class to query
    
    Returns:
        PolymorphicQueryBuilder instance
    """
    return PolymorphicQueryBuilder(model_class)


def instantiate_polymorphic(
    model_class: Type[T],
    row: Dict[str, Any],
    use_polymorphism: bool = True,
) -> T:
    """
    Instantiate a database row as the correct polymorphic type.
    
    Args:
        model_class: The base model class
        row: Database row as dict
        use_polymorphism: Whether to use polymorphic type resolution
    
    Returns:
        Instance of correct subtype
    """
    if not use_polymorphism:
        return model_class(**row)
    
    strategy = get_strategy(model_class)
    
    if strategy:
        return strategy.instantiate_from_row(row)
    
    return model_class(**row)


__all__ = [
    "PolymorphicQueryMixin",
    "PolymorphicQueryBuilder",
    "polymorphic_query",
    "instantiate_polymorphic",
]

