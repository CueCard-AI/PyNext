"""
Unit tests for Go Bridge error types.

Tests all exception classes and error handling utilities.
"""

import pytest

from pynext_go.errors import (
    BridgeError,
    BridgeConfigError,
    BridgeConnectionError,
    BridgeQueryError,
    BridgeTimeoutError,
    BridgePoolError,
    BridgeArrowError,
    BridgeNotInitializedError,
    BridgeAlreadyInitializedError,
    GoNotAvailableError,
    error_from_code,
)


class TestBridgeErrorBase:
    """Base BridgeError tests."""
    
    def test_basic_error(self):
        """Basic error with message only."""
        err = BridgeError("something went wrong")
        assert str(err) == "something went wrong"
        assert err.message == "something went wrong"
        assert err.code == 0
        assert err.details == ""
    
    def test_error_with_code(self):
        """Error with code."""
        err = BridgeError("error", code=42)
        assert err.code == 42
    
    def test_error_with_details(self):
        """Error with details included in string."""
        err = BridgeError("error", details="additional info")
        assert str(err) == "error (additional info)"
        assert err.details == "additional info"
    
    def test_error_repr(self):
        """Error repr should include class name and details."""
        err = BridgeError("test error", code=5)
        r = repr(err)
        assert "BridgeError" in r
        assert "test error" in r
        assert "code=5" in r
    
    def test_error_to_dict(self):
        """Error should serialize to dict."""
        err = BridgeError("msg", code=3, details="det")
        d = err.to_dict()
        
        assert d["type"] == "BridgeError"
        assert d["message"] == "msg"
        assert d["code"] == 3
        assert d["details"] == "det"
    
    def test_error_inheritance(self):
        """All bridge errors should inherit from BridgeError."""
        for cls in [
            BridgeConfigError,
            BridgeConnectionError,
            BridgeQueryError,
            BridgeTimeoutError,
            BridgePoolError,
            BridgeArrowError,
            BridgeNotInitializedError,
            BridgeAlreadyInitializedError,
            GoNotAvailableError,
        ]:
            assert issubclass(cls, BridgeError)
            assert issubclass(cls, Exception)


class TestBridgeConfigError:
    """BridgeConfigError tests."""
    
    def test_config_error(self):
        """Config error with message."""
        err = BridgeConfigError("invalid config")
        assert "invalid config" in str(err)
    
    def test_config_error_with_code(self):
        """Config error should use code 1."""
        err = BridgeConfigError("error", code=1)
        assert err.code == 1
    
    def test_catching_as_bridge_error(self):
        """ConfigError should be catchable as BridgeError."""
        try:
            raise BridgeConfigError("test")
        except BridgeError as e:
            assert "test" in str(e)


class TestBridgeConnectionError:
    """BridgeConnectionError tests."""
    
    def test_connection_error(self):
        """Connection error with message."""
        err = BridgeConnectionError("connection refused")
        assert "connection refused" in str(err)
    
    def test_connection_error_code(self):
        """Connection error should use code 2."""
        err = BridgeConnectionError("error", code=2)
        assert err.code == 2


class TestBridgeQueryError:
    """BridgeQueryError tests."""
    
    def test_query_error_basic(self):
        """Basic query error."""
        err = BridgeQueryError("syntax error")
        assert "syntax error" in str(err)
    
    def test_query_error_with_sql(self):
        """Query error with SQL included."""
        err = BridgeQueryError(
            "syntax error",
            sql="SELECT * FORM users",
            params=[1, 2],
        )
        assert err.sql == "SELECT * FORM users"
        assert err.params == [1, 2]
        assert "SQL:" in str(err)
    
    def test_query_error_long_sql_truncated(self):
        """Long SQL should be truncated in string."""
        long_sql = "SELECT " + "x, " * 100
        err = BridgeQueryError("error", sql=long_sql)
        s = str(err)
        assert "..." in s
        assert len(s) < len(long_sql) + 100
    
    def test_query_error_code(self):
        """Query error should use code 3."""
        err = BridgeQueryError("error", code=3)
        assert err.code == 3


class TestBridgeTimeoutError:
    """BridgeTimeoutError tests."""
    
    def test_timeout_error_default_message(self):
        """Timeout error should have default message."""
        err = BridgeTimeoutError()
        assert "timed out" in str(err).lower()
    
    def test_timeout_error_with_duration(self):
        """Timeout error with duration included."""
        err = BridgeTimeoutError("Query timed out", timeout_ms=5000)
        assert "5000ms" in str(err)
    
    def test_timeout_error_code(self):
        """Timeout error should use code 4."""
        err = BridgeTimeoutError(code=4)
        assert err.code == 4


class TestBridgePoolError:
    """BridgePoolError tests."""
    
    def test_pool_error(self):
        """Pool error with message."""
        err = BridgePoolError("pool exhausted")
        assert "pool exhausted" in str(err)
    
    def test_pool_error_code(self):
        """Pool error should use code 5."""
        err = BridgePoolError("error", code=5)
        assert err.code == 5


class TestBridgeArrowError:
    """BridgeArrowError tests."""
    
    def test_arrow_error(self):
        """Arrow error with message."""
        err = BridgeArrowError("failed to convert type")
        assert "convert" in str(err)
    
    def test_arrow_error_code(self):
        """Arrow error should use code 6."""
        err = BridgeArrowError("error", code=6)
        assert err.code == 6


class TestBridgeNotInitializedError:
    """BridgeNotInitializedError tests."""
    
    def test_not_initialized_default_message(self):
        """Not initialized error should have helpful message."""
        err = BridgeNotInitializedError()
        assert "not initialized" in str(err).lower()
        assert "init()" in str(err)
    
    def test_not_initialized_code(self):
        """Not initialized error should use code 7."""
        err = BridgeNotInitializedError()
        assert err.code == 7


class TestBridgeAlreadyInitializedError:
    """BridgeAlreadyInitializedError tests."""
    
    def test_already_initialized_default_message(self):
        """Already initialized error should have helpful message."""
        err = BridgeAlreadyInitializedError()
        assert "already initialized" in str(err).lower()
        assert "close()" in str(err)
    
    def test_already_initialized_code(self):
        """Already initialized error should use code 8."""
        err = BridgeAlreadyInitializedError()
        assert err.code == 8


class TestGoNotAvailableError:
    """GoNotAvailableError tests."""
    
    def test_go_not_available_default_message(self):
        """Go not available should have default message."""
        err = GoNotAvailableError()
        assert "not available" in str(err).lower()
    
    def test_go_not_available_custom_message(self):
        """Go not available with custom message."""
        err = GoNotAvailableError("custom message")
        assert "custom message" in str(err)
    
    def test_go_not_available_code(self):
        """Go not available should use code -1."""
        err = GoNotAvailableError()
        assert err.code == -1


class TestErrorFromCode:
    """error_from_code utility tests."""
    
    def test_code_0_returns_base_error(self):
        """Code 0 should return BridgeError."""
        err = error_from_code(0, "message")
        assert type(err) == BridgeError
    
    def test_code_1_returns_config_error(self):
        """Code 1 should return BridgeConfigError."""
        err = error_from_code(1, "message")
        assert isinstance(err, BridgeConfigError)
    
    def test_code_2_returns_connection_error(self):
        """Code 2 should return BridgeConnectionError."""
        err = error_from_code(2, "message")
        assert isinstance(err, BridgeConnectionError)
    
    def test_code_3_returns_query_error(self):
        """Code 3 should return BridgeQueryError."""
        err = error_from_code(3, "message")
        assert isinstance(err, BridgeQueryError)
    
    def test_code_4_returns_timeout_error(self):
        """Code 4 should return BridgeTimeoutError."""
        err = error_from_code(4, "message")
        assert isinstance(err, BridgeTimeoutError)
    
    def test_code_5_returns_pool_error(self):
        """Code 5 should return BridgePoolError."""
        err = error_from_code(5, "message")
        assert isinstance(err, BridgePoolError)
    
    def test_code_6_returns_arrow_error(self):
        """Code 6 should return BridgeArrowError."""
        err = error_from_code(6, "message")
        assert isinstance(err, BridgeArrowError)
    
    def test_code_7_returns_not_initialized(self):
        """Code 7 should return BridgeNotInitializedError."""
        err = error_from_code(7, "message")
        assert isinstance(err, BridgeNotInitializedError)
    
    def test_code_8_returns_already_initialized(self):
        """Code 8 should return BridgeAlreadyInitializedError."""
        err = error_from_code(8, "message")
        assert isinstance(err, BridgeAlreadyInitializedError)
    
    def test_unknown_code_returns_base_error(self):
        """Unknown code should return BridgeError."""
        err = error_from_code(999, "message")
        assert type(err) == BridgeError
    
    def test_error_from_code_includes_details(self):
        """error_from_code should preserve details."""
        err = error_from_code(3, "message", "details here")
        assert err.details == "details here"


class TestFromGoError:
    """BridgeError.from_go_error tests."""
    
    def test_from_go_error_basic(self):
        """from_go_error with minimal dict."""
        d = {"code": 3, "message": "syntax error"}
        err = BridgeError.from_go_error(d)
        
        assert isinstance(err, BridgeQueryError)
        assert err.message == "syntax error"
        assert err.code == 3
    
    def test_from_go_error_with_details(self):
        """from_go_error with details."""
        d = {
            "code": 2,
            "message": "connection failed",
            "details": "timeout after 5s",
        }
        err = BridgeError.from_go_error(d)
        
        assert isinstance(err, BridgeConnectionError)
        assert err.details == "timeout after 5s"
    
    def test_from_go_error_empty_dict(self):
        """from_go_error with empty dict should use defaults."""
        d = {}
        err = BridgeError.from_go_error(d)
        
        assert err.message == "Unknown error"
        assert err.code == 0
    
    def test_from_go_error_unknown_code(self):
        """from_go_error with unknown code should return base error."""
        d = {"code": 12345, "message": "weird error"}
        err = BridgeError.from_go_error(d)
        
        assert type(err) == BridgeError
        assert err.message == "weird error"


class TestErrorHierarchy:
    """Error hierarchy and catching tests."""
    
    def test_catch_all_as_bridge_error(self):
        """All specific errors should be catchable as BridgeError."""
        errors = [
            BridgeConfigError("test"),
            BridgeConnectionError("test"),
            BridgeQueryError("test"),
            BridgeTimeoutError(),
            BridgePoolError("test"),
            BridgeArrowError("test"),
        ]
        
        for err in errors:
            try:
                raise err
            except BridgeError:
                pass  # Should catch all
    
    def test_catch_as_exception(self):
        """All errors should be catchable as Exception."""
        try:
            raise BridgeQueryError("test")
        except Exception:
            pass  # Should catch
    
    def test_specific_catch_doesnt_catch_other_types(self):
        """Specific error catch shouldn't catch other types."""
        with pytest.raises(BridgeConnectionError):
            try:
                raise BridgeConnectionError("conn error")
            except BridgeQueryError:
                pass  # Should NOT catch

