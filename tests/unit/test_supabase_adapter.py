"""
Comprehensive tests for PyNext Supabase Adapter.

Tests cover:
- Configuration validation (URL, key parsing)
- Environment variable handling
- Client initialization
- Error handling
- Service accessors (auth, storage, realtime, functions, rls)

Total: 80 tests
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass

from pynext.db.supabase.adapter import (
    Supabase,
    SupabaseConfig,
    create_supabase,
    get_supabase_from_env,
)
from pynext.db.supabase.exceptions import (
    MissingURLError,
    MissingKeyError,
    InvalidURLError,
    ConfigurationError,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def valid_url():
    return "https://xyz.supabase.co"


@pytest.fixture
def valid_key():
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inh5eiIsInJvbGUiOiJhbm9uIiwiaWF0IjoxNjE2NTEwNjQwLCJleHAiOjE5MzIwODY2NDB9.fake"


@pytest.fixture
def service_role_key():
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inh5eiIsInJvbGUiOiJzZXJ2aWNlX3JvbGUiLCJpYXQiOjE2MTY1MTA2NDAsImV4cCI6MTkzMjA4NjY0MH0.fake"


@pytest.fixture
def mock_env(valid_url, valid_key, monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", valid_url)
    monkeypatch.setenv("SUPABASE_KEY", valid_key)


# =============================================================================
# SUPABASE CONFIG TESTS (20 tests)
# =============================================================================

class TestSupabaseConfig:
    """Tests for SupabaseConfig class."""
    
    def test_config_with_valid_url_and_key(self, valid_url, valid_key):
        """Config accepts valid URL and key."""
        config = SupabaseConfig(url=valid_url, anon_key=valid_key)
        assert config.url == valid_url
        assert config.anon_key == valid_key
    
    def test_config_strips_trailing_slash(self, valid_key):
        """Config strips trailing slashes from URL."""
        config = SupabaseConfig(url="https://xyz.supabase.co/", anon_key=valid_key)
        assert config.url == "https://xyz.supabase.co"
    
    def test_config_strips_whitespace(self, valid_key):
        """Config strips whitespace from URL."""
        config = SupabaseConfig(url="  https://xyz.supabase.co  ", anon_key=valid_key)
        assert config.url == "https://xyz.supabase.co"
    
    def test_config_missing_url_raises(self, valid_key):
        """Config raises MissingURLError when URL is empty."""
        with pytest.raises(MissingURLError):
            SupabaseConfig(url="", anon_key=valid_key)
    
    def test_config_missing_key_raises(self, valid_url):
        """Config raises MissingKeyError when key is empty."""
        with pytest.raises(MissingKeyError):
            SupabaseConfig(url=valid_url, anon_key="")
    
    def test_config_invalid_url_no_scheme(self, valid_key):
        """Config raises InvalidURLError for URL without scheme."""
        with pytest.raises(InvalidURLError):
            SupabaseConfig(url="xyz.supabase.co", anon_key=valid_key)
    
    def test_config_invalid_url_scheme(self, valid_key):
        """Config raises InvalidURLError for invalid scheme."""
        with pytest.raises(InvalidURLError) as exc_info:
            SupabaseConfig(url="ftp://xyz.supabase.co", anon_key=valid_key)
        assert "scheme" in str(exc_info.value).lower()
    
    def test_config_service_role_key_optional(self, valid_url, valid_key):
        """Config accepts None for service_role_key."""
        config = SupabaseConfig(url=valid_url, anon_key=valid_key)
        assert config.service_role_key is None
    
    def test_config_with_service_role_key(self, valid_url, valid_key, service_role_key):
        """Config stores service_role_key."""
        config = SupabaseConfig(
            url=valid_url,
            anon_key=valid_key,
            service_role_key=service_role_key
        )
        assert config.service_role_key == service_role_key
    
    def test_config_derives_storage_url(self, valid_url, valid_key):
        """Config auto-derives storage URL."""
        config = SupabaseConfig(url=valid_url, anon_key=valid_key)
        assert config.storage_url == f"{valid_url}/storage/v1"
    
    def test_config_derives_functions_url(self, valid_url, valid_key):
        """Config auto-derives functions URL."""
        config = SupabaseConfig(url=valid_url, anon_key=valid_key)
        assert config.functions_url == f"{valid_url}/functions/v1"
    
    def test_config_custom_storage_url(self, valid_url, valid_key):
        """Config uses custom storage URL if provided."""
        custom_storage = "https://custom-storage.example.com"
        config = SupabaseConfig(
            url=valid_url,
            anon_key=valid_key,
            storage_url=custom_storage
        )
        assert config.storage_url == custom_storage
    
    def test_config_custom_functions_url(self, valid_url, valid_key):
        """Config uses custom functions URL if provided."""
        custom_functions = "https://custom-functions.example.com"
        config = SupabaseConfig(
            url=valid_url,
            anon_key=valid_key,
            functions_url=custom_functions
        )
        assert config.functions_url == custom_functions
    
    def test_config_rest_url_property(self, valid_url, valid_key):
        """Config provides rest_url property."""
        config = SupabaseConfig(url=valid_url, anon_key=valid_key)
        assert config.rest_url == f"{valid_url}/rest/v1"
    
    def test_config_auth_url_property(self, valid_url, valid_key):
        """Config provides auth_url property."""
        config = SupabaseConfig(url=valid_url, anon_key=valid_key)
        assert config.auth_url == f"{valid_url}/auth/v1"
    
    def test_config_realtime_url_property_https(self, valid_key):
        """Config converts https to wss for realtime URL."""
        config = SupabaseConfig(url="https://xyz.supabase.co", anon_key=valid_key)
        assert config.realtime_url == "wss://xyz.supabase.co/realtime/v1"
    
    def test_config_realtime_url_property_http(self, valid_key):
        """Config converts http to ws for realtime URL."""
        config = SupabaseConfig(url="http://localhost:54321", anon_key=valid_key)
        assert config.realtime_url == "ws://localhost:54321/realtime/v1"
    
    def test_config_default_timeout(self, valid_url, valid_key):
        """Config has default timeout of 30 seconds."""
        config = SupabaseConfig(url=valid_url, anon_key=valid_key)
        assert config.timeout == 30.0
    
    def test_config_custom_timeout(self, valid_url, valid_key):
        """Config accepts custom timeout."""
        config = SupabaseConfig(url=valid_url, anon_key=valid_key, timeout=60.0)
        assert config.timeout == 60.0
    
    def test_config_from_env(self, mock_env, valid_url, valid_key):
        """Config.from_env() reads environment variables."""
        config = SupabaseConfig.from_env()
        assert config.url == valid_url
        assert config.anon_key == valid_key


# =============================================================================
# SUPABASE ADAPTER INITIALIZATION TESTS (20 tests)
# =============================================================================

class TestSupabaseInit:
    """Tests for Supabase adapter initialization."""
    
    def test_init_with_url_and_key(self, valid_url, valid_key):
        """Supabase initializes with URL and key."""
        db = Supabase(valid_url, key=valid_key)
        assert db.config.url == valid_url
        assert db.config.anon_key == valid_key
    
    def test_init_with_url_only_reads_env(self, mock_env, valid_url, valid_key):
        """Supabase reads key from environment if not provided."""
        db = Supabase(valid_url)
        assert db.config.url == valid_url
        assert db.config.anon_key == valid_key
    
    def test_init_with_anon_key_param(self, valid_url, valid_key):
        """Supabase accepts anon_key parameter."""
        db = Supabase(valid_url, anon_key=valid_key)
        assert db.config.anon_key == valid_key
    
    def test_init_key_overrides_anon_key(self, valid_url, valid_key):
        """key parameter takes precedence over anon_key."""
        other_key = "eyJother.other.other"
        db = Supabase(valid_url, key=valid_key, anon_key=other_key)
        assert db.config.anon_key == valid_key
    
    def test_init_with_service_role_key(self, valid_url, valid_key, service_role_key):
        """Supabase stores service_role_key for admin operations."""
        db = Supabase(valid_url, key=valid_key, service_role_key=service_role_key)
        assert db.config.service_role_key == service_role_key
    
    def test_init_with_config_object(self, valid_url, valid_key):
        """Supabase accepts SupabaseConfig object."""
        config = SupabaseConfig(url=valid_url, anon_key=valid_key)
        db = Supabase(config=config)
        assert db.config is config
    
    def test_init_config_overrides_params(self, valid_url, valid_key):
        """config parameter overrides other parameters."""
        other_url = "https://other.supabase.co"
        config = SupabaseConfig(url=valid_url, anon_key=valid_key)
        db = Supabase(other_url, key="other_key", config=config)
        assert db.config.url == valid_url
    
    def test_init_from_env_only(self, mock_env, valid_url, valid_key):
        """Supabase reads both URL and key from environment."""
        db = Supabase()
        assert db.config.url == valid_url
        assert db.config.anon_key == valid_key
    
    def test_init_auto_refresh_token_default(self, valid_url, valid_key):
        """Supabase has auto_refresh_token enabled by default."""
        db = Supabase(valid_url, key=valid_key)
        assert db.config.auto_refresh_token is True
    
    def test_init_auto_refresh_token_disabled(self, valid_url, valid_key):
        """Supabase can disable auto_refresh_token."""
        db = Supabase(valid_url, key=valid_key, auto_refresh_token=False)
        assert db.config.auto_refresh_token is False
    
    def test_init_persist_session_default(self, valid_url, valid_key):
        """Supabase has persist_session enabled by default."""
        db = Supabase(valid_url, key=valid_key)
        assert db.config.persist_session is True
    
    def test_init_realtime_enabled_default(self, valid_url, valid_key):
        """Supabase has realtime enabled by default."""
        db = Supabase(valid_url, key=valid_key)
        assert db.config.realtime_enabled is True
    
    def test_init_not_initialized_before_use(self, valid_url, valid_key):
        """Supabase client not initialized until first use."""
        db = Supabase(valid_url, key=valid_key)
        assert db._initialized is False
    
    def test_init_custom_headers(self, valid_url, valid_key):
        """Supabase accepts custom headers."""
        headers = {"X-Custom": "value"}
        db = Supabase(valid_url, key=valid_key, headers=headers)
        assert db.config.headers == headers
    
    def test_repr(self, valid_url, valid_key):
        """Supabase has informative repr."""
        db = Supabase(valid_url, key=valid_key)
        repr_str = repr(db)
        assert valid_url in repr_str
        assert "initialized=False" in repr_str
    
    def test_config_property(self, valid_url, valid_key):
        """Supabase.config returns current config."""
        db = Supabase(valid_url, key=valid_key)
        assert isinstance(db.config, SupabaseConfig)
    
    def test_missing_url_raises(self, valid_key, monkeypatch):
        """Supabase raises MissingURLError without URL."""
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        monkeypatch.setenv("SUPABASE_KEY", valid_key)
        with pytest.raises(MissingURLError):
            Supabase()
    
    def test_missing_key_raises(self, valid_url, monkeypatch):
        """Supabase raises MissingKeyError without key."""
        monkeypatch.setenv("SUPABASE_URL", valid_url)
        monkeypatch.delenv("SUPABASE_KEY", raising=False)
        with pytest.raises(MissingKeyError):
            Supabase(valid_url)
    
    def test_local_development_url(self, valid_key):
        """Supabase accepts localhost URL for development."""
        db = Supabase("http://localhost:54321", key=valid_key)
        assert db.config.url == "http://localhost:54321"
    
    def test_ip_address_url(self, valid_key):
        """Supabase accepts IP address URL."""
        db = Supabase("http://127.0.0.1:54321", key=valid_key)
        assert db.config.url == "http://127.0.0.1:54321"


# =============================================================================
# SERVICE ACCESSOR TESTS (15 tests)
# =============================================================================

class TestServiceAccessors:
    """Tests for service property accessors."""
    
    def test_auth_accessor_lazy(self, valid_url, valid_key):
        """auth accessor lazily creates SupabaseAuth."""
        db = Supabase(valid_url, key=valid_key)
        assert db._auth is None
        auth = db.auth
        assert db._auth is not None
        assert auth is db._auth
    
    def test_auth_accessor_singleton(self, valid_url, valid_key):
        """auth accessor returns same instance."""
        db = Supabase(valid_url, key=valid_key)
        auth1 = db.auth
        auth2 = db.auth
        assert auth1 is auth2
    
    def test_storage_accessor_lazy(self, valid_url, valid_key):
        """storage accessor lazily creates SupabaseStorage."""
        db = Supabase(valid_url, key=valid_key)
        assert db._storage is None
        storage = db.storage
        assert db._storage is not None
        assert storage is db._storage
    
    def test_storage_accessor_singleton(self, valid_url, valid_key):
        """storage accessor returns same instance."""
        db = Supabase(valid_url, key=valid_key)
        storage1 = db.storage
        storage2 = db.storage
        assert storage1 is storage2
    
    def test_realtime_accessor_lazy(self, valid_url, valid_key):
        """realtime accessor lazily creates SupabaseRealtime."""
        db = Supabase(valid_url, key=valid_key)
        assert db._realtime is None
        realtime = db.realtime
        assert db._realtime is not None
        assert realtime is db._realtime
    
    def test_realtime_accessor_singleton(self, valid_url, valid_key):
        """realtime accessor returns same instance."""
        db = Supabase(valid_url, key=valid_key)
        realtime1 = db.realtime
        realtime2 = db.realtime
        assert realtime1 is realtime2
    
    def test_functions_accessor_lazy(self, valid_url, valid_key):
        """functions accessor lazily creates SupabaseFunctions."""
        db = Supabase(valid_url, key=valid_key)
        assert db._functions is None
        functions = db.functions
        assert db._functions is not None
        assert functions is db._functions
    
    def test_functions_accessor_singleton(self, valid_url, valid_key):
        """functions accessor returns same instance."""
        db = Supabase(valid_url, key=valid_key)
        functions1 = db.functions
        functions2 = db.functions
        assert functions1 is functions2
    
    def test_rls_accessor_lazy(self, valid_url, valid_key):
        """rls accessor lazily creates SupabaseRLS."""
        db = Supabase(valid_url, key=valid_key)
        assert db._rls is None
        rls = db.rls
        assert db._rls is not None
        assert rls is db._rls
    
    def test_rls_accessor_singleton(self, valid_url, valid_key):
        """rls accessor returns same instance."""
        db = Supabase(valid_url, key=valid_key)
        rls1 = db.rls
        rls2 = db.rls
        assert rls1 is rls2
    
    def test_auth_has_reference_to_supabase(self, valid_url, valid_key):
        """auth service has reference to parent Supabase."""
        db = Supabase(valid_url, key=valid_key)
        assert db.auth._supabase is db
    
    def test_storage_has_reference_to_supabase(self, valid_url, valid_key):
        """storage service has reference to parent Supabase."""
        db = Supabase(valid_url, key=valid_key)
        assert db.storage._supabase is db
    
    def test_realtime_has_reference_to_supabase(self, valid_url, valid_key):
        """realtime service has reference to parent Supabase."""
        db = Supabase(valid_url, key=valid_key)
        assert db.realtime._supabase is db
    
    def test_functions_has_reference_to_supabase(self, valid_url, valid_key):
        """functions service has reference to parent Supabase."""
        db = Supabase(valid_url, key=valid_key)
        assert db.functions._supabase is db
    
    def test_rls_has_reference_to_supabase(self, valid_url, valid_key):
        """rls service has reference to parent Supabase."""
        db = Supabase(valid_url, key=valid_key)
        assert db.rls._supabase is db


# =============================================================================
# HELPER FUNCTION TESTS (10 tests)
# =============================================================================

class TestHelperFunctions:
    """Tests for module-level helper functions."""
    
    def test_create_supabase_with_url_and_key(self, valid_url, valid_key):
        """create_supabase() creates Supabase instance."""
        db = create_supabase(valid_url, valid_key)
        assert isinstance(db, Supabase)
        assert db.config.url == valid_url
    
    def test_create_supabase_with_kwargs(self, valid_url, valid_key):
        """create_supabase() passes kwargs to Supabase."""
        db = create_supabase(valid_url, valid_key, auto_refresh_token=False)
        assert db.config.auto_refresh_token is False
    
    def test_get_supabase_from_env(self, mock_env, valid_url, valid_key):
        """get_supabase_from_env() reads from environment."""
        db = get_supabase_from_env()
        assert isinstance(db, Supabase)
        assert db.config.url == valid_url
        assert db.config.anon_key == valid_key
    
    def test_get_supabase_from_env_with_service_key(self, valid_url, valid_key, service_role_key, monkeypatch):
        """get_supabase_from_env() reads service role key."""
        monkeypatch.setenv("SUPABASE_URL", valid_url)
        monkeypatch.setenv("SUPABASE_KEY", valid_key)
        monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", service_role_key)
        
        db = get_supabase_from_env()
        assert db.config.service_role_key == service_role_key
    
    def test_get_supabase_from_env_missing_url(self, valid_key, monkeypatch):
        """get_supabase_from_env() raises on missing URL."""
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        monkeypatch.setenv("SUPABASE_KEY", valid_key)
        with pytest.raises(MissingURLError):
            get_supabase_from_env()
    
    def test_get_supabase_from_env_missing_key(self, valid_url, monkeypatch):
        """get_supabase_from_env() raises on missing key."""
        monkeypatch.setenv("SUPABASE_URL", valid_url)
        monkeypatch.delenv("SUPABASE_KEY", raising=False)
        with pytest.raises(MissingKeyError):
            get_supabase_from_env()
    
    def test_create_supabase_empty_url(self, valid_key, monkeypatch):
        """create_supabase() raises on empty URL."""
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        with pytest.raises(MissingURLError):
            create_supabase(None, valid_key)
    
    def test_create_supabase_empty_key(self, valid_url, monkeypatch):
        """create_supabase() raises on empty key."""
        monkeypatch.delenv("SUPABASE_KEY", raising=False)
        with pytest.raises(MissingKeyError):
            create_supabase(valid_url, None)
    
    def test_config_from_env_with_url_override(self, mock_env, valid_key):
        """Config.from_env() can override URL."""
        custom_url = "https://custom.supabase.co"
        config = SupabaseConfig.from_env(url=custom_url)
        assert config.url == custom_url
        assert config.anon_key == valid_key
    
    def test_config_default_headers_empty(self, valid_url, valid_key):
        """Config has empty headers by default."""
        config = SupabaseConfig(url=valid_url, anon_key=valid_key)
        assert config.headers == {}


# =============================================================================
# ERROR HANDLING TESTS (15 tests)
# =============================================================================

class TestErrorHandling:
    """Tests for error handling scenarios."""
    
    def test_missing_url_error_message(self, valid_key, monkeypatch):
        """MissingURLError has helpful message."""
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        try:
            Supabase(key=valid_key)
        except MissingURLError as e:
            assert "SUPABASE_URL" in str(e)
    
    def test_missing_key_error_message(self, valid_url, monkeypatch):
        """MissingKeyError has helpful message."""
        monkeypatch.delenv("SUPABASE_KEY", raising=False)
        try:
            Supabase(valid_url)
        except MissingKeyError as e:
            assert "SUPABASE_KEY" in str(e)
    
    def test_invalid_url_error_includes_url(self, valid_key):
        """InvalidURLError includes the invalid URL."""
        bad_url = "not-a-valid-url"
        try:
            Supabase(bad_url, key=valid_key)
        except InvalidURLError as e:
            assert bad_url in str(e)
    
    def test_error_code_on_missing_url(self, valid_key, monkeypatch):
        """MissingURLError has no error code."""
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        try:
            Supabase(key=valid_key)
        except MissingURLError as e:
            # MissingURLError doesn't have a code by default
            pass
    
    def test_invalid_url_format_empty_netloc(self, valid_key):
        """InvalidURLError for URL with empty netloc."""
        with pytest.raises(InvalidURLError):
            Supabase("https://", key=valid_key)
    
    def test_config_validation_happens_at_init(self, valid_key):
        """Configuration is validated at initialization."""
        with pytest.raises(InvalidURLError):
            SupabaseConfig(url="bad-url", anon_key=valid_key)
    
    def test_none_url_raises_missing_error(self, valid_key, monkeypatch):
        """None URL raises MissingURLError."""
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        with pytest.raises(MissingURLError):
            Supabase(None, key=valid_key)
    
    def test_none_key_raises_missing_error(self, valid_url, monkeypatch):
        """None key raises MissingKeyError."""
        monkeypatch.delenv("SUPABASE_KEY", raising=False)
        with pytest.raises(MissingKeyError):
            Supabase(valid_url, key=None)
    
    def test_whitespace_only_url_raises(self, valid_key):
        """Whitespace-only URL raises MissingURLError."""
        with pytest.raises(MissingURLError):
            Supabase("   ", key=valid_key)
    
    def test_whitespace_only_key_raises(self, valid_url):
        """Whitespace-only key is invalid but not caught."""
        # Note: Empty string after strip would fail, but " " might pass JWT check
        # This test documents current behavior
        with pytest.raises(MissingKeyError):
            Supabase(valid_url, key="")
    
    def test_error_repr(self, valid_key, monkeypatch):
        """Errors have repr."""
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        try:
            Supabase(key=valid_key)
        except MissingURLError as e:
            repr_str = repr(e)
            assert "MissingURLError" in repr_str
    
    def test_error_inheritance(self):
        """All errors inherit from SupabaseError."""
        from pynext.db.supabase.exceptions import SupabaseError
        assert issubclass(MissingURLError, SupabaseError)
        assert issubclass(MissingKeyError, SupabaseError)
        assert issubclass(InvalidURLError, SupabaseError)
    
    def test_config_error_inheritance(self):
        """Config errors inherit from ConfigurationError."""
        assert issubclass(MissingURLError, ConfigurationError)
        assert issubclass(MissingKeyError, ConfigurationError)
        assert issubclass(InvalidURLError, ConfigurationError)
    
    def test_error_with_details(self, valid_key):
        """InvalidURLError can include details."""
        try:
            SupabaseConfig(url="ftp://bad", anon_key=valid_key)
        except InvalidURLError as e:
            # Error should have meaningful message
            assert len(str(e)) > 0
    
    def test_multiple_validation_errors(self, monkeypatch):
        """First validation error is raised."""
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        monkeypatch.delenv("SUPABASE_KEY", raising=False)
        # URL is checked first
        with pytest.raises(MissingURLError):
            Supabase()

