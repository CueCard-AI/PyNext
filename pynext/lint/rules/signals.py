"""
PyNext Linting - Signal Rules

Rules for proper signal usage:
    PNX001: Unused Signal - signal created but never read
    PNX002: Signal in loop - creating signals inside loops
    PNX008: Untracked effect - Effect without dependency tracking
    PNX009: Direct signal mutation - using .value instead of .set()

Why These Rules:
    Signals are the core of PyNext reactivity. Misusing them
    leads to bugs that are hard to track down:
    
    - Unused signals waste memory
    - Signals in loops create new signals each iteration
    - Untracked effects don't re-run when dependencies change
    - Direct mutation bypasses reactivity
"""

from __future__ import annotations

import ast
from typing import Dict, List, Set

from pynext.lint.rules.base import BaseLinter, LintError


class SignalLinter(BaseLinter):
    """
    Lint signal usage in PyNext code.
    
    Checks for:
    - PNX001: Signal created but never called (read)
    - PNX002: Signal created inside a loop
    - PNX008: Effect without signal reads
    - PNX009: Direct assignment to signal.value
    """
    
    def check(
        self,
        source: str,
        filename: str,
        enabled_rules: Set[str],
    ) -> List[LintError]:
        """Check source for signal issues."""
        self.errors = []
        self.filename = filename
        self.source = source
        self.enabled_rules = enabled_rules
        
        tree = self.parse_source(source)
        if tree is None:
            return self.errors
        
        # Track signals
        signals: Dict[str, int] = {}  # name -> line defined
        signal_reads: Set[str] = set()
        signal_writes: Set[str] = set()
        
        # Track context
        in_loop = False
        loop_depth = 0
        
        # Effects without reads
        effects_without_reads: List[ast.Call] = []
        
        class SignalVisitor(ast.NodeVisitor):
            def __init__(self, linter: SignalLinter):
                self.linter = linter
                self.in_loop = False
                self.loop_depth = 0
                self.current_effect = None
            
            def visit_For(self, node: ast.For):
                self.loop_depth += 1
                was_in_loop = self.in_loop
                self.in_loop = True
                self.generic_visit(node)
                self.in_loop = was_in_loop
                self.loop_depth -= 1
            
            def visit_While(self, node: ast.While):
                self.loop_depth += 1
                was_in_loop = self.in_loop
                self.in_loop = True
                self.generic_visit(node)
                self.in_loop = was_in_loop
                self.loop_depth -= 1
            
            def visit_Assign(self, node: ast.Assign):
                # Check for Signal() creation
                if self._is_signal_call(node.value):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            signals[target.id] = node.lineno
                            
                            # PNX002: Signal in loop
                            if self.in_loop:
                                self.linter.add_error(
                                    "PNX002",
                                    f"Signal '{target.id}' created inside loop. "
                                    "This creates a new signal each iteration.",
                                    node.lineno,
                                    node.col_offset,
                                    "error",
                                )
                
                # PNX009: Check for direct .value assignment
                for target in node.targets:
                    if isinstance(target, ast.Attribute) and target.attr == "value":
                        if isinstance(target.value, ast.Name):
                            signal_name = target.value.id
                            if signal_name in signals:
                                self.linter.add_error(
                                    "PNX009",
                                    f"Direct mutation of signal '{signal_name}.value'. "
                                    f"Use '{signal_name}.set({ast.unparse(node.value)})' instead.",
                                    node.lineno,
                                    node.col_offset,
                                    "error",
                                    fix=f"{signal_name}.set({ast.unparse(node.value)})",
                                    fix_description="Replace .value = with .set()",
                                )
                
                self.generic_visit(node)
            
            def visit_Call(self, node: ast.Call):
                # Track signal reads (calling the signal)
                if isinstance(node.func, ast.Name):
                    if node.func.id in signals:
                        signal_reads.add(node.func.id)
                
                # Track Effect calls
                if isinstance(node.func, ast.Name) and node.func.id == "Effect":
                    self.current_effect = node
                    # Check if effect body reads any signals
                    if node.args:
                        effect_func = node.args[0]
                        if isinstance(effect_func, ast.Lambda):
                            self._check_effect_body(effect_func.body, node)
                
                # Track .set() calls
                if isinstance(node.func, ast.Attribute) and node.func.attr == "set":
                    if isinstance(node.func.value, ast.Name):
                        signal_writes.add(node.func.value.id)
                
                self.generic_visit(node)
            
            def _check_effect_body(self, body: ast.expr, effect_node: ast.Call):
                """Check if effect body reads any signals."""
                reads_signal = False
                
                class EffectBodyVisitor(ast.NodeVisitor):
                    def visit_Call(self, node: ast.Call):
                        nonlocal reads_signal
                        if isinstance(node.func, ast.Name) and node.func.id in signals:
                            reads_signal = True
                        self.generic_visit(node)
                
                EffectBodyVisitor().visit(body)
                
                if not reads_signal:
                    self.linter.add_error(
                        "PNX008",
                        "Effect doesn't read any signals. "
                        "It will only run once and never re-run.",
                        effect_node.lineno,
                        effect_node.col_offset,
                        "warning",
                    )
            
            def _is_signal_call(self, node: ast.expr) -> bool:
                """Check if node is Signal(...)."""
                return (
                    isinstance(node, ast.Call) and
                    isinstance(node.func, ast.Name) and
                    node.func.id == "Signal"
                )
        
        visitor = SignalVisitor(self)
        visitor.visit(tree)
        
        # PNX001: Check for unused signals
        for name, line in signals.items():
            if name not in signal_reads:
                self.add_error(
                    "PNX001",
                    f"Signal '{name}' is created but never read. "
                    "Either use it or remove it.",
                    line,
                    0,
                    "warning",
                    fix=f"# Remove unused signal: {name}",
                    fix_description="Remove the unused signal",
                )
        
        return self.errors
    
    @staticmethod
    def explain(rule_id: str) -> str:
        """Get detailed explanation for a rule."""
        explanations = {
            "PNX001": """
## PNX001: Unused Signal

A Signal was created but never read (called).

### Bad:
```python
def Counter():
    count = Signal(0)  # Created but never used
    other = Signal(10)
    return div()[other()]  # Only 'other' is read
```

### Good:
```python
def Counter():
    count = Signal(0)
    return div()[count()]  # Signal is read
```

### Why This Matters:
- Unused signals waste memory
- Often indicates a bug (forgot to display the value)
- Clutters code with dead variables

### How to Fix:
- Read the signal by calling it: `count()`
- Or remove the signal if it's not needed
""",
            "PNX002": """
## PNX002: Signal in Loop

A Signal was created inside a loop.

### Bad:
```python
def ItemList(items):
    for item in items:
        selected = Signal(False)  # Creates new signal each iteration!
        # ...
```

### Good:
```python
def ItemList(items):
    selected_items = Signal(set())  # One signal outside loop
    for item in items:
        # Use the single signal for all items
        # ...
```

### Why This Matters:
- Each loop iteration creates a NEW signal
- Previous signals become orphaned
- Causes memory leaks and unexpected behavior
- State is lost on each iteration

### How to Fix:
- Move signal creation outside the loop
- Use a single signal with a collection (list, set, dict)
- Or use a Store for complex nested state
""",
            "PNX008": """
## PNX008: Untracked Effect

An Effect doesn't read any signals in its body.

### Bad:
```python
count = Signal(0)

Effect(lambda: print("Effect ran"))  # Never re-runs!
```

### Good:
```python
count = Signal(0)

Effect(lambda: print(f"Count: {count()}"))  # Re-runs when count changes
```

### Why This Matters:
- Effects re-run when their tracked signals change
- If no signals are read, the effect only runs once
- Usually indicates a bug (forgot to read the signal)

### How to Fix:
- Read the signals you want to track inside the effect
- Or use a regular function if you only need it to run once
""",
            "PNX009": """
## PNX009: Direct Signal Mutation

Signal is mutated directly with `.value = x` instead of `.set(x)`.

### Bad:
```python
count = Signal(0)
count.value = 5  # Direct mutation - bypasses reactivity!
```

### Good:
```python
count = Signal(0)
count.set(5)  # Proper mutation - triggers reactivity
```

### Why This Matters:
- Direct mutation bypasses the reactive system
- Effects won't re-run
- UI won't update
- Very hard to debug

### How to Fix:
- Use `.set(value)` instead of `.value = value`
- Auto-fix is available for this rule
""",
        }
        return explanations.get(rule_id, f"No detailed explanation for {rule_id}")

