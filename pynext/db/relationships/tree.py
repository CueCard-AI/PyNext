"""
PyNext Tree Mixin for Self-Referential Relationships.

Provides tree traversal helpers for parent-child hierarchies.
Dramatically simpler than SQLAlchemy - no remote_side confusion!

Design Philosophy:
- TreeMixin adds all tree methods to any model with parent_id
- Hybrid strategy: CTE for PostgreSQL, app-level fallback for others
- Runtime path computation (no extra columns, no sync issues)
- Intuitive API that any developer can understand

Usage:
    from pynext.db import Table, TreeMixin
    
    class Category(Table, TreeMixin):
        name: str
        parent_id: Optional[int]
    
    # Now has all tree methods:
    category.is_root              # True if no parent
    category.path                 # "Electronics/Computers/Laptops"
    await category.ancestors()    # [Parent, Grandparent, Root]
    await category.descendants()  # All children recursively
    await category.root()         # Root node of this tree
    await category.depth()        # Level (root=0)
    await category.is_leaf()      # True if no children
    await category.siblings()     # Nodes with same parent

SQLAlchemy Comparison:
    SQLAlchemy (confusing):
        children = relationship("Node", backref=backref("parent", remote_side=[id]))
        # Then write your own CTE for ancestors/descendants
    
    PyNext (simple):
        class Node(Table, TreeMixin):
            parent_id: Optional[int]
        # Done! All tree methods available.
"""

from __future__ import annotations

from typing import (
    Any,
    Callable,
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

T = TypeVar("T", bound="Table")


class TreeMixin:
    """
    Mixin that adds tree traversal methods to self-referential models.
    
    Requirements:
        - Model must have a `parent_id` field (Optional[int])
        - Model should have `parent` and `children` relationships
          (auto-detected or explicitly defined)
    
    Properties (sync, no DB):
        is_root     - True if parent_id is None
        path        - Path string like "Root/Parent/Child"
        path_ids    - List of IDs from root to this node
    
    Methods (async, DB calls):
        ancestors() - Get all ancestors from parent to root
        descendants() - Get all descendants recursively
        root()      - Get the root node of this tree
        depth()     - Get depth level (root=0)
        is_leaf()   - True if no children
        siblings()  - Get nodes with same parent
        subtree()   - Get this node and all descendants
    
    Configuration:
        _tree_parent_field  - Field name for parent reference (default: "parent_id")
        _tree_name_field    - Field name for path display (default: "name" or "title" or "id")
        _tree_separator     - Path separator (default: "/")
    
    Example:
        class Category(Table, TreeMixin):
            name: str
            parent_id: Optional[int]
            
            # Optional: customize path field
            _tree_name_field = "name"
        
        cat = await Category.get(5)
        print(cat.is_root)           # False
        print(cat.path)              # "Electronics/Computers/Laptops"
        ancestors = await cat.ancestors()  # [Computers, Electronics]
    """
    
    # Configuration (override in subclass if needed)
    _tree_parent_field: str = "parent_id"
    _tree_name_field: str = "name"  # Falls back to "title", then "id"
    _tree_separator: str = "/"
    
    # Cache for ancestors (populated on first access)
    _cached_ancestors: Optional[List] = None
    
    # ==========================================================================
    # Sync Properties (No DB Call)
    # ==========================================================================
    
    @property
    def is_root(self) -> bool:
        """
        Check if this node is a root (has no parent).
        
        Returns:
            True if parent_id is None
        
        Example:
            if category.is_root:
                print("This is a top-level category")
        """
        parent_id = getattr(self, self._tree_parent_field, None)
        return parent_id is None
    
    @property
    def path(self) -> str:
        """
        Get the path from root to this node.
        
        Computed at runtime by walking up the parent chain.
        Uses cached ancestors if available.
        
        Returns:
            Path string like "Root/Parent/Child"
        
        Example:
            print(category.path)  # "Electronics/Computers/Laptops"
        
        Note:
            This is a sync property that uses cached ancestors.
            Call ancestors() first to populate the cache for accurate path.
        """
        # Try to use cached ancestors
        if hasattr(self, '_cached_ancestors') and self._cached_ancestors is not None:
            names = [self._get_node_name(a) for a in reversed(self._cached_ancestors)]
            names.append(self._get_node_name(self))
            return self._tree_separator.join(names)
        
        # No cache - just return this node's name
        return self._get_node_name(self)
    
    @property
    def path_ids(self) -> List[int]:
        """
        Get list of IDs from root to this node.
        
        Returns:
            List of IDs like [1, 5, 12] (root to current)
        
        Example:
            ids = category.path_ids  # [1, 5, 12]
        
        Note:
            Uses cached ancestors. Call ancestors() first for complete path.
        """
        if hasattr(self, '_cached_ancestors') and self._cached_ancestors is not None:
            ids = [getattr(a, 'id') for a in reversed(self._cached_ancestors)]
            ids.append(getattr(self, 'id'))
            return ids
        
        # No cache - just return this node's ID
        node_id = getattr(self, 'id', None)
        return [node_id] if node_id else []
    
    def _get_node_name(self, node: Any) -> str:
        """Get display name for a node."""
        # Try configured field first (if value is not None)
        if hasattr(node, self._tree_name_field):
            val = getattr(node, self._tree_name_field)
            if val is not None:
                return str(val)
        
        # Fallback: try common name fields
        for field in ('name', 'title', 'label'):
            if hasattr(node, field):
                val = getattr(node, field)
                if val is not None:
                    return str(val)
        
        # Last resort: use ID
        return str(getattr(node, 'id', '?'))
    
    # ==========================================================================
    # Async Methods (DB Calls)
    # ==========================================================================
    
    async def ancestors(
        self,
        include_self: bool = False,
        use_cte: Optional[bool] = None,
    ) -> List["TreeMixin"]:
        """
        Get all ancestors from parent to root.
        
        Args:
            include_self: Include this node in the result (default: False)
            use_cte: Force CTE (True) or app-level (False). None = auto-detect.
        
        Returns:
            List of ancestor nodes, ordered from parent to root.
            [Parent, Grandparent, ..., Root]
        
        Example:
            # For: Root > Electronics > Computers > Laptops
            laptop = await Category.get(id=4)
            ancestors = await laptop.ancestors()
            # Returns: [Computers, Electronics, Root]
            
            # Include self
            path = await laptop.ancestors(include_self=True)
            # Returns: [Laptops, Computers, Electronics, Root]
        
        Performance:
            - PostgreSQL: Single recursive CTE query
            - Other DBs: Multiple queries (one per level)
        """
        if self.is_root:
            return [self] if include_self else []
        
        # Determine strategy
        if use_cte is None:
            use_cte = await self._supports_cte()
        
        if use_cte:
            ancestors = await self._ancestors_cte()
        else:
            ancestors = await self._ancestors_app_level()
        
        # Cache for path property
        self._cached_ancestors = ancestors
        
        if include_self:
            return [self] + ancestors
        return ancestors
    
    async def _ancestors_cte(self) -> List["TreeMixin"]:
        """Fetch ancestors using PostgreSQL recursive CTE."""
        from pynext.db.relationships.tree_query import TreeQueryBuilder
        
        model_class = type(self)
        node_id = getattr(self, 'id')
        parent_field = self._tree_parent_field
        
        builder = TreeQueryBuilder()
        query, params = builder.ancestors_query(
            model_class,
            node_id,
            parent_field,
        )
        
        # Execute raw query
        adapter = await self._get_adapter()
        rows = await adapter.fetch(query, *params)
        
        # Convert rows to model instances
        return [model_class(**dict(row)) for row in rows]
    
    async def _ancestors_app_level(self) -> List["TreeMixin"]:
        """Fetch ancestors by walking up the parent chain."""
        ancestors = []
        model_class = type(self)
        current_parent_id = getattr(self, self._tree_parent_field)
        
        # Walk up the tree
        while current_parent_id is not None:
            # Fetch parent
            parent = await model_class.get(current_parent_id)
            if parent is None:
                break
            
            ancestors.append(parent)
            current_parent_id = getattr(parent, self._tree_parent_field)
        
        return ancestors
    
    async def descendants(
        self,
        include_self: bool = False,
        use_cte: Optional[bool] = None,
        max_depth: Optional[int] = None,
    ) -> List["TreeMixin"]:
        """
        Get all descendants recursively.
        
        Args:
            include_self: Include this node in the result (default: False)
            use_cte: Force CTE (True) or app-level (False). None = auto-detect.
            max_depth: Maximum depth to traverse (None = unlimited)
        
        Returns:
            List of all descendant nodes (breadth-first order)
        
        Example:
            # For: Root > [A > [A1, A2], B > [B1]]
            root = await Category.get(id=1)
            all_children = await root.descendants()
            # Returns: [A, B, A1, A2, B1]
            
            # Limit depth
            direct = await root.descendants(max_depth=1)
            # Returns: [A, B]
        
        Performance:
            - PostgreSQL: Single recursive CTE query
            - Other DBs: Multiple queries (one per level)
        """
        # Determine strategy
        if use_cte is None:
            use_cte = await self._supports_cte()
        
        if use_cte:
            descendants = await self._descendants_cte(max_depth)
        else:
            descendants = await self._descendants_app_level(max_depth)
        
        if include_self:
            return [self] + descendants
        return descendants
    
    async def _descendants_cte(
        self,
        max_depth: Optional[int] = None,
    ) -> List["TreeMixin"]:
        """Fetch descendants using PostgreSQL recursive CTE."""
        from pynext.db.relationships.tree_query import TreeQueryBuilder
        
        model_class = type(self)
        node_id = getattr(self, 'id')
        parent_field = self._tree_parent_field
        
        builder = TreeQueryBuilder()
        query, params = builder.descendants_query(
            model_class,
            node_id,
            parent_field,
            max_depth,
        )
        
        # Execute raw query
        adapter = await self._get_adapter()
        rows = await adapter.fetch(query, *params)
        
        # Convert rows to model instances
        return [model_class(**dict(row)) for row in rows]
    
    async def _descendants_app_level(
        self,
        max_depth: Optional[int] = None,
    ) -> List["TreeMixin"]:
        """Fetch descendants by walking down the tree (BFS)."""
        model_class = type(self)
        descendants = []
        current_level = [self]
        current_depth = 0
        
        while current_level:
            if max_depth is not None and current_depth >= max_depth:
                break
            
            # Get IDs of current level
            current_ids = [getattr(n, 'id') for n in current_level]
            
            # Fetch all children of current level
            children = await model_class.select().where_in(
                **{self._tree_parent_field: current_ids}
            )
            
            if not children:
                break
            
            descendants.extend(children)
            current_level = children
            current_depth += 1
        
        return descendants
    
    async def root(self) -> "TreeMixin":
        """
        Get the root node of this tree.
        
        Returns:
            The root ancestor (or self if this is root)
        
        Example:
            laptop = await Category.get(id=4)
            root = await laptop.root()
            print(root.name)  # "Electronics"
        """
        if self.is_root:
            return self
        
        ancestors = await self.ancestors()
        if ancestors:
            return ancestors[-1]  # Last one is root
        return self
    
    async def depth(self) -> int:
        """
        Get the depth level of this node (root = 0).
        
        Returns:
            Depth level as integer
        
        Example:
            # Root > Electronics > Computers > Laptops
            laptop = await Category.get(id=4)
            print(await laptop.depth())  # 3
        """
        if self.is_root:
            return 0
        
        ancestors = await self.ancestors()
        return len(ancestors)
    
    async def is_leaf(self) -> bool:
        """
        Check if this node has no children.
        
        Returns:
            True if no children exist
        
        Example:
            if await category.is_leaf():
                print("This category has no subcategories")
        """
        model_class = type(self)
        node_id = getattr(self, 'id')
        
        # Check if any children exist
        count = await model_class.select().where(
            **{self._tree_parent_field: node_id}
        ).count()
        
        return count == 0
    
    async def siblings(
        self,
        include_self: bool = False,
    ) -> List["TreeMixin"]:
        """
        Get nodes with the same parent.
        
        Args:
            include_self: Include this node in the result (default: False)
        
        Returns:
            List of sibling nodes
        
        Example:
            # If Computers has siblings: Phones, TVs
            computers = await Category.get(id=2)
            siblings = await computers.siblings()
            # Returns: [Phones, TVs]
        """
        model_class = type(self)
        parent_id = getattr(self, self._tree_parent_field)
        node_id = getattr(self, 'id')
        
        # Get all nodes with same parent
        if parent_id is None:
            # Root level - get all roots
            query = model_class.select().where_null(self._tree_parent_field)
        else:
            query = model_class.select().where(
                **{self._tree_parent_field: parent_id}
            )
        
        siblings = await query
        
        # Filter out self if requested
        if not include_self:
            siblings = [s for s in siblings if getattr(s, 'id') != node_id]
        
        return siblings
    
    async def subtree(
        self,
        include_self: bool = True,
        max_depth: Optional[int] = None,
    ) -> List["TreeMixin"]:
        """
        Get this node and all its descendants.
        
        Args:
            include_self: Include this node (default: True)
            max_depth: Maximum depth to traverse
        
        Returns:
            List with this node and all descendants
        
        Example:
            electronics = await Category.get(id=1)
            all_nodes = await electronics.subtree()
            # Returns: [Electronics, Computers, Phones, Laptops, ...]
        """
        return await self.descendants(
            include_self=include_self,
            max_depth=max_depth,
        )
    
    async def children(self) -> List["TreeMixin"]:
        """
        Get direct children of this node.
        
        Returns:
            List of direct child nodes
        
        Example:
            electronics = await Category.get(id=1)
            direct_children = await electronics.children()
            # Returns: [Computers, Phones, TVs]
        """
        model_class = type(self)
        node_id = getattr(self, 'id')
        
        return await model_class.select().where(
            **{self._tree_parent_field: node_id}
        )
    
    async def parent(self) -> Optional["TreeMixin"]:
        """
        Get the parent of this node.
        
        Returns:
            Parent node or None if root
        
        Example:
            computers = await Category.get(id=2)
            parent = await computers.parent()
            print(parent.name)  # "Electronics"
        """
        if self.is_root:
            return None
        
        parent_id = getattr(self, self._tree_parent_field)
        model_class = type(self)
        return await model_class.get(parent_id)
    
    # ==========================================================================
    # Tree Modification Helpers
    # ==========================================================================
    
    async def move_to(self, new_parent: Optional["TreeMixin"]) -> None:
        """
        Move this node to a new parent.
        
        Args:
            new_parent: New parent node, or None to make root
        
        Example:
            laptops = await Category.get(id=4)
            phones = await Category.get(id=3)
            await laptops.move_to(phones)  # Laptops now under Phones
        
        Raises:
            ValueError: If moving to self or a descendant
        """
        node_id = getattr(self, 'id')
        
        if new_parent is not None:
            new_parent_id = getattr(new_parent, 'id')
            
            # Can't move to self
            if new_parent_id == node_id:
                raise ValueError("Cannot move a node to itself")
            
            # Can't move to a descendant (would create cycle)
            descendants = await self.descendants()
            descendant_ids = {getattr(d, 'id') for d in descendants}
            if new_parent_id in descendant_ids:
                raise ValueError("Cannot move a node to one of its descendants")
            
            setattr(self, self._tree_parent_field, new_parent_id)
        else:
            setattr(self, self._tree_parent_field, None)
        
        # Clear cached ancestors
        self._cached_ancestors = None
        
        # Save the change
        await self.save()
    
    async def make_root(self) -> None:
        """
        Make this node a root (remove parent).
        
        Example:
            computers = await Category.get(id=2)
            await computers.make_root()
            print(computers.is_root)  # True
        """
        await self.move_to(None)
    
    # ==========================================================================
    # Helper Methods
    # ==========================================================================
    
    async def _supports_cte(self) -> bool:
        """Check if current database supports CTEs."""
        try:
            adapter = await self._get_adapter()
            # PostgreSQL supports CTEs
            return hasattr(adapter, 'supports_cte') and adapter.supports_cte
        except Exception:
            return False
    
    async def _get_adapter(self):
        """Get the current database adapter."""
        # Try to get from model class
        model_class = type(self)
        if hasattr(model_class, '_adapter'):
            return model_class._adapter
        
        # Try to get from global
        try:
            from pynext.db import get_adapter
            return await get_adapter()
        except ImportError:
            pass
        
        # Mock adapter for testing
        return MockAdapter()


class MockAdapter:
    """Mock adapter for testing when no real adapter is available."""
    supports_cte = False
    
    async def fetch(self, query: str, *params) -> List[dict]:
        """Mock fetch - returns empty list."""
        return []


__all__ = [
    "TreeMixin",
]

