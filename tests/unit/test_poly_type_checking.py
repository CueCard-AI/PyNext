"""
Test Phase 7.7: Type Checking and Validation Tests.

Tests for type checking, validation, and safety.
"""

import pytest
from typing import Optional, Union, List
from unittest.mock import Mock, MagicMock, patch

from pynext.db.polymorphic import (
    polymorphic,
    generic_fk,
    is_polymorphic,
    is_polymorphic_base,
    is_polymorphic_subtype,
    get_polymorphic_identity,
    get_polymorphic_base,
    get_generic_fk_config,
    get_polymorphic_registry,
    reset_polymorphic_registry,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def reset_registry():
    """Reset registry before each test."""
    reset_polymorphic_registry()
    yield
    reset_polymorphic_registry()


# =============================================================================
# Test is_polymorphic
# =============================================================================

class TestIsPolymorphic:
    """Test is_polymorphic function."""
    
    def test_true_for_base(self):
        """True for base class."""
        @polymorphic("type")
        class Content:
            pass
        
        assert is_polymorphic(Content) is True
    
    def test_true_for_subtype(self):
        """True for subtype."""
        @polymorphic("type")
        class Content:
            pass
        
        @polymorphic.subtype("article")
        class Article(Content):
            pass
        
        assert is_polymorphic(Article) is True
    
    def test_false_for_regular(self):
        """False for regular class."""
        class Regular:
            pass
        
        assert is_polymorphic(Regular) is False
    
    def test_false_for_builtin(self):
        """False for builtin types."""
        assert is_polymorphic(str) is False
        assert is_polymorphic(int) is False
        assert is_polymorphic(list) is False


# =============================================================================
# Test is_polymorphic_base
# =============================================================================

class TestIsPolymorphicBase:
    """Test is_polymorphic_base function."""
    
    def test_true_for_base(self):
        """True for base class."""
        @polymorphic("type")
        class Content:
            pass
        
        assert is_polymorphic_base(Content) is True
    
    def test_false_for_subtype(self):
        """False for subtype."""
        @polymorphic("type")
        class Content:
            pass
        
        @polymorphic.subtype("article")
        class Article(Content):
            pass
        
        assert is_polymorphic_base(Article) is False
    
    def test_false_for_regular(self):
        """False for regular class."""
        class Regular:
            pass
        
        assert is_polymorphic_base(Regular) is False


# =============================================================================
# Test is_polymorphic_subtype
# =============================================================================

class TestIsPolymorphicSubtype:
    """Test is_polymorphic_subtype function."""
    
    def test_false_for_base(self):
        """False for base class."""
        @polymorphic("type")
        class Content:
            pass
        
        assert is_polymorphic_subtype(Content) is False
    
    def test_true_for_subtype(self):
        """True for subtype."""
        @polymorphic("type")
        class Content:
            pass
        
        @polymorphic.subtype("article")
        class Article(Content):
            pass
        
        assert is_polymorphic_subtype(Article) is True
    
    def test_false_for_regular(self):
        """False for regular class."""
        class Regular:
            pass
        
        assert is_polymorphic_subtype(Regular) is False


# =============================================================================
# Test get_polymorphic_identity
# =============================================================================

class TestGetPolymorphicIdentity:
    """Test get_polymorphic_identity function."""
    
    def test_returns_identity_for_subtype(self):
        """Returns identity for subtype."""
        @polymorphic("type")
        class Content:
            pass
        
        @polymorphic.subtype("article")
        class Article(Content):
            pass
        
        assert get_polymorphic_identity(Article) == "article"
    
    def test_none_for_base_without_identity(self):
        """None for base without identity."""
        @polymorphic("type")
        class Content:
            pass
        
        assert get_polymorphic_identity(Content) is None
    
    def test_returns_identity_for_base_with_identity(self):
        """Returns identity for base with identity."""
        @polymorphic("type", identity="base")
        class Content:
            pass
        
        assert get_polymorphic_identity(Content) == "base"
    
    def test_none_for_regular(self):
        """None for regular class."""
        class Regular:
            pass
        
        assert get_polymorphic_identity(Regular) is None


# =============================================================================
# Test get_polymorphic_base
# =============================================================================

class TestGetPolymorphicBase:
    """Test get_polymorphic_base function."""
    
    def test_returns_self_for_base(self):
        """Returns self for base class."""
        @polymorphic("type")
        class Content:
            pass
        
        assert get_polymorphic_base(Content) == Content
    
    def test_returns_base_for_subtype(self):
        """Returns base for subtype."""
        @polymorphic("type")
        class Content:
            pass
        
        @polymorphic.subtype("article")
        class Article(Content):
            pass
        
        assert get_polymorphic_base(Article) == Content
    
    def test_none_for_regular(self):
        """None for regular class."""
        class Regular:
            pass
        
        assert get_polymorphic_base(Regular) is None


# =============================================================================
# Test Generic FK Type Validation
# =============================================================================

class MockModel1:
    __tablename__ = "models1"
    def __init__(self, id):
        self.id = id


class MockModel2:
    __tablename__ = "models2"
    def __init__(self, id):
        self.id = id


class MockModel3:
    __tablename__ = "models3"
    def __init__(self, id):
        self.id = id


class TestGenericFKTypeValidation:
    """Test generic FK type validation."""
    
    def test_valid_type_accepted(self):
        """Valid type is accepted."""
        class Container:
            target: Union[MockModel1, MockModel2] = generic_fk()
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        obj = Container()
        obj.target = MockModel1(id=1)  # Should not raise
        
        assert obj.target_type == "models1"
    
    def test_invalid_type_raises(self):
        """Invalid type raises TypeError."""
        class Container:
            target: Union[MockModel1, MockModel2] = generic_fk()
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        obj = Container()
        
        with pytest.raises(TypeError, match="Invalid target type"):
            obj.target = MockModel3(id=1)
    
    def test_none_accepted(self):
        """None is always accepted."""
        class Container:
            target: Union[MockModel1, MockModel2] = generic_fk()
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        obj = Container()
        obj.target = None  # Should not raise
        
        assert obj.target_type is None


# =============================================================================
# Test GenericFKConfig Validation
# =============================================================================

class TestGenericFKConfigValidation:
    """Test GenericFKConfig validation methods."""
    
    def test_validate_target_valid(self):
        """validate_target for valid type."""
        class Container:
            target: Union[MockModel1, MockModel2] = generic_fk()
        
        config = get_generic_fk_config(Container, "target")
        
        assert config.validate_target(MockModel1(id=1)) is True
        assert config.validate_target(MockModel2(id=1)) is True
    
    def test_validate_target_invalid(self):
        """validate_target for invalid type."""
        class Container:
            target: Union[MockModel1, MockModel2] = generic_fk()
        
        config = get_generic_fk_config(Container, "target")
        
        assert config.validate_target(MockModel3(id=1)) is False
    
    def test_validate_target_none(self):
        """validate_target for None."""
        class Container:
            target: Union[MockModel1, MockModel2] = generic_fk()
        
        config = get_generic_fk_config(Container, "target")
        
        assert config.validate_target(None) is True
    
    def test_get_type_name(self):
        """get_type_name returns table name."""
        class Container:
            target: Union[MockModel1, MockModel2] = generic_fk()
        
        config = get_generic_fk_config(Container, "target")
        
        assert config.get_type_name(MockModel1(id=1)) == "models1"
        assert config.get_type_name(MockModel2(id=1)) == "models2"
    
    def test_get_target_id(self):
        """get_target_id returns id."""
        class Container:
            target: Union[MockModel1, MockModel2] = generic_fk()
        
        config = get_generic_fk_config(Container, "target")
        
        assert config.get_target_id(MockModel1(id=42)) == 42
    
    def test_get_type_class(self):
        """get_type_class returns class."""
        class Container:
            target: Union[MockModel1, MockModel2] = generic_fk()
        
        config = get_generic_fk_config(Container, "target")
        
        assert config.get_type_class("models1") == MockModel1
        assert config.get_type_class("models2") == MockModel2
    
    def test_get_type_class_unknown(self):
        """get_type_class returns None for unknown."""
        class Container:
            target: Union[MockModel1, MockModel2] = generic_fk()
        
        config = get_generic_fk_config(Container, "target")
        
        assert config.get_type_class("unknown") is None

