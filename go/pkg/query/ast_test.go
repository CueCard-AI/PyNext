package query

import (
	"testing"
)

// =============================================================================
// ParseAST Tests
// =============================================================================

func TestParseAST_Basic(t *testing.T) {
	tests := []struct {
		name    string
		json    string
		wantErr bool
	}{
		{
			name: "basic select",
			json: `{
				"table": "users",
				"type": "SELECT"
			}`,
			wantErr: false,
		},
		{
			name: "select with columns",
			json: `{
				"table": "users",
				"type": "SELECT",
				"columns": ["id", "name", "email"]
			}`,
			wantErr: false,
		},
		{
			name: "empty table name",
			json: `{
				"table": "",
				"type": "SELECT"
			}`,
			wantErr: true,
		},
		{
			name: "missing type defaults to SELECT",
			json: `{
				"table": "users"
			}`,
			wantErr: false,
		},
		{
			name:    "invalid json",
			json:    `{invalid}`,
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			ast, err := ParseAST([]byte(tt.json))
			if (err != nil) != tt.wantErr {
				t.Errorf("ParseAST() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			if !tt.wantErr && ast == nil {
				t.Error("ParseAST() returned nil ast without error")
			}
		})
	}
}

func TestParseAST_WithConditions(t *testing.T) {
	tests := []struct {
		name          string
		json          string
		wantCondType  string
		wantCondField string
		wantCondOp    string
	}{
		{
			name: "simple equality",
			json: `{
				"table": "users",
				"type": "SELECT",
				"conditions": {
					"type": "condition",
					"field": "status",
					"op": "=",
					"value": "active"
				}
			}`,
			wantCondType:  "condition",
			wantCondField: "status",
			wantCondOp:    "=",
		},
		{
			name: "greater than",
			json: `{
				"table": "users",
				"type": "SELECT",
				"conditions": {
					"type": "condition",
					"field": "age",
					"op": ">",
					"value": 18
				}
			}`,
			wantCondType:  "condition",
			wantCondField: "age",
			wantCondOp:    ">",
		},
		{
			name: "IN operator",
			json: `{
				"table": "users",
				"type": "SELECT",
				"conditions": {
					"type": "condition",
					"field": "role",
					"op": "IN",
					"value": ["admin", "moderator"]
				}
			}`,
			wantCondType:  "condition",
			wantCondField: "role",
			wantCondOp:    "IN",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			ast, err := ParseAST([]byte(tt.json))
			if err != nil {
				t.Fatalf("ParseAST() error = %v", err)
			}

			if ast.Conditions == nil {
				t.Fatal("Expected conditions, got nil")
			}

			if ast.Conditions.Type != tt.wantCondType {
				t.Errorf("Condition type = %v, want %v", ast.Conditions.Type, tt.wantCondType)
			}
			if ast.Conditions.Field != tt.wantCondField {
				t.Errorf("Condition field = %v, want %v", ast.Conditions.Field, tt.wantCondField)
			}
			if ast.Conditions.Op != tt.wantCondOp {
				t.Errorf("Condition op = %v, want %v", ast.Conditions.Op, tt.wantCondOp)
			}
		})
	}
}

func TestParseAST_LogicalConditions(t *testing.T) {
	tests := []struct {
		name         string
		json         string
		wantType     string
		wantLogicOp  string
		wantNumItems int
	}{
		{
			name: "AND condition",
			json: `{
				"table": "users",
				"type": "SELECT",
				"conditions": {
					"type": "logical",
					"op": "AND",
					"conditions": [
						{"type": "condition", "field": "age", "op": ">", "value": 18},
						{"type": "condition", "field": "status", "op": "=", "value": "active"}
					]
				}
			}`,
			wantType:     "logical",
			wantLogicOp:  "AND",
			wantNumItems: 2,
		},
		{
			name: "OR condition",
			json: `{
				"table": "users",
				"type": "SELECT",
				"conditions": {
					"type": "logical",
					"op": "OR",
					"conditions": [
						{"type": "condition", "field": "role", "op": "=", "value": "admin"},
						{"type": "condition", "field": "role", "op": "=", "value": "moderator"}
					]
				}
			}`,
			wantType:     "logical",
			wantLogicOp:  "OR",
			wantNumItems: 2,
		},
		{
			name: "nested conditions",
			json: `{
				"table": "users",
				"type": "SELECT",
				"conditions": {
					"type": "logical",
					"op": "AND",
					"conditions": [
						{"type": "condition", "field": "age", "op": ">", "value": 18},
						{
							"type": "logical",
							"op": "OR",
							"conditions": [
								{"type": "condition", "field": "role", "op": "=", "value": "admin"},
								{"type": "condition", "field": "role", "op": "=", "value": "mod"}
							]
						}
					]
				}
			}`,
			wantType:     "logical",
			wantLogicOp:  "AND",
			wantNumItems: 2,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			ast, err := ParseAST([]byte(tt.json))
			if err != nil {
				t.Fatalf("ParseAST() error = %v", err)
			}

			if ast.Conditions == nil {
				t.Fatal("Expected conditions, got nil")
			}

			if ast.Conditions.Type != tt.wantType {
				t.Errorf("Condition type = %v, want %v", ast.Conditions.Type, tt.wantType)
			}
			if ast.Conditions.Op != tt.wantLogicOp {
				t.Errorf("Op = %v, want %v", ast.Conditions.Op, tt.wantLogicOp)
			}
			if len(ast.Conditions.Conditions) != tt.wantNumItems {
				t.Errorf("Conditions count = %v, want %v", len(ast.Conditions.Conditions), tt.wantNumItems)
			}
		})
	}
}

func TestParseAST_OrderBy(t *testing.T) {
	tests := []struct {
		name       string
		json       string
		wantOrders []OrderNode
	}{
		{
			name: "single order ASC",
			json: `{
				"table": "users",
				"type": "SELECT",
				"order": [{"field": "name", "direction": "ASC"}]
			}`,
			wantOrders: []OrderNode{{Field: "name", Direction: "ASC"}},
		},
		{
			name: "single order DESC",
			json: `{
				"table": "users",
				"type": "SELECT",
				"order": [{"field": "created_at", "direction": "DESC"}]
			}`,
			wantOrders: []OrderNode{{Field: "created_at", Direction: "DESC"}},
		},
		{
			name: "multiple orders",
			json: `{
				"table": "users",
				"type": "SELECT",
				"order": [
					{"field": "status", "direction": "ASC"},
					{"field": "age", "direction": "DESC"}
				]
			}`,
			wantOrders: []OrderNode{
				{Field: "status", Direction: "ASC"},
				{Field: "age", Direction: "DESC"},
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			ast, err := ParseAST([]byte(tt.json))
			if err != nil {
				t.Fatalf("ParseAST() error = %v", err)
			}

			if len(ast.Order) != len(tt.wantOrders) {
				t.Fatalf("Order count = %v, want %v", len(ast.Order), len(tt.wantOrders))
			}

			for i, want := range tt.wantOrders {
				if ast.Order[i].Field != want.Field {
					t.Errorf("Order[%d].Field = %v, want %v", i, ast.Order[i].Field, want.Field)
				}
				if ast.Order[i].Direction != want.Direction {
					t.Errorf("Order[%d].Direction = %v, want %v", i, ast.Order[i].Direction, want.Direction)
				}
			}
		})
	}
}

func TestParseAST_LimitOffset(t *testing.T) {
	tests := []struct {
		name       string
		json       string
		wantLimit  *int
		wantOffset *int
	}{
		{
			name: "limit only",
			json: `{
				"table": "users",
				"type": "SELECT",
				"limit": 10
			}`,
			wantLimit:  intPtr(10),
			wantOffset: nil,
		},
		{
			name: "offset only",
			json: `{
				"table": "users",
				"type": "SELECT",
				"offset": 20
			}`,
			wantLimit:  nil,
			wantOffset: intPtr(20),
		},
		{
			name: "both limit and offset",
			json: `{
				"table": "users",
				"type": "SELECT",
				"limit": 10,
				"offset": 20
			}`,
			wantLimit:  intPtr(10),
			wantOffset: intPtr(20),
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			ast, err := ParseAST([]byte(tt.json))
			if err != nil {
				t.Fatalf("ParseAST() error = %v", err)
			}

			if tt.wantLimit != nil {
				if ast.Limit == nil || *ast.Limit != *tt.wantLimit {
					t.Errorf("Limit = %v, want %v", ast.Limit, *tt.wantLimit)
				}
			}
			if tt.wantOffset != nil {
				if ast.Offset == nil || *ast.Offset != *tt.wantOffset {
					t.Errorf("Offset = %v, want %v", ast.Offset, *tt.wantOffset)
				}
			}
		})
	}
}

func TestParseAST_QueryTypes(t *testing.T) {
	tests := []struct {
		name     string
		json     string
		wantType QueryType
	}{
		{
			name:     "SELECT",
			json:     `{"table": "users", "type": "SELECT"}`,
			wantType: QueryTypeSelect,
		},
		{
			name:     "INSERT",
			json:     `{"table": "users", "type": "INSERT"}`,
			wantType: QueryTypeInsert,
		},
		{
			name:     "UPDATE",
			json:     `{"table": "users", "type": "UPDATE"}`,
			wantType: QueryTypeUpdate,
		},
		{
			name:     "DELETE",
			json:     `{"table": "users", "type": "DELETE"}`,
			wantType: QueryTypeDelete,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			ast, err := ParseAST([]byte(tt.json))
			if err != nil {
				t.Fatalf("ParseAST() error = %v", err)
			}

			if ast.Type != tt.wantType {
				t.Errorf("Type = %v, want %v", ast.Type, tt.wantType)
			}
		})
	}
}

// =============================================================================
// QueryAST Methods Tests
// =============================================================================

func TestQueryAST_HasConditions(t *testing.T) {
	tests := []struct {
		name string
		ast  *QueryAST
		want bool
	}{
		{
			name: "no conditions",
			ast:  &QueryAST{Table: "users", Type: QueryTypeSelect},
			want: false,
		},
		{
			name: "with conditions",
			ast: &QueryAST{
				Table:      "users",
				Type:       QueryTypeSelect,
				Conditions: &ConditionNode{Type: "condition", Field: "id", Op: "="},
			},
			want: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := tt.ast.HasConditions(); got != tt.want {
				t.Errorf("HasConditions() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestQueryAST_HasOrder(t *testing.T) {
	tests := []struct {
		name string
		ast  *QueryAST
		want bool
	}{
		{
			name: "no order",
			ast:  &QueryAST{Table: "users", Type: QueryTypeSelect},
			want: false,
		},
		{
			name: "with order",
			ast: &QueryAST{
				Table: "users",
				Type:  QueryTypeSelect,
				Order: []OrderNode{{Field: "name", Direction: "ASC"}},
			},
			want: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := tt.ast.HasOrder(); got != tt.want {
				t.Errorf("HasOrder() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestQueryAST_HasLimit(t *testing.T) {
	tests := []struct {
		name string
		ast  *QueryAST
		want bool
	}{
		{
			name: "no limit",
			ast:  &QueryAST{Table: "users", Type: QueryTypeSelect},
			want: false,
		},
		{
			name: "with limit",
			ast: &QueryAST{
				Table: "users",
				Type:  QueryTypeSelect,
				Limit: intPtr(10),
			},
			want: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := tt.ast.HasLimit(); got != tt.want {
				t.Errorf("HasLimit() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestQueryAST_IsRawQuery(t *testing.T) {
	tests := []struct {
		name string
		ast  *QueryAST
		want bool
	}{
		{
			name: "not raw",
			ast:  &QueryAST{Table: "users", Type: QueryTypeSelect},
			want: false,
		},
		{
			name: "with raw SQL",
			ast: &QueryAST{
				Table:  "users",
				Type:   QueryTypeSelect,
				RawSQL: "SELECT * FROM users WHERE complex_func()",
			},
			want: true,
		},
		{
			name: "raw type",
			ast: &QueryAST{
				Table: "users",
				Type:  QueryTypeRaw,
			},
			want: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := tt.ast.IsRawQuery(); got != tt.want {
				t.Errorf("IsRawQuery() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestQueryAST_ColumnList(t *testing.T) {
	tests := []struct {
		name string
		ast  *QueryAST
		want string
	}{
		{
			name: "no columns (select all)",
			ast:  &QueryAST{Table: "users", Type: QueryTypeSelect},
			want: "*",
		},
		{
			name: "single column",
			ast:  &QueryAST{Table: "users", Type: QueryTypeSelect, Columns: []string{"id"}},
			want: "id",
		},
		{
			name: "multiple columns",
			ast:  &QueryAST{Table: "users", Type: QueryTypeSelect, Columns: []string{"id", "name", "email"}},
			want: "id, name, email",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := tt.ast.ColumnList(); got != tt.want {
				t.Errorf("ColumnList() = %v, want %v", got, tt.want)
			}
		})
	}
}

// =============================================================================
// ConditionNode Methods Tests
// =============================================================================

func TestConditionNode_IsSimple(t *testing.T) {
	tests := []struct {
		name string
		node *ConditionNode
		want bool
	}{
		{
			name: "simple condition",
			node: &ConditionNode{Type: "condition", Field: "id", Op: "="},
			want: true,
		},
		{
			name: "logical condition",
			node: &ConditionNode{Type: "logical", Op: "AND"},
			want: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := tt.node.IsSimple(); got != tt.want {
				t.Errorf("IsSimple() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestConditionNode_IsLogical(t *testing.T) {
	tests := []struct {
		name string
		node *ConditionNode
		want bool
	}{
		{
			name: "logical condition",
			node: &ConditionNode{Type: "logical", Op: "AND"},
			want: true,
		},
		{
			name: "simple condition",
			node: &ConditionNode{Type: "condition", Field: "id", Op: "="},
			want: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := tt.node.IsLogical(); got != tt.want {
				t.Errorf("IsLogical() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestConditionNode_IsRaw(t *testing.T) {
	tests := []struct {
		name string
		node *ConditionNode
		want bool
	}{
		{
			name: "raw condition",
			node: &ConditionNode{Type: "raw", SQL: "custom_func() > 10"},
			want: true,
		},
		{
			name: "simple condition",
			node: &ConditionNode{Type: "condition", Field: "id", Op: "="},
			want: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := tt.node.IsRaw(); got != tt.want {
				t.Errorf("IsRaw() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestConditionNode_ConditionCount(t *testing.T) {
	tests := []struct {
		name string
		node *ConditionNode
		want int
	}{
		{
			name: "simple condition",
			node: &ConditionNode{Type: "condition", Field: "id", Op: "="},
			want: 1,
		},
		{
			name: "two conditions AND",
			node: &ConditionNode{
				Type: "logical",
				Op:   "AND",
				Conditions: []ConditionNode{
					{Type: "condition", Field: "a", Op: "="},
					{Type: "condition", Field: "b", Op: "="},
				},
			},
			want: 2,
		},
		{
			name: "nested conditions",
			node: &ConditionNode{
				Type: "logical",
				Op:   "AND",
				Conditions: []ConditionNode{
					{Type: "condition", Field: "a", Op: "="},
					{
						Type: "logical",
						Op:   "OR",
						Conditions: []ConditionNode{
							{Type: "condition", Field: "b", Op: "="},
							{Type: "condition", Field: "c", Op: "="},
						},
					},
				},
			},
			want: 3,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := tt.node.ConditionCount(); got != tt.want {
				t.Errorf("ConditionCount() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestConditionNode_Depth(t *testing.T) {
	tests := []struct {
		name string
		node *ConditionNode
		want int
	}{
		{
			name: "simple condition",
			node: &ConditionNode{Type: "condition", Field: "id", Op: "="},
			want: 1,
		},
		{
			name: "one level AND",
			node: &ConditionNode{
				Type: "logical",
				Op:   "AND",
				Conditions: []ConditionNode{
					{Type: "condition", Field: "a", Op: "="},
					{Type: "condition", Field: "b", Op: "="},
				},
			},
			want: 2,
		},
		{
			name: "two level nesting",
			node: &ConditionNode{
				Type: "logical",
				Op:   "AND",
				Conditions: []ConditionNode{
					{Type: "condition", Field: "a", Op: "="},
					{
						Type: "logical",
						Op:   "OR",
						Conditions: []ConditionNode{
							{Type: "condition", Field: "b", Op: "="},
						},
					},
				},
			},
			want: 3,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := tt.node.Depth(); got != tt.want {
				t.Errorf("Depth() = %v, want %v", got, tt.want)
			}
		})
	}
}

// =============================================================================
// String/Debug Tests
// =============================================================================

func TestQueryAST_String(t *testing.T) {
	ast := &QueryAST{
		Table:   "users",
		Type:    QueryTypeSelect,
		Columns: []string{"id", "name"},
		Conditions: &ConditionNode{
			Type:  "condition",
			Field: "age",
			Op:    ">",
			Value: 18,
		},
		Limit: intPtr(10),
	}

	str := ast.String()
	if str == "" {
		t.Error("String() returned empty string")
	}

	// Should contain key parts
	if !containsStr(str, "SELECT") {
		t.Error("String() should contain SELECT")
	}
	if !containsStr(str, "users") {
		t.Error("String() should contain table name")
	}
}

func TestConditionNode_String(t *testing.T) {
	tests := []struct {
		name string
		node *ConditionNode
	}{
		{
			name: "simple",
			node: &ConditionNode{Type: "condition", Field: "age", Op: ">", Value: 18},
		},
		{
			name: "logical",
			node: &ConditionNode{
				Type: "logical",
				Op:   "AND",
				Conditions: []ConditionNode{
					{Type: "condition", Field: "a", Op: "=", Value: 1},
				},
			},
		},
		{
			name: "raw",
			node: &ConditionNode{Type: "raw", SQL: "custom()"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			str := tt.node.String()
			if str == "" {
				t.Error("String() returned empty string")
			}
		})
	}
}

// =============================================================================
// Helper Functions
// =============================================================================

func intPtr(i int) *int {
	return &i
}

func containsStr(s, substr string) bool {
	return len(s) >= len(substr) && (s == substr || len(s) > 0 && containsStr(s[1:], substr) || s[:len(substr)] == substr)
}
