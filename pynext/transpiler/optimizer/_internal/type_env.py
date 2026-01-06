"""
PyNext Transpiler Optimizer - Type Environment

=============================================================================
WHAT THIS FILE DOES
=============================================================================

Provides a type environment for tracking variable types during optimization.
This enables the optimizer to make safe decisions about wrapper elision.

=============================================================================
WHY THIS EXISTS (Problem It Solves)
=============================================================================

To safely elide __py.* wrappers, we need to know the types of variables:

    x = 5        # x is int
    y = 3        # y is int
    z = x + y    # Can use native + instead of __py.add()

Without type tracking, we must conservatively keep all wrappers.

=============================================================================
HOW IT WORKS (Architecture)
=============================================================================

    ┌─────────────────────────────────────────────────────────────────┐
    │  TypeEnv (hierarchical type environment)                         │
    ├─────────────────────────────────────────────────────────────────┤
    │                                                                  │
    │  Global Scope                                                    │
    │    ├── x: int                                                    │
    │    └── y: str                                                    │
    │                                                                  │
    │  Function Scope (parent=Global)                                  │
    │    ├── a: int (parameter)                                        │
    │    └── b: list                                                   │
    │                                                                  │
    │  Block Scope (parent=Function)                                   │
    │    └── i: int (loop variable)                                    │
    │                                                                  │
    └─────────────────────────────────────────────────────────────────┘

=============================================================================
WHO USES THIS
=============================================================================

- types.py: Type inference engine populates TypeEnv
- elision.py: Queries TypeEnv to decide if wrapper can be elided
- inline.py: Queries TypeEnv to decide inline strategy

=============================================================================
EXAMPLES
=============================================================================

```python
from pynext.transpiler.optimizer._internal import TypeEnv, PyType

# Create a type environment
env = TypeEnv()

# Set variable types
env.set_type("x", PyType.INT)
env.set_type("items", PyType.LIST)

# Query types
env.get_type("x")  # → PyType.INT
env.get_type("unknown")  # → PyType.ANY (conservative default)

# Create nested scope
inner = env.child_scope()
inner.set_type("i", PyType.INT)
inner.get_type("x")  # → PyType.INT (inherited from parent)
```
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Dict


class PyType(Enum):
    """
    Python types tracked by the optimizer.
    
    These are the types we can reason about for optimization purposes.
    The type system is intentionally simple - we only need enough
    information to decide if wrappers can be elided safely.
    """
    # Primitive types (safe for native JS operations when matched)
    INT = auto()      # Integer: 0, 1, -5, len(x)
    FLOAT = auto()    # Float: 3.14, 2.0
    BOOL = auto()     # Boolean: True, False, x > 0
    STR = auto()      # String: "hello", f"{x}"
    NONE = auto()     # None/null
    
    # Collection types (need wrappers for most operations)
    LIST = auto()     # List: [1, 2, 3]
    DICT = auto()     # Dict: {"a": 1}
    SET = auto()      # Set: {1, 2, 3}
    TUPLE = auto()    # Tuple: (1, 2)
    
    # Callable types
    FUNC = auto()     # Function
    LAMBDA = auto()   # Lambda
    
    # Unknown type (conservative - keep all wrappers)
    ANY = auto()
    
    # Number union (int or float - still safe for arithmetic)
    NUMBER = auto()
    
    def is_numeric(self) -> bool:
        """Check if type is numeric (safe for arithmetic without wrappers)."""
        return self in (PyType.INT, PyType.FLOAT, PyType.NUMBER)
    
    def is_primitive(self) -> bool:
        """Check if type is a JS primitive (safe for === comparison)."""
        return self in (PyType.INT, PyType.FLOAT, PyType.BOOL, PyType.STR, 
                       PyType.NONE, PyType.NUMBER)
    
    def is_collection(self) -> bool:
        """Check if type is a collection (needs wrappers for operations)."""
        return self in (PyType.LIST, PyType.DICT, PyType.SET, PyType.TUPLE)
    
    def is_known(self) -> bool:
        """Check if type is known (not ANY)."""
        return self != PyType.ANY


@dataclass
class TypeEnv:
    """
    Hierarchical type environment for tracking variable types.
    
    Supports nested scopes (functions, loops, conditionals) with
    proper shadowing and lookup semantics.
    """
    _types: Dict[str, PyType] = field(default_factory=dict)
    _parent: Optional["TypeEnv"] = None
    _name: str = "global"  # For debugging
    
    def get_type(self, name: str) -> PyType:
        """
        Get the type of a variable, searching up the scope chain.
        
        Returns PyType.ANY if variable is not found (conservative default).
        """
        if name in self._types:
            return self._types[name]
        if self._parent is not None:
            return self._parent.get_type(name)
        return PyType.ANY
    
    def set_type(self, name: str, typ: PyType) -> None:
        """Set the type of a variable in the current scope."""
        self._types[name] = typ
    
    def has_type(self, name: str) -> bool:
        """Check if a variable has a known type in any scope."""
        return self.get_type(name) != PyType.ANY
    
    def child_scope(self, name: str = "block") -> "TypeEnv":
        """Create a child scope for nested blocks."""
        return TypeEnv(_parent=self, _name=name)
    
    def merge_types(self, other: "TypeEnv") -> None:
        """
        Merge types from another environment (for branch convergence).
        
        When two branches assign different types to the same variable,
        we take the more general type (or ANY if incompatible).
        """
        for var_name, other_type in other._types.items():
            current_type = self.get_type(var_name)
            if current_type == PyType.ANY:
                # If we don't know the type, use other's type
                self._types[var_name] = other_type
            elif current_type != other_type:
                # Types differ - use ANY to be safe
                # Exception: int + float → number
                if current_type.is_numeric() and other_type.is_numeric():
                    self._types[var_name] = PyType.NUMBER
                else:
                    self._types[var_name] = PyType.ANY
    
    def copy(self) -> "TypeEnv":
        """Create a copy of this environment (for branch analysis)."""
        return TypeEnv(
            _types=dict(self._types),
            _parent=self._parent,
            _name=self._name
        )
    
    def all_types(self) -> Dict[str, PyType]:
        """Get all types in this scope (not including parent scopes)."""
        return dict(self._types)
    
    def __repr__(self) -> str:
        types_str = ", ".join(f"{k}: {v.name}" for k, v in self._types.items())
        parent_str = f" (parent={self._parent._name})" if self._parent else ""
        return f"TypeEnv[{self._name}]({types_str}){parent_str}"
