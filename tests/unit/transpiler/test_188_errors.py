"""
Phase 18.8: Error Messages Tests

Tests for enhanced error messages and suggestions.

Tests: 50
"""

import pytest
from pynext.transpiler.errors import (
    TranspileError,
    UnsupportedSyntax,
    SemanticError,
    InternalError,
    unsupported,
    get_suggestion,
    format_error_with_context,
    SUGGESTIONS,
)


class TestSuggestions:
    """Tests for error suggestions."""
    
    def test_yield_suggestion(self):
        """Suggestion for yield."""
        suggestion = get_suggestion("yield")
        assert suggestion is not None
        assert "@server_action" in suggestion
    
    def test_async_with_suggestion(self):
        """Suggestion for async with."""
        suggestion = get_suggestion("async_with")
        assert suggestion is not None
        assert "@server_action" in suggestion
    
    def test_async_for_suggestion(self):
        """Suggestion for async for."""
        suggestion = get_suggestion("async_for")
        assert suggestion is not None
    
    def test_match_suggestion(self):
        """Suggestion for match/case."""
        suggestion = get_suggestion("match")
        assert suggestion is not None
        assert "if/elif/else" in suggestion
    
    def test_walrus_suggestion(self):
        """Suggestion for walrus operator issues."""
        suggestion = get_suggestion("walrus")
        assert suggestion is not None
    
    def test_global_suggestion(self):
        """Suggestion for global statement."""
        suggestion = get_suggestion("global")
        assert suggestion is not None
        assert "signal" in suggestion.lower()
    
    def test_nonlocal_suggestion(self):
        """Suggestion for nonlocal statement."""
        suggestion = get_suggestion("nonlocal")
        assert suggestion is not None
    
    def test_multiple_inheritance_suggestion(self):
        """Suggestion for multiple inheritance."""
        suggestion = get_suggestion("class_multiple_inheritance")
        assert suggestion is not None
        assert "composition" in suggestion.lower() or "single" in suggestion.lower()
    
    def test_classmethod_suggestion(self):
        """Suggestion for @classmethod."""
        suggestion = get_suggestion("classmethod")
        assert suggestion is not None
        assert "@staticmethod" in suggestion
    
    def test_metaclass_suggestion(self):
        """Suggestion for metaclass."""
        suggestion = get_suggestion("metaclass")
        assert suggestion is not None
    
    def test_slots_suggestion(self):
        """Suggestion for __slots__."""
        suggestion = get_suggestion("slots")
        assert suggestion is not None
    
    def test_property_setter_suggestion(self):
        """Suggestion for property setter."""
        suggestion = get_suggestion("property_setter")
        assert suggestion is not None
        assert "setter" in suggestion.lower()
    
    def test_import_suggestion(self):
        """Suggestion for import statements."""
        suggestion = get_suggestion("import")
        assert suggestion is not None
    
    def test_division_by_zero_suggestion(self):
        """Suggestion for division by zero."""
        suggestion = get_suggestion("division_by_zero")
        assert suggestion is not None
        assert "Infinity" in suggestion
    
    def test_integer_overflow_suggestion(self):
        """Suggestion for integer overflow."""
        suggestion = get_suggestion("integer_overflow")
        assert suggestion is not None
        assert "2^53" in suggestion
    
    def test_unknown_suggestion(self):
        """Unknown kind returns None."""
        suggestion = get_suggestion("unknown_error_type")
        assert suggestion is None


class TestSuggestionsContent:
    """Tests for suggestion content quality."""
    
    def test_suggestions_have_examples(self):
        """Most suggestions include examples or explanations."""
        for key, suggestion in SUGGESTIONS.items():
            # Check that longer suggestions have code examples or explanations
            if len(suggestion) > 100:
                has_example = (
                    ":" in suggestion or 
                    "def " in suggestion or 
                    "class " in suggestion or
                    "→" in suggestion or  # Arrow showing transformation
                    "consider" in suggestion.lower()  # Explanation
                )
                assert has_example, f"Suggestion for {key} should have examples"
    
    def test_suggestions_are_actionable(self):
        """Suggestions tell you what to do."""
        action_words = ["Use", "Instead", "Remove", "Add", "Move", "Avoid", "Pass", "For", "Note"]
        for key, suggestion in SUGGESTIONS.items():
            has_action = any(word in suggestion for word in action_words)
            assert has_action, f"Suggestion for {key} should be actionable"


class TestTranspileError:
    """Tests for TranspileError base class."""
    
    def test_create_error(self):
        """Create a TranspileError."""
        error = TranspileError(
            message="Something went wrong",
            line=10,
            col=5,
        )
        assert error.message == "Something went wrong"
        assert error.line == 10
        assert error.col == 5
    
    def test_error_format(self):
        """Error formats correctly."""
        error = TranspileError(
            message="Error message",
            line=5,
        )
        formatted = error.format()
        assert "line 5" in formatted
        assert "Error message" in formatted
    
    def test_error_with_suggestion(self):
        """Error includes suggestion."""
        error = TranspileError(
            message="Not allowed",
            line=1,
            suggestion="Try this instead",
        )
        formatted = error.format()
        assert "Suggestion:" in formatted
        assert "Try this instead" in formatted
    
    def test_error_with_source_context(self):
        """Error shows source context."""
        error = TranspileError(
            message="Bad code",
            line=2,
            col=4,
            source="x = 1\nbad code here\ny = 2",
        )
        formatted = error.format()
        assert "bad code here" in formatted
    
    def test_error_with_filename(self):
        """Error includes filename."""
        error = TranspileError(
            message="Error",
            line=5,
            filename="handler.py",
        )
        formatted = error.format()
        assert "handler.py" in formatted
    
    def test_error_from_node(self):
        """Create error from AST node."""
        import ast
        node = ast.parse("x = 1").body[0]
        error = TranspileError.from_node(
            message="Error",
            node=node,
        )
        assert error.line == 1


class TestUnsupportedSyntax:
    """Tests for UnsupportedSyntax error."""
    
    def test_create_unsupported(self):
        """Create UnsupportedSyntax error."""
        error = UnsupportedSyntax(
            message="yield not supported",
            line=5,
        )
        assert isinstance(error, TranspileError)
    
    def test_unsupported_helper(self):
        """Use unsupported() helper."""
        import ast
        node = ast.parse("x = 1").body[0]
        error = unsupported("generators", node)
        assert "generators" in str(error)
        assert "not supported" in str(error)
    
    def test_unsupported_with_suggestion(self):
        """unsupported() with suggestion."""
        import ast
        node = ast.parse("x = 1").body[0]
        error = unsupported("yield", node, suggestion="Use @server_action")
        assert "Use @server_action" in str(error)


class TestSemanticError:
    """Tests for SemanticError."""
    
    def test_create_semantic_error(self):
        """Create SemanticError."""
        error = SemanticError(
            message="Cannot do this",
            line=10,
        )
        assert isinstance(error, TranspileError)


class TestInternalError:
    """Tests for InternalError."""
    
    def test_create_internal_error(self):
        """Create InternalError."""
        error = InternalError(
            message="Bug found",
            line=1,
        )
        assert isinstance(error, TranspileError)
    
    def test_internal_error_asks_to_report(self):
        """InternalError asks to report bug."""
        error = InternalError(
            message="Oops",
            line=1,
        )
        formatted = error.format()
        assert "bug" in formatted.lower() or "report" in formatted.lower()


class TestFormatErrorWithContext:
    """Tests for format_error_with_context function."""
    
    def test_format_with_source(self):
        """Format error with source context."""
        source = "x = 1\ny = 2\nz = 3"
        formatted = format_error_with_context(
            message="Error on line 2",
            source=source,
            line=2,
        )
        assert "y = 2" in formatted
        assert "Error on line 2" in formatted
    
    def test_format_with_caret(self):
        """Format includes caret at column."""
        source = "x = some_error_here"
        formatted = format_error_with_context(
            message="Error",
            source=source,
            line=1,
            col=4,
        )
        assert "^" in formatted
    
    def test_format_with_suggestion(self):
        """Format includes suggestion."""
        formatted = format_error_with_context(
            message="Error",
            source="x = 1",
            line=1,
            suggestion="Try something else",
        )
        assert "Suggestion:" in formatted
        assert "Try something else" in formatted
    
    def test_format_with_context_lines(self):
        """Format includes context lines."""
        source = "\n".join([f"line {i}" for i in range(10)])
        formatted = format_error_with_context(
            message="Error",
            source=source,
            line=5,
            num_context_lines=2,
        )
        # Should show lines around line 5
        assert "line 3" in formatted or "line 4" in formatted
    
    def test_format_line_at_start(self):
        """Format when error is at start of file."""
        source = "first line\nsecond line"
        formatted = format_error_with_context(
            message="Error",
            source=source,
            line=1,
        )
        assert "first line" in formatted
    
    def test_format_line_at_end(self):
        """Format when error is at end of file."""
        source = "line 1\nline 2\nlast line"
        formatted = format_error_with_context(
            message="Error",
            source=source,
            line=3,
        )
        assert "last line" in formatted


class TestErrorIntegration:
    """Integration tests for error handling."""
    
    def test_parse_error_has_context(self):
        """Parse errors include source context."""
        from pynext.transpiler import parse
        from pynext.transpiler.errors import UnsupportedSyntax
        
        try:
            parse("class Multi(A, B): pass")
        except UnsupportedSyntax as e:
            formatted = str(e)
            assert "Multiple inheritance" in formatted
    
    def test_class_metaclass_error(self):
        """Metaclass error has good message."""
        from pynext.transpiler import parse
        from pynext.transpiler.errors import UnsupportedSyntax
        
        try:
            parse("class Singleton(metaclass=Meta): pass")
        except UnsupportedSyntax as e:
            assert "Metaclass" in str(e)
    
    def test_classmethod_error(self):
        """@classmethod error has suggestion."""
        from pynext.transpiler import parse
        from pynext.transpiler.errors import UnsupportedSyntax
        
        try:
            parse("""
class Factory:
    @classmethod
    def create(cls):
        pass
""")
        except UnsupportedSyntax as e:
            assert "@classmethod" in str(e)
            assert "@staticmethod" in str(e)

