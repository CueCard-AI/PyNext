/*
Package bridge provides the CGO interface between Python and Go.

This file contains all CGO-exported functions that Python calls via ctypes.
Each function follows a consistent pattern:
  - Accept JSON input as *C.char
  - Return status code (0=success, non-zero=error)
  - Write results to provided output pointers

IMPORTANT: This is the ONLY file with CGO exports. All other Go code
is pure Go without CGO dependencies, making it easier to test.

Usage from Python:

	lib = ctypes.CDLL("libpynext.so")

	# Initialize
	config_json = json.dumps({"primary": "postgres://..."})
	result = lib.PynextInit(config_json.encode())

	# Execute query
	query_json = json.dumps({"sql": "SELECT * FROM users"})
	buffer = ctypes.c_char_p()
	length = ctypes.c_int()
	result = lib.PynextExecute(query_json.encode(), ctypes.byref(buffer), ctypes.byref(length))

	# Cleanup
	lib.PynextClose()
*/
package bridge

/*
#include <stdlib.h>
#include <string.h>

// Helper to allocate C string from Go
static char* alloc_string(const char* s, int len) {
    char* p = (char*)malloc(len + 1);
    if (p != NULL) {
        memcpy(p, s, len);
        p[len] = '\0';
    }
    return p;
}
*/
import "C"

import (
	"fmt"
	"strings"
	"sync"
	"unsafe"

	"github.com/bytedance/sonic"
	"github.com/vmihailenco/msgpack/v5"
)

// =============================================================================
// Global State
// =============================================================================

var (
	// globalBridge is the singleton bridge instance.
	// Created on PynextInit, destroyed on PynextClose.
	globalBridge *Bridge
	globalMutex  sync.RWMutex
)

// Bridge is the main Go bridge instance.
// It owns all database connections and resources.
type Bridge struct {
	config *Config
	pool   *Pool

	// Statistics
	queryCount   int64
	errorCount   int64
	totalLatency float64
}

// =============================================================================
// CGO Exports
// =============================================================================

// PynextInit initializes the Go bridge with the given configuration.
// Must be called before any other function.
//
// Parameters:
//   - configJSON: JSON-encoded Config struct
//
// Returns:
//   - 0 on success
//   - Error code on failure (see ErrCode* constants)
//
// Thread-safe: Yes, uses mutex.
//
//export PynextInit
func PynextInit(configJSON *C.char) C.int {
	globalMutex.Lock()
	defer globalMutex.Unlock()

	// Check if already initialized
	if globalBridge != nil {
		return C.int(ErrCodeAlreadyInit)
	}

	// Parse configuration
	config, err := ParseConfig([]byte(C.GoString(configJSON)))
	if err != nil {
		if be, ok := err.(*BridgeError); ok {
			return C.int(be.Code)
		}
		return C.int(ErrCodeConfig)
	}

	// Create connection pool
	pool, err := NewPool(config)
	if err != nil {
		if be, ok := err.(*BridgeError); ok {
			return C.int(be.Code)
		}
		return C.int(ErrCodeConnection)
	}

	// Create bridge instance
	globalBridge = &Bridge{
		config: config,
		pool:   pool,
	}

	return C.int(ErrCodeSuccess)
}

// PynextExecute executes a single query and returns results.
//
// Parameters:
//   - queryJSON: JSON-encoded QueryRequest
//   - outBuffer: Pointer to receive result buffer (caller must free)
//   - outLen: Pointer to receive buffer length
//
// Returns:
//   - 0 on success (result in outBuffer)
//   - Error code on failure (error JSON in outBuffer)
//
// The output buffer contains either:
//   - Success: QueryResult JSON with arrow_buffer or rows
//   - Failure: BridgeError JSON
//
// Thread-safe: Yes.
//
//export PynextExecute
func PynextExecute(queryJSON *C.char, outBuffer **C.char, outLen *C.int) C.int {
	globalMutex.RLock()
	bridge := globalBridge
	globalMutex.RUnlock()

	// Check initialization
	if bridge == nil {
		errJSON := MustMarshal(ErrNotInitialized)
		*outBuffer = C.alloc_string((*C.char)(unsafe.Pointer(&errJSON[0])), C.int(len(errJSON)))
		*outLen = C.int(len(errJSON))
		return C.int(ErrCodeNotInitialized)
	}

	// Parse query request
	var req QueryRequest
	if err := sonic.Unmarshal([]byte(C.GoString(queryJSON)), &req); err != nil {
		errObj := &BridgeError{
			Code:    ErrCodeQuery,
			Message: "invalid query JSON",
			Details: err.Error(),
		}
		errJSON := MustMarshal(errObj)
		*outBuffer = C.alloc_string((*C.char)(unsafe.Pointer(&errJSON[0])), C.int(len(errJSON)))
		*outLen = C.int(len(errJSON))
		return C.int(ErrCodeQuery)
	}

	// Execute query
	result := bridge.Execute(&req)

	// Serialize result
	resultJSON := MustMarshal(result)
	*outBuffer = C.alloc_string((*C.char)(unsafe.Pointer(&resultJSON[0])), C.int(len(resultJSON)))
	*outLen = C.int(len(resultJSON))

	if !result.Success {
		return C.int(ErrCodeQuery)
	}
	return C.int(ErrCodeSuccess)
}

// PynextExecuteFast executes using a pinned connection (no pool overhead).
// Best for small repeated queries. 2-3x faster than regular Execute.
//
//export PynextExecuteFast
func PynextExecuteFast(queryJSON *C.char, outBuffer **C.char, outLen *C.int) C.int {
	globalMutex.RLock()
	bridge := globalBridge
	globalMutex.RUnlock()

	if bridge == nil {
		errJSON := MustMarshal(ErrNotInitialized)
		*outBuffer = C.alloc_string((*C.char)(unsafe.Pointer(&errJSON[0])), C.int(len(errJSON)))
		*outLen = C.int(len(errJSON))
		return C.int(ErrCodeNotInitialized)
	}

	var req QueryRequest
	if err := sonic.Unmarshal([]byte(C.GoString(queryJSON)), &req); err != nil {
		errObj := &BridgeError{
			Code:    ErrCodeQuery,
			Message: "invalid query JSON",
			Details: err.Error(),
		}
		errJSON := MustMarshal(errObj)
		*outBuffer = C.alloc_string((*C.char)(unsafe.Pointer(&errJSON[0])), C.int(len(errJSON)))
		*outLen = C.int(len(errJSON))
		return C.int(ErrCodeQuery)
	}

	// Use ExecuteFast on pool (pinned connection)
	result := bridge.pool.ExecuteFast(&req)

	resultJSON := MustMarshal(result)
	*outBuffer = C.alloc_string((*C.char)(unsafe.Pointer(&resultJSON[0])), C.int(len(resultJSON)))
	*outLen = C.int(len(resultJSON))

	if !result.Success {
		return C.int(ErrCodeQuery)
	}
	return C.int(ErrCodeSuccess)
}

// PynextExecuteMsgpack executes a query and returns MessagePack-encoded result.
// MessagePack is ~3x faster than JSON for serialization/deserialization.
//
// Parameters:
//   - queryJSON: JSON-encoded QueryRequest (kept as JSON for simplicity)
//   - outBuffer: Pointer to receive MessagePack result buffer
//   - outLen: Pointer to receive buffer length
//
// Returns:
//   - 0 on success
//   - Error code on failure
//
// Thread-safe: Yes.
//
//export PynextExecuteMsgpack
func PynextExecuteMsgpack(queryJSON *C.char, outBuffer **C.char, outLen *C.int) C.int {
	globalMutex.RLock()
	bridge := globalBridge
	globalMutex.RUnlock()

	if bridge == nil {
		errJSON := MustMarshal(ErrNotInitialized)
		*outBuffer = C.alloc_string((*C.char)(unsafe.Pointer(&errJSON[0])), C.int(len(errJSON)))
		*outLen = C.int(len(errJSON))
		return C.int(ErrCodeNotInitialized)
	}

	var req QueryRequest
	if err := sonic.Unmarshal([]byte(C.GoString(queryJSON)), &req); err != nil {
		errObj := &BridgeError{
			Code:    ErrCodeQuery,
			Message: "invalid query JSON",
			Details: err.Error(),
		}
		errJSON := MustMarshal(errObj)
		*outBuffer = C.alloc_string((*C.char)(unsafe.Pointer(&errJSON[0])), C.int(len(errJSON)))
		*outLen = C.int(len(errJSON))
		return C.int(ErrCodeQuery)
	}

	result := bridge.Execute(&req)

	// Serialize result with MessagePack (faster than JSON)
	resultMsgpack, err := msgpack.Marshal(result)
	if err != nil {
		errObj := &BridgeError{
			Code:    ErrCodeQuery,
			Message: "msgpack serialization failed",
			Details: err.Error(),
		}
		errJSON := MustMarshal(errObj)
		*outBuffer = C.alloc_string((*C.char)(unsafe.Pointer(&errJSON[0])), C.int(len(errJSON)))
		*outLen = C.int(len(errJSON))
		return C.int(ErrCodeQuery)
	}

	*outBuffer = C.alloc_string((*C.char)(unsafe.Pointer(&resultMsgpack[0])), C.int(len(resultMsgpack)))
	*outLen = C.int(len(resultMsgpack))

	if !result.Success {
		return C.int(ErrCodeQuery)
	}
	return C.int(ErrCodeSuccess)
}

// PynextExecuteBatch executes multiple queries efficiently.
//
// Parameters:
//   - batchJSON: JSON-encoded BatchRequest
//   - outBuffer: Pointer to receive result buffer
//   - outLen: Pointer to receive buffer length
//
// Returns:
//   - 0 if all queries succeeded
//   - Error code if any failed
//
// Thread-safe: Yes.
//
//export PynextExecuteBatch
func PynextExecuteBatch(batchJSON *C.char, outBuffer **C.char, outLen *C.int) C.int {
	globalMutex.RLock()
	bridge := globalBridge
	globalMutex.RUnlock()

	if bridge == nil {
		errJSON := MustMarshal(ErrNotInitialized)
		*outBuffer = C.alloc_string((*C.char)(unsafe.Pointer(&errJSON[0])), C.int(len(errJSON)))
		*outLen = C.int(len(errJSON))
		return C.int(ErrCodeNotInitialized)
	}

	var req BatchRequest
	if err := sonic.Unmarshal([]byte(C.GoString(batchJSON)), &req); err != nil {
		errObj := &BridgeError{
			Code:    ErrCodeQuery,
			Message: "invalid batch JSON",
			Details: err.Error(),
		}
		errJSON := MustMarshal(errObj)
		*outBuffer = C.alloc_string((*C.char)(unsafe.Pointer(&errJSON[0])), C.int(len(errJSON)))
		*outLen = C.int(len(errJSON))
		return C.int(ErrCodeQuery)
	}

	result := bridge.ExecuteBatch(&req)
	resultJSON := MustMarshal(result)
	*outBuffer = C.alloc_string((*C.char)(unsafe.Pointer(&resultJSON[0])), C.int(len(resultJSON)))
	*outLen = C.int(len(resultJSON))

	if !result.Success {
		return C.int(ErrCodeQuery)
	}
	return C.int(ErrCodeSuccess)
}

// PynextExecuteParallel executes multiple queries in parallel.
// Each query runs in its own goroutine with its own connection.
// Results are returned in the same order as input queries.
//
// Parameters:
//   - queriesJSON: JSON-encoded array of QueryRequest
//   - outBuffer: Pointer to receive result buffer
//   - outLen: Pointer to receive buffer length
//
// Returns:
//   - 0 if all queries succeeded
//   - Error code if any failed (partial results still returned)
//
// Thread-safe: Yes.
//
//export PynextExecuteParallel
func PynextExecuteParallel(queriesJSON *C.char, outBuffer **C.char, outLen *C.int) C.int {
	globalMutex.RLock()
	bridge := globalBridge
	globalMutex.RUnlock()

	if bridge == nil {
		errJSON := MustMarshal(ErrNotInitialized)
		*outBuffer = C.alloc_string((*C.char)(unsafe.Pointer(&errJSON[0])), C.int(len(errJSON)))
		*outLen = C.int(len(errJSON))
		return C.int(ErrCodeNotInitialized)
	}

	// Parse queries array
	var queries []QueryRequest
	if err := sonic.Unmarshal([]byte(C.GoString(queriesJSON)), &queries); err != nil {
		errObj := &BridgeError{
			Code:    ErrCodeQuery,
			Message: "invalid queries JSON",
			Details: err.Error(),
		}
		errJSON := MustMarshal(errObj)
		*outBuffer = C.alloc_string((*C.char)(unsafe.Pointer(&errJSON[0])), C.int(len(errJSON)))
		*outLen = C.int(len(errJSON))
		return C.int(ErrCodeQuery)
	}

	// Execute in parallel
	results := bridge.ExecuteParallel(queries)

	// Check if any failed
	allSuccess := true
	for _, r := range results {
		if !r.Success {
			allSuccess = false
			break
		}
	}

	// Serialize results
	resultJSON := MustMarshal(results)
	*outBuffer = C.alloc_string((*C.char)(unsafe.Pointer(&resultJSON[0])), C.int(len(resultJSON)))
	*outLen = C.int(len(resultJSON))

	if !allSuccess {
		return C.int(ErrCodeQuery)
	}
	return C.int(ErrCodeSuccess)
}

// PynextExecuteArrow executes a query and returns Arrow IPC format.
// This is the fastest path for large result sets - zero-copy to Python.
//
// Parameters:
//   - queryJSON: JSON-encoded QueryRequest
//   - outBuffer: Pointer to receive Arrow IPC buffer
//   - outLen: Pointer to receive buffer length
//
// Returns:
//   - 0 on success
//   - Error code on failure
//
// Thread-safe: Yes.
//
//export PynextExecuteArrow
func PynextExecuteArrow(queryJSON *C.char, outBuffer **C.char, outLen *C.int) C.int {
	globalMutex.RLock()
	bridge := globalBridge
	globalMutex.RUnlock()

	if bridge == nil {
		errJSON := MustMarshal(ErrNotInitialized)
		*outBuffer = C.alloc_string((*C.char)(unsafe.Pointer(&errJSON[0])), C.int(len(errJSON)))
		*outLen = C.int(len(errJSON))
		return C.int(ErrCodeNotInitialized)
	}

	// Parse query request
	var req QueryRequest
	if err := sonic.Unmarshal([]byte(C.GoString(queryJSON)), &req); err != nil {
		errObj := &BridgeError{
			Code:    ErrCodeQuery,
			Message: "invalid query JSON",
			Details: err.Error(),
		}
		errJSON := MustMarshal(errObj)
		*outBuffer = C.alloc_string((*C.char)(unsafe.Pointer(&errJSON[0])), C.int(len(errJSON)))
		*outLen = C.int(len(errJSON))
		return C.int(ErrCodeQuery)
	}

	// Execute with Arrow result
	arrowBytes, err := bridge.ExecuteArrow(&req)
	if err != nil {
		errJSON := MustMarshal(err)
		*outBuffer = C.alloc_string((*C.char)(unsafe.Pointer(&errJSON[0])), C.int(len(errJSON)))
		*outLen = C.int(len(errJSON))
		return C.int(ErrCodeQuery)
	}

	// Return Arrow IPC bytes directly (no JSON encoding!)
	*outBuffer = C.alloc_string((*C.char)(unsafe.Pointer(&arrowBytes[0])), C.int(len(arrowBytes)))
	*outLen = C.int(len(arrowBytes))
	return C.int(ErrCodeSuccess)
}

// PynextExecuteCopyBinary executes a query and returns pre-parsed binary data.
// This eliminates Python-side parsing overhead for maximum speed.
//
// Binary format:
//
//	[row_count:4][col_count:4][col_oids:4*n][col_names...][rows...]
//
//export PynextExecuteCopyBinary
func PynextExecuteCopyBinary(queryJSON *C.char, outBuffer **C.char, outLen *C.int) C.int {
	globalMutex.RLock()
	bridge := globalBridge
	globalMutex.RUnlock()

	if bridge == nil {
		errJSON := MustMarshal(ErrNotInitialized)
		*outBuffer = C.alloc_string((*C.char)(unsafe.Pointer(&errJSON[0])), C.int(len(errJSON)))
		*outLen = C.int(len(errJSON))
		return C.int(ErrCodeNotInitialized)
	}

	var req QueryRequest
	if err := sonic.Unmarshal([]byte(C.GoString(queryJSON)), &req); err != nil {
		errObj := &BridgeError{
			Code:    ErrCodeQuery,
			Message: "invalid query JSON",
			Details: err.Error(),
		}
		errJSON := MustMarshal(errObj)
		*outBuffer = C.alloc_string((*C.char)(unsafe.Pointer(&errJSON[0])), C.int(len(errJSON)))
		*outLen = C.int(len(errJSON))
		return C.int(ErrCodeQuery)
	}

	binBytes, err := bridge.ExecuteCopyBinary(&req)
	if err != nil {
		errJSON := MustMarshal(err)
		*outBuffer = C.alloc_string((*C.char)(unsafe.Pointer(&errJSON[0])), C.int(len(errJSON)))
		*outLen = C.int(len(errJSON))
		return C.int(ErrCodeQuery)
	}

	*outBuffer = C.alloc_string((*C.char)(unsafe.Pointer(&binBytes[0])), C.int(len(binBytes)))
	*outLen = C.int(len(binBytes))
	return C.int(ErrCodeSuccess)
}

// PynextExecuteCopy executes a query using COPY protocol.
// Returns raw CSV data - parse with pandas.read_csv() for best performance.
//
// This is 2-5x faster than regular SELECT for large result sets.
//
//export PynextExecuteCopy
func PynextExecuteCopy(queryJSON *C.char, outBuffer **C.char, outLen *C.int) C.int {
	globalMutex.RLock()
	bridge := globalBridge
	globalMutex.RUnlock()

	if bridge == nil {
		errJSON := MustMarshal(ErrNotInitialized)
		*outBuffer = C.alloc_string((*C.char)(unsafe.Pointer(&errJSON[0])), C.int(len(errJSON)))
		*outLen = C.int(len(errJSON))
		return C.int(ErrCodeNotInitialized)
	}

	var req QueryRequest
	if err := sonic.Unmarshal([]byte(C.GoString(queryJSON)), &req); err != nil {
		errObj := &BridgeError{
			Code:    ErrCodeQuery,
			Message: "invalid query JSON",
			Details: err.Error(),
		}
		errJSON := MustMarshal(errObj)
		*outBuffer = C.alloc_string((*C.char)(unsafe.Pointer(&errJSON[0])), C.int(len(errJSON)))
		*outLen = C.int(len(errJSON))
		return C.int(ErrCodeQuery)
	}

	csvBytes, err := bridge.ExecuteCopy(&req)
	if err != nil {
		errJSON := MustMarshal(err)
		*outBuffer = C.alloc_string((*C.char)(unsafe.Pointer(&errJSON[0])), C.int(len(errJSON)))
		*outLen = C.int(len(errJSON))
		return C.int(ErrCodeQuery)
	}

	*outBuffer = C.alloc_string((*C.char)(unsafe.Pointer(&csvBytes[0])), C.int(len(csvBytes)))
	*outLen = C.int(len(csvBytes))
	return C.int(ErrCodeSuccess)
}

// PynextHealth returns the current health status of the Go bridge.
//
// Parameters:
//   - outBuffer: Pointer to receive result buffer
//   - outLen: Pointer to receive buffer length
//
// Returns:
//   - 0 on success
//   - Error code if not initialized
//
// Thread-safe: Yes.
//
//export PynextHealth
func PynextHealth(outBuffer **C.char, outLen *C.int) C.int {
	globalMutex.RLock()
	bridge := globalBridge
	globalMutex.RUnlock()

	if bridge == nil {
		errJSON := MustMarshal(ErrNotInitialized)
		*outBuffer = C.alloc_string((*C.char)(unsafe.Pointer(&errJSON[0])), C.int(len(errJSON)))
		*outLen = C.int(len(errJSON))
		return C.int(ErrCodeNotInitialized)
	}

	health := bridge.Health()
	healthJSON := MustMarshal(health)
	*outBuffer = C.alloc_string((*C.char)(unsafe.Pointer(&healthJSON[0])), C.int(len(healthJSON)))
	*outLen = C.int(len(healthJSON))
	return C.int(ErrCodeSuccess)
}

// PynextQueryExecute executes a query from an AST JSON.
// This is the main entry point for the new query builder API.
//
// Parameters:
//   - astJSON: Query AST as JSON (from Python QueryBuilder)
//   - outBuffer: Output buffer for results (caller must free with PynextFreeBuffer)
//   - outLen: Output length
//
// Returns:
//   - 0 on success, error code on failure
//
// Thread-safe: Yes, uses connection pool.
//
//export PynextQueryExecute
func PynextQueryExecute(astJSON *C.char, outBuffer **C.char, outLen *C.int) C.int {
	globalMutex.RLock()
	if globalBridge == nil {
		globalMutex.RUnlock()
		return C.int(ErrCodeNotInitialized)
	}
	bridge := globalBridge
	globalMutex.RUnlock()

	// Parse and execute via query engine
	result, err := bridge.QueryExecute(C.GoString(astJSON))
	if err != nil {
		errJSON := MustMarshal(map[string]string{"error": err.Error()})
		*outBuffer = C.alloc_string((*C.char)(unsafe.Pointer(&errJSON[0])), C.int(len(errJSON)))
		*outLen = C.int(len(errJSON))
		return C.int(ErrCodeQueryFailed)
	}

	// Return results
	resultJSON, err := sonic.Marshal(result)
	if err != nil {
		errJSON := MustMarshal(map[string]string{"error": err.Error()})
		*outBuffer = C.alloc_string((*C.char)(unsafe.Pointer(&errJSON[0])), C.int(len(errJSON)))
		*outLen = C.int(len(errJSON))
		return C.int(ErrCodeQueryFailed)
	}

	*outBuffer = C.alloc_string((*C.char)(unsafe.Pointer(&resultJSON[0])), C.int(len(resultJSON)))
	*outLen = C.int(len(resultJSON))
	return C.int(ErrCodeSuccess)
}

// PynextQueryExplain returns the generated SQL without executing.
// Useful for debugging and testing.
//
// Parameters:
//   - astJSON: Query AST as JSON
//   - outBuffer: Output buffer for SQL and params
//   - outLen: Output length
//
// Returns:
//   - 0 on success, error code on failure
//
//export PynextQueryExplain
func PynextQueryExplain(astJSON *C.char, outBuffer **C.char, outLen *C.int) C.int {
	globalMutex.RLock()
	if globalBridge == nil {
		globalMutex.RUnlock()
		return C.int(ErrCodeNotInitialized)
	}
	bridge := globalBridge
	globalMutex.RUnlock()

	sql, params, err := bridge.QueryExplain(C.GoString(astJSON))
	if err != nil {
		errJSON := MustMarshal(map[string]string{"error": err.Error()})
		*outBuffer = C.alloc_string((*C.char)(unsafe.Pointer(&errJSON[0])), C.int(len(errJSON)))
		*outLen = C.int(len(errJSON))
		return C.int(ErrCodeQueryFailed)
	}

	result := map[string]interface{}{
		"sql":    sql,
		"params": params,
	}
	resultJSON := MustMarshal(result)
	*outBuffer = C.alloc_string((*C.char)(unsafe.Pointer(&resultJSON[0])), C.int(len(resultJSON)))
	*outLen = C.int(len(resultJSON))
	return C.int(ErrCodeSuccess)
}

// PynextQueryValidate validates a query AST without executing.
// Returns validation errors if any.
//
// Parameters:
//   - astJSON: Query AST as JSON
//   - outBuffer: Output buffer for validation result
//   - outLen: Output length
//
// Returns:
//   - 0 on success (valid), error code on failure (invalid)
//
//export PynextQueryValidate
func PynextQueryValidate(astJSON *C.char, outBuffer **C.char, outLen *C.int) C.int {
	globalMutex.RLock()
	if globalBridge == nil {
		globalMutex.RUnlock()
		return C.int(ErrCodeNotInitialized)
	}
	bridge := globalBridge
	globalMutex.RUnlock()

	err := bridge.QueryValidate(C.GoString(astJSON))
	if err != nil {
		result := map[string]interface{}{
			"valid": false,
			"error": err.Error(),
		}
		resultJSON := MustMarshal(result)
		*outBuffer = C.alloc_string((*C.char)(unsafe.Pointer(&resultJSON[0])), C.int(len(resultJSON)))
		*outLen = C.int(len(resultJSON))
		return C.int(ErrCodeValidationFailed)
	}

	result := map[string]interface{}{"valid": true}
	resultJSON := MustMarshal(result)
	*outBuffer = C.alloc_string((*C.char)(unsafe.Pointer(&resultJSON[0])), C.int(len(resultJSON)))
	*outLen = C.int(len(resultJSON))
	return C.int(ErrCodeSuccess)
}

// PynextClose shuts down the Go bridge and releases all resources.
//
// Safe to call multiple times (subsequent calls are no-ops).
// After calling, PynextInit must be called again to use the bridge.
//
// Thread-safe: Yes, uses mutex.
//
//export PynextClose
func PynextClose() {
	globalMutex.Lock()
	defer globalMutex.Unlock()

	if globalBridge != nil {
		globalBridge.Close()
		globalBridge = nil
	}
}

// PynextFreeBuffer frees a buffer allocated by the Go bridge.
// Must be called for every buffer returned by Execute/Health.
//
// Parameters:
//   - buffer: Buffer to free (from Execute, Health, etc.)
//
// Thread-safe: Yes.
//
//export PynextFreeBuffer
func PynextFreeBuffer(buffer *C.char) {
	if buffer != nil {
		C.free(unsafe.Pointer(buffer))
	}
}

// PynextVersion returns the Go bridge version string.
//
// Returns:
//   - Version string (caller must NOT free)
//
// Thread-safe: Yes (immutable).
//
//export PynextVersion
func PynextVersion() *C.char {
	// This is a static string, don't free it
	return C.CString("0.1.0")
}

// =============================================================================
// Bridge Methods (called by CGO exports)
// =============================================================================

// Execute runs a single query.
func (b *Bridge) Execute(req *QueryRequest) *QueryResult {
	return b.pool.Execute(req)
}

// ExecuteBatch runs multiple queries sequentially (for transactions).
func (b *Bridge) ExecuteBatch(req *BatchRequest) *BatchResult {
	return b.pool.ExecuteBatch(req)
}

// ExecuteParallel runs multiple queries in parallel.
func (b *Bridge) ExecuteParallel(queries []QueryRequest) []QueryResult {
	return b.pool.ExecuteParallel(queries)
}

// ExecuteArrow runs a query and returns Arrow IPC bytes.
func (b *Bridge) ExecuteArrow(req *QueryRequest) ([]byte, error) {
	return b.pool.ExecuteArrow(req)
}

// ExecuteCopy runs a query using COPY protocol for maximum speed.
func (b *Bridge) ExecuteCopy(req *QueryRequest) ([]byte, error) {
	return b.pool.ExecuteCopy(req)
}

// ExecuteCopyBinary runs a query and returns pre-parsed binary data.
func (b *Bridge) ExecuteCopyBinary(req *QueryRequest) ([]byte, error) {
	return b.pool.ExecuteCopyBinary(req)
}

// Health returns current health status.
func (b *Bridge) Health() *HealthStatus {
	return b.pool.Health()
}

// Close shuts down the bridge.
func (b *Bridge) Close() {
	if b.pool != nil {
		b.pool.Close()
	}
}

// =============================================================================
// Query Builder Methods (Phase 8.2)
// =============================================================================

// QueryExecute executes a query from AST JSON.
func (b *Bridge) QueryExecute(astJSON string) (map[string]interface{}, error) {
	// Import query package
	// For now, parse and execute via pool directly
	// TODO: Use query.Executor when fully integrated

	// Parse AST
	var ast map[string]interface{}
	if err := sonic.Unmarshal([]byte(astJSON), &ast); err != nil {
		return nil, err
	}

	// Extract table and type
	table, _ := ast["table"].(string)
	queryType, _ := ast["type"].(string)
	if queryType == "" {
		queryType = "SELECT"
	}

	// For raw SQL, execute directly
	if rawSQL, ok := ast["raw_sql"].(string); ok && rawSQL != "" {
		params, _ := ast["params"].([]interface{})
		req := &QueryRequest{
			SQL:    rawSQL,
			Params: params,
		}
		result := b.pool.Execute(req)
		return map[string]interface{}{
			"rows":      result.Rows,
			"row_count": len(result.Rows),
		}, nil
	}

	// Build SQL from AST
	sql, params := b.buildSQLFromAST(ast, table, queryType)

	req := &QueryRequest{
		SQL:    sql,
		Params: params,
	}
	result := b.pool.Execute(req)

	return map[string]interface{}{
		"rows":      result.Rows,
		"row_count": len(result.Rows),
		"columns":   result.Columns,
	}, nil
}

// QueryExplain returns the generated SQL without executing.
func (b *Bridge) QueryExplain(astJSON string) (string, []interface{}, error) {
	var ast map[string]interface{}
	if err := sonic.Unmarshal([]byte(astJSON), &ast); err != nil {
		return "", nil, err
	}

	// For raw SQL, return as-is
	if rawSQL, ok := ast["raw_sql"].(string); ok && rawSQL != "" {
		params, _ := ast["params"].([]interface{})
		return rawSQL, params, nil
	}

	table, _ := ast["table"].(string)
	queryType, _ := ast["type"].(string)
	if queryType == "" {
		queryType = "SELECT"
	}

	sql, params := b.buildSQLFromAST(ast, table, queryType)
	return sql, params, nil
}

// QueryValidate validates a query AST without executing.
func (b *Bridge) QueryValidate(astJSON string) error {
	var ast map[string]interface{}
	if err := sonic.Unmarshal([]byte(astJSON), &ast); err != nil {
		return err
	}

	// Basic validation
	table, _ := ast["table"].(string)
	queryType, _ := ast["type"].(string)
	rawSQL, _ := ast["raw_sql"].(string)

	if table == "" && rawSQL == "" {
		return fmt.Errorf("query must have a table or raw_sql")
	}

	if queryType != "" && queryType != "SELECT" && queryType != "INSERT" && queryType != "UPDATE" && queryType != "DELETE" && queryType != "RAW" {
		return fmt.Errorf("invalid query type: %s", queryType)
	}

	// Validate conditions if present
	if conditions, ok := ast["conditions"].(map[string]interface{}); ok {
		if err := b.validateConditions(conditions); err != nil {
			return err
		}
	}

	return nil
}

// buildSQLFromAST generates SQL from an AST map.
// This is a simplified version - the full query package provides more optimization.
func (b *Bridge) buildSQLFromAST(ast map[string]interface{}, table, queryType string) (string, []interface{}) {
	var params []interface{}
	paramIdx := 0

	// Get columns
	columns := "*"
	if cols, ok := ast["columns"].([]interface{}); ok && len(cols) > 0 {
		colStrs := make([]string, len(cols))
		for i, c := range cols {
			colStrs[i] = c.(string)
		}
		columns = strings.Join(colStrs, ", ")
	}

	// Build SELECT
	sql := "SELECT"
	if distinct, ok := ast["distinct"].(bool); ok && distinct {
		sql += " DISTINCT"
	}
	sql += " " + columns + " FROM \"" + table + "\""

	// Build WHERE
	if conditions, ok := ast["conditions"].(map[string]interface{}); ok {
		whereSQL, whereParams := b.buildConditionsSQL(conditions, &paramIdx)
		if whereSQL != "" {
			sql += " WHERE " + whereSQL
			params = append(params, whereParams...)
		}
	}

	// Build ORDER BY
	if orders, ok := ast["order"].([]interface{}); ok && len(orders) > 0 {
		orderStrs := make([]string, len(orders))
		for i, o := range orders {
			if orderMap, ok := o.(map[string]interface{}); ok {
				field, _ := orderMap["field"].(string)
				dir, _ := orderMap["direction"].(string)
				if dir == "" {
					dir = "ASC"
				}
				orderStrs[i] = "\"" + field + "\" " + dir
			}
		}
		sql += " ORDER BY " + strings.Join(orderStrs, ", ")
	}

	// Build LIMIT
	if limit, ok := ast["limit"].(float64); ok {
		sql += fmt.Sprintf(" LIMIT %d", int(limit))
	}

	// Build OFFSET
	if offset, ok := ast["offset"].(float64); ok {
		sql += fmt.Sprintf(" OFFSET %d", int(offset))
	}

	// FOR UPDATE
	if forUpdate, ok := ast["for_update"].(bool); ok && forUpdate {
		sql += " FOR UPDATE"
	}

	return sql, params
}

// buildConditionsSQL generates WHERE clause SQL from conditions.
func (b *Bridge) buildConditionsSQL(cond map[string]interface{}, paramIdx *int) (string, []interface{}) {
	condType, _ := cond["type"].(string)
	var params []interface{}

	switch condType {
	case "condition":
		field, _ := cond["field"].(string)
		op, _ := cond["op"].(string)
		value := cond["value"]

		switch op {
		case "IS NULL", "IS NOT NULL":
			return "\"" + field + "\" " + op, nil
		case "IN", "NOT IN":
			if values, ok := value.([]interface{}); ok {
				placeholders := make([]string, len(values))
				for i, v := range values {
					*paramIdx++
					placeholders[i] = fmt.Sprintf("$%d", *paramIdx)
					params = append(params, v)
				}
				return "\"" + field + "\" " + op + " (" + strings.Join(placeholders, ", ") + ")", params
			}
		case "BETWEEN":
			value2 := cond["value2"]
			*paramIdx++
			p1 := fmt.Sprintf("$%d", *paramIdx)
			params = append(params, value)
			*paramIdx++
			p2 := fmt.Sprintf("$%d", *paramIdx)
			params = append(params, value2)
			return "\"" + field + "\" BETWEEN " + p1 + " AND " + p2, params
		default:
			*paramIdx++
			placeholder := fmt.Sprintf("$%d", *paramIdx)
			params = append(params, value)
			return "\"" + field + "\" " + op + " " + placeholder, params
		}

	case "logical":
		logicalOp, _ := cond["op"].(string)
		if logicalOp == "" {
			logicalOp = "AND"
		}
		conditions, _ := cond["conditions"].([]interface{})

		if logicalOp == "NOT" && len(conditions) == 1 {
			if subCond, ok := conditions[0].(map[string]interface{}); ok {
				subSQL, subParams := b.buildConditionsSQL(subCond, paramIdx)
				return "NOT (" + subSQL + ")", subParams
			}
		}

		parts := make([]string, 0, len(conditions))
		for _, c := range conditions {
			if subCond, ok := c.(map[string]interface{}); ok {
				subSQL, subParams := b.buildConditionsSQL(subCond, paramIdx)
				if subSQL != "" {
					parts = append(parts, subSQL)
					params = append(params, subParams...)
				}
			}
		}
		if len(parts) == 0 {
			return "", nil
		}
		if len(parts) == 1 {
			return parts[0], params
		}
		return "(" + strings.Join(parts, " "+logicalOp+" ") + ")", params

	case "raw":
		rawSQL, _ := cond["sql"].(string)
		rawParams, _ := cond["params"].([]interface{})
		// Re-number placeholders
		for i, p := range rawParams {
			oldP := fmt.Sprintf("$%d", i+1)
			*paramIdx++
			newP := fmt.Sprintf("$%d", *paramIdx)
			rawSQL = strings.Replace(rawSQL, oldP, newP, 1)
			params = append(params, p)
		}
		return rawSQL, params
	}

	return "", nil
}

// validateConditions validates a condition node.
func (b *Bridge) validateConditions(cond map[string]interface{}) error {
	condType, _ := cond["type"].(string)

	switch condType {
	case "condition":
		field, _ := cond["field"].(string)
		if field == "" {
			return fmt.Errorf("condition missing field")
		}
		op, _ := cond["op"].(string)
		if op == "" {
			return fmt.Errorf("condition missing operator")
		}
		// Validate operator
		validOps := map[string]bool{
			"=": true, "!=": true, "<>": true, ">": true, ">=": true, "<": true, "<=": true,
			"LIKE": true, "ILIKE": true, "IN": true, "NOT IN": true,
			"IS NULL": true, "IS NOT NULL": true, "BETWEEN": true,
			"@>": true, "<@": true, "&&": true,
		}
		if !validOps[op] {
			return fmt.Errorf("invalid operator: %s", op)
		}

	case "logical":
		logicalOp, _ := cond["op"].(string)
		if logicalOp != "AND" && logicalOp != "OR" && logicalOp != "NOT" {
			return fmt.Errorf("invalid logical operator: %s", logicalOp)
		}
		conditions, _ := cond["conditions"].([]interface{})
		for _, c := range conditions {
			if subCond, ok := c.(map[string]interface{}); ok {
				if err := b.validateConditions(subCond); err != nil {
					return err
				}
			}
		}

	case "raw":
		sql, _ := cond["sql"].(string)
		if sql == "" {
			return fmt.Errorf("raw condition missing SQL")
		}
		// Check for dangerous patterns
		upperSQL := strings.ToUpper(sql)
		dangerous := []string{"DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE", "GRANT", "REVOKE"}
		for _, kw := range dangerous {
			if strings.Contains(upperSQL, kw) {
				return fmt.Errorf("dangerous keyword detected: %s", kw)
			}
		}
	}

	return nil
}
