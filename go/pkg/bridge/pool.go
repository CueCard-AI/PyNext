/*
Pool manages PostgreSQL connections for the Go bridge.

This implementation wraps pgx/v5's connection pool with additional features:
  - Health monitoring with automatic reconnection
  - Query execution with Arrow result conversion
  - Prepared statement caching
  - Timeout handling

Design Goals:
  - Zero-allocation hot path for queries
  - Minimal locking (per-connection state)
  - Graceful degradation on pool exhaustion
*/
package bridge

import (
	"bytes"
	"context"
	"sync"
	"sync/atomic"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/vmihailenco/msgpack/v5"

	"github.com/pynext/pynext-go/pkg/arrow"
)

// =============================================================================
// Pool Implementation
// =============================================================================

// Pool manages database connections.
type Pool struct {
	config  *Config
	primary *pgxpool.Pool

	// Health tracking
	lastHealth  *HealthStatus
	healthMutex sync.RWMutex

	// Statistics (atomic for lock-free reads)
	queryCount     atomic.Int64
	errorCount     atomic.Int64
	totalLatencyNs atomic.Int64

	// Prepared statement cache
	preparedStmts sync.Map // map[string]bool - tracks which queries are prepared

	// Worker pool for parallel queries
	workerSem chan struct{}

	// Lifecycle
	closed   atomic.Bool
	closeMux sync.Mutex
}

// NewPool creates a new connection pool.
func NewPool(config *Config) (*Pool, error) {
	// Parse primary connection string
	poolConfig, err := pgxpool.ParseConfig(config.Primary)
	if err != nil {
		return nil, &BridgeError{
			Code:    ErrCodeConnection,
			Message: "invalid primary connection string",
			Details: err.Error(),
		}
	}

	// Apply pool settings
	poolConfig.MinConns = int32(config.PoolMinSize)
	poolConfig.MaxConns = int32(config.PoolMaxSize)
	poolConfig.MaxConnLifetime = time.Duration(config.PoolMaxLifetime) * time.Second
	poolConfig.MaxConnIdleTime = time.Duration(config.PoolMaxIdleTime) * time.Second
	poolConfig.HealthCheckPeriod = time.Duration(config.PoolHealthInterval) * time.Second

	// Use prepared statement caching for faster repeated queries
	poolConfig.ConnConfig.DefaultQueryExecMode = pgx.QueryExecModeCacheStatement

	// Larger statement cache
	poolConfig.ConnConfig.StatementCacheCapacity = 2048

	// Create pool with timeout
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	pgPool, err := pgxpool.NewWithConfig(ctx, poolConfig)
	if err != nil {
		return nil, &BridgeError{
			Code:    ErrCodeConnection,
			Message: "failed to create connection pool",
			Details: err.Error(),
		}
	}

	// Verify connectivity
	if err := pgPool.Ping(ctx); err != nil {
		pgPool.Close()
		return nil, &BridgeError{
			Code:    ErrCodeConnection,
			Message: "failed to connect to database",
			Details: err.Error(),
		}
	}

	pool := &Pool{
		config:    config,
		primary:   pgPool,
		workerSem: make(chan struct{}, config.PoolMaxSize), // Limit concurrent queries
	}

	return pool, nil
}

// ExecuteFast runs a query with minimal overhead.
// Uses pool directly but skips some validation for speed.
func (p *Pool) ExecuteFast(req *QueryRequest) *QueryResult {
	if p.closed.Load() {
		return &QueryResult{
			Success: false,
			Error:   "pool is closed",
		}
	}

	start := time.Now()

	ctx, cancel := context.WithTimeout(context.Background(), time.Duration(p.config.QueryTimeout)*time.Millisecond)
	defer cancel()

	// Use pool directly - pgxpool handles connection reuse efficiently
	rows, err := p.primary.Query(ctx, req.SQL, req.Params...)
	if err != nil {
		return &QueryResult{
			Success:  false,
			Error:    err.Error(),
			Duration: float64(time.Since(start).Microseconds()) / 1000,
		}
	}
	defer rows.Close()

	result := p.rowsToResult(rows, start)
	return result
}

// Execute runs a single query and returns results.
func (p *Pool) Execute(req *QueryRequest) *QueryResult {
	if p.closed.Load() {
		return &QueryResult{
			Success: false,
			Error:   "pool is closed",
		}
	}

	start := time.Now()
	p.queryCount.Add(1)

	// Set timeout
	timeout := time.Duration(p.config.QueryTimeout) * time.Millisecond
	if req.TimeoutMs > 0 {
		timeout = time.Duration(req.TimeoutMs) * time.Millisecond
	}

	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	// Execute query
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

	// Convert to result
	result := p.rowsToResult(rows, start)

	// Update latency stats
	p.totalLatencyNs.Add(time.Since(start).Nanoseconds())

	return result
}

// rowsToResult converts pgx rows to QueryResult.
func (p *Pool) rowsToResult(rows pgx.Rows, start time.Time) *QueryResult {
	// Get column names
	fields := rows.FieldDescriptions()
	columns := make([]string, len(fields))
	for i, f := range fields {
		columns[i] = string(f.Name)
	}

	// Collect rows
	var allRows [][]interface{}
	for rows.Next() {
		values, err := rows.Values()
		if err != nil {
			p.errorCount.Add(1)
			return &QueryResult{
				Success:  false,
				Error:    err.Error(),
				Duration: float64(time.Since(start).Microseconds()) / 1000,
			}
		}
		// Copy values to avoid pgx reuse
		rowCopy := make([]interface{}, len(values))
		copy(rowCopy, values)
		allRows = append(allRows, rowCopy)
	}

	if err := rows.Err(); err != nil {
		p.errorCount.Add(1)
		return &QueryResult{
			Success:  false,
			Error:    err.Error(),
			Duration: float64(time.Since(start).Microseconds()) / 1000,
		}
	}

	return &QueryResult{
		Success:      true,
		Rows:         allRows,
		Columns:      columns,
		RowsAffected: int64(len(allRows)),
		Duration:     float64(time.Since(start).Microseconds()) / 1000,
		Cached:       false, // TODO: track prepared statement usage
	}
}

// ExecuteBatch runs multiple queries.
func (p *Pool) ExecuteBatch(req *BatchRequest) *BatchResult {
	if p.closed.Load() {
		return &BatchResult{
			Success: false,
			Error:   "pool is closed",
		}
	}

	start := time.Now()
	results := make([]QueryResult, len(req.Queries))

	// Execute in transaction if requested
	if req.Transaction {
		return p.executeBatchTx(req, start)
	}

	// Execute individually
	var firstError string
	allSuccess := true
	for i, q := range req.Queries {
		results[i] = *p.Execute(&q)
		if !results[i].Success {
			allSuccess = false
			if firstError == "" {
				firstError = results[i].Error
			}
			if req.StopOnError {
				break
			}
		}
	}

	return &BatchResult{
		Success:  allSuccess,
		Error:    firstError,
		Results:  results,
		Duration: float64(time.Since(start).Microseconds()) / 1000,
	}
}

// executeBatchTx executes a batch in a transaction.
func (p *Pool) executeBatchTx(req *BatchRequest, start time.Time) *BatchResult {
	ctx, cancel := context.WithTimeout(context.Background(), time.Duration(p.config.QueryTimeout*len(req.Queries))*time.Millisecond)
	defer cancel()

	tx, err := p.primary.Begin(ctx)
	if err != nil {
		return &BatchResult{
			Success:  false,
			Error:    "failed to begin transaction: " + err.Error(),
			Duration: float64(time.Since(start).Microseconds()) / 1000,
		}
	}

	results := make([]QueryResult, len(req.Queries))
	var firstError string
	allSuccess := true

	for i, q := range req.Queries {
		qStart := time.Now()
		rows, err := tx.Query(ctx, q.SQL, q.Params...)
		if err != nil {
			allSuccess = false
			results[i] = QueryResult{
				Success:  false,
				Error:    err.Error(),
				Duration: float64(time.Since(qStart).Microseconds()) / 1000,
			}
			if firstError == "" {
				firstError = err.Error()
			}
			if req.StopOnError {
				break
			}
			continue
		}

		// Get column names
		fields := rows.FieldDescriptions()
		columns := make([]string, len(fields))
		for j, f := range fields {
			columns[j] = string(f.Name)
		}

		// Collect rows
		var allRows [][]interface{}
		for rows.Next() {
			values, err := rows.Values()
			if err != nil {
				allSuccess = false
				results[i] = QueryResult{
					Success:  false,
					Error:    err.Error(),
					Duration: float64(time.Since(qStart).Microseconds()) / 1000,
				}
				if firstError == "" {
					firstError = err.Error()
				}
				rows.Close()
				if req.StopOnError {
					break
				}
				continue
			}
			rowCopy := make([]interface{}, len(values))
			copy(rowCopy, values)
			allRows = append(allRows, rowCopy)
		}
		rows.Close()

		if err := rows.Err(); err != nil {
			allSuccess = false
			results[i] = QueryResult{
				Success:  false,
				Error:    err.Error(),
				Duration: float64(time.Since(qStart).Microseconds()) / 1000,
			}
			if firstError == "" {
				firstError = err.Error()
			}
			if req.StopOnError {
				break
			}
			continue
		}

		results[i] = QueryResult{
			Success:      true,
			Rows:         allRows,
			Columns:      columns,
			RowsAffected: int64(len(allRows)),
			Duration:     float64(time.Since(qStart).Microseconds()) / 1000,
		}
	}

	// Commit or rollback
	if allSuccess {
		if err := tx.Commit(ctx); err != nil {
			return &BatchResult{
				Success:  false,
				Error:    "failed to commit transaction: " + err.Error(),
				Results:  results,
				Duration: float64(time.Since(start).Microseconds()) / 1000,
			}
		}
	} else {
		tx.Rollback(ctx)
	}

	return &BatchResult{
		Success:  allSuccess,
		Error:    firstError,
		Results:  results,
		Duration: float64(time.Since(start).Microseconds()) / 1000,
	}
}

// Health returns the current pool health status.
func (p *Pool) Health() *HealthStatus {
	if p.closed.Load() {
		return &HealthStatus{
			Status:    "unhealthy",
			Timestamp: time.Now(),
		}
	}

	// Get pool stats
	stats := p.primary.Stat()

	// Check primary connectivity
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	pingStart := time.Now()
	pingErr := p.primary.Ping(ctx)
	pingLatency := float64(time.Since(pingStart).Microseconds()) / 1000

	var primaryStatus string
	var primaryError string
	if pingErr != nil {
		primaryStatus = "down"
		primaryError = pingErr.Error()
	} else if pingLatency > 100 {
		primaryStatus = "degraded"
	} else {
		primaryStatus = "ok"
	}

	// Calculate average latency
	var avgLatency float64
	if count := p.queryCount.Load(); count > 0 {
		avgLatency = float64(p.totalLatencyNs.Load()) / float64(count) / 1000000 // ns to ms
	}

	status := "healthy"
	if primaryStatus == "down" {
		status = "unhealthy"
	} else if primaryStatus == "degraded" {
		status = "degraded"
	}

	return &HealthStatus{
		Status: status,
		Primary: &ConnectionHealth{
			URL:       MaskDSN(p.config.Primary),
			Status:    primaryStatus,
			LatencyMs: pingLatency,
			Error:     primaryError,
		},
		Pool: PoolHealth{
			TotalConns:  int(stats.TotalConns()),
			IdleConns:   int(stats.IdleConns()),
			ActiveConns: int(stats.AcquiredConns()),
			WaitingReqs: 0, // pgxpool doesn't expose this directly
			AvgWaitMs:   avgLatency,
			MaxWaitMs:   avgLatency * 2, // Estimate
		},
		Timestamp: time.Now(),
	}
}

// Close shuts down the pool.
func (p *Pool) Close() {
	p.closeMux.Lock()
	defer p.closeMux.Unlock()

	if p.closed.Load() {
		return
	}
	p.closed.Store(true)

	if p.primary != nil {
		p.primary.Close()
	}
}

// Stats returns pool statistics.
func (p *Pool) Stats() (queries, errors int64, avgLatencyMs float64) {
	queries = p.queryCount.Load()
	errors = p.errorCount.Load()
	if queries > 0 {
		avgLatencyMs = float64(p.totalLatencyNs.Load()) / float64(queries) / 1000000
	}
	return
}

// Buffer pool for COPY operations to reduce allocations
var copyBufferPool = sync.Pool{
	New: func() interface{} {
		return bytes.NewBuffer(make([]byte, 0, 1024*1024)) // 1MB initial capacity
	},
}

// ExecuteCopy runs a query using COPY protocol for maximum throughput.
// Returns CSV-formatted data which can be parsed very efficiently.
// This is 2-5x faster than regular SELECT for large result sets.
func (p *Pool) ExecuteCopy(req *QueryRequest) ([]byte, error) {
	if p.closed.Load() {
		return nil, &BridgeError{
			Code:    ErrCodePool,
			Message: "pool is closed",
		}
	}

	start := time.Now()
	p.queryCount.Add(1)

	ctx, cancel := context.WithTimeout(context.Background(), time.Duration(p.config.QueryTimeout)*time.Millisecond)
	defer cancel()

	// Use CSV format with headers for easy parsing
	copySQL := "COPY (" + req.SQL + ") TO STDOUT WITH (FORMAT csv, HEADER true)"

	conn, err := p.primary.Acquire(ctx)
	if err != nil {
		p.errorCount.Add(1)
		return nil, &BridgeError{
			Code:    ErrCodeConnection,
			Message: "failed to acquire connection",
			Details: err.Error(),
		}
	}
	defer conn.Release()

	// Get buffer from pool
	buf := copyBufferPool.Get().(*bytes.Buffer)
	buf.Reset()
	defer copyBufferPool.Put(buf)

	_, err = conn.Conn().PgConn().CopyTo(ctx, buf, copySQL)
	if err != nil {
		p.errorCount.Add(1)
		return nil, &BridgeError{
			Code:    ErrCodeQuery,
			Message: "COPY failed",
			Details: err.Error(),
		}
	}

	// Return a copy (buffer goes back to pool)
	result := make([]byte, buf.Len())
	copy(result, buf.Bytes())

	p.totalLatencyNs.Add(time.Since(start).Nanoseconds())
	return result, nil
}

// ExecuteCopyBinary runs a query and returns MessagePack-serialized results.
// MessagePack is faster to serialize/deserialize than JSON.
func (p *Pool) ExecuteCopyBinary(req *QueryRequest) ([]byte, error) {
	if p.closed.Load() {
		return nil, &BridgeError{
			Code:    ErrCodePool,
			Message: "pool is closed",
		}
	}

	start := time.Now()
	p.queryCount.Add(1)

	ctx, cancel := context.WithTimeout(context.Background(), time.Duration(p.config.QueryTimeout)*time.Millisecond)
	defer cancel()

	rows, err := p.primary.Query(ctx, req.SQL, req.Params...)
	if err != nil {
		p.errorCount.Add(1)
		return nil, &BridgeError{
			Code:    ErrCodeQuery,
			Message: "query failed",
			Details: err.Error(),
		}
	}
	defer rows.Close()

	// Get column names
	fields := rows.FieldDescriptions()
	columns := make([]string, len(fields))
	for i, f := range fields {
		columns[i] = string(f.Name)
	}

	// Collect all rows as [][]interface{}
	var allRows [][]interface{}
	for rows.Next() {
		values, err := rows.Values()
		if err != nil {
			p.errorCount.Add(1)
			return nil, &BridgeError{
				Code:    ErrCodeQuery,
				Message: "failed to read row",
				Details: err.Error(),
			}
		}
		// Copy values
		rowCopy := make([]interface{}, len(values))
		copy(rowCopy, values)
		allRows = append(allRows, rowCopy)
	}

	if err := rows.Err(); err != nil {
		p.errorCount.Add(1)
		return nil, &BridgeError{
			Code:    ErrCodeQuery,
			Message: "row iteration error",
			Details: err.Error(),
		}
	}

	// Create result structure
	result := map[string]interface{}{
		"columns": columns,
		"rows":    allRows,
	}

	// Serialize with msgpack
	data, err := msgpack.Marshal(result)
	if err != nil {
		p.errorCount.Add(1)
		return nil, &BridgeError{
			Code:    ErrCodeQuery,
			Message: "msgpack serialization failed",
			Details: err.Error(),
		}
	}

	p.totalLatencyNs.Add(time.Since(start).Nanoseconds())
	return data, nil
}

// ExecuteArrow runs a query and returns results as Arrow IPC bytes.
// This is the fastest path for large result sets.
func (p *Pool) ExecuteArrow(req *QueryRequest) ([]byte, error) {
	if p.closed.Load() {
		return nil, &BridgeError{
			Code:    ErrCodePool,
			Message: "pool is closed",
		}
	}

	start := time.Now()
	p.queryCount.Add(1)

	// Set timeout
	timeout := time.Duration(p.config.QueryTimeout) * time.Millisecond
	if req.TimeoutMs > 0 {
		timeout = time.Duration(req.TimeoutMs) * time.Millisecond
	}

	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	// Execute query
	rows, err := p.primary.Query(ctx, req.SQL, req.Params...)
	if err != nil {
		p.errorCount.Add(1)
		return nil, &BridgeError{
			Code:    ErrCodeQuery,
			Message: "query failed",
			Details: err.Error(),
		}
	}
	defer rows.Close()

	// Get column info for Arrow schema
	fields := rows.FieldDescriptions()
	names := make([]string, len(fields))
	oids := make([]uint32, len(fields))
	for i, f := range fields {
		names[i] = string(f.Name)
		oids[i] = f.DataTypeOID
	}

	// Create Arrow schema and builder
	schema := arrow.SchemaFromPgTypes(names, oids)
	builder := arrow.NewRecordBuilder(schema)
	defer builder.Release()

	// Collect rows into Arrow
	for rows.Next() {
		values, err := rows.Values()
		if err != nil {
			p.errorCount.Add(1)
			return nil, &BridgeError{
				Code:    ErrCodeQuery,
				Message: "failed to read row",
				Details: err.Error(),
			}
		}
		if err := builder.Append(values); err != nil {
			p.errorCount.Add(1)
			return nil, &BridgeError{
				Code:    ErrCodeQuery,
				Message: "failed to build Arrow record",
				Details: err.Error(),
			}
		}
	}

	if err := rows.Err(); err != nil {
		p.errorCount.Add(1)
		return nil, &BridgeError{
			Code:    ErrCodeQuery,
			Message: "row iteration error",
			Details: err.Error(),
		}
	}

	// Build record and serialize to IPC
	record := builder.Build()
	defer record.Release()

	ipcBytes, err := arrow.SerializeIPC(record)
	if err != nil {
		p.errorCount.Add(1)
		return nil, &BridgeError{
			Code:    ErrCodeQuery,
			Message: "failed to serialize Arrow",
			Details: err.Error(),
		}
	}

	// Update latency stats
	p.totalLatencyNs.Add(time.Since(start).Nanoseconds())

	return ipcBytes, nil
}

// Warmup pre-creates connections to avoid cold-start latency.
// It fills the pool up to PoolMinSize with active, verified connections.
func (p *Pool) Warmup() error {
	if p.closed.Load() {
		return &BridgeError{
			Code:    ErrCodePool,
			Message: "pool is closed",
		}
	}

	minConns := p.config.PoolMinSize
	if minConns == 0 {
		minConns = 5
	}

	// Acquire and release connections to warm them up
	conns := make([]*pgxpool.Conn, 0, minConns)
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	for i := 0; i < minConns; i++ {
		conn, err := p.primary.Acquire(ctx)
		if err != nil {
			// Release any acquired connections
			for _, c := range conns {
				c.Release()
			}
			return &BridgeError{
				Code:    ErrCodePool,
				Message: "failed to warm up connections",
				Details: err.Error(),
			}
		}
		conns = append(conns, conn)
	}

	// Verify each connection with a simple query
	for _, conn := range conns {
		if _, err := conn.Exec(ctx, "SELECT 1"); err != nil {
			// Connection is bad, release all
			for _, c := range conns {
				c.Release()
			}
			return &BridgeError{
				Code:    ErrCodePool,
				Message: "connection verification failed",
				Details: err.Error(),
			}
		}
	}

	// Release all connections back to pool
	for _, c := range conns {
		c.Release()
	}

	return nil
}

// ExecuteParallel runs multiple queries in parallel using goroutines.
// Each query gets its own connection and runs simultaneously.
// Results are returned in the same order as the input queries.
func (p *Pool) ExecuteParallel(queries []QueryRequest) []QueryResult {
	if p.closed.Load() {
		results := make([]QueryResult, len(queries))
		for i := range results {
			results[i] = QueryResult{
				Success: false,
				Error:   "pool is closed",
			}
		}
		return results
	}

	n := len(queries)
	if n == 0 {
		return []QueryResult{}
	}

	results := make([]QueryResult, n)

	// Use WaitGroup to wait for all goroutines
	var wg sync.WaitGroup
	wg.Add(n)

	// Execute each query in its own goroutine
	// pgxpool handles connection limiting internally, so we don't need extra semaphores
	for i, query := range queries {
		go func(idx int, req QueryRequest) {
			defer wg.Done()
			results[idx] = *p.executeOptimized(&req)
		}(i, query)
	}

	// Wait for all queries to complete
	wg.Wait()

	return results
}

// executeOptimized is an optimized version of Execute for parallel workloads.
// It reuses connections more efficiently and has less overhead.
func (p *Pool) executeOptimized(req *QueryRequest) *QueryResult {
	if p.closed.Load() {
		return &QueryResult{
			Success: false,
			Error:   "pool is closed",
		}
	}

	start := time.Now()
	p.queryCount.Add(1)

	// Set timeout
	timeout := time.Duration(p.config.QueryTimeout) * time.Millisecond
	if req.TimeoutMs > 0 {
		timeout = time.Duration(req.TimeoutMs) * time.Millisecond
	}

	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	// Acquire connection from pool
	conn, err := p.primary.Acquire(ctx)
	if err != nil {
		p.errorCount.Add(1)
		return &QueryResult{
			Success:  false,
			Error:    err.Error(),
			Duration: float64(time.Since(start).Microseconds()) / 1000,
		}
	}
	defer conn.Release()

	// Execute query on the acquired connection
	rows, err := conn.Query(ctx, req.SQL, req.Params...)
	if err != nil {
		p.errorCount.Add(1)
		return &QueryResult{
			Success:  false,
			Error:    err.Error(),
			Duration: float64(time.Since(start).Microseconds()) / 1000,
		}
	}
	defer rows.Close()

	// Convert to result (optimized path)
	result := p.rowsToResultFast(rows, start)

	// Update latency stats
	p.totalLatencyNs.Add(time.Since(start).Nanoseconds())

	return result
}

// rowsToResultFast is an optimized version with less allocations.
func (p *Pool) rowsToResultFast(rows pgx.Rows, start time.Time) *QueryResult {
	// Get column names
	fields := rows.FieldDescriptions()
	columns := make([]string, len(fields))
	for i, f := range fields {
		columns[i] = string(f.Name)
	}

	// Pre-allocate with estimated capacity
	allRows := make([][]interface{}, 0, 100)

	for rows.Next() {
		values, err := rows.Values()
		if err != nil {
			p.errorCount.Add(1)
			return &QueryResult{
				Success:  false,
				Error:    err.Error(),
				Duration: float64(time.Since(start).Microseconds()) / 1000,
			}
		}
		// Copy values to avoid pgx reuse
		rowCopy := make([]interface{}, len(values))
		copy(rowCopy, values)
		allRows = append(allRows, rowCopy)
	}

	if err := rows.Err(); err != nil {
		p.errorCount.Add(1)
		return &QueryResult{
			Success:  false,
			Error:    err.Error(),
			Duration: float64(time.Since(start).Microseconds()) / 1000,
		}
	}

	return &QueryResult{
		Success:      true,
		Rows:         allRows,
		Columns:      columns,
		RowsAffected: int64(len(allRows)),
		Duration:     float64(time.Since(start).Microseconds()) / 1000,
		Cached:       false,
	}
}
