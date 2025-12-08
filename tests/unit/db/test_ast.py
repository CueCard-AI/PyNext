"""
Tests for pynext.db.ast module.

Test count: 50 tests
"""

import pytest
from pynext.db.ast import (
    QueryAST,
    QueryType,
    OrderNode,
    JoinNode,
    ConditionNode,
    build_condition_node,
    merge_conditions,
    extract_params,
)
from pynext.db.conditions import (
    eq, gt, lt, between, in_, isnull, and_, or_, raw,
    Condition, LogicalCondition, RawCondition,
    Operator, LogicalOp,
)


# =============================================================================
# QueryType Tests - 5 tests
# =============================================================================

class TestQueryType:
    """Tests for QueryType enum."""
    
    def test_select(self):
        """SELECT type."""
        assert QueryType.SELECT == "SELECT"
    
    def test_insert(self):
        """INSERT type."""
        assert QueryType.INSERT == "INSERT"
    
    def test_update(self):
        """UPDATE type."""
        assert QueryType.UPDATE == "UPDATE"
    
    def test_delete(self):
        """DELETE type."""
        assert QueryType.DELETE == "DELETE"
    
    def test_raw(self):
        """RAW type."""
        assert QueryType.RAW == "RAW"


# =============================================================================
# OrderNode Tests - 8 tests
# =============================================================================

class TestOrderNode:
    """Tests for OrderNode."""
    
    def test_create_asc(self):
        """Create ASC order."""
        node = OrderNode(field="name", direction="ASC")
        assert node.field == "name"
        assert node.direction == "ASC"
    
    def test_create_desc(self):
        """Create DESC order."""
        node = OrderNode(field="created_at", direction="DESC")
        assert node.direction == "DESC"
    
    def test_default_direction(self):
        """Default direction is ASC."""
        node = OrderNode(field="name")
        assert node.direction == "ASC"
    
    def test_to_dict(self):
        """to_dict serialization."""
        node = OrderNode(field="name", direction="DESC")
        d = node.to_dict()
        assert d["field"] == "name"
        assert d["direction"] == "DESC"
    
    def test_parse_simple(self):
        """Parse simple field name."""
        node = OrderNode.parse("name")
        assert node.field == "name"
        assert node.direction == "ASC"
    
    def test_parse_desc(self):
        """Parse descending with - prefix."""
        node = OrderNode.parse("-created_at")
        assert node.field == "created_at"
        assert node.direction == "DESC"
    
    def test_parse_asc_explicit(self):
        """Parse explicit + prefix."""
        node = OrderNode.parse("+score")
        assert node.field == "score"
        assert node.direction == "ASC"
    
    def test_repr(self):
        """repr output."""
        node = OrderNode(field="name", direction="DESC")
        r = repr(node)
        assert "name" in r
        assert "DESC" in r


# =============================================================================
# JoinNode Tests - 6 tests
# =============================================================================

class TestJoinNode:
    """Tests for JoinNode."""
    
    def test_create_inner(self):
        """Create INNER JOIN."""
        node = JoinNode(
            table="posts",
            on_field="users.id",
            to_field="posts.user_id"
        )
        assert node.join_type == "INNER"
    
    def test_create_left(self):
        """Create LEFT JOIN."""
        node = JoinNode(
            table="posts",
            join_type="LEFT",
            on_field="users.id",
            to_field="posts.user_id"
        )
        assert node.join_type == "LEFT"
    
    def test_with_alias(self):
        """Create with alias."""
        node = JoinNode(
            table="posts",
            alias="p",
            on_field="users.id",
            to_field="p.user_id"
        )
        assert node.alias == "p"
    
    def test_to_dict(self):
        """to_dict serialization."""
        node = JoinNode(
            table="posts",
            alias="p",
            join_type="LEFT",
            on_field="users.id",
            to_field="posts.user_id"
        )
        d = node.to_dict()
        assert d["table"] == "posts"
        assert d["alias"] == "p"
        assert d["join_type"] == "LEFT"
    
    def test_repr(self):
        """repr output."""
        node = JoinNode(
            table="posts",
            join_type="LEFT",
            on_field="users.id",
            to_field="posts.user_id"
        )
        r = repr(node)
        assert "LEFT" in r
        assert "posts" in r


# =============================================================================
# ConditionNode Tests - 6 tests
# =============================================================================

class TestConditionNode:
    """Tests for ConditionNode."""
    
    def test_wrap_condition(self):
        """Wrap Condition."""
        cond = eq("age", 18)
        node = ConditionNode(cond)
        assert node.condition == cond
    
    def test_wrap_logical(self):
        """Wrap LogicalCondition."""
        cond = and_(eq("a", 1), eq("b", 2))
        node = ConditionNode(cond)
        assert node.condition == cond
    
    def test_wrap_raw(self):
        """Wrap RawCondition."""
        cond = raw("x > 1")
        node = ConditionNode(cond)
        assert node.condition == cond
    
    def test_to_dict(self):
        """to_dict delegates to condition."""
        cond = eq("age", 18)
        node = ConditionNode(cond)
        d = node.to_dict()
        assert d == cond.to_dict()
    
    def test_repr(self):
        """repr delegates to condition."""
        cond = eq("age", 18)
        node = ConditionNode(cond)
        assert repr(cond) in repr(node)


# =============================================================================
# QueryAST Tests - 15 tests
# =============================================================================

class TestQueryAST:
    """Tests for QueryAST."""
    
    def test_create_simple(self):
        """Create simple SELECT AST."""
        ast = QueryAST(table="users")
        assert ast.table == "users"
        assert ast.query_type == QueryType.SELECT
    
    def test_with_columns(self):
        """with_columns creates new AST."""
        ast1 = QueryAST(table="users")
        ast2 = ast1.with_columns("id", "name")
        assert ast1.columns is None
        assert ast2.columns == ["id", "name"]
    
    def test_with_conditions(self):
        """with_conditions creates new AST."""
        ast1 = QueryAST(table="users")
        node = ConditionNode(eq("age", 18))
        ast2 = ast1.with_conditions(node)
        assert ast1.conditions is None
        assert ast2.conditions == node
    
    def test_with_order(self):
        """with_order creates new AST."""
        ast1 = QueryAST(table="users")
        order = OrderNode(field="name", direction="ASC")
        ast2 = ast1.with_order(order)
        assert len(ast1.order) == 0
        assert len(ast2.order) == 1
    
    def test_with_limit(self):
        """with_limit creates new AST."""
        ast1 = QueryAST(table="users")
        ast2 = ast1.with_limit(10)
        assert ast1.limit is None
        assert ast2.limit == 10
    
    def test_with_offset(self):
        """with_offset creates new AST."""
        ast1 = QueryAST(table="users")
        ast2 = ast1.with_offset(20)
        assert ast1.offset is None
        assert ast2.offset == 20
    
    def test_with_includes(self):
        """with_includes creates new AST."""
        ast1 = QueryAST(table="users")
        ast2 = ast1.with_includes("posts", "comments")
        assert len(ast1.includes) == 0
        assert ast2.includes == ["posts", "comments"]
    
    def test_with_params(self):
        """with_params creates new AST."""
        ast1 = QueryAST(table="users")
        ast2 = ast1.with_params([18, "active"])
        assert len(ast1.params) == 0
        assert ast2.params == [18, "active"]
    
    def test_to_dict_minimal(self):
        """to_dict with minimal AST."""
        ast = QueryAST(table="users")
        d = ast.to_dict()
        assert d["table"] == "users"
        assert d["type"] == "SELECT"
        assert "columns" not in d  # Not set
        assert "conditions" not in d  # Not set
    
    def test_to_dict_complete(self):
        """to_dict with complete AST."""
        ast = QueryAST(
            table="users",
            query_type=QueryType.SELECT,
            columns=["id", "name"],
            limit=10,
            offset=20,
            distinct=True,
            for_update=True,
        )
        d = ast.to_dict()
        assert d["columns"] == ["id", "name"]
        assert d["limit"] == 10
        assert d["offset"] == 20
        assert d["distinct"] is True
        assert d["for_update"] is True
    
    def test_has_conditions(self):
        """has_conditions check."""
        ast = QueryAST(table="users")
        assert ast.HasConditions() is False
        
        node = ConditionNode(eq("age", 18))
        ast2 = ast.with_conditions(node)
        assert ast2.HasConditions() is True
    
    def test_has_order(self):
        """has_order check."""
        ast = QueryAST(table="users")
        assert ast.HasOrder() is False
        
        order = OrderNode(field="name")
        ast2 = ast.with_order(order)
        assert ast2.HasOrder() is True
    
    def test_column_list_default(self):
        """column_list default is *."""
        ast = QueryAST(table="users")
        assert ast.ColumnList() == "*"
    
    def test_column_list_custom(self):
        """column_list with custom columns."""
        ast = QueryAST(table="users", columns=["id", "name"])
        assert ast.ColumnList() == "id, name"
    
    def test_is_raw_query(self):
        """is_raw_query check."""
        ast1 = QueryAST(table="users")
        assert ast1.IsRawQuery() is False
        
        ast2 = QueryAST(table="users", query_type=QueryType.RAW)
        assert ast2.IsRawQuery() is True
        
        ast3 = QueryAST(table="users", raw_sql="SELECT 1")
        assert ast3.IsRawQuery() is True


# =============================================================================
# Helper Functions - 10 tests
# =============================================================================

class TestBuildConditionNode:
    """Tests for build_condition_node function."""
    
    def test_empty_list(self):
        """Empty list returns None."""
        result = build_condition_node([])
        assert result is None
    
    def test_single_condition(self):
        """Single condition returned directly."""
        cond = eq("age", 18)
        result = build_condition_node([cond])
        assert result.condition == cond
    
    def test_multiple_conditions_and(self):
        """Multiple conditions ANDed."""
        c1 = eq("a", 1)
        c2 = eq("b", 2)
        result = build_condition_node([c1, c2])
        assert result.condition.op == LogicalOp.AND


class TestMergeConditions:
    """Tests for merge_conditions function."""
    
    def test_merge_none_empty(self):
        """Merge None with empty returns None."""
        result = merge_conditions(None, [])
        assert result is None
    
    def test_merge_none_with_new(self):
        """Merge None with new conditions."""
        cond = eq("age", 18)
        result = merge_conditions(None, [cond])
        assert result is not None
    
    def test_merge_existing_with_new(self):
        """Merge existing with new conditions."""
        existing = ConditionNode(eq("a", 1))
        new = [eq("b", 2)]
        result = merge_conditions(existing, new)
        # Result should be AND of both
        assert result.condition.op == LogicalOp.AND


class TestExtractParams:
    """Tests for extract_params function."""
    
    def test_extract_simple(self):
        """Extract from simple condition."""
        cond = eq("age", 18)
        params = extract_params(cond)
        assert params == [18]
    
    def test_extract_in(self):
        """Extract from IN condition."""
        cond = in_("status", ["a", "b"])
        params = extract_params(cond)
        assert params == ["a", "b"]
    
    def test_extract_between(self):
        """Extract from BETWEEN condition."""
        cond = between("age", 18, 65)
        params = extract_params(cond)
        assert params == [18, 65]
    
    def test_extract_logical(self):
        """Extract from logical condition."""
        cond = and_(eq("a", 1), eq("b", 2))
        params = extract_params(cond)
        assert params == [1, 2]
    
    def test_extract_raw(self):
        """Extract from raw condition."""
        cond = raw("x > $1", 10)
        params = extract_params(cond)
        assert params == [10]
    
    def test_extract_null_skipped(self):
        """NULL values not extracted."""
        cond = isnull("deleted_at")
        params = extract_params(cond)
        assert params == []

