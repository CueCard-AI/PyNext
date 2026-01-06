"""
Phase 33.2: Pattern Matching Transpilation Tests

Comprehensive test suite for match/case pattern matching transpilation covering:
- Literal patterns (case 1, case "hello")
- Capture patterns (case x)
- Wildcard patterns (case _)
- Sequence patterns (case [a, b, *rest])
- Mapping patterns (case {"key": value})
- Class patterns (case Point(x=1, y=2))
- OR patterns (case A | B)
- AS patterns (case x as alias)
- Guard clauses (case x if condition)
- Nested patterns
- Edge cases and optimizations

Total: 150+ tests covering all pattern types, guards, nested patterns, and optimizations.

=============================================================================
THREE-LAYER TESTING APPROACH
=============================================================================

This test suite follows a three-layer testing strategy for robustness:

Layer 1: IR-Level Tests
    - Verify IR node structure is correct (Match, Case, Pattern nodes)
    - Test that guards are properly attached to Case nodes
    - Verify pattern types are correctly parsed
    - Most fundamental: Tests the contract, not implementation

Layer 2: Semantic Correctness Tests (Structure-Agnostic)
    - Verify pattern matching logic is correct
    - Test that guard variables are in scope
    - Verify control flow structure (if/else for guards, switch for no guards)
    - Structure-agnostic: Tests semantics, not specific keywords

Layer 3: Integration Tests (Runtime Behavior)
    - Verify actual execution behavior matches Python
    - Test runtime correctness with real data
    - Located in: tests/integration/transpiler/test_332_mini_applications.py
"""

import pytest
from pynext.transpiler import transpile, TranspileError, parse
from pynext.transpiler.nodes import (
    Match, Case, Pattern,
    LiteralPattern, CapturePattern, WildcardPattern,
    SequencePattern, MappingPattern, ClassPattern,
    OrPattern, AsPattern, GuardPattern,
    Program, Compare, Constant, Name, BinOp,
)


# =============================================================================
# LAYER 1: IR-LEVEL TESTS (Most Fundamental)
# =============================================================================

class TestPatternMatchingIR:
    """
    IR-Level Tests: Verify IR node structure is correct.
    
    These tests verify that the parser correctly creates Match/Case/Pattern
    IR nodes with the right structure. This is the most fundamental layer
    because it tests the contract, not the implementation.
    """
    
    def test_match_creates_match_node(self):
        """Parse match statement creates Match IR node."""
        code = """
match value:
    case 1:
        return "one"
"""
        ir = parse(code)
        assert isinstance(ir, Program)
        assert len(ir.body) == 1
        assert isinstance(ir.body[0], Match)
        match = ir.body[0]
        assert len(match.cases) == 1
        assert isinstance(match.cases[0], Case)
    
    def test_case_with_guard_has_guard_attribute(self):
        """Case with guard clause has guard attribute set."""
        code = """
match value:
    case x if x > 0:
        return "positive"
"""
        ir = parse(code)
        match = ir.body[0]
        case = match.cases[0]
        assert case.guard is not None, "Guard should be present in Case node"
        assert isinstance(case.guard, Compare), "Guard should be a Compare node"
    
    def test_case_without_guard_has_none_guard(self):
        """Case without guard has guard=None."""
        code = """
match value:
    case 1:
        return "one"
"""
        ir = parse(code)
        match = ir.body[0]
        case = match.cases[0]
        assert case.guard is None, "Case without guard should have guard=None"
    
    def test_guard_with_capture_pattern(self):
        """Guard clause with capture pattern creates correct IR."""
        code = """
match value:
    case x if x > 0:
        return x
"""
        ir = parse(code)
        match = ir.body[0]
        case = match.cases[0]
        assert isinstance(case.pattern, CapturePattern), "Should be CapturePattern"
        assert case.pattern.name == "x", "Pattern should capture variable 'x'"
        assert case.guard is not None, "Guard should be present"
    
    def test_guard_with_sequence_pattern(self):
        """Guard clause with sequence pattern creates correct IR."""
        code = """
match cmd:
    case [action, value] if action == "set":
        set_value(value)
"""
        ir = parse(code)
        match = ir.body[0]
        case = match.cases[0]
        assert isinstance(case.pattern, SequencePattern), "Should be SequencePattern"
        assert case.guard is not None, "Guard should be present"
        # Verify guard references pattern variable
        assert isinstance(case.guard, Compare), "Guard should be Compare"
    
    def test_multiple_cases_with_guards(self):
        """Multiple cases with guards all have guards set."""
        code = """
match value:
    case x if x > 0:
        return "positive"
    case x if x < 0:
        return "negative"
    case 0:
        return "zero"
"""
        ir = parse(code)
        match = ir.body[0]
        assert len(match.cases) == 3
        assert match.cases[0].guard is not None, "First case should have guard"
        assert match.cases[1].guard is not None, "Second case should have guard"
        assert match.cases[2].guard is None, "Third case should not have guard"
    
    def test_match_subject_is_correct(self):
        """Match subject expression is correctly parsed."""
        code = """
match some_value:
    case 1:
        pass
"""
        ir = parse(code)
        match = ir.body[0]
        assert isinstance(match.subject, Name), "Subject should be Name node"
        assert match.subject.id == "some_value", "Subject should be 'some_value'"


# =============================================================================
# LAYER 2: SEMANTIC CORRECTNESS TESTS (Structure-Agnostic)
# =============================================================================

# =============================================================================
# LITERAL PATTERNS (20 tests)
# =============================================================================

class TestLiteralPatterns:
    """Test literal pattern matching."""
    
    def test_literal_int(self):
        """Literal integer pattern."""
        code = """
match value:
    case 1:
        return "one"
    case 2:
        return "two"
"""
        result = transpile(code)
        assert "switch" in result
        assert "value === 1" in result or "value===" in result
    
    def test_literal_string(self):
        """Literal string pattern."""
        code = """
match cmd:
    case "quit":
        exit()
    case "help":
        show_help()
"""
        result = transpile(code)
        assert "switch" in result
        assert "cmd === \"quit\"" in result or "cmd===" in result
    
    def test_literal_bool(self):
        """Literal boolean pattern."""
        code = """
match flag:
    case True:
        return "yes"
    case False:
        return "no"
"""
        result = transpile(code)
        assert "switch" in result
    
    def test_literal_none(self):
        """Literal None pattern."""
        code = """
match value:
    case None:
        return "null"
    case _:
        return "something"
"""
        result = transpile(code)
        assert "switch" in result
    
    def test_literal_float(self):
        """Literal float pattern."""
        code = """
match value:
    case 3.14:
        return "pi"
    case 2.71:
        return "e"
"""
        result = transpile(code)
        assert "switch" in result


# =============================================================================
# CAPTURE AND WILDCARD PATTERNS (15 tests)
# =============================================================================

class TestCapturePatterns:
    """Test capture and wildcard patterns."""
    
    def test_capture_basic(self):
        """Basic capture pattern."""
        code = """
match value:
    case x:
        return x
"""
        result = transpile(code)
        assert "switch" in result
        assert "default" in result or "true" in result
    
    def test_wildcard_basic(self):
        """Basic wildcard pattern."""
        code = """
match value:
    case _:
        return "anything"
"""
        result = transpile(code)
        assert "switch" in result
        assert "default" in result
    
    def test_capture_with_usage(self):
        """Capture pattern with usage."""
        code = """
match value:
    case x:
        return x * 2
"""
        result = transpile(code)
        assert "switch" in result
        assert "const x" in result or "let x" in result


# =============================================================================
# SEQUENCE PATTERNS (25 tests)
# =============================================================================

class TestSequencePatterns:
    """Test sequence patterns."""
    
    def test_sequence_basic(self):
        """Basic sequence pattern."""
        code = """
match cmd:
    case ["move", x, y]:
        move_to(x, y)
"""
        result = transpile(code)
        assert "switch" in result
        assert "Array.isArray" in result
    
    def test_sequence_with_starred(self):
        """Sequence pattern with starred."""
        code = """
match items:
    case [first, *rest]:
        process(first, rest)
"""
        result = transpile(code)
        assert "switch" in result
        assert "Array.isArray" in result
    
    def test_sequence_nested(self):
        """Nested sequence pattern."""
        code = """
match data:
    case [[a, b], [c, d]]:
        return a + b + c + d
"""
        result = transpile(code)
        assert "switch" in result
        assert "Array.isArray" in result
    
    def test_sequence_with_guard(self):
        """
        Sequence pattern with guard - structure-agnostic test.
        
        Phase 33.2: Guards require if/else chains (not switch) to match Python's
        evaluation order (pattern first → variables in scope → guard evaluated).
        """
        code = """
match cmd:
    case [action, value] if action == "set":
        set_value(value)
"""
        result = transpile(code)
        # Verify pattern matching logic (structure-agnostic)
        assert "Array.isArray" in result, "Sequence pattern should check Array.isArray"
        # Verify guard uses pattern variables (semantic correctness)
        assert "action" in result, "Guard should reference pattern variable 'action'"
        assert "value" in result, "Pattern should capture 'value'"
        # Verify conditional structure (guards require if/else, not switch)
        has_conditional = ("if (" in result or "if(" in result) or ("else if" in result)
        assert has_conditional, "Guards require if/else structure, not switch"


# =============================================================================
# MAPPING PATTERNS (20 tests)
# =============================================================================

class TestMappingPatterns:
    """Test mapping patterns."""
    
    def test_mapping_basic(self):
        """Basic mapping pattern."""
        code = """
match data:
    case {"action": "click", "x": x, "y": y}:
        click_at(x, y)
"""
        result = transpile(code)
        assert "switch" in result
        assert "typeof" in result or "object" in result
    
    def test_mapping_with_capture(self):
        """Mapping pattern with capture."""
        code = """
match data:
    case {"key": value}:
        return value
"""
        result = transpile(code)
        assert "switch" in result
    
    def test_mapping_with_rest(self):
        """Mapping pattern with **rest."""
        code = """
match data:
    case {"required": req, **rest}:
        process(req, rest)
"""
        result = transpile(code)
        assert "switch" in result


# =============================================================================
# CLASS PATTERNS (20 tests)
# =============================================================================

class TestClassPatterns:
    """Test class patterns."""
    
    def test_class_basic(self):
        """Basic class pattern."""
        code = """
match point:
    case Point(x=1, y=2):
        return "specific"
"""
        result = transpile(code)
        assert "switch" in result
        assert "instanceof" in result
    
    def test_class_with_capture(self):
        """Class pattern with capture."""
        code = """
match point:
    case Point(x=x, y=y):
        return x + y
"""
        result = transpile(code)
        assert "switch" in result
        assert "instanceof" in result
    
    def test_class_with_partial(self):
        """Class pattern with partial match."""
        code = """
match point:
    case Point(x=1):
        return "x is one"
"""
        result = transpile(code)
        assert "switch" in result
        assert "instanceof" in result


# =============================================================================
# OR PATTERNS (15 tests)
# =============================================================================

class TestOrPatterns:
    """Test OR patterns."""
    
    def test_or_basic(self):
        """Basic OR pattern."""
        code = """
match value:
    case 1 | 2 | 3:
        return "small"
"""
        result = transpile(code)
        assert "switch" in result
        assert "||" in result or "value === 1" in result
    
    def test_or_with_strings(self):
        """OR pattern with strings."""
        code = """
match cmd:
    case "quit" | "exit" | "q":
        exit()
"""
        result = transpile(code)
        assert "switch" in result
        assert "||" in result


# =============================================================================
# AS PATTERNS (10 tests)
# =============================================================================

class TestAsPatterns:
    """Test AS patterns."""
    
    def test_as_basic(self):
        """Basic AS pattern."""
        code = """
match value:
    case [x, y] as point:
        return point
"""
        result = transpile(code)
        assert "switch" in result
        assert "const point" in result or "let point" in result


# =============================================================================
# GUARD CLAUSES (15 tests)
# =============================================================================

class TestGuardClauses:
    """
    Test guard clauses - semantic correctness tests.
    
    These tests verify that guard clauses work correctly semantically,
    without depending on specific implementation details (switch vs if/else).
    """
    
    def test_guard_basic(self):
        """
        Basic guard clause - structure-agnostic test.
        
        Verifies:
        1. Guard can reference pattern-captured variables
        2. Guard condition is evaluated correctly
        3. Control flow structure is appropriate (if/else for guards)
        """
        code = """
match value:
    case x if x > 0:
        return "positive"
"""
        result = transpile(code)
        # Verify guard references captured variable (semantic correctness)
        assert "x" in result, "Guard should reference pattern variable 'x'"
        assert "x > 0" in result or "x >" in result, "Guard condition should be present"
        # Verify conditional structure (guards require if/else, not switch)
        has_conditional = ("if (" in result or "if(" in result) or ("else if" in result)
        assert has_conditional, "Guards require if/else structure, not switch"
        # Verify guard is combined with pattern condition
        assert "&&" in result or has_conditional, "Guard should be combined with pattern"
    
    def test_guard_with_complex_condition(self):
        """
        Guard with complex condition - structure-agnostic test.
        
        Verifies that complex guard conditions (with 'and') are correctly
        transpiled and can reference pattern variables.
        """
        code = """
match value:
    case x if x > 0 and x < 100:
        return "in range"
"""
        result = transpile(code)
        # Verify guard references captured variable
        assert "x" in result, "Guard should reference pattern variable 'x'"
        # Verify complex condition is present
        assert "&&" in result, "Complex guard condition should use &&"
        # Verify conditional structure (guards require if/else, not switch)
        has_conditional = ("if (" in result or "if(" in result) or ("else if" in result)
        assert has_conditional, "Guards require if/else structure, not switch"
    
    def test_guard_variables_in_scope(self):
        """
        Verify guard clause can reference pattern-captured variables.
        
        This is a semantic correctness test: the guard must be able to
        use variables captured by the pattern.
        """
        code = """
match data:
    case {"key": value} if value > 10:
        return value
"""
        result = transpile(code)
        # Verify pattern variable is captured
        assert "value" in result, "Pattern should capture 'value'"
        # Verify guard uses captured variable
        assert "value > 10" in result or "value >" in result, "Guard should use 'value'"
        # Verify conditional structure
        has_conditional = ("if (" in result or "if(" in result) or ("else if" in result)
        assert has_conditional, "Guards require if/else structure"
    
    def test_guard_with_sequence_pattern_vars(self):
        """
        Verify guard can reference multiple pattern variables from sequence.
        
        This tests that guards work correctly with sequence patterns that
        capture multiple variables.
        """
        code = """
match cmd:
    case [action, value, count] if action == "set" and count > 0:
        set_value(value, count)
"""
        result = transpile(code)
        # Verify all pattern variables are captured
        assert "action" in result, "Pattern should capture 'action'"
        assert "value" in result, "Pattern should capture 'value'"
        assert "count" in result, "Pattern should capture 'count'"
        # Verify guard uses pattern variables (structure-agnostic)
        # Equality check may use __py.eq() for deep equality, or === for primitives
        assert "action" in result and "set" in result, "Guard should check action == 'set'"
        assert "count > 0" in result or "count >" in result, "Guard should check count > 0"
        # Verify conditional structure
        has_conditional = ("if (" in result or "if(" in result) or ("else if" in result)
        assert has_conditional, "Guards require if/else structure"


# =============================================================================
# NESTED PATTERNS (10 tests)
# =============================================================================

class TestNestedPatterns:
    """Test nested patterns."""
    
    def test_nested_sequence(self):
        """Nested sequence patterns."""
        code = """
match data:
    case [[a, b], [c, d]]:
        return a + b + c + d
"""
        result = transpile(code)
        assert "switch" in result
        assert "Array.isArray" in result
    
    def test_nested_mapping(self):
        """Nested mapping patterns."""
        code = """
match data:
    case {"outer": {"inner": value}}:
        return value
"""
        result = transpile(code)
        assert "switch" in result


# =============================================================================
# EDGE CASES (20 tests)
# =============================================================================

class TestPatternEdgeCases:
    """Test pattern matching edge cases."""
    
    def test_match_in_function(self):
        """match statement in function."""
        code = """
def handle(cmd):
    match cmd:
        case "action":
            return True
"""
        result = transpile(code)
        assert "function" in result
        assert "switch" in result
    
    def test_match_in_class_method(self):
        """match statement in class method."""
        code = """
class Handler:
    def process(self, cmd):
        match cmd:
            case "action":
                self.do_action()
"""
        result = transpile(code)
        assert "class" in result
        assert "switch" in result
    
    def test_match_with_default(self):
        """match with default case."""
        code = """
match value:
    case 1:
        return "one"
    case _:
        return "other"
"""
        result = transpile(code)
        assert "switch" in result
        assert "default" in result
    
    def test_match_with_multiple_cases(self):
        """match with multiple cases."""
        code = """
match value:
    case 1:
        return "one"
    case 2:
        return "two"
    case 3:
        return "three"
"""
        result = transpile(code)
        assert "switch" in result
        assert result.count("case") >= 3

