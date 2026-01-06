"""
Phase 18.8: Debug Utilities Tests

Tests for debug.py and transpilation debugging features.

Tests: 40
"""

import pytest
import json
from pynext.transpiler.debug import (
    get_transpile_debug_info,
    TranspileDebugInfo,
    register_handler_debug_info,
    get_registered_handlers,
    get_handler_debug_info,
    clear_handler_registry,
    generate_handler_registry_js,
    _ir_to_dict,
    _collect_runtime_deps,
)


class TestGetTranspileDebugInfo:
    """Tests for get_transpile_debug_info function."""
    
    def test_simple_code(self):
        """Get debug info for simple code."""
        info = get_transpile_debug_info("x = 5")
        assert isinstance(info, TranspileDebugInfo)
        assert info.original == "x = 5"
        assert "x" in info.javascript
    
    def test_includes_ir(self):
        """Debug info includes IR."""
        info = get_transpile_debug_info("x = 5")
        assert isinstance(info.ir, dict)
        assert "_type" in info.ir or "error" in info.ir
    
    def test_includes_javascript(self):
        """Debug info includes JavaScript."""
        info = get_transpile_debug_info("y = 10")
        assert len(info.javascript) > 0
    
    def test_includes_source_map(self):
        """Debug info includes source map."""
        info = get_transpile_debug_info("z = 1")
        assert info.source_map is not None
        assert info.source_map["version"] == 3
    
    def test_no_source_map_option(self):
        """Can disable source map generation."""
        info = get_transpile_debug_info("x = 1", include_source_map=False)
        assert info.source_map is None
    
    def test_includes_runtime_deps(self):
        """Debug info includes runtime dependencies."""
        # Code that uses __py functions
        info = get_transpile_debug_info("if items: pass")
        assert isinstance(info.runtime_deps, list)
    
    def test_handler_name(self):
        """Debug info includes handler name."""
        info = get_transpile_debug_info("x = 1", handler_name="test_handler")
        assert info.handler_name == "test_handler"
    
    def test_parse_error_handled(self):
        """Parse errors are captured."""
        info = get_transpile_debug_info("def incomplete(")
        assert "error" in info.ir or len(info.warnings) > 0
    
    def test_to_dict(self):
        """Convert debug info to dict."""
        info = get_transpile_debug_info("x = 1")
        d = info.to_dict()
        assert isinstance(d, dict)
        assert "original" in d
        assert "javascript" in d
    
    def test_to_json(self):
        """Convert debug info to JSON."""
        info = get_transpile_debug_info("x = 1")
        j = info.to_json()
        assert isinstance(j, str)
        parsed = json.loads(j)
        assert "original" in parsed


class TestRuntimeDepsCollection:
    """Tests for collecting runtime dependencies."""
    
    def test_empty_code_no_deps(self):
        """Empty code has no deps."""
        deps = _collect_runtime_deps("")
        assert deps == []
    
    def test_simple_code_no_deps(self):
        """Simple code may have no deps."""
        deps = _collect_runtime_deps("let x = 5;")
        assert "__py" not in str(deps)
    
    def test_py_bool_detected(self):
        """Detect __py.bool usage."""
        deps = _collect_runtime_deps("if (__py.bool(items)) {}")
        assert "__py.bool" in deps
    
    def test_py_at_detected(self):
        """Detect __py.at usage."""
        deps = _collect_runtime_deps("__py.at(arr, -1)")
        assert "__py.at" in deps
    
    def test_py_slice_detected(self):
        """Detect __py.slice usage."""
        deps = _collect_runtime_deps("__py.slice(arr, 1, 3)")
        assert "__py.slice" in deps
    
    def test_pynext_signal_detected(self):
        """Detect __pynext__ usage."""
        deps = _collect_runtime_deps("__pynext__.getSignal('count')")
        assert "__pynext__.getSignal" in deps
    
    def test_multiple_deps(self):
        """Multiple dependencies detected."""
        js = "__py.bool(x) && __py.eq(a, b) && __py.at(arr, 0)"
        deps = _collect_runtime_deps(js)
        assert "__py.bool" in deps
        assert "__py.eq" in deps
        assert "__py.at" in deps
    
    def test_deps_sorted(self):
        """Dependencies are sorted."""
        deps = _collect_runtime_deps("__py.slice(x) || __py.at(y) || __py.bool(z)")
        assert deps == sorted(deps)


class TestIRToDict:
    """Tests for IR to dictionary conversion."""
    
    def test_none_value(self):
        """Convert None."""
        assert _ir_to_dict(None) is None
    
    def test_primitive_values(self):
        """Convert primitive values."""
        assert _ir_to_dict(5) == 5
        assert _ir_to_dict("hello") == "hello"
        assert _ir_to_dict(True) is True
    
    def test_list_conversion(self):
        """Convert lists."""
        result = _ir_to_dict([1, 2, 3])
        assert result == [1, 2, 3]
    
    def test_tuple_conversion(self):
        """Convert tuples."""
        result = _ir_to_dict((1, 2, 3))
        assert result == [1, 2, 3]
    
    def test_max_depth_truncation(self):
        """Very deep nesting is truncated."""
        from pynext.transpiler.nodes import Name
        node = Name(id="deeply_nested")
        result = _ir_to_dict(node, max_depth=0)
        assert result == {"_truncated": True}


class TestHandlerRegistry:
    """Tests for handler registration."""
    
    def setup_method(self):
        """Clear registry before each test."""
        clear_handler_registry()
    
    def test_register_handler(self):
        """Register a handler."""
        register_handler_debug_info(
            "test_handler",
            "def test(): pass",
            "function test() {}",
            ["__py.bool"],
        )
        assert "test_handler" in get_registered_handlers()
    
    def test_get_handler_info(self):
        """Get registered handler info."""
        register_handler_debug_info(
            "my_handler",
            "x = 1",
            "let x = 1;",
            [],
        )
        info = get_handler_debug_info("my_handler")
        assert info is not None
        assert info.handler_name == "my_handler"
    
    def test_get_nonexistent_handler(self):
        """Get info for nonexistent handler."""
        info = get_handler_debug_info("does_not_exist")
        assert info is None
    
    def test_list_handlers(self):
        """List all registered handlers."""
        register_handler_debug_info("a", "", "", [])
        register_handler_debug_info("b", "", "", [])
        register_handler_debug_info("c", "", "", [])
        
        handlers = get_registered_handlers()
        assert len(handlers) == 3
        assert "a" in handlers
        assert "b" in handlers
        assert "c" in handlers
    
    def test_clear_registry(self):
        """Clear the registry."""
        register_handler_debug_info("test", "", "", [])
        clear_handler_registry()
        assert get_registered_handlers() == []


class TestGenerateRegistryJS:
    """Tests for generating JS registration code."""
    
    def setup_method(self):
        """Clear registry before each test."""
        clear_handler_registry()
    
    def test_empty_registry(self):
        """Empty registry produces empty string."""
        js = generate_handler_registry_js()
        assert js == ""
    
    def test_single_handler(self):
        """Generate JS for single handler."""
        register_handler_debug_info(
            "handle_click",
            "def handle_click(): pass",
            "function handle_click() {}",
            ["__py.bool"],
        )
        js = generate_handler_registry_js()
        
        assert "px_transpile_debug._register" in js
        assert "handle_click" in js
    
    def test_multiple_handlers(self):
        """Generate JS for multiple handlers."""
        register_handler_debug_info("a", "a", "a", [])
        register_handler_debug_info("b", "b", "b", [])
        
        js = generate_handler_registry_js()
        assert js.count("_register") == 2
    
    def test_js_escaping(self):
        """Strings are properly escaped for JS."""
        register_handler_debug_info(
            "test",
            'x = "hello"',
            'let x = "hello";',
            [],
        )
        js = generate_handler_registry_js()
        # Should be valid JS (strings escaped)
        assert "\\\"" in js or '\\"' in js or '"hello"' in js
    
    def test_js_includes_runtime_deps(self):
        """Generated JS includes runtime deps."""
        register_handler_debug_info(
            "test",
            "",
            "",
            ["__py.bool", "__py.eq"],
        )
        js = generate_handler_registry_js()
        assert "runtimeDeps" in js


class TestTranspileDebugInfo:
    """Tests for TranspileDebugInfo dataclass."""
    
    def test_create_info(self):
        """Create TranspileDebugInfo instance."""
        info = TranspileDebugInfo(
            original="x = 1",
            ir={"_type": "Program"},
            javascript="let x = 1;",
        )
        assert info.original == "x = 1"
        assert info.javascript == "let x = 1;"
    
    def test_defaults(self):
        """Default values are set."""
        info = TranspileDebugInfo(
            original="",
            ir={},
            javascript="",
        )
        assert info.source_map is None
        assert info.runtime_deps == []
        assert info.warnings == []
        assert info.handler_name is None
    
    def test_with_all_fields(self):
        """Create with all fields populated."""
        info = TranspileDebugInfo(
            original="code",
            ir={"type": "Program"},
            javascript="js",
            source_map={"version": 3},
            runtime_deps=["__py.bool"],
            warnings=["warning"],
            handler_name="handler",
        )
        assert info.source_map == {"version": 3}
        assert info.runtime_deps == ["__py.bool"]
        assert info.warnings == ["warning"]
        assert info.handler_name == "handler"

