"""
PyNext Live Query - Strategy Selector.

Automatically selects the best update strategy for a query change.

Selection Logic:
┌─────────────────────────────────────────────────────────┐
│ Scenario                      │ Strategy               │
├───────────────────────────────┼────────────────────────┤
│ Simple list (User.all())      │ Surgical (add/remove)  │
│ Filtered (.where())           │ Re-evaluate + surgical │
│ Ordered (.order_by())         │ Re-sort + surgical     │
│ Limited (.limit())            │ Full refresh           │
│ Aggregations (.count())       │ Full refresh           │
│ Joins (.with_related())       │ Full refresh           │
└─────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from pynext.db.live.updates.base import UpdateStrategy
from pynext.db.live.updates.surgical import SurgicalUpdate
from pynext.db.live.updates.refresh import FullRefresh
from pynext.db.live.config import UpdateGranularity

if TYPE_CHECKING:
    from pynext.db.live.detection.base import ChangeEvent
    from pynext.db.live.config import QuerySignature, LiveQueryConfig


class StrategySelector:
    """
    Selects the best update strategy for a query change.
    
    The selector considers:
    - Query complexity (filters, ordering, limits)
    - Change type (INSERT, UPDATE, DELETE)
    - Which columns changed
    - Configuration preferences
    """
    
    def __init__(self):
        self._surgical = SurgicalUpdate()
        self._refresh = FullRefresh()
    
    def select(
        self,
        signature: "QuerySignature",
        event: "ChangeEvent",
        config: "LiveQueryConfig",
    ) -> UpdateStrategy:
        """
        Select the best strategy for this event.
        
        Args:
            signature: The query signature
            event: The change event
            config: Live query configuration
        
        Returns:
            The selected update strategy
        """
        # Check configuration preference
        if config.granularity == UpdateGranularity.SURGICAL:
            return self._surgical
        elif config.granularity == UpdateGranularity.REFRESH:
            return self._refresh
        
        # AUTO mode - decide based on query characteristics
        
        # Limited queries always need refresh
        # (changes may affect which items are in top N)
        if signature.has_limit:
            return self._refresh
        
        # Simple queries (no filters, ordering) use surgical
        if signature.is_simple:
            return self._surgical
        
        # Check if surgical update can handle this event
        if self._surgical.can_apply(event, signature):
            return self._surgical
        
        # Default to refresh
        return self._refresh
    
    def get_strategy(self, name: str) -> Optional[UpdateStrategy]:
        """Get a strategy by name."""
        if name.lower() == "surgical":
            return self._surgical
        elif name.lower() in ("refresh", "fullrefresh", "full_refresh"):
            return self._refresh
        return None


# Global selector instance
_selector: Optional[StrategySelector] = None


def get_strategy_selector() -> StrategySelector:
    """Get the global strategy selector."""
    global _selector
    if _selector is None:
        _selector = StrategySelector()
    return _selector

