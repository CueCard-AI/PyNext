#!/bin/bash
#
# Build Go shared library for all supported platforms.
#
# This script is designed for CI/CD to build binaries for:
#   - linux/amd64
#   - linux/arm64
#   - darwin/amd64
#   - darwin/arm64
#   - windows/amd64
#
# Usage:
#   ./scripts/build-go-all.sh              # Build all platforms
#   ./scripts/build-go-all.sh --platform linux/amd64  # Build specific platform
#
# Requirements:
#   - Go 1.21+ with cross-compilation support
#   - For Windows: mingw-w64 (apt install mingw-w64)
#   - For ARM: appropriate cross-compilers
#
# Output:
#   pynext_go/_lib/
#   ├── linux_amd64/libpynext.so
#   ├── linux_arm64/libpynext.so
#   ├── darwin_amd64/libpynext.dylib
#   ├── darwin_arm64/libpynext.dylib
#   └── windows_amd64/pynext.dll

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

GO_DIR="$PROJECT_ROOT/go"
OUTPUT_DIR="$PROJECT_ROOT/pynext_go/_lib"

# All supported platforms
PLATFORMS=(
    "linux/amd64"
    "linux/arm64"
    "darwin/amd64"
    "darwin/arm64"
    "windows/amd64"
)

# Parse arguments
SPECIFIC_PLATFORM=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --platform)
            SPECIFIC_PLATFORM="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# If specific platform requested, only build that
if [ -n "$SPECIFIC_PLATFORM" ]; then
    PLATFORMS=("$SPECIFIC_PLATFORM")
fi

# Check Go
if ! command -v go &> /dev/null; then
    echo -e "${RED}Error: Go is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}Go version: $(go version)${NC}"

# Change to Go directory
cd "$GO_DIR"

# Download dependencies once
echo -e "${YELLOW}Downloading Go dependencies...${NC}"
go mod download

# Build function
build_platform() {
    local GOOS=$1
    local GOARCH=$2
    
    # Determine output file
    local LIB_NAME
    case $GOOS in
        darwin)
            LIB_NAME="libpynext.dylib"
            ;;
        windows)
            LIB_NAME="pynext.dll"
            ;;
        *)
            LIB_NAME="libpynext.so"
            ;;
    esac
    
    local PLATFORM_DIR="${GOOS}_${GOARCH}"
    local OUTPUT_PATH="$OUTPUT_DIR/$PLATFORM_DIR/$LIB_NAME"
    
    echo -e "${YELLOW}Building for $PLATFORM_DIR...${NC}"
    
    # Create output directory
    mkdir -p "$OUTPUT_DIR/$PLATFORM_DIR"
    
    # Set cross-compiler for Windows
    local CC=""
    if [ "$GOOS" = "windows" ] && [ "$GOARCH" = "amd64" ]; then
        CC="x86_64-w64-mingw32-gcc"
        if ! command -v $CC &> /dev/null; then
            echo -e "${RED}Warning: $CC not found, skipping Windows build${NC}"
            return 1
        fi
    fi
    
    # Build
    local BUILD_CMD="CGO_ENABLED=1 GOOS=$GOOS GOARCH=$GOARCH"
    if [ -n "$CC" ]; then
        BUILD_CMD="$BUILD_CMD CC=$CC"
    fi
    
    # Try to build (may fail for some cross-compilation targets)
    if eval "$BUILD_CMD go build -buildmode=c-shared -ldflags='-s -w' -o '$OUTPUT_PATH' ./cmd/pynext/" 2>/dev/null; then
        local SIZE=$(du -h "$OUTPUT_PATH" 2>/dev/null | cut -f1 || echo "?")
        echo -e "${GREEN}✓ $PLATFORM_DIR: $OUTPUT_PATH ($SIZE)${NC}"
        return 0
    else
        echo -e "${RED}✗ $PLATFORM_DIR: Build failed (may need cross-compiler)${NC}"
        return 1
    fi
}

# Track results
BUILT=0
FAILED=0

# Build each platform
for platform in "${PLATFORMS[@]}"; do
    GOOS=$(echo "$platform" | cut -d'/' -f1)
    GOARCH=$(echo "$platform" | cut -d'/' -f2)
    
    if build_platform "$GOOS" "$GOARCH"; then
        ((BUILT++))
    else
        ((FAILED++))
    fi
done

# Summary
echo ""
echo -e "${GREEN}Build Summary:${NC}"
echo -e "  Built: $BUILT"
echo -e "  Failed: $FAILED"

# List output files
echo ""
echo -e "${GREEN}Output files:${NC}"
find "$OUTPUT_DIR" -type f \( -name "*.so" -o -name "*.dylib" -o -name "*.dll" \) 2>/dev/null | while read f; do
    SIZE=$(du -h "$f" | cut -f1)
    echo "  $f ($SIZE)"
done

if [ $FAILED -gt 0 ]; then
    exit 1
fi

