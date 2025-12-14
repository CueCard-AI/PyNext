"""
PyNext Compiler - Source Map Generator

=============================================================================
WHAT THIS FILE DOES
=============================================================================

This file generates V3 source maps that link compiled JavaScript back to the
original Python source code. This enables:

1. Setting breakpoints in Python code while debugging in browser DevTools
2. Seeing Python line numbers in error stack traces
3. Stepping through Python code in the debugger

Example:
    When you see an error at line 5 of the compiled JS, the source map
    tells the browser "this corresponds to line 12 of counter.py"

=============================================================================
WHY THIS EXISTS (Problem It Solves)
=============================================================================

When Python is compiled to JavaScript, the resulting code looks nothing like
the original. Without source maps:

    - Error messages show JavaScript line numbers (useless!)
    - You can't set breakpoints in your Python code
    - Debugging becomes a nightmare

With source maps:

    - Browser DevTools show Python file in Sources panel
    - Breakpoints work on Python lines
    - Stack traces show Python file:line
    - Variable names from Python are preserved

=============================================================================
HOW IT WORKS (Architecture)
=============================================================================

    IslandIR + Compiled JS
            │
            ▼
    ┌───────────────────────────────────────────────────────────────────────┐
    │                                                                        │
    │  Source Map V3 Format:                                                 │
    │  {                                                                     │
    │    "version": 3,                                                       │
    │    "file": "counter.js",                                               │
    │    "sources": ["counter.py"],                                          │
    │    "sourcesContent": ["@island\ndef Counter():\n..."],                │
    │    "names": ["count", "signal", ...],                                 │
    │    "mappings": "AAAA,IAAI;AACJ,..."                                   │
    │  }                                                                     │
    │                                                                        │
    │  Mappings use VLQ-encoded segments:                                    │
    │    "AAAA" = (col 0, source 0, line 0, col 0)                          │
    │    "IAAI" = (col 4, source 0, line 0, col 4)                          │
    │                                                                        │
    └───────────────────────────────────────────────────────────────────────┘

=============================================================================
WHO USES THIS
=============================================================================

- __init__.py: Called after emit_javascript()
- Build system: Writes .map files alongside .js files
- Browser DevTools: Reads source maps for debugging

=============================================================================
WHEN TO USE (vs Alternatives)
=============================================================================

Always generated as part of compile_island(). Source maps are:
- Required for development (debugging)
- Optional for production (can be stripped or hosted separately)

=============================================================================
COMPILATION (Input → Output)
=============================================================================

INPUT:
- IslandIR with source line information
- Compiled JavaScript string
- Original filename

OUTPUT (JSON):
```json
{
    "version": 3,
    "file": "counter.js",
    "sources": ["counter.py"],
    "sourcesContent": ["@island\\ndef Counter():\\n    count = signal(0)\\n..."],
    "names": ["Counter", "count", "signal"],
    "mappings": "AAAA;AACA,IAAI,KAAK,GAAG,YAAY,CAAC,CAAC,CAAC;AAC3B,..."
}
```
=============================================================================
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

from .parser import IslandIR, DOMNode


# =============================================================================
# VLQ ENCODING
# =============================================================================
#
# Source maps use Variable Length Quantity (VLQ) encoding for compact
# representation of line/column mappings.
#
# Each VLQ value is a series of Base64 characters where:
# - Each character represents 6 bits
# - Bit 5 (0x20) indicates continuation
# - For signed values, bit 0 is the sign bit
#
# Characters: ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/

VLQ_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
VLQ_SHIFT = 5
VLQ_CONTINUATION = 1 << VLQ_SHIFT
VLQ_MASK = VLQ_CONTINUATION - 1


def vlq_encode(value: int) -> str:
    """
    Encode a single integer as VLQ.
    
    Args:
        value: Integer to encode (can be negative)
    
    Returns:
        VLQ-encoded string
    
    Example:
        >>> vlq_encode(0)
        'A'
        >>> vlq_encode(1)
        'C'
        >>> vlq_encode(-1)
        'D'
    """
    # Convert to unsigned with sign in LSB
    if value < 0:
        value = ((-value) << 1) | 1
    else:
        value = value << 1
    
    result = []
    while True:
        digit = value & VLQ_MASK
        value >>= VLQ_SHIFT
        
        if value > 0:
            digit |= VLQ_CONTINUATION
        
        result.append(VLQ_CHARS[digit])
        
        if value == 0:
            break
    
    return "".join(result)


def vlq_encode_segment(values: List[int]) -> str:
    """
    Encode a segment (multiple values) as VLQ.
    
    Args:
        values: List of integers to encode
    
    Returns:
        VLQ-encoded string for the segment
    """
    return "".join(vlq_encode(v) for v in values)


# =============================================================================
# MAPPING BUILDER
# =============================================================================

@dataclass
class SourceMapping:
    """
    A single source mapping.
    
    Attributes:
        js_line: Line in generated JavaScript (0-indexed)
        js_col: Column in generated JavaScript (0-indexed)
        py_line: Line in Python source (0-indexed)
        py_col: Column in Python source (0-indexed)
        name_index: Index into names array (optional)
    """
    js_line: int
    js_col: int
    py_line: int
    py_col: int
    name_index: Optional[int] = None


@dataclass
class SourceMapBuilder:
    """
    Builds a V3 source map incrementally.
    
    Usage:
        builder = SourceMapBuilder("counter.py", source_content)
        builder.add_name("count")
        builder.add_mapping(js_line=2, js_col=6, py_line=3, py_col=4, name="count")
        source_map = builder.build()
    """
    filename: str
    source_content: str
    names: List[str] = field(default_factory=list)
    name_index: Dict[str, int] = field(default_factory=dict)
    mappings: List[SourceMapping] = field(default_factory=list)
    
    def add_name(self, name: str) -> int:
        """Add a name and return its index."""
        if name in self.name_index:
            return self.name_index[name]
        
        index = len(self.names)
        self.names.append(name)
        self.name_index[name] = index
        return index
    
    def add_mapping(
        self,
        js_line: int,
        js_col: int,
        py_line: int,
        py_col: int,
        name: Optional[str] = None,
    ) -> None:
        """
        Add a source mapping.
        
        Args:
            js_line: Line in JavaScript (0-indexed)
            js_col: Column in JavaScript (0-indexed)
            py_line: Line in Python (0-indexed)
            py_col: Column in Python (0-indexed)
            name: Optional name at this position
        """
        name_index = self.add_name(name) if name else None
        
        self.mappings.append(SourceMapping(
            js_line=js_line,
            js_col=js_col,
            py_line=py_line,
            py_col=py_col,
            name_index=name_index,
        ))
    
    def build(self, output_filename: str = "") -> str:
        """
        Build the complete source map JSON.
        
        Args:
            output_filename: Name of the generated JS file
        
        Returns:
            JSON string of the source map
        """
        # Sort mappings by JS line, then column
        sorted_mappings = sorted(self.mappings, key=lambda m: (m.js_line, m.js_col))
        
        # Group by JS line
        lines: List[List[SourceMapping]] = []
        current_line = 0
        current_line_mappings: List[SourceMapping] = []
        
        for mapping in sorted_mappings:
            while current_line < mapping.js_line:
                lines.append(current_line_mappings)
                current_line_mappings = []
                current_line += 1
            
            current_line_mappings.append(mapping)
        
        if current_line_mappings:
            lines.append(current_line_mappings)
        
        # Encode mappings
        encoded_lines = []
        
        prev_js_col = 0
        prev_source = 0
        prev_py_line = 0
        prev_py_col = 0
        prev_name = 0
        
        for line_mappings in lines:
            segments = []
            prev_js_col = 0  # Reset column for each line
            
            for mapping in line_mappings:
                segment = [
                    mapping.js_col - prev_js_col,  # Column in generated
                    0 - prev_source,                # Source file index (always 0)
                    mapping.py_line - prev_py_line, # Line in source
                    mapping.py_col - prev_py_col,   # Column in source
                ]
                
                if mapping.name_index is not None:
                    segment.append(mapping.name_index - prev_name)
                    prev_name = mapping.name_index
                
                prev_js_col = mapping.js_col
                prev_source = 0
                prev_py_line = mapping.py_line
                prev_py_col = mapping.py_col
                
                segments.append(vlq_encode_segment(segment))
            
            encoded_lines.append(",".join(segments))
        
        # Build source map object
        source_map = {
            "version": 3,
            "file": output_filename or f"{self.filename.rsplit('.', 1)[0]}.js",
            "sources": [self.filename],
            "sourcesContent": [self.source_content],
            "names": self.names,
            "mappings": ";".join(encoded_lines),
        }
        
        return json.dumps(source_map, indent=2)


# =============================================================================
# MAIN FUNCTION
# =============================================================================

def generate_sourcemap(ir: IslandIR, js: str, filename: str) -> str:
    """
    Generate a V3 source map for compiled JavaScript.
    
    This function walks through the IR and JS to create mappings between
    Python source locations and JavaScript output locations.
    
    Args:
        ir: IslandIR with source line information
        js: Compiled JavaScript string
        filename: Original Python filename
    
    Returns:
        JSON string of the source map
    
    Example:
        >>> ir = parse_island(source, "counter.py")
        >>> ir = analyze_dependencies(ir)
        >>> js = emit_javascript(ir)
        >>> sourcemap = generate_sourcemap(ir, js, "counter.py")
    """
    builder = SourceMapBuilder(filename, ir.source)
    
    # Add component name
    builder.add_name(ir.name)
    
    # Map function declaration
    _add_function_mapping(builder, ir, js)
    
    # Map signals
    _add_signal_mappings(builder, ir, js)
    
    # Map memos
    _add_memo_mappings(builder, ir, js)
    
    # Map handlers
    _add_handler_mappings(builder, ir, js)
    
    # Map DOM tree
    if ir.dom_tree:
        _add_dom_mappings(builder, ir.dom_tree, js)
    
    return builder.build(f"{filename.rsplit('.', 1)[0]}.js")


def _add_function_mapping(builder: SourceMapBuilder, ir: IslandIR, js: str) -> None:
    """Add mapping for function declaration."""
    # Find function line in JS
    js_lines = js.split("\n")
    for i, line in enumerate(js_lines):
        if f"function {ir.name}" in line:
            # Find the actual column
            col = line.find(ir.name)
            builder.add_mapping(
                js_line=i,
                js_col=col if col >= 0 else 0,
                py_line=0,  # @island is usually line 0 or 1
                py_col=0,
                name=ir.name,
            )
            break


def _add_signal_mappings(builder: SourceMapBuilder, ir: IslandIR, js: str) -> None:
    """Add mappings for signal declarations."""
    js_lines = js.split("\n")
    
    for sig in ir.signals:
        builder.add_name(sig.name)
        
        # Find signal line in JS
        for i, line in enumerate(js_lines):
            if f"const {sig.name} = createSignal" in line:
                col = line.find(sig.name)
                builder.add_mapping(
                    js_line=i,
                    js_col=col if col >= 0 else 0,
                    py_line=sig.line - 1,  # Convert to 0-indexed
                    py_col=sig.column,
                    name=sig.name,
                )
                break


def _add_memo_mappings(builder: SourceMapBuilder, ir: IslandIR, js: str) -> None:
    """Add mappings for memo declarations."""
    js_lines = js.split("\n")
    
    for memo in ir.memos:
        builder.add_name(memo.name)
        
        # Find memo line in JS
        for i, line in enumerate(js_lines):
            if f"const {memo.name} = createMemo" in line:
                col = line.find(memo.name)
                builder.add_mapping(
                    js_line=i,
                    js_col=col if col >= 0 else 0,
                    py_line=memo.line - 1,
                    py_col=memo.column,
                    name=memo.name,
                )
                break


def _add_handler_mappings(builder: SourceMapBuilder, ir: IslandIR, js: str) -> None:
    """Add mappings for event handlers."""
    js_lines = js.split("\n")
    
    for handler in ir.handlers:
        # Find handler line in JS
        for i, line in enumerate(js_lines):
            if f'addEventListener("{handler.event}"' in line:
                col = line.find("addEventListener")
                builder.add_mapping(
                    js_line=i,
                    js_col=col if col >= 0 else 0,
                    py_line=handler.line - 1,
                    py_col=handler.column,
                )
                break


def _add_dom_mappings(builder: SourceMapBuilder, node: DOMNode, js: str) -> None:
    """Add mappings for DOM elements."""
    js_lines = js.split("\n")
    
    if node.element_id and node.line > 0:
        # Find element creation in JS
        for i, line in enumerate(js_lines):
            if f"const {node.element_id} = document.createElement" in line:
                builder.add_mapping(
                    js_line=i,
                    js_col=0,
                    py_line=node.line - 1,
                    py_col=node.column,
                )
                break
    
    # Recurse into children
    for child in node.children:
        _add_dom_mappings(builder, child, js)

