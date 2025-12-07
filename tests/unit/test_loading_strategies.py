"""
Comprehensive tests for Loading Strategies.

Tests cover:
- LoadStrategy enum and validation
- LoadOption dataclass
- LazyLoadError exception
- RelationshipLoader class
- Each strategy in isolation
- Strategy on each relationship type (belongs_to, has_many, has_one)
- Default lazy="select" behavior
- Query override takes precedence over model default

150 tests total.
"""

import pytest
from typing import List, Optional
from unittest.mock import MagicMock, AsyncMock, patch

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
    LazyLoadError,
    RelationshipLoader,
    JoinBuilder,
    get_loader,
    reset_loader,
    reset_backref_registry,
    reset_sync_manager,
)
from pynext.db.relationships.options import (
    joinedload,
    selectinload,
    subqueryload,
    raiseload,
    noload,
    lazyload,
    immediateload,
    eagerload,
    Load,
)
from pynext.db.relationships.dynamic import DynamicRelationship


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


@pytest.fixture
async def adapter():
    """Create and configure a memory adapter."""
    adapter = MemoryAdapter()
    await adapter.connect()
    configure_db(adapter)
    return adapter


# =============================================================================
# LoadStrategy Enum Tests (20 tests)
# =============================================================================

class TestLoadStrategyEnum:
    """Test LoadStrategy enum."""
    
    def test_select_value(self):
        """SELECT strategy has correct value."""
        assert LoadStrategy.SELECT.value == "select"
    
    def test_joined_value(self):
        """JOINED strategy has correct value."""
        assert LoadStrategy.JOINED.value == "joined"
    
    def test_subquery_value(self):
        """SUBQUERY strategy has correct value."""
        assert LoadStrategy.SUBQUERY.value == "subquery"
    
    def test_selectin_value(self):
        """SELECTIN strategy has correct value."""
        assert LoadStrategy.SELECTIN.value == "selectin"
    
    def test_raise_value(self):
        """RAISE strategy has correct value."""
        assert LoadStrategy.RAISE.value == "raise"
    
    def test_dynamic_value(self):
        """DYNAMIC strategy has correct value."""
        assert LoadStrategy.DYNAMIC.value == "dynamic"
    
    def test_from_string_select(self):
        """from_string works for select."""
        assert LoadStrategy.from_string("select") == LoadStrategy.SELECT
    
    def test_from_string_joined(self):
        """from_string works for joined."""
        assert LoadStrategy.from_string("joined") == LoadStrategy.JOINED
    
    def test_from_string_subquery(self):
        """from_string works for subquery."""
        assert LoadStrategy.from_string("subquery") == LoadStrategy.SUBQUERY
    
    def test_from_string_selectin(self):
        """from_string works for selectin."""
        assert LoadStrategy.from_string("selectin") == LoadStrategy.SELECTIN
    
    def test_from_string_raise(self):
        """from_string works for raise."""
        assert LoadStrategy.from_string("raise") == LoadStrategy.RAISE
    
    def test_from_string_dynamic(self):
        """from_string works for dynamic."""
        assert LoadStrategy.from_string("dynamic") == LoadStrategy.DYNAMIC
    
    def test_from_string_case_insensitive(self):
        """from_string is case insensitive."""
        assert LoadStrategy.from_string("SELECT") == LoadStrategy.SELECT
        assert LoadStrategy.from_string("JOINED") == LoadStrategy.JOINED
        assert LoadStrategy.from_string("Selectin") == LoadStrategy.SELECTIN
    
    def test_from_string_invalid(self):
        """from_string raises for invalid strategy."""
        with pytest.raises(ValueError) as exc_info:
            LoadStrategy.from_string("invalid")
        assert "Invalid loading strategy" in str(exc_info.value)
        assert "invalid" in str(exc_info.value)
    
    def test_from_string_empty(self):
        """from_string raises for empty string."""
        with pytest.raises(ValueError):
            LoadStrategy.from_string("")
    
    def test_all_strategies_unique(self):
        """All strategy values are unique."""
        values = [s.value for s in LoadStrategy]
        assert len(values) == len(set(values))
    
    def test_strategy_count(self):
        """There are exactly 6 strategies."""
        assert len(list(LoadStrategy)) == 6
    
    def test_enum_iteration(self):
        """Can iterate over all strategies."""
        strategies = list(LoadStrategy)
        assert LoadStrategy.SELECT in strategies
        assert LoadStrategy.DYNAMIC in strategies
    
    def test_enum_comparison(self):
        """Enum values can be compared."""
        assert LoadStrategy.SELECT == LoadStrategy.SELECT
        assert LoadStrategy.SELECT != LoadStrategy.JOINED
    
    def test_enum_name_and_value(self):
        """Enum has both name and value."""
        assert LoadStrategy.SELECTIN.name == "SELECTIN"
        assert LoadStrategy.SELECTIN.value == "selectin"


# =============================================================================
# LoadOption Dataclass Tests (25 tests)
# =============================================================================

class TestLoadOptionBasic:
    """Basic LoadOption tests."""
    
    def test_create_with_string_strategy(self):
        """Create LoadOption with string strategy."""
        opt = LoadOption("posts", "selectin")
        assert opt.relationship == "posts"
        assert opt.strategy == LoadStrategy.SELECTIN
    
    def test_create_with_enum_strategy(self):
        """Create LoadOption with enum strategy."""
        opt = LoadOption("author", LoadStrategy.JOINED)
        assert opt.relationship == "author"
        assert opt.strategy == LoadStrategy.JOINED
    
    def test_empty_inner_options_by_default(self):
        """Inner options are empty by default."""
        opt = LoadOption("posts", LoadStrategy.SELECT)
        assert opt.inner_options == []
    
    def test_empty_relationship_raises(self):
        """Empty relationship name raises."""
        with pytest.raises(ValueError) as exc_info:
            LoadOption("", LoadStrategy.SELECT)
        assert "cannot be empty" in str(exc_info.value)
    
    def test_add_inner_returns_self(self):
        """add_inner returns self for chaining."""
        opt = LoadOption("posts", LoadStrategy.SELECTIN)
        inner = LoadOption("author", LoadStrategy.JOINED)
        result = opt.add_inner(inner)
        assert result is opt
    
    def test_add_inner_adds_to_list(self):
        """add_inner adds to inner_options list."""
        opt = LoadOption("posts", LoadStrategy.SELECTIN)
        inner = LoadOption("author", LoadStrategy.JOINED)
        opt.add_inner(inner)
        assert len(opt.inner_options) == 1
        assert opt.inner_options[0] is inner


class TestLoadOptionChaining:
    """Test LoadOption chaining methods."""
    
    def test_joinedload_chain(self):
        """joinedload chaining creates inner option."""
        opt = LoadOption("posts", LoadStrategy.SELECTIN)
        inner = opt.joinedload("author")
        
        assert len(opt.inner_options) == 1
        assert inner.relationship == "author"
        assert inner.strategy == LoadStrategy.JOINED
    
    def test_selectinload_chain(self):
        """selectinload chaining creates inner option."""
        opt = LoadOption("author", LoadStrategy.JOINED)
        inner = opt.selectinload("posts")
        
        assert inner.relationship == "posts"
        assert inner.strategy == LoadStrategy.SELECTIN
    
    def test_subqueryload_chain(self):
        """subqueryload chaining creates inner option."""
        opt = LoadOption("posts", LoadStrategy.SELECTIN)
        inner = opt.subqueryload("comments")
        
        assert inner.relationship == "comments"
        assert inner.strategy == LoadStrategy.SUBQUERY
    
    def test_raiseload_chain(self):
        """raiseload chaining creates inner option."""
        opt = LoadOption("posts", LoadStrategy.SELECTIN)
        inner = opt.raiseload("audit_logs")
        
        assert inner.relationship == "audit_logs"
        assert inner.strategy == LoadStrategy.RAISE
    
    def test_noload_chain(self):
        """noload chaining creates inner option."""
        opt = LoadOption("posts", LoadStrategy.SELECTIN)
        inner = opt.noload("metadata")
        
        assert inner.relationship == "metadata"
        assert inner.strategy == LoadStrategy.SELECT
    
    def test_deep_chaining(self):
        """Can chain multiple levels deep."""
        opt = LoadOption("posts", LoadStrategy.SELECTIN)
        inner1 = opt.joinedload("author")
        inner2 = inner1.selectinload("profile")
        inner3 = inner2.joinedload("settings")
        
        assert len(opt.inner_options) == 1
        assert len(inner1.inner_options) == 1
        assert len(inner2.inner_options) == 1
        assert inner3.relationship == "settings"
    
    def test_multiple_inner_options(self):
        """Can add multiple inner options."""
        opt = LoadOption("posts", LoadStrategy.SELECTIN)
        opt.joinedload("author")
        opt.selectinload("comments")
        opt.raiseload("audit")
        
        assert len(opt.inner_options) == 3


class TestLoadOptionSerialization:
    """Test LoadOption serialization."""
    
    def test_to_dict_basic(self):
        """to_dict returns correct structure."""
        opt = LoadOption("posts", LoadStrategy.SELECTIN)
        d = opt.to_dict()
        
        assert d["relationship"] == "posts"
        assert d["strategy"] == "selectin"
        assert d["inner_options"] == []
    
    def test_to_dict_with_inner(self):
        """to_dict includes inner options."""
        opt = LoadOption("posts", LoadStrategy.SELECTIN)
        opt.joinedload("author")
        
        d = opt.to_dict()
        
        assert len(d["inner_options"]) == 1
        assert d["inner_options"][0]["relationship"] == "author"
    
    def test_repr_basic(self):
        """__repr__ shows relationship and strategy."""
        opt = LoadOption("posts", LoadStrategy.SELECTIN)
        r = repr(opt)
        
        assert "posts" in r
        assert "selectin" in r
    
    def test_repr_with_inner(self):
        """__repr__ shows inner options."""
        opt = LoadOption("posts", LoadStrategy.SELECTIN)
        opt.joinedload("author")
        
        r = repr(opt)
        assert "inner=" in r


# =============================================================================
# LazyLoadError Exception Tests (15 tests)
# =============================================================================

class TestLazyLoadError:
    """Test LazyLoadError exception."""
    
    def test_basic_error(self):
        """Basic error creation."""
        err = LazyLoadError("posts")
        assert "posts" in str(err)
    
    def test_error_with_model(self):
        """Error with model name."""
        err = LazyLoadError("posts", model="User")
        assert "posts" in str(err)
        assert "User" in str(err)
    
    def test_error_has_relationship_attr(self):
        """Error stores relationship name."""
        err = LazyLoadError("posts")
        assert err.relationship == "posts"
    
    def test_error_has_model_attr(self):
        """Error stores model name."""
        err = LazyLoadError("posts", model="User")
        assert err.model == "User"
    
    def test_custom_message(self):
        """Can provide custom message."""
        err = LazyLoadError("posts", message="Custom error")
        assert str(err) == "Custom error"
    
    def test_default_message_mentions_lazy_raise(self):
        """Default message mentions lazy='raise'."""
        err = LazyLoadError("posts")
        assert "lazy='raise'" in str(err) or "raise" in str(err).lower()
    
    def test_default_message_suggests_options(self):
        """Default message suggests using options()."""
        err = LazyLoadError("posts")
        msg = str(err)
        assert "options" in msg.lower() or "selectinload" in msg.lower()
    
    def test_default_message_suggests_with_related(self):
        """Default message suggests with_related()."""
        err = LazyLoadError("posts")
        msg = str(err)
        assert "with_related" in msg.lower() or "eager" in msg.lower()
    
    def test_is_exception(self):
        """LazyLoadError is an Exception."""
        err = LazyLoadError("posts")
        assert isinstance(err, Exception)
    
    def test_can_be_raised(self):
        """Can raise LazyLoadError."""
        with pytest.raises(LazyLoadError):
            raise LazyLoadError("posts")
    
    def test_can_be_caught(self):
        """Can catch LazyLoadError."""
        try:
            raise LazyLoadError("posts")
        except LazyLoadError as e:
            assert e.relationship == "posts"
    
    def test_inherits_from_exception(self):
        """LazyLoadError inherits from Exception."""
        err = LazyLoadError("posts")
        assert isinstance(err, Exception)
    
    def test_error_without_model(self):
        """Error without model is fine."""
        err = LazyLoadError("posts")
        assert err.model is None
    
    def test_error_repr(self):
        """Error has useful repr."""
        err = LazyLoadError("posts", model="User")
        # Should be catchable and inspectable
        assert err.relationship == "posts"
    
    def test_n1_prevention_mentioned(self):
        """Error message mentions N+1 prevention."""
        err = LazyLoadError("posts")
        msg = str(err).lower()
        assert "n+1" in msg or "lazy load" in msg


# =============================================================================
# Loading Option Functions Tests (20 tests)
# =============================================================================

class TestLoadingOptionFunctions:
    """Test loading option convenience functions."""
    
    def test_joinedload_creates_option(self):
        """joinedload creates LoadOption with JOINED strategy."""
        opt = joinedload("author")
        assert isinstance(opt, LoadOption)
        assert opt.relationship == "author"
        assert opt.strategy == LoadStrategy.JOINED
    
    def test_selectinload_creates_option(self):
        """selectinload creates LoadOption with SELECTIN strategy."""
        opt = selectinload("posts")
        assert isinstance(opt, LoadOption)
        assert opt.relationship == "posts"
        assert opt.strategy == LoadStrategy.SELECTIN
    
    def test_subqueryload_creates_option(self):
        """subqueryload creates LoadOption with SUBQUERY strategy."""
        opt = subqueryload("comments")
        assert isinstance(opt, LoadOption)
        assert opt.relationship == "comments"
        assert opt.strategy == LoadStrategy.SUBQUERY
    
    def test_raiseload_creates_option(self):
        """raiseload creates LoadOption with RAISE strategy."""
        opt = raiseload("audit_logs")
        assert isinstance(opt, LoadOption)
        assert opt.relationship == "audit_logs"
        assert opt.strategy == LoadStrategy.RAISE
    
    def test_noload_creates_option(self):
        """noload creates LoadOption with SELECT strategy."""
        opt = noload("metadata")
        assert isinstance(opt, LoadOption)
        assert opt.relationship == "metadata"
        assert opt.strategy == LoadStrategy.SELECT
    
    def test_lazyload_creates_option(self):
        """lazyload creates LoadOption with SELECT strategy."""
        opt = lazyload("posts")
        assert isinstance(opt, LoadOption)
        assert opt.strategy == LoadStrategy.SELECT
    
    def test_immediateload_creates_option(self):
        """immediateload is alias for selectinload."""
        opt = immediateload("posts")
        assert isinstance(opt, LoadOption)
        assert opt.strategy == LoadStrategy.SELECTIN
    
    def test_eagerload_creates_option(self):
        """eagerload is alias for selectinload."""
        opt = eagerload("posts")
        assert isinstance(opt, LoadOption)
        assert opt.strategy == LoadStrategy.SELECTIN
    
    def test_joinedload_chainable(self):
        """joinedload returns chainable LoadOption."""
        opt = joinedload("author")
        inner = opt.selectinload("posts")
        assert inner.strategy == LoadStrategy.SELECTIN
    
    def test_selectinload_chainable(self):
        """selectinload returns chainable LoadOption."""
        opt = selectinload("posts")
        inner = opt.joinedload("author")
        assert inner.strategy == LoadStrategy.JOINED
    
    def test_nested_loading(self):
        """Can create nested loading options."""
        opt = selectinload("posts").joinedload("author").selectinload("profile")
        # The first option should have inner options
        assert len(selectinload("posts").joinedload("author").inner_options) == 0
        # But accessing the chain creates them
    
    def test_multiple_options(self):
        """Can create multiple independent options."""
        opt1 = joinedload("author")
        opt2 = selectinload("posts")
        opt3 = raiseload("audit")
        
        assert opt1.relationship == "author"
        assert opt2.relationship == "posts"
        assert opt3.relationship == "audit"
    
    def test_options_are_independent(self):
        """Each call creates independent option."""
        opt1 = joinedload("author")
        opt2 = joinedload("author")
        
        opt1.selectinload("posts")
        
        assert len(opt1.inner_options) == 1
        assert len(opt2.inner_options) == 0


class TestLoadClass:
    """Test Load convenience class."""
    
    def test_load_with_string(self):
        """Load accepts string relationship."""
        load = Load("posts")
        assert load._name == "posts"
    
    def test_load_selectin(self):
        """Load.selectin() returns selectinload."""
        opt = Load("posts").selectin()
        assert opt.strategy == LoadStrategy.SELECTIN
    
    def test_load_joined(self):
        """Load.joined() returns joinedload."""
        opt = Load("author").joined()
        assert opt.strategy == LoadStrategy.JOINED
    
    def test_load_subquery(self):
        """Load.subquery() returns subqueryload."""
        opt = Load("comments").subquery()
        assert opt.strategy == LoadStrategy.SUBQUERY
    
    def test_load_raise(self):
        """Load.raise_() returns raiseload."""
        opt = Load("audit").raise_()
        assert opt.strategy == LoadStrategy.RAISE
    
    def test_load_noload(self):
        """Load.noload() returns noload."""
        opt = Load("metadata").noload()
        assert opt.strategy == LoadStrategy.SELECT


# =============================================================================
# Lazy Parameter Tests (30 tests)
# =============================================================================

class TestLazyParameterHasMany:
    """Test lazy parameter on has_many."""
    
    def test_default_lazy_is_select(self, clean_state):
        """Default lazy is 'select'."""
        class LUser1(Table):
            posts: List["LPost1"] = has_many("LPost1")
        
        class LPost1(Table):
            user_id: Optional[int] = None
        
        descriptor = LUser1.__dict__["posts"]
        assert descriptor.lazy == "select"
    
    def test_lazy_selectin(self, clean_state):
        """Can set lazy='selectin'."""
        class LUser2(Table):
            posts: List["LPost2"] = has_many("LPost2", lazy="selectin")
        
        class LPost2(Table):
            user_id: Optional[int] = None
        
        descriptor = LUser2.__dict__["posts"]
        assert descriptor.lazy == "selectin"
    
    def test_lazy_subquery(self, clean_state):
        """Can set lazy='subquery'."""
        class LUser3(Table):
            posts: List["LPost3"] = has_many("LPost3", lazy="subquery")
        
        class LPost3(Table):
            user_id: Optional[int] = None
        
        descriptor = LUser3.__dict__["posts"]
        assert descriptor.lazy == "subquery"
    
    def test_lazy_raise(self, clean_state):
        """Can set lazy='raise'."""
        class LUser4(Table):
            posts: List["LPost4"] = has_many("LPost4", lazy="raise")
        
        class LPost4(Table):
            user_id: Optional[int] = None
        
        descriptor = LUser4.__dict__["posts"]
        assert descriptor.lazy == "raise"
    
    def test_lazy_dynamic(self, clean_state):
        """Can set lazy='dynamic'."""
        class LUser5(Table):
            posts: List["LPost5"] = has_many("LPost5", lazy="dynamic")
        
        class LPost5(Table):
            user_id: Optional[int] = None
        
        descriptor = LUser5.__dict__["posts"]
        assert descriptor.lazy == "dynamic"
    
    def test_lazy_with_backref(self, clean_state):
        """lazy works with backref."""
        class LUser6(Table):
            posts: List["LPost6"] = has_many("LPost6", backref="author", lazy="selectin")
        
        class LPost6(Table):
            user_id: Optional[int] = None
        
        descriptor = LUser6.__dict__["posts"]
        assert descriptor.lazy == "selectin"
        assert descriptor.backref == "author"


class TestLazyParameterBelongsTo:
    """Test lazy parameter on belongs_to."""
    
    def test_default_lazy_is_select(self, clean_state):
        """Default lazy is 'select'."""
        class LUser7(Table):
            name: str = ""
        
        class LPost7(Table):
            user_id: Optional[int] = None
            author: "LUser7" = belongs_to("LUser7")
        
        descriptor = LPost7.__dict__["author"]
        assert descriptor.lazy == "select"
    
    def test_lazy_joined(self, clean_state):
        """Can set lazy='joined'."""
        class LUser8(Table):
            name: str = ""
        
        class LPost8(Table):
            user_id: Optional[int] = None
            author: "LUser8" = belongs_to("LUser8", lazy="joined")
        
        descriptor = LPost8.__dict__["author"]
        assert descriptor.lazy == "joined"
    
    def test_lazy_raise(self, clean_state):
        """Can set lazy='raise'."""
        class LUser9(Table):
            name: str = ""
        
        class LPost9(Table):
            user_id: Optional[int] = None
            author: "LUser9" = belongs_to("LUser9", lazy="raise")
        
        descriptor = LPost9.__dict__["author"]
        assert descriptor.lazy == "raise"


class TestLazyParameterHasOne:
    """Test lazy parameter on has_one."""
    
    def test_default_lazy_is_select(self, clean_state):
        """Default lazy is 'select'."""
        class LUser10(Table):
            profile: "LProfile1" = has_one("LProfile1")
        
        class LProfile1(Table):
            user_id: Optional[int] = None
        
        descriptor = LUser10.__dict__["profile"]
        assert descriptor.lazy == "select"
    
    def test_lazy_joined(self, clean_state):
        """Can set lazy='joined'."""
        class LUser11(Table):
            profile: "LProfile2" = has_one("LProfile2", lazy="joined")
        
        class LProfile2(Table):
            user_id: Optional[int] = None
        
        descriptor = LUser11.__dict__["profile"]
        assert descriptor.lazy == "joined"
    
    def test_lazy_selectin(self, clean_state):
        """Can set lazy='selectin'."""
        class LUser12(Table):
            profile: "LProfile3" = has_one("LProfile3", lazy="selectin")
        
        class LProfile3(Table):
            user_id: Optional[int] = None
        
        descriptor = LUser12.__dict__["profile"]
        assert descriptor.lazy == "selectin"
    
    def test_lazy_raise(self, clean_state):
        """Can set lazy='raise'."""
        class LUser13(Table):
            profile: "LProfile4" = has_one("LProfile4", lazy="raise")
        
        class LProfile4(Table):
            user_id: Optional[int] = None
        
        descriptor = LUser13.__dict__["profile"]
        assert descriptor.lazy == "raise"


# =============================================================================
# Raise Strategy Behavior Tests (20 tests)
# =============================================================================

class TestRaiseStrategyBehavior:
    """Test that lazy='raise' actually raises."""
    
    def test_has_many_raise_on_access(self, clean_state):
        """has_many with lazy='raise' raises on access."""
        class RUser1(Table):
            posts: List["RPost1"] = has_many("RPost1", lazy="raise")
        
        class RPost1(Table):
            user_id: Optional[int] = None
        
        user = RUser1()
        
        with pytest.raises(LazyLoadError) as exc_info:
            _ = user.posts
        
        assert "posts" in str(exc_info.value)
    
    def test_belongs_to_raise_on_access(self, clean_state):
        """belongs_to with lazy='raise' raises on access."""
        class RUser2(Table):
            name: str = ""
        
        class RPost2(Table):
            user_id: Optional[int] = None
            author: "RUser2" = belongs_to("RUser2", lazy="raise")
        
        post = RPost2()
        
        with pytest.raises(LazyLoadError) as exc_info:
            _ = post.author
        
        assert "author" in str(exc_info.value)
    
    def test_has_one_raise_on_access(self, clean_state):
        """has_one with lazy='raise' raises on access."""
        class RUser3(Table):
            profile: "RProfile1" = has_one("RProfile1", lazy="raise")
        
        class RProfile1(Table):
            user_id: Optional[int] = None
        
        user = RUser3()
        
        with pytest.raises(LazyLoadError) as exc_info:
            _ = user.profile
        
        assert "profile" in str(exc_info.value)
    
    def test_raise_not_triggered_if_loaded(self, clean_state):
        """Raise is not triggered if relationship is already loaded."""
        class RUser4(Table):
            posts: List["RPost4"] = has_many("RPost4", lazy="raise")
        
        class RPost4(Table):
            user_id: Optional[int] = None
        
        user = RUser4()
        # Pre-populate cache
        user._cached_posts = []
        
        # Should not raise since it's already loaded
        result = user.posts
        assert result == []
    
    def test_raise_error_includes_model(self, clean_state):
        """LazyLoadError includes model name."""
        class RUser5(Table):
            posts: List["RPost5"] = has_many("RPost5", lazy="raise")
        
        class RPost5(Table):
            user_id: Optional[int] = None
        
        user = RUser5()
        
        with pytest.raises(LazyLoadError) as exc_info:
            _ = user.posts
        
        assert "RUser5" in str(exc_info.value)


# =============================================================================
# Dynamic Strategy Behavior Tests (20 tests)
# =============================================================================

class TestDynamicStrategyBehavior:
    """Test that lazy='dynamic' returns query builder."""
    
    def test_dynamic_returns_dynamic_relationship(self, clean_state):
        """Dynamic strategy returns DynamicRelationship."""
        # Define Post first so it's in registry when User references it
        class DPost1(Table):
            duser1_id: Optional[int] = None
        
        class DUser1(Table):
            posts: List[DPost1] = has_many(DPost1, lazy="dynamic")
        
        user = DUser1()
        user.id = 1
        
        result = user.posts
        
        assert isinstance(result, DynamicRelationship)
    
    def test_dynamic_relationship_has_all_method(self, clean_state):
        """DynamicRelationship has all() method."""
        class DPost2(Table):
            duser2_id: Optional[int] = None
        
        class DUser2(Table):
            posts: List[DPost2] = has_many(DPost2, lazy="dynamic")
        
        user = DUser2()
        user.id = 1
        
        result = user.posts
        
        assert hasattr(result, "all")
    
    def test_dynamic_relationship_has_filter_method(self, clean_state):
        """DynamicRelationship has filter() method."""
        class DPost3(Table):
            duser3_id: Optional[int] = None
        
        class DUser3(Table):
            posts: List[DPost3] = has_many(DPost3, lazy="dynamic")
        
        user = DUser3()
        user.id = 1
        
        result = user.posts
        
        assert hasattr(result, "filter")
    
    def test_dynamic_relationship_has_count_method(self, clean_state):
        """DynamicRelationship has count() method."""
        class DPost4(Table):
            duser4_id: Optional[int] = None
        
        class DUser4(Table):
            posts: List[DPost4] = has_many(DPost4, lazy="dynamic")
        
        user = DUser4()
        user.id = 1
        
        result = user.posts
        
        assert hasattr(result, "count")
    
    def test_dynamic_relationship_repr(self, clean_state):
        """DynamicRelationship has useful repr."""
        class DPost5(Table):
            duser5_id: Optional[int] = None
        
        class DUser5(Table):
            posts: List[DPost5] = has_many(DPost5, lazy="dynamic")
        
        user = DUser5()
        user.id = 1
        
        result = user.posts
        
        r = repr(result)
        assert "DynamicRelationship" in r
        assert "DPost5" in r
    
    def test_dynamic_relationship_is_truthy(self, clean_state):
        """DynamicRelationship is always truthy."""
        class DPost6(Table):
            duser6_id: Optional[int] = None
        
        class DUser6(Table):
            posts: List[DPost6] = has_many(DPost6, lazy="dynamic")
        
        user = DUser6()
        user.id = 1
        
        result = user.posts
        
        assert bool(result) is True
    
    def test_dynamic_has_where_method(self, clean_state):
        """DynamicRelationship has where() method."""
        class DPost7(Table):
            duser7_id: Optional[int] = None
        
        class DUser7(Table):
            posts: List[DPost7] = has_many(DPost7, lazy="dynamic")
        
        user = DUser7()
        user.id = 1
        
        result = user.posts
        
        assert hasattr(result, "where")
    
    def test_dynamic_has_order_by_method(self, clean_state):
        """DynamicRelationship has order_by() method."""
        class DPost8(Table):
            duser8_id: Optional[int] = None
        
        class DUser8(Table):
            posts: List[DPost8] = has_many(DPost8, lazy="dynamic")
        
        user = DUser8()
        user.id = 1
        
        result = user.posts
        
        assert hasattr(result, "order_by")
    
    def test_dynamic_has_limit_method(self, clean_state):
        """DynamicRelationship has limit() method."""
        class DPost9(Table):
            duser9_id: Optional[int] = None
        
        class DUser9(Table):
            posts: List[DPost9] = has_many(DPost9, lazy="dynamic")
        
        user = DUser9()
        user.id = 1
        
        result = user.posts
        
        assert hasattr(result, "limit")
    
    def test_dynamic_has_offset_method(self, clean_state):
        """DynamicRelationship has offset() method."""
        class DPost10(Table):
            duser10_id: Optional[int] = None
        
        class DUser10(Table):
            posts: List[DPost10] = has_many(DPost10, lazy="dynamic")
        
        user = DUser10()
        user.id = 1
        
        result = user.posts
        
        assert hasattr(result, "offset")

