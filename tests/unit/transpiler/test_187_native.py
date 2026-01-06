"""
Phase 18.7 Tests - @js_native Escape Hatch

50 comprehensive tests for the @js_native decorator handling.

Test Categories:
1. Decorator detection (20 tests)
2. Native function handling (15 tests)
3. Decorator stripping (15 tests)
"""

import pytest
from pynext.transpiler.nodes import (
    Program, FunctionDef, Return, ExprStmt, Assignment,
    Name, Constant, BinOp, Call, Attribute,
    Decorator, DecoratedFunction,
)
from pynext.transpiler.optimizer.native import (
    is_js_native, mark_native_functions,
    strip_js_native_decorator,
    NativeOptimizer, count_native_functions,
)


# =============================================================================
# HELPERS
# =============================================================================

def make_program(stmts) -> Program:
    return Program(body=tuple(stmts))


def make_function(name: str, body: list, args: tuple = ()) -> FunctionDef:
    """Create a function definition."""
    return FunctionDef(
        name=name,
        args=args,
        body=tuple(body),
        is_async=False,
    )


def make_native_function(name: str, body: list, args: tuple = ()) -> DecoratedFunction:
    """Create a function with @js_native decorator."""
    func = make_function(name, body, args)
    return DecoratedFunction(
        decorators=(Decorator(name="js_native"),),
        function=func,
    )


def make_decorated_function(decorators: list, func: FunctionDef) -> DecoratedFunction:
    """Create a decorated function."""
    return DecoratedFunction(
        decorators=tuple(decorators),
        function=func,
    )


# =============================================================================
# 1. DECORATOR DETECTION (20 tests)
# =============================================================================

class TestDecoratorDetection:
    """Tests for detecting @js_native decorator."""
    
    def test_is_native_decorated_function(self):
        """DecoratedFunction with js_native."""
        decorated = make_native_function(
            "test_func",
            [Return(value=Constant(value=1))]
        )
        assert is_js_native(decorated) is True
    
    def test_is_native_plain_function(self):
        """Plain FunctionDef is not native."""
        func = make_function(
            "test_func",
            [Return(value=Constant(value=1))]
        )
        assert is_js_native(func) is False
    
    def test_is_native_other_decorator(self):
        """DecoratedFunction with other decorator."""
        func = make_function("test_func", [Return(value=Constant(value=1))])
        decorated = make_decorated_function(
            [Decorator(name="memoize")],
            func
        )
        assert is_js_native(decorated) is False
    
    def test_is_native_multiple_decorators_with_native(self):
        """DecoratedFunction with multiple decorators including js_native."""
        func = make_function("test_func", [Return(value=Constant(value=1))])
        decorated = make_decorated_function(
            [
                Decorator(name="memoize"),
                Decorator(name="js_native"),
            ],
            func
        )
        assert is_js_native(decorated) is True
    
    def test_is_native_multiple_decorators_without_native(self):
        """DecoratedFunction with multiple decorators without js_native."""
        func = make_function("test_func", [Return(value=Constant(value=1))])
        decorated = make_decorated_function(
            [
                Decorator(name="memoize"),
                Decorator(name="cached"),
            ],
            func
        )
        assert is_js_native(decorated) is False
    
    def test_mark_native_empty_program(self):
        """Empty program has no native functions."""
        program = make_program([])
        result = mark_native_functions(program)
        assert result == set()
    
    def test_mark_native_single_native(self):
        """Single native function."""
        decorated = make_native_function(
            "fast_sum",
            [Return(value=Constant(value=0))]
        )
        program = make_program([decorated])
        
        result = mark_native_functions(program)
        assert result == {"fast_sum"}
    
    def test_mark_native_multiple_native(self):
        """Multiple native functions."""
        decorated1 = make_native_function(
            "fast_sum",
            [Return(value=Constant(value=0))]
        )
        decorated2 = make_native_function(
            "fast_mul",
            [Return(value=Constant(value=0))]
        )
        program = make_program([decorated1, decorated2])
        
        result = mark_native_functions(program)
        assert result == {"fast_sum", "fast_mul"}
    
    def test_mark_native_mixed(self):
        """Mix of native and non-native functions."""
        decorated = make_native_function(
            "fast_sum",
            [Return(value=Constant(value=0))]
        )
        func = make_function(
            "regular_func",
            [Return(value=Constant(value=0))]
        )
        program = make_program([decorated, func])
        
        result = mark_native_functions(program)
        assert result == {"fast_sum"}
    
    def test_mark_native_only_plain_functions(self):
        """Program with only plain functions."""
        func1 = make_function("func1", [Return(value=Constant(value=0))])
        func2 = make_function("func2", [Return(value=Constant(value=0))])
        program = make_program([func1, func2])
        
        result = mark_native_functions(program)
        assert result == set()
    
    def test_is_native_non_function_node(self):
        """Non-function nodes return False."""
        assign = Assignment(target="x", value=Constant(value=1))
        assert is_js_native(assign) is False
    
    def test_count_native_functions_empty(self):
        """Count in empty program."""
        program = make_program([])
        assert count_native_functions(program) == 0
    
    def test_count_native_functions_some(self):
        """Count some native functions."""
        decorated = make_native_function(
            "fast_sum",
            [Return(value=Constant(value=0))]
        )
        func = make_function(
            "regular",
            [Return(value=Constant(value=0))]
        )
        program = make_program([decorated, func])
        
        assert count_native_functions(program) == 1
    
    def test_count_native_functions_all(self):
        """Count when all are native."""
        funcs = [
            make_native_function(
                f"func_{i}",
                [Return(value=Constant(value=i))]
            )
            for i in range(3)
        ]
        program = make_program(funcs)
        
        assert count_native_functions(program) == 3
    
    def test_is_native_case_sensitive(self):
        """js_native is case-sensitive."""
        func = make_function("test_func", [Return(value=Constant(value=1))])
        decorated = make_decorated_function(
            [Decorator(name="JS_NATIVE")],
            func
        )
        assert is_js_native(decorated) is False
    
    def test_is_native_similar_name(self):
        """Similar but not exact name."""
        func = make_function("test_func", [Return(value=Constant(value=1))])
        decorated = make_decorated_function(
            [Decorator(name="js_native_mode")],
            func
        )
        assert is_js_native(decorated) is False
    
    def test_mark_native_with_other_statements(self):
        """Mark native with other statement types."""
        assign = Assignment(target="x", value=Constant(value=1))
        decorated = make_native_function(
            "fast_sum",
            [Return(value=Constant(value=0))]
        )
        program = make_program([assign, decorated])
        
        result = mark_native_functions(program)
        assert result == {"fast_sum"}
    
    def test_is_native_empty_decorators(self):
        """DecoratedFunction with empty decorators tuple."""
        func = make_function("test_func", [Return(value=Constant(value=1))])
        decorated = DecoratedFunction(
            decorators=(),
            function=func,
        )
        assert is_js_native(decorated) is False
    
    def test_native_first_in_list(self):
        """js_native as first decorator."""
        func = make_function("test_func", [Return(value=Constant(value=1))])
        decorated = make_decorated_function(
            [
                Decorator(name="js_native"),
                Decorator(name="memoize"),
            ],
            func
        )
        assert is_js_native(decorated) is True


# =============================================================================
# 2. NATIVE FUNCTION HANDLING (15 tests)
# =============================================================================

class TestNativeFunctionHandling:
    """Tests for handling @js_native functions."""
    
    def test_optimizer_init(self):
        """Optimizer initializes with empty set."""
        opt = NativeOptimizer()
        assert opt.native_functions == set()
    
    def test_optimizer_detects_native(self):
        """Optimizer detects native functions."""
        decorated = make_native_function(
            "fast_sum",
            [Return(value=Constant(value=0))]
        )
        program = make_program([decorated])
        
        opt = NativeOptimizer()
        opt.visit(program)
        
        assert "fast_sum" in opt.native_functions
    
    def test_optimizer_skips_non_native(self):
        """Optimizer skips non-native decorated functions."""
        func = make_function("regular_func", [Return(value=Constant(value=0))])
        decorated = make_decorated_function(
            [Decorator(name="memoize")],
            func
        )
        program = make_program([decorated])
        
        opt = NativeOptimizer()
        opt.visit(program)
        
        assert opt.native_functions == set()
    
    def test_optimizer_handles_plain_function(self):
        """Optimizer handles plain FunctionDef."""
        func = make_function(
            "regular_func",
            [Return(value=Constant(value=0))]
        )
        program = make_program([func])
        
        opt = NativeOptimizer()
        opt.visit(program)
        
        assert opt.native_functions == set()
    
    def test_optimizer_handles_mixed(self):
        """Optimizer handles mix of decorated and plain."""
        decorated = make_native_function(
            "native_func",
            [Return(value=Constant(value=0))]
        )
        func = make_function(
            "regular_func",
            [Return(value=Constant(value=0))]
        )
        program = make_program([decorated, func])
        
        opt = NativeOptimizer()
        opt.visit(program)
        
        assert opt.native_functions == {"native_func"}
    
    def test_native_function_body_preserved(self):
        """Native function body is preserved."""
        body = [
            Assignment(target="x", value=Constant(value=0)),
            Return(value=Name(id="x")),
        ]
        decorated = make_native_function("fast_sum", body)
        program = make_program([decorated])
        
        opt = NativeOptimizer()
        result = opt.visit(program)
        
        result_func = result.body[0]
        assert len(result_func.body) == 2
    
    def test_native_function_args_preserved(self):
        """Native function args are preserved."""
        decorated = make_native_function(
            "fast_sum",
            [Return(value=Constant(value=0))],
            args=("items",)
        )
        program = make_program([decorated])
        
        opt = NativeOptimizer()
        result = opt.visit(program)
        
        result_func = result.body[0]
        assert result_func.args == ("items",)
    
    def test_native_async_function(self):
        """Native async function."""
        func = FunctionDef(
            name="fast_fetch",
            args=("url",),
            body=(Return(value=Constant(value=None)),),
            is_async=True,
        )
        decorated = make_decorated_function(
            [Decorator(name="js_native")],
            func
        )
        program = make_program([decorated])
        
        opt = NativeOptimizer()
        result = opt.visit(program)
        
        result_func = result.body[0]
        assert result_func.is_async is True
    
    def test_optimizer_with_other_statements(self):
        """Optimizer handles program with other statements."""
        assign = Assignment(target="x", value=Constant(value=1))
        decorated = make_native_function(
            "native_func",
            [Return(value=Constant(value=0))]
        )
        program = make_program([assign, decorated])
        
        opt = NativeOptimizer()
        result = opt.visit(program)
        
        assert len(result.body) == 2
        assert opt.native_functions == {"native_func"}
    
    def test_multiple_native_functions(self):
        """Multiple native functions detected."""
        funcs = [
            make_native_function(
                f"fast_{name}",
                [Return(value=Constant(value=0))]
            )
            for name in ["sum", "mul", "div"]
        ]
        program = make_program(funcs)
        
        opt = NativeOptimizer()
        opt.visit(program)
        
        assert len(opt.native_functions) == 3
        assert "fast_sum" in opt.native_functions
        assert "fast_mul" in opt.native_functions
        assert "fast_div" in opt.native_functions
    
    def test_empty_program(self):
        """Empty program handling."""
        program = make_program([])
        
        opt = NativeOptimizer()
        result = opt.visit(program)
        
        assert result.body == ()
        assert opt.native_functions == set()
    
    def test_decorated_function_with_other_decorators(self):
        """DecoratedFunction with multiple decorators."""
        func = make_function(
            "my_func",
            [Return(value=Constant(value=0))]
        )
        decorated = make_decorated_function(
            [
                Decorator(name="memoize"),
                Decorator(name="js_native"),
            ],
            func
        )
        program = make_program([decorated])
        
        opt = NativeOptimizer()
        result = opt.visit(program)
        
        assert "my_func" in opt.native_functions
    
    def test_decorated_function_without_native(self):
        """DecoratedFunction without js_native."""
        func = make_function(
            "my_func",
            [Return(value=Constant(value=0))]
        )
        decorated = make_decorated_function(
            [Decorator(name="memoize")],
            func
        )
        program = make_program([decorated])
        
        opt = NativeOptimizer()
        opt.visit(program)
        
        assert opt.native_functions == set()
    
    def test_native_function_with_defaults(self):
        """Native function with default arguments."""
        func = FunctionDef(
            name="fast_func",
            args=("a", "b"),
            body=(Return(value=Constant(value=0)),),
            is_async=False,
            defaults=(None, Constant(value=10)),
        )
        decorated = make_decorated_function(
            [Decorator(name="js_native")],
            func
        )
        program = make_program([decorated])
        
        opt = NativeOptimizer()
        result = opt.visit(program)
        
        result_func = result.body[0]
        assert len(result_func.defaults) == 2


# =============================================================================
# 3. DECORATOR STRIPPING (15 tests)
# =============================================================================

class TestDecoratorStripping:
    """Tests for stripping @js_native decorator."""
    
    def test_strip_single_native(self):
        """Strip single js_native decorator."""
        decorated = make_native_function(
            "test_func",
            [Return(value=Constant(value=1))]
        )
        
        result = strip_js_native_decorator(decorated)
        
        # Should return plain FunctionDef
        assert isinstance(result, FunctionDef)
        assert result.name == "test_func"
    
    def test_strip_preserves_other_decorators(self):
        """Stripping preserves other decorators."""
        func = make_function("test_func", [Return(value=Constant(value=1))])
        decorated = make_decorated_function(
            [
                Decorator(name="memoize"),
                Decorator(name="js_native"),
                Decorator(name="cached"),
            ],
            func
        )
        
        result = strip_js_native_decorator(decorated)
        
        assert isinstance(result, DecoratedFunction)
        assert len(result.decorators) == 2
        assert result.decorators[0].name == "memoize"
        assert result.decorators[1].name == "cached"
    
    def test_strip_plain_function_unchanged(self):
        """Stripping plain function returns unchanged."""
        func = make_function(
            "test_func",
            [Return(value=Constant(value=1))]
        )
        
        result = strip_js_native_decorator(func)
        
        assert result is func
    
    def test_strip_no_native_decorator(self):
        """Stripping function without js_native returns unchanged."""
        func = make_function("test_func", [Return(value=Constant(value=1))])
        decorated = make_decorated_function(
            [Decorator(name="memoize")],
            func
        )
        
        result = strip_js_native_decorator(decorated)
        
        assert isinstance(result, DecoratedFunction)
        assert len(result.decorators) == 1
        assert result.decorators[0].name == "memoize"
    
    def test_strip_preserves_name(self):
        """Stripping preserves function name."""
        decorated = make_native_function(
            "my_function",
            [Return(value=Constant(value=1))]
        )
        
        result = strip_js_native_decorator(decorated)
        
        assert result.name == "my_function"
    
    def test_strip_preserves_body(self):
        """Stripping preserves function body."""
        body = [
            Assignment(target="x", value=Constant(value=1)),
            Return(value=Name(id="x")),
        ]
        decorated = make_native_function("test_func", body)
        
        result = strip_js_native_decorator(decorated)
        
        assert len(result.body) == 2
    
    def test_strip_preserves_args(self):
        """Stripping preserves function arguments."""
        decorated = make_native_function(
            "test_func",
            [Return(value=Constant(value=1))],
            args=("a", "b", "c")
        )
        
        result = strip_js_native_decorator(decorated)
        
        assert result.args == ("a", "b", "c")
    
    def test_strip_preserves_async(self):
        """Stripping preserves async status."""
        func = FunctionDef(
            name="test_func",
            args=(),
            body=(Return(value=Constant(value=1)),),
            is_async=True,
        )
        decorated = make_decorated_function(
            [Decorator(name="js_native")],
            func
        )
        
        result = strip_js_native_decorator(decorated)
        
        assert result.is_async is True
    
    def test_optimizer_strips_decorator(self):
        """NativeOptimizer strips js_native when visiting."""
        decorated = make_native_function(
            "fast_sum",
            [Return(value=Constant(value=0))]
        )
        program = make_program([decorated])
        
        opt = NativeOptimizer()
        result = opt.visit(program)
        
        result_func = result.body[0]
        # Should be plain FunctionDef now
        assert isinstance(result_func, FunctionDef)
    
    def test_optimizer_strips_only_native(self):
        """Optimizer strips only js_native, keeps others."""
        func = make_function(
            "fast_sum",
            [Return(value=Constant(value=0))]
        )
        decorated = make_decorated_function(
            [
                Decorator(name="memoize"),
                Decorator(name="js_native"),
            ],
            func
        )
        program = make_program([decorated])
        
        opt = NativeOptimizer()
        result = opt.visit(program)
        
        result_func = result.body[0]
        assert isinstance(result_func, DecoratedFunction)
        assert len(result_func.decorators) == 1
        assert result_func.decorators[0].name == "memoize"
    
    def test_strip_returns_new_node(self):
        """Stripping returns a new node, doesn't mutate."""
        decorated = make_native_function(
            "test_func",
            [Return(value=Constant(value=1))]
        )
        
        result = strip_js_native_decorator(decorated)
        
        # Original should be unchanged
        assert len(decorated.decorators) == 1
        assert result is not decorated
    
    def test_strip_empty_decorators(self):
        """Strip with empty decorators tuple."""
        func = make_function("test_func", [Return(value=Constant(value=1))])
        decorated = DecoratedFunction(
            decorators=(),
            function=func,
        )
        
        result = strip_js_native_decorator(decorated)
        
        # No js_native to strip, returns plain function
        assert isinstance(result, FunctionDef)
    
    def test_strip_non_function_node(self):
        """Stripping non-function node returns it unchanged."""
        assign = Assignment(target="x", value=Constant(value=1))
        result = strip_js_native_decorator(assign)
        assert result is assign
    
    def test_native_at_end(self):
        """js_native as last decorator."""
        func = make_function("test_func", [Return(value=Constant(value=1))])
        decorated = make_decorated_function(
            [
                Decorator(name="memoize"),
                Decorator(name="cached"),
                Decorator(name="js_native"),
            ],
            func
        )
        
        result = strip_js_native_decorator(decorated)
        
        assert isinstance(result, DecoratedFunction)
        assert len(result.decorators) == 2
