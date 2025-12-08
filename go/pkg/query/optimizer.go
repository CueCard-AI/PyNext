package query

import (
	"sort"
	"strings"
)

// =============================================================================
// Query Optimizer
// =============================================================================

// Optimizer optimizes QueryAST for better performance.
type Optimizer struct {
	// Index hints: fields that are likely indexed
	indexedFields map[string]bool

	// Statistics (optional): field selectivity estimates
	selectivity map[string]float64
}

// NewOptimizer creates a new optimizer with default settings.
func NewOptimizer() *Optimizer {
	// Common indexed field patterns
	indexedFields := map[string]bool{
		"id":         true,
		"_id":        true,
		"uuid":       true,
		"created_at": true,
		"updated_at": true,
		"email":      true,
		"username":   true,
		"slug":       true,
	}

	return &Optimizer{
		indexedFields: indexedFields,
		selectivity:   make(map[string]float64),
	}
}

// =============================================================================
// Main Optimization Method
// =============================================================================

// Optimize applies optimizations to a QueryAST.
// Returns a new optimized AST (does not modify original).
func (o *Optimizer) Optimize(ast *QueryAST) *QueryAST {
	// Clone the AST
	optimized := o.cloneAST(ast)

	// Apply optimizations
	if optimized.Conditions != nil {
		// Flatten unnecessary nesting
		optimized.Conditions = o.flattenConditions(optimized.Conditions)

		// Reorder conditions (most selective first)
		optimized.Conditions = o.reorderConditions(optimized.Conditions)

		// Simplify redundant conditions
		optimized.Conditions = o.simplifyConditions(optimized.Conditions)
	}

	// Optimize column selection
	optimized.Columns = o.optimizeColumns(optimized.Columns)

	// Add default order for consistent results if limit but no order
	if optimized.Limit != nil && len(optimized.Order) == 0 {
		// Add id order for deterministic pagination
		optimized.Order = []OrderNode{{Field: "id", Direction: "ASC"}}
	}

	return optimized
}

// =============================================================================
// Condition Optimization
// =============================================================================

// flattenConditions removes unnecessary nesting.
// e.g., AND(AND(a, b), c) → AND(a, b, c)
func (o *Optimizer) flattenConditions(cond *ConditionNode) *ConditionNode {
	if cond == nil || cond.Type != "logical" {
		return cond
	}

	op := cond.Op

	// NOT can't be flattened
	if op == "NOT" {
		if len(cond.Conditions) == 1 {
			cond.Conditions[0] = *o.flattenConditions(&cond.Conditions[0])
		}
		return cond
	}

	// Flatten AND/OR
	var flattened []ConditionNode
	for _, child := range cond.Conditions {
		optimizedChild := o.flattenConditions(&child)

		// If child has same op, merge its children
		if optimizedChild.Type == "logical" && optimizedChild.Op == op {
			flattened = append(flattened, optimizedChild.Conditions...)
		} else {
			flattened = append(flattened, *optimizedChild)
		}
	}

	// If only one condition left, return it directly
	if len(flattened) == 1 {
		return &flattened[0]
	}

	return &ConditionNode{
		Type:       "logical",
		Op:         op,
		Conditions: flattened,
	}
}

// reorderConditions puts most selective conditions first.
// This helps the database use indexes more effectively.
func (o *Optimizer) reorderConditions(cond *ConditionNode) *ConditionNode {
	if cond == nil || cond.Type != "logical" {
		return cond
	}

	// Only reorder AND conditions (OR order doesn't matter as much)
	if cond.Op != "AND" {
		// Recursively optimize children
		for i := range cond.Conditions {
			cond.Conditions[i] = *o.reorderConditions(&cond.Conditions[i])
		}
		return cond
	}

	// Calculate selectivity score for each condition
	type scoredCondition struct {
		cond  ConditionNode
		score float64
	}

	scored := make([]scoredCondition, len(cond.Conditions))
	for i, child := range cond.Conditions {
		scored[i] = scoredCondition{
			cond:  child,
			score: o.selectivityScore(&child),
		}
	}

	// Sort by selectivity (lower score = more selective = first)
	sort.Slice(scored, func(i, j int) bool {
		return scored[i].score < scored[j].score
	})

	// Rebuild conditions in optimized order
	for i, sc := range scored {
		optimized := o.reorderConditions(&sc.cond)
		cond.Conditions[i] = *optimized
	}

	return cond
}

// selectivityScore estimates how selective a condition is.
// Lower score = more selective = should be evaluated first.
func (o *Optimizer) selectivityScore(cond *ConditionNode) float64 {
	if cond.Type != "condition" {
		// Logical conditions get average score
		return 0.5
	}

	// Check if field is likely indexed
	field := cond.Field
	if strings.HasSuffix(field, "_id") || o.isLikelyIndexed(field) {
		// Indexed fields are very selective
		return 0.1
	}

	// Score based on operator
	switch cond.Op {
	case "=":
		return 0.2 // Equality is usually selective
	case "IN":
		// Less selective with more values
		if values, ok := cond.Value.([]interface{}); ok {
			return 0.2 + float64(len(values))*0.05
		}
		return 0.3
	case "IS NULL", "IS NOT NULL":
		return 0.3 // Often selective
	case ">", ">=", "<", "<=":
		return 0.4 // Range queries are moderately selective
	case "LIKE", "ILIKE":
		// Prefix LIKE is more selective than contains
		if strVal, ok := cond.Value.(string); ok && !strings.HasPrefix(strVal, "%") {
			return 0.4 // Prefix LIKE
		}
		return 0.7 // Contains LIKE
	case "!=":
		return 0.8 // Not equal is usually not selective
	default:
		return 0.5
	}
}

// isLikelyIndexed checks if a field is likely indexed.
func (o *Optimizer) isLikelyIndexed(field string) bool {
	// Check exact match
	if o.indexedFields[field] {
		return true
	}

	// Check common patterns
	lowerField := strings.ToLower(field)

	// Primary key patterns
	if lowerField == "id" || strings.HasSuffix(lowerField, "_id") {
		return true
	}

	// Unique constraint patterns
	if lowerField == "email" || lowerField == "username" || lowerField == "slug" {
		return true
	}

	// Timestamp fields (often indexed for range queries)
	if strings.HasSuffix(lowerField, "_at") {
		return true
	}

	return false
}

// simplifyConditions removes redundant conditions.
func (o *Optimizer) simplifyConditions(cond *ConditionNode) *ConditionNode {
	if cond == nil || cond.Type != "logical" {
		return cond
	}

	// Remove duplicates in AND/OR
	seen := make(map[string]bool)
	var unique []ConditionNode

	for _, child := range cond.Conditions {
		simplified := o.simplifyConditions(&child)
		key := o.conditionKey(simplified)

		if !seen[key] {
			seen[key] = true
			unique = append(unique, *simplified)
		}
	}

	// If only one condition left, return it directly
	if len(unique) == 1 {
		return &unique[0]
	}

	cond.Conditions = unique
	return cond
}

// conditionKey generates a key for deduplication.
func (o *Optimizer) conditionKey(cond *ConditionNode) string {
	if cond.Type == "condition" {
		return cond.Field + ":" + cond.Op
	}
	if cond.Type == "raw" {
		return "raw:" + cond.SQL
	}
	return "logical:" + cond.Op
}

// =============================================================================
// Column Optimization
// =============================================================================

// optimizeColumns removes duplicate columns and optimizes selection.
func (o *Optimizer) optimizeColumns(columns []string) []string {
	if len(columns) == 0 {
		return columns
	}

	// Check for * - if present, it supersedes everything
	for _, col := range columns {
		if col == "*" {
			return []string{"*"}
		}
	}

	// Remove duplicates while preserving order
	seen := make(map[string]bool)
	unique := make([]string, 0, len(columns))

	for _, col := range columns {
		if !seen[col] {
			seen[col] = true
			unique = append(unique, col)
		}
	}

	return unique
}

// =============================================================================
// AST Cloning
// =============================================================================

// cloneAST creates a deep copy of a QueryAST.
func (o *Optimizer) cloneAST(ast *QueryAST) *QueryAST {
	if ast == nil {
		return nil
	}

	clone := &QueryAST{
		Table:     ast.Table,
		Type:      ast.Type,
		Distinct:  ast.Distinct,
		ForUpdate: ast.ForUpdate,
		RawSQL:    ast.RawSQL,
	}

	// Clone columns
	if ast.Columns != nil {
		clone.Columns = make([]string, len(ast.Columns))
		copy(clone.Columns, ast.Columns)
	}

	// Clone conditions
	if ast.Conditions != nil {
		clone.Conditions = o.cloneCondition(ast.Conditions)
	}

	// Clone order
	if ast.Order != nil {
		clone.Order = make([]OrderNode, len(ast.Order))
		copy(clone.Order, ast.Order)
	}

	// Clone limit/offset
	if ast.Limit != nil {
		v := *ast.Limit
		clone.Limit = &v
	}
	if ast.Offset != nil {
		v := *ast.Offset
		clone.Offset = &v
	}

	// Clone includes
	if ast.Includes != nil {
		clone.Includes = make([]string, len(ast.Includes))
		copy(clone.Includes, ast.Includes)
	}

	// Clone joins
	if ast.Joins != nil {
		clone.Joins = make([]JoinNode, len(ast.Joins))
		copy(clone.Joins, ast.Joins)
	}

	// Clone group by
	if ast.GroupBy != nil {
		clone.GroupBy = make([]string, len(ast.GroupBy))
		copy(clone.GroupBy, ast.GroupBy)
	}

	// Clone having
	if ast.Having != nil {
		clone.Having = o.cloneCondition(ast.Having)
	}

	// Clone params
	if ast.Params != nil {
		clone.Params = make([]interface{}, len(ast.Params))
		copy(clone.Params, ast.Params)
	}

	return clone
}

func (o *Optimizer) cloneCondition(cond *ConditionNode) *ConditionNode {
	if cond == nil {
		return nil
	}

	clone := &ConditionNode{
		Type:   cond.Type,
		Field:  cond.Field,
		Op:     cond.Op,
		Value:  cond.Value,
		Value2: cond.Value2,
		SQL:    cond.SQL,
	}

	if cond.Conditions != nil {
		clone.Conditions = make([]ConditionNode, len(cond.Conditions))
		for i, child := range cond.Conditions {
			clone.Conditions[i] = *o.cloneCondition(&child)
		}
	}

	if cond.Params != nil {
		clone.Params = make([]interface{}, len(cond.Params))
		copy(clone.Params, cond.Params)
	}

	return clone
}

// =============================================================================
// Configuration
// =============================================================================

// AddIndexedField marks a field as likely indexed.
func (o *Optimizer) AddIndexedField(field string) {
	o.indexedFields[field] = true
}

// SetSelectivity sets the estimated selectivity for a field.
// Value between 0 (very selective) and 1 (not selective).
func (o *Optimizer) SetSelectivity(field string, selectivity float64) {
	o.selectivity[field] = selectivity
}
