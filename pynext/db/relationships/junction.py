"""
PyNext Junction Table Management.

Handles creation and management of junction tables for many-to-many relationships.

Design Philosophy:
- Auto-create junction tables when not specified (dead simple)
- Support explicit junction tables with extra columns
- Consistent naming conventions
- AI-friendly: explicit, traceable behavior

SQLAlchemy Comparison:
    SQLAlchemy (verbose):
        association_table = Table('association', Base.metadata,
            Column('left_id', Integer, ForeignKey('left.id')),
            Column('right_id', Integer, ForeignKey('right.id'))
        )
        class Parent(Base):
            children = relationship("Child", secondary=association_table)
    
    PyNext (simple):
        class Parent(Table):
            children: List[Child] = many_to_many(Child, backref="parents")
        # Junction table auto-created!
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import (
    Any,
    Dict,
    Generic,
    List,
    Optional,
    Type,
    TypeVar,
    TYPE_CHECKING,
    Union,
)

if TYPE_CHECKING:
    from pynext.db.table import Table
    from pynext.db.fields import FieldInfo

T = TypeVar("T", bound="Table")


# =============================================================================
# Junction Configuration
# =============================================================================

@dataclass
class JunctionConfig:
    """
    Configuration for a junction table.
    
    Stores all information needed to create and manage a junction table
    for a many-to-many relationship.
    
    Attributes:
        name: Junction table name (e.g., "students_courses")
        source_model: The model that defines the relationship (e.g., Student)
        target_model: The related model (e.g., Course)
        source_fk: Foreign key column for source (e.g., "student_id")
        target_fk: Foreign key column for target (e.g., "course_id")
        through_model: Explicit junction model if provided (e.g., Enrollment)
        source_attr: Attribute name on source model (e.g., "courses")
        target_attr: Attribute name on target model (e.g., "students")
    
    Example:
        config = JunctionConfig(
            name="students_courses",
            source_model=Student,
            target_model=Course,
            source_fk="student_id",
            target_fk="course_id",
            through_model=None,  # Auto-create
            source_attr="courses",
            target_attr="students",
        )
    """
    
    name: str
    source_model: Union[Type["Table"], str]
    target_model: Union[Type["Table"], str]
    source_fk: str
    target_fk: str
    through_model: Optional[Union[Type["Table"], str]] = None
    source_attr: str = ""
    target_attr: str = ""
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.name:
            raise ValueError("Junction table name cannot be empty")
        if not self.source_fk:
            raise ValueError("Source foreign key cannot be empty")
        if not self.target_fk:
            raise ValueError("Target foreign key cannot be empty")
    
    @property
    def is_explicit(self) -> bool:
        """Check if this uses an explicit through model."""
        return self.through_model is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "source_model": (
                self.source_model.__name__ 
                if hasattr(self.source_model, "__name__") 
                else str(self.source_model)
            ),
            "target_model": (
                self.target_model.__name__ 
                if hasattr(self.target_model, "__name__") 
                else str(self.target_model)
            ),
            "source_fk": self.source_fk,
            "target_fk": self.target_fk,
            "through_model": (
                self.through_model.__name__ 
                if hasattr(self.through_model, "__name__") 
                else str(self.through_model) if self.through_model else None
            ),
            "source_attr": self.source_attr,
            "target_attr": self.target_attr,
        }
    
    def __repr__(self) -> str:
        return (
            f"JunctionConfig(name={self.name!r}, "
            f"source={self.source_model}, target={self.target_model})"
        )


# =============================================================================
# Junction Table Factory
# =============================================================================

class JunctionTableFactory:
    """
    Creates and manages junction tables for many-to-many relationships.
    
    Responsibilities:
    - Generate junction table names from model names
    - Create implicit junction table classes dynamically
    - Cache created junction tables to avoid duplicates
    - Resolve string model references
    
    Usage:
        factory = JunctionTableFactory()
        
        # Auto-create junction table
        junction_class = factory.create_implicit_junction(Student, Course)
        # Creates: students_courses table with student_id, course_id
        
        # Get or create with config
        junction_class = factory.get_or_create(config)
    """
    
    def __init__(self):
        """Initialize the factory with empty cache."""
        self._cache: Dict[str, Type["Table"]] = {}
        self._configs: Dict[str, JunctionConfig] = {}
    
    def generate_junction_name(
        self,
        source_model: Union[Type["Table"], str],
        target_model: Union[Type["Table"], str],
    ) -> str:
        """
        Generate a consistent junction table name from two models.
        
        Convention: Sort names alphabetically, join with underscore.
        This ensures the same name regardless of which side defines the relationship.
        
        Args:
            source_model: First model
            target_model: Second model
        
        Returns:
            Junction table name (e.g., "courses_students")
        
        Examples:
            generate_junction_name(Student, Course) -> "courses_students"
            generate_junction_name(Course, Student) -> "courses_students"
        """
        source_name = self._get_table_name(source_model)
        target_name = self._get_table_name(target_model)
        
        # Sort alphabetically for consistency
        names = sorted([source_name, target_name])
        return "_".join(names)
    
    def _get_table_name(self, model: Union[Type["Table"], str]) -> str:
        """Get table name from model class or string."""
        if isinstance(model, str):
            # Convert class name to table name convention
            # e.g., "Student" -> "students"
            return model.lower() + "s"
        
        if hasattr(model, "__table_name__"):
            return model.__table_name__
        
        # Fallback to class name
        return model.__name__.lower() + "s"
    
    def _get_fk_name(self, model: Union[Type["Table"], str]) -> str:
        """Get foreign key column name for a model."""
        table_name = self._get_table_name(model)
        # Remove trailing 's' and add '_id'
        # e.g., "students" -> "student_id"
        singular = table_name.rstrip("s")
        return f"{singular}_id"
    
    def create_implicit_junction(
        self,
        source_model: Union[Type["Table"], str],
        target_model: Union[Type["Table"], str],
        source_attr: str = "",
        target_attr: str = "",
    ) -> Type["Table"]:
        """
        Create an implicit junction table class.
        
        Dynamically creates a Table subclass with just the two foreign keys.
        
        Args:
            source_model: Source model class or name
            target_model: Target model class or name
            source_attr: Attribute name on source
            target_attr: Attribute name on target
        
        Returns:
            Dynamically created junction Table class
        
        Example:
            JunctionClass = factory.create_implicit_junction(Student, Course)
            # Creates class with:
            #   __table_name__ = "courses_students"
            #   student_id: int
            #   course_id: int
        """
        junction_name = self.generate_junction_name(source_model, target_model)
        
        # Check cache first
        if junction_name in self._cache:
            return self._cache[junction_name]
        
        # Import here to avoid circular imports
        from pynext.db.table import Table, _model_registry
        
        # Generate foreign key names
        source_fk = self._get_fk_name(source_model)
        target_fk = self._get_fk_name(target_model)
        
        # Create class dynamically
        class_name = "".join(word.capitalize() for word in junction_name.split("_"))
        
        # Define the junction class with proper annotations
        junction_class = type(
            class_name,
            (Table,),
            {
                "__table_name__": junction_name,
                "__annotations__": {
                    source_fk: int,
                    target_fk: int,
                },
                source_fk: 0,
                target_fk: 0,
                "_is_junction": True,
            }
        )
        
        # Register in model registry
        _model_registry[junction_name] = junction_class
        
        # Cache the class
        self._cache[junction_name] = junction_class
        
        # Store config
        config = JunctionConfig(
            name=junction_name,
            source_model=source_model,
            target_model=target_model,
            source_fk=source_fk,
            target_fk=target_fk,
            through_model=None,
            source_attr=source_attr,
            target_attr=target_attr,
        )
        self._configs[junction_name] = config
        
        return junction_class
    
    def get_or_create(self, config: JunctionConfig) -> Type["Table"]:
        """
        Get existing or create new junction table from config.
        
        Args:
            config: Junction configuration
        
        Returns:
            Junction table class
        """
        # If explicit through model, just return it
        if config.through_model is not None:
            if isinstance(config.through_model, str):
                from pynext.db.table import _model_registry
                model = _model_registry.get(config.through_model)
                if model is None:
                    # Try lowercase + s convention
                    table_name = config.through_model.lower() + "s"
                    model = _model_registry.get(table_name)
                if model is None:
                    raise ValueError(
                        f"Could not resolve through model: {config.through_model}"
                    )
                return model
            return config.through_model
        
        # Check cache
        if config.name in self._cache:
            return self._cache[config.name]
        
        # Create implicit junction
        return self.create_implicit_junction(
            config.source_model,
            config.target_model,
            config.source_attr,
            config.target_attr,
        )
    
    def get_config(self, junction_name: str) -> Optional[JunctionConfig]:
        """Get configuration for a junction table."""
        return self._configs.get(junction_name)
    
    def clear(self) -> None:
        """Clear all cached junction tables."""
        self._cache.clear()
        self._configs.clear()


# =============================================================================
# Junction Manager (Row Operations)
# =============================================================================

class JunctionManager:
    """
    Manages junction table rows for many-to-many relationships.
    
    Handles creation, deletion, and lookup of junction rows.
    Works with both implicit and explicit junction tables.
    
    Usage:
        manager = JunctionManager(config)
        
        # Create junction row
        row = await manager.create_row(student, course)
        
        # Create with extra data (explicit junction)
        row = await manager.create_row(student, course, grade="A")
        
        # Delete junction row
        deleted = await manager.delete_row(student, course)
        
        # Get junction row (for extra data access)
        row = await manager.get_row(student, course)
    """
    
    def __init__(self, config: JunctionConfig):
        """
        Initialize manager with junction configuration.
        
        Args:
            config: Junction table configuration
        """
        self.config = config
        self._factory = get_junction_factory()
    
    def _get_source_id(self, source: "Table") -> Optional[int]:
        """Get ID from source object."""
        return getattr(source, "id", None)
    
    def _get_target_id(self, target: "Table") -> Optional[int]:
        """Get ID from target object."""
        return getattr(target, "id", None)
    
    async def create_row(
        self,
        source: "Table",
        target: "Table",
        **extra: Any,
    ) -> "Table":
        """
        Create a junction table row.
        
        Args:
            source: Source model instance
            target: Target model instance
            **extra: Extra column values (for explicit junctions)
        
        Returns:
            Created junction row instance
        
        Raises:
            ValueError: If source or target has no id
        
        Example:
            # Simple junction
            row = await manager.create_row(student, course)
            
            # With extra data
            row = await manager.create_row(student, course, grade="A")
        """
        source_id = self._get_source_id(source)
        target_id = self._get_target_id(target)
        
        if source_id is None:
            raise ValueError(
                f"Cannot create junction row: source {type(source).__name__} has no id. "
                "Save the source object first."
            )
        if target_id is None:
            raise ValueError(
                f"Cannot create junction row: target {type(target).__name__} has no id. "
                "Save the target object first."
            )
        
        # Get junction table class
        junction_class = self._factory.get_or_create(self.config)
        
        # Create row data
        row_data = {
            self.config.source_fk: source_id,
            self.config.target_fk: target_id,
            **extra,
        }
        
        # Create instance
        row = junction_class(**row_data)
        
        # Save to database
        await row.save()
        
        return row
    
    async def delete_row(
        self,
        source: "Table",
        target: "Table",
    ) -> bool:
        """
        Delete a junction table row.
        
        Args:
            source: Source model instance
            target: Target model instance
        
        Returns:
            True if row was deleted, False if not found
        """
        source_id = self._get_source_id(source)
        target_id = self._get_target_id(target)
        
        if source_id is None or target_id is None:
            return False
        
        # Get junction table class
        junction_class = self._factory.get_or_create(self.config)
        
        # Find and delete the row
        row = await junction_class.select().where(**{
            self.config.source_fk: source_id,
            self.config.target_fk: target_id,
        }).first()
        
        if row:
            await row.delete()
            return True
        
        return False
    
    async def get_row(
        self,
        source: "Table",
        target: "Table",
    ) -> Optional["Table"]:
        """
        Get junction table row for accessing extra columns.
        
        Args:
            source: Source model instance
            target: Target model instance
        
        Returns:
            Junction row instance if found, None otherwise
        
        Example:
            row = await manager.get_row(student, course)
            if row:
                print(f"Grade: {row.grade}")
        """
        source_id = self._get_source_id(source)
        target_id = self._get_target_id(target)
        
        if source_id is None or target_id is None:
            return None
        
        # Get junction table class
        junction_class = self._factory.get_or_create(self.config)
        
        # Find the row
        return await junction_class.select().where(**{
            self.config.source_fk: source_id,
            self.config.target_fk: target_id,
        }).first()
    
    async def exists(
        self,
        source: "Table",
        target: "Table",
    ) -> bool:
        """
        Check if junction row exists.
        
        Args:
            source: Source model instance
            target: Target model instance
        
        Returns:
            True if junction row exists
        """
        row = await self.get_row(source, target)
        return row is not None
    
    async def get_all_for_source(
        self,
        source: "Table",
    ) -> List["Table"]:
        """
        Get all junction rows for a source object.
        
        Args:
            source: Source model instance
        
        Returns:
            List of junction row instances
        """
        source_id = self._get_source_id(source)
        
        if source_id is None:
            return []
        
        junction_class = self._factory.get_or_create(self.config)
        
        return await junction_class.select().where(**{
            self.config.source_fk: source_id,
        }).all()
    
    async def get_all_for_target(
        self,
        target: "Table",
    ) -> List["Table"]:
        """
        Get all junction rows for a target object.
        
        Args:
            target: Target model instance
        
        Returns:
            List of junction row instances
        """
        target_id = self._get_target_id(target)
        
        if target_id is None:
            return []
        
        junction_class = self._factory.get_or_create(self.config)
        
        return await junction_class.select().where(**{
            self.config.target_fk: target_id,
        }).all()
    
    async def delete_all_for_source(
        self,
        source: "Table",
    ) -> int:
        """
        Delete all junction rows for a source object.
        
        Args:
            source: Source model instance
        
        Returns:
            Number of rows deleted
        """
        rows = await self.get_all_for_source(source)
        for row in rows:
            await row.delete()
        return len(rows)
    
    async def delete_all_for_target(
        self,
        target: "Table",
    ) -> int:
        """
        Delete all junction rows for a target object.
        
        Args:
            target: Target model instance
        
        Returns:
            Number of rows deleted
        """
        rows = await self.get_all_for_target(target)
        for row in rows:
            await row.delete()
        return len(rows)
    
    async def update_row(
        self,
        source: "Table",
        target: "Table",
        **updates: Any,
    ) -> Optional["Table"]:
        """
        Update extra columns on a junction row.
        
        Args:
            source: Source model instance
            target: Target model instance
            **updates: Column values to update
        
        Returns:
            Updated junction row if found, None otherwise
        
        Example:
            row = await manager.update_row(student, course, grade="A+")
        """
        row = await self.get_row(source, target)
        
        if row is None:
            return None
        
        for key, value in updates.items():
            setattr(row, key, value)
        
        await row.save()
        return row


# =============================================================================
# Global Factory Instance
# =============================================================================

_junction_factory: Optional[JunctionTableFactory] = None


def get_junction_factory() -> JunctionTableFactory:
    """Get the global junction table factory instance."""
    global _junction_factory
    if _junction_factory is None:
        _junction_factory = JunctionTableFactory()
    return _junction_factory


def reset_junction_factory() -> None:
    """Reset the global junction table factory (for testing)."""
    global _junction_factory
    if _junction_factory is not None:
        _junction_factory.clear()
    _junction_factory = None


# =============================================================================
# Utility Functions
# =============================================================================

def create_junction_config(
    source_model: Union[Type["Table"], str],
    target_model: Union[Type["Table"], str],
    through: Optional[Union[Type["Table"], str]] = None,
    source_attr: str = "",
    target_attr: str = "",
) -> JunctionConfig:
    """
    Create a JunctionConfig with auto-generated values.
    
    Args:
        source_model: Source model class or name
        target_model: Target model class or name
        through: Optional explicit junction table
        source_attr: Attribute name on source
        target_attr: Attribute name on target
    
    Returns:
        Configured JunctionConfig instance
    """
    factory = get_junction_factory()
    
    junction_name = factory.generate_junction_name(source_model, target_model)
    source_fk = factory._get_fk_name(source_model)
    target_fk = factory._get_fk_name(target_model)
    
    # If using explicit through model, get its table name
    if through is not None:
        if isinstance(through, str):
            junction_name = through.lower() + "s"
        elif hasattr(through, "__table_name__"):
            junction_name = through.__table_name__
    
    return JunctionConfig(
        name=junction_name,
        source_model=source_model,
        target_model=target_model,
        source_fk=source_fk,
        target_fk=target_fk,
        through_model=through,
        source_attr=source_attr,
        target_attr=target_attr,
    )


def create_junction_with_extra(
    source_model: Union[Type["Table"], str],
    target_model: Union[Type["Table"], str],
    extra_columns: Dict[str, Any],
) -> Type["Table"]:
    """
    Create an inline junction table model with extra columns.
    
    This is the simpler alternative to defining a separate through= model.
    Instead of:
        class Enrollment(Table):
            student_id: int
            course_id: int
            grade: Optional[str]
        
        courses = many_to_many(Course, through=Enrollment)
    
    You can write:
        courses = many_to_many(Course, extra={"grade": Optional[str]})
    
    Args:
        source_model: Source model class or name
        target_model: Target model class or name
        extra_columns: Dict of {column_name: type} for extra columns
    
    Returns:
        Dynamically created junction table model
    
    Example:
        JunctionModel = create_junction_with_extra(
            Student, 
            Course, 
            {"grade": Optional[str], "enrolled_at": datetime}
        )
        # Creates a model equivalent to:
        # class StudentCourseJunction(Table):
        #     student_id: int
        #     course_id: int
        #     grade: Optional[str]
        #     enrolled_at: datetime
    """
    from pynext.db.table import Table
    
    # Get model names
    source_name = source_model.__name__ if hasattr(source_model, "__name__") else str(source_model)
    target_name = target_model.__name__ if hasattr(target_model, "__name__") else str(target_model)
    
    # Generate class name
    class_name = f"{source_name}{target_name}Junction"
    
    # Build field annotations
    factory = get_junction_factory()
    source_fk = factory._get_fk_name(source_model)
    target_fk = factory._get_fk_name(target_model)
    
    annotations = {
        source_fk: int,
        target_fk: int,
        **extra_columns,
    }
    
    # Create the class dynamically
    junction_class = type(class_name, (Table,), {
        "__annotations__": annotations,
        "__module__": source_model.__module__ if hasattr(source_model, "__module__") else __name__,
    })
    
    # Store extra column info for runtime access
    junction_class._extra_columns = list(extra_columns.keys())
    
    return junction_class

