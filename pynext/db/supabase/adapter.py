"""
PyNext Supabase Adapter.

The main entry point for Supabase integration. Wraps the official supabase-py
client with a simpler, more Pythonic API.

Why This Exists:
    Supabase-py is a great library, but it's designed for general Python use.
    PyNext wraps it to provide:
    - Simpler initialization (URL from env, key from env)
    - Consistent error handling (our exception hierarchy)
    - Integration with PyNext's reactive signals
    - RLS policy decorators and migration generation

Usage (Stupid Easy):
    # Level 1: Just works (reads from environment)
    from pynext.db.supabase import Supabase
    db = Supabase("https://xyz.supabase.co")
    
    # Level 2: Explicit configuration
    db = Supabase("https://xyz.supabase.co", key="your-anon-key")
    
    # Level 3: Full control
    db = Supabase(
        url="https://xyz.supabase.co",
        anon_key="your-anon-key",
        service_role_key="your-service-key",  # For admin operations
        auto_refresh_token=True,
        persist_session=True,
    )

Architecture:
    Supabase
    ├── auth      → SupabaseAuth (sign_up, sign_in, etc.)
    ├── storage   → SupabaseStorage (upload, download, etc.)
    ├── realtime  → SupabaseRealtime (subscribe, on_insert, etc.)
    ├── functions → SupabaseFunctions (invoke)
    └── rls       → SupabaseRLS (policy decorators, sync)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Union
from urllib.parse import urlparse
import os
import re

from .exceptions import (
    SupabaseError,
    ConfigurationError,
    MissingURLError,
    MissingKeyError,
    InvalidURLError,
)


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class SupabaseConfig:
    """
    Configuration for Supabase connection.
    
    Attributes:
        url: Your Supabase project URL (e.g., https://xyz.supabase.co)
        anon_key: Your Supabase anon/public API key
        service_role_key: Optional admin key for privileged operations
        auto_refresh_token: Automatically refresh auth tokens (default: True)
        persist_session: Persist auth session across restarts (default: True)
        realtime_enabled: Enable realtime subscriptions (default: True)
        storage_url: Custom storage URL (auto-detected if not provided)
        functions_url: Custom functions URL (auto-detected if not provided)
        timeout: Request timeout in seconds (default: 30)
        headers: Additional headers for all requests
    
    Example:
        config = SupabaseConfig(
            url="https://xyz.supabase.co",
            anon_key="eyJ...",
            service_role_key="eyJ...",  # Optional
        )
        db = Supabase(config=config)
    """
    url: str
    anon_key: str
    service_role_key: Optional[str] = None
    auto_refresh_token: bool = True
    persist_session: bool = True
    realtime_enabled: bool = True
    storage_url: Optional[str] = None
    functions_url: Optional[str] = None
    timeout: float = 30.0
    headers: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate_url()
        self._validate_key()
        self._derive_urls()
    
    def _validate_url(self):
        """Ensure URL is valid Supabase project URL."""
        # Clean up URL first
        if self.url:
            self.url = self.url.strip().rstrip("/")
        
        # Check if URL is missing after cleanup
        if not self.url:
            raise MissingURLError()
        
        # Parse and validate
        try:
            parsed = urlparse(self.url)
            if not parsed.scheme or not parsed.netloc:
                raise InvalidURLError(url=self.url)
            if parsed.scheme not in ("http", "https"):
                raise InvalidURLError(
                    url=self.url,
                    message=f"Invalid URL scheme: '{parsed.scheme}'. Must be http or https."
                )
        except Exception as e:
            if isinstance(e, InvalidURLError):
                raise
            raise InvalidURLError(url=self.url) from e
    
    def _validate_key(self):
        """Ensure API key is present."""
        if not self.anon_key:
            raise MissingKeyError()
        
        # Basic JWT format check (header.payload.signature)
        if not re.match(r"^eyJ[\w-]+\.[\w-]+\.[\w-]+$", self.anon_key):
            # Not a strict error - key format might change
            pass
    
    def _derive_urls(self):
        """Derive storage and functions URLs from main URL if not provided."""
        if not self.storage_url:
            self.storage_url = f"{self.url}/storage/v1"
        if not self.functions_url:
            self.functions_url = f"{self.url}/functions/v1"
    
    @property
    def rest_url(self) -> str:
        """REST API URL for database queries."""
        return f"{self.url}/rest/v1"
    
    @property
    def auth_url(self) -> str:
        """Auth API URL."""
        return f"{self.url}/auth/v1"
    
    @property
    def realtime_url(self) -> str:
        """Realtime WebSocket URL."""
        # Convert https:// to wss:// or http:// to ws://
        ws_url = self.url.replace("https://", "wss://").replace("http://", "ws://")
        return f"{ws_url}/realtime/v1"
    
    @classmethod
    def from_env(cls, url: Optional[str] = None) -> "SupabaseConfig":
        """
        Create config from environment variables.
        
        Environment Variables:
            SUPABASE_URL: Project URL
            SUPABASE_KEY: Anon/public key
            SUPABASE_SERVICE_ROLE_KEY: Optional service role key
        
        Args:
            url: Optional URL override (reads from SUPABASE_URL if not provided)
        
        Returns:
            SupabaseConfig instance
        
        Raises:
            MissingURLError: If URL not provided and SUPABASE_URL not set
            MissingKeyError: If SUPABASE_KEY not set
        """
        final_url = url or os.environ.get("SUPABASE_URL", "")
        anon_key = os.environ.get("SUPABASE_KEY", "")
        service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        
        return cls(
            url=final_url,
            anon_key=anon_key,
            service_role_key=service_role_key,
        )


# =============================================================================
# MAIN ADAPTER CLASS
# =============================================================================

class Supabase:
    """
    Main Supabase adapter for PyNext.
    
    This is your entry point for all Supabase operations:
    - Authentication (sign up, sign in, OAuth)
    - Storage (file upload, download)
    - Realtime (subscribe to database changes)
    - Edge Functions (invoke serverless functions)
    - RLS (row level security policy management)
    
    Usage (Stupid Easy):
        # Most common - just provide URL, key from environment
        db = Supabase("https://xyz.supabase.co")
        
        # Explicit key
        db = Supabase("https://xyz.supabase.co", key="your-anon-key")
        
        # Full configuration
        db = Supabase(
            url="https://xyz.supabase.co",
            anon_key="your-anon-key",
            service_role_key="your-service-key",
        )
    
    Accessing Services:
        db.auth.sign_up(email, password)      # Authentication
        db.storage.upload(bucket, path, file) # File storage
        db.realtime.subscribe("users")        # Real-time updates
        db.functions.invoke("function-name")  # Edge functions
        db.rls.sync()                         # RLS policy sync
    
    Database Queries:
        # Query using PostgrestClient
        result = await db.table("users").select("*").execute()
        
        # Insert
        await db.table("users").insert({"name": "Alice"}).execute()
        
        # Update
        await db.table("users").update({"name": "Bob"}).eq("id", 1).execute()
        
        # Delete
        await db.table("users").delete().eq("id", 1).execute()
    """
    
    def __init__(
        self,
        url: Optional[str] = None,
        key: Optional[str] = None,
        *,
        anon_key: Optional[str] = None,
        service_role_key: Optional[str] = None,
        auto_refresh_token: bool = True,
        persist_session: bool = True,
        realtime_enabled: bool = True,
        timeout: float = 30.0,
        headers: Optional[Dict[str, str]] = None,
        config: Optional[SupabaseConfig] = None,
    ):
        """
        Initialize Supabase adapter.
        
        Args:
            url: Supabase project URL (or set SUPABASE_URL env var)
            key: API key shorthand (same as anon_key)
            anon_key: Supabase anon/public key (or set SUPABASE_KEY env var)
            service_role_key: Admin key for privileged operations
            auto_refresh_token: Auto-refresh auth tokens (default: True)
            persist_session: Persist auth session (default: True)
            realtime_enabled: Enable realtime subscriptions (default: True)
            timeout: Request timeout in seconds (default: 30)
            headers: Additional headers for all requests
            config: Full SupabaseConfig object (overrides other params)
        
        Examples:
            # Simple - reads key from SUPABASE_KEY env var
            db = Supabase("https://xyz.supabase.co")
            
            # Explicit key
            db = Supabase("https://xyz.supabase.co", key="eyJ...")
            
            # With service role for admin operations
            db = Supabase(
                "https://xyz.supabase.co",
                key="eyJ...",
                service_role_key="eyJ..."
            )
        """
        # Use provided config or build from parameters
        if config:
            self._config = config
        else:
            # Resolve URL
            final_url = url or os.environ.get("SUPABASE_URL", "")
            
            # Resolve key (key is shorthand for anon_key)
            final_key = key or anon_key or os.environ.get("SUPABASE_KEY", "")
            
            # Resolve service role key
            final_service_key = service_role_key or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
            
            self._config = SupabaseConfig(
                url=final_url,
                anon_key=final_key,
                service_role_key=final_service_key,
                auto_refresh_token=auto_refresh_token,
                persist_session=persist_session,
                realtime_enabled=realtime_enabled,
                timeout=timeout,
                headers=headers or {},
            )
        
        # Initialize the underlying supabase-py client
        self._client = None
        self._admin_client = None  # Uses service_role_key
        self._initialized = False
        
        # Lazy-loaded service modules
        self._auth = None
        self._storage = None
        self._realtime = None
        self._functions = None
        self._rls = None
    
    def _ensure_initialized(self):
        """Initialize the underlying supabase-py client if not already done."""
        if self._initialized:
            return
        
        try:
            from supabase import create_client, Client
            
            # Create main client with anon key
            self._client = create_client(
                self._config.url,
                self._config.anon_key,
            )
            
            # Create admin client if service role key provided
            if self._config.service_role_key:
                self._admin_client = create_client(
                    self._config.url,
                    self._config.service_role_key,
                )
            
            self._initialized = True
            
        except ImportError:
            raise ConfigurationError(
                message="supabase-py is not installed. Install with: pip install supabase"
            )
        except Exception as e:
            raise ConfigurationError(
                message=f"Failed to initialize Supabase client: {e}",
                details={"url": self._config.url}
            )
    
    @property
    def config(self) -> SupabaseConfig:
        """Get the current configuration."""
        return self._config
    
    @property
    def client(self):
        """
        Get the underlying supabase-py Client.
        
        Use this for direct access to supabase-py features not wrapped by PyNext.
        """
        self._ensure_initialized()
        return self._client
    
    @property
    def admin_client(self):
        """
        Get the admin client (uses service_role_key).
        
        Returns None if service_role_key was not provided.
        """
        self._ensure_initialized()
        return self._admin_client
    
    # =========================================================================
    # SERVICE ACCESSORS
    # =========================================================================
    
    @property
    def auth(self) -> "SupabaseAuth":
        """
        Authentication service.
        
        Usage:
            # Sign up
            user = await db.auth.sign_up("email@example.com", "password")
            
            # Sign in
            session = await db.auth.sign_in("email@example.com", "password")
            
            # Get current user
            user = await db.auth.get_user()
            
            # Sign out
            await db.auth.sign_out()
        """
        if self._auth is None:
            from .auth import SupabaseAuth
            self._auth = SupabaseAuth(self)
        return self._auth
    
    @property
    def storage(self) -> "SupabaseStorage":
        """
        Storage service for file operations.
        
        Usage:
            # Upload file
            await db.storage.upload("bucket", "path/file.png", file_data)
            
            # Download file
            data = await db.storage.download("bucket", "path/file.png")
            
            # Get public URL
            url = db.storage.get_public_url("bucket", "path/file.png")
            
            # Delete file
            await db.storage.delete("bucket", "path/file.png")
        """
        if self._storage is None:
            from .storage import SupabaseStorage
            self._storage = SupabaseStorage(self)
        return self._storage
    
    @property
    def realtime(self) -> "SupabaseRealtime":
        """
        Realtime subscription service.
        
        Usage:
            # Subscribe with decorator
            @on_insert("users")
            async def handle_new_user(record):
                print(f"New user: {record}")
            
            # Subscribe with signals
            users = await db.realtime.subscribe("users")
            
            # Start listening
            await db.realtime.start()
        """
        if self._realtime is None:
            from .realtime import SupabaseRealtime
            self._realtime = SupabaseRealtime(self)
        return self._realtime
    
    @property
    def functions(self) -> "SupabaseFunctions":
        """
        Edge Functions service.
        
        Usage:
            result = await db.functions.invoke("function-name", {
                "arg1": "value1",
                "arg2": "value2"
            })
        """
        if self._functions is None:
            from .functions import SupabaseFunctions
            self._functions = SupabaseFunctions(self)
        return self._functions
    
    @property
    def rls(self) -> "SupabaseRLS":
        """
        Row Level Security management.
        
        Usage:
            # Define policies with decorator
            @policy("users", "select")
            def users_select():
                return "auth.uid() = id"
            
            # Generate migration
            migration = generate_rls_migration()
            
            # Or sync directly
            await db.rls.sync()
        """
        if self._rls is None:
            from .rls import SupabaseRLS
            self._rls = SupabaseRLS(self)
        return self._rls
    
    # =========================================================================
    # DATABASE QUERY SHORTCUTS
    # =========================================================================
    
    def table(self, table_name: str):
        """
        Start a query on a table.
        
        This returns the PostgrestClient's table query builder.
        
        Args:
            table_name: Name of the table to query
        
        Returns:
            Postgrest QueryBuilder for chaining
        
        Example:
            # Select all users
            result = await db.table("users").select("*").execute()
            
            # Select with filter
            result = await db.table("users").select("*").eq("status", "active").execute()
            
            # Insert
            await db.table("users").insert({"name": "Alice", "email": "alice@example.com"}).execute()
            
            # Update
            await db.table("users").update({"status": "inactive"}).eq("id", 123).execute()
            
            # Delete
            await db.table("users").delete().eq("id", 123).execute()
        """
        self._ensure_initialized()
        return self._client.table(table_name)
    
    def from_(self, table_name: str):
        """
        Alias for table() - SQL-style syntax.
        
        Example:
            result = await db.from_("users").select("*").execute()
        """
        return self.table(table_name)
    
    def rpc(self, function_name: str, params: Optional[Dict[str, Any]] = None):
        """
        Call a Postgres function (RPC).
        
        Args:
            function_name: Name of the Postgres function
            params: Parameters to pass to the function
        
        Returns:
            Query result
        
        Example:
            # Call a Postgres function
            result = await db.rpc("get_user_stats", {"user_id": 123}).execute()
        """
        self._ensure_initialized()
        return self._client.rpc(function_name, params or {})
    
    # =========================================================================
    # LIFECYCLE
    # =========================================================================
    
    async def close(self):
        """
        Close all connections and cleanup resources.
        
        Call this when shutting down your application.
        """
        if self._realtime:
            await self._realtime.stop()
        
        # Note: supabase-py doesn't have explicit close, but we clean up our state
        self._initialized = False
        self._client = None
        self._admin_client = None
    
    async def __aenter__(self):
        """Support async context manager."""
        self._ensure_initialized()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup on context exit."""
        await self.close()
    
    def __repr__(self) -> str:
        return f"Supabase(url={self._config.url!r}, initialized={self._initialized})"


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_supabase(
    url: Optional[str] = None,
    key: Optional[str] = None,
    **kwargs
) -> Supabase:
    """
    Factory function to create a Supabase instance.
    
    This is an alternative to the Supabase class constructor.
    
    Args:
        url: Supabase project URL
        key: API key
        **kwargs: Additional configuration options
    
    Returns:
        Configured Supabase instance
    
    Example:
        db = create_supabase("https://xyz.supabase.co", "eyJ...")
    """
    return Supabase(url=url, key=key, **kwargs)


def get_supabase_from_env() -> Supabase:
    """
    Create a Supabase instance from environment variables.
    
    Required Environment Variables:
        SUPABASE_URL: Your Supabase project URL
        SUPABASE_KEY: Your Supabase anon/public key
    
    Optional Environment Variables:
        SUPABASE_SERVICE_ROLE_KEY: Admin key for privileged operations
    
    Returns:
        Configured Supabase instance
    
    Raises:
        MissingURLError: If SUPABASE_URL not set
        MissingKeyError: If SUPABASE_KEY not set
    
    Example:
        # In .env file:
        # SUPABASE_URL=https://xyz.supabase.co
        # SUPABASE_KEY=eyJ...
        
        db = get_supabase_from_env()
    """
    return Supabase(
        url=os.environ.get("SUPABASE_URL"),
        key=os.environ.get("SUPABASE_KEY"),
        service_role_key=os.environ.get("SUPABASE_SERVICE_ROLE_KEY"),
    )

