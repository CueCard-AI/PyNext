# Go Bridge Internals: Deep Technical Implementation Guide

This document explains the complete technical implementation of the Go Bridge, from the low-level CGO bindings to the high-level Python API. It's intended for developers who want to understand how everything works under the hood.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [The CGO Bridge Layer](#the-cgo-bridge-layer)
3. [Connection Pool Implementation](#connection-pool-implementation)
4. [Query Execution Pipeline](#query-execution-pipeline)
5. [Parallel Execution with Goroutines](#parallel-execution-with-goroutines)
6. [Serialization: JSON, MessagePack, and Arrow](#serialization-json-messagepack-and-arrow)
7. [The COPY Protocol](#the-copy-protocol)
8. [Python ctypes Integration](#python-ctypes-integration)
9. [Memory Management](#memory-management)
10. [Performance Optimizations](#performance-optimizations)
11. [Error Handling Across Boundaries](#error-handling-across-boundaries)

---

## Architecture Overview

The Go Bridge consists of three layers:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Python Layer                                  │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  pynext_go/__init__.py        pynext_go/bridge.py                 │  │
│  │  - Module-level API           - GoBridge class                    │  │
│  │  - init(), execute()          - ctypes bindings                   │  │
│  │  - batch(), close()           - Error translation                 │  │
│  │                               - QueryBatch, DeferredResult        │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                    │                                    │
│                                    │ ctypes FFI                         │
│                                    ▼                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                            CGO Layer                                    │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  go/pkg/bridge/bridge.go                                          │  │
│  │  - //export directives for C symbols                              │  │
│  │  - PynextInit, PynextExecute, PynextExecuteParallel, etc.         │  │
│  │  - C string ↔ Go string conversion                                │  │
│  │  - Memory allocation for return values                            │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                    │                                    │
│                                    │ Pure Go                            │
│                                    ▼                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                           Go Core Layer                                 │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  go/pkg/bridge/pool.go        go/pkg/bridge/types.go              │  │
│  │  - Connection pool (pgxpool)  - Config, QueryRequest, QueryResult │  │
│  │  - Execute, ExecuteParallel   - JSON/sonic serialization          │  │
│  │  - ExecuteCopy, ExecuteArrow                                      │  │
│  │                                                                    │  │
│  │  go/pkg/arrow/builder.go                                          │  │
│  │  - PostgreSQL → Arrow type mapping                                │  │
│  │  - Arrow IPC serialization                                        │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                    │                                    │
│                                    │ pgx driver                         │
│                                    ▼                                    │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                         PostgreSQL                                 │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## The CGO Bridge Layer

CGO (C-Go) allows Go code to be compiled as a C shared library that can be called from any language that supports C FFI, including Python via ctypes.

### How CGO Exports Work

In Go, you create exportable C functions using the `//export` directive:

```go
// go/pkg/bridge/bridge.go

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

//export PynextInit
func PynextInit(configJSON *C.char) C.int {
    // This function is now callable from C/Python
    goConfigStr := C.GoString(configJSON)  // Convert C string to Go string
    
    // ... initialization logic ...
    
    return C.int(0)  // Return C int
}
```

**Key Points:**

1. **The `import "C"` statement** - This special import enables CGO. The comment block immediately above it is treated as C code.

2. **`//export FunctionName`** - This directive must be directly above the function (no blank lines). It tells the Go compiler to expose this function as a C symbol.

3. **C types** - All parameters and return values must use C types (`*C.char`, `C.int`, etc.)

4. **String conversion** - `C.GoString()` converts C strings to Go, `C.CString()` goes the other way (but requires manual memory management).

### The Exported Functions

```go
// Initialization
//export PynextInit
func PynextInit(configJSON *C.char) C.int

//export PynextClose  
func PynextClose()

// Query execution
//export PynextExecute
func PynextExecute(queryJSON *C.char, outBuffer **C.char, outLen *C.int) C.int

//export PynextExecuteFast
func PynextExecuteFast(queryJSON *C.char, outBuffer **C.char, outLen *C.int) C.int

//export PynextExecuteParallel
func PynextExecuteParallel(queriesJSON *C.char, outBuffer **C.char, outLen *C.int) C.int

//export PynextExecuteCopy
func PynextExecuteCopy(queryJSON *C.char, outBuffer **C.char, outLen *C.int) C.int

//export PynextExecuteArrow
func PynextExecuteArrow(queryJSON *C.char, outBuffer **C.char, outLen *C.int) C.int

// Utility
//export PynextHealth
func PynextHealth(outBuffer **C.char, outLen *C.int) C.int

//export PynextFreeBuffer
func PynextFreeBuffer(buffer *C.char)

//export PynextVersion
func PynextVersion() *C.char
```

### Memory Allocation Pattern

The pattern for returning data to Python:

```go
//export PynextExecute
func PynextExecute(queryJSON *C.char, outBuffer **C.char, outLen *C.int) C.int {
    // 1. Parse input
    var req QueryRequest
    if err := sonic.Unmarshal([]byte(C.GoString(queryJSON)), &req); err != nil {
        // Handle error...
    }
    
    // 2. Execute query
    result := globalBridge.pool.Execute(&req)
    
    // 3. Serialize result to JSON
    resultJSON := MustMarshal(result)
    
    // 4. Allocate C memory and copy result
    // This memory must be freed by Python later!
    *outBuffer = C.alloc_string(
        (*C.char)(unsafe.Pointer(&resultJSON[0])),
        C.int(len(resultJSON)),
    )
    *outLen = C.int(len(resultJSON))
    
    return C.int(0)  // Success
}
```

**Why allocate in C?** Go's garbage collector might move or free Go-allocated memory. By allocating in C (via `malloc`), we ensure the memory remains stable until Python explicitly frees it.

---

## Connection Pool Implementation

The Go side uses `pgxpool` from the jackc/pgx library, which is one of the fastest PostgreSQL drivers.

### Pool Configuration

```go
// go/pkg/bridge/pool.go

func NewPool(config *Config) (*Pool, error) {
    // Parse connection string
    poolConfig, err := pgxpool.ParseConfig(config.Primary)
    if err != nil {
        return nil, err
    }
    
    // Configure pool size
    poolConfig.MinConns = int32(config.PoolMinSize)
    poolConfig.MaxConns = int32(config.PoolMaxSize)
    
    // Enable prepared statement caching
    // This caches query plans on the server, making repeated queries faster
    poolConfig.ConnConfig.DefaultQueryExecMode = pgx.QueryExecModeCacheStatement
    
    // Large statement cache (2048 unique queries)
    poolConfig.ConnConfig.StatementCacheCapacity = 2048
    
    // Create the pool
    pgPool, err := pgxpool.NewWithConfig(context.Background(), poolConfig)
    if err != nil {
        return nil, err
    }
    
    return &Pool{
        config:    config,
        primary:   pgPool,
        workerSem: make(chan struct{}, config.PoolMaxSize),
    }, nil
}
```

### The Pool Struct

```go
type Pool struct {
    config  *Config
    primary *pgxpool.Pool
    
    // Health tracking
    lastHealth    *HealthStatus
    healthMutex   sync.RWMutex
    
    // Statistics (atomic for lock-free reads)
    queryCount     atomic.Int64
    errorCount     atomic.Int64
    totalLatencyNs atomic.Int64
    
    // Prepared statement cache
    preparedStmts sync.Map  // map[string]bool
    
    // Worker pool for parallel queries
    workerSem chan struct{}
    
    // Lifecycle
    closed   atomic.Bool
    closeMux sync.Mutex
}
```

---

## Query Execution Pipeline

### Standard Execute

Here's what happens when you call `pynext_go.execute()`:

```
Python                          Go                              PostgreSQL
  │                              │                                   │
  │  execute(sql, params)        │                                   │
  │  ──────────────────────────▶ │                                   │
  │  JSON: {"sql": "...",        │                                   │
  │         "params": [...]}     │                                   │
  │                              │                                   │
  │                              │  1. Parse JSON request            │
  │                              │  2. Get connection from pool      │
  │                              │  3. Execute query ─────────────────▶
  │                              │                                   │
  │                              │  ◀───────────────── Rows returned │
  │                              │  4. Convert rows to [][]any       │
  │                              │  5. Serialize to JSON             │
  │                              │                                   │
  │  ◀────────────────────────── │                                   │
  │  JSON: {"rows": [...],       │                                   │
  │         "columns": [...]}    │                                   │
  │                              │                                   │
  │  Parse JSON to QueryResult   │                                   │
  │                              │                                   │
```

### Code Flow

```go
// go/pkg/bridge/pool.go

func (p *Pool) Execute(req *QueryRequest) *QueryResult {
    // 1. Check pool is open
    if p.closed.Load() {
        return &QueryResult{Success: false, Error: "pool is closed"}
    }

    start := time.Now()
    p.queryCount.Add(1)

    // 2. Set up timeout
    timeout := time.Duration(p.config.QueryTimeout) * time.Millisecond
    if req.TimeoutMs > 0 {
        timeout = time.Duration(req.TimeoutMs) * time.Millisecond
    }
    ctx, cancel := context.WithTimeout(context.Background(), timeout)
    defer cancel()

    // 3. Execute query (pgxpool handles connection acquisition)
    rows, err := p.primary.Query(ctx, req.SQL, req.Params...)
    if err != nil {
        p.errorCount.Add(1)
        return &QueryResult{
            Success:  false,
            Error:    err.Error(),
            Duration: float64(time.Since(start).Microseconds()) / 1000,
        }
    }
    defer rows.Close()

    // 4. Convert rows to result
    result := p.rowsToResult(rows, start)
    p.totalLatencyNs.Add(time.Since(start).Nanoseconds())

    return result
}

func (p *Pool) rowsToResult(rows pgx.Rows, start time.Time) *QueryResult {
    // Get column names
    fieldDescs := rows.FieldDescriptions()
    columns := make([]string, len(fieldDescs))
    for i, fd := range fieldDescs {
        columns[i] = string(fd.Name)
    }

    // Collect all rows
    var resultRows [][]any
    for rows.Next() {
        values, err := rows.Values()
        if err != nil {
            return &QueryResult{
                Success: false,
                Error:   err.Error(),
            }
        }
        resultRows = append(resultRows, values)
    }

    return &QueryResult{
        Success:  true,
        Columns:  columns,
        Rows:     resultRows,
        RowCount: len(resultRows),
        Duration: float64(time.Since(start).Microseconds()) / 1000,
    }
}
```

---

## Parallel Execution with Goroutines

This is where Go Bridge's main performance advantage comes from.

### The Problem with Python

Python's asyncio provides **concurrency** (handling many tasks) but not **parallelism** (running tasks simultaneously). Even with `asyncio.gather()`:

```python
# This looks parallel but isn't!
results = await asyncio.gather(
    conn.fetch("SELECT * FROM users"),
    conn.fetch("SELECT * FROM orders"),
    conn.fetch("SELECT * FROM products"),
)
```

asyncpg's connection is a single TCP socket. While waiting for one query's response, it can't send another query on the same connection. You'd need multiple connections, which requires pool management.

### The Go Solution

Go's goroutines are lightweight threads that can truly run in parallel:

```go
// go/pkg/bridge/pool.go

func (p *Pool) ExecuteParallel(requests []*QueryRequest) []*QueryResult {
    // Create result slice
    results := make([]*QueryResult, len(requests))
    
    // WaitGroup to track completion
    var wg sync.WaitGroup
    wg.Add(len(requests))
    
    // Launch each query in its own goroutine
    for i, req := range requests {
        go func(idx int, r *QueryRequest) {
            defer wg.Done()
            
            // Limit concurrency to pool size
            p.workerSem <- struct{}{}        // Acquire semaphore
            defer func() { <-p.workerSem }() // Release semaphore
            
            // Execute query (each goroutine gets its own connection!)
            results[idx] = p.Execute(r)
        }(i, req)
    }
    
    // Wait for all goroutines to complete
    wg.Wait()
    
    return results
}
```

### How Goroutines Achieve True Parallelism

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Go Runtime Scheduler                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                 │
│  │ goroutine 1 │    │ goroutine 2 │    │ goroutine 3 │                 │
│  │   Query 1   │    │   Query 2   │    │   Query 3   │                 │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘                 │
│         │                  │                  │                         │
│         ▼                  ▼                  ▼                         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                 │
│  │ Connection  │    │ Connection  │    │ Connection  │                 │
│  │     1       │    │     2       │    │     3       │                 │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘                 │
│         │                  │                  │                         │
│         └──────────────────┼──────────────────┘                         │
│                            │                                            │
│                            ▼                                            │
│                    ┌───────────────┐                                    │
│                    │  PostgreSQL   │                                    │
│                    │               │                                    │
│                    │  3 parallel   │                                    │
│                    │  connections  │                                    │
│                    └───────────────┘                                    │
│                                                                         │
│  Time for 3 queries: MAX(Q1, Q2, Q3) instead of Q1 + Q2 + Q3           │
└─────────────────────────────────────────────────────────────────────────┘
```

**Key Points:**

1. **Each goroutine gets its own connection** - pgxpool automatically manages this
2. **Goroutines run on OS threads** - Go's scheduler multiplexes goroutines onto threads
3. **No GIL** - Go doesn't have a Global Interpreter Lock
4. **Efficient memory** - Goroutines start with ~2KB stack (vs ~1MB for OS threads)

---

## Serialization: JSON, MessagePack, and Arrow

### JSON with sonic (Default)

We use bytedance/sonic for JSON serialization, which is 2-3x faster than Go's encoding/json:

```go
// go/pkg/bridge/types.go

import sonic "github.com/bytedance/sonic"

func MustMarshal(v any) []byte {
    data, err := sonic.Marshal(v)
    if err != nil {
        // This should never happen for our types
        panic(err)
    }
    return data
}

func ParseConfig(data []byte) (*Config, error) {
    var config Config
    if err := sonic.Unmarshal(data, &config); err != nil {
        return nil, err
    }
    return &config, nil
}
```

### Python Side: orjson

On the Python side, we use orjson which is written in Rust:

```python
# pynext_go/bridge.py

try:
    import orjson
    def json_loads(s):
        return orjson.loads(s)
    def json_dumps(obj):
        return orjson.dumps(obj)
except ImportError:
    import json
    def json_loads(s):
        return json.loads(s)
    def json_dumps(obj):
        return json.dumps(obj).encode("utf-8")
```

### Arrow IPC Format

For DataFrame operations, we use Apache Arrow's IPC format for zero-copy transfer:

```go
// go/pkg/arrow/builder.go

func BuildRecordBatch(columns []string, types []uint32, rows [][]any) (arrow.Record, error) {
    // 1. Build Arrow schema from PostgreSQL types
    fields := make([]arrow.Field, len(columns))
    for i, col := range columns {
        fields[i] = arrow.Field{
            Name: col,
            Type: pgTypeToArrow(types[i]),
        }
    }
    schema := arrow.NewSchema(fields, nil)
    
    // 2. Create builders for each column
    pool := memory.NewGoAllocator()
    builders := make([]array.Builder, len(columns))
    for i, field := range fields {
        builders[i] = array.NewBuilder(pool, field.Type)
    }
    
    // 3. Append values
    for _, row := range rows {
        for i, val := range row {
            appendValue(builders[i], val)
        }
    }
    
    // 4. Build arrays and create record batch
    arrays := make([]arrow.Array, len(builders))
    for i, b := range builders {
        arrays[i] = b.NewArray()
    }
    
    return array.NewRecord(schema, arrays, int64(len(rows))), nil
}

func SerializeIPC(record arrow.Record) ([]byte, error) {
    var buf bytes.Buffer
    writer := ipc.NewWriter(&buf, ipc.WithSchema(record.Schema()))
    
    if err := writer.Write(record); err != nil {
        return nil, err
    }
    if err := writer.Close(); err != nil {
        return nil, err
    }
    
    return buf.Bytes(), nil
}
```

### PostgreSQL OID to Arrow Type Mapping

```go
func pgTypeToArrow(oid uint32) arrow.DataType {
    switch oid {
    case pgtype.Int2OID:
        return arrow.PrimitiveTypes.Int16
    case pgtype.Int4OID:
        return arrow.PrimitiveTypes.Int32
    case pgtype.Int8OID:
        return arrow.PrimitiveTypes.Int64
    case pgtype.Float4OID:
        return arrow.PrimitiveTypes.Float32
    case pgtype.Float8OID:
        return arrow.PrimitiveTypes.Float64
    case pgtype.BoolOID:
        return arrow.FixedWidthTypes.Boolean
    case pgtype.TimestampOID, pgtype.TimestamptzOID:
        return arrow.FixedWidthTypes.Timestamp_us
    case pgtype.DateOID:
        return arrow.FixedWidthTypes.Date32
    case pgtype.NumericOID:
        return arrow.PrimitiveTypes.Float64  // Decimal → float64
    default:
        return arrow.BinaryTypes.String  // Default to string
    }
}
```

---

## The COPY Protocol

PostgreSQL's COPY protocol is the fastest way to transfer bulk data.

### How COPY Works

Normal query protocol:
```
Client → Server: Query
Server → Client: RowDescription (column info)
Server → Client: DataRow (row 1)
Server → Client: DataRow (row 2)
...
Server → Client: CommandComplete
```

COPY protocol:
```
Client → Server: COPY query
Server → Client: CopyOutResponse
Server → Client: CopyData (entire result as stream)
Server → Client: CopyDone
```

### Implementation

```go
// go/pkg/bridge/pool.go

func (p *Pool) ExecuteCopy(req *QueryRequest) ([]byte, error) {
    ctx, cancel := context.WithTimeout(
        context.Background(),
        time.Duration(p.config.QueryTimeout)*time.Millisecond,
    )
    defer cancel()

    // Wrap the query in COPY TO STDOUT
    copySQL := "COPY (" + req.SQL + ") TO STDOUT WITH (FORMAT csv, HEADER true)"

    // Acquire a dedicated connection
    conn, err := p.primary.Acquire(ctx)
    if err != nil {
        return nil, err
    }
    defer conn.Release()

    // Execute COPY
    var buf bytes.Buffer
    _, err = conn.Conn().PgConn().CopyTo(ctx, &buf, copySQL)
    if err != nil {
        return nil, err
    }

    return buf.Bytes(), nil
}
```

### Why COPY is Faster

1. **Less parsing overhead** - Data is streamed as CSV/binary, not row-by-row protocol messages
2. **No type conversion** - PostgreSQL outputs data directly, no intermediate representation
3. **Bulk transfer** - Single TCP stream instead of many small packets
4. **Server-side efficiency** - PostgreSQL has highly optimized COPY code paths

---

## Python ctypes Integration

### Loading the Shared Library

```python
# pynext_go/bridge.py

def _find_library() -> Path | None:
    """Find the Go shared library."""
    # 1. Check environment variable
    env_path = os.environ.get("PYNEXT_GO_LIB")
    if env_path:
        path = Path(env_path)
        if path.exists():
            return path
    
    # 2. Determine platform-specific library name
    system = platform.system().lower()
    if system == "darwin":
        lib_name = "libpynext.dylib"
    elif system == "windows":
        lib_name = "pynext.dll"
    else:
        lib_name = "libpynext.so"
    
    # 3. Look in package directory
    package_dir = Path(__file__).parent
    lib_path = package_dir / "_lib" / f"{system}_{machine}" / lib_name
    if lib_path.exists():
        return lib_path
    
    return None

# Load the library
_library_path = _find_library()
if _library_path:
    _GO_LIB = ctypes.CDLL(str(_library_path))
    GO_AVAILABLE = True
else:
    _GO_LIB = None
    GO_AVAILABLE = False
```

### Defining Function Signatures

```python
def _setup_functions():
    """Set up ctypes function signatures."""
    
    # PynextInit(configJSON *C.char) C.int
    _GO_LIB.PynextInit.argtypes = [ctypes.c_char_p]
    _GO_LIB.PynextInit.restype = ctypes.c_int

    # PynextExecute(queryJSON *C.char, outBuffer **C.char, outLen *C.int) C.int
    _GO_LIB.PynextExecute.argtypes = [
        ctypes.c_char_p,                    # queryJSON
        ctypes.POINTER(ctypes.c_char_p),    # outBuffer (pointer to pointer)
        ctypes.POINTER(ctypes.c_int),       # outLen (pointer to int)
    ]
    _GO_LIB.PynextExecute.restype = ctypes.c_int
    
    # ... similar for other functions
```

### Calling Go Functions

```python
def execute(self, sql: str, params: list = None) -> QueryResult:
    self._check_initialized()
    
    # 1. Build request and serialize to JSON
    request = {"sql": sql, "params": params or []}
    request_json = json_dumps(request)  # Returns bytes
    
    # 2. Prepare output pointers
    out_buffer = ctypes.c_char_p()  # Will hold pointer to result
    out_len = ctypes.c_int()        # Will hold result length
    
    # 3. Call Go function
    result_code = _GO_LIB.PynextExecute(
        request_json,
        ctypes.byref(out_buffer),
        ctypes.byref(out_len),
    )
    
    try:
        # 4. Parse response
        if out_buffer.value:
            response = json_loads(out_buffer.value)
        else:
            raise BridgeError("No response from Go bridge")
        
        # 5. Check for error
        if result_code != 0:
            raise BridgeQueryError(
                message=response.get("error", "Query failed"),
                code=result_code,
            )
        
        return QueryResult.from_dict(response)
    
    finally:
        # 6. Free Go-allocated memory!
        if out_buffer.value:
            _GO_LIB.PynextFreeBuffer(out_buffer)
```

---

## Memory Management

### The Challenge

Go and Python have different memory management models:
- **Go**: Garbage collected, but GC might move objects
- **Python**: Reference counted
- **C**: Manual malloc/free

### Our Approach

1. **Allocate in C** - Use `malloc()` for data returned to Python
2. **Track in Python** - Python holds the pointer
3. **Free explicitly** - Python calls `PynextFreeBuffer()` when done

```go
// Allocate in C (won't be moved by Go GC)
*outBuffer = C.alloc_string(
    (*C.char)(unsafe.Pointer(&resultJSON[0])),
    C.int(len(resultJSON)),
)
```

```python
# Free when done
finally:
    if out_buffer.value:
        _GO_LIB.PynextFreeBuffer(out_buffer)
```

### Handling Binary Data with Null Bytes

A subtle bug: `ctypes.c_char_p.value` stops at null bytes (`\x00`), which can appear in binary data!

```python
# ❌ BAD: Truncates at null bytes
data = out_buffer.value  # Stops at first \x00

# ✅ GOOD: Use string_at with explicit length
data = ctypes.string_at(out_buffer, out_len.value)
```

---

## Performance Optimizations

### 1. Statement Caching

```go
// Enable prepared statement caching
poolConfig.ConnConfig.DefaultQueryExecMode = pgx.QueryExecModeCacheStatement
poolConfig.ConnConfig.StatementCacheCapacity = 2048
```

This caches query plans on the PostgreSQL server. Repeated queries skip the parsing phase.

### 2. Atomic Statistics

```go
// Use atomic operations for stats (no locks)
queryCount     atomic.Int64
errorCount     atomic.Int64
totalLatencyNs atomic.Int64

func (p *Pool) Execute(req *QueryRequest) *QueryResult {
    p.queryCount.Add(1)  // Lock-free increment
    // ...
}
```

### 3. Worker Semaphore

```go
// Limit concurrent queries to pool size
workerSem: make(chan struct{}, config.PoolMaxSize)

func (p *Pool) ExecuteParallel(requests []*QueryRequest) []*QueryResult {
    for i, req := range requests {
        go func(idx int, r *QueryRequest) {
            p.workerSem <- struct{}{}        // Block if pool full
            defer func() { <-p.workerSem }() // Release slot
            results[idx] = p.Execute(r)
        }(i, req)
    }
}
```

### 4. Efficient JSON with sonic

sonic uses SIMD instructions for JSON parsing:

```go
import sonic "github.com/bytedance/sonic"

// 2-3x faster than encoding/json
sonic.Marshal(result)
sonic.Unmarshal(data, &request)
```

### 5. orjson on Python Side

```python
import orjson  # Written in Rust, uses SIMD

# 2x faster than json module
orjson.loads(data)
orjson.dumps(obj)
```

---

## Error Handling Across Boundaries

### Error Codes

```go
// go/pkg/bridge/bridge.go

const (
    ErrCodeSuccess        = 0
    ErrCodeNotInitialized = 1
    ErrCodeConfig         = 2
    ErrCodeConnection     = 3
    ErrCodeQuery          = 4
    ErrCodeTimeout        = 5
    ErrCodePool           = 6
    ErrCodeArrow          = 7
)
```

### Go Side

```go
func PynextExecute(...) C.int {
    if bridge == nil {
        errJSON := MustMarshal(ErrNotInitialized)
        *outBuffer = C.alloc_string(...)
        *outLen = C.int(len(errJSON))
        return C.int(ErrCodeNotInitialized)  // Error code
    }
    
    // Execute query
    result := bridge.Execute(&req)
    
    if !result.Success {
        return C.int(ErrCodeQuery)  // Error code
    }
    return C.int(ErrCodeSuccess)
}
```

### Python Side

```python
# pynext_go/errors.py

def error_from_code(code: int, message: str) -> BridgeError:
    """Create appropriate exception from Go error code."""
    if code == 1:
        return BridgeError("Bridge not initialized")
    elif code == 2:
        return BridgeConfigError(message)
    elif code == 3:
        return BridgeConnectionError(message)
    elif code == 4:
        return BridgeQueryError(message)
    elif code == 5:
        return BridgeTimeoutError(message)
    elif code == 6:
        return BridgePoolError(message)
    elif code == 7:
        return BridgeArrowError(message)
    else:
        return BridgeError(message)
```

---

## Building the Shared Library

### Build Command

```bash
cd go/
go build -buildmode=c-shared -o ../pynext_go/_lib/darwin_arm64/libpynext.dylib ./cmd/pynext/
```

### What `-buildmode=c-shared` Does

1. Compiles all Go code
2. Includes the Go runtime
3. Generates C header file (libpynext.h)
4. Creates shared library with exported symbols

### Cross-Compilation

```bash
# For Linux amd64
GOOS=linux GOARCH=amd64 go build -buildmode=c-shared -o libpynext.so ./cmd/pynext/

# For Linux arm64
GOOS=linux GOARCH=arm64 go build -buildmode=c-shared -o libpynext.so ./cmd/pynext/

# For Windows
GOOS=windows GOARCH=amd64 go build -buildmode=c-shared -o pynext.dll ./cmd/pynext/
```

---

## Debugging Tips

### Enable Debug Logging

```python
import logging
logging.getLogger("pynext_go").setLevel(logging.DEBUG)
```

### Check Symbol Visibility

```bash
# macOS
nm -gU libpynext.dylib | grep Pynext

# Linux
nm -D libpynext.so | grep Pynext
```

### Verify Library Loading

```python
import pynext_go
print(f"GO_AVAILABLE: {pynext_go.GO_AVAILABLE}")
print(f"Library path: {pynext_go.GO_LIBRARY_PATH}")
```

---

## Conclusion

The Go Bridge achieves its 2-3x performance gains through:

1. **True parallelism** via goroutines (bypassing Python's GIL)
2. **Efficient connection pooling** with pgxpool
3. **Fast serialization** with sonic (Go) and orjson (Python)
4. **PostgreSQL COPY protocol** for bulk data
5. **Zero-copy Arrow IPC** for DataFrame operations

The architecture carefully manages memory across the Go/Python boundary and provides a clean, Pythonic API despite the underlying complexity.

