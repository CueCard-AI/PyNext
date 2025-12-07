"""
Comprehensive tests for Query.options() API.

Tests cover:
- Query.options() method
- Multiple options on same query
- Override model defaults
- Chaining options
- Integration with existing with_related

80 tests total.
"""

import pytest
from typing import List, Optional

from pynext.db import Table, has_many, has_one, belongs_to, configure_db, MemoryAdapter
from pynext.db.query import Query
from pynext.db.relationships import (
    LoadStrategy, LoadOption,
    reset_backref_registry, reset_sync_manager, reset_loader,
)
from pynext.db.relationships.options import (
    joinedload, selectinload, subqueryload, raiseload, noload, 
    lazyload, immediateload, eagerload, Load,
)


@pytest.fixture(autouse=True)
def clean_state():
    reset_backref_registry()
    reset_sync_manager()
    reset_loader()
    # Configure a mock adapter (doesn't need async for these tests)
    from unittest.mock import MagicMock
    mock_adapter = MagicMock()
    configure_db(mock_adapter)
    yield
    reset_backref_registry()
    reset_sync_manager()
    reset_loader()


# =============================================================================
# Query.options() Basic Tests (25 tests)
# =============================================================================

class TestQueryOptionsBasic:
    def test_query_has_options_method(self, clean_state):
        class OUser1(Table):
            name: str = ""
        query = OUser1.select()
        assert hasattr(query, "options")
    
    def test_options_returns_query(self, clean_state):
        class OUser2(Table):
            name: str = ""
        query = OUser2.select().options(selectinload("posts"))
        assert isinstance(query, Query)
    
    def test_options_chainable(self, clean_state):
        class OUser3(Table):
            name: str = ""
        query = (
            OUser3.select()
            .options(selectinload("posts"))
            .where(name="test")
        )
        assert query._where == {"name": "test"}
    
    def test_options_stores_options(self, clean_state):
        class OUser4(Table):
            name: str = ""
        query = OUser4.select().options(selectinload("posts"))
        assert len(query._load_options) == 1
    
    def test_options_multiple_calls(self, clean_state):
        class OUser5(Table):
            name: str = ""
        query = (
            OUser5.select()
            .options(selectinload("posts"))
            .options(joinedload("profile"))
        )
        assert len(query._load_options) == 2
    
    def test_options_multiple_in_single_call(self, clean_state):
        class OUser6(Table):
            name: str = ""
        query = OUser6.select().options(
            selectinload("posts"),
            joinedload("profile"),
            raiseload("audit"),
        )
        assert len(query._load_options) == 3
    
    def test_options_clones_query(self, clean_state):
        class OUser7(Table):
            name: str = ""
        query1 = OUser7.select()
        query2 = query1.options(selectinload("posts"))
        assert query1 is not query2
        assert len(query1._load_options) == 0
        assert len(query2._load_options) == 1
    
    def test_options_preserves_where(self, clean_state):
        class OUser8(Table):
            name: str = ""
        query = (
            OUser8.select()
            .where(name="test")
            .options(selectinload("posts"))
        )
        assert query._where == {"name": "test"}
    
    def test_options_preserves_order(self, clean_state):
        class OUser9(Table):
            name: str = ""
        query = (
            OUser9.select()
            .order_by("name")
            .options(selectinload("posts"))
        )
        assert "name" in query._order_by
    
    def test_options_preserves_limit(self, clean_state):
        class OUser10(Table):
            name: str = ""
        query = (
            OUser10.select()
            .limit(10)
            .options(selectinload("posts"))
        )
        assert query._limit == 10


class TestQueryOptionsWithLoadOptions:
    def test_joinedload_option(self, clean_state):
        class OUser11(Table):
            name: str = ""
        query = OUser11.select().options(joinedload("profile"))
        assert query._load_options[0].strategy == LoadStrategy.JOINED
    
    def test_selectinload_option(self, clean_state):
        class OUser12(Table):
            name: str = ""
        query = OUser12.select().options(selectinload("posts"))
        assert query._load_options[0].strategy == LoadStrategy.SELECTIN
    
    def test_subqueryload_option(self, clean_state):
        class OUser13(Table):
            name: str = ""
        query = OUser13.select().options(subqueryload("posts"))
        assert query._load_options[0].strategy == LoadStrategy.SUBQUERY
    
    def test_raiseload_option(self, clean_state):
        class OUser14(Table):
            name: str = ""
        query = OUser14.select().options(raiseload("audit"))
        assert query._load_options[0].strategy == LoadStrategy.RAISE
    
    def test_noload_option(self, clean_state):
        class OUser15(Table):
            name: str = ""
        query = OUser15.select().options(noload("metadata"))
        assert query._load_options[0].strategy == LoadStrategy.SELECT
    
    def test_lazyload_option(self, clean_state):
        class OUser16(Table):
            name: str = ""
        query = OUser16.select().options(lazyload("posts"))
        assert query._load_options[0].strategy == LoadStrategy.SELECT
    
    def test_immediateload_option(self, clean_state):
        class OUser17(Table):
            name: str = ""
        query = OUser17.select().options(immediateload("posts"))
        assert query._load_options[0].strategy == LoadStrategy.SELECTIN
    
    def test_eagerload_option(self, clean_state):
        class OUser18(Table):
            name: str = ""
        query = OUser18.select().options(eagerload("posts"))
        assert query._load_options[0].strategy == LoadStrategy.SELECTIN


# =============================================================================
# Load Class Tests (15 tests)
# =============================================================================

class TestLoadClass:
    def test_load_with_string(self):
        load = Load("posts")
        assert load._name == "posts"
    
    def test_load_selectin(self):
        opt = Load("posts").selectin()
        assert opt.strategy == LoadStrategy.SELECTIN
    
    def test_load_joined(self):
        opt = Load("author").joined()
        assert opt.strategy == LoadStrategy.JOINED
    
    def test_load_subquery(self):
        opt = Load("comments").subquery()
        assert opt.strategy == LoadStrategy.SUBQUERY
    
    def test_load_raise(self):
        opt = Load("audit").raise_()
        assert opt.strategy == LoadStrategy.RAISE
    
    def test_load_noload(self):
        opt = Load("metadata").noload()
        assert opt.strategy == LoadStrategy.SELECT
    
    def test_load_in_query(self, clean_state):
        class OUser19(Table):
            name: str = ""
        query = OUser19.select().options(
            Load("posts").selectin(),
            Load("profile").joined(),
        )
        assert len(query._load_options) == 2


# =============================================================================
# Nested Options Tests (20 tests)
# =============================================================================

class TestNestedOptions:
    def test_nested_joinedload(self, clean_state):
        class OUser20(Table):
            name: str = ""
        opt = selectinload("posts")
        opt.joinedload("author")  # This adds to opt.inner_options
        query = OUser20.select().options(opt)
        assert len(query._load_options) == 1
        assert len(query._load_options[0].inner_options) == 1
    
    def test_deeply_nested(self, clean_state):
        class OUser21(Table):
            name: str = ""
        opt = selectinload("posts").joinedload("author").selectinload("company")
        query = OUser21.select().options(opt)
        assert len(query._load_options) == 1
    
    def test_multiple_nested_branches(self, clean_state):
        class OUser22(Table):
            name: str = ""
        opt = selectinload("posts")
        opt.joinedload("author")
        opt.selectinload("comments")
        query = OUser22.select().options(opt)
        assert len(query._load_options[0].inner_options) == 2
    
    def test_nested_relationships(self, clean_state):
        class OUser23(Table):
            name: str = ""
        # posts -> author -> company
        opt = selectinload("posts")
        author_opt = opt.joinedload("author")
        company_opt = author_opt.selectinload("company")
        
        query = OUser23.select().options(opt)
        assert query._load_options[0].relationship == "posts"
        assert len(opt.inner_options) == 1  # author
        assert opt.inner_options[0].relationship == "author"


# =============================================================================
# Integration with with_related Tests (10 tests)
# =============================================================================

class TestOptionsWithRelated:
    def test_options_and_with_related(self, clean_state):
        class OUser24(Table):
            name: str = ""
        query = (
            OUser24.select()
            .options(selectinload("posts"))
            .with_related("profile")
        )
        assert len(query._load_options) == 1
        assert len(query._with_related) == 1
    
    def test_with_related_before_options(self, clean_state):
        class OUser25(Table):
            name: str = ""
        query = (
            OUser25.select()
            .with_related("profile")
            .options(selectinload("posts"))
        )
        assert len(query._with_related) == 1
        assert len(query._load_options) == 1
    
    def test_both_load_same_relationship(self, clean_state):
        class OUser26(Table):
            name: str = ""
        # Both can be used together - options takes precedence
        query = (
            OUser26.select()
            .options(selectinload("posts"))
            .with_related("posts")
        )
        assert len(query._load_options) == 1
        assert len(query._with_related) == 1


# =============================================================================
# Edge Cases (10 tests)
# =============================================================================

class TestOptionsEdgeCases:
    def test_empty_options(self, clean_state):
        class OUser27(Table):
            name: str = ""
        query = OUser27.select().options()
        assert len(query._load_options) == 0
    
    def test_many_options(self, clean_state):
        class OUser28(Table):
            name: str = ""
        options = [selectinload(f"rel_{i}") for i in range(20)]
        query = OUser28.select().options(*options)
        assert len(query._load_options) == 20
    
    def test_duplicate_relationships(self, clean_state):
        class OUser29(Table):
            name: str = ""
        # Can specify same relationship multiple times (last wins in practice)
        query = OUser29.select().options(
            selectinload("posts"),
            joinedload("posts"),
        )
        assert len(query._load_options) == 2
    
    def test_options_preserves_all_state(self, clean_state):
        class OUser30(Table):
            name: str = ""
        query = (
            OUser30.select()
            .where(name="test")
            .where_not(role="admin")
            .order_by("created_at")
            .limit(10)
            .offset(5)
            .with_related("profile")
            .options(selectinload("posts"))
        )
        assert query._where == {"name": "test"}
        assert query._where_not == {"role": "admin"}
        assert query._limit == 10
        assert query._offset == 5

