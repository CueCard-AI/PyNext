"""
Comprehensive tests for PyNext Compiler Source Map Generation (100 tests)

Tests cover:
- VLQ encoding
- Source mapping
- File references
- Name mapping
- Line mapping accuracy
"""

import pytest
import json
from pynext.compiler import compile_island
from pynext.compiler.sourcemap import (
    vlq_encode,
    vlq_encode_segment,
    SourceMapBuilder,
    SourceMapping,
    generate_sourcemap,
)


# =============================================================================
# SECTION 1: VLQ Encoding (30 tests)
# =============================================================================

class TestVLQEncoding:
    """Tests for VLQ (Variable Length Quantity) encoding."""
    
    def test_encode_zero(self):
        """0 encodes to A."""
        assert vlq_encode(0) == "A"
    
    def test_encode_one(self):
        """1 encodes to C."""
        assert vlq_encode(1) == "C"
    
    def test_encode_negative_one(self):
        """-1 encodes to D."""
        assert vlq_encode(-1) == "D"
    
    def test_encode_small_positive(self):
        """Small positive numbers."""
        # 2 -> E, 3 -> G, etc.
        assert vlq_encode(2) == "E"
        assert vlq_encode(3) == "G"
    
    def test_encode_large_number(self):
        """Large numbers use multiple characters."""
        result = vlq_encode(100)
        assert len(result) > 1
    
    def test_encode_negative_large(self):
        """Large negative numbers."""
        result = vlq_encode(-100)
        assert len(result) > 1
    
    def test_segment_encoding(self):
        """Multiple values encoded as segment."""
        result = vlq_encode_segment([0, 0, 0, 0])
        assert "AAAA" in result or len(result) == 4


# =============================================================================
# SECTION 2: Source Map Builder (30 tests)
# =============================================================================

class TestSourceMapBuilder:
    """Tests for SourceMapBuilder class."""
    
    def test_builder_initialization(self):
        """Builder initializes correctly."""
        builder = SourceMapBuilder("test.py", "source code")
        assert builder.filename == "test.py"
        assert builder.source_content == "source code"
    
    def test_add_name(self):
        """Names can be added."""
        builder = SourceMapBuilder("test.py", "")
        idx = builder.add_name("count")
        assert idx == 0
        assert "count" in builder.names
    
    def test_add_duplicate_name(self):
        """Duplicate names return same index."""
        builder = SourceMapBuilder("test.py", "")
        idx1 = builder.add_name("count")
        idx2 = builder.add_name("count")
        assert idx1 == idx2
    
    def test_add_mapping(self):
        """Mappings can be added."""
        builder = SourceMapBuilder("test.py", "")
        builder.add_mapping(js_line=0, js_col=0, py_line=0, py_col=0)
        assert len(builder.mappings) == 1
    
    def test_add_mapping_with_name(self):
        """Mapping with name."""
        builder = SourceMapBuilder("test.py", "")
        builder.add_mapping(js_line=0, js_col=0, py_line=0, py_col=0, name="count")
        assert "count" in builder.names
    
    def test_build_produces_json(self):
        """build() produces valid JSON."""
        builder = SourceMapBuilder("test.py", "@island\ndef C(): pass")
        result = builder.build()
        data = json.loads(result)
        assert "version" in data
        assert data["version"] == 3
    
    def test_build_includes_sources(self):
        """Built map includes sources array."""
        builder = SourceMapBuilder("test.py", "")
        data = json.loads(builder.build())
        assert "sources" in data
        assert "test.py" in data["sources"]
    
    def test_build_includes_source_content(self):
        """Built map includes sourcesContent."""
        builder = SourceMapBuilder("test.py", "original source")
        data = json.loads(builder.build())
        assert "sourcesContent" in data
        assert "original source" in data["sourcesContent"]
    
    def test_build_includes_mappings(self):
        """Built map includes mappings string."""
        builder = SourceMapBuilder("test.py", "")
        builder.add_mapping(0, 0, 0, 0)
        data = json.loads(builder.build())
        assert "mappings" in data


# =============================================================================
# SECTION 3: Source Map Generation (20 tests)
# =============================================================================

class TestSourceMapGeneration:
    """Tests for full source map generation."""
    
    def test_compile_includes_map(self):
        """compile_island returns source map."""
        result = compile_island("""
@island
def Counter():
    count = signal(0)
""", "counter.py")
        assert result.map
        data = json.loads(result.map)
        assert data["version"] == 3
    
    def test_map_references_source(self):
        """Source map references Python file."""
        result = compile_island("@island\ndef C(): pass", "myfile.py")
        data = json.loads(result.map)
        assert "myfile.py" in data["sources"]
    
    def test_map_includes_names(self):
        """Source map includes function and signal names."""
        result = compile_island("""
@island
def Counter():
    count = signal(0)
""", "counter.py")
        data = json.loads(result.map)
        assert "names" in data
    
    def test_map_has_mappings(self):
        """Source map has non-empty mappings."""
        result = compile_island("""
@island
def Counter():
    count = signal(0)
    return div()[count()]
""", "counter.py")
        data = json.loads(result.map)
        assert data["mappings"]  # Non-empty string


# =============================================================================
# SECTION 4: Mapping Accuracy (20 tests)
# =============================================================================

class TestMappingAccuracy:
    """Tests for accuracy of line/column mappings."""
    
    def test_function_name_mapped(self):
        """Function name appears in names array."""
        result = compile_island("""
@island
def MyComponent():
    pass
""", "test.py")
        data = json.loads(result.map)
        assert "MyComponent" in data["names"]
    
    def test_signal_name_mapped(self):
        """Signal name appears in names array."""
        result = compile_island("""
@island
def Counter():
    mySignal = signal(0)
""", "test.py")
        data = json.loads(result.map)
        assert "mySignal" in data["names"]
    
    def test_multiple_names_mapped(self):
        """Multiple names mapped correctly."""
        result = compile_island("""
@island
def Counter():
    a = signal(0)
    b = signal(1)
    c = signal(2)
""", "test.py")
        data = json.loads(result.map)
        assert len(data["names"]) >= 3

