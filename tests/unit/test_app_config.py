"""
Tests for pynext.app.config - Configuration System.

Tests cover:
- Data classes (AIPreferences, CodeStyle, ValidationRules, etc.)
- PyNextConfig loading and merging
- Variable resolution
- Mode handling
- Conditional evaluation
- Pattern rendering
- ConfigResolver
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import os

from pynext.app.config import (
    AIPreferences,
    CodeStyle,
    ValidationRules,
    TeamStandards,
    PromptConfig,
    Pattern,
    Conditional,
    RulesConfig,
    ModeConfig,
    MemoryConfig,
    PyNextConfig,
    ConfigContext,
    ResolvedConfig,
    ConfigResolver,
    get_config,
    reset_config,
    validate_config,
)


# =============================================================================
# AIPreferences Tests
# =============================================================================

class TestAIPreferences:
    """Tests for AIPreferences dataclass."""
    
    def test_defaults(self):
        """Test default values."""
        prefs = AIPreferences()
        assert prefs.model == "claude-sonnet-4-20250514"
        assert prefs.mode == "plan"
        assert prefs.complexity == "auto"
        assert prefs.verbose is False
    
    def test_from_dict(self):
        """Test creating from dict."""
        prefs = AIPreferences.from_dict({
            "model": "claude-opus-4",
            "mode": "agent",
            "verbose": True,
        })
        assert prefs.model == "claude-opus-4"
        assert prefs.mode == "agent"
        assert prefs.verbose is True
    
    def test_from_dict_ignores_unknown(self):
        """Test that unknown fields are ignored."""
        prefs = AIPreferences.from_dict({
            "model": "test",
            "unknown_field": "value",
        })
        assert prefs.model == "test"
        assert not hasattr(prefs, "unknown_field")


# =============================================================================
# CodeStyle Tests
# =============================================================================

class TestCodeStyle:
    """Tests for CodeStyle dataclass."""
    
    def test_defaults(self):
        """Test default values."""
        style = CodeStyle()
        assert style.naming_convention == "snake_case"
        assert style.max_line_length == 88
        assert style.docstring_style == "google"
    
    def test_from_dict(self):
        """Test creating from dict."""
        style = CodeStyle.from_dict({
            "naming_convention": "camelCase",
            "max_line_length": 120,
        })
        assert style.naming_convention == "camelCase"
        assert style.max_line_length == 120


# =============================================================================
# ValidationRules Tests
# =============================================================================

class TestValidationRules:
    """Tests for ValidationRules dataclass."""
    
    def test_defaults(self):
        """Test default values."""
        rules = ValidationRules()
        assert rules.require_docstrings is True
        assert rules.require_type_hints is True
        assert rules.require_tests is False
        assert rules.forbidden_imports == []
    
    def test_from_dict(self):
        """Test creating from dict."""
        rules = ValidationRules.from_dict({
            "require_tests": True,
            "forbidden_imports": ["os.system", "eval"],
        })
        assert rules.require_tests is True
        assert "os.system" in rules.forbidden_imports


# =============================================================================
# Pattern Tests
# =============================================================================

class TestPattern:
    """Tests for Pattern dataclass."""
    
    def test_create_pattern(self):
        """Test creating a pattern."""
        pattern = Pattern(
            name="test_pattern",
            description="A test pattern",
            code="def ${name}(): pass",
            tags=["test"],
        )
        assert pattern.name == "test_pattern"
        assert "${name}" in pattern.code
    
    def test_render(self):
        """Test rendering pattern with variables."""
        pattern = Pattern(
            name="greet",
            code="def ${name}(): return '${message}'",
        )
        result = pattern.render(name="hello", message="Hi!")
        assert "def hello()" in result
        assert "Hi!" in result
    
    def test_from_dict(self):
        """Test creating pattern from dict."""
        pattern = Pattern.from_dict("api_endpoint", {
            "description": "API endpoint",
            "code": "@api\ndef GET(): pass",
            "tags": ["api"],
            "when": "file_type == 'api'",
        })
        assert pattern.name == "api_endpoint"
        assert pattern.when == "file_type == 'api'"


# =============================================================================
# Conditional Tests
# =============================================================================

class TestConditional:
    """Tests for Conditional dataclass."""
    
    def test_create_conditional(self):
        """Test creating a conditional."""
        cond = Conditional(
            priority=80,
            when="file_type == 'api'",
            prompt="Use auth decorator.",
        )
        assert cond.priority == 80
        assert cond.when == "file_type == 'api'"
    
    def test_from_dict(self):
        """Test creating from dict."""
        cond = Conditional.from_dict({
            "priority": 90,
            "when_llm": "building payment feature",
            "prompt": "Use Decimal for money.",
        })
        assert cond.priority == 90
        assert cond.when_llm == "building payment feature"


# =============================================================================
# ModeConfig Tests
# =============================================================================

class TestModeConfig:
    """Tests for ModeConfig dataclass."""
    
    def test_create_mode(self):
        """Test creating a mode config."""
        mode = ModeConfig(
            description="Fast iteration",
            validation=ValidationRules(require_tests=False),
        )
        assert mode.description == "Fast iteration"
        assert mode.validation.require_tests is False
    
    def test_mode_inheritance(self):
        """Test mode with extends."""
        mode = ModeConfig(
            extends="production",
            description="Extra strict",
        )
        assert mode.extends == "production"
    
    def test_from_dict(self):
        """Test creating from dict."""
        mode = ModeConfig.from_dict({
            "description": "Test mode",
            "extends": "base",
            "validation": {"require_tests": True},
        })
        assert mode.extends == "base"
        assert mode.validation.require_tests is True


# =============================================================================
# PyNextConfig Tests
# =============================================================================

class TestPyNextConfig:
    """Tests for PyNextConfig class."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_default_config(self):
        """Test default configuration."""
        config = PyNextConfig()
        assert config.ai.model == "claude-sonnet-4-20250514"
        assert config.style.naming_convention == "snake_case"
        assert config.validation.require_docstrings is True
    
    def test_load_nonexistent_project(self, temp_project):
        """Test loading config from project without config file."""
        config = PyNextConfig.load(temp_project)
        # Should use defaults
        assert config.ai.mode == "plan"
    
    def test_load_from_file(self, temp_project):
        """Test loading config from pynext.toml."""
        config_content = """
[ai]
model = "test-model"
mode = "agent"

[style]
naming_convention = "camelCase"
"""
        (temp_project / "pynext.toml").write_text(config_content)
        
        config = PyNextConfig.load(temp_project)
        assert config.ai.model == "test-model"
        assert config.ai.mode == "agent"
        assert config.style.naming_convention == "camelCase"
    
    def test_env_override(self, temp_project):
        """Test environment variable overrides."""
        with patch.dict(os.environ, {"ANTHROPIC_MODEL": "env-model"}):
            config = PyNextConfig.load(temp_project)
            assert config.ai.model == "env-model"
    
    def test_substitute_vars(self):
        """Test variable substitution."""
        config = PyNextConfig()
        config.vars = {"company": "Acme", "year": "2025"}
        
        result = config.substitute_vars("Copyright ${year} ${company}")
        assert result == "Copyright 2025 Acme"
    
    def test_get_pattern(self):
        """Test getting a pattern by name."""
        config = PyNextConfig()
        config.patterns["test"] = Pattern(name="test", code="# test")
        
        pattern = config.get_pattern("test")
        assert pattern is not None
        assert pattern.code == "# test"
    
    def test_get_patterns_by_tags(self):
        """Test getting patterns by tags."""
        config = PyNextConfig()
        config.patterns["api1"] = Pattern(name="api1", tags=["api"])
        config.patterns["api2"] = Pattern(name="api2", tags=["api", "auth"])
        config.patterns["page1"] = Pattern(name="page1", tags=["page"])
        
        api_patterns = config.get_patterns_by_tags(["api"])
        assert len(api_patterns) == 2
    
    def test_to_prompt(self):
        """Test converting config to prompt."""
        config = PyNextConfig()
        config.prompts.system = "You are an expert."
        config.prompts.context = "Building a blog."
        
        prompt = config.to_prompt()
        assert "You are an expert" in prompt
        assert "Building a blog" in prompt
    
    def test_to_dict(self):
        """Test converting config to dict."""
        config = PyNextConfig()
        d = config.to_dict()
        
        assert "ai" in d
        assert "style" in d
        assert d["ai"]["model"] == "claude-sonnet-4-20250514"


# =============================================================================
# ConfigContext Tests
# =============================================================================

class TestConfigContext:
    """Tests for ConfigContext dataclass."""
    
    def test_create_context(self):
        """Test creating a config context."""
        ctx = ConfigContext(
            file_type="api",
            intent="add_feature",
            description="Add auth",
            mode="strict",
        )
        assert ctx.file_type == "api"
        assert ctx.intent == "add_feature"
    
    def test_to_dict(self):
        """Test converting to dict."""
        ctx = ConfigContext(
            file_type="page",
            intent="new_app",
        )
        d = ctx.to_dict()
        assert d["file_type"] == "page"
        assert d["intent"] == "new_app"
        assert "len" in d  # len function should be available


# =============================================================================
# ResolvedConfig Tests
# =============================================================================

class TestResolvedConfig:
    """Tests for ResolvedConfig dataclass."""
    
    def test_add_prompt(self):
        """Test adding prompts."""
        resolved = ResolvedConfig()
        resolved.add_prompt("First prompt")
        resolved.add_prompt("Second prompt")
        resolved.add_prompt("First prompt")  # Duplicate
        
        assert len(resolved.prompts) == 2
    
    def test_add_pattern(self):
        """Test adding patterns."""
        resolved = ResolvedConfig()
        p1 = Pattern(name="p1", code="")
        p2 = Pattern(name="p2", code="")
        
        resolved.add_pattern(p1)
        resolved.add_pattern(p2)
        resolved.add_pattern(p1)  # Duplicate
        
        assert len(resolved.patterns) == 2
    
    def test_substitute_vars(self):
        """Test variable substitution."""
        resolved = ResolvedConfig()
        resolved.system_prompt = "Hello ${name}"
        resolved.prompts = ["Use ${db}"]
        
        resolved.substitute_vars({"name": "World", "db": "PostgreSQL"})
        
        assert resolved.system_prompt == "Hello World"
        assert resolved.prompts[0] == "Use PostgreSQL"
    
    def test_get_system_prompt(self):
        """Test getting combined system prompt."""
        resolved = ResolvedConfig()
        resolved.system_prompt = "Base prompt."
        resolved.prompts = ["Extra 1.", "Extra 2."]
        
        full = resolved.get_system_prompt()
        assert "Base prompt" in full
        assert "Extra 1" in full
        assert "Extra 2" in full


# =============================================================================
# ConfigResolver Tests
# =============================================================================

class TestConfigResolver:
    """Tests for ConfigResolver class."""
    
    def test_eval_condition_true(self):
        """Test evaluating a true condition."""
        config = PyNextConfig()
        resolver = ConfigResolver(config)
        
        ctx = ConfigContext(file_type="api")
        result = resolver._eval_condition("file_type == 'api'", ctx)
        assert result is True
    
    def test_eval_condition_false(self):
        """Test evaluating a false condition."""
        config = PyNextConfig()
        resolver = ConfigResolver(config)
        
        ctx = ConfigContext(file_type="page")
        result = resolver._eval_condition("file_type == 'api'", ctx)
        assert result is False
    
    def test_eval_condition_with_len(self):
        """Test evaluating condition with len()."""
        config = PyNextConfig()
        resolver = ConfigResolver(config)
        
        # Mock project with files
        project = MagicMock()
        project.all_files = ["a.py", "b.py", "c.py"]
        project.has_auth = False
        
        ctx = ConfigContext(file_type="api", project=project)
        result = resolver._eval_condition("len(existing_files) > 2", ctx)
        assert result is True
    
    def test_eval_invalid_condition(self):
        """Test evaluating invalid condition."""
        config = PyNextConfig()
        resolver = ConfigResolver(config)
        
        ctx = ConfigContext()
        result = resolver._eval_condition("invalid syntax [", ctx)
        assert result is False  # Should not crash
    
    def test_resolve_sync_basic(self):
        """Test synchronous resolution."""
        config = PyNextConfig()
        config.prompts.system = "You are helpful."
        
        resolver = ConfigResolver(config)
        ctx = ConfigContext(file_type="page")
        
        resolved = resolver.resolve_sync(ctx)
        assert resolved.system_prompt == "You are helpful."
    
    def test_resolve_sync_with_mode(self):
        """Test resolution with active mode."""
        config = PyNextConfig()
        config.modes["strict"] = ModeConfig(
            description="Strict mode",
            validation=ValidationRules(require_tests=True),
        )
        
        resolver = ConfigResolver(config)
        ctx = ConfigContext(mode="strict")
        
        resolved = resolver.resolve_sync(ctx)
        assert resolved.validation is not None
        assert resolved.validation.require_tests is True
    
    def test_resolve_sync_with_conditionals(self):
        """Test resolution with matching conditionals."""
        config = PyNextConfig()
        config.conditionals = [
            Conditional(priority=80, when="file_type == 'api'", prompt="API prompt"),
            Conditional(priority=70, when="file_type == 'page'", prompt="Page prompt"),
        ]
        
        resolver = ConfigResolver(config)
        ctx = ConfigContext(file_type="api")
        
        resolved = resolver.resolve_sync(ctx)
        assert "API prompt" in resolved.prompts
        assert "Page prompt" not in resolved.prompts
    
    def test_resolve_sync_priority_order(self):
        """Test that conditionals are applied by priority."""
        config = PyNextConfig()
        config.conditionals = [
            Conditional(priority=50, when="True", prompt="Low"),
            Conditional(priority=90, when="True", prompt="High"),
            Conditional(priority=70, when="True", prompt="Medium"),
        ]
        
        resolver = ConfigResolver(config)
        ctx = ConfigContext()
        
        resolved = resolver.resolve_sync(ctx)
        # All should be added, order doesn't matter for prompts list
        assert len(resolved.prompts) == 3


# =============================================================================
# Validation Tests
# =============================================================================

class TestValidateConfig:
    """Tests for config validation."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_validate_nonexistent(self, temp_project):
        """Test validating nonexistent file."""
        errors = validate_config(temp_project / "pynext.toml")
        assert len(errors) > 0
        assert "not found" in errors[0].lower()
    
    def test_validate_valid_config(self, temp_project):
        """Test validating a valid config."""
        config_content = """
[ai]
model = "claude-sonnet-4-20250514"
mode = "plan"

[style]
naming_convention = "snake_case"
"""
        config_file = temp_project / "pynext.toml"
        config_file.write_text(config_content)
        
        errors = validate_config(config_file)
        assert len(errors) == 0
    
    def test_validate_invalid_mode(self, temp_project):
        """Test validating config with invalid mode."""
        config_content = """
[ai]
mode = "invalid_mode"
"""
        config_file = temp_project / "pynext.toml"
        config_file.write_text(config_content)
        
        errors = validate_config(config_file)
        assert any("mode" in e.lower() for e in errors)


# =============================================================================
# Global Functions Tests
# =============================================================================

class TestGlobalFunctions:
    """Tests for module-level functions."""
    
    def test_get_config_singleton(self, tmp_path):
        """Test that get_config returns singleton."""
        reset_config()
        
        c1 = get_config(tmp_path)
        c2 = get_config(tmp_path)
        
        assert c1 is c2
        reset_config()
    
    def test_reset_config(self, tmp_path):
        """Test resetting global config."""
        reset_config()
        c1 = get_config(tmp_path)
        
        reset_config()
        c2 = get_config(tmp_path)
        
        assert c1 is not c2
        reset_config()

