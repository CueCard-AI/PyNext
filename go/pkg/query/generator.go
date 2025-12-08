package query

import (
	"fmt"
	"strings"
)

// =============================================================================
// SQL Generator
// =============================================================================

// Generator produces SQL from a QueryAST.
type Generator struct {
	// Dialect for SQL generation (default: PostgreSQL)
	dialect string

	// Parameter counter (for $1, $2, etc.)
	paramCounter int

	// Collected parameters in order
	params []interface{}

	// Schema information for validation (optional)
	schema map[string][]string // table -> columns
}

// NewGenerator creates a new SQL generator.
func NewGenerator() *Generator {
	return &Generator{
		dialect:      "postgres",
		paramCounter: 0,
		params:       make([]interface{}, 0),
	}
}

// GeneratedQuery holds the generated SQL and parameters.
type GeneratedQuery struct {
	SQL    string
	Params []interface{}
}

// =============================================================================
// Main Generation Method
// =============================================================================

// Generate produces SQL from a QueryAST.
func (g *Generator) Generate(ast *QueryAST) (*GeneratedQuery, error) {
	// Reset state
	g.paramCounter = 0
	g.params = make([]interface{}, 0)

	// Handle raw SQL
	if ast.IsRawQuery() {
		return &GeneratedQuery{
			SQL:    ast.RawSQL,
			Params: ast.Params,
		}, nil
	}

	var sql string
	var err error

	switch ast.Type {
	case QueryTypeSelect:
		sql, err = g.generateSelect(ast)
	case QueryTypeInsert:
		sql, err = g.generateInsert(ast)
	case QueryTypeUpdate:
		sql, err = g.generateUpdate(ast)
	case QueryTypeDelete:
		sql, err = g.generateDelete(ast)
	default:
		return nil, fmt.Errorf("unsupported query type: %s", ast.Type)
	}

	if err != nil {
		return nil, err
	}

	return &GeneratedQuery{
		SQL:    sql,
		Params: g.params,
	}, nil
}

// =============================================================================
// SELECT Generation
// =============================================================================

func (g *Generator) generateSelect(ast *QueryAST) (string, error) {
	var parts []string

	// SELECT
	selectClause := "SELECT"
	if ast.Distinct {
		selectClause += " DISTINCT"
	}
	selectClause += " " + ast.ColumnList()
	parts = append(parts, selectClause)

	// FROM
	parts = append(parts, fmt.Sprintf("FROM %s", g.quoteIdentifier(ast.Table)))

	// JOINs
	if ast.HasJoins() {
		for _, join := range ast.Joins {
			joinSQL := g.generateJoin(&join)
			parts = append(parts, joinSQL)
		}
	}

	// WHERE
	if ast.HasConditions() {
		whereSQL, err := g.generateConditions(ast.Conditions, ast.Params)
		if err != nil {
			return "", err
		}
		parts = append(parts, "WHERE "+whereSQL)
	}

	// GROUP BY
	if len(ast.GroupBy) > 0 {
		parts = append(parts, "GROUP BY "+strings.Join(ast.GroupBy, ", "))
	}

	// HAVING
	if ast.Having != nil {
		havingSQL, err := g.generateConditions(ast.Having, nil)
		if err != nil {
			return "", err
		}
		parts = append(parts, "HAVING "+havingSQL)
	}

	// ORDER BY
	if ast.HasOrder() {
		orderClauses := make([]string, len(ast.Order))
		for i, order := range ast.Order {
			orderClauses[i] = fmt.Sprintf("%s %s", g.quoteIdentifier(order.Field), order.Direction)
		}
		parts = append(parts, "ORDER BY "+strings.Join(orderClauses, ", "))
	}

	// LIMIT
	if ast.HasLimit() {
		parts = append(parts, fmt.Sprintf("LIMIT %d", *ast.Limit))
	}

	// OFFSET
	if ast.HasOffset() {
		parts = append(parts, fmt.Sprintf("OFFSET %d", *ast.Offset))
	}

	// FOR UPDATE
	if ast.ForUpdate {
		parts = append(parts, "FOR UPDATE")
	}

	return strings.Join(parts, " "), nil
}

// =============================================================================
// INSERT/UPDATE/DELETE Generation
// =============================================================================

func (g *Generator) generateInsert(ast *QueryAST) (string, error) {
	// TODO: Implement INSERT generation
	return "", fmt.Errorf("INSERT generation not yet implemented")
}

func (g *Generator) generateUpdate(ast *QueryAST) (string, error) {
	// TODO: Implement UPDATE generation
	return "", fmt.Errorf("UPDATE generation not yet implemented")
}

func (g *Generator) generateDelete(ast *QueryAST) (string, error) {
	var parts []string

	parts = append(parts, fmt.Sprintf("DELETE FROM %s", g.quoteIdentifier(ast.Table)))

	// WHERE (required for DELETE to avoid accidental full table delete)
	if ast.HasConditions() {
		whereSQL, err := g.generateConditions(ast.Conditions, ast.Params)
		if err != nil {
			return "", err
		}
		parts = append(parts, "WHERE "+whereSQL)
	} else {
		return "", fmt.Errorf("DELETE without WHERE clause is not allowed")
	}

	return strings.Join(parts, " "), nil
}

// =============================================================================
// JOIN Generation
// =============================================================================

func (g *Generator) generateJoin(join *JoinNode) string {
	joinType := join.JoinType
	if joinType == "" {
		joinType = "INNER"
	}

	tableRef := g.quoteIdentifier(join.Table)
	if join.Alias != "" {
		tableRef += " AS " + g.quoteIdentifier(join.Alias)
	}

	return fmt.Sprintf("%s JOIN %s ON %s = %s",
		joinType,
		tableRef,
		g.quoteIdentifier(join.OnField),
		g.quoteIdentifier(join.ToField),
	)
}

// =============================================================================
// Condition Generation
// =============================================================================

func (g *Generator) generateConditions(cond *ConditionNode, astParams []interface{}) (string, error) {
	if cond == nil {
		return "", nil
	}

	switch cond.Type {
	case "condition":
		return g.generateSimpleCondition(cond, astParams)
	case "logical":
		return g.generateLogicalCondition(cond, astParams)
	case "raw":
		return g.generateRawCondition(cond)
	default:
		return "", fmt.Errorf("unknown condition type: %s", cond.Type)
	}
}

func (g *Generator) generateSimpleCondition(cond *ConditionNode, astParams []interface{}) (string, error) {
	field := g.quoteIdentifier(cond.Field)
	op := cond.Op

	switch op {
	case "IS NULL", "IS NOT NULL":
		return fmt.Sprintf("%s %s", field, op), nil

	case "IN", "NOT IN":
		values, ok := cond.Value.([]interface{})
		if !ok {
			return "", fmt.Errorf("IN/NOT IN requires array value, got: %T", cond.Value)
		}
		placeholders := make([]string, len(values))
		for i, v := range values {
			g.paramCounter++
			placeholders[i] = fmt.Sprintf("$%d", g.paramCounter)
			g.params = append(g.params, v)
		}
		return fmt.Sprintf("%s %s (%s)", field, op, strings.Join(placeholders, ", ")), nil

	case "BETWEEN":
		g.paramCounter++
		p1 := fmt.Sprintf("$%d", g.paramCounter)
		g.params = append(g.params, cond.Value)

		g.paramCounter++
		p2 := fmt.Sprintf("$%d", g.paramCounter)
		g.params = append(g.params, cond.Value2)

		return fmt.Sprintf("%s BETWEEN %s AND %s", field, p1, p2), nil

	case "@>", "<@", "&&":
		// PostgreSQL array/jsonb operators
		g.paramCounter++
		placeholder := fmt.Sprintf("$%d", g.paramCounter)
		g.params = append(g.params, cond.Value)
		return fmt.Sprintf("%s %s %s", field, op, placeholder), nil

	default:
		// Standard comparison operators: =, !=, >, >=, <, <=, LIKE, ILIKE
		g.paramCounter++
		placeholder := fmt.Sprintf("$%d", g.paramCounter)
		g.params = append(g.params, cond.Value)
		return fmt.Sprintf("%s %s %s", field, op, placeholder), nil
	}
}

func (g *Generator) generateLogicalCondition(cond *ConditionNode, astParams []interface{}) (string, error) {
	if len(cond.Conditions) == 0 {
		return "", nil
	}

	op := cond.Op // Op field holds logical operator for "logical" type
	if op == "" {
		op = "AND"
	}

	// Handle NOT (unary)
	if op == "NOT" {
		if len(cond.Conditions) != 1 {
			return "", fmt.Errorf("NOT requires exactly 1 condition, got %d", len(cond.Conditions))
		}
		inner, err := g.generateConditions(&cond.Conditions[0], astParams)
		if err != nil {
			return "", err
		}
		return fmt.Sprintf("NOT (%s)", inner), nil
	}

	// Handle AND/OR (binary/n-ary)
	parts := make([]string, 0, len(cond.Conditions))
	for _, child := range cond.Conditions {
		childSQL, err := g.generateConditions(&child, astParams)
		if err != nil {
			return "", err
		}
		if childSQL != "" {
			parts = append(parts, childSQL)
		}
	}

	if len(parts) == 0 {
		return "", nil
	}
	if len(parts) == 1 {
		return parts[0], nil
	}

	// Wrap in parentheses and join with operator
	return "(" + strings.Join(parts, fmt.Sprintf(" %s ", op)) + ")", nil
}

func (g *Generator) generateRawCondition(cond *ConditionNode) (string, error) {
	// Raw SQL - append params and adjust placeholders
	sql := cond.SQL

	// Re-number placeholders ($1, $2, ...) based on our counter
	// This is a simple approach - could be improved with regex
	for i, param := range cond.Params {
		oldPlaceholder := fmt.Sprintf("$%d", i+1)
		g.paramCounter++
		newPlaceholder := fmt.Sprintf("$%d", g.paramCounter)
		sql = strings.Replace(sql, oldPlaceholder, newPlaceholder, 1)
		g.params = append(g.params, param)
	}

	return sql, nil
}

// =============================================================================
// Utility Methods
// =============================================================================

// quoteIdentifier wraps an identifier in double quotes for PostgreSQL.
// Handles dot notation for table.column.
func (g *Generator) quoteIdentifier(name string) string {
	// Don't quote special cases
	if name == "*" {
		return name
	}

	// Don't quote if it's an expression (contains spaces, parens, etc.)
	if strings.ContainsAny(name, " ()") {
		return name
	}

	// Handle table.column notation
	if strings.Contains(name, ".") {
		parts := strings.Split(name, ".")
		quoted := make([]string, len(parts))
		for i, part := range parts {
			quoted[i] = `"` + part + `"`
		}
		return strings.Join(quoted, ".")
	}

	// Simple identifier
	return `"` + name + `"`
}

// Reset clears the generator state for reuse.
func (g *Generator) Reset() {
	g.paramCounter = 0
	g.params = make([]interface{}, 0)
}
