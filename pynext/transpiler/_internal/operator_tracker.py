"""
PyNext Transpiler - Operator Class Tracking

=============================================================================
WHO: Transpiler developers, bundle size optimizers
=============================================================================

=============================================================================
WHAT THIS FILE DOES
=============================================================================

Tracks which classes define operator overloading methods (__add__, __eq__, etc.)
and determines when it's safe to emit direct JavaScript operators vs runtime calls.

=============================================================================
WHEN: During transpilation, when emitting binary operations
=============================================================================

=============================================================================
WHERE: Used by emitter.py when handling BinOp nodes
=============================================================================

=============================================================================
WHY THIS EXISTS (Problem It Solves)
=============================================================================

Python supports operator overloading - any class can define __add__, __eq__, etc.
When transpiling, we must handle this, but it has significant bundle size cost:

    # For potentially-overloaded operators:
    __py.dunders.add(a, b)  # ~200B per operator in runtime

For code that ONLY uses primitives (int, float, str, list, dict), we don't need
the runtime helpers at all:

    # For known primitives:
    a + b  # Direct JS operator, zero runtime cost

This tracker determines which approach to use based on what's in scope.

=============================================================================
HOW IT WORKS
=============================================================================

1. During class parsing, track which classes define operator methods:
   - scope.declare_operator_class("Vector", {"__add__", "__mul__"})

2. During expression emission, check if operands might have operators:
   - If both operands are primitives → emit direct JS operator
   - If either might be a custom class → emit runtime helper

3. Primitives are: int, float, str, bool, list, dict, set, tuple

=============================================================================
SIZE IMPACT
=============================================================================

| Scenario | Before | After | Savings |
|----------|--------|-------|---------|
| Numeric only | uses __py.dunders | a + b | 100% of dunders.js |
| Has custom ops | __py.dunders.add() | __py.dunders.add() | 0% (needed) |

=============================================================================
EXAMPLES
=============================================================================

```python
# Primitive-only code:
x = 1 + 2  # Emits: let x = 1 + 2;

# Custom class with operator:
class Vector:
    def __add__(self, other): ...
    
v1 + v2  # Emits: __py.dunders.add(v1, v2)
```
"""

from __future__ import annotations
from typing import Set, Dict, Optional, FrozenSet
from dataclasses import dataclass, field


# =============================================================================
# OPERATOR METHODS BY CATEGORY
# =============================================================================

# Arithmetic operators
ARITHMETIC_DUNDERS: FrozenSet[str] = frozenset({
    "__add__", "__radd__", "__iadd__",
    "__sub__", "__rsub__", "__isub__",
    "__mul__", "__rmul__", "__imul__",
    "__truediv__", "__rtruediv__", "__itruediv__",
    "__floordiv__", "__rfloordiv__", "__ifloordiv__",
    "__mod__", "__rmod__", "__imod__",
    "__pow__", "__rpow__", "__ipow__",
    "__matmul__", "__rmatmul__", "__imatmul__",
})

# Comparison operators
COMPARISON_DUNDERS: FrozenSet[str] = frozenset({
    "__eq__", "__ne__",
    "__lt__", "__le__",
    "__gt__", "__ge__",
})

# Bitwise operators
BITWISE_DUNDERS: FrozenSet[str] = frozenset({
    "__and__", "__rand__", "__iand__",
    "__or__", "__ror__", "__ior__",
    "__xor__", "__rxor__", "__ixor__",
    "__lshift__", "__rlshift__", "__ilshift__",
    "__rshift__", "__rrshift__", "__irshift__",
    "__invert__",
})

# Unary operators
UNARY_DUNDERS: FrozenSet[str] = frozenset({
    "__neg__", "__pos__", "__abs__",
    "__invert__",
})

# All operator dunders
ALL_OPERATOR_DUNDERS: FrozenSet[str] = (
    ARITHMETIC_DUNDERS | COMPARISON_DUNDERS | BITWISE_DUNDERS | UNARY_DUNDERS
)


# =============================================================================
# PRIMITIVE TYPES (known to not have custom operators)
# =============================================================================

# These types use JavaScript's native operators directly
PRIMITIVE_TYPES: FrozenSet[str] = frozenset({
    "int", "float", "str", "bool", "list", "dict", "set", "tuple",
    "NoneType", "None",
})


# =============================================================================
# OPERATOR TRACKER
# =============================================================================

@dataclass
class OperatorClass:
    """
    Represents a class with operator methods.
    
    Attributes:
        name: Class name
        operators: Set of operator dunder methods defined on this class
    """
    name: str
    operators: FrozenSet[str] = field(default_factory=frozenset)


class OperatorTracker:
    """
    Tracks classes with operator overloading methods.
    
    Usage:
        tracker = OperatorTracker()
        
        # During class parsing:
        tracker.declare_class("Vector", {"__add__", "__mul__"})
        
        # During expression emission:
        if tracker.needs_runtime_operator("add", left_var, right_var):
            emit: "__py.dunders.add(left, right)"
        else:
            emit: "left + right"
    """
    
    def __init__(self):
        # Maps class name to set of operator methods
        self._classes: Dict[str, FrozenSet[str]] = {}
        # Maps variable name to class name (for known instances)
        self._instances: Dict[str, str] = {}
    
    def declare_class(self, name: str, operators: Set[str]) -> None:
        """
        Declare a class with its operator methods.
        
        Args:
            name: Class name
            operators: Set of dunder method names defined on this class
        """
        operator_dunders = frozenset(operators & ALL_OPERATOR_DUNDERS)
        if operator_dunders:
            self._classes[name] = operator_dunders
    
    def declare_instance(self, var_name: str, class_name: str) -> None:
        """
        Declare that a variable holds an instance of a specific class.
        
        Args:
            var_name: Variable name
            class_name: Class name
        """
        if class_name in self._classes:
            self._instances[var_name] = class_name
    
    def clear_instance(self, var_name: str) -> None:
        """Clear instance tracking for a variable (reassignment)."""
        self._instances.pop(var_name, None)
    
    def has_operator_classes(self) -> bool:
        """Check if any classes with operators are declared."""
        return len(self._classes) > 0
    
    def class_has_operator(self, class_name: str, operator: str) -> bool:
        """Check if a class has a specific operator method."""
        return operator in self._classes.get(class_name, frozenset())
    
    def instance_has_operator(self, var_name: str, operator: str) -> bool:
        """Check if a variable's class has a specific operator method."""
        class_name = self._instances.get(var_name)
        if not class_name:
            return False
        return self.class_has_operator(class_name, operator)
    
    def is_primitive_type(self, type_name: str) -> bool:
        """Check if a type name is a primitive (no custom operators)."""
        return type_name in PRIMITIVE_TYPES
    
    def needs_runtime_operator(self, operator: str, 
                               left_type: Optional[str], 
                               right_type: Optional[str]) -> bool:
        """
        Determine if a binary operation needs runtime operator dispatch.
        
        Returns:
            True if runtime dispatch is needed (custom operators possible)
            False if direct JS operator can be used (primitives only)
        """
        # If no classes with operators are declared, we can use direct ops
        if not self.has_operator_classes():
            return False
        
        # Check if types are known primitives
        if left_type and left_type in PRIMITIVE_TYPES:
            if right_type and right_type in PRIMITIVE_TYPES:
                return False  # Both are primitives, use direct ops
        
        # Unknown types or custom classes - use runtime dispatch
        return True
    
    def get_operator_dunder(self, op: str) -> Optional[str]:
        """
        Get the dunder method name for a binary operator.
        
        Args:
            op: Operator name (e.g., "add", "sub", "eq")
        
        Returns:
            Dunder method name (e.g., "__add__", "__sub__", "__eq__")
        """
        return f"__{op}__" if f"__{op}__" in ALL_OPERATOR_DUNDERS else None
    
    def reset(self) -> None:
        """Reset all tracking (e.g., between files)."""
        self._classes.clear()
        self._instances.clear()


# =============================================================================
# GLOBAL TRACKER INSTANCE
# =============================================================================

_tracker: Optional[OperatorTracker] = None


def get_operator_tracker() -> OperatorTracker:
    """Get the global operator tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = OperatorTracker()
    return _tracker


def reset_operator_tracker() -> None:
    """Reset the global operator tracker."""
    global _tracker
    if _tracker is not None:
        _tracker.reset()
    _tracker = None


# =============================================================================
# HELPER FUNCTIONS FOR EMITTER
# =============================================================================

def is_primitive_context(left_type: Optional[str], right_type: Optional[str]) -> bool:
    """
    Check if both operands are primitives (can use direct JS operators).
    
    Args:
        left_type: Type of left operand (from type inference)
        right_type: Type of right operand (from type inference)
    
    Returns:
        True if both are primitives, False otherwise
    """
    if not left_type or not right_type:
        return False  # Unknown types - be conservative
    return left_type in PRIMITIVE_TYPES and right_type in PRIMITIVE_TYPES


def should_use_dunder_runtime(has_operator_classes: bool,
                               left_type: Optional[str],
                               right_type: Optional[str]) -> bool:
    """
    Determine if dunder runtime should be used for an operation.
    
    This is the main decision function for bundle optimization.
    
    Args:
        has_operator_classes: Whether any operator classes are in scope
        left_type: Type of left operand
        right_type: Type of right operand
    
    Returns:
        True if __py.dunders should be used
        False if direct JS operators are safe
    
    Decision logic:
        1. No operator classes in file → use direct JS (100% savings)
        2. Both operands are primitives → use direct JS
        3. Otherwise → use runtime (preserve correctness)
    """
    # Optimization: no operator classes means no custom operators possible
    if not has_operator_classes:
        return False
    
    # Optimization: primitives don't have custom operators
    if is_primitive_context(left_type, right_type):
        return False
    
    # Conservative: use runtime for correctness
    return True

