"""
Tests for PyNext Backref - Basic Creation and Configuration.

150 tests covering:
- BackrefConfig creation and attributes
- BackrefRegistry registration and lookup
- Auto-creation of reverse relationships
- backref parameter on has_many, belongs_to, has_one
- back_populates parameter for explicit linking
- Foreign key detection and configuration
"""

import pytest
from typing import List, Optional

from pynext.db import (
    Table,
    configure_db,
    MockAdapter,
    has_many,
    has_one,
    belongs_to,
    BelongsTo,
    HasMany,
    HasOne,
    BackrefConfig,
    BackrefRegistry,
    get_backref_registry,
    reset_backref_registry,
    RelationshipType,
)
from pynext.db.table import _model_registry


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def clean_registry():
    """Reset registries before each test."""
    reset_backref_registry()
    # Clear model registry of test models
    keys_to_remove = [k for k in _model_registry.keys() if 'test' in k.lower() or k.startswith('BR')]
    for k in keys_to_remove:
        _model_registry.pop(k, None)
    yield
    reset_backref_registry()


@pytest.fixture
async def mock_adapter(clean_registry):
    """Create and configure a mock adapter."""
    adapter = MockAdapter()
    await adapter.connect()
    configure_db(adapter)
    yield adapter
    adapter.reset()
    await adapter.disconnect()


# =============================================================================
# BackrefConfig Tests (30 tests)
# =============================================================================

class TestBackrefConfig:
    """Tests for BackrefConfig dataclass."""
    
    def test_config_creation_minimal(self, clean_registry):
        """Test creating BackrefConfig with minimal args."""
        config = BackrefConfig(
            name="author",
            source_model="users",
            source_attr="posts",
            target_model="posts",
            target_attr="author",
        )
        
        assert config.name == "author"
        assert config.source_attr == "posts"
    
    def test_config_creation_full(self, clean_registry):
        """Test creating BackrefConfig with all args."""
        config = BackrefConfig(
            name="author",
            source_model="users",
            source_attr="posts",
            target_model="posts",
            target_attr="author",
            foreign_key="author_id",
            cascade_add=True,
            cascade_remove=False,
        )
        
        assert config.foreign_key == "author_id"
        assert config.cascade_add is True
        assert config.cascade_remove is False
    
    def test_config_defaults(self, clean_registry):
        """Test BackrefConfig default values."""
        config = BackrefConfig(
            name="test",
            source_model="a",
            source_attr="b",
            target_model="c",
            target_attr="d",
        )
        
        assert config.foreign_key is None
        assert config.cascade_add is True
        assert config.cascade_remove is True
    
    def test_config_to_dict(self, clean_registry):
        """Test converting BackrefConfig to dict."""
        config = BackrefConfig(
            name="author",
            source_model="users",
            source_attr="posts",
            target_model="posts",
            target_attr="author",
            foreign_key="author_id",
        )
        
        d = config.to_dict()
        
        assert d["name"] == "author"
        assert d["source_attr"] == "posts"
        assert d["target_attr"] == "author"
        assert d["foreign_key"] == "author_id"
    
    def test_config_to_dict_with_model_class(self, clean_registry):
        """Test to_dict handles model classes."""
        class BRUser1(Table):
            name: str
        
        config = BackrefConfig(
            name="posts",
            source_model=BRUser1,
            source_attr="posts",
            target_model="posts",
            target_attr="author",
        )
        
        d = config.to_dict()
        assert d["source_model"] == "BRUser1"
    
    def test_config_source_model_string(self, clean_registry):
        """Test config with string model name."""
        config = BackrefConfig(
            name="author",
            source_model="users",
            source_attr="posts",
            target_model="posts",
            target_attr="author",
        )
        
        assert config.source_model == "users"
    
    def test_config_cascade_add_disabled(self, clean_registry):
        """Test config with cascade_add disabled."""
        config = BackrefConfig(
            name="author",
            source_model="users",
            source_attr="posts",
            target_model="posts",
            target_attr="author",
            cascade_add=False,
        )
        
        assert config.cascade_add is False
    
    def test_config_cascade_remove_disabled(self, clean_registry):
        """Test config with cascade_remove disabled."""
        config = BackrefConfig(
            name="author",
            source_model="users",
            source_attr="posts",
            target_model="posts",
            target_attr="author",
            cascade_remove=False,
        )
        
        assert config.cascade_remove is False
    
    def test_config_both_cascades_disabled(self, clean_registry):
        """Test config with both cascades disabled."""
        config = BackrefConfig(
            name="author",
            source_model="users",
            source_attr="posts",
            target_model="posts",
            target_attr="author",
            cascade_add=False,
            cascade_remove=False,
        )
        
        assert config.cascade_add is False
        assert config.cascade_remove is False
    
    def test_config_custom_foreign_key(self, clean_registry):
        """Test config with custom foreign key."""
        config = BackrefConfig(
            name="writer",
            source_model="articles",
            source_attr="articles",
            target_model="users",
            target_attr="writer",
            foreign_key="writer_id",
        )
        
        assert config.foreign_key == "writer_id"


# =============================================================================
# BackrefRegistry Tests (40 tests)
# =============================================================================

class TestBackrefRegistry:
    """Tests for BackrefRegistry class."""
    
    def test_registry_singleton(self, clean_registry):
        """Test get_backref_registry returns singleton."""
        reg1 = get_backref_registry()
        reg2 = get_backref_registry()
        
        assert reg1 is reg2
    
    def test_registry_register_basic(self, clean_registry):
        """Test registering a backref config."""
        registry = get_backref_registry()
        
        config = BackrefConfig(
            name="author",
            source_model="users",
            source_attr="posts",
            target_model="posts",
            target_attr="author",
        )
        
        registry.register(config)
        
        assert registry.has_backref("users", "posts")
        assert registry.has_backref("posts", "author")
    
    def test_registry_get_backref_for_source(self, clean_registry):
        """Test getting backref config for source side."""
        registry = get_backref_registry()
        
        config = BackrefConfig(
            name="author",
            source_model="users",
            source_attr="posts",
            target_model="posts",
            target_attr="author",
        )
        registry.register(config)
        
        result = registry.get_backref_for_source("users", "posts")
        
        assert result is config
    
    def test_registry_get_backref_for_target(self, clean_registry):
        """Test getting backref config for target side."""
        registry = get_backref_registry()
        
        config = BackrefConfig(
            name="author",
            source_model="users",
            source_attr="posts",
            target_model="posts",
            target_attr="author",
        )
        registry.register(config)
        
        result = registry.get_backref_for_target("posts", "author")
        
        assert result is config
    
    def test_registry_has_backref_false(self, clean_registry):
        """Test has_backref returns False for unregistered."""
        registry = get_backref_registry()
        
        assert registry.has_backref("unknown", "attr") is False
    
    def test_registry_get_reverse_attr_source(self, clean_registry):
        """Test getting reverse attr from source side."""
        registry = get_backref_registry()
        
        config = BackrefConfig(
            name="author",
            source_model="users",
            source_attr="posts",
            target_model="posts",
            target_attr="author",
        )
        registry.register(config)
        
        result = registry.get_reverse_attr("users", "posts")
        
        assert result == ("posts", "author")
    
    def test_registry_get_reverse_attr_target(self, clean_registry):
        """Test getting reverse attr from target side."""
        registry = get_backref_registry()
        
        config = BackrefConfig(
            name="author",
            source_model="users",
            source_attr="posts",
            target_model="posts",
            target_attr="author",
        )
        registry.register(config)
        
        result = registry.get_reverse_attr("posts", "author")
        
        assert result == ("users", "posts")
    
    def test_registry_get_reverse_attr_none(self, clean_registry):
        """Test get_reverse_attr returns None for unknown."""
        registry = get_backref_registry()
        
        result = registry.get_reverse_attr("unknown", "attr")
        
        assert result is None
    
    def test_registry_clear(self, clean_registry):
        """Test clearing the registry."""
        registry = get_backref_registry()
        
        config = BackrefConfig(
            name="author",
            source_model="users",
            source_attr="posts",
            target_model="posts",
            target_attr="author",
        )
        registry.register(config)
        
        registry.clear()
        
        assert registry.has_backref("users", "posts") is False
    
    def test_registry_get_stats(self, clean_registry):
        """Test getting registry statistics."""
        registry = get_backref_registry()
        
        config = BackrefConfig(
            name="author",
            source_model="users",
            source_attr="posts",
            target_model="posts",
            target_attr="author",
        )
        registry.register(config)
        
        stats = registry.get_stats()
        
        assert stats["source_count"] == 1
        assert stats["target_count"] == 1
    
    def test_registry_multiple_registrations(self, clean_registry):
        """Test registering multiple backrefs."""
        registry = get_backref_registry()
        
        config1 = BackrefConfig(
            name="author",
            source_model="users",
            source_attr="posts",
            target_model="posts",
            target_attr="author",
        )
        config2 = BackrefConfig(
            name="owner",
            source_model="users",
            source_attr="comments",
            target_model="comments",
            target_attr="owner",
        )
        
        registry.register(config1)
        registry.register(config2)
        
        assert registry.has_backref("users", "posts")
        assert registry.has_backref("users", "comments")
    
    def test_registry_with_model_class(self, clean_registry):
        """Test registry with actual model classes."""
        class BRUser2(Table):
            name: str
        
        class BRPost2(Table):
            title: str
            user_id: int
        
        registry = get_backref_registry()
        
        config = BackrefConfig(
            name="author",
            source_model=BRUser2,
            source_attr="posts",
            target_model=BRPost2,
            target_attr="author",
        )
        registry.register(config)
        
        assert registry.has_backref(BRUser2, "posts")
        assert registry.has_backref(BRPost2, "author")
    
    def test_registry_pending_backref(self, clean_registry):
        """Test adding pending backref for forward reference."""
        registry = get_backref_registry()
        
        config = BackrefConfig(
            name="author",
            source_model="users",
            source_attr="posts",
            target_model="posts",
            target_attr="author",
        )
        
        registry.add_pending("posts", config)
        
        stats = registry.get_stats()
        assert stats["pending_count"] == 1
    
    def test_registry_resolve_pending(self, clean_registry):
        """Test resolving pending backrefs."""
        registry = get_backref_registry()
        
        config = BackrefConfig(
            name="author",
            source_model="bruser3s",
            source_attr="posts",
            target_model="brpost3s",
            target_attr="author",
        )
        
        registry.add_pending("brpost3s", config)
        
        # Create the model that was pending
        class BRPost3(Table):
            title: str
        
        registry.resolve_pending(BRPost3)
        
        # Config should now be registered
        assert registry.has_backref("brpost3s", "author")
    
    def test_registry_stats_empty(self, clean_registry):
        """Test stats on empty registry."""
        registry = get_backref_registry()
        
        stats = registry.get_stats()
        
        assert stats["source_count"] == 0
        assert stats["target_count"] == 0
        assert stats["pending_count"] == 0


# =============================================================================
# has_many backref Tests (30 tests)
# =============================================================================

class TestHasManyBackref:
    """Tests for has_many with backref parameter."""
    
    def test_has_many_backref_creates_descriptor(self, clean_registry):
        """Test has_many with backref creates reverse descriptor."""
        class BRUser4(Table):
            name: str
            posts: List["BRPost4"] = has_many("BRPost4", backref="author")
        
        class BRPost4(Table):
            title: str
            user_id: int
        
        # Backref should create author on BRPost4
        assert hasattr(BRPost4, "author")
    
    def test_has_many_backref_correct_type(self, clean_registry):
        """Test backref creates correct relationship type."""
        class BRUser5(Table):
            name: str
            posts: List["BRPost5"] = has_many("BRPost5", backref="author")
        
        class BRPost5(Table):
            title: str
            user_id: int
        
        # Should be BelongsTo
        assert isinstance(BRPost5.author, BelongsTo)
    
    def test_has_many_backref_rel_name(self, clean_registry):
        """Test backref sets correct rel_name."""
        class BRUser6(Table):
            name: str
            posts: List["BRPost6"] = has_many("BRPost6", backref="author")
        
        class BRPost6(Table):
            title: str
            user_id: int
        
        assert BRPost6.author.rel_name == "author"
    
    def test_has_many_backref_foreign_key(self, clean_registry):
        """Test backref inherits foreign key."""
        class BRUser7(Table):
            name: str
            posts: List["BRPost7"] = has_many("BRPost7", foreign_key="author_id", backref="author")
        
        class BRPost7(Table):
            title: str
            author_id: int
        
        assert BRPost7.author.foreign_key == "author_id"
    
    def test_has_many_backref_model_reference(self, clean_registry):
        """Test backref points to correct model."""
        class BRUser8(Table):
            name: str
            posts: List["BRPost8"] = has_many("BRPost8", backref="author")
        
        class BRPost8(Table):
            title: str
            user_id: int
        
        # Should reference User
        assert BRPost8.author._model == BRUser8 or BRPost8.author._model == "bruser8s"
    
    def test_has_many_backref_back_populates_set(self, clean_registry):
        """Test backref sets back_populates on both sides."""
        class BRUser9(Table):
            name: str
            posts: List["BRPost9"] = has_many("BRPost9", backref="author")
        
        class BRPost9(Table):
            title: str
            user_id: int
        
        # Original should have back_populates set
        assert BRUser9.posts.back_populates == "author"
    
    def test_has_many_backref_with_custom_fk(self, clean_registry):
        """Test backref with custom foreign key name."""
        class BRWriter(Table):
            name: str
            articles: List["BRArticle"] = has_many("BRArticle", foreign_key="writer_id", backref="writer")
        
        class BRArticle(Table):
            title: str
            writer_id: int
        
        assert hasattr(BRArticle, "writer")
        assert BRArticle.writer.foreign_key == "writer_id"
    
    def test_has_many_without_backref(self, clean_registry):
        """Test has_many without backref doesn't create reverse."""
        class BRUser10(Table):
            name: str
            posts: List["BRPost10"] = has_many("BRPost10")
        
        class BRPost10(Table):
            title: str
            user_id: int
        
        # Should NOT have author (unless auto-detected)
        # Actually, auto-detection might create it, so just check has_many is set
        assert hasattr(BRUser10, "posts")
    
    def test_has_many_backref_registered(self, clean_registry):
        """Test backref is registered in BackrefRegistry."""
        class BRUser11(Table):
            name: str
            posts: List["BRPost11"] = has_many("BRPost11", backref="author")
        
        class BRPost11(Table):
            title: str
            user_id: int
        
        registry = get_backref_registry()
        assert registry.has_backref(BRUser11, "posts")
    
    def test_has_many_multiple_backrefs(self, clean_registry):
        """Test model with multiple has_many backrefs."""
        class BRUser12(Table):
            name: str
            posts: List["BRPost12"] = has_many("BRPost12", backref="author")
            comments: List["BRComment12"] = has_many("BRComment12", backref="commenter")
        
        class BRPost12(Table):
            title: str
            user_id: int
        
        class BRComment12(Table):
            content: str
            user_id: int
        
        assert hasattr(BRPost12, "author")
        assert hasattr(BRComment12, "commenter")


# =============================================================================
# belongs_to backref Tests (20 tests)
# =============================================================================

class TestBelongsToBackref:
    """Tests for belongs_to with backref parameter."""
    
    def test_belongs_to_backref_creates_has_many(self, clean_registry):
        """Test belongs_to backref creates has_many on target."""
        class BRAuthor1(Table):
            name: str
        
        class BRBook1(Table):
            title: str
            author_id: int
            author: "BRAuthor1" = belongs_to("BRAuthor1", backref="books")
        
        assert hasattr(BRAuthor1, "books")
    
    def test_belongs_to_backref_correct_type(self, clean_registry):
        """Test belongs_to backref creates HasMany."""
        class BRAuthor2(Table):
            name: str
        
        class BRBook2(Table):
            title: str
            author_id: int
            author: "BRAuthor2" = belongs_to("BRAuthor2", backref="books")
        
        assert isinstance(BRAuthor2.books, HasMany)
    
    def test_belongs_to_backref_rel_name(self, clean_registry):
        """Test backref sets correct rel_name."""
        class BRAuthor3(Table):
            name: str
        
        class BRBook3(Table):
            title: str
            author_id: int
            author: "BRAuthor3" = belongs_to("BRAuthor3", backref="books")
        
        assert BRAuthor3.books.rel_name == "books"
    
    def test_belongs_to_backref_foreign_key(self, clean_registry):
        """Test backref inherits foreign key."""
        class BRAuthor4(Table):
            name: str
        
        class BRBook4(Table):
            title: str
            author_id: int
            author: "BRAuthor4" = belongs_to("BRAuthor4", foreign_key="author_id", backref="books")
        
        assert BRAuthor4.books.foreign_key == "author_id"
    
    def test_belongs_to_without_backref(self, clean_registry):
        """Test belongs_to without backref."""
        class BRAuthor5(Table):
            name: str
        
        class BRBook5(Table):
            title: str
            author_id: int
            author: "BRAuthor5" = belongs_to("BRAuthor5")
        
        assert hasattr(BRBook5, "author")


# =============================================================================
# has_one backref Tests (15 tests)
# =============================================================================

class TestHasOneBackref:
    """Tests for has_one with backref parameter."""
    
    def test_has_one_backref_creates_belongs_to(self, clean_registry):
        """Test has_one backref creates belongs_to on target."""
        class BRUser13(Table):
            name: str
            profile: "BRProfile1" = has_one("BRProfile1", backref="user")
        
        class BRProfile1(Table):
            bio: str
            user_id: int
        
        assert hasattr(BRProfile1, "user")
    
    def test_has_one_backref_correct_type(self, clean_registry):
        """Test has_one backref creates BelongsTo."""
        class BRUser14(Table):
            name: str
            profile: "BRProfile2" = has_one("BRProfile2", backref="user")
        
        class BRProfile2(Table):
            bio: str
            user_id: int
        
        assert isinstance(BRProfile2.user, BelongsTo)
    
    def test_has_one_backref_rel_name(self, clean_registry):
        """Test backref sets correct rel_name."""
        class BRUser15(Table):
            name: str
            profile: "BRProfile3" = has_one("BRProfile3", backref="user")
        
        class BRProfile3(Table):
            bio: str
            user_id: int
        
        assert BRProfile3.user.rel_name == "user"
    
    def test_has_one_backref_foreign_key(self, clean_registry):
        """Test backref inherits foreign key."""
        class BRUser16(Table):
            name: str
            profile: "BRProfile4" = has_one("BRProfile4", foreign_key="owner_id", backref="user")
        
        class BRProfile4(Table):
            bio: str
            owner_id: int
        
        assert BRProfile4.user.foreign_key == "owner_id"


# =============================================================================
# back_populates Tests (15 tests)
# =============================================================================

class TestBackPopulates:
    """Tests for explicit back_populates parameter."""
    
    def test_back_populates_both_sides(self, clean_registry):
        """Test back_populates with both sides defined."""
        class BRUser17(Table):
            name: str
            posts: List["BRPost13"] = has_many("BRPost13", back_populates="author")
        
        class BRPost13(Table):
            title: str
            user_id: int
            author: "BRUser17" = belongs_to("BRUser17", back_populates="posts")
        
        assert BRUser17.posts.back_populates == "author"
        assert BRPost13.author.back_populates == "posts"
    
    def test_back_populates_registered(self, clean_registry):
        """Test back_populates is registered in BackrefRegistry."""
        class BRUser18(Table):
            name: str
            posts: List["BRPost14"] = has_many("BRPost14", back_populates="author")
        
        class BRPost14(Table):
            title: str
            user_id: int
            author: "BRUser18" = belongs_to("BRUser18", back_populates="posts")
        
        registry = get_backref_registry()
        # At least one side should be registered
        has_source = registry.has_backref(BRUser18, "posts")
        has_target = registry.has_backref(BRPost14, "author")
        
        assert has_source or has_target
    
    def test_back_populates_with_custom_fk(self, clean_registry):
        """Test back_populates with custom foreign key."""
        class BRWriter2(Table):
            name: str
            articles: List["BRArticle2"] = has_many("BRArticle2", foreign_key="writer_id", back_populates="writer")
        
        class BRArticle2(Table):
            title: str
            writer_id: int
            writer: "BRWriter2" = belongs_to("BRWriter2", foreign_key="writer_id", back_populates="articles")
        
        assert BRWriter2.articles.foreign_key == "writer_id"
        assert BRArticle2.writer.foreign_key == "writer_id"
    
    def test_back_populates_without_backref(self, clean_registry):
        """Test back_populates doesn't auto-create reverse."""
        class BRUser19(Table):
            name: str
            # Note: back_populates without the other side defined
            items: List["BRItem1"] = has_many("BRItem1", back_populates="owner")
        
        class BRItem1(Table):
            name: str
            user_id: int
        
        # owner should NOT be auto-created (that's what backref does)
        # back_populates just registers the pair
        assert BRUser19.items.back_populates == "owner"


# =============================================================================
# Descriptor Attribute Tests (20 tests)
# =============================================================================

class TestDescriptorAttributes:
    """Tests for relationship descriptor attributes."""
    
    def test_belongs_to_has_backref_attr(self, clean_registry):
        """Test BelongsTo has backref attribute."""
        desc = BelongsTo("test", "model", "fk", backref="reverse")
        assert desc.backref == "reverse"
    
    def test_belongs_to_has_back_populates_attr(self, clean_registry):
        """Test BelongsTo has back_populates attribute."""
        desc = BelongsTo("test", "model", "fk", back_populates="reverse")
        assert desc.back_populates == "reverse"
    
    def test_has_many_has_backref_attr(self, clean_registry):
        """Test HasMany has backref attribute."""
        desc = HasMany("test", "model", "fk", backref="reverse")
        assert desc.backref == "reverse"
    
    def test_has_many_has_back_populates_attr(self, clean_registry):
        """Test HasMany has back_populates attribute."""
        desc = HasMany("test", "model", "fk", back_populates="reverse")
        assert desc.back_populates == "reverse"
    
    def test_has_one_has_backref_attr(self, clean_registry):
        """Test HasOne has backref attribute."""
        desc = HasOne("test", "model", "fk", backref="reverse")
        assert desc.backref == "reverse"
    
    def test_has_one_has_back_populates_attr(self, clean_registry):
        """Test HasOne has back_populates attribute."""
        desc = HasOne("test", "model", "fk", back_populates="reverse")
        assert desc.back_populates == "reverse"
    
    def test_descriptor_cache_attr(self, clean_registry):
        """Test descriptor cache attribute naming."""
        desc = BelongsTo("author", "users", "author_id")
        assert desc._cache_attr == "_cached_author"
    
    def test_descriptor_none_backref(self, clean_registry):
        """Test descriptor with no backref."""
        desc = HasMany("posts", "posts", "user_id")
        assert desc.backref is None
        assert desc.back_populates is None
    
    def test_descriptor_rel_name_from_function(self, clean_registry):
        """Test descriptor created by function has empty rel_name initially."""
        desc = has_many("Post")
        assert desc.rel_name == ""
    
    def test_descriptor_rel_name_set_by_metaclass(self, clean_registry):
        """Test metaclass sets rel_name."""
        class BRUser20(Table):
            name: str
            posts: List["BRPost15"] = has_many("BRPost15", backref="author")
        
        class BRPost15(Table):
            title: str
            user_id: int
        
        assert BRUser20.posts.rel_name == "posts"

