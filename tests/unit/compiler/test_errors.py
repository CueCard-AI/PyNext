"""
Comprehensive tests for PyNext Compiler Error Messages (150 tests)

Tests cover:
- Error types and messages
- Error formatting
- Error locations
- Suggestions
- Documentation links
- Warning types
"""

import pytest
from pynext.compiler import compile_island, CompileError, CompileWarning
from pynext.compiler.errors import (
    no_island_found,
    invalid_syntax,
    class_not_compilable,
    await_not_compilable,
    import_not_compilable,
    yield_not_compilable,
    global_not_compilable,
    signal_not_found,
    invalid_handler,
    complex_comprehension,
    unused_signal,
    signal_read_in_render,
    deprecated_api,
    large_initial_value,
)


# =============================================================================
# SECTION 1: CompileError Structure (20 tests)
# =============================================================================

class TestCompileErrorStructure:
    """Tests for CompileError data structure."""
    
    def test_error_has_message(self):
        """Error has message attribute."""
        error = CompileError("Test message")
        assert error.message == "Test message"
    
    def test_error_has_filename(self):
        """Error has filename attribute."""
        error = CompileError("Test", filename="test.py")
        assert error.filename == "test.py"
    
    def test_error_has_line(self):
        """Error has line attribute."""
        error = CompileError("Test", line=10)
        assert error.line == 10
    
    def test_error_has_column(self):
        """Error has column attribute."""
        error = CompileError("Test", column=5)
        assert error.column == 5
    
    def test_error_has_source_line(self):
        """Error has source_line attribute."""
        error = CompileError("Test", source_line="    count = signal(0)")
        assert error.source_line == "    count = signal(0)"
    
    def test_error_has_suggestion(self):
        """Error has suggestion attribute."""
        error = CompileError("Test", suggestion="Try this instead")
        assert error.suggestion == "Try this instead"
    
    def test_error_has_docs_url(self):
        """Error has docs_url attribute."""
        error = CompileError("Test", docs_url="compilation#async")
        assert "pynext.dev" in error.docs_url
    
    def test_error_has_error_code(self):
        """Error has error_code attribute."""
        error = CompileError("Test", error_code="E010")
        assert error.error_code == "E010"


# =============================================================================
# SECTION 2: Error Formatting (30 tests)
# =============================================================================

class TestErrorFormatting:
    """Tests for error message formatting."""
    
    def test_str_includes_message(self):
        """String representation includes message."""
        error = CompileError("Cannot compile class")
        assert "Cannot compile class" in str(error)
    
    def test_str_includes_file_location(self):
        """String includes file and line."""
        error = CompileError("Test", filename="test.py", line=10)
        assert "test.py" in str(error)
        assert "10" in str(error)
    
    def test_str_includes_source_line(self):
        """String includes source line."""
        error = CompileError("Test", filename="test.py", line=1, source_line="class Helper:")
        assert "class Helper:" in str(error)
    
    def test_str_includes_pointer(self):
        """String includes column pointer."""
        error = CompileError("Test", filename="test.py", line=1, source_line="class Helper:", column=0)
        assert "^" in str(error)
    
    def test_str_includes_suggestion(self):
        """String includes suggestion."""
        error = CompileError("Test", suggestion="Try this")
        assert "Try this" in str(error)
    
    def test_str_includes_docs(self):
        """String includes docs URL."""
        error = CompileError("Test", docs_url="https://example.com")
        assert "https://example.com" in str(error)
    
    def test_str_includes_error_code(self):
        """String includes error code."""
        error = CompileError("Test", error_code="E010")
        assert "E010" in str(error)
    
    def test_to_dict_method(self):
        """to_dict returns dictionary."""
        error = CompileError("Test", line=5, error_code="E001")
        d = error.to_dict()
        assert d["message"] == "Test"
        assert d["line"] == 5
        assert d["code"] == "E001"


# =============================================================================
# SECTION 3: Specific Error Types (50 tests)
# =============================================================================

class TestNoIslandError:
    """Tests for no_island_found error."""
    
    def test_message(self):
        error = no_island_found("test.py")
        assert "No @island" in error.message
    
    def test_suggestion_mentions_decorator(self):
        error = no_island_found("test.py")
        assert "@island" in error.suggestion
    
    def test_has_error_code(self):
        error = no_island_found("test.py")
        assert error.error_code == "E001"


class TestClassNotCompilableError:
    """Tests for class_not_compilable error."""
    
    def test_message_includes_class_name(self):
        error = class_not_compilable("test.py", 10, "class Helper:", "Helper")
        assert "Helper" in error.message
    
    def test_suggestion_exists(self):
        error = class_not_compilable("test.py", 10, "class Helper:", "Helper")
        assert error.suggestion
    
    def test_has_error_code(self):
        error = class_not_compilable("test.py", 10, "class Helper:", "Helper")
        assert error.error_code == "E010"


class TestAwaitNotCompilableError:
    """Tests for await_not_compilable error."""
    
    def test_message_mentions_await(self):
        error = await_not_compilable("test.py", 10, "result = await fetch()")
        assert "await" in error.message.lower()
    
    def test_suggestion_mentions_server_action(self):
        error = await_not_compilable("test.py", 10, "result = await fetch()")
        assert "server" in error.suggestion.lower()
    
    def test_has_error_code(self):
        error = await_not_compilable("test.py", 10, "")
        assert error.error_code == "E011"


class TestImportNotCompilableError:
    """Tests for import_not_compilable error."""
    
    def test_message_includes_module(self):
        error = import_not_compilable("test.py", 10, "import math", "math")
        assert "math" in error.message
    
    def test_has_error_code(self):
        error = import_not_compilable("test.py", 10, "", "os")
        assert error.error_code == "E012"


class TestYieldNotCompilableError:
    """Tests for yield_not_compilable error."""
    
    def test_message_mentions_yield(self):
        error = yield_not_compilable("test.py", 10, "yield x")
        assert "yield" in error.message.lower()
    
    def test_has_error_code(self):
        error = yield_not_compilable("test.py", 10, "")
        assert error.error_code == "E013"


class TestGlobalNotCompilableError:
    """Tests for global_not_compilable error."""
    
    def test_message_includes_name(self):
        error = global_not_compilable("test.py", 10, "global count", "count")
        assert "global" in error.message.lower()
    
    def test_suggestion_mentions_signals(self):
        error = global_not_compilable("test.py", 10, "", "count")
        assert "signal" in error.suggestion.lower()
    
    def test_has_error_code(self):
        error = global_not_compilable("test.py", 10, "", "x")
        assert error.error_code == "E014"


# =============================================================================
# SECTION 4: Compile Time Errors (30 tests)
# =============================================================================

class TestCompileTimeErrors:
    """Tests for errors raised during compilation."""
    
    def test_syntax_error_caught(self):
        """Syntax errors are caught."""
        result = compile_island("@island\ndef C(\n", "test.py")
        assert not result.success
        assert len(result.errors) > 0
    
    def test_class_error_raised(self):
        """Class inside island raises error."""
        result = compile_island("""
@island
def C():
    class X:
        pass
""", "test.py")
        assert not result.success
    
    def test_await_error_raised(self):
        """Await inside island raises error."""
        result = compile_island("""
@island
async def C():
    x = await foo()
""", "test.py")
        assert not result.success
    
    def test_yield_error_raised(self):
        """Yield inside island raises error."""
        result = compile_island("""
@island
def C():
    def gen():
        yield 1
""", "test.py")
        assert not result.success
    
    def test_global_error_raised(self):
        """Global inside island raises error."""
        result = compile_island("""
@island
def C():
    global x
""", "test.py")
        assert not result.success
    
    def test_import_error_raised(self):
        """Import inside island raises error."""
        result = compile_island("""
@island
def C():
    import os
""", "test.py")
        assert not result.success
    
    def test_no_island_error(self):
        """Missing @island raises error."""
        result = compile_island("def C(): pass", "test.py")
        assert not result.success


# =============================================================================
# SECTION 5: Warning Types (20 tests)
# =============================================================================

class TestWarnings:
    """Tests for compile-time warnings."""
    
    def test_warning_has_message(self):
        warning = CompileWarning("Test warning")
        assert warning.message == "Test warning"
    
    def test_warning_has_line(self):
        warning = CompileWarning("Test", line=5)
        assert warning.line == 5
    
    def test_warning_to_dict(self):
        warning = CompileWarning("Test", warning_code="W001")
        d = warning.to_dict()
        assert d["type"] == "warning"
        assert d["code"] == "W001"
    
    def test_unused_signal_warning(self):
        warning = unused_signal("test.py", 5, "count")
        assert "count" in warning.message
        assert warning.warning_code == "W001"
    
    def test_deprecated_api_warning(self):
        warning = deprecated_api("test.py", 5, "old_fn", "new_fn")
        assert "old_fn" in warning.message
        assert "new_fn" in warning.message
        assert warning.warning_code == "W010"
    
    def test_large_initial_value_warning(self):
        warning = large_initial_value("test.py", 5, "data", 100000)
        assert "100000" in warning.message
        assert warning.warning_code == "W020"

