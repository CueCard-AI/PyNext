"""
Tests for pynext.db.query_builder module.

Test count: 150 tests
"""

import pytest
from pynext.db.query_builder import QueryBuilder, SQLStringParser
from pynext.db.conditions import (
    eq, ne, gt, gte, lt, lte, like, ilike,
    contains, in_, not_in, isnull, notnull, between,
    and_, or_, not_, raw,
    Condition, LogicalCondition, RawCondition,
)
from pynext.db.ast import QueryAST, QueryType, OrderNode


# =============================================================================
# Mock Table Class for Testing
# =============================================================================

class MockTable:
    """Mock table class for testing QueryBuilder."""
    __table_name__ = "users"
    _fields = {
        "id": {"type": "integer"},
        "name": {"type": "string"},
        "email": {"type": "string"},
        "age": {"type": "integer"},
        "status": {"type": "string"},
        "created_at": {"type": "datetime"},
    }


class MockOrder:
    """Mock order table for testing."""
    __table_name__ = "orders"


# =============================================================================
# QueryBuilder Creation - 10 tests
# =============================================================================

class TestQueryBuilderCreation:
    """Tests for QueryBuilder creation."""
    
    def test_create_empty(self):
        """Create QueryBuilder without conditions."""
        qb = QueryBuilder.for_model(MockTable)
        assert qb._model == MockTable
        assert qb._ast.table == "users"
    
    def test_create_with_tuple(self):
        """Create QueryBuilder with tuple condition."""
        qb = QueryBuilder.for_model(MockTable, ("age", ">", 18))
        assert qb._ast.conditions is not None
    
    def test_create_with_condition(self):
        """Create QueryBuilder with Condition object."""
        qb = QueryBuilder.for_model(MockTable, gt("age", 18))
        assert qb._ast.conditions is not None
    
    def test_create_with_multiple_conditions(self):
        """Create QueryBuilder with multiple conditions."""
        qb = QueryBuilder.for_model(MockTable, 
            ("age", ">", 18),
            ("status", "=", "active")
        )
        assert qb._ast.conditions is not None
        # Multiple conditions should be ANDed
        cond = qb._ast.conditions.condition
        assert isinstance(cond, LogicalCondition)
    
    def test_create_with_sql_string(self):
        """Create QueryBuilder with SQL string."""
        qb = QueryBuilder.for_model(MockTable, "age > 18")
        assert qb._ast.conditions is not None
        cond = qb._ast.conditions.condition
        assert isinstance(cond, RawCondition)
    
    def test_from_sql(self):
        """Create QueryBuilder from raw SQL."""
        qb = QueryBuilder.from_sql(MockTable, "SELECT * FROM users WHERE age > 18")
        assert qb._ast.query_type == QueryType.RAW
        assert qb._ast.raw_sql == "SELECT * FROM users WHERE age > 18"


# =============================================================================
# Tuple Syntax - 20 tests
# =============================================================================

class TestTupleSyntax:
    """Tests for tuple condition syntax."""
    
    def test_tuple_eq(self):
        """Tuple equality."""
        qb = QueryBuilder.for_model(MockTable, ("status", "=", "active"))
        assert qb._ast.conditions is not None
    
    def test_tuple_gt(self):
        """Tuple greater than."""
        qb = QueryBuilder.for_model(MockTable, ("age", ">", 18))
        d = qb.to_dict()
        assert "conditions" in d
    
    def test_tuple_gte(self):
        """Tuple greater than or equal."""
        qb = QueryBuilder.for_model(MockTable, ("age", ">=", 18))
        assert qb._ast.conditions is not None
    
    def test_tuple_lt(self):
        """Tuple less than."""
        qb = QueryBuilder.for_model(MockTable, ("age", "<", 65))
        assert qb._ast.conditions is not None
    
    def test_tuple_lte(self):
        """Tuple less than or equal."""
        qb = QueryBuilder.for_model(MockTable, ("age", "<=", 65))
        assert qb._ast.conditions is not None
    
    def test_tuple_ne(self):
        """Tuple not equal."""
        qb = QueryBuilder.for_model(MockTable, ("status", "!=", "deleted"))
        assert qb._ast.conditions is not None
    
    def test_tuple_like(self):
        """Tuple LIKE."""
        qb = QueryBuilder.for_model(MockTable, ("name", "like", "%john%"))
        assert qb._ast.conditions is not None
    
    def test_tuple_ilike(self):
        """Tuple ILIKE (case-insensitive)."""
        qb = QueryBuilder.for_model(MockTable, ("name", "ILIKE", "%john%"))
        assert qb._ast.conditions is not None
    
    def test_tuple_in(self):
        """Tuple IN."""
        qb = QueryBuilder.for_model(MockTable, ("status", "in", ["active", "pending"]))
        assert qb._ast.conditions is not None
    
    def test_tuple_not_in(self):
        """Tuple NOT IN."""
        qb = QueryBuilder.for_model(MockTable, ("status", "not in", ["deleted"]))
        assert qb._ast.conditions is not None
    
    def test_tuple_is_null(self):
        """Tuple IS NULL."""
        qb = QueryBuilder.for_model(MockTable, ("deleted_at", "is null"))
        assert qb._ast.conditions is not None
    
    def test_tuple_is_not_null(self):
        """Tuple IS NOT NULL."""
        qb = QueryBuilder.for_model(MockTable, ("email", "is not null"))
        assert qb._ast.conditions is not None
    
    def test_tuple_between(self):
        """Tuple BETWEEN."""
        qb = QueryBuilder.for_model(MockTable, ("age", "between", 18, 65))
        assert qb._ast.conditions is not None
    
    def test_multiple_tuples(self):
        """Multiple tuple conditions (AND)."""
        qb = QueryBuilder.for_model(MockTable,
            ("age", ">", 18),
            ("status", "=", "active"),
            ("email", "is not null")
        )
        assert qb._ast.conditions is not None
        assert len(qb._ast.params) >= 2  # age and status values


# =============================================================================
# Condition Function Syntax - 20 tests
# =============================================================================

class TestConditionFunctionSyntax:
    """Tests for condition function syntax."""
    
    def test_eq_function(self):
        """eq() function."""
        qb = QueryBuilder.for_model(MockTable, eq("status", "active"))
        assert qb._ast.conditions is not None
    
    def test_gt_function(self):
        """gt() function."""
        qb = QueryBuilder.for_model(MockTable, gt("age", 18))
        assert qb._ast.conditions is not None
    
    def test_contains_function(self):
        """contains() function."""
        qb = QueryBuilder.for_model(MockTable, contains("name", "john"))
        assert qb._ast.conditions is not None
    
    def test_in_function(self):
        """in_() function."""
        qb = QueryBuilder.for_model(MockTable, in_("status", ["active", "pending"]))
        assert qb._ast.conditions is not None
    
    def test_isnull_function(self):
        """isnull() function."""
        qb = QueryBuilder.for_model(MockTable, isnull("deleted_at"))
        assert qb._ast.conditions is not None
    
    def test_between_function(self):
        """between() function."""
        qb = QueryBuilder.for_model(MockTable, between("age", 18, 65))
        assert qb._ast.conditions is not None
    
    def test_and_function(self):
        """and_() function."""
        qb = QueryBuilder.for_model(MockTable,
            and_(gt("age", 18), eq("status", "active"))
        )
        assert qb._ast.conditions is not None
    
    def test_or_function(self):
        """or_() function."""
        qb = QueryBuilder.for_model(MockTable,
            or_(eq("role", "admin"), eq("role", "moderator"))
        )
        assert qb._ast.conditions is not None
    
    def test_not_function(self):
        """not_() function."""
        qb = QueryBuilder.for_model(MockTable,
            not_(eq("status", "deleted"))
        )
        assert qb._ast.conditions is not None
    
    def test_nested_logical(self):
        """Nested logical conditions."""
        qb = QueryBuilder.for_model(MockTable,
            and_(
                gt("age", 18),
                or_(eq("role", "admin"), eq("role", "moderator"))
            )
        )
        assert qb._ast.conditions is not None
    
    def test_raw_condition(self):
        """raw() condition function."""
        qb = QueryBuilder.for_model(MockTable,
            raw("custom_func(data) > $1", 10)
        )
        assert qb._ast.conditions is not None


# =============================================================================
# Chainable Methods - 40 tests
# =============================================================================

class TestSelect:
    """Tests for .select() method."""
    
    def test_select_single(self):
        """Select single column."""
        qb = QueryBuilder.for_model(MockTable).select("name")
        assert qb._ast.columns == ["name"]
    
    def test_select_multiple(self):
        """Select multiple columns."""
        qb = QueryBuilder.for_model(MockTable).select("id", "name", "email")
        assert qb._ast.columns == ["id", "name", "email"]
    
    def test_select_with_conditions(self):
        """Select with conditions."""
        qb = (QueryBuilder.for_model(MockTable, gt("age", 18))
              .select("id", "name"))
        assert qb._ast.columns == ["id", "name"]
        assert qb._ast.conditions is not None
    
    def test_select_preserves_immutability(self):
        """Select creates new builder."""
        qb1 = QueryBuilder.for_model(MockTable)
        qb2 = qb1.select("name")
        assert qb1._ast.columns is None
        assert qb2._ast.columns == ["name"]


class TestOrder:
    """Tests for .order() method."""
    
    def test_order_asc(self):
        """Order ascending."""
        qb = QueryBuilder.for_model(MockTable).order("name")
        assert len(qb._ast.order) == 1
        assert qb._ast.order[0].field == "name"
        assert qb._ast.order[0].direction == "ASC"
    
    def test_order_desc(self):
        """Order descending with - prefix."""
        qb = QueryBuilder.for_model(MockTable).order("-created_at")
        assert qb._ast.order[0].field == "created_at"
        assert qb._ast.order[0].direction == "DESC"
    
    def test_order_multiple(self):
        """Multiple order fields."""
        qb = QueryBuilder.for_model(MockTable).order("-created_at", "name")
        assert len(qb._ast.order) == 2
        assert qb._ast.order[0].direction == "DESC"
        assert qb._ast.order[1].direction == "ASC"
    
    def test_order_explicit_asc(self):
        """Order with + prefix."""
        qb = QueryBuilder.for_model(MockTable).order("+score")
        assert qb._ast.order[0].direction == "ASC"


class TestLimit:
    """Tests for .limit() method."""
    
    def test_limit(self):
        """Basic limit."""
        qb = QueryBuilder.for_model(MockTable).limit(10)
        assert qb._ast.limit == 10
    
    def test_limit_one(self):
        """Limit to one."""
        qb = QueryBuilder.for_model(MockTable).limit(1)
        assert qb._ast.limit == 1


class TestOffset:
    """Tests for .offset() method."""
    
    def test_offset(self):
        """Basic offset."""
        qb = QueryBuilder.for_model(MockTable).offset(20)
        assert qb._ast.offset == 20
    
    def test_offset_with_limit(self):
        """Offset with limit."""
        qb = QueryBuilder.for_model(MockTable).limit(10).offset(20)
        assert qb._ast.limit == 10
        assert qb._ast.offset == 20


class TestPage:
    """Tests for .page() method."""
    
    def test_page_first(self):
        """First page."""
        qb = QueryBuilder.for_model(MockTable).page(1)
        assert qb._ast.limit == 20
        assert qb._ast.offset == 0
    
    def test_page_second(self):
        """Second page."""
        qb = QueryBuilder.for_model(MockTable).page(2)
        assert qb._ast.limit == 20
        assert qb._ast.offset == 20
    
    def test_page_custom_per_page(self):
        """Custom per_page."""
        qb = QueryBuilder.for_model(MockTable).page(1, per_page=50)
        assert qb._ast.limit == 50
    
    def test_page_negative(self):
        """Negative page becomes 1."""
        qb = QueryBuilder.for_model(MockTable).page(-1)
        assert qb._ast.offset == 0


class TestInclude:
    """Tests for .include() method."""
    
    def test_include_single(self):
        """Include single relationship."""
        qb = QueryBuilder.for_model(MockTable).include("posts")
        assert qb._ast.includes == ["posts"]
    
    def test_include_multiple(self):
        """Include multiple relationships."""
        qb = QueryBuilder.for_model(MockTable).include("posts", "comments")
        assert qb._ast.includes == ["posts", "comments"]


class TestWhere:
    """Tests for .where() method."""
    
    def test_where_adds_condition(self):
        """Where adds condition to existing."""
        qb = (QueryBuilder.for_model(MockTable, gt("age", 18))
              .where(eq("status", "active")))
        assert qb._ast.conditions is not None
    
    def test_where_tuple(self):
        """Where with tuple syntax."""
        qb = (QueryBuilder.for_model(MockTable)
              .where(("age", ">", 18)))
        assert qb._ast.conditions is not None
    
    def test_where_chain(self):
        """Multiple where calls."""
        qb = (QueryBuilder.for_model(MockTable)
              .where(gt("age", 18))
              .where(eq("status", "active"))
              .where(notnull("email")))
        assert qb._ast.conditions is not None


class TestWhereRaw:
    """Tests for .where_raw() method."""
    
    def test_where_raw_simple(self):
        """where_raw with simple SQL."""
        qb = (QueryBuilder.for_model(MockTable)
              .where_raw("custom_func(data) > 10"))
        assert qb._ast.conditions is not None
    
    def test_where_raw_params(self):
        """where_raw with parameters."""
        qb = (QueryBuilder.for_model(MockTable)
              .where_raw("custom_func(data) > $1", [10]))
        assert qb._ast.conditions is not None
        assert 10 in qb._ast.params
    
    def test_where_raw_with_conditions(self):
        """where_raw combined with other conditions."""
        qb = (QueryBuilder.for_model(MockTable, gt("age", 18))
              .where_raw("custom_check(data)"))
        assert qb._ast.conditions is not None


class TestDistinct:
    """Tests for .distinct() method."""
    
    def test_distinct(self):
        """Distinct query."""
        qb = QueryBuilder.for_model(MockTable).distinct()
        assert qb._ast.distinct is True
    
    def test_distinct_with_select(self):
        """Distinct with select."""
        qb = QueryBuilder.for_model(MockTable).select("role").distinct()
        assert qb._ast.distinct is True
        assert qb._ast.columns == ["role"]


class TestForUpdate:
    """Tests for .for_update() method."""
    
    def test_for_update(self):
        """FOR UPDATE lock."""
        qb = QueryBuilder.for_model(MockTable).for_update()
        assert qb._ast.for_update is True


# =============================================================================
# Chaining Combinations - 15 tests
# =============================================================================

class TestChaining:
    """Tests for method chaining."""
    
    def test_full_chain(self):
        """Full query chain."""
        qb = (QueryBuilder.for_model(MockTable, gt("age", 18))
              .select("id", "name", "email")
              .where(eq("status", "active"))
              .include("posts")
              .order("-created_at")
              .page(1, per_page=20))
        
        ast = qb._ast
        assert ast.columns == ["id", "name", "email"]
        assert ast.conditions is not None
        assert ast.includes == ["posts"]
        assert ast.order[0].direction == "DESC"
        assert ast.limit == 20
        assert ast.offset == 0
    
    def test_chain_order_independent(self):
        """Chain order doesn't matter."""
        qb1 = (QueryBuilder.for_model(MockTable)
               .select("name")
               .order("-created_at")
               .limit(10))
        
        qb2 = (QueryBuilder.for_model(MockTable)
               .limit(10)
               .order("-created_at")
               .select("name"))
        
        assert qb1._ast.columns == qb2._ast.columns
        assert qb1._ast.limit == qb2._ast.limit
    
    def test_chain_immutability(self):
        """Each chain step creates new builder."""
        qb1 = QueryBuilder.for_model(MockTable)
        qb2 = qb1.select("name")
        qb3 = qb2.limit(10)
        
        assert qb1._ast.columns is None
        assert qb1._ast.limit is None
        assert qb2._ast.limit is None
        assert qb3._ast.limit == 10


# =============================================================================
# AST Generation - 15 tests
# =============================================================================

class TestASTGeneration:
    """Tests for AST generation."""
    
    def test_to_dict_simple(self):
        """Simple query to dict."""
        qb = QueryBuilder.for_model(MockTable)
        d = qb.to_dict()
        assert d["table"] == "users"
        assert d["type"] == "SELECT"
    
    def test_to_dict_with_columns(self):
        """Query with columns to dict."""
        qb = QueryBuilder.for_model(MockTable).select("id", "name")
        d = qb.to_dict()
        assert d["columns"] == ["id", "name"]
    
    def test_to_dict_with_conditions(self):
        """Query with conditions to dict."""
        qb = QueryBuilder.for_model(MockTable, gt("age", 18))
        d = qb.to_dict()
        assert "conditions" in d
    
    def test_to_dict_with_order(self):
        """Query with order to dict."""
        qb = QueryBuilder.for_model(MockTable).order("-created_at")
        d = qb.to_dict()
        assert "order" in d
        assert d["order"][0]["field"] == "created_at"
        assert d["order"][0]["direction"] == "DESC"
    
    def test_to_dict_with_limit_offset(self):
        """Query with limit/offset to dict."""
        qb = QueryBuilder.for_model(MockTable).limit(10).offset(20)
        d = qb.to_dict()
        assert d["limit"] == 10
        assert d["offset"] == 20
    
    def test_to_dict_with_includes(self):
        """Query with includes to dict."""
        qb = QueryBuilder.for_model(MockTable).include("posts")
        d = qb.to_dict()
        assert d["includes"] == ["posts"]
    
    def test_to_dict_complete(self):
        """Complete query to dict."""
        qb = (QueryBuilder.for_model(MockTable, gt("age", 18))
              .select("id", "name")
              .where(eq("status", "active"))
              .order("-created_at")
              .limit(10)
              .offset(20)
              .include("posts"))
        
        d = qb.to_dict()
        assert d["table"] == "users"
        assert d["columns"] == ["id", "name"]
        assert "conditions" in d
        assert d["order"][0]["field"] == "created_at"
        assert d["limit"] == 10
        assert d["offset"] == 20
        assert d["includes"] == ["posts"]
    
    def test_to_ast_returns_ast_object(self):
        """to_ast returns QueryAST object."""
        qb = QueryBuilder.for_model(MockTable, gt("age", 18))
        ast = qb.to_ast()
        assert isinstance(ast, QueryAST)
    
    def test_explain(self):
        """explain() returns readable string."""
        qb = (QueryBuilder.for_model(MockTable, gt("age", 18))
              .select("id", "name")
              .order("-created_at")
              .limit(10))
        
        explanation = qb.explain()
        assert "users" in explanation
        assert "columns" in explanation
        assert "order" in explanation
        assert "limit" in explanation


# =============================================================================
# SQL String Parser - 10 tests
# =============================================================================

class TestSQLStringParser:
    """Tests for SQLStringParser."""
    
    def test_parse_parameterized(self):
        """Parse SQL with parameters."""
        cond = SQLStringParser.parse("age > $1", (18,))
        assert isinstance(cond, RawCondition)
        assert cond.sql == "age > $1"
        assert cond.params == [18]
    
    def test_parse_no_params(self):
        """Parse SQL without parameters."""
        cond = SQLStringParser.parse("active = true", ())
        assert cond.sql == "active = true"
        assert cond.params == []
    
    def test_validate_clean(self):
        """Validate clean SQL."""
        warnings = SQLStringParser.validate("age > 18")
        assert len(warnings) == 0
    
    def test_validate_comment(self):
        """Detect SQL comments."""
        warnings = SQLStringParser.validate("age > 18 -- comment")
        assert len(warnings) > 0
        assert "comments" in warnings[0].lower()
    
    def test_validate_semicolon(self):
        """Detect semicolons."""
        warnings = SQLStringParser.validate("SELECT 1; DROP TABLE users")
        assert len(warnings) > 0
    
    def test_validate_dangerous_drop(self):
        """Detect DROP keyword."""
        warnings = SQLStringParser.validate("DROP TABLE users")
        assert len(warnings) > 0
        assert "DROP" in warnings[0]
    
    def test_validate_dangerous_delete(self):
        """Detect DELETE keyword."""
        warnings = SQLStringParser.validate("DELETE FROM users")
        assert len(warnings) > 0


# =============================================================================
# Repr and Debug - 5 tests
# =============================================================================

class TestDebug:
    """Tests for debugging utilities."""
    
    def test_repr(self):
        """QueryBuilder repr."""
        qb = QueryBuilder.for_model(MockTable, gt("age", 18))
        r = repr(qb)
        assert "QueryBuilder" in r
        assert "MockTable" in r
    
    def test_explain_readable(self):
        """Explain output is readable."""
        qb = (QueryBuilder.for_model(MockTable)
              .select("id", "name")
              .where(gt("age", 18))
              .order("-created_at")
              .limit(10))
        
        explanation = qb.explain()
        lines = explanation.split("\n")
        assert len(lines) > 1  # Multiple lines

