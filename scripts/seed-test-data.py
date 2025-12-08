#!/usr/bin/env python3
"""
Seed test database with sample data.

Usage:
    python scripts/seed-test-data.py                    # Default: 1000 users, 5000 orders
    python scripts/seed-test-data.py --users 10000     # Custom counts
    python scripts/seed-test-data.py --clean           # Clean tables first
"""

import argparse
import os
import random
import time
from datetime import datetime, timedelta

# Database URL
DB_URL = os.environ.get(
    "PYNEXT_TEST_DB_URL",
    "postgresql://pynext:pynext@localhost:5433/pynext_test"
)

# Sample data
FIRST_NAMES = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry", "Ivy", "Jack",
               "Kate", "Liam", "Mia", "Noah", "Olivia", "Paul", "Quinn", "Ruby", "Sam", "Tina"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
PRODUCT_NAMES = ["Widget", "Gadget", "Gizmo", "Doohickey", "Thingamajig", "Whatchamacallit", "Contraption"]
PRODUCT_ADJECTIVES = ["Super", "Ultra", "Mega", "Pro", "Plus", "Elite", "Premium", "Basic", "Advanced", "Deluxe"]
ORDER_STATUSES = ["pending", "processing", "shipped", "delivered", "cancelled"]


def create_tables(conn):
    """Create test tables if they don't exist."""
    print("Creating tables...")
    
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
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            price DECIMAL(10, 2) NOT NULL,
            stock INTEGER DEFAULT 0,
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
        CREATE TABLE IF NOT EXISTS order_items (
            id SERIAL PRIMARY KEY,
            order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
            product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
            quantity INTEGER NOT NULL,
            price DECIMAL(10, 2) NOT NULL
        )
    """)
    
    conn.commit()
    print("Tables created.")


def clean_tables(conn):
    """Truncate all tables."""
    print("Cleaning tables...")
    conn.execute("TRUNCATE TABLE order_items, orders, products, users RESTART IDENTITY CASCADE")
    conn.commit()
    print("Tables cleaned.")


def seed_users(conn, count: int):
    """Seed users table."""
    print(f"Seeding {count:,} users...")
    start = time.time()
    
    # Build data
    data = []
    for i in range(count):
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        email = f"user{i}@test.com"
        age = random.randint(18, 80)
        active = random.random() > 0.1  # 90% active
        created = datetime.now() - timedelta(days=random.randint(0, 365))
        data.append((name, email, age, active, created))
    
    # Use psycopg3's copy for speed
    with conn.cursor() as cur:
        with cur.copy("COPY users (name, email, age, active, created_at) FROM STDIN") as copy:
            for row in data:
                copy.write_row(row)
    conn.commit()
    
    print(f"  Seeded {count:,} users in {time.time() - start:.2f}s")


def seed_products(conn, count: int = 100):
    """Seed products table."""
    print(f"Seeding {count} products...")
    
    for i in range(count):
        name = f"{random.choice(PRODUCT_ADJECTIVES)} {random.choice(PRODUCT_NAMES)} {i}"
        price = round(random.uniform(9.99, 999.99), 2)
        stock = random.randint(0, 1000)
        conn.execute(
            "INSERT INTO products (name, price, stock) VALUES (%s, %s, %s)",
            (name, price, stock)
        )
    conn.commit()
    print(f"  Seeded {count} products.")


def seed_orders(conn, count: int, user_count: int):
    """Seed orders table."""
    print(f"Seeding {count:,} orders...")
    start = time.time()
    
    data = []
    for i in range(count):
        user_id = random.randint(1, user_count)
        total = round(random.uniform(10.00, 500.00), 2)
        status = random.choice(ORDER_STATUSES)
        created = datetime.now() - timedelta(days=random.randint(0, 180))
        data.append((user_id, total, status, created))
    
    with conn.cursor() as cur:
        with cur.copy("COPY orders (user_id, total, status, created_at) FROM STDIN") as copy:
            for row in data:
                copy.write_row(row)
    conn.commit()
    
    print(f"  Seeded {count:,} orders in {time.time() - start:.2f}s")


def seed_order_items(conn, order_count: int, product_count: int):
    """Seed order_items table."""
    item_count = order_count * 2  # ~2 items per order
    print(f"Seeding ~{item_count:,} order items...")
    start = time.time()
    
    data = []
    for order_id in range(1, order_count + 1):
        num_items = random.randint(1, 5)
        for _ in range(num_items):
            product_id = random.randint(1, product_count)
            quantity = random.randint(1, 10)
            price = round(random.uniform(9.99, 199.99), 2)
            data.append((order_id, product_id, quantity, price))
    
    with conn.cursor() as cur:
        with cur.copy("COPY order_items (order_id, product_id, quantity, price) FROM STDIN") as copy:
            for row in data:
                copy.write_row(row)
    conn.commit()
    
    actual_count = conn.execute("SELECT COUNT(*) FROM order_items").fetchone()[0]
    print(f"  Seeded {actual_count:,} order items in {time.time() - start:.2f}s")


def show_stats(conn):
    """Show table statistics."""
    print("\n=== Database Statistics ===")
    
    tables = ['users', 'products', 'orders', 'order_items']
    for table in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table}: {count:,} rows")


def main():
    parser = argparse.ArgumentParser(description="Seed test database")
    parser.add_argument("--users", type=int, default=1000, help="Number of users")
    parser.add_argument("--orders", type=int, default=5000, help="Number of orders")
    parser.add_argument("--products", type=int, default=100, help="Number of products")
    parser.add_argument("--clean", action="store_true", help="Clean tables first")
    parser.add_argument("--url", type=str, default=DB_URL, help="Database URL")
    args = parser.parse_args()
    
    print(f"Connecting to {args.url}...")
    
    try:
        import psycopg
    except ImportError:
        print("Error: psycopg not installed. Run: pip install psycopg[binary]")
        return 1
    
    try:
        conn = psycopg.connect(args.url)
    except Exception as e:
        print(f"Error: Cannot connect to database: {e}")
        print("Make sure PostgreSQL is running: docker-compose up -d postgres")
        return 1
    
    try:
        create_tables(conn)
        
        if args.clean:
            clean_tables(conn)
        
        print(f"\nSeeding data...")
        total_start = time.time()
        
        seed_users(conn, args.users)
        seed_products(conn, args.products)
        seed_orders(conn, args.orders, args.users)
        seed_order_items(conn, args.orders, args.products)
        
        print(f"\n✅ Total seeding time: {time.time() - total_start:.2f}s")
        
        show_stats(conn)
        
    finally:
        conn.close()
    
    return 0


if __name__ == "__main__":
    exit(main())

