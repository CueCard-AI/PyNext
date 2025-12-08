package query

import (
	"fmt"
	"regexp"
	"strings"
)

// =============================================================================
// Query Validator
// =============================================================================

// Validator validates queries for security and correctness.
type Validator struct {
	// Allowed operators
	allowedOps map[string]bool

	// Schema information (optional, for field validation)
	schema map[string][]string // table -> columns

	// Configuration
	maxConditions     int
	maxDepth          int
	maxJoins          int
	allowRawSQL       bool
	dangerousKeywords []string
}

// NewValidator creates a new validator with default settings.
func NewValidator() *Validator {
	allowedOps := map[string]bool{
		"=": true, "!=": true, "<>": true,
		">": true, ">=": true, "<": true, "<=": true,
		"LIKE": true, "ILIKE": true,
		"IN": true, "NOT IN": true,
		"IS NULL": true, "IS NOT NULL": true,
		"BETWEEN": true,
		"@>":      true, "<@": true, "&&": true,
	}

	return &Validator{
		allowedOps:    allowedOps,
		schema:        make(map[string][]string),
		maxConditions: 100,
		maxDepth:      10,
		maxJoins:      10,
		allowRawSQL:   true,
		dangerousKeywords: []string{
			"DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE",
			"GRANT", "REVOKE", "INSERT", "UPDATE",
		},
	}
}

// =============================================================================
// Validation Errors
// =============================================================================

// ValidationError represents a validation failure.
type ValidationError struct {
	Code    string `json:"code"`
	Message string `json:"message"`
	Field   string `json:"field,omitempty"`
}

func (e *ValidationError) Error() string {
	if e.Field != "" {
		return fmt.Sprintf("%s: %s (field: %s)", e.Code, e.Message, e.Field)
	}
	return fmt.Sprintf("%s: %s", e.Code, e.Message)
}

// =============================================================================
// Main Validation Method
// =============================================================================

// Validate checks a QueryAST for security and correctness issues.
func (v *Validator) Validate(ast *QueryAST) error {
	// Check table name
	if ast.Table == "" && ast.Type != QueryTypeRaw {
		return &ValidationError{
			Code:    "MISSING_TABLE",
			Message: "table name is required",
		}
	}

	// Validate table name format
	if ast.Table != "" && !v.isValidIdentifier(ast.Table) {
		return &ValidationError{
			Code:    "INVALID_TABLE",
			Message: "table name contains invalid characters",
			Field:   ast.Table,
		}
	}

	// Validate columns
	for _, col := range ast.Columns {
		if col != "*" && !v.isValidIdentifier(col) {
			return &ValidationError{
				Code:    "INVALID_COLUMN",
				Message: "column name contains invalid characters",
				Field:   col,
			}
		}
	}

	// Validate conditions
	if ast.Conditions != nil {
		if err := v.validateConditions(ast.Conditions); err != nil {
			return err
		}

		// Check complexity
		count := ast.Conditions.ConditionCount()
		if count > v.maxConditions {
			return &ValidationError{
				Code:    "TOO_COMPLEX",
				Message: fmt.Sprintf("query has %d conditions, max is %d", count, v.maxConditions),
			}
		}

		// Check depth
		depth := ast.Conditions.Depth()
		if depth > v.maxDepth {
			return &ValidationError{
				Code:    "TOO_DEEP",
				Message: fmt.Sprintf("condition nesting depth %d exceeds max %d", depth, v.maxDepth),
			}
		}
	}

	// Validate joins
	if len(ast.Joins) > v.maxJoins {
		return &ValidationError{
			Code:    "TOO_MANY_JOINS",
			Message: fmt.Sprintf("query has %d joins, max is %d", len(ast.Joins), v.maxJoins),
		}
	}

	for _, join := range ast.Joins {
		if !v.isValidIdentifier(join.Table) {
			return &ValidationError{
				Code:    "INVALID_JOIN_TABLE",
				Message: "join table name contains invalid characters",
				Field:   join.Table,
			}
		}
	}

	// Validate order
	for _, order := range ast.Order {
		if !v.isValidIdentifier(order.Field) {
			return &ValidationError{
				Code:    "INVALID_ORDER_FIELD",
				Message: "order field contains invalid characters",
				Field:   order.Field,
			}
		}
		if order.Direction != "ASC" && order.Direction != "DESC" {
			return &ValidationError{
				Code:    "INVALID_ORDER_DIRECTION",
				Message: "order direction must be ASC or DESC",
				Field:   order.Direction,
			}
		}
	}

	// Validate raw SQL if present
	if ast.RawSQL != "" && !v.allowRawSQL {
		return &ValidationError{
			Code:    "RAW_SQL_DISABLED",
			Message: "raw SQL is not allowed in strict mode",
		}
	}

	if ast.RawSQL != "" {
		warnings := v.ValidateRawSQL(ast.RawSQL)
		if len(warnings) > 0 {
			return &ValidationError{
				Code:    "DANGEROUS_SQL",
				Message: strings.Join(warnings, "; "),
			}
		}
	}

	return nil
}

// =============================================================================
// Condition Validation
// =============================================================================

func (v *Validator) validateConditions(cond *ConditionNode) error {
	switch cond.Type {
	case "condition":
		return v.validateSimpleCondition(cond)
	case "logical":
		return v.validateLogicalCondition(cond)
	case "raw":
		return v.validateRawCondition(cond)
	default:
		return &ValidationError{
			Code:    "UNKNOWN_CONDITION_TYPE",
			Message: fmt.Sprintf("unknown condition type: %s", cond.Type),
		}
	}
}

func (v *Validator) validateSimpleCondition(cond *ConditionNode) error {
	// Validate field name
	if !v.isValidIdentifier(cond.Field) {
		return &ValidationError{
			Code:    "INVALID_FIELD",
			Message: "field name contains invalid characters",
			Field:   cond.Field,
		}
	}

	// Validate operator
	if !v.allowedOps[cond.Op] {
		return &ValidationError{
			Code:    "INVALID_OPERATOR",
			Message: fmt.Sprintf("operator '%s' is not allowed", cond.Op),
			Field:   cond.Op,
		}
	}

	return nil
}

func (v *Validator) validateLogicalCondition(cond *ConditionNode) error {
	// Validate logical operator
	op := cond.Op
	if op != "AND" && op != "OR" && op != "NOT" {
		return &ValidationError{
			Code:    "INVALID_LOGICAL_OP",
			Message: fmt.Sprintf("logical operator '%s' is not valid", op),
		}
	}

	// NOT requires exactly one child
	if op == "NOT" && len(cond.Conditions) != 1 {
		return &ValidationError{
			Code:    "INVALID_NOT",
			Message: "NOT requires exactly one condition",
		}
	}

	// Recursively validate children
	for i, child := range cond.Conditions {
		if err := v.validateConditions(&child); err != nil {
			return fmt.Errorf("condition %d: %w", i, err)
		}
	}

	return nil
}

func (v *Validator) validateRawCondition(cond *ConditionNode) error {
	if !v.allowRawSQL {
		return &ValidationError{
			Code:    "RAW_SQL_DISABLED",
			Message: "raw SQL conditions are not allowed",
		}
	}

	warnings := v.ValidateRawSQL(cond.SQL)
	if len(warnings) > 0 {
		return &ValidationError{
			Code:    "DANGEROUS_RAW_SQL",
			Message: strings.Join(warnings, "; "),
		}
	}

	return nil
}

// =============================================================================
// Raw SQL Validation
// =============================================================================

// ValidateRawSQL checks raw SQL for dangerous patterns.
// Returns list of warnings (empty = OK).
func (v *Validator) ValidateRawSQL(sql string) []string {
	var warnings []string

	// Check for comments (potential injection)
	if strings.Contains(sql, "--") || strings.Contains(sql, "/*") {
		warnings = append(warnings, "SQL comments detected")
	}

	// Check for semicolons (multiple statements)
	if strings.Contains(sql, ";") {
		warnings = append(warnings, "semicolon detected - multiple statements not allowed")
	}

	// Check for dangerous keywords
	upperSQL := strings.ToUpper(sql)
	for _, keyword := range v.dangerousKeywords {
		// Use word boundary matching
		pattern := fmt.Sprintf(`\b%s\b`, keyword)
		matched, _ := regexp.MatchString(pattern, upperSQL)
		if matched {
			warnings = append(warnings, fmt.Sprintf("dangerous keyword '%s' detected", keyword))
		}
	}

	// Check for UNION (potential injection)
	if matched, _ := regexp.MatchString(`\bUNION\b`, upperSQL); matched {
		warnings = append(warnings, "UNION detected - potential SQL injection")
	}

	return warnings
}

// =============================================================================
// Identifier Validation
// =============================================================================

// isValidIdentifier checks if a string is a valid SQL identifier.
// Allows: letters, numbers, underscores, and dots (for table.column).
func (v *Validator) isValidIdentifier(name string) bool {
	if name == "" {
		return false
	}

	// Allow special cases
	if name == "*" {
		return true
	}

	// Check for SQL functions or expressions (allow them)
	if strings.Contains(name, "(") && strings.Contains(name, ")") {
		return true
	}

	// Basic identifier pattern: alphanumeric, underscore, dot
	pattern := `^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*$`
	matched, _ := regexp.MatchString(pattern, name)
	return matched
}

// =============================================================================
// Configuration
// =============================================================================

// SetSchema sets the schema for field validation.
func (v *Validator) SetSchema(schema map[string][]string) {
	v.schema = schema
}

// SetMaxConditions sets the maximum number of conditions.
func (v *Validator) SetMaxConditions(max int) {
	v.maxConditions = max
}

// SetMaxDepth sets the maximum condition nesting depth.
func (v *Validator) SetMaxDepth(max int) {
	v.maxDepth = max
}

// SetAllowRawSQL enables or disables raw SQL.
func (v *Validator) SetAllowRawSQL(allow bool) {
	v.allowRawSQL = allow
}
