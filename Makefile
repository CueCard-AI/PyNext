# PyNext Makefile
#
# Provides convenient commands for development and testing.
#
# Usage:
#   make install      # Install all dependencies
#   make test         # Run full test suite (with Docker)
#   make test-quick   # Run tests without database/E2E
#   make test-unit    # Run only unit tests
#   make db-up        # Start PostgreSQL container
#   make db-down      # Stop PostgreSQL container
#   make clean        # Clean build artifacts

.PHONY: install test test-quick test-unit test-integration test-e2e db-up db-down clean lint format help

# Default target
help:
	@echo "PyNext Development Commands"
	@echo ""
	@echo "  make install          Install all dependencies"
	@echo "  make test             Run full test suite (auto-starts Docker)"
	@echo "  make test-quick       Run tests without database/E2E"
	@echo "  make test-unit        Run only unit tests"
	@echo "  make test-integration Run only integration tests"
	@echo "  make test-e2e         Run only E2E tests"
	@echo "  make db-up            Start PostgreSQL container"
	@echo "  make db-down          Stop PostgreSQL container"
	@echo "  make lint             Run linters"
	@echo "  make format           Format code"
	@echo "  make clean            Clean build artifacts"

# =============================================================================
# Installation
# =============================================================================

install: install-go
	@echo "Installing Python dependencies..."
	pip install -e ".[dev]"
	@echo "Installing npm dependencies..."
	npm install
	@echo "Installing Playwright browsers..."
	playwright install chromium --with-deps || true
	@echo "Done!"

install-go:
	@echo "Building Go bridge..."
	@if command -v go >/dev/null 2>&1; then \
		cd go && go build -buildmode=c-shared -o ../pynext_go/_lib/$$(go env GOOS)_$$(go env GOARCH)/libpynext.$$(if [ "$$(go env GOOS)" = "darwin" ]; then echo "dylib"; else echo "so"; fi) ./cmd/pynext/main.go && \
		echo "  ✓ Go bridge built"; \
	else \
		echo "  ⚠ Go not installed, skipping Go bridge"; \
	fi

# =============================================================================
# Testing
# =============================================================================

test: db-up
	@echo "Running full test suite..."
	DATABASE_URL=postgresql://pynext:pynext@localhost:5433/pynext_test \
	TEST_DATABASE_URL=postgresql://pynext:pynext@localhost:5433/pynext_test \
	PYNEXT_TEST_DB_URL=postgresql://pynext:pynext@localhost:5433/pynext_test \
	pytest tests/ -v --tb=short

test-quick:
	@echo "Running quick test suite (no database/E2E)..."
	pytest tests/ -v --tb=short \
		--ignore=tests/integration/db \
		--ignore=tests/integration/dataframe \
		--ignore=tests/e2e

test-unit:
	@echo "Running unit tests..."
	pytest tests/unit -v --tb=short

test-integration: db-up
	@echo "Running integration tests..."
	DATABASE_URL=postgresql://pynext:pynext@localhost:5433/pynext_test \
	TEST_DATABASE_URL=postgresql://pynext:pynext@localhost:5433/pynext_test \
	PYNEXT_TEST_DB_URL=postgresql://pynext:pynext@localhost:5433/pynext_test \
	pytest tests/integration -v --tb=short

test-e2e:
	@echo "Running E2E tests..."
	pytest tests/e2e -v --tb=short

test-transpiler:
	@echo "Running transpiler tests..."
	pytest tests/unit/transpiler tests/integration/transpiler -v --tb=short

# =============================================================================
# Database
# =============================================================================

db-up:
	@echo "Starting PostgreSQL container..."
	@docker-compose -f docker-compose.test.yml up -d 2>/dev/null || true
	@echo "Waiting for PostgreSQL to be ready..."
	@for i in 1 2 3 4 5 6 7 8 9 10; do \
		docker exec pynext-postgres-test pg_isready -U pynext 2>/dev/null && break; \
		sleep 1; \
	done
	@echo "PostgreSQL ready!"

db-down:
	@echo "Stopping PostgreSQL container..."
	docker-compose -f docker-compose.test.yml down

db-reset: db-down db-up
	@echo "PostgreSQL reset complete!"

# =============================================================================
# Code Quality
# =============================================================================

lint:
	@echo "Running linters..."
	ruff check pynext tests
	black --check pynext tests

format:
	@echo "Formatting code..."
	black pynext tests
	ruff check --fix pynext tests

# =============================================================================
# Cleanup
# =============================================================================

clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "Clean complete!"

# =============================================================================
# CI Helpers
# =============================================================================

ci-test: install
	@echo "Running CI test suite..."
	pytest tests/ -v --tb=short --strict-markers \
		--ignore=tests/integration/db \
		--ignore=tests/integration/dataframe \
		--ignore=tests/e2e

ci-test-full: install db-up
	@echo "Running full CI test suite..."
	DATABASE_URL=postgresql://pynext:pynext@localhost:5433/pynext_test \
	TEST_DATABASE_URL=postgresql://pynext:pynext@localhost:5433/pynext_test \
	PYNEXT_TEST_DB_URL=postgresql://pynext:pynext@localhost:5433/pynext_test \
	pytest tests/ -v --tb=short --strict-markers

