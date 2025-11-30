"""
PyNext Database Exceptions.

Custom exceptions for the database layer with clear, helpful error messages.
Designed to be AI-friendly and easy to debug.
"""

from __future__ import annotations

from typing import Any, Optional


class DatabaseError(Exception):
    """Base exception for all database errors."""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)
    
    def __str__(self) -> str:
        if self.details:
            detail_str = ", ".join(f"{k}={v!r}" for k, v in self.details.items())
            return f"{self.message} ({detail_str})"
        return self.message


class ValidationError(DatabaseError):
    """
    Raised when model data fails validation.
    
    Examples:
        ValidationError("name: expected str, got int", field="name", expected="str", got="int")
        ValidationError("email: cannot be empty", field="email")
        ValidationError("age: must be positive", field="age", value=-5)
    """
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        expected: Optional[str] = None,
        got: Optional[str] = None,
        value: Any = None,
        errors: Optional[list[dict]] = None,
    ):
        details = {}
        if field:
            details["field"] = field
        if expected:
            details["expected"] = expected
        if got:
            details["got"] = got
        if value is not None:
            details["value"] = value
        if errors:
            details["errors"] = errors
        
        self.field = field
        self.expected = expected
        self.got = got
        self.value = value
        self.errors = errors or []
        
        super().__init__(message, details)
    
    @classmethod
    def type_mismatch(cls, field: str, expected: str, got: str, value: Any = None) -> "ValidationError":
        """Create a type mismatch error."""
        return cls(
            f"{field}: expected {expected}, got {got}",
            field=field,
            expected=expected,
            got=got,
            value=value,
        )
    
    @classmethod
    def required_field(cls, field: str) -> "ValidationError":
        """Create a required field error."""
        return cls(
            f"{field}: required field missing",
            field=field,
        )
    
    @classmethod
    def empty_value(cls, field: str) -> "ValidationError":
        """Create an empty value error."""
        return cls(
            f"{field}: cannot be empty",
            field=field,
            value="",
        )
    
    @classmethod
    def multiple(cls, errors: list["ValidationError"]) -> "ValidationError":
        """Create a validation error with multiple field errors."""
        messages = [e.message for e in errors]
        return cls(
            "; ".join(messages),
            errors=[{"field": e.field, "message": e.message} for e in errors],
        )


class NotFoundError(DatabaseError):
    """
    Raised when a record is not found.
    
    Examples:
        NotFoundError("User", id=42)
        NotFoundError("Post", slug="my-post")
    """
    
    def __init__(self, table: str, **lookup: Any):
        self.table = table
        self.lookup = lookup
        
        if lookup:
            lookup_str = ", ".join(f"{k}={v!r}" for k, v in lookup.items())
            message = f"{table} not found: {lookup_str}"
        else:
            message = f"{table} not found"
        
        super().__init__(message, {"table": table, **lookup})


class QueryError(DatabaseError):
    """
    Raised when a query is malformed or fails.
    
    Examples:
        QueryError("Invalid column: unknown_field")
        QueryError("Cannot chain .limit() twice")
    """
    
    def __init__(self, message: str, query: Optional[str] = None, params: Optional[tuple] = None):
        self.query = query
        self.params = params
        
        details = {}
        if query:
            details["query"] = query
        if params:
            details["params"] = params
        
        super().__init__(message, details)


class ConnectionError(DatabaseError):
    """
    Raised when database connection fails.
    
    Examples:
        ConnectionError("Failed to connect to PostgreSQL")
        ConnectionError("Connection pool exhausted")
    """
    
    def __init__(self, message: str, host: Optional[str] = None, port: Optional[int] = None):
        self.host = host
        self.port = port
        
        details = {}
        if host:
            details["host"] = host
        if port:
            details["port"] = port
        
        super().__init__(message, details)


class TransactionError(DatabaseError):
    """
    Raised when a transaction fails.
    
    Examples:
        TransactionError("Transaction already committed")
        TransactionError("Nested transaction not supported")
    """
    pass


class RelationshipError(DatabaseError):
    """
    Raised when a relationship operation fails.
    
    Examples:
        RelationshipError("Unknown relation: author")
        RelationshipError("Circular reference detected")
    """
    
    def __init__(self, message: str, relation: Optional[str] = None, model: Optional[str] = None):
        self.relation = relation
        self.model = model
        
        details = {}
        if relation:
            details["relation"] = relation
        if model:
            details["model"] = model
        
        super().__init__(message, details)


class ConfigurationError(DatabaseError):
    """
    Raised when database configuration is invalid.
    
    Examples:
        ConfigurationError("No adapter configured")
        ConfigurationError("Invalid database URL")
    """
    pass

