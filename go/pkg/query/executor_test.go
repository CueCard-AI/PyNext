package query

import (
	"testing"
)

// =============================================================================
// Executor Initialization Tests
// =============================================================================

func TestNewExecutor(t *testing.T) {
	exec := NewExecutor(nil, nil)
	if exec == nil {
		t.Error("NewExecutor() returned nil")
	}
}

func TestNewExecutor_WithConfig(t *testing.T) {
	config := &ExecutorConfig{
		StrictMode:    true,
		MaxComplexity: 50,
	}
	exec := NewExecutor(nil, config)

	if exec == nil {
		t.Error("NewExecutor() returned nil")
	}
	if !exec.strictMode {
		t.Error("StrictMode not applied from config")
	}
	if exec.maxComplexity != 50 {
		t.Errorf("MaxComplexity = %d, want 50", exec.maxComplexity)
	}
}

func TestDefaultExecutorConfig(t *testing.T) {
	config := DefaultExecutorConfig()

	if config == nil {
		t.Fatal("DefaultExecutorConfig() returned nil")
	}
	if config.QueryTimeout <= 0 {
		t.Error("Default QueryTimeout should be positive")
	}
	if config.MaxComplexity <= 0 {
		t.Error("Default MaxComplexity should be positive")
	}
}

// =============================================================================
// Explain Tests (SQL Generation without Execution)
// =============================================================================

func TestExecutor_Explain_SimpleSelect(t *testing.T) {
	exec := NewExecutor(nil, nil)

	astJSON := []byte(`{
		"table": "users",
		"type": "SELECT"
	}`)

	sql, params, err := exec.Explain(astJSON)
	if err != nil {
		t.Fatalf("Explain() error = %v", err)
	}

	if sql == "" {
		t.Error("SQL should not be empty")
	}
	if params == nil {
		t.Error("Params should not be nil")
	}
	t.Logf("Generated SQL: %s", sql)
}

func TestExecutor_Explain_WithConditions(t *testing.T) {
	exec := NewExecutor(nil, nil)

	astJSON := []byte(`{
		"table": "users",
		"type": "SELECT",
		"conditions": {
			"type": "condition",
			"field": "age",
			"op": ">",
			"value": 18
		}
	}`)

	sql, params, err := exec.Explain(astJSON)
	if err != nil {
		t.Fatalf("Explain() error = %v", err)
	}

	if len(params) != 1 {
		t.Errorf("Expected 1 param, got %d", len(params))
	}
	t.Logf("Generated SQL: %s", sql)
	t.Logf("Params: %v", params)
}

func TestExecutor_Explain_MultipleConditions(t *testing.T) {
	exec := NewExecutor(nil, nil)

	astJSON := []byte(`{
		"table": "users",
		"type": "SELECT",
		"conditions": {
			"type": "logical",
			"op": "AND",
			"conditions": [
				{"type": "condition", "field": "age", "op": ">", "value": 18},
				{"type": "condition", "field": "status", "op": "=", "value": "active"}
			]
		}
	}`)

	sql, params, err := exec.Explain(astJSON)
	if err != nil {
		t.Fatalf("Explain() error = %v", err)
	}

	if len(params) != 2 {
		t.Errorf("Expected 2 params, got %d", len(params))
	}
	t.Logf("Generated SQL: %s", sql)
	t.Logf("Params: %v", params)
}

func TestExecutor_Explain_WithOrderAndLimit(t *testing.T) {
	exec := NewExecutor(nil, nil)

	astJSON := []byte(`{
		"table": "users",
		"type": "SELECT",
		"columns": ["id", "name"],
		"order": [{"field": "created_at", "direction": "DESC"}],
		"limit": 10,
		"offset": 20
	}`)

	sql, _, err := exec.Explain(astJSON)
	if err != nil {
		t.Fatalf("Explain() error = %v", err)
	}

	t.Logf("Generated SQL: %s", sql)
}

func TestExecutor_Explain_ComplexQuery(t *testing.T) {
	exec := NewExecutor(nil, nil)

	astJSON := []byte(`{
		"table": "users",
		"type": "SELECT",
		"columns": ["id", "name", "email"],
		"conditions": {
			"type": "logical",
			"op": "AND",
			"conditions": [
				{"type": "condition", "field": "age", "op": ">", "value": 18},
				{"type": "condition", "field": "status", "op": "=", "value": "active"},
				{
					"type": "logical",
					"op": "OR",
					"conditions": [
						{"type": "condition", "field": "role", "op": "=", "value": "admin"},
						{"type": "condition", "field": "role", "op": "=", "value": "moderator"}
					]
				}
			]
		},
		"order": [{"field": "created_at", "direction": "DESC"}],
		"limit": 10,
		"offset": 20
	}`)

	sql, params, err := exec.Explain(astJSON)
	if err != nil {
		t.Fatalf("Explain() error = %v", err)
	}

	// Optimizer may collapse OR of same field into IN, so params count varies
	if len(params) < 3 {
		t.Errorf("Expected at least 3 params, got %d", len(params))
	}

	t.Logf("Complex query SQL: %s", sql)
	t.Logf("Params: %v", params)
}

// =============================================================================
// Error Cases
// =============================================================================

func TestExecutor_Explain_InvalidJSON(t *testing.T) {
	exec := NewExecutor(nil, nil)

	astJSON := []byte(`{invalid json}`)

	_, _, err := exec.Explain(astJSON)
	if err == nil {
		t.Error("Expected error for invalid JSON")
	}
}

func TestExecutor_Explain_MissingTable(t *testing.T) {
	exec := NewExecutor(nil, nil)

	astJSON := []byte(`{
		"table": "",
		"type": "SELECT"
	}`)

	_, _, err := exec.Explain(astJSON)
	if err == nil {
		t.Error("Expected error for missing table")
	}
}

// =============================================================================
// Strict Mode Tests
// =============================================================================

func TestExecutor_StrictMode_Validates(t *testing.T) {
	config := &ExecutorConfig{
		StrictMode: true,
	}
	exec := NewExecutor(nil, config)

	if !exec.strictMode {
		t.Error("Strict mode not enabled")
	}
}

// =============================================================================
// Complexity Limit Tests
// =============================================================================

func TestExecutor_ComplexityLimit(t *testing.T) {
	config := &ExecutorConfig{
		MaxComplexity: 2, // Very low limit for testing
	}
	exec := NewExecutor(nil, config)

	if exec.maxComplexity != 2 {
		t.Errorf("MaxComplexity = %d, want 2", exec.maxComplexity)
	}
}
