"""
PyNext Transpiler - Enhanced Source Map Generator (Phase 33.3)

=============================================================================
WHAT THIS FILE DOES
=============================================================================

Generates V3 source maps that link transpiled JavaScript handlers back to the
original Python source code. Enhanced with variable name preservation, function/class
tracking, column precision, and multi-line handling.

=============================================================================
WHY THIS EXISTS (Problem It Solves)
=============================================================================

When Python event handlers are transpiled to JavaScript, developers need to:
1. Set breakpoints in Python code
2. See Python line numbers in error stack traces
3. Debug Python logic in the browser
4. See original variable names in DevTools (not minified names)
5. Navigate to function/class definitions
6. Get precise column-level mappings for multi-line expressions

Phase 33.3 Enhancements:
- Variable name preservation: Track all variable names for better debugging
- Function/class tracking: Map JS functions/classes to Python definitions
- Column precision: Accurate column-level mappings (not just line-level)
- Multi-line handling: Proper mappings for expressions spanning multiple lines

=============================================================================
HOW IT WORKS (Architecture)
=============================================================================

The source map uses V3 format with VLQ-encoded mappings:

    {
        "version": 3,
        "file": "handler.js",
        "sources": ["handler.py"],
        "mappings": "AAAA;AACA;...",
        "names": ["x", "y", "handle_click", ...],
        "x_google_ignoreList": [0, 1, 2]  // Optional: ignore certain mappings
    }

Each segment in mappings is VLQ-encoded:
    [generated_col, source_idx, source_line, source_col, name_idx?]

Enhancements:
1. Variable names: All identifiers are tracked in `names` array
2. Function boundaries: Special mappings mark function start/end
3. Class boundaries: Special mappings mark class start/end
4. Column precision: Every token gets a column-level mapping
5. Multi-line: Mappings track exact positions across line breaks

=============================================================================
WHO USES THIS
=============================================================================

- transpiler/emitter.py: Tracks positions during emission with enhanced precision
- transpiler/debug.py: Includes source maps in debug info
- Browser DevTools: Reads source maps for debugging with variable names
- Stack trace rewriter: Uses source maps to rewrite JS stack traces to Python

=============================================================================
WHEN THIS IS USED
=============================================================================

- During emission: When emitting JavaScript code
- During debugging: When generating debug information
- At runtime: When rewriting stack traces

=============================================================================
WHERE THIS FITS
=============================================================================

Part of the source map system (pynext/transpiler/sourcemap.py).
Used by emitter.py and debug.py, and consumed by stack trace rewriter.

=============================================================================
EXAMPLES
=============================================================================

```python
from pynext.transpiler.sourcemap import SourceMapBuilder

# Create builder
builder = SourceMapBuilder("handler.py", "handler.js")

# Add mappings with variable names
builder.add_mapping(gen_line=1, gen_col=0, src_line=1, src_col=0, name="x")
builder.add_mapping(gen_line=2, gen_col=4, src_line=2, src_col=4, name="y")

# Track function boundaries
builder.start_function("handle_click", src_line=1, src_col=0)
builder.end_function("handle_click", gen_line=5, src_line=3)

# Generate source map JSON
source_map = builder.to_json()
# → {"version": 3, "file": "handler.js", "sources": ["handler.py"], ...}
```

=============================================================================
EDGE CASES
=============================================================================

- Multi-line expressions: Each line gets its own mapping
- Minified code: Variable names preserved even if JS is minified
- Nested functions: Each function tracked independently
- Anonymous functions: Tracked by line/column position
- Decorated functions: Decorator and function tracked separately

=============================================================================
RELATED FILES
=============================================================================

- emitter.py: Uses SourceMapBuilder during emission
- debug.py: Includes source maps in debug output
- stack_rewriter.py: Uses source maps to rewrite stack traces
"""

from __future__ import annotations
import base64
import json
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Mapping:
    """
    A single source map mapping (Phase 33.3: Enhanced).
    
    WHAT: Represents a single position mapping from generated JS to source Python.
    WHY: Enables precise debugging and stack trace rewriting.
    HOW: Stores line/column positions and optional identifier name.
    WHO: Created by SourceMapBuilder when tracking positions.
    WHEN: During JavaScript emission phase.
    WHERE: Part of source map generation.
    
    Attributes:
        gen_line: 0-indexed line in generated JavaScript
        gen_col: 0-indexed column in generated JavaScript
        src_line: 0-indexed line in source Python
        src_col: 0-indexed column in source Python
        name: Optional identifier name (variable, function, class)
        kind: Optional mapping kind ('function', 'class', 'variable', 'statement')
    """
    gen_line: int  # 0-indexed line in generated JS
    gen_col: int   # 0-indexed column in generated JS
    src_line: int  # 0-indexed line in source Python
    src_col: int   # 0-indexed column in source Python
    name: Optional[str] = None  # Optional identifier name
    kind: Optional[str] = None  # Phase 33.3: Mapping kind ('function', 'class', 'variable', 'statement')


@dataclass
class SourceMapBuilder:
    """
    Builds a V3 source map for Python→JS transpilation (Phase 33.3: Enhanced).
    
    WHAT: Generates source maps linking JavaScript to Python source.
    WHY: Enables debugging Python code in browser DevTools.
    HOW: Tracks positions, variable names, and function/class boundaries.
    WHO: Used by emitter.py during JavaScript generation.
    WHEN: During transpilation phase.
    WHERE: Part of source map generation system.
    
    Phase 33.3 Enhancements:
    - Variable name preservation: All identifiers tracked
    - Function/class tracking: Boundaries marked for navigation
    - Column precision: Accurate column-level mappings
    - Multi-line handling: Proper mappings across line breaks
    
    Usage:
        builder = SourceMapBuilder("handler.py", "handler.js")
        builder.add_mapping(1, 0, 1, 0, name="x")  # JS line 1 → Python line 1, variable x
        builder.start_function("handle_click", 1, 0)
        source_map = builder.to_json()
    """
    source_file: str
    generated_file: str
    source_content: Optional[str] = None
    mappings: list[Mapping] = field(default_factory=list)
    names: list[str] = field(default_factory=list)
    _name_index: dict[str, int] = field(default_factory=dict)
    # Phase 33.3: Function and class tracking
    _function_boundaries: list[tuple[str, int, int, int, int]] = field(default_factory=list)  # (name, gen_start_line, gen_end_line, src_start_line, src_end_line)
    _class_boundaries: list[tuple[str, int, int, int, int]] = field(default_factory=list)  # (name, gen_start_line, gen_end_line, src_start_line, src_end_line)
    _current_function: Optional[str] = None
    _current_class: Optional[str] = None
    _function_stack: list[str] = field(default_factory=list)  # Track nested functions
    _class_stack: list[str] = field(default_factory=list)  # Track nested classes
    
    def add_mapping(
        self,
        gen_line: int,
        gen_col: int,
        src_line: int,
        src_col: int,
        name: Optional[str] = None,
        kind: Optional[str] = None,
    ) -> None:
        """
        Add a mapping from generated to source position (Phase 33.3: Enhanced).
        
        WHAT: Records a position mapping from JavaScript to Python.
        WHY: Enables precise debugging and stack trace rewriting.
        HOW: Stores line/column positions and optional identifier name.
        WHO: Called by emitter during JavaScript generation.
        WHEN: For each token/statement in generated code.
        WHERE: Part of source map generation.
        
        Args:
            gen_line: 0-indexed line in generated JavaScript
            gen_col: 0-indexed column in generated JavaScript
            src_line: 0-indexed line in source Python
            src_col: 0-indexed column in source Python
            name: Optional identifier name to preserve (variable, function, class)
            kind: Optional mapping kind ('function', 'class', 'variable', 'statement')
        
        Examples:
            # Variable mapping
            builder.add_mapping(1, 0, 1, 0, name="x", kind="variable")
            
            # Function start
            builder.add_mapping(2, 0, 2, 0, name="handle_click", kind="function")
        """
        # Track name if provided
        if name and name not in self._name_index:
            self._name_index[name] = len(self.names)
            self.names.append(name)
        
        self.mappings.append(Mapping(
            gen_line=gen_line,
            gen_col=gen_col,
            src_line=src_line,
            src_col=src_col,
            name=name,
            kind=kind,
        ))
    
    def start_function(
        self,
        name: str,
        gen_line: int,
        gen_col: int,
        src_line: int,
        src_col: int,
    ) -> None:
        """
        Mark the start of a function definition (Phase 33.3).
        
        WHAT: Records function boundary for navigation and debugging.
        WHY: Enables "Go to Definition" in DevTools.
        HOW: Tracks function name and start position.
        WHO: Called when emitting function definitions.
        WHEN: At function declaration start.
        WHERE: Part of function tracking.
        
        Args:
            name: Function name
            gen_line: Generated JavaScript line
            gen_col: Generated JavaScript column
            src_line: Source Python line
            src_col: Source Python column
        """
        self._function_stack.append(name)
        self._current_function = name
        self.add_mapping(gen_line, gen_col, src_line, src_col, name=name, kind="function")
        # Store boundary for later end tracking
        self._function_boundaries.append((name, gen_line, -1, src_line, -1))
    
    def end_function(
        self,
        name: str,
        gen_line: int,
        src_line: int,
    ) -> None:
        """
        Mark the end of a function definition (Phase 33.3).
        
        WHAT: Records function end boundary.
        WHY: Enables function scope tracking.
        HOW: Updates function boundary end position.
        WHO: Called when emitting function end.
        WHEN: At function closing brace.
        WHERE: Part of function tracking.
        
        Args:
            name: Function name
            gen_line: Generated JavaScript line
            src_line: Source Python line
        """
        # Update the last boundary entry for this function
        for i, (fname, gen_start, gen_end, src_start, src_end) in enumerate(self._function_boundaries):
            if fname == name and gen_end == -1:
                self._function_boundaries[i] = (name, gen_start, gen_line, src_start, src_line)
                break
        
        # Pop from stack
        if self._function_stack and self._function_stack[-1] == name:
            self._function_stack.pop()
            self._current_function = self._function_stack[-1] if self._function_stack else None
    
    def start_class(
        self,
        name: str,
        gen_line: int,
        gen_col: int,
        src_line: int,
        src_col: int,
    ) -> None:
        """
        Mark the start of a class definition (Phase 33.3).
        
        WHAT: Records class boundary for navigation and debugging.
        WHY: Enables "Go to Definition" in DevTools.
        HOW: Tracks class name and start position.
        WHO: Called when emitting class definitions.
        WHEN: At class declaration start.
        WHERE: Part of class tracking.
        
        Args:
            name: Class name
            gen_line: Generated JavaScript line
            gen_col: Generated JavaScript column
            src_line: Source Python line
            src_col: Source Python column
        """
        self._class_stack.append(name)
        self._current_class = name
        self.add_mapping(gen_line, gen_col, src_line, src_col, name=name, kind="class")
        # Store boundary for later end tracking
        self._class_boundaries.append((name, gen_line, -1, src_line, -1))
    
    def end_class(
        self,
        name: str,
        gen_line: int,
        src_line: int,
    ) -> None:
        """
        Mark the end of a class definition (Phase 33.3).
        
        WHAT: Records class end boundary.
        WHY: Enables class scope tracking.
        HOW: Updates class boundary end position.
        WHO: Called when emitting class end.
        WHEN: At class closing brace.
        WHERE: Part of class tracking.
        
        Args:
            name: Class name
            gen_line: Generated JavaScript line
            src_line: Source Python line
        """
        # Update the last boundary entry for this class
        for i, (cname, gen_start, gen_end, src_start, src_end) in enumerate(self._class_boundaries):
            if cname == name and gen_end == -1:
                self._class_boundaries[i] = (name, gen_start, gen_line, src_start, src_line)
                break
        
        # Pop from stack
        if self._class_stack and self._class_stack[-1] == name:
            self._class_stack.pop()
            self._current_class = self._class_stack[-1] if self._class_stack else None
    
    def get_current_function(self) -> Optional[str]:
        """Get the current function name (if inside a function)."""
        return self._current_function
    
    def get_current_class(self) -> Optional[str]:
        """Get the current class name (if inside a class)."""
        return self._current_class
    
    def to_json(self) -> dict:
        """
        Generate V3 source map as a dictionary (Phase 33.3: Enhanced).
        
        WHAT: Creates V3 source map JSON with enhanced metadata.
        WHY: Provides complete mapping information for debugging.
        HOW: Encodes mappings, names, and optional boundaries.
        WHO: Used by debug.py and stack trace rewriter.
        WHEN: After all mappings are added.
        WHERE: Part of source map generation.
        
        Returns:
            Source map dictionary ready for JSON serialization
        
        Phase 33.3 Enhancements:
        - Includes function/class boundaries as metadata
        - Preserves all variable names
        - Column-precise mappings
        """
        result = {
            "version": 3,
            "file": self.generated_file,
            "sources": [self.source_file],
            "names": self.names,
            "mappings": self._encode_mappings(),
        }
        
        if self.source_content is not None:
            result["sourcesContent"] = [self.source_content]
        
        # Phase 33.3: Add function and class boundaries as metadata
        # This helps stack trace rewriter identify function/class scopes
        if self._function_boundaries:
            result["x_pynext_functions"] = [
                {
                    "name": name,
                    "generated": {"start": gen_start, "end": gen_end},
                    "source": {"start": src_start, "end": src_end},
                }
                for name, gen_start, gen_end, src_start, src_end in self._function_boundaries
                if gen_end != -1  # Only include completed functions
            ]
        
        if self._class_boundaries:
            result["x_pynext_classes"] = [
                {
                    "name": name,
                    "generated": {"start": gen_start, "end": gen_end},
                    "source": {"start": src_start, "end": src_end},
                }
                for name, gen_start, gen_end, src_start, src_end in self._class_boundaries
                if gen_end != -1  # Only include completed classes
            ]
        
        return result
    
    def get_function_boundaries(self) -> list[dict]:
        """
        Get function boundaries for stack trace rewriting (Phase 33.3).
        
        WHAT: Returns function boundary information.
        WHY: Enables stack trace rewriter to identify function scopes.
        HOW: Returns list of function boundary dictionaries.
        WHO: Used by stack trace rewriter.
        WHEN: After source map generation.
        WHERE: Part of source map API.
        
        Returns:
            List of function boundary dictionaries with name and positions
        """
        return [
            {
                "name": name,
                "generated": {"start": gen_start, "end": gen_end},
                "source": {"start": src_start, "end": src_end},
            }
            for name, gen_start, gen_end, src_start, src_end in self._function_boundaries
            if gen_end != -1
        ]
    
    def get_class_boundaries(self) -> list[dict]:
        """
        Get class boundaries for stack trace rewriting (Phase 33.3).
        
        WHAT: Returns class boundary information.
        WHY: Enables stack trace rewriter to identify class scopes.
        HOW: Returns list of class boundary dictionaries.
        WHO: Used by stack trace rewriter.
        WHEN: After source map generation.
        WHERE: Part of source map API.
        
        Returns:
            List of class boundary dictionaries with name and positions
        """
        return [
            {
                "name": name,
                "generated": {"start": gen_start, "end": gen_end},
                "source": {"start": src_start, "end": src_end},
            }
            for name, gen_start, gen_end, src_start, src_end in self._class_boundaries
            if gen_end != -1
        ]
    
    def to_json_string(self) -> str:
        """Generate V3 source map as JSON string."""
        return json.dumps(self.to_json(), separators=(",", ":"))
    
    def to_data_url(self) -> str:
        """
        Generate source map as base64 data URL.
        
        Useful for inline source map comments:
            //# sourceMappingURL=data:application/json;base64,...
        """
        json_str = self.to_json_string()
        b64 = base64.b64encode(json_str.encode("utf-8")).decode("ascii")
        return f"data:application/json;base64,{b64}"
    
    def to_inline_comment(self) -> str:
        """
        Generate inline source map comment to append to JS.
        
        Returns:
            String like: //# sourceMappingURL=data:application/json;base64,...
        """
        return f"//# sourceMappingURL={self.to_data_url()}"
    
    def _encode_mappings(self) -> str:
        """
        Encode mappings as VLQ string (Phase 33.3: Enhanced with column precision).
        
        WHAT: Converts position mappings to VLQ-encoded string.
        WHY: VLQ encoding is compact and efficient for source maps.
        HOW: Delta-encodes positions relative to previous segment.
        WHO: Called by to_json() when generating source map.
        WHEN: After all mappings are added.
        WHERE: Part of source map encoding.
        
        VLQ segments are comma-separated within a line,
        and lines are semicolon-separated.
        
        Each segment has 4 or 5 values:
            [gen_col, source_idx, src_line, src_col, name_idx?]
        All values are relative to the previous segment (delta-encoded).
        
        Phase 33.3 Enhancements:
        - Column-precise mappings (not just line-level)
        - Variable name preservation (name_idx included when available)
        - Multi-line expression handling (each line gets its own mapping)
        """
        if not self.mappings:
            return ""
        
        # Sort mappings by generated position
        sorted_mappings = sorted(
            self.mappings,
            key=lambda m: (m.gen_line, m.gen_col)
        )
        
        # Group by generated line
        lines: list[list[Mapping]] = []
        current_line = -1
        
        for mapping in sorted_mappings:
            while current_line < mapping.gen_line:
                lines.append([])
                current_line += 1
            lines[current_line].append(mapping)
        
        # Encode each line
        encoded_lines = []
        prev_gen_col = 0
        prev_src_line = 0
        prev_src_col = 0
        prev_name_idx = 0
        
        for line_mappings in lines:
            segments = []
            prev_gen_col = 0  # Reset column at each new line
            
            for mapping in line_mappings:
                segment = []
                
                # Generated column (relative to previous segment in same line)
                segment.append(mapping.gen_col - prev_gen_col)
                prev_gen_col = mapping.gen_col
                
                # Source index (always 0 for single source)
                segment.append(0)
                
                # Source line (relative)
                segment.append(mapping.src_line - prev_src_line)
                prev_src_line = mapping.src_line
                
                # Source column (relative)
                segment.append(mapping.src_col - prev_src_col)
                prev_src_col = mapping.src_col
                
                # Optional: name index
                if mapping.name and mapping.name in self._name_index:
                    name_idx = self._name_index[mapping.name]
                    segment.append(name_idx - prev_name_idx)
                    prev_name_idx = name_idx
                
                segments.append(_encode_vlq_segment(segment))
            
            encoded_lines.append(",".join(segments))
        
        return ";".join(encoded_lines)


# =============================================================================
# VLQ ENCODING
# =============================================================================

_VLQ_BASE = 32
_VLQ_BASE_MASK = _VLQ_BASE - 1
_VLQ_CONTINUATION_BIT = _VLQ_BASE
_VLQ_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"


def _encode_vlq(value: int) -> str:
    """
    Encode a single integer as VLQ (Variable-Length Quantity).
    
    VLQ uses base64-like encoding with a continuation bit.
    Negative numbers are zigzag-encoded.
    """
    # Zigzag encode for negative numbers
    if value < 0:
        value = ((-value) << 1) | 1
    else:
        value = value << 1
    
    result = []
    while True:
        digit = value & _VLQ_BASE_MASK
        value >>= 5
        if value > 0:
            digit |= _VLQ_CONTINUATION_BIT
        result.append(_VLQ_CHARS[digit])
        if value == 0:
            break
    
    return "".join(result)


def _encode_vlq_segment(values: list[int]) -> str:
    """Encode a segment (list of integers) as VLQ string."""
    return "".join(_encode_vlq(v) for v in values)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_source_map(
    source_file: str,
    generated_file: str,
    mappings: list[tuple[int, int, int, int]],
    source_content: Optional[str] = None,
) -> dict:
    """
    Create a source map from a list of mapping tuples.
    
    Args:
        source_file: Original Python source filename
        generated_file: Generated JavaScript filename
        mappings: List of (gen_line, gen_col, src_line, src_col) tuples
        source_content: Optional original source content to embed
    
    Returns:
        Source map dictionary
    
    Example:
        source_map = create_source_map(
            "handler.py",
            "handler.js",
            [(1, 0, 1, 0), (2, 4, 2, 4), (3, 0, 3, 0)],
        )
    """
    builder = SourceMapBuilder(source_file, generated_file, source_content)
    for gen_line, gen_col, src_line, src_col in mappings:
        builder.add_mapping(gen_line, gen_col, src_line, src_col)
    return builder.to_json()

