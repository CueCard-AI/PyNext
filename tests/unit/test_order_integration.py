"""
Tests for real-world ordering integration patterns.

Tests cover:
- Blog posts ordering
- E-commerce product ordering
- Task/todo list ordering
- Comment threads
- Social media feeds
- Multi-level categories
"""

import pytest
from typing import List, Optional
from datetime import datetime, date, timedelta

from pynext.db.relationships.ordering import (
    OrderSpec,
    OrderingConfig,
    parse_order_by,
    build_order_clause,
    sort_items,
    asc,
    desc,
)
from pynext.db.relationships.core import has_many, many_to_many


# =============================================================================
# Mock Models for Real-World Scenarios
# =============================================================================

class MockUser:
    """Mock User model."""
    
    def __init__(self, id=None, name=None):
        self.id = id
        self.name = name


class MockPost:
    """Mock Post model for blog."""
    
    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.title = kwargs.get("title")
        self.created_at = kwargs.get("created_at", datetime.now())
        self.updated_at = kwargs.get("updated_at")
        self.pinned = kwargs.get("pinned", False)
        self.featured = kwargs.get("featured", False)
        self.views = kwargs.get("views", 0)
        self.status = kwargs.get("status", "draft")


class MockComment:
    """Mock Comment model."""
    
    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.content = kwargs.get("content")
        self.created_at = kwargs.get("created_at", datetime.now())
        self.votes = kwargs.get("votes", 0)
        self.highlighted = kwargs.get("highlighted", False)
        self.parent_id = kwargs.get("parent_id")


class MockProduct:
    """Mock Product model for e-commerce."""
    
    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.name = kwargs.get("name")
        self.price = kwargs.get("price", 0)
        self.rating = kwargs.get("rating")
        self.sold_count = kwargs.get("sold_count", 0)
        self.position = kwargs.get("position", 0)
        self.featured = kwargs.get("featured", False)
        self.in_stock = kwargs.get("in_stock", True)


class MockTask:
    """Mock Task model for todo app."""
    
    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.title = kwargs.get("title")
        self.priority = kwargs.get("priority", 0)
        self.due_date = kwargs.get("due_date")
        self.created_at = kwargs.get("created_at", datetime.now())
        self.completed = kwargs.get("completed", False)
        self.project_id = kwargs.get("project_id")


class MockCategory:
    """Mock Category model for nested categories."""
    
    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.name = kwargs.get("name")
        self.position = kwargs.get("position", 0)
        self.parent_id = kwargs.get("parent_id")


class MockFeedItem:
    """Mock Feed item for social media."""
    
    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.content = kwargs.get("content")
        self.created_at = kwargs.get("created_at", datetime.now())
        self.engagement_score = kwargs.get("engagement_score", 0)
        self.promoted = kwargs.get("promoted", False)


# =============================================================================
# Test: Blog Post Ordering
# =============================================================================

class TestBlogPostOrdering:
    """Test blog post ordering patterns."""
    
    def test_chronological_newest_first(self):
        """Posts ordered by created_at desc (newest first)."""
        rel = has_many(MockPost, order_by="created_at desc")
        rel.rel_name = "posts"
        
        sql = rel.ordering.to_sql()
        assert sql == "ORDER BY created_at DESC"
    
    def test_pinned_posts_first(self):
        """Pinned posts first, then by date."""
        rel = has_many(MockPost, order_by=["pinned desc", "created_at desc"])
        rel.rel_name = "posts"
        
        sql = rel.ordering.to_sql()
        assert "pinned DESC" in sql
        assert "created_at DESC" in sql
    
    def test_featured_and_pinned(self):
        """Featured first, then pinned, then by date."""
        rel = has_many(MockPost, order_by=[
            "featured desc",
            "pinned desc",
            "created_at desc"
        ])
        rel.rel_name = "posts"
        
        columns = rel.ordering.get_columns()
        assert columns[0] == "featured DESC"
        assert columns[1] == "pinned DESC"
        assert columns[2] == "created_at DESC"
    
    def test_most_viewed_posts(self):
        """Posts ordered by view count."""
        rel = has_many(MockPost, order_by="views desc")
        rel.rel_name = "popular_posts"
        
        sql = rel.ordering.to_sql()
        assert sql == "ORDER BY views DESC"
    
    def test_recently_updated(self):
        """Posts ordered by updated_at."""
        rel = has_many(MockPost, order_by="updated_at desc nulls last")
        rel.rel_name = "recent_posts"
        
        sql = rel.ordering.to_sql()
        assert "updated_at DESC NULLS LAST" in sql


class TestBlogPostSorting:
    """Test in-memory blog post sorting."""
    
    def test_sort_by_date(self):
        """Sort posts by date."""
        now = datetime.now()
        posts = [
            MockPost(title="Old", created_at=now - timedelta(days=10)),
            MockPost(title="New", created_at=now),
            MockPost(title="Medium", created_at=now - timedelta(days=5)),
        ]
        
        specs = [OrderSpec("created_at", "desc")]
        sorted_posts = sort_items(posts, specs)
        
        assert sorted_posts[0].title == "New"
        assert sorted_posts[-1].title == "Old"
    
    def test_sort_pinned_first(self):
        """Sort with pinned posts first."""
        posts = [
            MockPost(title="Normal1", pinned=False, created_at=datetime.now()),
            MockPost(title="Pinned", pinned=True, created_at=datetime.now() - timedelta(days=1)),
            MockPost(title="Normal2", pinned=False, created_at=datetime.now()),
        ]
        
        specs = [
            OrderSpec("pinned", "desc"),
            OrderSpec("created_at", "desc")
        ]
        sorted_posts = sort_items(posts, specs)
        
        assert sorted_posts[0].title == "Pinned"


# =============================================================================
# Test: E-commerce Product Ordering
# =============================================================================

class TestProductOrdering:
    """Test e-commerce product ordering patterns."""
    
    def test_bestsellers(self):
        """Products ordered by sales count."""
        rel = has_many(MockProduct, order_by="sold_count desc")
        rel.rel_name = "bestsellers"
        
        sql = rel.ordering.to_sql()
        assert sql == "ORDER BY sold_count DESC"
    
    def test_top_rated(self):
        """Products ordered by rating (nulls last)."""
        rel = has_many(MockProduct, order_by="rating desc nulls last")
        rel.rel_name = "top_rated"
        
        sql = rel.ordering.to_sql()
        assert "rating DESC NULLS LAST" in sql
    
    def test_price_low_to_high(self):
        """Products ordered by price ascending."""
        rel = has_many(MockProduct, order_by="price")
        rel.rel_name = "products"
        
        sql = rel.ordering.to_sql()
        assert sql == "ORDER BY price ASC"
    
    def test_price_high_to_low(self):
        """Products ordered by price descending."""
        rel = has_many(MockProduct, order_by="price desc")
        rel.rel_name = "products"
        
        sql = rel.ordering.to_sql()
        assert sql == "ORDER BY price DESC"
    
    def test_featured_products_first(self):
        """Featured products first, then by position."""
        rel = has_many(MockProduct, order_by=["featured desc", "position"])
        rel.rel_name = "products"
        
        columns = rel.ordering.get_columns()
        assert "featured DESC" in columns
        assert "position ASC" in columns
    
    def test_category_position(self):
        """Products ordered by category position."""
        rel = has_many(MockProduct, order_by="position")
        rel.rel_name = "category_products"
        
        sql = rel.ordering.to_sql()
        assert sql == "ORDER BY position ASC"


# =============================================================================
# Test: Task/Todo Ordering
# =============================================================================

class TestTaskOrdering:
    """Test task/todo ordering patterns."""
    
    def test_priority_queue(self):
        """Tasks ordered by priority."""
        rel = has_many(MockTask, order_by="priority desc")
        rel.rel_name = "tasks"
        
        sql = rel.ordering.to_sql()
        assert sql == "ORDER BY priority DESC"
    
    def test_due_date_with_nulls_last(self):
        """Tasks by due date, tasks without due date last."""
        rel = has_many(MockTask, order_by="due_date nulls last")
        rel.rel_name = "tasks"
        
        sql = rel.ordering.to_sql()
        assert "due_date ASC NULLS LAST" in sql
    
    def test_priority_then_due_date(self):
        """High priority first, then by due date."""
        rel = has_many(MockTask, order_by=[
            "priority desc",
            "due_date nulls last"
        ])
        rel.rel_name = "tasks"
        
        columns = rel.ordering.get_columns()
        assert columns[0] == "priority DESC"
        assert columns[1] == "due_date ASC NULLS LAST"
    
    def test_incomplete_first(self):
        """Incomplete tasks first, then by priority."""
        rel = has_many(MockTask, order_by=["completed", "priority desc"])
        rel.rel_name = "tasks"
        
        columns = rel.ordering.get_columns()
        assert columns[0] == "completed ASC"  # False (0) before True (1)
        assert columns[1] == "priority DESC"


class TestTaskSorting:
    """Test in-memory task sorting."""
    
    def test_sort_by_priority(self):
        """Sort tasks by priority."""
        tasks = [
            MockTask(title="Low", priority=1),
            MockTask(title="High", priority=3),
            MockTask(title="Medium", priority=2),
        ]
        
        specs = [OrderSpec("priority", "desc")]
        sorted_tasks = sort_items(tasks, specs)
        
        assert sorted_tasks[0].title == "High"
        assert sorted_tasks[-1].title == "Low"
    
    def test_sort_with_null_due_dates(self):
        """Sort with null due dates handled."""
        today = date.today()
        tasks = [
            MockTask(title="No Due", due_date=None),
            MockTask(title="Tomorrow", due_date=today + timedelta(days=1)),
            MockTask(title="Today", due_date=today),
        ]
        
        specs = [OrderSpec("due_date", "asc", "last")]
        sorted_tasks = sort_items(tasks, specs)
        
        assert sorted_tasks[-1].title == "No Due"


# =============================================================================
# Test: Comment Thread Ordering
# =============================================================================

class TestCommentOrdering:
    """Test comment thread ordering patterns."""
    
    def test_chronological(self):
        """Comments in chronological order."""
        rel = has_many(MockComment, order_by="created_at")
        rel.rel_name = "comments"
        
        sql = rel.ordering.to_sql()
        assert sql == "ORDER BY created_at ASC"
    
    def test_newest_first(self):
        """Comments newest first."""
        rel = has_many(MockComment, order_by="created_at desc")
        rel.rel_name = "comments"
        
        sql = rel.ordering.to_sql()
        assert sql == "ORDER BY created_at DESC"
    
    def test_most_upvoted(self):
        """Comments by upvotes."""
        rel = has_many(MockComment, order_by="votes desc")
        rel.rel_name = "top_comments"
        
        sql = rel.ordering.to_sql()
        assert sql == "ORDER BY votes DESC"
    
    def test_highlighted_first(self):
        """Highlighted comments first, then by votes."""
        rel = has_many(MockComment, order_by=["highlighted desc", "votes desc"])
        rel.rel_name = "comments"
        
        columns = rel.ordering.get_columns()
        assert columns[0] == "highlighted DESC"
        assert columns[1] == "votes DESC"


# =============================================================================
# Test: Social Media Feed Ordering
# =============================================================================

class TestFeedOrdering:
    """Test social media feed ordering patterns."""
    
    def test_reverse_chronological(self):
        """Feed in reverse chronological order."""
        rel = has_many(MockFeedItem, order_by="created_at desc")
        rel.rel_name = "feed_items"
        
        sql = rel.ordering.to_sql()
        assert sql == "ORDER BY created_at DESC"
    
    def test_engagement_based(self):
        """Feed by engagement score."""
        rel = has_many(MockFeedItem, order_by="engagement_score desc")
        rel.rel_name = "feed_items"
        
        sql = rel.ordering.to_sql()
        assert sql == "ORDER BY engagement_score DESC"
    
    def test_promoted_first(self):
        """Promoted items first, then by time."""
        rel = has_many(MockFeedItem, order_by=[
            "promoted desc",
            "created_at desc"
        ])
        rel.rel_name = "feed_items"
        
        columns = rel.ordering.get_columns()
        assert columns[0] == "promoted DESC"
        assert columns[1] == "created_at DESC"


# =============================================================================
# Test: Category/Navigation Ordering
# =============================================================================

class TestCategoryOrdering:
    """Test category/navigation ordering patterns."""
    
    def test_by_position(self):
        """Categories by position."""
        rel = has_many(MockCategory, order_by="position")
        rel.rel_name = "subcategories"
        
        sql = rel.ordering.to_sql()
        assert sql == "ORDER BY position ASC"
    
    def test_position_then_name(self):
        """Categories by position, then alphabetically."""
        rel = has_many(MockCategory, order_by=["position", "name"])
        rel.rel_name = "subcategories"
        
        columns = rel.ordering.get_columns()
        assert columns == ["position ASC", "name ASC"]
    
    def test_alphabetical(self):
        """Categories alphabetically."""
        rel = has_many(MockCategory, order_by="name")
        rel.rel_name = "subcategories"
        
        sql = rel.ordering.to_sql()
        assert sql == "ORDER BY name ASC"


# =============================================================================
# Test: Many-to-Many Ordering
# =============================================================================

class TestM2MOrdering:
    """Test many-to-many ordering patterns."""
    
    def test_tags_alphabetical(self):
        """Tags ordered alphabetically."""
        rel = many_to_many(MockCategory, order_by="name")
        rel.rel_name = "tags"
        
        sql = rel.ordering.to_sql()
        assert sql == "ORDER BY name ASC"
    
    def test_categories_by_position(self):
        """M2M categories by position."""
        rel = many_to_many(MockCategory, order_by="position")
        rel.rel_name = "categories"
        
        sql = rel.ordering.to_sql()
        assert sql == "ORDER BY position ASC"
    
    def test_related_products_by_rating(self):
        """Related products by rating."""
        rel = many_to_many(MockProduct, order_by="rating desc nulls last")
        rel.rel_name = "related_products"
        
        sql = rel.ordering.to_sql()
        assert "rating DESC NULLS LAST" in sql


# =============================================================================
# Test: Complex Multi-Sort Scenarios
# =============================================================================

class TestComplexSorting:
    """Test complex multi-column sorting scenarios."""
    
    def test_ecommerce_product_grid(self):
        """Complex product grid: in-stock first, featured, rating, price."""
        rel = has_many(MockProduct, order_by=[
            "in_stock desc",
            "featured desc",
            "rating desc nulls last",
            "price"
        ])
        rel.rel_name = "products"
        
        columns = rel.ordering.get_columns()
        assert len(columns) == 4
        assert "in_stock DESC" in columns[0]
    
    def test_project_tasks_board(self):
        """Project tasks: incomplete first, priority, due date, created."""
        rel = has_many(MockTask, order_by=[
            "completed",
            "priority desc",
            "due_date nulls last",
            "created_at"
        ])
        rel.rel_name = "tasks"
        
        columns = rel.ordering.get_columns()
        assert len(columns) == 4
    
    def test_content_feed_algorithm(self):
        """Content feed: promoted, engagement, recency."""
        rel = has_many(MockFeedItem, order_by=[
            "promoted desc",
            "engagement_score desc",
            "created_at desc"
        ])
        rel.rel_name = "feed"
        
        sql = rel.ordering.to_sql()
        assert "promoted DESC" in sql
        assert "engagement_score DESC" in sql
        assert "created_at DESC" in sql


# =============================================================================
# Test: Ordering with Table Aliases
# =============================================================================

class TestTableAliasOrdering:
    """Test ordering with table aliases for joins."""
    
    def test_single_column_with_alias(self):
        """Single column with table alias."""
        config = OrderingConfig.from_order_by("created_at desc")
        sql = config.to_sql(table_alias="p")
        
        assert sql == "ORDER BY p.created_at DESC"
    
    def test_multiple_columns_with_alias(self):
        """Multiple columns with table alias."""
        config = OrderingConfig.from_order_by(["pinned desc", "created_at desc"])
        sql = config.to_sql(table_alias="posts")
        
        assert "posts.pinned DESC" in sql
        assert "posts.created_at DESC" in sql
    
    def test_with_nulls_and_alias(self):
        """With NULLS and table alias."""
        config = OrderingConfig.from_order_by("due_date nulls last")
        sql = config.to_sql(table_alias="t")
        
        assert sql == "ORDER BY t.due_date ASC NULLS LAST"

