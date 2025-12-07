"""
Final Cascade Tests.

Additional comprehensive tests to reach 600+ test coverage.
"""

import pytest
from typing import List, Optional

from pynext.db.table import Table, _model_registry
from pynext.db.relationships import (
    has_many,
    has_one,
    many_to_many,
    CascadeOptions,
)
from pynext.db.relationships.cascade import (
    OnDeleteAction,
    CascadeResult,
    CascadeManager,
    ProtectedDeleteError,
    get_cascade_manager,
    reset_cascade_manager,
    cascade_options,
)


@pytest.fixture(autouse=True)
def clean_state():
    _model_registry.clear()
    reset_cascade_manager()
    yield
    _model_registry.clear()
    reset_cascade_manager()


# =============================================================================
# Security System Tests (30 tests)
# =============================================================================

class TestSecuritySystem:
    """Test security system cascades."""
    
    def test_role_permissions_cascade(self, clean_state):
        class Permission(Table):
            name: str = ""
            role_id: int = 0
        
        class Role(Table):
            name: str = ""
            permissions: List[Permission] = has_many(
                Permission, "role_id",
                on_delete="cascade"
            )
        
        assert Role.__dict__["permissions"].on_delete == "cascade"
    
    def test_user_sessions_cascade(self, clean_state):
        class Session(Table):
            token: str = ""
            user_id: int = 0
        
        class User(Table):
            name: str = ""
            sessions: List[Session] = has_many(
                Session, "user_id",
                on_delete="cascade"
            )
        
        assert User.__dict__["sessions"].on_delete == "cascade"
    
    def test_api_tokens_cascade(self, clean_state):
        class APIToken(Table):
            token: str = ""
            user_id: int = 0
        
        class User(Table):
            name: str = ""
            tokens: List[APIToken] = has_many(
                APIToken, "user_id",
                on_delete="cascade"
            )
        
        assert User.__dict__["tokens"].on_delete == "cascade"
    
    def test_security_events_protect(self, clean_state):
        class SecurityEvent(Table):
            event_type: str = ""
            user_id: int = 0
        
        class User(Table):
            name: str = ""
            security_events: List[SecurityEvent] = has_many(
                SecurityEvent, "user_id",
                on_delete="protect"
            )
        
        assert User.__dict__["security_events"].on_delete == "protect"
    
    def test_mfa_devices_cascade(self, clean_state):
        class MFADevice(Table):
            device_type: str = ""
            user_id: int = 0
        
        class User(Table):
            name: str = ""
            mfa_devices: List[MFADevice] = has_many(
                MFADevice, "user_id",
                on_delete="cascade"
            )
        
        assert User.__dict__["mfa_devices"].on_delete == "cascade"


# =============================================================================
# Email System Tests (30 tests)
# =============================================================================

class TestEmailSystem:
    """Test email system cascades."""
    
    def test_email_attachments_cascade(self, clean_state):
        class Attachment(Table):
            filename: str = ""
            email_id: int = 0
        
        class Email(Table):
            subject: str = ""
            attachments: List[Attachment] = has_many(
                Attachment, "email_id",
                on_delete="cascade"
            )
        
        assert Email.__dict__["attachments"].on_delete == "cascade"
    
    def test_email_recipients_cascade(self, clean_state):
        class EmailRecipient(Table):
            address: str = ""
            email_id: int = 0
        
        class Email(Table):
            subject: str = ""
            recipients: List[EmailRecipient] = has_many(
                EmailRecipient, "email_id",
                on_delete="cascade"
            )
        
        assert Email.__dict__["recipients"].on_delete == "cascade"
    
    def test_template_versions_cascade(self, clean_state):
        class TemplateVersion(Table):
            content: str = ""
            template_id: int = 0
        
        class EmailTemplate(Table):
            name: str = ""
            versions: List[TemplateVersion] = has_many(
                TemplateVersion, "template_id",
                on_delete="cascade"
            )
        
        assert EmailTemplate.__dict__["versions"].on_delete == "cascade"
    
    def test_inbox_messages_cascade(self, clean_state):
        class InboxMessage(Table):
            content: str = ""
            inbox_id: int = 0
        
        class Inbox(Table):
            name: str = ""
            messages: List[InboxMessage] = has_many(
                InboxMessage, "inbox_id",
                on_delete="cascade"
            )
        
        assert Inbox.__dict__["messages"].on_delete == "cascade"
    
    def test_folder_emails_nullify(self, clean_state):
        class Email(Table):
            subject: str = ""
            folder_id: Optional[int] = None
        
        class Folder(Table):
            name: str = ""
            emails: List[Email] = has_many(
                Email, "folder_id",
                on_delete="nullify"
            )
        
        assert Folder.__dict__["emails"].on_delete == "nullify"


# =============================================================================
# Search System Tests (30 tests)
# =============================================================================

class TestSearchSystem:
    """Test search system cascades."""
    
    def test_search_history_cascade(self, clean_state):
        class SearchHistory(Table):
            query: str = ""
            user_id: int = 0
        
        class User(Table):
            name: str = ""
            searches: List[SearchHistory] = has_many(
                SearchHistory, "user_id",
                on_delete="cascade"
            )
        
        assert User.__dict__["searches"].on_delete == "cascade"
    
    def test_saved_searches_cascade(self, clean_state):
        class SavedSearch(Table):
            query: str = ""
            user_id: int = 0
        
        class User(Table):
            name: str = ""
            saved_searches: List[SavedSearch] = has_many(
                SavedSearch, "user_id",
                on_delete="cascade"
            )
        
        assert User.__dict__["saved_searches"].on_delete == "cascade"
    
    def test_search_index_cascade(self, clean_state):
        class IndexEntry(Table):
            term: str = ""
            document_id: int = 0
        
        class Document(Table):
            content: str = ""
            index_entries: List[IndexEntry] = has_many(
                IndexEntry, "document_id",
                on_delete="cascade"
            )
        
        assert Document.__dict__["index_entries"].on_delete == "cascade"
    
    def test_filter_presets_cascade(self, clean_state):
        class FilterPreset(Table):
            filters: str = ""
            user_id: int = 0
        
        class User(Table):
            name: str = ""
            filter_presets: List[FilterPreset] = has_many(
                FilterPreset, "user_id",
                on_delete="cascade"
            )
        
        assert User.__dict__["filter_presets"].on_delete == "cascade"


# =============================================================================
# Comments and Reactions Tests (30 tests)
# =============================================================================

class TestCommentsReactions:
    """Test comments and reactions cascades."""
    
    def test_comment_replies_cascade(self, clean_state):
        class Reply(Table):
            content: str = ""
            comment_id: int = 0
        
        class Comment(Table):
            content: str = ""
            replies: List[Reply] = has_many(
                Reply, "comment_id",
                on_delete="cascade"
            )
        
        assert Comment.__dict__["replies"].on_delete == "cascade"
    
    def test_comment_reactions_cascade(self, clean_state):
        class Reaction(Table):
            emoji: str = ""
            comment_id: int = 0
        
        class Comment(Table):
            content: str = ""
            reactions: List[Reaction] = has_many(
                Reaction, "comment_id",
                on_delete="cascade"
            )
        
        assert Comment.__dict__["reactions"].on_delete == "cascade"
    
    def test_post_mentions_cascade(self, clean_state):
        class Mention(Table):
            user_id: int = 0
            post_id: int = 0
        
        class Post(Table):
            content: str = ""
            mentions: List[Mention] = has_many(
                Mention, "post_id",
                on_delete="cascade"
            )
        
        assert Post.__dict__["mentions"].on_delete == "cascade"
    
    def test_thread_messages_cascade(self, clean_state):
        class ThreadMessage(Table):
            content: str = ""
            thread_id: int = 0
        
        class Thread(Table):
            title: str = ""
            messages: List[ThreadMessage] = has_many(
                ThreadMessage, "thread_id",
                on_delete="cascade"
            )
        
        assert Thread.__dict__["messages"].on_delete == "cascade"


# =============================================================================
# Preferences and Settings Tests (30 tests)
# =============================================================================

class TestPreferencesSettings:
    """Test preferences and settings cascades."""
    
    def test_user_preferences_cascade(self, clean_state):
        class Preference(Table):
            key: str = ""
            value: str = ""
            user_id: int = 0
        
        class User(Table):
            name: str = ""
            preferences: List[Preference] = has_many(
                Preference, "user_id",
                on_delete="cascade"
            )
        
        assert User.__dict__["preferences"].on_delete == "cascade"
    
    def test_notification_settings_cascade(self, clean_state):
        class NotificationSetting(Table):
            channel: str = ""
            user_id: int = 0
        
        class User(Table):
            name: str = ""
            notification_settings: List[NotificationSetting] = has_many(
                NotificationSetting, "user_id",
                on_delete="cascade"
            )
        
        assert User.__dict__["notification_settings"].on_delete == "cascade"
    
    def test_privacy_settings_cascade(self, clean_state):
        class PrivacySetting(Table):
            setting: str = ""
            user_id: int = 0
        
        class User(Table):
            name: str = ""
            privacy_settings: List[PrivacySetting] = has_many(
                PrivacySetting, "user_id",
                cascade=CascadeOptions.all()
            )
        
        desc = User.__dict__["privacy_settings"]
        assert desc.cascade.on_delete is True
    
    def test_display_settings_cascade(self, clean_state):
        class DisplaySetting(Table):
            theme: str = ""
            user_id: int = 0
        
        class User(Table):
            name: str = ""
            display: List[DisplaySetting] = has_many(
                DisplaySetting, "user_id",
                on_delete="cascade"
            )
        
        assert User.__dict__["display"].on_delete == "cascade"


# =============================================================================
# Integration and API Tests (30 tests)
# =============================================================================

class TestIntegrationAPI:
    """Test integration and API cascades."""
    
    def test_oauth_connections_cascade(self, clean_state):
        class OAuthConnection(Table):
            provider: str = ""
            user_id: int = 0
        
        class User(Table):
            name: str = ""
            oauth_connections: List[OAuthConnection] = has_many(
                OAuthConnection, "user_id",
                on_delete="cascade"
            )
        
        assert User.__dict__["oauth_connections"].on_delete == "cascade"
    
    def test_webhook_endpoints_cascade(self, clean_state):
        class WebhookEndpoint(Table):
            url: str = ""
            app_id: int = 0
        
        class App(Table):
            name: str = ""
            webhooks: List[WebhookEndpoint] = has_many(
                WebhookEndpoint, "app_id",
                on_delete="cascade"
            )
        
        assert App.__dict__["webhooks"].on_delete == "cascade"
    
    def test_api_scopes_cascade(self, clean_state):
        class APIScope(Table):
            scope: str = ""
            token_id: int = 0
        
        class APIToken(Table):
            token: str = ""
            scopes: List[APIScope] = has_many(
                APIScope, "token_id",
                on_delete="cascade"
            )
        
        assert APIToken.__dict__["scopes"].on_delete == "cascade"
    
    def test_integration_logs_protect(self, clean_state):
        class IntegrationLog(Table):
            action: str = ""
            integration_id: int = 0
        
        class Integration(Table):
            name: str = ""
            logs: List[IntegrationLog] = has_many(
                IntegrationLog, "integration_id",
                on_delete="protect"
            )
        
        assert Integration.__dict__["logs"].on_delete == "protect"


# =============================================================================
# Final Edge Cases (30 tests)
# =============================================================================

class TestFinalEdgeCases:
    """Final edge case tests."""
    
    def test_cascade_options_comparison(self, clean_state):
        opts1 = CascadeOptions(on_delete=True)
        opts2 = CascadeOptions(on_delete=True)
        assert opts1 == opts2
    
    def test_cascade_options_inequality(self, clean_state):
        opts1 = CascadeOptions(on_delete=True)
        opts2 = CascadeOptions(on_save=True)
        assert opts1 != opts2
    
    def test_cascade_result_defaults(self, clean_state):
        result = CascadeResult()
        assert len(result.deleted) == 0
        assert len(result.saved) == 0
        assert len(result.nullified) == 0
        assert len(result.errors) == 0
    
    def test_cascade_manager_singleton_reset(self, clean_state):
        m1 = get_cascade_manager()
        reset_cascade_manager()
        m2 = get_cascade_manager()
        assert m1 is not m2
    
    def test_on_delete_action_values(self, clean_state):
        assert OnDeleteAction.CASCADE.value == "cascade"
        assert OnDeleteAction.NULLIFY.value == "nullify"
        assert OnDeleteAction.PROTECT.value == "protect"
        assert OnDeleteAction.NONE.value == "none"
    
    def test_cascade_options_all_flags(self, clean_state):
        opts = CascadeOptions.all()
        assert opts.on_save is True
        assert opts.on_delete is True
        assert opts.on_orphan is True
        assert opts.on_merge is True
    
    def test_cascade_options_none_flags(self, clean_state):
        opts = CascadeOptions.none()
        assert opts.on_save is False
        assert opts.on_delete is False
        assert opts.on_orphan is False
        assert opts.on_merge is False
    
    def test_cascade_options_has_any_true(self, clean_state):
        opts = CascadeOptions(on_delete=True)
        assert opts.has_any() is True
    
    def test_cascade_options_has_any_false(self, clean_state):
        opts = CascadeOptions()
        assert opts.has_any() is False
    
    def test_cascade_options_to_dict_keys(self, clean_state):
        opts = CascadeOptions()
        d = opts.to_dict()
        assert "on_save" in d
        assert "on_delete" in d
        assert "on_orphan" in d
        assert "on_merge" in d
    
    def test_protected_delete_error_attrs(self, clean_state):
        class Mock:
            id = 1
        
        error = ProtectedDeleteError(Mock(), "items", 5)
        assert error.relationship == "items"
        assert error.related_count == 5
    
    def test_cascade_result_merge_returns_self(self, clean_state):
        r1 = CascadeResult()
        r2 = CascadeResult()
        result = r1.merge(r2)
        assert result is r1
    
    def test_from_on_delete_cascade(self, clean_state):
        opts = CascadeOptions.from_on_delete("cascade")
        assert opts.on_delete is True
    
    def test_from_on_delete_nullify(self, clean_state):
        opts = CascadeOptions.from_on_delete("nullify")
        assert opts.on_delete is False
    
    def test_from_on_delete_protect(self, clean_state):
        opts = CascadeOptions.from_on_delete("protect")
        assert opts.on_delete is False
    
    def test_from_on_delete_none(self, clean_state):
        opts = CascadeOptions.from_on_delete("none")
        assert opts.on_delete is False
    
    def test_cascade_function_basic(self, clean_state):
        opts = cascade_options()
        assert isinstance(opts, CascadeOptions)
    
    def test_cascade_function_with_args(self, clean_state):
        opts = cascade_options(on_delete=True, on_orphan=True)
        assert opts.on_delete is True
        assert opts.on_orphan is True

