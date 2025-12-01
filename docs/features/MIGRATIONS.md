# Database Migrations

## Table of Contents

1. [Introduction: Why Migrations?](#introduction-why-migrations)
2. [Chapter 1: The Schema Evolution Problem](#chapter-1-the-schema-evolution-problem)
3. [Chapter 2: What is a Migration?](#chapter-2-what-is-a-migration)
4. [Chapter 3: Your First Migration](#chapter-3-your-first-migration)
5. [Chapter 4: Model-Driven Migrations](#chapter-4-model-driven-migrations)
6. [Chapter 5: Declarative Migrations](#chapter-5-declarative-migrations)
7. [Chapter 6: Python Migrations](#chapter-6-python-migrations)
8. [Chapter 7: The Interactive Experience](#chapter-7-the-interactive-experience)
9. [Chapter 8: Rolling Back](#chapter-8-rolling-back)
10. [Chapter 9: Viewing Changes Before Applying](#chapter-9-viewing-changes-before-applying)
11. [Chapter 10: Migration History](#chapter-10-migration-history)
12. [Chapter 11: Team Workflows](#chapter-11-team-workflows)
13. [Chapter 12: Production Deployments](#chapter-12-production-deployments)
14. [CLI Reference](#cli-reference)
15. [Troubleshooting](#troubleshooting)

---

## Introduction: Why Migrations?

### The Growing Application

Your app starts simple:

```python
class User(Table):
    name: str
    email: str
```

A week later, you need ages:

```python
class User(Table):
    name: str
    email: str
    age: int  # ← New field!
```

A month later, you need profiles:

```python
class User(Table):
    name: str
    email: str
    age: int
    bio: str           # ← New!
    avatar_url: str    # ← New!
    is_verified: bool  # ← New!
```

**The question**: How do you update the database to match your new code?

### The Naive Approach (Don't Do This!)

```sql
-- You could manually run SQL...
ALTER TABLE users ADD COLUMN age INTEGER;
ALTER TABLE users ADD COLUMN bio TEXT;
-- etc.
```

**Problems with manual SQL:**

| Problem | Why It's Bad |
|---------|--------------|
| **No history** | Which changes were applied? When? By whom? |
| **No coordination** | What if your teammate made different changes? |
| **No rollback** | How do you undo if something breaks? |
| **Environment drift** | Dev, staging, and prod databases get out of sync |
| **Human error** | Easy to forget a step, make a typo |

### The Migration Solution

**Migrations** are version-controlled database changes. Think of them like Git for your database schema:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DATABASE MIGRATION HISTORY                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  v1: Create users table                                             │
│  ├── 2024-01-01_create_users.py                                    │
│  │                                                                  │
│  v2: Add age column                                                 │
│  ├── 2024-01-15_add_age.py                                         │
│  │                                                                  │
│  v3: Add profile fields                                             │
│  ├── 2024-02-01_add_profile.py                                     │
│  │                                                                  │
│  v4: Create posts table                                             │
│  └── 2024-02-15_create_posts.py                                    │
│                                                                      │
│  Each migration knows how to:                                        │
│  → UPGRADE: Apply the change                                        │
│  → DOWNGRADE: Undo the change                                       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Chapter 1: The Schema Evolution Problem

### What is a Schema?

A **schema** is the structure of your database - the tables, columns, types, and constraints:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DATABASE SCHEMA                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Table: users                                                        │
│  ├── id: INTEGER PRIMARY KEY                                        │
│  ├── name: TEXT NOT NULL                                            │
│  ├── email: TEXT UNIQUE                                             │
│  └── age: INTEGER DEFAULT 0                                         │
│                                                                      │
│  Table: posts                                                        │
│  ├── id: INTEGER PRIMARY KEY                                        │
│  ├── title: TEXT NOT NULL                                           │
│  ├── content: TEXT                                                  │
│  └── user_id: INTEGER REFERENCES users(id)                          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### The Two Truths Problem

You have two sources of truth:

1. **Python models** (what you want)
2. **Database schema** (what exists)

```
Python Models                    Database Schema
─────────────                    ───────────────

class User(Table):               CREATE TABLE users (
    name: str                        id INTEGER,
    email: str                       name TEXT,
    age: int       ← NEW!            email TEXT
    bio: str       ← NEW!            -- no age!
                                     -- no bio!
                                 );

MISMATCH! 😱
```

When these get out of sync, you get errors:
- "Column 'age' doesn't exist"
- "Cannot insert: unknown column 'bio'"

### How Migrations Solve This

Migrations bridge the gap:

```
Python Models         Migration              Database Schema
─────────────         ─────────              ───────────────

class User:           Detects diff:          Before:
    name: str         "age" is new →         CREATE TABLE users (
    email: str        "bio" is new →             name TEXT,
    age: int                                      email TEXT
    bio: str          Generates SQL:         );
                      ALTER TABLE users
                      ADD COLUMN age INT;    After:
                      ALTER TABLE users      CREATE TABLE users (
                      ADD COLUMN bio TEXT;       name TEXT,
                                                 email TEXT,
                                                 age INTEGER,
                                                 bio TEXT
                                             );
                      ✓ In sync!
```

---

## Chapter 2: What is a Migration?

### The Migration Concept

A **migration** is a reversible change to your database schema. It has two parts:

| Part | Purpose | Example |
|------|---------|---------|
| **Upgrade** | Apply the change | `ADD COLUMN age INTEGER` |
| **Downgrade** | Undo the change | `DROP COLUMN age` |

### Migration File Structure

```
migrations/
├── env.py                          # Configuration
├── versions/                       # Migration files
│   ├── 0001_create_users.py       # First migration
│   ├── 0002_add_age.py            # Second migration
│   └── 0003_create_posts.py       # Third migration
└── migration_history               # Track applied migrations
```

### Anatomy of a Migration

```python
# migrations/versions/0002_add_age.py

"""
Add age column to users.

Revision: 0002
Previous: 0001
Created: 2024-01-15 10:30:00
"""

revision = "0002"
down_revision = "0001"
message = "Add age column to users"

# What this migration does (forward)
upgrade = {
    "add_column": {
        "table": "users",
        "column": "age",
        "type": "INTEGER",
        "default": 0
    }
}

# How to undo it (backward)
downgrade = {
    "drop_column": {
        "table": "users",
        "column": "age"
    }
}
```

### The Migration Chain

Migrations form a chain. Each knows its predecessor:

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  0001    │───►│  0002    │───►│  0003    │───►│  0004    │
│ create   │    │ add age  │    │ create   │    │ add bio  │
│ users    │    │          │    │ posts    │    │          │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
     ▲
     │
   HEAD
(current state)
```

When you upgrade:
- Start at current position (HEAD)
- Apply each migration in order
- Stop at target (usually latest)

When you downgrade:
- Start at current position
- Undo each migration in reverse order
- Stop at target

---

## Chapter 3: Your First Migration

### Step 1: Initialize Migrations

```bash
pynext db init
```

This creates the migrations folder structure:

```
your_project/
├── pynext.py           # Your app
├── models.py           # Your models
└── migrations/         # ← Created!
    ├── env.py
    └── versions/
```

### Step 2: Create Your Model

```python
# models.py
from pynext.db import Table

class User(Table):
    name: str
    email: str
```

### Step 3: Generate Migration

```bash
pynext db migrate -m "create users table"
```

PyNext detects that:
- You have a `User` model
- No `users` table exists
- → Creates a migration to create the table

Output:
```
✓ Detected changes:
  + Table 'users' (new)
    + Column 'id' (INTEGER, primary key)
    + Column 'name' (TEXT, not null)
    + Column 'email' (TEXT, not null)
    + Column 'created_at' (TIMESTAMP)
    + Column 'updated_at' (TIMESTAMP)

Generated: migrations/versions/0001_create_users.py
```

### Step 4: Review the Migration

```python
# migrations/versions/0001_create_users.py

revision = "0001"
down_revision = None  # First migration, no predecessor
message = "create users table"

upgrade = {
    "create_table": {
        "name": "users",
        "columns": [
            {"name": "id", "type": "INTEGER", "primary_key": True, "autoincrement": True},
            {"name": "name", "type": "TEXT", "nullable": False},
            {"name": "email", "type": "TEXT", "nullable": False},
            {"name": "created_at", "type": "TIMESTAMP", "default": "CURRENT_TIMESTAMP"},
            {"name": "updated_at", "type": "TIMESTAMP", "default": "CURRENT_TIMESTAMP"},
        ]
    }
}

downgrade = {
    "drop_table": {
        "name": "users"
    }
}
```

### Step 5: Apply the Migration

```bash
pynext db upgrade
```

Output:
```
Applying migrations:
  → 0001_create_users... ✓

Database is now at: 0001
```

### Step 6: Verify

```bash
pynext db status
```

Output:
```
Current revision: 0001
Applied migrations:
  ✓ 0001 - create users table (applied 2024-01-15 10:30:00)

No pending migrations.
```

### The Complete Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MIGRATION WORKFLOW                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. EDIT MODELS                                                      │
│     class User(Table):                                              │
│         name: str                                                   │
│         email: str                                                  │
│         age: int  ← add new field                                   │
│                                                                      │
│  2. GENERATE MIGRATION                                               │
│     $ pynext db migrate -m "add age column"                         │
│     ✓ Generated 0002_add_age.py                                     │
│                                                                      │
│  3. REVIEW (optional)                                               │
│     $ pynext db preview                                             │
│     ALTER TABLE users ADD COLUMN age INTEGER                        │
│                                                                      │
│  4. APPLY                                                           │
│     $ pynext db upgrade                                             │
│     ✓ Applied 0002_add_age                                          │
│                                                                      │
│  5. VERIFY                                                          │
│     $ pynext db status                                              │
│     Current: 0002                                                   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Chapter 4: Model-Driven Migrations

### The Magic: Auto-Detection

PyNext compares your Python models to the current database schema and detects differences:

```python
# Before
class User(Table):
    name: str
    email: str

# After
class User(Table):
    name: str
    email: str
    age: int           # ← Added
    is_active: bool    # ← Added
```

When you run `pynext db migrate`:

```
Comparing models to database schema...

Detected changes:
  ~ Table 'users' (modified)
    + Column 'age' (INTEGER)
    + Column 'is_active' (BOOLEAN)

Generate migration? [Y/n]: y
Generated: migrations/versions/0002_add_user_fields.py
```

### What Gets Detected

| Change | Example | Detected? |
|--------|---------|-----------|
| New table | `class Post(Table)` | ✅ Yes |
| New column | `age: int` added | ✅ Yes |
| Column type change | `age: int` → `age: str` | ✅ Yes |
| Column removed | Remove `age: int` | ✅ Yes |
| Default changed | `age: int = 0` → `age: int = 18` | ✅ Yes |
| Nullable changed | `age: int` → `age: Optional[int]` | ✅ Yes |
| Unique added | `Field(unique=True)` | ✅ Yes |
| Index added | `Field(index=True)` | ✅ Yes |
| Rename column | `name` → `full_name` | ⚠️ Interactive |
| Rename table | `User` → `Account` | ⚠️ Interactive |

### Handling Renames (Interactive Mode)

Renames are ambiguous. Did you rename a column, or delete one and add another?

```python
# Before
class User(Table):
    name: str

# After
class User(Table):
    full_name: str  # Is this a rename, or add+delete?
```

PyNext asks you:

```
Detected changes:
  ~ Table 'users' (modified)
    - Column 'name' (removed)
    + Column 'full_name' (added)

Did you rename 'name' to 'full_name'? [y/N]: y

✓ Will generate RENAME instead of DROP+ADD
```

If you say yes → `ALTER TABLE users RENAME COLUMN name TO full_name`
If you say no → `DROP COLUMN name` + `ADD COLUMN full_name`

### Multiple Models

```python
# models.py
from pynext.db import Table, ForeignKey

class User(Table):
    name: str
    email: str

class Post(Table):
    title: str
    content: str
    user_id: int = ForeignKey(User)

class Comment(Table):
    text: str
    post_id: int = ForeignKey(Post)
    user_id: int = ForeignKey(User)
```

Running `pynext db migrate -m "initial schema"` detects all three tables and creates migrations in the correct order (respecting foreign key dependencies).

---

## Chapter 5: Declarative Migrations

### What is Declarative?

**Declarative** means describing **what** you want, not **how** to do it:

```python
# Declarative: What I want
upgrade = {
    "add_column": {
        "table": "users",
        "column": "age",
        "type": "INTEGER"
    }
}

# Imperative: How to do it (you manage the SQL)
def upgrade():
    op.execute("ALTER TABLE users ADD COLUMN age INTEGER")
```

Declarative is simpler and safer. PyNext generates the correct SQL for your database.

### Declarative Operations

#### Create Table

```python
upgrade = {
    "create_table": {
        "name": "products",
        "columns": [
            {"name": "id", "type": "INTEGER", "primary_key": True},
            {"name": "name", "type": "TEXT", "nullable": False},
            {"name": "price", "type": "DECIMAL(10,2)"},
            {"name": "stock", "type": "INTEGER", "default": 0},
        ]
    }
}

downgrade = {
    "drop_table": {"name": "products"}
}
```

#### Add Column

```python
upgrade = {
    "add_column": {
        "table": "users",
        "column": "age",
        "type": "INTEGER",
        "default": 0,
        "nullable": True
    }
}

downgrade = {
    "drop_column": {
        "table": "users",
        "column": "age"
    }
}
```

#### Modify Column

```python
upgrade = {
    "alter_column": {
        "table": "users",
        "column": "age",
        "type": "BIGINT",  # Change type
        "nullable": False,  # Make required
        "default": 18       # Change default
    }
}

downgrade = {
    "alter_column": {
        "table": "users",
        "column": "age",
        "type": "INTEGER",
        "nullable": True,
        "default": 0
    }
}
```

#### Rename Column

```python
upgrade = {
    "rename_column": {
        "table": "users",
        "from": "name",
        "to": "full_name"
    }
}

downgrade = {
    "rename_column": {
        "table": "users",
        "from": "full_name",
        "to": "name"
    }
}
```

#### Create Index

```python
upgrade = {
    "create_index": {
        "name": "idx_users_email",
        "table": "users",
        "columns": ["email"],
        "unique": True
    }
}

downgrade = {
    "drop_index": {"name": "idx_users_email"}
}
```

#### Add Foreign Key

```python
upgrade = {
    "add_foreign_key": {
        "table": "posts",
        "column": "user_id",
        "references": {
            "table": "users",
            "column": "id"
        },
        "on_delete": "CASCADE"
    }
}

downgrade = {
    "drop_constraint": {
        "table": "posts",
        "name": "posts_user_id_fkey"
    }
}
```

### Multiple Operations in One Migration

```python
upgrade = [
    {
        "add_column": {
            "table": "users",
            "column": "age",
            "type": "INTEGER"
        }
    },
    {
        "add_column": {
            "table": "users",
            "column": "bio",
            "type": "TEXT"
        }
    },
    {
        "create_index": {
            "name": "idx_users_age",
            "table": "users",
            "columns": ["age"]
        }
    }
]

downgrade = [
    {"drop_index": {"name": "idx_users_age"}},
    {"drop_column": {"table": "users", "column": "bio"}},
    {"drop_column": {"table": "users", "column": "age"}},
]
```

---

## Chapter 6: Python Migrations

### When to Use Python

Declarative migrations handle schema changes. But sometimes you need **data migrations**:

- Backfilling new columns with computed values
- Splitting or merging columns
- Complex data transformations
- Conditionally migrating based on existing data

### Python Migration Structure

```python
# migrations/versions/0005_backfill_full_name.py

revision = "0005"
down_revision = "0004"
message = "Backfill full_name from first_name + last_name"

# Use Python for complex logic
async def upgrade(db):
    # Add the column first
    await db.execute("""
        ALTER TABLE users ADD COLUMN full_name TEXT
    """)
    
    # Backfill from existing data
    users = await db.execute("SELECT id, first_name, last_name FROM users")
    for user in users:
        full_name = f"{user['first_name']} {user['last_name']}"
        await db.execute(
            "UPDATE users SET full_name = $1 WHERE id = $2",
            full_name, user['id']
        )

async def downgrade(db):
    await db.execute("ALTER TABLE users DROP COLUMN full_name")
```

### Real-World Python Migration Examples

#### Example 1: Split a Column

```python
# Before: users.name = "Alice Smith"
# After: users.first_name = "Alice", users.last_name = "Smith"

async def upgrade(db):
    # Add new columns
    await db.execute("ALTER TABLE users ADD COLUMN first_name TEXT")
    await db.execute("ALTER TABLE users ADD COLUMN last_name TEXT")
    
    # Split existing data
    users = await db.execute("SELECT id, name FROM users")
    for user in users:
        parts = user['name'].split(' ', 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ''
        
        await db.execute(
            "UPDATE users SET first_name = $1, last_name = $2 WHERE id = $3",
            first_name, last_name, user['id']
        )
    
    # Drop old column
    await db.execute("ALTER TABLE users DROP COLUMN name")

async def downgrade(db):
    await db.execute("ALTER TABLE users ADD COLUMN name TEXT")
    
    users = await db.execute("SELECT id, first_name, last_name FROM users")
    for user in users:
        name = f"{user['first_name']} {user['last_name']}".strip()
        await db.execute(
            "UPDATE users SET name = $1 WHERE id = $2",
            name, user['id']
        )
    
    await db.execute("ALTER TABLE users DROP COLUMN first_name")
    await db.execute("ALTER TABLE users DROP COLUMN last_name")
```

#### Example 2: Hash Passwords

```python
# Migrate from plain text to hashed passwords
import hashlib

async def upgrade(db):
    await db.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
    
    users = await db.execute("SELECT id, password FROM users")
    for user in users:
        # Hash the password
        password_hash = hashlib.sha256(user['password'].encode()).hexdigest()
        await db.execute(
            "UPDATE users SET password_hash = $1 WHERE id = $2",
            password_hash, user['id']
        )
    
    await db.execute("ALTER TABLE users DROP COLUMN password")

async def downgrade(db):
    # Cannot reverse a hash! Just add empty column back
    await db.execute("ALTER TABLE users ADD COLUMN password TEXT DEFAULT ''")
    await db.execute("ALTER TABLE users DROP COLUMN password_hash")
```

#### Example 3: Conditional Migration

```python
# Only migrate active users
async def upgrade(db):
    await db.execute("ALTER TABLE users ADD COLUMN migrated_at TIMESTAMP")
    
    # Only process active users
    active_users = await db.execute("""
        SELECT id, email FROM users 
        WHERE is_active = true AND last_login > NOW() - INTERVAL '30 days'
    """)
    
    for user in active_users:
        # Do something with active users
        await db.execute(
            "UPDATE users SET migrated_at = NOW() WHERE id = $1",
            user['id']
        )
```

### Hybrid: Declarative + Python

You can mix both in one migration:

```python
revision = "0006"
down_revision = "0005"
message = "Add status column with backfill"

# Declarative part (schema change)
upgrade_schema = {
    "add_column": {
        "table": "orders",
        "column": "status",
        "type": "TEXT",
        "default": "'pending'"
    }
}

# Python part (data migration)
async def upgrade_data(db):
    # Set status based on existing data
    await db.execute("""
        UPDATE orders SET status = 'completed' 
        WHERE paid_at IS NOT NULL AND shipped_at IS NOT NULL
    """)
    await db.execute("""
        UPDATE orders SET status = 'shipped' 
        WHERE paid_at IS NOT NULL AND shipped_at IS NOT NULL AND delivered_at IS NULL
    """)
```

---

## Chapter 7: The Interactive Experience

### Smart Prompts

PyNext asks questions when it can't determine intent:

#### Rename vs Add/Drop

```
$ pynext db migrate

Comparing models to database...

Column 'name' was removed from 'users'
Column 'full_name' was added to 'users'

Did you rename 'name' to 'full_name'? [y/N]: y
→ Will generate: ALTER TABLE users RENAME COLUMN name TO full_name

─────────────────────────────────────────────────

Column 'age' was removed from 'users'
Column 'birth_year' was added to 'users'

Did you rename 'age' to 'birth_year'? [y/N]: n
→ Will generate: DROP COLUMN age, ADD COLUMN birth_year
```

#### Destructive Changes

```
$ pynext db migrate

Detected changes:
  ~ Table 'users' (modified)
    - Column 'temporary_data' (removed)

⚠️  This will delete the 'temporary_data' column and all its data!

Proceed? [y/N]: y
→ Generated migration with DROP COLUMN
```

#### Table Renames

```
$ pynext db migrate

Table 'users' no longer exists in models.
Table 'accounts' is new in models.

Did you rename 'users' to 'accounts'? [y/N]: y
→ Will generate: ALTER TABLE users RENAME TO accounts
```

### Skipping Interactive Mode

For CI/CD, use `--non-interactive`:

```bash
# Use defaults (assume drops, not renames)
pynext db migrate --non-interactive

# Assume all ambiguous changes are renames
pynext db migrate --non-interactive --assume-rename

# Fail if any ambiguous changes (safest for CI)
pynext db migrate --non-interactive --strict
```

---

## Chapter 8: Rolling Back

### Why Roll Back?

Things go wrong:
- Migration has a bug
- Feature is delayed
- Need to test previous version

### Basic Rollback

```bash
# Undo the last migration
pynext db downgrade

# Undo the last 3 migrations
pynext db downgrade -n 3

# Go to a specific revision
pynext db downgrade 0002
```

### Understanding Downgrade

```
Current: 0005

$ pynext db downgrade

Downgrading from 0005...
  ← 0005_add_comments... (undoing)
  
Current: 0004

The database schema is now at revision 0004.
Migration 0005 has been reversed but the file still exists.
```

### The Downgrade Chain

```
Before: 0001 → 0002 → 0003 → 0004 → 0005 (HEAD)

$ pynext db downgrade -n 2

Rolling back:
  ← 0005_add_comments
  ← 0004_add_posts

After: 0001 → 0002 → 0003 (HEAD)

Migrations 0004 and 0005 still exist but are not applied.
You can re-apply them with: pynext db upgrade
```

### What Can Go Wrong

Some migrations are hard to reverse:

| Operation | Reversible? | Notes |
|-----------|-------------|-------|
| Create table | ✅ Yes | DROP TABLE |
| Add column | ✅ Yes | DROP COLUMN |
| Drop column | ⚠️ Data lost | Can recreate column, but data is gone |
| Rename column | ✅ Yes | Rename back |
| Change type | ⚠️ Maybe | May lose precision or fail |
| Delete rows | ❌ No | Data is gone unless you backed up |

### Safe Rollback Practices

1. **Always test downgrades** before deploying:
   ```bash
   pynext db upgrade
   pynext db downgrade
   pynext db upgrade  # Make sure it still works
   ```

2. **Backup before destructive migrations**:
   ```sql
   -- In your migration, backup first
   CREATE TABLE users_backup AS SELECT * FROM users;
   ALTER TABLE users DROP COLUMN sensitive_data;
   ```

3. **Make irreversible migrations explicit**:
   ```python
   async def downgrade(db):
       raise IrreversibleMigration(
           "Cannot restore deleted data. Restore from backup."
       )
   ```

---

## Chapter 9: Viewing Changes Before Applying

### Preview Mode

See exactly what SQL will run:

```bash
pynext db preview
```

Output:
```
Pending migrations: 2

0003_add_posts:
────────────────
CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT,
    user_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_posts_user_id ON posts(user_id);

0004_add_age_to_users:
──────────────────────
ALTER TABLE users ADD COLUMN age INTEGER DEFAULT 0;
```

### SQL Output

Generate SQL file instead of applying:

```bash
# Output to file
pynext db upgrade --sql > changes.sql

# Review the file
cat changes.sql

# Apply manually if needed
psql -f changes.sql
```

### Dry Run

Simulate upgrade without applying:

```bash
pynext db upgrade --dry-run
```

Output:
```
Would apply:
  → 0003_add_posts
  → 0004_add_age_to_users

No changes were made (dry run).
```

---

## Chapter 10: Migration History

### Viewing History

```bash
pynext db history
```

Output:
```
Migration History
─────────────────

  ✓ 0001 - create users table
    Applied: 2024-01-01 10:00:00
    
  ✓ 0002 - add email unique constraint  
    Applied: 2024-01-15 14:30:00
    
  ✓ 0003 - create posts table
    Applied: 2024-02-01 09:15:00
    
  ○ 0004 - add comments table
    Not applied (pending)

Current revision: 0003
Pending migrations: 1
```

### Where History is Stored

PyNext tracks applied migrations in a database table:

```sql
-- The migration_history table (auto-created)
SELECT * FROM pynext_migrations;

-- revision  | applied_at           | checksum
-- ----------|----------------------|------------------
-- 0001      | 2024-01-01 10:00:00 | abc123...
-- 0002      | 2024-01-15 14:30:00 | def456...
-- 0003      | 2024-02-01 09:15:00 | ghi789...
```

### Checking Status

```bash
pynext db status
```

Output:
```
Database Status
───────────────
Connection: postgresql://localhost/myapp
Current revision: 0003

Applied migrations: 3
Pending migrations: 1

Next pending: 0004_add_comments
```

---

## Chapter 11: Team Workflows

### The Git Workflow

Migrations are version-controlled files. Treat them like code:

```
1. Create branch for your feature
   $ git checkout -b add-comments

2. Make model changes
   # models.py
   class Comment(Table):
       text: str
       post_id: int

3. Generate migration
   $ pynext db migrate -m "add comments table"

4. Commit migration with code
   $ git add models.py migrations/versions/0004_add_comments.py
   $ git commit -m "Add comments feature"

5. Push and create PR
   $ git push origin add-comments
```

### Handling Merge Conflicts

When two developers create migrations on different branches:

```
main: 0001 → 0002 → 0003

Developer A:          Developer B:
0001 → 0002 → 0003    0001 → 0002 → 0003
                ↓                   ↓
              0004a               0004b

After merge:
0001 → 0002 → 0003 → 0004a
                   ↘
                     0004b  ← Problem! Same number!
```

**Solution: Merge migrations**

```bash
# After merging branches, fix the sequence
pynext db merge

# This will:
# 1. Detect both 0004a and 0004b
# 2. Renumber one to 0005
# 3. Update the down_revision links
```

### Migration Naming Conventions

Use consistent, descriptive names:

```
✓ Good:
  0003_create_posts_table.py
  0004_add_user_age_column.py
  0005_add_email_unique_constraint.py
  0006_create_comments_with_fk_to_posts.py

✗ Bad:
  0003_update.py
  0004_fix.py
  0005_new_stuff.py
```

---

## Chapter 12: Production Deployments

### The Deployment Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PRODUCTION DEPLOYMENT                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. CI/CD Pipeline                                                   │
│     ├── Run tests                                                   │
│     ├── Build application                                           │
│     └── Validate migrations (pynext db check)                       │
│                                                                      │
│  2. Pre-Deployment                                                   │
│     ├── Create database backup                                      │
│     └── Verify migration safety (pynext db preview)                 │
│                                                                      │
│  3. Deployment                                                       │
│     ├── Apply migrations (pynext db upgrade)                        │
│     └── Deploy new application code                                 │
│                                                                      │
│  4. Post-Deployment                                                  │
│     ├── Verify application health                                   │
│     └── Monitor for errors                                          │
│                                                                      │
│  5. Rollback (if needed)                                            │
│     ├── Rollback application code                                   │
│     ├── Rollback migrations (pynext db downgrade)                   │
│     └── Restore from backup (if needed)                             │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### CI/CD Commands

```bash
# In your CI/CD pipeline:

# 1. Validate migrations (no database needed)
pynext db check

# 2. Test migrations in test database
pynext db upgrade --database-url=$TEST_DATABASE_URL
pynext db downgrade --database-url=$TEST_DATABASE_URL
pynext db upgrade --database-url=$TEST_DATABASE_URL

# 3. Generate SQL for review
pynext db preview --database-url=$PROD_DATABASE_URL > migration.sql

# 4. Apply in production (after approval)
pynext db upgrade --database-url=$PROD_DATABASE_URL
```

### Zero-Downtime Migrations

For production systems that can't go offline:

```python
# Phase 1: Add column (nullable)
upgrade = {
    "add_column": {
        "table": "users",
        "column": "new_field",
        "type": "TEXT",
        "nullable": True  # Allow NULL initially
    }
}

# Deploy code that writes to both old and new columns

# Phase 2: Backfill data
async def upgrade(db):
    await db.execute("""
        UPDATE users SET new_field = old_field WHERE new_field IS NULL
    """)

# Phase 3: Make non-nullable
upgrade = {
    "alter_column": {
        "table": "users",
        "column": "new_field",
        "nullable": False
    }
}

# Phase 4: Drop old column (after code no longer uses it)
upgrade = {
    "drop_column": {
        "table": "users",
        "column": "old_field"
    }
}
```

### Backup Before Destructive Changes

```bash
# Create backup before risky migration
pg_dump mydb > backup_before_0005.sql

# Apply migration
pynext db upgrade

# If something goes wrong:
psql mydb < backup_before_0005.sql
```

---

## CLI Reference

### All Commands

| Command | Description |
|---------|-------------|
| `pynext db init` | Initialize migrations folder |
| `pynext db migrate -m "msg"` | Generate migration from model changes |
| `pynext db upgrade` | Apply pending migrations |
| `pynext db downgrade` | Undo last migration |
| `pynext db status` | Show current state |
| `pynext db history` | Show migration history |
| `pynext db preview` | Show SQL that would run |
| `pynext db check` | Validate migrations |
| `pynext db merge` | Fix duplicate revision numbers |

### Command Details

#### pynext db init

```bash
pynext db init [--directory migrations]
```

Creates migration infrastructure:
- `migrations/` folder
- `migrations/env.py` configuration
- `migrations/versions/` for migration files

#### pynext db migrate

```bash
pynext db migrate -m "description" [options]

Options:
  -m, --message     Migration description (required)
  --autogenerate    Detect changes from models (default)
  --empty           Create empty migration template
  --sql             Output SQL instead of Python
  --non-interactive Skip prompts
```

#### pynext db upgrade

```bash
pynext db upgrade [revision] [options]

Arguments:
  revision          Target revision (default: head/latest)

Options:
  --sql             Output SQL instead of applying
  --dry-run         Show what would happen without applying
  -n, --count       Apply up to N migrations
```

#### pynext db downgrade

```bash
pynext db downgrade [revision] [options]

Arguments:
  revision          Target revision (default: previous)

Options:
  --sql             Output SQL instead of applying
  --dry-run         Show what would happen
  -n, --count       Undo N migrations
```

#### pynext db status

```bash
pynext db status

Shows:
  - Current revision
  - Applied migrations count
  - Pending migrations count
  - Next pending migration
```

#### pynext db history

```bash
pynext db history [options]

Options:
  --verbose         Show full migration details
  --limit N         Show only last N migrations
```

#### pynext db preview

```bash
pynext db preview [options]

Options:
  --revision REV    Preview specific revision
  --all             Preview all pending migrations
```

---

## Troubleshooting

### Common Errors

**"No migrations folder found"**

```bash
# Solution: Initialize migrations
pynext db init
```

**"Migration X depends on Y which doesn't exist"**

```bash
# Solution: Check your down_revision chain
# Make sure each migration points to an existing predecessor
```

**"Database is ahead of migrations"**

Someone applied migrations directly to the database without committing the files.

```bash
# Solution: Stamp the database with current state
pynext db stamp head
```

**"Duplicate revision numbers"**

Two developers created migrations with the same number.

```bash
# Solution: Merge and renumber
pynext db merge
```

### Debugging Migrations

```bash
# Verbose output
pynext db upgrade --verbose

# See exact SQL
pynext db preview

# Check migration files
pynext db check

# View detailed history
pynext db history --verbose
```

### Recovery Scenarios

**Applied migration with bug:**
```bash
pynext db downgrade  # Undo it
# Fix the migration file
pynext db upgrade    # Re-apply
```

**Database out of sync with migrations:**
```bash
# If database is ahead:
pynext db stamp <current_revision>

# If database is behind:
pynext db upgrade
```

**Need to start fresh (development only!):**
```bash
# Nuclear option - drop everything
pynext db drop-all
pynext db upgrade
```

---

## Summary

Migrations are version-controlled database schema changes that:

1. **Track history** - Know what changed, when, and why
2. **Enable collaboration** - Team members can share schema changes
3. **Support rollback** - Undo changes when needed
4. **Ensure consistency** - Dev, staging, and prod stay in sync

PyNext migrations are:
- **Model-driven** - Generate from Python class changes
- **Declarative** - Simple dict-based format for most operations
- **Python-powered** - Full async Python when you need it
- **Interactive** - Smart prompts for ambiguous changes
- **Production-ready** - Preview, dry-run, and rollback support

**The workflow:**
1. Edit your Python models
2. Run `pynext db migrate -m "description"`
3. Review the generated migration
4. Run `pynext db upgrade`
5. Commit everything to git

**Next steps:**
- [DATABASE.md](./DATABASE.md) - Core database concepts
- [POSTGRES.md](./POSTGRES.md) - PostgreSQL-specific features
- [RELIABILITY.md](./RELIABILITY.md) - Production fault tolerance
