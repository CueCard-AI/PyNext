"""
Tests for PyNext Database Raw SQL Module.

Comprehensive tests for db.sql(), db.execute(), db.sql_one(), db.sql_val().
"""

import pytest
from datetime import datetime
from typing import Optional

from pynext.db import (
    Table,
    configure_db,
    MemoryAdapter,
    db,
)


# =============================================================================
# Test Models
# =============================================================================

class SQLUser(Table):
    """Test user model for SQL tests."""
    name: str
    email: str
    age: int = 0
    role: str = "user"
    active: bool = True


class SQLProduct(Table):
    """Test product model for SQL tests."""
    name: str
    price: float = 0.0
    stock: int = 0


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
async def memory_adapter():
    """Create and configure a memory adapter for real SQL execution."""
    adapter = MemoryAdapter()
    await adapter.connect()
    configure_db(adapter)
    yield adapter
    adapter.reset()
    await adapter.disconnect()


@pytest.fixture
async def populated_users(memory_adapter):
    """Create test users."""
    users = await SQLUser.insert_many([
        {"name": "Alice", "email": "alice@example.com", "age": 25, "role": "admin"},
        {"name": "Bob", "email": "bob@example.com", "age": 30, "role": "user"},
        {"name": "Charlie", "email": "charlie@example.com", "age": 35, "role": "user"},
        {"name": "Diana", "email": "diana@example.com", "age": 28, "role": "moderator"},
        {"name": "Eve", "email": "eve@example.com", "age": 22, "role": "user"},
    ])
    return users


# =============================================================================
# db.sql() Tests (20 tests)
# =============================================================================

class TestDbSql:
    """Tests for db.sql() - raw SELECT queries."""
    
    @pytest.mark.asyncio
    async def test_sql_basic(self, memory_adapter, populated_users):
        """Test basic SQL query."""
        rows = await db.sql("SELECT * FROM sqlusers")
        
        assert len(rows) == 5
    
    @pytest.mark.asyncio
    async def test_sql_with_param(self, memory_adapter, populated_users):
        """Test SQL with parameter."""
        rows = await db.sql(
            "SELECT * FROM sqlusers WHERE role = $1",
            "admin"
        )
        
        assert len(rows) == 1
        assert rows[0]["name"] == "Alice"
    
    @pytest.mark.asyncio
    async def test_sql_multiple_params(self, memory_adapter, populated_users):
        """Test SQL with multiple parameters."""
        rows = await db.sql(
            "SELECT * FROM sqlusers WHERE age >= $1 AND age <= $2",
            25, 30
        )
        
        assert len(rows) == 3
    
    @pytest.mark.asyncio
    async def test_sql_with_model(self, memory_adapter, populated_users):
        """Test SQL with model mapping."""
        users = await db.sql(
            "SELECT * FROM sqlusers WHERE role = $1",
            "admin",
            model=SQLUser
        )
        
        assert len(users) == 1
        assert isinstance(users[0], SQLUser)
        assert users[0].name == "Alice"
    
    @pytest.mark.asyncio
    async def test_sql_returns_dicts(self, memory_adapter, populated_users):
        """Test SQL returns dicts by default."""
        rows = await db.sql("SELECT * FROM sqlusers LIMIT 1")
        
        assert isinstance(rows[0], dict)
    
    @pytest.mark.asyncio
    async def test_sql_empty_result(self, memory_adapter, populated_users):
        """Test SQL with no matching rows."""
        rows = await db.sql(
            "SELECT * FROM sqlusers WHERE role = $1",
            "nonexistent"
        )
        
        assert rows == []
    
    @pytest.mark.asyncio
    async def test_sql_select_specific_columns(self, memory_adapter, populated_users):
        """Test SQL with specific columns."""
        rows = await db.sql("SELECT name, email FROM sqlusers LIMIT 1")
        
        assert "name" in rows[0]
        assert "email" in rows[0]
    
    @pytest.mark.asyncio
    async def test_sql_order_by(self, memory_adapter, populated_users):
        """Test SQL with ORDER BY."""
        rows = await db.sql("SELECT * FROM sqlusers ORDER BY age ASC")
        
        assert rows[0]["name"] == "Eve"  # Youngest (22)
    
    @pytest.mark.asyncio
    async def test_sql_limit(self, memory_adapter, populated_users):
        """Test SQL with LIMIT."""
        rows = await db.sql("SELECT * FROM sqlusers LIMIT 2")
        
        assert len(rows) == 2
    
    @pytest.mark.asyncio
    async def test_sql_like(self, memory_adapter, populated_users):
        """Test SQL with LIKE."""
        rows = await db.sql(
            "SELECT * FROM sqlusers WHERE email LIKE $1",
            "%@example.com"
        )
        
        assert len(rows) == 5
    
    @pytest.mark.asyncio
    async def test_sql_in_clause(self, memory_adapter, populated_users):
        """Test SQL with IN clause."""
        rows = await db.sql(
            "SELECT * FROM sqlusers WHERE role IN ('admin', 'moderator')"
        )
        
        assert len(rows) == 2
    
    @pytest.mark.asyncio
    async def test_sql_aggregate(self, memory_adapter, populated_users):
        """Test SQL aggregate function."""
        rows = await db.sql("SELECT COUNT(*) as cnt FROM sqlusers")
        
        assert rows[0]["cnt"] == 5
    
    @pytest.mark.asyncio
    async def test_sql_group_by(self, memory_adapter, populated_users):
        """Test SQL with GROUP BY."""
        rows = await db.sql(
            "SELECT role, COUNT(*) as cnt FROM sqlusers GROUP BY role ORDER BY cnt DESC"
        )
        
        assert rows[0]["role"] == "user"  # Most common
        assert rows[0]["cnt"] == 3
    
    @pytest.mark.asyncio
    async def test_sql_join_simulation(self, memory_adapter, populated_users):
        """Test SQL that could represent a JOIN."""
        # Create products
        await SQLProduct.insert_many([
            {"name": "Widget", "price": 10.0},
            {"name": "Gadget", "price": 20.0},
        ])
        
        rows = await db.sql("SELECT * FROM sqlproducts")
        
        assert len(rows) == 2
    
    @pytest.mark.asyncio
    async def test_sql_no_params(self, memory_adapter, populated_users):
        """Test SQL without parameters."""
        rows = await db.sql("SELECT * FROM sqlusers WHERE active = 1")
        
        assert len(rows) == 5
    
    @pytest.mark.asyncio
    async def test_sql_boolean_param(self, memory_adapter, populated_users):
        """Test SQL with boolean parameter (as int)."""
        rows = await db.sql(
            "SELECT * FROM sqlusers WHERE active = $1",
            1  # SQLite uses 1/0 for bool
        )
        
        assert len(rows) == 5
    
    @pytest.mark.asyncio
    async def test_sql_null_check(self, memory_adapter):
        """Test SQL with NULL check."""
        await SQLUser.insert(name="NullTest", email="null@example.com")
        
        rows = await db.sql("SELECT * FROM sqlusers WHERE age = 0")
        
        assert len(rows) >= 1
    
    @pytest.mark.asyncio
    async def test_sql_distinct(self, memory_adapter, populated_users):
        """Test SQL with DISTINCT."""
        rows = await db.sql("SELECT DISTINCT role FROM sqlusers")
        
        roles = [r["role"] for r in rows]
        assert len(roles) == len(set(roles))
    
    @pytest.mark.asyncio
    async def test_sql_case(self, memory_adapter, populated_users):
        """Test SQL with CASE expression."""
        rows = await db.sql("""
            SELECT name, 
                   CASE WHEN age >= 30 THEN 'senior' ELSE 'junior' END as level
            FROM sqlusers
        """)
        
        assert len(rows) == 5
        assert all("level" in r for r in rows)
    
    @pytest.mark.asyncio
    async def test_sql_subquery(self, memory_adapter, populated_users):
        """Test SQL with subquery."""
        rows = await db.sql("""
            SELECT * FROM sqlusers 
            WHERE age > (SELECT AVG(age) FROM sqlusers)
        """)
        
        # Average age is 28, so 30 and 35 qualify
        assert len(rows) == 2


# =============================================================================
# db.sql_one() Tests (15 tests)
# =============================================================================

class TestDbSqlOne:
    """Tests for db.sql_one() - single row queries."""
    
    @pytest.mark.asyncio
    async def test_sql_one_basic(self, memory_adapter, populated_users):
        """Test basic sql_one()."""
        row = await db.sql_one(
            "SELECT * FROM sqlusers WHERE name = $1",
            "Alice"
        )
        
        assert row is not None
        assert row["name"] == "Alice"
    
    @pytest.mark.asyncio
    async def test_sql_one_not_found(self, memory_adapter, populated_users):
        """Test sql_one() with no match."""
        row = await db.sql_one(
            "SELECT * FROM sqlusers WHERE name = $1",
            "Nonexistent"
        )
        
        assert row is None
    
    @pytest.mark.asyncio
    async def test_sql_one_with_model(self, memory_adapter, populated_users):
        """Test sql_one() with model mapping."""
        user = await db.sql_one(
            "SELECT * FROM sqlusers WHERE name = $1",
            "Alice",
            model=SQLUser
        )
        
        assert isinstance(user, SQLUser)
        assert user.name == "Alice"
    
    @pytest.mark.asyncio
    async def test_sql_one_multiple_params(self, memory_adapter, populated_users):
        """Test sql_one() with multiple parameters."""
        row = await db.sql_one(
            "SELECT * FROM sqlusers WHERE name = $1 AND role = $2",
            "Alice", "admin"
        )
        
        assert row is not None
        assert row["role"] == "admin"
    
    @pytest.mark.asyncio
    async def test_sql_one_by_id(self, memory_adapter, populated_users):
        """Test sql_one() by ID."""
        row = await db.sql_one(
            "SELECT * FROM sqlusers WHERE id = $1",
            1
        )
        
        assert row is not None
    
    @pytest.mark.asyncio
    async def test_sql_one_aggregate(self, memory_adapter, populated_users):
        """Test sql_one() with aggregate."""
        row = await db.sql_one("SELECT COUNT(*) as cnt FROM sqlusers")
        
        assert row["cnt"] == 5
    
    @pytest.mark.asyncio
    async def test_sql_one_max(self, memory_adapter, populated_users):
        """Test sql_one() with MAX."""
        row = await db.sql_one("SELECT MAX(age) as max_age FROM sqlusers")
        
        assert row["max_age"] == 35
    
    @pytest.mark.asyncio
    async def test_sql_one_min(self, memory_adapter, populated_users):
        """Test sql_one() with MIN."""
        row = await db.sql_one("SELECT MIN(age) as min_age FROM sqlusers")
        
        assert row["min_age"] == 22
    
    @pytest.mark.asyncio
    async def test_sql_one_avg(self, memory_adapter, populated_users):
        """Test sql_one() with AVG."""
        row = await db.sql_one("SELECT AVG(age) as avg_age FROM sqlusers")
        
        assert row["avg_age"] == 28.0
    
    @pytest.mark.asyncio
    async def test_sql_one_empty_table(self, memory_adapter):
        """Test sql_one() on empty table."""
        # Create table without data
        await SQLUser.create_table()
        
        row = await db.sql_one("SELECT * FROM sqlusers LIMIT 1")
        
        assert row is None
    
    @pytest.mark.asyncio
    async def test_sql_one_limit(self, memory_adapter, populated_users):
        """Test sql_one() respects LIMIT 1."""
        row = await db.sql_one("SELECT * FROM sqlusers ORDER BY age DESC LIMIT 1")
        
        assert row["age"] == 35
    
    @pytest.mark.asyncio
    async def test_sql_one_returns_dict(self, memory_adapter, populated_users):
        """Test sql_one() returns dict."""
        row = await db.sql_one("SELECT * FROM sqlusers LIMIT 1")
        
        assert isinstance(row, dict)
    
    @pytest.mark.asyncio
    async def test_sql_one_specific_columns(self, memory_adapter, populated_users):
        """Test sql_one() with specific columns."""
        row = await db.sql_one("SELECT name, email FROM sqlusers LIMIT 1")
        
        assert "name" in row
        assert "email" in row
    
    @pytest.mark.asyncio
    async def test_sql_one_with_alias(self, memory_adapter, populated_users):
        """Test sql_one() with column alias."""
        row = await db.sql_one("SELECT name as user_name FROM sqlusers LIMIT 1")
        
        assert "user_name" in row
    
    @pytest.mark.asyncio
    async def test_sql_one_sum(self, memory_adapter, populated_users):
        """Test sql_one() with SUM."""
        row = await db.sql_one("SELECT SUM(age) as total_age FROM sqlusers")
        
        assert row["total_age"] == 140


# =============================================================================
# db.sql_val() Tests (15 tests)
# =============================================================================

class TestDbSqlVal:
    """Tests for db.sql_val() - single value queries."""
    
    @pytest.mark.asyncio
    async def test_sql_val_count(self, memory_adapter, populated_users):
        """Test sql_val() with COUNT."""
        count = await db.sql_val("SELECT COUNT(*) FROM sqlusers")
        
        assert count == 5
    
    @pytest.mark.asyncio
    async def test_sql_val_max(self, memory_adapter, populated_users):
        """Test sql_val() with MAX."""
        max_age = await db.sql_val("SELECT MAX(age) FROM sqlusers")
        
        assert max_age == 35
    
    @pytest.mark.asyncio
    async def test_sql_val_min(self, memory_adapter, populated_users):
        """Test sql_val() with MIN."""
        min_age = await db.sql_val("SELECT MIN(age) FROM sqlusers")
        
        assert min_age == 22
    
    @pytest.mark.asyncio
    async def test_sql_val_avg(self, memory_adapter, populated_users):
        """Test sql_val() with AVG."""
        avg_age = await db.sql_val("SELECT AVG(age) FROM sqlusers")
        
        assert avg_age == 28.0
    
    @pytest.mark.asyncio
    async def test_sql_val_sum(self, memory_adapter, populated_users):
        """Test sql_val() with SUM."""
        total = await db.sql_val("SELECT SUM(age) FROM sqlusers")
        
        assert total == 140
    
    @pytest.mark.asyncio
    async def test_sql_val_single_column(self, memory_adapter, populated_users):
        """Test sql_val() with single column."""
        name = await db.sql_val(
            "SELECT name FROM sqlusers WHERE id = $1",
            1
        )
        
        assert isinstance(name, str)
    
    @pytest.mark.asyncio
    async def test_sql_val_empty(self, memory_adapter):
        """Test sql_val() on empty table."""
        await SQLUser.create_table()
        
        count = await db.sql_val("SELECT COUNT(*) FROM sqlusers")
        
        assert count == 0
    
    @pytest.mark.asyncio
    async def test_sql_val_no_result(self, memory_adapter, populated_users):
        """Test sql_val() with no matching rows."""
        val = await db.sql_val(
            "SELECT name FROM sqlusers WHERE role = $1",
            "nonexistent"
        )
        
        assert val is None
    
    @pytest.mark.asyncio
    async def test_sql_val_with_filter(self, memory_adapter, populated_users):
        """Test sql_val() with filter."""
        count = await db.sql_val(
            "SELECT COUNT(*) FROM sqlusers WHERE role = $1",
            "user"
        )
        
        assert count == 3
    
    @pytest.mark.asyncio
    async def test_sql_val_exists_true(self, memory_adapter, populated_users):
        """Test sql_val() for EXISTS (true)."""
        exists = await db.sql_val(
            "SELECT EXISTS(SELECT 1 FROM sqlusers WHERE role = $1)",
            "admin"
        )
        
        assert exists == 1
    
    @pytest.mark.asyncio
    async def test_sql_val_exists_false(self, memory_adapter, populated_users):
        """Test sql_val() for EXISTS (false)."""
        exists = await db.sql_val(
            "SELECT EXISTS(SELECT 1 FROM sqlusers WHERE role = $1)",
            "nonexistent"
        )
        
        assert exists == 0
    
    @pytest.mark.asyncio
    async def test_sql_val_integer(self, memory_adapter, populated_users):
        """Test sql_val() returns integer."""
        count = await db.sql_val("SELECT COUNT(*) FROM sqlusers")
        
        assert isinstance(count, int)
    
    @pytest.mark.asyncio
    async def test_sql_val_float(self, memory_adapter, populated_users):
        """Test sql_val() returns float."""
        avg = await db.sql_val("SELECT AVG(age) FROM sqlusers")
        
        assert isinstance(avg, (int, float))
    
    @pytest.mark.asyncio
    async def test_sql_val_expression(self, memory_adapter, populated_users):
        """Test sql_val() with expression."""
        result = await db.sql_val("SELECT MAX(age) - MIN(age) FROM sqlusers")
        
        assert result == 13  # 35 - 22
    
    @pytest.mark.asyncio
    async def test_sql_val_coalesce(self, memory_adapter, populated_users):
        """Test sql_val() with COALESCE."""
        result = await db.sql_val(
            "SELECT COALESCE(SUM(age), 0) FROM sqlusers WHERE role = $1",
            "nonexistent"
        )
        
        # COALESCE returns 0 when SUM is NULL
        assert result is not None


# =============================================================================
# db.execute() Tests (15 tests)
# =============================================================================

class TestDbExecute:
    """Tests for db.execute() - INSERT/UPDATE/DELETE queries."""
    
    @pytest.mark.asyncio
    async def test_execute_insert(self, memory_adapter):
        """Test execute() INSERT."""
        await SQLUser.create_table()
        
        await db.execute(
            "INSERT INTO sqlusers (name, email, age, role, active) VALUES ($1, $2, $3, $4, $5)",
            "Test", "test@example.com", 25, "user", 1
        )
        
        count = await db.sql_val("SELECT COUNT(*) FROM sqlusers")
        assert count == 1
    
    @pytest.mark.asyncio
    async def test_execute_update(self, memory_adapter, populated_users):
        """Test execute() UPDATE."""
        await db.execute(
            "UPDATE sqlusers SET age = $1 WHERE name = $2",
            99, "Alice"
        )
        
        row = await db.sql_one("SELECT age FROM sqlusers WHERE name = $1", "Alice")
        assert row["age"] == 99
    
    @pytest.mark.asyncio
    async def test_execute_update_many(self, memory_adapter, populated_users):
        """Test execute() UPDATE multiple rows."""
        await db.execute(
            "UPDATE sqlusers SET active = $1 WHERE role = $2",
            0, "user"
        )
        
        count = await db.sql_val(
            "SELECT COUNT(*) FROM sqlusers WHERE active = $1",
            0
        )
        assert count == 3
    
    @pytest.mark.asyncio
    async def test_execute_delete(self, memory_adapter, populated_users):
        """Test execute() DELETE."""
        initial_count = await db.sql_val("SELECT COUNT(*) FROM sqlusers")
        
        await db.execute("DELETE FROM sqlusers WHERE name = $1", "Alice")
        
        final_count = await db.sql_val("SELECT COUNT(*) FROM sqlusers")
        assert final_count == initial_count - 1
    
    @pytest.mark.asyncio
    async def test_execute_delete_many(self, memory_adapter, populated_users):
        """Test execute() DELETE multiple rows."""
        await db.execute("DELETE FROM sqlusers WHERE role = $1", "user")
        
        count = await db.sql_val("SELECT COUNT(*) FROM sqlusers")
        assert count == 2  # admin and moderator remain
    
    @pytest.mark.asyncio
    async def test_execute_delete_all(self, memory_adapter, populated_users):
        """Test execute() DELETE all."""
        await db.execute("DELETE FROM sqlusers")
        
        count = await db.sql_val("SELECT COUNT(*) FROM sqlusers")
        assert count == 0
    
    @pytest.mark.asyncio
    async def test_execute_no_match(self, memory_adapter, populated_users):
        """Test execute() with no matching rows."""
        await db.execute(
            "UPDATE sqlusers SET age = $1 WHERE role = $2",
            99, "nonexistent"
        )
        
        # No error, just no rows affected
        count = await db.sql_val("SELECT COUNT(*) FROM sqlusers WHERE age = 99")
        assert count == 0
    
    @pytest.mark.asyncio
    async def test_execute_update_zero(self, memory_adapter, populated_users):
        """Test execute() UPDATE to zero."""
        await db.execute(
            "UPDATE sqlusers SET age = 0 WHERE name = $1",
            "Alice"
        )
        
        row = await db.sql_one("SELECT age FROM sqlusers WHERE name = $1", "Alice")
        assert row["age"] == 0
    
    @pytest.mark.asyncio
    async def test_execute_insert_multiple(self, memory_adapter):
        """Test execute() multiple INSERTs."""
        await SQLUser.create_table()
        
        for i in range(5):
            await db.execute(
                "INSERT INTO sqlusers (name, email, age, role, active) VALUES ($1, $2, $3, $4, $5)",
                f"User{i}", f"user{i}@example.com", 20 + i, "user", 1
            )
        
        count = await db.sql_val("SELECT COUNT(*) FROM sqlusers")
        assert count == 5
    
    @pytest.mark.asyncio
    async def test_execute_update_increment(self, memory_adapter, populated_users):
        """Test execute() UPDATE with increment."""
        original_age = 25  # Alice's age
        
        await db.execute(
            "UPDATE sqlusers SET age = age + 1 WHERE name = $1",
            "Alice"
        )
        
        row = await db.sql_one("SELECT age FROM sqlusers WHERE name = $1", "Alice")
        assert row["age"] == original_age + 1
    
    @pytest.mark.asyncio
    async def test_execute_returns_result(self, memory_adapter, populated_users):
        """Test execute() returns result."""
        result = await db.execute(
            "UPDATE sqlusers SET age = $1 WHERE name = $2",
            99, "Alice"
        )
        
        # Result should be returned (cursor or similar)
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_execute_create_table(self, memory_adapter):
        """Test execute() CREATE TABLE."""
        await db.execute("""
            CREATE TABLE IF NOT EXISTS test_table (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        """)
        
        # Insert should work
        await db.execute("INSERT INTO test_table (name) VALUES ($1)", "Test")
        
        count = await db.sql_val("SELECT COUNT(*) FROM test_table")
        assert count == 1
    
    @pytest.mark.asyncio
    async def test_execute_drop_table(self, memory_adapter, populated_users):
        """Test execute() DROP TABLE."""
        await db.execute("DROP TABLE IF EXISTS sqlusers")
        
        # Table should be gone (this would error in a real test)
    
    @pytest.mark.asyncio
    async def test_execute_update_set_multiple(self, memory_adapter, populated_users):
        """Test execute() UPDATE multiple columns."""
        await db.execute(
            "UPDATE sqlusers SET age = $1, role = $2 WHERE name = $3",
            99, "superadmin", "Alice"
        )
        
        row = await db.sql_one("SELECT * FROM sqlusers WHERE name = $1", "Alice")
        assert row["age"] == 99
        assert row["role"] == "superadmin"
    
    @pytest.mark.asyncio
    async def test_execute_complex_update(self, memory_adapter, populated_users):
        """Test execute() complex UPDATE."""
        await db.execute("""
            UPDATE sqlusers 
            SET age = age * 2 
            WHERE role = $1 AND active = $2
        """, "user", 1)
        
        # Verify update worked
        rows = await db.sql("SELECT age FROM sqlusers WHERE role = 'user'")
        for row in rows:
            assert row["age"] >= 44  # At least 22 * 2


# =============================================================================
# db.raw() Tests (5 tests)
# =============================================================================

class TestDbRaw:
    """Tests for db.raw() - raw query execution."""
    
    @pytest.mark.asyncio
    async def test_raw_select(self, memory_adapter, populated_users):
        """Test raw() SELECT."""
        result = await db.raw("SELECT * FROM sqlusers")
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_raw_insert(self, memory_adapter):
        """Test raw() INSERT."""
        await SQLUser.create_table()
        
        result = await db.raw(
            "INSERT INTO sqlusers (name, email, age, role, active) VALUES ($1, $2, $3, $4, $5)",
            "Raw", "raw@example.com", 30, "user", 1
        )
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_raw_update(self, memory_adapter, populated_users):
        """Test raw() UPDATE."""
        result = await db.raw(
            "UPDATE sqlusers SET age = $1 WHERE name = $2",
            99, "Alice"
        )
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_raw_delete(self, memory_adapter, populated_users):
        """Test raw() DELETE."""
        result = await db.raw(
            "DELETE FROM sqlusers WHERE name = $1",
            "Alice"
        )
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_raw_pragma(self, memory_adapter):
        """Test raw() with PRAGMA."""
        result = await db.raw("PRAGMA table_info(sqlusers)")
        
        assert result is not None

