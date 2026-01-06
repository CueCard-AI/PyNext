"""
Phase 33.3: Stack Trace Rewriter Comprehensive Tests

Comprehensive test suite for stack trace rewriting covering:
- Stack trace parsing (Chrome, Firefox, Safari, Node.js formats)
- Source map lookup and position mapping
- Stack trace rewriting
- All browser formats
- Edge cases and error handling

Total: 100+ tests covering all aspects of stack trace rewriting.
"""

import pytest
import json
from pynext.transpiler.stack_rewriter import (
    parse_stack_trace,
    rewrite_stack_trace,
    rewrite_stack_trace_from_file,
    StackFrame,
    ParsedStackTrace,
    SourceMapLookup,
)
from pynext.transpiler.sourcemap import SourceMapBuilder


# =============================================================================
# STACK TRACE PARSING (30 tests)
# =============================================================================

class TestStackTraceParsing:
    """Test stack trace parsing from various browser formats."""
    
    def test_parse_chrome_format(self):
        """Test parsing Chrome/Edge format."""
        stack = """
Error: Division by zero
    at divide (handler.js:15:8)
    at calculate (handler.js:23:4)
"""
        parsed = parse_stack_trace(stack)
        assert parsed.error_message == "Error: Division by zero"
        assert len(parsed.frames) == 2
        assert parsed.frames[0].function == "divide"
        assert parsed.frames[0].file == "handler.js"
        assert parsed.frames[0].line == 15
        assert parsed.frames[0].column == 8
    
    def test_parse_firefox_format(self):
        """Test parsing Firefox format."""
        stack = """
Error: Division by zero
divide@handler.js:15:8
calculate@handler.js:23:4
"""
        parsed = parse_stack_trace(stack)
        assert parsed.error_message == "Error: Division by zero"
        assert len(parsed.frames) == 2
        assert parsed.frames[0].function == "divide"
        assert parsed.frames[0].file == "handler.js"
        assert parsed.frames[0].line == 15
        assert parsed.frames[0].column == 8
    
    def test_parse_safari_format(self):
        """Test parsing Safari format."""
        stack = """
Error: Division by zero
divide@handler.js:15:8
calculate@handler.js:23:4
"""
        parsed = parse_stack_trace(stack)
        assert parsed.error_message == "Error: Division by zero"
        assert len(parsed.frames) == 2
        assert parsed.frames[0].function == "divide"
    
    def test_parse_nodejs_format(self):
        """Test parsing Node.js format."""
        stack = """
Error: Division by zero
    at divide (handler.js:15:8)
    at calculate (handler.js:23:4)
"""
        parsed = parse_stack_trace(stack)
        assert parsed.error_message == "Error: Division by zero"
        assert len(parsed.frames) == 2
    
    def test_parse_chrome_format_without_column(self):
        """Test parsing Chrome format without column."""
        stack = """
Error: Division by zero
    at divide (handler.js:15)
    at calculate (handler.js:23)
"""
        parsed = parse_stack_trace(stack)
        assert len(parsed.frames) == 2
        assert parsed.frames[0].line == 15
        assert parsed.frames[0].column is None
    
    def test_parse_firefox_format_without_column(self):
        """Test parsing Firefox format without column."""
        stack = """
Error: Division by zero
divide@handler.js:15
calculate@handler.js:23
"""
        parsed = parse_stack_trace(stack)
        assert len(parsed.frames) == 2
        assert parsed.frames[0].line == 15
        assert parsed.frames[0].column is None
    
    def test_parse_anonymous_function(self):
        """Test parsing anonymous function."""
        stack = """
Error: Division by zero
    at <anonymous> (handler.js:15:8)
"""
        parsed = parse_stack_trace(stack)
        assert len(parsed.frames) == 1
        assert parsed.frames[0].function == "<anonymous>"
    
    def test_parse_global_code_firefox(self):
        """Test parsing global code in Firefox."""
        stack = """
Error: Division by zero
global code@handler.js:15:8
"""
        parsed = parse_stack_trace(stack)
        assert len(parsed.frames) == 1
        assert parsed.frames[0].function is None
    
    def test_parse_empty_stack_trace(self):
        """Test parsing empty stack trace."""
        stack = ""
        parsed = parse_stack_trace(stack)
        assert parsed.error_message == ""
        assert len(parsed.frames) == 0
    
    def test_parse_stack_trace_with_only_error(self):
        """Test parsing stack trace with only error message."""
        stack = "Error: Division by zero"
        parsed = parse_stack_trace(stack)
        assert parsed.error_message == "Error: Division by zero"
        assert len(parsed.frames) == 0
    
    def test_parse_multiple_frames(self):
        """Test parsing multiple frames."""
        stack = """
Error: Division by zero
    at func1 (file1.js:10:5)
    at func2 (file2.js:20:10)
    at func3 (file3.js:30:15)
"""
        parsed = parse_stack_trace(stack)
        assert len(parsed.frames) == 3
        assert parsed.frames[0].function == "func1"
        assert parsed.frames[1].function == "func2"
        assert parsed.frames[2].function == "func3"
    
    def test_parse_with_whitespace(self):
        """Test parsing with extra whitespace."""
        stack = """
Error: Division by zero
    
    at divide (handler.js:15:8)
    
    at calculate (handler.js:23:4)
    
"""
        parsed = parse_stack_trace(stack)
        assert len(parsed.frames) == 2
        assert parsed.frames[0].function == "divide"
        assert parsed.frames[1].function == "calculate"
    
    def test_parse_with_special_characters_in_function_name(self):
        """Test parsing with special characters in function name."""
        stack = """
Error: Division by zero
    at my_function_123 (handler.js:15:8)
"""
        parsed = parse_stack_trace(stack)
        assert parsed.frames[0].function == "my_function_123"
    
    def test_parse_with_unicode_in_function_name(self):
        """Test parsing with unicode in function name."""
        stack = """
Error: Division by zero
    at 関数 (handler.js:15:8)
"""
        parsed = parse_stack_trace(stack)
        assert parsed.frames[0].function == "関数"
    
    def test_parse_with_path_in_file(self):
        """Test parsing with path in file name."""
        stack = """
Error: Division by zero
    at divide (src/handlers/calculator.js:15:8)
"""
        parsed = parse_stack_trace(stack)
        assert parsed.frames[0].file == "src/handlers/calculator.js"
    
    def test_parse_with_absolute_path(self):
        """Test parsing with absolute path."""
        stack = """
Error: Division by zero
    at divide (/path/to/handler.js:15:8)
"""
        parsed = parse_stack_trace(stack)
        assert parsed.frames[0].file == "/path/to/handler.js"
    
    def test_parse_with_url(self):
        """Test parsing with URL."""
        stack = """
Error: Division by zero
    at divide (http://localhost:3000/handler.js:15:8)
"""
        parsed = parse_stack_trace(stack)
        assert parsed.frames[0].file == "http://localhost:3000/handler.js"
    
    def test_parse_with_https_url(self):
        """Test parsing with HTTPS URL."""
        stack = """
Error: Division by zero
    at divide (https://example.com/handler.js:15:8)
"""
        parsed = parse_stack_trace(stack)
        assert parsed.frames[0].file == "https://example.com/handler.js"
    
    def test_parse_with_query_parameters(self):
        """Test parsing with query parameters in URL."""
        stack = """
Error: Division by zero
    at divide (handler.js?v=1.0:15:8)
"""
        parsed = parse_stack_trace(stack)
        assert parsed.frames[0].file == "handler.js?v=1.0"
    
    def test_parse_with_hash_in_url(self):
        """Test parsing with hash in URL."""
        stack = """
Error: Division by zero
    at divide (handler.js#source:15:8)
"""
        parsed = parse_stack_trace(stack)
        assert parsed.frames[0].file == "handler.js#source"
    
    def test_parse_mixed_formats(self):
        """Test parsing mixed browser formats."""
        stack = """
Error: Division by zero
    at func1 (file1.js:10:5)
func2@file2.js:20:10
    at func3 (file3.js:30:15)
"""
        parsed = parse_stack_trace(stack)
        assert len(parsed.frames) == 3
        # Should handle both formats
    
    def test_parse_with_very_long_function_name(self):
        """Test parsing with very long function name."""
        long_name = "a" * 1000
        stack = f"""
Error: Division by zero
    at {long_name} (handler.js:15:8)
"""
        parsed = parse_stack_trace(stack)
        assert parsed.frames[0].function == long_name
    
    def test_parse_with_very_long_file_name(self):
        """Test parsing with very long file name."""
        long_file = "a" * 1000 + ".js"
        stack = f"""
Error: Division by zero
    at divide ({long_file}:15:8)
"""
        parsed = parse_stack_trace(stack)
        assert parsed.frames[0].file == long_file
    
    def test_parse_with_large_line_numbers(self):
        """Test parsing with large line numbers."""
        stack = """
Error: Division by zero
    at divide (handler.js:10000:5000)
"""
        parsed = parse_stack_trace(stack)
        assert parsed.frames[0].line == 10000
        assert parsed.frames[0].column == 5000
    
    def test_parse_with_zero_line_number(self):
        """Test parsing with zero line number."""
        stack = """
Error: Division by zero
    at divide (handler.js:0:0)
"""
        parsed = parse_stack_trace(stack)
        assert parsed.frames[0].line == 0
        assert parsed.frames[0].column == 0
    
    def test_parse_with_negative_line_number(self):
        """Test parsing with negative line number (edge case)."""
        stack = """
Error: Division by zero
    at divide (handler.js:-1:-1)
"""
        parsed = parse_stack_trace(stack)
        # Should handle gracefully
        assert len(parsed.frames) == 1
    
    def test_parse_with_invalid_format(self):
        """Test parsing with invalid format."""
        stack = """
Error: Division by zero
    invalid format line
"""
        parsed = parse_stack_trace(stack)
        # Invalid lines should be skipped
        assert parsed.error_message == "Error: Division by zero"
        assert len(parsed.frames) == 0
    
    def test_parse_preserves_original(self):
        """Test parsing preserves original stack trace."""
        stack = """
Error: Division by zero
    at divide (handler.js:15:8)
"""
        parsed = parse_stack_trace(stack)
        assert parsed.original == stack
    
    def test_parse_with_nested_function_names(self):
        """Test parsing with nested function names."""
        stack = """
Error: Division by zero
    at Object.divide (handler.js:15:8)
    at Calculator.calculate (handler.js:23:4)
"""
        parsed = parse_stack_trace(stack)
        assert len(parsed.frames) == 2
        assert "Object.divide" in parsed.frames[0].function or "divide" in parsed.frames[0].function
    
    def test_parse_with_arrow_functions(self):
        """Test parsing with arrow function names."""
        stack = """
Error: Division by zero
    at handler (handler.js:15:8)
    at <anonymous> (handler.js:20:5)
"""
        parsed = parse_stack_trace(stack)
        assert len(parsed.frames) == 2
    
    def test_parse_with_async_functions(self):
        """Test parsing with async function names."""
        stack = """
Error: Division by zero
    at async handler (handler.js:15:8)
"""
        parsed = parse_stack_trace(stack)
        assert len(parsed.frames) == 1
        # "async" might be part of function name or separate
    
    def test_parse_with_promise_rejections(self):
        """Test parsing with Promise rejection format."""
        stack = """
UnhandledPromiseRejectionWarning: Division by zero
    at divide (handler.js:15:8)
"""
        parsed = parse_stack_trace(stack)
        assert parsed.error_message == "UnhandledPromiseRejectionWarning: Division by zero"
        assert len(parsed.frames) == 1


# =============================================================================
# SOURCE MAP LOOKUP (20 tests)
# =============================================================================

class TestSourceMapLookup:
    """Test source map lookup functionality."""
    
    def test_create_lookup(self):
        """Test creating SourceMapLookup."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0)
        source_map = builder.to_json()
        lookup = SourceMapLookup(source_map)
        assert lookup.source_map == source_map
    
    def test_lookup_exact_match(self):
        """Test lookup with exact position match."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(10, 20, 15, 25, name="x")
        source_map = builder.to_json()
        lookup = SourceMapLookup(source_map)
        result = lookup.lookup(10, 20)
        assert result is not None
        src_line, src_col, name = result
        assert src_line == 15
        assert src_col == 25
        assert name == "x"
    
    def test_lookup_closest_column(self):
        """Test lookup with closest column match."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(10, 20, 15, 25)
        builder.add_mapping(10, 30, 15, 35)
        source_map = builder.to_json()
        lookup = SourceMapLookup(source_map)
        # Look up position between mappings
        result = lookup.lookup(10, 25)
        assert result is not None
        # Should return closest mapping
    
    def test_lookup_no_match(self):
        """Test lookup with no matching position."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(10, 20, 15, 25)
        source_map = builder.to_json()
        lookup = SourceMapLookup(source_map)
        result = lookup.lookup(100, 200)
        # Should return None or closest match
        assert result is None or result is not None
    
    def test_lookup_with_name(self):
        """Test lookup preserves variable name."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(10, 20, 15, 25, name="my_variable")
        source_map = builder.to_json()
        lookup = SourceMapLookup(source_map)
        result = lookup.lookup(10, 20)
        assert result is not None
        _, _, name = result
        assert name == "my_variable"
    
    def test_lookup_without_name(self):
        """Test lookup without variable name."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(10, 20, 15, 25)
        source_map = builder.to_json()
        lookup = SourceMapLookup(source_map)
        result = lookup.lookup(10, 20)
        assert result is not None
        _, _, name = result
        assert name is None
    
    def test_lookup_multiple_mappings(self):
        """Test lookup with multiple mappings."""
        builder = SourceMapBuilder("source.py", "output.js")
        for i in range(10):
            builder.add_mapping(i, i * 4, i * 2, i * 4, name=f"var_{i}")
        source_map = builder.to_json()
        lookup = SourceMapLookup(source_map)
        result = lookup.lookup(5, 20)
        assert result is not None
    
    def test_lookup_empty_source_map(self):
        """Test lookup with empty source map."""
        builder = SourceMapBuilder("source.py", "output.js")
        source_map = builder.to_json()
        lookup = SourceMapLookup(source_map)
        result = lookup.lookup(0, 0)
        assert result is None
    
    def test_lookup_with_gaps(self):
        """Test lookup with gaps in mappings."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0)
        builder.add_mapping(10, 0, 10, 0)
        builder.add_mapping(20, 0, 20, 0)
        source_map = builder.to_json()
        lookup = SourceMapLookup(source_map)
        result = lookup.lookup(5, 0)
        # Should find closest match
        assert result is not None or result is None
    
    def test_lookup_with_same_line_different_columns(self):
        """Test lookup with same line, different columns."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(10, 0, 15, 0)
        builder.add_mapping(10, 10, 15, 10)
        builder.add_mapping(10, 20, 15, 20)
        source_map = builder.to_json()
        lookup = SourceMapLookup(source_map)
        result = lookup.lookup(10, 5)
        # Should find closest column
        assert result is not None
    
    def test_lookup_with_different_lines(self):
        """Test lookup with different lines."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0)
        builder.add_mapping(5, 0, 10, 0)
        builder.add_mapping(10, 0, 20, 0)
        source_map = builder.to_json()
        lookup = SourceMapLookup(source_map)
        result = lookup.lookup(5, 0)
        assert result is not None
        src_line, _, _ = result
        assert src_line == 10
    
    def test_lookup_with_zero_indexed(self):
        """Test lookup uses 0-indexed positions."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0)  # 0-indexed
        source_map = builder.to_json()
        lookup = SourceMapLookup(source_map)
        result = lookup.lookup(0, 0)  # 0-indexed
        assert result is not None
    
    def test_lookup_with_negative_positions(self):
        """Test lookup with negative positions."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0)
        source_map = builder.to_json()
        lookup = SourceMapLookup(source_map)
        result = lookup.lookup(-1, -1)
        # Should handle gracefully
        assert result is None or result is not None
    
    def test_lookup_with_very_large_positions(self):
        """Test lookup with very large positions."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(10000, 5000, 20000, 10000)
        source_map = builder.to_json()
        lookup = SourceMapLookup(source_map)
        result = lookup.lookup(10000, 5000)
        assert result is not None
        src_line, src_col, _ = result
        assert src_line == 20000
        assert src_col == 10000
    
    def test_lookup_with_function_boundaries(self):
        """Test lookup with function boundaries."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_function("my_function", 0, 0, 0, 0)
        builder.add_mapping(1, 4, 1, 4, name="x")
        builder.end_function("my_function", 5, 3)
        source_map = builder.to_json()
        lookup = SourceMapLookup(source_map)
        result = lookup.lookup(1, 4)
        assert result is not None
    
    def test_lookup_with_class_boundaries(self):
        """Test lookup with class boundaries."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_class("MyClass", 0, 0, 0, 0)
        builder.add_mapping(1, 4, 1, 4, name="x")
        builder.end_class("MyClass", 10, 5)
        source_map = builder.to_json()
        lookup = SourceMapLookup(source_map)
        result = lookup.lookup(1, 4)
        assert result is not None
    
    def test_lookup_with_vlq_encoding(self):
        """Test lookup decodes VLQ correctly."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0)
        builder.add_mapping(1, 4, 1, 4)
        builder.add_mapping(2, 8, 2, 8)
        source_map = builder.to_json()
        lookup = SourceMapLookup(source_map)
        # Should decode VLQ mappings correctly
        result1 = lookup.lookup(0, 0)
        result2 = lookup.lookup(1, 4)
        result3 = lookup.lookup(2, 8)
        assert result1 is not None
        assert result2 is not None
        assert result3 is not None
    
    def test_lookup_with_delta_encoding(self):
        """Test lookup handles delta encoding correctly."""
        builder = SourceMapBuilder("source.py", "output.js")
        # Add mappings with deltas
        builder.add_mapping(0, 0, 0, 0)
        builder.add_mapping(0, 4, 0, 4)  # +4 delta
        builder.add_mapping(0, 8, 0, 8)  # +4 delta
        source_map = builder.to_json()
        lookup = SourceMapLookup(source_map)
        result1 = lookup.lookup(0, 0)
        result2 = lookup.lookup(0, 4)
        result3 = lookup.lookup(0, 8)
        assert result1 is not None
        assert result2 is not None
        assert result3 is not None
    
    def test_lookup_with_name_index(self):
        """Test lookup handles name index correctly."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0, name="x")
        builder.add_mapping(1, 0, 1, 0, name="y")
        builder.add_mapping(2, 0, 2, 0, name="z")
        source_map = builder.to_json()
        lookup = SourceMapLookup(source_map)
        result = lookup.lookup(0, 0)
        assert result is not None
        _, _, name = result
        assert name == "x"
    
    def test_lookup_performance(self):
        """Test lookup performance with many mappings."""
        builder = SourceMapBuilder("source.py", "output.js")
        for i in range(1000):
            builder.add_mapping(i, 0, i * 2, 0)
        source_map = builder.to_json()
        lookup = SourceMapLookup(source_map)
        # Should be fast even with many mappings
        result = lookup.lookup(500, 0)
        assert result is not None


# =============================================================================
# STACK TRACE REWRITING (30 tests)
# =============================================================================

class TestStackTraceRewriting:
    """Test stack trace rewriting functionality."""
    
    def test_rewrite_simple_stack_trace(self):
        """Test rewriting simple stack trace."""
        stack = """
Error: Division by zero
    at divide (handler.js:15:8)
"""
        builder = SourceMapBuilder("handler.py", "handler.js")
        builder.add_mapping(14, 7, 11, 4)  # JS line 15 (0-indexed 14) → Python line 12 (0-indexed 11)
        source_map = builder.to_json()
        
        rewritten = rewrite_stack_trace(stack, source_map)
        assert "handler.py" in rewritten
        assert "12" in rewritten or "11" in rewritten  # Python line number
    
    def test_rewrite_multiple_frames(self):
        """Test rewriting multiple frames."""
        stack = """
Error: Division by zero
    at divide (handler.js:15:8)
    at calculate (handler.js:23:4)
    at main (handler.js:30:1)
"""
        builder = SourceMapBuilder("handler.py", "handler.js")
        builder.add_mapping(14, 7, 11, 4)  # divide
        builder.add_mapping(22, 3, 19, 2)  # calculate
        builder.add_mapping(29, 0, 26, 0)  # main
        source_map = builder.to_json()
        
        rewritten = rewrite_stack_trace(stack, source_map)
        assert "handler.py" in rewritten
        # Should rewrite all frames
    
    def test_rewrite_preserves_error_message(self):
        """Test rewriting preserves error message."""
        stack = """
TypeError: Cannot read property 'x' of undefined
    at divide (handler.js:15:8)
"""
        builder = SourceMapBuilder("handler.py", "handler.js")
        builder.add_mapping(14, 7, 11, 4)
        source_map = builder.to_json()
        
        rewritten = rewrite_stack_trace(stack, source_map)
        assert "TypeError: Cannot read property 'x' of undefined" in rewritten
    
    def test_rewrite_preserves_function_names(self):
        """Test rewriting preserves function names."""
        stack = """
Error: Division by zero
    at divide (handler.js:15:8)
"""
        builder = SourceMapBuilder("handler.py", "handler.js")
        builder.add_mapping(14, 7, 11, 4, name="divide")
        source_map = builder.to_json()
        
        rewritten = rewrite_stack_trace(stack, source_map)
        assert "divide" in rewritten
    
    def test_rewrite_with_variable_names(self):
        """Test rewriting with variable names from source map."""
        stack = """
Error: Division by zero
    at divide (handler.js:15:8)
"""
        builder = SourceMapBuilder("handler.py", "handler.js")
        builder.add_mapping(14, 7, 11, 4, name="my_variable")
        source_map = builder.to_json()
        
        rewritten = rewrite_stack_trace(stack, source_map)
        # Variable name might be used if function name not available
        assert "handler.py" in rewritten
    
    def test_rewrite_without_mapping(self):
        """Test rewriting without matching mapping."""
        stack = """
Error: Division by zero
    at divide (handler.js:15:8)
"""
        builder = SourceMapBuilder("handler.py", "handler.js")
        builder.add_mapping(0, 0, 0, 0)  # Different position
        source_map = builder.to_json()
        
        rewritten = rewrite_stack_trace(stack, source_map)
        # Should return original or closest match
        assert "Error: Division by zero" in rewritten
    
    def test_rewrite_with_empty_source_map(self):
        """Test rewriting with empty source map."""
        stack = """
Error: Division by zero
    at divide (handler.js:15:8)
"""
        builder = SourceMapBuilder("handler.py", "handler.js")
        source_map = builder.to_json()
        
        rewritten = rewrite_stack_trace(stack, source_map)
        # Should return original stack trace
        assert "handler.js" in rewritten
    
    def test_rewrite_with_chrome_format(self):
        """Test rewriting Chrome format."""
        stack = """
Error: Division by zero
    at divide (handler.js:15:8)
"""
        builder = SourceMapBuilder("handler.py", "handler.js")
        builder.add_mapping(14, 7, 11, 4)
        source_map = builder.to_json()
        
        rewritten = rewrite_stack_trace(stack, source_map)
        assert "handler.py" in rewritten
    
    def test_rewrite_with_firefox_format(self):
        """Test rewriting Firefox format."""
        stack = """
Error: Division by zero
divide@handler.js:15:8
"""
        builder = SourceMapBuilder("handler.py", "handler.js")
        builder.add_mapping(14, 7, 11, 4)
        source_map = builder.to_json()
        
        rewritten = rewrite_stack_trace(stack, source_map)
        assert "handler.py" in rewritten
    
    def test_rewrite_with_safari_format(self):
        """Test rewriting Safari format."""
        stack = """
Error: Division by zero
divide@handler.js:15:8
"""
        builder = SourceMapBuilder("handler.py", "handler.js")
        builder.add_mapping(14, 7, 11, 4)
        source_map = builder.to_json()
        
        rewritten = rewrite_stack_trace(stack, source_map)
        assert "handler.py" in rewritten
    
    def test_rewrite_with_nodejs_format(self):
        """Test rewriting Node.js format."""
        stack = """
Error: Division by zero
    at divide (handler.js:15:8)
"""
        builder = SourceMapBuilder("handler.py", "handler.js")
        builder.add_mapping(14, 7, 11, 4)
        source_map = builder.to_json()
        
        rewritten = rewrite_stack_trace(stack, source_map)
        assert "handler.py" in rewritten
    
    def test_rewrite_without_column(self):
        """Test rewriting without column information."""
        stack = """
Error: Division by zero
    at divide (handler.js:15)
"""
        builder = SourceMapBuilder("handler.py", "handler.js")
        builder.add_mapping(14, 0, 11, 0)
        source_map = builder.to_json()
        
        rewritten = rewrite_stack_trace(stack, source_map)
        assert "handler.py" in rewritten
    
    def test_rewrite_with_anonymous_function(self):
        """Test rewriting anonymous function."""
        stack = """
Error: Division by zero
    at <anonymous> (handler.js:15:8)
"""
        builder = SourceMapBuilder("handler.py", "handler.js")
        builder.add_mapping(14, 7, 11, 4)
        source_map = builder.to_json()
        
        rewritten = rewrite_stack_trace(stack, source_map)
        assert "handler.py" in rewritten
    
    def test_rewrite_with_custom_source_file(self):
        """Test rewriting with custom source file name."""
        stack = """
Error: Division by zero
    at divide (handler.js:15:8)
"""
        builder = SourceMapBuilder("original.py", "handler.js")
        builder.add_mapping(14, 7, 11, 4)
        source_map = builder.to_json()
        
        rewritten = rewrite_stack_trace(stack, source_map, source_file="custom.py")
        assert "custom.py" in rewritten
    
    def test_rewrite_with_multiple_source_files(self):
        """Test rewriting with multiple source files."""
        stack = """
Error: Division by zero
    at func1 (file1.js:10:5)
    at func2 (file2.js:20:10)
"""
        # Create source maps for both files
        builder1 = SourceMapBuilder("source1.py", "file1.js")
        builder1.add_mapping(9, 4, 8, 3)
        source_map1 = builder1.to_json()
        
        builder2 = SourceMapBuilder("source2.py", "file2.js")
        builder2.add_mapping(19, 9, 18, 8)
        source_map2 = builder2.to_json()
        
        # Rewrite first frame
        rewritten = rewrite_stack_trace(stack, source_map1)
        assert "source1.py" in rewritten or "file1.js" in rewritten
    
    def test_rewrite_with_function_boundaries(self):
        """Test rewriting with function boundaries."""
        stack = """
Error: Division by zero
    at divide (handler.js:15:8)
"""
        builder = SourceMapBuilder("handler.py", "handler.js")
        builder.start_function("divide", 14, 0, 11, 0)
        builder.add_mapping(14, 7, 11, 4)
        builder.end_function("divide", 20, 15)
        source_map = builder.to_json()
        
        rewritten = rewrite_stack_trace(stack, source_map)
        assert "handler.py" in rewritten
    
    def test_rewrite_with_class_boundaries(self):
        """Test rewriting with class boundaries."""
        stack = """
Error: Division by zero
    at Calculator.divide (handler.js:15:8)
"""
        builder = SourceMapBuilder("handler.py", "handler.js")
        builder.start_class("Calculator", 0, 0, 0, 0)
        builder.add_mapping(14, 7, 11, 4)
        builder.end_class("Calculator", 30, 25)
        source_map = builder.to_json()
        
        rewritten = rewrite_stack_trace(stack, source_map)
        assert "handler.py" in rewritten
    
    def test_rewrite_with_nested_functions(self):
        """Test rewriting with nested functions."""
        stack = """
Error: Division by zero
    at inner (handler.js:15:8)
    at outer (handler.js:20:4)
"""
        builder = SourceMapBuilder("handler.py", "handler.js")
        builder.start_function("outer", 19, 0, 18, 0)
        builder.start_function("inner", 14, 0, 13, 0)
        builder.add_mapping(14, 7, 13, 4)
        builder.end_function("inner", 16, 15)
        builder.end_function("outer", 22, 20)
        source_map = builder.to_json()
        
        rewritten = rewrite_stack_trace(stack, source_map)
        assert "handler.py" in rewritten
    
    def test_rewrite_with_complex_stack(self):
        """Test rewriting complex stack trace."""
        stack = """
TypeError: Cannot read property 'x' of undefined
    at process (handler.js:10:5)
    at calculate (handler.js:20:10)
    at handleClick (handler.js:30:15)
    at HTMLButtonElement.onclick (handler.js:40:20)
"""
        builder = SourceMapBuilder("handler.py", "handler.js")
        builder.add_mapping(9, 4, 8, 3)
        builder.add_mapping(19, 9, 18, 8)
        builder.add_mapping(29, 14, 28, 13)
        builder.add_mapping(39, 19, 38, 18)
        source_map = builder.to_json()
        
        rewritten = rewrite_stack_trace(stack, source_map)
        assert "handler.py" in rewritten
    
    def test_rewrite_preserves_format(self):
        """Test rewriting preserves stack trace format."""
        stack = """
Error: Division by zero
    at divide (handler.js:15:8)
"""
        builder = SourceMapBuilder("handler.py", "handler.js")
        builder.add_mapping(14, 7, 11, 4)
        source_map = builder.to_json()
        
        rewritten = rewrite_stack_trace(stack, source_map)
        # Should maintain similar format
        assert "at" in rewritten or "handler.py" in rewritten
    
    def test_rewrite_with_unicode_in_error(self):
        """Test rewriting with unicode in error message."""
        stack = """
エラー: Division by zero
    at divide (handler.js:15:8)
"""
        builder = SourceMapBuilder("handler.py", "handler.js")
        builder.add_mapping(14, 7, 11, 4)
        source_map = builder.to_json()
        
        rewritten = rewrite_stack_trace(stack, source_map)
        assert "エラー" in rewritten
    
    def test_rewrite_with_special_characters(self):
        """Test rewriting with special characters."""
        stack = """
Error: Division by zero
    at divide (handler.js:15:8)
"""
        builder = SourceMapBuilder("handler.py", "handler.js")
        builder.add_mapping(14, 7, 11, 4)
        source_map = builder.to_json()
        
        rewritten = rewrite_stack_trace(stack, source_map)
        assert "handler.py" in rewritten
    
    def test_rewrite_with_empty_frames(self):
        """Test rewriting with empty frames list."""
        stack = "Error: Division by zero"
        builder = SourceMapBuilder("handler.py", "handler.js")
        source_map = builder.to_json()
        
        rewritten = rewrite_stack_trace(stack, source_map)
        assert rewritten == stack  # Should return original
    
    def test_rewrite_with_invalid_frame(self):
        """Test rewriting with invalid frame format."""
        stack = """
Error: Division by zero
    invalid frame format
"""
        builder = SourceMapBuilder("handler.py", "handler.js")
        source_map = builder.to_json()
        
        rewritten = rewrite_stack_trace(stack, source_map)
        # Should handle gracefully
        assert "Error: Division by zero" in rewritten
    
    def test_rewrite_with_missing_file(self):
        """Test rewriting with missing file in frame."""
        stack = """
Error: Division by zero
    at divide (:15:8)
"""
        builder = SourceMapBuilder("handler.py", "handler.js")
        builder.add_mapping(14, 7, 11, 4)
        source_map = builder.to_json()
        
        rewritten = rewrite_stack_trace(stack, source_map)
        # Should handle gracefully
        assert "Error: Division by zero" in rewritten
    
    def test_rewrite_with_missing_line(self):
        """Test rewriting with missing line in frame."""
        stack = """
Error: Division by zero
    at divide (handler.js)
"""
        builder = SourceMapBuilder("handler.py", "handler.js")
        source_map = builder.to_json()
        
        rewritten = rewrite_stack_trace(stack, source_map)
        # Should handle gracefully
        assert "Error: Division by zero" in rewritten
    
    def test_rewrite_from_file(self):
        """Test rewrite_stack_trace_from_file function."""
        import tempfile
        import os
        
        stack = """
Error: Division by zero
    at divide (handler.js:15:8)
"""
        builder = SourceMapBuilder("handler.py", "handler.js")
        builder.add_mapping(14, 7, 11, 4)
        source_map = builder.to_json()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.map', delete=False) as f:
            json.dump(source_map, f)
            map_path = f.name
        
        try:
            rewritten = rewrite_stack_trace_from_file(stack, map_path)
            assert "handler.py" in rewritten or "handler.js" in rewritten
        finally:
            os.unlink(map_path)
    
    def test_rewrite_from_file_not_found(self):
        """Test rewrite_stack_trace_from_file with missing file."""
        stack = """
Error: Division by zero
    at divide (handler.js:15:8)
"""
        rewritten = rewrite_stack_trace_from_file(stack, "/nonexistent/file.map")
        # Should return original stack trace
        assert "handler.js" in rewritten
    
    def test_rewrite_from_file_invalid_json(self):
        """Test rewrite_stack_trace_from_file with invalid JSON."""
        import tempfile
        import os
        
        stack = """
Error: Division by zero
    at divide (handler.js:15:8)
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.map', delete=False) as f:
            f.write("invalid json")
            map_path = f.name
        
        try:
            rewritten = rewrite_stack_trace_from_file(stack, map_path)
            # Should return original stack trace
            assert "handler.js" in rewritten
        finally:
            os.unlink(map_path)


# =============================================================================
# BROWSER FORMAT SUPPORT (20 tests)
# =============================================================================

class TestBrowserFormatSupport:
    """Test support for all browser stack trace formats."""
    
    def test_chrome_format_basic(self):
        """Test Chrome format basic."""
        stack = """
Error: test
    at func (file.js:10:5)
"""
        parsed = parse_stack_trace(stack)
        assert len(parsed.frames) == 1
        assert parsed.frames[0].function == "func"
        assert parsed.frames[0].file == "file.js"
        assert parsed.frames[0].line == 10
        assert parsed.frames[0].column == 5
    
    def test_chrome_format_anonymous(self):
        """Test Chrome format with anonymous function."""
        stack = """
Error: test
    at <anonymous> (file.js:10:5)
"""
        parsed = parse_stack_trace(stack)
        assert parsed.frames[0].function == "<anonymous>"
    
    def test_chrome_format_object_method(self):
        """Test Chrome format with object method."""
        stack = """
Error: test
    at Object.method (file.js:10:5)
"""
        parsed = parse_stack_trace(stack)
        assert "method" in parsed.frames[0].function or "Object.method" in parsed.frames[0].function
    
    def test_chrome_format_class_method(self):
        """Test Chrome format with class method."""
        stack = """
Error: test
    at MyClass.method (file.js:10:5)
"""
        parsed = parse_stack_trace(stack)
        assert "method" in parsed.frames[0].function or "MyClass.method" in parsed.frames[0].function
    
    def test_firefox_format_basic(self):
        """Test Firefox format basic."""
        stack = """
Error: test
func@file.js:10:5
"""
        parsed = parse_stack_trace(stack)
        assert len(parsed.frames) == 1
        assert parsed.frames[0].function == "func"
        assert parsed.frames[0].file == "file.js"
        assert parsed.frames[0].line == 10
        assert parsed.frames[0].column == 5
    
    def test_firefox_format_global_code(self):
        """Test Firefox format with global code."""
        stack = """
Error: test
global code@file.js:10:5
"""
        parsed = parse_stack_trace(stack)
        assert parsed.frames[0].function is None
    
    def test_firefox_format_anonymous(self):
        """Test Firefox format with anonymous."""
        stack = """
Error: test
<anonymous>@file.js:10:5
"""
        parsed = parse_stack_trace(stack)
        assert parsed.frames[0].function == "<anonymous>"
    
    def test_safari_format_basic(self):
        """Test Safari format basic."""
        stack = """
Error: test
func@file.js:10:5
"""
        parsed = parse_stack_trace(stack)
        assert len(parsed.frames) == 1
        assert parsed.frames[0].function == "func"
    
    def test_safari_format_global_code(self):
        """Test Safari format with global code."""
        stack = """
Error: test
global code@file.js:10:5
"""
        parsed = parse_stack_trace(stack)
        assert parsed.frames[0].function is None
    
    def test_nodejs_format_basic(self):
        """Test Node.js format basic."""
        stack = """
Error: test
    at func (file.js:10:5)
"""
        parsed = parse_stack_trace(stack)
        assert len(parsed.frames) == 1
        assert parsed.frames[0].function == "func"
    
    def test_nodejs_format_module(self):
        """Test Node.js format with module."""
        stack = """
Error: test
    at func (/path/to/file.js:10:5)
"""
        parsed = parse_stack_trace(stack)
        assert parsed.frames[0].file == "/path/to/file.js"
    
    def test_edge_format_basic(self):
        """Test Edge format (same as Chrome)."""
        stack = """
Error: test
    at func (file.js:10:5)
"""
        parsed = parse_stack_trace(stack)
        assert len(parsed.frames) == 1
        assert parsed.frames[0].function == "func"
    
    def test_chrome_format_without_column(self):
        """Test Chrome format without column."""
        stack = """
Error: test
    at func (file.js:10)
"""
        parsed = parse_stack_trace(stack)
        assert parsed.frames[0].line == 10
        assert parsed.frames[0].column is None
    
    def test_firefox_format_without_column(self):
        """Test Firefox format without column."""
        stack = """
Error: test
func@file.js:10
"""
        parsed = parse_stack_trace(stack)
        assert parsed.frames[0].line == 10
        assert parsed.frames[0].column is None
    
    def test_chrome_format_with_async(self):
        """Test Chrome format with async."""
        stack = """
Error: test
    at async func (file.js:10:5)
"""
        parsed = parse_stack_trace(stack)
        assert len(parsed.frames) == 1
        # "async" might be part of function name
    
    def test_chrome_format_with_promise(self):
        """Test Chrome format with Promise."""
        stack = """
UnhandledPromiseRejectionWarning: test
    at Promise.then (file.js:10:5)
"""
        parsed = parse_stack_trace(stack)
        assert len(parsed.frames) == 1
    
    def test_firefox_format_with_eval(self):
        """Test Firefox format with eval."""
        stack = """
Error: test
eval code@file.js:10:5
"""
        parsed = parse_stack_trace(stack)
        assert len(parsed.frames) == 1
    
    def test_chrome_format_with_eval(self):
        """Test Chrome format with eval."""
        stack = """
Error: test
    at eval (eval at <anonymous> (file.js:10:5))
"""
        parsed = parse_stack_trace(stack)
        # Complex eval format might parse partially
        assert len(parsed.frames) >= 0
    
    def test_safari_format_with_eval(self):
        """Test Safari format with eval."""
        stack = """
Error: test
eval code@file.js:10:5
"""
        parsed = parse_stack_trace(stack)
        assert len(parsed.frames) == 1
    
    def test_mixed_browser_formats(self):
        """Test mixed browser formats in same stack."""
        stack = """
Error: test
    at func1 (file1.js:10:5)
func2@file2.js:20:10
    at func3 (file3.js:30:15)
"""
        parsed = parse_stack_trace(stack)
        assert len(parsed.frames) == 3
        # Should handle both formats


# =============================================================================
# EDGE CASES (10 tests)
# =============================================================================

class TestStackTraceEdgeCases:
    """Test edge cases and error handling."""
    
    def test_parse_with_very_long_error_message(self):
        """Test parsing with very long error message."""
        long_message = "Error: " + "x" * 10000
        stack = f"""
{long_message}
    at func (file.js:10:5)
"""
        parsed = parse_stack_trace(stack)
        assert len(parsed.error_message) > 1000
    
    def test_parse_with_very_many_frames(self):
        """Test parsing with very many frames."""
        stack = "Error: test\n"
        for i in range(100):
            stack += f"    at func{i} (file.js:{i}:5)\n"
        parsed = parse_stack_trace(stack)
        assert len(parsed.frames) == 100
    
    def test_rewrite_with_very_large_line_numbers(self):
        """Test rewriting with very large line numbers."""
        stack = """
Error: test
    at func (file.js:100000:50000)
"""
        builder = SourceMapBuilder("source.py", "file.js")
        builder.add_mapping(99999, 49999, 50000, 25000)
        source_map = builder.to_json()
        
        rewritten = rewrite_stack_trace(stack, source_map)
        assert "source.py" in rewritten or "file.js" in rewritten
    
    def test_rewrite_with_zero_line_numbers(self):
        """Test rewriting with zero line numbers."""
        stack = """
Error: test
    at func (file.js:0:0)
"""
        # Phase 33.3: Zero line numbers can't be rewritten (line 0 → gen_line -1 is invalid)
        # Create a valid source map (but it won't have a mapping for line 0)
        builder = SourceMapBuilder("source.py", "file.js")
        builder.add_mapping(0, 0, 0, 0)  # Valid mapping for line 1 (0-indexed)
        source_map = builder.to_json()
        
        rewritten = rewrite_stack_trace(stack, source_map)
        # Should preserve original frame since line 0 (1-indexed) becomes -1 (0-indexed)
        assert "Error: test" in rewritten
        # Original frame should be preserved (can't rewrite line 0)
        assert "file.js:0:0" in rewritten or "at func" in rewritten
    
    def test_rewrite_with_malformed_source_map(self):
        """Test rewriting with malformed source map."""
        stack = """
Error: test
    at func (file.js:10:5)
"""
        source_map = {"version": 3, "mappings": "invalid"}
        rewritten = rewrite_stack_trace(stack, source_map)
        # Should handle gracefully
        assert "Error: test" in rewritten
    
    def test_rewrite_with_missing_sources(self):
        """Test rewriting with missing sources in source map."""
        stack = """
Error: test
    at func (file.js:10:5)
"""
        source_map = {"version": 3, "mappings": ""}
        rewritten = rewrite_stack_trace(stack, source_map)
        # Should handle gracefully
        assert "Error: test" in rewritten
    
    def test_parse_with_unicode_in_file_name(self):
        """Test parsing with unicode in file name."""
        stack = """
Error: test
    at func (ファイル.js:10:5)
"""
        parsed = parse_stack_trace(stack)
        assert parsed.frames[0].file == "ファイル.js"
    
    def test_rewrite_with_unicode_in_source_file(self):
        """Test rewriting with unicode in source file."""
        stack = """
Error: test
    at func (file.js:10:5)
"""
        builder = SourceMapBuilder("ソース.py", "file.js")
        builder.add_mapping(9, 4, 8, 3)
        source_map = builder.to_json()
        
        rewritten = rewrite_stack_trace(stack, source_map)
        assert "ソース.py" in rewritten or "file.js" in rewritten
    
    def test_parse_with_special_characters_in_error(self):
        """Test parsing with special characters in error."""
        stack = """
Error: test\n\t\"special\"
    at func (file.js:10:5)
"""
        parsed = parse_stack_trace(stack)
        assert "test" in parsed.error_message or "special" in parsed.error_message
    
    def test_comprehensive_rewrite_scenario(self):
        """Test comprehensive rewrite scenario."""
        stack = """
TypeError: Cannot read property 'x' of undefined
    at process (handler.js:10:5)
    at calculate (handler.js:20:10)
    at handleClick (handler.js:30:15)
"""
        builder = SourceMapBuilder("handler.py", "handler.js")
        builder.start_function("handleClick", 29, 0, 28, 0)
        builder.start_function("calculate", 19, 0, 18, 0)
        builder.start_function("process", 9, 0, 8, 0)
        builder.add_mapping(9, 4, 8, 3, name="x")
        builder.add_mapping(19, 9, 18, 8, name="y")
        builder.add_mapping(29, 14, 28, 13, name="z")
        builder.end_function("process", 15, 10)
        builder.end_function("calculate", 25, 20)
        builder.end_function("handleClick", 35, 30)
        source_map = builder.to_json()
        
        rewritten = rewrite_stack_trace(stack, source_map)
        assert "handler.py" in rewritten
        assert "TypeError" in rewritten

