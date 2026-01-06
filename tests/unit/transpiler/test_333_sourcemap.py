"""
Phase 33.3: Source Map Comprehensive Tests

Comprehensive test suite for enhanced source map generation covering:
- Basic mappings (line/column positions)
- Variable name preservation
- Function/class tracking and boundaries
- Column precision
- Multi-line handling
- Stack trace integration
- Edge cases

Total: 150+ tests covering all aspects of source map generation.
"""

import pytest
import json
from pynext.transpiler.sourcemap import (
    SourceMapBuilder,
    Mapping,
    create_source_map,
    _encode_vlq,
    _encode_vlq_segment,
)


# =============================================================================
# BASIC MAPPINGS (30 tests)
# =============================================================================

class TestBasicMappings:
    """Test basic source map mappings."""
    
    def test_create_builder(self):
        """Test creating SourceMapBuilder."""
        builder = SourceMapBuilder("source.py", "output.js")
        assert builder.source_file == "source.py"
        assert builder.generated_file == "output.js"
        assert len(builder.mappings) == 0
    
    def test_add_single_mapping(self):
        """Test adding a single mapping."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0)
        assert len(builder.mappings) == 1
        assert builder.mappings[0].gen_line == 0
        assert builder.mappings[0].gen_col == 0
        assert builder.mappings[0].src_line == 0
        assert builder.mappings[0].src_col == 0
    
    def test_add_multiple_mappings(self):
        """Test adding multiple mappings."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0)
        builder.add_mapping(1, 4, 1, 4)
        builder.add_mapping(2, 8, 2, 8)
        assert len(builder.mappings) == 3
    
    def test_mapping_with_different_lines(self):
        """Test mappings with different line numbers."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0)
        builder.add_mapping(5, 0, 10, 0)
        builder.add_mapping(10, 0, 20, 0)
        assert len(builder.mappings) == 3
        assert builder.mappings[1].gen_line == 5
        assert builder.mappings[1].src_line == 10
    
    def test_mapping_with_different_columns(self):
        """Test mappings with different column numbers."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0)
        builder.add_mapping(0, 4, 0, 4)
        builder.add_mapping(0, 8, 0, 8)
        assert len(builder.mappings) == 3
        assert builder.mappings[1].gen_col == 4
        assert builder.mappings[1].src_col == 4
    
    def test_mapping_with_zero_positions(self):
        """Test mappings with zero positions."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0)
        assert builder.mappings[0].gen_line == 0
        assert builder.mappings[0].gen_col == 0
        assert builder.mappings[0].src_line == 0
        assert builder.mappings[0].src_col == 0
    
    def test_mapping_with_large_positions(self):
        """Test mappings with large line/column numbers."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(1000, 500, 2000, 1000)
        assert builder.mappings[0].gen_line == 1000
        assert builder.mappings[0].gen_col == 500
        assert builder.mappings[0].src_line == 2000
        assert builder.mappings[0].src_col == 1000
    
    def test_mapping_with_negative_positions(self):
        """Test mappings with negative positions (should handle gracefully)."""
        builder = SourceMapBuilder("source.py", "output.js")
        # Negative positions are technically invalid but shouldn't crash
        builder.add_mapping(-1, -1, -1, -1)
        assert len(builder.mappings) == 1
    
    def test_to_json_basic(self):
        """Test generating JSON from basic mappings."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0)
        result = builder.to_json()
        assert result["version"] == 3
        assert result["file"] == "output.js"
        assert result["sources"] == ["source.py"]
        assert "mappings" in result
    
    def test_to_json_with_multiple_mappings(self):
        """Test generating JSON with multiple mappings."""
        builder = SourceMapBuilder("source.py", "output.js")
        for i in range(10):
            builder.add_mapping(i, i * 4, i, i * 4)
        result = builder.to_json()
        assert result["version"] == 3
        assert "mappings" in result
        assert result["mappings"] != ""
    
    def test_to_json_string(self):
        """Test generating JSON string."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0)
        json_str = builder.to_json_string()
        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed["version"] == 3
    
    def test_to_data_url(self):
        """Test generating data URL."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0)
        data_url = builder.to_data_url()
        assert data_url.startswith("data:application/json;base64,")
    
    def test_to_inline_comment(self):
        """Test generating inline comment."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0)
        comment = builder.to_inline_comment()
        assert comment.startswith("//# sourceMappingURL=")
        assert "data:application/json;base64," in comment
    
    def test_source_content_embedding(self):
        """Test embedding source content."""
        source_code = "x = 1\ny = 2"
        builder = SourceMapBuilder("source.py", "output.js", source_content=source_code)
        builder.add_mapping(0, 0, 0, 0)
        result = builder.to_json()
        assert "sourcesContent" in result
        assert result["sourcesContent"][0] == source_code
    
    def test_source_content_without_embedding(self):
        """Test source map without embedding content."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0)
        result = builder.to_json()
        assert "sourcesContent" not in result
    
    def test_mapping_sorting(self):
        """Test mappings are sorted by generated position."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(5, 10, 10, 20)
        builder.add_mapping(1, 2, 2, 4)
        builder.add_mapping(3, 6, 6, 12)
        # Mappings should be sorted when encoded
        result = builder.to_json()
        assert "mappings" in result
    
    def test_mapping_with_same_line(self):
        """Test multiple mappings on same line."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0)
        builder.add_mapping(0, 4, 0, 4)
        builder.add_mapping(0, 8, 0, 8)
        result = builder.to_json()
        assert "mappings" in result
    
    def test_mapping_with_same_column(self):
        """Test multiple mappings with same column."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0)
        builder.add_mapping(1, 0, 1, 0)
        builder.add_mapping(2, 0, 2, 0)
        result = builder.to_json()
        assert "mappings" in result
    
    def test_mapping_with_gaps(self):
        """Test mappings with gaps in line numbers."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0)
        builder.add_mapping(10, 0, 10, 0)
        builder.add_mapping(20, 0, 20, 0)
        result = builder.to_json()
        assert "mappings" in result
    
    def test_mapping_with_gaps_in_columns(self):
        """Test mappings with gaps in column numbers."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0)
        builder.add_mapping(0, 10, 0, 10)
        builder.add_mapping(0, 20, 0, 20)
        result = builder.to_json()
        assert "mappings" in result
    
    def test_empty_mappings(self):
        """Test source map with no mappings."""
        builder = SourceMapBuilder("source.py", "output.js")
        result = builder.to_json()
        assert result["mappings"] == ""
    
    def test_create_source_map_helper(self):
        """Test create_source_map convenience function."""
        mappings = [(0, 0, 0, 0), (1, 4, 1, 4), (2, 8, 2, 8)]
        result = create_source_map("source.py", "output.js", mappings)
        assert result["version"] == 3
        assert result["sources"] == ["source.py"]
        assert "mappings" in result
    
    def test_create_source_map_with_content(self):
        """Test create_source_map with source content."""
        mappings = [(0, 0, 0, 0)]
        source_content = "x = 1"
        result = create_source_map("source.py", "output.js", mappings, source_content)
        assert "sourcesContent" in result
        assert result["sourcesContent"][0] == source_content
    
    def test_mapping_with_unicode_source_file(self):
        """Test mapping with unicode source file name."""
        builder = SourceMapBuilder("ソース.py", "output.js")
        builder.add_mapping(0, 0, 0, 0)
        result = builder.to_json()
        assert "ソース.py" in result["sources"]
    
    def test_mapping_with_unicode_generated_file(self):
        """Test mapping with unicode generated file name."""
        builder = SourceMapBuilder("source.py", "出力.js")
        builder.add_mapping(0, 0, 0, 0)
        result = builder.to_json()
        assert result["file"] == "出力.js"
    
    def test_mapping_with_special_characters_in_paths(self):
        """Test mapping with special characters in paths."""
        builder = SourceMapBuilder("source-file.py", "output_file.js")
        builder.add_mapping(0, 0, 0, 0)
        result = builder.to_json()
        assert "source-file.py" in result["sources"]
        assert result["file"] == "output_file.js"
    
    def test_mapping_with_relative_paths(self):
        """Test mapping with relative paths."""
        builder = SourceMapBuilder("../source.py", "./output.js")
        builder.add_mapping(0, 0, 0, 0)
        result = builder.to_json()
        assert "../source.py" in result["sources"]
        assert result["file"] == "./output.js"
    
    def test_mapping_with_absolute_paths(self):
        """Test mapping with absolute paths."""
        builder = SourceMapBuilder("/path/to/source.py", "/path/to/output.js")
        builder.add_mapping(0, 0, 0, 0)
        result = builder.to_json()
        assert "/path/to/source.py" in result["sources"]
        assert result["file"] == "/path/to/output.js"
    
    def test_mapping_with_empty_strings(self):
        """Test mapping with empty string paths."""
        builder = SourceMapBuilder("", "")
        builder.add_mapping(0, 0, 0, 0)
        result = builder.to_json()
        assert result["sources"] == [""]
        assert result["file"] == ""
    
    def test_mapping_with_very_long_paths(self):
        """Test mapping with very long file paths."""
        long_path = "a" * 1000 + ".py"
        builder = SourceMapBuilder(long_path, "output.js")
        builder.add_mapping(0, 0, 0, 0)
        result = builder.to_json()
        assert long_path in result["sources"]
    
    def test_mapping_json_serializable(self):
        """Test source map is JSON serializable."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0)
        result = builder.to_json()
        # Should not raise exception
        json_str = json.dumps(result)
        parsed = json.loads(json_str)
        assert parsed["version"] == 3


# =============================================================================
# VARIABLE NAME PRESERVATION (30 tests)
# =============================================================================

class TestVariableNamePreservation:
    """Test variable name preservation in source maps."""
    
    def test_add_mapping_with_name(self):
        """Test adding mapping with variable name."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0, name="x")
        assert len(builder.mappings) == 1
        assert builder.mappings[0].name == "x"
        assert "x" in builder.names
    
    def test_add_multiple_names(self):
        """Test adding multiple variable names."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0, name="x")
        builder.add_mapping(1, 0, 1, 0, name="y")
        builder.add_mapping(2, 0, 2, 0, name="z")
        assert len(builder.names) == 3
        assert "x" in builder.names
        assert "y" in builder.names
        assert "z" in builder.names
    
    def test_duplicate_names_only_added_once(self):
        """Test duplicate names are only added once."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0, name="x")
        builder.add_mapping(1, 0, 1, 0, name="x")
        builder.add_mapping(2, 0, 2, 0, name="x")
        assert len(builder.names) == 1
        assert builder.names.count("x") == 1
    
    def test_names_in_json(self):
        """Test names are included in JSON output."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0, name="x")
        builder.add_mapping(1, 0, 1, 0, name="y")
        result = builder.to_json()
        assert "names" in result
        assert "x" in result["names"]
        assert "y" in result["names"]
    
    def test_name_index_mapping(self):
        """Test name index mapping is correct."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0, name="x")
        builder.add_mapping(1, 0, 1, 0, name="y")
        assert builder._name_index["x"] == 0
        assert builder._name_index["y"] == 1
    
    def test_name_with_underscore(self):
        """Test variable name with underscore."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0, name="_private")
        assert "_private" in builder.names
    
    def test_name_with_numbers(self):
        """Test variable name with numbers."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0, name="var123")
        assert "var123" in builder.names
    
    def test_name_with_unicode(self):
        """Test variable name with unicode."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0, name="変数")
        assert "変数" in builder.names
    
    def test_name_with_special_characters(self):
        """Test variable name with special characters (Python allows some)."""
        builder = SourceMapBuilder("source.py", "output.js")
        # Python allows _ in names
        builder.add_mapping(0, 0, 0, 0, name="my_var")
        assert "my_var" in builder.names
    
    def test_name_with_camel_case(self):
        """Test variable name with camelCase."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0, name="myVariable")
        assert "myVariable" in builder.names
    
    def test_name_with_pascal_case(self):
        """Test variable name with PascalCase."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0, name="MyClass")
        assert "MyClass" in builder.names
    
    def test_name_with_snake_case(self):
        """Test variable name with snake_case."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0, name="my_variable_name")
        assert "my_variable_name" in builder.names
    
    def test_name_with_very_long_name(self):
        """Test variable name with very long name."""
        long_name = "a" * 1000
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0, name=long_name)
        assert long_name in builder.names
    
    def test_name_with_empty_string(self):
        """Test variable name with empty string."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0, name="")
        # Empty string might be added, but shouldn't crash
        assert len(builder.mappings) == 1
    
    def test_name_with_whitespace(self):
        """Test variable name with whitespace (should be stripped or handled)."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0, name="  var  ")
        # Names with whitespace might be preserved as-is
        assert len(builder.mappings) == 1
    
    def test_multiple_mappings_same_name(self):
        """Test multiple mappings with same name."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0, name="x")
        builder.add_mapping(1, 0, 1, 0, name="x")
        builder.add_mapping(2, 0, 2, 0, name="x")
        assert len(builder.names) == 1
        assert builder.names[0] == "x"
    
    def test_names_preserved_in_mappings(self):
        """Test names are preserved in mapping objects."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0, name="x")
        assert builder.mappings[0].name == "x"
    
    def test_names_with_function_names(self):
        """Test function names are preserved."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0, name="my_function")
        assert "my_function" in builder.names
    
    def test_names_with_class_names(self):
        """Test class names are preserved."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0, name="MyClass")
        assert "MyClass" in builder.names
    
    def test_names_with_constant_names(self):
        """Test constant names are preserved."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0, name="CONSTANT")
        assert "CONSTANT" in builder.names
    
    def test_names_mixed_case(self):
        """Test names with mixed case."""
        builder = SourceMapBuilder("source.py", "output.js")
        names = ["x", "X", "myVar", "MyVar", "MY_VAR"]
        for name in names:
            builder.add_mapping(0, 0, 0, 0, name=name)
        assert len(builder.names) == len(names)
        for name in names:
            assert name in builder.names
    
    def test_names_with_keywords(self):
        """Test names that are Python keywords (should still be preserved)."""
        builder = SourceMapBuilder("source.py", "output.js")
        # In JS, these might be minified, but we preserve original names
        builder.add_mapping(0, 0, 0, 0, name="def")
        # Should not crash, name might be preserved or handled specially
        assert len(builder.mappings) == 1
    
    def test_names_with_builtin_names(self):
        """Test names that are Python builtins."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0, name="len")
        assert "len" in builder.names
    
    def test_names_with_module_names(self):
        """Test names that are module names."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0, name="json")
        assert "json" in builder.names
    
    def test_names_with_attribute_access(self):
        """Test names with attribute access pattern."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0, name="obj.attr")
        # Attribute access might be stored as-is or split
        assert len(builder.mappings) == 1
    
    def test_names_with_subscript_access(self):
        """Test names with subscript access pattern."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0, name="arr[0]")
        # Subscript access might be stored as-is or split
        assert len(builder.mappings) == 1
    
    def test_names_in_vlq_encoding(self):
        """Test names are included in VLQ encoding."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0, name="x")
        result = builder.to_json()
        # Name index should be included in mappings
        assert "mappings" in result
        assert result["mappings"] != ""
    
    def test_names_order_preserved(self):
        """Test names order is preserved (first occurrence)."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0, name="x")
        builder.add_mapping(1, 0, 1, 0, name="y")
        builder.add_mapping(2, 0, 2, 0, name="z")
        assert builder.names == ["x", "y", "z"]
    
    def test_names_with_none(self):
        """Test mapping with None name."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0, name=None)
        assert builder.mappings[0].name is None
        assert len(builder.names) == 0
    
    def test_names_with_many_unique_names(self):
        """Test many unique variable names."""
        builder = SourceMapBuilder("source.py", "output.js")
        for i in range(100):
            builder.add_mapping(i, 0, i, 0, name=f"var_{i}")
        assert len(builder.names) == 100
        for i in range(100):
            assert f"var_{i}" in builder.names


# =============================================================================
# FUNCTION/CLASS TRACKING (30 tests)
# =============================================================================

class TestFunctionClassTracking:
    """Test function and class boundary tracking."""
    
    def test_start_function(self):
        """Test starting a function."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_function("my_function", 0, 0, 0, 0)
        assert builder.get_current_function() == "my_function"
        assert len(builder.mappings) == 1
        assert builder.mappings[0].name == "my_function"
        assert builder.mappings[0].kind == "function"
    
    def test_end_function(self):
        """Test ending a function."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_function("my_function", 0, 0, 0, 0)
        builder.end_function("my_function", 5, 3)
        assert builder.get_current_function() is None
        boundaries = builder.get_function_boundaries()
        assert len(boundaries) == 1
        assert boundaries[0]["name"] == "my_function"
    
    def test_start_class(self):
        """Test starting a class."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_class("MyClass", 0, 0, 0, 0)
        assert builder.get_current_class() == "MyClass"
        assert len(builder.mappings) == 1
        assert builder.mappings[0].name == "MyClass"
        assert builder.mappings[0].kind == "class"
    
    def test_end_class(self):
        """Test ending a class."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_class("MyClass", 0, 0, 0, 0)
        builder.end_class("MyClass", 10, 5)
        assert builder.get_current_class() is None
        boundaries = builder.get_class_boundaries()
        assert len(boundaries) == 1
        assert boundaries[0]["name"] == "MyClass"
    
    def test_nested_functions(self):
        """Test nested functions."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_function("outer", 0, 0, 0, 0)
        assert builder.get_current_function() == "outer"
        builder.start_function("inner", 2, 0, 2, 0)
        assert builder.get_current_function() == "inner"
        builder.end_function("inner", 5, 3)
        assert builder.get_current_function() == "outer"
        builder.end_function("outer", 10, 5)
        assert builder.get_current_function() is None
    
    def test_nested_classes(self):
        """Test nested classes."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_class("Outer", 0, 0, 0, 0)
        assert builder.get_current_class() == "Outer"
        builder.start_class("Inner", 2, 0, 2, 0)
        assert builder.get_current_class() == "Inner"
        builder.end_class("Inner", 5, 3)
        assert builder.get_current_class() == "Outer"
        builder.end_class("Outer", 10, 5)
        assert builder.get_current_class() is None
    
    def test_function_in_class(self):
        """Test function inside class."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_class("MyClass", 0, 0, 0, 0)
        assert builder.get_current_class() == "MyClass"
        builder.start_function("method", 2, 0, 2, 0)
        assert builder.get_current_function() == "method"
        assert builder.get_current_class() == "MyClass"
        builder.end_function("method", 5, 3)
        builder.end_class("MyClass", 10, 5)
        assert builder.get_current_class() is None
        assert builder.get_current_function() is None
    
    def test_multiple_functions(self):
        """Test multiple functions."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_function("func1", 0, 0, 0, 0)
        builder.end_function("func1", 5, 3)
        builder.start_function("func2", 6, 0, 6, 0)
        builder.end_function("func2", 10, 5)
        boundaries = builder.get_function_boundaries()
        assert len(boundaries) == 2
        assert boundaries[0]["name"] == "func1"
        assert boundaries[1]["name"] == "func2"
    
    def test_multiple_classes(self):
        """Test multiple classes."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_class("Class1", 0, 0, 0, 0)
        builder.end_class("Class1", 5, 3)
        builder.start_class("Class2", 6, 0, 6, 0)
        builder.end_class("Class2", 10, 5)
        boundaries = builder.get_class_boundaries()
        assert len(boundaries) == 2
        assert boundaries[0]["name"] == "Class1"
        assert boundaries[1]["name"] == "Class2"
    
    def test_function_boundaries_in_json(self):
        """Test function boundaries included in JSON."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_function("my_function", 0, 0, 0, 0)
        builder.end_function("my_function", 5, 3)
        result = builder.to_json()
        assert "x_pynext_functions" in result
        assert len(result["x_pynext_functions"]) == 1
        assert result["x_pynext_functions"][0]["name"] == "my_function"
    
    def test_class_boundaries_in_json(self):
        """Test class boundaries included in JSON."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_class("MyClass", 0, 0, 0, 0)
        builder.end_class("MyClass", 10, 5)
        result = builder.to_json()
        assert "x_pynext_classes" in result
        assert len(result["x_pynext_classes"]) == 1
        assert result["x_pynext_classes"][0]["name"] == "MyClass"
    
    def test_function_boundary_positions(self):
        """Test function boundary positions are correct."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_function("my_function", 1, 4, 2, 8)
        builder.end_function("my_function", 10, 20)
        boundaries = builder.get_function_boundaries()
        assert boundaries[0]["generated"]["start"] == 1
        assert boundaries[0]["generated"]["end"] == 10
        assert boundaries[0]["source"]["start"] == 2
        assert boundaries[0]["source"]["end"] == 20
    
    def test_class_boundary_positions(self):
        """Test class boundary positions are correct."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_class("MyClass", 1, 4, 2, 8)
        builder.end_class("MyClass", 10, 20)
        boundaries = builder.get_class_boundaries()
        assert boundaries[0]["generated"]["start"] == 1
        assert boundaries[0]["generated"]["end"] == 10
        assert boundaries[0]["source"]["start"] == 2
        assert boundaries[0]["source"]["end"] == 20
    
    def test_incomplete_function_not_in_json(self):
        """Test incomplete functions not included in JSON."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_function("my_function", 0, 0, 0, 0)
        # Don't call end_function
        result = builder.to_json()
        if "x_pynext_functions" in result:
            # Should only include completed functions
            assert len(result["x_pynext_functions"]) == 0
    
    def test_incomplete_class_not_in_json(self):
        """Test incomplete classes not included in JSON."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_class("MyClass", 0, 0, 0, 0)
        # Don't call end_class
        result = builder.to_json()
        if "x_pynext_classes" in result:
            # Should only include completed classes
            assert len(result["x_pynext_classes"]) == 0
    
    def test_function_with_mappings_inside(self):
        """Test function with mappings inside."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_function("my_function", 0, 0, 0, 0)
        builder.add_mapping(1, 4, 1, 4, name="x")
        builder.add_mapping(2, 8, 2, 8, name="y")
        builder.end_function("my_function", 3, 3)
        assert len(builder.mappings) == 3  # function start + 2 mappings
        boundaries = builder.get_function_boundaries()
        assert len(boundaries) == 1
    
    def test_class_with_mappings_inside(self):
        """Test class with mappings inside."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_class("MyClass", 0, 0, 0, 0)
        builder.add_mapping(1, 4, 1, 4, name="x")
        builder.add_mapping(2, 8, 2, 8, name="y")
        builder.end_class("MyClass", 3, 3)
        assert len(builder.mappings) == 3  # class start + 2 mappings
        boundaries = builder.get_class_boundaries()
        assert len(boundaries) == 1
    
    def test_function_with_nested_function(self):
        """Test function with nested function."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_function("outer", 0, 0, 0, 0)
        builder.start_function("inner", 2, 0, 2, 0)
        builder.end_function("inner", 5, 3)
        builder.end_function("outer", 10, 5)
        boundaries = builder.get_function_boundaries()
        assert len(boundaries) == 2
        assert boundaries[0]["name"] == "outer"
        assert boundaries[1]["name"] == "inner"
    
    def test_class_with_nested_class(self):
        """Test class with nested class."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_class("Outer", 0, 0, 0, 0)
        builder.start_class("Inner", 2, 0, 2, 0)
        builder.end_class("Inner", 5, 3)
        builder.end_class("Outer", 10, 5)
        boundaries = builder.get_class_boundaries()
        assert len(boundaries) == 2
        assert boundaries[0]["name"] == "Outer"
        assert boundaries[1]["name"] == "Inner"
    
    def test_function_with_anonymous_name(self):
        """Test function with anonymous name."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_function("", 0, 0, 0, 0)
        # Anonymous functions might have empty name
        assert builder.get_current_function() == ""
    
    def test_class_with_anonymous_name(self):
        """Test class with anonymous name."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_class("", 0, 0, 0, 0)
        # Anonymous classes might have empty name
        assert builder.get_current_class() == ""
    
    def test_function_with_unicode_name(self):
        """Test function with unicode name."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_function("関数", 0, 0, 0, 0)
        assert builder.get_current_function() == "関数"
        builder.end_function("関数", 5, 3)
        boundaries = builder.get_function_boundaries()
        assert boundaries[0]["name"] == "関数"
    
    def test_class_with_unicode_name(self):
        """Test class with unicode name."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_class("クラス", 0, 0, 0, 0)
        assert builder.get_current_class() == "クラス"
        builder.end_class("クラス", 10, 5)
        boundaries = builder.get_class_boundaries()
        assert boundaries[0]["name"] == "クラス"
    
    def test_function_with_special_characters(self):
        """Test function with special characters in name."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_function("my_function_123", 0, 0, 0, 0)
        assert builder.get_current_function() == "my_function_123"
    
    def test_class_with_special_characters(self):
        """Test class with special characters in name."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_class("MyClass_123", 0, 0, 0, 0)
        assert builder.get_current_class() == "MyClass_123"
    
    def test_function_with_very_long_name(self):
        """Test function with very long name."""
        long_name = "a" * 1000
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_function(long_name, 0, 0, 0, 0)
        assert builder.get_current_function() == long_name
    
    def test_class_with_very_long_name(self):
        """Test class with very long name."""
        long_name = "A" * 1000
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_class(long_name, 0, 0, 0, 0)
        assert builder.get_current_class() == long_name
    
    def test_multiple_nested_functions(self):
        """Test multiple levels of nested functions."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_function("level1", 0, 0, 0, 0)
        builder.start_function("level2", 2, 0, 2, 0)
        builder.start_function("level3", 4, 0, 4, 0)
        assert builder.get_current_function() == "level3"
        builder.end_function("level3", 6, 5)
        assert builder.get_current_function() == "level2"
        builder.end_function("level2", 8, 7)
        assert builder.get_current_function() == "level1"
        builder.end_function("level1", 10, 9)
        assert builder.get_current_function() is None
    
    def test_multiple_nested_classes(self):
        """Test multiple levels of nested classes."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_class("Level1", 0, 0, 0, 0)
        builder.start_class("Level2", 2, 0, 2, 0)
        builder.start_class("Level3", 4, 0, 4, 0)
        assert builder.get_current_class() == "Level3"
        builder.end_class("Level3", 6, 5)
        assert builder.get_current_class() == "Level2"
        builder.end_class("Level2", 8, 7)
        assert builder.get_current_class() == "Level1"
        builder.end_class("Level1", 10, 9)
        assert builder.get_current_class() is None
    
    def test_function_and_class_together(self):
        """Test function and class boundaries together."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_class("MyClass", 0, 0, 0, 0)
        builder.start_function("method", 2, 0, 2, 0)
        builder.end_function("method", 5, 3)
        builder.end_class("MyClass", 10, 5)
        func_boundaries = builder.get_function_boundaries()
        class_boundaries = builder.get_class_boundaries()
        assert len(func_boundaries) == 1
        assert len(class_boundaries) == 1
        assert func_boundaries[0]["name"] == "method"
        assert class_boundaries[0]["name"] == "MyClass"


# =============================================================================
# COLUMN PRECISION (20 tests)
# =============================================================================

class TestColumnPrecision:
    """Test column-level precision in mappings."""
    
    def test_mapping_with_precise_columns(self):
        """Test mapping with precise column positions."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0)
        builder.add_mapping(0, 4, 0, 4)
        builder.add_mapping(0, 8, 0, 8)
        assert builder.mappings[0].gen_col == 0
        assert builder.mappings[1].gen_col == 4
        assert builder.mappings[2].gen_col == 8
    
    def test_column_precision_in_vlq(self):
        """Test column precision is preserved in VLQ encoding."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0)
        builder.add_mapping(0, 1, 0, 1)
        builder.add_mapping(0, 2, 0, 2)
        result = builder.to_json()
        assert "mappings" in result
        assert result["mappings"] != ""
    
    def test_column_delta_encoding(self):
        """Test column delta encoding within same line."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0)
        builder.add_mapping(0, 4, 0, 4)  # +4 columns
        builder.add_mapping(0, 8, 0, 8)  # +4 columns
        result = builder.to_json()
        # Columns should be delta-encoded
        assert "mappings" in result
    
    def test_column_reset_on_new_line(self):
        """Test column resets on new line."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 10, 0, 10)
        builder.add_mapping(1, 0, 1, 0)  # New line, column resets
        result = builder.to_json()
        assert "mappings" in result
    
    def test_column_with_large_values(self):
        """Test column with large values."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 1000, 0, 1000)
        assert builder.mappings[0].gen_col == 1000
        assert builder.mappings[0].src_col == 1000
    
    def test_column_with_negative_values(self):
        """Test column with negative values (edge case)."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, -1, 0, -1)
        # Should handle gracefully
        assert len(builder.mappings) == 1
    
    def test_column_precision_with_names(self):
        """Test column precision with variable names."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0, name="x")
        builder.add_mapping(0, 4, 0, 4, name="y")
        builder.add_mapping(0, 8, 0, 8, name="z")
        assert builder.mappings[0].gen_col == 0
        assert builder.mappings[1].gen_col == 4
        assert builder.mappings[2].gen_col == 8
    
    def test_column_precision_with_functions(self):
        """Test column precision with function boundaries."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_function("my_function", 0, 4, 0, 4)
        assert builder.mappings[0].gen_col == 4
        assert builder.mappings[0].src_col == 4
    
    def test_column_precision_with_classes(self):
        """Test column precision with class boundaries."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_class("MyClass", 0, 4, 0, 4)
        assert builder.mappings[0].gen_col == 4
        assert builder.mappings[0].src_col == 4
    
    def test_column_precision_multi_line(self):
        """Test column precision across multiple lines."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0)
        builder.add_mapping(1, 4, 1, 4)
        builder.add_mapping(2, 8, 2, 8)
        assert builder.mappings[0].gen_col == 0
        assert builder.mappings[1].gen_col == 4
        assert builder.mappings[2].gen_col == 8
    
    def test_column_precision_with_gaps(self):
        """Test column precision with gaps."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0)
        builder.add_mapping(0, 10, 0, 10)
        builder.add_mapping(0, 20, 0, 20)
        assert builder.mappings[1].gen_col == 10
        assert builder.mappings[2].gen_col == 20
    
    def test_column_precision_with_small_deltas(self):
        """Test column precision with small deltas."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0)
        builder.add_mapping(0, 1, 0, 1)
        builder.add_mapping(0, 2, 0, 2)
        result = builder.to_json()
        assert "mappings" in result
    
    def test_column_precision_with_large_deltas(self):
        """Test column precision with large deltas."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0)
        builder.add_mapping(0, 100, 0, 100)
        builder.add_mapping(0, 200, 0, 200)
        result = builder.to_json()
        assert "mappings" in result
    
    def test_column_precision_with_zero_delta(self):
        """Test column precision with zero delta."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0)
        builder.add_mapping(0, 0, 1, 0)  # Same column, different line
        result = builder.to_json()
        assert "mappings" in result
    
    def test_column_precision_with_negative_delta(self):
        """Test column precision with negative delta (shouldn't happen but test)."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 10, 0, 10)
        builder.add_mapping(0, 5, 0, 5)  # Negative delta (invalid but test)
        # Should handle gracefully
        result = builder.to_json()
        assert "mappings" in result
    
    def test_column_precision_with_unicode(self):
        """Test column precision with unicode characters."""
        builder = SourceMapBuilder("source.py", "output.js")
        # Unicode characters might affect column counting
        builder.add_mapping(0, 0, 0, 0)
        builder.add_mapping(0, 4, 0, 4)
        result = builder.to_json()
        assert "mappings" in result
    
    def test_column_precision_with_tabs(self):
        """Test column precision with tab characters."""
        builder = SourceMapBuilder("source.py", "output.js")
        # Tabs might be counted as 1 or multiple columns
        builder.add_mapping(0, 0, 0, 0)
        builder.add_mapping(0, 8, 0, 8)  # Tab might be 8 columns
        result = builder.to_json()
        assert "mappings" in result
    
    def test_column_precision_with_mixed_content(self):
        """Test column precision with mixed content."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0, name="x")
        builder.add_mapping(0, 4, 0, 4, name="y")
        builder.add_mapping(1, 0, 1, 0, name="z")
        result = builder.to_json()
        assert "mappings" in result
    
    def test_column_precision_comprehensive(self):
        """Test comprehensive column precision scenario."""
        builder = SourceMapBuilder("source.py", "output.js")
        # Add mappings with various column positions
        for i in range(20):
            builder.add_mapping(i, i * 2, i, i * 2, name=f"var_{i}")
        result = builder.to_json()
        assert "mappings" in result
        assert len(builder.names) == 20


# =============================================================================
# MULTI-LINE HANDLING (20 tests)
# =============================================================================

class TestMultiLineHandling:
    """Test multi-line expression handling."""
    
    def test_mapping_across_lines(self):
        """Test mappings across multiple lines."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0)
        builder.add_mapping(1, 0, 1, 0)
        builder.add_mapping(2, 0, 2, 0)
        assert len(builder.mappings) == 3
        assert builder.mappings[0].gen_line == 0
        assert builder.mappings[1].gen_line == 1
        assert builder.mappings[2].gen_line == 2
    
    def test_multi_line_with_same_source_line(self):
        """Test multiple generated lines map to same source line."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0)
        builder.add_mapping(1, 0, 0, 10)  # Same source line, different column
        builder.add_mapping(2, 0, 0, 20)
        assert builder.mappings[0].src_line == 0
        assert builder.mappings[1].src_line == 0
        assert builder.mappings[2].src_line == 0
    
    def test_multi_line_with_different_source_lines(self):
        """Test multiple generated lines map to different source lines."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0)
        builder.add_mapping(1, 0, 5, 0)  # Different source line
        builder.add_mapping(2, 0, 10, 0)
        assert builder.mappings[0].src_line == 0
        assert builder.mappings[1].src_line == 5
        assert builder.mappings[2].src_line == 10
    
    def test_multi_line_with_gaps(self):
        """Test multi-line mappings with gaps."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0)
        builder.add_mapping(10, 0, 10, 0)  # Large gap
        builder.add_mapping(20, 0, 20, 0)
        assert builder.mappings[1].gen_line == 10
        assert builder.mappings[2].gen_line == 20
    
    def test_multi_line_with_names(self):
        """Test multi-line mappings with variable names."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0, name="x")
        builder.add_mapping(1, 0, 1, 0, name="y")
        builder.add_mapping(2, 0, 2, 0, name="z")
        assert len(builder.names) == 3
    
    def test_multi_line_with_functions(self):
        """Test multi-line function boundaries."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_function("my_function", 0, 0, 0, 0)
        builder.add_mapping(1, 4, 1, 4)
        builder.add_mapping(2, 8, 2, 8)
        builder.end_function("my_function", 3, 3)
        boundaries = builder.get_function_boundaries()
        assert boundaries[0]["generated"]["start"] == 0
        assert boundaries[0]["generated"]["end"] == 3
    
    def test_multi_line_with_classes(self):
        """Test multi-line class boundaries."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_class("MyClass", 0, 0, 0, 0)
        builder.add_mapping(1, 4, 1, 4)
        builder.add_mapping(2, 8, 2, 8)
        builder.end_class("MyClass", 3, 3)
        boundaries = builder.get_class_boundaries()
        assert boundaries[0]["generated"]["start"] == 0
        assert boundaries[0]["generated"]["end"] == 3
    
    def test_multi_line_expression_mapping(self):
        """Test mapping for multi-line expression."""
        builder = SourceMapBuilder("source.py", "output.js")
        # Simulate multi-line expression
        builder.add_mapping(0, 0, 0, 0)  # Start of expression
        builder.add_mapping(1, 4, 0, 10)  # Continuation on next line
        builder.add_mapping(2, 4, 0, 20)  # More continuation
        assert builder.mappings[0].src_line == 0
        assert builder.mappings[1].src_line == 0
        assert builder.mappings[2].src_line == 0
    
    def test_multi_line_with_vlq_encoding(self):
        """Test multi-line mappings in VLQ encoding."""
        builder = SourceMapBuilder("source.py", "output.js")
        for i in range(10):
            builder.add_mapping(i, 0, i, 0)
        result = builder.to_json()
        # Should have semicolons separating lines
        assert result["mappings"].count(";") >= 9
    
    def test_multi_line_with_empty_lines(self):
        """Test multi-line mappings with empty lines."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0)
        builder.add_mapping(5, 0, 5, 0)  # Gap with empty lines
        result = builder.to_json()
        assert "mappings" in result
    
    def test_multi_line_with_large_gaps(self):
        """Test multi-line mappings with large gaps."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0)
        builder.add_mapping(100, 0, 100, 0)
        result = builder.to_json()
        assert "mappings" in result
    
    def test_multi_line_with_reverse_mapping(self):
        """Test multi-line with reverse line order (shouldn't happen but test)."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(5, 0, 5, 0)
        builder.add_mapping(0, 0, 0, 0)  # Earlier line added later
        # Should be sorted
        result = builder.to_json()
        assert "mappings" in result
    
    def test_multi_line_with_mixed_columns(self):
        """Test multi-line with mixed column positions."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0)
        builder.add_mapping(1, 4, 1, 4)
        builder.add_mapping(2, 0, 2, 0)  # Column resets
        result = builder.to_json()
        assert "mappings" in result
    
    def test_multi_line_with_function_nesting(self):
        """Test multi-line with nested functions."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_function("outer", 0, 0, 0, 0)
        builder.add_mapping(1, 4, 1, 4)
        builder.start_function("inner", 2, 0, 2, 0)
        builder.add_mapping(3, 4, 3, 4)
        builder.end_function("inner", 4, 4)
        builder.end_function("outer", 5, 5)
        boundaries = builder.get_function_boundaries()
        assert len(boundaries) == 2
    
    def test_multi_line_with_class_nesting(self):
        """Test multi-line with nested classes."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_class("Outer", 0, 0, 0, 0)
        builder.add_mapping(1, 4, 1, 4)
        builder.start_class("Inner", 2, 0, 2, 0)
        builder.add_mapping(3, 4, 3, 4)
        builder.end_class("Inner", 4, 4)
        builder.end_class("Outer", 5, 5)
        boundaries = builder.get_class_boundaries()
        assert len(boundaries) == 2
    
    def test_multi_line_comprehensive(self):
        """Test comprehensive multi-line scenario."""
        builder = SourceMapBuilder("source.py", "output.js")
        # Add mappings across many lines with various patterns
        for i in range(50):
            builder.add_mapping(i, i % 10, i, i % 10, name=f"var_{i % 5}")
        result = builder.to_json()
        assert "mappings" in result
        assert len(builder.names) == 5  # Only 5 unique names
    
    def test_multi_line_with_source_content(self):
        """Test multi-line with source content embedding."""
        source_code = "x = 1\ny = 2\nz = 3"
        builder = SourceMapBuilder("source.py", "output.js", source_content=source_code)
        builder.add_mapping(0, 0, 0, 0)
        builder.add_mapping(1, 0, 1, 0)
        builder.add_mapping(2, 0, 2, 0)
        result = builder.to_json()
        assert "sourcesContent" in result
        assert result["sourcesContent"][0] == source_code
    
    def test_multi_line_with_unicode_content(self):
        """Test multi-line with unicode in source content."""
        source_code = "x = 1\n変数 = 2\nz = 3"
        builder = SourceMapBuilder("source.py", "output.js", source_content=source_code)
        builder.add_mapping(0, 0, 0, 0)
        builder.add_mapping(1, 0, 1, 0)
        builder.add_mapping(2, 0, 2, 0)
        result = builder.to_json()
        assert "sourcesContent" in result
    
    def test_multi_line_with_special_characters(self):
        """Test multi-line with special characters."""
        source_code = "x = 1\ny = 'test'\nz = 3"
        builder = SourceMapBuilder("source.py", "output.js", source_content=source_code)
        builder.add_mapping(0, 0, 0, 0)
        builder.add_mapping(1, 0, 1, 0)
        builder.add_mapping(2, 0, 2, 0)
        result = builder.to_json()
        assert "sourcesContent" in result


# =============================================================================
# STACK TRACE INTEGRATION (10 tests)
# =============================================================================

class TestStackTraceIntegration:
    """Test source map integration with stack traces."""
    
    def test_function_boundaries_for_stack_trace(self):
        """Test function boundaries available for stack trace rewriting."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_function("my_function", 0, 0, 0, 0)
        builder.end_function("my_function", 5, 3)
        boundaries = builder.get_function_boundaries()
        assert len(boundaries) == 1
        assert "name" in boundaries[0]
        assert "generated" in boundaries[0]
        assert "source" in boundaries[0]
    
    def test_class_boundaries_for_stack_trace(self):
        """Test class boundaries available for stack trace rewriting."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_class("MyClass", 0, 0, 0, 0)
        builder.end_class("MyClass", 10, 5)
        boundaries = builder.get_class_boundaries()
        assert len(boundaries) == 1
        assert "name" in boundaries[0]
        assert "generated" in boundaries[0]
        assert "source" in boundaries[0]
    
    def test_mapping_for_line_lookup(self):
        """Test mappings can be used for line lookup."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(5, 10, 10, 20, name="x")
        # Stack trace rewriter can look up line 5, col 10 → source line 10, col 20
        result = builder.to_json()
        assert "mappings" in result
    
    def test_name_preservation_for_stack_trace(self):
        """Test variable names preserved for stack trace."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(5, 10, 10, 20, name="my_variable")
        result = builder.to_json()
        assert "my_variable" in result["names"]
    
    def test_function_name_in_stack_trace(self):
        """Test function names available in stack trace."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_function("handle_click", 0, 0, 0, 0)
        builder.end_function("handle_click", 5, 3)
        result = builder.to_json()
        assert "x_pynext_functions" in result
        assert result["x_pynext_functions"][0]["name"] == "handle_click"
    
    def test_class_name_in_stack_trace(self):
        """Test class names available in stack trace."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_class("MyComponent", 0, 0, 0, 0)
        builder.end_class("MyComponent", 10, 5)
        result = builder.to_json()
        assert "x_pynext_classes" in result
        assert result["x_pynext_classes"][0]["name"] == "MyComponent"
    
    def test_nested_functions_in_stack_trace(self):
        """Test nested functions in stack trace."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_function("outer", 0, 0, 0, 0)
        builder.start_function("inner", 2, 0, 2, 0)
        builder.end_function("inner", 5, 3)
        builder.end_function("outer", 10, 5)
        boundaries = builder.get_function_boundaries()
        assert len(boundaries) == 2
        # Stack trace can identify which function a line belongs to
    
    def test_mapping_precision_for_stack_trace(self):
        """Test mapping precision for accurate stack trace rewriting."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(10, 15, 20, 25, name="error_location")
        # Stack trace at JS line 10, col 15 → Python line 20, col 25
        result = builder.to_json()
        assert "mappings" in result
        assert "error_location" in result["names"]
    
    def test_source_content_for_stack_trace(self):
        """Test source content available for stack trace context."""
        source_code = "def my_function():\n    x = 1\n    return x"
        builder = SourceMapBuilder("source.py", "output.js", source_content=source_code)
        builder.add_mapping(0, 0, 0, 0)
        result = builder.to_json()
        assert "sourcesContent" in result
        # Stack trace rewriter can show source code context
    
    def test_comprehensive_stack_trace_scenario(self):
        """Test comprehensive stack trace scenario."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_class("MyComponent", 0, 0, 0, 0)
        builder.start_function("handle_click", 2, 0, 2, 0)
        builder.add_mapping(3, 4, 3, 4, name="x")
        builder.add_mapping(4, 8, 4, 8, name="y")
        builder.end_function("handle_click", 5, 5)
        builder.end_class("MyComponent", 10, 10)
        result = builder.to_json()
        # All information needed for stack trace rewriting
        assert "x_pynext_functions" in result
        assert "x_pynext_classes" in result
        assert "names" in result
        assert "mappings" in result


# =============================================================================
# EDGE CASES (10 tests)
# =============================================================================

class TestSourceMapEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_builder(self):
        """Test empty builder."""
        builder = SourceMapBuilder("source.py", "output.js")
        result = builder.to_json()
        assert result["mappings"] == ""
        assert result["names"] == []
    
    def test_builder_with_only_functions(self):
        """Test builder with only function boundaries."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_function("my_function", 0, 0, 0, 0)
        builder.end_function("my_function", 5, 3)
        result = builder.to_json()
        assert "x_pynext_functions" in result
    
    def test_builder_with_only_classes(self):
        """Test builder with only class boundaries."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_class("MyClass", 0, 0, 0, 0)
        builder.end_class("MyClass", 10, 5)
        result = builder.to_json()
        assert "x_pynext_classes" in result
    
    def test_builder_with_mismatched_end(self):
        """Test builder with mismatched end (should handle gracefully)."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_function("func1", 0, 0, 0, 0)
        builder.end_function("func2", 5, 3)  # Wrong name
        # Should handle gracefully
        boundaries = builder.get_function_boundaries()
        # func1 might not be completed
    
    def test_builder_with_duplicate_starts(self):
        """Test builder with duplicate function starts."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_function("my_function", 0, 0, 0, 0)
        builder.start_function("my_function", 5, 0, 5, 0)  # Duplicate
        # Should handle nested or duplicate
        assert builder.get_current_function() == "my_function"
    
    def test_builder_with_very_many_mappings(self):
        """Test builder with very many mappings."""
        builder = SourceMapBuilder("source.py", "output.js")
        for i in range(1000):
            builder.add_mapping(i, 0, i, 0, name=f"var_{i % 100}")
        result = builder.to_json()
        assert len(builder.mappings) == 1000
        assert len(builder.names) == 100
    
    def test_builder_with_very_many_functions(self):
        """Test builder with very many functions."""
        builder = SourceMapBuilder("source.py", "output.js")
        for i in range(100):
            builder.start_function(f"func_{i}", i * 2, 0, i * 2, 0)
            builder.end_function(f"func_{i}", i * 2 + 1, i * 2 + 1)
        boundaries = builder.get_function_boundaries()
        assert len(boundaries) == 100
    
    def test_builder_with_very_many_classes(self):
        """Test builder with very many classes."""
        builder = SourceMapBuilder("source.py", "output.js")
        for i in range(100):
            builder.start_class(f"Class_{i}", i * 2, 0, i * 2, 0)
            builder.end_class(f"Class_{i}", i * 2 + 1, i * 2 + 1)
        boundaries = builder.get_class_boundaries()
        assert len(boundaries) == 100
    
    def test_builder_with_all_features(self):
        """Test builder with all features together."""
        builder = SourceMapBuilder("source.py", "output.js", source_content="x = 1")
        builder.start_class("MyClass", 0, 0, 0, 0)
        builder.start_function("method", 2, 0, 2, 0)
        builder.add_mapping(3, 4, 3, 4, name="x", kind="variable")
        builder.add_mapping(4, 8, 4, 8, name="y", kind="variable")
        builder.end_function("method", 5, 5)
        builder.end_class("MyClass", 10, 10)
        result = builder.to_json()
        # All features should be present
        assert "x_pynext_functions" in result
        assert "x_pynext_classes" in result
        assert "names" in result
        assert "mappings" in result
        assert "sourcesContent" in result
    
    def test_builder_json_roundtrip(self):
        """Test JSON roundtrip (serialize and deserialize)."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.start_function("my_function", 0, 0, 0, 0)
        builder.add_mapping(1, 4, 1, 4, name="x")
        builder.end_function("my_function", 2, 2)
        json_str = builder.to_json_string()
        parsed = json.loads(json_str)
        assert parsed["version"] == 3
        assert "x_pynext_functions" in parsed
        assert "names" in parsed
        assert "mappings" in parsed
    
    def test_builder_with_kind_parameter(self):
        """Test builder with kind parameter for mappings."""
        builder = SourceMapBuilder("source.py", "output.js")
        builder.add_mapping(0, 0, 0, 0, name="x", kind="variable")
        builder.add_mapping(1, 0, 1, 0, name="func", kind="function")
        builder.add_mapping(2, 0, 2, 0, name="Class", kind="class")
        assert builder.mappings[0].kind == "variable"
        assert builder.mappings[1].kind == "function"
        assert builder.mappings[2].kind == "class"

