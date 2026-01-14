"""
PyNext Client - Client-Side Utilities

=============================================================================
WHAT THIS MODULE DOES
=============================================================================

Provides client-side utilities for PyNext applications including:
- DOM APIs (document, Element, Node, etc.)
- Type checking (@typed decorator)
- Promise utilities
- Scheduling APIs

=============================================================================
WHY THIS EXISTS
=============================================================================

Client-side Python code needs access to browser APIs in a Pythonic way.
This module provides the Python interface that transpiles to JavaScript.

=============================================================================
HOW IT WORKS
=============================================================================

- DOM APIs are passthrough - they transpile 1:1 to JavaScript
- Type checking is optional and can be stripped in production
- All APIs are fully typed for IDE autocompletion

=============================================================================
WHO USES THIS
=============================================================================

- Web developers writing client-side Python code
- Code decorated with @client
- Transpiled JavaScript code in the browser

=============================================================================
EXAMPLES
=============================================================================

    from pynext.client import document, Element
    
    # Query and manipulate DOM
    app = document.getElementById("app")
    app.innerHTML = "<h1>Hello, World!</h1>"
    
    # Create elements
    div = document.createElement("div")
    div.classList.add("container")
    document.body.appendChild(div)
    
    # Type-checked functions
    from pynext.client import typed
    
    @typed
    def greet(name: str) -> str:
        return f"Hello, {name}"
"""

# Type checking utilities
from pynext.client.typed import typed, enable_type_checking, is_type_checking_enabled

# DOM types - full type stubs for DOM manipulation
from pynext.client.dom import (
    # Main interfaces
    Document,
    Element,
    # Supporting types
    CSSStyleDeclaration,
    DOMRect,
    # Global instance
    document,
)

# Node types
from pynext.client.node import (
    # Base node
    Node,
    Text,
    Comment,
    DocumentFragment,
    # Collections
    NodeList,
    HTMLCollection,
    DOMStringMap,
    DOMTokenList,
    NamedNodeMap,
    Attr,
    # Node type constants
    ELEMENT_NODE,
    TEXT_NODE,
    COMMENT_NODE,
    DOCUMENT_NODE,
    DOCUMENT_FRAGMENT_NODE,
)

# Window interface (Phase 34.2)
from pynext.client.window import (
    Window,
    window,
    MediaQueryList,
)

# Pythonic style utilities (Phase 34.2)
from pynext.client.styles import (
    StylesProxy,
    create_styles,
)

from pynext.client.css_vars import (
    set_css_var,
    get_css_var,
    remove_css_var,
    set_theme,
    get_theme,
    toggle_theme,
)

from pynext.client.style_utils import (
    classes,
    set_styles,
    toggle_class,
    add_classes,
    remove_classes,
    has_class,
    replace_class,
    clear_styles,
    get_style,
)

# Web Animations API (Phase 34.2)
from pynext.client.animation import (
    Animation,
    AnimationOptions,
    KeyframeEffect,
    fade_in,
    fade_out,
    slide_in,
    slide_out,
    scale_in,
    scale_out,
    shake,
    pulse,
)

# CSS Typed Object Model (Phase 34.3)
from pynext.client.typed_om import (
    # Factory namespace
    CSS,
    # Base types
    CSSStyleValue,
    CSSNumericValue,
    CSSUnitValue,
    CSSKeywordValue,
    CSSUnparsedValue,
    CSSVariableReferenceValue,
    # Math types
    CSSMathValue,
    CSSMathSum,
    CSSMathProduct,
    CSSMathMin,
    CSSMathMax,
    CSSMathClamp,
    # Transform types
    CSSTransformComponent,
    CSSTranslate,
    CSSRotate,
    CSSScale,
    CSSSkew,
    CSSPerspective,
    CSSMatrixComponent,
    CSSTransformValue,
    # Image types
    CSSImageValue,
    CSSURLImageValue,
    CSSLinearGradient,
    CSSRadialGradient,
    CSSConicGradient,
    # Matrix
    DOMMatrix,
    # Style maps
    StylePropertyMapReadOnly,
    StylePropertyMap,
)

from pynext.client.css_color import (
    CSSColor,
)

# Events (Phase 34.4)
from pynext.client.events import (
    # Base events
    Event,
    UIEvent,
    
    # Mouse events
    MouseEvent,
    WheelEvent,
    PointerEvent,
    
    # Keyboard events
    KeyboardEvent,
    
    # Touch events
    Touch,
    TouchList,
    TouchEvent,
    
    # Drag events
    DataTransfer,
    DataTransferItem,
    DataTransferItemList,
    FileList,
    DragEvent,
    
    # Focus events
    FocusEvent,
    
    # Input events
    InputEvent,
    
    # Custom events
    CustomEvent,
    
    # Animation events
    AnimationEvent,
    TransitionEvent,
    
    # Form events
    SubmitEvent,
    FormDataEvent,
    
    # Clipboard events
    ClipboardEvent,
    
    # Composition events
    CompositionEvent,
    
    # Storage events
    StorageEvent,
    
    # Message events
    MessageEvent,
    
    # Error events
    ErrorEvent,
    
    # WebSocket close events
    CloseEvent,
    
    # History events
    HashChangeEvent,
    PopStateEvent,
    BeforeUnloadEvent,
    
    # Promise rejection events
    PromiseRejectionEvent,
    
    # Security events
    SecurityPolicyViolationEvent,
    
    # Page transition events
    PageTransitionEvent,
    
    # Progress events
    ProgressEvent,
    
    # Device motion events
    DeviceMotionEvent,
    DeviceOrientationEvent,
)

# URL API (Phase 34.5)
from pynext.client.url import (
    URL,
    URLSearchParams,
)

# Encoding API (Phase 34.5)
from pynext.client.encoding import (
    TextEncoder,
    TextDecoder,
    btoa,
    atob,
)

# Binary Data API (Phase 34.5)
from pynext.client.binary import (
    ArrayBuffer,
    Uint8Array,
    Int8Array,
    Uint8ClampedArray,
    Int16Array,
    Uint16Array,
    Int32Array,
    Uint32Array,
    Float32Array,
    Float64Array,
    BigInt64Array,
    BigUint64Array,
    DataView,
    Blob,
    File,
    FileReader,
)

__all__ = [
    # Type checking
    "typed",
    "enable_type_checking",
    "is_type_checking_enabled",
    
    # DOM interfaces
    "Document",
    "Element",
    "document",
    "CSSStyleDeclaration",
    "DOMRect",
    
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
    "TEXT_NODE",
    "COMMENT_NODE",
    "DOCUMENT_NODE",
    "DOCUMENT_FRAGMENT_NODE",
    
    # Window interface (Phase 34.2)
    "Window",
    "window",
    "MediaQueryList",
    
    # Pythonic style utilities (Phase 34.2)
    "StylesProxy",
    "create_styles",
    "set_css_var",
    "get_css_var",
    "remove_css_var",
    "set_theme",
    "get_theme",
    "toggle_theme",
    "classes",
    "set_styles",
    "toggle_class",
    "add_classes",
    "remove_classes",
    "has_class",
    "replace_class",
    "clear_styles",
    "get_style",
    
    # Web Animations API (Phase 34.2)
    "Animation",
    "AnimationOptions",
    "KeyframeEffect",
    "fade_in",
    "fade_out",
    "slide_in",
    "slide_out",
    "scale_in",
    "scale_out",
    "shake",
    "pulse",
    
    # CSS Typed Object Model (Phase 34.3)
    "CSS",
    "CSSStyleValue",
    "CSSNumericValue",
    "CSSUnitValue",
    "CSSKeywordValue",
    "CSSUnparsedValue",
    "CSSVariableReferenceValue",
    "CSSMathValue",
    "CSSMathSum",
    "CSSMathProduct",
    "CSSMathMin",
    "CSSMathMax",
    "CSSMathClamp",
    "CSSTransformComponent",
    "CSSTranslate",
    "CSSRotate",
    "CSSScale",
    "CSSSkew",
    "CSSPerspective",
    "CSSMatrixComponent",
    "CSSTransformValue",
    "CSSImageValue",
    "CSSURLImageValue",
    "CSSLinearGradient",
    "CSSRadialGradient",
    "CSSConicGradient",
    "DOMMatrix",
    "StylePropertyMapReadOnly",
    "StylePropertyMap",
    "CSSColor",
    
    # Events (Phase 34.4)
    "Event",
    "UIEvent",
    "MouseEvent",
    "WheelEvent",
    "PointerEvent",
    "KeyboardEvent",
    "Touch",
    "TouchList",
    "TouchEvent",
    "DataTransfer",
    "DataTransferItem",
    "DataTransferItemList",
    "FileList",
    "DragEvent",
    "FocusEvent",
    "InputEvent",
    "CustomEvent",
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
    "PromiseRejectionEvent",
    "SecurityPolicyViolationEvent",
    "PageTransitionEvent",
    "ProgressEvent",
    "DeviceMotionEvent",
    "DeviceOrientationEvent",
    
    # URL API (Phase 34.5)
    "URL",
    "URLSearchParams",
    
    # Encoding API (Phase 34.5)
    "TextEncoder",
    "TextDecoder",
    "btoa",
    "atob",
    
    # Binary Data API (Phase 34.5)
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
    "Blob",
    "File",
    "FileReader",
]

