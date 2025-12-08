"""
Tests for pynext.db.conditions module.

Test count: 100 tests
"""

import pytest
from pynext.db.conditions import (
    # Comparison operators
    eq, ne, gt, gte, lt, lte,
    like, ilike, contains, startswith, endswith,
    in_, not_in, isnull, notnull, between,
    # PostgreSQL specific
    json_contains, json_contained_by, array_overlaps,
    # Logical operators
    and_, or_, not_,
    # Raw SQL
    raw,
    # Classes
    Condition, LogicalCondition, RawCondition,
    Operator, LogicalOp,
    # Parsing
    parse_tuple_condition, parse_condition,
)


# =============================================================================
# Equality Operators (eq, ne) - 10 tests
# =============================================================================

class TestEq:
    """Tests for eq() function."""
    
    def test_eq_string(self):
        """eq with string value."""
        cond = eq("status", "active")
        assert cond.field == "status"
        assert cond.op == Operator.EQ
        assert cond.value == "active"
    
    def test_eq_integer(self):
        """eq with integer value."""
        cond = eq("age", 18)
        assert cond.field == "age"
        assert cond.value == 18
    
    def test_eq_boolean(self):
        """eq with boolean value."""
        cond = eq("is_admin", True)
        assert cond.value is True
    
    def test_eq_none(self):
        """eq with None value."""
        cond = eq("deleted_at", None)
        assert cond.value is None
    
    def test_eq_to_dict(self):
        """eq to_dict serialization."""
        cond = eq("status", "active")
        d = cond.to_dict()
        assert d["type"] == "condition"
        assert d["field"] == "status"
        assert d["op"] == "="
        assert d["value"] == "active"


class TestNe:
    """Tests for ne() function."""
    
    def test_ne_string(self):
        """ne with string value."""
        cond = ne("status", "deleted")
        assert cond.op == Operator.NE
        assert cond.value == "deleted"
    
    def test_ne_integer(self):
        """ne with integer value."""
        cond = ne("priority", 0)
        assert cond.value == 0
    
    def test_ne_to_dict(self):
        """ne to_dict serialization."""
        cond = ne("status", "deleted")
        d = cond.to_dict()
        assert d["op"] == "!="


# =============================================================================
# Comparison Operators (gt, gte, lt, lte) - 16 tests
# =============================================================================

class TestGt:
    """Tests for gt() function."""
    
    def test_gt_integer(self):
        """gt with integer value."""
        cond = gt("age", 18)
        assert cond.field == "age"
        assert cond.op == Operator.GT
        assert cond.value == 18
    
    def test_gt_float(self):
        """gt with float value."""
        cond = gt("price", 100.50)
        assert cond.value == 100.50
    
    def test_gt_to_dict(self):
        """gt to_dict serialization."""
        cond = gt("age", 18)
        d = cond.to_dict()
        assert d["op"] == ">"
    
    def test_gt_repr(self):
        """gt repr string."""
        cond = gt("age", 18)
        assert "age" in repr(cond)
        assert "18" in repr(cond)


class TestGte:
    """Tests for gte() function."""
    
    def test_gte_integer(self):
        """gte with integer value."""
        cond = gte("score", 80)
        assert cond.op == Operator.GTE
        assert cond.value == 80
    
    def test_gte_to_dict(self):
        """gte to_dict serialization."""
        cond = gte("score", 80)
        d = cond.to_dict()
        assert d["op"] == ">="


class TestLt:
    """Tests for lt() function."""
    
    def test_lt_integer(self):
        """lt with integer value."""
        cond = lt("age", 65)
        assert cond.op == Operator.LT
        assert cond.value == 65
    
    def test_lt_to_dict(self):
        """lt to_dict serialization."""
        cond = lt("age", 65)
        d = cond.to_dict()
        assert d["op"] == "<"


class TestLte:
    """Tests for lte() function."""
    
    def test_lte_integer(self):
        """lte with integer value."""
        cond = lte("priority", 5)
        assert cond.op == Operator.LTE
        assert cond.value == 5
    
    def test_lte_to_dict(self):
        """lte to_dict serialization."""
        cond = lte("priority", 5)
        d = cond.to_dict()
        assert d["op"] == "<="


# =============================================================================
# Pattern Matching (like, ilike, contains, startswith, endswith) - 20 tests
# =============================================================================

class TestLike:
    """Tests for like() function."""
    
    def test_like_prefix(self):
        """like with prefix pattern."""
        cond = like("name", "john%")
        assert cond.op == Operator.LIKE
        assert cond.value == "john%"
    
    def test_like_suffix(self):
        """like with suffix pattern."""
        cond = like("email", "%@gmail.com")
        assert cond.value == "%@gmail.com"
    
    def test_like_contains(self):
        """like with contains pattern."""
        cond = like("bio", "%python%")
        assert cond.value == "%python%"
    
    def test_like_to_dict(self):
        """like to_dict serialization."""
        cond = like("name", "john%")
        d = cond.to_dict()
        assert d["op"] == "LIKE"


class TestIlike:
    """Tests for ilike() function (case-insensitive)."""
    
    def test_ilike_prefix(self):
        """ilike with prefix pattern."""
        cond = ilike("name", "John%")
        assert cond.op == Operator.ILIKE
        assert cond.value == "John%"
    
    def test_ilike_to_dict(self):
        """ilike to_dict serialization."""
        cond = ilike("name", "john%")
        d = cond.to_dict()
        assert d["op"] == "ILIKE"


class TestContains:
    """Tests for contains() function."""
    
    def test_contains_string(self):
        """contains wraps with %."""
        cond = contains("name", "john")
        assert cond.op == Operator.ILIKE
        assert cond.value == "%john%"
    
    def test_contains_special_chars(self):
        """contains with special characters."""
        cond = contains("bio", "C++")
        assert cond.value == "%C++%"


class TestStartswith:
    """Tests for startswith() function."""
    
    def test_startswith_string(self):
        """startswith adds %."""
        cond = startswith("name", "Dr.")
        assert cond.op == Operator.ILIKE
        assert cond.value == "Dr.%"


class TestEndswith:
    """Tests for endswith() function."""
    
    def test_endswith_string(self):
        """endswith adds %."""
        cond = endswith("email", "@gmail.com")
        assert cond.op == Operator.ILIKE
        assert cond.value == "%@gmail.com"


# =============================================================================
# List Operators (in_, not_in) - 10 tests
# =============================================================================

class TestIn:
    """Tests for in_() function."""
    
    def test_in_strings(self):
        """in_ with string list."""
        cond = in_("status", ["active", "pending"])
        assert cond.op == Operator.IN
        assert cond.value == ["active", "pending"]
    
    def test_in_integers(self):
        """in_ with integer list."""
        cond = in_("id", [1, 2, 3])
        assert cond.value == [1, 2, 3]
    
    def test_in_empty_list(self):
        """in_ with empty list."""
        cond = in_("id", [])
        assert cond.value == []
    
    def test_in_to_dict(self):
        """in_ to_dict serialization."""
        cond = in_("status", ["active", "pending"])
        d = cond.to_dict()
        assert d["op"] == "IN"
        assert d["value"] == ["active", "pending"]


class TestNotIn:
    """Tests for not_in() function."""
    
    def test_not_in_strings(self):
        """not_in with string list."""
        cond = not_in("status", ["deleted", "banned"])
        assert cond.op == Operator.NOT_IN
        assert cond.value == ["deleted", "banned"]
    
    def test_not_in_to_dict(self):
        """not_in to_dict serialization."""
        cond = not_in("status", ["deleted"])
        d = cond.to_dict()
        assert d["op"] == "NOT IN"


# =============================================================================
# Null Operators (isnull, notnull) - 8 tests
# =============================================================================

class TestIsnull:
    """Tests for isnull() function."""
    
    def test_isnull(self):
        """isnull creates IS NULL condition."""
        cond = isnull("deleted_at")
        assert cond.field == "deleted_at"
        assert cond.op == Operator.IS_NULL
        assert cond.value is None
    
    def test_isnull_to_dict(self):
        """isnull to_dict doesn't include value."""
        cond = isnull("deleted_at")
        d = cond.to_dict()
        assert d["op"] == "IS NULL"
        assert "value" not in d
    
    def test_isnull_repr(self):
        """isnull repr string."""
        cond = isnull("deleted_at")
        assert "IS NULL" in repr(cond)


class TestNotnull:
    """Tests for notnull() function."""
    
    def test_notnull(self):
        """notnull creates IS NOT NULL condition."""
        cond = notnull("email")
        assert cond.op == Operator.IS_NOT_NULL
    
    def test_notnull_to_dict(self):
        """notnull to_dict serialization."""
        cond = notnull("email")
        d = cond.to_dict()
        assert d["op"] == "IS NOT NULL"


# =============================================================================
# Between Operator - 6 tests
# =============================================================================

class TestBetween:
    """Tests for between() function."""
    
    def test_between_integers(self):
        """between with integer range."""
        cond = between("age", 18, 65)
        assert cond.op == Operator.BETWEEN
        assert cond.value == 18
        assert cond.value2 == 65
    
    def test_between_floats(self):
        """between with float range."""
        cond = between("price", 10.0, 100.0)
        assert cond.value == 10.0
        assert cond.value2 == 100.0
    
    def test_between_to_dict(self):
        """between to_dict serialization."""
        cond = between("age", 18, 65)
        d = cond.to_dict()
        assert d["op"] == "BETWEEN"
        assert d["value"] == 18
        assert d["value2"] == 65
    
    def test_between_repr(self):
        """between repr string."""
        cond = between("age", 18, 65)
        assert "BETWEEN" in repr(cond)
        assert "18" in repr(cond)
        assert "65" in repr(cond)


# =============================================================================
# PostgreSQL Operators (json_contains, etc) - 6 tests
# =============================================================================

class TestPostgreSQLOperators:
    """Tests for PostgreSQL-specific operators."""
    
    def test_json_contains_list(self):
        """json_contains with list."""
        cond = json_contains("tags", ["python"])
        assert cond.op == Operator.CONTAINS
        assert cond.value == ["python"]
    
    def test_json_contains_dict(self):
        """json_contains with dict."""
        cond = json_contains("data", {"key": "value"})
        assert cond.value == {"key": "value"}
    
    def test_json_contained_by(self):
        """json_contained_by operator."""
        cond = json_contained_by("tags", ["a", "b", "c"])
        assert cond.op == Operator.CONTAINED_BY
    
    def test_array_overlaps(self):
        """array_overlaps operator."""
        cond = array_overlaps("tags", ["python", "go"])
        assert cond.op == Operator.OVERLAPS


# =============================================================================
# Logical Operators (and_, or_, not_) - 15 tests
# =============================================================================

class TestAnd:
    """Tests for and_() function."""
    
    def test_and_two_conditions(self):
        """and_ with two conditions."""
        cond = and_(eq("a", 1), eq("b", 2))
        assert isinstance(cond, LogicalCondition)
        assert cond.op == LogicalOp.AND
        assert len(cond.conditions) == 2
    
    def test_and_three_conditions(self):
        """and_ with three conditions."""
        cond = and_(eq("a", 1), eq("b", 2), eq("c", 3))
        assert len(cond.conditions) == 3
    
    def test_and_nested(self):
        """and_ with nested conditions."""
        inner = or_(eq("x", 1), eq("y", 2))
        cond = and_(eq("a", 1), inner)
        assert len(cond.conditions) == 2
        assert isinstance(cond.conditions[1], LogicalCondition)
    
    def test_and_to_dict(self):
        """and_ to_dict serialization."""
        cond = and_(eq("a", 1), eq("b", 2))
        d = cond.to_dict()
        assert d["type"] == "logical"
        assert d["op"] == "AND"
        assert len(d["conditions"]) == 2


class TestOr:
    """Tests for or_() function."""
    
    def test_or_two_conditions(self):
        """or_ with two conditions."""
        cond = or_(eq("role", "admin"), eq("role", "moderator"))
        assert cond.op == LogicalOp.OR
        assert len(cond.conditions) == 2
    
    def test_or_to_dict(self):
        """or_ to_dict serialization."""
        cond = or_(eq("a", 1), eq("b", 2))
        d = cond.to_dict()
        assert d["op"] == "OR"


class TestNot:
    """Tests for not_() function."""
    
    def test_not_condition(self):
        """not_ with single condition."""
        cond = not_(eq("status", "deleted"))
        assert cond.op == LogicalOp.NOT
        assert len(cond.conditions) == 1
    
    def test_not_logical(self):
        """not_ with logical condition."""
        inner = or_(eq("a", 1), eq("b", 2))
        cond = not_(inner)
        assert len(cond.conditions) == 1
    
    def test_not_to_dict(self):
        """not_ to_dict serialization."""
        cond = not_(eq("status", "deleted"))
        d = cond.to_dict()
        assert d["op"] == "NOT"


# =============================================================================
# Raw SQL - 8 tests
# =============================================================================

class TestRaw:
    """Tests for raw() function."""
    
    def test_raw_simple(self):
        """raw with simple SQL."""
        cond = raw("custom_func(data) > 10")
        assert isinstance(cond, RawCondition)
        assert cond.sql == "custom_func(data) > 10"
        assert cond.params == []
    
    def test_raw_with_params(self):
        """raw with parameters."""
        cond = raw("custom_func(data) > $1", 10)
        assert cond.sql == "custom_func(data) > $1"
        assert cond.params == [10]
    
    def test_raw_multiple_params(self):
        """raw with multiple parameters."""
        cond = raw("x > $1 AND y < $2", 10, 20)
        assert cond.params == [10, 20]
    
    def test_raw_to_dict(self):
        """raw to_dict serialization."""
        cond = raw("x > $1", 10)
        d = cond.to_dict()
        assert d["type"] == "raw"
        assert d["sql"] == "x > $1"
        assert d["params"] == [10]


# =============================================================================
# Tuple Parsing - 15 tests
# =============================================================================

class TestParseTupleCondition:
    """Tests for parse_tuple_condition() function."""
    
    def test_parse_eq(self):
        """Parse equality tuple."""
        cond = parse_tuple_condition(("age", "=", 18))
        assert cond.field == "age"
        assert cond.op == Operator.EQ
        assert cond.value == 18
    
    def test_parse_double_eq(self):
        """Parse == operator."""
        cond = parse_tuple_condition(("age", "==", 18))
        assert cond.op == Operator.EQ
    
    def test_parse_ne(self):
        """Parse not equal tuple."""
        cond = parse_tuple_condition(("status", "!=", "deleted"))
        assert cond.op == Operator.NE
    
    def test_parse_gt(self):
        """Parse greater than tuple."""
        cond = parse_tuple_condition(("age", ">", 18))
        assert cond.op == Operator.GT
    
    def test_parse_gte(self):
        """Parse greater than or equal tuple."""
        cond = parse_tuple_condition(("age", ">=", 18))
        assert cond.op == Operator.GTE
    
    def test_parse_lt(self):
        """Parse less than tuple."""
        cond = parse_tuple_condition(("age", "<", 65))
        assert cond.op == Operator.LT
    
    def test_parse_lte(self):
        """Parse less than or equal tuple."""
        cond = parse_tuple_condition(("age", "<=", 65))
        assert cond.op == Operator.LTE
    
    def test_parse_like(self):
        """Parse LIKE tuple."""
        cond = parse_tuple_condition(("name", "like", "%john%"))
        assert cond.op == Operator.LIKE
    
    def test_parse_ilike(self):
        """Parse ILIKE tuple."""
        cond = parse_tuple_condition(("name", "ILIKE", "%john%"))
        assert cond.op == Operator.ILIKE
    
    def test_parse_in(self):
        """Parse IN tuple."""
        cond = parse_tuple_condition(("status", "in", ["active", "pending"]))
        assert cond.op == Operator.IN
    
    def test_parse_not_in(self):
        """Parse NOT IN tuple."""
        cond = parse_tuple_condition(("status", "not in", ["deleted"]))
        assert cond.op == Operator.NOT_IN
    
    def test_parse_is_null(self):
        """Parse IS NULL tuple (2 elements)."""
        cond = parse_tuple_condition(("deleted_at", "is null"))
        assert cond.op == Operator.IS_NULL
    
    def test_parse_is_not_null(self):
        """Parse IS NOT NULL tuple (2 elements)."""
        cond = parse_tuple_condition(("email", "is not null"))
        assert cond.op == Operator.IS_NOT_NULL
    
    def test_parse_between(self):
        """Parse BETWEEN tuple (4 elements)."""
        cond = parse_tuple_condition(("age", "between", 18, 65))
        assert cond.op == Operator.BETWEEN
        assert cond.value == 18
        assert cond.value2 == 65
    
    def test_parse_invalid_operator(self):
        """Parse with invalid operator raises ValueError."""
        with pytest.raises(ValueError, match="Unknown operator"):
            parse_tuple_condition(("age", "??", 18))
    
    def test_parse_invalid_length(self):
        """Parse with invalid tuple length raises ValueError."""
        with pytest.raises(ValueError, match="Invalid tuple"):
            parse_tuple_condition(("age",))


# =============================================================================
# Parse Condition - 6 tests
# =============================================================================

class TestParseCondition:
    """Tests for parse_condition() function."""
    
    def test_parse_tuple(self):
        """parse_condition with tuple."""
        cond = parse_condition(("age", ">", 18))
        assert isinstance(cond, Condition)
    
    def test_parse_condition_obj(self):
        """parse_condition with Condition object."""
        original = eq("age", 18)
        cond = parse_condition(original)
        assert cond is original
    
    def test_parse_logical(self):
        """parse_condition with LogicalCondition."""
        original = and_(eq("a", 1), eq("b", 2))
        cond = parse_condition(original)
        assert cond is original
    
    def test_parse_raw(self):
        """parse_condition with RawCondition."""
        original = raw("x > 1")
        cond = parse_condition(original)
        assert cond is original
    
    def test_parse_invalid_type(self):
        """parse_condition with invalid type raises TypeError."""
        with pytest.raises(TypeError, match="Invalid condition type"):
            parse_condition(42)

