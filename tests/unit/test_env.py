"""
Unit tests for environment variable system.

Tests cover:
- File loading and parsing
- Simple getters with type conversion
- Schema validation
- Client-side exposure
- CLI commands
"""

import pytest
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock


# ============================================
# Loader Tests (20 tests)
# ============================================

class TestEnvLoader:
    """Tests for pynext.env.loader."""
    
    def test_parse_simple_env(self, tmp_path):
        """Parse basic KEY=value format."""
        from pynext.env.loader import parse_env_file
        
        env_file = tmp_path / ".env"
        env_file.write_text("DATABASE_URL=postgres://localhost/db\nPORT=8000")
        
        result = parse_env_file(env_file)
        
        assert result["DATABASE_URL"] == "postgres://localhost/db"
        assert result["PORT"] == "8000"
    
    def test_parse_quoted_values(self, tmp_path):
        """Parse quoted values."""
        from pynext.env.loader import parse_env_file
        
        env_file = tmp_path / ".env"
        env_file.write_text('API_KEY="secret-with-spaces"\nNAME=\'single quotes\'')
        
        result = parse_env_file(env_file)
        
        assert result["API_KEY"] == "secret-with-spaces"
        assert result["NAME"] == "single quotes"
    
    def test_parse_comments(self, tmp_path):
        """Skip comment lines."""
        from pynext.env.loader import parse_env_file
        
        env_file = tmp_path / ".env"
        env_file.write_text("# This is a comment\nVALID=yes\n# Another comment")
        
        result = parse_env_file(env_file)
        
        assert "This" not in result
        assert result["VALID"] == "yes"
    
    def test_parse_inline_comments(self, tmp_path):
        """Handle inline comments."""
        from pynext.env.loader import parse_env_file
        
        env_file = tmp_path / ".env"
        env_file.write_text("PORT=8000 # default port")
        
        result = parse_env_file(env_file)
        
        assert result["PORT"] == "8000"
    
    def test_parse_empty_lines(self, tmp_path):
        """Skip empty lines."""
        from pynext.env.loader import parse_env_file
        
        env_file = tmp_path / ".env"
        env_file.write_text("A=1\n\n\nB=2\n")
        
        result = parse_env_file(env_file)
        
        assert result["A"] == "1"
        assert result["B"] == "2"
    
    def test_parse_empty_value(self, tmp_path):
        """Handle empty values."""
        from pynext.env.loader import parse_env_file
        
        env_file = tmp_path / ".env"
        env_file.write_text("EMPTY=\nNOT_EMPTY=value")
        
        result = parse_env_file(env_file)
        
        assert result["EMPTY"] == ""
        assert result["NOT_EMPTY"] == "value"
    
    def test_expand_variables(self):
        """Expand ${VAR} references."""
        from pynext.env.loader import expand_variables
        
        vars = {
            "BASE_URL": "http://localhost",
            "API_URL": "${BASE_URL}/api",
        }
        
        result = expand_variables(vars)
        
        assert result["API_URL"] == "http://localhost/api"
    
    def test_expand_nested_variables(self):
        """Expand nested variable references."""
        from pynext.env.loader import expand_variables
        
        vars = {
            "HOST": "localhost",
            "PORT": "8000",
            "BASE": "http://${HOST}:${PORT}",
            "API": "${BASE}/api",
        }
        
        result = expand_variables(vars)
        
        assert result["BASE"] == "http://localhost:8000"
        assert result["API"] == "http://localhost:8000/api"
    
    def test_expand_unresolved_variable(self):
        """Keep unresolved variables as-is."""
        from pynext.env.loader import expand_variables
        
        vars = {
            "URL": "${UNDEFINED}/path",
        }
        
        result = expand_variables(vars)
        
        assert result["URL"] == "${UNDEFINED}/path"
    
    def test_load_env_files_order(self, tmp_path):
        """Load files in correct priority order."""
        from pynext.env.loader import load_env_files
        
        # Create files with same key, different values
        (tmp_path / ".env").write_text("KEY=base")
        (tmp_path / ".env.local").write_text("KEY=local")
        (tmp_path / ".env.development").write_text("KEY=dev")
        
        result = load_env_files(tmp_path, "development")
        
        # .env.development should override .env.local which overrides .env
        assert result["KEY"] == "dev"
    
    def test_load_env_files_mode_specific(self, tmp_path):
        """Load mode-specific files."""
        from pynext.env.loader import load_env_files
        
        (tmp_path / ".env").write_text("KEY=base")
        (tmp_path / ".env.production").write_text("KEY=prod")
        
        result = load_env_files(tmp_path, "production")
        
        assert result["KEY"] == "prod"
    
    def test_load_env_files_os_override(self, tmp_path):
        """OS environment overrides files."""
        from pynext.env.loader import load_env_files
        
        (tmp_path / ".env").write_text("KEY=file")
        
        with patch.dict(os.environ, {"KEY": "os_value"}):
            result = load_env_files(tmp_path, "development")
        
        assert result["KEY"] == "os_value"
    
    def test_load_nonexistent_files(self, tmp_path):
        """Handle missing env files gracefully."""
        from pynext.env.loader import load_env_files
        
        # No env files exist
        result = load_env_files(tmp_path, "development")
        
        # Should still return dict (with OS environ)
        assert isinstance(result, dict)
    
    def test_get_env_files_info(self, tmp_path):
        """Get info about env files."""
        from pynext.env.loader import get_env_files_info
        
        (tmp_path / ".env").write_text("A=1\nB=2")
        (tmp_path / ".env.development").write_text("C=3")
        
        info = get_env_files_info(tmp_path, "development")
        
        assert len(info) == 4  # .env, .env.local, .env.development, .env.development.local
        
        env_info = next(i for i in info if i["name"] == ".env")
        assert env_info["exists"] is True
        assert env_info["vars"] == 2
        
        local_info = next(i for i in info if i["name"] == ".env.local")
        assert local_info["exists"] is False
    
    def test_parse_special_characters(self, tmp_path):
        """Handle special characters in values."""
        from pynext.env.loader import parse_env_file
        
        env_file = tmp_path / ".env"
        env_file.write_text('URL="https://example.com?foo=bar&baz=qux"')
        
        result = parse_env_file(env_file)
        
        assert result["URL"] == "https://example.com?foo=bar&baz=qux"
    
    def test_parse_equals_in_value(self, tmp_path):
        """Handle = in values."""
        from pynext.env.loader import parse_env_file
        
        env_file = tmp_path / ".env"
        env_file.write_text('CONNECTION="host=localhost;port=5432"')
        
        result = parse_env_file(env_file)
        
        assert result["CONNECTION"] == "host=localhost;port=5432"
    
    def test_parse_unicode(self, tmp_path):
        """Handle unicode characters."""
        from pynext.env.loader import parse_env_file
        
        env_file = tmp_path / ".env"
        env_file.write_text("GREETING=こんにちは\nEMOJI=🎉")
        
        result = parse_env_file(env_file)
        
        assert result["GREETING"] == "こんにちは"
        assert result["EMOJI"] == "🎉"
    
    def test_invalid_key_format(self, tmp_path):
        """Skip invalid key formats."""
        from pynext.env.loader import parse_env_file
        
        env_file = tmp_path / ".env"
        env_file.write_text("VALID=yes\n123INVALID=no\n-ALSO-INVALID=no")
        
        result = parse_env_file(env_file)
        
        assert "VALID" in result
        assert "123INVALID" not in result
        assert "-ALSO-INVALID" not in result
    
    def test_load_order_diagram(self):
        """Verify load order diagram exists."""
        from pynext.env.loader import get_load_order_diagram
        
        diagram = get_load_order_diagram()
        
        assert ".env" in diagram
        assert ".env.local" in diagram
        assert "OS Environment" in diagram


# ============================================
# Simple Getters Tests (15 tests)
# ============================================

class TestEnvGetters:
    """Tests for pynext.env_module.Env getters."""
    
    @pytest.fixture
    def mock_env(self, tmp_path):
        """Create a mock environment."""
        from pynext.env_module import Env
        
        # Reset singleton
        Env._instance = None
        Env._loaded = False
        Env._vars = {}
        
        # Create .env file
        env_file = tmp_path / ".env"
        env_file.write_text("""
DATABASE_URL=postgres://localhost/db
PORT=8000
DEBUG=true
RATE=1.5
HOSTS=localhost,example.com
CONFIG={"key": "value"}
PYNEXT_PUBLIC_API_URL=https://api.example.com
""")
        
        # Load env from temp dir
        env = Env()
        env._load(tmp_path)
        
        return env
    
    def test_get_str(self, mock_env):
        """Get string value."""
        result = mock_env.get_str("DATABASE_URL", "default")
        
        assert result == "postgres://localhost/db"
    
    def test_get_str_default(self, mock_env):
        """Get string with default."""
        result = mock_env.get_str("NONEXISTENT", "default")
        
        assert result == "default"
    
    def test_get_int(self, mock_env):
        """Get integer value."""
        result = mock_env.get_int("PORT", 3000)
        
        assert result == 8000
        assert isinstance(result, int)
    
    def test_get_int_default(self, mock_env):
        """Get integer with default."""
        result = mock_env.get_int("NONEXISTENT", 3000)
        
        assert result == 3000
    
    def test_get_int_invalid(self, mock_env):
        """Get integer with invalid value raises."""
        mock_env._vars["INVALID"] = "not-a-number"
        
        with pytest.raises(ValueError) as exc_info:
            mock_env.get_int("INVALID", 0)
        
        assert "must be an integer" in str(exc_info.value)
    
    def test_get_bool_true(self, mock_env):
        """Get boolean true values."""
        mock_env._vars["T1"] = "true"
        mock_env._vars["T2"] = "1"
        mock_env._vars["T3"] = "yes"
        mock_env._vars["T4"] = "on"
        
        assert mock_env.get_bool("T1") is True
        assert mock_env.get_bool("T2") is True
        assert mock_env.get_bool("T3") is True
        assert mock_env.get_bool("T4") is True
    
    def test_get_bool_false(self, mock_env):
        """Get boolean false values."""
        mock_env._vars["F1"] = "false"
        mock_env._vars["F2"] = "0"
        mock_env._vars["F3"] = "no"
        
        assert mock_env.get_bool("F1") is False
        assert mock_env.get_bool("F2") is False
        assert mock_env.get_bool("F3") is False
    
    def test_get_bool_default(self, mock_env):
        """Get boolean with default."""
        assert mock_env.get_bool("NONEXISTENT", True) is True
        assert mock_env.get_bool("NONEXISTENT", False) is False
    
    def test_get_float(self, mock_env):
        """Get float value."""
        result = mock_env.get_float("RATE", 1.0)
        
        assert result == 1.5
        assert isinstance(result, float)
    
    def test_get_list(self, mock_env):
        """Get list value."""
        result = mock_env.get_list("HOSTS", [])
        
        assert result == ["localhost", "example.com"]
    
    def test_get_list_custom_separator(self, mock_env):
        """Get list with custom separator."""
        mock_env._vars["ITEMS"] = "a|b|c"
        
        result = mock_env.get_list("ITEMS", [], separator="|")
        
        assert result == ["a", "b", "c"]
    
    def test_get_json(self, mock_env):
        """Get JSON value."""
        result = mock_env.get_json("CONFIG", {})
        
        assert result == {"key": "value"}
    
    def test_get_json_invalid(self, mock_env):
        """Get JSON with invalid value raises."""
        mock_env._vars["INVALID"] = "not-json"
        
        with pytest.raises(ValueError) as exc_info:
            mock_env.get_json("INVALID", {})
        
        assert "must be valid JSON" in str(exc_info.value)
    
    def test_has(self, mock_env):
        """Check if key exists."""
        assert mock_env.has("PORT") is True
        assert mock_env.has("NONEXISTENT") is False
    
    def test_get_public(self, mock_env):
        """Get public vars with prefix stripped."""
        result = mock_env.get_public()
        
        assert "API_URL" in result
        assert result["API_URL"] == "https://api.example.com"
        assert "PYNEXT_PUBLIC_API_URL" not in result


# ============================================
# Schema Validation Tests (25 tests)
# ============================================

class TestEnvSchema:
    """Tests for pynext.env.schema."""
    
    def test_var_required(self):
        """Required var validation."""
        from pynext.env.schema import EnvSchema, Var
        
        schema = EnvSchema(
            DATABASE_URL=Var(str, required=True),
        )
        
        result = schema.validate({})
        
        assert result.valid is False
        assert len(result.errors) == 1
        assert "DATABASE_URL" in result.errors[0].key
    
    def test_var_optional(self):
        """Optional var with default."""
        from pynext.env.schema import EnvSchema, Var
        
        schema = EnvSchema(
            PORT=Var(int, default=8000),
        )
        
        result = schema.validate({})
        
        assert result.valid is True
    
    def test_var_type_int(self):
        """Integer type validation."""
        from pynext.env.schema import EnvSchema, Var
        
        schema = EnvSchema(
            PORT=Var(int, required=True),
        )
        
        result = schema.validate({"PORT": "not-a-number"})
        
        assert result.valid is False
        assert "Invalid type" in result.errors[0].message
    
    def test_var_type_bool(self):
        """Boolean type validation."""
        from pynext.env.schema import EnvSchema, Var
        
        schema = EnvSchema(
            DEBUG=Var(bool, default=False),
        )
        
        result = schema.validate({"DEBUG": "true"})
        
        assert result.valid is True
    
    def test_var_choices(self):
        """Choices validation."""
        from pynext.env.schema import EnvSchema, Var
        
        schema = EnvSchema(
            MODE=Var(str, choices=["development", "production"]),
        )
        
        # Valid choice
        result = schema.validate({"MODE": "production"})
        assert result.valid is True
        
        # Invalid choice
        result = schema.validate({"MODE": "staging"})
        assert result.valid is False
        assert "Must be one of" in result.errors[0].message
    
    def test_var_custom_validator(self):
        """Custom validator function."""
        from pynext.env.schema import EnvSchema, Var
        
        schema = EnvSchema(
            URL=Var(str, validator=lambda x: x.startswith("http")),
        )
        
        # Valid
        result = schema.validate({"URL": "https://example.com"})
        assert result.valid is True
        
        # Invalid
        result = schema.validate({"URL": "not-a-url"})
        assert result.valid is False
    
    def test_var_secret_masked(self):
        """Secret values are masked in errors."""
        from pynext.env.schema import EnvSchema, Var
        
        schema = EnvSchema(
            API_KEY=Var(int, secret=True),  # Wrong type to trigger error
        )
        
        result = schema.validate({"API_KEY": "secret-value"})
        
        assert result.valid is False
        assert "***" in str(result.errors[0].value)
        assert "secret-value" not in str(result.errors[0])
    
    def test_var_description(self):
        """Description in error messages."""
        from pynext.env.schema import EnvSchema, Var
        
        schema = EnvSchema(
            DATABASE_URL=Var(str, required=True, description="PostgreSQL connection string"),
        )
        
        result = schema.validate({})
        
        assert "PostgreSQL connection string" in result.errors[0].message
    
    def test_validate_multiple_errors(self):
        """Collect all validation errors."""
        from pynext.env.schema import EnvSchema, Var
        
        schema = EnvSchema(
            A=Var(str, required=True),
            B=Var(str, required=True),
            C=Var(str, required=True),
        )
        
        result = schema.validate({})
        
        assert len(result.errors) == 3
    
    def test_validation_result_raise(self):
        """raise_if_invalid method."""
        from pynext.env.schema import EnvSchema, Var
        
        schema = EnvSchema(
            REQUIRED=Var(str, required=True),
        )
        
        result = schema.validate({})
        
        with pytest.raises(EnvironmentError):
            result.raise_if_invalid()
    
    def test_load_returns_config(self):
        """load() returns typed config."""
        from pynext.env.schema import EnvSchema, Var
        
        schema = EnvSchema(
            PORT=Var(int, default=8000),
            DEBUG=Var(bool, default=False),
        )
        
        config = schema.load({"PORT": "3000", "DEBUG": "true"})
        
        assert config.PORT == 3000
        assert isinstance(config.PORT, int)
        assert config.DEBUG is True
    
    def test_config_attribute_access(self):
        """Config attribute access."""
        from pynext.env.schema import EnvSchema, Var
        
        schema = EnvSchema(
            NAME=Var(str, default="test"),
        )
        
        config = schema.load({})
        
        assert config.NAME == "test"
    
    def test_config_missing_attribute(self):
        """Config missing attribute raises."""
        from pynext.env.schema import EnvSchema, Var
        
        schema = EnvSchema(
            NAME=Var(str, default="test"),
        )
        
        config = schema.load({})
        
        with pytest.raises(AttributeError):
            _ = config.NONEXISTENT
    
    def test_generate_template(self):
        """Generate .env.example template."""
        from pynext.env.schema import EnvSchema, Var
        
        schema = EnvSchema(
            DATABASE_URL=Var(str, required=True, description="Database connection"),
            PORT=Var(int, default=8000),
            API_KEY=Var(str, required=True, secret=True),
        )
        
        template = schema.generate_template()
        
        assert "DATABASE_URL" in template
        assert "PORT=8000" in template
        assert "your_secret_here" in template
        assert "Required" in template
    
    def test_load_schema_from_file(self, tmp_path):
        """Load schema from env.schema.py."""
        from pynext.env.schema import load_schema
        
        schema_file = tmp_path / "env.schema.py"
        schema_file.write_text("""
from pynext.env.schema import EnvSchema, Var

schema = EnvSchema(
    PORT=Var(int, default=8000),
)
""")
        
        schema = load_schema(tmp_path)
        
        assert schema is not None
        assert "PORT" in schema.vars
    
    def test_load_schema_missing_file(self, tmp_path):
        """Return None if no schema file."""
        from pynext.env.schema import load_schema
        
        schema = load_schema(tmp_path)
        
        assert schema is None
    
    def test_get_required_vars(self):
        """Get list of required vars."""
        from pynext.env.schema import EnvSchema, Var
        
        schema = EnvSchema(
            A=Var(str, required=True),
            B=Var(str, required=False),
            C=Var(str, required=True),
        )
        
        required = schema.get_required_vars()
        
        assert set(required) == {"A", "C"}
    
    def test_get_optional_vars(self):
        """Get list of optional vars."""
        from pynext.env.schema import EnvSchema, Var
        
        schema = EnvSchema(
            A=Var(str, required=True),
            B=Var(str, required=False),
        )
        
        optional = schema.get_optional_vars()
        
        assert optional == ["B"]
    
    def test_get_secret_vars(self):
        """Get list of secret vars."""
        from pynext.env.schema import EnvSchema, Var
        
        schema = EnvSchema(
            API_KEY=Var(str, secret=True),
            PUBLIC=Var(str, secret=False),
        )
        
        secrets = schema.get_secret_vars()
        
        assert secrets == ["API_KEY"]
    
    def test_var_list_type(self):
        """List type validation."""
        from pynext.env.schema import EnvSchema, Var
        
        schema = EnvSchema(
            HOSTS=Var(list, default=[]),
        )
        
        config = schema.load({"HOSTS": "a,b,c"})
        
        assert config.HOSTS == ["a", "b", "c"]
    
    def test_validation_result_str(self):
        """ValidationResult string representation."""
        from pynext.env.schema import ValidationResult
        
        valid = ValidationResult(valid=True)
        invalid = ValidationResult(valid=False, errors=[])
        
        assert "passed" in str(valid)
        assert "failed" in str(invalid)
    
    def test_env_config_to_dict(self):
        """EnvConfig to_dict method."""
        from pynext.env.schema import EnvConfig
        
        config = EnvConfig({"A": 1, "B": "two"})
        
        result = config.to_dict()
        
        assert result == {"A": 1, "B": "two"}
    
    def test_env_config_get(self):
        """EnvConfig get method."""
        from pynext.env.schema import EnvConfig
        
        config = EnvConfig({"A": 1})
        
        assert config.get("A") == 1
        assert config.get("B", "default") == "default"
    
    def test_env_config_contains(self):
        """EnvConfig __contains__."""
        from pynext.env.schema import EnvConfig
        
        config = EnvConfig({"A": 1})
        
        assert "A" in config
        assert "B" not in config


# ============================================
# Client Exposure Tests (10 tests)
# ============================================

class TestEnvClient:
    """Tests for pynext.env.client."""
    
    def test_get_public_vars(self):
        """Extract public vars."""
        from pynext.env.client import get_public_vars
        
        vars = {
            "DATABASE_URL": "secret",
            "PYNEXT_PUBLIC_API_URL": "https://api.example.com",
            "PYNEXT_PUBLIC_APP_NAME": "My App",
        }
        
        result = get_public_vars(vars)
        
        assert "API_URL" in result
        assert "APP_NAME" in result
        assert "DATABASE_URL" not in result
    
    def test_generate_inline_script(self):
        """Generate inline script tag."""
        from pynext.env.client import generate_inline_script
        
        vars = {"API_URL": "https://api.example.com"}
        
        result = generate_inline_script(vars)
        
        assert "<script>" in result
        assert "__PYNEXT_ENV__" in result
        assert "API_URL" in result
    
    def test_generate_inline_script_empty(self):
        """Handle empty vars."""
        from pynext.env.client import generate_inline_script
        
        result = generate_inline_script({})
        
        assert "__PYNEXT_ENV__={}" in result
    
    def test_generate_runtime_script(self):
        """Generate runtime loader script."""
        from pynext.env.client import generate_runtime_script
        
        result = generate_runtime_script()
        
        assert "fetch" in result
        assert "/_pynext/env.json" in result
    
    def test_inline_env_in_js(self):
        """Replace env refs in JS."""
        from pynext.env.client import inline_env_in_js
        
        js = "const api = process.env.API_URL;"
        vars = {"API_URL": "https://api.example.com"}
        
        result = inline_env_in_js(js, vars)
        
        assert '"https://api.example.com"' in result
        assert "process.env.API_URL" not in result
    
    def test_inline_import_meta_env(self):
        """Replace import.meta.env refs."""
        from pynext.env.client import inline_env_in_js
        
        js = "const api = import.meta.env.API_URL;"
        vars = {"API_URL": "https://api.example.com"}
        
        result = inline_env_in_js(js, vars)
        
        assert '"https://api.example.com"' in result
    
    def test_get_client_env_accessor(self):
        """Generate client accessor code."""
        from pynext.env.client import get_client_env_accessor
        
        result = get_client_env_accessor()
        
        assert "__pynext__" in result
        assert "env" in result
        assert "get" in result
        assert "has" in result
    
    def test_validate_public_var_name(self):
        """Validate var name for client."""
        from pynext.env.client import validate_public_var_name
        
        assert validate_public_var_name("API_URL") is True
        assert validate_public_var_name("PYNEXT_PUBLIC_API_URL") is True
        assert validate_public_var_name("123_INVALID") is False
    
    def test_inject_env_into_html(self):
        """Inject env into HTML."""
        from pynext.env.client import inject_env_into_html
        
        html = "<html><head></head><body></body></html>"
        vars = {"API_URL": "https://api.example.com"}
        
        result = inject_env_into_html(html, vars, mode="inline")
        
        assert "__PYNEXT_ENV__" in result
    
    def test_get_env_injection_point(self):
        """Get injection point marker."""
        from pynext.env.client import get_env_injection_point
        
        result = get_env_injection_point()
        
        assert "PYNEXT_ENV" in result


# ============================================
# Build Integration Tests (10 tests)
# ============================================

class TestEnvBuild:
    """Tests for pynext.build.env."""
    
    def test_validate_env_for_build(self, tmp_path):
        """Validate env before build."""
        from pynext.build.env import validate_env_for_build
        
        (tmp_path / ".env").write_text("PORT=8000")
        
        # Should not raise without schema
        result = validate_env_for_build(tmp_path, "production")
        
        assert result is True
    
    def test_validate_env_with_schema(self, tmp_path):
        """Validate with schema present."""
        from pynext.build.env import validate_env_for_build
        
        (tmp_path / ".env").write_text("DATABASE_URL=postgres://localhost")
        (tmp_path / "env.schema.py").write_text("""
from pynext.env.schema import EnvSchema, Var
schema = EnvSchema(
    DATABASE_URL=Var(str, required=True),
)
""")
        
        result = validate_env_for_build(tmp_path, "production")
        
        assert result is True
    
    def test_validate_env_missing_required(self, tmp_path):
        """Fail validation for missing required."""
        from pynext.build.env import validate_env_for_build
        
        (tmp_path / ".env").write_text("OTHER=value")
        (tmp_path / "env.schema.py").write_text("""
from pynext.env.schema import EnvSchema, Var
schema = EnvSchema(
    REQUIRED=Var(str, required=True),
)
""")
        
        with pytest.raises(EnvironmentError):
            validate_env_for_build(tmp_path, "production")
    
    def test_process_js_bundle(self, tmp_path):
        """Process JS bundle with env vars."""
        from pynext.build.env import process_js_bundle
        
        js_file = tmp_path / "app.js"
        js_file.write_text("const api = process.env.API_URL;")
        
        process_js_bundle(
            js_file,
            {"PYNEXT_PUBLIC_API_URL": "https://api.example.com"}
        )
        
        result = js_file.read_text()
        assert '"https://api.example.com"' in result
    
    def test_generate_env_json(self, tmp_path):
        """Generate env.json file."""
        from pynext.build.env import generate_env_json
        
        (tmp_path / ".env").write_text(
            "PYNEXT_PUBLIC_API_URL=https://api.example.com\n"
            "SECRET=hidden"
        )
        
        output_dir = tmp_path / "public"
        path = generate_env_json(tmp_path, output_dir, "production")
        
        assert path.exists()
        
        content = json.loads(path.read_text())
        assert "API_URL" in content
        assert "SECRET" not in content
    
    def test_generate_env_types(self, tmp_path):
        """Generate TypeScript types."""
        from pynext.build.env import generate_env_types
        
        (tmp_path / "env.schema.py").write_text("""
from pynext.env.schema import EnvSchema, Var
schema = EnvSchema(
    PYNEXT_PUBLIC_API_URL=Var(str, required=True),
    PYNEXT_PUBLIC_DEBUG=Var(bool, default=False),
)
""")
        
        types = generate_env_types(tmp_path)
        
        assert types is not None
        assert "API_URL" in types
        assert "string" in types
        assert "boolean" in types
    
    def test_get_build_env_summary(self, tmp_path):
        """Get build environment summary."""
        from pynext.build.env import get_build_env_summary
        
        (tmp_path / ".env").write_text(
            "DATABASE_URL=postgres://localhost\n"
            "PYNEXT_PUBLIC_API_URL=https://api.example.com"
        )
        
        summary = get_build_env_summary(tmp_path, "production")
        
        assert summary["total_vars"] >= 2
        assert summary["public_vars"] == 1
        assert "API_URL" in summary["public_var_names"]
    
    def test_inject_env_into_html_file(self, tmp_path):
        """Inject env into HTML file."""
        from pynext.build.env import inject_env_into_html
        
        html_file = tmp_path / "index.html"
        html_file.write_text("<html><head></head><body></body></html>")
        
        inject_env_into_html(
            html_file,
            {"PYNEXT_PUBLIC_API_URL": "https://api.example.com"}
        )
        
        result = html_file.read_text()
        assert "__PYNEXT_ENV__" in result
    
    def test_process_all_js_bundles(self, tmp_path):
        """Process all JS files in directory."""
        from pynext.build.env import process_all_js_bundles
        
        (tmp_path / "app.js").write_text("process.env.API_URL")
        (tmp_path / "utils.js").write_text("// no env refs")
        
        count = process_all_js_bundles(
            tmp_path,
            {"PYNEXT_PUBLIC_API_URL": "https://api.example.com"}
        )
        
        assert count == 1  # Only app.js needed processing
    
    def test_generate_env_types_no_public(self, tmp_path):
        """Handle schema with no public vars."""
        from pynext.build.env import generate_env_types
        
        (tmp_path / "env.schema.py").write_text("""
from pynext.env.schema import EnvSchema, Var
schema = EnvSchema(
    DATABASE_URL=Var(str, required=True),  # Not public
)
""")
        
        types = generate_env_types(tmp_path)
        
        # Should still generate but without public vars
        assert types is not None


# ============================================
# CLI Tests (15 tests)
# ============================================

class TestEnvCLI:
    """Tests for CLI env commands."""
    
    def test_cmd_env_list(self, tmp_path):
        """pynext env list command."""
        from pynext.cli import cmd_env
        
        (tmp_path / ".env").write_text("TEST_VAR=hello")
        
        args = MagicMock()
        args.env_command = "list"
        args.dir = str(tmp_path)
        args.show_values = False
        args.public = False
        args.mode = "development"
        
        result = cmd_env(args)
        
        assert result == 0
    
    def test_cmd_env_list_with_values(self, tmp_path):
        """pynext env list -v shows values."""
        from pynext.cli import cmd_env
        
        (tmp_path / ".env").write_text("TEST_VAR=hello")
        
        args = MagicMock()
        args.env_command = "list"
        args.dir = str(tmp_path)
        args.show_values = True
        args.public = False
        args.mode = "development"
        
        result = cmd_env(args)
        
        assert result == 0
    
    def test_cmd_env_list_public_only(self, tmp_path):
        """pynext env list -p shows only public."""
        from pynext.cli import cmd_env
        
        (tmp_path / ".env").write_text(
            "SECRET=hidden\n"
            "PYNEXT_PUBLIC_API=visible"
        )
        
        args = MagicMock()
        args.env_command = "list"
        args.dir = str(tmp_path)
        args.show_values = True
        args.public = True
        args.mode = "development"
        
        result = cmd_env(args)
        
        assert result == 0
    
    def test_cmd_env_check(self, tmp_path):
        """pynext env check command."""
        from pynext.cli import cmd_env
        
        (tmp_path / ".env").write_text("VAR=value")
        
        args = MagicMock()
        args.env_command = "check"
        args.dir = str(tmp_path)
        args.mode = "development"
        
        result = cmd_env(args)
        
        assert result == 0
    
    def test_cmd_env_validate_no_schema(self, tmp_path):
        """pynext env validate without schema."""
        from pynext.cli import cmd_env
        
        args = MagicMock()
        args.env_command = "validate"
        args.dir = str(tmp_path)
        args.mode = "production"
        
        result = cmd_env(args)
        
        assert result == 1  # No schema = error
    
    def test_cmd_env_validate_with_schema(self, tmp_path):
        """pynext env validate with valid schema."""
        from pynext.cli import cmd_env
        
        (tmp_path / ".env").write_text("REQUIRED=value")
        (tmp_path / "env.schema.py").write_text("""
from pynext.env.schema import EnvSchema, Var
schema = EnvSchema(REQUIRED=Var(str, required=True))
""")
        
        args = MagicMock()
        args.env_command = "validate"
        args.dir = str(tmp_path)
        args.mode = "production"
        
        result = cmd_env(args)
        
        assert result == 0
    
    def test_cmd_env_validate_missing_required(self, tmp_path):
        """pynext env validate with missing required."""
        from pynext.cli import cmd_env
        
        (tmp_path / ".env").write_text("OTHER=value")
        (tmp_path / "env.schema.py").write_text("""
from pynext.env.schema import EnvSchema, Var
schema = EnvSchema(REQUIRED=Var(str, required=True))
""")
        
        args = MagicMock()
        args.env_command = "validate"
        args.dir = str(tmp_path)
        args.mode = "production"
        
        result = cmd_env(args)
        
        assert result == 1
    
    def test_cmd_env_init_no_schema(self, tmp_path):
        """pynext env init without schema."""
        from pynext.cli import cmd_env
        
        args = MagicMock()
        args.env_command = "init"
        args.dir = str(tmp_path)
        args.force = False
        
        result = cmd_env(args)
        
        assert result == 1  # No schema = error
    
    def test_cmd_env_init_creates_files(self, tmp_path):
        """pynext env init creates files."""
        from pynext.cli import cmd_env
        
        (tmp_path / "env.schema.py").write_text("""
from pynext.env.schema import EnvSchema, Var
schema = EnvSchema(PORT=Var(int, default=8000))
""")
        
        args = MagicMock()
        args.env_command = "init"
        args.dir = str(tmp_path)
        args.force = False
        
        result = cmd_env(args)
        
        assert result == 0
        assert (tmp_path / ".env.example").exists()
        assert (tmp_path / ".env").exists()
    
    def test_cmd_env_init_no_overwrite(self, tmp_path):
        """pynext env init doesn't overwrite without force."""
        from pynext.cli import cmd_env
        
        (tmp_path / ".env.example").write_text("existing")
        (tmp_path / "env.schema.py").write_text("""
from pynext.env.schema import EnvSchema, Var
schema = EnvSchema(PORT=Var(int, default=8000))
""")
        
        args = MagicMock()
        args.env_command = "init"
        args.dir = str(tmp_path)
        args.force = False
        
        result = cmd_env(args)
        
        assert result == 1
    
    def test_cmd_env_init_force(self, tmp_path):
        """pynext env init --force overwrites."""
        from pynext.cli import cmd_env
        
        (tmp_path / ".env.example").write_text("existing")
        (tmp_path / "env.schema.py").write_text("""
from pynext.env.schema import EnvSchema, Var
schema = EnvSchema(PORT=Var(int, default=8000))
""")
        
        args = MagicMock()
        args.env_command = "init"
        args.dir = str(tmp_path)
        args.force = True
        
        result = cmd_env(args)
        
        assert result == 0
    
    def test_cmd_env_no_subcommand(self, tmp_path):
        """pynext env without subcommand shows status."""
        from pynext.cli import cmd_env
        
        (tmp_path / ".env").write_text("VAR=value")
        
        args = MagicMock()
        args.env_command = None
        args.dir = str(tmp_path)
        
        result = cmd_env(args)
        
        assert result == 0
    
    def test_cmd_env_masks_secrets(self, tmp_path, capsys):
        """pynext env list masks secret values."""
        from pynext.cli import cmd_env
        
        (tmp_path / ".env").write_text("API_KEY=super-secret-key")
        
        args = MagicMock()
        args.env_command = "list"
        args.dir = str(tmp_path)
        args.show_values = True
        args.public = False
        args.mode = "development"
        
        cmd_env(args)
        
        captured = capsys.readouterr()
        assert "***" in captured.out
        assert "super-secret-key" not in captured.out
    
    def test_cmd_env_generate_types(self, tmp_path):
        """pynext env generate creates TypeScript types."""
        from pynext.cli import cmd_env
        
        (tmp_path / "env.schema.py").write_text("""
from pynext.env.schema import EnvSchema, Var
schema = EnvSchema(
    PYNEXT_PUBLIC_API_URL=Var(str, required=True),
)
""")
        
        args = MagicMock()
        args.env_command = "generate"
        args.dir = str(tmp_path)
        args.output = None
        
        result = cmd_env(args)
        
        assert result == 0
        assert (tmp_path / "env.d.ts").exists()
    
    def test_cmd_env_truncates_long_values(self, tmp_path, capsys):
        """pynext env list truncates long values."""
        from pynext.cli import cmd_env
        
        long_value = "x" * 100
        (tmp_path / ".env").write_text(f"LONG={long_value}")
        
        args = MagicMock()
        args.env_command = "list"
        args.dir = str(tmp_path)
        args.show_values = True
        args.public = False
        args.mode = "development"
        
        cmd_env(args)
        
        captured = capsys.readouterr()
        assert "..." in captured.out


# ============================================
# Integration Tests (10 tests)
# ============================================

class TestEnvIntegration:
    """Integration tests for env system."""
    
    def test_full_workflow(self, tmp_path):
        """Test complete env workflow."""
        from pynext.env.loader import load_env_files
        from pynext.env.schema import EnvSchema, Var
        from pynext.env.client import get_public_vars, generate_inline_script
        
        # Create env files
        (tmp_path / ".env").write_text("""
DATABASE_URL=postgres://localhost/db
PYNEXT_PUBLIC_API_URL=https://api.example.com
PYNEXT_PUBLIC_DEBUG=true
""")
        
        # Load
        env_vars = load_env_files(tmp_path, "development")
        
        assert env_vars["DATABASE_URL"] == "postgres://localhost/db"
        
        # Validate
        schema = EnvSchema(
            DATABASE_URL=Var(str, required=True),
            PYNEXT_PUBLIC_API_URL=Var(str, required=True),
            PYNEXT_PUBLIC_DEBUG=Var(bool, default=False),
        )
        
        result = schema.validate(env_vars)
        assert result.valid
        
        # Get public vars
        public = get_public_vars(env_vars)
        assert "API_URL" in public
        assert "DATABASE_URL" not in public
        
        # Generate script
        script = generate_inline_script(public)
        assert "API_URL" in script
    
    def test_mode_override(self, tmp_path):
        """Test mode-specific overrides."""
        from pynext.env.loader import load_env_files
        
        (tmp_path / ".env").write_text("DEBUG=false\nPORT=3000")
        (tmp_path / ".env.development").write_text("DEBUG=true")
        (tmp_path / ".env.production").write_text("DEBUG=false\nPORT=80")
        
        dev_vars = load_env_files(tmp_path, "development")
        prod_vars = load_env_files(tmp_path, "production")
        
        assert dev_vars["DEBUG"] == "true"
        assert prod_vars["DEBUG"] == "false"
        assert prod_vars["PORT"] == "80"
    
    def test_variable_expansion_in_files(self, tmp_path):
        """Test variable expansion across files."""
        from pynext.env.loader import load_env_files
        
        (tmp_path / ".env").write_text("BASE=http://localhost")
        (tmp_path / ".env.local").write_text("API=${BASE}/api")
        
        vars = load_env_files(tmp_path, "development")
        
        assert vars["API"] == "http://localhost/api"
    
    def test_schema_with_custom_validators(self, tmp_path):
        """Test schema with custom validators."""
        from pynext.env.loader import load_env_files
        from pynext.env.schema import EnvSchema, Var
        
        (tmp_path / ".env").write_text("URL=https://secure.example.com")
        
        def validate_https(value):
            return value.startswith("https://")
        
        schema = EnvSchema(
            URL=Var(str, required=True, validator=validate_https),
        )
        
        vars = load_env_files(tmp_path, "development")
        result = schema.validate(vars)
        
        assert result.valid
    
    def test_env_module_singleton(self, tmp_path):
        """Test Env class is singleton."""
        from pynext.env_module import Env
        
        # Reset
        Env._instance = None
        Env._loaded = False
        
        env1 = Env()
        env2 = Env()
        
        assert env1 is env2
    
    def test_env_reload(self, tmp_path):
        """Test env reload functionality."""
        from pynext.env_module import Env
        
        # Reset
        Env._instance = None
        Env._loaded = False
        Env._vars = {}
        
        (tmp_path / ".env").write_text("VAR=original")
        
        env = Env()
        env._load(tmp_path)
        
        assert env.get("VAR") == "original"
        
        # Change file
        (tmp_path / ".env").write_text("VAR=updated")
        
        # Reload
        env.reload(tmp_path)
        
        assert env.get("VAR") == "updated"
    
    def test_env_require_multiple(self, tmp_path):
        """Test requiring multiple vars."""
        from pynext.env_module import Env
        
        # Reset
        Env._instance = None
        Env._loaded = False
        Env._vars = {}
        
        (tmp_path / ".env").write_text("A=1\nB=2")
        
        env = Env()
        env._load(tmp_path)
        
        # Should not raise
        env.require("A", "B")
        
        # Should raise
        with pytest.raises(KeyError) as exc_info:
            env.require("A", "B", "C", "D")
        
        assert "C" in str(exc_info.value)
        assert "D" in str(exc_info.value)
    
    def test_build_time_processing(self, tmp_path):
        """Test build-time env processing."""
        from pynext.build.env import validate_env_for_build, process_js_bundle, generate_env_json
        
        (tmp_path / ".env").write_text("PYNEXT_PUBLIC_API=https://api.example.com")
        
        # Validate
        validate_env_for_build(tmp_path, "production")
        
        # Process JS
        js_file = tmp_path / "app.js"
        js_file.write_text("fetch(process.env.API)")
        
        process_js_bundle(js_file, {"PYNEXT_PUBLIC_API": "https://api.example.com"})
        
        assert '"https://api.example.com"' in js_file.read_text()
        
        # Generate JSON
        output = tmp_path / "public"
        generate_env_json(tmp_path, output, "production")
        
        assert (output / "env.json").exists()
    
    def test_env_in_production_mode(self, tmp_path):
        """Test env behavior in production mode."""
        from pynext.env.loader import load_env_files
        
        (tmp_path / ".env").write_text("MODE=base")
        (tmp_path / ".env.production").write_text("MODE=production")
        
        vars = load_env_files(tmp_path, "production")
        
        assert vars["MODE"] == "production"
    
    def test_env_json_endpoint_integration(self, tmp_path):
        """Test env.json endpoint output format."""
        from pynext.env.loader import load_env_files
        from pynext.env.client import get_public_vars
        import json
        
        (tmp_path / ".env").write_text("""
SECRET=hidden
PYNEXT_PUBLIC_API_URL=https://api.example.com
PYNEXT_PUBLIC_APP_NAME=My App
""")
        
        vars = load_env_files(tmp_path, "production")
        public = get_public_vars(vars)
        
        # Simulate endpoint output
        output = json.dumps(public, indent=2)
        parsed = json.loads(output)
        
        assert "API_URL" in parsed
        assert "APP_NAME" in parsed
        assert "SECRET" not in parsed

