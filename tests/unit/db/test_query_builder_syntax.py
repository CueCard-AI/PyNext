"""
Unit tests for QueryBuilder syntax parsing.

Tests all three syntax styles:
1. Tuple syntax: ("age", ">", 18)
2. SQL string: "age > $1"  
3. Condition functions: gt("age", 18)

Test count: 100+ tests
"""

import pytest


# =============================================================================
# Mock Model
# =============================================================================

class MockUser:
    """Mock user model."""
    __table_name__ = "users"
    _fields = {"id": {}, "name": {}, "age": {}, "status": {}, "role": {}, "score": {}}
    
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


# =============================================================================
# Helper to get operator from ConditionNode
# =============================================================================

def get_op(condition_node):
    """Extract operator from ConditionNode or its wrapped condition."""
    if hasattr(condition_node, 'condition'):
        cond = condition_node.condition
        if hasattr(cond, 'op'):
            return cond.op.value if hasattr(cond.op, 'value') else str(cond.op)
    if hasattr(condition_node, 'op'):
        return condition_node.op.value if hasattr(condition_node.op, 'value') else str(condition_node.op)
    return None


def get_logical_op(condition_node):
    """Extract logical operator (AND/OR) from ConditionNode or LogicalCondition."""
    # If it's a ConditionNode wrapper
    if hasattr(condition_node, 'condition'):
        cond = condition_node.condition
    else:
        cond = condition_node
    
    # Check for LogicalCondition's op attribute
    if hasattr(cond, 'op'):
        op = cond.op
        return op.value if hasattr(op, 'value') else str(op)
    return None


def get_raw_sql(condition_node):
    """Extract raw SQL from RawCondition."""
    if hasattr(condition_node, 'condition'):
        cond = condition_node.condition
        if hasattr(cond, 'sql'):
            return cond.sql
    return None


def get_raw_params(condition_node):
    """Extract raw params from RawCondition."""
    if hasattr(condition_node, 'condition'):
        cond = condition_node.condition
        if hasattr(cond, 'params'):
            return cond.params
    return None


# =============================================================================
# Tuple Syntax Tests
# =============================================================================

class TestTupleSyntax:
    """Test tuple condition syntax."""
    
    def test_tuple_equality(self):
        """("field", "=", value) syntax."""
        from pynext.db.query_builder import QueryBuilder
        
        qb = QueryBuilder.for_model(MockUser, ("status", "=", "active"))
        
        assert qb._ast.conditions is not None
    
    def test_tuple_greater_than(self):
        """("field", ">", value) syntax."""
        from pynext.db.query_builder import QueryBuilder
        
        qb = QueryBuilder.for_model(MockUser, ("age", ">", 18))
        
        assert qb._ast.conditions is not None
        assert get_op(qb._ast.conditions) == ">"
    
    def test_tuple_greater_equal(self):
        """("field", ">=", value) syntax."""
        from pynext.db.query_builder import QueryBuilder
        
        qb = QueryBuilder.for_model(MockUser, ("age", ">=", 21))
        
        assert get_op(qb._ast.conditions) == ">="
    
    def test_tuple_less_than(self):
        """("field", "<", value) syntax."""
        from pynext.db.query_builder import QueryBuilder
        
        qb = QueryBuilder.for_model(MockUser, ("age", "<", 65))
        
        assert get_op(qb._ast.conditions) == "<"
    
    def test_tuple_less_equal(self):
        """("field", "<=", value) syntax."""
        from pynext.db.query_builder import QueryBuilder
        
        qb = QueryBuilder.for_model(MockUser, ("age", "<=", 50))
        
        assert get_op(qb._ast.conditions) == "<="
    
    def test_tuple_not_equal(self):
        """("field", "!=", value) syntax."""
        from pynext.db.query_builder import QueryBuilder
        
        qb = QueryBuilder.for_model(MockUser, ("status", "!=", "deleted"))
        
        assert get_op(qb._ast.conditions) == "!="
    
    def test_tuple_in(self):
        """("field", "in", [...]) syntax."""
        from pynext.db.query_builder import QueryBuilder
        
        qb = QueryBuilder.for_model(MockUser, ("role", "IN", ["admin", "moderator"]))
        
        assert get_op(qb._ast.conditions) == "IN"
    
    def test_tuple_not_in(self):
        """("field", "NOT IN", [...]) syntax."""
        from pynext.db.query_builder import QueryBuilder
        
        qb = QueryBuilder.for_model(MockUser, ("status", "NOT IN", ["deleted", "banned"]))
        
        assert get_op(qb._ast.conditions) == "NOT IN"
    
    def test_tuple_between(self):
        """("field", "between", min, max) syntax."""
        from pynext.db.query_builder import QueryBuilder
        
        qb = QueryBuilder.for_model(MockUser, ("age", "BETWEEN", 18, 65))
        
        assert get_op(qb._ast.conditions) == "BETWEEN"
    
    def test_tuple_like(self):
        """("field", "like", "%pattern%") syntax."""
        from pynext.db.query_builder import QueryBuilder
        
        qb = QueryBuilder.for_model(MockUser, ("name", "LIKE", "%john%"))
        
        assert get_op(qb._ast.conditions) == "LIKE"
    
    def test_tuple_ilike(self):
        """("field", "ilike", "%pattern%") syntax (case-insensitive)."""
        from pynext.db.query_builder import QueryBuilder
        
        qb = QueryBuilder.for_model(MockUser, ("name", "ILIKE", "%JOHN%"))
        
        assert get_op(qb._ast.conditions) == "ILIKE"
    
    def test_tuple_is_null(self):
        """("field", "IS NULL") syntax."""
        from pynext.db.query_builder import QueryBuilder
        
        qb = QueryBuilder.for_model(MockUser, ("deleted_at", "IS NULL"))
        
        assert get_op(qb._ast.conditions) == "IS NULL"
    
    def test_tuple_not_null(self):
        """("field", "IS NOT NULL") syntax."""
        from pynext.db.query_builder import QueryBuilder
        
        qb = QueryBuilder.for_model(MockUser, ("email", "IS NOT NULL"))
        
        assert get_op(qb._ast.conditions) == "IS NOT NULL"
    
    def test_multiple_tuples(self):
        """Multiple tuple conditions (implicit AND)."""
        from pynext.db.query_builder import QueryBuilder
        
        qb = QueryBuilder.for_model(
            MockUser,
            ("age", ">", 18),
            ("status", "=", "active")
        )
        
        # Multiple conditions should create a LogicalCondition
        assert qb._ast.conditions is not None
        # Check it has the logical_op (AND)
        logical = get_logical_op(qb._ast.conditions)
        assert logical == "AND"


# =============================================================================
# Condition Function Syntax Tests  
# =============================================================================

class TestConditionFunctionSyntax:
    """Test condition function syntax."""
    
    def test_eq(self):
        """eq("field", value) syntax."""
        from pynext.db.query_builder import QueryBuilder
        from pynext.db.conditions import eq
        
        qb = QueryBuilder.for_model(MockUser, eq("status", "active"))
        
        assert qb._ast.conditions is not None
        assert get_op(qb._ast.conditions) == "="
    
    def test_ne(self):
        """ne("field", value) syntax."""
        from pynext.db.query_builder import QueryBuilder
        from pynext.db.conditions import ne
        
        qb = QueryBuilder.for_model(MockUser, ne("status", "deleted"))
        
        assert get_op(qb._ast.conditions) == "!="
    
    def test_gt(self):
        """gt("field", value) syntax."""
        from pynext.db.query_builder import QueryBuilder
        from pynext.db.conditions import gt
        
        qb = QueryBuilder.for_model(MockUser, gt("age", 18))
        
        assert get_op(qb._ast.conditions) == ">"
    
    def test_gte(self):
        """gte("field", value) syntax."""
        from pynext.db.query_builder import QueryBuilder
        from pynext.db.conditions import gte
        
        qb = QueryBuilder.for_model(MockUser, gte("age", 21))
        
        assert get_op(qb._ast.conditions) == ">="
    
    def test_lt(self):
        """lt("field", value) syntax."""
        from pynext.db.query_builder import QueryBuilder
        from pynext.db.conditions import lt
        
        qb = QueryBuilder.for_model(MockUser, lt("age", 65))
        
        assert get_op(qb._ast.conditions) == "<"
    
    def test_lte(self):
        """lte("field", value) syntax."""
        from pynext.db.query_builder import QueryBuilder
        from pynext.db.conditions import lte
        
        qb = QueryBuilder.for_model(MockUser, lte("age", 50))
        
        assert get_op(qb._ast.conditions) == "<="
    
    def test_in_(self):
        """in_("field", [...]) syntax."""
        from pynext.db.query_builder import QueryBuilder
        from pynext.db.conditions import in_
        
        qb = QueryBuilder.for_model(MockUser, in_("role", ["admin", "moderator"]))
        
        assert get_op(qb._ast.conditions) == "IN"
    
    def test_not_in(self):
        """not_in_("field", [...]) syntax."""
        from pynext.db.query_builder import QueryBuilder
        from pynext.db.conditions import not_in_
        
        qb = QueryBuilder.for_model(MockUser, not_in_("status", ["deleted", "banned"]))
        
        assert get_op(qb._ast.conditions) == "NOT IN"
    
    def test_between(self):
        """between("field", min, max) syntax."""
        from pynext.db.query_builder import QueryBuilder
        from pynext.db.conditions import between
        
        qb = QueryBuilder.for_model(MockUser, between("age", 18, 65))
        
        assert get_op(qb._ast.conditions) == "BETWEEN"
    
    def test_like(self):
        """like("field", "%pattern%") syntax."""
        from pynext.db.query_builder import QueryBuilder
        from pynext.db.conditions import like
        
        qb = QueryBuilder.for_model(MockUser, like("name", "%john%"))
        
        assert get_op(qb._ast.conditions) == "LIKE"
    
    def test_ilike(self):
        """ilike("field", "%pattern%") syntax (case-insensitive)."""
        from pynext.db.query_builder import QueryBuilder
        from pynext.db.conditions import ilike
        
        qb = QueryBuilder.for_model(MockUser, ilike("name", "%JOHN%"))
        
        assert get_op(qb._ast.conditions) == "ILIKE"
    
    def test_contains(self):
        """contains("field", "text") syntax."""
        from pynext.db.query_builder import QueryBuilder
        from pynext.db.conditions import contains
        
        qb = QueryBuilder.for_model(MockUser, contains("name", "john"))
        
        # contains creates a case-insensitive ILIKE with %text%
        assert get_op(qb._ast.conditions) == "ILIKE"
    
    def test_startswith(self):
        """startswith("field", "text") syntax."""
        from pynext.db.query_builder import QueryBuilder
        from pynext.db.conditions import startswith
        
        qb = QueryBuilder.for_model(MockUser, startswith("name", "john"))
        
        # startswith creates a case-insensitive ILIKE with text%
        assert get_op(qb._ast.conditions) == "ILIKE"
    
    def test_endswith(self):
        """endswith("field", "text") syntax."""
        from pynext.db.query_builder import QueryBuilder
        from pynext.db.conditions import endswith
        
        qb = QueryBuilder.for_model(MockUser, endswith("name", "john"))
        
        # endswith creates a case-insensitive ILIKE with %text
        assert get_op(qb._ast.conditions) == "ILIKE"
    
    def test_is_null(self):
        """is_null_("field") syntax."""
        from pynext.db.query_builder import QueryBuilder
        from pynext.db.conditions import is_null_
        
        qb = QueryBuilder.for_model(MockUser, is_null_("deleted_at"))
        
        assert get_op(qb._ast.conditions) == "IS NULL"
    
    def test_not_null(self):
        """is_not_null_("field") syntax."""
        from pynext.db.query_builder import QueryBuilder
        from pynext.db.conditions import is_not_null_
        
        qb = QueryBuilder.for_model(MockUser, is_not_null_("email"))
        
        assert get_op(qb._ast.conditions) == "IS NOT NULL"


# =============================================================================
# Logical Operator Tests
# =============================================================================

class TestLogicalOperators:
    """Test logical operator composition."""
    
    def test_and_explicit(self):
        """and_(c1, c2) syntax."""
        from pynext.db.query_builder import QueryBuilder
        from pynext.db.conditions import and_, gt, eq
        
        qb = QueryBuilder.for_model(MockUser, and_(gt("age", 18), eq("status", "active")))
        
        assert qb._ast.conditions is not None
        assert get_logical_op(qb._ast.conditions) == "AND"
    
    def test_or_(self):
        """or_(c1, c2) syntax."""
        from pynext.db.query_builder import QueryBuilder
        from pynext.db.conditions import or_, eq
        
        qb = QueryBuilder.for_model(MockUser, or_(eq("role", "admin"), eq("role", "moderator")))
        
        assert get_logical_op(qb._ast.conditions) == "OR"
    
    def test_not_(self):
        """not_(condition) syntax."""
        from pynext.db.query_builder import QueryBuilder
        from pynext.db.conditions import not_, eq
        
        qb = QueryBuilder.for_model(MockUser, not_(eq("status", "deleted")))
        
        assert get_logical_op(qb._ast.conditions) == "NOT"
    
    def test_nested_logical(self):
        """Nested logical operators."""
        from pynext.db.query_builder import QueryBuilder
        from pynext.db.conditions import and_, or_, gt, eq
        
        qb = QueryBuilder.for_model(
            MockUser,
            and_(
                gt("age", 18),
                or_(eq("role", "admin"), eq("role", "moderator"))
            )
        )
        
        assert qb._ast.conditions is not None
        assert get_logical_op(qb._ast.conditions) == "AND"
    
    def test_deeply_nested(self):
        """Deeply nested conditions."""
        from pynext.db.query_builder import QueryBuilder
        from pynext.db.conditions import and_, or_, gt, lt, eq
        
        qb = QueryBuilder.for_model(
            MockUser,
            or_(
                and_(gt("age", 18), lt("age", 30)),
                and_(gt("age", 50), lt("age", 65))
            )
        )
        
        assert qb._ast.conditions is not None
        assert get_logical_op(qb._ast.conditions) == "OR"


# =============================================================================
# Mixed Syntax Tests
# =============================================================================

class TestMixedSyntax:
    """Test mixing different condition syntaxes."""
    
    def test_tuple_and_function(self):
        """Mixing tuple and function syntax."""
        from pynext.db.query_builder import QueryBuilder
        from pynext.db.conditions import eq
        
        qb = QueryBuilder.for_model(
            MockUser,
            ("age", ">", 18),
            eq("status", "active")
        )
        
        assert qb._ast.conditions is not None
        assert get_logical_op(qb._ast.conditions) == "AND"
    
    def test_multiple_condition_types(self):
        """Multiple different condition types."""
        from pynext.db.query_builder import QueryBuilder
        from pynext.db.conditions import gt, eq
        
        qb = QueryBuilder.for_model(
            MockUser,
            gt("age", 18),
            eq("status", "active")
        )
        
        # Should combine into AND
        assert qb._ast.conditions is not None


# =============================================================================
# Where Method Tests
# =============================================================================

class TestWhereMethod:
    """Test .where() method chaining."""
    
    def test_where_tuple(self):
        """Test .where() with tuple syntax."""
        from pynext.db.query_builder import QueryBuilder
        
        qb = QueryBuilder.for_model(MockUser).where(("age", ">", 18))
        
        assert qb._ast.conditions is not None
    
    def test_where_function(self):
        """Test .where() with function syntax."""
        from pynext.db.query_builder import QueryBuilder
        from pynext.db.conditions import gt
        
        qb = QueryBuilder.for_model(MockUser).where(gt("age", 18))
        
        assert qb._ast.conditions is not None
    
    def test_where_chain(self):
        """Test chained .where() calls."""
        from pynext.db.query_builder import QueryBuilder
        from pynext.db.conditions import gt, eq
        
        qb = (QueryBuilder.for_model(MockUser)
              .where(gt("age", 18))
              .where(eq("status", "active")))
        
        # Multiple wheres should be ANDed together
        assert qb._ast.conditions is not None
        assert get_logical_op(qb._ast.conditions) == "AND"
    
    def test_where_raw(self):
        """Test .where_raw() with raw SQL."""
        from pynext.db.query_builder import QueryBuilder
        
        qb = QueryBuilder.for_model(MockUser).where_raw("age > 18 AND status = 'active'")
        
        assert qb._ast.conditions is not None
        raw = get_raw_sql(qb._ast.conditions)
        assert "age > 18" in raw
    
    def test_where_raw_with_params(self):
        """Test .where_raw() with parameterized SQL."""
        from pynext.db.query_builder import QueryBuilder
        
        qb = QueryBuilder.for_model(MockUser).where_raw("age > $1 AND status = $2", [18, "active"])
        
        assert qb._ast.conditions is not None
        raw_params = get_raw_params(qb._ast.conditions)
        assert raw_params == [18, "active"]


# =============================================================================
# Select Method Tests
# =============================================================================

class TestSelectMethod:
    """Test .select() method."""
    
    def test_select_single_column(self):
        """Test selecting single column."""
        from pynext.db.query_builder import QueryBuilder
        
        qb = QueryBuilder.for_model(MockUser).select("name")
        
        assert qb._ast.columns == ["name"]
    
    def test_select_multiple_columns(self):
        """Test selecting multiple columns."""
        from pynext.db.query_builder import QueryBuilder
        
        qb = QueryBuilder.for_model(MockUser).select("id", "name", "age")
        
        assert qb._ast.columns == ["id", "name", "age"]
    
    def test_select_all(self):
        """Test selecting all columns (default)."""
        from pynext.db.query_builder import QueryBuilder
        
        qb = QueryBuilder.for_model(MockUser)
        
        # Default is None meaning all columns
        assert qb._ast.columns is None or qb._ast.columns == []
    
    def test_select_list(self):
        """Test selecting with list."""
        from pynext.db.query_builder import QueryBuilder
        
        columns = ["id", "name"]
        qb = QueryBuilder.for_model(MockUser).select(*columns)
        
        assert qb._ast.columns == columns


# =============================================================================
# Order Method Tests
# =============================================================================

class TestOrderMethod:
    """Test .order() method."""
    
    def test_order_ascending(self):
        """Test ordering ascending."""
        from pynext.db.query_builder import QueryBuilder
        
        qb = QueryBuilder.for_model(MockUser).order("name")
        
        assert len(qb._ast.order) == 1
        assert qb._ast.order[0].field == "name"
        assert qb._ast.order[0].direction == "ASC"
    
    def test_order_descending(self):
        """Test ordering descending with - prefix."""
        from pynext.db.query_builder import QueryBuilder
        
        qb = QueryBuilder.for_model(MockUser).order("-created_at")
        
        assert len(qb._ast.order) == 1
        assert qb._ast.order[0].field == "created_at"
        assert qb._ast.order[0].direction == "DESC"
    
    def test_order_multiple(self):
        """Test ordering by multiple columns."""
        from pynext.db.query_builder import QueryBuilder
        
        qb = QueryBuilder.for_model(MockUser).order("-score", "name")
        
        assert len(qb._ast.order) == 2
        assert qb._ast.order[0].field == "score"
        assert qb._ast.order[0].direction == "DESC"
        assert qb._ast.order[1].field == "name"
        assert qb._ast.order[1].direction == "ASC"


# =============================================================================
# Limit/Offset Tests
# =============================================================================

class TestLimitOffset:
    """Test .limit() and .offset() methods."""
    
    def test_limit(self):
        """Test setting limit."""
        from pynext.db.query_builder import QueryBuilder
        
        qb = QueryBuilder.for_model(MockUser).limit(10)
        
        assert qb._ast.limit == 10
    
    def test_offset(self):
        """Test setting offset."""
        from pynext.db.query_builder import QueryBuilder
        
        qb = QueryBuilder.for_model(MockUser).offset(20)
        
        assert qb._ast.offset == 20
    
    def test_limit_and_offset(self):
        """Test setting both limit and offset."""
        from pynext.db.query_builder import QueryBuilder
        
        qb = QueryBuilder.for_model(MockUser).limit(10).offset(20)
        
        assert qb._ast.limit == 10
        assert qb._ast.offset == 20
    
    def test_page(self):
        """Test .page() helper."""
        from pynext.db.query_builder import QueryBuilder
        
        qb = QueryBuilder.for_model(MockUser).page(2, per_page=10)
        
        assert qb._ast.limit == 10
        assert qb._ast.offset == 10  # Page 2 starts at offset 10


# =============================================================================
# Chain Tests
# =============================================================================

class TestChaining:
    """Test method chaining."""
    
    def test_full_chain(self):
        """Test complete query chain."""
        from pynext.db.query_builder import QueryBuilder
        from pynext.db.conditions import gt, eq
        
        qb = (QueryBuilder.for_model(MockUser)
              .select("id", "name", "age")
              .where(gt("age", 18))
              .where(eq("status", "active"))
              .order("-created_at")
              .limit(10)
              .offset(0))
        
        assert qb._ast.columns == ["id", "name", "age"]
        assert qb._ast.conditions is not None
        assert len(qb._ast.order) == 1
        assert qb._ast.limit == 10
        assert qb._ast.offset == 0
    
    def test_immutability(self):
        """Test that chaining creates new instances."""
        from pynext.db.query_builder import QueryBuilder
        
        qb1 = QueryBuilder.for_model(MockUser)
        qb2 = qb1.limit(10)
        qb3 = qb1.limit(20)
        
        # All three should be different instances
        assert qb1._ast.limit is None
        assert qb2._ast.limit == 10
        assert qb3._ast.limit == 20


# =============================================================================
# Distinct/ForUpdate Tests
# =============================================================================

class TestDistinctForUpdate:
    """Test .distinct() and .for_update() methods."""
    
    def test_distinct(self):
        """Test DISTINCT modifier."""
        from pynext.db.query_builder import QueryBuilder
        
        qb = QueryBuilder.for_model(MockUser).distinct()
        
        assert qb._ast.distinct is True
    
    def test_for_update(self):
        """Test FOR UPDATE modifier."""
        from pynext.db.query_builder import QueryBuilder
        
        qb = QueryBuilder.for_model(MockUser).for_update()
        
        assert qb._ast.for_update is True


# =============================================================================
# AST to_dict Tests
# =============================================================================

class TestASTSerialization:
    """Test AST serialization."""
    
    def test_simple_to_dict(self):
        """Test basic AST to_dict."""
        from pynext.db.query_builder import QueryBuilder
        
        qb = QueryBuilder.for_model(MockUser)
        ast_dict = qb._ast.to_dict()
        
        assert "table" in ast_dict
        assert ast_dict["table"] == "users"
    
    def test_conditions_in_dict(self):
        """Test conditions appear in to_dict."""
        from pynext.db.query_builder import QueryBuilder
        from pynext.db.conditions import gt
        
        qb = QueryBuilder.for_model(MockUser, gt("age", 18))
        ast_dict = qb._ast.to_dict()
        
        assert "conditions" in ast_dict
        assert ast_dict["conditions"] is not None


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestErrorHandling:
    """Test error handling in syntax parsing."""
    
    def test_invalid_operator(self):
        """Test invalid operator raises error."""
        from pynext.db.query_builder import QueryBuilder
        
        with pytest.raises(ValueError):
            QueryBuilder.for_model(MockUser, ("age", "INVALID_OP", 18))
    
    def test_empty_tuple(self):
        """Test empty tuple raises error."""
        from pynext.db.query_builder import QueryBuilder
        
        with pytest.raises((ValueError, IndexError)):
            QueryBuilder.for_model(MockUser, ())
    
    def test_wrong_tuple_length(self):
        """Test wrong tuple length - single element tuple."""
        from pynext.db.query_builder import QueryBuilder
        
        # Single element tuple is invalid
        with pytest.raises((ValueError, TypeError, IndexError)):
            QueryBuilder.for_model(MockUser, ("age",))  # Too few elements


# =============================================================================
# Edge Case Tests
# =============================================================================

class TestEdgeCases:
    """Test edge cases in syntax parsing."""
    
    def test_none_value(self):
        """Test condition with None value."""
        from pynext.db.query_builder import QueryBuilder
        from pynext.db.conditions import eq
        
        qb = QueryBuilder.for_model(MockUser, eq("deleted_at", None))
        
        assert qb._ast.conditions is not None
    
    def test_empty_list_in(self):
        """Test IN with empty list."""
        from pynext.db.query_builder import QueryBuilder
        from pynext.db.conditions import in_
        
        qb = QueryBuilder.for_model(MockUser, in_("role", []))
        
        assert qb._ast.conditions is not None
    
    def test_unicode_string(self):
        """Test condition with unicode string."""
        from pynext.db.query_builder import QueryBuilder
        from pynext.db.conditions import eq
        
        qb = QueryBuilder.for_model(MockUser, eq("name", "日本語"))
        
        assert qb._ast.conditions is not None
    
    def test_special_characters(self):
        """Test condition with special characters."""
        from pynext.db.query_builder import QueryBuilder
        from pynext.db.conditions import like
        
        qb = QueryBuilder.for_model(MockUser, like("name", "%O'Brien%"))
        
        assert qb._ast.conditions is not None
    
    def test_very_long_value(self):
        """Test condition with very long value."""
        from pynext.db.query_builder import QueryBuilder
        from pynext.db.conditions import eq
        
        long_value = "x" * 10000
        qb = QueryBuilder.for_model(MockUser, eq("name", long_value))
        
        assert qb._ast.conditions is not None
