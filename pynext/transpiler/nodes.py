"""
PyNext Transpiler - IR Node Definitions

=============================================================================
WHAT THIS FILE DOES
=============================================================================

Defines the Intermediate Representation (IR) nodes used by the transpiler.
These are simple, immutable dataclasses that represent Python constructs
in a form optimized for JavaScript code generation.

    Python AST → [Parser] → IR Nodes → [Emitter] → JavaScript

=============================================================================
WHY THIS EXISTS (Problem It Solves)
=============================================================================

Python's AST is complex and tightly coupled to Python semantics. We need
a simpler representation that:

1. Is easy to understand and debug
2. Maps cleanly to JavaScript constructs
3. Is immutable (no accidental mutations)
4. Carries source location for error messages
5. Can be serialized for debugging/logging

=============================================================================
HOW IT WORKS (Architecture)
=============================================================================

    ┌─────────────────────────────────────────────────────────────────┐
    │                         IR Node Hierarchy                        │
    ├─────────────────────────────────────────────────────────────────┤
    │                                                                  │
    │  JSNode (base)                                                   │
    │    │                                                             │
    │    ├── Statements                                                │
    │    │   ├── Assignment      x = 5                                │
    │    │   ├── AugAssign       x += 1                               │
    │    │   ├── If              if/elif/else                         │
    │    │   ├── For             for x in items:                      │
    │    │   ├── While           while cond:                          │
    │    │   ├── FunctionDef     def foo():                           │
    │    │   ├── Return          return x                             │
    │    │   ├── Pass            pass                                 │
    │    │   ├── Break           break                                │
    │    │   ├── Continue        continue                             │
    │    │   ├── Delete          del x[0]                             │
    │    │   └── ExprStmt        foo()  (expression as statement)     │
    │    │                                                             │
    │    └── Expressions                                               │
    │        ├── Name            x                                    │
    │        ├── Constant        5, "hello", True                     │
    │        ├── BinOp           a + b                                │
    │        ├── UnaryOp         -x, not x                            │
    │        ├── Compare         a < b, a == b                        │
    │        ├── BoolOp          a and b, a or b                      │
    │        ├── IfExp           a if cond else b                     │
    │        ├── Call            foo(a, b)                            │
    │        ├── Attribute       obj.attr                             │
    │        ├── Subscript       items[0], items[-1]                  │
    │        ├── Slice           items[1:3], items[::-1]              │
    │        ├── List            [1, 2, 3]                            │
    │        ├── Dict            {"a": 1}                             │
    │        ├── Tuple           (a, b)                               │
    │        ├── Lambda          lambda x: x * 2                      │
    │        └── Starred         *args                                │
    │                                                                  │
    └─────────────────────────────────────────────────────────────────┘

=============================================================================
WHO USES THIS
=============================================================================

- parser.py: Creates IR nodes from Python AST
- emitter.py: Converts IR nodes to JavaScript strings
- optimizer/: (future) Transforms IR nodes for optimization
- Tests: Verify correct IR structure

=============================================================================
WHEN TO USE (vs Alternatives)
=============================================================================

Always use these nodes as the intermediate representation. Never pass raw
Python AST nodes to the emitter - always convert to IR first.

=============================================================================
EXAMPLES
=============================================================================

Creating nodes:

```python
# x = 5
node = Assignment(
    target="x",
    value=Constant(value=5),
    line=1,
    col=0
)

# if x > 0:
#     print(x)
node = If(
    test=Compare(left=Name("x"), op="gt", right=Constant(0)),
    body=[ExprStmt(Call(func=Name("print"), args=[Name("x")]))],
    orelse=[],
    line=1,
    col=0
)
```
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional, Union


# =============================================================================
# BASE NODE
# =============================================================================

@dataclass(frozen=True)
class JSNode:
    """
    Base class for all IR nodes.
    
    All nodes carry source location (line, col) for error messages
    and source map generation.
    
    Frozen=True makes nodes immutable, preventing accidental mutations
    and enabling safe sharing/caching.
    """
    line: int = 0
    col: int = 0


# =============================================================================
# STATEMENTS
# =============================================================================

@dataclass(frozen=True)
class Assignment(JSNode):
    """
    Simple assignment: x = value
    
    Examples:
        x = 5           → let x = 5;
        x = y + 1       → let x = y + 1;
        x = [1, 2, 3]   → let x = [1, 2, 3];
    """
    target: str = ""
    value: JSNode = field(default_factory=lambda: Constant(None))


@dataclass(frozen=True)
class AugAssign(JSNode):
    """
    Augmented assignment: x += value, x -= value, etc.
    
    Examples:
        x += 1   → x += 1;
        x *= 2   → x *= 2;
        x //= 2  → x = __py.floordiv(x, 2);
    """
    target: str = ""
    op: str = ""  # "add", "sub", "mul", "div", "floordiv", "mod", "pow"
    value: JSNode = field(default_factory=lambda: Constant(None))


@dataclass(frozen=True)
class If(JSNode):
    """
    If/elif/else statement.
    
    Examples:
        if x > 0:       → if (x > 0) {
            foo()       →     foo();
        elif x < 0:     → } else if (x < 0) {
            bar()       →     bar();
        else:           → } else {
            baz()       →     baz();
                        → }
    
    The orelse field contains either:
    - An empty list (no else)
    - A list with an If node (elif chain)
    - A list of statement nodes (else block)
    """
    test: JSNode = field(default_factory=lambda: Constant(None))
    body: tuple[JSNode, ...] = field(default_factory=tuple)
    orelse: tuple[JSNode, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class For(JSNode):
    """
    For loop: for target in iter:
    
    Examples:
        for x in items:     → for (const x of items) {
            print(x)        →     console.log(x);
                            → }
        
        for i in range(10): → for (let i = 0; i < 10; i++) {
            print(i)        →     console.log(i);
                            → }
        
        for k in my_dict:   → for (const k of Object.keys(my_dict)) {
            print(k)        →     console.log(k);
                            → }
        
        async for x in gen: → for await (const x of gen) {
            await process(x) →     await process(x);
                            → }
    """
    target: str = ""
    iter: JSNode = field(default_factory=lambda: Constant(None))
    body: tuple[JSNode, ...] = field(default_factory=tuple)
    orelse: tuple[JSNode, ...] = field(default_factory=tuple)  # Phase 33.1: for...else support
    is_range: bool = False  # True if iterating over range()
    range_args: tuple[JSNode, ...] = field(default_factory=tuple)  # (start, stop, step) for range
    is_async: bool = False  # Phase 33.2: True for async for loops


@dataclass(frozen=True)
class ForUnpack(JSNode):
    """
    For loop with tuple unpacking: for a, b in items:
    
    Examples:
        for i, x in enumerate(items): → for (const [i, x] of __py.enumerate(items)) {
            print(i, x)               →     console.log(i, x);
                                      → }
        
        for k, v in d.items():        → for (const [k, v] of Object.entries(d)) {
            print(k, v)               →     console.log(k, v);
                                      → }
    """
    targets: tuple[str, ...] = field(default_factory=tuple)
    iter: JSNode = field(default_factory=lambda: Constant(None))
    body: tuple[JSNode, ...] = field(default_factory=tuple)
    orelse: tuple[JSNode, ...] = field(default_factory=tuple)  # Phase 33.1: for...else


@dataclass(frozen=True)
class While(JSNode):
    """
    While loop: while cond:
    
    Examples:
        while x > 0:    → while (x > 0) {
            x -= 1      →     x -= 1;
                        → }
    """
    test: JSNode = field(default_factory=lambda: Constant(None))
    body: tuple[JSNode, ...] = field(default_factory=tuple)
    orelse: tuple[JSNode, ...] = field(default_factory=tuple)  # Phase 33.1: while...else support


@dataclass(frozen=True)
class FunctionDef(JSNode):
    """
    Function definition: def name(args):
    
    Examples:
        def foo(a, b):          → function foo(a, b) {
            return a + b        →     return a + b;
                                → }
        
        def bar(x=1):           → function bar(x = 1) {
            return x            →     return x;
                                → }
        
        def varargs(*args):     → function varargs(...args) {
            return args         →     return args;
                                → }
        
        def kwargs(**kw):       → function kwargs(kw = {}) {
            return kw           →     return kw;
                                → }
        
        def mixed(a, *args, **kw):
            pass
            → Complex handling with rest parameters
        
        def posonly(x, y, /, z):  → function posonly(x, y, z) {
            pass                →     // Runtime validates positional-only
                                → }
        
        def kwonly(*, x, y=10): → function kwonly({x, y = 10} = {}) {
            pass                → }
    """
    name: str = ""
    args: tuple[str, ...] = field(default_factory=tuple)  # Regular positional args (after /)
    defaults: tuple[JSNode, ...] = field(default_factory=tuple)  # Default values (aligned to end of all positional args)
    posonly_args: tuple[str, ...] = field(default_factory=tuple)  # Positional-only args (before /) - Phase 33.1
    posonly_defaults: tuple[Optional[JSNode], ...] = field(default_factory=tuple)  # Positional-only defaults - Phase 33.1
    vararg: Optional[str] = None      # *args name (Phase 18.5)
    kwarg: Optional[str] = None       # **kwargs name (Phase 18.5)
    kwonly_args: tuple[str, ...] = field(default_factory=tuple)  # Keyword-only args (Phase 18.5)
    kwonly_defaults: tuple[Optional[JSNode], ...] = field(default_factory=tuple)  # Their defaults
    body: tuple[JSNode, ...] = field(default_factory=tuple)
    is_async: bool = False


@dataclass(frozen=True)
class Decorator(JSNode):
    """
    A single decorator: @name or @name(args)
    
    Examples:
        @memoize            → Decorator(name="memoize", args=())
        @debounce(300)      → Decorator(name="debounce", args=(Constant(300),))
        @log_calls          → Decorator(name="log_calls", args=())
        @validate(*rules)   → Decorator(name="validate", starred_args=(Name("rules"),))
        @config(**settings) → Decorator(name="config", double_starred_kwargs=(Name("settings"),))
    """
    name: str = ""
    args: tuple[JSNode, ...] = field(default_factory=tuple)
    kwargs: tuple[tuple[str, JSNode], ...] = field(default_factory=tuple)
    starred_args: tuple[JSNode, ...] = field(default_factory=tuple)  # *args spreads
    double_starred_kwargs: tuple[JSNode, ...] = field(default_factory=tuple)  # **kwargs spreads


@dataclass(frozen=True)
class DecoratedFunction(JSNode):
    """
    Function with decorators applied.
    
    Decorators are applied in reverse order (bottom to top in Python syntax).
    
    Examples:
        @memoize                    → const fib = __py.memoize(function fib(n) {...});
        def fib(n): ...
        
        @debounce(300)              → const search = __py.debounce(300)(function search(q) {...});
        def search(q): ...
        
        @log_calls                  → const foo = __py.log_calls(__py.memoize(function foo() {...}));
        @memoize
        def foo(): ...
    """
    decorators: tuple[Decorator, ...] = field(default_factory=tuple)
    function: FunctionDef = field(default_factory=FunctionDef)


@dataclass(frozen=True)
class Return(JSNode):
    """
    Return statement: return value
    
    Examples:
        return          → return;
        return x        → return x;
        return x, y     → return [x, y];
    """
    value: Optional[JSNode] = None


@dataclass(frozen=True)
class Pass(JSNode):
    """
    Pass statement (no-op).
    
    Examples:
        pass    → /* pass */
    """
    pass


@dataclass(frozen=True)
class Break(JSNode):
    """
    Break statement.
    
    Examples:
        break   → break;
    """
    pass


@dataclass(frozen=True)
class Continue(JSNode):
    """
    Continue statement.
    
    Examples:
        continue    → continue;
    """
    pass


@dataclass(frozen=True)
class Delete(JSNode):
    """
    Delete statement: del target
    
    Examples:
        del items[0]    → items.splice(0, 1);
        del obj["key"]  → delete obj["key"];
        del obj.attr    → delete obj.attr;
    """
    target: JSNode = field(default_factory=lambda: Constant(None))


@dataclass(frozen=True)
class ExceptHandler(JSNode):
    """
    Exception handler clause.
    
    Attributes:
        type: Exception type name (e.g., "ValueError"), or None for bare except
        name: Variable name to bind exception to, or None
        body: Statements in the handler
    
    Examples:
        except ValueError:           → catch (e) { if (e instanceof ValueError) { ... } }
        except ValueError as e:      → catch (e) { if (e instanceof ValueError) { ... } }
        except:                       → catch (e) { ... }
    """
    type: Optional[str] = None
    name: Optional[str] = None
    body: tuple = field(default_factory=tuple)


@dataclass(frozen=True)
class Try(JSNode):
    """
    Try/except/else/finally statement.
    
    Examples:
        try:                         → try {
            risky()                  →     risky();
        except ValueError as e:      → } catch (_e) {
            handle(e)                →     if (_e instanceof ValueError) { let e = _e; handle(e); }
        else:                        →     else { ... }  (runs if no exception)
            success()
        finally:                     → } finally {
            cleanup()                →     cleanup();
                                     → }
    
    Attributes:
        body: Statements in try block
        handlers: ExceptHandler clauses
        orelse: Statements in else block (runs if no exception)
        finalbody: Statements in finally block
    """
    body: tuple = field(default_factory=tuple)
    handlers: tuple = field(default_factory=tuple)  # tuple[ExceptHandler, ...]
    orelse: tuple = field(default_factory=tuple)
    finalbody: tuple = field(default_factory=tuple)


@dataclass(frozen=True)
class ExprStmt(JSNode):
    """
    Expression used as a statement (e.g., function call).
    
    Examples:
        print(x)    → console.log(x);
        foo()       → foo();
    """
    value: JSNode = field(default_factory=lambda: Constant(None))


# =============================================================================
# EXPRESSIONS
# =============================================================================

@dataclass(frozen=True)
class Name(JSNode):
    """
    Variable reference.
    
    Examples:
        x       → x
        foo     → foo
    """
    id: str = ""


@dataclass(frozen=True)
class This(JSNode):
    """
    JavaScript 'this' reference (from Python 'self').
    
    This node is created during parsing when 'self' is encountered in a method context.
    It directly emits to 'this' in JavaScript, avoiding string replacement.
    
    Examples:
        self.x      → this.x  (when This is the value of Attribute)
        return self → return this
        self.foo()  → this.foo()
    
    This is the fundamental fix for self → this transformation:
    - Parsed as This node when in MethodContext
    - Emitted directly as 'this' (no string manipulation)
    - Handles all edge cases automatically (f-strings, nested contexts, etc.)
    """
    pass


@dataclass(frozen=True)
class Constant(JSNode):
    """
    Literal constant value.
    
    Examples:
        5       → 5
        "hi"    → "hi"
        True    → true
        None    → null
    """
    value: Any = None


@dataclass(frozen=True)
class BinOp(JSNode):
    """
    Binary operation: left op right
    
    Examples:
        a + b   → a + b
        a - b   → a - b
        a * b   → a * b  (but "a" * 3 → "a".repeat(3))
        a / b   → a / b
        a // b  → __py.floordiv(a, b)
        a % b   → __py.mod(a, b)
        a ** b  → a ** b
    """
    left: JSNode = field(default_factory=lambda: Constant(None))
    op: str = ""  # "add", "sub", "mul", "div", "floordiv", "mod", "pow"
    right: JSNode = field(default_factory=lambda: Constant(None))


@dataclass(frozen=True)
class UnaryOp(JSNode):
    """
    Unary operation: op operand
    
    Examples:
        -x      → -x
        +x      → +x
        not x   → !__py.bool(x)
        ~x      → ~x
    """
    op: str = ""  # "neg", "pos", "not", "invert"
    operand: JSNode = field(default_factory=lambda: Constant(None))


@dataclass(frozen=True)
class Compare(JSNode):
    """
    Comparison: left op right (or chained: a < b < c)
    
    Examples:
        a == b      → __py.eq(a, b)
        a != b      → !__py.eq(a, b)
        a < b       → a < b
        a <= b      → a <= b
        a > b       → a > b
        a >= b      → a >= b
        a is None   → a === null
        a is not None → a !== null
        a in b      → __py.in(a, b)
        a < b < c   → a < b && b < c
    """
    left: JSNode = field(default_factory=lambda: Constant(None))
    ops: tuple[str, ...] = field(default_factory=tuple)  # "eq", "ne", "lt", "le", "gt", "ge", "is", "isnot", "in", "notin"
    comparators: tuple[JSNode, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class BoolOp(JSNode):
    """
    Boolean operation: a and b, a or b
    
    Examples:
        a and b     → __py.bool(a) ? b : a
        a or b      → __py.bool(a) ? a : b
        a and b and c → (__py.bool(a) ? (__py.bool(b) ? c : b) : a)
    """
    op: str = ""  # "and", "or"
    values: tuple[JSNode, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class IfExp(JSNode):
    """
    Conditional expression (ternary): body if test else orelse
    
    Examples:
        x if cond else y    → cond ? x : y
    """
    test: JSNode = field(default_factory=lambda: Constant(None))
    body: JSNode = field(default_factory=lambda: Constant(None))
    orelse: JSNode = field(default_factory=lambda: Constant(None))


@dataclass(frozen=True)
class Call(JSNode):
    """
    Function call: func(args, **kwargs)
    
    Examples:
        foo()           → foo()
        foo(1, 2)       → foo(1, 2)
        foo(a=1)        → foo({a: 1})  or handled specially
        print(x)        → console.log(x)
        len(items)      → items.length
    """
    func: JSNode = field(default_factory=lambda: Constant(None))
    args: tuple[JSNode, ...] = field(default_factory=tuple)
    keywords: tuple[tuple[str, JSNode], ...] = field(default_factory=tuple)  # (name, value) pairs


@dataclass(frozen=True)
class Attribute(JSNode):
    """
    Attribute access: obj.attr
    
    Examples:
        obj.foo     → obj.foo
        s.lower()   → s.toLowerCase()  (method mapping in emitter)
    """
    value: JSNode = field(default_factory=lambda: Constant(None))
    attr: str = ""


@dataclass(frozen=True)
class Subscript(JSNode):
    """
    Subscript access: obj[key]
    
    Examples:
        items[0]    → items[0]
        items[-1]   → __py.at(items, -1)
        items[1:3]  → __py.slice(items, 1, 3)
        d["key"]    → d["key"]
    """
    value: JSNode = field(default_factory=lambda: Constant(None))
    slice: JSNode = field(default_factory=lambda: Constant(None))
    is_negative: bool = False  # True if index might be negative


@dataclass(frozen=True)
class Slice(JSNode):
    """
    Slice specification: start:stop:step
    
    Examples:
        [1:3]       → __py.slice(arr, 1, 3)
        [:3]        → __py.slice(arr, null, 3)
        [1:]        → __py.slice(arr, 1, null)
        [::2]       → __py.slice(arr, null, null, 2)
        [::-1]      → __py.slice(arr, null, null, -1)
    """
    lower: Optional[JSNode] = None
    upper: Optional[JSNode] = None
    step: Optional[JSNode] = None


@dataclass(frozen=True)
class List(JSNode):
    """
    List literal: [a, b, c]
    
    Examples:
        []          → []
        [1, 2, 3]   → [1, 2, 3]
        [*a, *b]    → [...a, ...b]
    """
    elts: tuple[JSNode, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Dict(JSNode):
    """
    Dictionary literal: {k: v}
    
    Examples:
        {}              → {}
        {"a": 1}        → {"a": 1}
        {**a, **b}      → {...a, ...b}
    """
    keys: tuple[Optional[JSNode], ...] = field(default_factory=tuple)  # None for **spread
    values: tuple[JSNode, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Tuple(JSNode):
    """
    Tuple literal: (a, b, c)
    
    Transpiles to array since JS has no tuple type.
    
    Examples:
        (1, 2)      → [1, 2]
        x, y        → [x, y]
    """
    elts: tuple[JSNode, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Lambda(JSNode):
    """
    Lambda expression: lambda args: body
    
    Examples:
        lambda x: x * 2           → (x) => x * 2
        lambda x, y: x + y        → (x, y) => x + y
        lambda: 42                → () => 42
        lambda *args: len(args)  → (...args) => args.length
        lambda **kw: len(kw)      → (kw = {}) => Object.keys(kw).length
        lambda x, y=10: x + y     → (x, y = 10) => x + y
    
    Phase 33.1: Enhanced to support *args, **kwargs, and default arguments.
    Note: Lambdas don't support positional-only or keyword-only args in Python.
    """
    args: tuple[str, ...] = field(default_factory=tuple)
    defaults: tuple[JSNode, ...] = field(default_factory=tuple)
    vararg: Optional[str] = None      # *args name - Phase 33.1
    kwarg: Optional[str] = None       # **kwargs name - Phase 33.1
    body: JSNode = field(default_factory=lambda: Constant(None))


@dataclass(frozen=True)
class Await(JSNode):
    """
    Await expression: await value
    
    Used in async functions to wait for promises/coroutines.
    
    Examples:
        await fetch(url)           → await fetch(url)
        await response.json()      → await response.json()
        x = await get_data()       → let x = await get_data();
        await (await fetch()).json() → await (await fetch()).json()
    
    Note: Must be inside an async function, the parser validates this.
    """
    value: JSNode = field(default_factory=lambda: Constant(None))


@dataclass(frozen=True)
class Starred(JSNode):
    """
    Starred expression: *args (spread)
    
    Examples:
        [*items]    → [...items]
        foo(*args)  → foo(...args)
    """
    value: JSNode = field(default_factory=lambda: Constant(None))


@dataclass(frozen=True) 
class DictSpread(JSNode):
    """
    Dictionary spread: **kwargs
    
    Examples:
        {**d}       → {...d}
    """
    value: JSNode = field(default_factory=lambda: Constant(None))


# =============================================================================
# F-STRINGS
# =============================================================================

@dataclass(frozen=True)
class FString(JSNode):
    """
    F-string: f"Hello {name}" → `Hello ${name}`

    Examples:
        f"Hello {name}"      → `Hello ${name}`
        f"Value: {x:.2f}"    → `Value: ${__py.format(x, '.2f')}`
        f"{a} + {b} = {c}"   → `${a} + ${b} = ${c}`
        f"{obj!r}"           → `${__py.repr(obj)}`  (repr conversion)
        f"{val!s}"           → `${String(val)}`     (str conversion)
    """
    parts: tuple = field(default_factory=tuple)  # Alternating str and JSNode
    format_specs: tuple[str, ...] = field(default_factory=tuple)  # One per expression
    conversions: tuple[str, ...] = field(default_factory=tuple)  # 's', 'r', 'a', or '' per expression


@dataclass(frozen=True)
class FormattedValue(JSNode):
    """
    Single formatted value in an f-string: {x:.2f}
    
    Examples:
        {x}         → ${x}
        {x:.2f}     → ${__py.format(x, '.2f')}
        {x:>10}     → ${x.padStart(10)}
    """
    value: JSNode = field(default_factory=lambda: Constant(None))
    format_spec: str = ""
    conversion: str = ""  # 's', 'r', 'a' for str(), repr(), ascii()


# =============================================================================
# COMPREHENSIONS
# =============================================================================

@dataclass(frozen=True)
class Comprehension(JSNode):
    """
    Single for...in...if clause in a comprehension.
    
    Examples:
        for x in items if x > 0
    """
    target: str = ""
    targets: tuple[str, ...] = field(default_factory=tuple)  # For tuple unpacking
    iter: JSNode = field(default_factory=lambda: Constant(None))
    ifs: tuple[JSNode, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ListComp(JSNode):
    """
    List comprehension: [expr for ... in ... if ...]
    
    Examples:
        [x*2 for x in items]           → items.map(x => x*2)
        [x for x in items if x > 0]    → items.filter(x => x > 0)
        [x*2 for x in items if x > 0]  → items.filter(x => x > 0).map(x => x*2)
    """
    element: JSNode = field(default_factory=lambda: Constant(None))
    generators: tuple[Comprehension, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class DictComp(JSNode):
    """
    Dict comprehension: {k: v for ... in ... if ...}
    
    Examples:
        {k: v for k, v in items}  → Object.fromEntries(items)
        {k: v*2 for k, v in items if v > 0}  → Object.fromEntries(...)
    """
    key: JSNode = field(default_factory=lambda: Constant(None))
    value: JSNode = field(default_factory=lambda: Constant(None))
    generators: tuple[Comprehension, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class SetComp(JSNode):
    """
    Set comprehension: {expr for ... in ... if ...}
    
    Examples:
        {x for x in items}           → new Set(items)
        {x*2 for x in items if x}    → new Set(items.filter(x => x).map(x => x*2))
    """
    element: JSNode = field(default_factory=lambda: Constant(None))
    generators: tuple[Comprehension, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class GeneratorExp(JSNode):
    """
    Generator expression: (expr for ... in ... if ...)
    
    Usually appears in function calls like sum(), any(), all().
    
    Examples:
        sum(x for x in items)     → __py.sum(items)
        any(x > 0 for x in items) → items.some(x => x > 0)
    """
    element: JSNode = field(default_factory=lambda: Constant(None))
    generators: tuple[Comprehension, ...] = field(default_factory=tuple)


# =============================================================================
# TUPLE UNPACKING
# =============================================================================

@dataclass(frozen=True)
class TupleUnpack(JSNode):
    """
    Tuple unpacking assignment: a, b = value
    
    Examples:
        a, b = pair         → const [a, b] = pair;
        a, b = b, a         → [a, b] = [b, a];
        first, *rest = lst  → const [first, ...rest] = lst;
        a, *m, z = lst      → const [a, ...m] = lst; const z = m.pop();
    """
    targets: tuple[str, ...] = field(default_factory=tuple)
    starred_index: Optional[int] = None  # Index of starred target, or None
    value: JSNode = field(default_factory=lambda: Constant(None))


# =============================================================================
# PROGRAM CONTAINER
# =============================================================================

@dataclass(frozen=True)
class Program(JSNode):
    """
    Top-level program (list of statements).
    
    Used as the root node when transpiling a function body.
    """
    body: tuple[JSNode, ...] = field(default_factory=tuple)


# =============================================================================
# CLASSES (Phase 18.8)
# =============================================================================

@dataclass(frozen=True)
class ClassDef(JSNode):
    """
    Python class definition → JavaScript class.
    
    Supports single inheritance only. Multiple inheritance raises an error
    with a helpful suggestion to use composition.
    
    Examples:
        class Todo:                     → class Todo {
            def __init__(self, title):  →     constructor(title) {
                self.title = title      →         this.title = title;
                                        →     }
                                        → }
        
        class Child(Parent):            → class Child extends Parent {
            def __init__(self):         →     constructor() {
                super().__init__()      →         super();
                                        →     }
                                        → }
    
    Attributes:
        name: Class name
        bases: Base class names (first is primary, rest are mixins for multiple inheritance)
        mixins: Additional base classes for multiple inheritance (Phase 33.1)
        body: List of MethodDef, PropertyDef, or other class body nodes
        decorators: Class decorators (limited support)
        is_dataclass: Whether this class is decorated with @dataclass
        dataclass_fields: Field definitions for @dataclass (name, type_hint, default)
        is_abstract: Whether this class extends ABC (Abstract Base Class)
        abstract_methods: List of abstract method names (Phase 33.1)
    """
    name: str = ""
    bases: tuple[str, ...] = field(default_factory=tuple)  # First base is primary (extends), rest are mixins
    mixins: tuple[str, ...] = field(default_factory=tuple)  # Phase 33.1: Additional mixin classes
    body: tuple[JSNode, ...] = field(default_factory=tuple)
    decorators: tuple["Decorator", ...] = field(default_factory=tuple)
    is_dataclass: bool = False  # Phase 33.1: @dataclass support
    dataclass_fields: tuple[tuple[str, str, "JSNode | None"], ...] = field(default_factory=tuple)  # (name, type_hint, default)
    is_abstract: bool = False  # Phase 33.1: ABC support
    abstract_methods: tuple[str, ...] = field(default_factory=tuple)  # Phase 33.1: Abstract method names
    has_call_method: bool = False  # Phase 33.2: True if class has __call__ method


@dataclass(frozen=True)
class MethodDef(JSNode):
    """
    Method definition within a class.
    
    The 'self' or 'cls' parameter is automatically stripped during parsing.
    
    Examples:
        def toggle(self):               → toggle() {
            self.done = not self.done   →     this.done = !this.done;
                                        → }
        
        @staticmethod                   → static validate(title) {
        def validate(title):            →     return title.length > 0;
            return len(title) > 0       → }
        
        @classmethod                    → static from_dict(data) {
        def from_dict(cls, data):       →     const cls = this.constructor ?? this;
            return cls(**data)          →     return new cls(data);
                                        → }
        
        async def fetch_data(self):     → async fetch_data() {
            ...                         →     ...
                                        → }
    
    Attributes:
        name: Method name (or "constructor" for __init__)
        args: Parameter names (excludes 'self' or 'cls')
        defaults: Default values for parameters
        body: Method body statements
        is_static: True if @staticmethod decorated
        is_classmethod: True if @classmethod decorated (Phase 33.1)
        is_abstract: True if @abstractmethod decorated (Phase 33.1)
        is_async: True if async def
        is_private: True if method name starts with single underscore (Phase 33.1)
        is_mangled: True if method name starts with double underscore (Phase 33.1)
    """
    name: str = ""
    args: tuple[str, ...] = field(default_factory=tuple)
    defaults: tuple[JSNode, ...] = field(default_factory=tuple)
    vararg: Optional[str] = None  # Phase 33.1: *args support
    kwarg: Optional[str] = None  # Phase 33.1: **kwargs support
    kwonly_args: tuple[str, ...] = field(default_factory=tuple)  # Phase 33.1: Keyword-only args
    kwonly_defaults: tuple[Optional[JSNode], ...] = field(default_factory=tuple)  # Phase 33.1: Keyword-only defaults
    body: tuple[JSNode, ...] = field(default_factory=tuple)
    is_static: bool = False
    is_classmethod: bool = False  # Phase 33.1: @classmethod support
    is_abstract: bool = False  # Phase 33.1: @abstractmethod support
    is_async: bool = False
    is_private: bool = False  # Phase 33.1: Single underscore prefix
    is_mangled: bool = False  # Phase 33.1: Double underscore prefix (name mangling)


@dataclass(frozen=True)
class PropertyDef(JSNode):
    """
    Property getter definition (from @property decorator).
    
    Examples:
        @property                       → get status() {
        def status(self):               →     return this.done ? "Done" : "Pending";
            return "Done" if self.done  → }
                   else "Pending"
    
    Attributes:
        name: Property name
        body: Getter body statements
    """
    name: str = ""
    body: tuple[JSNode, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class PropertySetterDef(JSNode):
    """
    Property setter definition (from @name.setter decorator).
    
    Examples:
        @value.setter                   → set value(val) {
        def value(self, val):           →     this._value = val;
            self._value = val           → }
    
    Attributes:
        name: Property name (must match a @property getter)
        arg: Setter argument name (the value parameter)
        body: Setter body statements
    """
    name: str = ""
    arg: str = ""
    body: tuple[JSNode, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class PropertyDeleterDef(JSNode):
    """
    Property deleter definition (from @name.deleter decorator) - Phase 33.1.
    
    Examples:
        @value.deleter                  → delete value() {
        def value(self):                →     delete this._value;
            del self._value             → }
    
    Attributes:
        name: Property name (must match a @property getter)
        body: Deleter body statements
    """
    name: str = ""
    body: tuple[JSNode, ...] = field(default_factory=tuple)


# =============================================================================
# ASSERT STATEMENT (Phase 18.8)
# =============================================================================

@dataclass(frozen=True)
class Assert(JSNode):
    """
    Assert statement: assert condition, message
    
    Transpiles to an if-throw pattern.
    
    Examples:
        assert x > 0                    → if (!(x > 0)) {
                                        →     throw new Error("AssertionError");
                                        → }
        
        assert x > 0, "must be pos"     → if (!(x > 0)) {
                                        →     throw new Error("AssertionError: must be pos");
                                        → }
    
    Attributes:
        test: The condition to assert
        msg: Optional error message (can be any expression)
    """
    test: JSNode = field(default_factory=lambda: Constant(None))
    msg: Optional[JSNode] = None


# =============================================================================
# WALRUS OPERATOR (Phase 18.8)
# =============================================================================

@dataclass(frozen=True)
class NamedExpr(JSNode):
    """
    Named expression (walrus operator): (x := value)
    
    Allows assignment as an expression. In JavaScript, we pre-declare
    the variable and use assignment expression.
    
    Examples:
        if (x := get_value()):          → let x;
            use(x)                      → if (x = get_value()) {
                                        →     use(x);
                                        → }
        
        while (line := read()):         → let line;
            process(line)               → while (line = read()) {
                                        →     process(line);
                                        → }
        
        [y for x in items               → items.map(x => {
         if (y := transform(x))]        →     let y;
                                        →     if (y = transform(x)) return y;
                                        → }).filter(x => x !== undefined)
    
    Attributes:
        target: Variable name to assign to
        value: Expression to evaluate and assign
    """
    target: str = ""
    value: JSNode = field(default_factory=lambda: Constant(None))


# =============================================================================
# PHASE 33.2: ADVANCED CONSTRUCTS
# =============================================================================

# =============================================================================
# DUNDER METHODS (Phase 33.2)
# =============================================================================

@dataclass(frozen=True)
class DunderMethod(JSNode):
    """
    Dunder method definition (special method like __str__, __eq__, etc.).
    
    Dunder methods are Python's way of enabling operator overloading and
    special behaviors. They are transpiled to JavaScript equivalents:
    - __str__ → toString()
    - __repr__ → Symbol.for("repr")
    - __eq__ → equals() method or direct === when optimized
    - __iter__ → Symbol.iterator
    - __getitem__ → Proxy handler
    
    Examples:
        def __str__(self):              → toString() {
            return f"{self.x}"              return `${this.x}`;
                                        → }
        
        def __eq__(self, other):        → equals(other) {
            return self.x == other.x         return this.x === other.x;
                                        → }
        
        def __iter__(self):             → *[Symbol.iterator]() {
            yield self.x                    yield this.x;
            yield self.y                    yield this.y;
                                        → }
    
    Attributes:
        name: Dunder method name (e.g., "__str__", "__eq__", "__iter__")
        args: Parameter names (excludes 'self')
        defaults: Default values for parameters
        body: Method body statements
        dunder_type: Category of dunder method for optimization:
            - "string": __str__, __repr__, __format__
            - "comparison": __eq__, __ne__, __lt__, __gt__, __le__, __ge__
            - "container": __len__, __bool__, __iter__, __next__, __contains__, __getitem__, __setitem__, __delitem__
            - "arithmetic": __add__, __sub__, __mul__, __truediv__, __radd__, etc.
            - "callable": __call__
            - "attribute": __getattr__, __setattr__, __delattr__
    """
    name: str = ""  # e.g., "__str__", "__eq__", "__iter__"
    args: tuple[str, ...] = field(default_factory=tuple)
    defaults: tuple[JSNode, ...] = field(default_factory=tuple)
    body: tuple[JSNode, ...] = field(default_factory=tuple)
    dunder_type: str = ""  # "string", "comparison", "container", "arithmetic", "callable", "attribute"


# =============================================================================
# GENERATORS (Phase 33.2)
# =============================================================================

@dataclass(frozen=True)
class Yield(JSNode):
    """
    Yield statement: yield expression
    
    Transpiles to JavaScript yield keyword in generator functions.
    
    Examples:
        def gen():                      → function* gen() {
            yield 1                         yield 1;
            yield 2                         yield 2;
                                        → }
        
        def gen():                      → function* gen() {
            x = yield value                let x = yield value;
                                        → }
    
    Attributes:
        value: Expression to yield (can be None for yield without value)
    """
    value: Optional[JSNode] = None


@dataclass(frozen=True)
class YieldFrom(JSNode):
    """
    Yield from statement: yield from iterable
    
    Transpiles to JavaScript yield* for generator delegation.
    
    Examples:
        def flatten(nested):            → function* flatten(nested) {
            for item in nested:             for (const item of nested) {
                if isinstance(item, list):      if (Array.isArray(item)) {
                    yield from flatten(item)        yield* flatten(item);
                else:                           } else {
                    yield item                      yield item;
                                                }
                                            }
                                        → }
    
    Attributes:
        value: Iterable to yield from (generator or iterable)
    """
    value: JSNode = field(default_factory=lambda: Constant(None))


# =============================================================================
# CONTEXT MANAGERS (Phase 33.2)
# =============================================================================

@dataclass(frozen=True)
class WithItem(JSNode):
    """
    Individual context manager item in a with statement.
    
    Examples:
        with open("file.txt") as f:     → const f = open("file.txt");
            ...                          → try { ... } finally { f.close(); }
    
    Attributes:
        context_expr: Expression that returns a context manager
        optional_vars: Optional variable name(s) to bind the context manager to
        is_async: True if this is an async with statement
    """
    context_expr: JSNode = field(default_factory=lambda: Constant(None))
    optional_vars: Optional[Union[str, tuple[str, ...]]] = None  # Can be single name or tuple for multiple
    is_async: bool = False


@dataclass(frozen=True)
class With(JSNode):
    """
    With statement: with context as var:
    
    Transpiles to try/finally pattern with __enter__/__exit__ protocol.
    
    Examples:
        with resource() as r:            → const r = resource();
            use(r)                       → try {
                                        →     use(r);
                                        → } finally {
                                        →     r.__exit__();
                                        → }
        
        with r1() as a, r2() as b:       → const a = r1();
            process(a, b)                → try {
                                        →     const b = r2();
                                        →     try {
                                        →         process(a, b);
                                        →     } finally {
                                        →         b.__exit__();
                                        →     }
                                        → } finally {
                                        →     a.__exit__();
                                        → }
    
    Attributes:
        items: List of WithItem (context managers)
        body: Statements in the with block
        orelse: Optional else clause (runs if no exception)
    """
    items: tuple[WithItem, ...] = field(default_factory=tuple)
    body: tuple[JSNode, ...] = field(default_factory=tuple)
    orelse: tuple[JSNode, ...] = field(default_factory=tuple)


# =============================================================================
# PATTERN MATCHING (Phase 33.2)
# =============================================================================

@dataclass(frozen=True)
class Pattern(JSNode):
    """
    Base class for pattern matching patterns.
    
    Patterns are used in match/case statements to match values.
    Different pattern types are represented by subclasses.
    """
    pass


@dataclass(frozen=True)
class LiteralPattern(Pattern):
    """
    Literal pattern: case 1:, case "hello":
    
    Matches exact literal values.
    
    Examples:
        match x:                        → switch (true) {
            case 1: ...                     case x === 1: ...
            case "hello": ...               case x === "hello": ...
                                        → }
    
    Attributes:
        value: Literal value to match (number, string, bool, None)
    """
    value: JSNode = field(default_factory=lambda: Constant(None))


@dataclass(frozen=True)
class CapturePattern(Pattern):
    """
    Capture pattern: case x:
    
    Captures the matched value into a variable.
    
    Examples:
        match value:                    → switch (true) {
            case x: ...                     default: const x = value; ...
                                        → }
    
    Attributes:
        name: Variable name to capture into
    """
    name: str = ""


@dataclass(frozen=True)
class WildcardPattern(Pattern):
    """
    Wildcard pattern: case _:
    
    Matches anything (always succeeds).
    
    Examples:
        match value:                    → switch (true) {
            case _: ...                     default: ...
                                        → }
    """
    pass


@dataclass(frozen=True)
class SequencePattern(Pattern):
    """
    Sequence pattern: case [a, b, *rest]:
    
    Matches sequences (lists, tuples) with unpacking.
    
    Examples:
        match cmd:                      → switch (true) {
            case ["move", x, y]: ...        case Array.isArray(cmd) && cmd.length >= 2 && cmd[0] === "move":
                                                const x = cmd[1];
                                                const y = cmd[2];
                                                ...
    
    Attributes:
        patterns: List of patterns to match against sequence elements
        starred: Optional starred pattern name for rest elements
    """
    patterns: tuple[Pattern, ...] = field(default_factory=tuple)
    starred: Optional[str] = None


@dataclass(frozen=True)
class MappingPattern(Pattern):
    """
    Mapping pattern: case {"key": value}:
    
    Matches dictionaries/objects with key-value pairs.
    
    Examples:
        match data:                     → switch (true) {
            case {"action": "click"}: ...    case typeof data === "object" && data.action === "click": ...
                                        → }
    
    Attributes:
        keys: List of key patterns (can be literal or capture)
        values: List of value patterns (corresponding to keys)
        rest: Optional variable name to capture remaining keys
    """
    keys: tuple[Pattern, ...] = field(default_factory=tuple)
    values: tuple[Pattern, ...] = field(default_factory=tuple)
    rest: Optional[str] = None


@dataclass(frozen=True)
class ClassPattern(Pattern):
    """
    Class pattern: case Point(x=1, y=2):
    
    Matches class instances with attribute patterns.
    
    Examples:
        match point:                    → switch (true) {
            case Point(x=1, y=2): ...       case point instanceof Point && point.x === 1 && point.y === 2: ...
                                        → }
    
    Attributes:
        class_name: Class name to match
        keyword_patterns: Dictionary of attribute name → pattern mappings
    """
    class_name: str = ""
    keyword_patterns: tuple[tuple[str, Pattern], ...] = field(default_factory=tuple)  # (attr_name, pattern) pairs


@dataclass(frozen=True)
class OrPattern(Pattern):
    """
    OR pattern: case A | B:
    
    Matches if any of the patterns match.
    
    Examples:
        match value:                    → switch (true) {
            case 1 | 2 | 3: ...             case value === 1 || value === 2 || value === 3: ...
                                        → }
    
    Attributes:
        patterns: List of alternative patterns
    """
    patterns: tuple[Pattern, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class AsPattern(Pattern):
    """
    AS pattern: case x as alias:
    
    Matches a pattern and binds it to an alias.
    
    Examples:
        match value:                    → switch (true) {
            case [x, y] as point: ...       case Array.isArray(value) && value.length >= 2:
                                                const point = value;
                                                const x = value[0];
                                                const y = value[1];
                                                ...
    
    Attributes:
        pattern: Pattern to match
        alias: Variable name to bind the matched value to
    """
    pattern: Pattern = field(default_factory=lambda: WildcardPattern())
    alias: str = ""


@dataclass(frozen=True)
class GuardPattern(Pattern):
    """
    Pattern with guard clause: case x if condition:
    
    Matches pattern only if guard condition is true.
    
    Examples:
        match value:                    → switch (true) {
            case x if x > 0: ...            case (const x = value) && x > 0: ...
                                        → }
    
    Attributes:
        pattern: Pattern to match
        guard: Guard condition expression
    """
    pattern: Pattern = field(default_factory=lambda: WildcardPattern())
    guard: JSNode = field(default_factory=lambda: Constant(None))


@dataclass(frozen=True)
class Case(JSNode):
    """
    Case clause in a match statement.
    
    Examples:
        match value:                    → switch (true) {
            case 1:                          case value === 1:
                return "one"                     return "one";
            case 2:                              break;
                                        →     case value === 2:
                                        →         return "two";
                                        → }
    
    Attributes:
        pattern: Pattern to match
        guard: Optional guard condition
        body: Statements to execute if pattern matches
    """
    pattern: Pattern = field(default_factory=lambda: WildcardPattern())
    guard: Optional[JSNode] = None
    body: tuple[JSNode, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Match(JSNode):
    """
    Match statement: match value: case pattern: ...
    
    Transpiles to optimized switch/if chains.
    
    Examples:
        match command:                  → switch (true) {
            case "quit":                     case command === "quit":
                exit()                          exit();
            case "help":                         break;
                show_help()                  case command === "help":
            case _:                          show_help();
                unknown()                         break;
                                        →     default:
                                        →         unknown();
                                        → }
    
    Attributes:
        subject: Expression to match against
        cases: List of Case clauses
    """
    subject: JSNode = field(default_factory=lambda: Constant(None))
    cases: tuple[Case, ...] = field(default_factory=tuple)


# =============================================================================
# ASYNC SUPPORT (Phase 33.2)
# =============================================================================

@dataclass(frozen=True)
class AsyncFunctionDef(JSNode):
    """
    Async function definition: async def name():
    
    Extends FunctionDef with async semantics. Transpiles to async function.
    
    Examples:
        async def fetch():               → async function fetch() {
            data = await get_data()          const data = await get_data();
            return data                      return data;
                                        → }
    
    Attributes:
        name: Function name
        args: Parameter names
        defaults: Default values for parameters
        vararg: *args parameter name (if any)
        kwarg: **kwargs parameter name (if any)
        kwonly_args: Keyword-only argument names
        kwonly_defaults: Default values for keyword-only arguments
        body: Function body statements
        decorators: Function decorators
        returns: Return type annotation (informational)
    """
    name: str = ""
    posonly_args: tuple[str, ...] = field(default_factory=tuple)  # Positional-only args (before /) - Phase 33.1
    posonly_defaults: tuple[Optional[JSNode], ...] = field(default_factory=tuple)  # Positional-only defaults - Phase 33.1
    args: tuple[str, ...] = field(default_factory=tuple)
    defaults: tuple[JSNode, ...] = field(default_factory=tuple)
    vararg: Optional[str] = None
    kwarg: Optional[str] = None
    kwonly_args: tuple[str, ...] = field(default_factory=tuple)
    kwonly_defaults: tuple[Optional[JSNode], ...] = field(default_factory=tuple)
    body: tuple[JSNode, ...] = field(default_factory=tuple)
    decorators: tuple["Decorator", ...] = field(default_factory=tuple)
    returns: Optional[JSNode] = None


# =============================================================================
# IMPORTS (Phase 33.3)
# =============================================================================

@dataclass(frozen=True)
class Import(JSNode):
    """
    Import statement: import module [as alias]
    
    WHAT: Represents Python 'import module' statements.
    WHY: Converts Python imports to JavaScript ES6 imports.
    HOW: Stores module name, alias, and resolved path.
    WHO: Generated by imports.py when parsing ast.Import.
    WHEN: During AST parsing phase.
    WHERE: Part of import system IR.
    
    Examples:
        import json → Import(module="json", alias="json", path="./json.js")
        import json as j → Import(module="json", alias="j", path="./json.js")
    
    Attributes:
        module: Python module name (e.g., "json", "package.module")
        alias: JavaScript variable name (e.g., "json", "j")
        path: Resolved JavaScript import path (e.g., "./json.js")
        is_type_checking: True if inside `if TYPE_CHECKING:` block (Phase 33.3)
    """
    module: str = ""
    alias: str = ""
    path: str = ""
    is_type_checking: bool = False  # Phase 33.3: Stripped at runtime if True


@dataclass(frozen=True)
class ImportFrom(JSNode):
    """
    From import statement: from module import x, y [as alias]
    
    WHAT: Represents Python 'from module import ...' statements.
    WHY: Converts Python from imports to JavaScript ES6 named imports.
    HOW: Stores module name, import names, and resolved path.
    WHO: Generated by imports.py when parsing ast.ImportFrom.
    WHEN: During AST parsing phase.
    WHERE: Part of import system IR.
    
    Examples:
        from module import x, y → ImportFrom(module="module", names=[("x", "x"), ("y", "y")], path="./module.js")
        from . import utils → ImportFrom(module=None, names=[("utils", "utils")], path="./utils.js", is_relative=True)
        from module import x as alias → ImportFrom(module="module", names=[("x", "alias")], path="./module.js")
    
    Attributes:
        module: Python module name (None for relative imports)
        names: List of (original_name, alias_name) tuples
        path: Resolved JavaScript import path
        is_relative: True if this is a relative import (from . import x)
        level: Number of dots for relative imports (1 = current dir, 2 = parent, etc.)
        is_type_checking: True if inside `if TYPE_CHECKING:` block (Phase 33.3)
    """
    module: Optional[str] = None
    names: tuple[tuple[str, str], ...] = field(default_factory=tuple)  # (original_name, alias_name) pairs
    path: str = ""
    is_relative: bool = False
    level: int = 0  # Number of dots for relative imports
    is_type_checking: bool = False  # Phase 33.3: Stripped at runtime if True


@dataclass(frozen=True)
class ImportStar(JSNode):
    """
    Star import statement: from module import *
    
    WHAT: Represents Python 'from module import *' statements.
    WHY: Converts Python star imports to JavaScript namespace imports.
    HOW: Stores module name and resolved path. Emitter handles __all__.
    WHO: Generated by imports.py when parsing ast.ImportFrom with *.
    WHEN: During AST parsing phase.
    WHERE: Part of import system IR.
    
    Examples:
        from module import * → ImportStar(module="module", path="./module.js")
        from . import * → ImportStar(module=None, path="./", is_relative=True)
    
    Attributes:
        module: Python module name (None for relative imports)
        path: Resolved JavaScript import path
        is_relative: True if this is a relative import
        level: Number of dots for relative imports
        is_type_checking: True if inside `if TYPE_CHECKING:` block (Phase 33.3)
    """
    module: Optional[str] = None
    path: str = ""
    is_relative: bool = False
    level: int = 0
    is_type_checking: bool = False  # Phase 33.3: Stripped at runtime if True
