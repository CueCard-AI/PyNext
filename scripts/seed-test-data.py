#!/usr/bin/env python3
"""
Seed Test Data for Go Bridge Benchmarks

This script populates the test database with data needed for benchmark tests.
Run with: python scripts/seed-test-data.py

Creates:
- users table (10 rows)
- orders table (5,000 rows)
- logs table (100,000 rows for bulk read tests)
"""

import os
import sys
import time

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_URL = os.environ.get(
    "PYNEXT_TEST_DB_URL",
    "postgresql://pynext:pynext@localhost:5433/pynext_test"
)


def seed_with_go_bridge():
    """Seed data using Go bridge."""
    import pynext_go
    
    print("🔌 Connecting via Go Bridge...")
    
    # Close any existing connection
    try:
        pynext_go.close()
    except Exception:
        pass
    
    # Initialize
    pynext_go.init(primary=DB_URL, pool_min_size=5, pool_max_size=20)
    pynext_go.warmup()
    
    print("✅ Connected to database")
    
    # Create tables
    print("\n📋 Creating tables...")
    
    # Users table
    pynext_go.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE,
            age INTEGER,
            active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """, [])
    print("  - users table ready")
    
    # Orders table
    pynext_go.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            total DECIMAL(10, 2) NOT NULL,
            status VARCHAR(50) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """, [])
    print("  - orders table ready")
    
    # Logs table (for large bulk read tests)
    pynext_go.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id SERIAL PRIMARY KEY,
            level VARCHAR(20) NOT NULL,
            message TEXT NOT NULL,
            metadata JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """, [])
    print("  - logs table ready")
    
    # Check current data
    result = pynext_go.execute("SELECT COUNT(*) as count FROM users", [])
    user_count = result.rows[0][0] if result.rows else 0
    
    result = pynext_go.execute("SELECT COUNT(*) as count FROM orders", [])
    order_count = result.rows[0][0] if result.rows else 0
    
    result = pynext_go.execute("SELECT COUNT(*) as count FROM logs", [])
    log_count = result.rows[0][0] if result.rows else 0
    
    print(f"\n📊 Current data: {user_count} users, {order_count} orders, {log_count} logs")
    
    # Seed users if needed
    if user_count < 10:
        print("\n👥 Seeding users...")
        # Clear existing
        pynext_go.execute("TRUNCATE users CASCADE", [])
        
        for i in range(10):
            pynext_go.execute(
                "INSERT INTO users (name, email, age, active) VALUES ($1, $2, $3, $4)",
                [f"User {i}", f"user{i}@test.com", 20 + i, i % 2 == 0]
            )
        print("  ✓ Created 10 users")
    else:
        print("  → Users already seeded")
    
    # Seed orders if needed
    if order_count < 5000:
        print("\n📦 Seeding orders (5,000 rows)...")
        # Clear existing
        pynext_go.execute("TRUNCATE orders", [])
        
        start = time.time()
        batch_size = 500
        statuses = ['pending', 'processing', 'completed', 'cancelled']
        
        for batch in range(0, 5000, batch_size):
            # Use batch insert for speed
            values = []
            placeholders = []
            param_idx = 1
            
            for i in range(batch, min(batch + batch_size, 5000)):
                placeholders.append(f"(${param_idx}, ${param_idx+1}, ${param_idx+2})")
                values.extend([
                    (i % 10) + 1,  # user_id
                    round(10.0 * (i + 1), 2),  # total
                    statuses[i % 4]  # status
                ])
                param_idx += 3
            
            sql = f"INSERT INTO orders (user_id, total, status) VALUES {', '.join(placeholders)}"
            pynext_go.execute(sql, values)
            
            if (batch + batch_size) % 1000 == 0:
                print(f"    {batch + batch_size} / 5000 orders inserted...")
        
        elapsed = time.time() - start
        print(f"  ✓ Created 5,000 orders in {elapsed:.2f}s")
    else:
        print("  → Orders already seeded")
    
    # Seed logs if needed (for large bulk read tests)
    if log_count < 100000:
        print("\n📝 Seeding logs (100,000 rows)...")
        # Clear existing
        pynext_go.execute("TRUNCATE logs", [])
        
        start = time.time()
        batch_size = 1000
        levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        
        for batch in range(0, 100000, batch_size):
            values = []
            placeholders = []
            param_idx = 1
            
            for i in range(batch, min(batch + batch_size, 100000)):
                placeholders.append(f"(${param_idx}, ${param_idx+1}, ${param_idx+2})")
                values.extend([
                    levels[i % 5],
                    f"Log message {i}: This is a test log entry for benchmarking purposes.",
                    f'{{"request_id": "{i}", "user_id": {i % 10 + 1}}}'
                ])
                param_idx += 3
            
            sql = f"INSERT INTO logs (level, message, metadata) VALUES {', '.join(placeholders)}"
            pynext_go.execute(sql, values)
            
            if (batch + batch_size) % 10000 == 0:
                print(f"    {batch + batch_size} / 100,000 logs inserted...")
        
        elapsed = time.time() - start
        print(f"  ✓ Created 100,000 logs in {elapsed:.2f}s")
    else:
        print("  → Logs already seeded")
    
    # Final verification
    print("\n✅ Final verification:")
    user_count = pynext_go.execute("SELECT COUNT(*) as count FROM users", []).rows[0][0]
    order_count = pynext_go.execute("SELECT COUNT(*) as count FROM orders", []).rows[0][0]
    log_count = pynext_go.execute("SELECT COUNT(*) as count FROM logs", []).rows[0][0]
    
    print(f"  - Users: {user_count}")
    print(f"  - Orders: {order_count}")
    print(f"  - Logs: {log_count}")
    
    pynext_go.close()
    print("\n🎉 Database seeding complete!")


def seed_with_psycopg():
    """Fallback: seed using psycopg (sync)."""
    import psycopg
    
    print("🔌 Connecting via psycopg (fallback)...")
    
    with psycopg.connect(DB_URL) as conn:
        with conn.cursor() as cur:
            # Create tables
            print("\n📋 Creating tables...")
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) UNIQUE,
                    age INTEGER,
                    active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    total DECIMAL(10, 2) NOT NULL,
                    status VARCHAR(50) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id SERIAL PRIMARY KEY,
                    level VARCHAR(20) NOT NULL,
                    message TEXT NOT NULL,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            print("  ✓ Tables created")
            
            # Check counts
            cur.execute("SELECT COUNT(*) FROM users")
            user_count = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM orders")
            order_count = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM logs")
            log_count = cur.fetchone()[0]
            
            print(f"\n📊 Current data: {user_count} users, {order_count} orders, {log_count} logs")
            
            # Seed users
            if user_count < 10:
                print("\n👥 Seeding users...")
                cur.execute("TRUNCATE users CASCADE")
                for i in range(10):
                    cur.execute(
                        "INSERT INTO users (name, email, age, active) VALUES (%s, %s, %s, %s)",
                        (f"User {i}", f"user{i}@test.com", 20 + i, i % 2 == 0)
                    )
                conn.commit()
                print("  ✓ Created 10 users")
            
            # Seed orders
            if order_count < 5000:
                print("\n📦 Seeding orders...")
                cur.execute("TRUNCATE orders")
                statuses = ['pending', 'processing', 'completed', 'cancelled']
                for i in range(5000):
                    cur.execute(
                        "INSERT INTO orders (user_id, total, status) VALUES (%s, %s, %s)",
                        ((i % 10) + 1, round(10.0 * (i + 1), 2), statuses[i % 4])
                    )
                    if (i + 1) % 1000 == 0:
                        conn.commit()
                        print(f"    {i + 1} / 5000...")
                conn.commit()
                print("  ✓ Created 5,000 orders")
            
            # Seed logs  
            if log_count < 100000:
                print("\n📝 Seeding logs...")
                cur.execute("TRUNCATE logs")
                levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
                for i in range(100000):
                    cur.execute(
                        "INSERT INTO logs (level, message, metadata) VALUES (%s, %s, %s)",
                        (
                            levels[i % 5],
                            f"Log message {i}",
                            f'{{"request_id": "{i}"}}'
                        )
                    )
                    if (i + 1) % 10000 == 0:
                        conn.commit()
                        print(f"    {i + 1} / 100,000...")
                conn.commit()
                print("  ✓ Created 100,000 logs")
    
    print("\n🎉 Database seeding complete!")


def main():
    print("=" * 60)
    print("PyNext Go Bridge - Test Data Seeder")
    print("=" * 60)
    print(f"\nDatabase: {DB_URL}")
    
    try:
        import pynext_go
        if pynext_go.GO_AVAILABLE:
            seed_with_go_bridge()
        else:
            raise ImportError("Go bridge not available")
    except ImportError:
        print("⚠️  Go bridge not available, using psycopg fallback...")
        seed_with_psycopg()


if __name__ == "__main__":
    main()
