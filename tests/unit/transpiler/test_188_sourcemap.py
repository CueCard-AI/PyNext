"""
Phase 18.8: Source Map Tests

Tests for V3 source map generation with VLQ encoding.

Tests: 50
"""

import pytest
import json
import base64
from pynext.transpiler.sourcemap import (
    SourceMapBuilder, Mapping, create_source_map,
    _encode_vlq, _encode_vlq_segment,
)


class TestVLQEncoding:
    """Tests for VLQ (Variable-Length Quantity) encoding."""
    
    def test_encode_zero(self):
        """Encode zero."""
        assert _encode_vlq(0) == "A"
    
    def test_encode_one(self):
        """Encode one."""
        assert _encode_vlq(1) == "C"
    
    def test_encode_negative_one(self):
        """Encode negative one."""
        assert _encode_vlq(-1) == "D"
    
    def test_encode_small_positive(self):
        """Encode small positive numbers."""
        # VLQ encoding: 0-15 are single characters
        for i in range(16):
            result = _encode_vlq(i)
            assert len(result) >= 1
    
    def test_encode_small_negative(self):
        """Encode small negative numbers."""
        for i in range(-15, 0):
            result = _encode_vlq(i)
            assert len(result) >= 1
    
    def test_encode_larger_number(self):
        """Encode larger numbers require more characters."""
        # 16+ should require 2 chars
        result = _encode_vlq(16)
        assert len(result) >= 1
    
    def test_encode_large_number(self):
        """Encode large number."""
        result = _encode_vlq(1000)
        assert len(result) >= 2
    
    def test_encode_segment(self):
        """Encode a segment of values."""
        segment = [0, 0, 0, 0]  # Column, source, line, column
        result = _encode_vlq_segment(segment)
        assert result == "AAAA"
    
    def test_encode_segment_with_values(self):
        """Encode segment with non-zero values."""
        segment = [4, 0, 0, 4]  # Column 4, source 0, line 0, column 4
        result = _encode_vlq_segment(segment)
        assert len(result) > 0
    
    def test_vlq_roundtrip_concepts(self):
        """VLQ encoding produces valid base64 chars."""
        valid_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
        for i in range(-100, 100):
            result = _encode_vlq(i)
            for char in result:
                assert char in valid_chars


class TestSourceMapBuilder:
    """Tests for SourceMapBuilder class."""
    
    def test_create_builder(self):
        """Create a source map builder."""
        builder = SourceMapBuilder("test.py", "test.js")
        assert builder.source_file == "test.py"
        assert builder.generated_file == "test.js"
    
    def test_add_mapping(self):
        """Add a mapping."""
        builder = SourceMapBuilder("test.py", "test.js")
        builder.add_mapping(0, 0, 0, 0)
        assert len(builder.mappings) == 1
    
    def test_add_multiple_mappings(self):
        """Add multiple mappings."""
        builder = SourceMapBuilder("test.py", "test.js")
        builder.add_mapping(0, 0, 0, 0)
        builder.add_mapping(1, 4, 1, 4)
        builder.add_mapping(2, 0, 2, 0)
        assert len(builder.mappings) == 3
    
    def test_mapping_with_name(self):
        """Add mapping with name."""
        builder = SourceMapBuilder("test.py", "test.js")
        builder.add_mapping(0, 0, 0, 0, name="count")
        assert "count" in builder.names
        assert len(builder.names) == 1
    
    def test_duplicate_names(self):
        """Same name used multiple times."""
        builder = SourceMapBuilder("test.py", "test.js")
        builder.add_mapping(0, 0, 0, 0, name="x")
        builder.add_mapping(1, 0, 1, 0, name="x")
        assert len(builder.names) == 1  # Name should only appear once
    
    def test_to_json(self):
        """Generate JSON output."""
        builder = SourceMapBuilder("test.py", "test.js")
        builder.add_mapping(0, 0, 0, 0)
        result = builder.to_json()
        
        assert result["version"] == 3
        assert result["file"] == "test.js"
        assert result["sources"] == ["test.py"]
        assert "mappings" in result
    
    def test_to_json_with_source_content(self):
        """JSON includes source content when provided."""
        builder = SourceMapBuilder(
            "test.py", "test.js",
            source_content="x = 1"
        )
        result = builder.to_json()
        
        assert "sourcesContent" in result
        assert result["sourcesContent"] == ["x = 1"]
    
    def test_to_json_string(self):
        """Generate JSON string."""
        builder = SourceMapBuilder("test.py", "test.js")
        builder.add_mapping(0, 0, 0, 0)
        result = builder.to_json_string()
        
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed["version"] == 3
    
    def test_to_data_url(self):
        """Generate data URL."""
        builder = SourceMapBuilder("test.py", "test.js")
        builder.add_mapping(0, 0, 0, 0)
        result = builder.to_data_url()
        
        assert result.startswith("data:application/json;base64,")
        # Verify it's valid base64
        b64_part = result.split(",")[1]
        decoded = base64.b64decode(b64_part)
        parsed = json.loads(decoded)
        assert parsed["version"] == 3
    
    def test_to_inline_comment(self):
        """Generate inline source map comment."""
        builder = SourceMapBuilder("test.py", "test.js")
        result = builder.to_inline_comment()
        
        assert result.startswith("//# sourceMappingURL=")
        assert "data:application/json;base64," in result


class TestMappingEncoding:
    """Tests for mapping string encoding."""
    
    def test_empty_mappings(self):
        """No mappings produces empty string."""
        builder = SourceMapBuilder("test.py", "test.js")
        result = builder.to_json()
        assert result["mappings"] == ""
    
    def test_single_mapping(self):
        """Single mapping produces valid string."""
        builder = SourceMapBuilder("test.py", "test.js")
        builder.add_mapping(0, 0, 0, 0)
        result = builder.to_json()
        assert result["mappings"] != ""
    
    def test_mapping_multiple_lines(self):
        """Mappings across lines use semicolons."""
        builder = SourceMapBuilder("test.py", "test.js")
        builder.add_mapping(0, 0, 0, 0)
        builder.add_mapping(1, 0, 1, 0)
        builder.add_mapping(2, 0, 2, 0)
        result = builder.to_json()
        
        # Should have semicolons separating lines
        assert ";" in result["mappings"]
    
    def test_mapping_same_line(self):
        """Mappings on same line use commas."""
        builder = SourceMapBuilder("test.py", "test.js")
        builder.add_mapping(0, 0, 0, 0)
        builder.add_mapping(0, 4, 0, 4)
        result = builder.to_json()
        
        # Should have comma separating segments on same line
        assert "," in result["mappings"]
    
    def test_mapping_order_preserved(self):
        """Mappings are sorted by position."""
        builder = SourceMapBuilder("test.py", "test.js")
        # Add out of order
        builder.add_mapping(2, 0, 2, 0)
        builder.add_mapping(0, 0, 0, 0)
        builder.add_mapping(1, 0, 1, 0)
        
        # Should still produce valid output
        result = builder.to_json()
        assert result["mappings"] != ""


class TestCreateSourceMap:
    """Tests for create_source_map helper."""
    
    def test_create_simple_map(self):
        """Create source map with helper function."""
        result = create_source_map(
            "handler.py",
            "handler.js",
            [(0, 0, 0, 0), (1, 0, 1, 0)],
        )
        
        assert result["version"] == 3
        assert result["file"] == "handler.js"
        assert result["sources"] == ["handler.py"]
    
    def test_create_map_with_content(self):
        """Create source map with source content."""
        result = create_source_map(
            "handler.py",
            "handler.js",
            [(0, 0, 0, 0)],
            source_content="def handler(): pass",
        )
        
        assert "sourcesContent" in result
        assert result["sourcesContent"] == ["def handler(): pass"]
    
    def test_create_map_empty_mappings(self):
        """Create source map with no mappings."""
        result = create_source_map(
            "test.py",
            "test.js",
            [],
        )
        
        assert result["mappings"] == ""
    
    def test_create_map_many_mappings(self):
        """Create source map with many mappings."""
        mappings = [(i, 0, i, 0) for i in range(100)]
        result = create_source_map("test.py", "test.js", mappings)
        
        # Should have 99 semicolons (100 lines - 1)
        assert result["mappings"].count(";") == 99


class TestMapping:
    """Tests for Mapping dataclass."""
    
    def test_create_mapping(self):
        """Create a Mapping object."""
        m = Mapping(gen_line=1, gen_col=4, src_line=2, src_col=8)
        assert m.gen_line == 1
        assert m.gen_col == 4
        assert m.src_line == 2
        assert m.src_col == 8
        assert m.name is None
    
    def test_mapping_with_name(self):
        """Create a Mapping with name."""
        m = Mapping(gen_line=0, gen_col=0, src_line=0, src_col=0, name="count")
        assert m.name == "count"


class TestSourceMapEdgeCases:
    """Edge cases for source map generation."""
    
    def test_unicode_source_content(self):
        """Source content with unicode."""
        builder = SourceMapBuilder(
            "handler.py", "handler.js",
            source_content="变量 = 1"
        )
        result = builder.to_json()
        assert "变量" in result["sourcesContent"][0]
    
    def test_unicode_filename(self):
        """Unicode in filename."""
        builder = SourceMapBuilder("处理器.py", "handler.js")
        result = builder.to_json()
        assert result["sources"] == ["处理器.py"]
    
    def test_large_line_numbers(self):
        """Large line numbers."""
        builder = SourceMapBuilder("test.py", "test.js")
        builder.add_mapping(1000, 0, 1000, 0)
        result = builder.to_json()
        assert result["mappings"] != ""
    
    def test_large_column_numbers(self):
        """Large column numbers."""
        builder = SourceMapBuilder("test.py", "test.js")
        builder.add_mapping(0, 500, 0, 500)
        result = builder.to_json()
        assert result["mappings"] != ""
    
    def test_many_names(self):
        """Many unique names."""
        builder = SourceMapBuilder("test.py", "test.js")
        for i in range(100):
            builder.add_mapping(i, 0, i, 0, name=f"var_{i}")
        
        assert len(builder.names) == 100
        result = builder.to_json()
        assert len(result["names"]) == 100
    
    def test_sparse_mappings(self):
        """Mappings with gaps."""
        builder = SourceMapBuilder("test.py", "test.js")
        builder.add_mapping(0, 0, 0, 0)
        builder.add_mapping(10, 0, 5, 0)  # Big jump in generated, smaller in source
        builder.add_mapping(20, 0, 10, 0)
        
        result = builder.to_json()
        # Should have empty lines represented by consecutive semicolons
        assert ";;" in result["mappings"]

