"""
PyNext Client - DOM Node Types

=============================================================================
WHAT THIS FILE DOES
=============================================================================

Provides Python type stubs for DOM node types including Node, NodeList,
HTMLCollection, and DOMStringMap. These types enable IDE autocompletion
and type checking for DOM manipulation code.

=============================================================================
WHY THIS EXISTS
=============================================================================

DOM node types are the foundation of the DOM API. This module provides:
- Full type hints for IDE autocompletion
- Documentation for each type and method
- Zero runtime overhead (pure type stubs)

=============================================================================
HOW IT WORKS
=============================================================================

These are type stubs that:
1. Provide type information for static analysis (mypy, pyright)
2. Enable IDE autocompletion (VS Code, PyCharm)
3. Transpile to nothing - they're passthrough to browser globals

=============================================================================
WHO USES THIS
=============================================================================

- Web developers using PyNext for DOM manipulation
- The transpiler for type-aware passthrough detection
- IDEs for autocompletion and type checking

=============================================================================
EXAMPLES
=============================================================================

    from pynext.client import document
    from pynext.client.node import NodeList, HTMLCollection
    
    # Get all divs
    divs: NodeList = document.querySelectorAll("div")
    for div in divs:
        print(div.textContent)
    
    # Get by class
    items: HTMLCollection = document.getElementsByClassName("item")
    print(items.length)
"""

from __future__ import annotations
from typing import (
    Any,
    Callable,
    Iterator,
    List,
    Optional,
    Tuple,
    TYPE_CHECKING,
)

if TYPE_CHECKING:
    from pynext.client.dom import Element, Document


# =============================================================================
# Node Type Constants
# =============================================================================

ELEMENT_NODE = 1
ATTRIBUTE_NODE = 2
TEXT_NODE = 3
CDATA_SECTION_NODE = 4
PROCESSING_INSTRUCTION_NODE = 7
COMMENT_NODE = 8
DOCUMENT_NODE = 9
DOCUMENT_TYPE_NODE = 10
DOCUMENT_FRAGMENT_NODE = 11


# =============================================================================
# Node Base Class
# =============================================================================

class Node:
    """
    WHO: Web developers working with DOM nodes
    WHAT: Base class for all DOM nodes (Element, Text, Comment, Document, etc.)
    WHEN: Use when you need generic node manipulation
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Provides the foundation for all DOM operations
    HOW: Passthrough to JavaScript - same API, zero runtime cost
    
    Node Types:
        - ELEMENT_NODE (1): Element nodes like <div>, <span>
        - TEXT_NODE (3): Text content within elements
        - COMMENT_NODE (8): HTML comments
        - DOCUMENT_NODE (9): The document itself
        - DOCUMENT_FRAGMENT_NODE (11): Document fragments
    
    Example:
        node = document.getElementById("app")
        print(node.nodeType)  # 1 (ELEMENT_NODE)
        print(node.nodeName)  # "DIV"
    """
    
    # Node type constants (read-only)
    ELEMENT_NODE: int = 1
    ATTRIBUTE_NODE: int = 2
    TEXT_NODE: int = 3
    CDATA_SECTION_NODE: int = 4
    PROCESSING_INSTRUCTION_NODE: int = 7
    COMMENT_NODE: int = 8
    DOCUMENT_NODE: int = 9
    DOCUMENT_TYPE_NODE: int = 10
    DOCUMENT_FRAGMENT_NODE: int = 11
    
    # Properties
    @property
    def nodeType(self) -> int:
        """
        Returns the node type as an integer constant.
        
        Common values:
            - 1: ELEMENT_NODE
            - 3: TEXT_NODE
            - 8: COMMENT_NODE
            - 9: DOCUMENT_NODE
            - 11: DOCUMENT_FRAGMENT_NODE
        """
        ...
    
    @property
    def nodeName(self) -> str:
        """
        Returns the node name.
        
        For elements: uppercase tag name (e.g., "DIV", "SPAN")
        For text nodes: "#text"
        For comments: "#comment"
        For documents: "#document"
        """
        ...
    
    @property
    def nodeValue(self) -> Optional[str]:
        """
        Returns the node value.
        
        For text/comment nodes: the text content
        For elements/documents: None
        """
        ...
    
    @nodeValue.setter
    def nodeValue(self, value: Optional[str]) -> None:
        """Set the node value (for text/comment nodes)."""
        ...
    
    @property
    def textContent(self) -> Optional[str]:
        """
        Returns the text content of the node and its descendants.
        
        For elements: concatenated text of all text node descendants
        For text/comment nodes: the text content
        For documents: None
        """
        ...
    
    @textContent.setter
    def textContent(self, value: Optional[str]) -> None:
        """
        Set the text content, replacing all children.
        
        This removes all child nodes and replaces them with a single text node.
        """
        ...
    
    @property
    def parentNode(self) -> Optional["Node"]:
        """Returns the parent node, or None if this is the root."""
        ...
    
    @property
    def parentElement(self) -> Optional["Element"]:
        """Returns the parent element, or None if parent is not an element."""
        ...
    
    @property
    def childNodes(self) -> "NodeList":
        """Returns a NodeList of all child nodes (including text nodes)."""
        ...
    
    @property
    def firstChild(self) -> Optional["Node"]:
        """Returns the first child node, or None if no children."""
        ...
    
    @property
    def lastChild(self) -> Optional["Node"]:
        """Returns the last child node, or None if no children."""
        ...
    
    @property
    def nextSibling(self) -> Optional["Node"]:
        """Returns the next sibling node, or None if this is the last child."""
        ...
    
    @property
    def previousSibling(self) -> Optional["Node"]:
        """Returns the previous sibling node, or None if this is the first child."""
        ...
    
    @property
    def ownerDocument(self) -> Optional["Document"]:
        """Returns the document this node belongs to."""
        ...
    
    @property
    def isConnected(self) -> bool:
        """Returns True if the node is connected to the document tree."""
        ...
    
    # Methods
    def appendChild(self, child: "Node") -> "Node":
        """
        Append a child node to this node.
        
        Args:
            child: The node to append
        
        Returns:
            The appended child node
        
        Example:
            parent.appendChild(newChild)
        """
        ...
    
    def insertBefore(self, newChild: "Node", refChild: Optional["Node"]) -> "Node":
        """
        Insert a node before a reference child.
        
        Args:
            newChild: The node to insert
            refChild: The reference child (insert before this), or None to append
        
        Returns:
            The inserted node
        
        Example:
            parent.insertBefore(newNode, existingChild)
        """
        ...
    
    def removeChild(self, child: "Node") -> "Node":
        """
        Remove a child node.
        
        Args:
            child: The node to remove
        
        Returns:
            The removed node
        
        Example:
            removed = parent.removeChild(child)
        """
        ...
    
    def replaceChild(self, newChild: "Node", oldChild: "Node") -> "Node":
        """
        Replace a child node with a new node.
        
        Args:
            newChild: The new node
            oldChild: The node to replace
        
        Returns:
            The replaced (old) node
        
        Example:
            old = parent.replaceChild(newNode, oldNode)
        """
        ...
    
    def cloneNode(self, deep: bool = False) -> "Node":
        """
        Clone this node.
        
        Args:
            deep: If True, clone all descendants. If False, clone only this node.
        
        Returns:
            The cloned node
        
        Example:
            clone = node.cloneNode(deep=True)
        """
        ...
    
    def contains(self, other: Optional["Node"]) -> bool:
        """
        Check if this node contains another node.
        
        Args:
            other: The node to check
        
        Returns:
            True if other is a descendant of this node
        
        Example:
            if parent.contains(child):
                print("child is a descendant")
        """
        ...
    
    def hasChildNodes(self) -> bool:
        """
        Check if this node has any child nodes.
        
        Returns:
            True if this node has at least one child
        """
        ...
    
    def normalize(self) -> None:
        """
        Merge adjacent text nodes and remove empty text nodes.
        
        This is useful after DOM manipulations that might leave
        fragmented text nodes.
        """
        ...
    
    def getRootNode(self) -> "Node":
        """
        Get the root node of this node's tree.
        
        Returns:
            The root node (usually the Document)
        """
        ...
    
    def isSameNode(self, other: Optional["Node"]) -> bool:
        """
        Check if two node references point to the same node.
        
        Args:
            other: The node to compare
        
        Returns:
            True if both references point to the same node
        """
        ...
    
    def isEqualNode(self, other: Optional["Node"]) -> bool:
        """
        Check if two nodes are equal (same type, attributes, and children).
        
        Args:
            other: The node to compare
        
        Returns:
            True if nodes are structurally equal
        """
        ...
    
    def compareDocumentPosition(self, other: "Node") -> int:
        """
        Compare the document position of two nodes.
        
        Args:
            other: The node to compare
        
        Returns:
            A bitmask indicating the relative position
        """
        ...


# =============================================================================
# Text Node
# =============================================================================

class Text(Node):
    """
    WHO: Web developers working with text content
    WHAT: Represents text content within an element
    WHEN: Use for fine-grained text manipulation
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Provides direct access to text nodes for manipulation
    HOW: Passthrough to JavaScript - same API, zero runtime cost
    
    Example:
        text = document.createTextNode("Hello, World!")
        element.appendChild(text)
    """
    
    @property
    def data(self) -> str:
        """The text content of this text node."""
        ...
    
    @data.setter
    def data(self, value: str) -> None:
        """Set the text content."""
        ...
    
    @property
    def length(self) -> int:
        """The length of the text content."""
        ...
    
    @property
    def wholeText(self) -> str:
        """The concatenated text of all adjacent text nodes."""
        ...
    
    def splitText(self, offset: int) -> "Text":
        """
        Split this text node at the given offset.
        
        Args:
            offset: The character position to split at
        
        Returns:
            A new text node containing the text after the offset
        """
        ...


# =============================================================================
# Comment Node
# =============================================================================

class Comment(Node):
    """
    WHO: Web developers working with HTML comments
    WHAT: Represents an HTML comment node
    WHEN: Use when you need to create or manipulate comments
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Comments can be used for markers or conditional processing
    HOW: Passthrough to JavaScript - same API, zero runtime cost
    
    Example:
        comment = document.createComment("TODO: Add feature")
        element.appendChild(comment)
    """
    
    @property
    def data(self) -> str:
        """The comment text (without <!-- and -->)."""
        ...
    
    @data.setter
    def data(self, value: str) -> None:
        """Set the comment text."""
        ...


# =============================================================================
# Document Fragment
# =============================================================================

class DocumentFragment(Node):
    """
    WHO: Web developers doing batch DOM operations
    WHAT: A minimal document object for holding document fragments
    WHEN: Use for efficient batch DOM manipulations
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Reduces reflows by allowing off-document DOM operations
    HOW: Passthrough to JavaScript - same API, zero runtime cost
    
    Example:
        fragment = document.createDocumentFragment()
        for item in items:
            li = document.createElement("li")
            li.textContent = item
            fragment.appendChild(li)
        ul.appendChild(fragment)  # Single reflow
    """
    
    @property
    def childElementCount(self) -> int:
        """Number of child elements."""
        ...
    
    @property
    def children(self) -> "HTMLCollection":
        """Child elements (HTMLCollection)."""
        ...
    
    @property
    def firstElementChild(self) -> Optional["Element"]:
        """First child element."""
        ...
    
    @property
    def lastElementChild(self) -> Optional["Element"]:
        """Last child element."""
        ...
    
    def querySelector(self, selector: str) -> Optional["Element"]:
        """Find first matching element."""
        ...
    
    def querySelectorAll(self, selector: str) -> "NodeList":
        """Find all matching elements."""
        ...
    
    def getElementById(self, id: str) -> Optional["Element"]:
        """Find element by ID."""
        ...
    
    def append(self, *nodes: Any) -> None:
        """Append multiple nodes or strings."""
        ...
    
    def prepend(self, *nodes: Any) -> None:
        """Prepend multiple nodes or strings."""
        ...
    
    def replaceChildren(self, *nodes: Any) -> None:
        """Replace all children."""
        ...


# =============================================================================
# NodeList
# =============================================================================

class NodeList:
    """
    WHO: Web developers iterating over DOM nodes
    WHAT: A collection of nodes returned by querySelectorAll and childNodes
    WHEN: Use when you have multiple nodes to process
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Provides array-like access to node collections
    HOW: Passthrough to JavaScript - same API, zero runtime cost
    
    Note: NodeList can be "live" (updates automatically) or "static"
    (snapshot at creation time). querySelectorAll returns static,
    childNodes returns live.
    
    Example:
        nodes = document.querySelectorAll(".item")
        for node in nodes:
            node.classList.add("processed")
        
        print(f"Found {nodes.length} items")
    """
    
    @property
    def length(self) -> int:
        """The number of nodes in the list."""
        ...
    
    def item(self, index: int) -> Optional[Node]:
        """
        Get the node at the given index.
        
        Args:
            index: Zero-based index
        
        Returns:
            The node at the index, or None if out of bounds
        """
        ...
    
    def forEach(
        self,
        callback: Callable[[Node, int, "NodeList"], None],
        thisArg: Any = None
    ) -> None:
        """
        Execute a callback for each node.
        
        Args:
            callback: Function(node, index, list) to call
            thisArg: Value to use as 'this' (JS context)
        """
        ...
    
    def entries(self) -> Iterator[Tuple[int, Node]]:
        """Return an iterator of [index, node] pairs."""
        ...
    
    def keys(self) -> Iterator[int]:
        """Return an iterator of indices."""
        ...
    
    def values(self) -> Iterator[Node]:
        """Return an iterator of nodes."""
        ...
    
    def __iter__(self) -> Iterator[Node]:
        """Iterate over nodes."""
        ...
    
    def __len__(self) -> int:
        """Return the number of nodes."""
        ...
    
    def __getitem__(self, index: int) -> Optional[Node]:
        """Get node by index (supports negative indexing in Python)."""
        ...


# =============================================================================
# HTMLCollection
# =============================================================================

class HTMLCollection:
    """
    WHO: Web developers working with element collections
    WHAT: A live collection of elements returned by getElementsBy* methods
    WHEN: Use when you need a live-updating element collection
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Provides live access to matching elements
    HOW: Passthrough to JavaScript - same API, zero runtime cost
    
    Note: HTMLCollection is always "live" - it updates automatically
    when the DOM changes. This is different from NodeList which may
    be static.
    
    Example:
        items = document.getElementsByClassName("item")
        print(f"Found {items.length} items")
        
        # Access by index
        first = items.item(0)
        
        # Access by name/id
        special = items.namedItem("special-item")
    """
    
    @property
    def length(self) -> int:
        """The number of elements in the collection."""
        ...
    
    def item(self, index: int) -> Optional["Element"]:
        """
        Get the element at the given index.
        
        Args:
            index: Zero-based index
        
        Returns:
            The element at the index, or None if out of bounds
        """
        ...
    
    def namedItem(self, name: str) -> Optional["Element"]:
        """
        Get the element with the given name or id.
        
        Args:
            name: The name or id attribute value
        
        Returns:
            The matching element, or None if not found
        """
        ...
    
    def __iter__(self) -> Iterator["Element"]:
        """Iterate over elements."""
        ...
    
    def __len__(self) -> int:
        """Return the number of elements."""
        ...
    
    def __getitem__(self, index: int) -> Optional["Element"]:
        """Get element by index."""
        ...


# =============================================================================
# DOMStringMap (for dataset)
# =============================================================================

class DOMStringMap:
    """
    WHO: Web developers working with data-* attributes
    WHAT: A map-like interface for data-* attributes on elements
    WHEN: Use element.dataset to access data attributes
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Provides convenient access to custom data attributes
    HOW: Passthrough to JavaScript - same API, zero runtime cost
    
    Data attribute names are automatically converted:
        - data-user-id → dataset.userId
        - data-item-name → dataset.itemName
    
    Example:
        # HTML: <div data-user-id="123" data-user-name="Alice">
        el = document.getElementById("user")
        print(el.dataset.userId)     # "123"
        print(el.dataset.userName)   # "Alice"
        
        # Set a data attribute
        el.dataset.role = "admin"    # Sets data-role="admin"
        
        # Delete a data attribute
        del el.dataset.userId        # Removes data-user-id
    """
    
    def __getattr__(self, name: str) -> str:
        """Get a data attribute value by camelCase name."""
        ...
    
    def __setattr__(self, name: str, value: str) -> None:
        """Set a data attribute value by camelCase name."""
        ...
    
    def __delattr__(self, name: str) -> None:
        """Delete a data attribute by camelCase name."""
        ...
    
    def __contains__(self, name: str) -> bool:
        """Check if a data attribute exists."""
        ...


# =============================================================================
# DOMTokenList (for classList)
# =============================================================================

class DOMTokenList:
    """
    WHO: Web developers managing CSS classes
    WHAT: A set-like interface for managing CSS classes on elements
    WHEN: Use element.classList to add/remove/toggle classes
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Provides convenient class manipulation without string parsing
    HOW: Passthrough to JavaScript - same API, zero runtime cost
    
    Example:
        el = document.getElementById("button")
        
        # Add classes
        el.classList.add("active", "primary")
        
        # Remove classes
        el.classList.remove("disabled")
        
        # Toggle a class
        el.classList.toggle("visible")
        
        # Check if class exists
        if el.classList.contains("active"):
            print("Button is active")
        
        # Replace a class
        el.classList.replace("primary", "secondary")
    """
    
    @property
    def length(self) -> int:
        """The number of classes."""
        ...
    
    @property
    def value(self) -> str:
        """The class attribute value as a string."""
        ...
    
    @value.setter
    def value(self, value: str) -> None:
        """Set the class attribute value."""
        ...
    
    def item(self, index: int) -> Optional[str]:
        """
        Get the class at the given index.
        
        Args:
            index: Zero-based index
        
        Returns:
            The class name, or None if out of bounds
        """
        ...
    
    def contains(self, token: str) -> bool:
        """
        Check if a class exists.
        
        Args:
            token: The class name to check
        
        Returns:
            True if the class exists
        """
        ...
    
    def add(self, *tokens: str) -> None:
        """
        Add one or more classes.
        
        Args:
            *tokens: Class names to add
        
        Example:
            el.classList.add("foo", "bar", "baz")
        """
        ...
    
    def remove(self, *tokens: str) -> None:
        """
        Remove one or more classes.
        
        Args:
            *tokens: Class names to remove
        
        Example:
            el.classList.remove("foo", "bar")
        """
        ...
    
    def toggle(self, token: str, force: Optional[bool] = None) -> bool:
        """
        Toggle a class on or off.
        
        Args:
            token: The class name to toggle
            force: If provided, force add (True) or remove (False)
        
        Returns:
            True if the class is now present, False if removed
        
        Example:
            # Toggle visibility
            el.classList.toggle("visible")
            
            # Force add
            el.classList.toggle("active", True)
            
            # Force remove
            el.classList.toggle("disabled", False)
        """
        ...
    
    def replace(self, oldToken: str, newToken: str) -> bool:
        """
        Replace a class with another.
        
        Args:
            oldToken: The class to replace
            newToken: The replacement class
        
        Returns:
            True if the old class was found and replaced
        
        Example:
            el.classList.replace("old-style", "new-style")
        """
        ...
    
    def supports(self, token: str) -> bool:
        """
        Check if a token is supported (always True for classList).
        
        This method exists for DOMTokenList compatibility but
        always returns True for class lists.
        """
        ...
    
    def __iter__(self) -> Iterator[str]:
        """Iterate over class names."""
        ...
    
    def __len__(self) -> int:
        """Return the number of classes."""
        ...
    
    def __contains__(self, token: str) -> bool:
        """Check if a class exists."""
        ...


# =============================================================================
# NamedNodeMap (for attributes)
# =============================================================================

class NamedNodeMap:
    """
    WHO: Web developers working with element attributes
    WHAT: A collection of attribute nodes
    WHEN: Use element.attributes to access all attributes
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Provides access to all attributes including non-standard ones
    HOW: Passthrough to JavaScript - same API, zero runtime cost
    
    Example:
        attrs = el.attributes
        for i in range(attrs.length):
            attr = attrs.item(i)
            print(f"{attr.name} = {attr.value}")
        
        # Get by name
        id_attr = attrs.getNamedItem("id")
        if id_attr:
            print(id_attr.value)
    """
    
    @property
    def length(self) -> int:
        """The number of attributes."""
        ...
    
    def item(self, index: int) -> Optional["Attr"]:
        """Get attribute at index."""
        ...
    
    def getNamedItem(self, name: str) -> Optional["Attr"]:
        """Get attribute by name."""
        ...
    
    def setNamedItem(self, attr: "Attr") -> Optional["Attr"]:
        """Set or replace an attribute."""
        ...
    
    def removeNamedItem(self, name: str) -> "Attr":
        """Remove an attribute by name."""
        ...
    
    def __iter__(self) -> Iterator["Attr"]:
        """Iterate over attributes."""
        ...
    
    def __len__(self) -> int:
        """Return the number of attributes."""
        ...


class Attr:
    """
    Represents a single attribute on an element.
    
    Example:
        attr = el.attributes.getNamedItem("class")
        print(attr.name)   # "class"
        print(attr.value)  # "foo bar"
    """
    
    @property
    def name(self) -> str:
        """The attribute name."""
        ...
    
    @property
    def value(self) -> str:
        """The attribute value."""
        ...
    
    @value.setter
    def value(self, value: str) -> None:
        """Set the attribute value."""
        ...
    
    @property
    def ownerElement(self) -> Optional["Element"]:
        """The element this attribute belongs to."""
        ...


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Node types
    "Node",
    "Text",
    "Comment",
    "DocumentFragment",
    
    # Collections
    "NodeList",
    "HTMLCollection",
    "DOMStringMap",
    "DOMTokenList",
    "NamedNodeMap",
    "Attr",
    
    # Node type constants
    "ELEMENT_NODE",
    "ATTRIBUTE_NODE",
    "TEXT_NODE",
    "CDATA_SECTION_NODE",
    "PROCESSING_INSTRUCTION_NODE",
    "COMMENT_NODE",
    "DOCUMENT_NODE",
    "DOCUMENT_TYPE_NODE",
    "DOCUMENT_FRAGMENT_NODE",
]

