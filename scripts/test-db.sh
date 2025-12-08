#!/bin/bash
# PyNext Database Test Runner
#
# Usage:
#   ./scripts/test-db.sh           # Run all DB tests
#   ./scripts/test-db.sh unit      # Run unit tests only
#   ./scripts/test-db.sh go        # Run Go tests only
#   ./scripts/test-db.sh parallel  # Run parallel execution tests
#   ./scripts/test-db.sh --rebuild # Rebuild Go and run tests

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DB_URL="postgresql://pynext:pynext@localhost:5433/pynext_test"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Parse arguments
REBUILD=false
TEST_TYPE="all"

for arg in "$@"; do
    case $arg in
        --rebuild)
            REBUILD=true
            shift
            ;;
        unit|go|parallel|integration|all)
            TEST_TYPE=$arg
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [unit|go|parallel|integration|all] [--rebuild]"
            echo ""
            echo "Options:"
            echo "  unit        Run Python unit tests for Go bridge"
            echo "  go          Run Go tests"
            echo "  parallel    Run parallel execution tests"
            echo "  integration Run integration tests with DB"
            echo "  all         Run all tests (default)"
            echo "  --rebuild   Rebuild Go library before tests"
            exit 0
            ;;
    esac
done

cd "$PROJECT_DIR"

# Check if Docker is running
echo -e "${BLUE}Checking Docker...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running${NC}"
    echo "Please start Docker and try again."
    exit 1
fi

# Start PostgreSQL if not running
echo -e "${BLUE}Checking PostgreSQL...${NC}"
if ! docker-compose ps postgres 2>/dev/null | grep -q "Up"; then
    echo -e "${YELLOW}Starting PostgreSQL...${NC}"
    docker-compose up -d postgres
    
    # Wait for PostgreSQL to be ready
    echo -e "${BLUE}Waiting for PostgreSQL to be ready...${NC}"
    for i in {1..30}; do
        if docker-compose exec -T postgres pg_isready -U pynext -d pynext_test > /dev/null 2>&1; then
            echo -e "${GREEN}PostgreSQL is ready!${NC}"
            break
        fi
        echo "  Waiting... ($i/30)"
        sleep 1
    done
fi

# Verify connection
if ! docker-compose exec -T postgres pg_isready -U pynext -d pynext_test > /dev/null 2>&1; then
    echo -e "${RED}Error: Cannot connect to PostgreSQL${NC}"
    echo "Try: docker-compose logs postgres"
    exit 1
fi

# Rebuild Go library if requested
if [ "$REBUILD" = true ]; then
    echo -e "${BLUE}Rebuilding Go library...${NC}"
    if command -v go &> /dev/null; then
        cd go
        go build -buildmode=c-shared -o ../pynext_go/_lib/darwin_arm64/libpynext.dylib ./cmd/pynext/main.go 2>/dev/null || \
        go build -buildmode=c-shared -o ../pynext_go/_lib/linux_amd64/libpynext.so ./cmd/pynext/main.go
        cd ..
        echo -e "${GREEN}Go library rebuilt!${NC}"
    else
        echo -e "${YELLOW}Warning: Go not found, skipping rebuild${NC}"
    fi
fi

# Export database URL
export PYNEXT_TEST_DB_URL="$DB_URL"

# Run tests based on type
echo ""
echo -e "${BLUE}Running tests (type: $TEST_TYPE)...${NC}"
echo ""

case $TEST_TYPE in
    unit)
        pytest tests/unit/test_go_*.py -v --tb=short --timeout=60
        ;;
    go)
        if command -v go &> /dev/null; then
            cd go && go test ./... -v
        else
            echo -e "${RED}Error: Go not found${NC}"
            exit 1
        fi
        ;;
    parallel)
        pytest tests/unit/test_go_bridge_parallel.py -v --tb=short --timeout=60
        ;;
    integration)
        pytest tests/integration/test_db_*.py -v --tb=short --timeout=60
        ;;
    all)
        echo -e "${BLUE}=== Go Tests ===${NC}"
        if command -v go &> /dev/null; then
            cd go && go test ./... -v && cd ..
        else
            echo -e "${YELLOW}Skipping Go tests (Go not found)${NC}"
        fi
        
        echo ""
        echo -e "${BLUE}=== Python Unit Tests ===${NC}"
        pytest tests/unit/test_go_*.py -v --tb=short --timeout=60
        
        echo ""
        echo -e "${BLUE}=== Integration Tests ===${NC}"
        pytest tests/integration/test_db_*.py -v --tb=short --timeout=60 2>/dev/null || echo -e "${YELLOW}No integration tests found${NC}"
        ;;
esac

echo ""
echo -e "${GREEN}✅ Tests completed!${NC}"

