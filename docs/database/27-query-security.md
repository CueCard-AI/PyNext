# Query Builder Security

The PyNext Query Builder is designed with security as a core principle. This document explains the multi-layer protection against SQL injection and other security threats.

## Security Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                        PYTHON LAYER                                 │
│  User Input → QueryBuilder → AST → Validation → JSON               │
│                                                                      │
│  Layer 1: Input Parsing - Type validation, operator whitelist       │
│  Layer 2: AST Validation - Structure checks, field validation       │
└────────────────────────────────────────────────────────────────────┘
                              ↓ JSON
┌────────────────────────────────────────────────────────────────────┐
│                          GO LAYER                                   │
│  JSON → Parse → Validate → Optimize → Generate SQL → Execute       │
│                                                                      │
│  Layer 3: Go Validation - Operator whitelist, keyword detection     │
│  Layer 4: SQL Generation - Parameterized queries only               │
│  Layer 5: Execution - Prepared statements                          │
└────────────────────────────────────────────────────────────────────┘
```

## Key Security Principles

### 1. All Values Are Parameters

**NEVER** interpolated into SQL:

```python
# ✓ Safe - value becomes $1 parameter
users = await User.q(("name", "=", user_input))

# ✓ Safe - values become parameters
users = await User.q(gt("age", user_age))

# ✓ Safe - parameterized
users = await User.q("name = $1", user_input)
```

The generated SQL always uses parameterized queries:

```sql
-- Generated SQL
SELECT * FROM "users" WHERE "name" = $1
-- Parameters: [user_input]
```

### 2. Operator Whitelist

Only known operators are allowed:

```python
# Allowed operators
VALID_OPERATORS = {
    "=", "!=", "<>",
    ">", ">=", "<", "<=",
    "LIKE", "ILIKE",
    "IN", "NOT IN",
    "IS NULL", "IS NOT NULL",
    "BETWEEN",
    "@>", "<@", "&&",  # PostgreSQL array/jsonb
}

# Invalid operators raise errors
User.q(("age", "??", 18))  # ValueError: Unknown operator
```

### 3. Field Name Validation

Field names are validated and quoted:

```python
# Field names are validated against a pattern
# Only alphanumeric, underscores, and dots allowed
VALID_FIELD = r'^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*$'

# ✓ Valid
User.q(("user_name", "=", "john"))
User.q(("users.id", "=", 1))

# ✗ Invalid - rejected
User.q(("1; DROP TABLE", "=", "x"))  # Validation error
```

All field names are quoted in generated SQL:

```sql
SELECT * FROM "users" WHERE "user_name" = $1
```

### 4. Dangerous Keyword Detection

SQL keywords that could indicate injection are detected:

```python
DANGEROUS_KEYWORDS = [
    "DROP", "DELETE", "TRUNCATE",
    "ALTER", "CREATE",
    "GRANT", "REVOKE",
    "INSERT", "UPDATE",  # In raw SQL
]

# Detected in raw SQL
User.sql("SELECT * FROM users; DROP TABLE users")
# Error: Dangerous keyword 'DROP' detected
```

### 5. Pattern Detection

Common injection patterns are blocked:

```python
# SQL comments
User.q("age > 18 -- comment")
# Warning: SQL comments detected

# Multiple statements
User.q("SELECT 1; DROP TABLE users")
# Error: Semicolon detected

# UNION injection
User.q("1 UNION SELECT password FROM users")
# Warning: UNION detected
```

## Strict Mode

Enable strict mode for production environments:

```python
from pynext_go import init

# Enable strict mode
init(
    primary="postgresql://...",
    strict_mode=True
)
```

In strict mode:
- All SQL strings are validated
- Unknown fields raise errors (if schema provided)
- Complexity limits enforced
- All queries logged with parameters

## Complexity Limits

Prevent denial-of-service via complex queries:

```python
# Default limits
MAX_CONDITIONS = 100    # Max conditions in WHERE clause
MAX_DEPTH = 10          # Max nesting depth
MAX_JOINS = 10          # Max JOIN clauses

# Exceeding limits raises error
User.q(
    and_(*[eq(f"field{i}", i) for i in range(150)])
)
# Error: Query too complex: 150 conditions (max: 100)
```

## Raw SQL Safety

When using escape hatches, parameterization is still enforced:

```python
# ✓ Safe - parameterized
users = await db.sql("SELECT * FROM users WHERE role = $1", "admin")

# ✓ Safe - parameters passed correctly
users = await User.sql(
    "SELECT * FROM users WHERE created_at > $1",
    datetime(2024, 1, 1)
)

# ⚠ Validated in strict mode
users = await User.sql("SELECT * FROM users")  # OK, no injection risk

# ✗ Blocked - dangerous patterns
users = await db.sql("DROP TABLE users")
# Error: Dangerous keyword 'DROP' detected
```

## Best Practices

### 1. Use Query Builder Over Raw SQL

```python
# Prefer this (automatic safety)
users = await User.q(
    and_(
        gt("age", 18),
        eq("status", "active")
    )
)

# Over this (requires care)
users = await db.sql(
    "SELECT * FROM users WHERE age > $1 AND status = $2",
    18, "active"
)
```

### 2. Always Validate User Input

```python
async def get_users(status: str):
    # Validate status is a known value
    if status not in ["active", "pending", "inactive"]:
        raise ValueError(f"Invalid status: {status}")
    
    return await User.q(eq("status", status))
```

### 3. Use Type Hints and Validation

```python
from pydantic import BaseModel, validator

class UserQuery(BaseModel):
    status: str
    min_age: int = 0
    
    @validator("status")
    def validate_status(cls, v):
        allowed = {"active", "pending", "inactive"}
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v

async def search_users(query: UserQuery):
    return await User.q(
        eq("status", query.status),
        gt("age", query.min_age)
    )
```

### 4. Enable Strict Mode in Production

```python
import os

init(
    primary=os.environ["DATABASE_URL"],
    strict_mode=os.environ.get("ENV") == "production"
)
```

### 5. Monitor Query Logs

All queries are logged with their parameters (not interpolated):

```
INFO: Query executed in 2.3ms
  SQL: SELECT * FROM "users" WHERE "age" > $1 AND "status" = $2
  Params: [18, "active"]
```

## Common Attack Prevention

### SQL Injection

```python
# Attack attempt
malicious_input = "'; DROP TABLE users; --"

# ✓ Safe with query builder
users = await User.q(eq("name", malicious_input))
# Generated: WHERE "name" = $1
# Params: ["'; DROP TABLE users; --"]

# ✓ Safe with parameterized SQL
users = await db.sql("SELECT * FROM users WHERE name = $1", malicious_input)
# name is literally "'; DROP TABLE users; --", not executed
```

### UNION Injection

```python
# Attack attempt
malicious_input = "1 UNION SELECT password FROM users"

# ✓ Safe - treated as literal value
users = await User.q(eq("id", malicious_input))
# WHERE "id" = '1 UNION SELECT password FROM users'
```

### Blind SQL Injection

```python
# Attack attempt
malicious_input = "1 AND 1=1"

# ✓ Safe - operator is fixed
users = await User.q(("id", "=", malicious_input))
# WHERE "id" = '1 AND 1=1'
# The AND is part of the string, not SQL
```

### Second-Order Injection

```python
# Even if malicious data is stored in DB
# Query builder always parameterizes

stored_name = "Robert'); DROP TABLE users; --"  # From DB
users = await User.q(eq("name", stored_name))
# Still parameterized, no injection
```

## Audit Trail

For compliance, enable query logging:

```python
import logging

# Enable SQL query logging
logging.getLogger("pynext.db").setLevel(logging.DEBUG)

# All queries are logged with:
# - Timestamp
# - SQL (parameterized)
# - Parameters (separate, not interpolated)
# - Duration
# - Source location
```

## Security Checklist

- [ ] Use query builder instead of raw SQL when possible
- [ ] Enable strict mode in production
- [ ] Validate user input at API boundary
- [ ] Use Pydantic or similar for input validation
- [ ] Never interpolate user input into SQL
- [ ] Monitor query logs for anomalies
- [ ] Keep pynext_go updated for security patches
- [ ] Use read-only replicas for reports
- [ ] Limit database user permissions
- [ ] Enable PostgreSQL query logging

