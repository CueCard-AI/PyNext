"""
PyNext Transform Layer - Transform IR Nodes to __pynext__ API

=============================================================================
WHAT THIS FILE DOES
=============================================================================

This module transforms transpiler IR nodes to use the `__pynext__.*` runtime
API. It's the bridge between the generic Python transpiler (Phase 18.1-18.5)
and PyNext's reactive system.

=============================================================================
WHY THIS EXISTS
=============================================================================

The base transpiler produces generic JavaScript:

    count.set(count() + 1)
    → count.set(count() + 1);  // Won't work - count isn't defined

We need to transform this to use PyNext's runtime API:

    __pynext__.getSignal('sig_1').set(
        __pynext__.getSignal('sig_1').read() + 1
    );

This module handles all PyNext-specific transformations:
- Signal reads: signal() → __pynext__.getSignal('id').read()
- Signal writes: signal.set(v) → __pynext__.getSignal('id').set(v)
- Form operations: form.validate() → __pynext__.getForm('id').validate()
- Store access: store.items → __pynext__.getStore('id').items
- Memo reads: memo() → __pynext__.getMemo('id').read()

=============================================================================
HOW IT WORKS
=============================================================================

    IR Nodes (from parser)
           │
           ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │  PyNextTransformer                                               │
    │                                                                  │
    │  Input: Name("count")  (where count is a signal)                │
    │                                                                  │
    │  transform_name():                                               │
    │    - Check if "count" is in ctx.signals                         │
    │    - Return Call to __pynext__.getSignal('sig_1')               │
    │                                                                  │
    │  Output: Call(                                                   │
    │    func=Attribute(                                               │
    │      value=Name("__pynext__"),                                  │
    │      attr="getSignal"                                           │
    │    ),                                                            │
    │    args=(Constant("sig_1"),)                                    │
    │  )                                                               │
    └─────────────────────────────────────────────────────────────────┘
           │
           ▼
    Emitter produces: __pynext__.getSignal('sig_1')

=============================================================================
TRANSFORMATION TABLE
=============================================================================

| Python Pattern              | JavaScript Output                           |
|-----------------------------|---------------------------------------------|
| signal()                    | __pynext__.getSignal('id').read()           |
| signal.set(v)               | __pynext__.getSignal('id').set(v)           |
| signal.update(fn)           | __pynext__.getSignal('id').update(fn)       |
| signal.peek()               | __pynext__.getSignal('id').peek()           |
| form.validate()             | __pynext__.getForm('id').validate()         |
| form.values                 | __pynext__.getForm('id').values             |
| form.reset()                | __pynext__.getForm('id').reset()            |
| form.field_name             | __pynext__.getForm('id').field_name         |
| form.errors.field           | __pynext__.getForm('id').errors.field       |
| store.prop                  | __pynext__.getStore('id').prop              |
| store["key"]                | __pynext__.getStore('id')["key"]            |
| memo()                      | __pynext__.getMemo('id').read()             |

=============================================================================
WHO USES THIS
=============================================================================

- pynext/transpiler/hydration.py: Main entry point
- pynext/core/html.py: Via transpile_handler()

=============================================================================
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass, replace, fields, is_dataclass
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .nodes import (
    JSNode, Assignment, AugAssign, If, For, While, FunctionDef, Return,
    Pass, Break, Continue, Delete, ExprStmt, Name, Constant, BinOp,
    UnaryOp, Compare, BoolOp, IfExp, Call, Attribute, Subscript,
    Slice, List as ListNode, Dict as DictNode, Tuple as TupleNode,
    Lambda, Starred, DictSpread, TupleUnpack, Program, ListComp,
    GeneratorExp, SetComp, DictComp, Try, ExceptHandler, Await,
)
from .reactive import ReactiveContext, ReactiveObjectInfo


# =============================================================================
# HELPERS TO BUILD IR NODES
# =============================================================================

def _pynext_get_signal(signal_id: str) -> Call:
    """Build: __pynext__.getSignal('signal_id')"""
    return Call(
        func=Attribute(
            value=Name(id="__pynext__"),
            attr="getSignal",
        ),
        args=(Constant(value=signal_id),),
    )


def _pynext_get_store(store_id: str) -> Call:
    """Build: __pynext__.getStore('store_id')"""
    return Call(
        func=Attribute(
            value=Name(id="__pynext__"),
            attr="getStore",
        ),
        args=(Constant(value=store_id),),
    )


def _pynext_get_form(form_id: str) -> Call:
    """Build: __pynext__.getForm('form_id')"""
    return Call(
        func=Attribute(
            value=Name(id="__pynext__"),
            attr="getForm",
        ),
        args=(Constant(value=form_id),),
    )


def _pynext_get_memo(memo_id: str) -> Call:
    """Build: __pynext__.getMemo('memo_id')"""
    return Call(
        func=Attribute(
            value=Name(id="__pynext__"),
            attr="getMemo",
        ),
        args=(Constant(value=memo_id),),
    )


def _method_call(obj: JSNode, method: str, args: tuple = ()) -> Call:
    """Build: obj.method(args)"""
    return Call(
        func=Attribute(value=obj, attr=method),
        args=args,
    )


# =============================================================================
# PYNEXT TRANSFORMER
# =============================================================================

class PyNextTransformer:
    """
    Transform IR nodes to use __pynext__ API.
    
    This is the core transformation engine. It walks the IR tree and
    replaces references to reactive objects with __pynext__.get*() calls.
    
    Example:
        ctx = ReactiveContext(signals={"count": SignalInfo(id="sig_1", ...)})
        transformer = PyNextTransformer(ctx)
        
        # Transform: count.set(count() + 1)
        node = Call(
            func=Attribute(value=Name("count"), attr="set"),
            args=(BinOp(
                left=Call(func=Name("count"), args=()),
                op="add",
                right=Constant(1)
            ),)
        )
        
        result = transformer.transform(node)
        # Result: __pynext__.getSignal('sig_1').set(
        #     __pynext__.getSignal('sig_1').read() + 1
        # )
    """
    
    def __init__(self, ctx: ReactiveContext, *, validate_fields: bool = True):
        self.ctx = ctx
        self._validate_fields = validate_fields
        self._validation_warnings: List[str] = []
        
        # Build lookup sets for fast checking
        self._signal_names: Set[str] = set(ctx.signals.keys())
        self._store_names: Set[str] = set(ctx.stores.keys())
        self._form_names: Set[str] = set(ctx.forms.keys())
        self._memo_names: Set[str] = set(ctx.memos.keys())
        self._all_reactive_names: Set[str] = (
            self._signal_names | self._store_names | 
            self._form_names | self._memo_names
        )
        
        # Extract known form fields for validation
        # Form fields are stored as "form_name.field_name" in signals
        self._form_fields: Dict[str, Set[str]] = {}
        for form_name in self._form_names:
            self._form_fields[form_name] = set()
            # Find all signals that start with "form_name."
            prefix = f"{form_name}."
            for sig_name in self._signal_names:
                if sig_name.startswith(prefix):
                    field_name = sig_name[len(prefix):]
                    self._form_fields[form_name].add(field_name)
        
        # Known form properties that are not fields
        self._form_properties: Set[str] = {
            "values", "errors", "is_valid", "is_dirty", "is_touched",
            "validate", "reset", "submit", "set_error", "clear_errors"
        }
    
    @property
    def warnings(self) -> List[str]:
        """Get validation warnings from transformation."""
        return self._validation_warnings
    
    def _validate_form_field(self, form_name: str, field_name: str, line: int = 0) -> None:
        """
        Validate that a form field exists.
        
        If validate_fields is True and the field is not known, add a warning.
        """
        if not self._validate_fields:
            return
        
        # Skip known properties
        if field_name in self._form_properties:
            return
        
        # Check if form has known fields
        known_fields = self._form_fields.get(form_name, set())
        if not known_fields:
            # No fields registered, can't validate (form was created without fields)
            return
        
        if field_name not in known_fields:
            self._validation_warnings.append(
                f"Line {line}: Form '{form_name}' may not have field '{field_name}'. "
                f"Known fields: {', '.join(sorted(known_fields)) or 'none'}"
            )
    
    # =========================================================================
    # PUBLIC API
    # =========================================================================
    
    def transform(self, node: JSNode) -> JSNode:
        """
        Transform an IR node, recursively handling children.
        
        This is the main entry point. Call this on the root node (Program
        or FunctionDef) to transform the entire tree.
        """
        if node is None:
            return node
        
        # Dispatch based on node type
        node_type = type(node).__name__
        method_name = f"_transform_{node_type.lower()}"
        
        if hasattr(self, method_name):
            return getattr(self, method_name)(node)
        
        # Default: recursively transform children
        return self._transform_generic(node)
    
    def transform_all(self, nodes: tuple) -> tuple:
        """Transform a tuple of nodes."""
        return tuple(self.transform(n) for n in nodes)
    
    # =========================================================================
    # STATEMENT TRANSFORMS
    # =========================================================================
    
    def _transform_program(self, node: Program) -> Program:
        """Transform Program node."""
        return replace(node, body=self.transform_all(node.body))
    
    def _transform_functiondef(self, node: FunctionDef) -> FunctionDef:
        """Transform FunctionDef node."""
        return replace(node, body=self.transform_all(node.body))
    
    def _transform_assignment(self, node: Assignment) -> Assignment:
        """Transform Assignment: x = value"""
        return replace(node, value=self.transform(node.value))
    
    def _transform_augassign(self, node: AugAssign) -> AugAssign:
        """Transform AugAssign: x += value"""
        return replace(node, value=self.transform(node.value))
    
    def _transform_if(self, node: If) -> If:
        """Transform If statement."""
        return replace(
            node,
            test=self.transform(node.test),
            body=self.transform_all(node.body),
            orelse=self.transform_all(node.orelse),
        )
    
    def _transform_for(self, node: For) -> For:
        """Transform For loop."""
        return replace(
            node,
            iter=self.transform(node.iter),
            body=self.transform_all(node.body),
        )
    
    def _transform_while(self, node: While) -> While:
        """Transform While loop."""
        return replace(
            node,
            test=self.transform(node.test),
            body=self.transform_all(node.body),
        )
    
    def _transform_return(self, node: Return) -> Return:
        """Transform Return statement."""
        if node.value is None:
            return node
        return replace(node, value=self.transform(node.value))
    
    def _transform_delete(self, node: Delete) -> Delete:
        """Transform Delete statement."""
        return replace(node, target=self.transform(node.target))
    
    def _transform_exprstmt(self, node: ExprStmt) -> ExprStmt:
        """Transform ExprStmt."""
        return replace(node, value=self.transform(node.value))
    
    # =========================================================================
    # EXPRESSION TRANSFORMS - CORE REACTIVE LOGIC
    # =========================================================================
    
    def _transform_call(self, node: Call) -> Call:
        """
        Transform Call node - THIS IS THE HEART OF PYNEXT TRANSFORMS.
        
        Handles:
        - signal() → __pynext__.getSignal('id').read()
        - signal.set(v) → __pynext__.getSignal('id').set(v)
        - signal.update(fn) → __pynext__.getSignal('id').update(fn)
        - memo() → __pynext__.getMemo('id').read()
        - form.validate() → __pynext__.getForm('id').validate()
        - form.reset() → __pynext__.getForm('id').reset()
        """
        # Case 1: Direct call like signal() or memo()
        if isinstance(node.func, Name):
            name = node.func.id
            
            # Signal read: count() → __pynext__.getSignal('count').read()
            # IMPORTANT: Use signal NAME (not internal ID) for client-side lookups
            # The client runtime stores signals by name for stable references
            if name in self._signal_names:
                signal_name = self.ctx.signals[name].name
                return _method_call(_pynext_get_signal(signal_name), "read")
            
            # Memo read: total() → __pynext__.getSignal('total').read()
            # Memos are hydrated as signals on the client, so use getSignal with name
            if name in self._memo_names:
                memo_name = self.ctx.memos[name].name
                return _method_call(_pynext_get_signal(memo_name), "read")
        
        # Case 2: Method call like signal.set(v) or form.validate()
        if isinstance(node.func, Attribute):
            obj = node.func.value
            method = node.func.attr
            
            # Transform arguments first
            transformed_args = self.transform_all(node.args)
            transformed_keywords = tuple(
                (k, self.transform(v)) for k, v in node.keywords
            )
            
            # Signal methods: count.set(v), count.update(fn), count.peek()
            # Use signal NAME (not ID) for stable client-side lookups
            if isinstance(obj, Name) and obj.id in self._signal_names:
                signal_name = self.ctx.signals[obj.id].name
                signal_obj = _pynext_get_signal(signal_name)
                
                if method in ("set", "update", "peek"):
                    return Call(
                        func=Attribute(value=signal_obj, attr=method),
                        args=transformed_args,
                        keywords=transformed_keywords,
                        line=node.line,
                        col=node.col,
                    )
            
            # Form methods: form.validate(), form.reset()
            if isinstance(obj, Name) and obj.id in self._form_names:
                form_id = self.ctx.forms[obj.id].id
                form_obj = _pynext_get_form(form_id)
                
                if method in ("validate", "reset", "submit", "set_error", "clear_errors"):
                    return Call(
                        func=Attribute(value=form_obj, attr=method),
                        args=transformed_args,
                        keywords=transformed_keywords,
                        line=node.line,
                        col=node.col,
                    )
            
            # Form field access: form.title.set(v)
            if isinstance(obj, Attribute):
                if isinstance(obj.value, Name) and obj.value.id in self._form_names:
                    form_name = obj.value.id
                    field_name = obj.attr
                    
                    # Validate form field exists
                    self._validate_form_field(form_name, field_name, node.line or 0)
                    
                    form_id = self.ctx.forms[form_name].id
                    form_obj = _pynext_get_form(form_id)
                    
                    # form.title.set(v) → __pynext__.getForm('id').title.set(v)
                    return Call(
                        func=Attribute(
                            value=Attribute(value=form_obj, attr=field_name),
                            attr=method,
                        ),
                        args=transformed_args,
                        keywords=transformed_keywords,
                        line=node.line,
                        col=node.col,
                    )
            
            # Store methods: store.items.append(v), etc.
            if isinstance(obj, Attribute):
                if isinstance(obj.value, Name) and obj.value.id in self._store_names:
                    store_name = obj.value.id
                    prop_name = obj.attr
                    store_id = self.ctx.stores[store_name].id
                    store_obj = _pynext_get_store(store_id)
                    
                    # store.items.append(v) → __pynext__.getStore('id').items.append(v)
                    return Call(
                        func=Attribute(
                            value=Attribute(value=store_obj, attr=prop_name),
                            attr=method,
                        ),
                        args=transformed_args,
                        keywords=transformed_keywords,
                        line=node.line,
                        col=node.col,
                    )
            
            # Memo method: memo.peek()
            if isinstance(obj, Name) and obj.id in self._memo_names:
                memo_id = self.ctx.memos[obj.id].id
                memo_obj = _pynext_get_memo(memo_id)
                
                if method == "peek":
                    return Call(
                        func=Attribute(value=memo_obj, attr=method),
                        args=transformed_args,
                        keywords=transformed_keywords,
                        line=node.line,
                        col=node.col,
                    )
        
        # Handle signals/memos passed as arguments to any function
        # Example: some_function(count()) where count is a signal
        # The signal() call inside args needs to be transformed
        transformed_args = self.transform_all(node.args)
        transformed_keywords = tuple((k, self.transform(v)) for k, v in node.keywords)
        
        # Default: recursively transform func and args
        return replace(
            node,
            func=self.transform(node.func),
            args=transformed_args,
            keywords=transformed_keywords,
        )
    
    def _transform_attribute(self, node: Attribute) -> JSNode:
        """
        Transform Attribute access.
        
        Handles:
        - form.values → __pynext__.getForm('id').values
        - form.errors → __pynext__.getForm('id').errors
        - store.items → __pynext__.getStore('id').items
        """
        # Form property access: form.values, form.errors, form.is_valid
        if isinstance(node.value, Name) and node.value.id in self._form_names:
            form_id = self.ctx.forms[node.value.id].id
            form_obj = _pynext_get_form(form_id)
            
            # form.values → __pynext__.getForm('id').values
            return Attribute(
                value=form_obj,
                attr=node.attr,
                line=node.line,
                col=node.col,
            )
        
        # Store property access: store.items
        if isinstance(node.value, Name) and node.value.id in self._store_names:
            store_id = self.ctx.stores[node.value.id].id
            store_obj = _pynext_get_store(store_id)
            
            # store.items → __pynext__.getStore('id').items
            return Attribute(
                value=store_obj,
                attr=node.attr,
                line=node.line,
                col=node.col,
            )
        
        # Form field access: form.title (for reading)
        # But NOT form.errors (that's a property)
        if isinstance(node.value, Name) and node.value.id in self._form_names:
            # Validate field access (unless it's a known property)
            self._validate_form_field(node.value.id, node.attr, node.line or 0)
        
        # Nested attribute: form.errors.title
        if isinstance(node.value, Attribute):
            if isinstance(node.value.value, Name):
                base_name = node.value.value.id
                
                if base_name in self._form_names:
                    form_id = self.ctx.forms[base_name].id
                    form_obj = _pynext_get_form(form_id)
                    
                    # form.errors.title → __pynext__.getForm('id').errors.title
                    return Attribute(
                        value=Attribute(
                            value=form_obj,
                            attr=node.value.attr,
                        ),
                        attr=node.attr,
                        line=node.line,
                        col=node.col,
                    )
                
                if base_name in self._store_names:
                    store_id = self.ctx.stores[base_name].id
                    store_obj = _pynext_get_store(store_id)
                    
                    # store.user.name → __pynext__.getStore('id').user.name
                    return Attribute(
                        value=Attribute(
                            value=store_obj,
                            attr=node.value.attr,
                        ),
                        attr=node.attr,
                        line=node.line,
                        col=node.col,
                    )
        
        # Default: recursively transform value
        return replace(node, value=self.transform(node.value))
    
    def _transform_subscript(self, node: Subscript) -> Subscript:
        """
        Transform Subscript access.
        
        Handles:
        - store["key"] → __pynext__.getStore('id')["key"]
        - store.items[signal()] → __pynext__.getStore('id').items[__pynext__.getSignal('id').read()]
        
        CRITICAL FIX: Also transforms signal() calls inside the slice/index.
        """
        # Store subscript: store["items"]
        if isinstance(node.value, Name) and node.value.id in self._store_names:
            store_id = self.ctx.stores[node.value.id].id
            store_obj = _pynext_get_store(store_id)
            
            return Subscript(
                value=store_obj,
                slice=self.transform(node.slice),  # Transform the slice too!
                line=node.line,
                col=node.col,
            )
        
        # Handle store.prop[signal()] - nested attribute + subscript with dynamic index
        if isinstance(node.value, Attribute):
            if isinstance(node.value.value, Name) and node.value.value.id in self._store_names:
                store_id = self.ctx.stores[node.value.value.id].id
                store_obj = _pynext_get_store(store_id)
                
                return Subscript(
                    value=Attribute(value=store_obj, attr=node.value.attr),
                    slice=self.transform(node.slice),  # Transform signals in index
                    line=node.line,
                    col=node.col,
                )
        
        # Default: recursively transform both value AND slice
        # This ensures signal() calls in indexes are transformed
        return replace(
            node,
            value=self.transform(node.value),
            slice=self.transform(node.slice),
        )
    
    def _transform_name(self, node: Name) -> JSNode:
        """
        Transform Name reference.
        
        NOTE: Most Name transforms happen in Call context.
        Bare Name references to reactive objects are typically errors
        (you should call them), but we handle gracefully.
        
        CRITICAL: Substitute constants captured from closure with their values.
        This handles patterns like:
            issue_id = 1
            lambda: all_issues.set([i for i in all_issues() if i["id"] != issue_id])
        Here issue_id should become the literal value 1 in JavaScript.
        """
        # Check if this name is a captured constant that should be inlined
        if node.id in self.ctx.constants:
            value = self.ctx.constants[node.id]
            return Constant(value=value, line=node.line, col=node.col)
        
        # Don't transform bare names - they're handled in Call context
        return node
    
    # =========================================================================
    # OTHER EXPRESSION TRANSFORMS
    # =========================================================================
    
    def _transform_binop(self, node: BinOp) -> BinOp:
        """Transform BinOp."""
        return replace(
            node,
            left=self.transform(node.left),
            right=self.transform(node.right),
        )
    
    def _transform_unaryop(self, node: UnaryOp) -> UnaryOp:
        """Transform UnaryOp."""
        return replace(node, operand=self.transform(node.operand))
    
    def _transform_compare(self, node: Compare) -> Compare:
        """Transform Compare."""
        return replace(
            node,
            left=self.transform(node.left),
            comparators=self.transform_all(node.comparators),
        )
    
    def _transform_boolop(self, node: BoolOp) -> BoolOp:
        """Transform BoolOp."""
        return replace(node, values=self.transform_all(node.values))
    
    def _transform_ifexp(self, node: IfExp) -> IfExp:
        """Transform IfExp (ternary)."""
        return replace(
            node,
            test=self.transform(node.test),
            body=self.transform(node.body),
            orelse=self.transform(node.orelse),
        )
    
    def _transform_lambda(self, node: Lambda) -> Lambda:
        """Transform Lambda."""
        return replace(node, body=self.transform(node.body))
    
    def _transform_await(self, node: Await) -> Await:
        """
        Transform Await expression.
        
        CRITICAL: Signals inside awaited expressions must be transformed.
        
        Example:
            await api.fetch(count())
            → await api.fetch(__pynext__.getSignal('id').read())
        """
        return replace(node, value=self.transform(node.value))
    
    def _transform_list(self, node: ListNode) -> ListNode:
        """Transform List literal."""
        return replace(node, elts=self.transform_all(node.elts))
    
    def _transform_dict(self, node: DictNode) -> DictNode:
        """Transform Dict literal."""
        return replace(
            node,
            keys=self.transform_all(node.keys),
            values=self.transform_all(node.values),
        )
    
    def _transform_tuple(self, node: TupleNode) -> TupleNode:
        """Transform Tuple literal."""
        return replace(node, elts=self.transform_all(node.elts))
    
    def _transform_starred(self, node: Starred) -> Starred:
        """Transform Starred (*args)."""
        return replace(node, value=self.transform(node.value))
    
    def _transform_slice(self, node: Slice) -> Slice:
        """Transform Slice."""
        return replace(
            node,
            lower=self.transform(node.lower) if node.lower else None,
            upper=self.transform(node.upper) if node.upper else None,
            step=self.transform(node.step) if node.step else None,
        )
    
    def _transform_listcomp(self, node: ListComp) -> ListComp:
        """Transform list comprehension."""
        return replace(
            node,
            element=self.transform(node.element),
            generators=tuple(
                replace(
                    g,
                    iter=self.transform(g.iter),
                    ifs=tuple(self.transform(c) for c in g.ifs),
                )
                for g in node.generators
            ),
        )
    
    def _transform_generatorexp(self, node: GeneratorExp) -> GeneratorExp:
        """Transform generator expression."""
        return replace(
            node,
            element=self.transform(node.element),
            generators=tuple(
                replace(
                    g,
                    iter=self.transform(g.iter),
                    ifs=tuple(self.transform(c) for c in g.ifs),
                )
                for g in node.generators
            ),
        )
    
    def _transform_dictcomp(self, node: DictComp) -> DictComp:
        """
        Transform dict comprehension.
        
        CRITICAL FIX: This was missing, causing signals inside dict
        comprehensions to not be transformed.
        
        Example:
            {x: count() for x in items}
            → {x: __pynext__.getSignal('id').read() for x in items}
        """
        return replace(
            node,
            key=self.transform(node.key),
            value=self.transform(node.value),
            generators=tuple(
                replace(
                    g,
                    iter=self.transform(g.iter),
                    ifs=tuple(self.transform(c) for c in g.ifs),
                )
                for g in node.generators
            ),
        )
    
    def _transform_setcomp(self, node: SetComp) -> SetComp:
        """
        Transform set comprehension.
        
        CRITICAL FIX: This was missing, causing signals inside set
        comprehensions to not be transformed.
        
        Example:
            {count() for x in items}
            → {__pynext__.getSignal('id').read() for x in items}
        """
        return replace(
            node,
            element=self.transform(node.element),
            generators=tuple(
                replace(
                    g,
                    iter=self.transform(g.iter),
                    ifs=tuple(self.transform(c) for c in g.ifs),
                )
                for g in node.generators
            ),
        )
    
    def _transform_try(self, node: Try) -> Try:
        """
        Transform Try/Except/Finally statement.
        
        CRITICAL FIX: Signals inside try/except blocks must be transformed.
        
        Example:
            try:
                count.set(risky_operation())
            except:
                error.set("Failed")
        
        Transforms to:
            try {
                __pynext__.getSignal('sig_1').set(risky_operation());
            } catch (_e) {
                __pynext__.getSignal('sig_2').set("Failed");
            }
        """
        return replace(
            node,
            body=self.transform_all(node.body),
            handlers=tuple(
                replace(
                    h,
                    body=self.transform_all(h.body),
                )
                for h in node.handlers
            ),
            orelse=self.transform_all(node.orelse),
            finalbody=self.transform_all(node.finalbody),
        )
    
    # =========================================================================
    # GENERIC FALLBACK - RECURSIVE TRANSFORMATION
    # =========================================================================
    
    def _transform_generic(self, node: JSNode) -> JSNode:
        """
        Generic transform for nodes without specific handlers.
        
        =============================================================================
        WHAT THIS DOES
        =============================================================================
        
        Recursively transforms all JSNode children of a node, even when there's
        no specific `_transform_{NodeType}` handler. This ensures that reactive
        transformations (signal.set(), form.validate(), etc.) are applied to
        ALL nodes, including:
        
        - AsyncFunctionDef: Transforms the function body
        - ClassDef: Transforms class body methods
        - With/AsyncWith: Transforms context manager body
        - Match: Transforms pattern matching cases
        - Any future node types with JSNode children
        
        =============================================================================
        WHY THIS EXISTS (Problem It Solves)
        =============================================================================
        
        Before this fix, if a node type didn't have a specific handler (like
        AsyncFunctionDef), the transformer would return it unchanged. This meant
        that reactive transformations inside async functions, class methods, or
        context managers were never applied, causing runtime errors.
        
        Example of the problem:
        
            async def handle_click():
                count.set(count() + 1)  # ❌ Never transformed!
            
            # Without this fix:
            # → async function handle_click() {
            #       count.set(count() + 1);  // ERROR: count is not defined
            #   }
            
            # With this fix:
            # → async function handle_click() {
            #       __pynext__.getSignal('sig_1').set(
            #           __pynext__.getSignal('sig_1').read() + 1
            #       );
            #   }
        
        =============================================================================
        HOW IT WORKS (Architecture)
        =============================================================================
        
        This method uses the same proven pattern as `IRVisitor.generic_visit`
        from the optimizer (see `optimizer/_internal/visitor.py`). It:
        
        1. Checks if the node is a dataclass (all IR nodes are)
        2. Iterates through all fields of the dataclass
        3. For each field, calls `_transform_field()` to recursively transform
           JSNode children
        4. Only creates a new node if any children were transformed (immutability
           optimization)
        5. Returns the transformed (or original) node
        
        This pattern is:
        - **Robust**: Works for ALL node types automatically
        - **Efficient**: Only transforms JSNode children, skips primitives
        - **Future-proof**: New node types work without code changes
        - **Proven**: Same pattern used successfully in the optimizer
        
        =============================================================================
        WHO USES THIS
        =============================================================================
        
        - `transform()`: Calls this when no specific `_transform_{NodeType}`
          handler exists
        - Indirectly: All async handlers, class methods, context managers,
          pattern matching, and any future constructs that don't have specific
          handlers
        
        =============================================================================
        WHEN TO USE (vs Alternatives)
        =============================================================================
        
        This is the fallback for nodes without specific handlers. If you need
        special transformation logic for a specific node type, add a
        `_transform_{NodeType}` method instead. This generic handler ensures
        that even without a specific handler, children are still transformed.
        
        =============================================================================
        EFFICIENCY ANALYSIS
        =============================================================================
        
        Time Complexity: O(n) where n = number of JSNode children
        - This is necessary - we must visit all children
        - `isinstance()` checks are O(1) and very fast
        - Dataclass field introspection is cached by Python
        
        Space Complexity: O(1)
        - Only creates new nodes when changes occur
        - No additional data structures needed
        
        Performance Characteristics:
        - Minimal overhead: Only iterates dataclass fields (fast introspection)
        - Early exit: Only creates new node if changes occurred
        - Fast checks: `isinstance(value, JSNode)` is optimized in Python
        - No redundant work: Doesn't transform unchanged nodes
        
        =============================================================================
        EXAMPLES
        =============================================================================
        
        Example 1: AsyncFunctionDef without specific handler
        
            Input IR:
                AsyncFunctionDef(
                    name="handle_click",
                    body=(
                        ExprStmt(Call(
                            func=Attribute(
                                value=Name("count"),
                                attr="set"
                            ),
                            args=(Call(func=Name("count")),)
                        ))
                    )
                )
            
            Without this fix:
                → Returns unchanged (reactive transforms never applied)
            
            With this fix:
                → Recursively transforms body → ExprStmt → Call → Attribute → Name
                → Name("count") → Call(__pynext__.getSignal('sig_1'), "read")
                → Final output has all reactive transforms applied
        
        Example 2: ClassDef with methods
        
            Input IR:
                ClassDef(
                    name="Todo",
                    body=(
                        MethodDef(
                            name="toggle",
                            body=(
                                ExprStmt(Call(
                                    func=Attribute(
                                        value=Name("self"),
                                        attr="done"
                                    ),
                                    attr="set"
                                ))
                            )
                        )
                    )
                )
            
            This fix ensures:
                → MethodDef body is transformed
                → ExprStmt is transformed
                → Call is transformed
                → Attribute is transformed
                → If "done" is a signal, it becomes __pynext__.getSignal(...)
        
        Example 3: With statement (context manager)
        
            Input IR:
                With(
                    items=(WithItem(context=Name("file"), target=Name("f")),),
                    body=(
                        ExprStmt(Call(func=Name("process"), args=(Name("f"),))),
                    )
                )
            
            This fix ensures:
                → With body is transformed
                → ExprStmt is transformed
                → Call is transformed
                → If "process" is a signal/memo, it's correctly transformed
        
        =============================================================================
        DESIGN DECISIONS
        =============================================================================
        
        1. **Why reuse IRVisitor pattern?**
           - It's proven and battle-tested in the optimizer
           - Handles all edge cases (tuples, lists, nested structures)
           - Consistent with the rest of the codebase
        
        2. **Why not add specific handlers for every node type?**
           - Would require maintaining handlers for 50+ node types
           - This generic handler covers 95% of cases automatically
           - Specific handlers only needed for special transformation logic
        
        3. **Why not use type hints for field detection?**
           - Type hints aren't available at runtime in a way that's more efficient
           - `isinstance()` checks are fast and reliable
           - Simpler and more maintainable
        
        4. **Why only transform if changes occurred?**
           - Immutability optimization: don't create new nodes unnecessarily
           - Reduces memory allocation
           - Faster for unchanged subtrees
        
        =============================================================================
        EDGE CASES HANDLED
        =============================================================================
        
        - **None values**: Safely skipped (not JSNode)
        - **Primitive values**: Safely skipped (int, str, bool, etc.)
        - **Empty tuples/lists**: Handled correctly (no-op)
        - **Mixed collections**: Only transforms JSNode items, preserves others
        - **Nested structures**: Recursively handles deeply nested nodes
        - **Frozen dataclasses**: Uses `replace()` to create new instances
        
        =============================================================================
        TESTING
        =============================================================================
        
        This fix is tested by:
        - `tests/unit/bridge/test_event_handler_pipeline.py`: Async handler tests
        - `tests/integration/transpiler/test_332_mini_applications.py`: Integration tests
        - All tests that use async functions, classes, context managers, pattern matching
        
        =============================================================================
        RELATED CODE
        =============================================================================
        
        - `optimizer/_internal/visitor.py`: IRVisitor.generic_visit (same pattern)
        - `optimizer/_internal/visitor.py`: _visit_field (same logic)
        - `pynext/transpiler/pynext.py`: transform() (calls this method)
        - `pynext/transpiler/pynext.py`: _transform_field() (helper method)
        
        =============================================================================
        """
        # Early exit: Not a dataclass (shouldn't happen for IR nodes, but defensive)
        if not is_dataclass(node):
            return node
        
        # Track which fields were transformed (for immutability optimization)
        changes = {}
        
        # Iterate through all dataclass fields
        # This automatically handles ALL node types without needing specific handlers
        for field in fields(node):
            # Get the current field value
            value = getattr(node, field.name)
            
            # Recursively transform the field (handles JSNode, tuples, lists)
            new_value = self._transform_field(value)
            
            # Only track changes (don't create new node if nothing changed)
            if new_value is not value:
                changes[field.name] = new_value
        
        # Only create a new node if changes occurred (immutability optimization)
        if changes:
            return replace(node, **changes)
        
        # No changes: return original node (avoids unnecessary allocations)
        return node
    
    def _transform_field(self, value: Any) -> Any:
        """
        Transform a field value - recursively handles JSNode and collections.
        
        =============================================================================
        WHAT THIS DOES
        =============================================================================
        
        Recursively transforms a field value that may be:
        - A single JSNode (e.g., `body: JSNode`)
        - A tuple of JSNodes (e.g., `body: tuple[JSNode, ...]`)
        - A list of JSNodes (e.g., `body: list[JSNode]`)
        - A primitive value (e.g., `name: str`) - returned unchanged
        - None - returned unchanged
        
        This is the core recursive logic that enables `_transform_generic` to
        automatically transform all children of any node type.
        
        =============================================================================
        WHY THIS EXISTS
        =============================================================================
        
        IR nodes have different field types:
        - Some fields are single JSNode: `test: JSNode` in If
        - Some fields are tuples: `body: tuple[JSNode, ...]` in FunctionDef
        - Some fields are primitives: `name: str` in FunctionDef
        
        We need a unified way to transform all JSNode children, regardless of
        the container type. This method provides that.
        
        =============================================================================
        HOW IT WORKS
        =============================================================================
        
        1. **JSNode**: Directly transform it via `self.transform()`
        2. **Tuple/List**: Iterate through items, transform JSNode items only
        3. **Primitive/None**: Return unchanged (not JSNode, no transformation needed)
        
        The method preserves the original container type (tuple vs list) and only
        creates a new container if items were actually transformed.
        
        =============================================================================
        EFFICIENCY
        =============================================================================
        
        - **Fast checks**: `isinstance()` is O(1) and optimized in Python
        - **Early exit**: Returns original value if not JSNode/collection
        - **Lazy transformation**: Only creates new containers if changes occurred
        - **Type preservation**: Maintains tuple vs list distinction
        
        =============================================================================
        EXAMPLES
        =============================================================================
        
        Example 1: Single JSNode field
        
            Input: Name(id="count")
            → Calls self.transform(Name(id="count"))
            → Returns transformed Name (or original if unchanged)
        
        Example 2: Tuple of JSNodes
        
            Input: (Name(id="a"), Name(id="b"), Constant(value=5))
            → Transforms Name("a") → transformed_a
            → Transforms Name("b") → transformed_b
            → Transforms Constant(5) → transformed_c
            → Returns (transformed_a, transformed_b, transformed_c)
            → Or original tuple if no changes
        
        Example 3: Mixed collection
        
            Input: (Name(id="count"), "string", 42, None)
            → Transforms Name("count") → transformed_name
            → Skips "string" (not JSNode)
            → Skips 42 (not JSNode)
            → Skips None (not JSNode)
            → Returns (transformed_name, "string", 42, None)
        
        Example 4: Primitive value
        
            Input: "function_name"
            → Returns "function_name" unchanged (not JSNode)
        
        =============================================================================
        EDGE CASES
        =============================================================================
        
        - **Empty collections**: Returns empty collection unchanged
        - **None values**: Returns None unchanged
        - **Nested collections**: Handles recursively (though IR nodes don't use this)
        - **Mixed types**: Only transforms JSNode items, preserves others
        
        =============================================================================
        RELATED CODE
        =============================================================================
        
        - `optimizer/_internal/visitor.py`: _visit_field() (same logic)
        - `pynext/transpiler/pynext.py`: _transform_generic() (calls this)
        - `pynext/transpiler/pynext.py`: transform() (entry point)
        
        =============================================================================
        """
        # Case 1: Single JSNode - transform it directly
        if isinstance(value, JSNode):
            return self.transform(value)
        
        # Case 2: Tuple or list of items - transform JSNode items only
        elif isinstance(value, (tuple, list)):
            new_items = []
            changed = False
            
            for item in value:
                # Only transform JSNode items, preserve primitives
                if isinstance(item, JSNode):
                    new_item = self.transform(item)
                    # Track if this item was transformed
                    if new_item is not item:
                        changed = True
                    new_items.append(new_item)
                else:
                    # Not a JSNode - preserve as-is
                    new_items.append(item)
            
            # Only create new container if items were transformed
            if changed:
                # Preserve original container type (tuple vs list)
                return tuple(new_items) if isinstance(value, tuple) else new_items
            
            # No changes: return original container (immutability optimization)
            return value
        
        # Case 3: Primitive value or None - return unchanged
        # (This includes: str, int, bool, None, etc.)
        return value


# =============================================================================
# PUBLIC API
# =============================================================================

def transpile_handler(
    func: Callable,
    ctx: ReactiveContext = None,
) -> str:
    """
    Transpile a Python handler function to JavaScript.
    
    This is the main entry point for PyNext handler transpilation.
    It combines:
    1. Reactive context analysis (if not provided)
    2. Python→IR parsing
    3. PyNext transforms
    4. JavaScript emission
    
    Args:
        func: The Python function to transpile
        ctx: Optional ReactiveContext (auto-detected if not provided)
    
    Returns:
        JavaScript source code
    
    Example:
        def handle_click():
            count.set(count() + 1)
        
        js = transpile_handler(handle_click, ctx)
        # → "function handle_click() {
        #       __pynext__.getSignal('sig_1').set(
        #           __pynext__.getSignal('sig_1').read() + 1
        #       );
        #   }"
    """
    from .reactive import analyze_handler, get_handler_source
    from .parser import parse
    from .emitter import emit
    
    # Auto-detect reactive context if not provided
    if ctx is None:
        ctx = analyze_handler(func)
    
    # Get source code
    source = get_handler_source(func)
    if source is None:
        raise ValueError(f"Cannot get source for {func}")
    
    # Parse to IR
    ir = parse(source)
    
    # Transform for PyNext
    transformer = PyNextTransformer(ctx)
    transformed_ir = transformer.transform(ir)
    
    # Emit JavaScript
    return emit(transformed_ir)


def transpile_handler_source(
    source: str,
    ctx: ReactiveContext,
) -> str:
    """
    Transpile Python handler source code to JavaScript.
    
    Use this when you have source code but not the function object.
    
    Args:
        source: Python source code
        ctx: ReactiveContext with name→id mappings
    
    Returns:
        JavaScript source code
    """
    from .parser import parse
    from .emitter import emit
    
    # Parse to IR
    ir = parse(source)
    
    # Transform for PyNext
    transformer = PyNextTransformer(ctx)
    transformed_ir = transformer.transform(ir)
    
    # Emit JavaScript
    return emit(transformed_ir)


def transpile_handler_body(
    func: Callable,
    ctx: ReactiveContext = None,
) -> str:
    """
    Transpile just the body of a handler (no function wrapper).
    
    This is useful for inline event handlers where you just need
    the statements, not the function definition.
    
    Args:
        func: The Python function
        ctx: Optional ReactiveContext
    
    Returns:
        JavaScript statements (no function wrapper)
    """
    from .reactive import analyze_handler, get_handler_source
    from .parser import parse_function
    from .emitter import emit
    import ast
    
    # Auto-detect reactive context if not provided
    if ctx is None:
        ctx = analyze_handler(func)
    
    # Get source code
    source = get_handler_source(func)
    if source is None:
        raise ValueError(f"Cannot get source for {func}")
    
    # Parse AST to find function or lambda
    tree = ast.parse(source)
    func_node = None
    lambda_node = None
    
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_node = node
            break
        elif isinstance(node, ast.Lambda):
            lambda_node = node
    
    if func_node is None and lambda_node is None:
        raise ValueError("No function or lambda definition found")
    
    # Handle lambda specially - wrap body in a Return
    if func_node is None and lambda_node is not None:
        # For lambda, create a synthetic function with the lambda body
        func_node = ast.FunctionDef(
            name='_lambda',
            args=lambda_node.args,
            body=[ast.Return(value=lambda_node.body)],
            decorator_list=[],
            returns=None,
        )
        ast.fix_missing_locations(func_node)
    
    # Parse to IR
    ir = parse_function(func_node, source=source)
    
    # Transform for PyNext
    transformer = PyNextTransformer(ctx)
    transformed_ir = transformer.transform(ir)
    
    # FUNDAMENTAL FIX: Extract parameter names for event handler aliasing
    # Python handlers commonly use 'e' for the event, but JS runtime uses 'event'
    # We emit aliases for the first parameter to ensure compatibility
    param_aliases = []
    if func_node.args and func_node.args.args:
        first_param = func_node.args.args[0].arg
        # Common event parameter names in Python: e, ev, evt, event
        # If the handler uses any of these (except 'event'), alias it
        if first_param in ('e', 'ev', 'evt'):
            # The JS runtime passes 'event', so we alias to the Python name
            param_aliases.append(f"const {first_param} = event;")
    
    # Emit just the body statements
    # Skip docstrings - they become string literals that break HTML attributes
    lines = param_aliases.copy()  # Start with aliases
    for stmt in transformed_ir.body:
        # Skip docstrings: ExprStmt containing just a Constant string
        from .nodes import ExprStmt, Constant
        if isinstance(stmt, ExprStmt) and isinstance(stmt.value, Constant) and isinstance(stmt.value.value, str):
            continue
        emitted = emit(stmt, indent=0)
        lines.append(emitted)
    
    return "\n".join(lines)


def transpile_memo_computation(
    func: Callable,
    ctx: ReactiveContext = None,
) -> str:
    """
    Transpile a memo's computation function to a JavaScript arrow function.
    
    Unlike transpile_handler which returns full function statements, this returns
    just the arrow function: "() => expression"
    
    This is specifically designed for memo computation functions that are typically
    defined as inline lambdas:
    
        total_count = memo(lambda: len(all_issues()), name="total_count")
    
    The result is a JavaScript arrow function that can be evaluated client-side:
    
        () => __py.len(__pynext__.getSignal('all_issues').read())
    
    Args:
        func: The Python lambda/function to transpile
        ctx: Optional ReactiveContext (auto-detected if not provided)
    
    Returns:
        JavaScript arrow function string: "() => expression"
    
    Example:
        >>> status_counts = memo(
        ...     lambda: {s: len([i for i in all_issues() if i["status"] == s])
        ...              for s in STATUS_LABELS.keys()},
        ...     name="status_counts"
        ... )
        >>> js = transpile_memo_computation(status_counts._fn, ctx)
        >>> # Returns: "() => Object.fromEntries([...STATUS_LABELS.keys()].map(...))"
    """
    from .reactive import analyze_handler, get_handler_source
    from .parser import parse
    from .emitter import emit
    import ast
    
    # Auto-detect reactive context if not provided
    if ctx is None:
        ctx = analyze_handler(func)
    
    # Get source code
    source = get_handler_source(func)
    if source is None:
        raise ValueError(f"Cannot get source for {func}")
    
    # Parse to find the lambda or function
    tree = ast.parse(source)
    lambda_node = None
    func_node = None
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Lambda):
            lambda_node = node
            break
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_node = node
    
    if lambda_node is not None:
        # Lambda: extract just the body expression
        body_source = ast.unparse(lambda_node.body)
        
        # Parse and transform just the body expression as a return statement
        ir = parse(f"return {body_source}")
        transformer = PyNextTransformer(ctx)
        transformed_ir = transformer.transform(ir)
        
        # Emit the transformed code
        body_js = emit(transformed_ir).strip()
        
        # Remove "return " prefix and trailing semicolon to get just the expression
        if body_js.startswith("return "):
            body_js = body_js[7:]
        if body_js.endswith(";"):
            body_js = body_js[:-1]
        
        return f"() => {body_js}"
    
    elif func_node is not None:
        # Regular function: transpile and extract body
        # For multi-statement functions, we need to wrap in an IIFE
        ir = parse(source)
        transformer = PyNextTransformer(ctx)
        transformed_ir = transformer.transform(ir)
        
        # Get the body statements
        body_lines = []
        for stmt in transformed_ir.body:
            body_lines.append(emit(stmt, indent=0))
        
        body_js = "\n".join(body_lines)
        
        # Wrap in an arrow function with block body
        return f"() => {{ {body_js} }}"
    
    else:
        # Fallback: treat the entire source as an expression
        ir = parse(f"return {source}")
        transformer = PyNextTransformer(ctx)
        transformed_ir = transformer.transform(ir)
        
        body_js = emit(transformed_ir).strip()
        if body_js.startswith("return "):
            body_js = body_js[7:]
        if body_js.endswith(";"):
            body_js = body_js[:-1]
        
        return f"() => {body_js}"
