"""
PyNext Supabase Exceptions.

A comprehensive hierarchy of exceptions for all Supabase operations.
Designed to be:
- Easy to catch (specific exceptions inherit from general ones)
- Informative (include context about what went wrong)
- AI-friendly (clear names that explain the error)

Exception Hierarchy:
    SupabaseError (base)
    ├── ConfigurationError
    │   ├── MissingURLError
    │   ├── MissingKeyError
    │   └── InvalidURLError
    ├── AuthError
    │   ├── InvalidCredentialsError
    │   ├── UserExistsError
    │   ├── UserNotFoundError
    │   ├── SessionExpiredError
    │   ├── InvalidTokenError
    │   └── OAuthError
    ├── StorageError
    │   ├── BucketNotFoundError
    │   ├── FileNotFoundError
    │   ├── UploadError
    │   ├── DownloadError
    │   └── PermissionDeniedError
    ├── RealtimeError
    │   ├── ConnectionError
    │   ├── SubscriptionError
    │   └── ChannelError
    ├── FunctionError
    │   ├── FunctionNotFoundError
    │   ├── FunctionTimeoutError
    │   └── FunctionInvocationError
    └── RLSError
        ├── PolicySyntaxError
        ├── PolicyConflictError
        └── SyncError
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


# =============================================================================
# BASE EXCEPTION
# =============================================================================

@dataclass
class SupabaseError(Exception):
    """
    Base exception for all Supabase-related errors.
    
    All Supabase exceptions inherit from this, so you can catch everything with:
    
        try:
            await db.auth.sign_in(email, password)
        except SupabaseError as e:
            print(f"Supabase error: {e.message}")
    
    Attributes:
        message: Human-readable error description
        code: Error code from Supabase (if available)
        details: Additional context about the error
    """
    message: str
    code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    
    def __str__(self) -> str:
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r}, code={self.code!r})"


# =============================================================================
# CONFIGURATION ERRORS
# =============================================================================

@dataclass
class ConfigurationError(SupabaseError):
    """
    Error in Supabase configuration.
    
    Raised when the Supabase client cannot be initialized due to
    missing or invalid configuration.
    """
    pass


@dataclass
class MissingURLError(ConfigurationError):
    """
    Supabase URL is not provided.
    
    Example:
        # This will raise MissingURLError
        db = Supabase()  # No URL provided!
        
        # Fix: Provide URL or set SUPABASE_URL environment variable
        db = Supabase("https://xyz.supabase.co")
    """
    message: str = "Supabase URL is required. Provide it as first argument or set SUPABASE_URL environment variable."


@dataclass
class MissingKeyError(ConfigurationError):
    """
    Supabase API key is not provided.
    
    Example:
        # This will raise MissingKeyError if SUPABASE_KEY not in env
        db = Supabase("https://xyz.supabase.co")
        
        # Fix: Provide key or set SUPABASE_KEY environment variable
        db = Supabase("https://xyz.supabase.co", key="your-anon-key")
    """
    message: str = "Supabase API key is required. Provide it as 'key' argument or set SUPABASE_KEY environment variable."


@dataclass
class InvalidURLError(ConfigurationError):
    """
    Supabase URL is malformed or invalid.
    
    Valid URLs look like: https://xyz.supabase.co
    """
    url: str = ""
    message: str = field(default="")
    
    def __post_init__(self):
        if not self.message:
            self.message = f"Invalid Supabase URL: '{self.url}'. Expected format: https://xyz.supabase.co"


# =============================================================================
# AUTHENTICATION ERRORS
# =============================================================================

@dataclass
class AuthError(SupabaseError):
    """
    Base exception for authentication errors.
    
    Catch all auth errors with:
    
        try:
            await db.auth.sign_in(email, password)
        except AuthError as e:
            print(f"Authentication failed: {e.message}")
    """
    pass


@dataclass
class InvalidCredentialsError(AuthError):
    """
    Email or password is incorrect.
    
    Raised when sign_in fails due to wrong credentials.
    """
    message: str = "Invalid email or password."
    code: str = "invalid_credentials"


@dataclass
class UserExistsError(AuthError):
    """
    User already exists with this email.
    
    Raised when sign_up fails because email is already registered.
    """
    email: str = ""
    message: str = field(default="")
    code: str = "user_already_exists"
    
    def __post_init__(self):
        if not self.message:
            self.message = f"User already exists with email: {self.email}"


@dataclass
class UserNotFoundError(AuthError):
    """
    User does not exist.
    
    Raised when trying to perform operations on a non-existent user.
    """
    email: str = ""
    message: str = field(default="")
    code: str = "user_not_found"
    
    def __post_init__(self):
        if not self.message:
            self.message = f"User not found: {self.email}"


@dataclass
class SessionExpiredError(AuthError):
    """
    User session has expired.
    
    The user needs to sign in again or refresh their token.
    """
    message: str = "Session has expired. Please sign in again."
    code: str = "session_expired"


@dataclass
class InvalidTokenError(AuthError):
    """
    Token is invalid or malformed.
    
    This can happen with:
    - Expired JWT tokens
    - Tampered tokens
    - Tokens from a different Supabase project
    """
    message: str = "Invalid or expired token."
    code: str = "invalid_token"


@dataclass
class OAuthError(AuthError):
    """
    OAuth authentication failed.
    
    This can happen when:
    - OAuth provider returns an error
    - State parameter mismatch (possible CSRF)
    - OAuth code exchange fails
    """
    provider: str = ""
    message: str = field(default="")
    code: str = "oauth_error"
    
    def __post_init__(self):
        if not self.message:
            self.message = f"OAuth authentication failed for provider: {self.provider}"


@dataclass
class WeakPasswordError(AuthError):
    """
    Password doesn't meet security requirements.
    
    Supabase requires passwords to be at least 6 characters.
    """
    message: str = "Password is too weak. Must be at least 6 characters."
    code: str = "weak_password"


@dataclass
class EmailNotConfirmedError(AuthError):
    """
    Email has not been confirmed.
    
    User needs to click the confirmation link sent to their email.
    """
    email: str = ""
    message: str = field(default="")
    code: str = "email_not_confirmed"
    
    def __post_init__(self):
        if not self.message:
            self.message = f"Email not confirmed: {self.email}. Check inbox for confirmation link."


# =============================================================================
# STORAGE ERRORS
# =============================================================================

@dataclass
class StorageError(SupabaseError):
    """
    Base exception for storage errors.
    
    Catch all storage errors with:
    
        try:
            await db.storage.upload("bucket", "path", file)
        except StorageError as e:
            print(f"Storage error: {e.message}")
    """
    pass


@dataclass
class BucketNotFoundError(StorageError):
    """
    Storage bucket does not exist.
    
    Create the bucket first:
        await db.storage.create_bucket("my-bucket")
    """
    bucket: str = ""
    message: str = field(default="")
    code: str = "bucket_not_found"
    
    def __post_init__(self):
        if not self.message:
            self.message = f"Bucket not found: '{self.bucket}'. Create it with db.storage.create_bucket('{self.bucket}')"


@dataclass
class FileNotFoundError(StorageError):
    """
    File does not exist in storage.
    
    The requested file path does not exist in the bucket.
    """
    bucket: str = ""
    path: str = ""
    message: str = field(default="")
    code: str = "file_not_found"
    
    def __post_init__(self):
        if not self.message:
            self.message = f"File not found: '{self.path}' in bucket '{self.bucket}'"


@dataclass
class UploadError(StorageError):
    """
    File upload failed.
    
    Common causes:
    - File too large
    - Invalid content type
    - Network issues
    """
    bucket: str = ""
    path: str = ""
    reason: str = ""
    message: str = field(default="")
    code: str = "upload_failed"
    
    def __post_init__(self):
        if not self.message:
            self.message = f"Failed to upload '{self.path}' to bucket '{self.bucket}': {self.reason}"


@dataclass
class DownloadError(StorageError):
    """
    File download failed.
    
    Common causes:
    - File doesn't exist
    - Permission denied
    - Network issues
    """
    bucket: str = ""
    path: str = ""
    reason: str = ""
    message: str = field(default="")
    code: str = "download_failed"
    
    def __post_init__(self):
        if not self.message:
            self.message = f"Failed to download '{self.path}' from bucket '{self.bucket}': {self.reason}"


@dataclass
class PermissionDeniedError(StorageError):
    """
    Permission denied for storage operation.
    
    Check RLS policies for the bucket.
    For admin operations, use service_role_key.
    """
    bucket: str = ""
    operation: str = ""
    message: str = field(default="")
    code: str = "permission_denied"
    
    def __post_init__(self):
        if not self.message:
            self.message = f"Permission denied: {self.operation} on bucket '{self.bucket}'"


@dataclass
class FileTooLargeError(StorageError):
    """
    File exceeds maximum size limit.
    """
    size_bytes: int = 0
    max_bytes: int = 0
    message: str = field(default="")
    code: str = "file_too_large"
    
    def __post_init__(self):
        if not self.message:
            size_mb = self.size_bytes / (1024 * 1024)
            max_mb = self.max_bytes / (1024 * 1024)
            self.message = f"File too large: {size_mb:.1f}MB exceeds limit of {max_mb:.1f}MB"


# =============================================================================
# REALTIME ERRORS
# =============================================================================

@dataclass
class RealtimeError(SupabaseError):
    """
    Base exception for realtime errors.
    
    Catch all realtime errors with:
    
        try:
            await db.realtime.subscribe("users")
        except RealtimeError as e:
            print(f"Realtime error: {e.message}")
    """
    pass


@dataclass
class RealtimeConnectionError(RealtimeError):
    """
    Failed to connect to Supabase Realtime.
    
    Common causes:
    - Network issues
    - Invalid API key
    - Supabase project is paused
    """
    message: str = "Failed to connect to Supabase Realtime. Check network and API key."
    code: str = "connection_failed"


@dataclass
class SubscriptionError(RealtimeError):
    """
    Failed to subscribe to a table/channel.
    
    Common causes:
    - Table doesn't exist
    - RLS policies block access
    - Invalid filter syntax
    """
    table: str = ""
    reason: str = ""
    message: str = field(default="")
    code: str = "subscription_failed"
    
    def __post_init__(self):
        if not self.message:
            self.message = f"Failed to subscribe to table '{self.table}': {self.reason}"


@dataclass
class ChannelError(RealtimeError):
    """
    Realtime channel error.
    
    The channel encountered an error during operation.
    """
    channel: str = ""
    message: str = field(default="")
    code: str = "channel_error"
    
    def __post_init__(self):
        if not self.message:
            self.message = f"Channel error on '{self.channel}'"


@dataclass
class AlreadySubscribedError(RealtimeError):
    """
    Already subscribed to this table/channel.
    
    Unsubscribe first before re-subscribing.
    """
    table: str = ""
    message: str = field(default="")
    code: str = "already_subscribed"
    
    def __post_init__(self):
        if not self.message:
            self.message = f"Already subscribed to table '{self.table}'. Unsubscribe first."


# =============================================================================
# EDGE FUNCTION ERRORS
# =============================================================================

@dataclass
class FunctionError(SupabaseError):
    """
    Base exception for Edge Function errors.
    
    Catch all function errors with:
    
        try:
            await db.functions.invoke("my-function", {"data": "value"})
        except FunctionError as e:
            print(f"Function error: {e.message}")
    """
    pass


@dataclass
class FunctionNotFoundError(FunctionError):
    """
    Edge Function does not exist.
    
    Check that the function is deployed in your Supabase project.
    """
    function_name: str = ""
    message: str = field(default="")
    code: str = "function_not_found"
    
    def __post_init__(self):
        if not self.message:
            self.message = f"Edge Function not found: '{self.function_name}'"


@dataclass
class FunctionTimeoutError(FunctionError):
    """
    Edge Function execution timed out.
    
    The function took too long to respond.
    """
    function_name: str = ""
    timeout_seconds: float = 0
    message: str = field(default="")
    code: str = "function_timeout"
    
    def __post_init__(self):
        if not self.message:
            self.message = f"Edge Function '{self.function_name}' timed out after {self.timeout_seconds}s"


@dataclass
class FunctionInvocationError(FunctionError):
    """
    Edge Function invocation failed.
    
    The function returned an error or threw an exception.
    """
    function_name: str = ""
    status_code: int = 0
    response_body: str = ""
    message: str = field(default="")
    code: str = "invocation_failed"
    
    def __post_init__(self):
        if not self.message:
            self.message = f"Edge Function '{self.function_name}' failed with status {self.status_code}: {self.response_body}"


# =============================================================================
# RLS (ROW LEVEL SECURITY) ERRORS
# =============================================================================

@dataclass
class RLSError(SupabaseError):
    """
    Base exception for Row Level Security errors.
    
    Catch all RLS errors with:
    
        try:
            await db.rls.sync()
        except RLSError as e:
            print(f"RLS error: {e.message}")
    """
    pass


@dataclass
class PolicySyntaxError(RLSError):
    """
    RLS policy has invalid SQL syntax.
    
    Check the policy expression for SQL errors.
    """
    table: str = ""
    policy_name: str = ""
    expression: str = ""
    sql_error: str = ""
    message: str = field(default="")
    code: str = "policy_syntax_error"
    
    def __post_init__(self):
        if not self.message:
            self.message = f"Invalid policy '{self.policy_name}' on table '{self.table}': {self.sql_error}"


@dataclass
class PolicyConflictError(RLSError):
    """
    RLS policy conflicts with existing policy.
    
    A policy with this name already exists on the table.
    """
    table: str = ""
    policy_name: str = ""
    message: str = field(default="")
    code: str = "policy_conflict"
    
    def __post_init__(self):
        if not self.message:
            self.message = f"Policy '{self.policy_name}' already exists on table '{self.table}'"


@dataclass
class SyncError(RLSError):
    """
    Failed to sync RLS policies with Supabase.
    
    This usually requires service_role_key with admin permissions.
    """
    reason: str = ""
    message: str = field(default="")
    code: str = "sync_failed"
    
    def __post_init__(self):
        if not self.message:
            self.message = f"Failed to sync RLS policies: {self.reason}"


@dataclass
class ServiceRoleRequiredError(RLSError):
    """
    Operation requires service_role_key.
    
    Provide service_role_key when initializing Supabase:
        db = Supabase(url, key, service_role_key="...")
    """
    operation: str = ""
    message: str = field(default="")
    code: str = "service_role_required"
    
    def __post_init__(self):
        if not self.message:
            self.message = f"Operation '{self.operation}' requires service_role_key. Initialize with: Supabase(url, key, service_role_key='...')"


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def from_supabase_exception(error: Exception, context: Optional[Dict[str, Any]] = None) -> SupabaseError:
    """
    Convert a supabase-py exception to a PyNext SupabaseError.
    
    This maps the underlying library's exceptions to our hierarchy.
    
    Args:
        error: Exception from supabase-py
        context: Additional context (table name, operation, etc.)
    
    Returns:
        Appropriate SupabaseError subclass
    """
    # If already a SupabaseError, just return it (don't re-wrap)
    if isinstance(error, SupabaseError):
        return error
    
    context = context or {}
    error_str = str(error).lower()
    
    # Auth errors
    if "invalid login credentials" in error_str:
        return InvalidCredentialsError()
    if "user already registered" in error_str:
        return UserExistsError(email=context.get("email", ""))
    if "user not found" in error_str:
        return UserNotFoundError(email=context.get("email", ""))
    if "token" in error_str and ("expired" in error_str or "invalid" in error_str):
        return InvalidTokenError()
    if "password" in error_str and "weak" in error_str:
        return WeakPasswordError()
    
    # Storage errors
    if "bucket" in error_str and "not found" in error_str:
        return BucketNotFoundError(bucket=context.get("bucket", ""))
    if "object not found" in error_str or ("file" in error_str and "not found" in error_str):
        return FileNotFoundError(bucket=context.get("bucket", ""), path=context.get("path", ""))
    
    # Function errors
    if "function" in error_str and "not found" in error_str:
        return FunctionNotFoundError(function_name=context.get("function_name", ""))
    if "timeout" in error_str:
        return FunctionTimeoutError(function_name=context.get("function_name", ""))
    
    # Generic error
    return SupabaseError(message=str(error), details=context)

