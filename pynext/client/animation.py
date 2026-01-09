"""
PyNext Client - Web Animations API

=============================================================================
WHAT THIS FILE DOES
=============================================================================

Provides Python type stubs and helpers for the Web Animations API, enabling
smooth, GPU-accelerated animations that can be controlled programmatically.

=============================================================================
WHY THIS EXISTS
=============================================================================

The Web Animations API offers:
- GPU-accelerated animations (60fps)
- Programmatic control (pause, reverse, seek)
- Awaitable completion (async/await friendly)
- Better performance than CSS transitions for dynamic animations

=============================================================================
HOW IT WORKS
=============================================================================

All animations are passthrough to the browser's Web Animations API:

    el.animate([{"opacity": "0"}, {"opacity": "1"}], duration=300)
    -> el.animate([{opacity: "0"}, {opacity: "1"}], {duration: 300})

=============================================================================
WHO USES THIS
=============================================================================

- Developers creating smooth UI animations
- Modal/dialog animations
- Page transitions
- Loading indicators
- Micro-interactions

=============================================================================
EXAMPLES
=============================================================================

    from pynext.client.animation import fade_in, slide_in, Animation
    
    # Use helper functions
    await fade_in(el)
    await slide_in(modal, direction="bottom")
    
    # Direct Web Animations API
    anim = el.animate([
        {"transform": "scale(0.9)", "opacity": "0"},
        {"transform": "scale(1)", "opacity": "1"},
    ], duration=300, easing="ease-out", fill="forwards")
    
    await anim.finished
    
    # Control animations
    anim.pause()
    anim.playbackRate = 2.0  # 2x speed
    anim.reverse()
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Union,
    TYPE_CHECKING,
)

if TYPE_CHECKING:
    from pynext.client.dom import Element


# =============================================================================
# Animation Types
# =============================================================================

# Keyframe type: a dictionary of CSS properties
Keyframe = Dict[str, str]

# Direction options
AnimationDirection = Literal["normal", "reverse", "alternate", "alternate-reverse"]

# Fill mode options
AnimationFillMode = Literal["none", "forwards", "backwards", "both", "auto"]

# Easing functions
EasingFunction = str  # "linear", "ease", "ease-in", "ease-out", "cubic-bezier(...)", etc.


@dataclass
class AnimationOptions:
    """
    Options for Web Animations API.
    
    WHO: Developers configuring animations
    WHAT: Configuration for animation timing and behavior
    WHEN: Pass to element.animate() or Animation constructor
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Type-safe animation configuration
    HOW: Converts to JavaScript options object
    
    Example:
        opts = AnimationOptions(
            duration=300,
            easing="ease-out",
            fill="forwards",
        )
    """
    
    duration: int = 0
    """Animation duration in milliseconds."""
    
    delay: int = 0
    """Delay before animation starts in milliseconds."""
    
    endDelay: int = 0
    """Delay after animation ends in milliseconds."""
    
    easing: str = "linear"
    """Timing function: "linear", "ease", "ease-in", "ease-out", "ease-in-out", 
    or CSS cubic-bezier/steps."""
    
    iterations: Union[int, float] = 1
    """Number of times to repeat. Use float("inf") for infinite."""
    
    direction: AnimationDirection = "normal"
    """Playback direction: "normal", "reverse", "alternate", "alternate-reverse"."""
    
    fill: AnimationFillMode = "none"
    """Fill mode: "none", "forwards", "backwards", "both"."""
    
    iterationStart: float = 0.0
    """Starting point within the iteration (0.0 to 1.0)."""
    
    composite: str = "replace"
    """Composite operation: "replace", "add", "accumulate"."""


# =============================================================================
# Animation Class (Web Animations API)
# =============================================================================

class Animation:
    """
    WHO: Developers controlling animations programmatically
    WHAT: Represents a running Web Animation
    WHEN: Returned by element.animate() or created directly
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Control playback, await completion, reverse, pause
    HOW: Passthrough to JavaScript Animation object
    
    Key Features:
        - Awaitable: `await anim.finished`
        - Controllable: pause(), play(), reverse(), cancel()
        - Seekable: set currentTime directly
        - Speed control: playbackRate property
    
    Example:
        anim = el.animate([
            {"opacity": "0"},
            {"opacity": "1"},
        ], duration=300)
        
        # Wait for completion
        await anim.finished
        
        # Or control it
        anim.pause()
        anim.currentTime = 150  # Seek to middle
        anim.play()
        
        # Speed up/slow down
        anim.playbackRate = 2.0  # 2x speed
        anim.playbackRate = 0.5  # Half speed
        
        # Reverse
        anim.reverse()
    """
    
    # =========================================================================
    # Properties
    # =========================================================================
    
    @property
    def id(self) -> str:
        """Animation ID."""
        ...
    
    @id.setter
    def id(self, value: str) -> None:
        """Set animation ID."""
        ...
    
    @property
    def playState(self) -> str:
        """
        Current play state.
        
        Values: "idle", "running", "paused", "finished"
        """
        ...
    
    @property
    def pending(self) -> bool:
        """True if animation is pending (not yet started)."""
        ...
    
    @property
    def playbackRate(self) -> float:
        """
        Playback rate (speed).
        
        1.0 = normal, 2.0 = 2x speed, 0.5 = half speed, -1.0 = reverse
        """
        ...
    
    @playbackRate.setter
    def playbackRate(self, value: float) -> None:
        """Set playback rate."""
        ...
    
    @property
    def currentTime(self) -> Optional[float]:
        """
        Current time in milliseconds.
        
        Can be set to seek within the animation.
        """
        ...
    
    @currentTime.setter
    def currentTime(self, value: float) -> None:
        """Seek to time in milliseconds."""
        ...
    
    @property
    def startTime(self) -> Optional[float]:
        """Animation start time (document timeline)."""
        ...
    
    @startTime.setter
    def startTime(self, value: float) -> None:
        """Set start time."""
        ...
    
    @property
    def finished(self) -> Awaitable[Animation]:
        """
        Promise that resolves when animation finishes.
        
        Example:
            await anim.finished
            print("Animation complete!")
        """
        ...
    
    @property
    def ready(self) -> Awaitable[Animation]:
        """
        Promise that resolves when animation is ready to play.
        
        Example:
            await anim.ready
            print("Animation ready!")
        """
        ...
    
    # =========================================================================
    # Event Handlers
    # =========================================================================
    
    onfinish: Optional[Callable[[Any], None]]
    """Called when animation finishes."""
    
    oncancel: Optional[Callable[[Any], None]]
    """Called when animation is cancelled."""
    
    onremove: Optional[Callable[[Any], None]]
    """Called when animation is removed."""
    
    # =========================================================================
    # Methods
    # =========================================================================
    
    def play(self) -> None:
        """
        Start or resume the animation.
        
        Example:
            anim.pause()
            # Later...
            anim.play()
        """
        ...
    
    def pause(self) -> None:
        """
        Pause the animation.
        
        Example:
            anim.pause()
            print(anim.currentTime)  # Time when paused
        """
        ...
    
    def cancel(self) -> None:
        """
        Cancel the animation and reset to initial state.
        
        Example:
            anim.cancel()
        """
        ...
    
    def finish(self) -> None:
        """
        Immediately finish the animation.
        
        Jumps to end state and triggers onfinish.
        
        Example:
            anim.finish()
        """
        ...
    
    def reverse(self) -> None:
        """
        Reverse the animation direction.
        
        If playing forward, plays backward. If playing backward, plays forward.
        
        Example:
            anim.reverse()  # Toggle direction
        """
        ...
    
    def updatePlaybackRate(self, rate: float) -> None:
        """
        Smoothly update playback rate.
        
        Unlike setting playbackRate directly, this maintains the current
        position and timing smoothly.
        
        Args:
            rate: New playback rate
        
        Example:
            anim.updatePlaybackRate(2.0)  # Smoothly speed up
        """
        ...
    
    def persist(self) -> None:
        """
        Persist the animation (prevent automatic removal).
        
        By default, finished animations are removed. Call persist() to keep.
        """
        ...
    
    def commitStyles(self) -> None:
        """
        Commit the animation's current styles to the element.
        
        Writes the animated styles as inline styles.
        """
        ...


# =============================================================================
# KeyframeEffect (for advanced use)
# =============================================================================

class KeyframeEffect:
    """
    WHO: Developers needing advanced animation control
    WHAT: Describes animation keyframes and timing
    WHEN: Use for creating reusable animation effects
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Separate effect definition from animation playback
    HOW: Passthrough to JavaScript KeyframeEffect
    
    Example:
        effect = KeyframeEffect(
            el,
            [{"opacity": "0"}, {"opacity": "1"}],
            {"duration": 300}
        )
        anim = Animation(effect)
        anim.play()
    """
    
    def __init__(
        self,
        target: Optional[Element],
        keyframes: List[Keyframe],
        options: Union[int, Dict[str, Any], AnimationOptions] = 0
    ) -> None:
        """
        Create a KeyframeEffect.
        
        Args:
            target: Element to animate (or None for group effects)
            keyframes: List of keyframe dictionaries
            options: Duration in ms, or options object
        """
        ...
    
    @property
    def target(self) -> Optional[Element]:
        """Target element."""
        ...
    
    @target.setter
    def target(self, value: Optional[Element]) -> None:
        """Set target element."""
        ...
    
    def getKeyframes(self) -> List[Keyframe]:
        """Get the keyframes."""
        ...
    
    def setKeyframes(self, keyframes: List[Keyframe]) -> None:
        """Set new keyframes."""
        ...


# =============================================================================
# Animation Helper Functions
# =============================================================================

async def fade_in(
    element: Element,
    duration: int = 300,
    easing: str = "ease-out"
) -> Animation:
    """
    Fade in an element.
    
    WHO: Developers adding fade-in animations
    WHAT: Animates opacity from 0 to 1
    WHEN: Showing elements, modals, tooltips
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Common pattern made easy
    HOW: Uses Web Animations API
    
    Args:
        element: Element to fade in
        duration: Animation duration in ms
        easing: Timing function
    
    Returns:
        The Animation object
    
    Example:
        modal = document.getElementById("modal")
        modal.style.display = "block"
        await fade_in(modal)
    """
    anim = element.animate([
        {"opacity": "0"},
        {"opacity": "1"},
    ], duration=duration, easing=easing, fill="forwards")
    await anim.finished
    return anim


async def fade_out(
    element: Element,
    duration: int = 300,
    easing: str = "ease-out"
) -> Animation:
    """
    Fade out an element.
    
    WHO: Developers adding fade-out animations
    WHAT: Animates opacity from 1 to 0
    WHEN: Hiding elements, dismissing modals
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Common pattern made easy
    HOW: Uses Web Animations API
    
    Args:
        element: Element to fade out
        duration: Animation duration in ms
        easing: Timing function
    
    Returns:
        The Animation object
    
    Example:
        await fade_out(modal)
        modal.style.display = "none"
    """
    anim = element.animate([
        {"opacity": "1"},
        {"opacity": "0"},
    ], duration=duration, easing=easing, fill="forwards")
    await anim.finished
    return anim


async def slide_in(
    element: Element,
    direction: Literal["left", "right", "top", "bottom"] = "bottom",
    distance: str = "20px",
    duration: int = 300,
    easing: str = "ease-out"
) -> Animation:
    """
    Slide in an element from a direction.
    
    WHO: Developers adding slide animations
    WHAT: Animates element sliding in from off-screen
    WHEN: Showing modals, drawers, notifications
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Common pattern made easy
    HOW: Uses Web Animations API with transform
    
    Args:
        element: Element to animate
        direction: Direction to slide from
        distance: How far to slide
        duration: Animation duration in ms
        easing: Timing function
    
    Returns:
        The Animation object
    
    Example:
        await slide_in(drawer, direction="left")
        await slide_in(modal, direction="bottom", distance="100%")
    """
    transforms = {
        "left": f"translateX(-{distance})",
        "right": f"translateX({distance})",
        "top": f"translateY(-{distance})",
        "bottom": f"translateY({distance})",
    }
    
    anim = element.animate([
        {"transform": transforms[direction], "opacity": "0"},
        {"transform": "translate(0)", "opacity": "1"},
    ], duration=duration, easing=easing, fill="forwards")
    await anim.finished
    return anim


async def slide_out(
    element: Element,
    direction: Literal["left", "right", "top", "bottom"] = "bottom",
    distance: str = "20px",
    duration: int = 300,
    easing: str = "ease-in"
) -> Animation:
    """
    Slide out an element in a direction.
    
    Args:
        element: Element to animate
        direction: Direction to slide to
        distance: How far to slide
        duration: Animation duration in ms
        easing: Timing function
    
    Returns:
        The Animation object
    """
    transforms = {
        "left": f"translateX(-{distance})",
        "right": f"translateX({distance})",
        "top": f"translateY(-{distance})",
        "bottom": f"translateY({distance})",
    }
    
    anim = element.animate([
        {"transform": "translate(0)", "opacity": "1"},
        {"transform": transforms[direction], "opacity": "0"},
    ], duration=duration, easing=easing, fill="forwards")
    await anim.finished
    return anim


async def scale_in(
    element: Element,
    from_scale: float = 0.9,
    duration: int = 300,
    easing: str = "ease-out"
) -> Animation:
    """
    Scale in an element (grow from smaller).
    
    WHO: Developers adding pop-in animations
    WHAT: Animates element scaling up from a smaller size
    WHEN: Showing modals, tooltips, popovers
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Creates pleasing "pop" effect
    HOW: Uses Web Animations API with transform
    
    Args:
        element: Element to animate
        from_scale: Starting scale (0.9 = 90% of final size)
        duration: Animation duration in ms
        easing: Timing function
    
    Returns:
        The Animation object
    
    Example:
        await scale_in(modal)  # Modal pops in
        await scale_in(tooltip, from_scale=0.8, duration=150)
    """
    anim = element.animate([
        {"transform": f"scale({from_scale})", "opacity": "0"},
        {"transform": "scale(1)", "opacity": "1"},
    ], duration=duration, easing=easing, fill="forwards")
    await anim.finished
    return anim


async def scale_out(
    element: Element,
    to_scale: float = 0.9,
    duration: int = 300,
    easing: str = "ease-in"
) -> Animation:
    """
    Scale out an element (shrink to smaller).
    
    Args:
        element: Element to animate
        to_scale: Ending scale (0.9 = 90% of original size)
        duration: Animation duration in ms
        easing: Timing function
    
    Returns:
        The Animation object
    """
    anim = element.animate([
        {"transform": "scale(1)", "opacity": "1"},
        {"transform": f"scale({to_scale})", "opacity": "0"},
    ], duration=duration, easing=easing, fill="forwards")
    await anim.finished
    return anim


async def shake(
    element: Element,
    intensity: str = "10px",
    duration: int = 500
) -> Animation:
    """
    Shake an element (error indication).
    
    WHO: Developers indicating errors
    WHAT: Animates horizontal shake motion
    WHEN: Invalid input, failed action
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Common error feedback pattern
    HOW: Uses Web Animations API with transform
    
    Args:
        element: Element to shake
        intensity: How far to shake
        duration: Total animation duration in ms
    
    Returns:
        The Animation object
    
    Example:
        if not is_valid:
            await shake(input_field)
    """
    anim = element.animate([
        {"transform": "translateX(0)"},
        {"transform": f"translateX(-{intensity})"},
        {"transform": f"translateX({intensity})"},
        {"transform": f"translateX(-{intensity})"},
        {"transform": f"translateX({intensity})"},
        {"transform": "translateX(0)"},
    ], duration=duration, easing="ease-in-out")
    await anim.finished
    return anim


async def pulse(
    element: Element,
    scale: float = 1.05,
    duration: int = 200
) -> Animation:
    """
    Pulse an element (attention/feedback).
    
    WHO: Developers adding feedback animations
    WHAT: Animates a quick scale up and back
    WHEN: Button press feedback, notifications
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Common feedback pattern
    HOW: Uses Web Animations API with transform
    
    Args:
        element: Element to pulse
        scale: How much to scale up
        duration: Total animation duration in ms
    
    Returns:
        The Animation object
    
    Example:
        async def on_click(e):
            await pulse(e.target)
            do_action()
    """
    anim = element.animate([
        {"transform": "scale(1)"},
        {"transform": f"scale({scale})"},
        {"transform": "scale(1)"},
    ], duration=duration, easing="ease-in-out")
    await anim.finished
    return anim


__all__ = [
    # Types
    "Animation",
    "AnimationOptions",
    "KeyframeEffect",
    "Keyframe",
    "AnimationDirection",
    "AnimationFillMode",
    "EasingFunction",
    
    # Helper functions
    "fade_in",
    "fade_out",
    "slide_in",
    "slide_out",
    "scale_in",
    "scale_out",
    "shake",
    "pulse",
]

