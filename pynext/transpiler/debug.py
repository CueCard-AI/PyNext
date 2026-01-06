"""
PyNext Transpiler - Debug Utilities (Phase 18.8)

=============================================================================
WHAT THIS FILE DOES
=============================================================================

Provides debug utilities for transpilation:
1. Detailed transpilation debug info (Python source, IR, JS output)
2. Handler registration for browser debugging
3. Runtime dependency tracking
4. Integration with px_transpile_debug browser API

=============================================================================
WHY THIS EXISTS
=============================================================================

When debugging transpilation issues, developers need to see:
1. The original Python code
2. The intermediate representation (IR)
3. The generated JavaScript
4. Which runtime functions (__py.*) are used
5. Any warnings or suggestions

=============================================================================
WHO USES THIS
=============================================================================

- transpiler/__init__.py: Optionally includes debug info
- hydration.py: Registers handlers for browser debugging
- px_transpile_debug (browser): Displays debug info in console

=============================================================================
EXAMPLES
=============================================================================

```python
from pynext.transpiler.debug import get_transpile_debug_info

# Get detailed debug info
info = get_transpile_debug_info('''
def handle_click():
    if items:
        count.set(count() + 1)
''')

print(info['javascript'])
print(info['runtime_deps'])  # ['__py.bool', '__pynext__.getSignal', ...]
```
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional, Any
import json

from .parser import parse
from .emitter import emit
from .sourcemap import SourceMapBuilder


@dataclass
class TranspileDebugInfo:
    """
    Complete debug information for a transpilation.
    
    Attributes:
        original: Original Python source code
        ir: Intermediate representation as dict (for JSON serialization)
        javascript: Generated JavaScript code
        source_map: V3 source map (if generated)
        runtime_deps: List of runtime functions used (__py.*, __pynext__.*)
        warnings: Any warnings generated during transpilation
        handler_name: Name of the handler (if applicable)
    """
    original: str
    ir: dict
    javascript: str
    source_map: Optional[dict] = None
    runtime_deps: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    handler_name: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


def get_transpile_debug_info(
    python_code: str,
    handler_name: Optional[str] = None,
    include_source_map: bool = True,
) -> TranspileDebugInfo:
    """
    Get detailed debug information for a transpilation.
    
    Args:
        python_code: Python source code to transpile
        handler_name: Optional name for the handler
        include_source_map: Whether to include source map
    
    Returns:
        TranspileDebugInfo with complete debug information
    
    Example:
        info = get_transpile_debug_info('''
        def handle_click():
            count.set(count() + 1)
        ''')
        print(info.javascript)
    """
    warnings = []
    
    # Parse Python to IR
    try:
        ir = parse(python_code)
    except Exception as e:
        return TranspileDebugInfo(
            original=python_code,
            ir={"error": str(e)},
            javascript="",
            warnings=[f"Parse error: {e}"],
            handler_name=handler_name,
        )
    
    # Emit JavaScript
    try:
        javascript = emit(ir)
    except Exception as e:
        return TranspileDebugInfo(
            original=python_code,
            ir=_ir_to_dict(ir),
            javascript="",
            warnings=[f"Emit error: {e}"],
            handler_name=handler_name,
        )
    
    # Collect runtime dependencies
    runtime_deps = _collect_runtime_deps(javascript)
    
    # Generate source map if requested
    source_map = None
    if include_source_map:
        source_map = _generate_debug_source_map(python_code, javascript, handler_name or "handler")
    
    return TranspileDebugInfo(
        original=python_code,
        ir=_ir_to_dict(ir),
        javascript=javascript,
        source_map=source_map,
        runtime_deps=runtime_deps,
        warnings=warnings,
        handler_name=handler_name,
    )


def _ir_to_dict(node: Any, max_depth: int = 10) -> dict:
    """
    Convert IR node to dictionary for JSON serialization.
    
    Handles nested dataclasses and tuples.
    """
    if max_depth <= 0:
        return {"_truncated": True}
    
    if node is None:
        return None
    
    if isinstance(node, (str, int, float, bool)):
        return node
    
    if isinstance(node, (list, tuple)):
        return [_ir_to_dict(item, max_depth - 1) for item in node]
    
    if hasattr(node, "__dataclass_fields__"):
        result = {"_type": type(node).__name__}
        for field_name in node.__dataclass_fields__:
            value = getattr(node, field_name)
            result[field_name] = _ir_to_dict(value, max_depth - 1)
        return result
    
    return str(node)


def _collect_runtime_deps(javascript: str) -> list[str]:
    """
    Collect runtime dependencies from generated JavaScript.
    
    Finds all __py.* and __pynext__.* calls.
    """
    import re
    
    deps = set()
    
    # Find __py.* calls
    py_pattern = r'__py\.(\w+)'
    for match in re.finditer(py_pattern, javascript):
        deps.add(f"__py.{match.group(1)}")
    
    # Find __pynext__.* calls
    pynext_pattern = r'__pynext__\.(\w+)'
    for match in re.finditer(pynext_pattern, javascript):
        deps.add(f"__pynext__.{match.group(1)}")
    
    return sorted(deps)


def _generate_debug_source_map(
    python_code: str,
    javascript: str,
    handler_name: str,
) -> dict:
    """
    Generate a simple line-to-line source map for debugging.
    
    This is a simplified mapping that maps each JS line to the
    corresponding Python line. For more precise mappings,
    use the full SourceMapBuilder during emission.
    """
    builder = SourceMapBuilder(
        source_file=f"{handler_name}.py",
        generated_file=f"{handler_name}.js",
        source_content=python_code,
    )
    
    # Simple line-to-line mapping
    py_lines = python_code.split("\n")
    js_lines = javascript.split("\n")
    
    # Map each JS line to corresponding Python line (1:1 for simplicity)
    min_lines = min(len(py_lines), len(js_lines))
    for i in range(min_lines):
        builder.add_mapping(
            gen_line=i,
            gen_col=0,
            src_line=i,
            src_col=0,
        )
    
    return builder.to_json()


# =============================================================================
# HANDLER REGISTRY
# =============================================================================

# Global registry for debug info (used by hydration)
_handler_registry: dict[str, TranspileDebugInfo] = {}


def register_handler_debug_info(
    name: str,
    python_source: str,
    javascript: str,
    runtime_deps: list[str],
    source_map: Optional[dict] = None,
) -> None:
    """
    Register debug info for a transpiled handler.
    
    Called by hydration when --ai-debug is active.
    This info is then available to px_transpile_debug in the browser.
    
    Args:
        name: Handler name (e.g., "handle_add_issue")
        python_source: Original Python source code
        javascript: Generated JavaScript code
        runtime_deps: List of runtime functions used
        source_map: Optional source map
    """
    _handler_registry[name] = TranspileDebugInfo(
        original=python_source,
        ir={},  # IR not needed for runtime debugging
        javascript=javascript,
        source_map=source_map,
        runtime_deps=runtime_deps,
        handler_name=name,
    )


def get_registered_handlers() -> list[str]:
    """Get list of all registered handler names."""
    return list(_handler_registry.keys())


def get_handler_debug_info(name: str) -> Optional[TranspileDebugInfo]:
    """Get debug info for a specific handler."""
    return _handler_registry.get(name)


def clear_handler_registry() -> None:
    """Clear all registered handlers (for testing)."""
    _handler_registry.clear()


def generate_handler_registry_js() -> str:
    """
    Generate JavaScript code to populate px_transpile_debug registry.
    
    This is injected into the page when --ai-debug is active.
    
    Returns:
        JavaScript code that registers all handlers
    """
    if not _handler_registry:
        return ""
    
    lines = ["if (window.px_transpile_debug) {"]
    
    for name, info in _handler_registry.items():
        # Escape strings for JS
        python_escaped = json.dumps(info.original)
        js_escaped = json.dumps(info.javascript)
        deps_json = json.dumps(info.runtime_deps)
        
        lines.append(f"  px_transpile_debug._register({json.dumps(name)}, {{")
        lines.append(f"    python: {python_escaped},")
        lines.append(f"    javascript: {js_escaped},")
        lines.append(f"    runtimeDeps: {deps_json},")
        lines.append("  });")
    
    lines.append("}")
    
    return "\n".join(lines)

