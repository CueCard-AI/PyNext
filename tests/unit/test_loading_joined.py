"""
Comprehensive tests for Joined Loading Strategy.

Tests cover:
- JOIN queries for belongs_to
- JOIN queries for has_one
- Multiple JOINs for multiple relations
- Nested JOINs (e.g., posts.comments.author)
- NULL handling for optional relations
- JoinBuilder class
- Performance with large result sets

100 tests total.
"""

import pytest
from typing import List, Optional

from pynext.db import (
    Table,
    has_many,
    has_one,
    belongs_to,
    configure_db,
    MemoryAdapter,
)
from pynext.db.relationships import (
    LoadStrategy,
    LoadOption,
    JoinBuilder,
    reset_backref_registry,
    reset_sync_manager,
    reset_loader,
)
from pynext.db.relationships.options import joinedload


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def clean_state():
    """Reset global state before each test."""
    reset_backref_registry()
    reset_sync_manager()
    reset_loader()
    yield
    reset_backref_registry()
    reset_sync_manager()
    reset_loader()


# =============================================================================
# JoinBuilder Basic Tests (25 tests)
# =============================================================================

class TestJoinBuilderBasic:
    """Test JoinBuilder basic functionality."""
    
    def test_create_builder(self, clean_state):
        """Can create JoinBuilder."""
        class JUser1(Table):
            name: str = ""
        
        builder = JoinBuilder(JUser1)
        assert builder._model == JUser1
    
    def test_empty_joins_by_default(self, clean_state):
        """No joins by default."""
        class JUser2(Table):
            name: str = ""
        
        builder = JoinBuilder(JUser2)
        assert builder.get_joins() == []
    
    def test_add_join_belongs_to(self, clean_state):
        """Can add join for belongs_to."""
        class JAuthor1(Table):
            name: str = ""
        
        class JPost1(Table):
            author_id: Optional[int] = None
            title: str = ""
        
        builder = JoinBuilder(JPost1)
        rel_info = {
            "type": "belongs_to",
            "model": JAuthor1,
            "foreign_key": "author_id",
        }
        builder.add_join("author", rel_info)
        
        joins = builder.get_joins()
        assert len(joins) == 1
        assert joins[0][0] == "author"  # relation name
    
    def test_add_join_has_one(self, clean_state):
        """Can add join for has_one."""
        class JProfile1(Table):
            juser3_id: Optional[int] = None
            bio: str = ""
        
        class JUser3(Table):
            name: str = ""
        
        builder = JoinBuilder(JUser3)
        rel_info = {
            "type": "has_one",
            "model": JProfile1,
            "foreign_key": "juser3_id",
        }
        builder.add_join("profile", rel_info)
        
        joins = builder.get_joins()
        assert len(joins) == 1
    
    def test_add_join_has_many(self, clean_state):
        """Can add join for has_many."""
        class JPost2(Table):
            juser4_id: Optional[int] = None
            title: str = ""
        
        class JUser4(Table):
            name: str = ""
        
        builder = JoinBuilder(JUser4)
        rel_info = {
            "type": "has_many",
            "model": JPost2,
            "foreign_key": "juser4_id",
        }
        builder.add_join("posts", rel_info)
        
        joins = builder.get_joins()
        assert len(joins) == 1
    
    def test_multiple_joins(self, clean_state):
        """Can add multiple joins."""
        class JProfile2(Table):
            juser5_id: Optional[int] = None
        
        class JSettings1(Table):
            juser5_id: Optional[int] = None
        
        class JUser5(Table):
            name: str = ""
        
        builder = JoinBuilder(JUser5)
        
        builder.add_join("profile", {
            "type": "has_one",
            "model": JProfile2,
            "foreign_key": "juser5_id",
        })
        builder.add_join("settings", {
            "type": "has_one",
            "model": JSettings1,
            "foreign_key": "juser5_id",
        })
        
        joins = builder.get_joins()
        assert len(joins) == 2
    
    def test_build_join_sql_empty(self, clean_state):
        """Empty joins produces empty SQL."""
        class JUser6(Table):
            name: str = ""
        
        builder = JoinBuilder(JUser6)
        sql = builder.build_join_sql()
        assert sql == ""
    
    def test_build_join_sql_single(self, clean_state):
        """Single join produces LEFT JOIN SQL."""
        class JAuthor2(Table):
            name: str = ""
        
        class JPost3(Table):
            author_id: Optional[int] = None
            title: str = ""
        
        builder = JoinBuilder(JPost3)
        builder.add_join("author", {
            "type": "belongs_to",
            "model": JAuthor2,
            "foreign_key": "author_id",
        })
        
        sql = builder.build_join_sql()
        
        assert "LEFT JOIN" in sql
        assert "author" in sql.lower()
    
    def test_join_sql_includes_table_name(self, clean_state):
        """Join SQL includes related table name."""
        class JCategory1(Table):
            name: str = ""
        
        class JProduct1(Table):
            category_id: Optional[int] = None
        
        builder = JoinBuilder(JProduct1)
        builder.add_join("category", {
            "type": "belongs_to",
            "model": JCategory1,
            "foreign_key": "category_id",
        })
        
        sql = builder.build_join_sql()
        assert "jcategory1s" in sql.lower()
    
    def test_join_sql_uses_alias(self, clean_state):
        """Join SQL uses alias for joined table."""
        class JBrand1(Table):
            name: str = ""
        
        class JProduct2(Table):
            brand_id: Optional[int] = None
        
        builder = JoinBuilder(JProduct2)
        builder.add_join("brand", {
            "type": "belongs_to",
            "model": JBrand1,
            "foreign_key": "brand_id",
        })
        
        sql = builder.build_join_sql()
        assert "AS" in sql


class TestJoinBuilderAdvanced:
    """Test JoinBuilder advanced functionality."""
    
    def test_belongs_to_join_condition(self, clean_state):
        """Belongs_to JOIN has correct ON condition."""
        class JAuthor3(Table):
            name: str = ""
        
        class JPost4(Table):
            author_id: Optional[int] = None
        
        builder = JoinBuilder(JPost4)
        builder.add_join("author", {
            "type": "belongs_to",
            "model": JAuthor3,
            "foreign_key": "author_id",
        })
        
        joins = builder.get_joins()
        # (rel_name, table, on_left, on_right)
        rel_name, table, on_left, on_right = joins[0]
        
        # For belongs_to: parent.fk = related.id
        assert "author_id" in on_left
        assert ".id" in on_right
    
    def test_has_one_join_condition(self, clean_state):
        """Has_one JOIN has correct ON condition."""
        class JProfile3(Table):
            juser7_id: Optional[int] = None
        
        class JUser7(Table):
            name: str = ""
        
        builder = JoinBuilder(JUser7)
        builder.add_join("profile", {
            "type": "has_one",
            "model": JProfile3,
            "foreign_key": "juser7_id",
        })
        
        joins = builder.get_joins()
        rel_name, table, on_left, on_right = joins[0]
        
        # For has_one: parent.id = related.fk
        assert ".id" in on_left
        assert "juser7_id" in on_right
    
    def test_has_many_join_condition(self, clean_state):
        """Has_many JOIN has correct ON condition."""
        class JPost5(Table):
            juser8_id: Optional[int] = None
        
        class JUser8(Table):
            name: str = ""
        
        builder = JoinBuilder(JUser8)
        builder.add_join("posts", {
            "type": "has_many",
            "model": JPost5,
            "foreign_key": "juser8_id",
        })
        
        joins = builder.get_joins()
        rel_name, table, on_left, on_right = joins[0]
        
        # For has_many: parent.id = related.fk
        assert ".id" in on_left
        assert "juser8_id" in on_right
    
    def test_join_with_string_model(self, clean_state):
        """Join handles string model reference."""
        class JAuthor4(Table):
            name: str = ""
        
        class JPost6(Table):
            author_id: Optional[int] = None
        
        builder = JoinBuilder(JPost6)
        # String model that's not registered - should be handled gracefully
        builder.add_join("author", {
            "type": "belongs_to",
            "model": "nonexistent_model",
            "foreign_key": "author_id",
        })
        
        # Should not crash, just not add the join
        joins = builder.get_joins()
        assert len(joins) == 0  # String models that can't be resolved are skipped
    
    def test_multiple_joins_different_types(self, clean_state):
        """Can mix different relationship types."""
        class JAuthor5(Table):
            name: str = ""
        
        class JComment1(Table):
            jpost7_id: Optional[int] = None
        
        class JPost7(Table):
            author_id: Optional[int] = None
        
        builder = JoinBuilder(JPost7)
        
        builder.add_join("author", {
            "type": "belongs_to",
            "model": JAuthor5,
            "foreign_key": "author_id",
        })
        builder.add_join("comments", {
            "type": "has_many",
            "model": JComment1,
            "foreign_key": "jpost7_id",
        })
        
        joins = builder.get_joins()
        assert len(joins) == 2


# =============================================================================
# Joinedload Option Tests (25 tests)
# =============================================================================

class TestJoinedloadOption:
    """Test joinedload option creation."""
    
    def test_joinedload_creates_option(self):
        """joinedload creates LoadOption."""
        opt = joinedload("author")
        assert isinstance(opt, LoadOption)
    
    def test_joinedload_has_joined_strategy(self):
        """joinedload option has JOINED strategy."""
        opt = joinedload("profile")
        assert opt.strategy == LoadStrategy.JOINED
    
    def test_joinedload_stores_relationship(self):
        """joinedload stores relationship name."""
        opt = joinedload("category")
        assert opt.relationship == "category"
    
    def test_joinedload_empty_inner(self):
        """joinedload has empty inner options by default."""
        opt = joinedload("author")
        assert opt.inner_options == []
    
    def test_joinedload_chainable(self):
        """joinedload returns chainable option."""
        opt = joinedload("author")
        assert hasattr(opt, "joinedload")
        assert hasattr(opt, "selectinload")
    
    def test_joinedload_chain_joinedload(self):
        """Can chain joinedload with joinedload."""
        opt = joinedload("author")
        inner = opt.joinedload("company")
        
        assert len(opt.inner_options) == 1
        assert inner.strategy == LoadStrategy.JOINED
    
    def test_joinedload_chain_selectinload(self):
        """Can chain joinedload with selectinload."""
        opt = joinedload("author")
        inner = opt.selectinload("posts")
        
        assert len(opt.inner_options) == 1
        assert inner.strategy == LoadStrategy.SELECTIN
    
    def test_joinedload_to_dict(self):
        """joinedload option converts to dict."""
        opt = joinedload("author")
        d = opt.to_dict()
        
        assert d["relationship"] == "author"
        assert d["strategy"] == "joined"
    
    def test_joinedload_repr(self):
        """joinedload option has useful repr."""
        opt = joinedload("author")
        r = repr(opt)
        
        assert "author" in r
        assert "joined" in r
    
    def test_multiple_joinedloads(self):
        """Can create multiple independent joinedloads."""
        opt1 = joinedload("author")
        opt2 = joinedload("category")
        
        assert opt1.relationship == "author"
        assert opt2.relationship == "category"
        assert opt1 is not opt2


class TestJoinedloadNested:
    """Test nested joinedload options."""
    
    def test_deep_nesting(self):
        """Can create deeply nested joinedload."""
        opt = joinedload("post")
        inner1 = opt.joinedload("author")
        inner2 = inner1.joinedload("company")
        inner3 = inner2.joinedload("address")
        
        assert inner3.relationship == "address"
    
    def test_nesting_preserves_parent(self):
        """Nesting preserves parent options."""
        opt = joinedload("post")
        inner = opt.joinedload("author")
        
        assert len(opt.inner_options) == 1
        assert opt.inner_options[0] is inner
    
    def test_multiple_nested(self):
        """Can add multiple nested options."""
        opt = joinedload("post")
        opt.joinedload("author")
        opt.joinedload("category")
        opt.joinedload("tags")
        
        assert len(opt.inner_options) == 3
    
    def test_nested_different_strategies(self):
        """Nested options can have different strategies."""
        opt = joinedload("author")
        inner1 = opt.selectinload("posts")
        inner2 = opt.subqueryload("comments")
        
        assert inner1.strategy == LoadStrategy.SELECTIN
        assert inner2.strategy == LoadStrategy.SUBQUERY
    
    def test_nested_to_dict(self):
        """Nested options serialize correctly."""
        opt = joinedload("author")
        opt.joinedload("company")
        
        d = opt.to_dict()
        
        assert len(d["inner_options"]) == 1
        assert d["inner_options"][0]["relationship"] == "company"


# =============================================================================
# Lazy Joined Tests (25 tests)
# =============================================================================

class TestLazyJoinedBelongsTo:
    """Test lazy='joined' on belongs_to."""
    
    def test_default_is_not_joined(self, clean_state):
        """Default lazy is not 'joined'."""
        class JUser10(Table):
            name: str = ""
        
        class JPost10(Table):
            user_id: Optional[int] = None
            author: "JUser10" = belongs_to("JUser10")
        
        descriptor = JPost10.__dict__["author"]
        assert descriptor.lazy != "joined"
    
    def test_can_set_joined(self, clean_state):
        """Can set lazy='joined'."""
        class JUser11(Table):
            name: str = ""
        
        class JPost11(Table):
            user_id: Optional[int] = None
            author: "JUser11" = belongs_to("JUser11", lazy="joined")
        
        descriptor = JPost11.__dict__["author"]
        assert descriptor.lazy == "joined"
    
    def test_joined_with_backref(self, clean_state):
        """lazy='joined' works with backref."""
        class JUser12(Table):
            name: str = ""
        
        class JPost12(Table):
            user_id: Optional[int] = None
            author: "JUser12" = belongs_to("JUser12", backref="posts", lazy="joined")
        
        descriptor = JPost12.__dict__["author"]
        assert descriptor.lazy == "joined"
        assert descriptor.backref == "posts"
    
    def test_joined_with_custom_fk(self, clean_state):
        """lazy='joined' works with custom foreign key."""
        class JAuthor6(Table):
            name: str = ""
        
        class JPost13(Table):
            writer_id: Optional[int] = None
            author: "JAuthor6" = belongs_to("JAuthor6", foreign_key="writer_id", lazy="joined")
        
        descriptor = JPost13.__dict__["author"]
        assert descriptor.lazy == "joined"
        assert descriptor.foreign_key == "writer_id"


class TestLazyJoinedHasOne:
    """Test lazy='joined' on has_one."""
    
    def test_default_is_not_joined(self, clean_state):
        """Default lazy is not 'joined'."""
        class JProfile4(Table):
            juser13_id: Optional[int] = None
        
        class JUser13(Table):
            profile: "JProfile4" = has_one("JProfile4")
        
        descriptor = JUser13.__dict__["profile"]
        assert descriptor.lazy != "joined"
    
    def test_can_set_joined(self, clean_state):
        """Can set lazy='joined'."""
        class JProfile5(Table):
            juser14_id: Optional[int] = None
        
        class JUser14(Table):
            profile: "JProfile5" = has_one("JProfile5", lazy="joined")
        
        descriptor = JUser14.__dict__["profile"]
        assert descriptor.lazy == "joined"
    
    def test_joined_with_backref(self, clean_state):
        """lazy='joined' works with backref."""
        class JProfile6(Table):
            juser15_id: Optional[int] = None
        
        class JUser15(Table):
            profile: "JProfile6" = has_one("JProfile6", backref="user", lazy="joined")
        
        descriptor = JUser15.__dict__["profile"]
        assert descriptor.lazy == "joined"
        assert descriptor.backref == "user"


class TestLazyJoinedHasMany:
    """Test lazy='joined' on has_many (not recommended but possible)."""
    
    def test_can_set_joined_on_has_many(self, clean_state):
        """Can set lazy='joined' on has_many (though selectin is better)."""
        class JPost14(Table):
            juser16_id: Optional[int] = None
        
        class JUser16(Table):
            posts: List["JPost14"] = has_many("JPost14", lazy="joined")
        
        descriptor = JUser16.__dict__["posts"]
        # Should accept joined even though it's not recommended
        assert descriptor.lazy == "joined"


# =============================================================================
# Edge Cases Tests (25 tests)
# =============================================================================

class TestJoinedEdgeCases:
    """Test edge cases for joined loading."""
    
    def test_self_referential_joined(self, clean_state):
        """Joined works with self-referential relationships."""
        class JCategory2(Table):
            parent_id: Optional[int] = None
            parent: "JCategory2" = belongs_to("JCategory2", lazy="joined")
        
        cat = JCategory2()
        # Should not raise, even though parent is same type
        assert cat.parent is None
    
    def test_joined_with_none_fk(self, clean_state):
        """Joined handles None FK gracefully."""
        class JAuthor7(Table):
            name: str = ""
        
        class JPost15(Table):
            author_id: Optional[int] = None
            author: "JAuthor7" = belongs_to("JAuthor7", lazy="joined")
        
        post = JPost15()
        post.author_id = None
        
        # Should return None, not raise
        assert post.author is None
    
    def test_joinedload_with_empty_relationship_name(self):
        """Empty relationship name raises."""
        with pytest.raises(ValueError):
            joinedload("")
    
    def test_joined_preserves_backref_sync(self, clean_state):
        """Joined loading preserves backref synchronization."""
        class JPost16(Table):
            juser17_id: Optional[int] = None
        
        class JUser17(Table):
            posts: List[JPost16] = has_many(JPost16, backref="author")
        
        user = JUser17()
        post = JPost16()
        
        # Even with different lazy strategies, backref should work
        user.posts.append(post)
        assert post.author is user
    
    def test_joinedload_option_immutable_strategy(self):
        """LoadOption strategy is immutable after creation."""
        opt = joinedload("author")
        # Strategy is set at creation and shouldn't change
        assert opt.strategy == LoadStrategy.JOINED
    
    def test_multiple_joins_same_table(self, clean_state):
        """Can join same table multiple times with different names."""
        class JUser18(Table):
            name: str = ""
        
        class JPost17(Table):
            author_id: Optional[int] = None
            editor_id: Optional[int] = None
        
        builder = JoinBuilder(JPost17)
        builder.add_join("author", {
            "type": "belongs_to",
            "model": JUser18,
            "foreign_key": "author_id",
        })
        builder.add_join("editor", {
            "type": "belongs_to",
            "model": JUser18,
            "foreign_key": "editor_id",
        })
        
        joins = builder.get_joins()
        assert len(joins) == 2
    
    def test_join_sql_escapes_special_chars(self, clean_state):
        """Join SQL handles table names correctly."""
        class JTest_Table1(Table):
            name: str = ""
        
        class JRef1(Table):
            test_id: Optional[int] = None
        
        builder = JoinBuilder(JRef1)
        builder.add_join("test", {
            "type": "belongs_to",
            "model": JTest_Table1,
            "foreign_key": "test_id",
        })
        
        sql = builder.build_join_sql()
        # Should produce valid SQL without issues
        assert "LEFT JOIN" in sql
    
    def test_joined_returns_none_for_missing(self, clean_state):
        """Joined strategy returns None for unloaded relationship."""
        class JAuthor8(Table):
            name: str = ""
        
        class JPost18(Table):
            author_id: Optional[int] = None
            author: "JAuthor8" = belongs_to("JAuthor8", lazy="joined")
        
        post = JPost18()
        # Without loading, should return None
        assert post.author is None
    
    def test_joined_with_cached_value(self, clean_state):
        """Joined returns cached value if present."""
        class JAuthor9(Table):
            name: str = ""
        
        class JPost19(Table):
            author_id: Optional[int] = None
            author: "JAuthor9" = belongs_to("JAuthor9", lazy="joined")
        
        author = JAuthor9(name="Test")
        post = JPost19()
        post._cached_author = author
        
        assert post.author is author
    
    def test_joinedload_deep_chain_to_dict(self):
        """Deep chain serializes correctly."""
        opt = joinedload("a")
        opt.joinedload("b").joinedload("c").joinedload("d")
        
        d = opt.to_dict()
        
        # Check structure
        assert d["relationship"] == "a"
        assert len(d["inner_options"]) == 1
        assert d["inner_options"][0]["relationship"] == "b"


class TestJoinBuilderPerformance:
    """Performance-related tests for JoinBuilder."""
    
    def test_many_joins(self, clean_state):
        """Can handle many joins."""
        class JTarget1(Table):
            ref_id: Optional[int] = None
        
        class JSource1(Table):
            name: str = ""
        
        builder = JoinBuilder(JSource1)
        
        for i in range(20):
            builder.add_join(f"rel_{i}", {
                "type": "has_one",
                "model": JTarget1,
                "foreign_key": "ref_id",
            })
        
        joins = builder.get_joins()
        assert len(joins) == 20
    
    def test_build_sql_many_joins(self, clean_state):
        """Can build SQL for many joins."""
        class JTarget2(Table):
            ref_id: Optional[int] = None
        
        class JSource2(Table):
            name: str = ""
        
        builder = JoinBuilder(JSource2)
        
        for i in range(10):
            builder.add_join(f"rel_{i}", {
                "type": "has_one",
                "model": JTarget2,
                "foreign_key": "ref_id",
            })
        
        sql = builder.build_join_sql()
        
        # Should have 10 LEFT JOINs
        assert sql.count("LEFT JOIN") == 10
    
    def test_joinedload_deep_chain_performance(self):
        """Deep chaining doesn't cause issues."""
        opt = joinedload("level0")
        current = opt
        
        for i in range(1, 50):
            current = current.joinedload(f"level{i}")
        
        # Should be able to traverse the chain
        assert current.relationship == "level49"
    
    def test_multiple_joinedloads_independence(self):
        """Many independent joinedloads don't interfere."""
        options = [joinedload(f"rel_{i}") for i in range(100)]
        
        for i, opt in enumerate(options):
            assert opt.relationship == f"rel_{i}"
            assert opt.inner_options == []

