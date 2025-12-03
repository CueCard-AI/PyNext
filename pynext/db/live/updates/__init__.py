"""
PyNext Live Query - Update Strategies.

Determines how to apply database changes to query results.

Strategies:
- SurgicalUpdate: Add/update/remove individual items (most efficient)
- FullRefresh: Re-run the entire query (most accurate)

The StrategySelector picks the best strategy based on:
- Query type (simple vs complex)
- Change type (insert/update/delete)
- Query characteristics (filters, ordering, limits)

Usage:
    from pynext.db.live.updates import get_strategy_selector
    
    selector = get_strategy_selector()
    strategy = selector.select(signature, event, config)
    result = strategy.apply(current_data, event, model)
"""

from pynext.db.live.updates.base import (
    UpdateStrategy,
    UpdateResult,
)

from pynext.db.live.updates.selector import (
    StrategySelector,
    get_strategy_selector,
)

__all__ = [
    "UpdateStrategy",
    "UpdateResult",
    "StrategySelector",
    "get_strategy_selector",
]

