"""
Test Phase 7.6: CTE Query Generation.

These tests verify the TreeQueryBuilder generates correct
PostgreSQL recursive CTE queries.
"""

import pytest
from typing import Optional, List
from unittest.mock import Mock, MagicMock

from pynext.db.relationships.tree_query import TreeQueryBuilder


# =============================================================================
# Mock Model for Testing
# =============================================================================

class MockModel:
    """Mock model for testing CTE generation."""
    __tablename__ = "categories"


class MockModelCustomTable:
    """Mock model with custom table name."""
    _table_name = "my_custom_table"


# =============================================================================
# Test ancestors_query
# =============================================================================

class TestAncestorsQuery:
    """Test ancestors_query CTE generation."""
    
    def test_generates_recursive_cte(self):
        """Query contains WITH RECURSIVE."""
        builder = TreeQueryBuilder()
        query, params = builder.ancestors_query(MockModel, 5)
        
        assert "WITH RECURSIVE" in query
    
    def test_uses_correct_table_name(self):
        """Query uses model's table name."""
        builder = TreeQueryBuilder()
        query, params = builder.ancestors_query(MockModel, 5)
        
        assert "categories" in query
    
    def test_parameterized_node_id(self):
        """Query uses parameterized node ID."""
        builder = TreeQueryBuilder()
        query, params = builder.ancestors_query(MockModel, 5)
        
        assert "$1" in query
        assert params == [5]
    
    def test_uses_parent_field(self):
        """Query joins on parent_id field."""
        builder = TreeQueryBuilder()
        query, params = builder.ancestors_query(MockModel, 5, "parent_id")
        
        assert "parent_id" in query
    
    def test_custom_parent_field(self):
        """Query uses custom parent field."""
        builder = TreeQueryBuilder()
        query, params = builder.ancestors_query(MockModel, 5, "manager_id")
        
        assert "manager_id" in query
    
    def test_orders_by_depth(self):
        """Query orders results by depth."""
        builder = TreeQueryBuilder()
        query, params = builder.ancestors_query(MockModel, 5)
        
        assert "ORDER BY" in query
        assert "_depth" in query
    
    def test_includes_depth_column(self):
        """Query calculates depth."""
        builder = TreeQueryBuilder()
        query, params = builder.ancestors_query(MockModel, 5)
        
        assert "_depth" in query


# =============================================================================
# Test descendants_query
# =============================================================================

class TestDescendantsQuery:
    """Test descendants_query CTE generation."""
    
    def test_generates_recursive_cte(self):
        """Query contains WITH RECURSIVE."""
        builder = TreeQueryBuilder()
        query, params = builder.descendants_query(MockModel, 1)
        
        assert "WITH RECURSIVE" in query
    
    def test_uses_correct_table_name(self):
        """Query uses model's table name."""
        builder = TreeQueryBuilder()
        query, params = builder.descendants_query(MockModel, 1)
        
        assert "categories" in query
    
    def test_parameterized_node_id(self):
        """Query uses parameterized node ID."""
        builder = TreeQueryBuilder()
        query, params = builder.descendants_query(MockModel, 1)
        
        assert "$1" in query
        assert params == [1]
    
    def test_joins_on_parent_field(self):
        """Query joins children via parent_id."""
        builder = TreeQueryBuilder()
        query, params = builder.descendants_query(MockModel, 1)
        
        assert "parent_id" in query
    
    def test_max_depth_filter(self):
        """Query includes depth filter when specified."""
        builder = TreeQueryBuilder()
        query, params = builder.descendants_query(MockModel, 1, max_depth=3)
        
        assert "_depth < 3" in query
    
    def test_no_depth_filter_when_none(self):
        """Query has no depth filter when max_depth is None."""
        builder = TreeQueryBuilder()
        query, params = builder.descendants_query(MockModel, 1, max_depth=None)
        
        # Should not have explicit depth filter in WHERE
        assert "_depth <" not in query or "WHERE d._depth" not in query
    
    def test_orders_by_depth_and_id(self):
        """Query orders by depth then ID."""
        builder = TreeQueryBuilder()
        query, params = builder.descendants_query(MockModel, 1)
        
        assert "ORDER BY _depth ASC, id ASC" in query


# =============================================================================
# Test subtree_query
# =============================================================================

class TestSubtreeQuery:
    """Test subtree_query CTE generation."""
    
    def test_include_self_default(self):
        """Query includes self by default."""
        builder = TreeQueryBuilder()
        query, params = builder.subtree_query(MockModel, 1, include_self=True)
        
        # Base case should select the node itself
        assert "WHERE t.id = $1" in query
    
    def test_exclude_self(self):
        """Query excludes self when specified."""
        builder = TreeQueryBuilder()
        query, params = builder.subtree_query(MockModel, 1, include_self=False)
        
        # Base case should select children of node
        assert "WHERE t.parent_id = $1" in query
    
    def test_with_max_depth(self):
        """Query respects max_depth."""
        builder = TreeQueryBuilder()
        query, params = builder.subtree_query(MockModel, 1, max_depth=2)
        
        assert "_depth < 2" in query


# =============================================================================
# Test path_query
# =============================================================================

class TestPathQuery:
    """Test path_query CTE generation."""
    
    def test_generates_recursive_cte(self):
        """Query contains WITH RECURSIVE."""
        builder = TreeQueryBuilder()
        query, params = builder.path_query(MockModel, 5)
        
        assert "WITH RECURSIVE" in query
    
    def test_builds_path_string(self):
        """Query concatenates name field into path."""
        builder = TreeQueryBuilder()
        query, params = builder.path_query(MockModel, 5, name_field="name")
        
        assert "name" in query
        assert "path" in query
    
    def test_uses_separator(self):
        """Query uses specified separator."""
        builder = TreeQueryBuilder()
        query, params = builder.path_query(MockModel, 5, separator=" > ")
        
        assert " > " in query
    
    def test_custom_name_field(self):
        """Query uses custom name field."""
        builder = TreeQueryBuilder()
        query, params = builder.path_query(MockModel, 5, name_field="title")
        
        assert "title" in query


# =============================================================================
# Test depth_query
# =============================================================================

class TestDepthQuery:
    """Test depth_query CTE generation."""
    
    def test_generates_recursive_cte(self):
        """Query contains WITH RECURSIVE."""
        builder = TreeQueryBuilder()
        query, params = builder.depth_query(MockModel, 5)
        
        assert "WITH RECURSIVE" in query
    
    def test_counts_depth(self):
        """Query calculates depth by counting ancestors."""
        builder = TreeQueryBuilder()
        query, params = builder.depth_query(MockModel, 5)
        
        assert "depth" in query
    
    def test_returns_max_depth(self):
        """Query returns MAX(depth)."""
        builder = TreeQueryBuilder()
        query, params = builder.depth_query(MockModel, 5)
        
        assert "MAX(depth)" in query


# =============================================================================
# Test siblings_query
# =============================================================================

class TestSiblingsQuery:
    """Test siblings_query generation."""
    
    def test_not_recursive(self):
        """Siblings query is not recursive (simple join)."""
        builder = TreeQueryBuilder()
        query, params = builder.siblings_query(MockModel, 5)
        
        # Siblings just need same parent, no recursion needed
        assert "WITH RECURSIVE" not in query
    
    def test_filters_by_parent(self):
        """Query filters by same parent_id."""
        builder = TreeQueryBuilder()
        query, params = builder.siblings_query(MockModel, 5)
        
        assert "parent_id" in query
    
    def test_excludes_self_by_default(self):
        """Query excludes self by default."""
        builder = TreeQueryBuilder()
        query, params = builder.siblings_query(MockModel, 5, include_self=False)
        
        assert "id != $1" in query
    
    def test_includes_self_when_specified(self):
        """Query includes self when specified."""
        builder = TreeQueryBuilder()
        query, params = builder.siblings_query(MockModel, 5, include_self=True)
        
        assert "id != $1" not in query


# =============================================================================
# Test roots_query
# =============================================================================

class TestRootsQuery:
    """Test roots_query generation."""
    
    def test_filters_null_parent(self):
        """Query filters for NULL parent_id."""
        builder = TreeQueryBuilder()
        query, params = builder.roots_query(MockModel)
        
        assert "parent_id IS NULL" in query
    
    def test_no_params_needed(self):
        """Roots query needs no parameters."""
        builder = TreeQueryBuilder()
        query, params = builder.roots_query(MockModel)
        
        assert params == []
    
    def test_orders_by_id(self):
        """Query orders by ID."""
        builder = TreeQueryBuilder()
        query, params = builder.roots_query(MockModel)
        
        assert "ORDER BY id" in query


# =============================================================================
# Test leaf_nodes_query
# =============================================================================

class TestLeafNodesQuery:
    """Test leaf_nodes_query generation."""
    
    def test_filters_no_children(self):
        """Query finds nodes with no children."""
        builder = TreeQueryBuilder()
        query, params = builder.leaf_nodes_query(MockModel)
        
        assert "NOT EXISTS" in query
    
    def test_no_params_for_all_leaves(self):
        """All leaves query needs no parameters."""
        builder = TreeQueryBuilder()
        query, params = builder.leaf_nodes_query(MockModel)
        
        assert params == []
    
    def test_with_root_id_is_recursive(self):
        """Query is recursive when scoped to subtree."""
        builder = TreeQueryBuilder()
        query, params = builder.leaf_nodes_query(MockModel, root_id=1)
        
        assert "WITH RECURSIVE" in query
        assert params == [1]


# =============================================================================
# Test tree_count_query
# =============================================================================

class TestTreeCountQuery:
    """Test tree_count_query generation."""
    
    def test_generates_recursive_cte(self):
        """Query contains WITH RECURSIVE."""
        builder = TreeQueryBuilder()
        query, params = builder.tree_count_query(MockModel, 1)
        
        assert "WITH RECURSIVE" in query
    
    def test_returns_count(self):
        """Query returns COUNT(*)."""
        builder = TreeQueryBuilder()
        query, params = builder.tree_count_query(MockModel, 1)
        
        assert "COUNT(*)" in query


# =============================================================================
# Test Table Name Resolution
# =============================================================================

class TestTableNameResolution:
    """Test _get_table_name helper."""
    
    def test_uses_tablename_attribute(self):
        """Uses __tablename__ attribute."""
        class Model:
            __tablename__ = "my_models"
        
        builder = TreeQueryBuilder()
        assert builder._get_table_name(Model) == "my_models"
    
    def test_uses_table_name_attribute(self):
        """Uses _table_name attribute."""
        class Model:
            _table_name = "other_models"
        
        builder = TreeQueryBuilder()
        assert builder._get_table_name(Model) == "other_models"
    
    def test_fallback_to_class_name(self):
        """Falls back to lowercase class name + 's'."""
        class Product:
            pass
        
        builder = TreeQueryBuilder()
        assert builder._get_table_name(Product) == "products"


# =============================================================================
# Test SQL Safety
# =============================================================================

class TestSQLSafety:
    """Test SQL queries are safe."""
    
    def test_uses_parameterized_queries(self):
        """All node IDs use parameterized queries."""
        builder = TreeQueryBuilder()
        
        # Test various queries
        q1, p1 = builder.ancestors_query(MockModel, 5)
        q2, p2 = builder.descendants_query(MockModel, 5)
        q3, p3 = builder.depth_query(MockModel, 5)
        
        # Node ID should never appear directly in query
        assert "5" not in q1 or "$1" in q1
        assert "5" not in q2 or "$1" in q2
        assert "5" not in q3 or "$1" in q3
    
    def test_params_contain_node_id(self):
        """Params list contains the node ID."""
        builder = TreeQueryBuilder()
        
        q, params = builder.ancestors_query(MockModel, 42)
        assert 42 in params

