// Package query provides the Go-side query engine for PyNext.
//
// This package receives query ASTs from Python, optimizes them,
// generates SQL, and executes queries via the connection pool.
//
// Architecture:
//
//	Python QueryBuilder → AST JSON → Go Parse → Optimize → Generate SQL → Execute
//
// The AST (Abstract Syntax Tree) represents a query in a language-agnostic
// format that can be optimized and transformed before SQL generation.
package query

import (
	"encoding/json"
	"fmt"
	"strings"
)

// =============================================================================
// Query Type
// =============================================================================

// QueryType represents the type of SQL operation.
type QueryType string

const (
	QueryTypeSelect QueryType = "SELECT"
	QueryTypeInsert QueryType = "INSERT"
	QueryTypeUpdate QueryType = "UPDATE"
	QueryTypeDelete QueryType = "DELETE"
	QueryTypeRaw    QueryType = "RAW"
)

// =============================================================================
// Operator Types
// =============================================================================

// Operator represents a SQL comparison operator.
type Operator string

const (
	OpEq          Operator = "="
	OpNe          Operator = "!="
	OpGt          Operator = ">"
	OpGte         Operator = ">="
	OpLt          Operator = "<"
	OpLte         Operator = "<="
	OpLike        Operator = "LIKE"
	OpILike       Operator = "ILIKE"
	OpIn          Operator = "IN"
	OpNotIn       Operator = "NOT IN"
	OpIsNull      Operator = "IS NULL"
	OpIsNotNull   Operator = "IS NOT NULL"
	OpBetween     Operator = "BETWEEN"
	OpContains    Operator = "@>"
	OpContainedBy Operator = "<@"
	OpOverlaps    Operator = "&&"
)

// LogicalOp represents a logical operator for combining conditions.
type LogicalOp string

const (
	LogicalAnd LogicalOp = "AND"
	LogicalOr  LogicalOp = "OR"
	LogicalNot LogicalOp = "NOT"
)

// =============================================================================
// AST Node Types
// =============================================================================

// OrderNode represents an ORDER BY clause element.
type OrderNode struct {
	Field     string `json:"field"`
	Direction string `json:"direction"` // "ASC" or "DESC"
}

// JoinNode represents a JOIN clause.
type JoinNode struct {
	Table    string `json:"table"`
	Alias    string `json:"alias,omitempty"`
	JoinType string `json:"join_type"` // "INNER", "LEFT", "RIGHT", "FULL"
	OnField  string `json:"on_field"`
	ToField  string `json:"to_field"`
}

// ConditionNode represents a condition in the WHERE clause.
// It can be a simple condition, a logical combination, or raw SQL.
type ConditionNode struct {
	// Type of condition: "condition", "logical", or "raw"
	Type string `json:"type"`

	// For simple conditions (type="condition")
	Field  string      `json:"field,omitempty"`
	Op     string      `json:"op,omitempty"` // Comparison op for "condition", logical op for "logical"
	Value  interface{} `json:"value,omitempty"`
	Value2 interface{} `json:"value2,omitempty"` // For BETWEEN

	// For logical conditions (type="logical")
	Conditions []ConditionNode `json:"conditions,omitempty"`

	// For raw SQL (type="raw")
	SQL    string        `json:"sql,omitempty"`
	Params []interface{} `json:"params,omitempty"`
}

// QueryAST represents the complete Abstract Syntax Tree for a query.
// This is parsed from JSON sent by Python.
type QueryAST struct {
	Table      string         `json:"table"`
	Type       QueryType      `json:"type"`
	Columns    []string       `json:"columns,omitempty"`
	Conditions *ConditionNode `json:"conditions,omitempty"`
	Order      []OrderNode    `json:"order,omitempty"`
	Limit      *int           `json:"limit,omitempty"`
	Offset     *int           `json:"offset,omitempty"`
	Includes   []string       `json:"includes,omitempty"`
	Joins      []JoinNode     `json:"joins,omitempty"`
	GroupBy    []string       `json:"group_by,omitempty"`
	Having     *ConditionNode `json:"having,omitempty"`
	Distinct   bool           `json:"distinct,omitempty"`
	ForUpdate  bool           `json:"for_update,omitempty"`
	Params     []interface{}  `json:"params,omitempty"`
	RawSQL     string         `json:"raw_sql,omitempty"`
}

// =============================================================================
// Parsing
// =============================================================================

// ParseAST parses a JSON string into a QueryAST.
func ParseAST(jsonData []byte) (*QueryAST, error) {
	var ast QueryAST
	if err := json.Unmarshal(jsonData, &ast); err != nil {
		return nil, fmt.Errorf("failed to parse query AST: %w", err)
	}

	// Validate required fields
	if ast.Table == "" && ast.Type != QueryTypeRaw {
		return nil, fmt.Errorf("query AST missing required field: table")
	}

	// Default to SELECT
	if ast.Type == "" {
		ast.Type = QueryTypeSelect
	}

	return &ast, nil
}

// =============================================================================
// AST Inspection Methods
// =============================================================================

// HasConditions returns true if the query has WHERE conditions.
func (q *QueryAST) HasConditions() bool {
	return q.Conditions != nil
}

// HasOrder returns true if the query has ORDER BY.
func (q *QueryAST) HasOrder() bool {
	return len(q.Order) > 0
}

// HasLimit returns true if the query has LIMIT.
func (q *QueryAST) HasLimit() bool {
	return q.Limit != nil
}

// HasOffset returns true if the query has OFFSET.
func (q *QueryAST) HasOffset() bool {
	return q.Offset != nil
}

// HasJoins returns true if the query has JOIN clauses.
func (q *QueryAST) HasJoins() bool {
	return len(q.Joins) > 0
}

// IsRawQuery returns true if this is a raw SQL query.
func (q *QueryAST) IsRawQuery() bool {
	return q.Type == QueryTypeRaw || q.RawSQL != ""
}

// ColumnList returns the columns to select, or "*" if none specified.
func (q *QueryAST) ColumnList() string {
	if len(q.Columns) == 0 {
		return "*"
	}
	return strings.Join(q.Columns, ", ")
}

// =============================================================================
// Condition Node Methods
// =============================================================================

// IsSimple returns true if this is a simple field comparison.
func (c *ConditionNode) IsSimple() bool {
	return c.Type == "condition"
}

// IsLogical returns true if this is a logical combination (AND/OR/NOT).
func (c *ConditionNode) IsLogical() bool {
	return c.Type == "logical"
}

// IsRaw returns true if this is raw SQL.
func (c *ConditionNode) IsRaw() bool {
	return c.Type == "raw"
}

// ConditionCount returns the total number of simple conditions in the tree.
func (c *ConditionNode) ConditionCount() int {
	if c.IsSimple() || c.IsRaw() {
		return 1
	}
	count := 0
	for _, child := range c.Conditions {
		count += child.ConditionCount()
	}
	return count
}

// Depth returns the maximum nesting depth of conditions.
func (c *ConditionNode) Depth() int {
	if c.IsSimple() || c.IsRaw() {
		return 1
	}
	maxDepth := 0
	for _, child := range c.Conditions {
		d := child.Depth()
		if d > maxDepth {
			maxDepth = d
		}
	}
	return maxDepth + 1
}

// =============================================================================
// Debugging
// =============================================================================

// String returns a human-readable representation of the AST.
func (q *QueryAST) String() string {
	var sb strings.Builder
	sb.WriteString(fmt.Sprintf("%s FROM %s", q.Type, q.Table))

	if len(q.Columns) > 0 {
		sb.WriteString(fmt.Sprintf(" [columns: %s]", strings.Join(q.Columns, ", ")))
	}

	if q.Conditions != nil {
		sb.WriteString(fmt.Sprintf(" WHERE %s", q.Conditions.String()))
	}

	if len(q.Order) > 0 {
		orders := make([]string, len(q.Order))
		for i, o := range q.Order {
			orders[i] = fmt.Sprintf("%s %s", o.Field, o.Direction)
		}
		sb.WriteString(fmt.Sprintf(" ORDER BY %s", strings.Join(orders, ", ")))
	}

	if q.Limit != nil {
		sb.WriteString(fmt.Sprintf(" LIMIT %d", *q.Limit))
	}

	if q.Offset != nil {
		sb.WriteString(fmt.Sprintf(" OFFSET %d", *q.Offset))
	}

	return sb.String()
}

// String returns a human-readable representation of the condition.
func (c *ConditionNode) String() string {
	switch c.Type {
	case "condition":
		if c.Value2 != nil {
			return fmt.Sprintf("(%s %s %v AND %v)", c.Field, c.Op, c.Value, c.Value2)
		}
		return fmt.Sprintf("(%s %s %v)", c.Field, c.Op, c.Value)

	case "logical":
		if len(c.Conditions) == 0 {
			return "(empty)"
		}
		parts := make([]string, len(c.Conditions))
		for i, child := range c.Conditions {
			parts[i] = child.String()
		}
		return fmt.Sprintf("(%s)", strings.Join(parts, fmt.Sprintf(" %s ", c.Op)))

	case "raw":
		return fmt.Sprintf("(RAW: %s)", c.SQL)

	default:
		return "(unknown)"
	}
}
