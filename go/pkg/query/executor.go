package query

import (
	"context"
	"fmt"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

// =============================================================================
// Query Executor
// =============================================================================

// Executor executes queries against the database.
type Executor struct {
	pool      *pgxpool.Pool
	generator *Generator
	validator *Validator
	optimizer *Optimizer

	// Configuration
	queryTimeout  time.Duration
	strictMode    bool
	maxComplexity int
}

// ExecutorConfig holds configuration for the executor.
type ExecutorConfig struct {
	QueryTimeout  time.Duration
	StrictMode    bool
	MaxComplexity int // Max condition count
}

// DefaultExecutorConfig returns sensible defaults.
func DefaultExecutorConfig() *ExecutorConfig {
	return &ExecutorConfig{
		QueryTimeout:  30 * time.Second,
		StrictMode:    false,
		MaxComplexity: 100, // Max 100 conditions
	}
}

// NewExecutor creates a new query executor.
func NewExecutor(pool *pgxpool.Pool, config *ExecutorConfig) *Executor {
	if config == nil {
		config = DefaultExecutorConfig()
	}

	return &Executor{
		pool:          pool,
		generator:     NewGenerator(),
		validator:     NewValidator(),
		optimizer:     NewOptimizer(),
		queryTimeout:  config.QueryTimeout,
		strictMode:    config.StrictMode,
		maxComplexity: config.MaxComplexity,
	}
}

// =============================================================================
// Query Result
// =============================================================================

// QueryResult holds the result of a query execution.
type QueryResult struct {
	Columns  []string        `json:"columns"`
	Rows     [][]interface{} `json:"rows"`
	RowCount int             `json:"row_count"`
	Duration float64         `json:"duration"`      // milliseconds
	SQL      string          `json:"sql,omitempty"` // For debugging
}

// =============================================================================
// Execution Methods
// =============================================================================

// Execute parses, optimizes, generates, and executes a query from AST JSON.
func (e *Executor) Execute(ctx context.Context, astJSON []byte) (*QueryResult, error) {
	start := time.Now()

	// 1. Parse AST
	ast, err := ParseAST(astJSON)
	if err != nil {
		return nil, fmt.Errorf("parse error: %w", err)
	}

	// 2. Validate (if strict mode)
	if e.strictMode {
		if err := e.validator.Validate(ast); err != nil {
			return nil, fmt.Errorf("validation error: %w", err)
		}
	}

	// 3. Check complexity
	if ast.Conditions != nil {
		complexity := ast.Conditions.ConditionCount()
		if complexity > e.maxComplexity {
			return nil, fmt.Errorf("query too complex: %d conditions (max: %d)", complexity, e.maxComplexity)
		}
	}

	// 4. Optimize
	optimizedAST := e.optimizer.Optimize(ast)

	// 5. Generate SQL
	generated, err := e.generator.Generate(optimizedAST)
	if err != nil {
		return nil, fmt.Errorf("generation error: %w", err)
	}

	// 6. Execute
	result, err := e.executeSQL(ctx, generated.SQL, generated.Params)
	if err != nil {
		return nil, fmt.Errorf("execution error: %w", err)
	}

	result.Duration = float64(time.Since(start).Microseconds()) / 1000.0
	result.SQL = generated.SQL // For debugging

	return result, nil
}

// ExecuteRaw executes raw SQL with parameters.
func (e *Executor) ExecuteRaw(ctx context.Context, sql string, params []interface{}) (*QueryResult, error) {
	start := time.Now()

	// Validate SQL in strict mode
	if e.strictMode {
		warnings := e.validator.ValidateRawSQL(sql)
		if len(warnings) > 0 {
			return nil, fmt.Errorf("SQL validation failed: %v", warnings)
		}
	}

	result, err := e.executeSQL(ctx, sql, params)
	if err != nil {
		return nil, err
	}

	result.Duration = float64(time.Since(start).Microseconds()) / 1000.0
	result.SQL = sql

	return result, nil
}

// executeSQL is the low-level execution method.
func (e *Executor) executeSQL(ctx context.Context, sql string, params []interface{}) (*QueryResult, error) {
	// Add timeout
	ctx, cancel := context.WithTimeout(ctx, e.queryTimeout)
	defer cancel()

	// Execute query
	rows, err := e.pool.Query(ctx, sql, params...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	// Get column info
	fieldDescs := rows.FieldDescriptions()
	columns := make([]string, len(fieldDescs))
	for i, fd := range fieldDescs {
		columns[i] = string(fd.Name)
	}

	// Collect rows
	var resultRows [][]interface{}
	for rows.Next() {
		values, err := rows.Values()
		if err != nil {
			return nil, err
		}
		resultRows = append(resultRows, values)
	}

	if err := rows.Err(); err != nil {
		return nil, err
	}

	return &QueryResult{
		Columns:  columns,
		Rows:     resultRows,
		RowCount: len(resultRows),
	}, nil
}

// ExecuteOne executes and expects exactly one row.
func (e *Executor) ExecuteOne(ctx context.Context, astJSON []byte) (map[string]interface{}, error) {
	result, err := e.Execute(ctx, astJSON)
	if err != nil {
		return nil, err
	}

	if result.RowCount == 0 {
		return nil, fmt.Errorf("no rows found")
	}
	if result.RowCount > 1 {
		return nil, fmt.Errorf("multiple rows found, expected one")
	}

	// Convert to map
	row := make(map[string]interface{})
	for i, col := range result.Columns {
		row[col] = result.Rows[0][i]
	}

	return row, nil
}

// ExecuteCount executes a COUNT query.
func (e *Executor) ExecuteCount(ctx context.Context, astJSON []byte) (int64, error) {
	// Parse and modify AST for count
	ast, err := ParseAST(astJSON)
	if err != nil {
		return 0, err
	}

	// Override columns to COUNT(*)
	ast.Columns = []string{"COUNT(*)"}
	ast.Order = nil  // No order for count
	ast.Limit = nil  // No limit for count
	ast.Offset = nil // No offset for count

	// Generate and execute
	generated, err := e.generator.Generate(ast)
	if err != nil {
		return 0, err
	}

	ctx, cancel := context.WithTimeout(ctx, e.queryTimeout)
	defer cancel()

	var count int64
	err = e.pool.QueryRow(ctx, generated.SQL, generated.Params...).Scan(&count)
	if err != nil {
		return 0, err
	}

	return count, nil
}

// ExecuteExists checks if any rows match.
func (e *Executor) ExecuteExists(ctx context.Context, astJSON []byte) (bool, error) {
	// Parse and modify AST
	ast, err := ParseAST(astJSON)
	if err != nil {
		return false, err
	}

	// Just need to know if any row exists
	one := 1
	ast.Limit = &one
	ast.Columns = []string{"1"}
	ast.Order = nil

	generated, err := e.generator.Generate(ast)
	if err != nil {
		return false, err
	}

	ctx, cancel := context.WithTimeout(ctx, e.queryTimeout)
	defer cancel()

	rows, err := e.pool.Query(ctx, generated.SQL, generated.Params...)
	if err != nil {
		return false, err
	}
	defer rows.Close()

	return rows.Next(), nil
}

// ExecuteModify executes DELETE/UPDATE and returns affected count.
func (e *Executor) ExecuteModify(ctx context.Context, astJSON []byte) (int64, error) {
	// Parse AST
	ast, err := ParseAST(astJSON)
	if err != nil {
		return 0, err
	}

	// Validate type
	if ast.Type != QueryTypeDelete && ast.Type != QueryTypeUpdate {
		return 0, fmt.Errorf("ExecuteModify requires DELETE or UPDATE query")
	}

	// Generate SQL
	generated, err := e.generator.Generate(ast)
	if err != nil {
		return 0, err
	}

	ctx, cancel := context.WithTimeout(ctx, e.queryTimeout)
	defer cancel()

	// Execute
	result, err := e.pool.Exec(ctx, generated.SQL, generated.Params...)
	if err != nil {
		return 0, err
	}

	return result.RowsAffected(), nil
}

// =============================================================================
// Explain (for debugging)
// =============================================================================

// Explain returns the generated SQL without executing it.
func (e *Executor) Explain(astJSON []byte) (string, []interface{}, error) {
	ast, err := ParseAST(astJSON)
	if err != nil {
		return "", nil, err
	}

	optimizedAST := e.optimizer.Optimize(ast)

	generated, err := e.generator.Generate(optimizedAST)
	if err != nil {
		return "", nil, err
	}

	return generated.SQL, generated.Params, nil
}

// ExplainQuery runs EXPLAIN ANALYZE on the query.
func (e *Executor) ExplainQuery(ctx context.Context, astJSON []byte) ([]string, error) {
	sql, params, err := e.Explain(astJSON)
	if err != nil {
		return nil, err
	}

	explainSQL := "EXPLAIN ANALYZE " + sql

	rows, err := e.pool.Query(ctx, explainSQL, params...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var plan []string
	for rows.Next() {
		var line string
		if err := rows.Scan(&line); err != nil {
			return nil, err
		}
		plan = append(plan, line)
	}

	return plan, nil
}

// =============================================================================
// Batch Execution
// =============================================================================

// BatchQuery represents a single query in a batch.
type BatchQuery struct {
	ASTJSON []byte
	Result  *QueryResult
	Error   error
}

// ExecuteBatch executes multiple queries in parallel.
func (e *Executor) ExecuteBatch(ctx context.Context, queries [][]byte) ([]*QueryResult, error) {
	results := make([]*QueryResult, len(queries))
	errors := make([]error, len(queries))

	// Use pgx batch for efficiency
	batch := &pgx.Batch{}
	parsedASTs := make([]*QueryAST, len(queries))
	generatedQueries := make([]*GeneratedQuery, len(queries))

	// Parse and generate all queries
	for i, astJSON := range queries {
		ast, err := ParseAST(astJSON)
		if err != nil {
			errors[i] = err
			continue
		}
		parsedASTs[i] = ast

		optimized := e.optimizer.Optimize(ast)
		generated, err := e.generator.Generate(optimized)
		if err != nil {
			errors[i] = err
			continue
		}
		generatedQueries[i] = generated

		batch.Queue(generated.SQL, generated.Params...)
	}

	// Execute batch
	ctx, cancel := context.WithTimeout(ctx, e.queryTimeout)
	defer cancel()

	batchResults := e.pool.SendBatch(ctx, batch)
	defer batchResults.Close()

	// Collect results
	for i := range queries {
		if errors[i] != nil {
			continue
		}

		rows, err := batchResults.Query()
		if err != nil {
			errors[i] = err
			continue
		}

		// Get columns
		fieldDescs := rows.FieldDescriptions()
		columns := make([]string, len(fieldDescs))
		for j, fd := range fieldDescs {
			columns[j] = string(fd.Name)
		}

		// Collect rows
		var resultRows [][]interface{}
		for rows.Next() {
			values, err := rows.Values()
			if err != nil {
				errors[i] = err
				break
			}
			resultRows = append(resultRows, values)
		}
		rows.Close()

		if errors[i] == nil {
			results[i] = &QueryResult{
				Columns:  columns,
				Rows:     resultRows,
				RowCount: len(resultRows),
			}
		}
	}

	// Check for any errors
	for i, err := range errors {
		if err != nil {
			return results, fmt.Errorf("query %d failed: %w", i, err)
		}
	}

	return results, nil
}
