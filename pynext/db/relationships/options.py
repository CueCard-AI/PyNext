"""
PyNext Query Loading Options.

Convenience functions for creating LoadOptions at query time.

Design Philosophy:
- Dead simple API: just call the function with the relationship name
- Chainable for nested loading: selectinload("posts").joinedload("author")
- Explicit strategy names match the lazy= parameter values
- AI-friendly: function names describe exactly what they do

Usage:
    from pynext.db import joinedload, selectinload, subqueryload
    
    # Simple eager loading
    users = await User.select().options(
        selectinload("posts"),
        joinedload("profile"),
    )
    
    # Nested loading
    users = await User.select().options(
        selectinload("posts").joinedload("author").selectinload("comments"),
    )
    
    # Prevent N+1 in production
    users = await User.select().options(
        raiseload("audit_logs"),  # Will raise if accessed
    )
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pynext.db.relationships.loading import LoadOption, LoadStrategy

if TYPE_CHECKING:
    pass


def joinedload(relationship: str) -> LoadOption:
    """
    Load a relationship using LEFT JOIN.
    
    Best for:
        - belongs_to relationships
        - has_one relationships
        - When you need the data immediately in the same query
    
    Trade-offs:
        - Single query (good)
        - Can cause duplicate rows for has_many (use selectin instead)
        - Always loads the data
    
    Args:
        relationship: Name of the relationship to load
        
    Returns:
        LoadOption configured for joined loading
    
    Example:
        # Load user with their profile in one query
        user = await User.select().options(
            joinedload("profile")
        ).where(id=1).first()
        
        # Nested: load author with their company
        posts = await Post.select().options(
            joinedload("author").joinedload("company")
        )
    """
    return LoadOption(relationship, LoadStrategy.JOINED)


def selectinload(relationship: str) -> LoadOption:
    """
    Load a relationship using SELECT WHERE id IN (...).
    
    Best for:
        - has_many relationships
        - Loading multiple parent objects at once
        - Most common eager loading choice
    
    Trade-offs:
        - 2 queries (one for parents, one for children)
        - Efficient for batches
        - No duplicate rows
    
    Args:
        relationship: Name of the relationship to load
        
    Returns:
        LoadOption configured for selectin loading
    
    Example:
        # Load users with all their posts
        users = await User.select().options(
            selectinload("posts")
        ).where(active=True)
        
        # Each user.posts is populated with their posts
        for user in users:
            print(f"{user.name} has {len(user.posts)} posts")
        
        # Nested: load posts with their comments
        users = await User.select().options(
            selectinload("posts").selectinload("comments")
        )
    """
    return LoadOption(relationship, LoadStrategy.SELECTIN)


def subqueryload(relationship: str) -> LoadOption:
    """
    Load a relationship using a subquery.
    
    Best for:
        - Complex queries with many filters
        - Deep nesting where selectin might have duplicate IDs
        - When you want consistent behavior with pagination
    
    Trade-offs:
        - Subquery might be slower than selectin for simple cases
        - Better for complex parent queries
    
    Args:
        relationship: Name of the relationship to load
        
    Returns:
        LoadOption configured for subquery loading
    
    Example:
        # Load with subquery (useful for complex parent queries)
        users = await User.select().options(
            subqueryload("posts")
        ).where_like(email="%@company.com%").order_by("-created_at").limit(100)
        
        # Nested loading
        users = await User.select().options(
            subqueryload("posts").subqueryload("comments")
        )
    """
    return LoadOption(relationship, LoadStrategy.SUBQUERY)


def raiseload(relationship: str) -> LoadOption:
    """
    Raise an error if the relationship is accessed.
    
    Best for:
        - Preventing N+1 queries in production
        - Making lazy loads explicit and intentional
        - Debugging performance issues
    
    Use this when:
        - You want to ensure all needed data is eager loaded
        - You're optimizing a slow endpoint
        - You want to catch unintended lazy loads
    
    Args:
        relationship: Name of the relationship to block
        
    Returns:
        LoadOption configured to raise on access
    
    Example:
        # Prevent N+1 - this will raise if posts is accessed
        users = await User.select().options(
            raiseload("posts")
        ).where(active=True)
        
        for user in users:
            # This would raise LazyLoadError!
            # print(user.posts)
            pass
        
        # To fix, add selectinload:
        users = await User.select().options(
            selectinload("posts"),  # Now it's eager loaded
            raiseload("audit_logs"),  # Still blocked
        )
    """
    return LoadOption(relationship, LoadStrategy.RAISE)


def noload(relationship: str) -> LoadOption:
    """
    Don't load the relationship at all.
    
    Best for:
        - Explicitly marking that a relationship should not be loaded
        - Overriding a model-level eager loading default
        - When you know you won't need the data
    
    Note:
        The relationship will return None or empty list when accessed.
        It won't trigger a lazy load.
    
    Args:
        relationship: Name of the relationship to skip
        
    Returns:
        LoadOption configured for no loading
    
    Example:
        # Don't load posts even if model has lazy="selectin"
        users = await User.select().options(
            noload("posts")
        ).where(active=True)
        
        # user.posts will be None/empty, no query executed
    """
    return LoadOption(relationship, LoadStrategy.SELECT)


def lazyload(relationship: str) -> LoadOption:
    """
    Use default lazy loading (query on first access).
    
    This is the default behavior, but can be used to explicitly
    override a model-level eager loading setting.
    
    Best for:
        - Relationships that are rarely accessed
        - Overriding model defaults when lazy loading is desired
    
    Warning:
        Can cause N+1 queries if accessed in a loop!
    
    Args:
        relationship: Name of the relationship
        
    Returns:
        LoadOption configured for lazy loading
    
    Example:
        # Override model's lazy="selectin" to use lazy loading
        users = await User.select().options(
            lazyload("rarely_used_relation")
        )
    """
    return LoadOption(relationship, LoadStrategy.SELECT)


def immediateload(relationship: str) -> LoadOption:
    """
    Alias for selectinload - load immediately after parent query.
    
    This is a more descriptive name for selectinload that some
    developers prefer.
    
    Args:
        relationship: Name of the relationship to load
        
    Returns:
        LoadOption configured for immediate loading
    """
    return LoadOption(relationship, LoadStrategy.SELECTIN)


def eagerload(relationship: str) -> LoadOption:
    """
    Alias for selectinload - eager load the relationship.
    
    This is a common term from other ORMs.
    
    Args:
        relationship: Name of the relationship to load
        
    Returns:
        LoadOption configured for eager loading
    """
    return LoadOption(relationship, LoadStrategy.SELECTIN)


# Convenience class for attribute-based access
class Load:
    """
    Alternative API using model attributes.
    
    Some developers prefer using model attributes instead of strings.
    This class provides that interface.
    
    Note: This requires the relationship descriptor, not a string.
    
    Example:
        from pynext.db import Load
        
        users = await User.select().options(
            Load(User.posts).selectin(),
            Load(User.profile).joined(),
        )
    """
    
    def __init__(self, relationship):
        """
        Initialize with a relationship descriptor or string.
        
        Args:
            relationship: Either a string name or descriptor
        """
        if isinstance(relationship, str):
            self._name = relationship
        elif hasattr(relationship, "rel_name"):
            self._name = relationship.rel_name
        else:
            # Assume it's a descriptor with __name__
            self._name = getattr(relationship, "__name__", str(relationship))
    
    def selectin(self) -> LoadOption:
        """Use SELECT IN loading."""
        return selectinload(self._name)
    
    def joined(self) -> LoadOption:
        """Use JOIN loading."""
        return joinedload(self._name)
    
    def subquery(self) -> LoadOption:
        """Use subquery loading."""
        return subqueryload(self._name)
    
    def raise_(self) -> LoadOption:
        """Raise on access."""
        return raiseload(self._name)
    
    def noload(self) -> LoadOption:
        """Don't load."""
        return noload(self._name)


# Export all public functions
__all__ = [
    "joinedload",
    "selectinload",
    "subqueryload",
    "raiseload",
    "noload",
    "lazyload",
    "immediateload",
    "eagerload",
    "Load",
]

