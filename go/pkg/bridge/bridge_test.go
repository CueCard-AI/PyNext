package bridge

import (
	"encoding/json"
	"testing"
)

// =============================================================================
// DefaultConfig Tests
// =============================================================================

func TestDefaultConfig(t *testing.T) {
	config := DefaultConfig()

	if config.PoolMinSize != 2 {
		t.Errorf("Expected PoolMinSize=2, got %d", config.PoolMinSize)
	}
	if config.PoolMaxSize != 10 {
		t.Errorf("Expected PoolMaxSize=10, got %d", config.PoolMaxSize)
	}
	if config.QueryTimeout != 30000 {
		t.Errorf("Expected QueryTimeout=30000, got %d", config.QueryTimeout)
	}
	if config.EnableArrow != true {
		t.Error("Expected EnableArrow=true")
	}
	if config.EnablePrepared != true {
		t.Error("Expected EnablePrepared=true")
	}
	if config.EnableBatch != true {
		t.Error("Expected EnableBatch=true")
	}
	if config.StatementCache != 256 {
		t.Errorf("Expected StatementCache=256, got %d", config.StatementCache)
	}
}

// =============================================================================
// Config Validation Tests
// =============================================================================

func TestConfigValidate_NoPrimary(t *testing.T) {
	config := Config{Primary: ""}
	err := config.Validate()
	if err != ErrNoPrimaryDSN {
		t.Errorf("Expected ErrNoPrimaryDSN, got %v", err)
	}
}

func TestConfigValidate_InvalidPoolMin(t *testing.T) {
	config := Config{Primary: "postgresql://localhost/test", PoolMinSize: -1}
	err := config.Validate()
	if err != ErrInvalidPoolMin {
		t.Errorf("Expected ErrInvalidPoolMin, got %v", err)
	}
}

func TestConfigValidate_InvalidPoolMax(t *testing.T) {
	config := Config{Primary: "postgresql://localhost/test", PoolMaxSize: 0}
	err := config.Validate()
	if err != ErrInvalidPoolMax {
		t.Errorf("Expected ErrInvalidPoolMax, got %v", err)
	}
}

func TestConfigValidate_PoolMinGtMax(t *testing.T) {
	config := Config{
		Primary:     "postgresql://localhost/test",
		PoolMinSize: 10,
		PoolMaxSize: 5,
	}
	err := config.Validate()
	if err != ErrPoolMinGtMax {
		t.Errorf("Expected ErrPoolMinGtMax, got %v", err)
	}
}

func TestConfigValidate_Valid(t *testing.T) {
	config := Config{
		Primary:     "postgresql://localhost/test",
		PoolMinSize: 2,
		PoolMaxSize: 10,
	}
	err := config.Validate()
	if err != nil {
		t.Errorf("Expected nil, got %v", err)
	}
}

func TestConfigValidate_ZeroPoolMin(t *testing.T) {
	config := Config{
		Primary:     "postgresql://localhost/test",
		PoolMinSize: 0,
		PoolMaxSize: 10,
	}
	err := config.Validate()
	if err != nil {
		t.Errorf("Expected nil for zero PoolMinSize, got %v", err)
	}
}

func TestConfigValidate_EqualMinMax(t *testing.T) {
	config := Config{
		Primary:     "postgresql://localhost/test",
		PoolMinSize: 5,
		PoolMaxSize: 5,
	}
	err := config.Validate()
	if err != nil {
		t.Errorf("Expected nil for equal min/max, got %v", err)
	}
}

// =============================================================================
// ParseConfig Tests
// =============================================================================

func TestParseConfig_Valid(t *testing.T) {
	jsonData := []byte(`{
		"primary": "postgresql://localhost/test",
		"pool_min_size": 5,
		"pool_max_size": 20,
		"query_timeout": 10000
	}`)

	config, err := ParseConfig(jsonData)
	if err != nil {
		t.Fatalf("ParseConfig failed: %v", err)
	}

	if config.Primary != "postgresql://localhost/test" {
		t.Errorf("Expected primary='postgresql://localhost/test', got '%s'", config.Primary)
	}
	if config.PoolMinSize != 5 {
		t.Errorf("Expected PoolMinSize=5, got %d", config.PoolMinSize)
	}
	if config.PoolMaxSize != 20 {
		t.Errorf("Expected PoolMaxSize=20, got %d", config.PoolMaxSize)
	}
	if config.QueryTimeout != 10000 {
		t.Errorf("Expected QueryTimeout=10000, got %d", config.QueryTimeout)
	}
}

func TestParseConfig_InvalidJSON(t *testing.T) {
	jsonData := []byte(`{invalid json}`)

	_, err := ParseConfig(jsonData)
	if err == nil {
		t.Error("Expected error for invalid JSON")
	}

	if be, ok := err.(*BridgeError); ok {
		if be.Code != ErrCodeConfig {
			t.Errorf("Expected error code %d, got %d", ErrCodeConfig, be.Code)
		}
	}
}

func TestParseConfig_MissingPrimary(t *testing.T) {
	jsonData := []byte(`{"pool_max_size": 10}`)

	_, err := ParseConfig(jsonData)
	if err != ErrNoPrimaryDSN {
		t.Errorf("Expected ErrNoPrimaryDSN, got %v", err)
	}
}

func TestParseConfig_DefaultsApplied(t *testing.T) {
	jsonData := []byte(`{"primary": "postgresql://localhost/test"}`)

	config, err := ParseConfig(jsonData)
	if err != nil {
		t.Fatalf("ParseConfig failed: %v", err)
	}

	// Defaults should be applied
	if config.PoolMinSize != 2 {
		t.Errorf("Expected default PoolMinSize=2, got %d", config.PoolMinSize)
	}
	if config.PoolMaxSize != 10 {
		t.Errorf("Expected default PoolMaxSize=10, got %d", config.PoolMaxSize)
	}
	if config.EnableArrow != true {
		t.Error("Expected default EnableArrow=true")
	}
}

func TestParseConfig_WithReplicas(t *testing.T) {
	jsonData := []byte(`{
		"primary": "postgresql://localhost/test",
		"replicas": ["postgresql://replica1/test", "postgresql://replica2/test"]
	}`)

	config, err := ParseConfig(jsonData)
	if err != nil {
		t.Fatalf("ParseConfig failed: %v", err)
	}

	if len(config.Replicas) != 2 {
		t.Errorf("Expected 2 replicas, got %d", len(config.Replicas))
	}
}

// =============================================================================
// QueryRequest Tests
// =============================================================================

func TestQueryRequestJSON(t *testing.T) {
	req := QueryRequest{
		SQL:        "SELECT * FROM users WHERE id = $1",
		Params:     []interface{}{1},
		TimeoutMs:  5000,
		UseReplica: true,
	}

	data, err := json.Marshal(req)
	if err != nil {
		t.Fatalf("Marshal failed: %v", err)
	}

	var parsed QueryRequest
	err = json.Unmarshal(data, &parsed)
	if err != nil {
		t.Fatalf("Unmarshal failed: %v", err)
	}

	if parsed.SQL != req.SQL {
		t.Errorf("Expected SQL='%s', got '%s'", req.SQL, parsed.SQL)
	}
	if parsed.TimeoutMs != req.TimeoutMs {
		t.Errorf("Expected TimeoutMs=%d, got %d", req.TimeoutMs, parsed.TimeoutMs)
	}
	if parsed.UseReplica != req.UseReplica {
		t.Errorf("Expected UseReplica=%v, got %v", req.UseReplica, parsed.UseReplica)
	}
}

func TestQueryRequest_EmptyParams(t *testing.T) {
	req := QueryRequest{SQL: "SELECT 1"}

	data, err := json.Marshal(req)
	if err != nil {
		t.Fatalf("Marshal failed: %v", err)
	}

	var parsed QueryRequest
	err = json.Unmarshal(data, &parsed)
	if err != nil {
		t.Fatalf("Unmarshal failed: %v", err)
	}

	if len(parsed.Params) != 0 {
		t.Errorf("Expected empty params, got %v", parsed.Params)
	}
}

// =============================================================================
// QueryResult Tests
// =============================================================================

func TestQueryResultJSON_Success(t *testing.T) {
	result := QueryResult{
		Success:      true,
		RowsAffected: 5,
		Duration:     1.5,
		Cached:       true,
		Rows:         [][]interface{}{{1, "test"}, {2, "test2"}},
		Columns:      []string{"id", "name"},
	}

	data, err := json.Marshal(result)
	if err != nil {
		t.Fatalf("Marshal failed: %v", err)
	}

	var parsed QueryResult
	err = json.Unmarshal(data, &parsed)
	if err != nil {
		t.Fatalf("Unmarshal failed: %v", err)
	}

	if !parsed.Success {
		t.Error("Expected Success=true")
	}
	if parsed.RowsAffected != 5 {
		t.Errorf("Expected RowsAffected=5, got %d", parsed.RowsAffected)
	}
	if len(parsed.Columns) != 2 {
		t.Errorf("Expected 2 columns, got %d", len(parsed.Columns))
	}
}

func TestQueryResultJSON_Error(t *testing.T) {
	result := QueryResult{
		Success:  false,
		Error:    "connection refused",
		Duration: 0.1,
	}

	data, err := json.Marshal(result)
	if err != nil {
		t.Fatalf("Marshal failed: %v", err)
	}

	var parsed QueryResult
	err = json.Unmarshal(data, &parsed)
	if err != nil {
		t.Fatalf("Unmarshal failed: %v", err)
	}

	if parsed.Success {
		t.Error("Expected Success=false")
	}
	if parsed.Error != "connection refused" {
		t.Errorf("Expected error='connection refused', got '%s'", parsed.Error)
	}
}

// =============================================================================
// BatchRequest/Result Tests
// =============================================================================

func TestBatchRequestJSON(t *testing.T) {
	req := BatchRequest{
		Queries: []QueryRequest{
			{SQL: "INSERT INTO t VALUES ($1)", Params: []interface{}{1}},
			{SQL: "INSERT INTO t VALUES ($1)", Params: []interface{}{2}},
		},
		Transaction: true,
		StopOnError: true,
	}

	data, err := json.Marshal(req)
	if err != nil {
		t.Fatalf("Marshal failed: %v", err)
	}

	var parsed BatchRequest
	err = json.Unmarshal(data, &parsed)
	if err != nil {
		t.Fatalf("Unmarshal failed: %v", err)
	}

	if len(parsed.Queries) != 2 {
		t.Errorf("Expected 2 queries, got %d", len(parsed.Queries))
	}
	if !parsed.Transaction {
		t.Error("Expected Transaction=true")
	}
	if !parsed.StopOnError {
		t.Error("Expected StopOnError=true")
	}
}

func TestBatchResultJSON(t *testing.T) {
	result := BatchResult{
		Success:  true,
		Duration: 10.5,
		Results: []QueryResult{
			{Success: true, RowsAffected: 1},
			{Success: true, RowsAffected: 1},
		},
	}

	data, err := json.Marshal(result)
	if err != nil {
		t.Fatalf("Marshal failed: %v", err)
	}

	var parsed BatchResult
	err = json.Unmarshal(data, &parsed)
	if err != nil {
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
// HealthStatus Tests
// =============================================================================

func TestHealthStatusJSON(t *testing.T) {
	health := HealthStatus{
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

	data, err := json.Marshal(health)
	if err != nil {
		t.Fatalf("Marshal failed: %v", err)
	}

	var parsed HealthStatus
	err = json.Unmarshal(data, &parsed)
	if err != nil {
		t.Fatalf("Unmarshal failed: %v", err)
	}

	if parsed.Status != "healthy" {
		t.Errorf("Expected Status='healthy', got '%s'", parsed.Status)
	}
	if parsed.Primary == nil {
		t.Fatal("Expected Primary to be set")
	}
	if parsed.Primary.Status != "ok" {
		t.Errorf("Expected Primary.Status='ok', got '%s'", parsed.Primary.Status)
	}
}

// =============================================================================
// BridgeError Tests
// =============================================================================

func TestBridgeError_String(t *testing.T) {
	err := &BridgeError{
		Code:    ErrCodeConfig,
		Message: "invalid config",
		Details: "pool_min > pool_max",
	}

	str := err.Error()
	if str != "invalid config" {
		t.Errorf("Expected 'invalid config', got '%s'", str)
	}
}

func TestBridgeError_Codes(t *testing.T) {
	if ErrCodeSuccess != 0 {
		t.Errorf("Expected ErrCodeSuccess=0, got %d", ErrCodeSuccess)
	}
	if ErrCodeConfig != 1 {
		t.Errorf("Expected ErrCodeConfig=1, got %d", ErrCodeConfig)
	}
	if ErrCodeConnection != 2 {
		t.Errorf("Expected ErrCodeConnection=2, got %d", ErrCodeConnection)
	}
	if ErrCodeQuery != 3 {
		t.Errorf("Expected ErrCodeQuery=3, got %d", ErrCodeQuery)
	}
	if ErrCodeTimeout != 4 {
		t.Errorf("Expected ErrCodeTimeout=4, got %d", ErrCodeTimeout)
	}
	if ErrCodePool != 5 {
		t.Errorf("Expected ErrCodePool=5, got %d", ErrCodePool)
	}
	if ErrCodeArrow != 6 {
		t.Errorf("Expected ErrCodeArrow=6, got %d", ErrCodeArrow)
	}
	if ErrCodeNotInitialized != 7 {
		t.Errorf("Expected ErrCodeNotInitialized=7, got %d", ErrCodeNotInitialized)
	}
	if ErrCodeAlreadyInit != 8 {
		t.Errorf("Expected ErrCodeAlreadyInit=8, got %d", ErrCodeAlreadyInit)
	}
}

// =============================================================================
// MaskDSN Tests
// =============================================================================

func TestMaskDSN_Empty(t *testing.T) {
	result := MaskDSN("")
	if result != "" {
		t.Errorf("Expected empty string, got '%s'", result)
	}
}

func TestMaskDSN_NonEmpty(t *testing.T) {
	result := MaskDSN("postgresql://user:password@localhost/db")
	if result != "***" {
		t.Errorf("Expected '***', got '%s'", result)
	}
}

// =============================================================================
// MustMarshal Tests
// =============================================================================

func TestMustMarshal_Simple(t *testing.T) {
	data := map[string]int{"a": 1, "b": 2}
	result := MustMarshal(data)

	if len(result) == 0 {
		t.Error("Expected non-empty result")
	}

	// Should be valid JSON
	var parsed map[string]int
	err := json.Unmarshal(result, &parsed)
	if err != nil {
		t.Errorf("Result is not valid JSON: %v", err)
	}
}

// =============================================================================
// Global State Tests
// =============================================================================

func TestGlobalBridge_NotInitialized(t *testing.T) {
	globalMutex.Lock()
	originalBridge := globalBridge
	globalBridge = nil
	globalMutex.Unlock()

	// Verify nil state
	globalMutex.RLock()
	if globalBridge != nil {
		t.Error("Expected globalBridge to be nil")
	}
	globalMutex.RUnlock()

	// Restore
	globalMutex.Lock()
	globalBridge = originalBridge
	globalMutex.Unlock()
}
