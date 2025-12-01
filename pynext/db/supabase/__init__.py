"""
PyNext Supabase Integration.

A simple, Pythonic wrapper around Supabase for PyNext applications.

Quick Start:
    from pynext.db.supabase import Supabase
    
    # Connect to Supabase
    db = Supabase("https://xyz.supabase.co", key="your-anon-key")
    
    # Or from environment
    db = Supabase("https://xyz.supabase.co")  # Reads SUPABASE_KEY from env

Authentication:
    # Sign up
    user = await db.auth.sign_up("user@example.com", "password123")
    
    # Sign in
    session = await db.auth.sign_in("user@example.com", "password123")
    
    # Get current user
    user = await db.auth.get_user()
    
    # Sign out
    await db.auth.sign_out()

Storage:
    # Upload file
    await db.storage.upload("avatars", "user_123.png", file_bytes)
    
    # Download file
    data = await db.storage.download("avatars", "user_123.png")
    
    # Get public URL
    url = db.storage.get_public_url("avatars", "user_123.png")

Realtime Subscriptions:
    # Using decorators (server-side)
    @on_insert("users")
    async def handle_new_user(record):
        print(f"New user: {record['email']}")
    
    @on_update("orders", columns=["status"])
    async def handle_order_status(old, new):
        if new['status'] == 'shipped':
            await notify_customer(new['user_id'])
    
    await db.realtime.start()
    
    # Using signals (frontend)
    users = await db.realtime.subscribe("users")
    
    def UserList():
        return ul([li(user['name']) for user in users()])

Edge Functions:
    result = await db.functions.invoke("send-email", {
        "to": "user@example.com",
        "subject": "Hello!",
        "body": "Welcome!"
    })

Row Level Security (RLS):
    @policy("users", "select")
    def users_select():
        '''Users can only see their own data'''
        return "auth.uid() = id"
    
    @policy("posts", "select")
    def posts_select():
        '''Public posts visible to all'''
        return "is_public = true OR auth.uid() = author_id"
    
    # Generate migration
    migration = generate_rls_migration()
    
    # Or sync directly
    await db.rls.sync()

For more details, see: docs/features/SUPABASE.md
"""

# =============================================================================
# MAIN ADAPTER
# =============================================================================

from pynext.db.supabase.adapter import (
    Supabase,
    SupabaseConfig,
    create_supabase,
    get_supabase_from_env,
)

# =============================================================================
# EXCEPTIONS
# =============================================================================

from pynext.db.supabase.exceptions import (
    # Base
    SupabaseError,
    # Configuration
    ConfigurationError,
    MissingURLError,
    MissingKeyError,
    InvalidURLError,
    # Auth
    AuthError,
    InvalidCredentialsError,
    UserExistsError,
    UserNotFoundError,
    SessionExpiredError,
    InvalidTokenError,
    OAuthError,
    WeakPasswordError,
    EmailNotConfirmedError,
    # Storage
    StorageError,
    BucketNotFoundError,
    FileNotFoundError,
    UploadError,
    DownloadError,
    PermissionDeniedError,
    FileTooLargeError,
    # Realtime
    RealtimeError,
    RealtimeConnectionError,
    SubscriptionError,
    ChannelError,
    AlreadySubscribedError,
    # Functions
    FunctionError,
    FunctionNotFoundError,
    FunctionTimeoutError,
    FunctionInvocationError,
    # RLS
    RLSError,
    PolicySyntaxError,
    PolicyConflictError,
    SyncError,
    ServiceRoleRequiredError,
    # Helper
    from_supabase_exception,
)

# =============================================================================
# AUTH
# =============================================================================

from pynext.db.supabase.auth import (
    SupabaseAuth,
    User,
    Session,
    AuthConfig,
    OAuthProvider,
)

# =============================================================================
# STORAGE
# =============================================================================

from pynext.db.supabase.storage import (
    SupabaseStorage,
    StorageFile,
    Bucket,
    UploadResult,
    SignedURL,
)

# =============================================================================
# REALTIME
# =============================================================================

from pynext.db.supabase.realtime import (
    SupabaseRealtime,
    RealtimeEvent,
    Subscription,
    RealtimeConfig,
    EventType,
    ChannelState,
    Signal,
    TableSignal,
    # Decorators
    on_insert,
    on_update,
    on_delete,
    on_change,
)

# =============================================================================
# EDGE FUNCTIONS
# =============================================================================

from pynext.db.supabase.functions import (
    SupabaseFunctions,
    FunctionResponse,
    FunctionsConfig,
)

# =============================================================================
# ROW LEVEL SECURITY
# =============================================================================

from pynext.db.supabase.rls import (
    SupabaseRLS,
    Policy,
    PolicyDiff,
    RLSConfig,
    PolicyOperation,
    PolicyCommand,
    # Decorators
    policy,
    select_policy,
    insert_policy,
    update_policy,
    delete_policy,
    # Migration generation
    generate_rls_migration,
    generate_rls_down_migration,
    # Common patterns
    own_data_policy,
    public_read_policy,
    authenticated_only_policy,
    role_based_policy,
)

# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Main adapter
    "Supabase",
    "SupabaseConfig",
    "create_supabase",
    "get_supabase_from_env",
    
    # Exceptions - Base
    "SupabaseError",
    "ConfigurationError",
    "MissingURLError",
    "MissingKeyError",
    "InvalidURLError",
    
    # Exceptions - Auth
    "AuthError",
    "InvalidCredentialsError",
    "UserExistsError",
    "UserNotFoundError",
    "SessionExpiredError",
    "InvalidTokenError",
    "OAuthError",
    "WeakPasswordError",
    "EmailNotConfirmedError",
    
    # Exceptions - Storage
    "StorageError",
    "BucketNotFoundError",
    "FileNotFoundError",
    "UploadError",
    "DownloadError",
    "PermissionDeniedError",
    "FileTooLargeError",
    
    # Exceptions - Realtime
    "RealtimeError",
    "RealtimeConnectionError",
    "SubscriptionError",
    "ChannelError",
    "AlreadySubscribedError",
    
    # Exceptions - Functions
    "FunctionError",
    "FunctionNotFoundError",
    "FunctionTimeoutError",
    "FunctionInvocationError",
    
    # Exceptions - RLS
    "RLSError",
    "PolicySyntaxError",
    "PolicyConflictError",
    "SyncError",
    "ServiceRoleRequiredError",
    
    # Exception helper
    "from_supabase_exception",
    
    # Auth
    "SupabaseAuth",
    "User",
    "Session",
    "AuthConfig",
    "OAuthProvider",
    
    # Storage
    "SupabaseStorage",
    "StorageFile",
    "Bucket",
    "UploadResult",
    "SignedURL",
    
    # Realtime
    "SupabaseRealtime",
    "RealtimeEvent",
    "Subscription",
    "RealtimeConfig",
    "EventType",
    "ChannelState",
    "Signal",
    "TableSignal",
    "on_insert",
    "on_update",
    "on_delete",
    "on_change",
    
    # Functions
    "SupabaseFunctions",
    "FunctionResponse",
    "FunctionsConfig",
    
    # RLS
    "SupabaseRLS",
    "Policy",
    "PolicyDiff",
    "RLSConfig",
    "PolicyOperation",
    "PolicyCommand",
    "policy",
    "select_policy",
    "insert_policy",
    "update_policy",
    "delete_policy",
    "generate_rls_migration",
    "generate_rls_down_migration",
    "own_data_policy",
    "public_read_policy",
    "authenticated_only_policy",
    "role_based_policy",
]

