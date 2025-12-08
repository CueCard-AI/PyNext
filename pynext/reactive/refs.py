"""
Refs - DOM Element References

Refs provide a way to access underlying DOM elements directly.
Useful for:
- Focus management
- Measuring elements
- Integrating with non-reactive libraries
- Animations
"""

from __future__ import annotations

from typing import Any, Callable, Generic, Optional, TypeVar

T = TypeVar("T")


class Ref(Generic[T]):
    """
    A reference to a DOM element or component instance.
    
    Usage:
        input_ref = createRef()
        
        def focus_input():
            if input_ref.current:
                input_ref.current.focus()
        
        return div()[
            input_(ref=input_ref),
            button(onclick=focus_input)["Focus"]
        ]
    """
    
    __slots__ = ("_current", "_callback")
    
    def __init__(self, initial: Optional[T] = None):
        self._current: Optional[T] = initial
        self._callback: Optional[Callable[[T], None]] = None
    
    @property
    def current(self) -> Optional[T]:
        """Get the current referenced element."""
        return self._current
    
    @current.setter
    def current(self, value: Optional[T]) -> None:
        """Set the referenced element."""
        self._current = value
        if self._callback and value is not None:
            self._callback(value)
    
    def __call__(self, element: T) -> None:
        """
        Callback form for ref assignment.
        
        Used by the compiler for ref binding:
            <input ref={myRef}>
        
        Compiles to:
            input_el.ref = myRef
            myRef(input_el)
        """
        self.current = element
    
    def __bool__(self) -> bool:
        """Check if ref has a value."""
        return self._current is not None
    
    def __repr__(self) -> str:
        return f"Ref({self._current!r})"


def createRef(initial: Optional[T] = None) -> Ref[T]:
    """
    Create a ref for DOM element access.
    
    Usage:
        my_ref = createRef()
        
        # In template
        div(ref=my_ref)["Content"]
        
        # Access element
        print(my_ref.current)  # <div>Content</div>
    
    Args:
        initial: Optional initial value
        
    Returns:
        Ref object
    """
    return Ref(initial)


def mergeRefs(*refs: Ref) -> Callable[[Any], None]:
    """
    Merge multiple refs into a single callback.
    
    Useful when you need to attach multiple refs to one element.
    
    Usage:
        ref1 = createRef()
        ref2 = createRef()
        
        div(ref=mergeRefs(ref1, ref2))["Content"]
    """
    def merged_callback(element: Any) -> None:
        for ref in refs:
            if ref is not None:
                ref.current = element
    
    return merged_callback


class ForwardRef(Generic[T]):
    """
    A ref that can be forwarded to child components.
    
    Usage:
        @component
        def CustomInput(props, ref):
            return input_(ref=ref, **props)
        
        # Parent
        input_ref = createRef()
        CustomInput(ref=input_ref, placeholder="Type here")
    """
    
    def __init__(self, render: Callable[[dict, Ref[T]], Any]):
        self._render = render
        self._ref: Optional[Ref[T]] = None
    
    def __call__(self, **props) -> Any:
        ref = props.pop("ref", None)
        return self._render(props, ref or createRef())


def forwardRef(
    render: Callable[[dict, Ref[T]], Any]
) -> ForwardRef[T]:
    """
    Create a component that forwards refs.
    
    Usage:
        CustomButton = forwardRef(lambda props, ref:
            button(ref=ref, class_="custom", **props)[props.get("children")]
        )
        
        btn_ref = createRef()
        CustomButton(ref=btn_ref)["Click me"]
    """
    return ForwardRef(render)


def useRef(initial: Optional[T] = None) -> Ref[T]:
    """
    Hook-style ref creation.
    
    Alias for createRef, provided for familiarity with React API.
    """
    return createRef(initial)


class RefCallback(Generic[T]):
    """
    A callback ref that runs a function when the element is attached.
    
    Usage:
        def on_mount(el):
            print(f"Element mounted: {el}")
            return lambda: print("Element unmounted")
        
        div(ref=RefCallback(on_mount))["Content"]
    """
    
    def __init__(
        self,
        callback: Callable[[T], Optional[Callable[[], None]]]
    ):
        self._callback = callback
        self._cleanup: Optional[Callable[[], None]] = None
        self._current: Optional[T] = None
    
    def __call__(self, element: Optional[T]) -> None:
        # Run cleanup if element is being removed
        if element is None and self._cleanup:
            self._cleanup()
            self._cleanup = None
            self._current = None
            return
        
        # Run callback for new element
        if element is not None:
            self._current = element
            result = self._callback(element)
            if callable(result):
                self._cleanup = result
    
    @property
    def current(self) -> Optional[T]:
        return self._current


def createRefCallback(
    callback: Callable[[T], Optional[Callable[[], None]]]
) -> RefCallback[T]:
    """
    Create a callback ref.
    
    The callback is called when the element is attached,
    and can return a cleanup function.
    
    Usage:
        def setup_animation(el):
            animation = animate(el)
            return lambda: animation.cancel()
        
        div(ref=createRefCallback(setup_animation))
    """
    return RefCallback(callback)

