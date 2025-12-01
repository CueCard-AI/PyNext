"""
PyNext Supabase Authentication.

Provides a simple, Pythonic API for Supabase authentication:
- Email/password sign up and sign in
- OAuth providers (Google, GitHub, etc.)
- Magic links and OTP
- Session management
- Password reset

Why This Exists:
    Supabase's GoTrue auth is powerful but has a complex API.
    We wrap it to provide:
    - Simpler method names (sign_up vs sign_up_with_email)
    - Consistent error handling
    - Async-first design
    - Type hints for better IDE support

Usage (Stupid Easy):
    from pynext.db.supabase import Supabase
    
    db = Supabase("https://xyz.supabase.co")
    
    # Sign up
    user = await db.auth.sign_up("email@example.com", "password123")
    
    # Sign in
    session = await db.auth.sign_in("email@example.com", "password123")
    
    # Get current user
    user = await db.auth.get_user()
    
    # Sign out
    await db.auth.sign_out()
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
from enum import Enum
import asyncio

from .exceptions import (
    AuthError,
    InvalidCredentialsError,
    UserExistsError,
    UserNotFoundError,
    SessionExpiredError,
    InvalidTokenError,
    OAuthError,
    WeakPasswordError,
    EmailNotConfirmedError,
    from_supabase_exception,
)

if TYPE_CHECKING:
    from .adapter import Supabase


# =============================================================================
# DATA MODELS
# =============================================================================

class OAuthProvider(str, Enum):
    """Supported OAuth providers."""
    GOOGLE = "google"
    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"
    AZURE = "azure"
    FACEBOOK = "facebook"
    TWITTER = "twitter"
    DISCORD = "discord"
    TWITCH = "twitch"
    SPOTIFY = "spotify"
    SLACK = "slack"
    LINKEDIN = "linkedin"
    APPLE = "apple"
    NOTION = "notion"
    ZOOM = "zoom"


@dataclass
class User:
    """
    Supabase user data model.
    
    Attributes:
        id: Unique user ID (UUID)
        email: User's email address
        phone: User's phone number (if provided)
        created_at: When the user was created
        updated_at: When the user was last updated
        confirmed_at: When email was confirmed (None if not confirmed)
        email_confirmed_at: Same as confirmed_at (alias)
        last_sign_in_at: When user last signed in
        role: User's role (usually 'authenticated')
        app_metadata: Metadata set by the application
        user_metadata: Metadata set by the user
        identities: Linked OAuth identities
    
    Example:
        user = await db.auth.get_user()
        print(f"User ID: {user.id}")
        print(f"Email: {user.email}")
        print(f"Signed up: {user.created_at}")
    """
    id: str
    email: Optional[str] = None
    phone: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    email_confirmed_at: Optional[datetime] = None
    last_sign_in_at: Optional[datetime] = None
    role: str = "authenticated"
    app_metadata: Dict[str, Any] = field(default_factory=dict)
    user_metadata: Dict[str, Any] = field(default_factory=dict)
    identities: List[Dict[str, Any]] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        """Create User from dictionary (API response)."""
        return cls(
            id=data.get("id", ""),
            email=data.get("email"),
            phone=data.get("phone"),
            created_at=_parse_datetime(data.get("created_at")),
            updated_at=_parse_datetime(data.get("updated_at")),
            confirmed_at=_parse_datetime(data.get("confirmed_at")),
            email_confirmed_at=_parse_datetime(data.get("email_confirmed_at")),
            last_sign_in_at=_parse_datetime(data.get("last_sign_in_at")),
            role=data.get("role", "authenticated"),
            app_metadata=data.get("app_metadata", {}),
            user_metadata=data.get("user_metadata", {}),
            identities=data.get("identities", []),
        )
    
    @property
    def is_confirmed(self) -> bool:
        """Check if user's email is confirmed."""
        return self.confirmed_at is not None or self.email_confirmed_at is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "email": self.email,
            "phone": self.phone,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "confirmed_at": self.confirmed_at.isoformat() if self.confirmed_at else None,
            "role": self.role,
            "app_metadata": self.app_metadata,
            "user_metadata": self.user_metadata,
        }


@dataclass
class Session:
    """
    Supabase session data model.
    
    A session contains the tokens needed to make authenticated requests.
    
    Attributes:
        access_token: JWT token for API requests
        refresh_token: Token to get a new access_token
        token_type: Usually "bearer"
        expires_in: Seconds until access_token expires
        expires_at: Unix timestamp when access_token expires
        user: The authenticated user
    
    Example:
        session = await db.auth.sign_in("email@example.com", "password")
        print(f"Token: {session.access_token}")
        print(f"Expires in: {session.expires_in} seconds")
        print(f"User: {session.user.email}")
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
    expires_at: Optional[int] = None
    user: Optional[User] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        """Create Session from dictionary (API response)."""
        user_data = data.get("user")
        return cls(
            access_token=data.get("access_token", ""),
            refresh_token=data.get("refresh_token", ""),
            token_type=data.get("token_type", "bearer"),
            expires_in=data.get("expires_in", 3600),
            expires_at=data.get("expires_at"),
            user=User.from_dict(user_data) if user_data else None,
        )
    
    @property
    def is_expired(self) -> bool:
        """Check if the session has expired."""
        if self.expires_at is None:
            return False
        import time
        return time.time() >= self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_type": self.token_type,
            "expires_in": self.expires_in,
            "expires_at": self.expires_at,
            "user": self.user.to_dict() if self.user else None,
        }


@dataclass
class AuthConfig:
    """
    Configuration for authentication behavior.
    
    Attributes:
        auto_refresh_token: Automatically refresh tokens before expiry
        persist_session: Save session to storage for persistence
        redirect_url: URL to redirect after OAuth sign in
        scopes: OAuth scopes to request
    """
    auto_refresh_token: bool = True
    persist_session: bool = True
    redirect_url: Optional[str] = None
    scopes: Optional[str] = None


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _parse_datetime(value: Optional[Union[str, int, float]]) -> Optional[datetime]:
    """Parse ISO datetime string or timestamp to datetime object."""
    if value is None:
        return None
    try:
        # Handle integer/float timestamps
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value)
        # Handle empty string
        if not value:
            return None
        # Handle various ISO formats
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except (ValueError, TypeError, OSError):
        return None


def _run_sync(coro):
    """Run coroutine synchronously (for compatibility)."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    
    if loop is None:
        return asyncio.run(coro)
    else:
        # We're in an async context, just return the coroutine
        return coro


# =============================================================================
# MAIN AUTH CLASS
# =============================================================================

class SupabaseAuth:
    """
    Supabase authentication service.
    
    Handles all authentication operations:
    - Email/password sign up and sign in
    - OAuth (Google, GitHub, etc.)
    - Magic links and OTP
    - Session management
    - Password reset
    
    Usage:
        db = Supabase("https://xyz.supabase.co")
        
        # Sign up
        user = await db.auth.sign_up("email@example.com", "password123")
        
        # Sign in
        session = await db.auth.sign_in("email@example.com", "password123")
        
        # Sign out
        await db.auth.sign_out()
    """
    
    def __init__(self, supabase: "Supabase"):
        """
        Initialize auth service.
        
        Args:
            supabase: Parent Supabase adapter instance
        """
        self._supabase = supabase
        self._current_session: Optional[Session] = None
        self._current_user: Optional[User] = None
    
    @property
    def _client(self):
        """Get the underlying supabase-py auth client."""
        self._supabase._ensure_initialized()
        return self._supabase.client.auth
    
    # =========================================================================
    # SIGN UP
    # =========================================================================
    
    async def sign_up(
        self,
        email: str,
        password: str,
        *,
        phone: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        redirect_to: Optional[str] = None,
        captcha_token: Optional[str] = None,
    ) -> User:
        """
        Create a new user account.
        
        Args:
            email: User's email address
            password: Password (min 6 characters)
            phone: Optional phone number
            data: Additional user metadata
            redirect_to: URL to redirect after email confirmation
            captcha_token: Captcha verification token (if enabled)
        
        Returns:
            The created User
        
        Raises:
            UserExistsError: If email already registered
            WeakPasswordError: If password is too short
            AuthError: For other authentication errors
        
        Example:
            user = await db.auth.sign_up(
                "alice@example.com",
                "secure-password-123",
                data={"full_name": "Alice Smith"}
            )
            print(f"Created user: {user.id}")
        """
        try:
            options = {}
            if data:
                options["data"] = data
            if redirect_to:
                options["email_redirect_to"] = redirect_to
            if captcha_token:
                options["captcha_token"] = captcha_token
            
            response = self._client.sign_up({
                "email": email,
                "password": password,
                "phone": phone,
                "options": options if options else None,
            })
            
            if response.user:
                user = User.from_dict(response.user.model_dump())
                self._current_user = user
                
                if response.session:
                    self._current_session = Session.from_dict(response.session.model_dump())
                
                return user
            else:
                raise AuthError(message="Sign up failed: No user returned")
                
        except Exception as e:
            error_str = str(e).lower()
            if "already registered" in error_str or "already exists" in error_str:
                raise UserExistsError(email=email)
            if "password" in error_str and ("weak" in error_str or "short" in error_str or "6" in error_str):
                raise WeakPasswordError()
            raise from_supabase_exception(e, {"email": email})
    
    # =========================================================================
    # SIGN IN
    # =========================================================================
    
    async def sign_in(
        self,
        email: str,
        password: str,
        *,
        captcha_token: Optional[str] = None,
    ) -> Session:
        """
        Sign in with email and password.
        
        Args:
            email: User's email address
            password: User's password
            captcha_token: Captcha verification token (if enabled)
        
        Returns:
            Session with access tokens
        
        Raises:
            InvalidCredentialsError: If email or password is wrong
            EmailNotConfirmedError: If email not verified (when required)
            AuthError: For other authentication errors
        
        Example:
            session = await db.auth.sign_in("alice@example.com", "password123")
            print(f"Signed in as: {session.user.email}")
            print(f"Token: {session.access_token}")
        """
        try:
            response = self._client.sign_in_with_password({
                "email": email,
                "password": password,
            })
            
            if response.session:
                session = Session.from_dict(response.session.model_dump())
                self._current_session = session
                if response.user:
                    self._current_user = User.from_dict(response.user.model_dump())
                    session.user = self._current_user
                return session
            else:
                raise InvalidCredentialsError()
                
        except Exception as e:
            error_str = str(e).lower()
            if "invalid" in error_str and ("credentials" in error_str or "login" in error_str or "password" in error_str):
                raise InvalidCredentialsError()
            if "not confirmed" in error_str or "confirm" in error_str:
                raise EmailNotConfirmedError(email=email)
            raise from_supabase_exception(e, {"email": email})
    
    async def sign_in_with_phone(
        self,
        phone: str,
        password: str,
    ) -> Session:
        """
        Sign in with phone number and password.
        
        Args:
            phone: User's phone number
            password: User's password
        
        Returns:
            Session with access tokens
        
        Raises:
            InvalidCredentialsError: If credentials are wrong
        """
        try:
            response = self._client.sign_in_with_password({
                "phone": phone,
                "password": password,
            })
            
            if response.session:
                session = Session.from_dict(response.session.model_dump())
                self._current_session = session
                if response.user:
                    self._current_user = User.from_dict(response.user.model_dump())
                    session.user = self._current_user
                return session
            else:
                raise InvalidCredentialsError()
                
        except Exception as e:
            raise from_supabase_exception(e, {"phone": phone})
    
    # =========================================================================
    # OAUTH
    # =========================================================================
    
    def get_oauth_url(
        self,
        provider: Union[str, OAuthProvider],
        *,
        redirect_to: Optional[str] = None,
        scopes: Optional[str] = None,
        query_params: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Get OAuth authorization URL.
        
        Redirect the user to this URL to start the OAuth flow.
        
        Args:
            provider: OAuth provider (google, github, etc.)
            redirect_to: URL to redirect after authentication
            scopes: OAuth scopes to request
            query_params: Additional query parameters
        
        Returns:
            Authorization URL to redirect user to
        
        Example:
            # Get Google sign in URL
            url = db.auth.get_oauth_url("google", redirect_to="https://myapp.com/callback")
            
            # Redirect user to this URL
            # After sign in, they'll be redirected to your callback URL
        """
        if isinstance(provider, OAuthProvider):
            provider = provider.value
        
        options = {}
        if redirect_to:
            options["redirect_to"] = redirect_to
        if scopes:
            options["scopes"] = scopes
        if query_params:
            options["query_params"] = query_params
        
        response = self._client.sign_in_with_oauth({
            "provider": provider,
            "options": options if options else None,
        })
        
        return response.url
    
    async def exchange_code(
        self,
        code: str,
    ) -> Session:
        """
        Exchange OAuth code for session.
        
        Call this after the OAuth callback with the code parameter.
        
        Args:
            code: Authorization code from OAuth callback
        
        Returns:
            Session with access tokens
        
        Raises:
            OAuthError: If code exchange fails
        
        Example:
            # In your callback handler:
            code = request.query_params.get("code")
            session = await db.auth.exchange_code(code)
        """
        try:
            response = self._client.exchange_code_for_session(code)
            
            if response.session:
                session = Session.from_dict(response.session.model_dump())
                self._current_session = session
                if response.user:
                    self._current_user = User.from_dict(response.user.model_dump())
                    session.user = self._current_user
                return session
            else:
                raise OAuthError(message="Code exchange failed: No session returned")
                
        except Exception as e:
            raise OAuthError(message=f"OAuth code exchange failed: {e}")
    
    # =========================================================================
    # MAGIC LINK / OTP
    # =========================================================================
    
    async def sign_in_with_otp(
        self,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        *,
        redirect_to: Optional[str] = None,
        should_create_user: bool = True,
        data: Optional[Dict[str, Any]] = None,
        captcha_token: Optional[str] = None,
    ) -> None:
        """
        Send a magic link or OTP code.
        
        For email: Sends a magic link that logs the user in when clicked.
        For phone: Sends an SMS with a one-time password.
        
        Args:
            email: Email to send magic link to
            phone: Phone to send OTP to
            redirect_to: URL to redirect after clicking magic link
            should_create_user: Create user if doesn't exist (default: True)
            data: Additional user metadata (if creating user)
            captcha_token: Captcha verification token
        
        Raises:
            AuthError: If OTP sending fails
        
        Example:
            # Send magic link to email
            await db.auth.sign_in_with_otp(email="user@example.com")
            
            # Send OTP to phone
            await db.auth.sign_in_with_otp(phone="+1234567890")
        """
        if not email and not phone:
            raise AuthError(message="Either email or phone is required for OTP sign in")
        
        try:
            options = {
                "should_create_user": should_create_user,
            }
            if redirect_to:
                options["email_redirect_to"] = redirect_to
            if data:
                options["data"] = data
            if captcha_token:
                options["captcha_token"] = captcha_token
            
            if email:
                self._client.sign_in_with_otp({
                    "email": email,
                    "options": options,
                })
            else:
                self._client.sign_in_with_otp({
                    "phone": phone,
                    "options": options,
                })
                
        except Exception as e:
            raise from_supabase_exception(e, {"email": email, "phone": phone})
    
    async def verify_otp(
        self,
        token: str,
        *,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        type: str = "email",
    ) -> Session:
        """
        Verify an OTP code.
        
        Args:
            token: The OTP code received
            email: Email the OTP was sent to
            phone: Phone the OTP was sent to
            type: Type of OTP (email, sms, phone_change, email_change)
        
        Returns:
            Session with access tokens
        
        Raises:
            InvalidTokenError: If OTP is invalid or expired
        
        Example:
            # Verify email OTP
            session = await db.auth.verify_otp("123456", email="user@example.com")
            
            # Verify phone OTP
            session = await db.auth.verify_otp("123456", phone="+1234567890", type="sms")
        """
        try:
            params = {
                "token": token,
                "type": type,
            }
            if email:
                params["email"] = email
            if phone:
                params["phone"] = phone
            
            response = self._client.verify_otp(params)
            
            if response.session:
                session = Session.from_dict(response.session.model_dump())
                self._current_session = session
                if response.user:
                    self._current_user = User.from_dict(response.user.model_dump())
                    session.user = self._current_user
                return session
            else:
                raise InvalidTokenError()
                
        except Exception as e:
            raise from_supabase_exception(e)
    
    # =========================================================================
    # SESSION MANAGEMENT
    # =========================================================================
    
    async def get_session(self) -> Optional[Session]:
        """
        Get the current session.
        
        Returns:
            Current Session or None if not signed in
        
        Example:
            session = await db.auth.get_session()
            if session:
                print(f"Signed in as: {session.user.email}")
            else:
                print("Not signed in")
        """
        try:
            response = self._client.get_session()
            if response:
                session = Session.from_dict(response.model_dump())
                self._current_session = session
                return session
            return None
        except Exception:
            return None
    
    async def get_user(self) -> Optional[User]:
        """
        Get the current user.
        
        Returns:
            Current User or None if not signed in
        
        Example:
            user = await db.auth.get_user()
            if user:
                print(f"User ID: {user.id}")
                print(f"Email: {user.email}")
        """
        try:
            response = self._client.get_user()
            if response and response.user:
                user = User.from_dict(response.user.model_dump())
                self._current_user = user
                return user
            return None
        except Exception:
            return None
    
    async def refresh_session(self) -> Session:
        """
        Refresh the current session.
        
        Call this to get new tokens before they expire.
        
        Returns:
            New Session with fresh tokens
        
        Raises:
            SessionExpiredError: If session cannot be refreshed
        
        Example:
            new_session = await db.auth.refresh_session()
            print(f"New token: {new_session.access_token}")
        """
        try:
            response = self._client.refresh_session()
            if response.session:
                session = Session.from_dict(response.session.model_dump())
                self._current_session = session
                if response.user:
                    self._current_user = User.from_dict(response.user.model_dump())
                    session.user = self._current_user
                return session
            else:
                raise SessionExpiredError()
                
        except Exception as e:
            raise SessionExpiredError()
    
    async def set_session(
        self,
        access_token: str,
        refresh_token: str,
    ) -> Session:
        """
        Set the current session manually.
        
        Use this to restore a session from stored tokens.
        
        Args:
            access_token: JWT access token
            refresh_token: Refresh token
        
        Returns:
            The restored Session
        
        Example:
            # Restore session from storage
            session = await db.auth.set_session(
                access_token=stored_access_token,
                refresh_token=stored_refresh_token
            )
        """
        try:
            response = self._client.set_session(access_token, refresh_token)
            if response.session:
                session = Session.from_dict(response.session.model_dump())
                self._current_session = session
                if response.user:
                    self._current_user = User.from_dict(response.user.model_dump())
                    session.user = self._current_user
                return session
            else:
                raise InvalidTokenError()
                
        except Exception as e:
            raise InvalidTokenError()
    
    # =========================================================================
    # SIGN OUT
    # =========================================================================
    
    async def sign_out(self, scope: str = "local") -> None:
        """
        Sign out the current user.
        
        Args:
            scope: Sign out scope
                - "local": Only sign out from this device
                - "global": Sign out from all devices
                - "others": Sign out from other devices
        
        Example:
            # Sign out from current device
            await db.auth.sign_out()
            
            # Sign out from all devices
            await db.auth.sign_out(scope="global")
        """
        try:
            self._client.sign_out({"scope": scope})
            self._current_session = None
            self._current_user = None
        except Exception:
            # Still clear local state even if API call fails
            self._current_session = None
            self._current_user = None
    
    # =========================================================================
    # PASSWORD MANAGEMENT
    # =========================================================================
    
    async def reset_password(
        self,
        email: str,
        *,
        redirect_to: Optional[str] = None,
        captcha_token: Optional[str] = None,
    ) -> None:
        """
        Send password reset email.
        
        The user will receive an email with a link to reset their password.
        
        Args:
            email: Email to send reset link to
            redirect_to: URL to redirect after clicking reset link
            captcha_token: Captcha verification token
        
        Example:
            await db.auth.reset_password("user@example.com")
            print("Check your email for reset link")
        """
        try:
            options = {}
            if redirect_to:
                options["redirect_to"] = redirect_to
            if captcha_token:
                options["captcha_token"] = captcha_token
            
            self._client.reset_password_email(
                email,
                options=options if options else None,
            )
        except Exception as e:
            raise from_supabase_exception(e, {"email": email})
    
    async def update_password(self, new_password: str) -> User:
        """
        Update the current user's password.
        
        User must be signed in to update password.
        
        Args:
            new_password: New password (min 6 characters)
        
        Returns:
            Updated User
        
        Raises:
            WeakPasswordError: If password is too short
            SessionExpiredError: If not signed in
        
        Example:
            user = await db.auth.update_password("new-secure-password")
        """
        try:
            response = self._client.update_user({"password": new_password})
            if response.user:
                user = User.from_dict(response.user.model_dump())
                self._current_user = user
                return user
            else:
                raise AuthError(message="Failed to update password")
                
        except Exception as e:
            error_str = str(e).lower()
            if "password" in error_str and ("weak" in error_str or "short" in error_str):
                raise WeakPasswordError()
            raise from_supabase_exception(e)
    
    # =========================================================================
    # USER UPDATES
    # =========================================================================
    
    async def update_user(
        self,
        *,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        password: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> User:
        """
        Update the current user's profile.
        
        Args:
            email: New email address (requires confirmation)
            phone: New phone number
            password: New password
            data: User metadata to update
        
        Returns:
            Updated User
        
        Example:
            user = await db.auth.update_user(
                data={"full_name": "Alice Smith", "avatar_url": "..."}
            )
        """
        try:
            updates = {}
            if email:
                updates["email"] = email
            if phone:
                updates["phone"] = phone
            if password:
                updates["password"] = password
            if data:
                updates["data"] = data
            
            response = self._client.update_user(updates)
            if response.user:
                user = User.from_dict(response.user.model_dump())
                self._current_user = user
                return user
            else:
                raise AuthError(message="Failed to update user")
                
        except Exception as e:
            raise from_supabase_exception(e)
    
    # =========================================================================
    # ADMIN OPERATIONS (requires service_role_key)
    # =========================================================================
    
    async def admin_get_user(self, user_id: str) -> User:
        """
        Get a user by ID (admin operation).
        
        Requires service_role_key.
        
        Args:
            user_id: User's UUID
        
        Returns:
            User data
        
        Raises:
            UserNotFoundError: If user doesn't exist
        """
        admin_client = self._supabase.admin_client
        if not admin_client:
            raise AuthError(message="Admin operations require service_role_key")
        
        try:
            response = admin_client.auth.admin.get_user_by_id(user_id)
            if response.user:
                return User.from_dict(response.user.model_dump())
            else:
                raise UserNotFoundError()
        except Exception as e:
            raise from_supabase_exception(e, {"user_id": user_id})
    
    async def admin_delete_user(self, user_id: str) -> None:
        """
        Delete a user by ID (admin operation).
        
        Requires service_role_key.
        
        Args:
            user_id: User's UUID
        """
        admin_client = self._supabase.admin_client
        if not admin_client:
            raise AuthError(message="Admin operations require service_role_key")
        
        try:
            admin_client.auth.admin.delete_user(user_id)
        except Exception as e:
            raise from_supabase_exception(e, {"user_id": user_id})
    
    async def admin_list_users(
        self,
        page: int = 1,
        per_page: int = 50,
    ) -> List[User]:
        """
        List all users (admin operation).
        
        Requires service_role_key.
        
        Args:
            page: Page number (1-indexed)
            per_page: Users per page
        
        Returns:
            List of Users
        """
        admin_client = self._supabase.admin_client
        if not admin_client:
            raise AuthError(message="Admin operations require service_role_key")
        
        try:
            response = admin_client.auth.admin.list_users(page=page, per_page=per_page)
            return [User.from_dict(u.model_dump()) for u in response]
        except Exception as e:
            raise from_supabase_exception(e)

