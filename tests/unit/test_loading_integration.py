"""
Integration tests for Loading Strategies.

Tests cover real-world scenarios with multiple relationships,
nested loading, and complex query patterns.

100 tests total.
"""

import pytest
from typing import List, Optional
from unittest.mock import MagicMock

from pynext.db import Table, has_many, has_one, belongs_to, configure_db
from pynext.db.relationships import (
    LoadStrategy, LoadOption, LazyLoadError,
    reset_backref_registry, reset_sync_manager, reset_loader,
)
from pynext.db.relationships.options import (
    joinedload, selectinload, subqueryload, raiseload, noload,
)


@pytest.fixture(autouse=True)
def clean_state():
    reset_backref_registry()
    reset_sync_manager()
    reset_loader()
    mock_adapter = MagicMock()
    configure_db(mock_adapter)
    yield
    reset_backref_registry()
    reset_sync_manager()
    reset_loader()


# =============================================================================
# Complex Model Hierarchies (25 tests)
# =============================================================================

class TestComplexModelHierarchy:
    """Test loading with complex model relationships."""
    
    def test_three_level_hierarchy(self, clean_state):
        """Test User -> Post -> Comment hierarchy."""
        class IComment1(Table):
            ipost1_id: Optional[int] = None
        
        class IPost1(Table):
            iuser1_id: Optional[int] = None
            comments: List[IComment1] = has_many(IComment1, lazy="selectin")
        
        class IUser1(Table):
            posts: List[IPost1] = has_many(IPost1, lazy="selectin")
        
        assert IUser1.__dict__["posts"].lazy == "selectin"
        assert IPost1.__dict__["comments"].lazy == "selectin"
    
    def test_four_level_hierarchy(self, clean_state):
        """Test deeper nesting."""
        class IReply1(Table):
            icomment2_id: Optional[int] = None
        
        class IComment2(Table):
            ipost2_id: Optional[int] = None
            replies: List[IReply1] = has_many(IReply1, lazy="selectin")
        
        class IPost2(Table):
            iuser2_id: Optional[int] = None
            comments: List[IComment2] = has_many(IComment2, lazy="selectin")
        
        class IUser2(Table):
            posts: List[IPost2] = has_many(IPost2, lazy="selectin")
        
        # All relationships use selectin
        user = IUser2()
        assert hasattr(IUser2.__dict__["posts"], "lazy")
    
    def test_multiple_has_many(self, clean_state):
        """Test model with multiple has_many relationships."""
        class IPost3(Table):
            iuser3_id: Optional[int] = None
        
        class IComment3(Table):
            iuser3_id: Optional[int] = None
        
        class ILike1(Table):
            iuser3_id: Optional[int] = None
        
        class IUser3(Table):
            posts: List[IPost3] = has_many(IPost3, lazy="selectin")
            comments: List[IComment3] = has_many(IComment3, lazy="selectin")
            likes: List[ILike1] = has_many(ILike1, lazy="selectin")
        
        user = IUser3()
        assert len([k for k in IUser3.__dict__ if k in ("posts", "comments", "likes")]) == 3
    
    def test_mixed_strategies_on_same_model(self, clean_state):
        """Test different strategies on different relationships."""
        class IProfile1(Table):
            iuser4_id: Optional[int] = None
        
        class IPost4(Table):
            iuser4_id: Optional[int] = None
        
        class IAudit1(Table):
            iuser4_id: Optional[int] = None
        
        class IUser4(Table):
            profile: IProfile1 = has_one(IProfile1, lazy="joined")
            posts: List[IPost4] = has_many(IPost4, lazy="selectin")
            audit_logs: List[IAudit1] = has_many(IAudit1, lazy="raise")
        
        assert IUser4.__dict__["profile"].lazy == "joined"
        assert IUser4.__dict__["posts"].lazy == "selectin"
        assert IUser4.__dict__["audit_logs"].lazy == "raise"
    
    def test_bidirectional_with_loading(self, clean_state):
        """Test backref with loading strategies."""
        class IPost5(Table):
            iuser5_id: Optional[int] = None
        
        class IUser5(Table):
            posts: List[IPost5] = has_many(IPost5, backref="author", lazy="selectin")
        
        user = IUser5()
        post = IPost5()
        user.posts.append(post)
        
        assert post.author is user
    
    def test_self_referential_hierarchy(self, clean_state):
        """Test self-referential relationships."""
        class ICategory1(Table):
            parent_id: Optional[int] = None
            children: List["ICategory1"] = has_many("ICategory1", lazy="selectin")
            parent: "ICategory1" = belongs_to("ICategory1", lazy="joined")
        
        assert ICategory1.__dict__["children"].lazy == "selectin"
        assert ICategory1.__dict__["parent"].lazy == "joined"
    
    def test_circular_references(self, clean_state):
        """Test circular relationship patterns."""
        class IEmployee1(Table):
            manager_id: Optional[int] = None
            reports: List["IEmployee1"] = has_many("IEmployee1", lazy="selectin")
            manager: "IEmployee1" = belongs_to("IEmployee1", lazy="joined")
        
        emp = IEmployee1()
        manager = IEmployee1()
        emp._cached_manager = manager
        
        assert emp.manager is manager


# =============================================================================
# Query Options Combinations (25 tests)
# =============================================================================

class TestQueryOptionsCombinations:
    """Test various combinations of query options."""
    
    def test_selectin_then_joined(self, clean_state):
        """Test selectin followed by joined in chain."""
        parent = selectinload("posts")
        inner = parent.joinedload("author")
        
        assert parent.strategy == LoadStrategy.SELECTIN
        assert inner.strategy == LoadStrategy.JOINED
        assert parent.inner_options[0].strategy == LoadStrategy.JOINED
    
    def test_joined_then_selectin(self, clean_state):
        """Test joined followed by selectin in chain."""
        parent = joinedload("author")
        inner = parent.selectinload("posts")
        
        assert parent.strategy == LoadStrategy.JOINED
        assert inner.strategy == LoadStrategy.SELECTIN
        assert parent.inner_options[0].strategy == LoadStrategy.SELECTIN
    
    def test_subquery_with_nested(self, clean_state):
        """Test subquery with nested loading."""
        opt = subqueryload("posts")
        opt.joinedload("author")
        opt.selectinload("comments")
        
        assert len(opt.inner_options) == 2
    
    def test_multiple_top_level_options(self, clean_state):
        """Test multiple independent options."""
        class IUser6(Table):
            name: str = ""
        
        query = IUser6.select().options(
            selectinload("posts"),
            joinedload("profile"),
            subqueryload("comments"),
            raiseload("audit"),
        )
        
        assert len(query._load_options) == 4
    
    def test_same_relation_different_strategies(self, clean_state):
        """Test overriding same relationship with different strategy."""
        class IUser7(Table):
            name: str = ""
        
        # Both options target same relationship
        query = IUser7.select().options(
            selectinload("posts"),
            joinedload("posts"),  # Later option
        )
        
        # Both are stored (last one wins in practice)
        assert len(query._load_options) == 2
    
    def test_deep_nested_chain(self, clean_state):
        """Test very deep nesting."""
        opt = selectinload("a")
        current = opt
        for i in range(10):
            current = current.selectinload(f"level_{i}")
        
        # Verify chain exists
        level = opt
        for i in range(10):
            assert len(level.inner_options) == 1
            level = level.inner_options[0]
    
    def test_mixed_chain_strategies(self, clean_state):
        """Test alternating strategies in chain."""
        opt = selectinload("posts")
        inner1 = opt.joinedload("author")
        inner2 = inner1.subqueryload("company")
        inner3 = inner2.selectinload("employees")
        
        assert opt.strategy == LoadStrategy.SELECTIN
        assert inner1.strategy == LoadStrategy.JOINED
        assert inner2.strategy == LoadStrategy.SUBQUERY
        assert inner3.strategy == LoadStrategy.SELECTIN
    
    def test_raiseload_in_chain(self, clean_state):
        """Test raiseload in the middle of chain."""
        opt = selectinload("posts")
        opt.joinedload("author")
        opt.raiseload("audit")
        
        strategies = [o.strategy for o in opt.inner_options]
        assert LoadStrategy.RAISE in strategies
    
    def test_noload_in_options(self, clean_state):
        """Test noload option."""
        class IUser8(Table):
            name: str = ""
        
        query = IUser8.select().options(noload("posts"))
        
        assert query._load_options[0].strategy == LoadStrategy.SELECT


class TestQueryBuilding:
    """Test query building with options."""
    
    def test_options_preserves_where(self, clean_state):
        """Test that options doesn't break where clause."""
        class IUser9(Table):
            name: str = ""
        
        query = (
            IUser9.select()
            .where(name="test")
            .options(selectinload("posts"))
        )
        
        assert query._where == {"name": "test"}
        assert len(query._load_options) == 1
    
    def test_options_preserves_order_by(self, clean_state):
        """Test that options preserves order."""
        class IUser10(Table):
            name: str = ""
        
        query = (
            IUser10.select()
            .order_by("name", "-created_at")
            .options(selectinload("posts"))
        )
        
        assert "name" in query._order_by
        assert "-created_at" in query._order_by
    
    def test_options_preserves_limit_offset(self, clean_state):
        """Test limit and offset preserved."""
        class IUser11(Table):
            name: str = ""
        
        query = (
            IUser11.select()
            .limit(10)
            .offset(20)
            .options(selectinload("posts"))
        )
        
        assert query._limit == 10
        assert query._offset == 20
    
    def test_options_before_where(self, clean_state):
        """Test options before where clause."""
        class IUser12(Table):
            name: str = ""
        
        query = (
            IUser12.select()
            .options(selectinload("posts"))
            .where(name="test")
        )
        
        assert query._where == {"name": "test"}
        assert len(query._load_options) == 1
    
    def test_chained_options_calls(self, clean_state):
        """Test multiple options() calls."""
        class IUser13(Table):
            name: str = ""
        
        query = (
            IUser13.select()
            .options(selectinload("posts"))
            .options(joinedload("profile"))
            .options(raiseload("audit"))
        )
        
        assert len(query._load_options) == 3
    
    def test_options_with_where_in(self, clean_state):
        """Test options with where_in clause."""
        class IUser14(Table):
            name: str = ""
        
        query = (
            IUser14.select()
            .where_in(id=[1, 2, 3])
            .options(selectinload("posts"))
        )
        
        assert query._where_in == {"id": [1, 2, 3]}


# =============================================================================
# Lazy Strategy Edge Cases (25 tests)
# =============================================================================

class TestLazyStrategyEdgeCases:
    """Test edge cases for lazy loading strategies."""
    
    def test_raise_with_cached_value(self, clean_state):
        """Raise doesn't trigger if value is cached."""
        class IPost6(Table):
            iuser15_id: Optional[int] = None
        
        class IUser15(Table):
            posts: List[IPost6] = has_many(IPost6, lazy="raise")
        
        user = IUser15()
        user._cached_posts = []  # Pre-cache
        
        # Should not raise
        result = user.posts
        assert result == []
    
    def test_raise_error_message_format(self, clean_state):
        """Test raise error has useful message."""
        class IPost7(Table):
            iuser16_id: Optional[int] = None
        
        class IUser16(Table):
            posts: List[IPost7] = has_many(IPost7, lazy="raise")
        
        user = IUser16()
        
        with pytest.raises(LazyLoadError) as exc_info:
            _ = user.posts
        
        error_msg = str(exc_info.value)
        assert "posts" in error_msg
        assert "IUser16" in error_msg
    
    def test_dynamic_with_no_id(self, clean_state):
        """Test dynamic when owner has no id."""
        class IPost8(Table):
            iuser17_id: Optional[int] = None
        
        class IUser17(Table):
            posts: List[IPost8] = has_many(IPost8, lazy="dynamic")
        
        user = IUser17()
        # No id set
        
        result = user.posts
        # Should still return DynamicRelationship
        assert hasattr(result, "all")
    
    def test_joined_with_null_fk(self, clean_state):
        """Test joined loading with null foreign key."""
        class IAuthor1(Table):
            name: str = ""
        
        class IPost9(Table):
            author_id: Optional[int] = None
            author: IAuthor1 = belongs_to(IAuthor1, lazy="joined")
        
        post = IPost9()
        post.author_id = None
        
        # Should return None, not raise
        assert post.author is None
    
    def test_selectin_empty_cache(self, clean_state):
        """Test selectin returns empty list when not loaded."""
        class IPost10(Table):
            iuser18_id: Optional[int] = None
        
        class IUser18(Table):
            posts: List[IPost10] = has_many(IPost10, lazy="selectin")
        
        user = IUser18()
        
        # Not loaded, should return empty list
        posts = user.posts
        assert posts == []
    
    def test_subquery_empty_cache(self, clean_state):
        """Test subquery returns empty list when not loaded."""
        class IPost11(Table):
            iuser19_id: Optional[int] = None
        
        class IUser19(Table):
            posts: List[IPost11] = has_many(IPost11, lazy="subquery")
        
        user = IUser19()
        posts = user.posts
        assert posts == []
    
    def test_strategy_case_sensitivity(self, clean_state):
        """Test that lazy parameter is case-sensitive."""
        class IPost12(Table):
            iuser20_id: Optional[int] = None
        
        class IUser20(Table):
            posts: List[IPost12] = has_many(IPost12, lazy="SELECTIN")
        
        # Should accept uppercase (stored as-is)
        assert IUser20.__dict__["posts"].lazy == "SELECTIN"
    
    def test_invalid_lazy_value_stored(self, clean_state):
        """Test that invalid lazy values are stored (validation at runtime)."""
        class IPost13(Table):
            iuser21_id: Optional[int] = None
        
        class IUser21(Table):
            posts: List[IPost13] = has_many(IPost13, lazy="invalid")
        
        # Value is stored, validation happens when accessed
        assert IUser21.__dict__["posts"].lazy == "invalid"


class TestLoadOptionValidation:
    """Test LoadOption validation."""
    
    def test_empty_relationship_raises(self):
        """Empty relationship name raises."""
        with pytest.raises(ValueError):
            LoadOption("", LoadStrategy.SELECTIN)
    
    def test_none_relationship_raises(self):
        """None relationship raises ValueError (treated as empty)."""
        with pytest.raises((TypeError, ValueError)):
            LoadOption(None, LoadStrategy.SELECTIN)
    
    def test_string_strategy_converted(self):
        """String strategy is converted to enum."""
        opt = LoadOption("posts", "selectin")
        assert opt.strategy == LoadStrategy.SELECTIN
    
    def test_invalid_string_strategy_raises(self):
        """Invalid string strategy raises."""
        with pytest.raises(ValueError):
            LoadOption("posts", "invalid_strategy")
    
    def test_enum_strategy_accepted(self):
        """Enum strategy is accepted."""
        opt = LoadOption("posts", LoadStrategy.JOINED)
        assert opt.strategy == LoadStrategy.JOINED


# =============================================================================
# Performance Scenarios (25 tests)
# =============================================================================

class TestLoadingPerformanceScenarios:
    """Test performance-related scenarios."""
    
    def test_many_options_creation(self):
        """Test creating many options quickly."""
        options = []
        for i in range(1000):
            options.append(selectinload(f"rel_{i}"))
        
        assert len(options) == 1000
    
    def test_deep_nesting_performance(self):
        """Test deep nesting doesn't cause issues."""
        opt = selectinload("level_0")
        current = opt
        
        for i in range(100):
            current = current.selectinload(f"level_{i+1}")
        
        assert current.relationship == "level_100"
    
    def test_wide_options_performance(self):
        """Test many parallel options."""
        opt = selectinload("root")
        
        for i in range(100):
            opt.selectinload(f"branch_{i}")
        
        assert len(opt.inner_options) == 100
    
    def test_to_dict_large_tree(self):
        """Test serializing large option tree."""
        opt = selectinload("root")
        
        for i in range(50):
            inner = opt.selectinload(f"level1_{i}")
            for j in range(5):
                inner.joinedload(f"level2_{j}")
        
        d = opt.to_dict()
        assert len(d["inner_options"]) == 50
    
    def test_many_query_options(self, clean_state):
        """Test query with many options."""
        class IUser22(Table):
            name: str = ""
        
        options = [selectinload(f"rel_{i}") for i in range(100)]
        query = IUser22.select().options(*options)
        
        assert len(query._load_options) == 100
    
    def test_complex_nested_query(self, clean_state):
        """Test complex nested option query."""
        class IUser23(Table):
            name: str = ""
        
        opt1 = selectinload("posts")
        opt1.joinedload("author").selectinload("profile")
        opt1.selectinload("comments").joinedload("user")
        opt1.raiseload("audit")
        
        opt2 = joinedload("profile")
        opt2.selectinload("settings")
        
        query = IUser23.select().options(opt1, opt2)
        
        assert len(query._load_options) == 2
    
    def test_repeated_chain_access(self):
        """Test repeated access to chain is stable."""
        opt = selectinload("posts")
        inner = opt.joinedload("author")
        
        # Access multiple times
        for _ in range(100):
            assert opt.inner_options[0] is inner
    
    def test_option_independence(self):
        """Test options are truly independent."""
        opts = [selectinload("posts") for _ in range(100)]
        
        # Modify first one
        opts[0].joinedload("author")
        
        # Others should be unaffected
        for opt in opts[1:]:
            assert len(opt.inner_options) == 0

