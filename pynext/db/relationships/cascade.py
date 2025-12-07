"""
PyNext Cascade Options.

Simple, type-safe cascade configuration that's easier than SQLAlchemy.

Design Philosophy:
- Simple presets for 90% of use cases: on_delete="cascade"
- Fine-grained control when needed: CascadeOptions(on_save=True, ...)
- Type-safe: Enum values with IDE autocomplete
- Explicit: No magic strings, clear behavior

SQLAlchemy Comparison:
    SQLAlchemy:
        posts = relationship("Post", cascade="all, delete-orphan")
        # What's in "all"? What if I typo? No IDE help.
    
    PyNext:
        posts = has_many(Post, on_delete="cascade")  # Clear, type-safe
        # OR for fine control:
        posts = has_many(Post, cascade=CascadeOptions(on_delete=True, on_orphan=True))

Usage:
    from pynext.db import Table, has_many, CascadeOptions
    
    class User(Table):
        # Simple preset - delete posts when user deleted
        posts: List[Post] = has_many(Post, on_delete="cascade")
        
        # Nullify FK when deleted
        comments: List[Comment] = has_many(Comment, on_delete="nullify")
        
        # Prevent deletion if has related
        orders: List[Order] = has_many(Order, on_delete="protect")
        
        # Fine-grained control
        audit_logs: List[Log] = has_many(Log, cascade=CascadeOptions(
            on_save=True,    # Save logs when user saved
            on_delete=True,  # Delete logs when user deleted
            on_orphan=True,  # Delete log when removed from collection
        ))
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Set,
    Type,
    TYPE_CHECKING,
    Union,
)

if TYPE_CHECKING:
    from pynext.db.table import Table


# =============================================================================
# Cascade Action Enum (Simple Presets)
# =============================================================================

class OnDeleteAction(str, Enum):
    """
    Simple presets for on_delete behavior.
    
    Use these for 90% of use cases. They're clear, type-safe, and 
    have IDE autocomplete.
    
    Values:
        CASCADE - Delete all related records when parent deleted
        NULLIFY - Set foreign key to NULL when parent deleted
        PROTECT - Raise error if trying to delete with related records
        NONE    - Do nothing (default, let database handle it)
    
    Example:
        posts: List[Post] = has_many(Post, on_delete="cascade")
        profile: Profile = has_one(Profile, on_delete="nullify")
        orders: List[Order] = has_many(Order, on_delete="protect")
    """
    CASCADE = "cascade"
    NULLIFY = "nullify"
    PROTECT = "protect"
    NONE = "none"
    
    @classmethod
    def from_string(cls, value: str) -> "OnDeleteAction":
        """
        Convert string to OnDeleteAction.
        
        Args:
            value: String value like "cascade", "nullify", etc.
        
        Returns:
            Corresponding OnDeleteAction enum value
        
        Raises:
            ValueError: If value is not a valid action
        """
        try:
            return cls(value.lower())
        except ValueError:
            valid = ", ".join(f'"{a.value}"' for a in cls)
            raise ValueError(
                f'Invalid on_delete value: "{value}". '
                f'Valid options: {valid}'
            )


# =============================================================================
# Cascade Options (Fine-Grained Control)
# =============================================================================

@dataclass
class CascadeOptions:
    """
    Fine-grained cascade control for relationships.
    
    Use this when you need more control than the simple on_delete presets.
    
    Attributes:
        on_save: Cascade save to related objects when parent saved
        on_delete: Delete related objects when parent deleted
        on_orphan: Delete related when removed from parent's collection
        on_merge: Cascade merge operations to related objects
    
    Example:
        class User(Table):
            posts: List[Post] = has_many(Post, cascade=CascadeOptions(
                on_save=True,    # user.save() also saves dirty posts
                on_delete=True,  # user.delete() also deletes posts
                on_orphan=True,  # removing post from user.posts deletes it
            ))
    
    Presets:
        CascadeOptions.all()          # All cascades enabled
        CascadeOptions.delete_only()  # Only cascade deletes
        CascadeOptions.save_only()    # Only cascade saves
        CascadeOptions.none()         # No cascades (default)
    """
    
    on_save: bool = False
    on_delete: bool = False
    on_orphan: bool = False
    on_merge: bool = False
    
    # Track what was affected for debugging/logging
    _affected_count: int = field(default=0, repr=False, compare=False)
    
    def __post_init__(self):
        """Validate options."""
        # on_orphan without on_delete is unusual but valid
        pass
    
    # =========================================================================
    # Factory Methods (Presets)
    # =========================================================================
    
    @classmethod
    def all(cls) -> "CascadeOptions":
        """
        All cascades enabled.
        
        Equivalent to SQLAlchemy's cascade="all, delete-orphan".
        
        Returns:
            CascadeOptions with all options True
        """
        return cls(on_save=True, on_delete=True, on_orphan=True, on_merge=True)
    
    @classmethod
    def delete_only(cls) -> "CascadeOptions":
        """
        Only cascade deletes.
        
        Returns:
            CascadeOptions with only on_delete=True
        """
        return cls(on_delete=True)
    
    @classmethod
    def delete_orphan(cls) -> "CascadeOptions":
        """
        Delete on parent delete AND when removed from collection.
        
        Equivalent to SQLAlchemy's cascade="all, delete-orphan".
        
        Returns:
            CascadeOptions with on_delete and on_orphan True
        """
        return cls(on_delete=True, on_orphan=True)
    
    @classmethod
    def save_only(cls) -> "CascadeOptions":
        """
        Only cascade saves.
        
        Returns:
            CascadeOptions with only on_save=True
        """
        return cls(on_save=True)
    
    @classmethod
    def none(cls) -> "CascadeOptions":
        """
        No cascades (default behavior).
        
        Returns:
            CascadeOptions with all options False
        """
        return cls()
    
    @classmethod
    def from_on_delete(cls, action: Union[str, OnDeleteAction]) -> "CascadeOptions":
        """
        Create CascadeOptions from an on_delete preset.
        
        Args:
            action: OnDeleteAction or string like "cascade", "nullify"
        
        Returns:
            CascadeOptions configured for that action
        """
        if isinstance(action, str):
            action = OnDeleteAction.from_string(action)
        
        if action == OnDeleteAction.CASCADE:
            return cls(on_delete=True)
        elif action == OnDeleteAction.NULLIFY:
            # Nullify is handled differently (FK update, not delete)
            return cls()  # No cascade, handled by CascadeManager
        elif action == OnDeleteAction.PROTECT:
            # Protect is handled differently (check before delete)
            return cls()  # No cascade, handled by CascadeManager
        else:
            return cls()  # NONE - no cascade
    
    # =========================================================================
    # Utility Methods
    # =========================================================================
    
    def has_any(self) -> bool:
        """Check if any cascade option is enabled."""
        return self.on_save or self.on_delete or self.on_orphan or self.on_merge
    
    def to_dict(self) -> Dict[str, bool]:
        """Convert to dictionary."""
        return {
            "on_save": self.on_save,
            "on_delete": self.on_delete,
            "on_orphan": self.on_orphan,
            "on_merge": self.on_merge,
        }
    
    def __str__(self) -> str:
        """Human-readable representation."""
        parts = []
        if self.on_save:
            parts.append("save")
        if self.on_delete:
            parts.append("delete")
        if self.on_orphan:
            parts.append("orphan")
        if self.on_merge:
            parts.append("merge")
        
        if not parts:
            return "CascadeOptions(none)"
        return f"CascadeOptions({', '.join(parts)})"


# =============================================================================
# Cascade Result (Tracking)
# =============================================================================

@dataclass
class CascadeResult:
    """
    Result of a cascade operation.
    
    Used for tracking, debugging, and logging what was affected.
    
    Attributes:
        deleted: List of deleted instances
        saved: List of saved instances
        nullified: List of (instance, field) tuples where FK was set to NULL
        errors: List of (instance, error) tuples for failed operations
    """
    
    deleted: List["Table"] = field(default_factory=list)
    saved: List["Table"] = field(default_factory=list)
    nullified: List[tuple] = field(default_factory=list)  # (instance, field_name)
    errors: List[tuple] = field(default_factory=list)  # (instance, error)
    
    @property
    def deleted_count(self) -> int:
        """Number of deleted records."""
        return len(self.deleted)
    
    @property
    def saved_count(self) -> int:
        """Number of saved records."""
        return len(self.saved)
    
    @property
    def nullified_count(self) -> int:
        """Number of nullified FKs."""
        return len(self.nullified)
    
    @property
    def has_errors(self) -> bool:
        """Check if any errors occurred."""
        return len(self.errors) > 0
    
    @property
    def total_affected(self) -> int:
        """Total affected records."""
        return self.deleted_count + self.saved_count + self.nullified_count
    
    def merge(self, other: "CascadeResult") -> "CascadeResult":
        """Merge another result into this one."""
        self.deleted.extend(other.deleted)
        self.saved.extend(other.saved)
        self.nullified.extend(other.nullified)
        self.errors.extend(other.errors)
        return self
    
    def __str__(self) -> str:
        """Human-readable summary."""
        parts = []
        if self.deleted_count:
            parts.append(f"{self.deleted_count} deleted")
        if self.saved_count:
            parts.append(f"{self.saved_count} saved")
        if self.nullified_count:
            parts.append(f"{self.nullified_count} nullified")
        if self.has_errors:
            parts.append(f"{len(self.errors)} errors")
        
        if not parts:
            return "CascadeResult(no changes)"
        return f"CascadeResult({', '.join(parts)})"


# =============================================================================
# Cascade Errors
# =============================================================================

class CascadeError(Exception):
    """Base exception for cascade operations."""
    pass


class ProtectedDeleteError(CascadeError):
    """
    Raised when trying to delete a record that has protected relationships.
    
    Example:
        class User(Table):
            orders: List[Order] = has_many(Order, on_delete="protect")
        
        user = await User.find(1)
        await user.delete()  # Raises ProtectedDeleteError if user has orders
    """
    
    def __init__(
        self,
        instance: "Table",
        relationship: str,
        related_count: int,
    ):
        self.instance = instance
        self.relationship = relationship
        self.related_count = related_count
        
        super().__init__(
            f"Cannot delete {instance.__class__.__name__} (id={getattr(instance, 'id', '?')}): "
            f"has {related_count} protected {relationship}"
        )


class OrphanDeleteError(CascadeError):
    """Raised when orphan deletion fails."""
    pass


# =============================================================================
# Cascade Manager
# =============================================================================

class CascadeManager:
    """
    Manages cascade operations for database models.
    
    This is the core engine that executes cascades when:
    - A model is deleted (cascade delete, nullify, or protect check)
    - A model is saved (cascade save to related)
    - An item is removed from a collection (delete orphan)
    
    Phase 7.4.1: Hybrid Execution
    -----------------------------
    When using PostgresAdapter with FK constraints:
    - on_delete="cascade" → DB handles via ON DELETE CASCADE (skipped here)
    - on_delete="nullify" → DB handles via ON DELETE SET NULL (skipped here)
    - on_delete="protect" → DB handles via ON DELETE RESTRICT (skipped here)
    - on_save, on_orphan, on_merge → App-level only (no DB equivalent)
    
    The manager is typically used internally by Table.delete() and Table.save(),
    but can be accessed directly for advanced use cases.
    
    Usage:
        manager = CascadeManager()
        
        # Before deleting user, handle cascades
        result = await manager.cascade_delete(user)
        print(f"Deleted {result.deleted_count} related records")
        
        # Before saving user, cascade to dirty related
        result = await manager.cascade_save(user)
        print(f"Saved {result.saved_count} related records")
    """
    
    def __init__(self, db_handles_fk: bool = True):
        """
        Initialize the cascade manager.
        
        Args:
            db_handles_fk: If True, skip app-level cascade for on_delete
                          when DB FK constraints handle it (default: True)
        """
        # Track instances being processed to prevent infinite loops
        self._processing: Set[int] = set()
        # Phase 7.4.1: Skip app-level cascade for DB-handled operations
        self._db_handles_fk = db_handles_fk
    
    # =========================================================================
    # Delete Cascades
    # =========================================================================
    
    async def cascade_delete(
        self,
        instance: "Table",
        visited: Optional[Set[int]] = None,
    ) -> CascadeResult:
        """
        Execute delete cascades for an instance.
        
        This handles:
        - @before_delete hooks: Fired before any cascade processing
        - on_delete="cascade": Delete all related records
        - on_delete="nullify": Set FK to NULL on related records
        - on_delete="protect": Raise error if related exist
        
        Phase 7.4.1: Hybrid Execution
        -----------------------------
        When db_handles_fk=True (default), the following are skipped at app-level
        because the database handles them via FK constraints:
        - on_delete="cascade" → ON DELETE CASCADE
        - on_delete="nullify" → ON DELETE SET NULL
        - on_delete="protect" → ON DELETE RESTRICT (DB raises error)
        
        App-level cascades (on_save, on_orphan) still execute here.
        
        Args:
            instance: The Table instance being deleted
            visited: Set of already-visited instance ids (for cycle detection)
        
        Returns:
            CascadeResult with details of what was affected
        
        Raises:
            ProtectedDeleteError: If protected relationships have data (app-level check)
        """
        from pynext.db.relationships.hook_executor import fire_before_delete
        
        result = CascadeResult()
        
        if visited is None:
            visited = set()
        
        instance_id = id(instance)
        if instance_id in visited:
            return result  # Already processed (cycle)
        
        visited.add(instance_id)
        
        # Fire @before_delete hooks before any cascade processing
        fire_before_delete(instance)
        
        # Get all relationship configs with cascade settings
        relationships = self._get_cascade_relationships(instance)
        
        for rel_name, rel_config in relationships.items():
            on_delete = rel_config.get("on_delete", "none")
            cascade_opts = rel_config.get("cascade")
            
            # Phase 7.4.1: Skip app-level cascade for DB-handled operations
            # The DB FK constraints handle cascade/nullify/protect automatically
            if self._db_handles_fk and on_delete in ("cascade", "nullify", "protect"):
                # DB handles it - skip app-level cascade
                # Note: For "protect", DB will raise ForeignKeyViolationError
                # which PostgresAdapter translates to ProtectedDeleteError
                continue
            
            # Get related items (only for app-level cascades)
            related = await self._get_related(instance, rel_name)
            if not related:
                continue
            
            # Ensure it's a list
            if not isinstance(related, list):
                related = [related]
            
            # Handle based on action (only if not DB-handled)
            if on_delete == "protect" and not self._db_handles_fk:
                raise ProtectedDeleteError(
                    instance=instance,
                    relationship=rel_name,
                    related_count=len(related),
                )
            
            elif (on_delete == "cascade" or (cascade_opts and cascade_opts.on_delete)) and not self._db_handles_fk:
                # Delete all related (app-level)
                for item in related:
                    # Recursively cascade delete
                    sub_result = await self.cascade_delete(item, visited)
                    result.merge(sub_result)
                    
                    # Delete the item itself
                    await self._delete_item(item)
                    result.deleted.append(item)
            
            elif on_delete == "nullify" and not self._db_handles_fk:
                # Set FK to NULL (app-level)
                fk_field = rel_config.get("foreign_key")
                if fk_field:
                    for item in related:
                        await self._nullify_fk(item, fk_field)
                        result.nullified.append((item, fk_field))
        
        return result
    
    async def check_protected(self, instance: "Table") -> Optional[ProtectedDeleteError]:
        """
        Check if any protected relationships would block deletion.
        
        Use this before delete to check without actually cascading.
        
        Args:
            instance: The Table instance to check
        
        Returns:
            ProtectedDeleteError if protected, None if safe to delete
        """
        relationships = self._get_cascade_relationships(instance)
        
        for rel_name, rel_config in relationships.items():
            if rel_config.get("on_delete") == "protect":
                related = await self._get_related(instance, rel_name)
                if related:
                    count = len(related) if isinstance(related, list) else 1
                    return ProtectedDeleteError(instance, rel_name, count)
        
        return None
    
    # =========================================================================
    # Save Cascades
    # =========================================================================
    
    async def cascade_save(
        self,
        instance: "Table",
        visited: Optional[Set[int]] = None,
    ) -> CascadeResult:
        """
        Execute save cascades for an instance.
        
        Saves any related objects that have cascade.on_save=True
        and are marked as dirty.
        
        Args:
            instance: The Table instance being saved
            visited: Set of already-visited instance ids (for cycle detection)
        
        Returns:
            CascadeResult with details of what was saved
        """
        result = CascadeResult()
        
        if visited is None:
            visited = set()
        
        instance_id = id(instance)
        if instance_id in visited:
            return result
        
        visited.add(instance_id)
        
        relationships = self._get_cascade_relationships(instance)
        
        for rel_name, rel_config in relationships.items():
            cascade_opts = rel_config.get("cascade")
            
            if not cascade_opts or not cascade_opts.on_save:
                continue
            
            related = await self._get_related(instance, rel_name)
            if not related:
                continue
            
            if not isinstance(related, list):
                related = [related]
            
            for item in related:
                if self._is_dirty(item):
                    # Recursively cascade save
                    sub_result = await self.cascade_save(item, visited)
                    result.merge(sub_result)
                    
                    # Save the item
                    await self._save_item(item)
                    result.saved.append(item)
        
        return result
    
    # =========================================================================
    # Orphan Handling
    # =========================================================================
    
    def schedule_orphan_delete(
        self,
        item: "Table",
        parent: "Table",
        rel_name: str,
    ) -> None:
        """
        Schedule an orphan for deletion.
        
        Called when an item is removed from a collection that has
        cascade.on_orphan=True.
        
        Args:
            item: The removed item
            parent: The parent it was removed from
            rel_name: The relationship name
        """
        # Store orphan info on the item for later deletion
        if not hasattr(item, "_pending_orphan_delete"):
            item._pending_orphan_delete = True
            item._orphan_parent = parent
            item._orphan_relationship = rel_name
    
    async def execute_orphan_deletes(
        self,
        items: List["Table"],
    ) -> CascadeResult:
        """
        Execute pending orphan deletes.
        
        Args:
            items: List of items that may be orphans
        
        Returns:
            CascadeResult with deleted orphans
        """
        result = CascadeResult()
        
        for item in items:
            if getattr(item, "_pending_orphan_delete", False):
                try:
                    await self._delete_item(item)
                    result.deleted.append(item)
                except Exception as e:
                    result.errors.append((item, e))
                finally:
                    # Clear orphan markers
                    if hasattr(item, "_pending_orphan_delete"):
                        del item._pending_orphan_delete
                    if hasattr(item, "_orphan_parent"):
                        del item._orphan_parent
                    if hasattr(item, "_orphan_relationship"):
                        del item._orphan_relationship
        
        return result
    
    # =========================================================================
    # Helper Methods
    # =========================================================================
    
    def _get_cascade_relationships(
        self,
        instance: "Table",
    ) -> Dict[str, Dict[str, Any]]:
        """Get all relationships with cascade settings."""
        result = {}
        
        # Check class for relationship descriptors
        for attr_name in dir(instance.__class__):
            if attr_name.startswith("_"):
                continue
            
            attr = getattr(instance.__class__, attr_name, None)
            if attr is None:
                continue
            
            # Check if it's a relationship descriptor
            if hasattr(attr, "on_delete") or hasattr(attr, "cascade"):
                result[attr_name] = {
                    "on_delete": getattr(attr, "on_delete", "none"),
                    "cascade": getattr(attr, "cascade", None),
                    "foreign_key": getattr(attr, "foreign_key", None),
                    "rel_type": getattr(attr, "rel_type", None),
                }
        
        return result
    
    async def _get_related(
        self,
        instance: "Table",
        rel_name: str,
    ) -> Optional[Union["Table", List["Table"]]]:
        """Get related objects for a relationship."""
        try:
            related = getattr(instance, rel_name)
            
            # Handle lazy loading
            if hasattr(related, "__await__"):
                related = await related
            
            # Handle collections
            if hasattr(related, "_items"):
                return list(related._items)
            elif hasattr(related, "__iter__") and not isinstance(related, (str, bytes)):
                return list(related)
            
            return related
        except Exception:
            return None
    
    async def _delete_item(self, item: "Table") -> None:
        """Delete a single item."""
        if hasattr(item, "delete"):
            # Skip cascade on the item itself to prevent recursion
            await item.delete(_skip_cascade=True)
        # If no delete method, it's an in-memory object, no action needed
    
    async def _save_item(self, item: "Table") -> None:
        """Save a single item."""
        if hasattr(item, "save"):
            await item.save(_skip_cascade=True)
    
    async def _nullify_fk(self, item: "Table", fk_field: str) -> None:
        """Set a foreign key to NULL."""
        if hasattr(item, fk_field):
            setattr(item, fk_field, None)
            if hasattr(item, "save"):
                await item.save(_skip_cascade=True)
    
    def _is_dirty(self, item: "Table") -> bool:
        """Check if an item has unsaved changes."""
        return getattr(item, "_dirty", False)


# =============================================================================
# Global Manager Instance
# =============================================================================

_cascade_manager: Optional[CascadeManager] = None


def get_cascade_manager() -> CascadeManager:
    """Get the global cascade manager instance."""
    global _cascade_manager
    if _cascade_manager is None:
        _cascade_manager = CascadeManager()
    return _cascade_manager


def reset_cascade_manager() -> None:
    """Reset the global cascade manager (for testing)."""
    global _cascade_manager
    _cascade_manager = None


# =============================================================================
# Convenience Functions
# =============================================================================

def cascade_options(
    on_save: bool = False,
    on_delete: bool = False,
    on_orphan: bool = False,
    on_merge: bool = False,
) -> CascadeOptions:
    """
    Create cascade options with a functional API.
    
    Example:
        posts = has_many(Post, cascade=cascade_options(on_delete=True, on_orphan=True))
    
    Args:
        on_save: Cascade save operations
        on_delete: Cascade delete operations
        on_orphan: Delete when removed from collection
        on_merge: Cascade merge operations
    
    Returns:
        CascadeOptions instance
    """
    return CascadeOptions(
        on_save=on_save,
        on_delete=on_delete,
        on_orphan=on_orphan,
        on_merge=on_merge,
    )

