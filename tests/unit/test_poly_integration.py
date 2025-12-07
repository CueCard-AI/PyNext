"""
Test Phase 7.7: Polymorphic Integration Tests.

Real-world integration patterns for polymorphic relationships.
"""

import pytest
from typing import Optional, Union, List
from datetime import datetime
from unittest.mock import Mock, MagicMock, AsyncMock, patch

from pynext.db.polymorphic import (
    polymorphic,
    generic_fk,
    get_strategy,
    get_polymorphic_registry,
    reset_polymorphic_registry,
    instantiate_polymorphic,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def reset_registry():
    """Reset registry before each test."""
    reset_polymorphic_registry()
    yield
    reset_polymorphic_registry()


# =============================================================================
# Pattern: Content Management System
# =============================================================================

class TestCMSPattern:
    """Test CMS-style polymorphic content."""
    
    def test_cms_hierarchy(self):
        """Define CMS content hierarchy."""
        @polymorphic("content_type")
        class Content:
            __tablename__ = "contents"
            id: int
            title: str
            slug: str
            published: bool
            created_at: datetime
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        @polymorphic.subtype("article")
        class Article(Content):
            body: str
            author_id: int
        
        @polymorphic.subtype("video")
        class Video(Content):
            url: str
            duration: int
            thumbnail: str
        
        @polymorphic.subtype("gallery")
        class Gallery(Content):
            image_urls: List[str]
        
        # All are properly registered
        registry = get_polymorphic_registry()
        assert registry.get_class(Content, "article") == Article
        assert registry.get_class(Content, "video") == Video
        assert registry.get_class(Content, "gallery") == Gallery
    
    def test_cms_instantiation(self):
        """Instantiate CMS content from rows."""
        @polymorphic("type")
        class Content:
            __tablename__ = "contents"
            id: int
            title: str
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        @polymorphic.subtype("article")
        class Article(Content):
            body: str
        
        @polymorphic.subtype("video")
        class Video(Content):
            url: str
        
        strategy = get_strategy(Content)
        
        # Simulate database rows
        rows = [
            {"id": 1, "title": "Article 1", "type": "article", "body": "Content..."},
            {"id": 2, "title": "Video 1", "type": "video", "url": "http://..."},
            {"id": 3, "title": "Article 2", "type": "article", "body": "More..."},
        ]
        
        instances = [strategy.instantiate_from_row(row) for row in rows]
        
        assert isinstance(instances[0], Article)
        assert isinstance(instances[1], Video)
        assert isinstance(instances[2], Article)


# =============================================================================
# Pattern: E-Commerce Products
# =============================================================================

class TestECommercePattern:
    """Test e-commerce product hierarchy."""
    
    def test_product_hierarchy(self):
        """Define product hierarchy."""
        @polymorphic("product_type", strategy="joined")
        class Product:
            __tablename__ = "products"
            id: int
            name: str
            price: float
            stock: int
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        @polymorphic.subtype("physical")
        class PhysicalProduct(Product):
            __tablename__ = "physical_products"
            weight: float
            dimensions: str
            shipping_class: str
        
        @polymorphic.subtype("digital")
        class DigitalProduct(Product):
            __tablename__ = "digital_products"
            download_url: str
            file_size: int
            license_type: str
        
        @polymorphic.subtype("subscription")
        class SubscriptionProduct(Product):
            __tablename__ = "subscription_products"
            billing_period: str
            trial_days: int
        
        # All registered correctly
        registry = get_polymorphic_registry()
        assert len(registry.get_all_subtypes(Product)) == 3


# =============================================================================
# Pattern: Activity Feed
# =============================================================================

class TestActivityFeedPattern:
    """Test activity feed with generic FKs."""
    
    def test_activity_with_generic_target(self):
        """Activity referencing different content types."""
        class Post:
            __tablename__ = "posts"
            
            def __init__(self, id, title):
                self.id = id
                self.title = title
        
        class Comment:
            __tablename__ = "comments"
            
            def __init__(self, id, content):
                self.id = id
                self.content = content
        
        class Like:
            __tablename__ = "likes"
            
            def __init__(self, id):
                self.id = id
        
        class Activity:
            actor_id: int
            action: str
            target: Union[Post, Comment, Like] = generic_fk()
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        # Create activities
        post = Post(id=1, title="Hello World")
        comment = Comment(id=1, content="Great post!")
        like = Like(id=1)
        
        activity1 = Activity(actor_id=1, action="created")
        activity1.target = post
        
        activity2 = Activity(actor_id=2, action="commented")
        activity2.target = comment
        
        activity3 = Activity(actor_id=3, action="liked")
        activity3.target = like
        
        assert activity1.target_type == "posts"
        assert activity2.target_type == "comments"
        assert activity3.target_type == "likes"


# =============================================================================
# Pattern: Notifications
# =============================================================================

class TestNotificationPattern:
    """Test notification system."""
    
    def test_polymorphic_notifications(self):
        """Different notification types."""
        @polymorphic("notification_type")
        class Notification:
            __tablename__ = "notifications"
            id: int
            user_id: int
            read: bool
            created_at: datetime
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        @polymorphic.subtype("mention")
        class MentionNotification(Notification):
            mentioned_by_id: int
            post_id: int
        
        @polymorphic.subtype("follow")
        class FollowNotification(Notification):
            follower_id: int
        
        @polymorphic.subtype("like")
        class LikeNotification(Notification):
            liker_id: int
            target_type: str
            target_id: int
        
        strategy = get_strategy(Notification)
        
        # Create from rows
        rows = [
            {"id": 1, "user_id": 100, "notification_type": "mention", 
             "mentioned_by_id": 5, "post_id": 42, "read": False,
             "created_at": datetime.now()},
            {"id": 2, "user_id": 100, "notification_type": "follow",
             "follower_id": 7, "read": True, "created_at": datetime.now()},
        ]
        
        notifications = [strategy.instantiate_from_row(row) for row in rows]
        
        assert isinstance(notifications[0], MentionNotification)
        assert isinstance(notifications[1], FollowNotification)
        assert notifications[0].mentioned_by_id == 5


# =============================================================================
# Pattern: Payment Methods
# =============================================================================

class TestPaymentPattern:
    """Test payment method hierarchy."""
    
    def test_payment_methods(self):
        """Different payment method types."""
        @polymorphic("method_type")
        class PaymentMethod:
            __tablename__ = "payment_methods"
            id: int
            user_id: int
            is_default: bool
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        @polymorphic.subtype("credit_card")
        class CreditCard(PaymentMethod):
            last_four: str
            brand: str
            exp_month: int
            exp_year: int
        
        @polymorphic.subtype("bank_account")
        class BankAccount(PaymentMethod):
            bank_name: str
            account_type: str
            last_four: str
        
        @polymorphic.subtype("paypal")
        class PayPal(PaymentMethod):
            email: str
        
        strategy = get_strategy(PaymentMethod)
        
        # Credit card
        cc_row = {
            "id": 1, "user_id": 100, "method_type": "credit_card",
            "is_default": True, "last_four": "4242", "brand": "Visa",
            "exp_month": 12, "exp_year": 2025
        }
        
        cc = strategy.instantiate_from_row(cc_row)
        assert isinstance(cc, CreditCard)
        assert cc.last_four == "4242"
        assert cc.brand == "Visa"


# =============================================================================
# Pattern: Audit Log
# =============================================================================

class TestAuditLogPattern:
    """Test audit log with polymorphic targets."""
    
    def test_audit_log(self):
        """Audit log tracking changes to various entities."""
        class User:
            __tablename__ = "users"
            
            def __init__(self, id, name):
                self.id = id
                self.name = name
        
        class Product:
            __tablename__ = "products"
            
            def __init__(self, id, name):
                self.id = id
                self.name = name
        
        class Order:
            __tablename__ = "orders"
            
            def __init__(self, id, total):
                self.id = id
                self.total = total
        
        class AuditLog:
            id: int
            action: str  # create, update, delete
            changed_by_id: int
            changed_at: datetime
            entity: Union[User, Product, Order] = generic_fk()
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        # Log changes
        user = User(id=1, name="Alice")
        product = Product(id=1, name="Widget")
        order = Order(id=1, total=99.99)
        
        logs = [
            AuditLog(id=1, action="create", changed_by_id=1, 
                    changed_at=datetime.now()),
            AuditLog(id=2, action="update", changed_by_id=1,
                    changed_at=datetime.now()),
        ]
        
        logs[0].entity = user
        logs[1].entity = product
        
        assert logs[0].entity_type == "users"
        assert logs[1].entity_type == "products"

