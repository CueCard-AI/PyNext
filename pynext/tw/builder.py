"""
Tailwind Class Builder

A type-safe, chainable API for building Tailwind CSS class strings.

Usage:
    from pynext.tw import tw
    
    # Chainable API
    tw.flex.items_center.justify_between.p(4)
    # → "flex items-center justify-between p-4"
    
    # With values
    tw.bg("blue-500").text("white").hover.bg("blue-600")
    # → "bg-blue-500 text-white hover:bg-blue-600"
    
    # Raw string fallback
    tw("flex items-center p-4")
    # → "flex items-center p-4"
"""

from typing import Union, List, Optional


class TailwindBuilder:
    """
    Chainable Tailwind class builder with type hints.
    
    Supports:
    - Simple classes: tw.flex, tw.hidden
    - Classes with values: tw.p(4), tw.bg("red-500")
    - Modifiers: tw.hover.bg("blue-600"), tw.md.flex
    - Arbitrary values: tw.w("[200px]")
    """
    
    def __init__(self, classes: Optional[List[str]] = None, prefix: str = ""):
        self._classes: List[str] = classes or []
        self._prefix = prefix  # For modifiers like "hover:", "md:"
    
    def __call__(self, *args: Union[str, int]) -> "TailwindBuilder":
        """
        Called when using tw("raw classes") or tw.p(4).
        """
        if len(args) == 1 and isinstance(args[0], str) and " " in args[0]:
            # Raw class string: tw("flex items-center")
            return TailwindBuilder(self._classes + args[0].split())
        
        # Value for current class: tw.p(4) or tw.bg("blue-500")
        if self._prefix:
            # This is a modifier being called with a value
            # e.g., tw.hover("bg-blue-500") → "hover:bg-blue-500"
            for arg in args:
                self._classes.append(f"{self._prefix}{arg}")
            return TailwindBuilder(self._classes)
        
        # Just adding raw values
        for arg in args:
            self._classes.append(str(arg))
        return TailwindBuilder(self._classes)
    
    def __getattr__(self, name: str) -> "TailwindBuilder":
        """
        Handle attribute access for class names.
        
        Converts Python names to Tailwind names:
        - items_center → items-center
        - bg_red_500 → bg-red-500
        """
        # Check if this is a modifier (hover, focus, md, lg, etc.)
        modifiers = {
            # State modifiers
            "hover", "focus", "active", "disabled", "visited",
            "focus_within", "focus_visible", "group_hover",
            # Responsive modifiers
            "sm", "md", "lg", "xl", "2xl",
            # Dark mode
            "dark",
            # Pseudo elements
            "before", "after", "placeholder",
            # Form states
            "checked", "required", "invalid", "valid",
            # First/last
            "first", "last", "odd", "even",
        }
        
        clean_name = name.replace("_", "-")
        
        if name.replace("_", "") in {m.replace("_", "") for m in modifiers}:
            # It's a modifier - return builder with prefix
            prefix = f"{self._prefix}{clean_name}:"
            return TailwindBuilder(self._classes, prefix)
        
        # Regular class name
        class_name = f"{self._prefix}{clean_name}" if self._prefix else clean_name
        return TailwindBuilder(self._classes + [class_name])
    
    def __str__(self) -> str:
        """Convert to space-separated class string."""
        return " ".join(self._classes)
    
    def __repr__(self) -> str:
        return f"TailwindBuilder({self._classes!r})"
    
    def __add__(self, other: Union[str, "TailwindBuilder"]) -> "TailwindBuilder":
        """Allow tw.flex + tw.items_center or tw.flex + "custom-class"."""
        if isinstance(other, TailwindBuilder):
            return TailwindBuilder(self._classes + other._classes)
        elif isinstance(other, str):
            return TailwindBuilder(self._classes + other.split())
        return NotImplemented
    
    def __radd__(self, other: str) -> "TailwindBuilder":
        """Allow "custom-class" + tw.flex."""
        if isinstance(other, str):
            return TailwindBuilder(other.split() + self._classes)
        return NotImplemented
    
    # Common utility methods that take values
    
    def p(self, value: Union[int, str]) -> "TailwindBuilder":
        """Padding: p-4, p-[20px]"""
        return self._with_value("p", value)
    
    def px(self, value: Union[int, str]) -> "TailwindBuilder":
        """Horizontal padding: px-4"""
        return self._with_value("px", value)
    
    def py(self, value: Union[int, str]) -> "TailwindBuilder":
        """Vertical padding: py-4"""
        return self._with_value("py", value)
    
    def pt(self, value: Union[int, str]) -> "TailwindBuilder":
        """Padding top: pt-4"""
        return self._with_value("pt", value)
    
    def pb(self, value: Union[int, str]) -> "TailwindBuilder":
        """Padding bottom: pb-4"""
        return self._with_value("pb", value)
    
    def pl(self, value: Union[int, str]) -> "TailwindBuilder":
        """Padding left: pl-4"""
        return self._with_value("pl", value)
    
    def pr(self, value: Union[int, str]) -> "TailwindBuilder":
        """Padding right: pr-4"""
        return self._with_value("pr", value)
    
    def m(self, value: Union[int, str]) -> "TailwindBuilder":
        """Margin: m-4"""
        return self._with_value("m", value)
    
    def mx(self, value: Union[int, str]) -> "TailwindBuilder":
        """Horizontal margin: mx-4, mx-auto"""
        return self._with_value("mx", value)
    
    def my(self, value: Union[int, str]) -> "TailwindBuilder":
        """Vertical margin: my-4"""
        return self._with_value("my", value)
    
    def mt(self, value: Union[int, str]) -> "TailwindBuilder":
        """Margin top: mt-4"""
        return self._with_value("mt", value)
    
    def mb(self, value: Union[int, str]) -> "TailwindBuilder":
        """Margin bottom: mb-4"""
        return self._with_value("mb", value)
    
    def ml(self, value: Union[int, str]) -> "TailwindBuilder":
        """Margin left: ml-4"""
        return self._with_value("ml", value)
    
    def mr(self, value: Union[int, str]) -> "TailwindBuilder":
        """Margin right: mr-4"""
        return self._with_value("mr", value)
    
    def w(self, value: Union[int, str]) -> "TailwindBuilder":
        """Width: w-4, w-full, w-[200px]"""
        return self._with_value("w", value)
    
    def h(self, value: Union[int, str]) -> "TailwindBuilder":
        """Height: h-4, h-full, h-screen"""
        return self._with_value("h", value)
    
    def min_w(self, value: Union[int, str]) -> "TailwindBuilder":
        """Min width: min-w-0, min-w-full"""
        return self._with_value("min-w", value)
    
    def min_h(self, value: Union[int, str]) -> "TailwindBuilder":
        """Min height: min-h-0, min-h-screen"""
        return self._with_value("min-h", value)
    
    def max_w(self, value: Union[int, str]) -> "TailwindBuilder":
        """Max width: max-w-md, max-w-screen-xl"""
        return self._with_value("max-w", value)
    
    def max_h(self, value: Union[int, str]) -> "TailwindBuilder":
        """Max height: max-h-96, max-h-screen"""
        return self._with_value("max-h", value)
    
    def text(self, value: str) -> "TailwindBuilder":
        """Text size or color: text-lg, text-red-500"""
        return self._with_value("text", value)
    
    def font(self, value: str) -> "TailwindBuilder":
        """Font weight or family: font-bold, font-sans"""
        return self._with_value("font", value)
    
    def bg(self, value: str) -> "TailwindBuilder":
        """Background color: bg-blue-500, bg-transparent"""
        return self._with_value("bg", value)
    
    def border(self, value: Optional[Union[int, str]] = None) -> "TailwindBuilder":
        """Border: border, border-2, border-red-500"""
        if value is None:
            return TailwindBuilder(self._classes + [f"{self._prefix}border"])
        return self._with_value("border", value)
    
    def rounded(self, value: Optional[str] = None) -> "TailwindBuilder":
        """Border radius: rounded, rounded-lg, rounded-full"""
        if value is None:
            return TailwindBuilder(self._classes + [f"{self._prefix}rounded"])
        return self._with_value("rounded", value)
    
    def shadow(self, value: Optional[str] = None) -> "TailwindBuilder":
        """Box shadow: shadow, shadow-lg, shadow-none"""
        if value is None:
            return TailwindBuilder(self._classes + [f"{self._prefix}shadow"])
        return self._with_value("shadow", value)
    
    def opacity(self, value: Union[int, str]) -> "TailwindBuilder":
        """Opacity: opacity-50, opacity-100"""
        return self._with_value("opacity", value)
    
    def gap(self, value: Union[int, str]) -> "TailwindBuilder":
        """Gap: gap-4, gap-x-2"""
        return self._with_value("gap", value)
    
    def space_x(self, value: Union[int, str]) -> "TailwindBuilder":
        """Horizontal space between: space-x-4"""
        return self._with_value("space-x", value)
    
    def space_y(self, value: Union[int, str]) -> "TailwindBuilder":
        """Vertical space between: space-y-4"""
        return self._with_value("space-y", value)
    
    def grid_cols(self, value: Union[int, str]) -> "TailwindBuilder":
        """Grid columns: grid-cols-3"""
        return self._with_value("grid-cols", value)
    
    def col_span(self, value: Union[int, str]) -> "TailwindBuilder":
        """Column span: col-span-2"""
        return self._with_value("col-span", value)
    
    def z(self, value: Union[int, str]) -> "TailwindBuilder":
        """Z-index: z-10, z-50"""
        return self._with_value("z", value)
    
    def top(self, value: Union[int, str]) -> "TailwindBuilder":
        """Top position: top-0, top-4"""
        return self._with_value("top", value)
    
    def bottom(self, value: Union[int, str]) -> "TailwindBuilder":
        """Bottom position: bottom-0, bottom-4"""
        return self._with_value("bottom", value)
    
    def left(self, value: Union[int, str]) -> "TailwindBuilder":
        """Left position: left-0, left-4"""
        return self._with_value("left", value)
    
    def right(self, value: Union[int, str]) -> "TailwindBuilder":
        """Right position: right-0, right-4"""
        return self._with_value("right", value)
    
    def inset(self, value: Union[int, str]) -> "TailwindBuilder":
        """All positions: inset-0, inset-4"""
        return self._with_value("inset", value)
    
    def ring(self, value: Optional[Union[int, str]] = None) -> "TailwindBuilder":
        """Ring: ring, ring-2, ring-blue-500"""
        if value is None:
            return TailwindBuilder(self._classes + [f"{self._prefix}ring"])
        return self._with_value("ring", value)
    
    def transition(self, value: Optional[str] = None) -> "TailwindBuilder":
        """Transition: transition, transition-all, transition-colors"""
        if value is None:
            return TailwindBuilder(self._classes + [f"{self._prefix}transition"])
        return self._with_value("transition", value)
    
    def duration(self, value: Union[int, str]) -> "TailwindBuilder":
        """Transition duration: duration-150, duration-300"""
        return self._with_value("duration", value)
    
    def _with_value(self, prefix: str, value: Union[int, str]) -> "TailwindBuilder":
        """Helper to add a class with a value."""
        # Handle arbitrary values: w("[200px]") → w-[200px]
        if isinstance(value, str) and value.startswith("["):
            class_name = f"{self._prefix}{prefix}-{value}"
        else:
            class_name = f"{self._prefix}{prefix}-{value}"
        return TailwindBuilder(self._classes + [class_name])


# Global instance for convenient imports
tw = TailwindBuilder()

