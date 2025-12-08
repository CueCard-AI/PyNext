/*
Package arrow provides Apache Arrow integration for the Go bridge.

This package converts PostgreSQL query results to Arrow format for
zero-copy transfer to Python. Arrow provides:
  - Columnar memory layout (cache-friendly)
  - Zero-copy sharing between languages
  - Efficient serialization (IPC format)

Type Mapping (PostgreSQL -> Arrow):
  - INTEGER/INT4     -> INT32
  - BIGINT/INT8      -> INT64
  - SMALLINT/INT2    -> INT16
  - REAL/FLOAT4      -> FLOAT32
  - DOUBLE/FLOAT8    -> FLOAT64
  - BOOLEAN          -> BOOL
  - TEXT/VARCHAR     -> STRING
  - BYTEA            -> BINARY
  - TIMESTAMP        -> TIMESTAMP (microseconds)
  - DATE             -> DATE32
  - UUID             -> FIXED_SIZE_BINARY(16)
  - JSON/JSONB       -> STRING (serialized)
  - ARRAY            -> LIST
  - NULL             -> null in respective type

Usage:
    builder := arrow.NewRecordBuilder(schema)
    for _, row := range rows {
        builder.Append(row)
    }
    record := builder.Build()
    buffer := arrow.SerializeIPC(record)
*/
package arrow

import (
	"bytes"
	"fmt"
	"time"

	"github.com/apache/arrow/go/v18/arrow"
	"github.com/apache/arrow/go/v18/arrow/array"
	"github.com/apache/arrow/go/v18/arrow/ipc"
	"github.com/apache/arrow/go/v18/arrow/memory"
	"github.com/jackc/pgx/v5/pgtype"
)

// =============================================================================
// Schema Builder
// =============================================================================

// SchemaFromPgTypes creates an Arrow schema from PostgreSQL type OIDs.
func SchemaFromPgTypes(names []string, oids []uint32) *arrow.Schema {
	fields := make([]arrow.Field, len(names))
	for i, name := range names {
		fields[i] = arrow.Field{
			Name:     name,
			Type:     pgTypeToArrow(oids[i]),
			Nullable: true,
		}
	}
	return arrow.NewSchema(fields, nil)
}

// pgTypeToArrow maps PostgreSQL type OID to Arrow type.
func pgTypeToArrow(oid uint32) arrow.DataType {
	switch oid {
	// Integer types
	case pgtype.Int2OID:
		return arrow.PrimitiveTypes.Int16
	case pgtype.Int4OID:
		return arrow.PrimitiveTypes.Int32
	case pgtype.Int8OID:
		return arrow.PrimitiveTypes.Int64

	// Float types
	case pgtype.Float4OID:
		return arrow.PrimitiveTypes.Float32
	case pgtype.Float8OID:
		return arrow.PrimitiveTypes.Float64

	// Boolean
	case pgtype.BoolOID:
		return arrow.FixedWidthTypes.Boolean

	// String types
	case pgtype.TextOID, pgtype.VarcharOID, pgtype.BPCharOID, pgtype.NameOID:
		return arrow.BinaryTypes.String

	// Binary
	case pgtype.ByteaOID:
		return arrow.BinaryTypes.Binary

	// Date/Time types
	case pgtype.TimestampOID, pgtype.TimestamptzOID:
		return arrow.FixedWidthTypes.Timestamp_us
	case pgtype.DateOID:
		return arrow.FixedWidthTypes.Date32

	// UUID
	case pgtype.UUIDOID:
		return &arrow.FixedSizeBinaryType{ByteWidth: 16}

	// JSON types - store as string
	case pgtype.JSONOID, pgtype.JSONBOID:
		return arrow.BinaryTypes.String

	// Numeric - store as string for precision
	case pgtype.NumericOID:
		return arrow.BinaryTypes.String

	// Default to string for unknown types
	default:
		return arrow.BinaryTypes.String
	}
}

// =============================================================================
// Record Builder
// =============================================================================

// RecordBuilder builds Arrow RecordBatches from rows.
type RecordBuilder struct {
	schema   *arrow.Schema
	builders []array.Builder
	alloc    memory.Allocator
	count    int
}

// NewRecordBuilder creates a new record builder for the given schema.
func NewRecordBuilder(schema *arrow.Schema) *RecordBuilder {
	alloc := memory.NewGoAllocator()
	builders := make([]array.Builder, len(schema.Fields()))
	
	for i, field := range schema.Fields() {
		builders[i] = array.NewBuilder(alloc, field.Type)
	}

	return &RecordBuilder{
		schema:   schema,
		builders: builders,
		alloc:    alloc,
		count:    0,
	}
}

// Append adds a row to the builder.
func (b *RecordBuilder) Append(values []interface{}) error {
	if len(values) != len(b.builders) {
		return fmt.Errorf("expected %d values, got %d", len(b.builders), len(values))
	}

	for i, v := range values {
		if err := appendValue(b.builders[i], v); err != nil {
			return fmt.Errorf("column %d: %w", i, err)
		}
	}

	b.count++
	return nil
}

// Build creates the RecordBatch and releases builder resources.
func (b *RecordBuilder) Build() arrow.Record {
	arrays := make([]arrow.Array, len(b.builders))
	for i, builder := range b.builders {
		arrays[i] = builder.NewArray()
	}
	return array.NewRecord(b.schema, arrays, int64(b.count))
}

// Release releases all builder resources.
func (b *RecordBuilder) Release() {
	for _, builder := range b.builders {
		builder.Release()
	}
}

// =============================================================================
// Value Appending
// =============================================================================

// appendValue appends a single value to a builder.
func appendValue(builder array.Builder, v interface{}) error {
	if v == nil {
		builder.AppendNull()
		return nil
	}

	switch b := builder.(type) {
	case *array.Int16Builder:
		return appendInt16(b, v)
	case *array.Int32Builder:
		return appendInt32(b, v)
	case *array.Int64Builder:
		return appendInt64(b, v)
	case *array.Float32Builder:
		return appendFloat32(b, v)
	case *array.Float64Builder:
		return appendFloat64(b, v)
	case *array.BooleanBuilder:
		return appendBool(b, v)
	case *array.StringBuilder:
		return appendString(b, v)
	case *array.BinaryBuilder:
		return appendBinary(b, v)
	case *array.TimestampBuilder:
		return appendTimestamp(b, v)
	case *array.Date32Builder:
		return appendDate32(b, v)
	case *array.FixedSizeBinaryBuilder:
		return appendFixedBinary(b, v)
	default:
		// Fallback: convert to string
		if sb, ok := builder.(*array.StringBuilder); ok {
			sb.Append(fmt.Sprintf("%v", v))
			return nil
		}
		return fmt.Errorf("unsupported builder type: %T", builder)
	}
}

func appendInt16(b *array.Int16Builder, v interface{}) error {
	switch val := v.(type) {
	case int16:
		b.Append(val)
	case int32:
		b.Append(int16(val))
	case int64:
		b.Append(int16(val))
	case int:
		b.Append(int16(val))
	default:
		return fmt.Errorf("cannot convert %T to int16", v)
	}
	return nil
}

func appendInt32(b *array.Int32Builder, v interface{}) error {
	switch val := v.(type) {
	case int32:
		b.Append(val)
	case int16:
		b.Append(int32(val))
	case int64:
		b.Append(int32(val))
	case int:
		b.Append(int32(val))
	default:
		return fmt.Errorf("cannot convert %T to int32", v)
	}
	return nil
}

func appendInt64(b *array.Int64Builder, v interface{}) error {
	switch val := v.(type) {
	case int64:
		b.Append(val)
	case int32:
		b.Append(int64(val))
	case int16:
		b.Append(int64(val))
	case int:
		b.Append(int64(val))
	default:
		return fmt.Errorf("cannot convert %T to int64", v)
	}
	return nil
}

func appendFloat32(b *array.Float32Builder, v interface{}) error {
	switch val := v.(type) {
	case float32:
		b.Append(val)
	case float64:
		b.Append(float32(val))
	default:
		return fmt.Errorf("cannot convert %T to float32", v)
	}
	return nil
}

func appendFloat64(b *array.Float64Builder, v interface{}) error {
	switch val := v.(type) {
	case float64:
		b.Append(val)
	case float32:
		b.Append(float64(val))
	default:
		return fmt.Errorf("cannot convert %T to float64", v)
	}
	return nil
}

func appendBool(b *array.BooleanBuilder, v interface{}) error {
	switch val := v.(type) {
	case bool:
		b.Append(val)
	default:
		return fmt.Errorf("cannot convert %T to bool", v)
	}
	return nil
}

func appendString(b *array.StringBuilder, v interface{}) error {
	switch val := v.(type) {
	case string:
		b.Append(val)
	case []byte:
		b.Append(string(val))
	default:
		// Convert anything to string
		b.Append(fmt.Sprintf("%v", v))
	}
	return nil
}

func appendBinary(b *array.BinaryBuilder, v interface{}) error {
	switch val := v.(type) {
	case []byte:
		b.Append(val)
	case string:
		b.Append([]byte(val))
	default:
		return fmt.Errorf("cannot convert %T to binary", v)
	}
	return nil
}

func appendTimestamp(b *array.TimestampBuilder, v interface{}) error {
	switch val := v.(type) {
	case time.Time:
		// Convert to microseconds since epoch
		b.Append(arrow.Timestamp(val.UnixMicro()))
	default:
		return fmt.Errorf("cannot convert %T to timestamp", v)
	}
	return nil
}

func appendDate32(b *array.Date32Builder, v interface{}) error {
	switch val := v.(type) {
	case time.Time:
		// Convert to days since epoch
		days := int32(val.Unix() / 86400)
		b.Append(arrow.Date32(days))
	default:
		return fmt.Errorf("cannot convert %T to date", v)
	}
	return nil
}

func appendFixedBinary(b *array.FixedSizeBinaryBuilder, v interface{}) error {
	switch val := v.(type) {
	case []byte:
		b.Append(val)
	case [16]byte:
		b.Append(val[:])
	default:
		return fmt.Errorf("cannot convert %T to fixed binary", v)
	}
	return nil
}

// =============================================================================
// IPC Serialization
// =============================================================================

// SerializeIPC serializes a RecordBatch to Arrow IPC stream format.
// Stream format doesn't require seeking and is simpler.
func SerializeIPC(record arrow.Record) ([]byte, error) {
	var buf bytes.Buffer
	
	writer := ipc.NewWriter(&buf, ipc.WithSchema(record.Schema()))
	if err := writer.Write(record); err != nil {
		return nil, fmt.Errorf("failed to write record: %w", err)
	}
	if err := writer.Close(); err != nil {
		return nil, fmt.Errorf("failed to close writer: %w", err)
	}

	return buf.Bytes(), nil
}

// DeserializeIPC deserializes Arrow IPC format to RecordBatches.
func DeserializeIPC(data []byte) ([]arrow.Record, error) {
	reader, err := ipc.NewReader(bytes.NewReader(data))
	if err != nil {
		return nil, fmt.Errorf("failed to create reader: %w", err)
	}
	defer reader.Release()

	var records []arrow.Record
	for reader.Next() {
		record := reader.Record()
		record.Retain() // Keep reference after reader closes
		records = append(records, record)
	}

	if err := reader.Err(); err != nil {
		return nil, fmt.Errorf("error reading records: %w", err)
	}

	return records, nil
}

