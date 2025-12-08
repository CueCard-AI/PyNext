package arrow

import (
	"testing"
	"time"

	"github.com/apache/arrow/go/v18/arrow"
	"github.com/jackc/pgx/v5/pgtype"
)

// =============================================================================
// Type Mapping Tests
// =============================================================================

func TestPgTypeToArrow_Int2(t *testing.T) {
	arrowType := pgTypeToArrow(pgtype.Int2OID)
	if arrowType != arrow.PrimitiveTypes.Int16 {
		t.Errorf("Expected Int16 for Int2OID, got %v", arrowType)
	}
}

func TestPgTypeToArrow_Int4(t *testing.T) {
	arrowType := pgTypeToArrow(pgtype.Int4OID)
	if arrowType != arrow.PrimitiveTypes.Int32 {
		t.Errorf("Expected Int32 for Int4OID, got %v", arrowType)
	}
}

func TestPgTypeToArrow_Int8(t *testing.T) {
	arrowType := pgTypeToArrow(pgtype.Int8OID)
	if arrowType != arrow.PrimitiveTypes.Int64 {
		t.Errorf("Expected Int64 for Int8OID, got %v", arrowType)
	}
}

func TestPgTypeToArrow_Float4(t *testing.T) {
	arrowType := pgTypeToArrow(pgtype.Float4OID)
	if arrowType != arrow.PrimitiveTypes.Float32 {
		t.Errorf("Expected Float32 for Float4OID, got %v", arrowType)
	}
}

func TestPgTypeToArrow_Float8(t *testing.T) {
	arrowType := pgTypeToArrow(pgtype.Float8OID)
	if arrowType != arrow.PrimitiveTypes.Float64 {
		t.Errorf("Expected Float64 for Float8OID, got %v", arrowType)
	}
}

func TestPgTypeToArrow_Bool(t *testing.T) {
	arrowType := pgTypeToArrow(pgtype.BoolOID)
	if arrowType != arrow.FixedWidthTypes.Boolean {
		t.Errorf("Expected Boolean for BoolOID, got %v", arrowType)
	}
}

func TestPgTypeToArrow_Text(t *testing.T) {
	arrowType := pgTypeToArrow(pgtype.TextOID)
	if arrowType != arrow.BinaryTypes.String {
		t.Errorf("Expected String for TextOID, got %v", arrowType)
	}
}

func TestPgTypeToArrow_Varchar(t *testing.T) {
	arrowType := pgTypeToArrow(pgtype.VarcharOID)
	if arrowType != arrow.BinaryTypes.String {
		t.Errorf("Expected String for VarcharOID, got %v", arrowType)
	}
}

func TestPgTypeToArrow_Bytea(t *testing.T) {
	arrowType := pgTypeToArrow(pgtype.ByteaOID)
	if arrowType != arrow.BinaryTypes.Binary {
		t.Errorf("Expected Binary for ByteaOID, got %v", arrowType)
	}
}

func TestPgTypeToArrow_Timestamp(t *testing.T) {
	arrowType := pgTypeToArrow(pgtype.TimestampOID)
	if arrowType != arrow.FixedWidthTypes.Timestamp_us {
		t.Errorf("Expected Timestamp_us for TimestampOID, got %v", arrowType)
	}
}

func TestPgTypeToArrow_Date(t *testing.T) {
	arrowType := pgTypeToArrow(pgtype.DateOID)
	if arrowType != arrow.FixedWidthTypes.Date32 {
		t.Errorf("Expected Date32 for DateOID, got %v", arrowType)
	}
}

func TestPgTypeToArrow_UUID(t *testing.T) {
	arrowType := pgTypeToArrow(pgtype.UUIDOID)
	fsb, ok := arrowType.(*arrow.FixedSizeBinaryType)
	if !ok {
		t.Errorf("Expected FixedSizeBinaryType for UUIDOID, got %T", arrowType)
	}
	if fsb.ByteWidth != 16 {
		t.Errorf("Expected ByteWidth=16 for UUID, got %d", fsb.ByteWidth)
	}
}

func TestPgTypeToArrow_JSON(t *testing.T) {
	arrowType := pgTypeToArrow(pgtype.JSONOID)
	if arrowType != arrow.BinaryTypes.String {
		t.Errorf("Expected String for JSONOID, got %v", arrowType)
	}
}

func TestPgTypeToArrow_JSONB(t *testing.T) {
	arrowType := pgTypeToArrow(pgtype.JSONBOID)
	if arrowType != arrow.BinaryTypes.String {
		t.Errorf("Expected String for JSONBOID, got %v", arrowType)
	}
}

func TestPgTypeToArrow_Numeric(t *testing.T) {
	arrowType := pgTypeToArrow(pgtype.NumericOID)
	// Numeric stored as string for precision
	if arrowType != arrow.BinaryTypes.String {
		t.Errorf("Expected String for NumericOID, got %v", arrowType)
	}
}

func TestPgTypeToArrow_Unknown(t *testing.T) {
	// Unknown OID should default to string
	arrowType := pgTypeToArrow(999999)
	if arrowType != arrow.BinaryTypes.String {
		t.Errorf("Expected String for unknown OID, got %v", arrowType)
	}
}

// =============================================================================
// Schema Builder Tests
// =============================================================================

func TestSchemaFromPgTypes(t *testing.T) {
	names := []string{"id", "name", "active"}
	oids := []uint32{pgtype.Int4OID, pgtype.TextOID, pgtype.BoolOID}

	schema := SchemaFromPgTypes(names, oids)

	if schema.NumFields() != 3 {
		t.Errorf("Expected 3 fields, got %d", schema.NumFields())
	}

	// Check field 0: id (int32)
	if schema.Field(0).Name != "id" {
		t.Errorf("Expected field 0 name='id', got '%s'", schema.Field(0).Name)
	}
	if schema.Field(0).Type != arrow.PrimitiveTypes.Int32 {
		t.Errorf("Expected field 0 type=Int32, got %v", schema.Field(0).Type)
	}

	// Check field 1: name (string)
	if schema.Field(1).Name != "name" {
		t.Errorf("Expected field 1 name='name', got '%s'", schema.Field(1).Name)
	}
	if schema.Field(1).Type != arrow.BinaryTypes.String {
		t.Errorf("Expected field 1 type=String, got %v", schema.Field(1).Type)
	}

	// Check field 2: active (bool)
	if schema.Field(2).Name != "active" {
		t.Errorf("Expected field 2 name='active', got '%s'", schema.Field(2).Name)
	}
	if schema.Field(2).Type != arrow.FixedWidthTypes.Boolean {
		t.Errorf("Expected field 2 type=Boolean, got %v", schema.Field(2).Type)
	}

	// All fields should be nullable
	for i := 0; i < schema.NumFields(); i++ {
		if !schema.Field(i).Nullable {
			t.Errorf("Expected field %d to be nullable", i)
		}
	}
}

func TestSchemaFromPgTypes_Empty(t *testing.T) {
	schema := SchemaFromPgTypes([]string{}, []uint32{})
	if schema.NumFields() != 0 {
		t.Errorf("Expected 0 fields, got %d", schema.NumFields())
	}
}

// =============================================================================
// Record Builder Tests
// =============================================================================

func TestNewRecordBuilder(t *testing.T) {
	schema := arrow.NewSchema(
		[]arrow.Field{
			{Name: "id", Type: arrow.PrimitiveTypes.Int32, Nullable: true},
			{Name: "name", Type: arrow.BinaryTypes.String, Nullable: true},
		},
		nil,
	)

	builder := NewRecordBuilder(schema)
	defer builder.Release()

	if builder.schema.NumFields() != 2 {
		t.Errorf("Expected 2 fields, got %d", builder.schema.NumFields())
	}
	if len(builder.builders) != 2 {
		t.Errorf("Expected 2 builders, got %d", len(builder.builders))
	}
	if builder.count != 0 {
		t.Errorf("Expected count=0, got %d", builder.count)
	}
}

func TestRecordBuilder_Append(t *testing.T) {
	schema := arrow.NewSchema(
		[]arrow.Field{
			{Name: "id", Type: arrow.PrimitiveTypes.Int32, Nullable: true},
			{Name: "name", Type: arrow.BinaryTypes.String, Nullable: true},
		},
		nil,
	)

	builder := NewRecordBuilder(schema)
	defer builder.Release()

	err := builder.Append([]interface{}{int32(1), "Alice"})
	if err != nil {
		t.Fatalf("Append failed: %v", err)
	}

	err = builder.Append([]interface{}{int32(2), "Bob"})
	if err != nil {
		t.Fatalf("Append failed: %v", err)
	}

	if builder.count != 2 {
		t.Errorf("Expected count=2, got %d", builder.count)
	}
}

func TestRecordBuilder_AppendWrongColumnCount(t *testing.T) {
	schema := arrow.NewSchema(
		[]arrow.Field{
			{Name: "id", Type: arrow.PrimitiveTypes.Int32, Nullable: true},
			{Name: "name", Type: arrow.BinaryTypes.String, Nullable: true},
		},
		nil,
	)

	builder := NewRecordBuilder(schema)
	defer builder.Release()

	// Too few values
	err := builder.Append([]interface{}{int32(1)})
	if err == nil {
		t.Error("Expected error for wrong column count")
	}

	// Too many values
	err = builder.Append([]interface{}{int32(1), "Alice", "extra"})
	if err == nil {
		t.Error("Expected error for wrong column count")
	}
}

func TestRecordBuilder_AppendNull(t *testing.T) {
	schema := arrow.NewSchema(
		[]arrow.Field{
			{Name: "id", Type: arrow.PrimitiveTypes.Int32, Nullable: true},
			{Name: "name", Type: arrow.BinaryTypes.String, Nullable: true},
		},
		nil,
	)

	builder := NewRecordBuilder(schema)
	defer builder.Release()

	// Null value should be handled
	err := builder.Append([]interface{}{int32(1), nil})
	if err != nil {
		t.Fatalf("Append with nil failed: %v", err)
	}

	if builder.count != 1 {
		t.Errorf("Expected count=1, got %d", builder.count)
	}
}

func TestRecordBuilder_Build(t *testing.T) {
	schema := arrow.NewSchema(
		[]arrow.Field{
			{Name: "id", Type: arrow.PrimitiveTypes.Int32, Nullable: true},
			{Name: "name", Type: arrow.BinaryTypes.String, Nullable: true},
		},
		nil,
	)

	builder := NewRecordBuilder(schema)

	_ = builder.Append([]interface{}{int32(1), "Alice"})
	_ = builder.Append([]interface{}{int32(2), "Bob"})

	record := builder.Build()
	defer record.Release()

	if record.NumRows() != 2 {
		t.Errorf("Expected 2 rows, got %d", record.NumRows())
	}
	if record.NumCols() != 2 {
		t.Errorf("Expected 2 columns, got %d", record.NumCols())
	}
}

// =============================================================================
// Value Appending Tests
// =============================================================================

func TestAppendInt16(t *testing.T) {
	schema := arrow.NewSchema(
		[]arrow.Field{{Name: "val", Type: arrow.PrimitiveTypes.Int16, Nullable: true}},
		nil,
	)
	builder := NewRecordBuilder(schema)
	defer builder.Release()

	// int16
	_ = builder.Append([]interface{}{int16(100)})
	// int32 should convert
	_ = builder.Append([]interface{}{int32(200)})
	// int should convert
	_ = builder.Append([]interface{}{int(300)})

	if builder.count != 3 {
		t.Errorf("Expected count=3, got %d", builder.count)
	}
}

func TestAppendInt32(t *testing.T) {
	schema := arrow.NewSchema(
		[]arrow.Field{{Name: "val", Type: arrow.PrimitiveTypes.Int32, Nullable: true}},
		nil,
	)
	builder := NewRecordBuilder(schema)
	defer builder.Release()

	_ = builder.Append([]interface{}{int32(100)})
	_ = builder.Append([]interface{}{int16(200)})
	_ = builder.Append([]interface{}{int64(300)})
	_ = builder.Append([]interface{}{int(400)})

	if builder.count != 4 {
		t.Errorf("Expected count=4, got %d", builder.count)
	}
}

func TestAppendInt64(t *testing.T) {
	schema := arrow.NewSchema(
		[]arrow.Field{{Name: "val", Type: arrow.PrimitiveTypes.Int64, Nullable: true}},
		nil,
	)
	builder := NewRecordBuilder(schema)
	defer builder.Release()

	_ = builder.Append([]interface{}{int64(100)})
	_ = builder.Append([]interface{}{int32(200)})
	_ = builder.Append([]interface{}{int(300)})

	if builder.count != 3 {
		t.Errorf("Expected count=3, got %d", builder.count)
	}
}

func TestAppendFloat32(t *testing.T) {
	schema := arrow.NewSchema(
		[]arrow.Field{{Name: "val", Type: arrow.PrimitiveTypes.Float32, Nullable: true}},
		nil,
	)
	builder := NewRecordBuilder(schema)
	defer builder.Release()

	_ = builder.Append([]interface{}{float32(1.5)})
	_ = builder.Append([]interface{}{float64(2.5)})

	if builder.count != 2 {
		t.Errorf("Expected count=2, got %d", builder.count)
	}
}

func TestAppendFloat64(t *testing.T) {
	schema := arrow.NewSchema(
		[]arrow.Field{{Name: "val", Type: arrow.PrimitiveTypes.Float64, Nullable: true}},
		nil,
	)
	builder := NewRecordBuilder(schema)
	defer builder.Release()

	_ = builder.Append([]interface{}{float64(1.5)})
	_ = builder.Append([]interface{}{float32(2.5)})

	if builder.count != 2 {
		t.Errorf("Expected count=2, got %d", builder.count)
	}
}

func TestAppendBool(t *testing.T) {
	schema := arrow.NewSchema(
		[]arrow.Field{{Name: "val", Type: arrow.FixedWidthTypes.Boolean, Nullable: true}},
		nil,
	)
	builder := NewRecordBuilder(schema)
	defer builder.Release()

	_ = builder.Append([]interface{}{true})
	_ = builder.Append([]interface{}{false})

	if builder.count != 2 {
		t.Errorf("Expected count=2, got %d", builder.count)
	}
}

func TestAppendString(t *testing.T) {
	schema := arrow.NewSchema(
		[]arrow.Field{{Name: "val", Type: arrow.BinaryTypes.String, Nullable: true}},
		nil,
	)
	builder := NewRecordBuilder(schema)
	defer builder.Release()

	_ = builder.Append([]interface{}{"hello"})
	_ = builder.Append([]interface{}{[]byte("world")})
	_ = builder.Append([]interface{}{12345}) // Should convert to string

	if builder.count != 3 {
		t.Errorf("Expected count=3, got %d", builder.count)
	}
}

func TestAppendBinary(t *testing.T) {
	schema := arrow.NewSchema(
		[]arrow.Field{{Name: "val", Type: arrow.BinaryTypes.Binary, Nullable: true}},
		nil,
	)
	builder := NewRecordBuilder(schema)
	defer builder.Release()

	_ = builder.Append([]interface{}{[]byte{1, 2, 3}})
	_ = builder.Append([]interface{}{"string"})

	if builder.count != 2 {
		t.Errorf("Expected count=2, got %d", builder.count)
	}
}

func TestAppendTimestamp(t *testing.T) {
	schema := arrow.NewSchema(
		[]arrow.Field{{Name: "val", Type: arrow.FixedWidthTypes.Timestamp_us, Nullable: true}},
		nil,
	)
	builder := NewRecordBuilder(schema)
	defer builder.Release()

	now := time.Now()
	_ = builder.Append([]interface{}{now})

	if builder.count != 1 {
		t.Errorf("Expected count=1, got %d", builder.count)
	}
}

func TestAppendDate32(t *testing.T) {
	schema := arrow.NewSchema(
		[]arrow.Field{{Name: "val", Type: arrow.FixedWidthTypes.Date32, Nullable: true}},
		nil,
	)
	builder := NewRecordBuilder(schema)
	defer builder.Release()

	date := time.Date(2024, 1, 15, 0, 0, 0, 0, time.UTC)
	_ = builder.Append([]interface{}{date})

	if builder.count != 1 {
		t.Errorf("Expected count=1, got %d", builder.count)
	}
}

// =============================================================================
// IPC Serialization Tests
// =============================================================================

func TestSerializeIPC(t *testing.T) {
	schema := arrow.NewSchema(
		[]arrow.Field{
			{Name: "id", Type: arrow.PrimitiveTypes.Int32, Nullable: true},
			{Name: "name", Type: arrow.BinaryTypes.String, Nullable: true},
		},
		nil,
	)

	builder := NewRecordBuilder(schema)
	_ = builder.Append([]interface{}{int32(1), "Alice"})
	_ = builder.Append([]interface{}{int32(2), "Bob"})

	record := builder.Build()
	defer record.Release()

	data, err := SerializeIPC(record)
	if err != nil {
		t.Fatalf("SerializeIPC failed: %v", err)
	}

	if len(data) == 0 {
		t.Error("Expected non-empty IPC data")
	}
}

func TestDeserializeIPC(t *testing.T) {
	schema := arrow.NewSchema(
		[]arrow.Field{
			{Name: "id", Type: arrow.PrimitiveTypes.Int32, Nullable: true},
			{Name: "name", Type: arrow.BinaryTypes.String, Nullable: true},
		},
		nil,
	)

	builder := NewRecordBuilder(schema)
	_ = builder.Append([]interface{}{int32(1), "Alice"})
	_ = builder.Append([]interface{}{int32(2), "Bob"})

	original := builder.Build()
	defer original.Release()

	// Serialize
	data, err := SerializeIPC(original)
	if err != nil {
		t.Fatalf("SerializeIPC failed: %v", err)
	}

	// Deserialize
	records, err := DeserializeIPC(data)
	if err != nil {
		t.Fatalf("DeserializeIPC failed: %v", err)
	}

	if len(records) != 1 {
		t.Errorf("Expected 1 record, got %d", len(records))
	}

	record := records[0]
	defer record.Release()

	if record.NumRows() != 2 {
		t.Errorf("Expected 2 rows, got %d", record.NumRows())
	}
	if record.NumCols() != 2 {
		t.Errorf("Expected 2 columns, got %d", record.NumCols())
	}
}

func TestDeserializeIPC_InvalidData(t *testing.T) {
	_, err := DeserializeIPC([]byte("invalid data"))
	if err == nil {
		t.Error("Expected error for invalid IPC data")
	}
}

// =============================================================================
// Edge Cases
// =============================================================================

func TestRecordBuilder_EmptyBuild(t *testing.T) {
	schema := arrow.NewSchema(
		[]arrow.Field{{Name: "id", Type: arrow.PrimitiveTypes.Int32, Nullable: true}},
		nil,
	)

	builder := NewRecordBuilder(schema)
	record := builder.Build()
	defer record.Release()

	if record.NumRows() != 0 {
		t.Errorf("Expected 0 rows, got %d", record.NumRows())
	}
}

func TestAppend_TypeMismatch(t *testing.T) {
	schema := arrow.NewSchema(
		[]arrow.Field{{Name: "val", Type: arrow.FixedWidthTypes.Boolean, Nullable: true}},
		nil,
	)
	builder := NewRecordBuilder(schema)
	defer builder.Release()

	// String is not convertible to bool
	err := builder.Append([]interface{}{"not a bool"})
	if err == nil {
		t.Error("Expected error for type mismatch")
	}
}

