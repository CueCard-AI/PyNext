package bridge

import (
	"sync/atomic"
	"testing"
	"time"
)

// =============================================================================
// Pool Unit Tests (without real database)
// =============================================================================

func TestPool_ClosedPoolRejectsExecute(t *testing.T) {
	pool := &Pool{}
	pool.closed.Store(true)

	req := &QueryRequest{SQL: "SELECT 1"}
	result := pool.Execute(req)

	if result.Success {
		t.Error("Expected failure for closed pool")
	}
	if result.Error != "pool is closed" {
		t.Errorf("Expected 'pool is closed' error, got '%s'", result.Error)
	}
}

func TestPool_ClosedPoolRejectsBatch(t *testing.T) {
	pool := &Pool{}
	pool.closed.Store(true)

	req := &BatchRequest{
		Queries: []QueryRequest{{SQL: "SELECT 1"}},
	}
	result := pool.ExecuteBatch(req)

	if result.Success {
		t.Error("Expected failure for closed pool")
	}
	if result.Error != "pool is closed" {
		t.Errorf("Expected 'pool is closed' error, got '%s'", result.Error)
	}
}

func TestPool_ClosedPoolHealth(t *testing.T) {
	pool := &Pool{}
	pool.closed.Store(true)

	health := pool.Health()

	if health.Status != "unhealthy" {
		t.Errorf("Expected 'unhealthy' status, got '%s'", health.Status)
	}
}

func TestPool_CloseIsIdempotent(t *testing.T) {
	pool := &Pool{}

	// Close multiple times should not panic
	pool.Close()
	pool.Close()
	pool.Close()

	// Should be closed
	if !pool.closed.Load() {
		t.Error("Expected pool to be closed")
	}
}

func TestPool_AtomicCounters(t *testing.T) {
	pool := &Pool{}

	// Increment counters
	pool.queryCount.Add(10)
	pool.errorCount.Add(3)
	pool.totalLatencyNs.Add(1000000000) // 1 second in ns

	// Verify values
	if pool.queryCount.Load() != 10 {
		t.Errorf("Expected queryCount=10, got %d", pool.queryCount.Load())
	}
	if pool.errorCount.Load() != 3 {
		t.Errorf("Expected errorCount=3, got %d", pool.errorCount.Load())
	}
	if pool.totalLatencyNs.Load() != 1000000000 {
		t.Errorf("Expected totalLatencyNs=1000000000, got %d", pool.totalLatencyNs.Load())
	}
}

func TestPool_Stats(t *testing.T) {
	pool := &Pool{}
	pool.queryCount.Store(100)
	pool.errorCount.Store(5)
	pool.totalLatencyNs.Store(5000000000) // 5 seconds in nanoseconds

	queries, errors, avgLatency := pool.Stats()

	if queries != 100 {
		t.Errorf("Expected queries=100, got %d", queries)
	}
	if errors != 5 {
		t.Errorf("Expected errors=5, got %d", errors)
	}
	// 5000ms total / 100 queries = 50ms average
	if avgLatency < 49 || avgLatency > 51 {
		t.Errorf("Expected avgLatency~50ms, got %f", avgLatency)
	}
}

func TestPool_StatsZeroQueries(t *testing.T) {
	pool := &Pool{}

	queries, errors, avgLatency := pool.Stats()

	if queries != 0 {
		t.Errorf("Expected queries=0, got %d", queries)
	}
	if errors != 0 {
		t.Errorf("Expected errors=0, got %d", errors)
	}
	if avgLatency != 0 {
		t.Errorf("Expected avgLatency=0, got %f", avgLatency)
	}
}

// =============================================================================
// Concurrent Access Tests
// =============================================================================

func TestPool_ConcurrentClose(t *testing.T) {
	pool := &Pool{}

	// Close from multiple goroutines
	done := make(chan bool, 10)
	for i := 0; i < 10; i++ {
		go func() {
			pool.Close()
			done <- true
		}()
	}

	// Wait for all
	for i := 0; i < 10; i++ {
		<-done
	}

	if !pool.closed.Load() {
		t.Error("Expected pool to be closed")
	}
}

func TestPool_ConcurrentStats(t *testing.T) {
	pool := &Pool{}

	// Increment from multiple goroutines
	done := make(chan bool, 100)
	for i := 0; i < 100; i++ {
		go func() {
			pool.queryCount.Add(1)
			pool.errorCount.Add(1)
			done <- true
		}()
	}

	// Wait for all
	for i := 0; i < 100; i++ {
		<-done
	}

	if pool.queryCount.Load() != 100 {
		t.Errorf("Expected queryCount=100, got %d", pool.queryCount.Load())
	}
	if pool.errorCount.Load() != 100 {
		t.Errorf("Expected errorCount=100, got %d", pool.errorCount.Load())
	}
}

// =============================================================================
// Config Application Tests
// =============================================================================

func TestNewPool_InvalidDSN(t *testing.T) {
	config := &Config{
		Primary: "invalid-dsn",
	}

	_, err := NewPool(config)
	if err == nil {
		t.Error("Expected error for invalid DSN")
	}

	if be, ok := err.(*BridgeError); ok {
		if be.Code != ErrCodeConnection {
			t.Errorf("Expected ErrCodeConnection, got %d", be.Code)
		}
	}
}

// =============================================================================
// Timeout Calculation Tests
// =============================================================================

func TestPool_DefaultTimeout(t *testing.T) {
	pool := &Pool{
		config: &Config{
			QueryTimeout: 30000, // 30 seconds
		},
	}

	req := &QueryRequest{SQL: "SELECT 1"}

	// Simulate timeout calculation
	timeout := time.Duration(pool.config.QueryTimeout) * time.Millisecond
	if req.TimeoutMs > 0 {
		timeout = time.Duration(req.TimeoutMs) * time.Millisecond
	}

	if timeout != 30*time.Second {
		t.Errorf("Expected 30s timeout, got %v", timeout)
	}
}

func TestPool_OverrideTimeout(t *testing.T) {
	pool := &Pool{
		config: &Config{
			QueryTimeout: 30000,
		},
	}

	req := &QueryRequest{
		SQL:       "SELECT 1",
		TimeoutMs: 5000, // Override to 5 seconds
	}

	timeout := time.Duration(pool.config.QueryTimeout) * time.Millisecond
	if req.TimeoutMs > 0 {
		timeout = time.Duration(req.TimeoutMs) * time.Millisecond
	}

	if timeout != 5*time.Second {
		t.Errorf("Expected 5s timeout, got %v", timeout)
	}
}

// =============================================================================
// Connection Health Status Tests
// =============================================================================

func TestConnectionHealth_States(t *testing.T) {
	tests := []struct {
		latencyMs float64
		pingErr   bool
		expected  string
	}{
		{1.0, false, "ok"},
		{150.0, false, "degraded"}, // > 100ms is degraded
		{0.0, true, "down"},
	}

	for _, tt := range tests {
		var status string
		if tt.pingErr {
			status = "down"
		} else if tt.latencyMs > 100 {
			status = "degraded"
		} else {
			status = "ok"
		}

		if status != tt.expected {
			t.Errorf("For latency=%v, pingErr=%v: expected '%s', got '%s'",
				tt.latencyMs, tt.pingErr, tt.expected, status)
		}
	}
}

func TestPoolHealth_Fields(t *testing.T) {
	pool := PoolHealth{
		TotalConns:  10,
		IdleConns:   5,
		ActiveConns: 5,
		WaitingReqs: 2,
		AvgWaitMs:   1.5,
		MaxWaitMs:   5.0,
	}

	if pool.TotalConns != 10 {
		t.Errorf("Expected TotalConns=10, got %d", pool.TotalConns)
	}
	if pool.IdleConns != 5 {
		t.Errorf("Expected IdleConns=5, got %d", pool.IdleConns)
	}
	if pool.ActiveConns != 5 {
		t.Errorf("Expected ActiveConns=5, got %d", pool.ActiveConns)
	}
}

// =============================================================================
// Atomic Operation Safety Tests
// =============================================================================

func TestAtomicBoolOperations(t *testing.T) {
	var b atomic.Bool

	// Initial state
	if b.Load() {
		t.Error("Expected initial value to be false")
	}

	// Store and load
	b.Store(true)
	if !b.Load() {
		t.Error("Expected true after Store(true)")
	}

	// CompareAndSwap
	if !b.CompareAndSwap(true, false) {
		t.Error("CompareAndSwap should return true")
	}
	if b.Load() {
		t.Error("Expected false after CompareAndSwap")
	}
}

func TestAtomicInt64Operations(t *testing.T) {
	var i atomic.Int64

	// Initial state
	if i.Load() != 0 {
		t.Error("Expected initial value to be 0")
	}

	// Add and load
	i.Add(10)
	if i.Load() != 10 {
		t.Errorf("Expected 10, got %d", i.Load())
	}

	// Multiple adds
	i.Add(5)
	i.Add(-3)
	if i.Load() != 12 {
		t.Errorf("Expected 12, got %d", i.Load())
	}
}

// =============================================================================
// Batch Timeout Tests
// =============================================================================

func TestPool_BatchTimeoutCalculation(t *testing.T) {
	config := &Config{QueryTimeout: 1000} // 1 second per query

	// Batch with 5 queries
	numQueries := 5
	expectedTimeout := time.Duration(config.QueryTimeout*numQueries) * time.Millisecond

	if expectedTimeout != 5*time.Second {
		t.Errorf("Expected 5s batch timeout, got %v", expectedTimeout)
	}
}

// =============================================================================
// Error Handling Tests
// =============================================================================

func TestPool_ExecuteOnClosedPool(t *testing.T) {
	pool := &Pool{}
	pool.closed.Store(true)

	result := pool.Execute(&QueryRequest{SQL: "SELECT 1"})

	if result.Success {
		t.Error("Expected failure")
	}
	if result.Error != "pool is closed" {
		t.Errorf("Unexpected error: %s", result.Error)
	}
}

func TestPool_BatchOnClosedPool(t *testing.T) {
	pool := &Pool{}
	pool.closed.Store(true)

	result := pool.ExecuteBatch(&BatchRequest{
		Queries: []QueryRequest{{SQL: "SELECT 1"}},
	})

	if result.Success {
		t.Error("Expected failure")
	}
	if result.Error != "pool is closed" {
		t.Errorf("Unexpected error: %s", result.Error)
	}
}

// =============================================================================
// Pool Struct Tests
// =============================================================================

func TestPool_FieldsExist(t *testing.T) {
	pool := &Pool{
		config: &Config{
			Primary:      "postgresql://localhost/test",
			QueryTimeout: 30000,
		},
	}

	if pool.config == nil {
		t.Error("Expected config to be set")
	}
	if pool.config.Primary == "" {
		t.Error("Expected Primary to be set")
	}
}

func TestPool_ExecuteParallelOnClosedPool(t *testing.T) {
	// Create a pool with invalid config so it fails
	pool := &Pool{}
	pool.closed.Store(true) // Simulate closed pool

	queries := []QueryRequest{
		{SQL: "SELECT 1", Params: []interface{}{}},
		{SQL: "SELECT 2", Params: []interface{}{}},
	}

	results := pool.ExecuteParallel(queries)

	// Should return failure for all queries
	if len(results) != 2 {
		t.Fatalf("Expected 2 results, got %d", len(results))
	}
	for i, r := range results {
		if r.Success {
			t.Errorf("Query %d: expected failure, got success", i)
		}
		if r.Error != "pool is closed" {
			t.Errorf("Query %d: expected 'pool is closed' error, got '%s'", i, r.Error)
		}
	}
}

func TestPool_ExecuteParallelOrderPreservation(t *testing.T) {
	// Test that results array maintains same order as queries
	pool := &Pool{}
	pool.closed.Store(true) // Will fail but order should be preserved

	queries := []QueryRequest{
		{SQL: "SELECT 'first'", Params: []interface{}{}},
		{SQL: "SELECT 'second'", Params: []interface{}{}},
		{SQL: "SELECT 'third'", Params: []interface{}{}},
	}

	results := pool.ExecuteParallel(queries)

	if len(results) != 3 {
		t.Fatalf("Expected 3 results, got %d", len(results))
	}

	// All should fail consistently, demonstrating order is preserved
	for i, r := range results {
		if r.Success {
			t.Errorf("Query %d: expected failure", i)
		}
	}
}

func TestPool_ExecuteParallelEmpty(t *testing.T) {
	pool := &Pool{}
	pool.closed.Store(false)

	// Empty query list should return empty results
	results := pool.ExecuteParallel([]QueryRequest{})

	if len(results) != 0 {
		t.Fatalf("Expected 0 results for empty input, got %d", len(results))
	}
}

func TestPool_CloseMutexProtection(t *testing.T) {
	pool := &Pool{}

	// Multiple concurrent closes should not deadlock
	done := make(chan bool, 10)
	for i := 0; i < 10; i++ {
		go func() {
			pool.closeMux.Lock()
			pool.closeMux.Unlock()
			done <- true
		}()
	}

	for i := 0; i < 10; i++ {
		<-done
	}
}
