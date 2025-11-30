"""
Migration Change Detector (Model Differ).

Compares Python model definitions to actual database schema
and detects all changes needed to sync them.

Design: Smart detection with minimal false positives.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple, Type, TYPE_CHECKING

from pynext.db.fields import FieldInfo, SQLType
from pynext.db.migrations.changes import (
    Change,
    ColumnDef,
    CreateTable,
    DropTable,
    RenameTable,
    AddColumn,
    DropColumn,
    RenameColumn,
    AlterColumn,
    AddIndex,
    DropIndex,
)

if TYPE_CHECKING:
    from pynext.db.table import Table
    from pynext.db.adapters.base import Adapter


@dataclass
class TableSchema:
    """Database table schema."""
    name: str
    columns: Dict[str, ColumnDef]
    indexes: Dict[str, Dict]  # name -> {columns, unique}
    row_count: int = 0


@dataclass
class DetectionResult:
    """Result of schema change detection."""
    changes: List[Change]
    ambiguous: List["AmbiguousChange"]
    warnings: List[str]
    
    @property
    def has_changes(self) -> bool:
        return bool(self.changes) or bool(self.ambiguous)
    
    @property
    def has_destructive(self) -> bool:
        return any(c.is_destructive() for c in self.changes)


@dataclass
class AmbiguousChange:
    """A change that needs user confirmation."""
    description: str
    question: str
    if_yes: Change
    if_no: List[Change]
    default: bool = False  # Default answer


def field_to_column_def(field: FieldInfo) -> ColumnDef:
    """Convert a FieldInfo to a ColumnDef."""
    # Map SQLType to string
    type_str = field.sql_type.value
    if field.sql_type == SQLType.VARCHAR:
        length = field.max_length or 255
        type_str = f"VARCHAR({length})"
    
    return ColumnDef(
        name=field.name,
        sql_type=type_str,
        nullable=field.nullable,
        default=field.default,
        primary_key=field.primary_key,
        auto_increment=field.auto_increment,
        unique=field.unique,
        foreign_key=field.foreign_key,
    )


class ModelDiffer:
    """
    Detects schema changes between Python models and database.
    
    Usage:
        from pynext.db import _model_registry, get_adapter
        
        differ = ModelDiffer(_model_registry, get_adapter())
        result = await differ.detect()
        
        for change in result.changes:
            print(change.description())
    """
    
    # Similarity threshold for rename detection (0.0 - 1.0)
    RENAME_THRESHOLD = 0.6
    
    def __init__(
        self,
        models: Dict[str, Type["Table"]],
        adapter: "Adapter",
    ):
        """
        Args:
            models: Registry of model classes (table_name -> Model class)
            adapter: Database adapter for schema introspection
        """
        self.models = models
        self.adapter = adapter
    
    async def detect(self) -> DetectionResult:
        """
        Detect all schema changes between models and database.
        
        Returns:
            DetectionResult with changes, ambiguous cases, and warnings
        """
        changes: List[Change] = []
        ambiguous: List[AmbiguousChange] = []
        warnings: List[str] = []
        
        # Get current database schema
        db_tables = await self._get_db_schema()
        
        # Get model definitions
        model_tables = self._get_model_schema()
        
        db_names = set(db_tables.keys())
        model_names = set(model_tables.keys())
        
        # New tables (in models, not in DB)
        new_tables = model_names - db_names
        
        # Dropped tables (in DB, not in models)
        dropped_tables = db_names - model_names
        
        # Handle potential table renames
        renames = self._detect_table_renames(
            new_tables, dropped_tables, model_tables, db_tables
        )
        
        for old_name, new_name in renames:
            # Ask user if this is a rename
            ambiguous.append(AmbiguousChange(
                description=f"Table '{old_name}' gone, '{new_name}' appeared",
                question=f"Did you rename '{old_name}' to '{new_name}'?",
                if_yes=RenameTable(old_name=old_name, new_name=new_name),
                if_no=[
                    DropTable(table=old_name, columns=list(db_tables[old_name].columns.values())),
                    CreateTable(
                        table=new_name,
                        columns=list(model_tables[new_name].columns.values()),
                    ),
                ],
            ))
            new_tables.discard(new_name)
            dropped_tables.discard(old_name)
        
        # Create new tables
        for table_name in new_tables:
            schema = model_tables[table_name]
            changes.append(CreateTable(
                table=table_name,
                columns=list(schema.columns.values()),
            ))
        
        # Drop old tables (with warning about data)
        for table_name in dropped_tables:
            schema = db_tables[table_name]
            if schema.row_count > 0:
                ambiguous.append(AmbiguousChange(
                    description=f"Table '{table_name}' has {schema.row_count} rows",
                    question=f"Drop table '{table_name}' with {schema.row_count} rows?",
                    if_yes=DropTable(table=table_name, columns=list(schema.columns.values())),
                    if_no=[],  # Keep as-is
                ))
            else:
                changes.append(DropTable(
                    table=table_name,
                    columns=list(schema.columns.values()),
                ))
        
        # Check existing tables for column changes
        for table_name in model_names & db_names:
            model_schema = model_tables[table_name]
            db_schema = db_tables[table_name]
            
            table_changes, table_ambiguous = self._detect_column_changes(
                table_name, model_schema, db_schema
            )
            changes.extend(table_changes)
            ambiguous.extend(table_ambiguous)
            
            # Detect index changes
            index_changes = self._detect_index_changes(
                table_name, model_schema, db_schema
            )
            changes.extend(index_changes)
        
        return DetectionResult(
            changes=changes,
            ambiguous=ambiguous,
            warnings=warnings,
        )
    
    def _detect_column_changes(
        self,
        table_name: str,
        model_schema: TableSchema,
        db_schema: TableSchema,
    ) -> Tuple[List[Change], List[AmbiguousChange]]:
        """Detect column-level changes for a table."""
        changes: List[Change] = []
        ambiguous: List[AmbiguousChange] = []
        
        model_cols = set(model_schema.columns.keys())
        db_cols = set(db_schema.columns.keys())
        
        new_cols = model_cols - db_cols
        dropped_cols = db_cols - model_cols
        
        # Detect column renames
        renames = self._detect_column_renames(
            new_cols, dropped_cols, model_schema.columns, db_schema.columns
        )
        
        for old_name, new_name in renames:
            ambiguous.append(AmbiguousChange(
                description=f"Column '{old_name}' gone, '{new_name}' appeared in '{table_name}'",
                question=f"Did you rename '{old_name}' to '{new_name}'?",
                if_yes=RenameColumn(table=table_name, old_name=old_name, new_name=new_name),
                if_no=[
                    DropColumn(table=table_name, column=db_schema.columns[old_name]),
                    AddColumn(table=table_name, column=model_schema.columns[new_name]),
                ],
            ))
            new_cols.discard(new_name)
            dropped_cols.discard(old_name)
        
        # Add new columns
        for col_name in new_cols:
            changes.append(AddColumn(
                table=table_name,
                column=model_schema.columns[col_name],
            ))
        
        # Drop old columns
        for col_name in dropped_cols:
            changes.append(DropColumn(
                table=table_name,
                column=db_schema.columns[col_name],
            ))
        
        # Check for column type/constraint changes
        for col_name in model_cols & db_cols:
            model_col = model_schema.columns[col_name]
            db_col = db_schema.columns[col_name]
            
            if self._column_differs(model_col, db_col):
                # Type narrowing is dangerous
                if self._is_narrowing(db_col.sql_type, model_col.sql_type):
                    ambiguous.append(AmbiguousChange(
                        description=f"Type change '{db_col.sql_type}' → '{model_col.sql_type}' may truncate data",
                        question=f"Change type for '{table_name}.{col_name}'? May lose data.",
                        if_yes=AlterColumn(
                            table=table_name,
                            column_name=col_name,
                            old_type=db_col.sql_type,
                            new_type=model_col.sql_type,
                            old_nullable=db_col.nullable,
                            new_nullable=model_col.nullable,
                            old_default=db_col.default,
                            new_default=model_col.default,
                        ),
                        if_no=[],
                    ))
                else:
                    changes.append(AlterColumn(
                        table=table_name,
                        column_name=col_name,
                        old_type=db_col.sql_type,
                        new_type=model_col.sql_type,
                        old_nullable=db_col.nullable,
                        new_nullable=model_col.nullable,
                        old_default=db_col.default,
                        new_default=model_col.default,
                    ))
        
        return changes, ambiguous
    
    def _detect_index_changes(
        self,
        table_name: str,
        model_schema: TableSchema,
        db_schema: TableSchema,
    ) -> List[Change]:
        """Detect index changes for a table."""
        changes: List[Change] = []
        
        model_indexes = set(model_schema.indexes.keys())
        db_indexes = set(db_schema.indexes.keys())
        
        # New indexes
        for idx_name in model_indexes - db_indexes:
            idx = model_schema.indexes[idx_name]
            changes.append(AddIndex(
                table=table_name,
                columns=idx["columns"],
                unique=idx.get("unique", False),
                name=idx_name,
            ))
        
        # Dropped indexes
        for idx_name in db_indexes - model_indexes:
            idx = db_schema.indexes[idx_name]
            changes.append(DropIndex(
                table=table_name,
                name=idx_name,
                columns=idx.get("columns", []),
                unique=idx.get("unique", False),
            ))
        
        return changes
    
    def _detect_table_renames(
        self,
        new_tables: Set[str],
        dropped_tables: Set[str],
        model_tables: Dict[str, TableSchema],
        db_tables: Dict[str, TableSchema],
    ) -> List[Tuple[str, str]]:
        """
        Detect potential table renames using column similarity.
        
        Returns:
            List of (old_name, new_name) pairs
        """
        renames = []
        
        for old_name in list(dropped_tables):
            old_cols = set(db_tables[old_name].columns.keys())
            
            best_match = None
            best_score = 0.0
            
            for new_name in list(new_tables):
                new_cols = set(model_tables[new_name].columns.keys())
                
                # Jaccard similarity
                intersection = len(old_cols & new_cols)
                union = len(old_cols | new_cols)
                score = intersection / union if union > 0 else 0.0
                
                if score > best_score and score >= self.RENAME_THRESHOLD:
                    best_score = score
                    best_match = new_name
            
            if best_match:
                renames.append((old_name, best_match))
        
        return renames
    
    def _detect_column_renames(
        self,
        new_cols: Set[str],
        dropped_cols: Set[str],
        model_cols: Dict[str, ColumnDef],
        db_cols: Dict[str, ColumnDef],
    ) -> List[Tuple[str, str]]:
        """
        Detect potential column renames using type and name similarity.
        
        Returns:
            List of (old_name, new_name) pairs
        """
        renames = []
        
        for old_name in list(dropped_cols):
            old_col = db_cols[old_name]
            
            best_match = None
            best_score = 0.0
            
            for new_name in list(new_cols):
                new_col = model_cols[new_name]
                
                # Must have same type
                if old_col.sql_type != new_col.sql_type:
                    continue
                
                # Calculate name similarity
                score = self._name_similarity(old_name, new_name)
                
                if score > best_score and score >= self.RENAME_THRESHOLD:
                    best_score = score
                    best_match = new_name
            
            if best_match:
                renames.append((old_name, best_match))
        
        return renames
    
    def _name_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate similarity between two names.
        
        Uses a combination of:
        - Substring matching
        - Character overlap
        - Common word stems
        """
        n1 = name1.lower()
        n2 = name2.lower()
        
        # Exact match (shouldn't happen, but just in case)
        if n1 == n2:
            return 1.0
        
        # Substring match
        if n1 in n2 or n2 in n1:
            return 0.8
        
        # Character-level Jaccard
        chars1 = set(n1)
        chars2 = set(n2)
        intersection = len(chars1 & chars2)
        union = len(chars1 | chars2)
        char_sim = intersection / union if union > 0 else 0.0
        
        return char_sim
    
    def _column_differs(self, model_col: ColumnDef, db_col: ColumnDef) -> bool:
        """Check if a column definition has changed."""
        # Compare normalized types
        model_type = self._normalize_type(model_col.sql_type)
        db_type = self._normalize_type(db_col.sql_type)
        
        if model_type != db_type:
            return True
        
        if model_col.nullable != db_col.nullable:
            return True
        
        # Don't compare defaults strictly - many edge cases
        
        return False
    
    def _normalize_type(self, type_str: str) -> str:
        """Normalize SQL type for comparison."""
        type_str = type_str.upper()
        
        # Normalize VARCHAR variations
        if type_str.startswith("VARCHAR"):
            return "VARCHAR"
        
        # Normalize INTEGER variations
        if type_str in ("INT", "INTEGER", "BIGINT", "SMALLINT"):
            return "INTEGER"
        
        # Normalize REAL variations
        if type_str in ("REAL", "FLOAT", "DOUBLE", "DOUBLE PRECISION"):
            return "REAL"
        
        return type_str
    
    def _is_narrowing(self, old_type: str, new_type: str) -> bool:
        """Check if a type change could lose data."""
        old = old_type.upper()
        new = new_type.upper()
        
        # TEXT -> VARCHAR is narrowing
        if old == "TEXT" and new.startswith("VARCHAR"):
            return True
        
        # BIGINT -> INTEGER is narrowing
        if old == "BIGINT" and new == "INTEGER":
            return True
        
        # DOUBLE -> REAL is narrowing
        if old in ("DOUBLE", "DOUBLE PRECISION") and new == "REAL":
            return True
        
        return False
    
    async def _get_db_schema(self) -> Dict[str, TableSchema]:
        """Get current database schema."""
        # This depends on the adapter - use introspection
        schemas = {}
        
        # Get table list
        try:
            tables = await self._get_table_names()
        except Exception:
            return {}
        
        for table_name in tables:
            try:
                columns = await self._get_table_columns(table_name)
                indexes = await self._get_table_indexes(table_name)
                row_count = await self._get_row_count(table_name)
                
                schemas[table_name] = TableSchema(
                    name=table_name,
                    columns=columns,
                    indexes=indexes,
                    row_count=row_count,
                )
            except Exception:
                continue
        
        return schemas
    
    async def _get_table_names(self) -> List[str]:
        """Get list of tables in database."""
        # SQLite-specific
        try:
            result = await self.adapter.fetch_all(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
            return [row["name"] for row in result]
        except Exception:
            return []
    
    async def _get_table_columns(self, table_name: str) -> Dict[str, ColumnDef]:
        """Get columns for a table."""
        columns = {}
        
        try:
            result = await self.adapter.fetch_all(
                f"PRAGMA table_info({table_name})"
            )
            
            for row in result:
                col = ColumnDef(
                    name=row["name"],
                    sql_type=row["type"],
                    nullable=not row["notnull"],
                    default=row["dflt_value"],
                    primary_key=bool(row["pk"]),
                )
                columns[col.name] = col
        except Exception:
            pass
        
        return columns
    
    async def _get_table_indexes(self, table_name: str) -> Dict[str, Dict]:
        """Get indexes for a table."""
        indexes = {}
        
        try:
            result = await self.adapter.fetch_all(
                f"PRAGMA index_list({table_name})"
            )
            
            for row in result:
                idx_name = row["name"]
                
                # Get columns in index
                cols_result = await self.adapter.fetch_all(
                    f"PRAGMA index_info({idx_name})"
                )
                cols = [r["name"] for r in cols_result]
                
                indexes[idx_name] = {
                    "columns": cols,
                    "unique": bool(row["unique"]),
                }
        except Exception:
            pass
        
        return indexes
    
    async def _get_row_count(self, table_name: str) -> int:
        """Get row count for a table."""
        try:
            result = await self.adapter.fetch_one(
                f"SELECT COUNT(*) as count FROM {table_name}"
            )
            return result["count"] if result else 0
        except Exception:
            return 0
    
    def _get_model_schema(self) -> Dict[str, TableSchema]:
        """Convert model definitions to schemas."""
        schemas = {}
        
        for table_name, model_cls in self.models.items():
            columns = {}
            indexes = {}
            
            for field_name, field_info in model_cls._fields.items():
                columns[field_name] = field_to_column_def(field_info)
                
                # Create index entry if indexed
                if field_info.index and not field_info.primary_key:
                    idx_name = f"ix_{table_name}_{field_name}"
                    indexes[idx_name] = {
                        "columns": [field_name],
                        "unique": field_info.unique,
                    }
            
            schemas[table_name] = TableSchema(
                name=table_name,
                columns=columns,
                indexes=indexes,
            )
        
        return schemas


__all__ = [
    "ModelDiffer",
    "DetectionResult",
    "AmbiguousChange",
    "TableSchema",
    "field_to_column_def",
]

