"""
PyNext Tree Query Builders.

Generates efficient recursive CTE queries for tree traversal.
Used by TreeMixin when PostgreSQL is available.

Design Philosophy:
- Single query for entire tree traversal (vs N+1 app-level)
- Parameterized queries to prevent SQL injection
- Returns rows in correct order (parent-to-root, breadth-first)

PostgreSQL CTE Explanation:
    WITH RECURSIVE cte AS (
        -- Base case: starting node
        SELECT * FROM table WHERE id = $1
        UNION ALL
        -- Recursive case: join with parent/children
        SELECT t.* FROM table t
        JOIN cte c ON t.id = c.parent_id  -- for ancestors
        -- OR
        JOIN cte c ON t.parent_id = c.id  -- for descendants
    )
    SELECT * FROM cte;

Usage:
    from pynext.db.relationships.tree_query import TreeQueryBuilder
    
    builder = TreeQueryBuilder()
    query, params = builder.ancestors_query(Category, 5, "parent_id")
    rows = await adapter.fetch(query, *params)
"""

from __future__ import annotations

from typing import Any, List, Optional, Tuple, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from pynext.db.table import Table


class TreeQueryBuilder:
    """
    Builds recursive CTE queries for tree operations.
    
    Supports PostgreSQL's WITH RECURSIVE syntax for efficient
    tree traversal in a single query.
    
    Example:
        builder = TreeQueryBuilder()
        
        # Get ancestors
        query, params = builder.ancestors_query(Category, node_id=5, parent_field="parent_id")
        
        # Get descendants
        query, params = builder.descendants_query(Category, node_id=1, parent_field="parent_id")
    """
    
    def ancestors_query(
        self,
        model: Type["Table"],
        node_id: int,
        parent_field: str = "parent_id",
    ) -> Tuple[str, List[Any]]:
        """
        Generate CTE query to fetch all ancestors.
        
        Args:
            model: The model class (for table name)
            node_id: ID of the starting node
            parent_field: Name of the parent_id field
        
        Returns:
            Tuple of (query_string, parameters)
        
        Example:
            query, params = builder.ancestors_query(Category, 5, "parent_id")
            # query = "WITH RECURSIVE ancestors AS (...) SELECT * FROM ancestors..."
            # params = [5]
        
        The result is ordered from immediate parent to root.
        """
        table_name = self._get_table_name(model)
        
        query = f"""
        WITH RECURSIVE ancestors AS (
            -- Base case: get the parent of the starting node
            SELECT t.*, 1 as _depth
            FROM {table_name} t
            WHERE t.id = (
                SELECT {parent_field} FROM {table_name} WHERE id = $1
            )
            
            UNION ALL
            
            -- Recursive case: get parent of each ancestor
            SELECT t.*, a._depth + 1
            FROM {table_name} t
            JOIN ancestors a ON t.id = a.{parent_field}
        )
        SELECT * FROM ancestors ORDER BY _depth ASC
        """
        
        return query.strip(), [node_id]
    
    def descendants_query(
        self,
        model: Type["Table"],
        node_id: int,
        parent_field: str = "parent_id",
        max_depth: Optional[int] = None,
    ) -> Tuple[str, List[Any]]:
        """
        Generate CTE query to fetch all descendants.
        
        Args:
            model: The model class (for table name)
            node_id: ID of the starting node
            parent_field: Name of the parent_id field
            max_depth: Maximum depth to traverse (None = unlimited)
        
        Returns:
            Tuple of (query_string, parameters)
        
        Example:
            query, params = builder.descendants_query(Category, 1, "parent_id")
            # Returns all descendants in breadth-first order
        
        The result is ordered by depth (breadth-first).
        """
        table_name = self._get_table_name(model)
        params = [node_id]
        
        # Build depth filter if specified
        depth_filter = ""
        if max_depth is not None:
            depth_filter = f"WHERE d._depth < {max_depth}"
            
        query = f"""
        WITH RECURSIVE descendants AS (
            -- Base case: direct children of starting node
            SELECT t.*, 1 as _depth
            FROM {table_name} t
            WHERE t.{parent_field} = $1
            
            UNION ALL
            
            -- Recursive case: children of each descendant
            SELECT t.*, d._depth + 1
            FROM {table_name} t
            JOIN descendants d ON t.{parent_field} = d.id
            {depth_filter}
        )
        SELECT * FROM descendants ORDER BY _depth ASC, id ASC
        """
        
        return query.strip(), params
    
    def subtree_query(
        self,
        model: Type["Table"],
        node_id: int,
        parent_field: str = "parent_id",
        include_self: bool = True,
        max_depth: Optional[int] = None,
    ) -> Tuple[str, List[Any]]:
        """
        Generate CTE query to fetch node and all descendants.
        
        Args:
            model: The model class
            node_id: ID of the root of subtree
            parent_field: Name of the parent_id field
            include_self: Include the starting node
            max_depth: Maximum depth to traverse
        
        Returns:
            Tuple of (query_string, parameters)
        """
        table_name = self._get_table_name(model)
        params = [node_id]
        
        # Build depth filter if specified
        depth_filter = ""
        if max_depth is not None:
            depth_filter = f"WHERE s._depth < {max_depth}"
        
        if include_self:
            query = f"""
            WITH RECURSIVE subtree AS (
                -- Base case: the starting node
                SELECT t.*, 0 as _depth
                FROM {table_name} t
                WHERE t.id = $1
                
                UNION ALL
                
                -- Recursive case: children of each node
                SELECT t.*, s._depth + 1
                FROM {table_name} t
                JOIN subtree s ON t.{parent_field} = s.id
                {depth_filter}
            )
            SELECT * FROM subtree ORDER BY _depth ASC, id ASC
            """
        else:
            query = f"""
            WITH RECURSIVE subtree AS (
                -- Base case: direct children of starting node
                SELECT t.*, 1 as _depth
                FROM {table_name} t
                WHERE t.{parent_field} = $1
                
                UNION ALL
                
                -- Recursive case: children of each node
                SELECT t.*, s._depth + 1
                FROM {table_name} t
                JOIN subtree s ON t.{parent_field} = s.id
                {depth_filter}
            )
            SELECT * FROM subtree ORDER BY _depth ASC, id ASC
            """
        
        return query.strip(), params
    
    def path_query(
        self,
        model: Type["Table"],
        node_id: int,
        parent_field: str = "parent_id",
        name_field: str = "name",
        separator: str = "/",
    ) -> Tuple[str, List[Any]]:
        """
        Generate CTE query to compute path string.
        
        Args:
            model: The model class
            node_id: ID of the target node
            parent_field: Name of the parent_id field
            name_field: Field to use for path segments
            separator: Path separator
        
        Returns:
            Tuple of (query_string, parameters)
        
        Example:
            query, params = builder.path_query(Category, 5, name_field="name")
            # Returns single row with path like "Electronics/Computers/Laptops"
        """
        table_name = self._get_table_name(model)
        
        query = f"""
        WITH RECURSIVE path_cte AS (
            -- Base case: starting node
            SELECT t.id, t.{parent_field}, t.{name_field}::text as path
            FROM {table_name} t
            WHERE t.id = $1
            
            UNION ALL
            
            -- Recursive case: prepend parent name
            SELECT t.id, t.{parent_field}, 
                   t.{name_field}::text || '{separator}' || p.path as path
            FROM {table_name} t
            JOIN path_cte p ON t.id = p.{parent_field}
        )
        SELECT path FROM path_cte WHERE {parent_field} IS NULL
        """
        
        return query.strip(), [node_id]
    
    def depth_query(
        self,
        model: Type["Table"],
        node_id: int,
        parent_field: str = "parent_id",
    ) -> Tuple[str, List[Any]]:
        """
        Generate CTE query to compute depth of a node.
        
        Args:
            model: The model class
            node_id: ID of the target node
            parent_field: Name of the parent_id field
        
        Returns:
            Tuple of (query_string, parameters)
        
        Example:
            query, params = builder.depth_query(Category, 5)
            # Returns single row with depth (integer)
        """
        table_name = self._get_table_name(model)
        
        query = f"""
        WITH RECURSIVE depth_cte AS (
            -- Base case: starting node at depth 0
            SELECT t.id, t.{parent_field}, 0 as depth
            FROM {table_name} t
            WHERE t.id = $1
            
            UNION ALL
            
            -- Recursive case: increment depth for each parent
            SELECT t.id, t.{parent_field}, d.depth + 1
            FROM {table_name} t
            JOIN depth_cte d ON t.id = d.{parent_field}
        )
        SELECT MAX(depth) as depth FROM depth_cte
        """
        
        return query.strip(), [node_id]
    
    def siblings_query(
        self,
        model: Type["Table"],
        node_id: int,
        parent_field: str = "parent_id",
        include_self: bool = False,
    ) -> Tuple[str, List[Any]]:
        """
        Generate query to fetch siblings (same parent).
        
        Args:
            model: The model class
            node_id: ID of the target node
            parent_field: Name of the parent_id field
            include_self: Include the node itself
        
        Returns:
            Tuple of (query_string, parameters)
        """
        table_name = self._get_table_name(model)
        
        exclude_self = "" if include_self else f"AND t.id != $1"
        
        query = f"""
        SELECT t.*
        FROM {table_name} t
        WHERE t.{parent_field} = (
            SELECT {parent_field} FROM {table_name} WHERE id = $1
        )
        {exclude_self}
        ORDER BY t.id
        """
        
        return query.strip(), [node_id]
    
    def roots_query(
        self,
        model: Type["Table"],
        parent_field: str = "parent_id",
    ) -> Tuple[str, List[Any]]:
        """
        Generate query to fetch all root nodes.
        
        Args:
            model: The model class
            parent_field: Name of the parent_id field
        
        Returns:
            Tuple of (query_string, parameters)
        """
        table_name = self._get_table_name(model)
        
        query = f"""
        SELECT * FROM {table_name}
        WHERE {parent_field} IS NULL
        ORDER BY id
        """
        
        return query.strip(), []
    
    def leaf_nodes_query(
        self,
        model: Type["Table"],
        parent_field: str = "parent_id",
        root_id: Optional[int] = None,
    ) -> Tuple[str, List[Any]]:
        """
        Generate query to fetch all leaf nodes (no children).
        
        Args:
            model: The model class
            parent_field: Name of the parent_id field
            root_id: Optional root to limit scope
        
        Returns:
            Tuple of (query_string, parameters)
        """
        table_name = self._get_table_name(model)
        params = []
        
        if root_id is not None:
            # First get all descendants, then filter for leaves
            query = f"""
            WITH RECURSIVE subtree AS (
                SELECT t.*, 0 as _depth
                FROM {table_name} t
                WHERE t.id = $1
                
                UNION ALL
                
                SELECT t.*, s._depth + 1
                FROM {table_name} t
                JOIN subtree s ON t.{parent_field} = s.id
            )
            SELECT s.* FROM subtree s
            WHERE NOT EXISTS (
                SELECT 1 FROM {table_name} t WHERE t.{parent_field} = s.id
            )
            ORDER BY s.id
            """
            params = [root_id]
        else:
            # All leaf nodes in entire table
            query = f"""
            SELECT t.* FROM {table_name} t
            WHERE NOT EXISTS (
                SELECT 1 FROM {table_name} c WHERE c.{parent_field} = t.id
            )
            ORDER BY t.id
            """
        
        return query.strip(), params
    
    def tree_count_query(
        self,
        model: Type["Table"],
        node_id: int,
        parent_field: str = "parent_id",
    ) -> Tuple[str, List[Any]]:
        """
        Generate query to count all nodes in subtree.
        
        Args:
            model: The model class
            node_id: ID of the root node
            parent_field: Name of the parent_id field
        
        Returns:
            Tuple of (query_string, parameters)
        """
        table_name = self._get_table_name(model)
        
        query = f"""
        WITH RECURSIVE subtree AS (
            SELECT id FROM {table_name} WHERE id = $1
            UNION ALL
            SELECT t.id FROM {table_name} t
            JOIN subtree s ON t.{parent_field} = s.id
        )
        SELECT COUNT(*) as count FROM subtree
        """
        
        return query.strip(), [node_id]
    
    def _get_table_name(self, model: Type["Table"]) -> str:
        """Get the table name for a model."""
        if hasattr(model, '__tablename__'):
            return model.__tablename__
        
        if hasattr(model, '_table_name'):
            return model._table_name
        
        # Fallback: lowercase class name + 's'
        return model.__name__.lower() + 's'


__all__ = [
    "TreeQueryBuilder",
]

