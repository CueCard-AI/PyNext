# PyNext Testing Guide

A comprehensive guide to running tests in PyNext, designed for developers, CI systems, and AI assistants.

---

## WHO Should Read This

- **Developers**: Before committing code, run tests to catch regressions
- **CI/CD Pipelines**: Automated testing on every push/PR
- **AI Assistants/LLMs**: When helping debug or implement features, use these commands to verify changes

---

## WHAT This Guide Covers

- How to run the full test suite (26,000+ tests)
- How to run specific subsets of tests
- How to debug failing tests
- Test categories and what they cover
- Common testing patterns

---

## WHEN To Run Tests

| Scenario | Recommended Command |
|----------|---------------------|
| Before committing | `make test-quick` |
| Before opening a PR | `make test` (full suite) |
| Debugging a specific feature | `pytest tests/unit/... -v` |
| Checking transpiler changes | `make test-transpiler` |
| CI/CD pipelines | `make ci-test` or `make ci-test-full` |

---

## WHERE To Run Commands

All commands should be run from the **project root** directory:

```bash
cd /path/to/PyNext
```

---

## WHY Test Structure Matters

PyNext has a layered test structure:

```
tests/
├── unit/                    # Fast, isolated tests (~15k tests)
│   ├── transpiler/          # Python → JavaScript transpiler
│   ├── orm/                 # Database ORM
│   ├── router/              # URL routing
│   └── ...
├── integration/             # Tests with real dependencies (~8k tests)
│   ├── transpiler/          # Transpiler with real files
│   ├── db/                  # Real database tests
│   └── dataframe/           # DataFrame tests
├── e2e/                     # End-to-end browser tests (~500 tests)
│   ├── transpiler/          # Full transpilation + execution
│   └── browser/             # Playwright browser tests
└── benchmarks/              # Performance tests
```

---

## HOW To Run Tests

### Quick Start

```bash
# Run ALL tests (26k+, takes ~6 minutes)
make test

# Run tests quickly (skip database/E2E, ~2 minutes)
make test-quick

# Run only unit tests (fastest, ~1 minute)
make test-unit
```

### By Category

```bash
# Unit tests only
make test-unit
# or: pytest tests/unit -v

# Integration tests (requires database)
make test-integration
# or: pytest tests/integration -v

# E2E tests (requires Playwright)
make test-e2e
# or: pytest tests/e2e -v

# Transpiler tests (unit + integration)
make test-transpiler
# or: pytest tests/unit/transpiler tests/integration/transpiler -v
```

### By Specific File or Directory

```bash
# Run a specific test file
pytest tests/unit/transpiler/test_emitter.py -v

# Run a specific test directory
pytest tests/unit/transpiler/ -v

# Run tests matching a pattern
pytest -k "test_bundle" -v

# Run tests matching a class
pytest -k "TestBundleSize" -v

# Run a specific test function
pytest tests/unit/transpiler/test_emitter.py::test_basic_assignment -v
```

### With Coverage

```bash
# Run with coverage report
pytest --cov=pynext --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Debugging Failing Tests

```bash
# Show full traceback
pytest tests/path/to/test.py -v --tb=long

# Stop on first failure
pytest tests/ -x

# Drop into debugger on failure
pytest tests/path/to/test.py --pdb

# Show print statements
pytest tests/path/to/test.py -s

# Run with verbose output
pytest tests/path/to/test.py -vvv
```

---

## Test Dependencies

### Database Tests

Some tests require a PostgreSQL database. The Makefile handles this automatically:

```bash
# Start the test database (Docker)
make db-up

# Run tests that need database
make test-integration

# Stop the database
make db-down
```

Manual database setup:
```bash
# Ensure Docker is running
docker-compose -f docker-compose.test.yml up -d

# Verify database is ready
docker exec pynext-postgres-test pg_isready -U pynext
```

### Browser Tests (E2E)

Browser tests require Playwright:

```bash
# Install Playwright browsers
playwright install chromium --with-deps

# Run E2E tests
make test-e2e
```

### Go Bridge

Some tests require the Go bridge to be built:

```bash
# Build Go bridge (included in make install)
make install-go
```

---

## Common Test Patterns

### Running Transpiler Tests After Changes

After modifying the transpiler, run these in order:

```bash
# 1. Quick syntax check
python -c "from pynext.transpiler import transpile; print(transpile('x = 5'))"

# 2. Run transpiler unit tests
pytest tests/unit/transpiler/ -v

# 3. Run transpiler integration tests
pytest tests/integration/transpiler/ -v

# 4. Check bundle sizes didn't grow
make bundle
```

### Running Tests for a Specific Phase

Tests are organized by implementation phase:

```bash
# Phase 34 tests (Browser APIs)
pytest -k "test_34" -v

# DOM tests
pytest tests/unit/transpiler/test_341*.py -v

# CSS tests
pytest tests/unit/transpiler/test_342*.py -v
```

### Running Benchmark Tests

```bash
# Run all benchmarks
pytest tests/benchmarks/ -v

# Run specific benchmark
pytest tests/benchmarks/bench_build.py -v
```

---

## CI/CD Integration

### GitHub Actions

The CI workflow runs:

```yaml
- name: Run tests
  run: make ci-test
```

For full tests with database:

```yaml
- name: Start database
  run: make db-up

- name: Run full tests
  run: make ci-test-full
```

### Exit Codes

- `0`: All tests passed
- `1`: Some tests failed
- `2`: Test execution error
- `5`: No tests collected

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'pynext'"

```bash
# Install in development mode
pip install -e ".[dev]"
```

### "Database connection refused"

```bash
# Start the test database
make db-up

# Wait for it to be ready
sleep 5

# Retry tests
make test-integration
```

### "Playwright not found"

```bash
# Install Playwright
pip install playwright
playwright install chromium --with-deps
```

### Tests are slow

```bash
# Run without slow tests
pytest tests/ -v --ignore=tests/benchmarks --ignore=tests/e2e

# Or use the quick target
make test-quick
```

---

## Summary

| What You Want | Command |
|---------------|---------|
| Run all tests | `make test` |
| Quick check | `make test-quick` |
| Unit tests only | `make test-unit` |
| Specific file | `pytest tests/path/to/file.py -v` |
| Matching pattern | `pytest -k "pattern" -v` |
| With debugger | `pytest --pdb` |
| With coverage | `pytest --cov=pynext` |
| Transpiler only | `make test-transpiler` |
