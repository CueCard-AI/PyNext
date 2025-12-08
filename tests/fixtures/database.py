"""
Database Test Fixtures

Provides PostgreSQL fixtures for testing with two isolation levels:
- Session-scoped: Shared across all tests (fast, use clean_tables for isolation)
- Function-scoped: Fresh connection/transaction per test (slower, fully isolated)

Usage:
    # Session fixture (fast, manually clean up)
    def test_query(db_pool, clean_tables):
        clean_tables(["users", "orders"])
        # test code...
    
    # Per-test transaction (auto-rollback, fully isolated)
    def test_insert(db_transaction):
        db_transaction.execute("INSERT INTO users ...")
        # automatically rolled back after test
    
    # With Go bridge
    def test_go_query(go_bridge):
        result = go_bridge.execute("SELECT 1", [])
        assert result.scalar() == 1

Environment Variables:
    PYNEXT_TEST_DB_URL: Override the default test database URL
    PYNEXT_SKIP_DB_TESTS: Skip all database tests if set
    PYNEXT_REQUIRE_GO: Fail if Go bridge not available (default: skip)
"""

from __future__ import annotations

import os
import pytest
from typing import Generator, Any
from contextlib import contextmanager

# =============================================================================
# Configuration
# =============================================================================

# Default test database URL (matches docker-compose.yml)
DEFAULT_TEST_DB_URL = "postgresql://pynext:pynext@localhost:5433/pynext_test"


def get_test_db_url() -> str:
    """Get the test database URL from environment or default."""
    return os.environ.get("PYNEXT_TEST_DB_URL", DEFAULT_TEST_DB_URL)


def is_db_available() -> bool:
    """Check if the test database is available."""
    try:
        import psycopg
        url = get_test_db_url()
        with psycopg.connect(url, connect_timeout=2) as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:
        return False


def is_go_available() -> bool:
    """Check if the Go bridge is available."""
    try:
        from pynext_go.bridge import GO_AVAILABLE
        return GO_AVAILABLE
    except ImportError:
        return False


# =============================================================================
# Markers
# =============================================================================

requires_db = pytest.mark.skipif(
    not is_db_available(),
    reason="PostgreSQL test database not available (run: docker-compose up -d)"
)

requires_go = pytest.mark.skipif(
    not is_go_available(),
    reason="Go bridge not available"
)


# =============================================================================
# URL Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def db_url() -> str:
    """Get the test database URL."""
    return get_test_db_url()


@pytest.fixture(scope="session")
def test_db_url() -> str:
    """Alias for db_url."""
    return get_test_db_url()


# =============================================================================
# Session-Scoped Fixtures (Shared - Fast)
# =============================================================================

@pytest.fixture(scope="session")
def db_engine(db_url: str):
    """
    Create a database engine for the entire test session.
    
    This is the fastest option - reuses connections across all tests.
    Use with clean_tables fixture for test isolation.
    """
    try:
        import psycopg_pool
    except ImportError:
        pytest.skip("psycopg[pool] not installed")
    
    if not is_db_available():
        pytest.skip("PostgreSQL test database not available")
    
    pool = psycopg_pool.ConnectionPool(
        db_url,
        min_size=2,
        max_size=10,
        open=True,
    )
    
    yield pool
    
    pool.close()


@pytest.fixture(scope="session")
def db_pool(db_engine):
    """Alias for db_engine."""
    return db_engine


# =============================================================================
# Function-Scoped Fixtures (Isolated - Safe)
# =============================================================================

@pytest.fixture
def db_connection(db_pool):
    """
    Get a database connection for a single test.
    
    Connection is returned to the pool after the test.
    """
    with db_pool.connection() as conn:
        yield conn


@pytest.fixture
def db_transaction(db_connection):
    """
    Get a database connection wrapped in a transaction.
    
    The transaction is ROLLED BACK after each test, ensuring
    complete isolation without needing to clean tables.
    
    Example:
        def test_insert(db_transaction):
            db_transaction.execute("INSERT INTO users (name) VALUES ('test')")
            # Automatically rolled back - no cleanup needed!
    """
    # Start a savepoint we can rollback to
    with db_connection.transaction() as tx:
        yield db_connection
        # Rollback happens automatically when exiting the context


@pytest.fixture
def clean_tables(db_pool):
    """
    Factory fixture to clean specific tables before a test.
    
    Example:
        def test_users(db_pool, clean_tables):
            clean_tables(["users", "orders"])
            # Tables are now empty
    """
    def _clean(tables: list[str], cascade: bool = True):
        with db_pool.connection() as conn:
            for table in tables:
                if cascade:
                    conn.execute(f"TRUNCATE TABLE {table} CASCADE")
                else:
                    conn.execute(f"TRUNCATE TABLE {table}")
            conn.commit()
    
    return _clean


# =============================================================================
# Go Bridge Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def go_bridge_session(db_url: str):
    """
    Initialize Go bridge for the entire test session.
    
    This is faster than initializing per-test.
    """
    if not is_go_available():
        pytest.skip("Go bridge not available")
    
    import pynext_go
    
    # Initialize once for all tests
    pynext_go.init(primary=db_url)
    pynext_go.warmup()
    
    yield pynext_go
    
    pynext_go.close()


@pytest.fixture
def go_bridge(go_bridge_session):
    """
    Get the Go bridge for a single test.
    
    Uses the session-scoped bridge for performance.
    """
    return go_bridge_session


# =============================================================================
# Test Data Helpers
# =============================================================================

@pytest.fixture
def seed_users(db_pool):
    """
    Factory fixture to seed test users.
    
    Example:
        def test_users(db_pool, seed_users, clean_tables):
            clean_tables(["users"])
            seed_users(10)  # Create 10 test users
    """
    def _seed(count: int = 5, table: str = "users"):
        with db_pool.connection() as conn:
            for i in range(count):
                conn.execute(
                    f"INSERT INTO {table} (name, email, age) VALUES (%s, %s, %s)",
                    (f"User {i}", f"user{i}@test.com", 20 + i)
                )
            conn.commit()
    
    return _seed


@pytest.fixture
def seed_orders(db_pool):
    """
    Factory fixture to seed test orders.
    
    Example:
        def test_orders(db_pool, seed_users, seed_orders, clean_tables):
            clean_tables(["orders", "users"])
            seed_users(3)
            seed_orders(10, user_ids=[1, 2, 3])
    """
    def _seed(count: int = 5, user_ids: list[int] | None = None, table: str = "orders"):
        import random
        with db_pool.connection() as conn:
            for i in range(count):
                user_id = random.choice(user_ids) if user_ids else 1
                conn.execute(
                    f"INSERT INTO {table} (user_id, total, status) VALUES (%s, %s, %s)",
                    (user_id, round(random.uniform(10, 500), 2), random.choice(["pending", "completed", "cancelled"]))
                )
            conn.commit()
    
    return _seed


# =============================================================================
# Schema Management
# =============================================================================

@pytest.fixture(scope="session")
def create_test_tables(db_pool):
    """
    Create test tables if they don't exist.
    
    This runs once per session before any tests that need it.
    """
    with db_pool.connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE,
                age INTEGER,
                active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                total DECIMAL(10, 2) NOT NULL,
                status VARCHAR(50) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                price DECIMAL(10, 2) NOT NULL,
                stock INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id SERIAL PRIMARY KEY,
                order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
                product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
                quantity INTEGER NOT NULL,
                price DECIMAL(10, 2) NOT NULL
            )
        """)
        
        conn.commit()
    
    return True


# =============================================================================
# Async Fixtures
# =============================================================================

@pytest.fixture
async def async_db_connection(db_url: str):
    """
    Async database connection for async tests.
    """
    try:
        import psycopg
    except ImportError:
        pytest.skip("psycopg not installed")
    
    if not is_db_available():
        pytest.skip("PostgreSQL test database not available")
    
    async with await psycopg.AsyncConnection.connect(db_url) as conn:
        yield conn


@pytest.fixture
async def async_db_transaction(async_db_connection):
    """
    Async database transaction that rolls back after each test.
    """
    async with async_db_connection.transaction():
        yield async_db_connection
        # Automatically rolled back

