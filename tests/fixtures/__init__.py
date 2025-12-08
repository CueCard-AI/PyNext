"""
PyNext Test Fixtures

Re-exports all fixtures for easy importing.
"""

from tests.fixtures.database import (
    # Configuration
    db_url,
    test_db_url,
    
    # Session-scoped (shared across all tests - fast)
    db_engine,
    db_pool,
    
    # Function-scoped (fresh per test - isolated)
    db_connection,
    db_transaction,
    clean_tables,
    
    # Go Bridge fixtures
    go_bridge,
    go_bridge_session,
    
    # Test data helpers
    seed_users,
    seed_orders,
    
    # Markers
    requires_db,
    requires_go,
)

__all__ = [
    "db_url",
    "test_db_url",
    "db_engine",
    "db_pool",
    "db_connection",
    "db_transaction",
    "clean_tables",
    "go_bridge",
    "go_bridge_session",
    "seed_users",
    "seed_orders",
    "requires_db",
    "requires_go",
]

