/*
Package bridge provides the CGO interface between Python and Go.

This package defines all types shared between Python and Go,
serialized via JSON for simplicity and debuggability.

Design Principles:
  - All types are JSON-serializable for easy debugging
  - Error messages are descriptive and actionable
  - Status codes follow HTTP conventions (0=success, 1=error)
*/
package bridge

import (
	"time"

	"github.com/bytedance/sonic"
)

// =============================================================================
// Configuration Types
// =============================================================================

// Config holds all Go bridge configuration.
// Passed from Python during initialization.
type Config struct {
	// Database connection
	Primary  string   `json:"primary"`            // Primary connection string
	Replicas []string `json:"replicas,omitempty"` // Read replica connection strings

	// Pool settings
	PoolMinSize        int `json:"pool_min_size"`        // Minimum connections (default: 2)
	PoolMaxSize        int `json:"pool_max_size"`        // Maximum connections (default: 10)
	PoolMaxIdleTime    int `json:"pool_max_idle_time"`   // Idle timeout in seconds (default: 300)
	PoolMaxLifetime    int `json:"pool_max_lifetime"`    // Max connection lifetime in seconds (default: 3600)
	PoolHealthInterval int `json:"pool_health_interval"` // Health check interval in seconds (default: 30)

	// Query settings
	QueryTimeout   int `json:"query_timeout"`    // Default query timeout in ms (default: 30000)
	StatementCache int `json:"statement_cache"`  // Prepared statement cache size (default: 256)
	MaxRetries     int `json:"max_retries"`      // Max retry attempts (default: 3)
	RetryBackoffMs int `json:"retry_backoff_ms"` // Initial backoff in ms (default: 100)

	// Feature flags
	EnableArrow    bool `json:"enable_arrow"`    // Use Arrow for results (default: true)
	EnablePrepared bool `json:"enable_prepared"` // Use prepared statements (default: true)
	EnableBatch    bool `json:"enable_batch"`    // Enable batch optimizations (default: true)
	Debug          bool `json:"debug"`           // Enable debug logging (default: false)
}

// DefaultConfig returns sensible defaults for production use.
func DefaultConfig() Config {
	return Config{
		PoolMinSize:        2,
		PoolMaxSize:        10,
		PoolMaxIdleTime:    300,
		PoolMaxLifetime:    3600,
		PoolHealthInterval: 30,
		QueryTimeout:       30000,
		StatementCache:     256,
		MaxRetries:         3,
		RetryBackoffMs:     100,
		EnableArrow:        true,
		EnablePrepared:     true,
		EnableBatch:        true,
		Debug:              false,
	}
}

// Validate checks if the config is valid.
func (c *Config) Validate() error {
	if c.Primary == "" {
		return ErrNoPrimaryDSN
	}
	if c.PoolMinSize < 0 {
		return ErrInvalidPoolMin
	}
	if c.PoolMaxSize < 1 {
		return ErrInvalidPoolMax
	}
	if c.PoolMinSize > c.PoolMaxSize {
		return ErrPoolMinGtMax
	}
	return nil
}

// =============================================================================
// Query Types
// =============================================================================

// QueryRequest represents a query from Python.
type QueryRequest struct {
	SQL        string        `json:"sql"`                   // SQL query text
	Params     []interface{} `json:"params,omitempty"`      // Query parameters
	TimeoutMs  int           `json:"timeout_ms,omitempty"`  // Override default timeout
	UseReplica bool          `json:"use_replica,omitempty"` // Route to replica
	NoCache    bool          `json:"no_cache,omitempty"`    // Skip prepared statement cache
}

// QueryResult represents the result of a query.
type QueryResult struct {
	// Status
	Success bool   `json:"success"`         // True if query succeeded
	Error   string `json:"error,omitempty"` // Error message if failed

	// Metadata
	RowsAffected int64   `json:"rows_affected"` // Number of rows affected
	Duration     float64 `json:"duration_ms"`   // Query duration in milliseconds
	Cached       bool    `json:"cached"`        // Whether prepared statement was used

	// Data (one of these will be set)
	ArrowBuffer []byte          `json:"arrow_buffer,omitempty"` // Arrow IPC buffer
	Rows        [][]interface{} `json:"rows,omitempty"`         // JSON rows (fallback)
	Columns     []string        `json:"columns,omitempty"`      // Column names
}

// BatchRequest represents multiple queries to execute.
type BatchRequest struct {
	Queries     []QueryRequest `json:"queries"`                 // Queries to execute
	Transaction bool           `json:"transaction,omitempty"`   // Wrap in transaction
	StopOnError bool           `json:"stop_on_error,omitempty"` // Stop on first error
}

// BatchResult represents the results of a batch operation.
type BatchResult struct {
	Success  bool          `json:"success"`         // True if all succeeded
	Error    string        `json:"error,omitempty"` // First error if failed
	Results  []QueryResult `json:"results"`         // Individual results
	Duration float64       `json:"duration_ms"`     // Total duration
}

// =============================================================================
// Health Types
// =============================================================================

// HealthStatus represents the overall health of the Go bridge.
type HealthStatus struct {
	Status    string             `json:"status"`    // "healthy", "degraded", "unhealthy"
	Primary   *ConnectionHealth  `json:"primary"`   // Primary connection health
	Replicas  []ConnectionHealth `json:"replicas"`  // Replica health
	Pool      PoolHealth         `json:"pool"`      // Pool statistics
	Timestamp time.Time          `json:"timestamp"` // When this was checked
}

// ConnectionHealth represents health of a single connection/pool.
type ConnectionHealth struct {
	URL       string  `json:"url"`        // Connection URL (masked)
	Status    string  `json:"status"`     // "ok", "degraded", "down"
	LatencyMs float64 `json:"latency_ms"` // Last ping latency
	Error     string  `json:"error,omitempty"`
}

// PoolHealth represents connection pool statistics.
type PoolHealth struct {
	TotalConns  int     `json:"total_conns"`  // Total connections in pool
	IdleConns   int     `json:"idle_conns"`   // Idle connections
	ActiveConns int     `json:"active_conns"` // Active connections
	WaitingReqs int     `json:"waiting_reqs"` // Waiting acquire requests
	AvgWaitMs   float64 `json:"avg_wait_ms"`  // Average wait time
	MaxWaitMs   float64 `json:"max_wait_ms"`  // Maximum wait time
}

// =============================================================================
// Error Types
// =============================================================================

// BridgeError is returned for all Go bridge errors.
type BridgeError struct {
	Code    int    `json:"code"`    // Error code
	Message string `json:"message"` // Human-readable message
	Details string `json:"details"` // Additional details
}

func (e *BridgeError) Error() string {
	return e.Message
}

// Error codes (match Python exceptions).
const (
	ErrCodeSuccess          = 0
	ErrCodeConfig           = 1
	ErrCodeConnection       = 2
	ErrCodeQuery            = 3
	ErrCodeTimeout          = 4
	ErrCodePool             = 5
	ErrCodeArrow            = 6
	ErrCodeNotInitialized   = 7
	ErrCodeAlreadyInit      = 8
	ErrCodeQueryFailed      = 9  // Query execution failed
	ErrCodeValidationFailed = 10 // Query validation failed
)

// Standard errors.
var (
	ErrNoPrimaryDSN   = &BridgeError{ErrCodeConfig, "primary connection string required", ""}
	ErrInvalidPoolMin = &BridgeError{ErrCodeConfig, "pool_min_size must be >= 0", ""}
	ErrInvalidPoolMax = &BridgeError{ErrCodeConfig, "pool_max_size must be >= 1", ""}
	ErrPoolMinGtMax   = &BridgeError{ErrCodeConfig, "pool_min_size cannot exceed pool_max_size", ""}
	ErrNotInitialized = &BridgeError{ErrCodeNotInitialized, "Go bridge not initialized - call PynextInit first", ""}
	ErrAlreadyInit    = &BridgeError{ErrCodeAlreadyInit, "Go bridge already initialized", ""}
)

// =============================================================================
// Utility Functions
// =============================================================================

// MustMarshal marshals v to JSON, panicking on error.
// Only use for types we control that are always valid.
func MustMarshal(v interface{}) []byte {
	b, err := sonic.Marshal(v)
	if err != nil {
		panic("json marshal failed: " + err.Error())
	}
	return b
}

// ParseConfig parses JSON config from Python.
func ParseConfig(jsonData []byte) (*Config, error) {
	config := DefaultConfig()
	if err := sonic.Unmarshal(jsonData, &config); err != nil {
		return nil, &BridgeError{
			Code:    ErrCodeConfig,
			Message: "invalid configuration JSON",
			Details: err.Error(),
		}
	}
	if err := config.Validate(); err != nil {
		return nil, err
	}
	return &config, nil
}

// MaskDSN masks sensitive parts of a connection string.
func MaskDSN(dsn string) string {
	// Simple masking - hide everything after @ and before /
	// Example: postgres://user:pass@host:5432/db -> postgres://***@host:5432/db
	if len(dsn) == 0 {
		return ""
	}
	// For security, just return a placeholder
	return "***"
}
