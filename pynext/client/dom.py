"""
PyNext Client - DOM Document and Element APIs

=============================================================================
WHAT THIS FILE DOES
=============================================================================

Provides Python type stubs for DOM Document and Element interfaces. These
types enable IDE autocompletion, type checking, and documentation for DOM
manipulation code that transpiles to JavaScript.

=============================================================================
WHY THIS EXISTS
=============================================================================

DOM APIs are the foundation of web development. This module provides:
- Full type hints for all 90+ DOM APIs
- IDE autocompletion (VS Code, PyCharm, etc.)
- Documentation with who/what/when/where/why/how
- Zero runtime overhead - pure passthrough transpilation

=============================================================================
HOW IT WORKS
=============================================================================

These are type stubs that:
1. Define the Python API that mirrors JavaScript DOM APIs exactly
2. Provide type information for static analysis
3. Transpile to identical JavaScript (passthrough - no transformation)

The key insight: DOM APIs are identical in Python and JavaScript syntax.
`document.getElementById("app")` in Python becomes `document.getElementById("app")`
in JavaScript - no runtime helpers needed.

=============================================================================
WHO USES THIS
=============================================================================

- Web developers using PyNext for DOM manipulation
- The transpiler for passthrough detection
- IDEs for autocompletion and type checking
- LLMs for understanding and generating code

=============================================================================
EXAMPLES
=============================================================================

    from pynext.client import document, Element
    
    # Query elements
    app: Element = document.getElementById("app")
    buttons = document.querySelectorAll("button.primary")
    
    # Create elements
    div = document.createElement("div")
    div.id = "container"
    div.className = "wrapper"
    div.innerHTML = "<h1>Hello</h1>"
    
    # Manipulate DOM
    document.body.appendChild(div)
    
    # Work with classes
    div.classList.add("active", "visible")
    div.classList.toggle("hidden")
    
    # Work with data attributes
    div.dataset.userId = "123"
    print(div.dataset.userId)
"""

from __future__ import annotations
from typing import (
    Any,
    List,
    Optional,
    Union,
    overload,
    TYPE_CHECKING,
)

from pynext.client.node import (
    Node,
    NodeList,
    HTMLCollection,
    DOMStringMap,
    DOMTokenList,
    NamedNodeMap,
    Text,
    Comment,
    DocumentFragment,
)


# =============================================================================
# CSSStyleDeclaration (for element.style)
# =============================================================================

class CSSStyleDeclaration:
    """
    WHO: Web developers styling elements programmatically
    WHAT: Interface for inline CSS styles on an element
    WHEN: Use element.style to get/set inline styles
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Provides direct access to element styling
    HOW: Passthrough to JavaScript - same API, zero runtime cost
    
    Example:
        el = document.getElementById("box")
        el.style.display = "flex"
        el.style.backgroundColor = "blue"
        el.style.setProperty("--custom-color", "red")
        
        # Vendor prefixes
        el.style.webkitTransform = "rotate(45deg)"
        
        # CSS Custom Properties
        el.style.setProperty("--primary", "#3b82f6")
        value = el.style.getPropertyValue("--primary")
    """
    
    # =========================================================================
    # Display & Visibility (10)
    # =========================================================================
    display: str
    visibility: str
    opacity: str
    pointerEvents: str
    userSelect: str
    contentVisibility: str
    contain: str
    containIntrinsicSize: str
    isolation: str
    mixBlendMode: str
    
    # =========================================================================
    # Positioning (15)
    # =========================================================================
    position: str
    top: str
    right: str
    bottom: str
    left: str
    inset: str
    insetBlock: str
    insetBlockStart: str
    insetBlockEnd: str
    insetInline: str
    insetInlineStart: str
    insetInlineEnd: str
    zIndex: str
    float: str
    clear: str
    
    # =========================================================================
    # Box Model - Dimensions (15)
    # =========================================================================
    width: str
    height: str
    minWidth: str
    minHeight: str
    maxWidth: str
    maxHeight: str
    boxSizing: str
    aspectRatio: str
    inlineSize: str
    blockSize: str
    minInlineSize: str
    maxInlineSize: str
    minBlockSize: str
    maxBlockSize: str
    objectFit: str
    
    # =========================================================================
    # Box Model - Margin (10)
    # =========================================================================
    margin: str
    marginTop: str
    marginRight: str
    marginBottom: str
    marginLeft: str
    marginBlock: str
    marginBlockStart: str
    marginBlockEnd: str
    marginInline: str
    marginInlineStart: str
    
    # =========================================================================
    # Box Model - Padding (10)
    # =========================================================================
    padding: str
    paddingTop: str
    paddingRight: str
    paddingBottom: str
    paddingLeft: str
    paddingBlock: str
    paddingBlockStart: str
    paddingBlockEnd: str
    paddingInline: str
    paddingInlineStart: str
    
    # =========================================================================
    # Border (20)
    # =========================================================================
    border: str
    borderWidth: str
    borderStyle: str
    borderColor: str
    borderTop: str
    borderRight: str
    borderBottom: str
    borderLeft: str
    borderTopWidth: str
    borderTopStyle: str
    borderTopColor: str
    borderBottomWidth: str
    borderBottomStyle: str
    borderBottomColor: str
    borderRadius: str
    borderTopLeftRadius: str
    borderTopRightRadius: str
    borderBottomLeftRadius: str
    borderBottomRightRadius: str
    borderImage: str
    
    # =========================================================================
    # Outline (5)
    # =========================================================================
    outline: str
    outlineWidth: str
    outlineStyle: str
    outlineColor: str
    outlineOffset: str
    
    # =========================================================================
    # Background (15)
    # =========================================================================
    background: str
    backgroundColor: str
    backgroundImage: str
    backgroundPosition: str
    backgroundPositionX: str
    backgroundPositionY: str
    backgroundSize: str
    backgroundRepeat: str
    backgroundAttachment: str
    backgroundOrigin: str
    backgroundClip: str
    backgroundBlendMode: str
    backdropFilter: str
    WebkitBackdropFilter: str
    filter: str
    
    # =========================================================================
    # Color (5)
    # =========================================================================
    color: str
    caretColor: str
    accentColor: str
    colorScheme: str
    forcedColorAdjust: str
    
    # =========================================================================
    # Typography (25)
    # =========================================================================
    font: str
    fontFamily: str
    fontSize: str
    fontWeight: str
    fontStyle: str
    fontVariant: str
    fontStretch: str
    fontSizeAdjust: str
    fontKerning: str
    fontOpticalSizing: str
    fontFeatureSettings: str
    fontVariationSettings: str
    lineHeight: str
    letterSpacing: str
    wordSpacing: str
    textAlign: str
    textAlignLast: str
    textDecoration: str
    textDecorationLine: str
    textDecorationColor: str
    textDecorationStyle: str
    textTransform: str
    textIndent: str
    textShadow: str
    textOverflow: str
    
    # =========================================================================
    # Text Layout (10)
    # =========================================================================
    whiteSpace: str
    wordBreak: str
    wordWrap: str
    overflowWrap: str
    hyphens: str
    writingMode: str
    direction: str
    textOrientation: str
    unicodeBidi: str
    verticalAlign: str
    
    # =========================================================================
    # Flexbox (15)
    # =========================================================================
    flexDirection: str
    flexWrap: str
    flexFlow: str
    justifyContent: str
    alignItems: str
    alignContent: str
    alignSelf: str
    flex: str
    flexGrow: str
    flexShrink: str
    flexBasis: str
    order: str
    gap: str
    rowGap: str
    columnGap: str
    
    # =========================================================================
    # Grid (20)
    # =========================================================================
    gridTemplateColumns: str
    gridTemplateRows: str
    gridTemplateAreas: str
    gridTemplate: str
    gridAutoColumns: str
    gridAutoRows: str
    gridAutoFlow: str
    grid: str
    gridColumn: str
    gridColumnStart: str
    gridColumnEnd: str
    gridRow: str
    gridRowStart: str
    gridRowEnd: str
    gridArea: str
    justifyItems: str
    justifySelf: str
    placeContent: str
    placeItems: str
    placeSelf: str
    
    # =========================================================================
    # Overflow & Scroll (10)
    # =========================================================================
    overflow: str
    overflowX: str
    overflowY: str
    overflowAnchor: str
    scrollBehavior: str
    scrollSnapType: str
    scrollSnapAlign: str
    scrollPadding: str
    scrollMargin: str
    overscrollBehavior: str
    
    # =========================================================================
    # Transform (10)
    # =========================================================================
    transform: str
    transformOrigin: str
    transformStyle: str
    perspective: str
    perspectiveOrigin: str
    backfaceVisibility: str
    rotate: str
    scale: str
    translate: str
    transformBox: str
    
    # =========================================================================
    # Transition (5)
    # =========================================================================
    transition: str
    transitionProperty: str
    transitionDuration: str
    transitionTimingFunction: str
    transitionDelay: str
    
    # =========================================================================
    # Animation (10)
    # =========================================================================
    animation: str
    animationName: str
    animationDuration: str
    animationTimingFunction: str
    animationDelay: str
    animationIterationCount: str
    animationDirection: str
    animationFillMode: str
    animationPlayState: str
    willChange: str
    
    # =========================================================================
    # Cursor & Interaction (5)
    # =========================================================================
    cursor: str
    resize: str
    touchAction: str
    scrollbarWidth: str
    scrollbarColor: str
    
    # =========================================================================
    # List (5)
    # =========================================================================
    listStyle: str
    listStyleType: str
    listStylePosition: str
    listStyleImage: str
    counterReset: str
    
    # =========================================================================
    # Table (5)
    # =========================================================================
    tableLayout: str
    borderCollapse: str
    borderSpacing: str
    captionSide: str
    emptyCells: str
    
    # =========================================================================
    # Vendor Prefixes - WebKit (10)
    # =========================================================================
    webkitTransform: str
    webkitTransition: str
    webkitAnimation: str
    webkitBackdropFilter: str
    webkitTextFillColor: str
    webkitTextStroke: str
    webkitTextStrokeWidth: str
    webkitTextStrokeColor: str
    webkitBoxReflect: str
    webkitMaskImage: str
    
    # =========================================================================
    # Vendor Prefixes - Mozilla (5)
    # =========================================================================
    mozTransform: str
    mozTransition: str
    mozAnimation: str
    mozAppearance: str
    mozUserSelect: str
    
    # =========================================================================
    # Modern CSS - Container Queries (5)
    # =========================================================================
    container: str
    containerType: str
    containerName: str
    
    # =========================================================================
    # Modern CSS - Logical Properties (already above)
    # =========================================================================
    
    # =========================================================================
    # Special Properties
    # =========================================================================
    all: str
    appearance: str
    clip: str
    clipPath: str
    mask: str
    maskImage: str
    shapeOutside: str
    shapeMargin: str
    shapeImageThreshold: str
    objectPosition: str
    content: str
    quotes: str
    
    # =========================================================================
    # Methods
    # =========================================================================
    
    @property
    def cssText(self) -> str:
        """The full inline style string."""
        ...
    
    @cssText.setter
    def cssText(self, value: str) -> None:
        """Set the full inline style string."""
        ...
    
    @property
    def length(self) -> int:
        """Number of style properties set."""
        ...
    
    def getPropertyValue(self, property: str) -> str:
        """
        Get a CSS property value.
        
        Args:
            property: CSS property name (e.g., "background-color" or "--custom-var")
        
        Returns:
            The property value, or empty string if not set
        
        Example:
            width = el.style.getPropertyValue("width")
            color = el.style.getPropertyValue("--primary-color")
        """
        ...
    
    def setProperty(
        self,
        property: str,
        value: str,
        priority: str = ""
    ) -> None:
        """
        Set a CSS property.
        
        Args:
            property: CSS property name (e.g., "background-color" or "--custom-var")
            value: The value to set
            priority: "important" or "" (default)
        
        Example:
            el.style.setProperty("--theme-color", "blue")
            el.style.setProperty("display", "none", "important")
            el.style.setProperty("--spacing", "16px")
        """
        ...
    
    def removeProperty(self, property: str) -> str:
        """
        Remove a CSS property.
        
        Args:
            property: CSS property name
        
        Returns:
            The old value
        
        Example:
            old_value = el.style.removeProperty("background-color")
            el.style.removeProperty("--custom-var")
        """
        ...
    
    def getPropertyPriority(self, property: str) -> str:
        """
        Get the priority of a property.
        
        Returns:
            "important" or ""
        """
        ...
    
    def item(self, index: int) -> str:
        """
        Get property name at index.
        
        Example:
            for i in range(el.style.length):
                prop = el.style.item(i)  # "background-color", "display", etc.
        """
        ...
    
    def __getattr__(self, name: str) -> str:
        """Get a style property by camelCase name."""
        ...
    
    def __setattr__(self, name: str, value: str) -> None:
        """Set a style property by camelCase name."""
        ...


# =============================================================================
# Element Class
# =============================================================================

class Element(Node):
    """
    WHO: Web developers manipulating DOM elements
    WHAT: Represents an HTML/SVG element in the document
    WHEN: Use when you need to modify element attributes, content, or structure
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Provides Pythonic DOM manipulation with full type safety
    HOW: Passthrough to JavaScript - same API, zero runtime cost
    
    Element is the base class for all HTML and SVG elements. It provides:
    - Attribute access (getAttribute, setAttribute, etc.)
    - Content manipulation (innerHTML, textContent)
    - Class management (classList)
    - Data attributes (dataset)
    - DOM traversal (parentElement, children, etc.)
    - DOM manipulation (appendChild, remove, etc.)
    
    Example:
        from pynext.client import document
        
        # Get an element
        el = document.getElementById("app")
        
        # Modify content
        el.innerHTML = "<h1>Hello, World!</h1>"
        
        # Modify classes
        el.classList.add("active")
        el.classList.remove("hidden")
        
        # Modify attributes
        el.setAttribute("data-loaded", "true")
        
        # Create and append
        child = document.createElement("div")
        child.textContent = "New content"
        el.appendChild(child)
    """
    
    # ==========================================================================
    # Identity Properties
    # ==========================================================================
    
    @property
    def id(self) -> str:
        """
        The element's id attribute.
        
        Example:
            el.id = "main-container"
            print(el.id)  # "main-container"
        """
        ...
    
    @id.setter
    def id(self, value: str) -> None:
        """Set the element's id."""
        ...
    
    @property
    def tagName(self) -> str:
        """
        The element's tag name (uppercase).
        
        Example:
            div = document.createElement("div")
            print(div.tagName)  # "DIV"
        """
        ...
    
    @property
    def className(self) -> str:
        """
        The element's class attribute as a string.
        
        Example:
            el.className = "foo bar baz"
            print(el.className)  # "foo bar baz"
        
        Note: Prefer classList for adding/removing individual classes.
        """
        ...
    
    @className.setter
    def className(self, value: str) -> None:
        """Set the class attribute string."""
        ...
    
    @property
    def slot(self) -> str:
        """The slot this element is assigned to (Web Components)."""
        ...
    
    @slot.setter
    def slot(self, value: str) -> None:
        """Set the slot assignment."""
        ...
    
    # ==========================================================================
    # Content Properties
    # ==========================================================================
    
    @property
    def innerHTML(self) -> str:
        """
        The HTML content inside this element.
        
        Example:
            el.innerHTML = "<span>Hello</span>"
            print(el.innerHTML)  # "<span>Hello</span>"
        
        Warning: Setting innerHTML with untrusted content is a security risk.
        """
        ...
    
    @innerHTML.setter
    def innerHTML(self, value: str) -> None:
        """Set the inner HTML content."""
        ...
    
    @property
    def outerHTML(self) -> str:
        """
        The HTML including this element and its content.
        
        Example:
            # <div id="x"><span>Hi</span></div>
            print(el.outerHTML)  # '<div id="x"><span>Hi</span></div>'
        """
        ...
    
    @outerHTML.setter
    def outerHTML(self, value: str) -> None:
        """Replace this element with the given HTML."""
        ...
    
    @property
    def innerText(self) -> str:
        """
        The visible text content (respects CSS display).
        
        Unlike textContent, innerText:
        - Respects CSS styling (hidden elements excluded)
        - Triggers reflow when read
        - Preserves visual line breaks
        """
        ...
    
    @innerText.setter
    def innerText(self, value: str) -> None:
        """Set the visible text content."""
        ...
    
    # Note: textContent is inherited from Node
    
    # ==========================================================================
    # Form Element Properties
    # ==========================================================================
    
    @property
    def value(self) -> str:
        """
        The value of form elements (input, textarea, select).
        
        Example:
            input_el = document.getElementById("name-input")
            print(input_el.value)  # Current input value
            input_el.value = "New value"
        """
        ...
    
    @value.setter
    def value(self, val: str) -> None:
        """Set the form element value."""
        ...
    
    @property
    def checked(self) -> bool:
        """Whether a checkbox/radio is checked."""
        ...
    
    @checked.setter
    def checked(self, val: bool) -> None:
        """Set the checked state."""
        ...
    
    @property
    def disabled(self) -> bool:
        """Whether the element is disabled."""
        ...
    
    @disabled.setter
    def disabled(self, val: bool) -> None:
        """Set the disabled state."""
        ...
    
    # ==========================================================================
    # Visibility Properties
    # ==========================================================================
    
    @property
    def hidden(self) -> bool:
        """
        Whether the element is hidden.
        
        Example:
            el.hidden = True   # Hide the element
            el.hidden = False  # Show the element
        """
        ...
    
    @hidden.setter
    def hidden(self, value: bool) -> None:
        """Set the hidden state."""
        ...
    
    @property
    def tabIndex(self) -> int:
        """
        The tab order of the element.
        
        -1: Not focusable via keyboard
        0: Focusable in document order
        >0: Explicit tab order (avoid using)
        """
        ...
    
    @tabIndex.setter
    def tabIndex(self, value: int) -> None:
        """Set the tab order."""
        ...
    
    # ==========================================================================
    # Special Objects
    # ==========================================================================
    
    @property
    def classList(self) -> DOMTokenList:
        """
        A DOMTokenList for managing CSS classes.
        
        Example:
            el.classList.add("active")
            el.classList.remove("hidden")
            el.classList.toggle("visible")
            if el.classList.contains("active"):
                print("Active!")
        """
        ...
    
    @property
    def dataset(self) -> DOMStringMap:
        """
        A DOMStringMap for data-* attributes.
        
        Example:
            # <div data-user-id="123" data-user-name="Alice">
            print(el.dataset.userId)     # "123"
            el.dataset.role = "admin"    # Sets data-role="admin"
        """
        ...
    
    @property
    def style(self) -> CSSStyleDeclaration:
        """
        The inline style of the element.
        
        Example:
            el.style.display = "flex"
            el.style.backgroundColor = "blue"
            el.style.setProperty("--custom", "red")
        """
        ...
    
    @property
    def attributes(self) -> NamedNodeMap:
        """
        A NamedNodeMap of all attributes.
        
        Example:
            for i in range(el.attributes.length):
                attr = el.attributes.item(i)
                print(f"{attr.name}={attr.value}")
        """
        ...
    
    # ==========================================================================
    # Traversal Properties
    # ==========================================================================
    
    @property
    def children(self) -> HTMLCollection:
        """
        A live HTMLCollection of child elements (not text nodes).
        
        Example:
            for child in el.children:
                print(child.tagName)
        """
        ...
    
    @property
    def childElementCount(self) -> int:
        """The number of child elements."""
        ...
    
    @property
    def firstElementChild(self) -> Optional["Element"]:
        """The first child element, or None."""
        ...
    
    @property
    def lastElementChild(self) -> Optional["Element"]:
        """The last child element, or None."""
        ...
    
    @property
    def nextElementSibling(self) -> Optional["Element"]:
        """The next sibling element, or None."""
        ...
    
    @property
    def previousElementSibling(self) -> Optional["Element"]:
        """The previous sibling element, or None."""
        ...
    
    # Note: parentElement, parentNode, childNodes, etc. are inherited from Node
    
    # ==========================================================================
    # Attribute Methods
    # ==========================================================================
    
    def getAttribute(self, name: str) -> Optional[str]:
        """
        Get an attribute value.
        
        Args:
            name: The attribute name
        
        Returns:
            The attribute value, or None if not present
        
        Example:
            href = el.getAttribute("href")
        """
        ...
    
    def setAttribute(self, name: str, value: str) -> None:
        """
        Set an attribute value.
        
        Args:
            name: The attribute name
            value: The value to set
        
        Example:
            el.setAttribute("data-id", "123")
        """
        ...
    
    def removeAttribute(self, name: str) -> None:
        """
        Remove an attribute.
        
        Args:
            name: The attribute name to remove
        
        Example:
            el.removeAttribute("disabled")
        """
        ...
    
    def hasAttribute(self, name: str) -> bool:
        """
        Check if an attribute exists.
        
        Args:
            name: The attribute name
        
        Returns:
            True if the attribute exists
        
        Example:
            if el.hasAttribute("disabled"):
                print("Element is disabled")
        """
        ...
    
    @overload
    def toggleAttribute(self, name: str) -> bool:
        """Toggle a boolean attribute."""
        ...
    
    @overload
    def toggleAttribute(self, name: str, force: bool) -> bool:
        """Force add or remove a boolean attribute."""
        ...
    
    def toggleAttribute(self, name: str, force: Optional[bool] = None) -> bool:
        """
        Toggle a boolean attribute.
        
        Args:
            name: The attribute name
            force: If provided, force add (True) or remove (False)
        
        Returns:
            True if the attribute is now present
        
        Example:
            el.toggleAttribute("disabled")        # Toggle
            el.toggleAttribute("disabled", True)  # Force add
            el.toggleAttribute("disabled", False) # Force remove
        """
        ...
    
    def getAttributeNames(self) -> List[str]:
        """
        Get all attribute names.
        
        Returns:
            A list of attribute names
        
        Example:
            names = el.getAttributeNames()
            # ["id", "class", "data-value"]
        """
        ...
    
    # ==========================================================================
    # Query Methods
    # ==========================================================================
    
    def querySelector(self, selector: str) -> Optional["Element"]:
        """
        Find the first descendant matching a CSS selector.
        
        Args:
            selector: A CSS selector string
        
        Returns:
            The first matching element, or None
        
        Example:
            btn = el.querySelector("button.primary")
        """
        ...
    
    def querySelectorAll(self, selector: str) -> NodeList:
        """
        Find all descendants matching a CSS selector.
        
        Args:
            selector: A CSS selector string
        
        Returns:
            A static NodeList of matching elements
        
        Example:
            items = el.querySelectorAll(".item")
            for item in items:
                item.classList.add("processed")
        """
        ...
    
    def getElementsByClassName(self, names: str) -> HTMLCollection:
        """
        Get descendants by class name(s).
        
        Args:
            names: Space-separated class names
        
        Returns:
            A live HTMLCollection of matching elements
        
        Example:
            items = el.getElementsByClassName("item active")
        """
        ...
    
    def getElementsByTagName(self, name: str) -> HTMLCollection:
        """
        Get descendants by tag name.
        
        Args:
            name: The tag name (case-insensitive)
        
        Returns:
            A live HTMLCollection of matching elements
        
        Example:
            divs = el.getElementsByTagName("div")
        """
        ...
    
    def closest(self, selector: str) -> Optional["Element"]:
        """
        Find the closest ancestor (or self) matching a selector.
        
        Args:
            selector: A CSS selector string
        
        Returns:
            The closest matching element, or None
        
        Example:
            container = el.closest(".container")
        """
        ...
    
    def matches(self, selector: str) -> bool:
        """
        Check if this element matches a selector.
        
        Args:
            selector: A CSS selector string
        
        Returns:
            True if the element matches
        
        Example:
            if el.matches(".active"):
                print("Element is active")
        """
        ...
    
    # ==========================================================================
    # Manipulation Methods
    # ==========================================================================
    
    def remove(self) -> None:
        """
        Remove this element from the DOM.
        
        Example:
            el.remove()  # Element is no longer in the document
        """
        ...
    
    def append(self, *nodes: Union[Node, str]) -> None:
        """
        Append nodes or strings to this element.
        
        Args:
            *nodes: Nodes or strings to append
        
        Example:
            el.append(child1, "text", child2)
        """
        ...
    
    def prepend(self, *nodes: Union[Node, str]) -> None:
        """
        Prepend nodes or strings to this element.
        
        Args:
            *nodes: Nodes or strings to prepend
        
        Example:
            el.prepend(header, "Title: ")
        """
        ...
    
    def after(self, *nodes: Union[Node, str]) -> None:
        """
        Insert nodes or strings after this element.
        
        Args:
            *nodes: Nodes or strings to insert
        
        Example:
            el.after(sibling, "text")
        """
        ...
    
    def before(self, *nodes: Union[Node, str]) -> None:
        """
        Insert nodes or strings before this element.
        
        Args:
            *nodes: Nodes or strings to insert
        
        Example:
            el.before(header)
        """
        ...
    
    def replaceWith(self, *nodes: Union[Node, str]) -> None:
        """
        Replace this element with nodes or strings.
        
        Args:
            *nodes: Nodes or strings to replace with
        
        Example:
            el.replaceWith(newElement)
        """
        ...
    
    def replaceChildren(self, *nodes: Union[Node, str]) -> None:
        """
        Replace all children with new nodes or strings.
        
        Args:
            *nodes: Nodes or strings to use as children
        
        Example:
            el.replaceChildren(child1, child2)
        """
        ...
    
    def cloneNode(self, deep: bool = False) -> "Element":
        """
        Clone this element.
        
        Args:
            deep: If True, clone all descendants
        
        Returns:
            The cloned element
        
        Example:
            clone = el.cloneNode(deep=True)
        """
        ...
    
    def insertAdjacentHTML(self, position: str, text: str) -> None:
        """
        Insert HTML at a specified position.
        
        Args:
            position: "beforebegin", "afterbegin", "beforeend", "afterend"
            text: HTML string to insert
        
        Example:
            el.insertAdjacentHTML("beforeend", "<span>New</span>")
        """
        ...
    
    def insertAdjacentElement(
        self,
        position: str,
        element: "Element"
    ) -> Optional["Element"]:
        """
        Insert an element at a specified position.
        
        Args:
            position: "beforebegin", "afterbegin", "beforeend", "afterend"
            element: Element to insert
        
        Returns:
            The inserted element, or None on failure
        """
        ...
    
    def insertAdjacentText(self, position: str, text: str) -> None:
        """
        Insert text at a specified position.
        
        Args:
            position: "beforebegin", "afterbegin", "beforeend", "afterend"
            text: Text to insert
        """
        ...
    
    # ==========================================================================
    # Focus Methods
    # ==========================================================================
    
    def focus(self) -> None:
        """
        Focus this element.
        
        Example:
            input_el.focus()
        """
        ...
    
    def blur(self) -> None:
        """
        Remove focus from this element.
        
        Example:
            input_el.blur()
        """
        ...
    
    def click(self) -> None:
        """
        Simulate a click on this element.
        
        Example:
            button.click()
        """
        ...
    
    # ==========================================================================
    # Scroll Methods
    # ==========================================================================
    
    def scrollIntoView(self, options: Any = None) -> None:
        """
        Scroll this element into view.
        
        Args:
            options: Boolean or ScrollIntoViewOptions dict
                - True: Align to top
                - False: Align to bottom
                - {behavior: "smooth", block: "center"}
        
        Example:
            el.scrollIntoView()
            el.scrollIntoView({"behavior": "smooth"})
        """
        ...
    
    @property
    def scrollTop(self) -> float:
        """Vertical scroll position."""
        ...
    
    @scrollTop.setter
    def scrollTop(self, value: float) -> None:
        """Set vertical scroll position."""
        ...
    
    @property
    def scrollLeft(self) -> float:
        """Horizontal scroll position."""
        ...
    
    @scrollLeft.setter
    def scrollLeft(self, value: float) -> None:
        """Set horizontal scroll position."""
        ...
    
    @property
    def scrollWidth(self) -> int:
        """Total scrollable width."""
        ...
    
    @property
    def scrollHeight(self) -> int:
        """Total scrollable height."""
        ...
    
    # ==========================================================================
    # Dimension Properties
    # ==========================================================================
    
    @property
    def clientWidth(self) -> int:
        """Inner width including padding (excluding scrollbar)."""
        ...
    
    @property
    def clientHeight(self) -> int:
        """Inner height including padding (excluding scrollbar)."""
        ...
    
    @property
    def clientTop(self) -> int:
        """Top border width."""
        ...
    
    @property
    def clientLeft(self) -> int:
        """Left border width."""
        ...
    
    @property
    def offsetWidth(self) -> int:
        """Layout width including borders."""
        ...
    
    @property
    def offsetHeight(self) -> int:
        """Layout height including borders."""
        ...
    
    @property
    def offsetTop(self) -> int:
        """Top position relative to offsetParent."""
        ...
    
    @property
    def offsetLeft(self) -> int:
        """Left position relative to offsetParent."""
        ...
    
    @property
    def offsetParent(self) -> Optional["Element"]:
        """The positioned ancestor element."""
        ...
    
    def getBoundingClientRect(self) -> "DOMRect":
        """
        Get the element's size and position.
        
        Returns:
            A DOMRect with top, right, bottom, left, width, height
        
        Example:
            rect = el.getBoundingClientRect()
            print(f"Position: ({rect.x}, {rect.y})")
            print(f"Size: {rect.width}x{rect.height}")
        """
        ...
    
    # ==========================================================================
    # Web Animations API (Phase 34.2)
    # ==========================================================================
    
    def animate(
        self,
        keyframes: List[Dict[str, str]],
        duration: int = 0,
        delay: int = 0,
        endDelay: int = 0,
        easing: str = "linear",
        iterations: Union[int, float] = 1,
        direction: str = "normal",
        fill: str = "none",
    ) -> Any:  # Returns Animation
        """
        Animate this element using the Web Animations API.
        
        WHO: Developers creating smooth, GPU-accelerated animations
        WHAT: Creates and plays an animation on this element
        WHEN: Use for programmatic animations that need control
        WHERE: Client-side code (transpiled to JavaScript)
        WHY: Better performance than CSS transitions for dynamic animations
        HOW: Passthrough to JavaScript element.animate()
        
        Args:
            keyframes: List of keyframe dictionaries with CSS properties
            duration: Animation duration in milliseconds
            delay: Delay before animation starts in ms
            endDelay: Delay after animation ends in ms
            easing: Timing function (linear, ease, ease-in, ease-out, etc.)
            iterations: Number of times to repeat (use float("inf") for infinite)
            direction: Playback direction (normal, reverse, alternate)
            fill: Fill mode (none, forwards, backwards, both)
        
        Returns:
            Animation object with play(), pause(), cancel(), finished, etc.
        
        Example:
            # Simple fade in
            anim = el.animate([
                {"opacity": "0"},
                {"opacity": "1"},
            ], duration=300)
            await anim.finished
            
            # Complex animation with easing
            anim = el.animate([
                {"transform": "scale(0.9)", "opacity": "0"},
                {"transform": "scale(1)", "opacity": "1"},
            ], duration=300, easing="ease-out", fill="forwards")
            
            # Control the animation
            anim.pause()
            anim.playbackRate = 2.0
            anim.reverse()
        """
        ...
    
    def getAnimations(self) -> List[Any]:  # Returns List[Animation]
        """
        Get all animations currently running on this element.
        
        WHO: Developers managing multiple animations
        WHAT: Returns list of active Animation objects
        WHEN: Use to inspect, pause, or cancel running animations
        WHERE: Client-side code (transpiled to JavaScript)
        WHY: Manage complex animation states
        HOW: Passthrough to JavaScript element.getAnimations()
        
        Returns:
            List of Animation objects
        
        Example:
            # Cancel all animations on an element
            for anim in el.getAnimations():
                anim.cancel()
            
            # Pause all animations
            for anim in el.getAnimations():
                anim.pause()
        """
        ...


# =============================================================================
# DOMRect (returned by getBoundingClientRect)
# =============================================================================

class DOMRect:
    """
    Represents an element's size and position.
    
    Example:
        rect = el.getBoundingClientRect()
        print(rect.top, rect.left, rect.width, rect.height)
    """
    
    @property
    def x(self) -> float:
        """X coordinate (same as left)."""
        ...
    
    @property
    def y(self) -> float:
        """Y coordinate (same as top)."""
        ...
    
    @property
    def width(self) -> float:
        """Width of the rectangle."""
        ...
    
    @property
    def height(self) -> float:
        """Height of the rectangle."""
        ...
    
    @property
    def top(self) -> float:
        """Top edge Y coordinate."""
        ...
    
    @property
    def right(self) -> float:
        """Right edge X coordinate."""
        ...
    
    @property
    def bottom(self) -> float:
        """Bottom edge Y coordinate."""
        ...
    
    @property
    def left(self) -> float:
        """Left edge X coordinate."""
        ...


# =============================================================================
# Document Class
# =============================================================================

class Document(Node):
    """
    WHO: Web developers working with the DOM
    WHAT: The Document interface - entry point for DOM manipulation
    WHEN: Use to query, create, and access document-level properties
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Provides access to the entire document tree
    HOW: Passthrough to JavaScript - same API, zero runtime cost
    
    The Document is the main entry point for DOM manipulation. It provides:
    - Query methods (getElementById, querySelector, etc.)
    - Creation methods (createElement, createTextNode, etc.)
    - Document properties (body, head, title, etc.)
    
    Example:
        from pynext.client import document
        
        # Query elements
        app = document.getElementById("app")
        buttons = document.querySelectorAll("button")
        
        # Create elements
        div = document.createElement("div")
        text = document.createTextNode("Hello")
        
        # Access document properties
        document.title = "My App"
        print(document.readyState)
    """
    
    # ==========================================================================
    # Document Properties
    # ==========================================================================
    
    @property
    def body(self) -> Element:
        """
        The document's <body> element.
        
        Example:
            document.body.appendChild(newElement)
        """
        ...
    
    @property
    def head(self) -> Element:
        """
        The document's <head> element.
        
        Example:
            meta = document.createElement("meta")
            document.head.appendChild(meta)
        """
        ...
    
    @property
    def documentElement(self) -> Element:
        """
        The root <html> element.
        
        Example:
            document.documentElement.lang = "en"
        """
        ...
    
    @property
    def title(self) -> str:
        """
        The document title.
        
        Example:
            document.title = "Welcome - My App"
        """
        ...
    
    @title.setter
    def title(self, value: str) -> None:
        """Set the document title."""
        ...
    
    @property
    def activeElement(self) -> Optional[Element]:
        """
        The currently focused element.
        
        Example:
            focused = document.activeElement
            if focused:
                print(focused.tagName)
        """
        ...
    
    @property
    def readyState(self) -> str:
        """
        The document loading state.
        
        Values:
            - "loading": Document is loading
            - "interactive": DOM is ready, resources loading
            - "complete": Fully loaded
        """
        ...
    
    @property
    def hidden(self) -> bool:
        """Whether the document is hidden (tab not visible)."""
        ...
    
    @property
    def visibilityState(self) -> str:
        """
        The visibility state of the document.
        
        Values:
            - "visible": Tab is in foreground
            - "hidden": Tab is in background
        """
        ...
    
    @property
    def cookie(self) -> str:
        """
        Document cookies as a string.
        
        Example:
            # Read
            print(document.cookie)
            
            # Write
            document.cookie = "name=value; path=/"
        """
        ...
    
    @cookie.setter
    def cookie(self, value: str) -> None:
        """Set a cookie."""
        ...
    
    @property
    def URL(self) -> str:
        """The document's URL."""
        ...
    
    @property
    def domain(self) -> str:
        """The document's domain."""
        ...
    
    @property
    def referrer(self) -> str:
        """The referrer URL."""
        ...
    
    @property
    def characterSet(self) -> str:
        """The document's character encoding."""
        ...
    
    @property
    def contentType(self) -> str:
        """The document's MIME type."""
        ...
    
    # ==========================================================================
    # Query Methods
    # ==========================================================================
    
    def getElementById(self, id: str) -> Optional[Element]:
        """
        Get an element by its id attribute.
        
        Args:
            id: The element's id (without #)
        
        Returns:
            The element, or None if not found
        
        Example:
            app = document.getElementById("app")
            if app:
                app.innerHTML = "Hello!"
        """
        ...
    
    def querySelector(self, selector: str) -> Optional[Element]:
        """
        Find the first element matching a CSS selector.
        
        Args:
            selector: A CSS selector string
        
        Returns:
            The first matching element, or None
        
        Example:
            btn = document.querySelector("button.primary")
            card = document.querySelector("#cards > .card:first-child")
        """
        ...
    
    def querySelectorAll(self, selector: str) -> NodeList:
        """
        Find all elements matching a CSS selector.
        
        Args:
            selector: A CSS selector string
        
        Returns:
            A static NodeList of matching elements
        
        Example:
            items = document.querySelectorAll(".item")
            for item in items:
                item.classList.add("processed")
        """
        ...
    
    def getElementsByClassName(self, names: str) -> HTMLCollection:
        """
        Get elements by class name(s).
        
        Args:
            names: Space-separated class names
        
        Returns:
            A live HTMLCollection of matching elements
        
        Example:
            items = document.getElementsByClassName("item")
            actives = document.getElementsByClassName("item active")
        """
        ...
    
    def getElementsByTagName(self, name: str) -> HTMLCollection:
        """
        Get elements by tag name.
        
        Args:
            name: The tag name (case-insensitive), or "*" for all
        
        Returns:
            A live HTMLCollection of matching elements
        
        Example:
            divs = document.getElementsByTagName("div")
            all_elements = document.getElementsByTagName("*")
        """
        ...
    
    def getElementsByName(self, name: str) -> NodeList:
        """
        Get elements by their name attribute.
        
        Args:
            name: The name attribute value
        
        Returns:
            A NodeList of matching elements
        
        Example:
            radios = document.getElementsByName("color")
        """
        ...
    
    # ==========================================================================
    # Creation Methods
    # ==========================================================================
    
    def createElement(self, tagName: str) -> Element:
        """
        Create an HTML element.
        
        Args:
            tagName: The tag name (e.g., "div", "span", "button")
        
        Returns:
            A new Element
        
        Example:
            div = document.createElement("div")
            div.id = "container"
            div.className = "wrapper"
            document.body.appendChild(div)
        """
        ...
    
    def createElementNS(self, namespace: str, tagName: str) -> Element:
        """
        Create a namespaced element (SVG, MathML).
        
        Args:
            namespace: The namespace URI
            tagName: The tag name
        
        Returns:
            A new Element
        
        Example:
            svg_ns = "http://www.w3.org/2000/svg"
            svg = document.createElementNS(svg_ns, "svg")
            circle = document.createElementNS(svg_ns, "circle")
            circle.setAttribute("r", "50")
        """
        ...
    
    def createTextNode(self, text: str) -> Text:
        """
        Create a text node.
        
        Args:
            text: The text content
        
        Returns:
            A new Text node
        
        Example:
            text = document.createTextNode("Hello, World!")
            element.appendChild(text)
        """
        ...
    
    def createComment(self, text: str) -> Comment:
        """
        Create a comment node.
        
        Args:
            text: The comment text
        
        Returns:
            A new Comment node
        
        Example:
            comment = document.createComment("TODO: Add feature")
            element.appendChild(comment)
        """
        ...
    
    def createDocumentFragment(self) -> DocumentFragment:
        """
        Create a document fragment for efficient batch operations.
        
        Returns:
            A new DocumentFragment
        
        Example:
            fragment = document.createDocumentFragment()
            for item in items:
                li = document.createElement("li")
                li.textContent = item
                fragment.appendChild(li)
            ul.appendChild(fragment)  # Single reflow
        """
        ...
    
    # ==========================================================================
    # Event Methods (commonly used)
    # ==========================================================================
    
    def addEventListener(
        self,
        type: str,
        listener: Any,
        options: Any = None
    ) -> None:
        """
        Add an event listener to the document.
        
        Args:
            type: Event type (e.g., "click", "keydown")
            listener: Event handler function
            options: Options dict or useCapture boolean
        """
        ...
    
    def removeEventListener(
        self,
        type: str,
        listener: Any,
        options: Any = None
    ) -> None:
        """Remove an event listener from the document."""
        ...


# =============================================================================
# Global Document Instance
# =============================================================================

# The global document object - available after import
# In JavaScript, this is the browser's document global
#
# This is a placeholder instance for type checking and IDE support.
# When transpiled to JavaScript, this becomes the browser's `document` global.
# The actual implementation is provided by the browser, not Python.
#
# Usage in Python (for type hints):
#     from pynext.client import document
#     el: Element = document.getElementById("app")
#
# Transpiles to JavaScript:
#     let el = document.getElementById("app");

class _DocumentStub(Document):
    """
    Placeholder document instance for Python-side type checking.
    
    This class exists only for IDE support and type checking.
    At runtime in the browser, the global `document` object is used.
    """
    
    def __getattr__(self, name: str) -> Any:
        """Allow any attribute access for dynamic typing."""
        raise RuntimeError(
            "document is a client-side object. This code should be transpiled "
            "to JavaScript and run in a browser, not executed directly in Python."
        )
    
    def __repr__(self) -> str:
        return "<document (client-side DOM stub)>"


# Global document instance (placeholder for type checking)
document: Document = _DocumentStub()  # type: ignore


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Main interfaces
    "Document",
    "Element",
    
    # Supporting types
    "CSSStyleDeclaration",
    "DOMRect",
    
    # Global instance
    "document",
    
    # Re-export node types for convenience
    "Node",
    "NodeList",
    "HTMLCollection",
    "DOMStringMap",
    "DOMTokenList",
    "NamedNodeMap",
    "Text",
    "Comment",
    "DocumentFragment",
]

