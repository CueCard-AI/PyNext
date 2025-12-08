# Query Builder Internals

This document provides a deep technical dive into the PyNext Query Builder implementation. It covers the AST structure, Go optimization, SQL generation, and the Python-Go bridge integration.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              PYTHON LAYER                                    │
│                                                                              │
│  User.q(gt("age", 18))                                                      │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐       │
│  │ Condition       │────▶│ QueryBuilder    │────▶│ QueryAST        │       │
│  │ Functions       │     │ (Chainable)     │     │ (Immutable)     │       │
│  │ gt(), eq(), ... │     │ .select()...    │     │ to_dict() → JSON│       │
│  └─────────────────┘     └─────────────────┘     └─────────────────┘       │
│                                                          │                   │
└──────────────────────────────────────────────────────────│───────────────────┘
                                                           │ JSON via ctypes
┌──────────────────────────────────────────────────────────▼───────────────────┐
│                               GO LAYER                                       │
│                                                                              │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐       │
│  │ query.ParseAST  │────▶│ query.Optimizer │────▶│ query.Generator │       │
│  │ (JSON → AST)    │     │ (Reorder, etc.) │     │ (AST → SQL)     │       │
│  └─────────────────┘     └─────────────────┘     └─────────────────┘       │
│                                                          │                   │
│                                                          ▼                   │
│                                                  ┌─────────────────┐       │
│                                                  │ query.Executor  │       │
│                                                  │ (pgx Pool)      │       │
│                                                  └─────────────────┘       │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Python Layer

### Condition Classes (`pynext/db/conditions.py`)

The condition module provides type-safe condition builders:

```python
# Condition class hierarchy
Condition         # Simple: field op value
LogicalCondition  # Logical: AND/OR/NOT with children
RawCondition      # Raw SQL with params

# Operator enum
class Operator(str, Enum):
    EQ = "="
    NE = "!="
    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="
    LIKE = "LIKE"
    ILIKE = "ILIKE"
    IN = "IN"
    NOT_IN = "NOT IN"
    IS_NULL = "IS NULL"
    IS_NOT_NULL = "IS NOT NULL"
    BETWEEN = "BETWEEN"
    CONTAINS = "@>"
    CONTAINED_BY = "<@"
    OVERLAPS = "&&"
```

Each condition function creates a `Condition` object:

```python
def gt(field: str, value: Any) -> Condition:
    return Condition(field=field, op=Operator.GT, value=value)

# Usage
cond = gt("age", 18)
cond.field   # "age"
cond.op      # Operator.GT
cond.value   # 18
```

### QueryBuilder (`pynext/db/query_builder.py`)

The QueryBuilder uses the builder pattern with immutability:

```python
class QueryBuilder(Generic[T]):
    __slots__ = ("_model", "_ast", "_adapter")
    
    def __init__(self, model: Type[T], ast: Optional[QueryAST] = None, adapter = None):
        self._model = model
        self._ast = ast or QueryAST(table=model.__table_name__)
        self._adapter = adapter
    
    # Every method returns NEW builder (immutable)
    def select(self, *columns: str) -> "QueryBuilder[T]":
        new_ast = self._ast.with_columns(*columns)
        return QueryBuilder(self._model, ast=new_ast, adapter=self._adapter)
```

### AST Structure (`pynext/db/ast.py`)

The AST is a complete, serializable representation of a query:

```python
@dataclass
class QueryAST:
    table: str
    query_type: QueryType = QueryType.SELECT
    columns: Optional[List[str]] = None
    conditions: Optional[ConditionNode] = None
    order: List[OrderNode] = field(default_factory=list)
    limit: Optional[int] = None
    offset: Optional[int] = None
    includes: List[str] = field(default_factory=list)
    joins: List[JoinNode] = field(default_factory=list)
    group_by: List[str] = field(default_factory=list)
    having: Optional[ConditionNode] = None
    distinct: bool = False
    for_update: bool = False
    params: List[Any] = field(default_factory=list)
    raw_sql: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Serialize to JSON-compatible dict for Go."""
        result = {"table": self.table, "type": self.query_type.value}
        if self.columns: result["columns"] = self.columns
        if self.conditions: result["conditions"] = self.conditions.to_dict()
        # ... etc
        return result
```

### Tuple Parsing

Tuples are parsed into Condition objects:

```python
_OPERATOR_MAP = {
    "=": Operator.EQ, "==": Operator.EQ,
    "!=": Operator.NE, "<>": Operator.NE,
    ">": Operator.GT, ">=": Operator.GTE,
    "<": Operator.LT, "<=": Operator.LTE,
    # ...
}

def parse_tuple_condition(tup: tuple) -> Condition:
    if len(tup) == 2:  # ("field", "is null")
        field, op_str = tup
        op = _OPERATOR_MAP.get(op_str.lower())
        return Condition(field=field, op=op, value=None)
    
    elif len(tup) == 3:  # ("field", "=", value)
        field, op_str, value = tup
        op = _OPERATOR_MAP.get(op_str)
        return Condition(field=field, op=op, value=value)
    
    elif len(tup) == 4:  # ("field", "between", low, high)
        field, op_str, value1, value2 = tup
        return Condition(field=field, op=Operator.BETWEEN, value=value1, value2=value2)
```

## Go Layer

### AST Parsing (`go/pkg/query/ast.go`)

The Go layer parses the JSON AST:

```go
type QueryAST struct {
    Table      string          `json:"table"`
    Type       QueryType       `json:"type"`
    Columns    []string        `json:"columns,omitempty"`
    Conditions *ConditionNode  `json:"conditions,omitempty"`
    Order      []OrderNode     `json:"order,omitempty"`
    Limit      *int            `json:"limit,omitempty"`
    Offset     *int            `json:"offset,omitempty"`
    // ...
}

func ParseAST(jsonData []byte) (*QueryAST, error) {
    var ast QueryAST
    if err := json.Unmarshal(jsonData, &ast); err != nil {
        return nil, fmt.Errorf("failed to parse query AST: %w", err)
    }
    // Validate
    if ast.Table == "" && ast.Type != QueryTypeRaw {
        return nil, fmt.Errorf("query AST missing required field: table")
    }
    return &ast, nil
}
```

### Optimizer (`go/pkg/query/optimizer.go`)

The optimizer applies several transformations:

```go
func (o *Optimizer) Optimize(ast *QueryAST) *QueryAST {
    optimized := o.cloneAST(ast)
    
    if optimized.Conditions != nil {
        // 1. Flatten unnecessary nesting
        // AND(AND(a, b), c) → AND(a, b, c)
        optimized.Conditions = o.flattenConditions(optimized.Conditions)
        
        // 2. Reorder conditions (most selective first)
        // Put id, *_id, unique fields first
        optimized.Conditions = o.reorderConditions(optimized.Conditions)
        
        // 3. Remove duplicates
        optimized.Conditions = o.simplifyConditions(optimized.Conditions)
    }
    
    // 4. Add default order for deterministic pagination
    if optimized.Limit != nil && len(optimized.Order) == 0 {
        optimized.Order = []OrderNode{{Field: "id", Direction: "ASC"}}
    }
    
    return optimized
}
```

#### Selectivity Scoring

Conditions are ordered by estimated selectivity:

```go
func (o *Optimizer) selectivityScore(cond *ConditionNode) float64 {
    // Indexed fields are most selective
    if o.isLikelyIndexed(cond.Field) {
        return 0.1
    }
    
    // Score by operator
    switch cond.Op {
    case "=":
        return 0.2  // Equality very selective
    case "IN":
        return 0.2 + float64(len(values))*0.05  // Less selective with more values
    case "IS NULL", "IS NOT NULL":
        return 0.3
    case ">", ">=", "<", "<=":
        return 0.4  // Range moderately selective
    case "LIKE", "ILIKE":
        if !strings.HasPrefix(value, "%") {
            return 0.4  // Prefix LIKE can use index
        }
        return 0.7  // Contains LIKE is slow
    case "!=":
        return 0.8  // Not equal rarely selective
    default:
        return 0.5
    }
}
```

### SQL Generator (`go/pkg/query/generator.go`)

The generator produces parameterized SQL:

```go
type Generator struct {
    dialect      string
    paramCounter int
    params       []interface{}
}

func (g *Generator) Generate(ast *QueryAST) (*GeneratedQuery, error) {
    g.paramCounter = 0
    g.params = make([]interface{}, 0)
    
    var sql string
    var err error
    
    switch ast.Type {
    case QueryTypeSelect:
        sql, err = g.generateSelect(ast)
    case QueryTypeDelete:
        sql, err = g.generateDelete(ast)
    // ...
    }
    
    return &GeneratedQuery{SQL: sql, Params: g.params}, nil
}

func (g *Generator) generateSelect(ast *QueryAST) (string, error) {
    var parts []string
    
    // SELECT [DISTINCT] columns
    selectClause := "SELECT"
    if ast.Distinct {
        selectClause += " DISTINCT"
    }
    selectClause += " " + ast.ColumnList()
    parts = append(parts, selectClause)
    
    // FROM table
    parts = append(parts, "FROM " + g.quoteIdentifier(ast.Table))
    
    // WHERE conditions
    if ast.HasConditions() {
        whereSQL, err := g.generateConditions(ast.Conditions, ast.Params)
        parts = append(parts, "WHERE "+whereSQL)
    }
    
    // ORDER BY, LIMIT, OFFSET, FOR UPDATE
    // ...
    
    return strings.Join(parts, " "), nil
}
```

#### Condition Generation

Each condition type has specific SQL generation:

```go
func (g *Generator) generateSimpleCondition(cond *ConditionNode) (string, error) {
    field := g.quoteIdentifier(cond.Field)
    
    switch cond.Op {
    case "IS NULL", "IS NOT NULL":
        return fmt.Sprintf("%s %s", field, cond.Op), nil
        
    case "IN", "NOT IN":
        values := cond.Value.([]interface{})
        placeholders := make([]string, len(values))
        for i, v := range values {
            g.paramCounter++
            placeholders[i] = fmt.Sprintf("$%d", g.paramCounter)
            g.params = append(g.params, v)
        }
        return fmt.Sprintf("%s %s (%s)", field, cond.Op, 
            strings.Join(placeholders, ", ")), nil
        
    case "BETWEEN":
        g.paramCounter++
        p1 := fmt.Sprintf("$%d", g.paramCounter)
        g.params = append(g.params, cond.Value)
        g.paramCounter++
        p2 := fmt.Sprintf("$%d", g.paramCounter)
        g.params = append(g.params, cond.Value2)
        return fmt.Sprintf("%s BETWEEN %s AND %s", field, p1, p2), nil
        
    default:
        g.paramCounter++
        placeholder := fmt.Sprintf("$%d", g.paramCounter)
        g.params = append(g.params, cond.Value)
        return fmt.Sprintf("%s %s %s", field, cond.Op, placeholder), nil
    }
}
```

### Validator (`go/pkg/query/validator.go`)

The validator checks for security issues:

```go
type Validator struct {
    allowedOps    map[string]bool
    maxConditions int
    maxDepth      int
    allowRawSQL   bool
}

func (v *Validator) Validate(ast *QueryAST) error {
    // Validate table name format
    if !v.isValidIdentifier(ast.Table) {
        return &ValidationError{Code: "INVALID_TABLE", ...}
    }
    
    // Validate conditions
    if ast.Conditions != nil {
        if err := v.validateConditions(ast.Conditions); err != nil {
            return err
        }
        
        // Check complexity
        count := ast.Conditions.ConditionCount()
        if count > v.maxConditions {
            return &ValidationError{Code: "TOO_COMPLEX", ...}
        }
        
        // Check depth
        depth := ast.Conditions.Depth()
        if depth > v.maxDepth {
            return &ValidationError{Code: "TOO_DEEP", ...}
        }
    }
    
    // Validate raw SQL for dangerous patterns
    if ast.RawSQL != "" {
        warnings := v.ValidateRawSQL(ast.RawSQL)
        if len(warnings) > 0 {
            return &ValidationError{Code: "DANGEROUS_SQL", ...}
        }
    }
    
    return nil
}
```

### Executor (`go/pkg/query/executor.go`)

The executor ties everything together:

```go
func (e *Executor) Execute(ctx context.Context, astJSON []byte) (*QueryResult, error) {
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
    
    // 3. Optimize
    optimizedAST := e.optimizer.Optimize(ast)
    
    // 4. Generate SQL
    generated, err := e.generator.Generate(optimizedAST)
    if err != nil {
        return nil, fmt.Errorf("generation error: %w", err)
    }
    
    // 5. Execute via pgx pool
    result, err := e.executeSQL(ctx, generated.SQL, generated.Params)
    
    return result, nil
}
```

## Python-Go Bridge

### CGO Exports (`go/pkg/bridge/bridge.go`)

Go functions are exported for Python via CGO:

```go
//export PynextQueryExecute
func PynextQueryExecute(astJSON *C.char, outBuffer **C.char, outLen *C.int) C.int {
    globalMutex.RLock()
    if globalBridge == nil {
        globalMutex.RUnlock()
        return C.int(ErrCodeNotInitialized)
    }
    bridge := globalBridge
    globalMutex.RUnlock()
    
    // Execute query
    result, err := bridge.QueryExecute(C.GoString(astJSON))
    if err != nil {
        errJSON := MustMarshal(map[string]string{"error": err.Error()})
        *outBuffer = C.alloc_string((*C.char)(unsafe.Pointer(&errJSON[0])), C.int(len(errJSON)))
        *outLen = C.int(len(errJSON))
        return C.int(ErrCodeQueryFailed)
    }
    
    // Return JSON result
    resultJSON, _ := sonic.Marshal(result)
    *outBuffer = C.alloc_string((*C.char)(unsafe.Pointer(&resultJSON[0])), C.int(len(resultJSON)))
    *outLen = C.int(len(resultJSON))
    return C.int(ErrCodeSuccess)
}
```

### Python ctypes (`pynext_go/bridge.py`)

Python calls Go via ctypes:

```python
# Set up function signature
_GO_LIB.PynextQueryExecute.argtypes = [
    ctypes.c_char_p,
    ctypes.POINTER(ctypes.c_char_p),
    ctypes.POINTER(ctypes.c_int),
]
_GO_LIB.PynextQueryExecute.restype = ctypes.c_int

# Call Go
def execute_query(self, ast_json: str) -> QueryResult:
    if isinstance(ast_json, str):
        ast_json = ast_json.encode("utf-8")
    
    out_buffer = ctypes.c_char_p()
    out_len = ctypes.c_int()
    
    result_code = _GO_LIB.PynextQueryExecute(
        ast_json,
        ctypes.byref(out_buffer),
        ctypes.byref(out_len),
    )
    
    try:
        response = json_loads(out_buffer.value)
        if result_code != 0:
            raise BridgeQueryError(response.get("error"))
        return QueryResult.from_dict(response)
    finally:
        _GO_LIB.PynextFreeBuffer(out_buffer)
```

## Performance Characteristics

### Memory Flow

```
Python str → bytes (encode) → C char* → Go string (copy) → Parse → Execute
          → Go []byte (result) → C char* (alloc) → Python bytes → dict (orjson)
```

Key optimizations:
- `orjson` for fast JSON in Python
- `sonic` for fast JSON in Go
- Reusable buffers in Go generator
- Parameter pooling

### Latency Breakdown

For a typical query:

```
Python QueryBuilder construction:  < 0.1ms
AST to JSON serialization:         < 0.1ms
ctypes call overhead:              < 0.1ms
Go JSON parsing:                   < 0.1ms
Go optimization:                   < 0.1ms
Go SQL generation:                 < 0.1ms
PostgreSQL execution:              1-10ms (varies)
Result serialization:              < 0.5ms
Python result parsing:             < 0.5ms
─────────────────────────────────────────────
Total overhead:                    < 1.5ms
```

The Go bridge adds minimal overhead (~1ms) while providing:
- True parallelism for batch queries
- Connection pooling
- Prepared statement caching
- Query optimization

## Testing

### Python Tests

```bash
# Run condition tests
pytest tests/unit/db/test_conditions.py -v

# Run query builder tests
pytest tests/unit/db/test_query_builder.py -v

# Run AST tests
pytest tests/unit/db/test_ast.py -v
```

### Go Tests

```bash
cd go

# Run all query tests
go test ./pkg/query/... -v

# Run specific test
go test ./pkg/query/... -run TestGenerate_SimpleSelect -v

# Run benchmarks
go test ./pkg/query/... -bench=. -benchmem
```

## Debugging

### Enable Verbose Logging

```python
import logging
logging.getLogger("pynext.db").setLevel(logging.DEBUG)
logging.getLogger("pynext_go").setLevel(logging.DEBUG)
```

### Inspect Generated SQL

```python
query = User.q(gt("age", 18)).select("id", "name")

# Get explanation
print(query.explain())

# Get AST dict
import json
print(json.dumps(query.to_dict(), indent=2))

# Get generated SQL (via Go)
import pynext_go
result = pynext_go.query_explain(json.dumps(query.to_dict()))
print(result["sql"])
print(result["params"])
```

### Go Debug Build

```bash
cd go
CGO_ENABLED=1 go build -gcflags="all=-N -l" -o libpynext.so -buildmode=c-shared ./cmd/bridge
```

Then use with gdb/lldb for Go-side debugging.

