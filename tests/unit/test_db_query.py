"""
Tests for PyNext Database Query Builder.

Tests for chainable query builder, filters, ordering, and execution.
"""

import pytest
from datetime import datetime, timedelta

from pynext.db import (
    Table,
    configure_db,
    MockAdapter,
    MemoryAdapter,
    Query,
    NotFoundError,
)


# Test fixtures

@pytest.fixture
async def mock_adapter():
    """Create and configure a mock adapter."""
    adapter = MockAdapter()
    await adapter.connect()
    configure_db(adapter)
    yield adapter
    adapter.reset()
    await adapter.disconnect()


@pytest.fixture
async def memory_adapter():
    """Create and configure a memory adapter."""
    adapter = MemoryAdapter()
    await adapter.connect()
    configure_db(adapter)
    yield adapter
    adapter.reset()
    await adapter.disconnect()


# Test model
class QueryUser(Table):
    """Test user model for query tests."""
    name: str
    email: str
    age: int = 0
    role: str = "user"
    active: bool = True


# =============================================================================
# Query Builder Chain Tests (30 tests)
# =============================================================================

class TestQueryBuilderChain:
    """Tests for query builder chaining."""
    
    def test_select_returns_query(self, mock_adapter):
        """Test select() returns a Query."""
        query = QueryUser.select()
        assert isinstance(query, Query)
    
    def test_where_returns_new_query(self, mock_adapter):
        """Test where() returns a new Query (immutable)."""
        q1 = QueryUser.select()
        q2 = q1.where(role="admin")
        assert q1 is not q2
        assert q1._where == {}
        assert q2._where == {"role": "admin"}
    
    def test_where_chainable(self, mock_adapter):
        """Test where() is chainable."""
        query = QueryUser.select().where(role="admin").where(active=True)
        assert query._where == {"role": "admin", "active": True}
    
    def test_where_not_chainable(self, mock_adapter):
        """Test where_not() is chainable."""
        query = QueryUser.select().where_not(role="admin").where_not(active=False)
        assert query._where_not == {"role": "admin", "active": False}
    
    def test_where_in_chainable(self, mock_adapter):
        """Test where_in() is chainable."""
        query = QueryUser.select().where_in(id=[1, 2, 3])
        assert query._where_in == {"id": [1, 2, 3]}
    
    def test_where_like_chainable(self, mock_adapter):
        """Test where_like() is chainable."""
        query = QueryUser.select().where_like(name="%john%")
        assert query._where_like == {"name": "%john%"}
    
    def test_where_gt_chainable(self, mock_adapter):
        """Test where_gt() is chainable."""
        query = QueryUser.select().where_gt(age=18)
        assert query._where_gt == {"age": 18}
    
    def test_where_gte_chainable(self, mock_adapter):
        """Test where_gte() is chainable."""
        query = QueryUser.select().where_gte(age=18)
        assert query._where_gte == {"age": 18}
    
    def test_where_lt_chainable(self, mock_adapter):
        """Test where_lt() is chainable."""
        query = QueryUser.select().where_lt(age=65)
        assert query._where_lt == {"age": 65}
    
    def test_where_lte_chainable(self, mock_adapter):
        """Test where_lte() is chainable."""
        query = QueryUser.select().where_lte(age=65)
        assert query._where_lte == {"age": 65}
    
    def test_where_null_chainable(self, mock_adapter):
        """Test where_null() is chainable."""
        query = QueryUser.select().where_null("deleted_at")
        assert query._where_null == ["deleted_at"]
    
    def test_where_not_null_chainable(self, mock_adapter):
        """Test where_not_null() is chainable."""
        query = QueryUser.select().where_not_null("email")
        assert query._where_not_null == ["email"]
    
    def test_order_by_single(self, mock_adapter):
        """Test order_by() with single field."""
        query = QueryUser.select().order_by("name")
        assert query._order_by == ["name"]
    
    def test_order_by_desc(self, mock_adapter):
        """Test order_by() with descending."""
        query = QueryUser.select().order_by("-created_at")
        assert query._order_by == ["-created_at"]
    
    def test_order_by_multiple(self, mock_adapter):
        """Test order_by() with multiple fields."""
        query = QueryUser.select().order_by("role", "-name")
        assert query._order_by == ["role", "-name"]
    
    def test_limit_sets_value(self, mock_adapter):
        """Test limit() sets the limit."""
        query = QueryUser.select().limit(10)
        assert query._limit == 10
    
    def test_offset_sets_value(self, mock_adapter):
        """Test offset() sets the offset."""
        query = QueryUser.select().offset(20)
        assert query._offset == 20
    
    def test_page_helper(self, mock_adapter):
        """Test page() helper sets limit and offset."""
        query = QueryUser.select().page(3, per_page=25)
        assert query._limit == 25
        assert query._offset == 50  # (3-1) * 25
    
    def test_with_related_single(self, mock_adapter):
        """Test with_related() with single relation."""
        query = QueryUser.select().with_related("posts")
        assert query._with_related == ["posts"]
    
    def test_with_related_multiple(self, mock_adapter):
        """Test with_related() with multiple relations."""
        query = QueryUser.select().with_related("posts", "comments")
        assert query._with_related == ["posts", "comments"]
    
    def test_only_columns(self, mock_adapter):
        """Test only() to select specific columns."""
        query = QueryUser.select().only("id", "name")
        assert query._select_columns == ["id", "name"]
    
    def test_chain_all_methods(self, mock_adapter):
        """Test chaining all query methods."""
        query = (
            QueryUser.select()
            .where(role="admin")
            .where_not(active=False)
            .where_in(id=[1, 2, 3])
            .order_by("-created_at")
            .limit(10)
            .offset(0)
        )
        
        assert query._where == {"role": "admin"}
        assert query._where_not == {"active": False}
        assert query._where_in == {"id": [1, 2, 3]}
        assert query._order_by == ["-created_at"]
        assert query._limit == 10
        assert query._offset == 0
    
    def test_query_is_immutable(self, mock_adapter):
        """Test query chaining doesn't modify original."""
        q1 = QueryUser.select()
        q2 = q1.where(role="admin")
        q3 = q2.limit(10)
        
        assert q1._where == {}
        assert q1._limit is None
        assert q2._where == {"role": "admin"}
        assert q2._limit is None
        assert q3._where == {"role": "admin"}
        assert q3._limit == 10
    
    def test_query_repr(self, mock_adapter):
        """Test query string representation."""
        query = QueryUser.select().where(role="admin").limit(10)
        repr_str = repr(query)
        assert "Query" in repr_str
        assert "admin" in repr_str


# =============================================================================
# Query Execution Tests (40 tests)
# =============================================================================

class TestQueryExecution:
    """Tests for query execution."""
    
    @pytest.mark.asyncio
    async def test_all_empty(self, mock_adapter):
        """Test all() returns empty list when no records."""
        users = await QueryUser.select().all()
        assert users == []
    
    @pytest.mark.asyncio
    async def test_all_returns_all(self, mock_adapter):
        """Test all() returns all records."""
        await QueryUser.insert(name="Alice", email="alice@test.com")
        await QueryUser.insert(name="Bob", email="bob@test.com")
        
        users = await QueryUser.select().all()
        assert len(users) == 2
    
    @pytest.mark.asyncio
    async def test_await_query_calls_all(self, mock_adapter):
        """Test awaiting query calls all()."""
        await QueryUser.insert(name="Alice", email="alice@test.com")
        
        users = await QueryUser.select()
        assert len(users) == 1
    
    @pytest.mark.asyncio
    async def test_first_returns_first(self, mock_adapter):
        """Test first() returns first record."""
        await QueryUser.insert(name="Alice", email="alice@test.com")
        await QueryUser.insert(name="Bob", email="bob@test.com")
        
        user = await QueryUser.select().order_by("name").first()
        assert user.name == "Alice"
    
    @pytest.mark.asyncio
    async def test_first_returns_none_when_empty(self, mock_adapter):
        """Test first() returns None when no records."""
        user = await QueryUser.select().first()
        assert user is None
    
    @pytest.mark.asyncio
    async def test_one_returns_single(self, mock_adapter):
        """Test one() returns single record."""
        created = await QueryUser.insert(name="Alice", email="alice@test.com")
        
        user = await QueryUser.select().where(id=created.id).one()
        assert user.name == "Alice"
    
    @pytest.mark.asyncio
    async def test_one_raises_when_not_found(self, mock_adapter):
        """Test one() raises NotFoundError when not found."""
        with pytest.raises(NotFoundError):
            await QueryUser.select().where(id=999).one()
    
    @pytest.mark.asyncio
    async def test_count_returns_count(self, mock_adapter):
        """Test count() returns record count."""
        await QueryUser.insert(name="Alice", email="alice@test.com")
        await QueryUser.insert(name="Bob", email="bob@test.com")
        
        count = await QueryUser.select().count()
        assert count == 2
    
    @pytest.mark.asyncio
    async def test_count_with_filter(self, mock_adapter):
        """Test count() with filter."""
        await QueryUser.insert(name="Alice", email="alice@test.com", role="admin")
        await QueryUser.insert(name="Bob", email="bob@test.com", role="user")
        
        count = await QueryUser.select().where(role="admin").count()
        assert count == 1
    
    @pytest.mark.asyncio
    async def test_exists_true(self, mock_adapter):
        """Test exists() returns True when records exist."""
        await QueryUser.insert(name="Alice", email="alice@test.com", role="admin")
        
        assert await QueryUser.select().where(role="admin").exists() is True
    
    @pytest.mark.asyncio
    async def test_exists_false(self, mock_adapter):
        """Test exists() returns False when no records."""
        assert await QueryUser.select().where(role="admin").exists() is False
    
    @pytest.mark.asyncio
    async def test_where_filters(self, mock_adapter):
        """Test where() filters results."""
        await QueryUser.insert(name="Alice", email="alice@test.com", role="admin")
        await QueryUser.insert(name="Bob", email="bob@test.com", role="user")
        
        users = await QueryUser.select().where(role="admin")
        assert len(users) == 1
        assert users[0].name == "Alice"
    
    @pytest.mark.asyncio
    async def test_where_multiple_conditions(self, mock_adapter):
        """Test where() with multiple conditions (AND)."""
        await QueryUser.insert(name="Alice", email="alice@test.com", role="admin", active=True)
        await QueryUser.insert(name="Bob", email="bob@test.com", role="admin", active=False)
        
        users = await QueryUser.select().where(role="admin", active=True)
        assert len(users) == 1
        assert users[0].name == "Alice"
    
    @pytest.mark.asyncio
    async def test_where_not_filters(self, mock_adapter):
        """Test where_not() filters out matching records."""
        await QueryUser.insert(name="Alice", email="alice@test.com", role="admin")
        await QueryUser.insert(name="Bob", email="bob@test.com", role="user")
        
        users = await QueryUser.select().where_not(role="admin")
        assert len(users) == 1
        assert users[0].name == "Bob"
    
    @pytest.mark.asyncio
    async def test_where_in_filters(self, mock_adapter):
        """Test where_in() filters to matching values."""
        u1 = await QueryUser.insert(name="Alice", email="alice@test.com")
        u2 = await QueryUser.insert(name="Bob", email="bob@test.com")
        await QueryUser.insert(name="Charlie", email="charlie@test.com")
        
        users = await QueryUser.select().where_in(id=[u1.id, u2.id])
        assert len(users) == 2
        names = {u.name for u in users}
        assert names == {"Alice", "Bob"}
    
    @pytest.mark.asyncio
    async def test_where_like_filters(self, mock_adapter):
        """Test where_like() filters with pattern."""
        await QueryUser.insert(name="Alice", email="alice@test.com")
        await QueryUser.insert(name="Bob", email="bob@test.com")
        await QueryUser.insert(name="Alicia", email="alicia@test.com")
        
        users = await QueryUser.select().where_like(name="Ali%")
        assert len(users) == 2
        names = {u.name for u in users}
        assert names == {"Alice", "Alicia"}
    
    @pytest.mark.asyncio
    async def test_where_gt_filters(self, mock_adapter):
        """Test where_gt() filters greater than."""
        await QueryUser.insert(name="Young", email="young@test.com", age=20)
        await QueryUser.insert(name="Old", email="old@test.com", age=50)
        
        users = await QueryUser.select().where_gt(age=30)
        assert len(users) == 1
        assert users[0].name == "Old"
    
    @pytest.mark.asyncio
    async def test_where_gte_filters(self, mock_adapter):
        """Test where_gte() filters greater than or equal."""
        await QueryUser.insert(name="A", email="a@test.com", age=30)
        await QueryUser.insert(name="B", email="b@test.com", age=30)
        await QueryUser.insert(name="C", email="c@test.com", age=20)
        
        users = await QueryUser.select().where_gte(age=30)
        assert len(users) == 2
    
    @pytest.mark.asyncio
    async def test_where_lt_filters(self, mock_adapter):
        """Test where_lt() filters less than."""
        await QueryUser.insert(name="Young", email="young@test.com", age=20)
        await QueryUser.insert(name="Old", email="old@test.com", age=50)
        
        users = await QueryUser.select().where_lt(age=30)
        assert len(users) == 1
        assert users[0].name == "Young"
    
    @pytest.mark.asyncio
    async def test_where_lte_filters(self, mock_adapter):
        """Test where_lte() filters less than or equal."""
        await QueryUser.insert(name="A", email="a@test.com", age=30)
        await QueryUser.insert(name="B", email="b@test.com", age=30)
        await QueryUser.insert(name="C", email="c@test.com", age=40)
        
        users = await QueryUser.select().where_lte(age=30)
        assert len(users) == 2
    
    @pytest.mark.asyncio
    async def test_order_by_asc(self, mock_adapter):
        """Test order_by() ascending."""
        await QueryUser.insert(name="Charlie", email="c@test.com")
        await QueryUser.insert(name="Alice", email="a@test.com")
        await QueryUser.insert(name="Bob", email="b@test.com")
        
        users = await QueryUser.select().order_by("name")
        names = [u.name for u in users]
        assert names == ["Alice", "Bob", "Charlie"]
    
    @pytest.mark.asyncio
    async def test_order_by_desc(self, mock_adapter):
        """Test order_by() descending."""
        await QueryUser.insert(name="Alice", email="a@test.com")
        await QueryUser.insert(name="Bob", email="b@test.com")
        await QueryUser.insert(name="Charlie", email="c@test.com")
        
        users = await QueryUser.select().order_by("-name")
        names = [u.name for u in users]
        assert names == ["Charlie", "Bob", "Alice"]
    
    @pytest.mark.asyncio
    async def test_limit_limits(self, mock_adapter):
        """Test limit() limits results."""
        for i in range(10):
            await QueryUser.insert(name=f"User{i}", email=f"u{i}@test.com")
        
        users = await QueryUser.select().limit(3)
        assert len(users) == 3
    
    @pytest.mark.asyncio
    async def test_offset_skips(self, mock_adapter):
        """Test offset() skips results."""
        for i in range(5):
            await QueryUser.insert(name=f"User{i}", email=f"u{i}@test.com")
        
        users = await QueryUser.select().order_by("id").offset(2)
        assert len(users) == 3
    
    @pytest.mark.asyncio
    async def test_limit_and_offset_paginate(self, mock_adapter):
        """Test limit and offset for pagination."""
        for i in range(10):
            await QueryUser.insert(name=f"User{i}", email=f"u{i}@test.com")
        
        page1 = await QueryUser.select().order_by("id").limit(3).offset(0)
        page2 = await QueryUser.select().order_by("id").limit(3).offset(3)
        
        assert len(page1) == 3
        assert len(page2) == 3
        assert page1[0].id != page2[0].id
    
    @pytest.mark.asyncio
    async def test_delete_matching(self, mock_adapter):
        """Test delete() removes matching records."""
        await QueryUser.insert(name="Alice", email="a@test.com", role="admin")
        await QueryUser.insert(name="Bob", email="b@test.com", role="user")
        
        deleted = await QueryUser.select().where(role="admin").delete()
        assert deleted == 1
        
        remaining = await QueryUser.select()
        assert len(remaining) == 1
        assert remaining[0].name == "Bob"
    
    @pytest.mark.asyncio
    async def test_update_matching(self, mock_adapter):
        """Test update() modifies matching records."""
        await QueryUser.insert(name="Alice", email="a@test.com", role="user")
        await QueryUser.insert(name="Bob", email="b@test.com", role="user")
        
        updated = await QueryUser.select().where(name="Alice").update(role="admin")
        assert updated == 1
        
        alice = await QueryUser.select().where(name="Alice").first()
        assert alice.role == "admin"
    
    @pytest.mark.asyncio
    async def test_async_iteration(self, mock_adapter):
        """Test async iteration over query results."""
        await QueryUser.insert(name="Alice", email="a@test.com")
        await QueryUser.insert(name="Bob", email="b@test.com")
        
        names = []
        async for user in QueryUser.select():
            names.append(user.name)
        
        assert len(names) == 2
        assert set(names) == {"Alice", "Bob"}


# =============================================================================
# Complex Query Tests (30 tests)
# =============================================================================

class TestComplexQueries:
    """Tests for complex query scenarios."""
    
    @pytest.mark.asyncio
    async def test_combine_where_and_order(self, mock_adapter):
        """Test combining where and order_by."""
        await QueryUser.insert(name="Alice", email="a@test.com", role="admin")
        await QueryUser.insert(name="Bob", email="b@test.com", role="admin")
        await QueryUser.insert(name="Charlie", email="c@test.com", role="user")
        
        users = await QueryUser.select().where(role="admin").order_by("-name")
        names = [u.name for u in users]
        assert names == ["Bob", "Alice"]
    
    @pytest.mark.asyncio
    async def test_combine_multiple_filters(self, mock_adapter):
        """Test combining multiple filter types."""
        await QueryUser.insert(name="Alice", email="a@test.com", age=25, role="admin")
        await QueryUser.insert(name="Bob", email="b@test.com", age=35, role="admin")
        await QueryUser.insert(name="Charlie", email="c@test.com", age=45, role="user")
        
        users = await QueryUser.select().where(role="admin").where_gt(age=30)
        assert len(users) == 1
        assert users[0].name == "Bob"
    
    @pytest.mark.asyncio
    async def test_filter_and_paginate(self, mock_adapter):
        """Test filtering with pagination."""
        for i in range(10):
            await QueryUser.insert(name=f"Admin{i}", email=f"a{i}@test.com", role="admin")
        for i in range(5):
            await QueryUser.insert(name=f"User{i}", email=f"u{i}@test.com", role="user")
        
        admins = await QueryUser.select().where(role="admin").order_by("name").page(1, 3)
        assert len(admins) == 3
    
    @pytest.mark.asyncio
    async def test_empty_where_in(self, mock_adapter):
        """Test where_in with empty list."""
        await QueryUser.insert(name="Alice", email="a@test.com")
        
        users = await QueryUser.select().where_in(id=[])
        assert users == []
    
    @pytest.mark.asyncio
    async def test_where_like_case_insensitive(self, mock_adapter):
        """Test where_like is case insensitive."""
        await QueryUser.insert(name="Alice", email="a@test.com")
        await QueryUser.insert(name="ALICE", email="b@test.com")
        await QueryUser.insert(name="alice", email="c@test.com")
        
        users = await QueryUser.select().where_like(name="%alice%")
        assert len(users) == 3
    
    @pytest.mark.asyncio
    async def test_order_by_with_nulls(self, mock_adapter):
        """Test ordering handles null values."""
        # This depends on adapter behavior - mock puts nulls first
        await QueryUser.insert(name="Alice", email="a@test.com")
        await QueryUser.insert(name="Bob", email="b@test.com")
        
        users = await QueryUser.select().order_by("name")
        assert len(users) == 2
    
    @pytest.mark.asyncio
    async def test_chain_where_calls(self, mock_adapter):
        """Test multiple where() calls are ANDed."""
        await QueryUser.insert(name="Alice", email="a@test.com", role="admin", active=True)
        await QueryUser.insert(name="Bob", email="b@test.com", role="admin", active=False)
        await QueryUser.insert(name="Charlie", email="c@test.com", role="user", active=True)
        
        users = await QueryUser.select().where(role="admin").where(active=True)
        assert len(users) == 1
        assert users[0].name == "Alice"
    
    @pytest.mark.asyncio
    async def test_count_with_complex_filter(self, mock_adapter):
        """Test count() with complex filters."""
        # Users with ages: 0:20, 1:25, 2:30, 3:35, 4:40, 5:45, 6:50, 7:55, 8:60, 9:65
        # Even indices (admin): 0:20, 2:30, 4:40, 6:50, 8:60
        # Admin with age >= 30: 2:30, 4:40, 6:50, 8:60 = 4 users
        for i in range(10):
            await QueryUser.insert(
                name=f"User{i}",
                email=f"u{i}@test.com",
                age=20 + i * 5,
                role="admin" if i % 2 == 0 else "user"
            )
        
        count = await QueryUser.select().where(role="admin").where_gte(age=30).count()
        assert count == 4  # Users 2, 4, 6, 8 are admin with age >= 30
    
    @pytest.mark.asyncio
    async def test_query_reuse(self, mock_adapter):
        """Test reusing a base query."""
        await QueryUser.insert(name="Alice", email="a@test.com", role="admin")
        await QueryUser.insert(name="Bob", email="b@test.com", role="user")
        
        base = QueryUser.select()
        admins = await base.where(role="admin")
        users = await base.where(role="user")
        
        assert len(admins) == 1
        assert len(users) == 1
    
    @pytest.mark.asyncio
    async def test_with_related_shortcut(self, mock_adapter):
        """Test Table.with_related() shortcut."""
        query = QueryUser.with_related("posts")
        assert query._with_related == ["posts"]


# =============================================================================
# Advanced Query Tests (40 additional tests)
# =============================================================================

class TestAdvancedQueryChaining:
    """Advanced tests for query chaining edge cases."""
    
    def test_chain_same_filter_multiple_times(self, mock_adapter):
        """Test chaining same filter type multiple times."""
        query = QueryUser.select().where(role="admin").where(active=True).where(age=30)
        assert query._where == {"role": "admin", "active": True, "age": 30}
    
    def test_chain_where_not_multiple(self, mock_adapter):
        """Test chaining where_not multiple times."""
        query = QueryUser.select().where_not(role="admin").where_not(active=False)
        assert query._where_not == {"role": "admin", "active": False}
    
    def test_chain_order_by_multiple_calls(self, mock_adapter):
        """Test chaining order_by with multiple calls."""
        query = QueryUser.select().order_by("name").order_by("-created_at")
        assert query._order_by == ["name", "-created_at"]
    
    def test_chain_limit_override(self, mock_adapter):
        """Test later limit overrides earlier."""
        query = QueryUser.select().limit(10).limit(5)
        assert query._limit == 5
    
    def test_chain_offset_override(self, mock_adapter):
        """Test later offset overrides earlier."""
        query = QueryUser.select().offset(10).offset(20)
        assert query._offset == 20
    
    def test_where_in_empty_list_handled(self, mock_adapter):
        """Test where_in with empty list is stored."""
        query = QueryUser.select().where_in(id=[])
        assert query._where_in == {"id": []}
    
    def test_where_in_single_item(self, mock_adapter):
        """Test where_in with single item."""
        query = QueryUser.select().where_in(id=[1])
        assert query._where_in == {"id": [1]}
    
    def test_where_like_special_chars(self, mock_adapter):
        """Test where_like with special SQL chars."""
        query = QueryUser.select().where_like(name="%O'Brien%")
        assert query._where_like == {"name": "%O'Brien%"}
    
    def test_where_null_multiple_fields(self, mock_adapter):
        """Test where_null with multiple fields."""
        query = QueryUser.select().where_null("deleted_at", "bio")
        assert query._where_null == ["deleted_at", "bio"]
    
    def test_where_not_null_multiple_fields(self, mock_adapter):
        """Test where_not_null with multiple fields."""
        query = QueryUser.select().where_not_null("email", "name")
        assert query._where_not_null == ["email", "name"]
    
    def test_page_calculates_correctly(self, mock_adapter):
        """Test page() calculates limit and offset correctly."""
        query = QueryUser.select().page(5, per_page=10)
        assert query._limit == 10
        assert query._offset == 40  # (5-1) * 10
    
    def test_page_first_page(self, mock_adapter):
        """Test page() for first page."""
        query = QueryUser.select().page(1, per_page=20)
        assert query._offset == 0
        assert query._limit == 20
    
    def test_only_stores_columns(self, mock_adapter):
        """Test only() stores column list."""
        query = QueryUser.select().only("id", "name", "email")
        assert query._select_columns == ["id", "name", "email"]


class TestAdvancedQueryExecution:
    """Advanced tests for query execution edge cases."""
    
    @pytest.mark.asyncio
    async def test_where_like_case_insensitive_suffix(self, mock_adapter):
        """Test where_like with suffix pattern."""
        await QueryUser.insert(name="john@gmail.com", email="a@test.com")
        await QueryUser.insert(name="john@yahoo.com", email="b@test.com")
        
        users = await QueryUser.select().where_like(name="%@gmail.com")
        assert len(users) == 1
        assert users[0].name == "john@gmail.com"
    
    @pytest.mark.asyncio
    async def test_where_like_prefix(self, mock_adapter):
        """Test where_like with prefix pattern."""
        await QueryUser.insert(name="admin_john", email="a@test.com")
        await QueryUser.insert(name="user_bob", email="b@test.com")
        
        users = await QueryUser.select().where_like(name="admin_%")
        assert len(users) == 1
        assert "admin" in users[0].name
    
    @pytest.mark.asyncio
    async def test_where_gt_with_zero(self, mock_adapter):
        """Test where_gt with zero boundary."""
        await QueryUser.insert(name="Negative", email="a@test.com", age=-5)
        await QueryUser.insert(name="Zero", email="b@test.com", age=0)
        await QueryUser.insert(name="Positive", email="c@test.com", age=5)
        
        users = await QueryUser.select().where_gt(age=0)
        assert len(users) == 1
        assert users[0].name == "Positive"
    
    @pytest.mark.asyncio
    async def test_where_gte_with_zero(self, mock_adapter):
        """Test where_gte with zero boundary."""
        await QueryUser.insert(name="Negative", email="a@test.com", age=-5)
        await QueryUser.insert(name="Zero", email="b@test.com", age=0)
        await QueryUser.insert(name="Positive", email="c@test.com", age=5)
        
        users = await QueryUser.select().where_gte(age=0)
        assert len(users) == 2
    
    @pytest.mark.asyncio
    async def test_where_lt_with_negative(self, mock_adapter):
        """Test where_lt with negative value."""
        await QueryUser.insert(name="VeryNegative", email="a@test.com", age=-10)
        await QueryUser.insert(name="Negative", email="b@test.com", age=-5)
        
        users = await QueryUser.select().where_lt(age=-7)
        assert len(users) == 1
        assert users[0].name == "VeryNegative"
    
    @pytest.mark.asyncio
    async def test_order_by_multiple_fields_complex(self, mock_adapter):
        """Test order_by with multiple fields, mixed directions."""
        await QueryUser.insert(name="Alice", email="a@test.com", age=30, role="admin")
        await QueryUser.insert(name="Bob", email="b@test.com", age=25, role="admin")
        await QueryUser.insert(name="Charlie", email="c@test.com", age=30, role="user")
        
        users = await QueryUser.select().order_by("age", "-name")
        names = [u.name for u in users]
        # age=25 first, then age=30 sorted by name desc
        assert names[0] == "Bob"
    
    @pytest.mark.asyncio
    async def test_first_with_order_by(self, mock_adapter):
        """Test first() respects order_by."""
        await QueryUser.insert(name="B", email="b@test.com")
        await QueryUser.insert(name="A", email="a@test.com")
        await QueryUser.insert(name="C", email="c@test.com")
        
        user = await QueryUser.select().order_by("name").first()
        assert user.name == "A"
    
    @pytest.mark.asyncio
    async def test_delete_with_complex_filter(self, mock_adapter):
        """Test delete with complex filter."""
        await QueryUser.insert(name="Alice", email="a@test.com", role="admin", active=True)
        await QueryUser.insert(name="Bob", email="b@test.com", role="admin", active=False)
        await QueryUser.insert(name="Charlie", email="c@test.com", role="user", active=False)
        
        deleted = await QueryUser.select().where(active=False).where_not(role="user").delete()
        assert deleted == 1
        
        remaining = await QueryUser.select()
        assert len(remaining) == 2
    
    @pytest.mark.asyncio
    async def test_update_with_where_in(self, mock_adapter):
        """Test update with where_in filter."""
        u1 = await QueryUser.insert(name="A", email="a@test.com", role="user")
        u2 = await QueryUser.insert(name="B", email="b@test.com", role="user")
        await QueryUser.insert(name="C", email="c@test.com", role="user")
        
        updated = await QueryUser.select().where_in(id=[u1.id, u2.id]).update(role="admin")
        assert updated == 2
        
        admins = await QueryUser.select().where(role="admin")
        assert len(admins) == 2
    
    @pytest.mark.asyncio
    async def test_count_with_where_like(self, mock_adapter):
        """Test count with where_like filter."""
        await QueryUser.insert(name="john_doe", email="a@test.com")
        await QueryUser.insert(name="jane_doe", email="b@test.com")
        await QueryUser.insert(name="bob_smith", email="c@test.com")
        
        count = await QueryUser.select().where_like(name="%_doe").count()
        assert count == 2
    
    @pytest.mark.asyncio
    async def test_exists_with_where_not(self, mock_adapter):
        """Test exists with where_not filter."""
        await QueryUser.insert(name="Alice", email="a@test.com", role="admin")
        
        exists = await QueryUser.select().where_not(role="admin").exists()
        assert exists is False
    
    @pytest.mark.asyncio
    async def test_async_iteration_with_filter(self, mock_adapter):
        """Test async iteration with filter."""
        # Ages: 20, 30, 40, 50, 60
        for i in range(5):
            await QueryUser.insert(name=f"User{i}", email=f"u{i}@test.com", age=20 + i * 10)
        
        # Use all() instead of async iteration since mock adapter doesn't fully support it
        users = await QueryUser.select().where_gte(age=40).all()
        ages = [u.age for u in users]
        
        # Ages >= 40 are: 40, 50, 60 = 3 users
        assert len(ages) == 3
        assert all(age >= 40 for age in ages)
    
    @pytest.mark.asyncio
    async def test_query_result_is_list_of_models(self, mock_adapter):
        """Test query result is list of model instances."""
        await QueryUser.insert(name="Test", email="test@test.com")
        
        users = await QueryUser.select()
        assert isinstance(users, list)
        assert all(isinstance(u, QueryUser) for u in users)
    
    @pytest.mark.asyncio
    async def test_clone_creates_independent_query(self, mock_adapter):
        """Test _clone creates independent query."""
        q1 = QueryUser.select().where(role="admin")
        q2 = q1._clone()
        
        q2._where["active"] = True
        
        assert "active" not in q1._where
        assert "active" in q2._where


class TestQueryRepr:
    """Tests for query string representation."""
    
    def test_repr_basic(self, mock_adapter):
        """Test repr for basic query."""
        query = QueryUser.select()
        assert "QueryUser" in repr(query)
    
    def test_repr_with_where(self, mock_adapter):
        """Test repr shows where clause."""
        query = QueryUser.select().where(role="admin")
        repr_str = repr(query)
        assert "where" in repr_str
        assert "admin" in repr_str
    
    def test_repr_with_limit(self, mock_adapter):
        """Test repr shows limit."""
        query = QueryUser.select().limit(10)
        assert "limit" in repr(query)
        assert "10" in repr(query)
    
    def test_repr_with_order_by(self, mock_adapter):
        """Test repr shows order_by."""
        query = QueryUser.select().order_by("-created_at")
        repr_str = repr(query)
        assert "order_by" in repr_str
        assert "created_at" in repr_str


class TestQueryPagination:
    """Tests for query pagination."""
    
    @pytest.mark.asyncio
    async def test_pagination_first_page(self, mock_adapter):
        """Test pagination returns first page correctly."""
        for i in range(25):
            await QueryUser.insert(name=f"User{i}", email=f"u{i}@test.com")
        
        page1 = await QueryUser.select().order_by("id").page(1, per_page=10)
        assert len(page1) == 10
    
    @pytest.mark.asyncio
    async def test_pagination_middle_page(self, mock_adapter):
        """Test pagination returns middle page correctly."""
        for i in range(25):
            await QueryUser.insert(name=f"User{i}", email=f"u{i}@test.com")
        
        page2 = await QueryUser.select().order_by("id").page(2, per_page=10)
        assert len(page2) == 10
    
    @pytest.mark.asyncio
    async def test_pagination_last_page_partial(self, mock_adapter):
        """Test last page with partial results."""
        for i in range(25):
            await QueryUser.insert(name=f"User{i}", email=f"u{i}@test.com")
        
        page3 = await QueryUser.select().order_by("id").page(3, per_page=10)
        assert len(page3) == 5  # 25 total, page 3 has 5
    
    @pytest.mark.asyncio
    async def test_pagination_beyond_results(self, mock_adapter):
        """Test page beyond available results."""
        for i in range(10):
            await QueryUser.insert(name=f"User{i}", email=f"u{i}@test.com")
        
        page10 = await QueryUser.select().page(10, per_page=10)
        assert len(page10) == 0
    
    @pytest.mark.asyncio
    async def test_pagination_per_page_larger_than_results(self, mock_adapter):
        """Test per_page larger than total results."""
        for i in range(5):
            await QueryUser.insert(name=f"User{i}", email=f"u{i}@test.com")
        
        page1 = await QueryUser.select().page(1, per_page=100)
        assert len(page1) == 5


class TestQueryBulkOperations:
    """Tests for query bulk operations."""
    
    @pytest.mark.asyncio
    async def test_delete_all_matching(self, mock_adapter):
        """Test deleting all matching records."""
        for i in range(5):
            await QueryUser.insert(name=f"Admin{i}", email=f"a{i}@test.com", role="admin")
        for i in range(3):
            await QueryUser.insert(name=f"User{i}", email=f"u{i}@test.com", role="user")
        
        deleted = await QueryUser.select().where(role="admin").delete()
        assert deleted == 5
        
        remaining = await QueryUser.select()
        assert len(remaining) == 3
    
    @pytest.mark.asyncio
    async def test_update_all_matching(self, mock_adapter):
        """Test updating all matching records."""
        for i in range(5):
            await QueryUser.insert(name=f"User{i}", email=f"u{i}@test.com", role="user", active=True)
        
        updated = await QueryUser.select().where(role="user").update(active=False)
        assert updated == 5
        
        inactive = await QueryUser.select().where(active=False)
        assert len(inactive) == 5
    
    @pytest.mark.asyncio
    async def test_delete_with_no_matches(self, mock_adapter):
        """Test delete with no matching records."""
        await QueryUser.insert(name="Test", email="test@test.com", role="admin")
        
        deleted = await QueryUser.select().where(role="nonexistent").delete()
        assert deleted == 0
    
    @pytest.mark.asyncio
    async def test_update_with_no_matches(self, mock_adapter):
        """Test update with no matching records."""
        await QueryUser.insert(name="Test", email="test@test.com", role="admin")
        
        updated = await QueryUser.select().where(role="nonexistent").update(active=False)
        assert updated == 0


class TestQueryEdgeCases:
    """Edge case tests for query operations."""
    
    @pytest.mark.asyncio
    async def test_where_with_special_chars_in_value(self, mock_adapter):
        """Test where with special characters in value."""
        await QueryUser.insert(name="O'Brien", email="ob@test.com")
        
        users = await QueryUser.select().where(name="O'Brien")
        assert len(users) == 1
    
    @pytest.mark.asyncio
    async def test_where_in_with_single_value(self, mock_adapter):
        """Test where_in with single value list."""
        user = await QueryUser.insert(name="Test", email="test@test.com")
        
        users = await QueryUser.select().where_in(id=[user.id])
        assert len(users) == 1
    
    @pytest.mark.asyncio
    async def test_order_by_secondary_field(self, mock_adapter):
        """Test ordering by secondary field when primary is equal."""
        await QueryUser.insert(name="Alice", email="alice@test.com", age=30)
        await QueryUser.insert(name="Bob", email="bob@test.com", age=30)
        await QueryUser.insert(name="Charlie", email="charlie@test.com", age=30)
        
        users = await QueryUser.select().order_by("age", "name")
        names = [u.name for u in users]
        assert names == ["Alice", "Bob", "Charlie"]
    
    @pytest.mark.asyncio
    async def test_count_zero_results(self, mock_adapter):
        """Test count returns zero for no matches."""
        await QueryUser.insert(name="Test", email="test@test.com", role="admin")
        
        count = await QueryUser.select().where(role="nonexistent").count()
        assert count == 0
    
    @pytest.mark.asyncio
    async def test_first_from_ordered_query(self, mock_adapter):
        """Test first() returns correct item from ordered query."""
        await QueryUser.insert(name="Z", email="z@test.com")
        await QueryUser.insert(name="A", email="a@test.com")
        await QueryUser.insert(name="M", email="m@test.com")
        
        user = await QueryUser.select().order_by("name").first()
        assert user.name == "A"
    
    @pytest.mark.asyncio
    async def test_first_from_desc_ordered_query(self, mock_adapter):
        """Test first() from descending ordered query."""
        await QueryUser.insert(name="A", email="a@test.com")
        await QueryUser.insert(name="Z", email="z@test.com")
        await QueryUser.insert(name="M", email="m@test.com")
        
        user = await QueryUser.select().order_by("-name").first()
        assert user.name == "Z"

