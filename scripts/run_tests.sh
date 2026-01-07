#!/bin/bash
#
# PyNext Full Test Suite Runner
#
# This script automatically sets up all dependencies and runs the complete test suite:
# 1. Installs Python dev dependencies (numpy, polars, pandas, playwright, etc.)
# 2. Installs npm dependencies (esbuild)
# 3. Starts PostgreSQL Docker container
# 4. Installs Playwright browsers
# 5. Runs the full pytest suite
#
# Usage:
#   ./scripts/run_tests.sh           # Run all tests
#   ./scripts/run_tests.sh --quick   # Skip database tests
#   ./scripts/run_tests.sh --ci      # CI mode (stricter, no Docker auto-start)
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           PyNext Test Suite Runner                         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Parse arguments
QUICK_MODE=false
CI_MODE=false
PYTEST_ARGS=""

for arg in "$@"; do
    case $arg in
        --quick)
            QUICK_MODE=true
            ;;
        --ci)
            CI_MODE=true
            ;;
        *)
            PYTEST_ARGS="$PYTEST_ARGS $arg"
            ;;
    esac
done

# =============================================================================
# Step 1: Install Python dependencies
# =============================================================================
echo -e "${YELLOW}[1/5] Installing Python dependencies...${NC}"

if pip install -e ".[dev]" --quiet 2>/dev/null; then
    echo -e "${GREEN}  ✓ Python dependencies installed${NC}"
else
    echo -e "${RED}  ✗ Failed to install Python dependencies${NC}"
    echo "    Run: pip install -e '.[dev]'"
    exit 1
fi

# =============================================================================
# Step 2: Install npm dependencies (esbuild)
# =============================================================================
echo -e "${YELLOW}[2/5] Installing npm dependencies...${NC}"

if [ -f "package.json" ]; then
    if npm install --silent 2>/dev/null; then
        echo -e "${GREEN}  ✓ npm dependencies installed${NC}"
    else
        echo -e "${YELLOW}  ⚠ npm install failed (tests will use fallback)${NC}"
    fi
else
    echo -e "${YELLOW}  ⚠ No package.json found${NC}"
fi

# =============================================================================
# Step 3: Start PostgreSQL Docker container
# =============================================================================
echo -e "${YELLOW}[3/5] Starting PostgreSQL container...${NC}"

if [ "$QUICK_MODE" = true ]; then
    echo -e "${YELLOW}  ⚠ Quick mode - skipping database setup${NC}"
elif ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}  ⚠ Docker not available - database tests will be skipped${NC}"
elif ! docker info &> /dev/null; then
    echo -e "${YELLOW}  ⚠ Docker daemon not running - database tests will be skipped${NC}"
else
    # Check if container is already running
    if docker exec pynext-postgres-test pg_isready -U pynext &> /dev/null; then
        echo -e "${GREEN}  ✓ PostgreSQL container already running${NC}"
    else
        # Start container
        if docker-compose -f docker-compose.test.yml up -d 2>/dev/null; then
            echo -e "${BLUE}  ⏳ Waiting for PostgreSQL to be ready...${NC}"
            for i in {1..30}; do
                if docker exec pynext-postgres-test pg_isready -U pynext &> /dev/null; then
                    echo -e "${GREEN}  ✓ PostgreSQL container ready${NC}"
                    break
                fi
                sleep 1
            done
        else
            echo -e "${YELLOW}  ⚠ Failed to start PostgreSQL container${NC}"
        fi
    fi
    
    # Set environment variables
    export DATABASE_URL="postgresql://pynext:pynext@localhost:5433/pynext_test"
    export TEST_DATABASE_URL="postgresql://pynext:pynext@localhost:5433/pynext_test"
fi

# =============================================================================
# Step 4: Install Playwright browsers
# =============================================================================
echo -e "${YELLOW}[4/5] Installing Playwright browsers...${NC}"

if [ "$QUICK_MODE" = true ]; then
    echo -e "${YELLOW}  ⚠ Quick mode - skipping Playwright setup${NC}"
elif python -c "from playwright.sync_api import sync_playwright" 2>/dev/null; then
    if playwright install chromium --with-deps 2>/dev/null; then
        echo -e "${GREEN}  ✓ Playwright browsers installed${NC}"
    else
        echo -e "${YELLOW}  ⚠ Failed to install Playwright browsers${NC}"
    fi
else
    echo -e "${YELLOW}  ⚠ Playwright not installed - E2E tests will be skipped${NC}"
fi

# =============================================================================
# Step 5: Run tests
# =============================================================================
echo -e "${YELLOW}[5/5] Running test suite...${NC}"
echo ""

if [ "$QUICK_MODE" = true ]; then
    # Quick mode: skip database and E2E tests
    PYTEST_ARGS="--ignore=tests/integration/db --ignore=tests/integration/dataframe --ignore=tests/e2e $PYTEST_ARGS"
fi

if [ "$CI_MODE" = true ]; then
    # CI mode: stricter settings
    PYTEST_ARGS="-v --tb=short --strict-markers $PYTEST_ARGS"
fi

# Run pytest
echo -e "${BLUE}Running: pytest tests/ $PYTEST_ARGS${NC}"
echo ""

pytest tests/ $PYTEST_ARGS

# =============================================================================
# Summary
# =============================================================================
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           Test Suite Complete!                             ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"

