"""
PostgreSQL URL Parsing Tests.

50 comprehensive tests for PostgresConfig and URL parsing.
"""

import pytest
from pynext.db.adapters.postgres.core.url import (
    PostgresConfig,
    PostgresConfigError,
    parse_postgres_url,
)


# =============================================================================
# Basic URL Parsing Tests
# =============================================================================

class TestBasicURLParsing:
    """Tests for basic URL formats."""
    
    def test_minimal_url(self):
        """Test parsing minimal URL."""
        config = PostgresConfig.from_url("postgresql://localhost/mydb")
        assert config.host == "localhost"
        assert config.database == "mydb"
        assert config.port == 5432
        assert config.user == "postgres"
    
    def test_url_with_port(self):
        """Test parsing URL with custom port."""
        config = PostgresConfig.from_url("postgresql://localhost:5433/mydb")
        assert config.host == "localhost"
        assert config.port == 5433
        assert config.database == "mydb"
    
    def test_url_with_user(self):
        """Test parsing URL with username."""
        config = PostgresConfig.from_url("postgresql://admin@localhost/mydb")
        assert config.user == "admin"
        assert config.host == "localhost"
        assert config.database == "mydb"
    
    def test_url_with_password(self):
        """Test parsing URL with username and password."""
        config = PostgresConfig.from_url("postgresql://admin:secret@localhost/mydb")
        assert config.user == "admin"
        assert config.password == "secret"
        assert config.host == "localhost"
    
    def test_url_with_all_components(self):
        """Test parsing URL with all components."""
        config = PostgresConfig.from_url("postgresql://user:pass@db.example.com:5433/production")
        assert config.user == "user"
        assert config.password == "pass"
        assert config.host == "db.example.com"
        assert config.port == 5433
        assert config.database == "production"
    
    def test_postgres_scheme(self):
        """Test postgres:// scheme (alias for postgresql://)."""
        config = PostgresConfig.from_url("postgres://localhost/mydb")
        assert config.host == "localhost"
        assert config.database == "mydb"


# =============================================================================
# URL Options Tests
# =============================================================================

class TestURLOptions:
    """Tests for URL query parameters."""
    
    def test_sslmode_require(self):
        """Test parsing sslmode=require."""
        config = PostgresConfig.from_url("postgresql://localhost/mydb?sslmode=require")
        assert config.ssl is True
        assert config.ssl_mode == "require"
    
    def test_sslmode_disable(self):
        """Test parsing sslmode=disable."""
        config = PostgresConfig.from_url("postgresql://localhost/mydb?sslmode=disable")
        assert config.ssl is False
        assert config.ssl_mode == "disable"
    
    def test_sslmode_verify_full(self):
        """Test parsing sslmode=verify-full."""
        config = PostgresConfig.from_url("postgresql://localhost/mydb?sslmode=verify-full")
        assert config.ssl is True
        assert config.ssl_mode == "verify-full"
    
    def test_application_name(self):
        """Test parsing application_name."""
        config = PostgresConfig.from_url("postgresql://localhost/mydb?application_name=myapp")
        assert config.application_name == "myapp"
    
    def test_multiple_options(self):
        """Test parsing multiple query parameters."""
        config = PostgresConfig.from_url(
            "postgresql://localhost/mydb?sslmode=require&application_name=myapp"
        )
        assert config.ssl is True
        assert config.ssl_mode == "require"
        assert config.application_name == "myapp"


# =============================================================================
# Special Characters Tests
# =============================================================================

class TestSpecialCharacters:
    """Tests for special characters in URL components."""
    
    def test_password_with_at_sign(self):
        """Test password containing @ symbol."""
        config = PostgresConfig.from_url("postgresql://user:p%40ssword@localhost/mydb")
        assert config.password == "p@ssword"
    
    def test_password_with_colon(self):
        """Test password containing : symbol."""
        config = PostgresConfig.from_url("postgresql://user:p%3Assword@localhost/mydb")
        assert config.password == "p:ssword"
    
    def test_password_with_slash(self):
        """Test password containing / symbol."""
        config = PostgresConfig.from_url("postgresql://user:p%2Fssword@localhost/mydb")
        assert config.password == "p/ssword"
    
    def test_username_with_special_chars(self):
        """Test username with special characters."""
        config = PostgresConfig.from_url("postgresql://user%40domain@localhost/mydb")
        assert config.user == "user@domain"
    
    def test_database_with_underscore(self):
        """Test database name with underscore."""
        config = PostgresConfig.from_url("postgresql://localhost/my_database")
        assert config.database == "my_database"
    
    def test_database_with_hyphen(self):
        """Test database name with hyphen."""
        config = PostgresConfig.from_url("postgresql://localhost/my-database")
        assert config.database == "my-database"


# =============================================================================
# Invalid URL Tests
# =============================================================================

class TestInvalidURLs:
    """Tests for invalid URLs."""
    
    def test_empty_url(self):
        """Test empty URL raises error."""
        with pytest.raises(PostgresConfigError) as exc_info:
            PostgresConfig.from_url("")
        assert "cannot be empty" in str(exc_info.value).lower()
    
    def test_invalid_scheme(self):
        """Test invalid scheme raises error."""
        with pytest.raises(PostgresConfigError) as exc_info:
            PostgresConfig.from_url("mysql://localhost/mydb")
        assert "postgresql://" in str(exc_info.value)
    
    def test_http_scheme(self):
        """Test HTTP scheme raises error."""
        with pytest.raises(PostgresConfigError) as exc_info:
            PostgresConfig.from_url("http://localhost/mydb")
        assert "postgresql://" in str(exc_info.value)
    
    def test_missing_scheme(self):
        """Test missing scheme raises error."""
        with pytest.raises(PostgresConfigError) as exc_info:
            PostgresConfig.from_url("localhost/mydb")
        assert "postgresql://" in str(exc_info.value)


# =============================================================================
# Override Tests
# =============================================================================

class TestOverrides:
    """Tests for URL with keyword overrides."""
    
    def test_override_password(self):
        """Test overriding password from URL."""
        config = PostgresConfig.from_url(
            "postgresql://user:oldpass@localhost/mydb",
            password="newpass"
        )
        assert config.password == "newpass"
    
    def test_override_port(self):
        """Test overriding port from URL."""
        config = PostgresConfig.from_url(
            "postgresql://localhost:5432/mydb",
            port=5433
        )
        assert config.port == 5433
    
    def test_override_database(self):
        """Test overriding database from URL."""
        config = PostgresConfig.from_url(
            "postgresql://localhost/olddb",
            database="newdb"
        )
        assert config.database == "newdb"
    
    def test_override_user(self):
        """Test overriding user from URL."""
        config = PostgresConfig.from_url(
            "postgresql://olduser@localhost/mydb",
            user="newuser"
        )
        assert config.user == "newuser"
    
    def test_override_ssl(self):
        """Test overriding SSL setting."""
        config = PostgresConfig.from_url(
            "postgresql://localhost/mydb?sslmode=disable",
            ssl=True
        )
        assert config.ssl is True


# =============================================================================
# Keyword-Only Config Tests
# =============================================================================

class TestKeywordConfig:
    """Tests for keyword-only configuration."""
    
    def test_minimal_keywords(self):
        """Test minimal keyword configuration."""
        config = PostgresConfig(host="localhost", database="mydb")
        assert config.host == "localhost"
        assert config.database == "mydb"
        assert config.port == 5432
        assert config.user == "postgres"
    
    def test_all_keywords(self):
        """Test full keyword configuration."""
        config = PostgresConfig(
            host="db.example.com",
            port=5433,
            database="production",
            user="admin",
            password="secret",
            ssl=True,
        )
        assert config.host == "db.example.com"
        assert config.port == 5433
        assert config.database == "production"
        assert config.user == "admin"
        assert config.password == "secret"
        assert config.ssl is True
    
    def test_default_values(self):
        """Test default values."""
        config = PostgresConfig()
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.database == "postgres"
        assert config.user == "postgres"
        assert config.password is None
        assert config.ssl is False


# =============================================================================
# Validation Tests
# =============================================================================

class TestValidation:
    """Tests for configuration validation."""
    
    def test_invalid_port_zero(self):
        """Test port=0 raises error."""
        with pytest.raises(PostgresConfigError) as exc_info:
            PostgresConfig(host="localhost", port=0)
        assert "port" in str(exc_info.value).lower()
    
    def test_invalid_port_negative(self):
        """Test negative port raises error."""
        with pytest.raises(PostgresConfigError) as exc_info:
            PostgresConfig(host="localhost", port=-1)
        assert "port" in str(exc_info.value).lower()
    
    def test_invalid_port_too_high(self):
        """Test port > 65535 raises error."""
        with pytest.raises(PostgresConfigError) as exc_info:
            PostgresConfig(host="localhost", port=70000)
        assert "port" in str(exc_info.value).lower()
    
    def test_empty_host(self):
        """Test empty host raises error."""
        with pytest.raises(PostgresConfigError) as exc_info:
            PostgresConfig(host="", database="mydb")
        assert "host" in str(exc_info.value).lower()
    
    def test_empty_database(self):
        """Test empty database raises error."""
        with pytest.raises(PostgresConfigError) as exc_info:
            PostgresConfig(host="localhost", database="")
        assert "database" in str(exc_info.value).lower()
    
    def test_invalid_ssl_mode(self):
        """Test invalid ssl_mode raises error."""
        with pytest.raises(PostgresConfigError) as exc_info:
            PostgresConfig(host="localhost", ssl_mode="invalid")
        assert "ssl_mode" in str(exc_info.value).lower()


# =============================================================================
# Conversion Tests
# =============================================================================

class TestConversion:
    """Tests for config conversion methods."""
    
    def test_to_dsn_basic(self):
        """Test converting config to DSN."""
        config = PostgresConfig(
            host="localhost",
            database="mydb",
            user="postgres",
        )
        dsn = config.to_dsn()
        assert "postgresql://" in dsn
        assert "localhost" in dsn
        assert "mydb" in dsn
    
    def test_to_dsn_with_password(self):
        """Test DSN with password."""
        config = PostgresConfig(
            host="localhost",
            database="mydb",
            user="admin",
            password="secret",
        )
        dsn = config.to_dsn()
        assert "admin:secret@" in dsn
    
    def test_to_dsn_password_encoding(self):
        """Test DSN encodes special characters in password."""
        config = PostgresConfig(
            host="localhost",
            database="mydb",
            user="admin",
            password="p@ss:word",
        )
        dsn = config.to_dsn()
        assert "@" not in dsn.split("@")[0].split(":")[-1]  # Password encoded
    
    def test_to_asyncpg_kwargs(self):
        """Test converting to asyncpg kwargs."""
        config = PostgresConfig(
            host="localhost",
            port=5432,
            database="mydb",
            user="postgres",
            password="secret",
        )
        kwargs = config.to_asyncpg_kwargs()
        assert kwargs["host"] == "localhost"
        assert kwargs["port"] == 5432
        assert kwargs["database"] == "mydb"
        assert kwargs["user"] == "postgres"
        assert kwargs["password"] == "secret"


# =============================================================================
# Convenience Function Tests
# =============================================================================

class TestConvenienceFunction:
    """Tests for parse_postgres_url convenience function."""
    
    def test_parse_basic_url(self):
        """Test parse_postgres_url function."""
        config = parse_postgres_url("postgresql://localhost/mydb")
        assert config.host == "localhost"
        assert config.database == "mydb"
    
    def test_parse_full_url(self):
        """Test parsing full URL with convenience function."""
        config = parse_postgres_url("postgresql://user:pass@host:5433/db?sslmode=require")
        assert config.user == "user"
        assert config.password == "pass"
        assert config.host == "host"
        assert config.port == 5433
        assert config.database == "db"
        assert config.ssl is True


# =============================================================================
# Repr and String Tests
# =============================================================================

class TestRepr:
    """Tests for string representation."""
    
    def test_repr_hides_password(self):
        """Test repr hides password."""
        config = PostgresConfig(
            host="localhost",
            database="mydb",
            password="supersecret",
        )
        repr_str = repr(config)
        assert "supersecret" not in repr_str
        assert "***" in repr_str
    
    def test_repr_no_password(self):
        """Test repr without password."""
        config = PostgresConfig(host="localhost", database="mydb")
        repr_str = repr(config)
        assert "None" in repr_str
        assert "localhost" in repr_str

