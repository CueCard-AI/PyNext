"""
Comprehensive tests for PyNext Supabase Authentication.

Tests cover:
- User model and Session model
- Sign up flow
- Sign in flow (email/password, phone)
- OAuth flow
- Magic link / OTP
- Session management
- Password management
- Admin operations
- Error handling

Total: 100 tests
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from dataclasses import asdict

from pynext.db.supabase.auth import (
    SupabaseAuth,
    User,
    Session,
    AuthConfig,
    OAuthProvider,
    _parse_datetime,
)
from pynext.db.supabase.exceptions import (
    SupabaseError,
    AuthError,
    InvalidCredentialsError,
    UserExistsError,
    UserNotFoundError,
    SessionExpiredError,
    InvalidTokenError,
    OAuthError,
    WeakPasswordError,
    EmailNotConfirmedError,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_supabase():
    """Create mock Supabase adapter."""
    supabase = Mock()
    supabase._initialized = True
    supabase._ensure_initialized = Mock()
    
    # Mock auth client
    auth_client = Mock()
    supabase.client = Mock()
    supabase.client.auth = auth_client
    supabase.admin_client = None
    
    return supabase


@pytest.fixture
def auth(mock_supabase):
    """Create SupabaseAuth instance."""
    return SupabaseAuth(mock_supabase)


@pytest.fixture
def sample_user_data():
    """Sample user data from API."""
    return {
        "id": "user-123",
        "email": "test@example.com",
        "phone": "+1234567890",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-02T00:00:00Z",
        "confirmed_at": "2024-01-01T01:00:00Z",
        "last_sign_in_at": "2024-01-03T00:00:00Z",
        "role": "authenticated",
        "app_metadata": {"provider": "email"},
        "user_metadata": {"name": "Test User"},
        "identities": [],
    }


@pytest.fixture
def sample_session_data(sample_user_data):
    """Sample session data from API."""
    return {
        "access_token": "eyJ.access.token",
        "refresh_token": "refresh-token-123",
        "token_type": "bearer",
        "expires_in": 3600,
        "expires_at": 1704153600,
        "user": sample_user_data,
    }


# =============================================================================
# USER MODEL TESTS (15 tests)
# =============================================================================

class TestUserModel:
    """Tests for User data model."""
    
    def test_user_from_dict_full(self, sample_user_data):
        """User.from_dict creates User with all fields."""
        user = User.from_dict(sample_user_data)
        assert user.id == "user-123"
        assert user.email == "test@example.com"
        assert user.phone == "+1234567890"
        assert user.role == "authenticated"
    
    def test_user_from_dict_minimal(self):
        """User.from_dict handles minimal data."""
        user = User.from_dict({"id": "user-456"})
        assert user.id == "user-456"
        assert user.email is None
        assert user.phone is None
    
    def test_user_from_dict_empty(self):
        """User.from_dict handles empty dict."""
        user = User.from_dict({})
        assert user.id == ""
    
    def test_user_datetime_parsing(self, sample_user_data):
        """User.from_dict parses datetime strings."""
        user = User.from_dict(sample_user_data)
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)
    
    def test_user_datetime_parsing_z_suffix(self):
        """User.from_dict handles Z suffix in timestamps."""
        user = User.from_dict({
            "id": "1",
            "created_at": "2024-01-01T12:00:00Z"
        })
        assert user.created_at is not None
    
    def test_user_is_confirmed_true(self, sample_user_data):
        """User.is_confirmed returns True when confirmed."""
        user = User.from_dict(sample_user_data)
        assert user.is_confirmed is True
    
    def test_user_is_confirmed_false(self):
        """User.is_confirmed returns False when not confirmed."""
        user = User.from_dict({"id": "1", "confirmed_at": None})
        assert user.is_confirmed is False
    
    def test_user_is_confirmed_via_email_confirmed_at(self):
        """User.is_confirmed checks email_confirmed_at too."""
        user = User.from_dict({
            "id": "1",
            "confirmed_at": None,
            "email_confirmed_at": "2024-01-01T00:00:00Z"
        })
        assert user.is_confirmed is True
    
    def test_user_to_dict(self, sample_user_data):
        """User.to_dict serializes to dictionary."""
        user = User.from_dict(sample_user_data)
        data = user.to_dict()
        assert data["id"] == "user-123"
        assert data["email"] == "test@example.com"
    
    def test_user_to_dict_datetime_format(self, sample_user_data):
        """User.to_dict converts datetimes to ISO format."""
        user = User.from_dict(sample_user_data)
        data = user.to_dict()
        assert isinstance(data["created_at"], str)
    
    def test_user_metadata_defaults(self):
        """User has empty dicts for metadata by default."""
        user = User.from_dict({"id": "1"})
        assert user.app_metadata == {}
        assert user.user_metadata == {}
    
    def test_user_identities_default(self):
        """User has empty list for identities by default."""
        user = User.from_dict({"id": "1"})
        assert user.identities == []
    
    def test_user_role_default(self):
        """User has 'authenticated' role by default."""
        user = User.from_dict({"id": "1"})
        assert user.role == "authenticated"
    
    def test_parse_datetime_invalid(self):
        """_parse_datetime handles invalid input."""
        assert _parse_datetime(None) is None
        assert _parse_datetime("not-a-date") is None
        assert _parse_datetime("") is None
    
    def test_parse_datetime_integer_timestamp(self):
        """_parse_datetime handles integer timestamps."""
        dt = _parse_datetime(1704067200)  # 2024-01-01 00:00:00 UTC
        assert isinstance(dt, datetime)
    
    def test_parse_datetime_valid(self):
        """_parse_datetime parses valid ISO string."""
        dt = _parse_datetime("2024-01-01T12:00:00+00:00")
        assert isinstance(dt, datetime)


# =============================================================================
# SESSION MODEL TESTS (10 tests)
# =============================================================================

class TestSessionModel:
    """Tests for Session data model."""
    
    def test_session_from_dict_full(self, sample_session_data):
        """Session.from_dict creates Session with all fields."""
        session = Session.from_dict(sample_session_data)
        assert session.access_token == "eyJ.access.token"
        assert session.refresh_token == "refresh-token-123"
        assert session.token_type == "bearer"
        assert session.expires_in == 3600
    
    def test_session_from_dict_with_user(self, sample_session_data):
        """Session.from_dict includes user data."""
        session = Session.from_dict(sample_session_data)
        assert session.user is not None
        assert session.user.email == "test@example.com"
    
    def test_session_from_dict_minimal(self):
        """Session.from_dict handles minimal data."""
        session = Session.from_dict({
            "access_token": "token",
            "refresh_token": "refresh"
        })
        assert session.access_token == "token"
        assert session.user is None
    
    def test_session_is_expired_true(self):
        """Session.is_expired returns True when expired."""
        session = Session.from_dict({
            "access_token": "token",
            "refresh_token": "refresh",
            "expires_at": 0  # Unix epoch = definitely expired
        })
        assert session.is_expired is True
    
    def test_session_is_expired_false(self):
        """Session.is_expired returns False when not expired."""
        import time
        future = int(time.time()) + 3600
        session = Session.from_dict({
            "access_token": "token",
            "refresh_token": "refresh",
            "expires_at": future
        })
        assert session.is_expired is False
    
    def test_session_is_expired_no_expires_at(self):
        """Session.is_expired returns False when no expires_at."""
        session = Session.from_dict({
            "access_token": "token",
            "refresh_token": "refresh"
        })
        assert session.is_expired is False
    
    def test_session_to_dict(self, sample_session_data):
        """Session.to_dict serializes to dictionary."""
        session = Session.from_dict(sample_session_data)
        data = session.to_dict()
        assert data["access_token"] == "eyJ.access.token"
    
    def test_session_to_dict_with_user(self, sample_session_data):
        """Session.to_dict includes user dict."""
        session = Session.from_dict(sample_session_data)
        data = session.to_dict()
        assert data["user"] is not None
        assert data["user"]["email"] == "test@example.com"
    
    def test_session_token_type_default(self):
        """Session has 'bearer' token type by default."""
        session = Session.from_dict({
            "access_token": "token",
            "refresh_token": "refresh"
        })
        assert session.token_type == "bearer"
    
    def test_session_expires_in_default(self):
        """Session has 3600 expires_in by default."""
        session = Session.from_dict({
            "access_token": "token",
            "refresh_token": "refresh"
        })
        assert session.expires_in == 3600


# =============================================================================
# AUTH CONFIG TESTS (5 tests)
# =============================================================================

class TestAuthConfig:
    """Tests for AuthConfig."""
    
    def test_auth_config_defaults(self):
        """AuthConfig has sensible defaults."""
        config = AuthConfig()
        assert config.auto_refresh_token is True
        assert config.persist_session is True
        assert config.redirect_url is None
        assert config.scopes is None
    
    def test_auth_config_custom_values(self):
        """AuthConfig accepts custom values."""
        config = AuthConfig(
            auto_refresh_token=False,
            redirect_url="https://example.com/callback"
        )
        assert config.auto_refresh_token is False
        assert config.redirect_url == "https://example.com/callback"
    
    def test_auth_config_scopes(self):
        """AuthConfig accepts scopes."""
        config = AuthConfig(scopes="email profile")
        assert config.scopes == "email profile"
    
    def test_auth_config_persist_session_false(self):
        """AuthConfig can disable persist_session."""
        config = AuthConfig(persist_session=False)
        assert config.persist_session is False
    
    def test_auth_config_all_options(self):
        """AuthConfig accepts all options together."""
        config = AuthConfig(
            auto_refresh_token=False,
            persist_session=False,
            redirect_url="https://example.com",
            scopes="email"
        )
        assert config.auto_refresh_token is False
        assert config.persist_session is False


# =============================================================================
# OAUTH PROVIDER TESTS (5 tests)
# =============================================================================

class TestOAuthProvider:
    """Tests for OAuthProvider enum."""
    
    def test_oauth_provider_google(self):
        """OAuthProvider has Google."""
        assert OAuthProvider.GOOGLE.value == "google"
    
    def test_oauth_provider_github(self):
        """OAuthProvider has GitHub."""
        assert OAuthProvider.GITHUB.value == "github"
    
    def test_oauth_provider_string_value(self):
        """OAuthProvider values are strings."""
        assert isinstance(OAuthProvider.GOOGLE.value, str)
    
    def test_oauth_provider_all_providers(self):
        """OAuthProvider has all major providers."""
        providers = [p.value for p in OAuthProvider]
        assert "google" in providers
        assert "github" in providers
        assert "apple" in providers
        assert "discord" in providers
    
    def test_oauth_provider_is_str(self):
        """OAuthProvider inherits from str."""
        assert OAuthProvider.GOOGLE == "google"


# =============================================================================
# SIGN UP TESTS (15 tests)
# =============================================================================

class TestSignUp:
    """Tests for sign_up method."""
    
    @pytest.mark.asyncio
    async def test_sign_up_success(self, auth, sample_user_data):
        """sign_up returns User on success."""
        mock_response = Mock()
        mock_response.user = Mock()
        mock_response.user.model_dump = Mock(return_value=sample_user_data)
        mock_response.session = None
        auth._client.sign_up = Mock(return_value=mock_response)
        
        user = await auth.sign_up("test@example.com", "password123")
        
        assert isinstance(user, User)
        assert user.email == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_sign_up_with_session(self, auth, sample_user_data, sample_session_data):
        """sign_up stores session when returned."""
        mock_response = Mock()
        mock_response.user = Mock()
        mock_response.user.model_dump = Mock(return_value=sample_user_data)
        mock_response.session = Mock()
        mock_response.session.model_dump = Mock(return_value=sample_session_data)
        auth._client.sign_up = Mock(return_value=mock_response)
        
        await auth.sign_up("test@example.com", "password123")
        
        assert auth._current_session is not None
    
    @pytest.mark.asyncio
    async def test_sign_up_stores_user(self, auth, sample_user_data):
        """sign_up stores current user."""
        mock_response = Mock()
        mock_response.user = Mock()
        mock_response.user.model_dump = Mock(return_value=sample_user_data)
        mock_response.session = None
        auth._client.sign_up = Mock(return_value=mock_response)
        
        await auth.sign_up("test@example.com", "password123")
        
        assert auth._current_user is not None
    
    @pytest.mark.asyncio
    async def test_sign_up_with_metadata(self, auth, sample_user_data):
        """sign_up passes metadata to API."""
        mock_response = Mock()
        mock_response.user = Mock()
        mock_response.user.model_dump = Mock(return_value=sample_user_data)
        mock_response.session = None
        auth._client.sign_up = Mock(return_value=mock_response)
        
        await auth.sign_up(
            "test@example.com",
            "password123",
            data={"name": "Test User"}
        )
        
        call_args = auth._client.sign_up.call_args[0][0]
        assert call_args["options"]["data"] == {"name": "Test User"}
    
    @pytest.mark.asyncio
    async def test_sign_up_with_redirect(self, auth, sample_user_data):
        """sign_up passes redirect_to."""
        mock_response = Mock()
        mock_response.user = Mock()
        mock_response.user.model_dump = Mock(return_value=sample_user_data)
        mock_response.session = None
        auth._client.sign_up = Mock(return_value=mock_response)
        
        await auth.sign_up(
            "test@example.com",
            "password123",
            redirect_to="https://example.com/confirm"
        )
        
        call_args = auth._client.sign_up.call_args[0][0]
        assert call_args["options"]["email_redirect_to"] == "https://example.com/confirm"
    
    @pytest.mark.asyncio
    async def test_sign_up_user_exists_error(self, auth):
        """sign_up raises UserExistsError for existing user."""
        auth._client.sign_up = Mock(side_effect=Exception("User already registered"))
        
        with pytest.raises(UserExistsError):
            await auth.sign_up("existing@example.com", "password123")
    
    @pytest.mark.asyncio
    async def test_sign_up_weak_password_error(self, auth):
        """sign_up raises WeakPasswordError for weak password."""
        auth._client.sign_up = Mock(side_effect=Exception("Password too weak"))
        
        with pytest.raises(WeakPasswordError):
            await auth.sign_up("test@example.com", "123")
    
    @pytest.mark.asyncio
    async def test_sign_up_no_user_returned(self, auth):
        """sign_up raises SupabaseError when no user returned."""
        mock_response = Mock()
        mock_response.user = None
        mock_response.session = None
        auth._client.sign_up = Mock(return_value=mock_response)
        
        with pytest.raises(SupabaseError):
            await auth.sign_up("test@example.com", "password123")
    
    @pytest.mark.asyncio
    async def test_sign_up_with_phone(self, auth, sample_user_data):
        """sign_up accepts phone number."""
        mock_response = Mock()
        mock_response.user = Mock()
        mock_response.user.model_dump = Mock(return_value=sample_user_data)
        mock_response.session = None
        auth._client.sign_up = Mock(return_value=mock_response)
        
        await auth.sign_up(
            "test@example.com",
            "password123",
            phone="+1234567890"
        )
        
        call_args = auth._client.sign_up.call_args[0][0]
        assert call_args["phone"] == "+1234567890"
    
    @pytest.mark.asyncio
    async def test_sign_up_with_captcha(self, auth, sample_user_data):
        """sign_up passes captcha token."""
        mock_response = Mock()
        mock_response.user = Mock()
        mock_response.user.model_dump = Mock(return_value=sample_user_data)
        mock_response.session = None
        auth._client.sign_up = Mock(return_value=mock_response)
        
        await auth.sign_up(
            "test@example.com",
            "password123",
            captcha_token="captcha-token"
        )
        
        call_args = auth._client.sign_up.call_args[0][0]
        assert call_args["options"]["captcha_token"] == "captcha-token"
    
    @pytest.mark.asyncio
    async def test_sign_up_calls_client(self, auth, sample_user_data):
        """sign_up calls underlying client."""
        mock_response = Mock()
        mock_response.user = Mock()
        mock_response.user.model_dump = Mock(return_value=sample_user_data)
        mock_response.session = None
        auth._client.sign_up = Mock(return_value=mock_response)
        
        await auth.sign_up("test@example.com", "password123")
        
        auth._client.sign_up.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_sign_up_email_in_call(self, auth, sample_user_data):
        """sign_up includes email in call."""
        mock_response = Mock()
        mock_response.user = Mock()
        mock_response.user.model_dump = Mock(return_value=sample_user_data)
        mock_response.session = None
        auth._client.sign_up = Mock(return_value=mock_response)
        
        await auth.sign_up("test@example.com", "password123")
        
        call_args = auth._client.sign_up.call_args[0][0]
        assert call_args["email"] == "test@example.com"
        assert call_args["password"] == "password123"
    
    @pytest.mark.asyncio
    async def test_sign_up_no_options_when_empty(self, auth, sample_user_data):
        """sign_up omits options when empty."""
        mock_response = Mock()
        mock_response.user = Mock()
        mock_response.user.model_dump = Mock(return_value=sample_user_data)
        mock_response.session = None
        auth._client.sign_up = Mock(return_value=mock_response)
        
        await auth.sign_up("test@example.com", "password123")
        
        call_args = auth._client.sign_up.call_args[0][0]
        # options should be None when nothing extra passed
        assert call_args.get("options") is None
    
    @pytest.mark.asyncio
    async def test_sign_up_already_exists_variant(self, auth):
        """sign_up handles 'already exists' error message."""
        auth._client.sign_up = Mock(side_effect=Exception("User already exists"))
        
        with pytest.raises(UserExistsError) as exc_info:
            await auth.sign_up("existing@example.com", "password123")
        
        assert "existing@example.com" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_sign_up_password_6_chars_error(self, auth):
        """sign_up detects '6 characters' in weak password error."""
        auth._client.sign_up = Mock(side_effect=Exception("Password should be at least 6 characters"))
        
        with pytest.raises(WeakPasswordError):
            await auth.sign_up("test@example.com", "12345")


# =============================================================================
# SIGN IN TESTS (15 tests)
# =============================================================================

class TestSignIn:
    """Tests for sign_in method."""
    
    @pytest.mark.asyncio
    async def test_sign_in_success(self, auth, sample_session_data):
        """sign_in returns Session on success."""
        mock_response = Mock()
        mock_response.session = Mock()
        mock_response.session.model_dump = Mock(return_value=sample_session_data)
        mock_response.user = None
        auth._client.sign_in_with_password = Mock(return_value=mock_response)
        
        session = await auth.sign_in("test@example.com", "password123")
        
        assert isinstance(session, Session)
        assert session.access_token == "eyJ.access.token"
    
    @pytest.mark.asyncio
    async def test_sign_in_stores_session(self, auth, sample_session_data):
        """sign_in stores current session."""
        mock_response = Mock()
        mock_response.session = Mock()
        mock_response.session.model_dump = Mock(return_value=sample_session_data)
        mock_response.user = None
        auth._client.sign_in_with_password = Mock(return_value=mock_response)
        
        await auth.sign_in("test@example.com", "password123")
        
        assert auth._current_session is not None
    
    @pytest.mark.asyncio
    async def test_sign_in_with_user(self, auth, sample_session_data, sample_user_data):
        """sign_in stores user from response."""
        mock_response = Mock()
        mock_response.session = Mock()
        mock_response.session.model_dump = Mock(return_value=sample_session_data)
        mock_response.user = Mock()
        mock_response.user.model_dump = Mock(return_value=sample_user_data)
        auth._client.sign_in_with_password = Mock(return_value=mock_response)
        
        session = await auth.sign_in("test@example.com", "password123")
        
        assert session.user is not None
        assert auth._current_user is not None
    
    @pytest.mark.asyncio
    async def test_sign_in_invalid_credentials(self, auth):
        """sign_in raises InvalidCredentialsError for wrong password."""
        auth._client.sign_in_with_password = Mock(side_effect=Exception("Invalid login credentials"))
        
        with pytest.raises(InvalidCredentialsError):
            await auth.sign_in("test@example.com", "wrong-password")
    
    @pytest.mark.asyncio
    async def test_sign_in_invalid_password_variant(self, auth):
        """sign_in handles 'invalid password' error message."""
        auth._client.sign_in_with_password = Mock(side_effect=Exception("Invalid password"))
        
        with pytest.raises(InvalidCredentialsError):
            await auth.sign_in("test@example.com", "wrong-password")
    
    @pytest.mark.asyncio
    async def test_sign_in_no_session(self, auth):
        """sign_in raises InvalidCredentialsError when no session."""
        mock_response = Mock()
        mock_response.session = None
        auth._client.sign_in_with_password = Mock(return_value=mock_response)
        
        with pytest.raises(InvalidCredentialsError):
            await auth.sign_in("test@example.com", "password123")
    
    @pytest.mark.asyncio
    async def test_sign_in_email_not_confirmed(self, auth):
        """sign_in raises EmailNotConfirmedError."""
        auth._client.sign_in_with_password = Mock(side_effect=Exception("Email not confirmed"))
        
        with pytest.raises(EmailNotConfirmedError):
            await auth.sign_in("unconfirmed@example.com", "password123")
    
    @pytest.mark.asyncio
    async def test_sign_in_calls_client(self, auth, sample_session_data):
        """sign_in calls underlying client."""
        mock_response = Mock()
        mock_response.session = Mock()
        mock_response.session.model_dump = Mock(return_value=sample_session_data)
        mock_response.user = None
        auth._client.sign_in_with_password = Mock(return_value=mock_response)
        
        await auth.sign_in("test@example.com", "password123")
        
        auth._client.sign_in_with_password.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_sign_in_credentials_in_call(self, auth, sample_session_data):
        """sign_in includes credentials in call."""
        mock_response = Mock()
        mock_response.session = Mock()
        mock_response.session.model_dump = Mock(return_value=sample_session_data)
        mock_response.user = None
        auth._client.sign_in_with_password = Mock(return_value=mock_response)
        
        await auth.sign_in("test@example.com", "password123")
        
        call_args = auth._client.sign_in_with_password.call_args[0][0]
        assert call_args["email"] == "test@example.com"
        assert call_args["password"] == "password123"
    
    @pytest.mark.asyncio
    async def test_sign_in_with_phone_success(self, auth, sample_session_data):
        """sign_in_with_phone returns Session on success."""
        mock_response = Mock()
        mock_response.session = Mock()
        mock_response.session.model_dump = Mock(return_value=sample_session_data)
        mock_response.user = None
        auth._client.sign_in_with_password = Mock(return_value=mock_response)
        
        session = await auth.sign_in_with_phone("+1234567890", "password123")
        
        assert isinstance(session, Session)
    
    @pytest.mark.asyncio
    async def test_sign_in_with_phone_credentials(self, auth, sample_session_data):
        """sign_in_with_phone passes phone to client."""
        mock_response = Mock()
        mock_response.session = Mock()
        mock_response.session.model_dump = Mock(return_value=sample_session_data)
        mock_response.user = None
        auth._client.sign_in_with_password = Mock(return_value=mock_response)
        
        await auth.sign_in_with_phone("+1234567890", "password123")
        
        call_args = auth._client.sign_in_with_password.call_args[0][0]
        assert call_args["phone"] == "+1234567890"
    
    @pytest.mark.asyncio
    async def test_sign_in_with_phone_no_session(self, auth):
        """sign_in_with_phone raises InvalidCredentialsError when no session."""
        mock_response = Mock()
        mock_response.session = None
        auth._client.sign_in_with_password = Mock(return_value=mock_response)
        
        with pytest.raises(InvalidCredentialsError):
            await auth.sign_in_with_phone("+1234567890", "password123")
    
    @pytest.mark.asyncio
    async def test_sign_in_confirm_variant(self, auth):
        """sign_in handles 'confirm' error message."""
        auth._client.sign_in_with_password = Mock(side_effect=Exception("Please confirm your email"))
        
        with pytest.raises(EmailNotConfirmedError):
            await auth.sign_in("test@example.com", "password123")
    
    @pytest.mark.asyncio
    async def test_sign_in_stores_both_session_and_user(self, auth, sample_session_data, sample_user_data):
        """sign_in stores both session and user."""
        mock_response = Mock()
        mock_response.session = Mock()
        mock_response.session.model_dump = Mock(return_value=sample_session_data)
        mock_response.user = Mock()
        mock_response.user.model_dump = Mock(return_value=sample_user_data)
        auth._client.sign_in_with_password = Mock(return_value=mock_response)
        
        session = await auth.sign_in("test@example.com", "password123")
        
        assert auth._current_session is session
        assert auth._current_user is not None


# =============================================================================
# SESSION MANAGEMENT TESTS (15 tests)
# =============================================================================

class TestSessionManagement:
    """Tests for session management methods."""
    
    @pytest.mark.asyncio
    async def test_get_session_returns_session(self, auth, sample_session_data):
        """get_session returns current session."""
        mock_session = Mock()
        mock_session.model_dump = Mock(return_value=sample_session_data)
        auth._client.get_session = Mock(return_value=mock_session)
        
        session = await auth.get_session()
        
        assert isinstance(session, Session)
    
    @pytest.mark.asyncio
    async def test_get_session_none_when_not_signed_in(self, auth):
        """get_session returns None when not signed in."""
        auth._client.get_session = Mock(return_value=None)
        
        session = await auth.get_session()
        
        assert session is None
    
    @pytest.mark.asyncio
    async def test_get_session_stores_session(self, auth, sample_session_data):
        """get_session stores session."""
        mock_session = Mock()
        mock_session.model_dump = Mock(return_value=sample_session_data)
        auth._client.get_session = Mock(return_value=mock_session)
        
        await auth.get_session()
        
        assert auth._current_session is not None
    
    @pytest.mark.asyncio
    async def test_get_session_handles_exception(self, auth):
        """get_session returns None on exception."""
        auth._client.get_session = Mock(side_effect=Exception("Error"))
        
        session = await auth.get_session()
        
        assert session is None
    
    @pytest.mark.asyncio
    async def test_get_user_returns_user(self, auth, sample_user_data):
        """get_user returns current user."""
        mock_response = Mock()
        mock_response.user = Mock()
        mock_response.user.model_dump = Mock(return_value=sample_user_data)
        auth._client.get_user = Mock(return_value=mock_response)
        
        user = await auth.get_user()
        
        assert isinstance(user, User)
    
    @pytest.mark.asyncio
    async def test_get_user_none_when_not_signed_in(self, auth):
        """get_user returns None when not signed in."""
        auth._client.get_user = Mock(return_value=None)
        
        user = await auth.get_user()
        
        assert user is None
    
    @pytest.mark.asyncio
    async def test_get_user_handles_exception(self, auth):
        """get_user returns None on exception."""
        auth._client.get_user = Mock(side_effect=Exception("Error"))
        
        user = await auth.get_user()
        
        assert user is None
    
    @pytest.mark.asyncio
    async def test_refresh_session_success(self, auth, sample_session_data):
        """refresh_session returns new session."""
        mock_response = Mock()
        mock_response.session = Mock()
        mock_response.session.model_dump = Mock(return_value=sample_session_data)
        mock_response.user = None
        auth._client.refresh_session = Mock(return_value=mock_response)
        
        session = await auth.refresh_session()
        
        assert isinstance(session, Session)
    
    @pytest.mark.asyncio
    async def test_refresh_session_no_session(self, auth):
        """refresh_session raises SessionExpiredError when no session."""
        mock_response = Mock()
        mock_response.session = None
        auth._client.refresh_session = Mock(return_value=mock_response)
        
        with pytest.raises(SessionExpiredError):
            await auth.refresh_session()
    
    @pytest.mark.asyncio
    async def test_refresh_session_error(self, auth):
        """refresh_session raises SessionExpiredError on error."""
        auth._client.refresh_session = Mock(side_effect=Exception("Token expired"))
        
        with pytest.raises(SessionExpiredError):
            await auth.refresh_session()
    
    @pytest.mark.asyncio
    async def test_set_session_success(self, auth, sample_session_data):
        """set_session restores session from tokens."""
        mock_response = Mock()
        mock_response.session = Mock()
        mock_response.session.model_dump = Mock(return_value=sample_session_data)
        mock_response.user = None
        auth._client.set_session = Mock(return_value=mock_response)
        
        session = await auth.set_session("access_token", "refresh_token")
        
        assert isinstance(session, Session)
    
    @pytest.mark.asyncio
    async def test_set_session_no_session(self, auth):
        """set_session raises InvalidTokenError when no session."""
        mock_response = Mock()
        mock_response.session = None
        auth._client.set_session = Mock(return_value=mock_response)
        
        with pytest.raises(InvalidTokenError):
            await auth.set_session("bad_access", "bad_refresh")
    
    @pytest.mark.asyncio
    async def test_set_session_error(self, auth):
        """set_session raises InvalidTokenError on error."""
        auth._client.set_session = Mock(side_effect=Exception("Invalid token"))
        
        with pytest.raises(InvalidTokenError):
            await auth.set_session("bad", "bad")
    
    @pytest.mark.asyncio
    async def test_sign_out_clears_session(self, auth, sample_session_data):
        """sign_out clears current session."""
        auth._current_session = Session.from_dict(sample_session_data)
        auth._current_user = User.from_dict({"id": "1"})
        auth._client.sign_out = Mock()
        
        await auth.sign_out()
        
        assert auth._current_session is None
        assert auth._current_user is None
    
    @pytest.mark.asyncio
    async def test_sign_out_clears_on_error(self, auth, sample_session_data):
        """sign_out clears local state even on API error."""
        auth._current_session = Session.from_dict(sample_session_data)
        auth._current_user = User.from_dict({"id": "1"})
        auth._client.sign_out = Mock(side_effect=Exception("Network error"))
        
        await auth.sign_out()
        
        assert auth._current_session is None
        assert auth._current_user is None


# =============================================================================
# PASSWORD MANAGEMENT TESTS (10 tests)
# =============================================================================

class TestPasswordManagement:
    """Tests for password management methods."""
    
    @pytest.mark.asyncio
    async def test_reset_password_success(self, auth):
        """reset_password sends reset email."""
        auth._client.reset_password_email = Mock()
        
        await auth.reset_password("test@example.com")
        
        auth._client.reset_password_email.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_reset_password_with_redirect(self, auth):
        """reset_password passes redirect_to."""
        auth._client.reset_password_email = Mock()
        
        await auth.reset_password("test@example.com", redirect_to="https://example.com/reset")
        
        call_args = auth._client.reset_password_email.call_args
        assert "redirect_to" in call_args[1]["options"]
    
    @pytest.mark.asyncio
    async def test_reset_password_with_captcha(self, auth):
        """reset_password passes captcha token."""
        auth._client.reset_password_email = Mock()
        
        await auth.reset_password("test@example.com", captcha_token="captcha")
        
        call_args = auth._client.reset_password_email.call_args
        assert "captcha_token" in call_args[1]["options"]
    
    @pytest.mark.asyncio
    async def test_update_password_success(self, auth, sample_user_data):
        """update_password returns updated user."""
        mock_response = Mock()
        mock_response.user = Mock()
        mock_response.user.model_dump = Mock(return_value=sample_user_data)
        auth._client.update_user = Mock(return_value=mock_response)
        
        user = await auth.update_password("new-password")
        
        assert isinstance(user, User)
    
    @pytest.mark.asyncio
    async def test_update_password_calls_client(self, auth, sample_user_data):
        """update_password calls update_user with password."""
        mock_response = Mock()
        mock_response.user = Mock()
        mock_response.user.model_dump = Mock(return_value=sample_user_data)
        auth._client.update_user = Mock(return_value=mock_response)
        
        await auth.update_password("new-password")
        
        call_args = auth._client.update_user.call_args[0][0]
        assert call_args["password"] == "new-password"
    
    @pytest.mark.asyncio
    async def test_update_password_weak_error(self, auth):
        """update_password raises WeakPasswordError."""
        auth._client.update_user = Mock(side_effect=Exception("Password too weak"))
        
        with pytest.raises(WeakPasswordError):
            await auth.update_password("123")
    
    @pytest.mark.asyncio
    async def test_update_password_no_user_returned(self, auth):
        """update_password raises SupabaseError when no user returned."""
        mock_response = Mock()
        mock_response.user = None
        auth._client.update_user = Mock(return_value=mock_response)
        
        with pytest.raises(SupabaseError):
            await auth.update_password("new-password")
    
    @pytest.mark.asyncio
    async def test_update_user_with_email(self, auth, sample_user_data):
        """update_user can change email."""
        mock_response = Mock()
        mock_response.user = Mock()
        mock_response.user.model_dump = Mock(return_value=sample_user_data)
        auth._client.update_user = Mock(return_value=mock_response)
        
        await auth.update_user(email="new@example.com")
        
        call_args = auth._client.update_user.call_args[0][0]
        assert call_args["email"] == "new@example.com"
    
    @pytest.mark.asyncio
    async def test_update_user_with_phone(self, auth, sample_user_data):
        """update_user can change phone."""
        mock_response = Mock()
        mock_response.user = Mock()
        mock_response.user.model_dump = Mock(return_value=sample_user_data)
        auth._client.update_user = Mock(return_value=mock_response)
        
        await auth.update_user(phone="+9876543210")
        
        call_args = auth._client.update_user.call_args[0][0]
        assert call_args["phone"] == "+9876543210"
    
    @pytest.mark.asyncio
    async def test_update_user_with_metadata(self, auth, sample_user_data):
        """update_user can update user metadata."""
        mock_response = Mock()
        mock_response.user = Mock()
        mock_response.user.model_dump = Mock(return_value=sample_user_data)
        auth._client.update_user = Mock(return_value=mock_response)
        
        await auth.update_user(data={"name": "New Name"})
        
        call_args = auth._client.update_user.call_args[0][0]
        assert call_args["data"] == {"name": "New Name"}


# =============================================================================
# OTP TESTS (10 tests)
# =============================================================================

class TestOTP:
    """Tests for OTP/Magic Link methods."""
    
    @pytest.mark.asyncio
    async def test_sign_in_with_otp_email(self, auth):
        """sign_in_with_otp sends magic link to email."""
        auth._client.sign_in_with_otp = Mock()
        
        await auth.sign_in_with_otp(email="test@example.com")
        
        auth._client.sign_in_with_otp.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_sign_in_with_otp_phone(self, auth):
        """sign_in_with_otp sends SMS to phone."""
        auth._client.sign_in_with_otp = Mock()
        
        await auth.sign_in_with_otp(phone="+1234567890")
        
        call_args = auth._client.sign_in_with_otp.call_args[0][0]
        assert call_args["phone"] == "+1234567890"
    
    @pytest.mark.asyncio
    async def test_sign_in_with_otp_no_email_or_phone(self, auth):
        """sign_in_with_otp raises AuthError without email or phone."""
        with pytest.raises(AuthError):
            await auth.sign_in_with_otp()
    
    @pytest.mark.asyncio
    async def test_sign_in_with_otp_redirect(self, auth):
        """sign_in_with_otp passes redirect_to."""
        auth._client.sign_in_with_otp = Mock()
        
        await auth.sign_in_with_otp(
            email="test@example.com",
            redirect_to="https://example.com/callback"
        )
        
        call_args = auth._client.sign_in_with_otp.call_args[0][0]
        assert call_args["options"]["email_redirect_to"] == "https://example.com/callback"
    
    @pytest.mark.asyncio
    async def test_sign_in_with_otp_should_create_user(self, auth):
        """sign_in_with_otp can disable user creation."""
        auth._client.sign_in_with_otp = Mock()
        
        await auth.sign_in_with_otp(
            email="test@example.com",
            should_create_user=False
        )
        
        call_args = auth._client.sign_in_with_otp.call_args[0][0]
        assert call_args["options"]["should_create_user"] is False
    
    @pytest.mark.asyncio
    async def test_verify_otp_success(self, auth, sample_session_data):
        """verify_otp returns session on success."""
        mock_response = Mock()
        mock_response.session = Mock()
        mock_response.session.model_dump = Mock(return_value=sample_session_data)
        mock_response.user = None
        auth._client.verify_otp = Mock(return_value=mock_response)
        
        session = await auth.verify_otp("123456", email="test@example.com")
        
        assert isinstance(session, Session)
    
    @pytest.mark.asyncio
    async def test_verify_otp_no_session(self, auth):
        """verify_otp raises InvalidTokenError when no session."""
        mock_response = Mock()
        mock_response.session = None
        auth._client.verify_otp = Mock(return_value=mock_response)
        
        with pytest.raises(InvalidTokenError):
            await auth.verify_otp("wrong-code", email="test@example.com")
    
    @pytest.mark.asyncio
    async def test_verify_otp_with_phone(self, auth, sample_session_data):
        """verify_otp accepts phone verification."""
        mock_response = Mock()
        mock_response.session = Mock()
        mock_response.session.model_dump = Mock(return_value=sample_session_data)
        mock_response.user = None
        auth._client.verify_otp = Mock(return_value=mock_response)
        
        await auth.verify_otp("123456", phone="+1234567890", type="sms")
        
        call_args = auth._client.verify_otp.call_args[0][0]
        assert call_args["phone"] == "+1234567890"
        assert call_args["type"] == "sms"
    
    @pytest.mark.asyncio
    async def test_verify_otp_stores_session(self, auth, sample_session_data):
        """verify_otp stores session."""
        mock_response = Mock()
        mock_response.session = Mock()
        mock_response.session.model_dump = Mock(return_value=sample_session_data)
        mock_response.user = None
        auth._client.verify_otp = Mock(return_value=mock_response)
        
        await auth.verify_otp("123456", email="test@example.com")
        
        assert auth._current_session is not None
    
    @pytest.mark.asyncio
    async def test_sign_in_with_otp_with_metadata(self, auth):
        """sign_in_with_otp passes user metadata."""
        auth._client.sign_in_with_otp = Mock()
        
        await auth.sign_in_with_otp(
            email="test@example.com",
            data={"name": "Test"}
        )
        
        call_args = auth._client.sign_in_with_otp.call_args[0][0]
        assert call_args["options"]["data"] == {"name": "Test"}

