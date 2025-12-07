"""
PyNext Polymorphic Inheritance Strategies.

Implements the three inheritance patterns for polymorphic models:
- Single Table Inheritance (STI)
- Joined Table Inheritance
- Concrete Table Inheritance

Each strategy handles:
- Table creation/schema
- Query generation
- Type instantiation from database rows

Design Philosophy:
- Strategy pattern for clean separation
- Efficient SQL generation for each pattern
- Automatic type inference from discriminator values
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Type,
    TypeVar,
    Tuple,
    TYPE_CHECKING,
)

from pynext.db.polymorphic.registry import (
    InheritanceStrategy,
    PolymorphicConfig,
    get_polymorphic_registry,
)

if TYPE_CHECKING:
    from pynext.db.table import Table

T = TypeVar("T", bound="Table")


class PolymorphicStrategy(ABC):
    """
    Abstract base for polymorphic inheritance strategies.
    
    Each strategy implementation handles the SQL generation
    and instance creation for its specific inheritance pattern.
    """
    
    def __init__(self, config: PolymorphicConfig):
        self.config = config
        self.base_class = config.base_class
        self.discriminator = config.discriminator
    
    @abstractmethod
    def get_table_name(self, cls: Type[T]) -> str:
        """Get the table name for a class."""
        pass
    
    @abstractmethod
    def build_select_query(
        self,
        cls: Type[T],
        columns: Optional[List[str]] = None,
    ) -> Tuple[str, List[Any]]:
        """
        Build SELECT query for this class.
        
        Returns:
            Tuple of (query_string, parameters)
        """
        pass
    
    @abstractmethod
    def build_insert_query(
        self,
        cls: Type[T],
        data: Dict[str, Any],
    ) -> Tuple[str, List[Any]]:
        """
        Build INSERT query for this class.
        
        Returns:
            Tuple of (query_string, parameters)
        """
        pass
    
    @abstractmethod
    def instantiate_from_row(
        self,
        row: Dict[str, Any],
        target_class: Optional[Type[T]] = None,
    ) -> T:
        """
        Create an instance from a database row.
        
        Uses discriminator value to determine correct subtype.
        """
        pass
    
    def get_discriminator_value(self, cls: Type[T]) -> Optional[str]:
        """Get discriminator value for a class."""
        registry = get_polymorphic_registry()
        return registry.get_identity(cls)


class SingleTableStrategy(PolymorphicStrategy):
    """
    Single Table Inheritance (STI) strategy.
    
    All types stored in one table with a discriminator column.
    Subtype-specific columns are nullable.
    
    Table Structure:
        contents
        ├── id (PK)
        ├── type (discriminator)
        ├── title (shared)
        ├── body (Article-only, nullable)
        └── url (Video-only, nullable)
    
    Pros:
        - Simple queries (no JOINs)
        - Fast inserts and selects
        - Easy to understand
    
    Cons:
        - Nullable columns for type-specific fields
        - Table can get wide with many subtypes
    """
    
    def get_table_name(self, cls: Type[T]) -> str:
        """STI: All classes use the base class table."""
        return self._get_base_table_name()
    
    def _get_base_table_name(self) -> str:
        """Get the base class table name."""
        if hasattr(self.base_class, '__tablename__'):
            return self.base_class.__tablename__
        if hasattr(self.base_class, '_table_name'):
            return self.base_class._table_name
        return self.base_class.__name__.lower() + 's'
    
    def build_select_query(
        self,
        cls: Type[T],
        columns: Optional[List[str]] = None,
    ) -> Tuple[str, List[Any]]:
        """
        Build SELECT for STI.
        
        If querying a subtype, adds WHERE type = 'value'.
        If querying base, returns all rows.
        """
        table_name = self.get_table_name(cls)
        
        if columns:
            cols = ", ".join(columns)
        else:
            cols = "*"
        
        query = f"SELECT {cols} FROM {table_name}"
        params = []
        
        # Add discriminator filter for subtypes
        identity = self.get_discriminator_value(cls)
        if identity and cls != self.base_class:
            query += f" WHERE {self.discriminator} = $1"
            params.append(identity)
        
        return query, params
    
    def build_insert_query(
        self,
        cls: Type[T],
        data: Dict[str, Any],
    ) -> Tuple[str, List[Any]]:
        """Build INSERT for STI with discriminator value."""
        table_name = self.get_table_name(cls)
        
        # Add discriminator value
        identity = self.get_discriminator_value(cls)
        if identity:
            data = {**data, self.discriminator: identity}
        
        columns = list(data.keys())
        placeholders = [f"${i+1}" for i in range(len(columns))]
        
        query = f"""
        INSERT INTO {table_name} ({', '.join(columns)})
        VALUES ({', '.join(placeholders)})
        RETURNING *
        """
        
        return query.strip(), list(data.values())
    
    def instantiate_from_row(
        self,
        row: Dict[str, Any],
        target_class: Optional[Type[T]] = None,
    ) -> T:
        """
        Create instance from row using discriminator.
        
        If discriminator value maps to a registered subtype,
        creates that subtype. Otherwise, creates base class.
        """
        if target_class:
            # Caller specified the class
            return target_class(**row)
        
        # Look up class from discriminator value
        discriminator_value = row.get(self.discriminator)
        
        if discriminator_value:
            registry = get_polymorphic_registry()
            subtype = registry.get_class(self.base_class, discriminator_value)
            if subtype:
                return subtype(**row)
        
        # Fallback to base class
        return self.base_class(**row)


class JoinedTableStrategy(PolymorphicStrategy):
    """
    Joined Table Inheritance strategy.
    
    Base table contains shared columns.
    Each subtype has its own table with FK to base.
    
    Table Structure:
        employees (base)
        ├── id (PK)
        ├── type (discriminator)
        ├── name
        └── email
        
        managers (subtype)
        ├── id (PK, FK → employees.id)
        ├── department
        └── budget
        
        engineers (subtype)
        ├── id (PK, FK → employees.id)
        ├── language
        └── level
    
    Pros:
        - Normalized, no nulls
        - Each table only has relevant columns
        - Better for many subtypes with distinct fields
    
    Cons:
        - Requires JOINs for queries
        - More complex inserts (two tables)
    """
    
    def get_table_name(self, cls: Type[T]) -> str:
        """Joined: Each class has its own table."""
        if hasattr(cls, '__tablename__'):
            return cls.__tablename__
        if hasattr(cls, '_table_name'):
            return cls._table_name
        return cls.__name__.lower() + 's'
    
    def _get_base_table_name(self) -> str:
        """Get the base class table name."""
        return self.get_table_name(self.base_class)
    
    def build_select_query(
        self,
        cls: Type[T],
        columns: Optional[List[str]] = None,
    ) -> Tuple[str, List[Any]]:
        """
        Build SELECT with JOIN for subtypes.
        
        Base class query:
            SELECT * FROM employees
        
        Subtype query:
            SELECT employees.*, managers.*
            FROM employees
            JOIN managers ON employees.id = managers.id
            WHERE employees.type = 'manager'
        """
        base_table = self._get_base_table_name()
        params = []
        
        if cls == self.base_class:
            # Querying base class - no JOIN needed
            if columns:
                cols = ", ".join(columns)
            else:
                cols = "*"
            query = f"SELECT {cols} FROM {base_table}"
        else:
            # Querying subtype - JOIN with subtype table
            subtype_table = self.get_table_name(cls)
            
            query = f"""
            SELECT {base_table}.*, {subtype_table}.*
            FROM {base_table}
            JOIN {subtype_table} ON {base_table}.id = {subtype_table}.id
            WHERE {base_table}.{self.discriminator} = $1
            """
            
            identity = self.get_discriminator_value(cls)
            params.append(identity)
        
        return query.strip(), params
    
    def build_insert_query(
        self,
        cls: Type[T],
        data: Dict[str, Any],
    ) -> Tuple[str, List[Any]]:
        """
        Build INSERT for joined tables.
        
        For subtypes, need to insert into both tables.
        Returns a composite query that:
        1. Inserts into base table
        2. Inserts into subtype table with the new ID
        """
        if cls == self.base_class:
            # Simple insert into base table
            return self._build_base_insert(data)
        
        # Subtype: need to separate base and subtype fields
        base_fields = self._get_base_fields()
        base_data = {}
        subtype_data = {}
        
        for key, value in data.items():
            if key in base_fields or key == self.discriminator:
                base_data[key] = value
            else:
                subtype_data[key] = value
        
        # Add discriminator to base data
        identity = self.get_discriminator_value(cls)
        if identity:
            base_data[self.discriminator] = identity
        
        # Build combined query using CTE
        base_table = self._get_base_table_name()
        subtype_table = self.get_table_name(cls)
        
        base_cols = list(base_data.keys())
        base_placeholders = [f"${i+1}" for i in range(len(base_cols))]
        
        subtype_cols = ['id'] + list(subtype_data.keys())
        offset = len(base_cols) + 1
        subtype_placeholders = ['new_row.id'] + [
            f"${i+offset}" for i in range(len(subtype_data))
        ]
        
        query = f"""
        WITH new_row AS (
            INSERT INTO {base_table} ({', '.join(base_cols)})
            VALUES ({', '.join(base_placeholders)})
            RETURNING *
        )
        INSERT INTO {subtype_table} ({', '.join(subtype_cols)})
        SELECT {', '.join(subtype_placeholders)}
        FROM new_row
        RETURNING *
        """
        
        params = list(base_data.values()) + list(subtype_data.values())
        return query.strip(), params
    
    def _build_base_insert(self, data: Dict[str, Any]) -> Tuple[str, List[Any]]:
        """Build insert for base table only."""
        table_name = self._get_base_table_name()
        
        columns = list(data.keys())
        placeholders = [f"${i+1}" for i in range(len(columns))]
        
        query = f"""
        INSERT INTO {table_name} ({', '.join(columns)})
        VALUES ({', '.join(placeholders)})
        RETURNING *
        """
        
        return query.strip(), list(data.values())
    
    def _get_base_fields(self) -> set:
        """Get field names defined on the base class."""
        if hasattr(self.base_class, '__annotations__'):
            return set(self.base_class.__annotations__.keys())
        return set()
    
    def instantiate_from_row(
        self,
        row: Dict[str, Any],
        target_class: Optional[Type[T]] = None,
    ) -> T:
        """Create instance from joined row."""
        if target_class:
            return target_class(**row)
        
        # Look up class from discriminator
        discriminator_value = row.get(self.discriminator)
        
        if discriminator_value:
            registry = get_polymorphic_registry()
            subtype = registry.get_class(self.base_class, discriminator_value)
            if subtype:
                return subtype(**row)
        
        return self.base_class(**row)


class ConcreteTableStrategy(PolymorphicStrategy):
    """
    Concrete Table Inheritance strategy.
    
    Each type has its own complete table.
    No shared table, each contains all fields.
    
    Table Structure:
        cars
        ├── id (PK)
        ├── make (inherited)
        ├── model (inherited)
        ├── year (inherited)
        ├── num_doors
        └── trunk_size
        
        motorcycles
        ├── id (PK)
        ├── make (inherited)
        ├── model (inherited)
        ├── year (inherited)
        ├── engine_cc
        └── has_sidecar
    
    Pros:
        - Most isolated
        - No nulls
        - Fastest single-type queries
    
    Cons:
        - Cross-type queries need UNION
        - Duplicated schema columns
    """
    
    def get_table_name(self, cls: Type[T]) -> str:
        """Concrete: Each class has its own table."""
        if hasattr(cls, '__tablename__'):
            return cls.__tablename__
        if hasattr(cls, '_table_name'):
            return cls._table_name
        return cls.__name__.lower() + 's'
    
    def build_select_query(
        self,
        cls: Type[T],
        columns: Optional[List[str]] = None,
    ) -> Tuple[str, List[Any]]:
        """
        Build SELECT for concrete tables.
        
        Subtype query:
            SELECT * FROM cars
        
        Base class query (UNION):
            SELECT *, 'car' as _type FROM cars
            UNION ALL
            SELECT *, 'motorcycle' as _type FROM motorcycles
        """
        if cls == self.base_class:
            # Query all subtypes with UNION
            return self._build_union_query(columns)
        
        # Simple query for specific subtype
        table_name = self.get_table_name(cls)
        
        if columns:
            cols = ", ".join(columns)
        else:
            cols = "*"
        
        query = f"SELECT {cols} FROM {table_name}"
        return query, []
    
    def _build_union_query(
        self,
        columns: Optional[List[str]] = None,
    ) -> Tuple[str, List[Any]]:
        """Build UNION query for all subtypes."""
        registry = get_polymorphic_registry()
        subtypes = registry.get_all_subtypes(self.base_class)
        
        if not subtypes:
            # No subtypes registered, query base table
            table_name = self.get_table_name(self.base_class)
            return f"SELECT * FROM {table_name}", []
        
        unions = []
        for subtype in subtypes:
            table_name = self.get_table_name(subtype)
            identity = registry.get_identity(subtype)
            
            if columns:
                cols = ", ".join(columns)
            else:
                cols = "*"
            
            # Add _type column for type identification
            unions.append(
                f"SELECT {cols}, '{identity}' as _type FROM {table_name}"
            )
        
        query = " UNION ALL ".join(unions)
        return query, []
    
    def build_insert_query(
        self,
        cls: Type[T],
        data: Dict[str, Any],
    ) -> Tuple[str, List[Any]]:
        """Build INSERT for concrete table."""
        table_name = self.get_table_name(cls)
        
        columns = list(data.keys())
        placeholders = [f"${i+1}" for i in range(len(columns))]
        
        query = f"""
        INSERT INTO {table_name} ({', '.join(columns)})
        VALUES ({', '.join(placeholders)})
        RETURNING *
        """
        
        return query.strip(), list(data.values())
    
    def instantiate_from_row(
        self,
        row: Dict[str, Any],
        target_class: Optional[Type[T]] = None,
    ) -> T:
        """Create instance from concrete table row."""
        if target_class:
            # Remove _type column if present
            row = {k: v for k, v in row.items() if k != '_type'}
            return target_class(**row)
        
        # Look up class from _type column (from UNION query)
        type_value = row.get('_type')
        row = {k: v for k, v in row.items() if k != '_type'}
        
        if type_value:
            registry = get_polymorphic_registry()
            subtype = registry.get_class(self.base_class, type_value)
            if subtype:
                return subtype(**row)
        
        return self.base_class(**row)


def get_strategy(cls: Type[T]) -> Optional[PolymorphicStrategy]:
    """
    Get the appropriate strategy for a polymorphic class.
    
    Args:
        cls: The polymorphic class
    
    Returns:
        Strategy instance, or None if not polymorphic
    """
    registry = get_polymorphic_registry()
    config = registry.get_base_config(cls)
    
    if config is None:
        return None
    
    strategy_map = {
        InheritanceStrategy.SINGLE_TABLE: SingleTableStrategy,
        InheritanceStrategy.JOINED: JoinedTableStrategy,
        InheritanceStrategy.CONCRETE: ConcreteTableStrategy,
    }
    
    strategy_class = strategy_map.get(config.strategy)
    if strategy_class:
        return strategy_class(config)
    
    return None


__all__ = [
    "PolymorphicStrategy",
    "SingleTableStrategy",
    "JoinedTableStrategy",
    "ConcreteTableStrategy",
    "get_strategy",
]

