"""
Tests for PyNext Database Type-Safe SQL Builder.

Comprehensive tests for sql.select(), sql.insert(), sql.update(), sql.delete().
"""

import pytest
from datetime import datetime

from pynext.db import (
    Table,
    configure_db,
    MemoryAdapter,
    sql,
    SQLBuilder,
    SelectBuilder,
    InsertBuilder,
    UpdateBuilder,
    DeleteBuilder,
    JoinType,
    OrderDirection,
)


# =============================================================================
# Test Models
# =============================================================================

class BuilderUser(Table):
    """Test user model for builder tests."""
    name: str
    email: str
    age: int = 0
    role: str = "user"
    active: bool = True


class BuilderPost(Table):
    """Test post model for builder tests."""
    title: str
    content: str = ""
    author_id: int = 0
    published: bool = False


class BuilderComment(Table):
    """Test comment model for builder tests."""
    content: str
    post_id: int = 0
    user_id: int = 0


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
async def memory_adapter():
    """Create and configure a memory adapter."""
    adapter = MemoryAdapter()
    await adapter.connect()
    configure_db(adapter)
    yield adapter
    adapter.reset()
    await adapter.disconnect()


@pytest.fixture
async def populated_db(memory_adapter):
    """Create test data."""
    users = await BuilderUser.insert_many([
        {"name": "Alice", "email": "alice@example.com", "age": 25, "role": "admin"},
        {"name": "Bob", "email": "bob@example.com", "age": 30, "role": "user"},
        {"name": "Charlie", "email": "charlie@example.com", "age": 35, "role": "user"},
    ])
    
    posts = await BuilderPost.insert_many([
        {"title": "First Post", "author_id": users[0].id, "published": True},
        {"title": "Second Post", "author_id": users[0].id, "published": False},
        {"title": "Third Post", "author_id": users[1].id, "published": True},
    ])
    
    return {"users": users, "posts": posts}


# =============================================================================
# SQLBuilder Instance Tests (5 tests)
# =============================================================================

class TestSQLBuilderInstance:
    """Tests for SQLBuilder instance."""
    
    def test_sql_is_builder(self):
        """Test sql is SQLBuilder instance."""
        assert isinstance(sql, SQLBuilder)
    
    def test_select_returns_select_builder(self):
        """Test select() returns SelectBuilder."""
        builder = sql.select("*")
        assert isinstance(builder, SelectBuilder)
    
    def test_insert_returns_insert_builder(self):
        """Test insert() returns InsertBuilder."""
        builder = sql.insert("users")
        assert isinstance(builder, InsertBuilder)
    
    def test_update_returns_update_builder(self):
        """Test update() returns UpdateBuilder."""
        builder = sql.update("users")
        assert isinstance(builder, UpdateBuilder)
    
    def test_delete_returns_delete_builder(self):
        """Test delete() returns DeleteBuilder."""
        builder = sql.delete("users")
        assert isinstance(builder, DeleteBuilder)


# =============================================================================
# SelectBuilder Tests (25 tests)
# =============================================================================

class TestSelectBuilder:
    """Tests for SelectBuilder."""
    
    def test_select_all(self):
        """Test SELECT *."""
        query, params = sql.select("*").from_("users").build()
        
        assert "SELECT *" in query
        assert "FROM users" in query
    
    def test_select_specific_columns(self):
        """Test SELECT with specific columns."""
        query, params = sql.select("id", "name", "email").from_("users").build()
        
        assert "id, name, email" in query
    
    def test_select_distinct(self):
        """Test SELECT DISTINCT."""
        query, params = sql.select("role").from_("users").distinct().build()
        
        assert "SELECT DISTINCT role" in query
    
    def test_where_basic(self):
        """Test WHERE clause."""
        query, params = sql.select("*").from_("users").where("role", "=", "admin").build()
        
        assert "WHERE role = $1" in query
        assert params == ("admin",)
    
    def test_where_multiple(self):
        """Test multiple WHERE conditions."""
        query, params = (
            sql.select("*")
            .from_("users")
            .where("role", "=", "admin")
            .where("active", "=", True)
            .build()
        )
        
        assert "WHERE role = $1 AND active = $2" in query
        assert params == ("admin", True)
    
    def test_where_in(self):
        """Test WHERE IN."""
        query, params = sql.select("*").from_("users").where_in("id", [1, 2, 3]).build()
        
        assert "WHERE id IN ($1, $2, $3)" in query
        assert params == (1, 2, 3)
    
    def test_where_not_in(self):
        """Test WHERE NOT IN."""
        query, params = sql.select("*").from_("users").where_not_in("role", ["banned"]).build()
        
        assert "NOT IN" in query
    
    def test_where_null(self):
        """Test WHERE IS NULL."""
        query, params = sql.select("*").from_("users").where_null("deleted_at").build()
        
        assert "WHERE deleted_at IS NULL" in query
    
    def test_where_not_null(self):
        """Test WHERE IS NOT NULL."""
        query, params = sql.select("*").from_("users").where_not_null("email").build()
        
        assert "WHERE email IS NOT NULL" in query
    
    def test_where_between(self):
        """Test WHERE BETWEEN."""
        query, params = sql.select("*").from_("users").where_between("age", 18, 65).build()
        
        assert "BETWEEN $1 AND $2" in query
        assert params == (18, 65)
    
    def test_order_by_asc(self):
        """Test ORDER BY ASC."""
        query, params = sql.select("*").from_("users").order_by("name", "ASC").build()
        
        assert "ORDER BY name ASC" in query
    
    def test_order_by_desc(self):
        """Test ORDER BY DESC."""
        query, params = sql.select("*").from_("users").order_by("created_at", "DESC").build()
        
        assert "ORDER BY created_at DESC" in query
    
    def test_order_by_enum(self):
        """Test ORDER BY with enum."""
        query, params = (
            sql.select("*")
            .from_("users")
            .order_by("name", OrderDirection.DESC)
            .build()
        )
        
        assert "ORDER BY name DESC" in query
    
    def test_limit(self):
        """Test LIMIT."""
        query, params = sql.select("*").from_("users").limit(10).build()
        
        assert "LIMIT 10" in query
    
    def test_offset(self):
        """Test OFFSET."""
        query, params = sql.select("*").from_("users").offset(20).build()
        
        assert "OFFSET 20" in query
    
    def test_page(self):
        """Test page() pagination."""
        query, params = sql.select("*").from_("users").page(3, 20).build()
        
        assert "LIMIT 20" in query
        assert "OFFSET 40" in query
    
    def test_join_inner(self):
        """Test INNER JOIN."""
        query, params = (
            sql.select("*")
            .from_("posts")
            .join("users", "posts.author_id", "=", "users.id")
            .build()
        )
        
        assert "INNER JOIN users ON posts.author_id = users.id" in query
    
    def test_join_left(self):
        """Test LEFT JOIN."""
        query, params = (
            sql.select("*")
            .from_("posts")
            .left_join("users", "posts.author_id", "=", "users.id")
            .build()
        )
        
        assert "LEFT JOIN users" in query
    
    def test_join_right(self):
        """Test RIGHT JOIN."""
        query, params = (
            sql.select("*")
            .from_("posts")
            .right_join("users", "posts.author_id", "=", "users.id")
            .build()
        )
        
        assert "RIGHT JOIN users" in query
    
    def test_join_type_enum(self):
        """Test JOIN with JoinType enum."""
        query, params = (
            sql.select("*")
            .from_("posts")
            .join("users", "posts.author_id", "=", "users.id", JoinType.LEFT)
            .build()
        )
        
        assert "LEFT JOIN users" in query
    
    def test_group_by(self):
        """Test GROUP BY."""
        query, params = (
            sql.select("role", "COUNT(*)")
            .from_("users")
            .group_by("role")
            .build()
        )
        
        assert "GROUP BY role" in query
    
    def test_having(self):
        """Test HAVING."""
        query, params = (
            sql.select("role", "COUNT(*)")
            .from_("users")
            .group_by("role")
            .having("COUNT(*)", ">", 5)
            .build()
        )
        
        assert "HAVING COUNT(*) > $1" in query
        assert params == (5,)
    
    def test_complex_query(self):
        """Test complex query with all features."""
        query, params = (
            sql.select("users.name", "posts.title")
            .from_("users")
            .join("posts", "users.id", "=", "posts.author_id")
            .where("users.role", "=", "admin")
            .where("posts.published", "=", True)
            .order_by("posts.created_at", "DESC")
            .limit(10)
            .build()
        )
        
        assert "SELECT users.name, posts.title" in query
        assert "INNER JOIN posts" in query
        assert "WHERE" in query
        assert "ORDER BY" in query
        assert "LIMIT 10" in query
    
    def test_no_table_raises(self):
        """Test build() without from_() raises."""
        with pytest.raises(ValueError):
            sql.select("*").build()
    
    @pytest.mark.asyncio
    async def test_execute(self, memory_adapter, populated_db):
        """Test execute() returns results."""
        rows = await (
            sql.select("*")
            .from_("builderusers")
            .where("role", "=", "admin")
            .execute()
        )
        
        assert len(rows) == 1
        assert rows[0]["name"] == "Alice"


# =============================================================================
# InsertBuilder Tests (15 tests)
# =============================================================================

class TestInsertBuilder:
    """Tests for InsertBuilder."""
    
    def test_insert_basic(self):
        """Test basic INSERT."""
        query, params = (
            sql.insert("users")
            .values(name="John", email="john@example.com")
            .build()
        )
        
        assert "INSERT INTO users" in query
        assert "VALUES" in query
    
    def test_insert_values(self):
        """Test INSERT values."""
        query, params = (
            sql.insert("users")
            .values(name="John", email="john@example.com", age=25)
            .build()
        )
        
        assert params == ("John", "john@example.com", 25)
    
    def test_insert_returning(self):
        """Test INSERT RETURNING."""
        query, params = (
            sql.insert("users")
            .values(name="John")
            .returning("*")
            .build()
        )
        
        assert "RETURNING *" in query
    
    def test_insert_returning_specific(self):
        """Test INSERT RETURNING specific columns."""
        query, params = (
            sql.insert("users")
            .values(name="John")
            .returning("id")
            .build()
        )
        
        assert "RETURNING id" in query
    
    def test_insert_on_conflict_do_nothing(self):
        """Test INSERT ON CONFLICT DO NOTHING."""
        query, params = (
            sql.insert("users")
            .values(email="john@example.com")
            .on_conflict_do_nothing("email")
            .build()
        )
        
        assert "ON CONFLICT (email) DO NOTHING" in query
    
    def test_insert_on_conflict_do_update(self):
        """Test INSERT ON CONFLICT DO UPDATE."""
        query, params = (
            sql.insert("users")
            .values(email="john@example.com", name="John")
            .on_conflict_do_update(["email"], {"name": "John Updated"})
            .build()
        )
        
        assert "ON CONFLICT (email) DO UPDATE SET" in query
    
    def test_insert_no_values_raises(self):
        """Test build() without values() raises."""
        with pytest.raises(ValueError):
            sql.insert("users").build()
    
    def test_insert_multiple_values(self):
        """Test INSERT with multiple values."""
        query, params = (
            sql.insert("users")
            .values(name="John", email="john@example.com", age=25, role="user", active=True)
            .build()
        )
        
        assert len(params) == 5
    
    def test_insert_chained_values(self):
        """Test chained values() calls merge."""
        query, params = (
            sql.insert("users")
            .values(name="John")
            .values(email="john@example.com")
            .build()
        )
        
        assert "name" in query
        assert "email" in query
    
    @pytest.mark.asyncio
    async def test_insert_execute(self, memory_adapter):
        """Test INSERT execute()."""
        await BuilderUser.create_table()
        
        # Note: SQLite doesn't support RETURNING in all versions
        # We'll execute the insert and verify by querying
        await (
            sql.insert("builderusers")
            .values(name="Test", email="test@example.com", age=25, role="user", active=1)
            .execute()
        )
        
        # Verify insert worked
        rows = await sql.select("*").from_("builderusers").execute()
        assert len(rows) == 1
        assert rows[0]["name"] == "Test"
    
    def test_insert_placeholders(self):
        """Test INSERT uses $1, $2 placeholders."""
        query, params = (
            sql.insert("users")
            .values(name="John", email="john@example.com")
            .build()
        )
        
        assert "$1" in query
        assert "$2" in query
    
    def test_insert_with_null(self):
        """Test INSERT with None value."""
        query, params = (
            sql.insert("users")
            .values(name="John", website=None)
            .build()
        )
        
        assert None in params
    
    def test_insert_with_integer(self):
        """Test INSERT with integer value."""
        query, params = (
            sql.insert("users")
            .values(name="John", age=25)
            .build()
        )
        
        assert 25 in params
    
    def test_insert_with_boolean(self):
        """Test INSERT with boolean value."""
        query, params = (
            sql.insert("users")
            .values(name="John", active=True)
            .build()
        )
        
        assert True in params
    
    def test_insert_with_float(self):
        """Test INSERT with float value."""
        query, params = (
            sql.insert("products")
            .values(name="Widget", price=19.99)
            .build()
        )
        
        assert 19.99 in params


# =============================================================================
# UpdateBuilder Tests (10 tests)
# =============================================================================

class TestUpdateBuilder:
    """Tests for UpdateBuilder."""
    
    def test_update_basic(self):
        """Test basic UPDATE."""
        query, params = (
            sql.update("users")
            .set(active=True)
            .where("role", "=", "user")
            .build()
        )
        
        assert "UPDATE users SET active = $1" in query
        assert "WHERE role = $2" in query
    
    def test_update_multiple_set(self):
        """Test UPDATE with multiple SET."""
        query, params = (
            sql.update("users")
            .set(role="admin", active=True)
            .where("id", "=", 1)
            .build()
        )
        
        assert "role = $1" in query or "active = $1" in query
    
    def test_update_where_in(self):
        """Test UPDATE with WHERE IN."""
        query, params = (
            sql.update("users")
            .set(active=False)
            .where_in("id", [1, 2, 3])
            .build()
        )
        
        assert "IN ($" in query
    
    def test_update_returning(self):
        """Test UPDATE RETURNING."""
        query, params = (
            sql.update("users")
            .set(active=True)
            .where("id", "=", 1)
            .returning("*")
            .build()
        )
        
        assert "RETURNING *" in query
    
    def test_update_no_set_raises(self):
        """Test build() without set() raises."""
        with pytest.raises(ValueError):
            sql.update("users").where("id", "=", 1).build()
    
    def test_update_without_where(self):
        """Test UPDATE without WHERE (updates all)."""
        query, params = (
            sql.update("users")
            .set(role="user")
            .build()
        )
        
        assert "WHERE" not in query
    
    def test_update_chained_set(self):
        """Test chained set() calls merge."""
        query, params = (
            sql.update("users")
            .set(name="John")
            .set(email="john@example.com")
            .where("id", "=", 1)
            .build()
        )
        
        assert "name" in query
        assert "email" in query
    
    @pytest.mark.asyncio
    async def test_update_execute(self, memory_adapter, populated_db):
        """Test UPDATE execute()."""
        await (
            sql.update("builderusers")
            .set(role="superadmin")
            .where("name", "=", "Alice")
            .execute()
        )
        
        user = await BuilderUser.get_by(name="Alice")
        assert user.role == "superadmin"
    
    def test_update_placeholders_order(self):
        """Test UPDATE placeholder ordering."""
        query, params = (
            sql.update("users")
            .set(name="New")
            .where("id", "=", 1)
            .build()
        )
        
        # SET comes first, WHERE second
        assert params[0] == "New"
        assert params[1] == 1
    
    def test_update_multiple_where(self):
        """Test UPDATE with multiple WHERE."""
        query, params = (
            sql.update("users")
            .set(active=False)
            .where("role", "=", "user")
            .where("age", "<", 18)
            .build()
        )
        
        assert "AND" in query


# =============================================================================
# DeleteBuilder Tests (10 tests)
# =============================================================================

class TestDeleteBuilder:
    """Tests for DeleteBuilder."""
    
    def test_delete_basic(self):
        """Test basic DELETE."""
        query, params = (
            sql.delete("users")
            .where("active", "=", False)
            .build()
        )
        
        assert "DELETE FROM users" in query
        assert "WHERE active = $1" in query
    
    def test_delete_where_in(self):
        """Test DELETE with WHERE IN."""
        query, params = (
            sql.delete("users")
            .where_in("id", [1, 2, 3])
            .build()
        )
        
        assert "IN ($1, $2, $3)" in query
    
    def test_delete_returning(self):
        """Test DELETE RETURNING."""
        query, params = (
            sql.delete("users")
            .where("id", "=", 1)
            .returning("*")
            .build()
        )
        
        assert "RETURNING *" in query
    
    def test_delete_without_where(self):
        """Test DELETE without WHERE (deletes all)."""
        query, params = sql.delete("users").build()
        
        assert "DELETE FROM users" in query
        assert "WHERE" not in query
    
    def test_delete_multiple_where(self):
        """Test DELETE with multiple WHERE."""
        query, params = (
            sql.delete("users")
            .where("role", "=", "user")
            .where("active", "=", False)
            .build()
        )
        
        assert "AND" in query
    
    @pytest.mark.asyncio
    async def test_delete_execute(self, memory_adapter, populated_db):
        """Test DELETE execute()."""
        initial_count = await BuilderUser.count()
        
        await (
            sql.delete("builderusers")
            .where("name", "=", "Charlie")
            .execute()
        )
        
        final_count = await BuilderUser.count()
        assert final_count == initial_count - 1
    
    def test_delete_by_id(self):
        """Test DELETE by ID."""
        query, params = (
            sql.delete("users")
            .where("id", "=", 123)
            .build()
        )
        
        assert params == (123,)
    
    def test_delete_by_string(self):
        """Test DELETE by string field."""
        query, params = (
            sql.delete("users")
            .where("email", "=", "test@example.com")
            .build()
        )
        
        assert "test@example.com" in params
    
    def test_delete_not_equals(self):
        """Test DELETE with != operator."""
        query, params = (
            sql.delete("users")
            .where("role", "!=", "admin")
            .build()
        )
        
        assert "!=" in query or "<>" in query
    
    def test_delete_greater_than(self):
        """Test DELETE with > operator."""
        query, params = (
            sql.delete("users")
            .where("age", ">", 100)
            .build()
        )
        
        assert ">" in query


# =============================================================================
# Integration Tests (10 tests)
# =============================================================================

class TestBuilderIntegration:
    """Integration tests for SQL builder."""
    
    @pytest.mark.asyncio
    async def test_select_execute_returns_list(self, memory_adapter, populated_db):
        """Test SELECT execute returns list."""
        rows = await sql.select("*").from_("builderusers").execute()
        
        assert isinstance(rows, list)
        assert len(rows) == 3
    
    @pytest.mark.asyncio
    async def test_select_execute_one(self, memory_adapter, populated_db):
        """Test SELECT execute_one returns single row."""
        row = await (
            sql.select("*")
            .from_("builderusers")
            .where("name", "=", "Alice")
            .execute_one()
        )
        
        assert row is not None
        assert row["name"] == "Alice"
    
    @pytest.mark.asyncio
    async def test_select_execute_one_none(self, memory_adapter, populated_db):
        """Test SELECT execute_one returns None when no match."""
        row = await (
            sql.select("*")
            .from_("builderusers")
            .where("name", "=", "Nonexistent")
            .execute_one()
        )
        
        assert row is None
    
    @pytest.mark.asyncio
    async def test_builder_with_orm(self, memory_adapter, populated_db):
        """Test builder works alongside ORM."""
        # Use ORM
        await BuilderUser.insert(name="ORM User", email="orm@example.com")
        
        # Use builder
        rows = await sql.select("*").from_("builderusers").execute()
        
        assert len(rows) == 4
    
    @pytest.mark.asyncio
    async def test_complex_join(self, memory_adapter, populated_db):
        """Test complex join query."""
        rows = await (
            sql.select("builderusers.name", "builderposts.title")
            .from_("builderposts")
            .join("builderusers", "builderposts.author_id", "=", "builderusers.id")
            .where("builderposts.published", "=", 1)
            .execute()
        )
        
        assert len(rows) == 2
    
    @pytest.mark.asyncio
    async def test_aggregation(self, memory_adapter, populated_db):
        """Test aggregation query."""
        rows = await (
            sql.select("role", "COUNT(*) as cnt")
            .from_("builderusers")
            .group_by("role")
            .execute()
        )
        
        assert len(rows) >= 1
    
    @pytest.mark.asyncio
    async def test_subquery_style(self, memory_adapter, populated_db):
        """Test subquery-style filter."""
        # Get users who have posts
        user_ids = [1, 2]  # Alice and Bob have posts
        
        rows = await (
            sql.select("*")
            .from_("builderusers")
            .where_in("id", user_ids)
            .execute()
        )
        
        assert len(rows) == 2
    
    @pytest.mark.asyncio
    async def test_builder_order_and_limit(self, memory_adapter, populated_db):
        """Test builder with order and limit."""
        rows = await (
            sql.select("*")
            .from_("builderusers")
            .order_by("age", "DESC")
            .limit(2)
            .execute()
        )
        
        assert len(rows) == 2
        assert rows[0]["age"] >= rows[1]["age"]
    
    @pytest.mark.asyncio
    async def test_builder_full_crud(self, memory_adapter):
        """Test full CRUD with builder."""
        await BuilderUser.create_table()
        
        # Insert
        await (
            sql.insert("builderusers")
            .values(name="CRUD", email="crud@example.com", age=30, role="user", active=1)
            .execute()
        )
        
        # Select
        rows = await sql.select("*").from_("builderusers").execute()
        assert len(rows) == 1
        
        # Update
        await (
            sql.update("builderusers")
            .set(name="CRUD Updated")
            .where("email", "=", "crud@example.com")
            .execute()
        )
        
        rows = await sql.select("*").from_("builderusers").execute()
        assert rows[0]["name"] == "CRUD Updated"
        
        # Delete
        await (
            sql.delete("builderusers")
            .where("email", "=", "crud@example.com")
            .execute()
        )
        
        rows = await sql.select("*").from_("builderusers").execute()
        assert len(rows) == 0
    
    @pytest.mark.asyncio
    async def test_builder_like(self, memory_adapter, populated_db):
        """Test builder with LIKE."""
        rows = await (
            sql.select("*")
            .from_("builderusers")
            .where("email", "LIKE", "%@example.com")
            .execute()
        )
        
        assert len(rows) == 3

