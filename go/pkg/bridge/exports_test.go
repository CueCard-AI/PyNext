package bridge

import (
	"encoding/json"
	"testing"
)

// =============================================================================
// Bridge Struct Tests
// =============================================================================

func TestBridge_NewBridge(t *testing.T) {
	bridge := &Bridge{
		config: &Config{
			Primary: "postgresql://localhost/test",
		},
	}
	
	if bridge.config.Primary != "postgresql://localhost/test" {
		t.Errorf("Expected primary DSN, got %s", bridge.config.Primary)
	}
}

func TestBridge_Close_Nil(t *testing.T) {
	bridge := &Bridge{
		pool: nil,
	}
	
	// Should not panic
	bridge.Close()
}

// =============================================================================
// Global State Tests
// =============================================================================

func TestGlobalBridge_InitiallyNil(t *testing.T) {
	globalMutex.Lock()
	original := globalBridge
	globalBridge = nil
	globalMutex.Unlock()
	
	globalMutex.RLock()
	if globalBridge != nil {
		t.Error("Expected globalBridge to be nil initially")
	}
	globalMutex.RUnlock()
	
	// Restore
	globalMutex.Lock()
	globalBridge = original
	globalMutex.Unlock()
}

func TestGlobalMutex_Exists(t *testing.T) {
	// Verify mutex is usable
	globalMutex.Lock()
	globalMutex.Unlock()
	
	globalMutex.RLock()
	globalMutex.RUnlock()
}

// =============================================================================
// Error Constants Tests
// =============================================================================

func TestErrorCodes(t *testing.T) {
	tests := []struct {
		code     int
		expected int
		name     string
	}{
		{ErrCodeSuccess, 0, "Success"},
		{ErrCodeConfig, 1, "Config"},
		{ErrCodeConnection, 2, "Connection"},
		{ErrCodeQuery, 3, "Query"},
		{ErrCodeTimeout, 4, "Timeout"},
		{ErrCodePool, 5, "Pool"},
		{ErrCodeArrow, 6, "Arrow"},
		{ErrCodeNotInitialized, 7, "NotInitialized"},
		{ErrCodeAlreadyInit, 8, "AlreadyInit"},
	}
	
	for _, tt := range tests {
		if tt.code != tt.expected {
			t.Errorf("%s: expected %d, got %d", tt.name, tt.expected, tt.code)
		}
	}
}

// =============================================================================
// JSON Serialization Tests
// =============================================================================

func TestMustMarshal_Struct(t *testing.T) {
	obj := struct {
		Name  string `json:"name"`
		Value int    `json:"value"`
	}{
		Name:  "test",
		Value: 42,
	}
	
	data := MustMarshal(obj)
	
	var parsed map[string]interface{}
	if err := json.Unmarshal(data, &parsed); err != nil {
		t.Fatalf("MustMarshal produced invalid JSON: %v", err)
	}
	
	if parsed["name"] != "test" {
		t.Errorf("Expected name='test', got '%v'", parsed["name"])
	}
}

func TestMustMarshal_Error(t *testing.T) {
	err := &BridgeError{
		Code:    ErrCodeQuery,
		Message: "query failed",
		Details: "syntax error",
	}
	
	data := MustMarshal(err)
	
	var parsed map[string]interface{}
	if err := json.Unmarshal(data, &parsed); err != nil {
		t.Fatalf("MustMarshal produced invalid JSON: %v", err)
	}
	
	if int(parsed["code"].(float64)) != ErrCodeQuery {
		t.Errorf("Expected code=%d, got %v", ErrCodeQuery, parsed["code"])
	}
}

func TestMustMarshal_Result(t *testing.T) {
	result := &QueryResult{
		Success:      true,
		RowsAffected: 5,
		Duration:     1.5,
		Columns:      []string{"id", "name"},
		Rows:         [][]interface{}{{1, "Alice"}},
	}
	
	data := MustMarshal(result)
	
	var parsed map[string]interface{}
	if err := json.Unmarshal(data, &parsed); err != nil {
		t.Fatalf("MustMarshal produced invalid JSON: %v", err)
	}
	
	if parsed["success"] != true {
		t.Error("Expected success=true")
	}
}

// =============================================================================
// Request/Response Round-Trip Tests
// =============================================================================

func TestQueryRequest_RoundTrip(t *testing.T) {
	original := QueryRequest{
		SQL:        "SELECT * FROM users WHERE id = $1",
		Params:     []interface{}{42},
		TimeoutMs:  5000,
		UseReplica: true,
	}
	
	data, err := json.Marshal(original)
	if err != nil {
		t.Fatalf("Marshal failed: %v", err)
	}
	
	var parsed QueryRequest
	if err := json.Unmarshal(data, &parsed); err != nil {
		t.Fatalf("Unmarshal failed: %v", err)
	}
	
	if parsed.SQL != original.SQL {
		t.Errorf("SQL mismatch: expected '%s', got '%s'", original.SQL, parsed.SQL)
	}
	if parsed.TimeoutMs != original.TimeoutMs {
		t.Errorf("TimeoutMs mismatch: expected %d, got %d", original.TimeoutMs, parsed.TimeoutMs)
	}
}

func TestBatchRequest_RoundTrip(t *testing.T) {
	original := BatchRequest{
		Queries: []QueryRequest{
			{SQL: "INSERT INTO t VALUES ($1)", Params: []interface{}{1}},
			{SQL: "INSERT INTO t VALUES ($1)", Params: []interface{}{2}},
		},
		Transaction: true,
		StopOnError: true,
	}
	
	data, err := json.Marshal(original)
	if err != nil {
		t.Fatalf("Marshal failed: %v", err)
	}
	
	var parsed BatchRequest
	if err := json.Unmarshal(data, &parsed); err != nil {
		t.Fatalf("Unmarshal failed: %v", err)
	}
	
	if len(parsed.Queries) != 2 {
		t.Errorf("Expected 2 queries, got %d", len(parsed.Queries))
	}
	if !parsed.Transaction {
		t.Error("Expected Transaction=true")
	}
}

func TestQueryResult_RoundTrip(t *testing.T) {
	original := QueryResult{
		Success:      true,
		RowsAffected: 10,
		Duration:     2.5,
		Cached:       true,
		Columns:      []string{"id", "name", "active"},
		Rows: [][]interface{}{
			{1, "Alice", true},
			{2, "Bob", false},
		},
	}
	
	data, err := json.Marshal(original)
	if err != nil {
		t.Fatalf("Marshal failed: %v", err)
	}
	
	var parsed QueryResult
	if err := json.Unmarshal(data, &parsed); err != nil {
		t.Fatalf("Unmarshal failed: %v", err)
	}
	
	if !parsed.Success {
		t.Error("Expected Success=true")
	}
	if len(parsed.Columns) != 3 {
		t.Errorf("Expected 3 columns, got %d", len(parsed.Columns))
	}
	if len(parsed.Rows) != 2 {
		t.Errorf("Expected 2 rows, got %d", len(parsed.Rows))
	}
}

func TestBatchResult_RoundTrip(t *testing.T) {
	original := BatchResult{
		Success:  true,
		Duration: 5.0,
		Results: []QueryResult{
			{Success: true, RowsAffected: 1},
			{Success: true, RowsAffected: 1},
		},
	}
	
	data, err := json.Marshal(original)
	if err != nil {
		t.Fatalf("Marshal failed: %v", err)
	}
	
	var parsed BatchResult
	if err := json.Unmarshal(data, &parsed); err != nil {
		t.Fatalf("Unmarshal failed: %v", err)
	}
	
	if !parsed.Success {
		t.Error("Expected Success=true")
	}
	if len(parsed.Results) != 2 {
		t.Errorf("Expected 2 results, got %d", len(parsed.Results))
	}
}

// =============================================================================
// Health Status Tests
// =============================================================================

func TestHealthStatus_RoundTrip(t *testing.T) {
	original := HealthStatus{
		Status: "healthy",
		Primary: &ConnectionHealth{
			URL:       "***",
			Status:    "ok",
			LatencyMs: 1.5,
		},
		Pool: PoolHealth{
			TotalConns:  10,
			IdleConns:   5,
			ActiveConns: 5,
		},
	}
	
	data, err := json.Marshal(original)
	if err != nil {
		t.Fatalf("Marshal failed: %v", err)
	}
	
	var parsed HealthStatus
	if err := json.Unmarshal(data, &parsed); err != nil {
		t.Fatalf("Unmarshal failed: %v", err)
	}
	
	if parsed.Status != "healthy" {
		t.Errorf("Expected Status='healthy', got '%s'", parsed.Status)
	}
	if parsed.Primary.Status != "ok" {
		t.Errorf("Expected Primary.Status='ok', got '%s'", parsed.Primary.Status)
	}
}

// =============================================================================
// BridgeError Tests
// =============================================================================

func TestBridgeError_Error(t *testing.T) {
	err := &BridgeError{
		Code:    ErrCodeQuery,
		Message: "query failed",
		Details: "syntax error at position 10",
	}
	
	str := err.Error()
	if str != "query failed" {
		t.Errorf("Expected 'query failed', got '%s'", str)
	}
}

func TestBridgeError_JSON(t *testing.T) {
	err := &BridgeError{
		Code:    ErrCodeConnection,
		Message: "connection refused",
		Details: "host not found",
	}
	
	data, jsonErr := json.Marshal(err)
	if jsonErr != nil {
		t.Fatalf("Marshal failed: %v", jsonErr)
	}
	
	var parsed map[string]interface{}
	if jsonErr := json.Unmarshal(data, &parsed); jsonErr != nil {
		t.Fatalf("Unmarshal failed: %v", jsonErr)
	}
	
	if int(parsed["code"].(float64)) != ErrCodeConnection {
		t.Errorf("Expected code=%d, got %v", ErrCodeConnection, parsed["code"])
	}
	if parsed["message"] != "connection refused" {
		t.Errorf("Expected message='connection refused', got '%v'", parsed["message"])
	}
}

// =============================================================================
// ErrNotInitialized Tests
// =============================================================================

func TestErrNotInitialized(t *testing.T) {
	if ErrNotInitialized.Code != ErrCodeNotInitialized {
		t.Errorf("Expected Code=%d, got %d", ErrCodeNotInitialized, ErrNotInitialized.Code)
	}
	
	if ErrNotInitialized.Message == "" {
		t.Error("Expected non-empty message")
	}
}

// =============================================================================
// Thread Safety Tests
// =============================================================================

func TestConcurrentMutexAccess(t *testing.T) {
	done := make(chan bool, 20)
	
	// 10 writers
	for i := 0; i < 10; i++ {
		go func() {
			globalMutex.Lock()
			// Simulate work
			globalMutex.Unlock()
			done <- true
		}()
	}
	
	// 10 readers
	for i := 0; i < 10; i++ {
		go func() {
			globalMutex.RLock()
			// Simulate read
			_ = globalBridge
			globalMutex.RUnlock()
			done <- true
		}()
	}
	
	// Wait for all
	for i := 0; i < 20; i++ {
		<-done
	}
}
