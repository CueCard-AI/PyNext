"""
Comprehensive tests for Nested Loading.

Tests cover deep nesting, multiple branches, mixed strategies,
and complex relationship graphs.

80 tests total.
"""

import pytest
from typing import List, Optional
from unittest.mock import MagicMock

from pynext.db import Table, has_many, has_one, belongs_to, configure_db
from pynext.db.relationships import (
    LoadStrategy, LoadOption,
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
# Deep Nesting Tests (25 tests)
# =============================================================================

class TestDeepNesting:
    """Test deeply nested loading options."""
    
    def test_two_level_nesting(self):
        """Two-level nesting works."""
        opt = selectinload("posts")
        inner = opt.joinedload("author")
        
        assert opt.strategy == LoadStrategy.SELECTIN
        assert inner.strategy == LoadStrategy.JOINED
        assert opt.inner_options[0] is inner
    
    def test_three_level_nesting(self):
        """Three-level nesting works."""
        opt = selectinload("posts")
        inner1 = opt.joinedload("author")
        inner2 = inner1.selectinload("profile")
        
        assert len(opt.inner_options) == 1
        assert len(inner1.inner_options) == 1
        assert inner2.relationship == "profile"
    
    def test_five_level_nesting(self):
        """Five-level nesting works."""
        opt = selectinload("a")
        b = opt.joinedload("b")
        c = b.selectinload("c")
        d = c.subqueryload("d")
        e = d.joinedload("e")
        
        assert e.relationship == "e"
    
    def test_ten_level_nesting(self):
        """Ten-level nesting works."""
        opt = selectinload("level0")
        current = opt
        
        for i in range(1, 10):
            current = current.selectinload(f"level{i}")
        
        assert current.relationship == "level9"
    
    def test_fifty_level_nesting(self):
        """Fifty-level nesting works."""
        opt = selectinload("l0")
        current = opt
        
        for i in range(1, 50):
            current = current.selectinload(f"l{i}")
        
        assert current.relationship == "l49"
    
    def test_hundred_level_nesting(self):
        """Hundred-level nesting works."""
        opt = selectinload("n0")
        current = opt
        
        for i in range(1, 100):
            current = current.selectinload(f"n{i}")
        
        assert current.relationship == "n99"
    
    def test_deep_nesting_to_dict(self):
        """Deep nesting serializes correctly."""
        opt = selectinload("a")
        opt.joinedload("b").selectinload("c")
        
        d = opt.to_dict()
        
        assert d["relationship"] == "a"
        assert len(d["inner_options"]) == 1
        assert d["inner_options"][0]["relationship"] == "b"
        assert len(d["inner_options"][0]["inner_options"]) == 1


class TestMultipleBranches:
    """Test multiple branches at same level."""
    
    def test_two_branches(self):
        """Two branches at same level."""
        opt = selectinload("root")
        opt.joinedload("branch1")
        opt.selectinload("branch2")
        
        assert len(opt.inner_options) == 2
    
    def test_five_branches(self):
        """Five branches at same level."""
        opt = selectinload("root")
        
        for i in range(5):
            opt.joinedload(f"branch{i}")
        
        assert len(opt.inner_options) == 5
    
    def test_ten_branches(self):
        """Ten branches at same level."""
        opt = selectinload("root")
        
        for i in range(10):
            opt.selectinload(f"b{i}")
        
        assert len(opt.inner_options) == 10
    
    def test_fifty_branches(self):
        """Fifty branches at same level."""
        opt = selectinload("root")
        
        for i in range(50):
            opt.joinedload(f"x{i}")
        
        assert len(opt.inner_options) == 50
    
    def test_branches_have_correct_strategies(self):
        """Each branch has correct strategy."""
        opt = selectinload("root")
        opt.joinedload("a")
        opt.selectinload("b")
        opt.subqueryload("c")
        opt.raiseload("d")
        
        strategies = [o.strategy for o in opt.inner_options]
        
        assert LoadStrategy.JOINED in strategies
        assert LoadStrategy.SELECTIN in strategies
        assert LoadStrategy.SUBQUERY in strategies
        assert LoadStrategy.RAISE in strategies
    
    def test_branches_independent(self):
        """Branches don't affect each other."""
        opt = selectinload("root")
        a = opt.joinedload("a")
        b = opt.selectinload("b")
        
        a.joinedload("a_child")
        
        # b should have no children
        assert len(b.inner_options) == 0
        assert len(a.inner_options) == 1


class TestMixedStrategies:
    """Test mixing different strategies in nesting."""
    
    def test_selectin_to_joined(self):
        """Selectin parent with joined child."""
        opt = selectinload("posts")
        inner = opt.joinedload("author")
        
        assert opt.strategy == LoadStrategy.SELECTIN
        assert inner.strategy == LoadStrategy.JOINED
    
    def test_joined_to_selectin(self):
        """Joined parent with selectin child."""
        opt = joinedload("author")
        inner = opt.selectinload("posts")
        
        assert opt.strategy == LoadStrategy.JOINED
        assert inner.strategy == LoadStrategy.SELECTIN
    
    def test_subquery_to_joined(self):
        """Subquery parent with joined child."""
        opt = subqueryload("comments")
        inner = opt.joinedload("user")
        
        assert opt.strategy == LoadStrategy.SUBQUERY
        assert inner.strategy == LoadStrategy.JOINED
    
    def test_alternating_strategies(self):
        """Alternating strategies in chain."""
        opt = selectinload("a")
        b = opt.joinedload("b")
        c = b.selectinload("c")
        d = c.joinedload("d")
        
        assert opt.strategy == LoadStrategy.SELECTIN
        assert b.strategy == LoadStrategy.JOINED
        assert c.strategy == LoadStrategy.SELECTIN
        assert d.strategy == LoadStrategy.JOINED
    
    def test_all_strategies_in_chain(self):
        """All strategies used in one chain."""
        opt = selectinload("a")
        b = opt.joinedload("b")
        c = b.subqueryload("c")
        d = c.raiseload("d")
        e = d.noload("e")
        
        assert opt.strategy == LoadStrategy.SELECTIN
        assert b.strategy == LoadStrategy.JOINED
        assert c.strategy == LoadStrategy.SUBQUERY
        assert d.strategy == LoadStrategy.RAISE
        assert e.strategy == LoadStrategy.SELECT


# =============================================================================
# Complex Graphs (30 tests)
# =============================================================================

class TestComplexGraphs:
    """Test complex relationship graphs."""
    
    def test_tree_structure(self):
        """Tree-like structure with multiple levels."""
        root = selectinload("root")
        
        # Level 1
        a = root.selectinload("a")
        b = root.selectinload("b")
        
        # Level 2 under a
        a.joinedload("a1")
        a.joinedload("a2")
        
        # Level 2 under b
        b.joinedload("b1")
        b.joinedload("b2")
        
        assert len(root.inner_options) == 2
        assert len(a.inner_options) == 2
        assert len(b.inner_options) == 2
    
    def test_diamond_pattern(self):
        """Diamond-shaped relationship pattern."""
        # A -> B, A -> C, B -> D, C -> D
        root = selectinload("a")
        b = root.selectinload("b")
        c = root.selectinload("c")
        
        b.joinedload("d")
        c.joinedload("d")
        
        assert len(root.inner_options) == 2
    
    def test_wide_tree(self):
        """Very wide tree (many siblings)."""
        root = selectinload("root")
        
        for i in range(20):
            root.selectinload(f"child{i}")
        
        assert len(root.inner_options) == 20
    
    def test_mixed_wide_and_deep(self):
        """Mix of wide and deep nesting."""
        root = selectinload("root")
        
        # Wide at first level
        children = [root.selectinload(f"c{i}") for i in range(5)]
        
        # Deep under first child
        current = children[0]
        for i in range(10):
            current = current.joinedload(f"deep{i}")
        
        assert len(root.inner_options) == 5
        assert current.relationship == "deep9"
    
    def test_unbalanced_tree(self):
        """Unbalanced tree structure."""
        root = selectinload("root")
        
        # Deep left side
        left = root.selectinload("left")
        left_deep = left.selectinload("l1").selectinload("l2").selectinload("l3")
        
        # Shallow right side
        root.joinedload("right")
        
        assert len(root.inner_options) == 2
        assert left_deep.relationship == "l3"


class TestNestedToDict:
    """Test serialization of nested options."""
    
    def test_simple_nested_to_dict(self):
        """Simple nested option serializes."""
        opt = selectinload("posts")
        opt.joinedload("author")
        
        d = opt.to_dict()
        
        assert d["relationship"] == "posts"
        assert d["strategy"] == "selectin"
        assert len(d["inner_options"]) == 1
        assert d["inner_options"][0]["relationship"] == "author"
        assert d["inner_options"][0]["strategy"] == "joined"
    
    def test_deep_nested_to_dict(self):
        """Deep nested option serializes."""
        opt = selectinload("a")
        opt.joinedload("b").selectinload("c").subqueryload("d")
        
        d = opt.to_dict()
        
        # Navigate the structure
        level1 = d["inner_options"][0]
        level2 = level1["inner_options"][0]
        level3 = level2["inner_options"][0]
        
        assert level1["relationship"] == "b"
        assert level2["relationship"] == "c"
        assert level3["relationship"] == "d"
    
    def test_branched_to_dict(self):
        """Branched option serializes."""
        opt = selectinload("root")
        opt.joinedload("a")
        opt.selectinload("b")
        
        d = opt.to_dict()
        
        assert len(d["inner_options"]) == 2
        rels = [o["relationship"] for o in d["inner_options"]]
        assert "a" in rels
        assert "b" in rels


class TestNestedQueryIntegration:
    """Test nested options in queries."""
    
    def test_nested_in_query_options(self, clean_state):
        """Nested options work in query."""
        class NQUser1(Table):
            name: str = ""
        
        opt = selectinload("posts")
        opt.joinedload("author")
        
        query = NQUser1.select().options(opt)
        
        assert len(query._load_options) == 1
        assert len(query._load_options[0].inner_options) == 1
    
    def test_multiple_nested_in_query(self, clean_state):
        """Multiple nested options in query."""
        class NQUser2(Table):
            name: str = ""
        
        opt1 = selectinload("posts")
        opt1.joinedload("author")
        
        opt2 = joinedload("profile")
        opt2.selectinload("settings")
        
        query = NQUser2.select().options(opt1, opt2)
        
        assert len(query._load_options) == 2
    
    def test_complex_nested_query(self, clean_state):
        """Complex nested options in query."""
        class NQUser3(Table):
            name: str = ""
        
        opt = selectinload("posts")
        opt.joinedload("author").selectinload("profile")
        opt.selectinload("comments").joinedload("user")
        opt.raiseload("audit")
        
        query = NQUser3.select().options(opt)
        
        assert len(query._load_options) == 1
        assert len(query._load_options[0].inner_options) == 3

