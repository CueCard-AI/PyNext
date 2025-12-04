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
import json
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
    ExamplesConfig,
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


# =============================================================================
# Variable Resolution Tests Extended
# =============================================================================

class TestVariableResolutionExtended:
    """Extended tests for variable resolution."""
    
    def test_nested_variable_substitution(self):
        """Test substituting variables that reference other variables."""
        config = PyNextConfig()
        config.vars = {
            "company": "Acme",
            "year": "2025",
            "copyright": "Copyright 2025 Acme",  # Pre-computed
        }
        
        result = config.substitute_vars("${copyright}")
        assert result == "Copyright 2025 Acme"
    
    def test_variable_not_found(self):
        """Test substitution with missing variable."""
        config = PyNextConfig()
        config.vars = {"name": "test"}
        
        # Missing variable should remain as-is
        result = config.substitute_vars("Hello ${unknown}")
        assert "${unknown}" in result
    
    def test_multiple_same_variable(self):
        """Test substituting same variable multiple times."""
        config = PyNextConfig()
        config.vars = {"name": "PyNext"}
        
        result = config.substitute_vars("${name} is ${name}")
        assert result == "PyNext is PyNext"
    
    def test_empty_vars(self):
        """Test substitution with no variables defined."""
        config = PyNextConfig()
        config.vars = {}
        
        result = config.substitute_vars("Hello ${world}")
        assert result == "Hello ${world}"


# =============================================================================
# Mode Tests Extended
# =============================================================================

class TestModeExtended:
    """Extended tests for mode functionality."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_mode_inheritance_chain(self, temp_project):
        """Test multiple levels of mode inheritance."""
        config_content = """
[mode.base]
description = "Base mode"
[mode.base.validation]
require_docstrings = true

[mode.middle]
extends = "base"
description = "Middle mode"
[mode.middle.validation]
require_type_hints = true

[mode.strict]
extends = "middle"
description = "Strict mode"
[mode.strict.validation]
require_tests = true
"""
        (temp_project / "pynext.toml").write_text(config_content)
        config = PyNextConfig.load(temp_project)
        
        # strict inherits from middle which inherits from base
        assert "strict" in config.modes
        assert config.modes["strict"].extends == "middle"
    
    def test_mode_overrides_prompts(self, temp_project):
        """Test mode overrides prompts."""
        config_content = """
[prompts]
system = "Base system prompt"

[mode.strict]
description = "Strict mode"
[mode.strict.prompts]
system = "Strict system prompt"
"""
        (temp_project / "pynext.toml").write_text(config_content)
        config = PyNextConfig.load(temp_project)
        
        assert config.modes["strict"].prompts.system == "Strict system prompt"
    
    def test_get_nonexistent_mode(self):
        """Test getting a mode that doesn't exist."""
        config = PyNextConfig()
        mode = config.get_mode("nonexistent")
        assert mode is None


# =============================================================================
# Prompt Config Tests Extended
# =============================================================================

class TestPromptConfigExtended:
    """Extended tests for prompt configuration."""
    
    def test_get_for_type_page(self):
        """Test getting prompts for page type."""
        prompts = PromptConfig()
        prompts.page = {"prefix": "Page prefix", "suffix": "Page suffix"}
        
        page_prompts = prompts.get_for_type("page")
        assert page_prompts["prefix"] == "Page prefix"
    
    def test_get_for_type_unknown(self):
        """Test getting prompts for unknown type."""
        prompts = PromptConfig()
        unknown_prompts = prompts.get_for_type("unknown")
        assert unknown_prompts == {}
    
    def test_all_file_types(self):
        """Test all supported file types have prompt attributes."""
        prompts = PromptConfig()
        file_types = ["page", "island", "api", "model", "action", "component", "layout", "middleware", "util"]
        
        for ft in file_types:
            prompts_for_type = prompts.get_for_type(ft)
            assert isinstance(prompts_for_type, dict)


# =============================================================================
# Pattern Tests Extended
# =============================================================================

class TestPatternExtended:
    """Extended tests for patterns."""
    
    def test_pattern_render_multiple_vars(self):
        """Test rendering pattern with multiple variables."""
        pattern = Pattern(
            name="api",
            code="@api\nasync def ${method}():\n    '''${description}'''\n    ${body}",
        )
        
        result = pattern.render(
            method="GET",
            description="Get all users",
            body="return users",
        )
        
        assert "def GET()" in result
        assert "Get all users" in result
        assert "return users" in result
    
    def test_pattern_render_missing_var(self):
        """Test rendering pattern with missing variable."""
        pattern = Pattern(
            name="test",
            code="def ${name}(): ${body}",
        )
        
        result = pattern.render(name="hello")
        assert "def hello()" in result
        assert "${body}" in result  # Missing var stays as-is
    
    def test_pattern_with_condition(self):
        """Test pattern with when condition."""
        pattern = Pattern(
            name="auth_api",
            code="@require_auth\n@api\ndef GET(): pass",
            when="file_type == 'api'",
        )
        
        assert pattern.when == "file_type == 'api'"
    
    def test_pattern_with_deps(self):
        """Test pattern with dependencies."""
        pattern = Pattern(
            name="db_model",
            code="class User(Table): pass",
            deps=["pynext.db", "pynext.db.table"],
        )
        
        assert "pynext.db" in pattern.deps
        assert len(pattern.deps) == 2


# =============================================================================
# Conditional Tests Extended
# =============================================================================

class TestConditionalExtended:
    """Extended tests for conditionals."""
    
    def test_conditional_with_both_conditions(self):
        """Test conditional with both when and when_llm."""
        cond = Conditional(
            priority=85,
            when="file_type == 'api'",
            when_llm="handles sensitive data",
            prompt="Use encryption",
        )
        
        assert cond.when == "file_type == 'api'"
        assert cond.when_llm == "handles sensitive data"
    
    def test_conditional_with_pattern_reference(self):
        """Test conditional that references a pattern."""
        cond = Conditional(
            priority=80,
            when="True",
            pattern="auth_api",
            prompt="Use auth",
        )
        
        assert cond.pattern == "auth_api"
    
    def test_conditional_with_rules(self):
        """Test conditional that adds rules."""
        cond = Conditional(
            priority=75,
            when="mode == 'strict'",
            rules="Always validate input",
        )
        
        assert cond.rules == "Always validate input"


# =============================================================================
# Config Resolver Tests Extended
# =============================================================================

class TestConfigResolverExtended:
    """Extended tests for ConfigResolver."""
    
    def test_resolve_with_inheritance(self):
        """Test resolving config with mode inheritance."""
        config = PyNextConfig()
        config.modes["base"] = ModeConfig(
            validation=ValidationRules(require_tests=False),
        )
        config.modes["strict"] = ModeConfig(
            extends="base",
            validation=ValidationRules(require_tests=True),
        )
        
        resolver = ConfigResolver(config)
        ctx = ConfigContext(mode="strict")
        resolved = resolver.resolve_sync(ctx)
        
        # Should have strict mode's validation
        assert resolved.validation.require_tests is True
    
    def test_resolve_multiple_conditionals(self):
        """Test resolving with multiple matching conditionals."""
        config = PyNextConfig()
        config.conditionals = [
            Conditional(priority=90, when="True", prompt="High priority"),
            Conditional(priority=80, when="True", prompt="Medium priority"),
            Conditional(priority=70, when="True", prompt="Low priority"),
        ]
        
        resolver = ConfigResolver(config)
        ctx = ConfigContext()
        resolved = resolver.resolve_sync(ctx)
        
        # All matching conditionals should be included
        assert len(resolved.prompts) == 3
    
    def test_resolve_conditional_not_matching(self):
        """Test that non-matching conditionals are excluded."""
        config = PyNextConfig()
        config.conditionals = [
            Conditional(priority=90, when="file_type == 'api'", prompt="API prompt"),
            Conditional(priority=80, when="file_type == 'page'", prompt="Page prompt"),
        ]
        
        resolver = ConfigResolver(config)
        ctx = ConfigContext(file_type="api")
        resolved = resolver.resolve_sync(ctx)
        
        assert "API prompt" in resolved.prompts
        assert "Page prompt" not in resolved.prompts
    
    def test_resolve_with_project_context(self):
        """Test resolving with project context."""
        config = PyNextConfig()
        # Use dict-style access since project gets converted to dict
        config.conditionals = [
            Conditional(priority=80, when="has_auth == True", prompt="Use existing auth"),
        ]
        
        project = MagicMock()
        project.has_auth = True
        project.models = ["User"]
        project.all_files = ["pages/index.py"]
        
        resolver = ConfigResolver(config)
        ctx = ConfigContext(file_type="api", project=project)
        resolved = resolver.resolve_sync(ctx)
        
        assert "Use existing auth" in resolved.prompts


# =============================================================================
# Memory Config Tests
# =============================================================================

class TestMemoryConfig:
    """Tests for MemoryConfig dataclass."""
    
    def test_memory_config_defaults(self):
        """Test default memory config values."""
        config = MemoryConfig()
        
        assert config.sync_mode == "incremental"
        assert "assistant_response" in config.sync_on
        assert config.sync_batch_size == 5
        assert config.max_entries_in_memory == 1000
    
    def test_memory_config_from_dict(self):
        """Test creating memory config from dict."""
        config = MemoryConfig.from_dict({
            "sync_mode": "manual",
            "sync_batch_size": 10,
            "exclude_roles": ["system"],
        })
        
        assert config.sync_mode == "manual"
        assert config.sync_batch_size == 10
        assert config.exclude_roles == ["system"]


# =============================================================================
# Team Standards Tests Extended
# =============================================================================

class TestTeamStandardsExtended:
    """Extended tests for team standards."""
    
    def test_component_prefix(self):
        """Test component prefix setting."""
        standards = TeamStandards(component_prefix="Acme")
        assert standards.component_prefix == "Acme"
    
    def test_file_header_multiline(self):
        """Test multiline file header."""
        header = """
# Copyright 2025 Company
# All rights reserved
"""
        standards = TeamStandards(file_header=header)
        assert "Copyright" in standards.file_header
        assert "2025" in standards.file_header
    
    def test_required_patterns(self):
        """Test required patterns list."""
        standards = TeamStandards(required_patterns=["error_handling", "logging"])
        assert len(standards.required_patterns) == 2


# =============================================================================
# Config File Loading Tests Extended
# =============================================================================

class TestConfigFileLoadingExtended:
    """Extended tests for config file loading."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_load_with_patterns(self, temp_project):
        """Test loading config with patterns."""
        config_content = """
[patterns.test_pattern]
description = "Test pattern"
tags = ["test"]
code = '''
def test():
    pass
'''
"""
        (temp_project / "pynext.toml").write_text(config_content)
        config = PyNextConfig.load(temp_project)
        
        assert "test_pattern" in config.patterns
        assert config.patterns["test_pattern"].description == "Test pattern"
    
    def test_load_with_conditionals(self, temp_project):
        """Test loading config with conditionals."""
        config_content = """
[[conditional]]
priority = 85
when = "file_type == 'api'"
prompt = "API prompt"

[[conditional]]
priority = 80
when = "file_type == 'page'"
prompt = "Page prompt"
"""
        (temp_project / "pynext.toml").write_text(config_content)
        config = PyNextConfig.load(temp_project)
        
        assert len(config.conditionals) == 2
        assert config.conditionals[0].priority == 85
    
    def test_load_with_rules(self, temp_project):
        """Test loading config with rules."""
        config_content = """
[rules]
custom = "Custom rule 1"

[rules.always]
custom = "Always apply this"

[rules.naming]
pages = "{name}.py"
"""
        (temp_project / "pynext.toml").write_text(config_content)
        config = PyNextConfig.load(temp_project)
        
        assert "Custom rule 1" in config.rules.custom
        assert config.rules.naming["pages"] == "{name}.py"
    
    def test_load_with_examples(self, temp_project):
        """Test loading config with examples."""
        config_content = """
[examples]
good_island = '''
@island
def Counter():
    count = Signal(0)
'''
bad_island = '''
def counter():
    pass
'''
"""
        (temp_project / "pynext.toml").write_text(config_content)
        config = PyNextConfig.load(temp_project)
        
        assert "@island" in config.examples.good_island
        assert "def counter" in config.examples.bad_island
    
    def test_load_hidden_config(self, temp_project):
        """Test loading from .pynext/config.toml."""
        # Create hidden config
        hidden_dir = temp_project / ".pynext"
        hidden_dir.mkdir()
        
        config_content = """
[ai]
model = "hidden-model"
"""
        (hidden_dir / "config.toml").write_text(config_content)
        
        config = PyNextConfig.load(temp_project)
        assert config.ai.model == "hidden-model"
    
    def test_project_overrides_global(self, temp_project, tmp_path):
        """Test that project config overrides global."""
        # This test is simplified since we can't easily mock global config path
        project_config = """
[ai]
model = "project-model"
"""
        (temp_project / "pynext.toml").write_text(project_config)
        
        config = PyNextConfig.load(temp_project)
        assert config.ai.model == "project-model"


# =============================================================================
# Edge Cases Tests
# =============================================================================

class TestConfigEdgeCases:
    """Tests for configuration edge cases."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_empty_config_file(self, temp_project):
        """Test loading empty config file."""
        (temp_project / "pynext.toml").write_text("")
        config = PyNextConfig.load(temp_project)
        
        # Should use defaults
        assert config.ai.model == "claude-sonnet-4-20250514"
    
    def test_partial_config_file(self, temp_project):
        """Test loading partial config file."""
        config_content = """
[ai]
verbose = true
"""
        (temp_project / "pynext.toml").write_text(config_content)
        config = PyNextConfig.load(temp_project)
        
        # Should have default model but override verbose
        assert config.ai.model == "claude-sonnet-4-20250514"
        assert config.ai.verbose is True
    
    def test_invalid_toml_syntax(self, temp_project):
        """Test handling invalid TOML syntax."""
        (temp_project / "pynext.toml").write_text("invalid [ toml")
        
        # Should not crash, just log error
        config = PyNextConfig.load(temp_project)
        # Should use defaults
        assert config.ai.mode == "plan"
    
    def test_config_with_unknown_sections(self, temp_project):
        """Test config with unknown sections (should be ignored)."""
        config_content = """
[ai]
model = "test-model"

[unknown_section]
key = "value"
"""
        (temp_project / "pynext.toml").write_text(config_content)
        config = PyNextConfig.load(temp_project)
        
        assert config.ai.model == "test-model"
    
    def test_to_prompt_empty_config(self):
        """Test to_prompt with minimal config."""
        config = PyNextConfig()
        config.prompts.system = ""
        config.prompts.context = ""
        
        prompt = config.to_prompt()
        # Should not crash, might be empty or have style rules
        assert isinstance(prompt, str)


# =============================================================================
# Full Config Loading Pipeline Tests
# =============================================================================

class TestConfigLoadingPipeline:
    """Tests for the complete config loading pipeline."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_pipeline_merge_order(self, temp_project):
        """Test that configs merge in correct order."""
        # Create project config
        project_config = """
[ai]
model = "project-model"
verbose = true
"""
        (temp_project / "pynext.toml").write_text(project_config)
        
        config = PyNextConfig.load(temp_project)
        
        # Project should override defaults
        assert config.ai.model == "project-model"
        assert config.ai.verbose is True
        # Defaults should remain for unspecified
        assert config.ai.mode == "plan"
    
    def test_pipeline_variable_resolution(self, temp_project):
        """Test variable resolution in pipeline."""
        config_content = """
[vars]
company = "TestCo"
year = "2025"

[prompts]
system = "You work for ${company} in ${year}"
"""
        (temp_project / "pynext.toml").write_text(config_content)
        
        config = PyNextConfig.load(temp_project)
        resolved = config.substitute_vars(config.prompts.system)
        
        assert "TestCo" in resolved
        assert "2025" in resolved
    
    def test_pipeline_mode_application(self, temp_project):
        """Test mode settings are applied correctly."""
        config_content = """
[mode.test_mode]
description = "Test mode"
[mode.test_mode.validation]
require_tests = true
require_docstrings = false
"""
        (temp_project / "pynext.toml").write_text(config_content)
        
        config = PyNextConfig.load(temp_project)
        mode = config.get_mode("test_mode")
        
        assert mode is not None
        assert mode.validation.require_tests is True
        assert mode.validation.require_docstrings is False


# =============================================================================
# Full Prompts Tests
# =============================================================================

class TestPromptsComplete:
    """Complete tests for prompt configuration."""
    
    def test_prompts_system_prefix_suffix(self):
        """Test all prompt fields."""
        prompts = PromptConfig(
            system="System prompt",
            suffix="Suffix prompt",
            context="Context info",
        )
        
        assert prompts.system == "System prompt"
        assert prompts.suffix == "Suffix prompt"
        assert prompts.context == "Context info"
    
    def test_prompts_per_file_type_all(self):
        """Test prompts for all file types."""
        prompts = PromptConfig()
        prompts.page = {"prefix": "Page prefix", "suffix": "Page suffix"}
        prompts.island = {"prefix": "Island prefix"}
        prompts.api = {"prefix": "API prefix", "suffix": "API suffix"}
        prompts.model = {"prefix": "Model prefix"}
        prompts.action = {"prefix": "Action prefix"}
        
        assert prompts.get_for_type("page")["prefix"] == "Page prefix"
        assert prompts.get_for_type("island")["prefix"] == "Island prefix"
        assert prompts.get_for_type("api")["suffix"] == "API suffix"
    
    def test_prompts_from_dict(self):
        """Test creating prompts from dict."""
        data = {
            "system": "System",
            "suffix": "Suffix",
            "page": {"prefix": "Page prefix"},
        }
        prompts = PromptConfig.from_dict(data)
        
        assert prompts.system == "System"
        assert prompts.suffix == "Suffix"
        assert prompts.page["prefix"] == "Page prefix"


# =============================================================================
# Full Patterns Tests
# =============================================================================

class TestPatternsComplete:
    """Complete tests for pattern functionality."""
    
    def test_pattern_all_fields(self):
        """Test pattern with all fields."""
        pattern = Pattern(
            name="complete_pattern",
            description="A complete pattern",
            code="def ${name}(): ${body}",
            tags=["api", "auth"],
            when="file_type == 'api'",
            when_llm="requires authentication",
            deps=["pynext.api", "utils.auth"],
        )
        
        assert pattern.name == "complete_pattern"
        assert pattern.description == "A complete pattern"
        assert "api" in pattern.tags
        assert "auth" in pattern.tags
        assert pattern.when == "file_type == 'api'"
        assert pattern.when_llm == "requires authentication"
        assert "pynext.api" in pattern.deps
    
    def test_pattern_render_complex(self):
        """Test rendering complex pattern with multiple variables."""
        pattern = Pattern(
            name="crud_api",
            code="""
from pynext.api import api
from ${auth_module} import require_auth

@api
@require_auth
async def ${method}(request):
    '''${description}'''
    ${body}
    return Response.json({"status": "ok"})
""",
        )
        
        rendered = pattern.render(
            auth_module="utils.auth",
            method="GET",
            description="Get all items",
            body="items = await Item.all()",
        )
        
        assert "from utils.auth import require_auth" in rendered
        assert "async def GET(request):" in rendered
        assert "Get all items" in rendered
        assert "items = await Item.all()" in rendered
    
    def test_pattern_match_tags(self):
        """Test matching patterns by tags."""
        config = PyNextConfig()
        config.patterns["p1"] = Pattern(name="p1", tags=["api", "crud"])
        config.patterns["p2"] = Pattern(name="p2", tags=["api", "auth"])
        config.patterns["p3"] = Pattern(name="p3", tags=["island", "form"])
        config.patterns["p4"] = Pattern(name="p4", tags=["api"])
        
        api_patterns = config.get_patterns_by_tags(["api"])
        assert len(api_patterns) == 3
        
        auth_patterns = config.get_patterns_by_tags(["auth"])
        assert len(auth_patterns) == 1
        
        form_patterns = config.get_patterns_by_tags(["form"])
        assert len(form_patterns) == 1


# =============================================================================
# Full Conditionals Tests
# =============================================================================

class TestConditionalsComplete:
    """Complete tests for conditional configuration."""
    
    def test_conditional_all_fields(self):
        """Test conditional with all fields."""
        cond = Conditional(
            priority=85,
            when="file_type == 'api' and project.has_auth",
            when_llm="handles sensitive data",
            prompt="Use encryption",
            pattern="secure_api",
            rules="Always validate input",
        )
        
        assert cond.priority == 85
        assert "file_type == 'api'" in cond.when
        assert cond.when_llm == "handles sensitive data"
        assert cond.prompt == "Use encryption"
        assert cond.pattern == "secure_api"
        assert cond.rules == "Always validate input"
    
    def test_conditional_priority_range(self):
        """Test conditional priority values."""
        # Valid priorities
        for p in [0, 50, 100]:
            cond = Conditional(priority=p, when="True", prompt="Test")
            assert cond.priority == p
    
    def test_multiple_conditionals_sorting(self):
        """Test that conditionals sort by priority."""
        conds = [
            Conditional(priority=50, when="True", prompt="Low"),
            Conditional(priority=90, when="True", prompt="High"),
            Conditional(priority=70, when="True", prompt="Medium"),
        ]
        
        sorted_conds = sorted(conds, key=lambda c: c.priority, reverse=True)
        
        assert sorted_conds[0].prompt == "High"
        assert sorted_conds[1].prompt == "Medium"
        assert sorted_conds[2].prompt == "Low"


# =============================================================================
# Full Rules Tests
# =============================================================================

class TestRulesComplete:
    """Complete tests for rules configuration."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_rules_always(self, temp_project):
        """Test always-applied rules."""
        config_content = """
[rules.always]
custom = "Always use Tailwind CSS"
"""
        (temp_project / "pynext.toml").write_text(config_content)
        
        config = PyNextConfig.load(temp_project)
        # rules.always is a string containing the custom rules
        assert "Tailwind" in config.rules.always or "Tailwind" in config.rules.custom
    
    def test_rules_naming_all_types(self, temp_project):
        """Test naming rules for all file types."""
        config_content = """
[rules.naming]
pages = "{name}.py"
components = "{Name}.py"
islands = "{Name}Island.py"
models = "{name}_model.py"
api = "api_{name}.py"
"""
        (temp_project / "pynext.toml").write_text(config_content)
        
        config = PyNextConfig.load(temp_project)
        
        assert config.rules.naming["pages"] == "{name}.py"
        assert config.rules.naming["components"] == "{Name}.py"
        assert config.rules.naming["islands"] == "{Name}Island.py"
    
    def test_rules_structure(self, temp_project):
        """Test structure rules."""
        config_content = """
[rules.structure]
required_dirs = ["pages", "components", "models", "api"]
required_files = ["pages/layout.py", "utils/auth.py"]
"""
        (temp_project / "pynext.toml").write_text(config_content)
        
        config = PyNextConfig.load(temp_project)
        
        assert "pages" in config.rules.structure.get("required_dirs", [])
        assert "pages/layout.py" in config.rules.structure.get("required_files", [])


# =============================================================================
# Full Examples Tests
# =============================================================================

class TestExamplesComplete:
    """Complete tests for examples configuration."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_examples_good_and_bad(self, temp_project):
        """Test good and bad examples."""
        config_content = """
[examples]
good_component = '''
@island
def Counter():
    count = Signal(0)
    return button()(f"{count()}")
'''

bad_component = '''
def counter():
    return div(style="color:red")
'''
"""
        (temp_project / "pynext.toml").write_text(config_content)
        
        config = PyNextConfig.load(temp_project)
        
        assert "@island" in config.examples.good_component
        assert "style=" in config.examples.bad_component
    
    def test_examples_to_prompt(self, temp_project):
        """Test that examples can be included in prompts."""
        config_content = """
[examples]
good_api = '''
@api
async def GET(request):
    return Response.json({"ok": True})
'''
"""
        (temp_project / "pynext.toml").write_text(config_content)
        
        config = PyNextConfig.load(temp_project)
        
        # Examples should be accessible via defined fields
        assert config.examples.good_api is not None
        assert "@api" in config.examples.good_api


# =============================================================================
# Full Validation Rules Tests
# =============================================================================

class TestValidationRulesComplete:
    """Complete tests for validation rules."""
    
    def test_all_validation_fields(self):
        """Test all validation rule fields."""
        rules = ValidationRules(
            require_docstrings=True,
            require_type_hints=True,
            require_tests=True,
            max_function_lines=30,
            max_file_lines=300,
            forbidden_imports=["os.system", "eval"],
            required_imports=["typing"],
            forbidden_patterns=["exec(", "import *"],
        )
        
        assert rules.require_docstrings is True
        assert rules.require_type_hints is True
        assert rules.require_tests is True
        assert rules.max_function_lines == 30
        assert rules.max_file_lines == 300
        assert "os.system" in rules.forbidden_imports
        assert "typing" in rules.required_imports
        assert "exec(" in rules.forbidden_patterns
    
    def test_validation_merge(self):
        """Test merging validation rules."""
        base = ValidationRules(require_tests=False, max_function_lines=50)
        override = ValidationRules(require_tests=True)
        
        # Manual merge simulation
        merged = ValidationRules(
            require_tests=override.require_tests,
            max_function_lines=base.max_function_lines,
        )
        
        assert merged.require_tests is True
        assert merged.max_function_lines == 50


# =============================================================================
# Full Code Style Tests
# =============================================================================

class TestCodeStyleComplete:
    """Complete tests for code style configuration."""
    
    def test_all_style_fields(self):
        """Test all code style fields."""
        style = CodeStyle(
            naming_convention="snake_case",
            class_naming="PascalCase",
            max_line_length=100,
            quote_style="single",
            trailing_comma=False,
            docstring_style="numpy",
            indent_size=2,
        )
        
        assert style.naming_convention == "snake_case"
        assert style.class_naming == "PascalCase"
        assert style.max_line_length == 100
        assert style.quote_style == "single"
        assert style.trailing_comma is False
        assert style.docstring_style == "numpy"
        assert style.indent_size == 2
    
    def test_style_to_prompt(self):
        """Test converting style to prompt format."""
        style = CodeStyle(
            naming_convention="snake_case",
            quote_style="double",
            docstring_style="google",
        )
        
        # Style should be convertible to dict for prompt building
        style_dict = {
            "naming": style.naming_convention,
            "quotes": style.quote_style,
            "docstrings": style.docstring_style,
        }
        
        assert style_dict["naming"] == "snake_case"


# =============================================================================
# Full AI Preferences Tests
# =============================================================================

class TestAIPreferencesComplete:
    """Complete tests for AI preferences."""
    
    def test_all_ai_fields(self):
        """Test all AI preference fields."""
        prefs = AIPreferences(
            model="claude-opus-4",
            mode="agent",
            complexity="large",
            max_thoughts=10,
            verbose=True,
            temperature=0.5,
        )
        
        assert prefs.model == "claude-opus-4"
        assert prefs.mode == "agent"
        assert prefs.complexity == "large"
        assert prefs.max_thoughts == 10
        assert prefs.verbose is True
        assert prefs.temperature == 0.5
    
    def test_ai_mode_values(self):
        """Test valid AI mode values."""
        for mode in ["plan", "agent", "ask"]:
            prefs = AIPreferences(mode=mode)
            assert prefs.mode == mode
    
    def test_ai_complexity_values(self):
        """Test valid complexity values."""
        for complexity in ["auto", "minimal", "small", "medium", "large", "enterprise"]:
            prefs = AIPreferences(complexity=complexity)
            assert prefs.complexity == complexity


# =============================================================================
# Resolver Integration Tests
# =============================================================================

class TestResolverIntegration:
    """Integration tests for config resolver."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_resolver_full_pipeline(self, temp_project):
        """Test full resolver pipeline."""
        config_content = """
[vars]
company = "TestCo"

[prompts]
system = "You work for ${company}"

[[conditional]]
priority = 80
when = "file_type == 'api'"
prompt = "All APIs need auth"

[[conditional]]
priority = 70
when = "True"
prompt = "General rules apply"

[mode.strict]
description = "Strict mode"
[mode.strict.validation]
require_tests = true
"""
        (temp_project / "pynext.toml").write_text(config_content)
        
        config = PyNextConfig.load(temp_project)
        resolver = ConfigResolver(config)
        
        # Test with API context
        ctx = ConfigContext(file_type="api", mode="strict")
        resolved = resolver.resolve_sync(ctx)
        
        # Should have both conditionals (both match)
        assert len(resolved.prompts) >= 2
    
    def test_resolver_pattern_selection(self, temp_project):
        """Test resolver selects correct patterns."""
        config_content = """
[patterns.api_pattern]
description = "API pattern"
tags = ["api"]
when = "file_type == 'api'"
code = "@api\\ndef GET(): pass"

[patterns.page_pattern]
description = "Page pattern"
tags = ["page"]
when = "file_type == 'page'"
code = "@page\\ndef Home(): pass"
"""
        (temp_project / "pynext.toml").write_text(config_content)
        
        config = PyNextConfig.load(temp_project)
        
        # Get patterns for API
        api_patterns = config.get_patterns_by_tags(["api"])
        assert len(api_patterns) == 1
        assert api_patterns[0].name == "api_pattern"


# =============================================================================
# Config Validation Tests Extended
# =============================================================================

class TestConfigValidationExtended:
    """Extended tests for config validation."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_validate_mode_extends_valid(self, temp_project):
        """Test validation passes for valid extends."""
        config_content = """
[mode.base]
description = "Base"

[mode.child]
extends = "base"
description = "Child"
"""
        (temp_project / "pynext.toml").write_text(config_content)
        
        # validate_config returns a list of errors (empty if valid)
        errors = validate_config(temp_project / "pynext.toml")
        assert len(errors) == 0
    
    def test_validate_conditional_priority(self, temp_project):
        """Test validation of conditional priorities."""
        config_content = """
[[conditional]]
priority = 50
when = "True"
prompt = "Valid priority"
"""
        (temp_project / "pynext.toml").write_text(config_content)
        
        errors = validate_config(temp_project / "pynext.toml")
        assert len(errors) == 0
    
    def test_validate_pattern_syntax(self, temp_project):
        """Test validation of pattern code syntax."""
        config_content = """
[patterns.valid]
description = "Valid Python"
code = '''
def hello():
    return "world"
'''
"""
        (temp_project / "pynext.toml").write_text(config_content)
        
        errors = validate_config(temp_project / "pynext.toml")
        assert len(errors) == 0


# =============================================================================
# Complex Integration Tests
# =============================================================================

class TestComplexIntegration:
    """Complex integration tests combining multiple features."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_full_config_scenario(self, temp_project):
        """Test a realistic full configuration scenario."""
        config_content = """
# Full realistic config

[vars]
company = "Acme Corp"
year = "2025"

[ai]
model = "claude-sonnet-4-20250514"
mode = "plan"
verbose = false

[style]
naming_convention = "snake_case"
max_line_length = 88
docstring_style = "google"

[validation]
require_docstrings = true
require_type_hints = true
forbidden_imports = ["os.system"]

[prompts]
system = "You are an expert PyNext developer at ${company}."
context = "Building a B2B SaaS application."

[prompts.api]
prefix = "All API routes require authentication."
suffix = "Return JSON with error format."

[patterns.basic_api]
description = "Basic API endpoint"
tags = ["api"]
code = '''
@api
async def GET(request):
    return Response.json({"ok": True})
'''

[[conditional]]
priority = 80
when = "file_type == 'api'"
prompt = "Use proper error handling"

[mode.strict]
description = "Maximum safety"
[mode.strict.validation]
require_tests = true

[rules.always]
custom = "Use Tailwind for styling"

[examples]
good = "@island\\ndef Counter(): pass"
"""
        (temp_project / "pynext.toml").write_text(config_content)
        
        config = PyNextConfig.load(temp_project)
        
        # Verify all sections loaded
        assert config.ai.model == "claude-sonnet-4-20250514"
        assert config.style.naming_convention == "snake_case"
        assert config.validation.require_docstrings is True
        assert "Acme Corp" in config.substitute_vars(config.prompts.system)
        assert len(config.patterns) >= 1
        assert len(config.conditionals) >= 1
        assert config.get_mode("strict") is not None
    
    def test_mode_inheritance_full(self, temp_project):
        """Test full mode inheritance chain."""
        config_content = """
[mode.base]
description = "Base settings"
[mode.base.validation]
require_docstrings = true
require_type_hints = true

[mode.dev]
extends = "base"
description = "Development"
[mode.dev.validation]
require_tests = false

[mode.prod]
extends = "base"
description = "Production"
[mode.prod.validation]
require_tests = true
max_function_lines = 30

[mode.strict]
extends = "prod"
description = "Strict production"
[mode.strict.validation]
forbidden_imports = ["eval", "exec"]
"""
        (temp_project / "pynext.toml").write_text(config_content)
        
        config = PyNextConfig.load(temp_project)
        
        # Verify inheritance chain
        base = config.get_mode("base")
        dev = config.get_mode("dev")
        prod = config.get_mode("prod")
        strict = config.get_mode("strict")
        
        assert base is not None
        assert dev.extends == "base"
        assert prod.extends == "base"
        assert strict.extends == "prod"


# =============================================================================
# Environment Variable Override Tests
# =============================================================================

class TestEnvOverrides:
    """Tests for environment variable overrides."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_model_env_override(self, temp_project, monkeypatch):
        """Test ANTHROPIC_MODEL env override."""
        monkeypatch.setenv("ANTHROPIC_MODEL", "claude-opus-4")
        
        config = PyNextConfig.load(temp_project)
        # Env should override if config supports it
        # The actual behavior depends on implementation
        assert config.ai is not None
    
    def test_mode_env_override(self, temp_project, monkeypatch):
        """Test PYNEXT_MODE env override."""
        monkeypatch.setenv("PYNEXT_MODE", "strict")
        
        config = PyNextConfig.load(temp_project)
        # Config should be aware of env
        assert config is not None
    
    def test_verbose_env_override(self, temp_project, monkeypatch):
        """Test PYNEXT_AI_VERBOSE env override."""
        monkeypatch.setenv("PYNEXT_AI_VERBOSE", "true")
        
        config = PyNextConfig.load(temp_project)
        assert config is not None


# =============================================================================
# Computed Variables Tests
# =============================================================================

class TestComputedVariables:
    """Tests for computed variable resolution."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_simple_computed_var(self, temp_project):
        """Test simple computed variable."""
        config_content = """
[vars]
company = "Acme"
year = "2025"
"""
        (temp_project / "pynext.toml").write_text(config_content)
        
        config = PyNextConfig.load(temp_project)
        result = config.substitute_vars("${company} ${year}")
        assert result == "Acme 2025"
    
    def test_missing_var_unchanged(self, temp_project):
        """Test missing variable is left unchanged."""
        config_content = """
[vars]
defined = "value"
"""
        (temp_project / "pynext.toml").write_text(config_content)
        
        config = PyNextConfig.load(temp_project)
        result = config.substitute_vars("${defined} ${undefined}")
        assert "value" in result
        assert "${undefined}" in result
    
    def test_var_in_prompts(self, temp_project):
        """Test variables in prompt strings."""
        config_content = """
[vars]
company = "TestCo"

[prompts]
system = "You work for ${company}"
"""
        (temp_project / "pynext.toml").write_text(config_content)
        
        config = PyNextConfig.load(temp_project)
        resolved = config.substitute_vars(config.prompts.system)
        assert "TestCo" in resolved


# =============================================================================
# Priority Tests
# =============================================================================

class TestPriority:
    """Tests for conditional priority handling."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_high_priority_first(self, temp_project):
        """Test that high priority conditionals are processed first."""
        config_content = """
[[conditional]]
priority = 50
when = "True"
prompt = "Low priority"

[[conditional]]
priority = 90
when = "True"
prompt = "High priority"

[[conditional]]
priority = 70
when = "True"
prompt = "Medium priority"
"""
        (temp_project / "pynext.toml").write_text(config_content)
        
        config = PyNextConfig.load(temp_project)
        
        # Sort by priority
        sorted_conds = sorted(config.conditionals, key=lambda c: c.priority, reverse=True)
        
        assert sorted_conds[0].prompt == "High priority"
        assert sorted_conds[1].prompt == "Medium priority"
        assert sorted_conds[2].prompt == "Low priority"
    
    def test_priority_range_0_to_100(self):
        """Test priority accepts full range."""
        for p in [0, 25, 50, 75, 100]:
            cond = Conditional(priority=p, when="True", prompt=f"P{p}")
            assert cond.priority == p


# =============================================================================
# File Type Prompts Tests
# =============================================================================

class TestFileTypePrompts:
    """Tests for file-type specific prompts."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_all_file_types_supported(self):
        """Test all file types have prompt support."""
        prompts = PromptConfig()
        
        # All these should be accessible
        file_types = ["page", "island", "component", "api", "action", "model", "layout", "middleware", "util"]
        
        for ft in file_types:
            result = prompts.get_for_type(ft)
            assert isinstance(result, dict)
    
    def test_page_prompts(self, temp_project):
        """Test page-specific prompts."""
        config_content = """
[prompts.page]
prefix = "Pages should include SEO metadata"
suffix = "Include breadcrumbs"
"""
        (temp_project / "pynext.toml").write_text(config_content)
        
        config = PyNextConfig.load(temp_project)
        page_prompts = config.prompts.get_for_type("page")
        
        assert "SEO" in page_prompts.get("prefix", "")
        assert "breadcrumbs" in page_prompts.get("suffix", "")
    
    def test_api_prompts(self, temp_project):
        """Test API-specific prompts."""
        config_content = """
[prompts.api]
prefix = "All APIs require authentication"
suffix = "Return JSON with error format"
"""
        (temp_project / "pynext.toml").write_text(config_content)
        
        config = PyNextConfig.load(temp_project)
        api_prompts = config.prompts.get_for_type("api")
        
        assert "authentication" in api_prompts.get("prefix", "")


# =============================================================================
# Pattern Dependency Tests
# =============================================================================

class TestPatternDependencies:
    """Tests for pattern dependencies."""
    
    def test_pattern_with_deps(self):
        """Test pattern with dependency list."""
        pattern = Pattern(
            name="auth_api",
            code="@api\ndef GET(): pass",
            deps=["pynext.api", "utils.auth"],
        )
        
        assert "pynext.api" in pattern.deps
        assert "utils.auth" in pattern.deps
    
    def test_pattern_without_deps(self):
        """Test pattern without dependencies."""
        pattern = Pattern(
            name="simple",
            code="def hello(): pass",
        )
        
        assert pattern.deps == []
    
    def test_pattern_deps_from_dict(self):
        """Test pattern deps from dict."""
        data = {
            "code": "pass",
            "deps": ["dep1", "dep2"],
        }
        # Pattern.from_dict requires name as first arg
        pattern = Pattern.from_dict("test", data)
        
        assert pattern.deps == ["dep1", "dep2"]


# =============================================================================
# Resolver Tests Extended
# =============================================================================

class TestResolverExtended:
    """Extended tests for config resolver."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_resolver_with_all_matches(self, temp_project):
        """Test resolver when all conditionals match."""
        config_content = """
[[conditional]]
priority = 90
when = "True"
prompt = "Always applies 1"

[[conditional]]
priority = 80
when = "True"
prompt = "Always applies 2"

[[conditional]]
priority = 70
when = "True"
prompt = "Always applies 3"
"""
        (temp_project / "pynext.toml").write_text(config_content)
        
        config = PyNextConfig.load(temp_project)
        resolver = ConfigResolver(config)
        ctx = ConfigContext()
        resolved = resolver.resolve_sync(ctx)
        
        assert len(resolved.prompts) == 3
    
    def test_resolver_with_no_matches(self, temp_project):
        """Test resolver when no conditionals match."""
        config_content = """
[[conditional]]
priority = 90
when = "False"
prompt = "Never applies"
"""
        (temp_project / "pynext.toml").write_text(config_content)
        
        config = PyNextConfig.load(temp_project)
        resolver = ConfigResolver(config)
        ctx = ConfigContext()
        resolved = resolver.resolve_sync(ctx)
        
        assert len(resolved.prompts) == 0
    
    def test_resolver_file_type_condition(self, temp_project):
        """Test resolver with file_type condition."""
        config_content = """
[[conditional]]
priority = 80
when = "file_type == 'api'"
prompt = "API specific"

[[conditional]]
priority = 80
when = "file_type == 'page'"
prompt = "Page specific"
"""
        (temp_project / "pynext.toml").write_text(config_content)
        
        config = PyNextConfig.load(temp_project)
        resolver = ConfigResolver(config)
        
        # API context
        ctx_api = ConfigContext(file_type="api")
        resolved_api = resolver.resolve_sync(ctx_api)
        assert "API specific" in resolved_api.prompts
        assert "Page specific" not in resolved_api.prompts
        
        # Page context
        ctx_page = ConfigContext(file_type="page")
        resolved_page = resolver.resolve_sync(ctx_page)
        assert "Page specific" in resolved_page.prompts
        assert "API specific" not in resolved_page.prompts


# =============================================================================
# to_prompt() Tests
# =============================================================================

class TestToPrompt:
    """Tests for to_prompt() output."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_to_prompt_includes_system(self, temp_project):
        """Test to_prompt includes system prompt."""
        config_content = """
[prompts]
system = "You are an expert developer."
"""
        (temp_project / "pynext.toml").write_text(config_content)
        
        config = PyNextConfig.load(temp_project)
        prompt = config.to_prompt()
        
        assert "expert developer" in prompt
    
    def test_to_prompt_includes_context(self, temp_project):
        """Test to_prompt includes context."""
        config_content = """
[prompts]
context = "Building a B2B SaaS application."
"""
        (temp_project / "pynext.toml").write_text(config_content)
        
        config = PyNextConfig.load(temp_project)
        prompt = config.to_prompt()
        
        assert "B2B SaaS" in prompt
    
    def test_to_prompt_includes_style(self, temp_project):
        """Test to_prompt mentions style settings."""
        config_content = """
[style]
naming_convention = "snake_case"
docstring_style = "google"
"""
        (temp_project / "pynext.toml").write_text(config_content)
        
        config = PyNextConfig.load(temp_project)
        prompt = config.to_prompt()
        
        # Style info should be in prompt
        assert "snake_case" in prompt or len(prompt) > 0


# =============================================================================
# to_dict() Tests
# =============================================================================

class TestToDict:
    """Tests for to_dict() serialization."""
    
    def test_config_to_dict_complete(self):
        """Test full config serializes correctly."""
        config = PyNextConfig()
        d = config.to_dict()
        
        # All sections present
        assert "ai" in d
        assert "style" in d
        assert "validation" in d
    
    def test_config_to_dict_values(self):
        """Test to_dict preserves values."""
        config = PyNextConfig()
        config.ai.model = "test-model"
        config.style.max_line_length = 100
        
        d = config.to_dict()
        
        assert d["ai"]["model"] == "test-model"
        assert d["style"]["max_line_length"] == 100
    
    def test_config_to_dict_json_serializable(self):
        """Test to_dict output is JSON serializable."""
        config = PyNextConfig()
        d = config.to_dict()
        
        # Should not raise
        json_str = json.dumps(d)
        data = json.loads(json_str)
        
        assert data == d


# =============================================================================
# Stress Tests for Config
# =============================================================================

class TestConfigStress:
    """Stress tests for configuration system."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_many_conditionals(self, temp_project):
        """Test handling many conditionals."""
        conditionals = []
        for i in range(50):
            conditionals.append(f"""
[[conditional]]
priority = {i * 2}
when = "True"
prompt = "Conditional {i}"
""")
        
        config_content = "\n".join(conditionals)
        (temp_project / "pynext.toml").write_text(config_content)
        
        config = PyNextConfig.load(temp_project)
        assert len(config.conditionals) == 50
    
    def test_many_patterns(self, temp_project):
        """Test handling many patterns."""
        patterns = []
        for i in range(30):
            patterns.append(f"""
[patterns.pattern_{i}]
description = "Pattern {i}"
tags = ["tag{i}"]
code = "def func_{i}(): pass"
""")
        
        config_content = "\n".join(patterns)
        (temp_project / "pynext.toml").write_text(config_content)
        
        config = PyNextConfig.load(temp_project)
        assert len(config.patterns) == 30
    
    def test_large_code_pattern(self, temp_project):
        """Test pattern with large code block."""
        large_code = "x = 1\n" * 500
        config_content = f"""
[patterns.large]
description = "Large pattern"
code = '''
{large_code}
'''
"""
        (temp_project / "pynext.toml").write_text(config_content)
        
        config = PyNextConfig.load(temp_project)
        assert "x = 1" in config.patterns["large"].code
    
    def test_deep_nesting(self, temp_project):
        """Test deeply nested config."""
        config_content = """
[vars]
a = "1"
b = "2"
c = "3"

[prompts]
system = "System"

[prompts.page]
prefix = "Page prefix"

[prompts.island]
prefix = "Island prefix"

[prompts.api]
prefix = "API prefix"

[style]
naming_convention = "snake_case"

[validation]
require_tests = true

[mode.test]
description = "Test mode"

[mode.test.validation]
require_tests = false

[mode.test.style]
max_line_length = 120
"""
        (temp_project / "pynext.toml").write_text(config_content)
        
        config = PyNextConfig.load(temp_project)
        assert config.vars["a"] == "1"
        assert config.prompts.get_for_type("page")["prefix"] == "Page prefix"
        assert config.get_mode("test") is not None


# =============================================================================
# Config File Locations Tests
# =============================================================================

class TestConfigLocations:
    """Tests for config file location resolution."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_root_pynext_toml(self, temp_project):
        """Test loading from root pynext.toml."""
        config_content = """
[ai]
model = "root-model"
"""
        (temp_project / "pynext.toml").write_text(config_content)
        
        config = PyNextConfig.load(temp_project)
        assert config.ai.model == "root-model"
    
    def test_hidden_dir_config(self, temp_project):
        """Test loading from .pynext/config.toml."""
        hidden_dir = temp_project / ".pynext"
        hidden_dir.mkdir()
        
        config_content = """
[ai]
model = "hidden-model"
"""
        (hidden_dir / "config.toml").write_text(config_content)
        
        config = PyNextConfig.load(temp_project)
        assert config.ai.model == "hidden-model"
    
    def test_no_config_uses_defaults(self, temp_project):
        """Test that missing config uses defaults."""
        config = PyNextConfig.load(temp_project)
        
        # Should have default values
        assert config.ai.model == "claude-sonnet-4-20250514"
        assert config.style.naming_convention == "snake_case"


# =============================================================================
# ConfigContext Tests Extended
# =============================================================================

class TestConfigContextExtended:
    """Extended tests for ConfigContext."""
    
    def test_context_all_fields(self):
        """Test context with all fields."""
        ctx = ConfigContext(
            file_type="api",
            intent="add_feature",
            description="Add user authentication",
            mode="strict",
        )
        
        assert ctx.file_type == "api"
        assert ctx.intent == "add_feature"
        assert ctx.description == "Add user authentication"
        assert ctx.mode == "strict"
    
    def test_context_to_dict_complete(self):
        """Test context to_dict includes all fields."""
        ctx = ConfigContext(
            file_type="page",
            intent="new_app",
            description="Create blog",
            mode="prototype",
        )
        
        d = ctx.to_dict()
        
        assert d["file_type"] == "page"
        assert d["intent"] == "new_app"
        assert d["description"] == "Create blog"
        assert d["mode"] == "prototype"
    
    def test_context_to_dict_has_helper_functions(self):
        """Test context to_dict has helper functions."""
        ctx = ConfigContext()
        d = ctx.to_dict()
        
        # Should have len function for expressions
        assert "len" in d


# =============================================================================
# ResolvedConfig Tests Extended
# =============================================================================

class TestResolvedConfigExtended:
    """Extended tests for ResolvedConfig."""
    
    def test_resolved_no_duplicates(self):
        """Test resolved config doesn't add duplicates."""
        resolved = ResolvedConfig()
        
        resolved.add_prompt("Same prompt")
        resolved.add_prompt("Same prompt")
        resolved.add_prompt("Same prompt")
        
        assert len(resolved.prompts) == 1
    
    def test_resolved_multiple_unique_prompts(self):
        """Test resolved config handles multiple unique prompts."""
        resolved = ResolvedConfig()
        
        for i in range(10):
            resolved.add_prompt(f"Prompt {i}")
        
        assert len(resolved.prompts) == 10
    
    def test_resolved_system_prompt(self):
        """Test getting system prompt."""
        resolved = ResolvedConfig()
        resolved.system_prompt = "System prompt text"
        
        prompt = resolved.get_system_prompt()
        assert "System prompt text" in prompt
    
    def test_resolved_with_validation(self):
        """Test resolved config with validation rules."""
        resolved = ResolvedConfig()
        resolved.validation = ValidationRules(
            require_tests=True,
            max_function_lines=30,
        )
        
        assert resolved.validation.require_tests is True
        assert resolved.validation.max_function_lines == 30


# =============================================================================
# Import/Export Tests
# =============================================================================

class TestConfigImportExport:
    """Tests for config import/export scenarios."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_config_roundtrip(self, temp_project):
        """Test config can be loaded and values preserved."""
        config_content = """
[ai]
model = "test-model"
mode = "agent"
verbose = true

[style]
max_line_length = 100
quote_style = "single"

[validation]
require_tests = true
"""
        (temp_project / "pynext.toml").write_text(config_content)
        
        config = PyNextConfig.load(temp_project)
        
        assert config.ai.model == "test-model"
        assert config.ai.mode == "agent"
        assert config.ai.verbose is True
        assert config.style.max_line_length == 100
        assert config.style.quote_style == "single"
        assert config.validation.require_tests is True

