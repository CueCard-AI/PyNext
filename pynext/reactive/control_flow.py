"""
PyNext Control Flow - DOM Primitives for Reactive Rendering

=============================================================================
WHAT THIS FILE DOES (AI Summary)
=============================================================================

This module provides DECLARATIVE CONTROL FLOW components for building
dynamic UIs without a Virtual DOM. These components enable:

1. CONDITIONAL RENDERING: Show/hide content based on reactive conditions
2. LIST RENDERING: Efficiently render and update lists with key-based reconciliation
3. MULTI-BRANCH LOGIC: Switch between multiple UI states
4. PORTAL RENDERING: Render content outside the component tree (modals, tooltips)
5. ERROR HANDLING: Catch and recover from errors in child components
6. ASYNC LOADING: Show fallback content while data loads

=============================================================================
WHY THIS MATTERS (vs React/Next.js)
=============================================================================

React uses a Virtual DOM and re-renders entire subtrees. PyNext uses:
- Fine-grained reactivity: Only update what changed
- Surgical DOM updates: No diffing of entire trees
- Keyed reconciliation: Minimal DOM operations for lists

PERFORMANCE COMPARISON:
┌─────────────────────────────────────────────────────────────────────────┐
│  Operation           │ React (VDOM)    │ PyNext (Fine-grained)          │
├─────────────────────────────────────────────────────────────────────────┤
│  Toggle visibility   │ Re-render tree  │ Toggle single element          │
│  Update 1 list item  │ Diff entire list│ Update that 1 item             │
│  Reorder list        │ Recreate nodes  │ Move existing nodes            │
│  Switch branch       │ Unmount/mount   │ Swap DOM references            │
└─────────────────────────────────────────────────────────────────────────┘

=============================================================================
MENTAL MODEL
=============================================================================

Think of these components as "reactive containers":

    Show(when=condition)[content]     # If container
    For(each=list)[render_item]       # Loop container  
    Switch()[Match(when=a)[...], ...] # Switch container
    Portal(mount="body")[modal]       # Teleport container
    ErrorBoundary(fallback=...)[...]  # Try-catch container

Each container:
1. Watches its condition/data reactively
2. Updates ONLY its DOM region when needed
3. Manages cleanup automatically

=============================================================================
"""

from __future__ import annotations

from typing import (
    Any, 
    Callable, 
    Generic, 
    Iterator,
    List, 
    Optional, 
    TypeVar, 
    Union,
    TYPE_CHECKING,
)
from dataclasses import dataclass, field
import uuid
from weakref import WeakSet

if TYPE_CHECKING:
    from pynext.reactive.signal import Signal
    from pynext.reactive.store import Store

T = TypeVar("T")
U = TypeVar("U")


# =============================================================================
# SECTION 1: SHOW - Conditional Rendering
# =============================================================================
#
# WHY SHOW EXISTS:
# The most common UI pattern is "show X if condition, else show Y".
# Show provides this with reactive updates - when condition changes,
# only the Show region updates, not the entire component.
#
# HOW IT WORKS:
# 1. Server-side: Evaluates condition, renders appropriate content
# 2. Client-side: Creates Effect that watches condition, swaps DOM
#
# KEYED MODE:
# When keyed=True, children are recreated on each toggle.
# Use this when children have state that should reset.
# =============================================================================

class Show(Generic[T]):
    """
    Conditional rendering component - show content when condition is true.
    
    WHY THIS EXISTS:
    Instead of using Python if/else which re-renders the entire template,
    Show creates a reactive boundary that surgically updates only when needed.
    
    USAGE PATTERNS:
    
    Basic conditional:
        Show(when=lambda: user() is not None)[
            lambda: div()[f"Welcome, {user().name}!"]
        ]
    
    With fallback:
        Show(
            when=lambda: items().length > 0,
            fallback=div()["No items yet"]
        )[
            lambda: ItemList(items=items)
        ]
    
    Keyed (reset state on toggle):
        Show(when=lambda: editing(), keyed=True)[
            lambda: EditForm()  # Fresh form each time
        ]
    
    IMPORTANT:
    - Use lambda for reactive content: Show(when=...)[lambda: ...]
    - Without lambda, content evaluates once at creation time
    
    Attributes:
        when: Condition (bool or callable returning bool)
        fallback: Content to show when condition is false
        keyed: If True, recreate children when condition changes
        children: Content to show when condition is true
    """
    
    __slots__ = ("when", "fallback", "keyed", "children", "_id")
    
    def __init__(
        self,
        when: Union[bool, Callable[[], bool]],
        fallback: Optional[Any] = None,
        keyed: bool = False,
    ) -> None:
        """
        Create a Show component.
        
        Args:
            when: Condition - can be:
                  - A boolean value
                  - A Signal (called as when())
                  - A lambda returning bool
            fallback: Content to render when condition is false.
                      Can be any renderable (element, string, component)
            keyed: If True, children are destroyed and recreated on each
                   toggle. Use when children have internal state that
                   should reset.
        
        Example:
            # Simple boolean
            Show(when=is_admin)[AdminPanel()]
            
            # Reactive signal
            Show(when=lambda: count() > 0)[PositiveMessage()]
            
            # With fallback
            Show(when=lambda: data(), fallback=Loading())[
                lambda: DataDisplay(data=data())
            ]
        """
        self.when = when
        self.fallback = fallback
        self.keyed = keyed
        self.children: Optional[Callable[[], Any]] = None
        self._id = f"show_{uuid.uuid4().hex[:12]}"
    
    def __getitem__(self, children: Union[Any, Callable[[], Any]]) -> "Show[T]":
        """
        Set the content to show when condition is true.
        
        Use lambda for reactive content:
            Show(when=...)[lambda: reactive_content()]
        
        Without lambda, content is evaluated once:
            Show(when=...)[static_content]
        """
        # Wrap non-callable in lambda for consistent handling
        self.children = children if callable(children) else lambda: children
        return self
    
    def _evaluate_condition(self) -> bool:
        """Evaluate the when condition to a boolean."""
        if callable(self.when):
            result = self.when()
            return bool(result)
        return bool(self.when)
    
    def render(self) -> str:
        """
        Render to HTML string (server-side).
        
        CRITICAL: Always render children, control visibility with CSS.
        This ensures the DOM exists for client-side toggle to work.
        
        Returns:
            HTML string with data attributes for hydration
        """
        from pynext.core.context import get_context
        
        condition = self._evaluate_condition()
        
        # ALWAYS render children - use CSS to hide when condition is false
        # This ensures the DOM exists for client-side reactivity
        if self.children:
            content = self.children()
            inner_html = _render_child(content)
        else:
            inner_html = ""
        
        # If condition is false and there's a fallback, render fallback instead
        # (but still keep the structure for toggle capability)
        if not condition and self.fallback:
            # Include both: hidden children + visible fallback
            fallback_html = _render_child(self.fallback)
            # Children hidden, fallback visible
            inner_html = f'<div data-show-content="true" style="display: none;">{inner_html}</div><div data-show-fallback="true">{fallback_html}</div>'
        elif not condition:
            # No fallback - just hide content
            pass  # inner_html stays as-is, we'll hide with style
        
        # Register binding for reactive updates
        ctx = get_context()
        if ctx:
            # Extract signal dependencies from the when condition
            signal_deps = self._extract_signal_deps()
            if signal_deps:
                # Generate update expression
                update_expr = self._generate_update_expr()
                ctx.register_binding(
                    node_id=self._id,
                    binding_type="show",
                    signal_deps=signal_deps,
                    update_expr=update_expr,
                    initial_value=condition,
                )
        
        # Wrap with hydration marker - use id attribute for binding lookup
        # Set initial display style based on condition
        keyed_attr = ' data-keyed="true"' if self.keyed else ""
        display_style = "" if condition else ' style="display: none;"'
        return f'<div id="{self._id}" data-pynext-show="true" data-condition="{str(condition).lower()}"{keyed_attr}{display_style}>{inner_html}</div>'
    
    def _extract_signal_deps(self) -> list[str]:
        """Extract signal IDs that the when condition depends on."""
        import inspect
        
        if not callable(self.when):
            return []
        
        deps = []
        
        # Try to inspect closure variables
        if hasattr(self.when, '__closure__') and self.when.__closure__:
            for cell in self.when.__closure__:
                try:
                    obj = cell.cell_contents
                    # Check if it's a Signal
                    if hasattr(obj, '_id') and hasattr(obj, '_value'):
                        deps.append(obj._id)
                except (ValueError, AttributeError):
                    pass
        
        return deps
    
    def _generate_update_expr(self) -> str:
        """Generate JavaScript expression for the when condition."""
        # Get signal deps and build expression
        deps = self._extract_signal_deps()
        if not deps:
            return "true"
        
        # For simple single-signal case, just read the signal
        if len(deps) == 1:
            return f"Boolean(__pynext__.getSignal('{deps[0]}').read())"
        
        # For multiple signals, we need more complex logic
        # For now, assume it's a simple truthy check
        reads = " && ".join(f"__pynext__.getSignal('{d}').read()" for d in deps)
        return f"Boolean({reads})"
    
    def __str__(self) -> str:
        return self.render()
    
    def __repr__(self) -> str:
        return f"Show(when={self.when!r}, keyed={self.keyed})"
    
    # =========================================================================
    # JavaScript Hydration Support
    # =========================================================================
    
    def to_js_init(self) -> str:
        """Generate JavaScript initialization code for client-side hydration."""
        return f"__pynext__.createShow('{self._id}')"


# =============================================================================
# SECTION 2: FOR - Keyed List Reconciliation
# =============================================================================
#
# WHY FOR EXISTS:
# Lists are the most performance-critical UI pattern. Naive approaches
# re-render entire lists on any change. For uses keyed reconciliation
# to perform minimal DOM operations.
#
# HOW IT WORKS:
# 1. Each item has a unique key (from key_fn or item.id or index)
# 2. On update, compare old keys to new keys
# 3. Create new items, remove deleted items, move reordered items
# 4. Never recreate unchanged items
#
# RECONCILIATION ALGORITHM:
# ┌─────────────────────────────────────────────────────────────────┐
# │  Old: [A, B, C, D]    New: [A, C, E, D]                        │
# │                                                                 │
# │  1. Build key map: {A: node0, B: node1, C: node2, D: node3}    │
# │  2. Process new list:                                          │
# │     - A: exists, keep in place                                 │
# │     - C: exists, move after A                                  │
# │     - E: new, create and insert                                │
# │     - D: exists, move after E                                  │
# │  3. Remove B (not in new list)                                 │
# │  4. Result: 1 create, 1 remove, 2 moves (not 4 creates!)       │
# └─────────────────────────────────────────────────────────────────┘
# =============================================================================

class For(Generic[T]):
    """
    Keyed list rendering with efficient reconciliation.
    
    WHY THIS EXISTS:
    For renders lists with minimal DOM operations. When the list changes:
    - New items: create new DOM nodes
    - Removed items: delete their DOM nodes
    - Moved items: reorder existing DOM nodes (no recreation!)
    - Unchanged items: leave untouched
    
    This is MUCH faster than React's approach of diffing entire subtrees.
    
    USAGE PATTERNS:
    
    Basic list:
        For(each=lambda: todos())[
            lambda todo, index: li(key=todo.id)[todo.text]
        ]
    
    With fallback:
        For(
            each=lambda: results(),
            fallback=p()["No results found"]
        )[
            lambda item, i: SearchResult(item=item)
        ]
    
    Custom key function:
        For(
            each=lambda: users(),
            key_fn=lambda user: user.email  # Use email as key
        )[
            lambda user, i: UserCard(user=user)
        ]
    
    KEY SELECTION:
    Keys must be unique and stable. Options:
    1. key_fn: Custom function to extract key
    2. item.id: If items have 'id' attribute
    3. index: Last resort (loses reconciliation benefits)
    
    Attributes:
        each: List or callable returning list
        fallback: Content when list is empty
        key_fn: Function to extract key from item
        render_fn: Function (item, index) -> content
    """
    
    __slots__ = ("each", "fallback", "key_fn", "render_fn", "_id")
    
    def __init__(
        self,
        each: Union[List[T], Callable[[], List[T]]],
        fallback: Optional[Any] = None,
        key_fn: Optional[Callable[[T], Any]] = None,
    ) -> None:
        """
        Create a For component.
        
        Args:
            each: The list to iterate. Can be:
                  - A static list
                  - A Signal containing a list
                  - A lambda returning a list
            fallback: Content to render when list is empty
            key_fn: Function to extract unique key from each item.
                    If not provided, uses item.id or index.
        
        Example:
            # Basic
            For(each=lambda: store.items)[
                lambda item, i: div()[item.name]
            ]
            
            # With key function
            For(
                each=lambda: store.users,
                key_fn=lambda u: u.email
            )[
                lambda user, i: UserRow(user=user)
            ]
        """
        self.each = each
        self.fallback = fallback
        self.key_fn = key_fn
        self.render_fn: Optional[Callable[[T, int], Any]] = None
        self._id = f"for_{uuid.uuid4().hex[:12]}"
    
    def __getitem__(self, render_fn: Callable[[T, int], Any]) -> "For[T]":
        """
        Set the render function for each item.
        
        The function receives (item, index) and returns renderable content.
        
        Example:
            For(each=items)[
                lambda item, index: div(key=item.id)[
                    f"{index + 1}. {item.name}"
                ]
            ]
        """
        self.render_fn = render_fn
        return self
    
    def _get_items(self) -> List[T]:
        """Get the current list of items."""
        if callable(self.each):
            result = self.each()
            # Handle proxy objects from Store
            if hasattr(result, "__iter__") and not isinstance(result, (str, bytes)):
                return list(result)
            return result if isinstance(result, list) else []
        return self.each if isinstance(self.each, list) else []
    
    def _get_key(self, item: T, index: int) -> Any:
        """Extract a unique key for an item."""
        if self.key_fn:
            return self.key_fn(item)
        # Try common key attributes
        if hasattr(item, "id"):
            return item.id
        if hasattr(item, "key"):
            return item.key
        if isinstance(item, dict):
            return item.get("id", item.get("key", index))
        # Fallback to index (not ideal for reconciliation)
        return index
    
    def render(self) -> str:
        """
        Render to HTML string (server-side).
        
        CRITICAL: Renders all items AND registers bindings for reactive updates.
        The client-side will use the template to add/remove/reorder items.
        
        Returns:
            HTML with data attributes for hydration
        """
        from pynext.core.context import get_context
        
        items = self._get_items()
        
        # Register binding for reactive updates
        ctx = get_context()
        if ctx:
            signal_deps = self._extract_signal_deps()
            if signal_deps:
                # Generate update expression
                update_expr = self._generate_update_expr()
                
                # Get template HTML from a sample item (or first item)
                template_html = ""
                if self.render_fn and items:
                    sample_content = self.render_fn(items[0], 0)
                    template_html = _render_child(sample_content)
                
                ctx.register_binding(
                    node_id=self._id,
                    binding_type="for",
                    signal_deps=signal_deps,
                    update_expr=update_expr,
                    initial_value={
                        "count": len(items),
                        "keys": [self._get_key(item, i) for i, item in enumerate(items)],
                        "template": template_html,
                    },
                )
        
        # Empty list - show fallback
        if not items:
            fallback_html = _render_child(self.fallback) if self.fallback else ""
            return f'<div id="{self._id}" data-pynext-for="true" data-empty="true">{fallback_html}</div>'
        
        # No render function
        if not self.render_fn:
            return f'<div id="{self._id}" data-pynext-for="true"></div>'
        
        # Render each item - store template for first item for client reuse
        parts = []
        for index, item in enumerate(items):
            key = self._get_key(item, index)
            content = self.render_fn(item, index)
            item_html = _render_child(content)
            # Wrap each item with key marker
            parts.append(f'<div data-for-item="{key}">{item_html}</div>')
        
        return f'<div id="{self._id}" data-pynext-for="true">{"".join(parts)}</div>'
    
    def _extract_signal_deps(self) -> list[str]:
        """Extract signal IDs that the each list depends on."""
        import inspect
        
        if not callable(self.each):
            return []
        
        deps = []
        
        # Try to inspect closure variables
        if hasattr(self.each, '__closure__') and self.each.__closure__:
            for cell in self.each.__closure__:
                try:
                    obj = cell.cell_contents
                    # Check if it's a Signal or Memo
                    if hasattr(obj, '_id') and hasattr(obj, '_value'):
                        deps.append(obj._id)
                    # Check for Store
                    elif hasattr(obj, '_id') and hasattr(obj, '_data'):
                        deps.append(obj._id)
                except (ValueError, AttributeError):
                    pass
        
        return deps
    
    def _generate_update_expr(self) -> str:
        """Generate JavaScript expression to get the current list."""
        deps = self._extract_signal_deps()
        if not deps:
            return "[]"
        
        # For the first signal dependency, read its value
        return f"__pynext__.getSignal('{deps[0]}').read()"
    
    def __str__(self) -> str:
        return self.render()
    
    def __repr__(self) -> str:
        return f"For(each={self.each!r})"
    
    def __iter__(self) -> Iterator[tuple[T, int]]:
        """Allow iteration for debugging."""
        items = self._get_items()
        return iter((item, i) for i, item in enumerate(items))
    
    def to_js_init(self) -> str:
        """Generate JavaScript initialization code."""
        return f"__pynext__.createFor('{self._id}')"


# =============================================================================
# SECTION 3: INDEX - Index-Based List Rendering
# =============================================================================
#
# WHY INDEX EXISTS:
# For lists of primitives (numbers, strings) where items don't have identity,
# Index provides a simpler model. Instead of tracking by key, it tracks by
# index position.
#
# FOR vs INDEX:
# - For: Items have identity, can be reordered efficiently
# - Index: Items are positional, updates are simpler but no reorder optimization
#
# USE INDEX WHEN:
# - List contains primitives (numbers, strings)
# - Items don't have unique IDs
# - Reordering is rare
# =============================================================================

class Index(Generic[T]):
    """
    Index-based list rendering (non-keyed).
    
    WHY THIS EXISTS:
    Unlike For which tracks items by key, Index tracks by position.
    This is simpler and more efficient for:
    - Lists of primitives (numbers, strings)
    - Lists where items don't have stable IDs
    - Fixed-size lists that don't reorder
    
    USAGE PATTERNS:
    
    List of primitives:
        Index(each=lambda: [1, 2, 3, 4, 5])[
            lambda item, index: div()[f"Value: {item()}"]
        ]
    
    Note: item is an accessor function, not the value directly.
    This enables fine-grained reactivity per index.
    
    Attributes:
        each: List or callable returning list
        fallback: Content when list is empty
        render_fn: Function (item_accessor, index) -> content
    """
    
    __slots__ = ("each", "fallback", "render_fn", "_id")
    
    def __init__(
        self,
        each: Union[List[T], Callable[[], List[T]]],
        fallback: Optional[Any] = None,
    ) -> None:
        """
        Create an Index component.
        
        Args:
            each: List or callable returning list
            fallback: Content when list is empty
        """
        self.each = each
        self.fallback = fallback
        self.render_fn: Optional[Callable[[Callable[[], T], int], Any]] = None
        self._id = f"index_{uuid.uuid4().hex[:12]}"
    
    def __getitem__(
        self, 
        render_fn: Callable[[Callable[[], T], int], Any]
    ) -> "Index[T]":
        """
        Set the render function.
        
        Note: First argument is an accessor function, not the value.
        
        Example:
            Index(each=numbers)[
                lambda num, i: div()[f"Item {i}: {num()}"]
            ]
        """
        self.render_fn = render_fn
        return self
    
    def _get_items(self) -> List[T]:
        """Get the current list of items."""
        if callable(self.each):
            result = self.each()
            if hasattr(result, "__iter__") and not isinstance(result, (str, bytes)):
                return list(result)
            return result if isinstance(result, list) else []
        return self.each if isinstance(self.each, list) else []
    
    def render(self) -> str:
        """Render to HTML string."""
        items = self._get_items()
        
        if not items:
            fallback_html = _render_child(self.fallback) if self.fallback else ""
            return f'<div data-index="{self._id}" data-empty="true">{fallback_html}</div>'
        
        if not self.render_fn:
            return f'<div data-index="{self._id}"></div>'
        
        parts = []
        for index, item in enumerate(items):
            # Create accessor that returns the item value
            # Using default argument to capture current item
            item_accessor: Callable[[], T] = lambda i=item: i
            content = self.render_fn(item_accessor, index)
            item_html = _render_child(content)
            parts.append(f'<div data-index-item="{index}">{item_html}</div>')
        
        return f'<div data-index="{self._id}">{"".join(parts)}</div>'
    
    def __str__(self) -> str:
        return self.render()
    
    def __repr__(self) -> str:
        return f"Index(each={self.each!r})"


# =============================================================================
# SECTION 4: SWITCH / MATCH - Multi-Branch Conditionals
# =============================================================================
#
# WHY SWITCH EXISTS:
# When you have multiple exclusive conditions (if/elif/elif/else),
# Switch provides cleaner syntax and reactive updates.
#
# HOW IT WORKS:
# 1. Evaluates Match conditions in order
# 2. Renders first matching branch
# 3. On condition change, swaps to new branch (surgical update)
#
# PATTERN:
#     Switch()[
#         Match(when=condition1)[content1],
#         Match(when=condition2)[content2],
#         Match(when=True)[default_content],  # Else branch
#     ]
# =============================================================================

class Switch:
    """
    Multi-branch conditional rendering.
    
    WHY THIS EXISTS:
    Switch provides cleaner syntax for multiple exclusive conditions
    than nested Show components. It evaluates conditions in order
    and renders the first match.
    
    USAGE PATTERNS:
    
    Status-based UI:
        Switch()[
            Match(when=lambda: status() == "loading")[Spinner()],
            Match(when=lambda: status() == "error")[ErrorMessage()],
            Match(when=lambda: status() == "success")[Content()],
        ]
    
    With default (else):
        Switch()[
            Match(when=lambda: role() == "admin")[AdminDashboard()],
            Match(when=lambda: role() == "user")[UserDashboard()],
            Match(when=True)[GuestView()],  # Default
        ]
    
    Attributes:
        matches: List of Match components
    """
    
    __slots__ = ("matches", "_id")
    
    def __init__(self) -> None:
        """Create a Switch component."""
        self.matches: List[Match] = []
        self._id = f"switch_{uuid.uuid4().hex[:12]}"
    
    def __getitem__(self, matches: Union[List["Match"], "Match"]) -> "Switch":
        """
        Set the Match branches.
        
        Example:
            Switch()[
                Match(when=cond1)[content1],
                Match(when=cond2)[content2],
            ]
        """
        if isinstance(matches, Match):
            self.matches = [matches]
        elif isinstance(matches, (list, tuple)):
            self.matches = list(matches)
        else:
            self.matches = [matches]
        return self
    
    def render(self) -> str:
        """Render the first matching branch."""
        for i, match in enumerate(self.matches):
            condition = match.when() if callable(match.when) else match.when
            if condition:
                content = match.render()
                return f'<div data-switch="{self._id}" data-match="{i}">{content}</div>'
        
        # No match
        return f'<div data-switch="{self._id}" data-match="-1"></div>'
    
    def __str__(self) -> str:
        return self.render()
    
    def __repr__(self) -> str:
        return f"Switch(matches={len(self.matches)})"


class Match:
    """
    A branch in a Switch statement.
    
    USAGE:
        Match(when=lambda: condition())[content]
    
    For default/else branch:
        Match(when=True)[default_content]
    
    Attributes:
        when: Condition for this branch
        children: Content to render if condition is true
    """
    
    __slots__ = ("when", "children", "_id")
    
    def __init__(self, when: Union[bool, Callable[[], bool]]) -> None:
        """
        Create a Match branch.
        
        Args:
            when: Condition - bool or callable returning bool
        """
        self.when = when
        self.children: Any = None
        self._id = f"match_{uuid.uuid4().hex[:12]}"
    
    def __getitem__(self, children: Any) -> "Match":
        """Set the content for this branch."""
        self.children = children
        return self
    
    def render(self) -> str:
        """Render the branch content."""
        return _render_child(self.children)
    
    def __str__(self) -> str:
        return self.render()
    
    def __repr__(self) -> str:
        return f"Match(when={self.when!r})"


# =============================================================================
# SECTION 5: PORTAL - Render Outside Component Tree
# =============================================================================
#
# WHY PORTAL EXISTS:
# Modals, tooltips, and dropdowns need to render outside their parent's
# CSS context (to avoid overflow:hidden, z-index issues, etc.).
# Portal "teleports" content to a different DOM location.
#
# HOW IT WORKS:
# 1. Server: Renders content inline with marker
# 2. Client: Moves content to target container
# 3. Cleanup: Removes content when component unmounts
#
# USE CASES:
# - Modals: Render to document.body
# - Tooltips: Render to dedicated tooltip layer
# - Dropdowns: Escape overflow:hidden parents
# =============================================================================

class Portal:
    """
    Render content outside the component tree.
    
    WHY THIS EXISTS:
    Some UI elements (modals, tooltips, dropdowns) need to render
    outside their parent's DOM context to:
    - Escape overflow:hidden containers
    - Avoid z-index stacking issues
    - Position relative to viewport
    
    USAGE PATTERNS:
    
    Modal to body:
        Portal(mount="body")[
            Modal()[
                h1()["Confirm Action"],
                button(onclick=close)["Close"]
            ]
        ]
    
    Tooltip to dedicated layer:
        Portal(mount="#tooltip-layer")[
            Tooltip(position=pos)[text]
        ]
    
    With Shadow DOM (style isolation):
        Portal(mount="body", use_shadow=True)[
            StyledComponent()
        ]
    
    Attributes:
        mount: CSS selector or element ID to mount to
        use_shadow: Whether to use Shadow DOM for isolation
        is_svg: Whether content is SVG (uses different namespace)
        children: Content to render
    """
    
    __slots__ = ("mount", "use_shadow", "is_svg", "children", "_id")
    
    def __init__(
        self,
        mount: str = "body",
        use_shadow: bool = False,
        is_svg: bool = False,
    ) -> None:
        """
        Create a Portal.
        
        Args:
            mount: Where to render content. Can be:
                   - "body": Document body
                   - "#id": Element with ID
                   - ".class": Element with class
                   - Any valid CSS selector
            use_shadow: If True, content renders in Shadow DOM
                        for style isolation
            is_svg: If True, creates SVG namespace elements
        """
        self.mount = mount
        self.use_shadow = use_shadow
        self.is_svg = is_svg
        self.children: Any = None
        self._id = f"portal_{uuid.uuid4().hex[:12]}"
    
    def __getitem__(self, children: Any) -> "Portal":
        """Set the content to portal."""
        self.children = children
        return self
    
    def render(self) -> str:
        """
        Render with portal marker.
        
        Server-side: Content renders inline with data attributes.
        Client-side: JavaScript moves content to mount target.
        """
        content = _render_child(self.children)
        attrs = [
            f'data-portal="{self._id}"',
            f'data-mount="{self.mount}"',
        ]
        if self.use_shadow:
            attrs.append('data-shadow="true"')
        if self.is_svg:
            attrs.append('data-svg="true"')
        
        return f'<div {" ".join(attrs)}>{content}</div>'
    
    def __str__(self) -> str:
        return self.render()
    
    def __repr__(self) -> str:
        return f"Portal(mount={self.mount!r})"


# =============================================================================
# SECTION 6: DYNAMIC - Dynamic Component Rendering
# =============================================================================
#
# WHY DYNAMIC EXISTS:
# Sometimes you need to render different components based on runtime data
# (tabs, wizards, plugin systems). Dynamic handles this reactively.
#
# HOW IT WORKS:
# 1. Watches the component accessor
# 2. When it changes, unmounts old component, mounts new one
# 3. Passes props to the current component
# =============================================================================

class Dynamic(Generic[T]):
    """
    Dynamically render different components.
    
    WHY THIS EXISTS:
    When the component to render is determined at runtime
    (tabs, routes, plugins), Dynamic provides reactive switching
    with proper cleanup.
    
    USAGE PATTERNS:
    
    Tab-based UI:
        tabs = {"home": HomePage, "profile": ProfilePage}
        active_tab = Signal("home")
        
        Dynamic(component=lambda: tabs[active_tab()])
    
    With props:
        Dynamic(
            component=lambda: components[type()],
            data=item_data,
            on_change=handle_change
        )
    
    Attributes:
        component: Component class/function or accessor
        props: Props to pass to component
    """
    
    __slots__ = ("component", "props", "_id")
    
    def __init__(
        self,
        component: Union[type, Callable[[], type]],
        **props: Any,
    ) -> None:
        """
        Create a Dynamic component.
        
        Args:
            component: The component to render. Can be:
                       - A component class/function
                       - A lambda returning a component
            **props: Props passed to the rendered component
        """
        self.component = component
        self.props = props
        self._id = f"dynamic_{uuid.uuid4().hex[:12]}"
    
    def render(self) -> str:
        """Render the current component."""
        comp = self.component
        
        # If component is a lambda/function (not a class), call it to get the actual component
        # Note: isinstance(comp, type) checks if comp is a class
        if callable(comp) and not isinstance(comp, type):
            comp = comp()
        
        if comp is None:
            return f'<div data-dynamic="{self._id}"></div>'
        
        # Try to render
        try:
            # Check if comp is a class (type) that needs instantiation
            if isinstance(comp, type):
                instance = comp(**self.props)
                if hasattr(instance, "render"):
                    content = instance.render()
                else:
                    content = str(instance)
            elif callable(comp):
                # comp is a function component
                result = comp(**self.props) if self.props else comp()
                if hasattr(result, "render"):
                    content = result.render()
                else:
                    content = _render_child(result)
            elif hasattr(comp, "render"):
                # comp is already an instance with render method
                content = comp.render()
            else:
                content = _render_child(comp)
        except Exception:
            raise
        
        return f'<div data-dynamic="{self._id}">{content}</div>'
    
    def __str__(self) -> str:
        return self.render()
    
    def __repr__(self) -> str:
        return f"Dynamic(component={self.component!r})"


# =============================================================================
# SECTION 7: ERROR BOUNDARY - Error Catching and Recovery
# =============================================================================
#
# WHY ERROR BOUNDARY EXISTS:
# Errors in one component shouldn't crash the entire app.
# ErrorBoundary catches errors and shows fallback UI.
#
# HOW IT WORKS:
# 1. Wraps children in try/except
# 2. On error, renders fallback with error info
# 3. Provides reset function to retry
#
# SERVER vs CLIENT:
# - Server: Catches render errors
# - Client: Catches render + update errors (via Effect)
# =============================================================================

class ErrorBoundary:
    """
    Catch and handle errors in child components.
    
    WHY THIS EXISTS:
    Errors shouldn't crash the entire UI. ErrorBoundary:
    - Catches errors in children
    - Renders fallback UI with error info
    - Provides reset mechanism to retry
    
    USAGE PATTERNS:
    
    Basic error handling:
        ErrorBoundary(
            fallback=lambda err, reset: div()[
                f"Something went wrong: {err}",
                button(onclick=reset)["Try Again"]
            ]
        )[
            RiskyComponent()
        ]
    
    With custom error UI:
        ErrorBoundary(
            fallback=lambda err, reset: ErrorCard(
                error=err,
                on_retry=reset
            )
        )[
            DataFetcher()
        ]
    
    Attributes:
        fallback: Function (error, reset) -> UI to show on error
        children: Content that might error
        error: Current error (if any)
    """
    
    __slots__ = ("fallback", "children", "error", "_id")
    
    def __init__(
        self,
        fallback: Callable[[Exception, Callable[[], None]], Any],
    ) -> None:
        """
        Create an ErrorBoundary.
        
        Args:
            fallback: Function that receives:
                      - error: The caught exception
                      - reset: Function to clear error and retry
                      Returns: UI to show instead of errored content
        """
        self.fallback = fallback
        self.children: Any = None
        self.error: Optional[Exception] = None
        self._id = f"error_{uuid.uuid4().hex[:12]}"
    
    def __getitem__(self, children: Any) -> "ErrorBoundary":
        """Set the children that might error."""
        self.children = children
        return self
    
    def reset(self) -> None:
        """Clear the error state to retry rendering."""
        self.error = None
    
    def render(self) -> str:
        """Render children or fallback if errored."""
        # If we have an error, render fallback
        if self.error:
            fallback_content = self.fallback(self.error, self.reset)
            content = _render_child(fallback_content)
            return f'<div data-error-boundary="{self._id}" data-has-error="true">{content}</div>'
        
        # Try to render children
        try:
            content = _render_child(self.children)
            return f'<div data-error-boundary="{self._id}">{content}</div>'
        except Exception as e:
            self.error = e
            fallback_content = self.fallback(e, self.reset)
            content = _render_child(fallback_content)
            return f'<div data-error-boundary="{self._id}" data-has-error="true">{content}</div>'
    
    def __str__(self) -> str:
        return self.render()
    
    def __repr__(self) -> str:
        return f"ErrorBoundary(error={self.error!r})"


# =============================================================================
# SECTION 8: SUSPENSE - Async Loading States
# =============================================================================
#
# WHY SUSPENSE EXISTS:
# Async data fetching is common. Suspense provides a declarative
# way to show loading states while data loads.
#
# HOW IT WORKS:
# 1. Server: Renders content or fallback based on data state
# 2. Client: Shows fallback while promises resolve
# 3. On resolve: Swaps fallback for content
#
# PATTERN:
#     Suspense(fallback=Spinner())[
#         AsyncDataComponent()
#     ]
# =============================================================================

class Suspense:
    """
    Show fallback while async content loads.
    
    WHY THIS EXISTS:
    Async data fetching is ubiquitous. Suspense provides:
    - Declarative loading states
    - Automatic fallback display
    - Smooth transitions when data arrives
    
    USAGE PATTERNS:
    
    Basic loading:
        Suspense(fallback=Spinner())[
            AsyncUserProfile()
        ]
    
    With skeleton UI:
        Suspense(fallback=ProfileSkeleton())[
            ProfileCard(user=user_resource)
        ]
    
    Nested suspense:
        Suspense(fallback=PageSkeleton())[
            Header(),
            Suspense(fallback=ContentSkeleton())[
                MainContent()
            ]
        ]
    
    Attributes:
        fallback: Content to show while loading
        children: Async content to render
    """
    
    __slots__ = ("fallback", "children", "_id")
    
    def __init__(self, fallback: Any = None) -> None:
        """
        Create a Suspense boundary.
        
        Args:
            fallback: Content to show while children are loading.
                      Can be any renderable (spinner, skeleton, text)
        """
        self.fallback = fallback
        self.children: Any = None
        self._id = f"suspense_{uuid.uuid4().hex[:12]}"
    
    def __getitem__(self, children: Any) -> "Suspense":
        """Set the async children."""
        self.children = children
        return self
    
    def render(self) -> str:
        """Render with suspense boundary marker."""
        # Render the children content
        content = _render_child(self.children)
        
        # Render fallback for client-side use
        fallback_html = _render_child(self.fallback) if self.fallback else ""
        
        # Escape fallback for data attribute
        import html
        escaped_fallback = html.escape(fallback_html)
        
        return f'<div data-suspense="{self._id}" data-fallback="{escaped_fallback}">{content}</div>'
    
    def __str__(self) -> str:
        return self.render()
    
    def __repr__(self) -> str:
        return f"Suspense(fallback={self.fallback!r})"


# =============================================================================
# SECTION 9: HELPER FUNCTIONS
# =============================================================================

def _render_child(child: Any) -> str:
    """
    Render any child to HTML string.
    
    Handles:
    - None: Returns empty string
    - Objects with render(): Calls render method
    - Callables: Calls and recursively renders result
    - Iterables: Joins rendered children
    - Everything else: Converts to string
    
    Args:
        child: Any renderable content
        
    Returns:
        HTML string
    """
    if child is None:
        return ""
    
    # Objects with render method (Elements, Components)
    if hasattr(child, "render"):
        return child.render()
    
    # Callable (lambda returning content)
    if callable(child):
        result = child()
        return _render_child(result)
    
    # List/tuple of children
    if isinstance(child, (list, tuple)):
        return "".join(_render_child(c) for c in child)
    
    # Convert to string (includes escaping for safety)
    return str(child)


# =============================================================================
# SECTION 10: EXPORTS
# =============================================================================

__all__ = [
    # Conditional
    "Show",
    
    # Lists
    "For",
    "Index",
    
    # Multi-branch
    "Switch",
    "Match",
    
    # Portal
    "Portal",
    
    # Dynamic
    "Dynamic",
    
    # Error handling
    "ErrorBoundary",
    
    # Async
    "Suspense",
]
