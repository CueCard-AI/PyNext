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
    
    # Events (Phase 34.4)
    "Event",
    "UIEvent",
    "MouseEvent",
    "KeyboardEvent",
    "TouchEvent",
    "FocusEvent",
    "InputEvent",
    "CustomEvent",
    "DragEvent",
    "WheelEvent",
    "PointerEvent",
    "AnimationEvent",
    "TransitionEvent",
    "SubmitEvent",
    "FormDataEvent",
    "ClipboardEvent",
    "CompositionEvent",
    "StorageEvent",
    "MessageEvent",
    "ErrorEvent",
    "CloseEvent",
    "HashChangeEvent",
    "PopStateEvent",
    "BeforeUnloadEvent",
    
    # WebSocket
    "WebSocket",
    
    # URL & Encoding (Phase 34.5)
    "TextEncoder",
    "TextDecoder",
    "ArrayBuffer",
    "Uint8Array",
    "Int8Array",
    "Uint8ClampedArray",
    "Int16Array",
    "Uint16Array",
    "Int32Array",
    "Uint32Array",
    "Float32Array",
    "Float64Array",
    "BigInt64Array",
    "BigUint64Array",
    "DataView",
    "btoa",
    "atob",
    "File",
    "FileReader",
    
    # Additional Events (Phase 34.4 Final)
    "PromiseRejectionEvent",
    "SecurityPolicyViolationEvent",
    "PageTransitionEvent",
    "ProgressEvent",
    "DeviceMotionEvent",
    "DeviceOrientationEvent",
    
    # XMLHttpRequest
    "XMLHttpRequest",
    
    # Event Supporting Types (Phase 34.4)
    "Touch",
    "TouchList",
    "DataTransfer",
    "DataTransferItem",
    "DataTransferItemList",
    "FileList",
    
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
# DOM Constructors (require 'new' keyword in JavaScript)
# =============================================================================
# These are browser APIs that must be called with 'new' in JavaScript.
# The transpiler checks this set and emits 'new Constructor(...)' instead of
# just 'Constructor(...)'.
#
# WHO: Called by emitter.py when transpiling Call nodes
# WHAT: Distinguishes constructor calls from regular function calls
# WHY: JavaScript requires 'new' for constructors; Python doesn't have this

DOM_CONSTRUCTORS: FrozenSet[str] = frozenset({
    # =========================================================================
    # URL & Encoding APIs (Phase 34.5)
    # =========================================================================
    "URL",
    "URLSearchParams",
    "TextEncoder",
    "TextDecoder",
    
    # =========================================================================
    # Binary Data APIs (Phase 34.5)
    # =========================================================================
    "ArrayBuffer",
    "SharedArrayBuffer",
    "DataView",
    "Blob",
    "File",
    "FileReader",
    
    # TypedArrays
    "Uint8Array",
    "Int8Array",
    "Uint8ClampedArray",
    "Int16Array",
    "Uint16Array",
    "Int32Array",
    "Uint32Array",
    "Float32Array",
    "Float64Array",
    "BigInt64Array",
    "BigUint64Array",
    
    # =========================================================================
    # Fetch/Network APIs
    # =========================================================================
    "Headers",
    "Request",
    "Response",
    "FormData",
    "WebSocket",
    "XMLHttpRequest",
    
    # =========================================================================
    # Event Constructors (Phase 34.4)
    # =========================================================================
    "Event",
    "CustomEvent",
    "MouseEvent",
    "KeyboardEvent",
    "FocusEvent",
    "TouchEvent",
    "WheelEvent",
    "PointerEvent",
    "DragEvent",
    "ClipboardEvent",
    "InputEvent",
    "CompositionEvent",
    "AnimationEvent",
    "TransitionEvent",
    "MessageEvent",
    "ErrorEvent",
    "StorageEvent",
    "PopStateEvent",
    "HashChangeEvent",
    "CloseEvent",
    "UIEvent",
    "SubmitEvent",
    "FormDataEvent",
    "BeforeUnloadEvent",
    "ProgressEvent",
    "PromiseRejectionEvent",
    "SecurityPolicyViolationEvent",
    "PageTransitionEvent",
    "DeviceMotionEvent",
    "DeviceOrientationEvent",
    
    # =========================================================================
    # Observer APIs
    # =========================================================================
    "MutationObserver",
    "IntersectionObserver",
    "ResizeObserver",
    "PerformanceObserver",
    
    # =========================================================================
    # Other Constructors
    # =========================================================================
    "AbortController",
    "Image",
    "Audio",
    "Worker",
    "SharedWorker",
    "BroadcastChannel",
    "MessageChannel",
    "EventSource",
    
    # CSS Typed OM (Phase 34.3)
    "CSSUnitValue",
    "CSSKeywordValue",
    "CSSMathSum",
    "CSSMathProduct",
    "CSSMathMin",
    "CSSMathMax",
    "CSSMathClamp",
    "CSSTransformValue",
    "CSSTranslate",
    "CSSRotate",
    "CSSScale",
    "CSSSkew",
    "CSSPerspective",
    "DOMMatrix",
})


# =============================================================================
# DOM Primitive Properties (always return JS primitives, safe for === comparison)
# =============================================================================
# These properties are guaranteed to return JavaScript primitives (string, number,
# boolean, null). The transpiler uses this to optimize comparisons:
# - url.port !== "" instead of !__py.eq(url.port, "")
#
# WHO: Called by emitter.py when optimizing comparison operators
# WHAT: Identifies properties that return primitives
# WHY: Allows using direct === instead of __py.eq for better performance

DOM_PRIMITIVE_PROPERTIES: FrozenSet[str] = frozenset({
    # =========================================================================
    # URL Properties (all strings)
    # =========================================================================
    "href",
    "protocol",
    "username",
    "password",
    "host",
    "hostname",
    "port",
    "pathname",
    "search",
    "hash",
    "origin",
    
    # =========================================================================
    # Blob/File Properties
    # =========================================================================
    "size",           # number
    "type",           # string (MIME type)
    "name",           # string (File.name)
    "lastModified",   # number (timestamp)
    
    # =========================================================================
    # Element Properties (strings/numbers)
    # =========================================================================
    "id",
    "className",
    "tagName",
    "nodeName",
    "nodeType",       # number
    "innerHTML",
    "outerHTML",
    "textContent",
    "innerText",
    "outerText",
    
    # Dimensions (numbers)
    "offsetWidth",
    "offsetHeight",
    "offsetTop",
    "offsetLeft",
    "clientWidth",
    "clientHeight",
    "clientTop",
    "clientLeft",
    "scrollWidth",
    "scrollHeight",
    "scrollTop",
    "scrollLeft",
    
    # =========================================================================
    # Form Element Properties
    # =========================================================================
    "value",          # string
    "checked",        # boolean
    "disabled",       # boolean
    "readOnly",       # boolean
    "required",       # boolean
    "selected",       # boolean
    "defaultValue",   # string
    "placeholder",    # string
    "maxLength",      # number
    "minLength",      # number
    
    # =========================================================================
    # Common Primitive Properties
    # =========================================================================
    "length",         # number (arrays, strings, collections)
    "byteLength",     # number (ArrayBuffer, TypedArray)
    "byteOffset",     # number (TypedArray, DataView)
    "nodeValue",      # string | null
    "data",           # string (Text, Comment nodes)
    
    # =========================================================================
    # Encoding Properties
    # =========================================================================
    "encoding",       # string (TextEncoder/Decoder)
    "fatal",          # boolean (TextDecoder)
    "ignoreBOM",      # boolean (TextDecoder)
    
    # =========================================================================
    # Event Properties (primitives)
    # =========================================================================
    "bubbles",        # boolean
    "cancelable",     # boolean
    "defaultPrevented",  # boolean
    "isTrusted",      # boolean
    "eventPhase",     # number
    "timeStamp",      # number
    "key",            # string (KeyboardEvent)
    "code",           # string (KeyboardEvent)
    "button",         # number (MouseEvent)
    "buttons",        # number (MouseEvent)
    "clientX",        # number
    "clientY",        # number
    "pageX",          # number
    "pageY",          # number
    "screenX",        # number
    "screenY",        # number
    "offsetX",        # number
    "offsetY",        # number
    "altKey",         # boolean
    "ctrlKey",        # boolean
    "metaKey",        # boolean
    "shiftKey",       # boolean
    "repeat",         # boolean (KeyboardEvent)
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
    # Event Methods (Phase 34.4)
    # =========================================================================
    "addEventListener",
    "removeEventListener",
    "dispatchEvent",
    "preventDefault",
    "stopPropagation",
    "stopImmediatePropagation",
    "composedPath",
    "getModifierState",
    
    # =========================================================================
    # DataTransfer Methods (Phase 34.4)
    # =========================================================================
    "setData",
    "getData",
    "clearData",
    "setDragImage",
    
    # =========================================================================
    # Touch/Pointer Methods (Phase 34.4)
    # =========================================================================
    "getCoalescedEvents",
    "getPredictedEvents",
    "setPointerCapture",
    "releasePointerCapture",
    "hasPointerCapture",
    
    # =========================================================================
    # AbortController Methods (Phase 34.4)
    # =========================================================================
    "abort",
    
    # =========================================================================
    # DataTransferItem Methods (Phase 34.4)
    # =========================================================================
    "getAsString",
    "getAsFile",
    
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
    # el.attributeStyleMap.set(), el.attributeStyleMap.get(), etc.
    # get/set/delete/has/clear are now in URLSearchParams section
    # =========================================================================
    "getAll",
    "computedStyleMap",
    
    # =========================================================================
    # URL & URLSearchParams Methods (Phase 34.5)
    # Note: get/set/delete/has may conflict with dict methods but DOM is primary
    # use case in @client code. Dict operations use __py helpers in practice.
    # =========================================================================
    "toString",
    "toJSON",
    "createObjectURL",
    "revokeObjectURL",
    "append",
    "sort",
    "keys",
    "values",
    "entries",
    "forEach",
    "get",       # URLSearchParams.get(), StylePropertyMap.get()
    "set",       # URLSearchParams.set(), StylePropertyMap.set()
    "delete",    # URLSearchParams.delete(), StylePropertyMap.delete()
    "has",       # URLSearchParams.has(), StylePropertyMap.has()
    "clear",     # StylePropertyMap.clear()
    
    # =========================================================================
    # TextEncoder/Decoder Methods (Phase 34.5)
    # =========================================================================
    "encode",
    "encodeInto",
    "decode",
    
    # =========================================================================
    # TypedArray Methods (Phase 34.5)
    # =========================================================================
    "subarray",
    "fill",
    "copyWithin",
    "reverse",
    "indexOf",
    "lastIndexOf",
    "includes",
    "find",
    "findIndex",
    "every",
    "some",
    "filter",
    "map",
    "reduce",
    "reduceRight",
    "join",
    
    # =========================================================================
    # DataView Methods (Phase 34.5)
    # =========================================================================
    "getInt8",
    "setInt8",
    "getUint8",
    "setUint8",
    "getInt16",
    "setInt16",
    "getUint16",
    "setUint16",
    "getInt32",
    "setInt32",
    "getUint32",
    "setUint32",
    "getFloat32",
    "setFloat32",
    "getFloat64",
    "setFloat64",
    "getBigInt64",
    "setBigInt64",
    "getBigUint64",
    "setBigUint64",
    
    # =========================================================================
    # Blob Methods (Phase 34.5)
    # =========================================================================
    "text",
    "arrayBuffer",
    "stream",
    
    # =========================================================================
    # FileReader Methods (Phase 34.5)
    # =========================================================================
    "readAsText",
    "readAsDataURL",
    "readAsArrayBuffer",
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
    
    # =========================================================================
    # Event Properties (Phase 34.4)
    # =========================================================================
    
    # Event base properties
    "type",               # Event.type (event name)
    "target",             # Event.target (origin element)
    "currentTarget",      # Event.currentTarget (listener element)
    "eventPhase",         # Event.eventPhase
    "bubbles",            # Event.bubbles
    "cancelable",         # Event.cancelable
    "composed",           # Event.composed
    "timeStamp",          # Event.timeStamp
    "isTrusted",          # Event.isTrusted
    "defaultPrevented",   # Event.defaultPrevented
    
    # UIEvent properties
    "view",               # UIEvent.view
    "detail",             # UIEvent.detail, CustomEvent.detail
    
    # MouseEvent position properties
    "clientX",            # MouseEvent.clientX
    "clientY",            # MouseEvent.clientY
    "pageX",              # MouseEvent.pageX
    "pageY",              # MouseEvent.pageY
    "screenX",            # MouseEvent.screenX
    "screenY",            # MouseEvent.screenY
    "offsetX",            # MouseEvent.offsetX
    "offsetY",            # MouseEvent.offsetY
    "movementX",          # MouseEvent.movementX
    "movementY",          # MouseEvent.movementY
    
    # MouseEvent button properties
    "button",             # MouseEvent.button
    "buttons",            # MouseEvent.buttons
    
    # Modifier key properties (shared)
    "altKey",             # MouseEvent, KeyboardEvent, TouchEvent
    "ctrlKey",
    "shiftKey",
    "metaKey",
    
    # MouseEvent other
    "relatedTarget",      # MouseEvent, FocusEvent
    
    # WheelEvent properties
    "deltaX",             # WheelEvent.deltaX
    "deltaY",             # WheelEvent.deltaY
    "deltaZ",             # WheelEvent.deltaZ
    "deltaMode",          # WheelEvent.deltaMode
    
    # KeyboardEvent properties
    "key",                # KeyboardEvent.key
    "code",               # KeyboardEvent.code
    "repeat",             # KeyboardEvent.repeat
    "isComposing",        # KeyboardEvent.isComposing
    "location",           # KeyboardEvent.location
    
    # Touch properties
    "identifier",         # Touch.identifier
    "radiusX",            # Touch.radiusX
    "radiusY",            # Touch.radiusY
    "rotationAngle",      # Touch.rotationAngle
    "force",              # Touch.force
    
    # TouchEvent properties
    "touches",            # TouchEvent.touches
    "changedTouches",     # TouchEvent.changedTouches
    "targetTouches",      # TouchEvent.targetTouches
    
    # DragEvent/DataTransfer properties
    "dataTransfer",       # DragEvent.dataTransfer
    "dropEffect",         # DataTransfer.dropEffect
    "effectAllowed",      # DataTransfer.effectAllowed
    "files",              # DataTransfer.files
    "items",              # DataTransfer.items
    "types",              # DataTransfer.types
    
    # DataTransferItem properties
    "kind",               # DataTransferItem.kind
    
    # InputEvent properties
    "inputType",          # InputEvent.inputType
    
    # PointerEvent properties
    "pointerId",          # PointerEvent.pointerId
    "pointerType",        # PointerEvent.pointerType
    "pressure",           # PointerEvent.pressure
    "tangentialPressure", # PointerEvent.tangentialPressure
    "tiltX",              # PointerEvent.tiltX
    "tiltY",              # PointerEvent.tiltY
    "twist",              # PointerEvent.twist
    "isPrimary",          # PointerEvent.isPrimary
    
    # AnimationEvent properties
    "animationName",      # AnimationEvent.animationName
    "elapsedTime",        # AnimationEvent.elapsedTime, TransitionEvent.elapsedTime
    "pseudoElement",      # AnimationEvent.pseudoElement, TransitionEvent.pseudoElement
    
    # TransitionEvent properties
    "propertyName",       # TransitionEvent.propertyName
    
    # SubmitEvent properties
    "submitter",          # SubmitEvent.submitter
    
    # FormDataEvent properties
    "formData",           # FormDataEvent.formData
    
    # ClipboardEvent properties
    "clipboardData",      # ClipboardEvent.clipboardData
    
    # StorageEvent properties
    "oldValue",           # StorageEvent.oldValue
    "newValue",           # StorageEvent.newValue
    "url",                # StorageEvent.url
    "storageArea",        # StorageEvent.storageArea
    
    # Window/Document event properties
    "innerWidth",         # window.innerWidth
    "innerHeight",        # window.innerHeight
    "scrollTop",          # document.documentElement.scrollTop
    "scrollHeight",       # document.documentElement.scrollHeight
    "visibilityState",    # document.visibilityState (already exists, just noting)
    "returnValue",        # BeforeUnloadEvent.returnValue
    "state",              # PopStateEvent.state
    "hash",               # location.hash (for hashchange)
    
    # Media element properties
    "currentTime",        # HTMLMediaElement.currentTime
    "duration",           # HTMLMediaElement.duration
    "paused",             # HTMLMediaElement.paused
    "volume",             # HTMLMediaElement.volume
    "muted",              # HTMLMediaElement.muted
    "playbackRate",       # HTMLMediaElement.playbackRate
    
    # AbortController/Signal properties
    "signal",             # AbortController.signal
    "aborted",            # AbortSignal.aborted
    "reason",             # AbortSignal.reason
    
    # MessageEvent properties
    "origin",             # MessageEvent.origin
    "source",             # MessageEvent.source
    "ports",              # MessageEvent.ports
    "lastEventId",        # MessageEvent.lastEventId
    
    # ErrorEvent properties
    "message",            # ErrorEvent.message
    "filename",           # ErrorEvent.filename
    "lineno",             # ErrorEvent.lineno
    "colno",              # ErrorEvent.colno
    "error",              # ErrorEvent.error
    
    # HashChangeEvent properties
    "oldURL",             # HashChangeEvent.oldURL
    "newURL",             # HashChangeEvent.newURL
    
    # CloseEvent properties
    "code",               # CloseEvent.code
    "wasClean",           # CloseEvent.wasClean
    
    # WebSocket properties
    "readyState",         # WebSocket.readyState
    "bufferedAmount",     # WebSocket.bufferedAmount
    "extensions",         # WebSocket.extensions
    "protocol",           # WebSocket.protocol
    "binaryType",         # WebSocket.binaryType
    
    # PromiseRejectionEvent properties
    "promise",            # PromiseRejectionEvent.promise
    
    # SecurityPolicyViolationEvent properties
    "violatedDirective",  # CSP directive violated
    "effectiveDirective", # Effective directive
    "blockedURI",         # Blocked resource URI
    "documentURI",        # Document URI
    "originalPolicy",     # Original CSP policy
    "sourceFile",         # Source file
    "lineNumber",         # Line number
    "columnNumber",       # Column number
    "statusCode",         # HTTP status code
    
    # PageTransitionEvent properties
    "persisted",          # PageTransitionEvent.persisted
    
    # ProgressEvent properties
    "lengthComputable",   # ProgressEvent.lengthComputable
    "loaded",             # ProgressEvent.loaded
    "total",              # ProgressEvent.total
    
    # DeviceMotionEvent properties
    "acceleration",       # DeviceMotionEvent.acceleration
    "accelerationIncludingGravity",  # With gravity
    "rotationRate",       # Rotation rate
    "interval",           # Event interval
    
    # DeviceOrientationEvent properties
    "alpha",              # Compass heading
    "beta",               # Front/back tilt
    "gamma",              # Left/right tilt
    "absolute",           # Absolute orientation
    
    # URL properties (Phase 34.5)
    "href",               # URL.href
    "protocol",           # URL.protocol
    "username",           # URL.username
    "password",           # URL.password
    "host",               # URL.host
    "hostname",           # URL.hostname
    "port",               # URL.port
    "pathname",           # URL.pathname
    "search",             # URL.search
    "searchParams",       # URL.searchParams
    "hash",               # URL.hash
    "origin",             # URL.origin
    
    # TextEncoder/Decoder properties (Phase 34.5)
    "encoding",           # TextEncoder.encoding, TextDecoder.encoding
    "fatal",              # TextDecoder.fatal
    "ignoreBOM",          # TextDecoder.ignoreBOM
    
    # ArrayBuffer/TypedArray properties (Phase 34.5)
    "byteLength",         # ArrayBuffer.byteLength
    "byteOffset",         # TypedArray.byteOffset
    "buffer",             # TypedArray.buffer
    "BYTES_PER_ELEMENT",  # TypedArray.BYTES_PER_ELEMENT
    
    # Blob/File properties (Phase 34.5)
    "size",               # Blob.size
    "name",               # File.name
    "lastModified",       # File.lastModified
    
    # FileReader properties (Phase 34.5)
    "result",             # FileReader.result
    "readyState",         # FileReader.readyState
    "onload",             # FileReader.onload
    "onerror",            # FileReader.onerror
    "onabort",            # FileReader.onabort
    "onloadstart",        # FileReader.onloadstart
    "onloadend",          # FileReader.onloadend
    "onprogress",         # FileReader.onprogress
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
# DOM Type Methods Registry (Phase 34.5+)
# =============================================================================
#
# Maps DOM constructor types to their methods that should passthrough.
# This enables type-aware method dispatch: when we know a variable was
# constructed from a DOM type, we emit direct method calls instead of
# wrapping with __py.* helpers.
#
# Example:
#   encoder = TextEncoder()      # scope tracks: encoder -> "TextEncoder"
#   encoder.encode("Hello")      # checks DOM_TYPE_METHODS["TextEncoder"]
#                                # "encode" is there -> emit: encoder.encode("Hello")
#
# Without this, encode() would become __py.str.encode(encoder, "Hello")
#
# =============================================================================

# Shared methods for all TypedArray types
_TYPED_ARRAY_METHODS: FrozenSet[str] = frozenset({
    "subarray", "slice", "set", "copyWithin", "fill", "reverse",
    "sort", "indexOf", "lastIndexOf", "includes", "find", "findIndex",
    "every", "some", "filter", "map", "reduce", "reduceRight", 
    "join", "forEach", "entries", "keys", "values", "at", "toReversed",
    "toSorted", "with_", "findLast", "findLastIndex",
})

DOM_TYPE_METHODS: dict[str, FrozenSet[str]] = {
    # =========================================================================
    # Encoding APIs (Phase 34.5)
    # =========================================================================
    "TextEncoder": frozenset({"encode", "encodeInto"}),
    "TextDecoder": frozenset({"decode"}),
    
    # =========================================================================
    # URL APIs (Phase 34.5)
    # =========================================================================
    "URL": frozenset({"toString", "toJSON"}),
    "URLSearchParams": frozenset({
        "get", "getAll", "set", "append", "delete", "has",
        "sort", "keys", "values", "entries", "forEach", "toString",
    }),
    
    # =========================================================================
    # Binary Data APIs (Phase 34.5)
    # =========================================================================
    "Blob": frozenset({"slice", "text", "arrayBuffer", "stream"}),
    "File": frozenset({"slice", "text", "arrayBuffer", "stream"}),
    "FileReader": frozenset({
        "readAsText", "readAsDataURL", "readAsArrayBuffer", "readAsBinaryString", "abort",
    }),
    "ArrayBuffer": frozenset({"slice", "transfer", "resize"}),
    "DataView": frozenset({
        "getInt8", "setInt8", "getUint8", "setUint8",
        "getInt16", "setInt16", "getUint16", "setUint16",
        "getInt32", "setInt32", "getUint32", "setUint32",
        "getFloat32", "setFloat32", "getFloat64", "setFloat64",
        "getBigInt64", "setBigInt64", "getBigUint64", "setBigUint64",
    }),
    
    # =========================================================================
    # TypedArrays (Phase 34.5) - All share same methods
    # =========================================================================
    "Uint8Array": _TYPED_ARRAY_METHODS,
    "Int8Array": _TYPED_ARRAY_METHODS,
    "Uint8ClampedArray": _TYPED_ARRAY_METHODS,
    "Int16Array": _TYPED_ARRAY_METHODS,
    "Uint16Array": _TYPED_ARRAY_METHODS,
    "Int32Array": _TYPED_ARRAY_METHODS,
    "Uint32Array": _TYPED_ARRAY_METHODS,
    "Float32Array": _TYPED_ARRAY_METHODS,
    "Float64Array": _TYPED_ARRAY_METHODS,
    "BigInt64Array": _TYPED_ARRAY_METHODS,
    "BigUint64Array": _TYPED_ARRAY_METHODS,
    
    # =========================================================================
    # WebSocket (Phase 34.4)
    # =========================================================================
    "WebSocket": frozenset({"send", "close"}),
    
    # =========================================================================
    # AbortController (Phase 34.4)
    # =========================================================================
    "AbortController": frozenset({"abort"}),
    
    # =========================================================================
    # FormData (Phase 34.5)
    # =========================================================================
    "FormData": frozenset({
        "get", "getAll", "set", "append", "delete", "has",
        "keys", "values", "entries", "forEach",
    }),
    
    # =========================================================================
    # Headers (Fetch API)
    # =========================================================================
    "Headers": frozenset({
        "get", "set", "append", "delete", "has",
        "keys", "values", "entries", "forEach",
    }),
}


def is_dom_type_method(constructor: str, method: str) -> bool:
    """
    Check if a method should passthrough for a given DOM constructor type.
    
    This enables type-aware method dispatch. When we know a variable's type
    from its constructor, we can emit direct method calls instead of
    wrapping with __py.* helpers.
    
    Args:
        constructor: The DOM constructor name (e.g., "TextEncoder", "URLSearchParams")
        method: The method name being called
    
    Returns:
        True if this method should passthrough for this type
    
    Example:
        is_dom_type_method("TextEncoder", "encode")      # True
        is_dom_type_method("TextEncoder", "toString")    # False (not in set)
        is_dom_type_method("URLSearchParams", "get")     # True
        is_dom_type_method("dict", "get")                # False (not a DOM type)
    """
    type_methods = DOM_TYPE_METHODS.get(constructor)
    if type_methods is None:
        return False
    return method in type_methods


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


def is_dom_constructor(name: str) -> bool:
    """
    Check if a name is a DOM constructor that requires 'new' keyword.
    
    Args:
        name: The constructor name
    
    Returns:
        True if this is a DOM constructor that should be called with 'new'
    
    Example:
        is_dom_constructor("URL")           # True
        is_dom_constructor("Blob")          # True
        is_dom_constructor("document")      # False (not a constructor)
        is_dom_constructor("MyClass")       # False (user-defined)
    """
    return name in DOM_CONSTRUCTORS


def is_dom_primitive_property(name: str) -> bool:
    """
    Check if a property name returns a JavaScript primitive.
    
    Args:
        name: The property name
    
    Returns:
        True if this property always returns a primitive (string, number, boolean)
    
    Example:
        is_dom_primitive_property("port")       # True (string)
        is_dom_primitive_property("length")     # True (number)
        is_dom_primitive_property("checked")    # True (boolean)
        is_dom_primitive_property("children")   # False (returns NodeList)
    """
    return name in DOM_PRIMITIVE_PROPERTIES


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
    "DOM_CONSTRUCTORS",
    "DOM_PRIMITIVE_PROPERTIES",
    "DOM_METHODS",
    "DOM_PROPERTIES",
    "DOM_TYPE_ONLY_IMPORTS",
    "DOM_TYPE_METHODS",
    
    # Helper functions
    "is_dom_global",
    "is_dom_method",
    "is_dom_property",
    "is_dom_passthrough",
    "is_dom_type_import",
    "is_dom_type_method",
    "should_skip_import",
    "is_dom_constructor",
    "is_dom_primitive_property",
]

