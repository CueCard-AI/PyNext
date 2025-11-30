# Database Migrations

PyNext's migration system wraps Alembic with a radically simplified API. One-liners for common operations, full power when needed.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Design Philosophy](#design-philosophy)
3. [CLI Commands](#cli-commands)
4. [Model-Driven Workflow](#model-driven-workflow)
5. [Declarative Migrations](#declarative-migrations)
6. [Python Migrations](#python-migrations)
7. [Interactive Mode](#interactive-mode)
8. [Preview/Dry-Run](#previewdry-run)
9. [Rollback Guide](#rollback-guide)
10. [Architecture](#architecture)
11. [Troubleshooting](#troubleshooting)
12. [Alembic Interop](#alembic-interop)

---

## Quick Start

Get your first migration running in 30 seconds:

```bash
# 1. Initialize migrations (creates migrations/ folder)
pynext db init

# 2. Create your first model
# models.py
from pynext.db import Table

class User(Table):
    name: str
    email: str

# 3. Generate migration from model
pynext db migrate -m "create users table"

# 4. Apply migration
pynext db upgrade
```

That's it! Your database now has a `users` table.

---

## Design Philosophy

```
┌─────────────────────────────────────────────────────────────────────┐
│                         WHY PYNEXT MIGRATIONS?                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐        │
│  │  One Command │     │ Smart Detect │     │  Interactive │        │
│  │              │     │              │     │              │        │
│  │  pynext db   │────▶│ Auto-detect  │────▶│ "Did you     │        │
│  │  migrate -m  │     │ new tables,  │     │  rename X    │        │
│  │  "message"   │     │ columns...   │     │  to Y?"      │        │
│  └──────────────┘     └──────────────┘     └──────────────┘        │
│                                                                      │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐        │
│  │  Declarative │     │ Python When  │     │ Preview      │        │
│  │  First       │     │ Needed       │     │ Before Apply │        │
│  │              │     │              │     │              │        │
│  │  Simple ops  │────▶│ Complex data │────▶│ --sql shows  │        │
│  │  as dicts    │     │ migrations   │     │ exact SQL    │        │
│  └──────────────┘     └──────────────┘     └──────────────┘        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

| Principle | Why | How |
|-----------|-----|-----|
| **One Command** | Migrations shouldn't require ceremonies | `pynext db migrate -m "add users"` does everything |
| **Smart Detection** | Don't make devs specify obvious changes | Auto-detect new tables, columns, types from models |
| **Interactive When Ambiguous** | Renames vs add/drop can't be auto-detected | Prompt: "Did you rename 'name' to 'full_name'?" |
| **Declarative First** | 90% of migrations are simple | YAML-like Python dict for create/alter/drop |
| **Python Escape Hatch** | Complex data migrations need code | Full async Python for when declarative isn't enough |
| **Preview Before Apply** | See SQL before committing | `--sql` flag shows exact statements |

### Why PyNext Migrations > Alternatives

| Alternative | Problem | Our Solution |
|-------------|---------|--------------|
| **Raw Alembic** | Verbose `op.add_column()` calls, manual env setup | One-liner CLI, auto-setup |
| **Django Migrations** | Requires Django, magic model detection | Standalone, explicit type hints |
| **Prisma Migrate** | Separate schema file, TypeScript | Models ARE the schema |
| **Drizzle** | TypeScript-only | Native Python |

---

## CLI Commands

### Initialize Migrations

```bash
pynext db init
```

Creates the `migrations/` folder and configuration. Run once per project.

### Generate Migration

```bash
# Auto-detect changes from models
pynext db migrate -m "add user roles"

# Create empty migration (for data migrations)
pynext db migrate -m "migrate data" --empty
```

### Apply Migrations

```bash
# Apply all pending migrations
pynext db upgrade

# Apply to specific version
pynext db upgrade abc123

# Preview SQL without applying
pynext db upgrade --sql
```

### Rollback Migrations

```bash
# Rollback last migration
pynext db downgrade

# Rollback N migrations
pynext db downgrade -n 3

# Rollback to specific version
pynext db downgrade abc123

# Rollback all (to base)
pynext db downgrade base
```

### View Status

```bash
# Show current status (applied vs pending)
pynext db status

# Show migration history
pynext db history

# Show last N migrations
pynext db history -n 10
```

### Reset Database

```bash
# Down all, up all (requires confirmation)
pynext db reset

# Skip confirmation (for CI/scripts)
pynext db reset --yes
```

---

## Model-Driven Workflow

The recommended workflow: change your model, generate migration, apply.

### Step 1: Define Your Model

```python
# models.py
from pynext.db import Table
from typing import Optional
from datetime import datetime

class User(Table):
    name: str
    email: str
    role: str = "user"
    created_at: datetime = datetime.now()
```

### Step 2: Generate Migration

```bash
pynext db migrate -m "create users table"
```

PyNext detects:
- New `users` table
- Columns: `id` (auto), `name`, `email`, `role`, `created_at`, `updated_at` (auto)
- Types: `VARCHAR(255)`, `TIMESTAMP`, etc.
- Defaults: `role = 'user'`, `created_at = now()`

### Step 3: Review Generated Migration

```python
# migrations/0001_20240101120000_create_users_table.py
"""Create users table.

Migration: 0001_20240101120000
Created: 2024-01-01 12:00:00

Changes:
- Create table 'users' with 6 columns
"""

from pynext.db.migrations import migration

migration.create_table("users", {
    "id": "serial primary key",
    "name": "varchar(255) not null",
    "email": "varchar(255) not null",
    "role": "varchar(50) default 'user'",
    "created_at": "timestamp default now()",
    "updated_at": "timestamp default now()",
})
```

### Step 4: Apply

```bash
pynext db upgrade
```

---

## Declarative Migrations

For simple schema changes, use the declarative format. It's concise and auto-generates rollback.

### Create Table

```python
from pynext.db.migrations import migration

migration.create_table("users", {
    "id": "serial primary key",
    "email": "varchar(255) unique not null",
    "name": "varchar(255) not null",
    "role": "varchar(50) default 'user'",
    "created_at": "timestamp default now()",
})

# Optional: create index
migration.create_index("users", ["email"], unique=True)
```

**Auto-generated rollback:**
- `DROP TABLE users`
- `DROP INDEX idx_users_email`

### Add Column

```python
migration.add_column("users", "phone", "varchar(20)")
```

**Auto-generated rollback:** `DROP COLUMN phone`

### Drop Column

```python
migration.drop_column("users", "phone")
```

**Auto-generated rollback:** `ADD COLUMN phone varchar(20)` (needs type info)

### Rename Column

```python
migration.rename_column("users", "name", "full_name")
```

**Auto-generated rollback:** `RENAME COLUMN full_name TO name`

### Add Index

```python
# Simple index
migration.create_index("users", ["email"])

# Unique index
migration.create_index("users", ["email"], unique=True)

# Composite index
migration.create_index("users", ["first_name", "last_name"])

# Partial index (PostgreSQL)
migration.create_index("users", ["email"], where="active = true")
```

### Add Constraint

```python
# Unique constraint
migration.add_constraint("users", "uq_email", "UNIQUE (email)")

# Check constraint
migration.add_constraint("users", "ck_age", "CHECK (age >= 0)")

# Foreign key
migration.add_constraint(
    "posts", "fk_author",
    "FOREIGN KEY (author_id) REFERENCES users(id)"
)
```

---

## Python Migrations

For complex operations like data migrations, use Python format.

### Basic Structure

```python
# migrations/0002_20240102_split_name.py
"""Split name into first_name and last_name."""

from pynext.db.migrations import migration, op

@migration.up
async def upgrade():
    # Your upgrade logic here
    pass

@migration.down
async def downgrade():
    # Your rollback logic here
    pass
```

### Data Migration Example

```python
"""Split name into first_name and last_name."""

from pynext.db.migrations import migration, op

@migration.up
async def upgrade():
    # 1. Add new columns
    await op.add_column("users", "first_name", "varchar(255)")
    await op.add_column("users", "last_name", "varchar(255)")
    
    # 2. Migrate data
    async for user in op.fetch("SELECT id, name FROM users"):
        parts = user["name"].split(" ", 1)
        first = parts[0]
        last = parts[1] if len(parts) > 1 else ""
        
        await op.execute(
            "UPDATE users SET first_name = $1, last_name = $2 WHERE id = $3",
            first, last, user["id"]
        )
    
    # 3. Drop old column
    await op.drop_column("users", "name")

@migration.down
async def downgrade():
    # 1. Add back original column
    await op.add_column("users", "name", "varchar(255)")
    
    # 2. Restore data
    async for user in op.fetch("SELECT id, first_name, last_name FROM users"):
        full_name = f"{user['first_name']} {user['last_name']}".strip()
        
        await op.execute(
            "UPDATE users SET name = $1 WHERE id = $2",
            full_name, user["id"]
        )
    
    # 3. Drop new columns
    await op.drop_column("users", "first_name")
    await op.drop_column("users", "last_name")
```

### Available Operations (op.*)

| Operation | Description |
|-----------|-------------|
| `op.execute(sql, *params)` | Execute SQL statement |
| `op.fetch(sql, *params)` | Fetch all rows |
| `op.fetch_one(sql, *params)` | Fetch single row |
| `op.fetch_val(sql, *params)` | Fetch single value |
| `op.create_table(name, columns)` | Create table |
| `op.drop_table(name)` | Drop table |
| `op.add_column(table, name, type)` | Add column |
| `op.drop_column(table, name)` | Drop column |
| `op.rename_column(table, old, new)` | Rename column |
| `op.create_index(table, columns)` | Create index |
| `op.drop_index(name)` | Drop index |

---

## Interactive Mode

When PyNext detects ambiguous changes, it prompts for clarification.

### Rename Detection

```
$ pynext db migrate -m "refactor user table"

Detected potential rename:
  Column 'name' dropped
  Column 'full_name' added (same type)

Did you rename 'name' to 'full_name'? [y/N]: y

Generated RENAME COLUMN instead of DROP + ADD
```

### Destructive Operation Warning

```
$ pynext db migrate -m "cleanup"

⚠️  Warning: Table 'old_users' has 1,234 rows
Dropping this table will permanently delete all data.

Continue? [y/N]: 
```

### Non-Interactive Mode

Skip all prompts for CI/scripts:

```bash
pynext db migrate -m "auto" --yes
```

This assumes:
- No renames (uses DROP + ADD)
- Accept all destructive operations

---

## Preview/Dry-Run

Always preview SQL before applying to production.

### Preview Upgrade

```bash
$ pynext db upgrade --sql

-- Migration: 0003_20240103_add_phone
BEGIN;
ALTER TABLE users ADD COLUMN phone VARCHAR(20);
COMMIT;
```

### Preview Downgrade

```bash
$ pynext db downgrade --sql

-- Rolling back: 0003_20240103_add_phone
BEGIN;
ALTER TABLE users DROP COLUMN phone;
COMMIT;
```

### Preview Multiple

```bash
$ pynext db upgrade head --sql

-- Migration: 0003_20240103_add_phone
ALTER TABLE users ADD COLUMN phone VARCHAR(20);

-- Migration: 0004_20240104_add_index
CREATE UNIQUE INDEX idx_users_phone ON users(phone);
```

---

## Rollback Guide

### Rollback Last Migration

```bash
pynext db downgrade
```

### Rollback Multiple Migrations

```bash
# Rollback last 3
pynext db downgrade -n 3
```

### Rollback to Specific Version

```bash
# Get version from history
pynext db history

# Rollback to that version
pynext db downgrade 0002_20240102_add_role
```

### Rollback Everything

```bash
pynext db downgrade base
```

### Partial Rollback Recovery

If a rollback fails midway:

1. Check status: `pynext db status`
2. Fix the migration file
3. Retry: `pynext db downgrade`

Or manually fix the database and mark as rolled back:

```bash
pynext db stamp 0002_20240102  # Mark as current version
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           CLI Layer                                  │
│   pynext db init | migrate | upgrade | downgrade | history          │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────────┐
│                        Migration Engine                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐  │
│  │  Detector   │  │  Generator  │  │         Executor            │  │
│  │ (model diff)│  │ (file gen)  │  │    (Alembic wrapper)        │  │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────────┘  │
│         │                │                      │                    │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌───────────▼─────────────────┐  │
│  │   Prompt    │  │  Formatter  │  │          History            │  │
│  │(interactive)│  │(decl/python)│  │    (version tracking)       │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────────┘  │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────────┐
│                      Alembic (Under the Hood)                        │
│  - env.py auto-generated and hidden                                  │
│  - alembic.ini replaced with pynext.config.py settings              │
│  - Migration scripts wrapped with PyNext API                         │
└─────────────────────────────────────────────────────────────────────┘
```

### Components

| Component | File | Purpose |
|-----------|------|---------|
| **Engine** | `engine.py` | Core orchestration |
| **Detector** | `detector.py` | Compares models to DB schema |
| **Changes** | `changes.py` | Change type classes |
| **Generator** | `generator.py` | Creates migration files |
| **Formatter** | `formatter.py` | Formats declarative/Python |
| **Prompt** | `prompt.py` | Interactive prompts |
| **Executor** | `executor.py` | Runs migrations (wraps Alembic) |
| **History** | `history.py` | Tracks applied versions |
| **Operations** | `operations.py` | `op.*` functions |

---

## Troubleshooting

### Common Issues

#### "Migration file not found"

```bash
# Check migrations directory
ls migrations/

# Regenerate if needed
pynext db migrate -m "recreate"
```

#### "Database connection failed"

```bash
# Check your pynext.config.py
cat pynext.config.py | grep DATABASE

# Test connection
pynext db status
```

#### "Migration already applied"

```bash
# Check what's applied
pynext db history

# Force re-apply (careful!)
pynext db stamp base  # Reset history
pynext db upgrade     # Re-apply all
```

#### "Syntax error in migration"

```bash
# Check the file
python -m py_compile migrations/0003_xxx.py

# Fix and retry
pynext db upgrade
```

#### "Rollback failed"

```bash
# Check current state
pynext db status

# Option 1: Fix the down migration and retry
# Option 2: Manually fix DB and stamp
pynext db stamp 0002_20240102
```

### Debug Mode

```bash
# Verbose output
pynext db upgrade -v

# Very verbose
pynext db upgrade -vv
```

---

## Alembic Interop

PyNext wraps Alembic, so you can use raw Alembic when needed.

### Access Alembic Directly

```python
from pynext.db.migrations import get_alembic_context

# Get the Alembic migration context
ctx = get_alembic_context()

# Use raw Alembic operations
from alembic import op as alembic_op
alembic_op.execute("SELECT 1")
```

### Use Alembic CLI

```bash
# PyNext creates alembic.ini for you
alembic current
alembic heads
```

### Migrate from Existing Alembic

If you have existing Alembic migrations:

1. Keep your `migrations/` folder
2. Run `pynext db init` (won't overwrite)
3. PyNext will use existing migrations

---

## Best Practices

### 1. One Change Per Migration

```python
# Good: One focused change
migration.add_column("users", "phone", "varchar(20)")

# Bad: Multiple unrelated changes
migration.add_column("users", "phone", "varchar(20)")
migration.create_table("products", {...})  # Separate migration!
```

### 2. Descriptive Messages

```bash
# Good
pynext db migrate -m "add phone column to users"

# Bad
pynext db migrate -m "update"
```

### 3. Always Preview Production

```bash
# Before deploying
pynext db upgrade --sql > migration.sql
# Review migration.sql
pynext db upgrade
```

### 4. Test Rollbacks

```bash
pynext db upgrade
pynext db downgrade
pynext db upgrade  # Should work again
```

### 5. Use Transactions

PyNext wraps each migration in a transaction by default. For PostgreSQL DDL:

```python
@migration.up
async def upgrade():
    # All operations in one transaction
    await op.create_table("users", {...})
    await op.create_index("users", ["email"])
    # If index fails, table creation is rolled back
```

---

## API Reference

### migration Module

```python
from pynext.db.migrations import migration

# Declarative
migration.create_table(name, columns)
migration.drop_table(name, cascade=False)
migration.add_column(table, name, type)
migration.drop_column(table, name)
migration.rename_column(table, old, new)
migration.alter_column(table, name, **changes)
migration.create_index(table, columns, unique=False)
migration.drop_index(name)
migration.add_constraint(table, name, definition)
migration.drop_constraint(table, name)

# Python decorators
@migration.up
async def upgrade(): ...

@migration.down
async def downgrade(): ...
```

### op Module

```python
from pynext.db.migrations import op

# Execute
await op.execute(sql, *params)
await op.fetch(sql, *params)
await op.fetch_one(sql, *params)
await op.fetch_val(sql, *params)

# DDL
await op.create_table(name, columns)
await op.drop_table(name)
await op.add_column(table, name, type)
await op.drop_column(table, name)
await op.rename_column(table, old, new)
await op.create_index(table, columns, unique=False)
await op.drop_index(name)

# Transactions
await op.begin_transaction()
await op.commit_transaction()
await op.rollback_transaction()
```

---

## Summary

PyNext migrations make database schema management simple:

1. **Change your model** - Just modify Python classes
2. **Generate migration** - `pynext db migrate -m "description"`
3. **Review** - Check the generated file
4. **Apply** - `pynext db upgrade`
5. **Rollback if needed** - `pynext db downgrade`

The system is designed to be:
- **Fast**: One command for most operations
- **Safe**: Preview before apply, interactive prompts
- **Flexible**: Declarative for simple, Python for complex
- **Familiar**: Builds on Alembic, standard SQL

