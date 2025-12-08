package query

import (
	"testing"
)

// =============================================================================
// Optimizer Basic Tests
// =============================================================================

func TestOptimizer_NoConditions(t *testing.T) {
	opt := NewOptimizer()
	ast := &QueryAST{
		Table: "users",
		Type:  QueryTypeSelect,
	}

	result := opt.Optimize(ast)

	if result == nil {
		t.Error("Optimize() returned nil")
	}
	if result.Table != "users" {
		t.Errorf("Table changed: %s", result.Table)
	}
}

func TestOptimizer_SimpleCondition(t *testing.T) {
	opt := NewOptimizer()
	ast := &QueryAST{
		Table: "users",
		Type:  QueryTypeSelect,
		Conditions: &ConditionNode{
			Type:  "condition",
			Field: "id",
			Op:    "=",
			Value: 1,
		},
	}

	result := opt.Optimize(ast)

	if result.Conditions == nil {
		t.Error("Optimize() removed conditions")
	}
}

// =============================================================================
// Condition Flattening Tests
// =============================================================================

func TestOptimizer_FlattenNestedAND(t *testing.T) {
	opt := NewOptimizer()
	// (a AND (b AND c)) should become (a AND b AND c)
	ast := &QueryAST{
		Table: "users",
		Type:  QueryTypeSelect,
		Conditions: &ConditionNode{
			Type: "logical",
			Op:   "AND",
			Conditions: []ConditionNode{
				{Type: "condition", Field: "a", Op: "=", Value: 1},
				{
					Type: "logical",
					Op:   "AND",
					Conditions: []ConditionNode{
						{Type: "condition", Field: "b", Op: "=", Value: 2},
						{Type: "condition", Field: "c", Op: "=", Value: 3},
					},
				},
			},
		},
	}

	result := opt.Optimize(ast)

	if result.Conditions == nil {
		t.Fatal("Optimize() removed conditions")
	}

	// After flattening, should have 3 items in top-level AND
	if result.Conditions.Op != "AND" {
		t.Errorf("Expected AND, got %s", result.Conditions.Op)
	}
	if len(result.Conditions.Conditions) != 3 {
		t.Errorf("Expected 3 flattened items, got %d", len(result.Conditions.Conditions))
	}
}

func TestOptimizer_FlattenNestedOR(t *testing.T) {
	opt := NewOptimizer()
	// (a OR (b OR c)) should become (a OR b OR c)
	ast := &QueryAST{
		Table: "users",
		Type:  QueryTypeSelect,
		Conditions: &ConditionNode{
			Type: "logical",
			Op:   "OR",
			Conditions: []ConditionNode{
				{Type: "condition", Field: "a", Op: "=", Value: 1},
				{
					Type: "logical",
					Op:   "OR",
					Conditions: []ConditionNode{
						{Type: "condition", Field: "b", Op: "=", Value: 2},
						{Type: "condition", Field: "c", Op: "=", Value: 3},
					},
				},
			},
		},
	}

	result := opt.Optimize(ast)

	if result.Conditions.Op != "OR" {
		t.Errorf("Expected OR, got %s", result.Conditions.Op)
	}
	if len(result.Conditions.Conditions) != 3 {
		t.Errorf("Expected 3 flattened items, got %d", len(result.Conditions.Conditions))
	}
}

func TestOptimizer_NoFlattenMixedLogical(t *testing.T) {
	opt := NewOptimizer()
	// (a AND (b OR c)) should NOT be flattened (different operators)
	ast := &QueryAST{
		Table: "users",
		Type:  QueryTypeSelect,
		Conditions: &ConditionNode{
			Type: "logical",
			Op:   "AND",
			Conditions: []ConditionNode{
				{Type: "condition", Field: "a", Op: "=", Value: 1},
				{
					Type: "logical",
					Op:   "OR",
					Conditions: []ConditionNode{
						{Type: "condition", Field: "b", Op: "=", Value: 2},
						{Type: "condition", Field: "c", Op: "=", Value: 3},
					},
				},
			},
		},
	}

	result := opt.Optimize(ast)

	// Should keep nested structure (2 items in AND: simple and OR)
	if len(result.Conditions.Conditions) != 2 {
		t.Errorf("Expected 2 items (no flattening), got %d", len(result.Conditions.Conditions))
	}
}

// =============================================================================
// Condition Reordering Tests
// =============================================================================

func TestOptimizer_ReorderEquality(t *testing.T) {
	opt := NewOptimizer()
	// Equality conditions should come before range conditions
	ast := &QueryAST{
		Table: "users",
		Type:  QueryTypeSelect,
		Conditions: &ConditionNode{
			Type: "logical",
			Op:   "AND",
			Conditions: []ConditionNode{
				{Type: "condition", Field: "age", Op: ">", Value: 18},          // range
				{Type: "condition", Field: "status", Op: "=", Value: "active"}, // equality
			},
		},
	}

	result := opt.Optimize(ast)

	// First condition should be equality (status)
	if result.Conditions.Conditions[0].Op != "=" {
		t.Errorf("First condition should be equality, got %s", result.Conditions.Conditions[0].Op)
	}
}

func TestOptimizer_ReorderPrimaryKey(t *testing.T) {
	opt := NewOptimizer()
	// id field should come first (likely primary key)
	ast := &QueryAST{
		Table: "users",
		Type:  QueryTypeSelect,
		Conditions: &ConditionNode{
			Type: "logical",
			Op:   "AND",
			Conditions: []ConditionNode{
				{Type: "condition", Field: "status", Op: "=", Value: "active"},
				{Type: "condition", Field: "id", Op: "=", Value: 1},
			},
		},
	}

	result := opt.Optimize(ast)

	// First condition should be id
	if result.Conditions.Conditions[0].Field != "id" {
		t.Errorf("First condition should be 'id', got '%s'", result.Conditions.Conditions[0].Field)
	}
}

func TestOptimizer_ReorderForeignKey(t *testing.T) {
	opt := NewOptimizer()
	// user_id should come before non-indexed fields (foreign key pattern)
	ast := &QueryAST{
		Table: "posts",
		Type:  QueryTypeSelect,
		Conditions: &ConditionNode{
			Type: "logical",
			Op:   "AND",
			Conditions: []ConditionNode{
				{Type: "condition", Field: "title", Op: "=", Value: "test"},
				{Type: "condition", Field: "user_id", Op: "=", Value: 1},
			},
		},
	}

	result := opt.Optimize(ast)

	// First condition should be user_id (ends with _id)
	if result.Conditions.Conditions[0].Field != "user_id" {
		t.Errorf("First condition should be 'user_id', got '%s'", result.Conditions.Conditions[0].Field)
	}
}

// =============================================================================
// Single Item Simplification Tests
// =============================================================================

func TestOptimizer_UnwrapSingleItemAND(t *testing.T) {
	opt := NewOptimizer()
	// (a) should become just a
	ast := &QueryAST{
		Table: "users",
		Type:  QueryTypeSelect,
		Conditions: &ConditionNode{
			Type: "logical",
			Op:   "AND",
			Conditions: []ConditionNode{
				{Type: "condition", Field: "id", Op: "=", Value: 1},
			},
		},
	}

	result := opt.Optimize(ast)

	// Should be unwrapped to simple condition
	if result.Conditions.Type != "condition" {
		t.Errorf("Single item AND should be unwrapped, got type %s", result.Conditions.Type)
	}
}

// =============================================================================
// Complex Optimization Tests
// =============================================================================

func TestOptimizer_ComplexQuery(t *testing.T) {
	opt := NewOptimizer()
	ast := &QueryAST{
		Table:   "users",
		Type:    QueryTypeSelect,
		Columns: []string{"id", "name"},
		Conditions: &ConditionNode{
			Type: "logical",
			Op:   "AND",
			Conditions: []ConditionNode{
				{Type: "condition", Field: "age", Op: ">", Value: 18},
				{Type: "condition", Field: "status", Op: "=", Value: "active"},
				{
					Type: "logical",
					Op:   "AND",
					Conditions: []ConditionNode{
						{Type: "condition", Field: "verified", Op: "=", Value: true},
						{Type: "condition", Field: "id", Op: ">", Value: 0},
					},
				},
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
		},
		Limit:  intPtr(10),
		Offset: intPtr(0),
	}

	result := opt.Optimize(ast)

	// Verify optimization didn't break anything
	if result.Table != "users" {
		t.Errorf("Table changed: %s", result.Table)
	}
	if result.Type != QueryTypeSelect {
		t.Errorf("Type changed: %s", result.Type)
	}
	if result.Conditions == nil {
		t.Error("Conditions removed")
	}
	if len(result.Order) != 1 {
		t.Errorf("Order changed: %v", result.Order)
	}
	if *result.Limit != 10 {
		t.Errorf("Limit changed: %d", *result.Limit)
	}
}

// =============================================================================
// Preservation Tests
// =============================================================================

func TestOptimizer_PreserveOrder(t *testing.T) {
	opt := NewOptimizer()
	ast := &QueryAST{
		Table: "users",
		Type:  QueryTypeSelect,
		Order: []OrderNode{
			{Field: "created_at", Direction: "DESC"},
			{Field: "name", Direction: "ASC"},
		},
	}

	result := opt.Optimize(ast)

	if len(result.Order) != 2 {
		t.Errorf("Order not preserved: got %d items", len(result.Order))
	}
}

func TestOptimizer_PreserveLimit(t *testing.T) {
	opt := NewOptimizer()
	ast := &QueryAST{
		Table: "users",
		Type:  QueryTypeSelect,
		Limit: intPtr(100),
	}

	result := opt.Optimize(ast)

	if result.Limit == nil || *result.Limit != 100 {
		t.Error("Limit not preserved")
	}
}

func TestOptimizer_PreserveOffset(t *testing.T) {
	opt := NewOptimizer()
	ast := &QueryAST{
		Table:  "users",
		Type:   QueryTypeSelect,
		Offset: intPtr(50),
	}

	result := opt.Optimize(ast)

	if result.Offset == nil || *result.Offset != 50 {
		t.Error("Offset not preserved")
	}
}

func TestOptimizer_PreserveColumns(t *testing.T) {
	opt := NewOptimizer()
	ast := &QueryAST{
		Table:   "users",
		Type:    QueryTypeSelect,
		Columns: []string{"id", "name", "email"},
	}

	result := opt.Optimize(ast)

	if len(result.Columns) != 3 {
		t.Errorf("Columns not preserved: got %v", result.Columns)
	}
}

func TestOptimizer_PreserveForUpdate(t *testing.T) {
	opt := NewOptimizer()
	ast := &QueryAST{
		Table:     "users",
		Type:      QueryTypeSelect,
		ForUpdate: true,
	}

	result := opt.Optimize(ast)

	if !result.ForUpdate {
		t.Error("ForUpdate not preserved")
	}
}

func TestOptimizer_PreserveDistinct(t *testing.T) {
	opt := NewOptimizer()
	ast := &QueryAST{
		Table:    "users",
		Type:     QueryTypeSelect,
		Distinct: true,
	}

	result := opt.Optimize(ast)

	if !result.Distinct {
		t.Error("Distinct not preserved")
	}
}

// =============================================================================
// Non-SELECT Query Tests
// =============================================================================

func TestOptimizer_OptimizeUpdate(t *testing.T) {
	opt := NewOptimizer()
	ast := &QueryAST{
		Table: "users",
		Type:  QueryTypeUpdate,
		Conditions: &ConditionNode{
			Type: "logical",
			Op:   "AND",
			Conditions: []ConditionNode{
				{Type: "condition", Field: "status", Op: "=", Value: "inactive"},
				{Type: "condition", Field: "id", Op: "=", Value: 1},
			},
		},
	}

	result := opt.Optimize(ast)

	if result.Type != QueryTypeUpdate {
		t.Errorf("Type changed: %s", result.Type)
	}
}

func TestOptimizer_OptimizeDelete(t *testing.T) {
	opt := NewOptimizer()
	ast := &QueryAST{
		Table: "users",
		Type:  QueryTypeDelete,
		Conditions: &ConditionNode{
			Type:  "condition",
			Field: "id",
			Op:    "=",
			Value: 1,
		},
	}

	result := opt.Optimize(ast)

	if result.Type != QueryTypeDelete {
		t.Errorf("Type changed: %s", result.Type)
	}
}
