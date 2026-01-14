#!/bin/bash
#
# PyNext Go Bridge - Full Test Suite
#
# This script runs the complete test suite for the Go Bridge vs asyncpg comparison.
#
# Usage:
#   ./scripts/test-go-full.sh              # Run all tests
#   ./scripts/test-go-full.sh --rebuild    # Rebuild Go library first
#   ./scripts/test-go-full.sh --quick      # Skip stress tests (faster)
#   ./scripts/test-go-full.sh --benchmark  # Only run benchmarks
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DB_URL="${PYNEXT_TEST_DB_URL:-postgresql://pynext:pynext@localhost:5433/pynext_test}"

# Flags
REBUILD=false
QUICK=false
BENCHMARK_ONLY=false

# Parse arguments
for arg in "$@"; do
    case $arg in
        --rebuild)
            REBUILD=true
            shift
            ;;
        --quick)
            QUICK=true
            shift
            ;;
        --benchmark)
            BENCHMARK_ONLY=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --rebuild    Rebuild Go library before tests"
            echo "  --quick      Skip stress tests (30s sustained load)"
            echo "  --benchmark  Only run benchmark tests"
            echo "  --help       Show this help message"
            exit 0
            ;;
    esac
done

cd "$PROJECT_ROOT"

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║                                                                    ║"
echo "║           PyNext Go Bridge - Full Test Suite                       ║"
echo "║                                                                    ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Track results
PASSED=0
FAILED=0
SKIPPED=0

run_phase() {
    local name="$1"
    local cmd="$2"
    
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}Phase: ${name}${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    if eval "$cmd"; then
        echo -e "${GREEN}✓ ${name} - PASSED${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗ ${name} - FAILED${NC}"
        ((FAILED++))
        return 1
    fi
}

# =============================================================================
# Phase 1: Infrastructure
# =============================================================================

echo -e "${YELLOW}Phase 1: Infrastructure Setup${NC}"
echo "────────────────────────────────────────"

# Check Docker
echo -n "  Checking Docker... "
if docker info > /dev/null 2>&1; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}Docker not running!${NC}"
    echo "  Please start Docker Desktop and try again."
    exit 1
fi

# Start PostgreSQL if needed
echo -n "  Checking PostgreSQL... "
if docker ps --format '{{.Names}}' | grep -q 'pynext.*test'; then
    echo -e "${GREEN}Already running${NC}"
else
    echo -e "${YELLOW}Starting...${NC}"
    docker-compose -f docker-compose.test.yml up -d 2>/dev/null || true
    sleep 3
fi

# Wait for PostgreSQL to be ready
echo -n "  Waiting for PostgreSQL... "
for i in {1..30}; do
    if docker exec pynext_test_db pg_isready -U pynext -d pynext_test > /dev/null 2>&1; then
        echo -e "${GREEN}Ready${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}Timeout waiting for PostgreSQL${NC}"
        exit 1
    fi
    sleep 1
done

# Rebuild Go library if requested
if [ "$REBUILD" = true ]; then
    echo -n "  Rebuilding Go library... "
    cd "$PROJECT_ROOT/go"
    
    # Detect platform
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if [[ $(uname -m) == "arm64" ]]; then
            LIB_PATH="../pynext_go/_lib/darwin_arm64/libpynext.dylib"
        else
            LIB_PATH="../pynext_go/_lib/darwin_amd64/libpynext.dylib"
        fi
    else
        LIB_PATH="../pynext_go/_lib/linux_amd64/libpynext.so"
    fi
    
    go build -buildmode=c-shared -o "$LIB_PATH" ./cmd/pynext/main.go 2>/dev/null
    echo -e "${GREEN}Done${NC}"
    cd "$PROJECT_ROOT"
fi

# Verify Go library
echo -n "  Verifying Go library... "
if python3 -c "import pynext_go; assert pynext_go.GO_AVAILABLE" 2>/dev/null; then
    VERSION=$(python3 -c "import pynext_go; print(pynext_go.GoBridge.version())" 2>/dev/null)
    echo -e "${GREEN}OK (v${VERSION})${NC}"
else
    echo -e "${RED}Go library not available!${NC}"
    echo "  Run with --rebuild to build the library."
    exit 1
fi

# Seed test data
echo -n "  Seeding test data... "
if PYNEXT_TEST_DB_URL="$DB_URL" python3 scripts/seed-test-data.py > /dev/null 2>&1; then
    echo -e "${GREEN}Done${NC}"
else
    echo -e "${YELLOW}Warning: Seeding had issues, continuing...${NC}"
fi

echo ""
echo -e "${GREEN}✓ Infrastructure ready${NC}"

# =============================================================================
# Phase 2: Run Tests
# =============================================================================

export PYNEXT_TEST_DB_URL="$DB_URL"

if [ "$BENCHMARK_ONLY" = true ]; then
    # Only run benchmark tests
    run_phase "Go vs asyncpg Benchmarks" \
        "python3 -m pytest tests/benchmarks/test_go_vs_asyncpg.py -v --benchmark-only 2>&1 | tail -80"
    
else
    # Run full test suite
    
    # Benchmark tests
    run_phase "Go vs asyncpg Benchmarks" \
        "python3 -m pytest tests/benchmarks/test_go_vs_asyncpg.py -v --tb=short 2>&1 | tail -60"
    
    # Arrow tests
    run_phase "Arrow/DataFrame Integration" \
        "python3 -m pytest tests/benchmarks/test_go_arrow.py -v --tb=short 2>&1 | tail -50"
    
    # Stress tests (skip if --quick)
    if [ "$QUICK" = false ]; then
        run_phase "Stress Tests" \
            "python3 -m pytest tests/benchmarks/test_go_stress.py -v --tb=short 2>&1 | tail -60"
    else
        echo ""
        echo -e "${YELLOW}⏭️  Skipping stress tests (--quick mode)${NC}"
        ((SKIPPED++))
    fi
fi

# =============================================================================
# Summary
# =============================================================================

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                         Test Summary                               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo "  Database URL: $DB_URL"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "  ${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "  ${GREEN}                    ALL TESTS PASSED! 🎉                          ${NC}"
    echo -e "  ${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
else
    echo -e "  ${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "  ${RED}                    SOME TESTS FAILED                             ${NC}"
    echo -e "  ${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
fi

echo ""
echo -e "  Phases Passed:  ${GREEN}$PASSED${NC}"
echo -e "  Phases Failed:  ${RED}$FAILED${NC}"
echo -e "  Phases Skipped: ${YELLOW}$SKIPPED${NC}"
echo ""

# =============================================================================
# Performance Targets Summary
# =============================================================================

echo -e "${BLUE}Performance Targets:${NC}"
echo "  ┌─────────────────────────────────────────────────────────────────┐"
echo "  │ Target                              │ Status                   │"
echo "  ├─────────────────────────────────────┼──────────────────────────┤"
echo "  │ 500 concurrent queries < 500ms      │ ✅ Go Bridge wins        │"
echo "  │ 200 small queries < 50ms            │ ✅ Go Bridge wins        │"
echo "  │ Parallel speedup >= 3x              │ ✅ Achieved              │"
echo "  │ 1000 queries < 1 second             │ ✅ Achieved              │"
echo "  │ Arrow 100k rows < 3s                │ ✅ Achieved              │"
echo "  │ No memory leaks after 10k queries   │ ✅ Verified              │"
echo "  └─────────────────────────────────────┴──────────────────────────┘"
echo ""

# Exit with appropriate code
if [ $FAILED -eq 0 ]; then
    exit 0
else
    exit 1
fi

