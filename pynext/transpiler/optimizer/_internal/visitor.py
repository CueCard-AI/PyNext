"""
PyNext Transpiler Optimizer - IR Visitor

=============================================================================
WHAT THIS FILE DOES
=============================================================================

Provides a base class for traversing and transforming IR nodes.
All optimizer passes inherit from IRVisitor.

=============================================================================
WHY THIS EXISTS (Problem It Solves)
=============================================================================

Each optimizer pass needs to traverse the IR tree and potentially transform
nodes. Instead of duplicating traversal logic, we provide a visitor pattern:

    class ElisionOptimizer(IRVisitor):
        def visit_Call(self, node):
            # Only handle Call nodes, others auto-traversed
            return self._try_elide(node)

=============================================================================
HOW IT WORKS (Architecture)
=============================================================================

    IRVisitor.visit(node)
         │
         ├── Dispatch to visit_{NodeType}(node) if exists
         │
         └── Otherwise, recursively visit children
                  │
                  └── Return transformed node

=============================================================================
EXAMPLES
=============================================================================

```python
from pynext.transpiler.optimizer._internal import IRVisitor
from pynext.transpiler.nodes import Call, Constant

class ConstantFolder(IRVisitor):
    def visit_BinOp(self, node):
        # First transform children
        node = self.generic_visit(node)
        
        # Then fold if both are constants
        if isinstance(node.left, Constant) and isinstance(node.right, Constant):
            result = eval_binop(node.op, node.left.value, node.right.value)
            return Constant(value=result)
        
        return node
```
"""

from __future__ import annotations
from dataclasses import replace, fields, is_dataclass
from typing import Any, TypeVar, Callable

# Import node types
from pynext.transpiler.nodes import (
    JSNode, Program,
    # Statements
    Assignment, AugAssign, If, For, ForUnpack, While, FunctionDef,
    Return, Pass, Break, Continue, Delete, ExprStmt,
    Try, ExceptHandler,
    # Expressions
    Name, Constant, BinOp, UnaryOp, Compare, BoolOp, IfExp,
    Call, Attribute, Subscript, Slice, List, Dict, Tuple,
    Lambda, Await, Starred, DictSpread, TupleUnpack,
    # Decorators
    Decorator, DecoratedFunction,
    # Comprehensions
    FString, FormattedValue, Comprehension,
    ListComp, DictComp, SetComp, GeneratorExp,
)

T = TypeVar("T", bound=JSNode)


class IRVisitor:
    """
    Base class for IR tree visitors and transformers.
    
    Override visit_{NodeType} methods to handle specific node types.
    The default behavior is to recursively visit all children.
    
    For transformations, return a new node from visit methods.
    Return the same node if no transformation is needed.
    """
    
    def visit(self, node: T) -> T:
        """
        Visit a node, dispatching to the appropriate visit_* method.
        
        Returns the transformed node (or original if unchanged).
        """
        if node is None:
            return None
        
        # Get the visitor method for this node type
        method_name = f"visit_{type(node).__name__}"
        visitor = getattr(self, method_name, None)
        
        if visitor is not None:
            return visitor(node)
        else:
            return self.generic_visit(node)
    
    def generic_visit(self, node: T) -> T:
        """
        Default visitor that recursively transforms children.
        
        This handles the common case where we want to transform
        all children but don't need special handling for this node type.
        """
        if not is_dataclass(node):
            return node
        
        changes = {}
        for f in fields(node):
            value = getattr(node, f.name)
            new_value = self._visit_field(value)
            if new_value is not value:
                changes[f.name] = new_value
        
        if changes:
            return replace(node, **changes)
        return node
    
    def _visit_field(self, value: Any) -> Any:
        """Visit a field value, handling tuples/lists of nodes."""
        if isinstance(value, JSNode):
            return self.visit(value)
        elif isinstance(value, (tuple, list)):
            new_items = []
            changed = False
            for item in value:
                if isinstance(item, JSNode):
                    new_item = self.visit(item)
                    if new_item is not item:
                        changed = True
                    new_items.append(new_item)
                else:
                    new_items.append(item)
            if changed:
                return tuple(new_items) if isinstance(value, tuple) else new_items
        return value
    
    def visit_all(self, nodes: tuple) -> tuple:
        """Visit a sequence of nodes, returning transformed sequence."""
        result = []
        changed = False
        for node in nodes:
            new_node = self.visit(node)
            if new_node is not node:
                changed = True
            result.append(new_node)
        return tuple(result) if changed else nodes


class IRCollector(IRVisitor):
    """
    Visitor that collects nodes matching a predicate.
    
    Usage:
        collector = IRCollector(lambda n: isinstance(n, Call))
        collector.visit(program)
        calls = collector.collected
    """
    
    def __init__(self, predicate: Callable[[JSNode], bool]):
        self.predicate = predicate
        self.collected: list[JSNode] = []
    
    def generic_visit(self, node: T) -> T:
        if self.predicate(node):
            self.collected.append(node)
        return super().generic_visit(node)


def collect_nodes(ir: JSNode, predicate: Callable[[JSNode], bool]) -> list[JSNode]:
    """Collect all nodes matching a predicate."""
    collector = IRCollector(predicate)
    collector.visit(ir)
    return collector.collected


def find_names(ir: JSNode) -> set[str]:
    """Find all variable names referenced in the IR."""
    names = set()
    
    def collect_names(node):
        if isinstance(node, Name):
            names.add(node.id)
    
    collector = IRCollector(lambda n: isinstance(n, Name))
    collector.visit(ir)
    return {n.id for n in collector.collected}


def find_assignments(ir: JSNode) -> list[Assignment]:
    """Find all assignments in the IR."""
    return collect_nodes(ir, lambda n: isinstance(n, Assignment))


def find_calls(ir: JSNode) -> list[Call]:
    """Find all function calls in the IR."""
    return collect_nodes(ir, lambda n: isinstance(n, Call))


def find_lambdas(ir: JSNode) -> list[Lambda]:
    """Find all lambda expressions in the IR."""
    return collect_nodes(ir, lambda n: isinstance(n, Lambda))
