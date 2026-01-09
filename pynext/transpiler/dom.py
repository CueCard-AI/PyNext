"""
PyNext Transpiler - DOM Passthrough Detection

=============================================================================
WHAT THIS FILE DOES
=============================================================================

Provides registry of DOM APIs that should pass through unchanged during
transpilation. DOM APIs are identical in Python and JavaScript, so they
require no transformation - the exact same code works in both languages.

=============================================================================
WHY THIS EXISTS
=============================================================================

Most Python constructs need transformation to JavaScript:
- `items[-1]` → `__py.at(items, -1)`
- `items.append(x)` → `items.push(x)`

But DOM APIs are standardized by W3C and work identically in both languages:
- `document.getElementById("app")` → `document.getElementById("app")`
- `el.classList.add("active")` → `el.classList.add("active")`

This module identifies which APIs are DOM passthrough to:
1. Skip unnecessary transformation
2. Avoid adding runtime overhead
3. Produce clean, idiomatic JavaScript

=============================================================================
HOW IT WORKS
=============================================================================

The transpiler checks API calls against these registries:
1. DOM_GLOBALS - Browser globals (document, window)
2. DOM_METHODS - Methods that pass through unchanged
3. DOM_PROPERTIES - Properties that pass through unchanged

When a call matches, the emitter outputs it unchanged instead of
wrapping it with `__py.*` helpers.

=============================================================================
WHO USES THIS
=============================================================================

- emitter.py: Checks if method/property is DOM passthrough
- imports.py: Handles `from pynext.client import document` specially
- optimizer/types.py: Type-based optimization detection

=============================================================================
EXAMPLES
=============================================================================

    # These all pass through unchanged:
    document.getElementById("app")      → document.getElementById("app")
    el.setAttribute("id", "123")        → el.setAttribute("id", "123")
    el.classList.add("active")          → el.classList.add("active")
    el.dataset.userId                   → el.dataset.userId
    el.children.length                  → el.children.length
"""

from typing import Set, FrozenSet


# =============================================================================
# Browser Globals
# =============================================================================

DOM_GLOBALS: FrozenSet[str] = frozenset({
    # Core globals
    "document",
    "window",
    
    # Web APIs that are global
    "console",
    "localStorage",
    "sessionStorage",
    "location",
    "history",
    "navigator",
    "screen",
    
    # Constructors
    "Element",
    "Node",
    "Document",
    "DocumentFragment",
    "Text",
    "Comment",
    "NodeList",
    "HTMLCollection",
    "DOMTokenList",
    "DOMStringMap",
    "NamedNodeMap",
    "Attr",
    "CSSStyleDeclaration",
    "DOMRect",
    
    # Events
    "Event",
    "MouseEvent",
    "KeyboardEvent",
    "TouchEvent",
    "FocusEvent",
    "InputEvent",
    "CustomEvent",
    
    # Others
    "MutationObserver",
    "ResizeObserver",
    "IntersectionObserver",
    "AbortController",
    "AbortSignal",
    "URL",
    "URLSearchParams",
    "FormData",
    "Headers",
    "Request",
    "Response",
    "Blob",
    "File",
    "FileReader",
    "XMLHttpRequest",
    "WebSocket",
    
    # =========================================================================
    # CSS Typed OM (Phase 34.3)
    # =========================================================================
    "CSS",                    # CSS factory namespace (CSS.px(), CSS.percent(), etc.)
    "CSSStyleValue",          # Base type for typed CSS values
    "CSSNumericValue",        # Numeric value base
    "CSSUnitValue",           # Value with unit (e.g., 100px)
    "CSSKeywordValue",        # Keyword values (auto, inherit)
    "CSSMathValue",           # Math expressions
    "CSSMathSum",             # calc() with +/-
    "CSSMathProduct",         # calc() with *//
    "CSSMathMin",             # min()
    "CSSMathMax",             # max()
    "CSSMathClamp",           # clamp()
    "CSSTransformValue",      # Combined transforms
    "CSSTransformComponent",  # Individual transform
    "CSSTranslate",           # translate()
    "CSSRotate",              # rotate()
    "CSSScale",               # scale()
    "CSSSkew",                # skew()
    "CSSPerspective",         # perspective()
    "CSSMatrixComponent",     # matrix()
    "StylePropertyMap",       # Typed style map
    "DOMMatrix",              # Transform matrix
})


# =============================================================================
# DOM Methods (all pass through unchanged)
# =============================================================================

DOM_METHODS: FrozenSet[str] = frozenset({
    # =========================================================================
    # Document Query Methods (6)
    # =========================================================================
    "getElementById",
    "querySelector",
    "querySelectorAll",
    "getElementsByClassName",
    "getElementsByTagName",
    "getElementsByName",
    
    # =========================================================================
    # Document Creation Methods (5)
    # =========================================================================
    "createElement",
    "createElementNS",
    "createTextNode",
    "createComment",
    "createDocumentFragment",
    
    # =========================================================================
    # Element Attribute Methods (6)
    # =========================================================================
    "getAttribute",
    "setAttribute",
    "removeAttribute",
    "hasAttribute",
    "toggleAttribute",
    "getAttributeNames",
    
    # =========================================================================
    # Element Manipulation Methods (12)
    # =========================================================================
    "appendChild",
    "insertBefore",
    "removeChild",
    "replaceChild",
    "remove",
    "cloneNode",
    "append",
    "prepend",
    "after",
    "before",
    "replaceWith",
    "replaceChildren",
    
    # =========================================================================
    # Element Traversal Methods (2)
    # =========================================================================
    "closest",
    "matches",
    
    # =========================================================================
    # Element Focus Methods (3)
    # =========================================================================
    "focus",
    "blur",
    "click",
    
    # =========================================================================
    # Element Scroll Methods (3)
    # =========================================================================
    "scrollIntoView",
    "scrollTo",
    "scrollBy",
    
    # =========================================================================
    # Element Dimension Methods (1)
    # =========================================================================
    "getBoundingClientRect",
    
    # =========================================================================
    # Element Content Methods (3)
    # =========================================================================
    "insertAdjacentHTML",
    "insertAdjacentElement",
    "insertAdjacentText",
    
    # =========================================================================
    # Collection Methods (6)
    # =========================================================================
    "item",
    "namedItem",
    "forEach",
    "entries",
    "keys",
    "values",
    
    # =========================================================================
    # DOMTokenList (classList) Methods (6)
    # =========================================================================
    "add",      # classList.add
    "contains", # classList.contains
    "toggle",   # classList.toggle
    "replace",  # classList.replace
    "supports", # classList.supports
    # "remove" is already in manipulation methods
    
    # =========================================================================
    # CSSStyleDeclaration Methods (4)
    # =========================================================================
    "getPropertyValue",
    "setProperty",
    "removeProperty",
    "getPropertyPriority",
    
    # =========================================================================
    # Window Methods (Phase 34.2)
    # =========================================================================
    "getComputedStyle",
    "matchMedia",
    "getSelection",
    
    # =========================================================================
    # Web Animations API Methods (Phase 34.2)
    # =========================================================================
    "animate",
    "getAnimations",
    "pause",
    "play",
    "cancel",
    "finish",
    "reverse",
    "updatePlaybackRate",
    "persist",
    "commitStyles",
    
    # =========================================================================
    # Node Methods (8)
    # =========================================================================
    "hasChildNodes",
    "normalize",
    "getRootNode",
    "isSameNode",
    "isEqualNode",
    "compareDocumentPosition",
    "lookupPrefix",
    "lookupNamespaceURI",
    
    # =========================================================================
    # Event Methods (4)
    # =========================================================================
    "addEventListener",
    "removeEventListener",
    "dispatchEvent",
    "preventDefault",
    "stopPropagation",
    "stopImmediatePropagation",
    
    # =========================================================================
    # Text Methods (1)
    # =========================================================================
    "splitText",
    
    # =========================================================================
    # NamedNodeMap Methods (3)
    # =========================================================================
    "getNamedItem",
    "setNamedItem",
    "removeNamedItem",
    
    # =========================================================================
    # CSS Typed OM Factory Methods (Phase 34.3)
    # CSS.px(), CSS.percent(), etc.
    # =========================================================================
    "px",
    "percent",
    "em",
    "rem",
    "vw",
    "vh",
    "vmin",
    "vmax",
    "cm",
    "mm",
    "Q",
    # "in" conflicts with Python keyword - handled specially
    "pt",
    "pc",
    "ch",
    "ex",
    "lh",
    "rlh",
    "svw",
    "svh",
    "lvw",
    "lvh",
    "dvw",
    "dvh",
    "deg",
    "rad",
    "turn",
    "grad",
    "ms",  # Note: also used elsewhere but safe to include
    # "s" is too short and conflicts - handled in context
    "Hz",
    "kHz",
    "dpi",
    "dpcm",
    "dppx",
    "fr",
    "number",
    "calc",
    # "min" and "max" handled specially (conflict with builtins)
    # "clamp" is unique
    
    # =========================================================================
    # CSS Typed OM Value Methods (Phase 34.3)
    # CSSNumericValue arithmetic
    # =========================================================================
    # "add" - conflicts with set.add, classList.add (handled by context)
    "sub",
    "mul",
    "div",
    "equals",
    "to",
    "toSum",
    "negate",
    "invert",
    
    # =========================================================================
    # CSS Typed OM Transform Methods (Phase 34.3)
    # CSS.translate(), CSS.rotate(), CSS.scale(), etc.
    # =========================================================================
    "translate",
    "translate3d",
    "translateX",
    "translateY",
    "translateZ",
    # "rotate" - conflict with CSSRotate usage
    "rotate3d",
    "rotateX",
    "rotateY",
    "rotateZ",
    # "scale" - conflicts with CSSScale (handled by context)
    "scale3d",
    "scaleX",
    "scaleY",
    "scaleZ",
    "skewX",
    "skewY",
    "matrix3d",
    "toMatrix",
    
    # =========================================================================
    # CSS Typed OM Color Methods (Phase 34.3)
    # =========================================================================
    "rgb",
    "hsl",
    "hwb",
    "oklch",
    "oklab",
    "lab",
    "lch",
    "lighten",
    "darken",
    "saturate",
    "desaturate",
    "grayscale",
    "fadeIn",
    "fadeOut",
    "complement",
    "adjustContrast",
    "toRGB",
    "toRGBA",
    "toHSL",
    "toOKLCH",
    "toHex",
    
    # =========================================================================
    # StylePropertyMap Methods (Phase 34.3)
    # el.attributeStyleMap.set(), etc.
    # =========================================================================
    # "set" - already in DOM methods (setAttribute context)
    # "get" - common pattern
    # "delete" - already common
    # "has" - already common
    # "clear" - already common
    "getAll",
    "computedStyleMap",
})


# =============================================================================
# DOM Properties (all pass through unchanged)
# =============================================================================

DOM_PROPERTIES: FrozenSet[str] = frozenset({
    # =========================================================================
    # Document Properties (15)
    # =========================================================================
    "body",
    "head",
    "documentElement",
    "title",
    "activeElement",
    "readyState",
    "hidden",
    "visibilityState",
    "cookie",
    "URL",
    "domain",
    "referrer",
    "characterSet",
    "contentType",
    "defaultView",
    
    # =========================================================================
    # Element Identity Properties (4)
    # =========================================================================
    "id",
    "tagName",
    "className",
    "slot",
    
    # =========================================================================
    # Element Content Properties (5)
    # =========================================================================
    "innerHTML",
    "outerHTML",
    "innerText",
    "textContent",
    "value",
    
    # =========================================================================
    # Element Form Properties (4)
    # =========================================================================
    "checked",
    "disabled",
    "readOnly",
    "required",
    
    # =========================================================================
    # Element Visibility Properties (2)
    # =========================================================================
    # "hidden" already in document properties
    "tabIndex",
    
    # =========================================================================
    # Element Special Objects (4)
    # =========================================================================
    "classList",
    "dataset",
    "style",
    "attributes",
    
    # =========================================================================
    # Node Traversal Properties (14)
    # =========================================================================
    "parentElement",
    "parentNode",
    "children",
    "childNodes",
    "firstElementChild",
    "lastElementChild",
    "firstChild",
    "lastChild",
    "nextElementSibling",
    "previousElementSibling",
    "nextSibling",
    "previousSibling",
    "childElementCount",
    "ownerDocument",
    
    # =========================================================================
    # Node State Properties (3)
    # =========================================================================
    "isConnected",
    "nodeType",
    "nodeName",
    "nodeValue",
    
    # =========================================================================
    # Element Dimension Properties (12)
    # =========================================================================
    "clientWidth",
    "clientHeight",
    "clientTop",
    "clientLeft",
    "offsetWidth",
    "offsetHeight",
    "offsetTop",
    "offsetLeft",
    "offsetParent",
    "scrollWidth",
    "scrollHeight",
    "scrollTop",
    "scrollLeft",
    
    # =========================================================================
    # Collection Properties (2)
    # =========================================================================
    "length",
    # "item" is a method
    
    # =========================================================================
    # DOMTokenList Properties (1)
    # =========================================================================
    # "length" already above
    # "value" already in content properties
    
    # =========================================================================
    # CSSStyleDeclaration Properties (commonly used)
    # =========================================================================
    "cssText",
    "display",
    "visibility",
    "opacity",
    "position",
    "top",
    "right",
    "bottom",
    "left",
    "width",
    "height",
    "margin",
    "padding",
    "border",
    "backgroundColor",
    "color",
    "fontSize",
    "fontWeight",
    "transform",
    "transition",
    "animation",
    "zIndex",
    "overflow",
    "cursor",
    "flexDirection",
    "justifyContent",
    "alignItems",
    
    # =========================================================================
    # DOMRect Properties (8)
    # =========================================================================
    "x",
    "y",
    # "width" already above
    # "height" already above
    # "top" already above
    # "right" already above
    # "bottom" already above
    # "left" already above
    
    # =========================================================================
    # Text Node Properties (3)
    # =========================================================================
    "data",
    "wholeText",
    # "length" already above
    
    # =========================================================================
    # Attr Properties (2)
    # =========================================================================
    "name",
    # "value" already above
    "ownerElement",
    
    # =========================================================================
    # CSS Typed OM Properties (Phase 34.3)
    # =========================================================================
    "attributeStyleMap",  # el.attributeStyleMap → StylePropertyMap
    "unit",               # CSSUnitValue.unit
    # "value" already above (CSSUnitValue.value, CSSKeywordValue.value)
    "size",               # StylePropertyMap.size
    "is2D",               # CSSTransformValue.is2D, CSSTransformComponent.is2D
    "isIdentity",         # DOMMatrix.isIdentity
    "operator",           # CSSMathValue.operator
    "values",             # CSSMathValue.values (iterator methods already exist)
    
    # DOMMatrix properties (for transform toMatrix())
    "a", "b", "c", "d", "e", "f",  # 2D matrix
    "m11", "m12", "m13", "m14",
    "m21", "m22", "m23", "m24",
    "m31", "m32", "m33", "m34",
    "m41", "m42", "m43", "m44",
    
    # CSSTransformComponent properties
    "ax", "ay",           # CSSSkew
    "angle",              # CSSRotate
})


# =============================================================================
# Type-Only Imports (no JS import needed)
# =============================================================================

DOM_TYPE_ONLY_IMPORTS: FrozenSet[str] = frozenset({
    # These are types that don't need actual imports - they're just type hints
    "Element",
    "Node",
    "Document",
    "NodeList",
    "HTMLCollection",
    "DOMTokenList",
    "DOMStringMap",
    "NamedNodeMap",
    "Attr",
    "Text",
    "Comment",
    "DocumentFragment",
    "CSSStyleDeclaration",
    "DOMRect",
    
    # CSS Typed OM types (Phase 34.3)
    "CSSStyleValue",
    "CSSNumericValue",
    "CSSUnitValue",
    "CSSKeywordValue",
    "CSSMathValue",
    "CSSMathSum",
    "CSSMathProduct",
    "CSSMathMin",
    "CSSMathMax",
    "CSSMathClamp",
    "CSSTransformValue",
    "CSSTransformComponent",
    "CSSTranslate",
    "CSSRotate",
    "CSSScale",
    "CSSSkew",
    "CSSPerspective",
    "CSSMatrixComponent",
    "StylePropertyMap",
    "StylePropertyMapReadOnly",
    "DOMMatrix",
    "CSSColor",
})


# =============================================================================
# Helper Functions
# =============================================================================

def is_dom_global(name: str) -> bool:
    """
    Check if a name is a browser global.
    
    Args:
        name: The identifier name
    
    Returns:
        True if this is a browser global (document, window, etc.)
    
    Example:
        is_dom_global("document")  # True
        is_dom_global("myVar")     # False
    """
    return name in DOM_GLOBALS


def is_dom_method(name: str) -> bool:
    """
    Check if a method name is a DOM API method.
    
    Args:
        name: The method name
    
    Returns:
        True if this is a DOM method that should pass through
    
    Example:
        is_dom_method("getElementById")  # True
        is_dom_method("append")          # True  
        is_dom_method("myMethod")        # False
    """
    return name in DOM_METHODS


def is_dom_property(name: str) -> bool:
    """
    Check if a property name is a DOM API property.
    
    Args:
        name: The property name
    
    Returns:
        True if this is a DOM property that should pass through
    
    Example:
        is_dom_property("innerHTML")     # True
        is_dom_property("children")      # True
        is_dom_property("myProperty")    # False
    """
    return name in DOM_PROPERTIES


def is_dom_passthrough(name: str) -> bool:
    """
    Check if an attribute access should pass through unchanged.
    
    This is the main entry point for the emitter to check if a method
    call or property access should be emitted as-is (passthrough).
    
    Args:
        name: The method or property name
    
    Returns:
        True if this should pass through without transformation
    
    Example:
        is_dom_passthrough("getElementById")  # True
        is_dom_passthrough("innerHTML")       # True
        is_dom_passthrough("append")          # True (Python list.append is different, but DOM append passes through)
    """
    return name in DOM_METHODS or name in DOM_PROPERTIES


def is_dom_type_import(name: str) -> bool:
    """
    Check if an import is type-only (no JS import needed).
    
    Args:
        name: The imported name
    
    Returns:
        True if this is a type-only import
    
    Example:
        is_dom_type_import("Element")    # True
        is_dom_type_import("document")   # False (this is a global, not a type)
    """
    return name in DOM_TYPE_ONLY_IMPORTS


def should_skip_import(name: str) -> bool:
    """
    Check if an import from pynext.client should be skipped.
    
    DOM globals and type-only imports don't need actual JavaScript imports
    because they're either browser globals or just type annotations.
    
    Args:
        name: The imported name
    
    Returns:
        True if the import should be skipped in generated JS
    
    Example:
        should_skip_import("document")   # True (browser global)
        should_skip_import("Element")    # True (type only)
        should_skip_import("typed")      # False (needs import)
    """
    return name in DOM_GLOBALS or name in DOM_TYPE_ONLY_IMPORTS


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Registries
    "DOM_GLOBALS",
    "DOM_METHODS",
    "DOM_PROPERTIES",
    "DOM_TYPE_ONLY_IMPORTS",
    
    # Helper functions
    "is_dom_global",
    "is_dom_method",
    "is_dom_property",
    "is_dom_passthrough",
    "is_dom_type_import",
    "should_skip_import",
]

