"""
PyNext Live Query - Update Strategy Base.

Abstract base class for update strategies.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Generic, List, Type, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from pynext.db.table import Table
    from pynext.db.live.detection.base import ChangeEvent
    from pynext.db.live.config import QuerySignature

T = TypeVar("T", bound="Table")


@dataclass
class UpdateResult(Generic[T]):
    """
    Result of applying an update strategy.
    
    Attributes:
        changed: Whether the data changed
        data: The updated list of results
        data_by_id: Dict mapping id -> row for efficient lookup
        added: IDs of newly added rows
        updated: IDs of updated rows
        removed: IDs of removed rows
    """
    changed: bool
    data: List[T]
    data_by_id: Dict[int, T]
    added: List[int] = field(default_factory=list)
    updated: List[int] = field(default_factory=list)
    removed: List[int] = field(default_factory=list)
    
    @property
    def change_count(self) -> int:
        """Total number of changes."""
        return len(self.added) + len(self.updated) + len(self.removed)
    
    @classmethod
    def no_change(
        cls,
        data: List[T],
        data_by_id: Dict[int, T],
    ) -> "UpdateResult[T]":
        """Create a result indicating no change."""
        return cls(
            changed=False,
            data=data,
            data_by_id=data_by_id,
        )


class UpdateStrategy(ABC, Generic[T]):
    """
    Abstract base class for update strategies.
    
    Strategies determine how to apply a change event to the current data.
    
    Implementations:
    - SurgicalUpdate: Efficient add/update/remove of individual items
    - FullRefresh: Re-run the entire query
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name for this strategy."""
        pass
    
    @abstractmethod
    def apply(
        self,
        current_data: List[T],
        current_by_id: Dict[int, T],
        event: "ChangeEvent",
        model: Type[T],
    ) -> UpdateResult[T]:
        """
        Apply a change event to the current data.
        
        Args:
            current_data: Current list of results
            current_by_id: Dict mapping id -> row
            event: The change event to apply
            model: The model class
        
        Returns:
            UpdateResult with the new data
        """
        pass
    
    def can_apply(
        self,
        event: "ChangeEvent",
        signature: "QuerySignature",
    ) -> bool:
        """
        Check if this strategy can handle the given event.
        
        Override in subclasses for strategy-specific logic.
        """
        return True

