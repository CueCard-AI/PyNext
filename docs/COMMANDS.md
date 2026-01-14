# PyNext Command Reference

Quick reference for all PyNext development commands. Run from project root.

---

## Quick Start

```bash
# First time setup
make install

# Run tests
make test

# Check bundle sizes
make bundle
```

---

## Testing

| Command | Description |
|---------|-------------|
| `make test` | Run full test suite (26k+ tests, ~6 min) |
| `make test-quick` | Skip database/E2E tests (~2 min) |
| `make test-unit` | Unit tests only (~1 min) |
| `make test-integration` | Integration tests (needs DB) |
| `make test-e2e` | E2E browser tests (needs Playwright) |
| `make test-transpiler` | Transpiler tests only |

### Pytest Commands

```bash
# Run specific file
pytest tests/unit/transpiler/test_emitter.py -v

# Run tests matching pattern
pytest -k "test_bundle" -v

# Stop on first failure
pytest tests/ -x

# Show print output
pytest tests/ -s

# With debugger
pytest tests/ --pdb

# With coverage
pytest tests/ --cov=pynext --cov-report=html
```

---

## Bundle Analysis

| Command | Description |
|---------|-------------|
| `make bundle` | Quick bundle size check |
| `make bundle-real-apps` | Real app bundle sizes |
| `make bundle-verbose` | Full analysis with breakdown |
| `make bundle-json` | JSON output for scripts |

### Python Alternative

```bash
python scripts/bundle_analyzer.py
python scripts/bundle_analyzer.py --real-apps
python scripts/bundle_analyzer.py --verbose
python scripts/bundle_analyzer.py --json
```

---

## Database (Testing)

| Command | Description |
|---------|-------------|
| `make db-up` | Start PostgreSQL container |
| `make db-down` | Stop PostgreSQL container |
| `make db-reset` | Stop and restart container |

---

## Code Quality

| Command | Description |
|---------|-------------|
| `make lint` | Run ruff + black check |
| `make format` | Auto-format code |

### Manual Commands

```bash
# Lint with ruff
ruff check pynext tests

# Check formatting
black --check pynext tests

# Format code
black pynext tests
```

---

## Installation

| Command | Description |
|---------|-------------|
| `make install` | Install all dependencies |
| `make install-go` | Build Go bridge only |

### Manual Installation

```bash
# Python dependencies
pip install -e ".[dev]"

# Node dependencies
npm install

# Playwright browsers
playwright install chromium --with-deps

# Go bridge
cd go && go build -buildmode=c-shared ...
```

---

## CI/CD

| Command | Description |
|---------|-------------|
| `make ci-test` | CI test suite (no DB) |
| `make ci-test-full` | Full CI suite (with DB) |

---

## Cleanup

| Command | Description |
|---------|-------------|
| `make clean` | Remove build artifacts |

---

## Development

### Transpiler Commands

```bash
# Quick transpile test
python -c "from pynext.transpiler import transpile; print(transpile('x = 5'))"

# Transpile with options
python -c "
from pynext.transpiler import transpile
code = '''
def hello():
    print('Hello')
'''
print(transpile(code, minify=True))
"
```

### Starting Development Server

```bash
# If you have a dev server configured
make dev
```

---

## Detailed Guides

- **Testing**: See `docs/TESTING.md` for comprehensive testing guide
- **Bundle Analysis**: See `docs/BUNDLE_ANALYSIS.md` for bundle optimization
- **Transpiler**: See `docs/internals/TRANSPILATION_LAYERS.md`

---

## Troubleshooting Quick Fixes

### Module not found

```bash
pip install -e ".[dev]"
```

### Database connection failed

```bash
make db-up
```

### Playwright not found

```bash
playwright install chromium --with-deps
```

### Go bridge not built

```bash
make install-go
```

### Bundle check failing

```bash
make bundle-verbose  # See which bundle is too large
```

### Tests are slow

```bash
make test-quick  # Skip slow tests
```

