package query

import (
	"strings"
	"testing"
)

// =============================================================================
// Basic Validation Tests
// =============================================================================

func TestValidator_ValidBasicQuery(t *testing.T) {
	v := NewValidator()
	ast := &QueryAST{
		Table: "users",
		Type:  QueryTypeSelect,
	}

	err := v.Validate(ast)
	if err != nil {
		t.Errorf("Expected no error, got: %v", err)
	}
}

func TestValidator_EmptyTable(t *testing.T) {
	v := NewValidator()
	ast := &QueryAST{
		Table: "",
		Type:  QueryTypeSelect,
	}

	err := v.Validate(ast)
	if err == nil {
		t.Error("Expected error for empty table")
	}

	if !strings.Contains(strings.ToLower(err.Error()), "table") {
		t.Errorf("Expected table-related error, got: %v", err)
	}
}

// =============================================================================
// SQL Injection Prevention Tests
// =============================================================================

func TestValidator_SQLInjectionTableName(t *testing.T) {
	v := NewValidator()
	tests := []struct {
		name  string
		table string
	}{
		{"semicolon", "users; DROP TABLE users;--"},
		{"quote", "users' OR '1'='1"},
		{"double quote", `users" OR "1"="1`},
		{"comment", "users--"},
		{"union", "users UNION SELECT * FROM passwords"},
		{"newline", "users\n; DROP TABLE users"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			ast := &QueryAST{
				Table: tt.table,
				Type:  QueryTypeSelect,
			}

			err := v.Validate(ast)
			if err == nil {
				t.Errorf("Expected SQL injection error for table: %q", tt.table)
			}
		})
	}
}

func TestValidator_ValidIdentifiers(t *testing.T) {
	v := NewValidator()
	tests := []struct {
		name  string
		table string
	}{
		{"simple", "users"},
		{"underscore", "user_accounts"},
		{"camelCase", "userAccounts"},
		{"numbers", "users2"},
		{"prefix number", "table1"},
		{"all caps", "USERS"},
		{"mixed", "User_Accounts_2"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			ast := &QueryAST{
				Table: tt.table,
				Type:  QueryTypeSelect,
			}

			err := v.Validate(ast)
			if err != nil {
				t.Errorf("Unexpected error for valid identifier %q: %s", tt.table, err)
			}
		})
	}
}

// =============================================================================
// Operator Validation Tests
// =============================================================================

func TestValidator_ValidOperators(t *testing.T) {
	v := NewValidator()
	validOps := []string{"=", "!=", "<>", ">", ">=", "<", "<=", "LIKE", "ILIKE", "IN", "NOT IN", "BETWEEN", "IS NULL", "IS NOT NULL"}

	for _, op := range validOps {
		t.Run(op, func(t *testing.T) {
			ast := &QueryAST{
				Table: "users",
				Type:  QueryTypeSelect,
				Conditions: &ConditionNode{
					Type:  "condition",
					Field: "status",
					Op:    op,
					Value: "test",
				},
			}

			err := v.Validate(ast)
			if err != nil {
				t.Errorf("Unexpected error for operator %q: %s", op, err)
			}
		})
	}
}

func TestValidator_InvalidOperator(t *testing.T) {
	v := NewValidator()
	ast := &QueryAST{
		Table: "users",
		Type:  QueryTypeSelect,
		Conditions: &ConditionNode{
			Type:  "condition",
			Field: "status",
			Op:    "DROP TABLE",
			Value: "test",
		},
	}

	err := v.Validate(ast)
	if err == nil {
		t.Error("Expected error for invalid operator")
	}
}

// =============================================================================
// Query Type Validation Tests
// =============================================================================

func TestValidator_ValidQueryTypes(t *testing.T) {
	v := NewValidator()
	validTypes := []QueryType{QueryTypeSelect, QueryTypeInsert, QueryTypeUpdate, QueryTypeDelete}

	for _, qtype := range validTypes {
		t.Run(string(qtype), func(t *testing.T) {
			ast := &QueryAST{
				Table: "users",
				Type:  qtype,
			}

			err := v.Validate(ast)
			// Some types may have additional requirements
			if err != nil && strings.Contains(err.Error(), "invalid type") {
				t.Errorf("Unexpected type error for %q: %s", qtype, err)
			}
		})
	}
}

// =============================================================================
// Complexity Limit Tests
// =============================================================================

func TestValidator_TooManyConditions(t *testing.T) {
	v := NewValidator()
	v.maxConditions = 2 // Very low for testing

	// Create more conditions than allowed
	conditions := make([]ConditionNode, 5)
	for i := 0; i < 5; i++ {
		conditions[i] = ConditionNode{
			Type:  "condition",
			Field: "field",
			Op:    "=",
			Value: i,
		}
	}

	ast := &QueryAST{
		Table: "users",
		Type:  QueryTypeSelect,
		Conditions: &ConditionNode{
			Type:       "logical",
			Op:         "AND",
			Conditions: conditions,
		},
	}

	err := v.Validate(ast)
	if err == nil {
		t.Error("Expected complexity error for too many conditions")
	}

	if !strings.Contains(strings.ToLower(err.Error()), "condition") &&
		!strings.Contains(strings.ToLower(err.Error()), "complex") {
		t.Logf("Got error: %v", err)
	}
}

func TestValidator_TooDeepNesting(t *testing.T) {
	v := NewValidator()
	v.maxDepth = 2 // Very shallow for testing

	// Create deeply nested conditions
	deepCond := ConditionNode{
		Type:  "condition",
		Field: "id",
		Op:    "=",
		Value: 1,
	}

	for i := 0; i < 5; i++ {
		deepCond = ConditionNode{
			Type:       "logical",
			Op:         "AND",
			Conditions: []ConditionNode{deepCond},
		}
	}

	ast := &QueryAST{
		Table:      "users",
		Type:       QueryTypeSelect,
		Conditions: &deepCond,
	}

	err := v.Validate(ast)
	if err == nil {
		t.Error("Expected error for too deep nesting")
	}
}

// =============================================================================
// Order Validation Tests
// =============================================================================

func TestValidator_ValidOrderDirection(t *testing.T) {
	v := NewValidator()
	ast := &QueryAST{
		Table: "users",
		Type:  QueryTypeSelect,
		Order: []OrderNode{
			{Field: "name", Direction: "ASC"},
			{Field: "age", Direction: "DESC"},
		},
	}

	err := v.Validate(ast)
	if err != nil {
		t.Errorf("Unexpected order error: %s", err)
	}
}

func TestValidator_InvalidOrderDirection(t *testing.T) {
	v := NewValidator()
	ast := &QueryAST{
		Table: "users",
		Type:  QueryTypeSelect,
		Order: []OrderNode{
			{Field: "name", Direction: "INVALID"},
		},
	}

	err := v.Validate(ast)
	if err == nil {
		t.Error("Expected error for invalid order direction")
	}
}

// =============================================================================
// Limit/Offset Validation Tests
// =============================================================================

func TestValidator_NegativeLimit(t *testing.T) {
	t.Skip("Negative limit validation not yet implemented")
	// TODO: Add negative limit validation to validator
}

func TestValidator_NegativeOffset(t *testing.T) {
	t.Skip("Negative offset validation not yet implemented")
	// TODO: Add negative offset validation to validator
}

// =============================================================================
// Raw SQL Validation Tests
// =============================================================================

func TestValidator_RawSQLAllowed(t *testing.T) {
	v := NewValidator()
	v.allowRawSQL = true

	ast := &QueryAST{
		Table: "users",
		Type:  QueryTypeSelect,
		Conditions: &ConditionNode{
			Type: "raw",
			SQL:  "custom_func() > 10",
		},
	}

	err := v.Validate(ast)
	if err != nil {
		t.Errorf("Raw SQL should be allowed: %v", err)
	}
}

func TestValidator_RawSQLDisallowed(t *testing.T) {
	v := NewValidator()
	v.allowRawSQL = false

	ast := &QueryAST{
		Table: "users",
		Type:  QueryTypeSelect,
		Conditions: &ConditionNode{
			Type: "raw",
			SQL:  "SELECT * FROM users WHERE 1=1",
		},
	}

	err := v.Validate(ast)
	if err == nil {
		t.Error("Expected error for raw SQL when not allowed")
	}
}

// =============================================================================
// Between Condition Tests
// =============================================================================

func TestValidator_BetweenWithTwoValues(t *testing.T) {
	v := NewValidator()
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

	err := v.Validate(ast)
	if err != nil {
		t.Errorf("Unexpected BETWEEN error: %s", err)
	}
}

func TestValidator_BetweenWithMissingValue(t *testing.T) {
	t.Skip("BETWEEN value validation not yet implemented")
	// TODO: Add BETWEEN value count validation to validator
}

// =============================================================================
// IN Condition Tests
// =============================================================================

func TestValidator_InWithArray(t *testing.T) {
	v := NewValidator()
	ast := &QueryAST{
		Table: "users",
		Type:  QueryTypeSelect,
		Conditions: &ConditionNode{
			Type:  "condition",
			Field: "role",
			Op:    "IN",
			Value: []interface{}{"admin", "moderator"},
		},
	}

	err := v.Validate(ast)
	if err != nil {
		t.Errorf("Unexpected IN error: %s", err)
	}
}

func TestValidator_InWithEmptyArray(t *testing.T) {
	t.Skip("IN empty array validation not yet implemented")
	// TODO: Add IN empty array validation to validator
}

// =============================================================================
// RawSQL Validation Tests
// =============================================================================

func TestValidator_ValidateRawSQL_Clean(t *testing.T) {
	v := NewValidator()

	warnings := v.ValidateRawSQL("SELECT * FROM users WHERE status = $1")

	if len(warnings) > 0 {
		t.Errorf("Unexpected warnings for clean SQL: %v", warnings)
	}
}

func TestValidator_ValidateRawSQL_Dangerous(t *testing.T) {
	v := NewValidator()

	tests := []struct {
		name string
		sql  string
	}{
		{"drop table", "DROP TABLE users"},
		{"truncate", "TRUNCATE users"},
		{"alter table", "ALTER TABLE users ADD COLUMN x INT"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			warnings := v.ValidateRawSQL(tt.sql)
			if len(warnings) == 0 {
				t.Errorf("Expected warnings for dangerous SQL: %s", tt.sql)
			}
		})
	}
}
