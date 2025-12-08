"""
PyNext Go Bridge - Error Types.

Defines all exception types raised by the Go bridge.

Error Hierarchy:
    BridgeError (base)
    ├── GoNotAvailableError    - Go library not found
    ├── BridgeConfigError      - Invalid configuration
    ├── BridgeConnectionError  - Connection failed
    ├── BridgeQueryError       - Query execution failed
    ├── BridgeTimeoutError     - Query timed out
    ├── BridgePoolError        - Pool exhausted/closed
    └── BridgeArrowError       - Arrow conversion failed

Usage:
    try:
        result = bridge.execute("SELECT * FROM users")
    except BridgeTimeoutError:
        print("Query timed out")
    except BridgeQueryError as e:
        print(f"Query failed: {e}")
    except BridgeError as e:
        print(f"Bridge error: {e}")
"""

from __future__ import annotations

from typing import Any


class BridgeError(Exception):
    """
    Base exception for all Go bridge errors.
    
    Attributes:
        message: Human-readable error message
        code: Error code from Go (matches ErrCode* constants)
        details: Additional error details from Go
    """
    
    def __init__(
        self,
        message: str,
        code: int = 0,
        details: str = "",
    ):
        self.message = message
        self.code = code
        self.details = details
        super().__init__(message)
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message} ({self.details})"
        return self.message
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.message!r}, code={self.code})"
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging/serialization."""
        return {
            "type": self.__class__.__name__,
            "message": self.message,
            "code": self.code,
            "details": self.details,
        }
    
    @classmethod
    def from_go_error(cls, error_dict: dict[str, Any]) -> BridgeError:
        """
        Create appropriate error from Go bridge error response.
        
        Args:
            error_dict: Error dictionary from Go (code, message, details)
            
        Returns:
            Appropriate BridgeError subclass
        """
        code = error_dict.get("code", 0)
        message = error_dict.get("message", "Unknown error")
        details = error_dict.get("details", "")
        
        # Map error code to appropriate subclass
        error_class = _ERROR_CODE_MAP.get(code, BridgeError)
        return error_class(message, code, details)


class GoNotAvailableError(BridgeError):
    """
    Raised when the Go library is not available.
    
    This happens when:
    - pynext-go is not installed
    - The shared library failed to load
    - Platform is not supported
    
    The application can catch this and fall back to asyncpg.
    """
    
    def __init__(self, message: str = "Go bridge not available"):
        super().__init__(message, code=-1)


class BridgeConfigError(BridgeError):
    """
    Raised for invalid bridge configuration.
    
    Examples:
    - Missing primary connection string
    - Invalid pool settings
    - Malformed connection URL
    """
    pass


class BridgeConnectionError(BridgeError):
    """
    Raised when database connection fails.
    
    Examples:
    - Database unreachable
    - Authentication failed
    - SSL/TLS error
    """
    pass


class BridgeQueryError(BridgeError):
    """
    Raised when query execution fails.
    
    Examples:
    - SQL syntax error
    - Constraint violation
    - Permission denied
    """
    
    def __init__(
        self,
        message: str,
        code: int = 0,
        details: str = "",
        sql: str = "",
        params: list | None = None,
    ):
        super().__init__(message, code, details)
        self.sql = sql
        self.params = params or []
    
    def __str__(self) -> str:
        base = super().__str__()
        if self.sql:
            return f"{base}\nSQL: {self.sql[:200]}..."
        return base


class BridgeTimeoutError(BridgeError):
    """
    Raised when query times out.
    
    The timeout can be configured globally or per-query:
    - Global: BridgeConfig(query_timeout=10000)
    - Per-query: bridge.execute(sql, timeout_ms=5000)
    """
    
    def __init__(
        self,
        message: str = "Query timed out",
        code: int = 4,
        details: str = "",
        timeout_ms: int = 0,
    ):
        super().__init__(message, code, details)
        self.timeout_ms = timeout_ms
    
    def __str__(self) -> str:
        if self.timeout_ms:
            return f"{self.message} (timeout: {self.timeout_ms}ms)"
        return self.message


class BridgePoolError(BridgeError):
    """
    Raised for connection pool errors.
    
    Examples:
    - Pool exhausted (all connections in use)
    - Pool closed
    - Failed to acquire connection
    """
    pass


class BridgeArrowError(BridgeError):
    """
    Raised for Arrow conversion errors.
    
    Examples:
    - Type conversion failed
    - Invalid Arrow buffer
    - Memory allocation failed
    """
    pass


class BridgeNotInitializedError(BridgeError):
    """
    Raised when using bridge before initialization.
    
    Call GoBridge.init() or pynext_go.init() first.
    """
    
    def __init__(
        self,
        message: str = "Go bridge not initialized - call init() first",
        code: int = 7,
        details: str = "",
    ):
        super().__init__(message, code, details)


class BridgeAlreadyInitializedError(BridgeError):
    """
    Raised when initializing an already-initialized bridge.
    
    Call GoBridge.close() first to reinitialize.
    """
    
    def __init__(
        self,
        message: str = "Go bridge already initialized - call close() first",
        code: int = 8,
        details: str = "",
    ):
        super().__init__(message, code, details)


# Error code to class mapping (matches Go ErrCode* constants)
_ERROR_CODE_MAP: dict[int, type[BridgeError]] = {
    0: BridgeError,  # Success (shouldn't be used for errors)
    1: BridgeConfigError,
    2: BridgeConnectionError,
    3: BridgeQueryError,
    4: BridgeTimeoutError,
    5: BridgePoolError,
    6: BridgeArrowError,
    7: BridgeNotInitializedError,
    8: BridgeAlreadyInitializedError,
}


def error_from_code(code: int, message: str, details: str = "") -> BridgeError:
    """
    Create appropriate error from Go error code.
    
    Args:
        code: Error code from Go
        message: Error message
        details: Additional details
        
    Returns:
        Appropriate BridgeError subclass instance
    """
    error_class = _ERROR_CODE_MAP.get(code, BridgeError)
    return error_class(message, code, details)

