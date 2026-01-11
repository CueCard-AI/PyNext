"""
PyNext Client - DOM Event Types

=============================================================================
WHAT THIS FILE DOES
=============================================================================

Provides comprehensive Python type stubs for all DOM Event interfaces.
These types enable IDE autocompletion, type checking, and documentation
for event handling code that transpiles to JavaScript.

=============================================================================
WHY THIS EXISTS
=============================================================================

DOM events are the primary mechanism for user interaction in web apps.
This module provides:
- Full type hints for 15+ event types
- IDE autocompletion for all event properties
- Documentation with who/what/when/where/why/how
- Zero runtime overhead - pure passthrough transpilation

=============================================================================
HOW IT WORKS
=============================================================================

These are type stubs that:
1. Define Python APIs that mirror JavaScript Event APIs exactly
2. Provide type information for static analysis
3. Transpile to identical JavaScript (passthrough - no transformation)

The key insight: Event APIs are identical in Python and JavaScript syntax.
`event.preventDefault()` in Python becomes `event.preventDefault()` in JS.

=============================================================================
WHO USES THIS
=============================================================================

- Web developers handling user interactions
- The transpiler for passthrough detection
- IDEs for autocompletion and type checking
- LLMs for understanding and generating code

=============================================================================
EXAMPLES
=============================================================================

    from pynext.client import document, MouseEvent, KeyboardEvent
    
    def on_click(event: MouseEvent):
        x = event.clientX
        y = event.clientY
        if event.ctrlKey:
            event.preventDefault()
    
    def on_keydown(event: KeyboardEvent):
        if event.key == "Enter":
            submit_form()
        elif event.key == "Escape":
            close_modal()
    
    el.addEventListener("click", on_click)
    el.addEventListener("keydown", on_keydown)
"""

from __future__ import annotations
from typing import (
    Any,
    Iterator,
    List,
    Optional,
    Union,
    TYPE_CHECKING,
)

if TYPE_CHECKING:
    from pynext.client.dom import Element


# =============================================================================
# Event Base Class
# =============================================================================

class Event:
    """
    WHO: Developers handling DOM events
    WHAT: Base class for all DOM event types
    WHEN: Triggered by user interaction or programmatic dispatch
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Type-safe event handling with IDE autocompletion
    HOW: Zero-runtime passthrough - Python code = JavaScript code
    
    The Event interface represents any event which takes place in the DOM.
    All other event interfaces inherit from this base class.
    
    Example:
        def handler(event: Event):
            print(event.type)      # "click", "keydown", etc.
            print(event.target)    # Element that triggered event
            event.preventDefault() # Cancel default action
    """
    
    # =========================================================================
    # Read-only Properties
    # =========================================================================
    
    @property
    def type(self) -> str:
        """
        The name of the event (case-insensitive).
        
        Examples: "click", "keydown", "submit", "custom-event"
        """
        ...
    
    @property
    def target(self) -> Element:
        """
        The element that triggered the event.
        
        This is the element where the event originated, not necessarily
        the element with the event listener attached.
        """
        ...
    
    @property
    def currentTarget(self) -> Element:
        """
        The element with the event listener attached.
        
        During event bubbling/capturing, this is the element currently
        handling the event (the one with addEventListener).
        """
        ...
    
    @property
    def eventPhase(self) -> int:
        """
        The phase of event flow being processed.
        
        Values:
            0 - Event.NONE (not being dispatched)
            1 - Event.CAPTURING_PHASE
            2 - Event.AT_TARGET
            3 - Event.BUBBLING_PHASE
        """
        ...
    
    @property
    def bubbles(self) -> bool:
        """
        Whether the event bubbles up through the DOM.
        
        If True, the event will propagate from target to ancestors.
        """
        ...
    
    @property
    def cancelable(self) -> bool:
        """
        Whether the event can be cancelled.
        
        If True, preventDefault() will have an effect.
        """
        ...
    
    @property
    def composed(self) -> bool:
        """
        Whether the event crosses shadow DOM boundary.
        
        If True, the event will propagate across shadow DOM boundaries.
        """
        ...
    
    @property
    def timeStamp(self) -> float:
        """
        Time when the event was created (milliseconds since epoch).
        
        Use for measuring time between events or animations.
        """
        ...
    
    @property
    def isTrusted(self) -> bool:
        """
        Whether the event was generated by user action.
        
        True for user-initiated events (click, keypress).
        False for programmatic events (dispatchEvent).
        """
        ...
    
    @property
    def defaultPrevented(self) -> bool:
        """
        Whether preventDefault() was called on this event.
        
        Check this to see if the default action has been cancelled.
        """
        ...
    
    # =========================================================================
    # Methods
    # =========================================================================
    
    def preventDefault(self) -> None:
        """
        Cancel the default action associated with this event.
        
        Only works if cancelable is True. Common uses:
        - Prevent form submission
        - Stop link navigation
        - Block context menu
        
        Example:
            def on_submit(event: Event):
                event.preventDefault()  # Handle form ourselves
                submit_via_ajax()
        """
        ...
    
    def stopPropagation(self) -> None:
        """
        Stop the event from bubbling to parent elements.
        
        The event will not trigger handlers on ancestor elements.
        Other handlers on the current element still run.
        
        Example:
            def inner_click(event: Event):
                event.stopPropagation()  # Don't trigger parent's click
        """
        ...
    
    def stopImmediatePropagation(self) -> None:
        """
        Stop event propagation and prevent other handlers on same element.
        
        Like stopPropagation(), but also prevents other handlers
        registered on the same element from running.
        """
        ...
    
    def composedPath(self) -> List[Element]:
        """
        Get the path of elements the event will propagate through.
        
        Returns:
            List of elements from target to window
        """
        ...
    
    # =========================================================================
    # Constructor
    # =========================================================================
    
    def __init__(
        self,
        type: str,
        options: Optional[dict] = None
    ) -> None:
        """
        Create a new Event.
        
        Args:
            type: Event type name
            options: Optional dict with bubbles, cancelable, composed
        
        Example:
            event = Event("custom-event", {"bubbles": True})
            element.dispatchEvent(event)
        """
        ...


# =============================================================================
# UIEvent - Base for UI Events
# =============================================================================

class UIEvent(Event):
    """
    Base class for UI events (mouse, keyboard, touch).
    
    Provides access to the Window object and detail count.
    """
    
    @property
    def view(self) -> Any:
        """The Window object where the event occurred."""
        ...
    
    @property
    def detail(self) -> int:
        """
        Event-specific detail value.
        
        For click events: click count (1 for single, 2 for double).
        For other events: usually 0.
        """
        ...


# =============================================================================
# MouseEvent - Mouse and Pointer Events
# =============================================================================

class MouseEvent(UIEvent):
    """
    WHO: Developers handling mouse interactions
    WHAT: Events for mouse clicks, movement, and buttons
    WHEN: User interacts with mouse/trackpad/pointer
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Type-safe mouse event handling
    HOW: Zero-runtime passthrough
    
    Covers: click, dblclick, mousedown, mouseup, mousemove,
            mouseenter, mouseleave, mouseover, mouseout, contextmenu
    
    Example:
        def on_click(event: MouseEvent):
            # Get click position
            x = event.clientX  # Viewport coordinates
            y = event.clientY
            
            # Check modifiers
            if event.ctrlKey:
                handle_ctrl_click()
            
            # Check button
            if event.button == 2:
                handle_right_click()
    """
    
    # =========================================================================
    # Position Properties
    # =========================================================================
    
    @property
    def clientX(self) -> float:
        """
        X coordinate relative to the viewport (visible area).
        
        Does not include scroll offset.
        """
        ...
    
    @property
    def clientY(self) -> float:
        """
        Y coordinate relative to the viewport (visible area).
        
        Does not include scroll offset.
        """
        ...
    
    @property
    def pageX(self) -> float:
        """
        X coordinate relative to the whole document.
        
        Includes scroll offset (clientX + scrollX).
        """
        ...
    
    @property
    def pageY(self) -> float:
        """
        Y coordinate relative to the whole document.
        
        Includes scroll offset (clientY + scrollY).
        """
        ...
    
    @property
    def screenX(self) -> float:
        """
        X coordinate relative to the screen.
        
        Position on the physical screen, not the browser window.
        """
        ...
    
    @property
    def screenY(self) -> float:
        """
        Y coordinate relative to the screen.
        
        Position on the physical screen, not the browser window.
        """
        ...
    
    @property
    def offsetX(self) -> float:
        """
        X coordinate relative to the target element.
        
        Position within the element that received the event.
        """
        ...
    
    @property
    def offsetY(self) -> float:
        """
        Y coordinate relative to the target element.
        
        Position within the element that received the event.
        """
        ...
    
    @property
    def movementX(self) -> float:
        """
        X movement since last mousemove event.
        
        Useful for drag operations and pointer lock.
        """
        ...
    
    @property
    def movementY(self) -> float:
        """
        Y movement since last mousemove event.
        
        Useful for drag operations and pointer lock.
        """
        ...
    
    # =========================================================================
    # Button Properties
    # =========================================================================
    
    @property
    def button(self) -> int:
        """
        Which button was pressed (for mousedown/mouseup).
        
        Values:
            0 - Primary (usually left)
            1 - Auxiliary (usually middle/wheel)
            2 - Secondary (usually right)
            3 - Fourth (usually back)
            4 - Fifth (usually forward)
        """
        ...
    
    @property
    def buttons(self) -> int:
        """
        Bitmask of currently pressed buttons.
        
        Values (can be combined):
            1 - Primary
            2 - Secondary
            4 - Auxiliary
            8 - Fourth
            16 - Fifth
        
        Example:
            if event.buttons & 1:  # Primary pressed
            if event.buttons & 2:  # Secondary pressed
        """
        ...
    
    # =========================================================================
    # Modifier Key Properties
    # =========================================================================
    
    @property
    def altKey(self) -> bool:
        """Whether Alt key was pressed during event."""
        ...
    
    @property
    def ctrlKey(self) -> bool:
        """Whether Ctrl key was pressed during event."""
        ...
    
    @property
    def shiftKey(self) -> bool:
        """Whether Shift key was pressed during event."""
        ...
    
    @property
    def metaKey(self) -> bool:
        """Whether Meta key (Cmd on Mac, Win on Windows) was pressed."""
        ...
    
    # =========================================================================
    # Related Element
    # =========================================================================
    
    @property
    def relatedTarget(self) -> Optional[Element]:
        """
        Secondary element involved in the event.
        
        For mouseenter/mouseover: element mouse came from
        For mouseleave/mouseout: element mouse went to
        """
        ...
    
    # =========================================================================
    # Methods
    # =========================================================================
    
    def getModifierState(self, key: str) -> bool:
        """
        Check if a modifier key was pressed.
        
        Args:
            key: Modifier name ("Alt", "Control", "Shift", "Meta", 
                 "CapsLock", "NumLock", etc.)
        
        Returns:
            True if the modifier was active
        
        Example:
            if event.getModifierState("CapsLock"):
                warn_caps_lock()
        """
        ...


# =============================================================================
# WheelEvent - Mouse Wheel Events
# =============================================================================

class WheelEvent(MouseEvent):
    """
    WHO: Developers handling scroll wheel interactions
    WHAT: Events for mouse wheel/trackpad scrolling
    WHEN: User scrolls with wheel or trackpad
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Type-safe wheel event handling
    HOW: Zero-runtime passthrough
    
    Example:
        def on_wheel(event: WheelEvent):
            if event.deltaY > 0:
                zoom_out()
            else:
                zoom_in()
    """
    
    @property
    def deltaX(self) -> float:
        """Horizontal scroll amount."""
        ...
    
    @property
    def deltaY(self) -> float:
        """Vertical scroll amount."""
        ...
    
    @property
    def deltaZ(self) -> float:
        """Z-axis scroll amount (rare)."""
        ...
    
    @property
    def deltaMode(self) -> int:
        """
        Unit of delta values.
        
        Values:
            0 - WheelEvent.DOM_DELTA_PIXEL
            1 - WheelEvent.DOM_DELTA_LINE
            2 - WheelEvent.DOM_DELTA_PAGE
        """
        ...


# =============================================================================
# KeyboardEvent - Keyboard Events
# =============================================================================

class KeyboardEvent(UIEvent):
    """
    WHO: Developers handling keyboard input
    WHAT: Events for key presses and releases
    WHEN: User interacts with keyboard
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Type-safe keyboard event handling
    HOW: Zero-runtime passthrough
    
    Covers: keydown, keyup, keypress (deprecated)
    
    Example:
        def on_keydown(event: KeyboardEvent):
            # Check specific key
            if event.key == "Enter":
                submit_form()
            elif event.key == "Escape":
                close_modal()
            
            # Check key with modifier
            if event.ctrlKey and event.key == "s":
                event.preventDefault()
                save_document()
    """
    
    # =========================================================================
    # Key Identification
    # =========================================================================
    
    @property
    def key(self) -> str:
        """
        The key value (what the key represents).
        
        Examples:
            - "a", "A" (letter keys, case-sensitive)
            - "Enter", "Escape", "Tab", "Backspace"
            - "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"
            - "Control", "Alt", "Shift", "Meta"
            - " " (space), "1", "!", etc.
        """
        ...
    
    @property
    def code(self) -> str:
        """
        The physical key code (keyboard layout independent).
        
        Examples:
            - "KeyA", "KeyZ" (letter keys)
            - "Digit1", "Digit0" (number row)
            - "Enter", "Escape", "Space"
            - "ArrowUp", "ArrowDown"
            - "ShiftLeft", "ShiftRight"
        
        Useful for keyboard shortcuts that should work
        regardless of keyboard layout.
        """
        ...
    
    @property
    def repeat(self) -> bool:
        """
        Whether this event is from a held key.
        
        True if the key is being held down and auto-repeating.
        """
        ...
    
    @property
    def isComposing(self) -> bool:
        """
        Whether an IME composition session is in progress.
        
        True during input method composition (e.g., typing
        Chinese, Japanese, Korean characters).
        """
        ...
    
    @property
    def location(self) -> int:
        """
        Location of the key on the keyboard.
        
        Values:
            0 - DOM_KEY_LOCATION_STANDARD
            1 - DOM_KEY_LOCATION_LEFT (left Shift, Ctrl, Alt)
            2 - DOM_KEY_LOCATION_RIGHT (right Shift, Ctrl, Alt)
            3 - DOM_KEY_LOCATION_NUMPAD (numeric keypad)
        """
        ...
    
    # =========================================================================
    # Modifier Key Properties
    # =========================================================================
    
    @property
    def altKey(self) -> bool:
        """Whether Alt key was pressed."""
        ...
    
    @property
    def ctrlKey(self) -> bool:
        """Whether Ctrl key was pressed."""
        ...
    
    @property
    def shiftKey(self) -> bool:
        """Whether Shift key was pressed."""
        ...
    
    @property
    def metaKey(self) -> bool:
        """Whether Meta key (Cmd/Win) was pressed."""
        ...
    
    # =========================================================================
    # Methods
    # =========================================================================
    
    def getModifierState(self, key: str) -> bool:
        """
        Check if a modifier key was pressed.
        
        Args:
            key: Modifier name ("Alt", "Control", "Shift", "Meta",
                 "CapsLock", "NumLock", "ScrollLock")
        
        Returns:
            True if the modifier was active
        """
        ...


# =============================================================================
# Touch Types
# =============================================================================

class Touch:
    """
    WHO: Developers handling touch interactions
    WHAT: Individual touch point in a multi-touch event
    WHEN: User touches the screen
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Access individual touch point data
    HOW: Zero-runtime passthrough
    
    Example:
        for touch in event.touches:
            x = touch.clientX
            y = touch.clientY
            id = touch.identifier
    """
    
    @property
    def identifier(self) -> int:
        """
        Unique identifier for this touch point.
        
        Remains consistent throughout the touch session.
        Use to track the same finger across events.
        """
        ...
    
    @property
    def target(self) -> Element:
        """Element where the touch originated."""
        ...
    
    @property
    def clientX(self) -> float:
        """X coordinate relative to viewport."""
        ...
    
    @property
    def clientY(self) -> float:
        """Y coordinate relative to viewport."""
        ...
    
    @property
    def pageX(self) -> float:
        """X coordinate relative to document."""
        ...
    
    @property
    def pageY(self) -> float:
        """Y coordinate relative to document."""
        ...
    
    @property
    def screenX(self) -> float:
        """X coordinate relative to screen."""
        ...
    
    @property
    def screenY(self) -> float:
        """Y coordinate relative to screen."""
        ...
    
    @property
    def radiusX(self) -> float:
        """X radius of touch contact area."""
        ...
    
    @property
    def radiusY(self) -> float:
        """Y radius of touch contact area."""
        ...
    
    @property
    def rotationAngle(self) -> float:
        """Rotation angle of the touch ellipse (0-90 degrees)."""
        ...
    
    @property
    def force(self) -> float:
        """
        Pressure of the touch (0.0 to 1.0).
        
        0.0 = no pressure detectable
        1.0 = maximum pressure
        """
        ...


class TouchList:
    """
    WHO: Developers handling multi-touch
    WHAT: Collection of Touch objects
    WHEN: Accessing touch points from TouchEvent
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Iterate over multiple touch points
    HOW: Zero-runtime passthrough
    
    Example:
        for i in range(event.touches.length):
            touch = event.touches.item(i)
            print(touch.clientX, touch.clientY)
        
        # Or use Python iteration
        for touch in event.touches:
            print(touch.identifier)
    """
    
    @property
    def length(self) -> int:
        """Number of touch points in the list."""
        ...
    
    def item(self, index: int) -> Optional[Touch]:
        """
        Get touch at index.
        
        Args:
            index: Zero-based index
        
        Returns:
            Touch at index, or None if out of bounds
        """
        ...
    
    def __getitem__(self, index: int) -> Touch:
        """Access touch by index: touches[0]"""
        ...
    
    def __iter__(self) -> Iterator[Touch]:
        """Iterate over touches: for touch in touches"""
        ...
    
    def __len__(self) -> int:
        """Get length: len(touches)"""
        ...


class TouchEvent(UIEvent):
    """
    WHO: Developers building touch interfaces
    WHAT: Events for touch screen interactions
    WHEN: User touches, moves, or lifts finger on screen
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Type-safe touch event handling
    HOW: Zero-runtime passthrough
    
    Covers: touchstart, touchmove, touchend, touchcancel
    
    Example:
        def on_touch_start(event: TouchEvent):
            # Get first touch
            if event.touches.length > 0:
                touch = event.touches[0]
                start_x = touch.clientX
                start_y = touch.clientY
        
        def on_touch_move(event: TouchEvent):
            # Track movement
            for touch in event.changedTouches:
                update_position(touch.identifier, touch.clientX, touch.clientY)
    """
    
    @property
    def touches(self) -> TouchList:
        """
        All active touch points on the screen.
        
        Includes all fingers currently touching, regardless of target.
        """
        ...
    
    @property
    def changedTouches(self) -> TouchList:
        """
        Touch points that changed in this event.
        
        For touchstart: new touches
        For touchmove: moved touches
        For touchend: removed touches
        """
        ...
    
    @property
    def targetTouches(self) -> TouchList:
        """
        Active touches on the event target element.
        
        Subset of touches that started on the target element.
        """
        ...
    
    @property
    def altKey(self) -> bool:
        """Whether Alt key was pressed."""
        ...
    
    @property
    def ctrlKey(self) -> bool:
        """Whether Ctrl key was pressed."""
        ...
    
    @property
    def shiftKey(self) -> bool:
        """Whether Shift key was pressed."""
        ...
    
    @property
    def metaKey(self) -> bool:
        """Whether Meta key was pressed."""
        ...


# =============================================================================
# Drag and Drop Types
# =============================================================================

class DataTransferItem:
    """
    Individual item in a drag operation.
    
    Represents one piece of data being dragged (text, file, etc.).
    """
    
    @property
    def kind(self) -> str:
        """Type of item: "string" or "file"."""
        ...
    
    @property
    def type(self) -> str:
        """MIME type of the item."""
        ...
    
    def getAsString(self, callback: Any) -> None:
        """Get string data asynchronously."""
        ...
    
    def getAsFile(self) -> Optional[Any]:
        """Get as File object (for file items)."""
        ...


class DataTransferItemList:
    """
    Collection of DataTransferItem objects.
    """
    
    @property
    def length(self) -> int:
        """Number of items."""
        ...
    
    def add(self, data: Union[str, Any], type: Optional[str] = None) -> Optional[DataTransferItem]:
        """Add an item to the list."""
        ...
    
    def remove(self, index: int) -> None:
        """Remove item at index."""
        ...
    
    def clear(self) -> None:
        """Remove all items."""
        ...
    
    def __getitem__(self, index: int) -> DataTransferItem:
        """Access item by index."""
        ...
    
    def __iter__(self) -> Iterator[DataTransferItem]:
        """Iterate over items."""
        ...
    
    def __len__(self) -> int:
        """Get length."""
        ...


class FileList:
    """
    Collection of File objects from file input or drag-drop.
    """
    
    @property
    def length(self) -> int:
        """Number of files."""
        ...
    
    def item(self, index: int) -> Optional[Any]:
        """Get file at index."""
        ...
    
    def __getitem__(self, index: int) -> Any:
        """Access file by index."""
        ...
    
    def __iter__(self) -> Iterator[Any]:
        """Iterate over files."""
        ...
    
    def __len__(self) -> int:
        """Get length."""
        ...


class DataTransfer:
    """
    WHO: Developers implementing drag-and-drop
    WHAT: Data being transferred during drag operation
    WHEN: Accessing drag data in drag events
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Read/write data during drag-and-drop
    HOW: Zero-runtime passthrough
    
    Example:
        def on_drag_start(event: DragEvent):
            event.dataTransfer.setData("text/plain", "Hello")
            event.dataTransfer.effectAllowed = "move"
        
        def on_drop(event: DragEvent):
            event.preventDefault()
            data = event.dataTransfer.getData("text/plain")
            
            # Handle dropped files
            for file in event.dataTransfer.files:
                upload(file)
    """
    
    @property
    def dropEffect(self) -> str:
        """
        Current drop effect.
        
        Values: "none", "copy", "link", "move"
        """
        ...
    
    @dropEffect.setter
    def dropEffect(self, value: str) -> None:
        """Set the drop effect."""
        ...
    
    @property
    def effectAllowed(self) -> str:
        """
        Allowed drag effects.
        
        Values: "none", "copy", "copyLink", "copyMove", "link",
                "linkMove", "move", "all", "uninitialized"
        """
        ...
    
    @effectAllowed.setter
    def effectAllowed(self, value: str) -> None:
        """Set allowed effects."""
        ...
    
    @property
    def files(self) -> FileList:
        """
        Files being dragged (for file drops).
        
        Empty if not a file drag operation.
        """
        ...
    
    @property
    def items(self) -> DataTransferItemList:
        """List of drag data items."""
        ...
    
    @property
    def types(self) -> List[str]:
        """
        Array of data format strings.
        
        Contains MIME types of available data.
        Example: ["text/plain", "text/html"]
        """
        ...
    
    def setData(self, format: str, data: str) -> None:
        """
        Set drag data for a given format.
        
        Args:
            format: MIME type (e.g., "text/plain", "text/html")
            data: String data to transfer
        
        Example:
            event.dataTransfer.setData("text/plain", "Hello")
            event.dataTransfer.setData("text/html", "<b>Hello</b>")
        """
        ...
    
    def getData(self, format: str) -> str:
        """
        Get drag data for a given format.
        
        Args:
            format: MIME type
        
        Returns:
            Data string, or empty string if not available
        """
        ...
    
    def clearData(self, format: Optional[str] = None) -> None:
        """
        Clear drag data.
        
        Args:
            format: Specific format to clear, or None for all
        """
        ...
    
    def setDragImage(self, image: Element, xOffset: int, yOffset: int) -> None:
        """
        Set custom drag image.
        
        Args:
            image: Element to use as drag image
            xOffset: Horizontal offset from cursor
            yOffset: Vertical offset from cursor
        """
        ...


class DragEvent(MouseEvent):
    """
    WHO: Developers implementing drag-and-drop interfaces
    WHAT: Events for drag-and-drop operations
    WHEN: User drags elements or files
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Type-safe drag-and-drop handling
    HOW: Zero-runtime passthrough
    
    Covers: dragstart, drag, dragend, dragenter, dragover, dragleave, drop
    
    Example:
        def on_drag_start(event: DragEvent):
            event.dataTransfer.setData("text/plain", item_id)
            event.dataTransfer.effectAllowed = "move"
        
        def on_drag_over(event: DragEvent):
            event.preventDefault()  # Required to allow drop
        
        def on_drop(event: DragEvent):
            event.preventDefault()
            item_id = event.dataTransfer.getData("text/plain")
            move_item(item_id, event.target)
    """
    
    @property
    def dataTransfer(self) -> DataTransfer:
        """
        Data being transferred in the drag operation.
        
        Contains methods to get/set drag data and files.
        """
        ...


# =============================================================================
# Focus Events
# =============================================================================

class FocusEvent(UIEvent):
    """
    WHO: Developers handling focus changes
    WHAT: Events for focus entering/leaving elements
    WHEN: User tabs through or clicks on focusable elements
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Type-safe focus event handling
    HOW: Zero-runtime passthrough
    
    Covers: focus, blur, focusin, focusout
    
    Example:
        def on_focus(event: FocusEvent):
            event.target.classList.add("focused")
        
        def on_blur(event: FocusEvent):
            validate_input(event.target)
            event.target.classList.remove("focused")
    """
    
    @property
    def relatedTarget(self) -> Optional[Element]:
        """
        The secondary focus target.
        
        For focus/focusin: element losing focus
        For blur/focusout: element gaining focus
        
        May be None if focus is entering/leaving the window.
        """
        ...


# =============================================================================
# Input Events
# =============================================================================

class InputEvent(UIEvent):
    """
    WHO: Developers handling text input
    WHAT: Events for content changes in editable elements
    WHEN: User types, pastes, or modifies input content
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Type-safe input event handling
    HOW: Zero-runtime passthrough
    
    Covers: input, beforeinput
    
    Example:
        def on_input(event: InputEvent):
            new_value = event.target.value
            
            # Check input type
            if event.inputType == "insertText":
                handle_typing(event.data)
            elif event.inputType == "deleteContentBackward":
                handle_backspace()
    """
    
    @property
    def data(self) -> Optional[str]:
        """
        Data being inserted.
        
        For text input: the character(s) typed
        For deletions: None
        """
        ...
    
    @property
    def inputType(self) -> str:
        """
        Type of input modification.
        
        Common values:
            - "insertText" - Character typed
            - "insertReplacementText" - Text replacement
            - "insertLineBreak" - Enter key
            - "insertParagraph" - Enter in contenteditable
            - "deleteContentBackward" - Backspace
            - "deleteContentForward" - Delete key
            - "insertFromPaste" - Paste
            - "insertFromDrop" - Drop
            - "deleteByCut" - Cut
        """
        ...
    
    @property
    def isComposing(self) -> bool:
        """
        Whether event is part of IME composition.
        
        True during input method composition (CJK input, etc.).
        """
        ...
    
    @property
    def dataTransfer(self) -> Optional[DataTransfer]:
        """
        Data being inserted (for paste/drop events).
        
        Access rich content being inserted.
        """
        ...


# =============================================================================
# Custom Events
# =============================================================================

class CustomEvent(Event):
    """
    WHO: Developers creating custom application events
    WHAT: User-defined events with arbitrary data
    WHEN: Need to dispatch custom events between components
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Type-safe custom event creation and handling
    HOW: Zero-runtime passthrough
    
    Example:
        # Dispatch custom event
        event = CustomEvent("user-login", {
            "detail": {"userId": 123, "username": "john"},
            "bubbles": True
        })
        element.dispatchEvent(event)
        
        # Handle custom event
        def on_user_login(event: CustomEvent):
            user_id = event.detail["userId"]
            update_ui_for_user(user_id)
        
        element.addEventListener("user-login", on_user_login)
    """
    
    @property
    def detail(self) -> Any:
        """
        Custom data attached to the event.
        
        Can be any value: dict, list, string, number, etc.
        """
        ...
    
    def __init__(
        self,
        type: str,
        options: Optional[dict] = None
    ) -> None:
        """
        Create a custom event.
        
        Args:
            type: Event type name (e.g., "my-event")
            options: Optional dict with:
                - detail: Custom data to attach
                - bubbles: Whether event bubbles (default: False)
                - cancelable: Whether event can be cancelled (default: False)
                - composed: Whether event crosses shadow DOM (default: False)
        
        Example:
            # Simple event
            event = CustomEvent("notification")
            
            # Event with data
            event = CustomEvent("data-loaded", {
                "detail": {"items": [1, 2, 3]},
                "bubbles": True
            })
        """
        ...


# =============================================================================
# Animation and Transition Events
# =============================================================================

class AnimationEvent(Event):
    """
    Events for CSS animation lifecycle.
    
    Covers: animationstart, animationend, animationiteration, animationcancel
    """
    
    @property
    def animationName(self) -> str:
        """Name of the CSS animation."""
        ...
    
    @property
    def elapsedTime(self) -> float:
        """Time the animation has been running (seconds)."""
        ...
    
    @property
    def pseudoElement(self) -> str:
        """Pseudo-element the animation runs on (e.g., "::before")."""
        ...


class TransitionEvent(Event):
    """
    Events for CSS transition lifecycle.
    
    Covers: transitionstart, transitionend, transitionrun, transitioncancel
    """
    
    @property
    def propertyName(self) -> str:
        """CSS property being transitioned (e.g., "opacity")."""
        ...
    
    @property
    def elapsedTime(self) -> float:
        """Time the transition has been running (seconds)."""
        ...
    
    @property
    def pseudoElement(self) -> str:
        """Pseudo-element the transition runs on."""
        ...


# =============================================================================
# Pointer Events (extends MouseEvent)
# =============================================================================

class PointerEvent(MouseEvent):
    """
    WHO: Developers handling unified pointer input
    WHAT: Events for mouse, pen, and touch input
    WHEN: User interacts with any pointing device
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Unified handling for all pointer types
    HOW: Zero-runtime passthrough
    
    Covers: pointerdown, pointerup, pointermove, pointerenter, 
            pointerleave, pointerover, pointerout, pointercancel
    
    Example:
        def on_pointer_down(event: PointerEvent):
            # Check pointer type
            if event.pointerType == "touch":
                start_touch_drag()
            elif event.pointerType == "pen":
                start_drawing(event.pressure)
    """
    
    @property
    def pointerId(self) -> int:
        """Unique identifier for the pointer."""
        ...
    
    @property
    def width(self) -> float:
        """Width of pointer contact geometry (CSS pixels)."""
        ...
    
    @property
    def height(self) -> float:
        """Height of pointer contact geometry (CSS pixels)."""
        ...
    
    @property
    def pressure(self) -> float:
        """Pressure of pointer (0.0 to 1.0)."""
        ...
    
    @property
    def tangentialPressure(self) -> float:
        """Barrel pressure for pen (-1.0 to 1.0)."""
        ...
    
    @property
    def tiltX(self) -> int:
        """Tilt angle X-axis (-90 to 90 degrees)."""
        ...
    
    @property
    def tiltY(self) -> int:
        """Tilt angle Y-axis (-90 to 90 degrees)."""
        ...
    
    @property
    def twist(self) -> int:
        """Rotation of pointer (0 to 359 degrees)."""
        ...
    
    @property
    def pointerType(self) -> str:
        """
        Type of pointer device.
        
        Values: "mouse", "pen", "touch"
        """
        ...
    
    @property
    def isPrimary(self) -> bool:
        """Whether this is the primary pointer of its type."""
        ...
    
    def getCoalescedEvents(self) -> List['PointerEvent']:
        """Get all coalesced events (for high-frequency tracking)."""
        ...
    
    def getPredictedEvents(self) -> List['PointerEvent']:
        """Get predicted future events (for low-latency input)."""
        ...


# =============================================================================
# Form Events (convenience aliases)
# =============================================================================

class SubmitEvent(Event):
    """
    Event fired when a form is submitted.
    
    Covers: submit
    
    Example:
        def on_submit(event: SubmitEvent):
            event.preventDefault()
            form_data = FormData(event.target)
            submit_async(form_data)
    """
    
    @property
    def submitter(self) -> Optional[Element]:
        """
        The button that triggered the form submission.
        
        May be None if form was submitted programmatically.
        """
        ...


class FormDataEvent(Event):
    """
    Event fired when FormData is constructed.
    
    Covers: formdata
    """
    
    @property
    def formData(self) -> Any:
        """FormData object being constructed."""
        ...


# =============================================================================
# Clipboard Events
# =============================================================================

class ClipboardEvent(Event):
    """
    Events for clipboard operations.
    
    Covers: cut, copy, paste
    """
    
    @property
    def clipboardData(self) -> Optional[DataTransfer]:
        """DataTransfer containing clipboard data."""
        ...


# =============================================================================
# Composition Events (IME Input)
# =============================================================================

class CompositionEvent(UIEvent):
    """
    WHO: Developers handling international text input
    WHAT: Events for IME (Input Method Editor) composition
    WHEN: User types with Chinese, Japanese, Korean, or other IME input
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Proper handling of multi-character input composition
    HOW: Zero-runtime passthrough
    
    Covers: compositionstart, compositionupdate, compositionend
    
    IME input works differently from direct keyboard input:
    1. compositionstart - User begins composing (e.g., typing pinyin)
    2. compositionupdate - Composition changes as user types
    3. compositionend - User confirms final characters
    
    Example:
        def create_search_input(input_id: str, on_search):
            input_el = document.getElementById(input_id)
            is_composing = False
            
            def on_composition_start(event: CompositionEvent):
                nonlocal is_composing
                is_composing = True
            
            def on_composition_end(event: CompositionEvent):
                nonlocal is_composing
                is_composing = False
                # Now safe to process the final text
                on_search(input_el.value)
            
            def on_input(event):
                if not is_composing:
                    on_search(input_el.value)
            
            input_el.addEventListener("compositionstart", on_composition_start)
            input_el.addEventListener("compositionend", on_composition_end)
            input_el.addEventListener("input", on_input)
    """
    
    @property
    def data(self) -> str:
        """
        Characters being composed or committed.
        
        During compositionstart: empty string or initial text
        During compositionupdate: current composition text
        During compositionend: final committed text
        """
        ...


# =============================================================================
# Storage Events (Cross-Tab Communication)
# =============================================================================

class StorageEvent(Event):
    """
    WHO: Developers syncing state across browser tabs
    WHAT: Events for localStorage/sessionStorage changes
    WHEN: Storage is modified in another tab/window
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Cross-tab communication and state synchronization
    HOW: Zero-runtime passthrough
    
    Note: StorageEvent only fires in OTHER tabs/windows, not the one
    that made the change. This enables cross-tab communication.
    
    Covers: storage
    
    Example:
        def sync_state_across_tabs(key: str, on_change):
            def on_storage(event: StorageEvent):
                if event.key == key:
                    if event.newValue:
                        data = JSON.parse(event.newValue)
                        on_change(data)
            
            window.addEventListener("storage", on_storage)
        
        # In another tab, when you do:
        # localStorage.setItem("user", JSON.stringify(user))
        # The storage event fires in all OTHER tabs
    """
    
    @property
    def key(self) -> Optional[str]:
        """
        The key that was changed.
        
        None if storage was cleared with clear().
        """
        ...
    
    @property
    def oldValue(self) -> Optional[str]:
        """
        The old value of the key.
        
        None if key was newly added.
        """
        ...
    
    @property
    def newValue(self) -> Optional[str]:
        """
        The new value of the key.
        
        None if key was removed.
        """
        ...
    
    @property
    def url(self) -> str:
        """URL of the document that made the change."""
        ...
    
    @property
    def storageArea(self) -> Any:
        """
        The Storage object that was affected.
        
        Either localStorage or sessionStorage.
        """
        ...


# =============================================================================
# Message Events (WebSocket, postMessage, Workers)
# =============================================================================

class MessageEvent(Event):
    """
    WHO: Developers building real-time communication features
    WHAT: Events for cross-origin messaging, WebSocket, and Worker communication
    WHEN: Messages received via postMessage, WebSocket, or Worker
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Type-safe handling of real-time messaging
    HOW: Zero-runtime passthrough
    
    Covers: message (on window, WebSocket, Worker, BroadcastChannel)
    
    Example:
        def setup_iframe_communication(iframe_origin: str, on_message):
            def on_post_message(event: MessageEvent):
                # Security: always verify origin
                if event.origin != iframe_origin:
                    return
                on_message(event.data)
            
            window.addEventListener("message", on_post_message)
    
    Example (WebSocket):
        ws = WebSocket("wss://api.example.com")
        
        def on_ws_message(event: MessageEvent):
            data = JSON.parse(event.data)
            handle_message(data)
        
        ws.addEventListener("message", on_ws_message)
    """
    
    @property
    def data(self) -> Any:
        """
        The message payload.
        
        Can be any type that's serializable:
        - String (most common for WebSocket)
        - Object (from postMessage with structured clone)
        - ArrayBuffer, Blob for binary data
        """
        ...
    
    @property
    def origin(self) -> str:
        """
        The origin of the message sender.
        
        Example: "https://example.com"
        
        IMPORTANT: Always verify origin for security!
        """
        ...
    
    @property
    def lastEventId(self) -> str:
        """
        The last event ID (for Server-Sent Events).
        
        Empty string if not applicable.
        """
        ...
    
    @property
    def source(self) -> Optional[Any]:
        """
        The WindowProxy or MessagePort that sent the message.
        
        None for WebSocket messages.
        """
        ...
    
    @property
    def ports(self) -> List[Any]:
        """
        Array of MessagePort objects for channel messaging.
        
        Empty array if no ports were transferred.
        """
        ...


# =============================================================================
# Error Events (Global Error Handling)
# =============================================================================

class ErrorEvent(Event):
    """
    WHO: Developers implementing error monitoring and reporting
    WHAT: Events for runtime script errors
    WHEN: Uncaught JavaScript errors occur
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Centralized error handling and reporting
    HOW: Zero-runtime passthrough
    
    Covers: error (on window)
    
    Example:
        def setup_error_boundary(report_url: str):
            def on_error(event: ErrorEvent):
                error_info = {
                    "message": event.message,
                    "file": event.filename,
                    "line": event.lineno,
                    "col": event.colno,
                    "stack": event.error.stack if event.error else None
                }
                send_error_report(report_url, error_info)
            
            window.addEventListener("error", on_error)
    """
    
    @property
    def message(self) -> str:
        """
        The error message.
        
        Example: "Uncaught TypeError: Cannot read property 'x' of undefined"
        """
        ...
    
    @property
    def filename(self) -> str:
        """
        The URL of the script where the error occurred.
        
        Example: "https://example.com/app.js"
        """
        ...
    
    @property
    def lineno(self) -> int:
        """
        The line number where the error occurred.
        
        1-indexed.
        """
        ...
    
    @property
    def colno(self) -> int:
        """
        The column number where the error occurred.
        
        1-indexed.
        """
        ...
    
    @property
    def error(self) -> Optional[Any]:
        """
        The Error object that was thrown.
        
        May be None in some cases (cross-origin errors).
        Access .stack for stack trace.
        """
        ...


# =============================================================================
# WebSocket Close Events
# =============================================================================

class CloseEvent(Event):
    """
    WHO: Developers building WebSocket and real-time applications
    WHAT: Events for WebSocket connection closure
    WHEN: WebSocket connection is closed (cleanly or abnormally)
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Handle connection lifecycle and implement reconnection logic
    HOW: Zero-runtime passthrough
    
    Covers: close (on WebSocket)
    
    Common Close Codes:
        1000 - Normal closure
        1001 - Going away (page closing)
        1006 - Abnormal closure (no close frame received)
        1011 - Server error
        1012 - Server restart
        1013 - Try again later
    
    Example:
        ws = WebSocket("wss://api.example.com")
        
        def on_close(event: CloseEvent):
            if event.wasClean:
                console.log(f"Connection closed cleanly: {event.code}")
            else:
                console.error(f"Connection lost: {event.code} - {event.reason}")
                if event.code != 1000:
                    schedule_reconnect()
        
        ws.addEventListener("close", on_close)
    """
    
    @property
    def code(self) -> int:
        """
        The WebSocket connection close code.
        
        Standard codes:
        - 1000: Normal closure
        - 1001: Going away
        - 1002: Protocol error
        - 1003: Unsupported data
        - 1006: Abnormal closure (no close frame)
        - 1007: Invalid frame payload data
        - 1008: Policy violation
        - 1009: Message too big
        - 1010: Mandatory extension missing
        - 1011: Internal server error
        - 1012: Service restart
        - 1013: Try again later
        - 1014: Bad gateway
        - 1015: TLS handshake failure
        - 3000-3999: Reserved for libraries/frameworks
        - 4000-4999: Reserved for applications
        """
        ...
    
    @property
    def reason(self) -> str:
        """
        Human-readable close reason.
        
        May be empty if not provided by server.
        Maximum 123 bytes (UTF-8).
        """
        ...
    
    @property
    def wasClean(self) -> bool:
        """
        Whether the connection closed cleanly.
        
        True if a close frame was received/sent.
        False if connection was lost abruptly.
        """
        ...


# =============================================================================
# History Events (Browser Navigation)
# =============================================================================

class HashChangeEvent(Event):
    """
    WHO: Developers building client-side routing
    WHAT: Events for URL hash changes
    WHEN: The fragment identifier (#...) of the URL changes
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Single-page app navigation without full reload
    HOW: Zero-runtime passthrough
    
    Covers: hashchange
    
    Example:
        def on_hashchange(event: HashChangeEvent):
            old_section = event.oldURL.split("#")[1]
            new_section = event.newURL.split("#")[1]
            navigate_to_section(new_section)
        
        window.addEventListener("hashchange", on_hashchange)
    """
    
    @property
    def oldURL(self) -> str:
        """The previous URL including the hash."""
        ...
    
    @property
    def newURL(self) -> str:
        """The new URL including the hash."""
        ...


class PopStateEvent(Event):
    """
    WHO: Developers building client-side routing with History API
    WHAT: Events for browser history navigation
    WHEN: User clicks back/forward or calls history.back()/forward()
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Handle browser navigation in single-page apps
    HOW: Zero-runtime passthrough
    
    Covers: popstate
    
    Example:
        def on_popstate(event: PopStateEvent):
            if event.state:
                route = event.state["route"]
                render_route(route)
            else:
                render_home()
        
        window.addEventListener("popstate", on_popstate)
        
        # Push state when navigating
        history.pushState({"route": "/about"}, "", "/about")
    """
    
    @property
    def state(self) -> Any:
        """
        The state object passed to pushState/replaceState.
        
        None if no state was associated.
        """
        ...


class BeforeUnloadEvent(Event):
    """
    WHO: Developers preventing accidental data loss
    WHAT: Events before the page unloads
    WHEN: User attempts to navigate away or close the tab
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Warn users about unsaved changes
    HOW: Zero-runtime passthrough
    
    Covers: beforeunload
    
    Example:
        has_unsaved_changes = False
        
        def on_beforeunload(event: BeforeUnloadEvent):
            if has_unsaved_changes:
                event.preventDefault()
                # Modern browsers ignore custom messages
                event.returnValue = ""
        
        window.addEventListener("beforeunload", on_beforeunload)
    
    Note: Modern browsers show a generic message regardless of returnValue.
    """
    
    @property
    def returnValue(self) -> str:
        """
        Set to non-empty string to trigger the browser's
        "Leave site?" dialog.
        
        Modern browsers ignore the actual value and show
        a generic message for security reasons.
        """
        ...
    
    @returnValue.setter
    def returnValue(self, value: str) -> None:
        """Set the return value to trigger the dialog."""
        ...


# =============================================================================
# Promise Rejection Events
# =============================================================================

class PromiseRejectionEvent(Event):
    """
    WHO: Developers implementing global error handling
    WHAT: Events for unhandled promise rejections
    WHEN: A Promise is rejected without a catch handler
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Catch and report unhandled async errors
    HOW: Zero-runtime passthrough
    
    Covers: unhandledrejection, rejectionhandled
    
    Example:
        def on_rejection(event: PromiseRejectionEvent):
            console.error("Unhandled rejection:", event.reason)
            # Optionally prevent default browser handling
            event.preventDefault()
        
        window.addEventListener("unhandledrejection", on_rejection)
    """
    
    @property
    def promise(self) -> Any:
        """
        The Promise that was rejected.
        
        Can be used to add a late .catch() handler.
        """
        ...
    
    @property
    def reason(self) -> Any:
        """
        The rejection reason (typically an Error object).
        
        Access .message and .stack for error details.
        """
        ...


# =============================================================================
# Security Events
# =============================================================================

class SecurityPolicyViolationEvent(Event):
    """
    WHO: Developers implementing Content Security Policy
    WHAT: Events for CSP violations
    WHEN: Browser blocks content due to CSP rules
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Monitor and report CSP violations
    HOW: Zero-runtime passthrough
    
    Covers: securitypolicyviolation
    
    Example:
        def on_csp_violation(event: SecurityPolicyViolationEvent):
            report = {
                "directive": event.violatedDirective,
                "blocked": event.blockedURI,
                "document": event.documentURI
            }
            send_to_reporting_service(report)
        
        document.addEventListener("securitypolicyviolation", on_csp_violation)
    """
    
    @property
    def violatedDirective(self) -> str:
        """The CSP directive that was violated (e.g., 'script-src')."""
        ...
    
    @property
    def effectiveDirective(self) -> str:
        """The effective directive (may differ from violated)."""
        ...
    
    @property
    def blockedURI(self) -> str:
        """The URI of the blocked resource."""
        ...
    
    @property
    def documentURI(self) -> str:
        """The URI of the document where violation occurred."""
        ...
    
    @property
    def originalPolicy(self) -> str:
        """The original CSP policy string."""
        ...
    
    @property
    def sourceFile(self) -> str:
        """The source file where violation occurred."""
        ...
    
    @property
    def lineNumber(self) -> int:
        """Line number in source file."""
        ...
    
    @property
    def columnNumber(self) -> int:
        """Column number in source file."""
        ...
    
    @property
    def statusCode(self) -> int:
        """HTTP status code of the document."""
        ...


# =============================================================================
# Page Transition Events
# =============================================================================

class PageTransitionEvent(Event):
    """
    WHO: Developers optimizing page load and bfcache
    WHAT: Events for page show/hide transitions
    WHEN: Page is shown, hidden, or restored from bfcache
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Handle bfcache restoration properly
    HOW: Zero-runtime passthrough
    
    Covers: pageshow, pagehide
    
    Example:
        def on_pageshow(event: PageTransitionEvent):
            if event.persisted:
                # Page was restored from bfcache
                refresh_dynamic_content()
                reconnect_websockets()
        
        window.addEventListener("pageshow", on_pageshow)
    
    Note: bfcache (back/forward cache) stores full page state.
    When restored, JavaScript doesn't re-execute, so you need
    to manually refresh stale data.
    """
    
    @property
    def persisted(self) -> bool:
        """
        True if page was restored from bfcache.
        
        When true:
        - Page state is restored from cache
        - No network request was made
        - JavaScript didn't re-execute
        - Timers, WebSockets may be stale
        """
        ...


# =============================================================================
# Progress Events
# =============================================================================

class ProgressEvent(Event):
    """
    WHO: Developers implementing file uploads/downloads with progress
    WHAT: Events for tracking operation progress
    WHEN: During XMLHttpRequest, fetch, or FileReader operations
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Show upload/download progress bars
    HOW: Zero-runtime passthrough
    
    Covers: progress, load, loadstart, loadend, abort, error, timeout
    
    Example (Upload Progress):
        xhr = XMLHttpRequest()
        xhr.upload.addEventListener("progress", on_progress)
        
        def on_progress(event: ProgressEvent):
            if event.lengthComputable:
                percent = (event.loaded / event.total) * 100
                update_progress_bar(percent)
    
    Example (Download Progress):
        xhr.addEventListener("progress", on_download_progress)
        
        def on_download_progress(event: ProgressEvent):
            if event.lengthComputable:
                console.log(f"{event.loaded} of {event.total} bytes")
    """
    
    @property
    def lengthComputable(self) -> bool:
        """
        True if total size is known.
        
        False for streaming responses or when Content-Length
        header is missing.
        """
        ...
    
    @property
    def loaded(self) -> int:
        """Number of bytes transferred so far."""
        ...
    
    @property
    def total(self) -> int:
        """
        Total number of bytes to transfer.
        
        Only meaningful if lengthComputable is True.
        """
        ...


# =============================================================================
# Device Motion Events (Mobile Sensors)
# =============================================================================

class DeviceMotionEvent(Event):
    """
    WHO: Developers building motion-aware apps (games, AR, fitness)
    WHAT: Events for device accelerometer and gyroscope data
    WHEN: Device moves or rotates
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: React to device motion for games, step counting, etc.
    HOW: Zero-runtime passthrough
    
    Covers: devicemotion
    
    Example:
        def on_motion(event: DeviceMotionEvent):
            accel = event.acceleration
            if accel:
                x, y, z = accel.x, accel.y, accel.z
                detect_shake(x, y, z)
        
        window.addEventListener("devicemotion", on_motion)
    
    Note: Requires user permission on iOS 13+. Use
    DeviceMotionEvent.requestPermission() first.
    """
    
    @property
    def acceleration(self) -> Optional[Any]:
        """
        Device acceleration excluding gravity (m/s²).
        
        Returns object with x, y, z properties.
        None if not available.
        """
        ...
    
    @property
    def accelerationIncludingGravity(self) -> Optional[Any]:
        """
        Device acceleration including gravity (m/s²).
        
        Returns object with x, y, z properties.
        None if not available.
        """
        ...
    
    @property
    def rotationRate(self) -> Optional[Any]:
        """
        Device rotation rate (degrees/second).
        
        Returns object with alpha, beta, gamma properties.
        None if not available.
        """
        ...
    
    @property
    def interval(self) -> float:
        """
        Interval between events in milliseconds.
        
        Typically 16ms (60fps) but varies by device.
        """
        ...


class DeviceOrientationEvent(Event):
    """
    WHO: Developers building compass, AR, or orientation-aware apps
    WHAT: Events for device orientation in 3D space
    WHEN: Device orientation changes
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Implement compass, AR overlays, 360° viewers
    HOW: Zero-runtime passthrough
    
    Covers: deviceorientation, deviceorientationabsolute
    
    Example:
        def on_orientation(event: DeviceOrientationEvent):
            heading = event.alpha  # Compass heading (0-360)
            tilt_front_back = event.beta  # Front/back tilt (-180 to 180)
            tilt_left_right = event.gamma  # Left/right tilt (-90 to 90)
            
            rotate_compass(heading)
        
        window.addEventListener("deviceorientation", on_orientation)
    
    Note: Requires user permission on iOS 13+.
    """
    
    @property
    def alpha(self) -> Optional[float]:
        """
        Rotation around z-axis (compass heading).
        
        0-360 degrees. 0 = North, 90 = East, etc.
        None if not available.
        """
        ...
    
    @property
    def beta(self) -> Optional[float]:
        """
        Rotation around x-axis (front/back tilt).
        
        -180 to 180 degrees.
        0 = flat, positive = tilted toward user.
        None if not available.
        """
        ...
    
    @property
    def gamma(self) -> Optional[float]:
        """
        Rotation around y-axis (left/right tilt).
        
        -90 to 90 degrees.
        0 = flat, positive = tilted right.
        None if not available.
        """
        ...
    
    @property
    def absolute(self) -> bool:
        """
        True if orientation is relative to Earth's coordinate frame.
        
        False if relative to an arbitrary frame (device-dependent).
        Use 'deviceorientationabsolute' event for guaranteed absolute.
        """
        ...


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Base events
    "Event",
    "UIEvent",
    
    # Mouse events
    "MouseEvent",
    "WheelEvent",
    "PointerEvent",
    
    # Keyboard events
    "KeyboardEvent",
    
    # Touch events
    "Touch",
    "TouchList",
    "TouchEvent",
    
    # Drag events
    "DataTransfer",
    "DataTransferItem",
    "DataTransferItemList",
    "FileList",
    "DragEvent",
    
    # Focus events
    "FocusEvent",
    
    # Input events
    "InputEvent",
    
    # Custom events
    "CustomEvent",
    
    # Animation events
    "AnimationEvent",
    "TransitionEvent",
    
    # Form events
    "SubmitEvent",
    "FormDataEvent",
    
    # Clipboard events
    "ClipboardEvent",
    
    # Composition events
    "CompositionEvent",
    
    # Storage events
    "StorageEvent",
    
    # Message events
    "MessageEvent",
    
    # Error events
    "ErrorEvent",
    
    # WebSocket close events
    "CloseEvent",
    
    # History events
    "HashChangeEvent",
    "PopStateEvent",
    "BeforeUnloadEvent",
    
    # Promise rejection events
    "PromiseRejectionEvent",
    
    # Security events
    "SecurityPolicyViolationEvent",
    
    # Page transition events
    "PageTransitionEvent",
    
    # Progress events
    "ProgressEvent",
    
    # Device motion events
    "DeviceMotionEvent",
    "DeviceOrientationEvent",
]

