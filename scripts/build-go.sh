#!/bin/bash
#
# Build Go shared library for the current platform.
#
# Usage:
#   ./scripts/build-go.sh           # Build for current platform
#   ./scripts/build-go.sh --debug   # Build with debug symbols
#
# Requirements:
#   - Go 1.21+
#   - CGO enabled (default on most platforms)
#
# Output:
#   - Linux:   pynext_go/_lib/linux_amd64/libpynext.so (or arm64)
#   - macOS:   pynext_go/_lib/darwin_amd64/libpynext.dylib (or arm64)
#   - Windows: pynext_go/_lib/windows_amd64/pynext.dll

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Configuration
GO_DIR="$PROJECT_ROOT/go"
OUTPUT_DIR="$PROJECT_ROOT/pynext_go/_lib"
DEBUG=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --debug)
            DEBUG=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Check Go installation
if ! command -v go &> /dev/null; then
    echo -e "${RED}Error: Go is not installed${NC}"
    echo "Install Go from https://go.dev/dl/"
    exit 1
fi

GO_VERSION=$(go version | awk '{print $3}' | sed 's/go//')
echo -e "${GREEN}Go version: $GO_VERSION${NC}"

# Detect platform
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

# Normalize architecture
case $ARCH in
    x86_64|amd64)
        ARCH="amd64"
        ;;
    arm64|aarch64)
        ARCH="arm64"
        ;;
    *)
        echo -e "${RED}Unsupported architecture: $ARCH${NC}"
        exit 1
        ;;
esac

# Determine output file
case $OS in
    darwin)
        LIB_NAME="libpynext.dylib"
        ;;
    linux)
        LIB_NAME="libpynext.so"
        ;;
    mingw*|msys*|cygwin*)
        OS="windows"
        LIB_NAME="pynext.dll"
        ;;
    *)
        echo -e "${RED}Unsupported OS: $OS${NC}"
        exit 1
        ;;
esac

PLATFORM_DIR="${OS}_${ARCH}"
OUTPUT_PATH="$OUTPUT_DIR/$PLATFORM_DIR/$LIB_NAME"

echo -e "${GREEN}Building for: $PLATFORM_DIR${NC}"

# Create output directory
mkdir -p "$OUTPUT_DIR/$PLATFORM_DIR"

# Change to Go directory
cd "$GO_DIR"

# Download dependencies
echo -e "${YELLOW}Downloading Go dependencies...${NC}"
go mod download

# Build flags
BUILD_FLAGS="-buildmode=c-shared"
if [ "$DEBUG" = true ]; then
    BUILD_FLAGS="$BUILD_FLAGS -gcflags=all=-N -gcflags=all=-l"
    echo -e "${YELLOW}Building with debug symbols...${NC}"
else
    BUILD_FLAGS="$BUILD_FLAGS -ldflags=-s -ldflags=-w"
fi

# Build
echo -e "${YELLOW}Building shared library...${NC}"
CGO_ENABLED=1 go build $BUILD_FLAGS -o "$OUTPUT_PATH" ./cmd/pynext/

# Check result
if [ -f "$OUTPUT_PATH" ]; then
    SIZE=$(du -h "$OUTPUT_PATH" | cut -f1)
    echo -e "${GREEN}✓ Built successfully: $OUTPUT_PATH ($SIZE)${NC}"
    
    # Also copy header file if generated
    HEADER_PATH="${OUTPUT_PATH%.*}.h"
    if [ -f "$HEADER_PATH" ]; then
        echo -e "${GREEN}✓ Header file: $HEADER_PATH${NC}"
    fi
else
    echo -e "${RED}✗ Build failed${NC}"
    exit 1
fi

