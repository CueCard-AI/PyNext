"""
PyNext Transpiler Optimizer

=============================================================================
WHAT THIS FILE DOES
=============================================================================

Provides the main optimize() API for the transpiler optimization pipeline.
Combines all optimization passes into a single, configurable function.

=============================================================================
WHY THIS EXISTS (Problem It Solves)
=============================================================================

The transpiler generates conservative code with many __py.* runtime calls.
The optimizer reduces this overhead by:

1. Eliding unnecessary wrappers when types are known
2. Inlining simple runtime calls
3. Fixing loop variable capture issues
4. Eliminating dead code
5. Tree-shaking unused runtime functions

=============================================================================
HOW IT WORKS (Architecture)
=============================================================================

    IR Tree
         │
         ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │  optimize(ir, options)                                           │
    ├─────────────────────────────────────────────────────────────────┤
    │                                                                  │
    │  Pass 1: Type Inference (annotate types)                         │
    │     │                                                            │
    │     ▼                                                            │
    │  Pass 2: Wrapper Elision (remove safe wrappers)                  │
    │     │                                                            │
    │     ▼                                                            │
    │  Pass 3: Loop Capture (fix closure-in-loop)                      │
    │     │                                                            │
    │     ▼                                                            │
    │  Pass 4: Inlining (inline simple calls)                          │
    │     │                                                            │
    │     ▼                                                            │
    │  Pass 5: DCE (remove dead code)                                  │
    │                                                                  │
    └─────────────────────────────────────────────────────────────────┘
         │
         ▼
    Optimized IR

=============================================================================
EXAMPLES
=============================================================================

```python
from pynext.transpiler import parse
from pynext.transpiler.optimizer import optimize, OptimizeOptions

# Basic optimization
ir = parse("if x > 0: y = x + 1")
optimized = optimize(ir)

# Custom options
options = OptimizeOptions(
    elision=True,
    inline=True,
    capture=True,
    dce=True,
)
optimized = optimize(ir, options)

# Get optimization statistics
stats = get_optimization_stats(ir, optimized)
print(f"Wrapper calls reduced: {stats['wrapper_reduction']}%")
```
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Set

from pynext.transpiler.nodes import Program

# Import individual optimizers
from .types import infer_types, TypeEnv, PyType
from .elision import elide_wrappers, count_py_calls
from .capture import fix_loop_captures, count_loop_lambdas
from .inline import inline_runtime_calls, count_inlinable_calls
from .dce import (
    collect_runtime_deps, eliminate_dead_code,
    generate_import, count_unreachable_blocks,
)
from .native import mark_native_functions, is_js_native


__all__ = [
    # Main API
    "optimize",
    "OptimizeOptions",
    "get_optimization_stats",
    
    # Type inference
    "infer_types",
    "TypeEnv",
    "PyType",
    
    # Individual passes
    "elide_wrappers",
    "fix_loop_captures",
    "inline_runtime_calls",
    "eliminate_dead_code",
    "collect_runtime_deps",
    
    # Native mode
    "mark_native_functions",
    "is_js_native",
    
    # Utilities
    "count_py_calls",
    "generate_import",
]


# =============================================================================
# OPTIONS
# =============================================================================

@dataclass
class OptimizeOptions:
    """
    Configuration options for the optimizer.
    
    Attributes:
        elision: Enable wrapper elision (default: True)
        inline: Enable runtime inlining (default: True)
        capture: Enable loop capture fix (default: True)
        dce: Enable dead code elimination (default: True)
        native_mode: Enable @js_native detection (default: True)
    """
    elision: bool = True
    inline: bool = True
    capture: bool = True
    dce: bool = True
    native_mode: bool = True


# =============================================================================
# MAIN API
# =============================================================================

def optimize(ir: Program, options: Optional[OptimizeOptions] = None) -> Program:
    """
    Apply optimization passes to IR.
    
    This is the main entry point for optimization. It runs all enabled
    passes in the correct order.
    
    Args:
        ir: The IR tree to optimize
        options: Optimization options (uses defaults if None)
    
    Returns:
        Optimized IR tree
    
    Example:
        ir = parse("if x > 0: y = x + 1")
        optimized = optimize(ir)
    """
    options = options or OptimizeOptions()
    
    # Pass 1: Type inference (always runs - needed by other passes)
    type_env = infer_types(ir)
    
    # Pass 2: Wrapper elision (uses type info)
    if options.elision:
        ir = elide_wrappers(ir, type_env)
    
    # Pass 3: Loop capture fix
    if options.capture:
        ir = fix_loop_captures(ir)
    
    # Pass 4: Runtime inlining (uses type info)
    if options.inline:
        ir = inline_runtime_calls(ir, type_env)
    
    # Pass 5: Dead code elimination
    if options.dce:
        ir = eliminate_dead_code(ir)
    
    return ir


# =============================================================================
# STATISTICS
# =============================================================================

@dataclass
class OptimizationStats:
    """Statistics about optimization results."""
    original_py_calls: int = 0
    optimized_py_calls: int = 0
    wrapper_reduction: float = 0.0
    inlinable_calls: int = 0
    loop_lambdas: int = 0
    unreachable_blocks: int = 0
    runtime_deps: Set[str] = field(default_factory=set)
    native_functions: Set[str] = field(default_factory=set)


def get_optimization_stats(original: Program, optimized: Program,
                           type_env: Optional[TypeEnv] = None) -> OptimizationStats:
    """
    Get statistics about optimization results.
    
    Args:
        original: Original IR before optimization
        optimized: IR after optimization
        type_env: Type environment (inferred if not provided)
    
    Returns:
        OptimizationStats with metrics
    """
    type_env = type_env or infer_types(original)
    
    original_calls = count_py_calls(original)
    optimized_calls = count_py_calls(optimized)
    
    reduction = 0.0
    if original_calls > 0:
        reduction = ((original_calls - optimized_calls) / original_calls) * 100
    
    return OptimizationStats(
        original_py_calls=original_calls,
        optimized_py_calls=optimized_calls,
        wrapper_reduction=reduction,
        inlinable_calls=count_inlinable_calls(original, type_env),
        loop_lambdas=count_loop_lambdas(original),
        unreachable_blocks=count_unreachable_blocks(original),
        runtime_deps=collect_runtime_deps(optimized),
        native_functions=mark_native_functions(original),
    )


def format_stats(stats: OptimizationStats) -> str:
    """Format optimization statistics as a string."""
    lines = [
        "Optimization Statistics:",
        f"  Original __py.* calls: {stats.original_py_calls}",
        f"  Optimized __py.* calls: {stats.optimized_py_calls}",
        f"  Wrapper reduction: {stats.wrapper_reduction:.1f}%",
        f"  Inlinable calls: {stats.inlinable_calls}",
        f"  Loop lambdas: {stats.loop_lambdas}",
        f"  Unreachable blocks: {stats.unreachable_blocks}",
        f"  Runtime deps: {sorted(stats.runtime_deps)}",
    ]
    if stats.native_functions:
        lines.append(f"  Native functions: {sorted(stats.native_functions)}")
    return "\n".join(lines)
