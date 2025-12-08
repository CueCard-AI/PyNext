package query

import (
	"strings"
	"testing"
)

// =============================================================================
// Basic SQL Generation Tests
// =============================================================================

func TestGenerator_SelectAll(t *testing.T) {
	gen := NewGenerator()
	ast := &QueryAST{
		Table: "users",
		Type:  QueryTypeSelect,
	}

	result, err := gen.Generate(ast)
	if err != nil {
		t.Fatalf("Generate() error = %v", err)
	}

	if !strings.Contains(result.SQL, "SELECT") {
		t.Errorf("SQL should contain SELECT: %s", result.SQL)
	}
	if !strings.Contains(result.SQL, "users") {
		t.Errorf("SQL should contain table name: %s", result.SQL)
	}
	if len(result.Params) != 0 {
		t.Errorf("Params = %v, want empty", result.Params)
	}
}

func TestGenerator_SelectColumns(t *testing.T) {
	gen := NewGenerator()
	ast := &QueryAST{
		Table:   "users",
		Type:    QueryTypeSelect,
		Columns: []string{"id", "name", "email"},
	}

	result, err := gen.Generate(ast)
	if err != nil {
		t.Fatalf("Generate() error = %v", err)
	}

	if !strings.Contains(result.SQL, "id") {
		t.Errorf("SQL should contain 'id' column: %s", result.SQL)
	}
	if !strings.Contains(result.SQL, "name") {
		t.Errorf("SQL should contain 'name' column: %s", result.SQL)
	}
	if !strings.Contains(result.SQL, "email") {
		t.Errorf("SQL should contain 'email' column: %s", result.SQL)
	}
}

func TestGenerator_SelectDistinct(t *testing.T) {
	gen := NewGenerator()
	ast := &QueryAST{
		Table:    "users",
		Type:     QueryTypeSelect,
		Columns:  []string{"status"},
		Distinct: true,
	}

	result, err := gen.Generate(ast)
	if err != nil {
		t.Fatalf("Generate() error = %v", err)
	}

	if !strings.Contains(result.SQL, "DISTINCT") {
		t.Errorf("SQL should contain DISTINCT: %s", result.SQL)
	}
}

// =============================================================================
// Condition Generation Tests
// =============================================================================

func TestGenerator_SimpleConditions(t *testing.T) {
	tests := []struct {
		name      string
		op        string
		value     interface{}
		wantParam bool
	}{
		{"equality", "=", "active", true},
		{"not equal", "!=", "deleted", true},
		{"greater than", ">", 18, true},
		{"greater or equal", ">=", 21, true},
		{"less than", "<", 100, true},
		{"less or equal", "<=", 50, true},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			gen := NewGenerator()
			ast := &QueryAST{
				Table: "users",
				Type:  QueryTypeSelect,
				Conditions: &ConditionNode{
					Type:  "condition",
					Field: "field",
					Op:    tt.op,
					Value: tt.value,
				},
			}

			result, err := gen.Generate(ast)
			if err != nil {
				t.Fatalf("Generate() error = %v", err)
			}

			if !strings.Contains(result.SQL, "WHERE") {
				t.Errorf("SQL should contain WHERE: %s", result.SQL)
			}
			if tt.wantParam && len(result.Params) == 0 {
				t.Error("Expected params, got none")
			}
		})
	}
}

func TestGenerator_InCondition(t *testing.T) {
	gen := NewGenerator()
	ast := &QueryAST{
		Table: "users",
		Type:  QueryTypeSelect,
		Conditions: &ConditionNode{
			Type:  "condition",
			Field: "role",
			Op:    "IN",
			Value: []interface{}{"admin", "moderator", "user"},
		},
	}

	result, err := gen.Generate(ast)
	if err != nil {
		t.Fatalf("Generate() error = %v", err)
	}

	if !strings.Contains(result.SQL, "IN") {
		t.Errorf("SQL should contain IN: %s", result.SQL)
	}
}

func TestGenerator_BetweenCondition(t *testing.T) {
	gen := NewGenerator()
	ast := &QueryAST{
		Table: "users",
		Type:  QueryTypeSelect,
		Conditions: &ConditionNode{
			Type:   "condition",
			Field:  "age",
			Op:     "BETWEEN",
			Value:  18,
			Value2: 65,
		},
	}

	result, err := gen.Generate(ast)
	if err != nil {
		t.Fatalf("Generate() error = %v", err)
	}

	if !strings.Contains(result.SQL, "BETWEEN") {
		t.Errorf("SQL should contain BETWEEN: %s", result.SQL)
	}
}

func TestGenerator_IsNullCondition(t *testing.T) {
	gen := NewGenerator()
	ast := &QueryAST{
		Table: "users",
		Type:  QueryTypeSelect,
		Conditions: &ConditionNode{
			Type:  "condition",
			Field: "deleted_at",
			Op:    "IS NULL",
		},
	}

	result, err := gen.Generate(ast)
	if err != nil {
		t.Fatalf("Generate() error = %v", err)
	}

	if !strings.Contains(result.SQL, "IS NULL") {
		t.Errorf("SQL should contain IS NULL: %s", result.SQL)
	}
	if len(result.Params) != 0 {
		t.Errorf("IS NULL should have no params, got %d", len(result.Params))
	}
}

// =============================================================================
// Logical Condition Tests
// =============================================================================

func TestGenerator_ANDCondition(t *testing.T) {
	gen := NewGenerator()
	ast := &QueryAST{
		Table: "users",
		Type:  QueryTypeSelect,
		Conditions: &ConditionNode{
			Type: "logical",
			Op:   "AND",
			Conditions: []ConditionNode{
				{Type: "condition", Field: "age", Op: ">", Value: 18},
				{Type: "condition", Field: "status", Op: "=", Value: "active"},
			},
		},
	}

	result, err := gen.Generate(ast)
	if err != nil {
		t.Fatalf("Generate() error = %v", err)
	}

	if !strings.Contains(result.SQL, "AND") {
		t.Errorf("SQL should contain AND: %s", result.SQL)
	}
	if len(result.Params) != 2 {
		t.Errorf("Expected 2 params, got %d", len(result.Params))
	}
}

func TestGenerator_ORCondition(t *testing.T) {
	gen := NewGenerator()
	ast := &QueryAST{
		Table: "users",
		Type:  QueryTypeSelect,
		Conditions: &ConditionNode{
			Type: "logical",
			Op:   "OR",
			Conditions: []ConditionNode{
				{Type: "condition", Field: "role", Op: "=", Value: "admin"},
				{Type: "condition", Field: "role", Op: "=", Value: "moderator"},
			},
		},
	}

	result, err := gen.Generate(ast)
	if err != nil {
		t.Fatalf("Generate() error = %v", err)
	}

	if !strings.Contains(result.SQL, "OR") {
		t.Errorf("SQL should contain OR: %s", result.SQL)
	}
}

func TestGenerator_NestedConditions(t *testing.T) {
	gen := NewGenerator()
	ast := &QueryAST{
		Table: "users",
		Type:  QueryTypeSelect,
		Conditions: &ConditionNode{
			Type: "logical",
			Op:   "AND",
			Conditions: []ConditionNode{
				{Type: "condition", Field: "age", Op: ">", Value: 18},
				{
					Type: "logical",
					Op:   "OR",
					Conditions: []ConditionNode{
						{Type: "condition", Field: "role", Op: "=", Value: "admin"},
						{Type: "condition", Field: "role", Op: "=", Value: "moderator"},
					},
				},
			},
		},
	}

	result, err := gen.Generate(ast)
	if err != nil {
		t.Fatalf("Generate() error = %v", err)
	}

	if !strings.Contains(result.SQL, "AND") {
		t.Errorf("SQL should contain AND: %s", result.SQL)
	}
	if !strings.Contains(result.SQL, "OR") {
		t.Errorf("SQL should contain OR: %s", result.SQL)
	}
	if len(result.Params) != 3 {
		t.Errorf("Expected 3 params, got %d", len(result.Params))
	}
}

// =============================================================================
// Raw SQL Condition Tests
// =============================================================================

func TestGenerator_RawCondition(t *testing.T) {
	gen := NewGenerator()
	ast := &QueryAST{
		Table: "users",
		Type:  QueryTypeSelect,
		Conditions: &ConditionNode{
			Type: "raw",
			SQL:  "custom_func(data) > 10",
		},
	}

	result, err := gen.Generate(ast)
	if err != nil {
		t.Fatalf("Generate() error = %v", err)
	}

	if !strings.Contains(result.SQL, "custom_func(data) > 10") {
		t.Errorf("SQL should contain raw SQL: %s", result.SQL)
	}
}

func TestGenerator_RawConditionWithParams(t *testing.T) {
	gen := NewGenerator()
	ast := &QueryAST{
		Table: "users",
		Type:  QueryTypeSelect,
		Conditions: &ConditionNode{
			Type:   "raw",
			SQL:    "jsonb_col @> $1",
			Params: []interface{}{`{"key": "value"}`},
		},
	}

	result, err := gen.Generate(ast)
	if err != nil {
		t.Fatalf("Generate() error = %v", err)
	}

	if !strings.Contains(result.SQL, "@>") {
		t.Errorf("SQL should contain raw operator: %s", result.SQL)
	}
}

// =============================================================================
// ORDER BY Tests
// =============================================================================

func TestGenerator_OrderByASC(t *testing.T) {
	gen := NewGenerator()
	ast := &QueryAST{
		Table: "users",
		Type:  QueryTypeSelect,
		Order: []OrderNode{{Field: "name", Direction: "ASC"}},
	}

	result, err := gen.Generate(ast)
	if err != nil {
		t.Fatalf("Generate() error = %v", err)
	}

	if !strings.Contains(result.SQL, "ORDER BY") {
		t.Errorf("SQL should contain ORDER BY: %s", result.SQL)
	}
	if !strings.Contains(result.SQL, "ASC") {
		t.Errorf("SQL should contain ASC: %s", result.SQL)
	}
}

func TestGenerator_OrderByDESC(t *testing.T) {
	gen := NewGenerator()
	ast := &QueryAST{
		Table: "users",
		Type:  QueryTypeSelect,
		Order: []OrderNode{{Field: "created_at", Direction: "DESC"}},
	}

	result, err := gen.Generate(ast)
	if err != nil {
		t.Fatalf("Generate() error = %v", err)
	}

	if !strings.Contains(result.SQL, "DESC") {
		t.Errorf("SQL should contain DESC: %s", result.SQL)
	}
}

func TestGenerator_MultipleOrderBy(t *testing.T) {
	gen := NewGenerator()
	ast := &QueryAST{
		Table: "users",
		Type:  QueryTypeSelect,
		Order: []OrderNode{
			{Field: "status", Direction: "ASC"},
			{Field: "age", Direction: "DESC"},
		},
	}

	result, err := gen.Generate(ast)
	if err != nil {
		t.Fatalf("Generate() error = %v", err)
	}

	if !strings.Contains(result.SQL, "ORDER BY") {
		t.Errorf("SQL should contain ORDER BY: %s", result.SQL)
	}
}

// =============================================================================
// LIMIT/OFFSET Tests
// =============================================================================

func TestGenerator_Limit(t *testing.T) {
	gen := NewGenerator()
	ast := &QueryAST{
		Table: "users",
		Type:  QueryTypeSelect,
		Limit: intPtr(10),
	}

	result, err := gen.Generate(ast)
	if err != nil {
		t.Fatalf("Generate() error = %v", err)
	}

	if !strings.Contains(result.SQL, "LIMIT") {
		t.Errorf("SQL should contain LIMIT: %s", result.SQL)
	}
}

func TestGenerator_Offset(t *testing.T) {
	gen := NewGenerator()
	ast := &QueryAST{
		Table:  "users",
		Type:   QueryTypeSelect,
		Offset: intPtr(20),
	}

	result, err := gen.Generate(ast)
	if err != nil {
		t.Fatalf("Generate() error = %v", err)
	}

	if !strings.Contains(result.SQL, "OFFSET") {
		t.Errorf("SQL should contain OFFSET: %s", result.SQL)
	}
}

func TestGenerator_LimitOffset(t *testing.T) {
	gen := NewGenerator()
	ast := &QueryAST{
		Table:  "users",
		Type:   QueryTypeSelect,
		Limit:  intPtr(10),
		Offset: intPtr(20),
	}

	result, err := gen.Generate(ast)
	if err != nil {
		t.Fatalf("Generate() error = %v", err)
	}

	if !strings.Contains(result.SQL, "LIMIT") {
		t.Errorf("SQL should contain LIMIT: %s", result.SQL)
	}
	if !strings.Contains(result.SQL, "OFFSET") {
		t.Errorf("SQL should contain OFFSET: %s", result.SQL)
	}
}

// =============================================================================
// FOR UPDATE Tests
// =============================================================================

func TestGenerator_ForUpdate(t *testing.T) {
	gen := NewGenerator()
	ast := &QueryAST{
		Table:     "users",
		Type:      QueryTypeSelect,
		ForUpdate: true,
	}

	result, err := gen.Generate(ast)
	if err != nil {
		t.Fatalf("Generate() error = %v", err)
	}

	if !strings.Contains(result.SQL, "FOR UPDATE") {
		t.Errorf("SQL should contain FOR UPDATE: %s", result.SQL)
	}
}

// =============================================================================
// Raw SQL Tests
// =============================================================================

func TestGenerator_RawSQL(t *testing.T) {
	gen := NewGenerator()
	ast := &QueryAST{
		Table:  "users",
		Type:   QueryTypeRaw,
		RawSQL: "SELECT * FROM users WHERE custom_func(data) > $1",
		Params: []interface{}{100},
	}

	result, err := gen.Generate(ast)
	if err != nil {
		t.Fatalf("Generate() error = %v", err)
	}

	if result.SQL != "SELECT * FROM users WHERE custom_func(data) > $1" {
		t.Errorf("Raw SQL should be passed through: %s", result.SQL)
	}
	if len(result.Params) != 1 || result.Params[0] != 100 {
		t.Errorf("Raw params should be passed through: %v", result.Params)
	}
}

// =============================================================================
// Complex Query Tests
// =============================================================================

func TestGenerator_ComplexQuery(t *testing.T) {
	gen := NewGenerator()
	ast := &QueryAST{
		Table:   "users",
		Type:    QueryTypeSelect,
		Columns: []string{"id", "name", "email", "age"},
		Conditions: &ConditionNode{
			Type: "logical",
			Op:   "AND",
			Conditions: []ConditionNode{
				{Type: "condition", Field: "age", Op: ">", Value: 18},
				{Type: "condition", Field: "status", Op: "=", Value: "active"},
				{
					Type: "logical",
					Op:   "OR",
					Conditions: []ConditionNode{
						{Type: "condition", Field: "role", Op: "=", Value: "admin"},
						{Type: "condition", Field: "role", Op: "=", Value: "moderator"},
					},
				},
			},
		},
		Order: []OrderNode{
			{Field: "created_at", Direction: "DESC"},
			{Field: "name", Direction: "ASC"},
		},
		Limit:  intPtr(10),
		Offset: intPtr(20),
	}

	result, err := gen.Generate(ast)
	if err != nil {
		t.Fatalf("Generate() error = %v", err)
	}

	// Verify all parts are present
	requiredParts := []string{
		"SELECT",
		"FROM",
		"WHERE",
		"ORDER BY",
		"LIMIT",
		"OFFSET",
	}

	for _, part := range requiredParts {
		if !strings.Contains(result.SQL, part) {
			t.Errorf("SQL should contain %s: %s", part, result.SQL)
		}
	}

	// Should have 4 params: age, status, role1, role2
	if len(result.Params) != 4 {
		t.Errorf("Expected 4 params, got %d", len(result.Params))
	}

	t.Logf("Complex SQL: %s", result.SQL)
	t.Logf("Params: %v", result.Params)
}
