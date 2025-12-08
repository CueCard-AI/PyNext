/*
PyNext Go Bridge - Build Entry Point

This file serves as the entry point for building the CGO shared library.
It imports the bridge package to ensure all CGO exports are included.

Build Command:
    CGO_ENABLED=1 go build -buildmode=c-shared -o libpynext.so ./cmd/pynext/

Platform-Specific Outputs:
    - Linux:   libpynext.so
    - macOS:   libpynext.dylib
    - Windows: pynext.dll

The resulting shared library exports these functions:
    - PynextInit(configJSON) -> int
    - PynextExecute(queryJSON, &buffer, &len) -> int
    - PynextExecuteBatch(batchJSON, &buffer, &len) -> int
    - PynextHealth(&buffer, &len) -> int
    - PynextClose()
    - PynextFreeBuffer(buffer)
    - PynextVersion() -> string
*/
package main

import "C"

// Import bridge package to include CGO exports
import _ "github.com/pynext/pynext-go/pkg/bridge"

// main is required for c-shared build mode but is never called.
func main() {}

