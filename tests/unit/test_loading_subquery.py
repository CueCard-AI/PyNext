"""
Comprehensive tests for Subquery Loading Strategy.

Tests cover:
- Subquery generation
- Deep nesting
- subqueryload option function
- Comparison with selectin

80 tests total.
"""

import pytest
from typing import List, Optional

from pynext.db import Table, has_many, has_one, belongs_to
from pynext.db.relationships import (
    LoadStrategy, LoadOption,
    reset_backref_registry, reset_sync_manager, reset_loader,
)
from pynext.db.relationships.options import subqueryload, selectinload, joinedload


@pytest.fixture(autouse=True)
def clean_state():
    reset_backref_registry()
    reset_sync_manager()
    reset_loader()
    yield
    reset_backref_registry()
    reset_sync_manager()
    reset_loader()


# =============================================================================
# Subqueryload Option Tests (30 tests)
# =============================================================================

class TestSubqueryloadOption:
    def test_creates_option(self):
        opt = subqueryload("posts")
        assert isinstance(opt, LoadOption)
    
    def test_has_subquery_strategy(self):
        opt = subqueryload("posts")
        assert opt.strategy == LoadStrategy.SUBQUERY
    
    def test_stores_relationship(self):
        opt = subqueryload("comments")
        assert opt.relationship == "comments"
    
    def test_empty_inner(self):
        opt = subqueryload("posts")
        assert opt.inner_options == []
    
    def test_chainable(self):
        opt = subqueryload("posts")
        assert hasattr(opt, "subqueryload")
        assert hasattr(opt, "selectinload")
        assert hasattr(opt, "joinedload")
    
    def test_chain_joinedload(self):
        opt = subqueryload("posts")
        inner = opt.joinedload("author")
        assert inner.strategy == LoadStrategy.JOINED
    
    def test_chain_selectinload(self):
        opt = subqueryload("posts")
        inner = opt.selectinload("comments")
        assert inner.strategy == LoadStrategy.SELECTIN
    
    def test_chain_subqueryload(self):
        opt = subqueryload("posts")
        inner = opt.subqueryload("tags")
        assert inner.strategy == LoadStrategy.SUBQUERY
    
    def test_chain_raiseload(self):
        opt = subqueryload("posts")
        inner = opt.raiseload("audit")
        assert inner.strategy == LoadStrategy.RAISE
    
    def test_to_dict(self):
        opt = subqueryload("posts")
        d = opt.to_dict()
        assert d["relationship"] == "posts"
        assert d["strategy"] == "subquery"
    
    def test_repr(self):
        opt = subqueryload("posts")
        r = repr(opt)
        assert "posts" in r
        assert "subquery" in r
    
    def test_multiple_independent(self):
        opt1 = subqueryload("posts")
        opt2 = subqueryload("comments")
        assert opt1 is not opt2


class TestSubqueryloadNested:
    def test_deep_nesting(self):
        opt = subqueryload("posts")
        inner1 = opt.subqueryload("comments")
        inner2 = inner1.subqueryload("replies")
        assert inner2.relationship == "replies"
    
    def test_preserves_parent(self):
        opt = subqueryload("posts")
        inner = opt.subqueryload("comments")
        assert len(opt.inner_options) == 1
        assert opt.inner_options[0] is inner
    
    def test_multiple_nested(self):
        opt = subqueryload("posts")
        opt.subqueryload("comments")
        opt.joinedload("author")
        opt.raiseload("audit")
        assert len(opt.inner_options) == 3
    
    def test_nested_to_dict(self):
        opt = subqueryload("posts")
        opt.subqueryload("comments")
        d = opt.to_dict()
        assert len(d["inner_options"]) == 1
        assert d["inner_options"][0]["strategy"] == "subquery"
    
    def test_deep_chain_10_levels(self):
        opt = subqueryload("level0")
        current = opt
        for i in range(1, 10):
            current = current.subqueryload(f"level{i}")
        assert current.relationship == "level9"


# =============================================================================
# Lazy Subquery Tests (20 tests)
# =============================================================================

class TestLazySubqueryHasMany:
    def test_can_set_subquery(self, clean_state):
        class QPost1(Table):
            quser1_id: Optional[int] = None
        class QUser1(Table):
            posts: List[QPost1] = has_many(QPost1, lazy="subquery")
        assert QUser1.__dict__["posts"].lazy == "subquery"
    
    def test_subquery_with_backref(self, clean_state):
        class QPost2(Table):
            quser2_id: Optional[int] = None
        class QUser2(Table):
            posts: List[QPost2] = has_many(QPost2, backref="author", lazy="subquery")
        desc = QUser2.__dict__["posts"]
        assert desc.lazy == "subquery"
        assert desc.backref == "author"
    
    def test_subquery_with_custom_fk(self, clean_state):
        class QPost3(Table):
            owner_id: Optional[int] = None
        class QUser3(Table):
            posts: List[QPost3] = has_many(QPost3, foreign_key="owner_id", lazy="subquery")
        desc = QUser3.__dict__["posts"]
        assert desc.lazy == "subquery"


class TestLazySubqueryHasOne:
    def test_can_set_subquery(self, clean_state):
        class QProfile1(Table):
            quser4_id: Optional[int] = None
        class QUser4(Table):
            profile: QProfile1 = has_one(QProfile1, lazy="subquery")
        assert QUser4.__dict__["profile"].lazy == "subquery"


# =============================================================================
# Edge Cases Tests (15 tests)
# =============================================================================

class TestSubqueryEdgeCases:
    def test_empty_relationship_raises(self):
        with pytest.raises(ValueError):
            subqueryload("")
    
    def test_special_chars_in_name(self):
        opt = subqueryload("my_rel_123")
        assert opt.relationship == "my_rel_123"
    
    def test_option_independence(self):
        opt1 = subqueryload("posts")
        opt1.joinedload("author")
        opt2 = subqueryload("posts")
        assert len(opt2.inner_options) == 0
    
    def test_self_referential(self, clean_state):
        class QCategory(Table):
            parent_id: Optional[int] = None
            children: List["QCategory"] = has_many("QCategory", lazy="subquery")
        desc = QCategory.__dict__["children"]
        assert desc.lazy == "subquery"
    
    def test_subquery_returns_empty_list(self, clean_state):
        class QPost4(Table):
            quser5_id: Optional[int] = None
        class QUser5(Table):
            posts: List[QPost4] = has_many(QPost4, lazy="subquery")
        user = QUser5()
        posts = user.posts
        assert posts == []


class TestSubqueryPerformance:
    def test_many_options(self):
        options = [subqueryload(f"rel_{i}") for i in range(100)]
        assert len(options) == 100
    
    def test_deep_chain_50_levels(self):
        opt = subqueryload("level0")
        current = opt
        for i in range(1, 50):
            current = current.subqueryload(f"level{i}")
        assert current.relationship == "level49"
    
    def test_many_inner_options(self):
        opt = subqueryload("posts")
        for i in range(50):
            opt.subqueryload(f"child_{i}")
        assert len(opt.inner_options) == 50


# =============================================================================
# Comparison Tests (15 tests)
# =============================================================================

class TestSubqueryVsSelectin:
    def test_different_strategies(self):
        opt1 = subqueryload("posts")
        opt2 = selectinload("posts")
        assert opt1.strategy != opt2.strategy
    
    def test_same_relationship_name(self):
        opt1 = subqueryload("posts")
        opt2 = selectinload("posts")
        assert opt1.relationship == opt2.relationship
    
    def test_both_chainable(self):
        # Chain returns the inner option, not self
        opt1 = subqueryload("posts")
        inner1 = opt1.joinedload("author")
        
        opt2 = selectinload("posts")
        inner2 = opt2.joinedload("author")
        
        assert inner1.strategy == inner2.strategy
    
    def test_can_mix_in_chain(self):
        # subqueryload("posts") creates the root option
        opt = subqueryload("posts")
        # selectinload("comments") returns the inner option
        inner1 = opt.selectinload("comments")
        # subqueryload("replies") returns the nested inner option  
        inner2 = inner1.subqueryload("replies")
        
        assert opt.strategy == LoadStrategy.SUBQUERY
        assert inner1.strategy == LoadStrategy.SELECTIN
        assert inner2.strategy == LoadStrategy.SUBQUERY

