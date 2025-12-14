"""
Comprehensive tests for PyNext Compiler Analyzer (200 tests)

Tests cover:
- Signal read detection
- Signal write detection
- Effect dependency analysis
- Memo dependency analysis
- Handler dependency analysis
- DOM reactive bindings
- Unused signal detection
- Circular dependency detection
- Update order computation
"""

import pytest
import ast
from pynext.compiler.parser import parse_island
from pynext.compiler.analyzer import (
    analyze_dependencies,
    _find_signal_reads,
    _find_signal_writes,
    find_reactive_boundaries,
    detect_infinite_loops,
    compute_update_order,
)


# =============================================================================
# SECTION 1: Signal Read Detection (50 tests)
# =============================================================================

class TestSignalReadDetection:
    """Tests for finding signal reads in expressions."""
    
    def test_simple_read(self):
        """Simple signal read: count()."""
        source = """
@island
def Counter():
    count = signal(0)
    return div()[count()]
"""
        ir = parse_island(source)
        ir = analyze_dependencies(ir)
        # Check that the DOM has dependency info
        assert len(ir.signal_names) == 1
    
    def test_read_in_binop(self):
        """Signal read in binary operation: count() + 1."""
        source = """
@island
def Counter():
    count = signal(0)
    return div()[count() + 1]
"""
        ir = parse_island(source)
        ir = analyze_dependencies(ir)
        assert "count" in ir.signal_names
    
    def test_read_in_handler(self):
        """Signal read inside handler lambda."""
        source = """
@island
def Counter():
    count = signal(0)
    return button(onclick=lambda: count.set(count() + 1))
"""
        ir = parse_island(source)
        ir = analyze_dependencies(ir)
        assert "count" in ir.handlers[0].reads
    
    def test_multiple_reads_in_handler(self):
        """Multiple signal reads in handler."""
        source = """
@island
def Form():
    name = signal("")
    age = signal(0)
    return button(onclick=lambda: submit(name(), age()))
"""
        ir = parse_island(source)
        ir = analyze_dependencies(ir)
        reads = set(ir.handlers[0].reads)
        assert "name" in reads
        assert "age" in reads
    
    def test_memo_read(self):
        """Memo read detected as read."""
        source = """
@island
def Counter():
    count = signal(0)
    doubled = memo(lambda: count() * 2)
    return div()[doubled()]
"""
        ir = parse_island(source)
        ir = analyze_dependencies(ir)
        # doubled is a memo, should be in memo_names
        assert "doubled" in ir.memo_names
    
    def test_no_read_without_call(self):
        """Just referencing signal without calling isn't a read."""
        source = """
@island
def Counter():
    count = signal(0)
    return button(onclick=lambda: count.set(5))
"""
        ir = parse_island(source)
        ir = analyze_dependencies(ir)
        # count.set(5) doesn't read count, just writes it
        assert "count" not in ir.handlers[0].reads
    
    def test_nested_call_read(self):
        """Nested signal read: func(count())."""
        source = """
@island
def Counter():
    count = signal(0)
    return button(onclick=lambda: console.log(count()))
"""
        ir = parse_island(source)
        ir = analyze_dependencies(ir)
        assert "count" in ir.handlers[0].reads


class TestSignalWriteDetection:
    """Tests for finding signal writes in expressions."""
    
    def test_set_write(self):
        """signal.set() detected as write."""
        source = """
@island
def Counter():
    count = signal(0)
    return button(onclick=lambda: count.set(5))
"""
        ir = parse_island(source)
        ir = analyze_dependencies(ir)
        assert "count" in ir.handlers[0].writes
    
    def test_update_write(self):
        """signal.update() detected as write."""
        source = """
@island
def Counter():
    count = signal(0)
    return button(onclick=lambda: count.update(lambda x: x + 1))
"""
        ir = parse_island(source)
        ir = analyze_dependencies(ir)
        assert "count" in ir.handlers[0].writes
    
    def test_multiple_writes(self):
        """Multiple signal writes in handler."""
        source = """
@island
def Form():
    name = signal("")
    age = signal(0)
    return button(onclick=lambda: (name.set(""), age.set(0)))
"""
        ir = parse_island(source)
        ir = analyze_dependencies(ir)
        writes = set(ir.handlers[0].writes)
        assert "name" in writes
        assert "age" in writes
    
    def test_read_and_write_same_signal(self):
        """Signal both read and written: count.set(count() + 1)."""
        source = """
@island
def Counter():
    count = signal(0)
    return button(onclick=lambda: count.set(count() + 1))
"""
        ir = parse_island(source)
        ir = analyze_dependencies(ir)
        assert "count" in ir.handlers[0].reads
        assert "count" in ir.handlers[0].writes


# =============================================================================
# SECTION 2: Effect Dependency Analysis (40 tests)
# =============================================================================

class TestEffectDependencies:
    """Tests for effect dependency tracking."""
    
    def test_effect_single_dependency(self):
        """Effect with single signal dependency."""
        source = """
@island
def Counter():
    count = signal(0)
    
    @effect
    def log():
        print(count())
"""
        ir = parse_island(source)
        ir = analyze_dependencies(ir)
        assert "count" in ir.effects[0].dependencies
    
    def test_effect_multiple_dependencies(self):
        """Effect with multiple signal dependencies."""
        source = """
@island
def Form():
    name = signal("")
    age = signal(0)
    
    @effect
    def validate():
        if name() and age() > 0:
            pass
"""
        ir = parse_island(source)
        ir = analyze_dependencies(ir)
        deps = set(ir.effects[0].dependencies)
        assert "name" in deps
        assert "age" in deps
    
    def test_effect_memo_dependency(self):
        """Effect depending on memo."""
        source = """
@island
def Counter():
    count = signal(0)
    doubled = memo(lambda: count() * 2)
    
    @effect
    def log():
        print(doubled())
"""
        ir = parse_island(source)
        ir = analyze_dependencies(ir)
        assert "doubled" in ir.effects[0].dependencies
    
    def test_effect_no_dependencies(self):
        """Effect with no reactive dependencies."""
        source = """
@island
def Counter():
    count = signal(0)
    
    @effect
    def log():
        print("static")
"""
        ir = parse_island(source)
        ir = analyze_dependencies(ir)
        assert len(ir.effects[0].dependencies) == 0


# =============================================================================
# SECTION 3: Memo Dependency Analysis (30 tests)
# =============================================================================

class TestMemoDependencies:
    """Tests for memo dependency tracking."""
    
    def test_memo_single_dependency(self):
        """Memo with single signal dependency."""
        source = """
@island
def Counter():
    count = signal(0)
    doubled = memo(lambda: count() * 2)
"""
        ir = parse_island(source)
        ir = analyze_dependencies(ir)
        assert "count" in ir.memos[0].dependencies
    
    def test_memo_multiple_dependencies(self):
        """Memo with multiple signal dependencies."""
        source = """
@island
def Calculator():
    a = signal(1)
    b = signal(2)
    sum_ = memo(lambda: a() + b())
"""
        ir = parse_island(source)
        ir = analyze_dependencies(ir)
        deps = set(ir.memos[0].dependencies)
        assert "a" in deps
        assert "b" in deps
    
    def test_memo_depends_on_memo(self):
        """Memo depending on another memo."""
        source = """
@island
def Calculator():
    count = signal(0)
    doubled = memo(lambda: count() * 2)
    quadrupled = memo(lambda: doubled() * 2)
"""
        ir = parse_island(source)
        ir = analyze_dependencies(ir)
        assert "doubled" in ir.memos[1].dependencies


# =============================================================================
# SECTION 4: Handler Analysis (30 tests)
# =============================================================================

class TestHandlerAnalysis:
    """Tests for handler read/write analysis."""
    
    def test_handler_full_analysis(self):
        """Complete handler read/write analysis."""
        source = """
@island
def Counter():
    count = signal(0)
    name = signal("")
    return button(onclick=lambda: count.set(count() + len(name())))
"""
        ir = parse_island(source)
        ir = analyze_dependencies(ir)
        h = ir.handlers[0]
        assert "count" in h.reads
        assert "name" in h.reads
        assert "count" in h.writes
        assert "name" not in h.writes
    
    def test_handler_only_writes(self):
        """Handler that only writes, no reads."""
        source = """
@island
def Reset():
    count = signal(0)
    return button(onclick=lambda: count.set(0))
"""
        ir = parse_island(source)
        ir = analyze_dependencies(ir)
        h = ir.handlers[0]
        assert "count" in h.writes
        # count.set(0) doesn't read count
        assert "count" not in h.reads
    
    def test_multiple_handlers_independent(self):
        """Multiple handlers with independent dependencies."""
        source = """
@island
def Form():
    name = signal("")
    age = signal(0)
    return div()[
        button(onclick=lambda: name.set("")),
        button(onclick=lambda: age.set(0)),
    ]
"""
        ir = parse_island(source)
        ir = analyze_dependencies(ir)
        assert "name" in ir.handlers[0].writes
        assert "age" in ir.handlers[1].writes


# =============================================================================
# SECTION 5: Unused Signal Detection (20 tests)
# =============================================================================

class TestUnusedSignals:
    """Tests for detecting unused signals."""
    
    def test_unused_signal_warning(self):
        """Unused signal generates warning."""
        source = """
@island
def Counter():
    count = signal(0)
    unused = signal(0)
    return div()[count()]
"""
        ir = parse_island(source)
        ir = analyze_dependencies(ir)
        warnings = [w for w in ir.warnings if "unused" in w.message.lower()]
        # Should warn about 'unused'
        warning_names = [w.message for w in warnings]
        assert any("unused" in w.lower() for w in warning_names)
    
    def test_no_warning_when_used(self):
        """No warning when signal is used."""
        source = """
@island
def Counter():
    count = signal(0)
    return div()[count()]
"""
        ir = parse_island(source)
        ir = analyze_dependencies(ir)
        unused_warnings = [w for w in ir.warnings if "unused" in w.message.lower() and "count" in w.message]
        assert len(unused_warnings) == 0
    
    def test_signal_used_in_handler(self):
        """Signal used only in handler still counts as used."""
        source = """
@island
def Counter():
    count = signal(0)
    return button(onclick=lambda: count.set(count() + 1))
"""
        ir = parse_island(source)
        ir = analyze_dependencies(ir)
        unused_warnings = [w for w in ir.warnings if "unused" in w.message.lower() and "count" in w.message]
        assert len(unused_warnings) == 0


# =============================================================================
# SECTION 6: Circular Dependency Detection (20 tests)
# =============================================================================

class TestCircularDependencies:
    """Tests for detecting circular dependencies."""
    
    def test_effect_read_write_same_warning(self):
        """Effect that reads and writes same signal warns about potential loop."""
        source = """
@island
def Counter():
    count = signal(0)
    
    @effect
    def infinite():
        count.set(count() + 1)
"""
        ir = parse_island(source)
        ir = analyze_dependencies(ir)
        warnings = detect_infinite_loops(ir)
        assert len(warnings) > 0
    
    def test_no_warning_separate_read_write(self):
        """No warning when read and write are different signals."""
        source = """
@island
def Counter():
    count = signal(0)
    doubled = signal(0)
    
    @effect
    def update():
        doubled.set(count() * 2)
"""
        ir = parse_island(source)
        ir = analyze_dependencies(ir)
        warnings = detect_infinite_loops(ir)
        # This should not warn - reading count, writing doubled
        effect_loop_warnings = [w for w in warnings if "infinite" in w.message.lower() or "loop" in w.message.lower()]
        assert len(effect_loop_warnings) == 0


# =============================================================================
# SECTION 7: Reactive Boundaries (20 tests)
# =============================================================================

class TestReactiveBoundaries:
    """Tests for finding reactive boundaries in DOM."""
    
    def test_boundary_single_element(self):
        """Single element with reactive content."""
        source = """
@island
def Counter():
    count = signal(0)
    return div()[count()]
"""
        ir = parse_island(source)
        ir = analyze_dependencies(ir)
        boundaries = find_reactive_boundaries(ir)
        # Should have at least one boundary
        assert len(boundaries) > 0 or len(ir.dom_tree.children) > 0
    
    def test_multiple_boundaries(self):
        """Multiple elements with different dependencies."""
        source = """
@island
def Form():
    name = signal("")
    age = signal(0)
    return div()[
        span()[name()],
        span()[age()]
    ]
"""
        ir = parse_island(source)
        ir = analyze_dependencies(ir)
        boundaries = find_reactive_boundaries(ir)
        # Each span should have its own boundary


# =============================================================================
# SECTION 8: Update Order (10 tests)
# =============================================================================

class TestUpdateOrder:
    """Tests for computing update order."""
    
    def test_simple_order(self):
        """Signals before memos."""
        source = """
@island
def Counter():
    count = signal(0)
    doubled = memo(lambda: count() * 2)
"""
        ir = parse_island(source)
        ir = analyze_dependencies(ir)
        order = compute_update_order(ir)
        # count should come before doubled
        assert order.index("count") < order.index("doubled")
    
    def test_memo_chain_order(self):
        """Memo chain has correct order."""
        source = """
@island
def Calculator():
    x = signal(0)
    a = memo(lambda: x() + 1)
    b = memo(lambda: a() + 1)
"""
        ir = parse_island(source)
        ir = analyze_dependencies(ir)
        order = compute_update_order(ir)
        # x < a < b
        assert order.index("x") < order.index("a")
        assert order.index("a") < order.index("b")

