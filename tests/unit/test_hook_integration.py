"""
Tests for hook integration patterns.

Tests real-world patterns and integration scenarios:
- Audit logging
- Notifications
- Validation
- Caching
- Statistics tracking
- Cascading operations
"""

import pytest
from typing import List, Optional, Any, Dict
from datetime import datetime

from pynext.db.relationships.hooks import (
    HookType,
    on_append,
    on_remove,
    on_set,
    before_delete,
    get_hook_registry,
    reset_hook_registries,
    discover_hooks,
)
from pynext.db.relationships.hook_executor import (
    fire_on_append,
    fire_on_remove,
    fire_on_set,
    fire_before_delete,
    reset_hook_executor,
)


# =============================================================================
# Mock Classes for Testing
# =============================================================================

class MockTable:
    """Base mock table for testing."""
    _fields = {}
    __table_name__ = "mock_table"
    
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class MockPost(MockTable):
    """Mock post for testing."""
    __table_name__ = "posts"
    
    def __init__(self, id: int = 1, title: str = "Test", author_id: int = None):
        super().__init__(id=id, title=title, author_id=author_id)


class MockComment(MockTable):
    """Mock comment for testing."""
    __table_name__ = "comments"
    
    def __init__(self, id: int = 1, content: str = "Test", post_id: int = None):
        super().__init__(id=id, content=content, post_id=post_id)


class MockProfile(MockTable):
    """Mock profile for testing."""
    __table_name__ = "profiles"
    
    def __init__(self, id: int = 1, bio: str = "Test bio"):
        super().__init__(id=id, bio=bio)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def reset_registries():
    """Reset all registries before each test."""
    reset_hook_registries()
    reset_hook_executor()
    yield
    reset_hook_registries()
    reset_hook_executor()


# =============================================================================
# Test: Audit Logging Pattern
# =============================================================================

class TestAuditLoggingPattern:
    """Test audit logging pattern with hooks."""
    
    def test_log_collection_append(self):
        """Log when items are added to collection."""
        audit_log = []
        
        class User(MockTable):
            @on_append("posts")
            def log_post_added(self, post):
                audit_log.append({
                    "action": "add",
                    "user_id": self.id,
                    "post_id": post.id,
                    "timestamp": "now",
                })
        
        discover_hooks(User)
        
        user = User(id=1, name="Alice")
        fire_on_append(user, "posts", MockPost(id=10, title="Hello"))
        fire_on_append(user, "posts", MockPost(id=20, title="World"))
        
        assert len(audit_log) == 2
        assert audit_log[0]["action"] == "add"
        assert audit_log[0]["user_id"] == 1
        assert audit_log[0]["post_id"] == 10
    
    def test_log_collection_remove(self):
        """Log when items are removed from collection."""
        audit_log = []
        
        class User(MockTable):
            @on_remove("posts")
            def log_post_removed(self, post):
                audit_log.append({
                    "action": "remove",
                    "user_id": self.id,
                    "post_id": post.id,
                })
        
        discover_hooks(User)
        
        user = User(id=1)
        fire_on_remove(user, "posts", MockPost(id=10))
        
        assert len(audit_log) == 1
        assert audit_log[0]["action"] == "remove"
    
    def test_log_relationship_change(self):
        """Log when relationship changes."""
        audit_log = []
        
        class Post(MockTable):
            @on_set("author")
            def log_author_changed(self, old_author, new_author):
                audit_log.append({
                    "action": "author_changed",
                    "post_id": self.id,
                    "old_author_id": old_author.id if old_author else None,
                    "new_author_id": new_author.id if new_author else None,
                })
        
        discover_hooks(Post)
        
        post = Post(id=1)
        alice = MockTable(id=10, name="Alice")
        bob = MockTable(id=20, name="Bob")
        
        fire_on_set(post, "author", None, alice)
        fire_on_set(post, "author", alice, bob)
        
        assert len(audit_log) == 2
        assert audit_log[0]["old_author_id"] is None
        assert audit_log[0]["new_author_id"] == 10
        assert audit_log[1]["old_author_id"] == 10
        assert audit_log[1]["new_author_id"] == 20
    
    def test_log_before_delete(self):
        """Log before entity is deleted."""
        audit_log = []
        
        class User(MockTable):
            @before_delete()
            def log_deletion(self):
                audit_log.append({
                    "action": "delete",
                    "user_id": self.id,
                    "user_name": self.name,
                    "user_email": self.email,
                })
        
        discover_hooks(User)
        
        user = User(id=1, name="Alice", email="alice@example.com")
        fire_before_delete(user)
        
        assert len(audit_log) == 1
        assert audit_log[0]["user_id"] == 1
        assert audit_log[0]["user_name"] == "Alice"


# =============================================================================
# Test: Notification Pattern
# =============================================================================

class TestNotificationPattern:
    """Test notification pattern with hooks."""
    
    def test_notify_on_new_post(self):
        """Send notification when new post is added."""
        notifications = []
        
        class User(MockTable):
            @on_append("posts")
            def notify_new_post(self, post):
                notifications.append({
                    "type": "new_post",
                    "recipient": self.id,
                    "message": f"New post: {post.title}",
                })
        
        discover_hooks(User)
        
        user = User(id=1)
        fire_on_append(user, "posts", MockPost(id=10, title="Hello World"))
        
        assert len(notifications) == 1
        assert notifications[0]["type"] == "new_post"
        assert "Hello World" in notifications[0]["message"]
    
    def test_notify_on_follower_added(self):
        """Notify when new follower is added."""
        notifications = []
        
        class User(MockTable):
            @on_append("followers")
            def notify_new_follower(self, follower):
                notifications.append({
                    "to": self.id,
                    "message": f"{follower.name} started following you",
                })
        
        discover_hooks(User)
        
        user = User(id=1, name="Alice")
        follower = MockTable(id=2, name="Bob")
        
        fire_on_append(user, "followers", follower)
        
        assert len(notifications) == 1
        assert "Bob" in notifications[0]["message"]


# =============================================================================
# Test: Validation Pattern
# =============================================================================

class TestValidationPattern:
    """Test validation pattern with hooks."""
    
    def test_validate_on_append(self):
        """Validate item on append."""
        
        class User(MockTable):
            @on_append("posts")
            def validate_post(self, post):
                if not post.title or len(post.title) < 3:
                    raise ValueError("Post title must be at least 3 characters")
        
        discover_hooks(User)
        
        user = User(id=1)
        
        # Valid post
        fire_on_append(user, "posts", MockPost(id=1, title="Hello"))
        
        # Invalid post
        with pytest.raises(ValueError, match="at least 3 characters"):
            fire_on_append(user, "posts", MockPost(id=2, title="Hi"))
    
    def test_validate_relationship_set(self):
        """Validate relationship on set."""
        
        class Post(MockTable):
            @on_set("category")
            def validate_category(self, old, new):
                if new and not hasattr(new, "is_active"):
                    raise ValueError("Category must have is_active attribute")
        
        discover_hooks(Post)
        
        post = Post(id=1)
        category = MockTable(id=1, name="Tech", is_active=True)
        
        # Valid category
        fire_on_set(post, "category", None, category)
        
        # Invalid category
        bad_category = MockTable(id=2, name="Bad")
        with pytest.raises(ValueError, match="is_active"):
            fire_on_set(post, "category", category, bad_category)


# =============================================================================
# Test: Statistics Tracking Pattern
# =============================================================================

class TestStatisticsPattern:
    """Test statistics tracking pattern."""
    
    def test_track_post_count(self):
        """Track post count on append/remove."""
        
        stats = {"posts_added": 0, "posts_removed": 0}
        
        class User(MockTable):
            @on_append("posts")
            def increment_posts(self, post):
                stats["posts_added"] += 1
            
            @on_remove("posts")
            def decrement_posts(self, post):
                stats["posts_removed"] += 1
        
        discover_hooks(User)
        
        user = User(id=1)
        
        fire_on_append(user, "posts", MockPost(id=1))
        fire_on_append(user, "posts", MockPost(id=2))
        fire_on_append(user, "posts", MockPost(id=3))
        fire_on_remove(user, "posts", MockPost(id=1))
        
        assert stats["posts_added"] == 3
        assert stats["posts_removed"] == 1
    
    def test_track_per_user_stats(self):
        """Track statistics per user."""
        
        user_stats: Dict[int, Dict[str, int]] = {}
        
        class User(MockTable):
            @on_append("posts")
            def track_post(self, post):
                if self.id not in user_stats:
                    user_stats[self.id] = {"posts": 0}
                user_stats[self.id]["posts"] += 1
        
        discover_hooks(User)
        
        user1 = User(id=1)
        user2 = User(id=2)
        
        fire_on_append(user1, "posts", MockPost(id=1))
        fire_on_append(user1, "posts", MockPost(id=2))
        fire_on_append(user2, "posts", MockPost(id=3))
        
        assert user_stats[1]["posts"] == 2
        assert user_stats[2]["posts"] == 1


# =============================================================================
# Test: Caching Pattern
# =============================================================================

class TestCachingPattern:
    """Test caching pattern with hooks."""
    
    def test_invalidate_cache_on_change(self):
        """Invalidate cache when collection changes."""
        
        cache_invalidations = []
        
        class User(MockTable):
            @on_append("posts")
            def invalidate_posts_cache(self, post):
                cache_invalidations.append(f"user:{self.id}:posts")
            
            @on_remove("posts")
            def invalidate_posts_cache_on_remove(self, post):
                cache_invalidations.append(f"user:{self.id}:posts")
        
        discover_hooks(User)
        
        user = User(id=42)
        
        fire_on_append(user, "posts", MockPost(id=1))
        fire_on_remove(user, "posts", MockPost(id=1))
        
        assert cache_invalidations == ["user:42:posts", "user:42:posts"]
    
    def test_clear_related_caches(self):
        """Clear related caches on relationship change."""
        
        cleared_caches = []
        
        class Post(MockTable):
            @on_set("author")
            def clear_author_cache(self, old_author, new_author):
                if old_author:
                    cleared_caches.append(f"user:{old_author.id}:posts")
                if new_author:
                    cleared_caches.append(f"user:{new_author.id}:posts")
        
        discover_hooks(Post)
        
        post = Post(id=1)
        alice = MockTable(id=10)
        bob = MockTable(id=20)
        
        fire_on_set(post, "author", alice, bob)
        
        assert "user:10:posts" in cleared_caches
        assert "user:20:posts" in cleared_caches


# =============================================================================
# Test: Cleanup Pattern
# =============================================================================

class TestCleanupPattern:
    """Test cleanup pattern with before_delete."""
    
    def test_cleanup_files_before_delete(self):
        """Clean up files before entity deletion."""
        
        cleaned_files = []
        
        class User(MockTable):
            @before_delete()
            def cleanup_files(self):
                cleaned_files.append(f"avatar_{self.id}.jpg")
                cleaned_files.append(f"data_{self.id}/")
        
        discover_hooks(User)
        
        user = User(id=123)
        fire_before_delete(user)
        
        assert cleaned_files == ["avatar_123.jpg", "data_123/"]
    
    def test_cleanup_sessions_before_delete(self):
        """Clean up sessions before user deletion."""
        
        invalidated_sessions = []
        
        class User(MockTable):
            @before_delete()
            def invalidate_sessions(self):
                invalidated_sessions.append(f"session:{self.id}:*")
        
        discover_hooks(User)
        
        user = User(id=42)
        fire_before_delete(user)
        
        assert invalidated_sessions == ["session:42:*"]


# =============================================================================
# Test: Cascading Operations Pattern
# =============================================================================

class TestCascadingPattern:
    """Test cascading operations with hooks."""
    
    def test_cascade_update_timestamps(self):
        """Cascade update timestamps on relationship change."""
        
        updated_timestamps = []
        
        class User(MockTable):
            @on_append("posts")
            def update_last_activity(self, post):
                updated_timestamps.append({
                    "entity": "user",
                    "id": self.id,
                    "field": "last_activity",
                })
        
        discover_hooks(User)
        
        user = User(id=1)
        fire_on_append(user, "posts", MockPost(id=1))
        
        assert len(updated_timestamps) == 1
        assert updated_timestamps[0]["entity"] == "user"
    
    def test_cascade_notify_related(self):
        """Cascade notifications to related entities."""
        
        notifications = []
        
        class Post(MockTable):
            @on_append("comments")
            def notify_author_of_comment(self, comment):
                notifications.append({
                    "to": f"author_of_post_{self.id}",
                    "message": f"New comment on your post: {comment.content}",
                })
        
        discover_hooks(Post)
        
        post = Post(id=1)
        fire_on_append(post, "comments", MockComment(id=1, content="Great post!"))
        
        assert len(notifications) == 1
        assert "Great post!" in notifications[0]["message"]


# =============================================================================
# Test: Complex Real-World Scenario
# =============================================================================

class TestComplexScenario:
    """Test complex real-world scenario."""
    
    def test_complete_user_workflow(self):
        """Test complete user workflow with multiple hooks."""
        
        events = []
        
        class User(MockTable):
            @on_append("posts")
            def on_post_added(self, post):
                events.append(f"post_added:{post.id}")
            
            @on_remove("posts")
            def on_post_removed(self, post):
                events.append(f"post_removed:{post.id}")
            
            @on_set("profile")
            def on_profile_changed(self, old, new):
                old_id = old.id if old else None
                new_id = new.id if new else None
                events.append(f"profile_changed:{old_id}->{new_id}")
            
            @before_delete()
            def on_delete(self):
                events.append(f"user_deleting:{self.id}")
        
        discover_hooks(User)
        
        user = User(id=1, name="Alice")
        
        # Add posts
        fire_on_append(user, "posts", MockPost(id=10))
        fire_on_append(user, "posts", MockPost(id=20))
        
        # Set profile
        fire_on_set(user, "profile", None, MockProfile(id=1))
        fire_on_set(user, "profile", MockProfile(id=1), MockProfile(id=2))
        
        # Remove post
        fire_on_remove(user, "posts", MockPost(id=10))
        
        # Delete user
        fire_before_delete(user)
        
        assert events == [
            "post_added:10",
            "post_added:20",
            "profile_changed:None->1",
            "profile_changed:1->2",
            "post_removed:10",
            "user_deleting:1",
        ]
    
    def test_multi_model_hooks(self):
        """Test hooks across multiple models."""
        
        events = []
        
        class User(MockTable):
            @on_append("posts")
            def user_post_added(self, post):
                events.append(f"user:{self.id}:post_added:{post.id}")
        
        class Post(MockTable):
            @on_append("comments")
            def post_comment_added(self, comment):
                events.append(f"post:{self.id}:comment_added:{comment.id}")
        
        discover_hooks(User)
        discover_hooks(Post)
        
        user = User(id=1)
        post = Post(id=10)
        
        fire_on_append(user, "posts", post)
        fire_on_append(post, "comments", MockComment(id=100))
        fire_on_append(post, "comments", MockComment(id=101))
        
        assert events == [
            "user:1:post_added:10",
            "post:10:comment_added:100",
            "post:10:comment_added:101",
        ]


# =============================================================================
# Test: Error Recovery Pattern
# =============================================================================

class TestErrorRecoveryPattern:
    """Test error recovery patterns."""
    
    def test_rollback_on_error(self):
        """Track state for potential rollback on error."""
        
        state_before_error = []
        
        class User(MockTable):
            @on_append("posts")
            def track_before_op(self, post):
                # In real app, this would save state for rollback
                state_before_error.append({
                    "user_id": self.id,
                    "post_id": post.id,
                })
                
                # Simulate potential error
                if post.id == 999:
                    raise ValueError("Invalid post")
        
        discover_hooks(User)
        
        user = User(id=1)
        
        # Normal operation
        fire_on_append(user, "posts", MockPost(id=1))
        
        # Error case
        with pytest.raises(ValueError):
            fire_on_append(user, "posts", MockPost(id=999))
        
        # State was tracked before error
        assert len(state_before_error) == 2
        assert state_before_error[1]["post_id"] == 999

