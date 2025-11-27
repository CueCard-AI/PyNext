"""
Templates - Layouts that remount on every navigation.

Use templates when you need:
- Page transition animations
- Analytics tracking on route change  
- Reset component state between pages
- Enter/exit effects

Example:
    # pages/(app)/template.py
    @template
    def app_template(children):
        return div(class_="fade-in")[children]
    
    # With animation config
    @template(animate=True, duration=200)
    def animated_template(children):
        return div(class_="slide-in")[children]

SolidJS Principle: Explicit remount (not hidden in lifecycle)
AI-Friendly: One decorator, three optional params
"""

from dataclasses import dataclass
from typing import Callable, Optional, Any, Union
from functools import wraps
from enum import Enum


class TransitionType(Enum):
    """Built-in transition types."""
    FADE = "fade"
    SLIDE_LEFT = "slide-left"
    SLIDE_RIGHT = "slide-right"
    SLIDE_UP = "slide-up"
    SLIDE_DOWN = "slide-down"
    SCALE = "scale"
    NONE = "none"


@dataclass
class TemplateConfig:
    """Configuration for a template."""
    name: str
    animate: bool = True               # Enable CSS transitions
    duration: int = 200                # Animation duration (ms)
    reset_scroll: bool = True          # Reset scroll on navigation
    transition: TransitionType = TransitionType.FADE  # Transition type
    easing: str = "ease-out"           # CSS easing function


class Template:
    """
    A template component that remounts on navigation.
    
    Unlike layouts (which persist), templates are fully
    replaced on every route change.
    """
    
    def __init__(self, fn: Callable, config: TemplateConfig):
        self.fn = fn
        self.config = config
        self._should_remount = True  # Always true for templates
        
        # Copy function metadata
        self.__name__ = fn.__name__
        self.__doc__ = fn.__doc__
    
    def __call__(self, children: Any = None) -> str:
        """Allow calling template as a function."""
        return self.render(children)
    
    def render(self, children: Any = None) -> str:
        """Render template with children."""
        # Handle both positional and keyword argument styles
        try:
            content = self.fn(children=children)
        except TypeError:
            # Function doesn't accept children kwarg, try positional
            try:
                content = self.fn(children)
            except TypeError:
                # Function takes no arguments
                content = self.fn()
        
        if hasattr(content, 'render'):
            html = content.render()
        else:
            html = str(content) if content else ""
        
        # Wrap with template marker for client-side handling
        attrs = [
            f'data-pynext-template="{self.config.name}"',
            f'data-animate="{str(self.config.animate).lower()}"',
            f'data-duration="{self.config.duration}"',
            f'data-reset-scroll="{str(self.config.reset_scroll).lower()}"',
            f'data-transition="{self.config.transition.value}"',
            f'data-easing="{self.config.easing}"',
        ]
        
        return f'<div {" ".join(attrs)}>{html}</div>'
    
    def get_hydration_data(self) -> dict:
        """Data for client-side template handling."""
        return {
            "name": self.config.name,
            "animate": self.config.animate,
            "duration": self.config.duration,
            "resetScroll": self.config.reset_scroll,
            "transition": self.config.transition.value,
            "easing": self.config.easing,
        }
    
    def get_css(self) -> str:
        """Generate CSS for this template's transitions."""
        name = self.config.name
        duration = self.config.duration
        easing = self.config.easing
        trans = self.config.transition
        
        if trans == TransitionType.NONE or not self.config.animate:
            return ""
        
        css_rules = []
        
        # Base styles
        css_rules.append(f"""
[data-pynext-template="{name}"] {{
    transition: opacity {duration}ms {easing}, 
                transform {duration}ms {easing};
}}
""")
        
        # Transition-specific styles
        if trans == TransitionType.FADE:
            css_rules.append(f"""
[data-pynext-template="{name}"].template-exit {{
    opacity: 0;
}}
[data-pynext-template="{name}"].template-enter {{
    opacity: 0;
}}
[data-pynext-template="{name}"].template-enter-active {{
    opacity: 1;
}}
""")
        elif trans == TransitionType.SLIDE_LEFT:
            css_rules.append(f"""
[data-pynext-template="{name}"].template-exit {{
    transform: translateX(-100%);
    opacity: 0;
}}
[data-pynext-template="{name}"].template-enter {{
    transform: translateX(100%);
    opacity: 0;
}}
[data-pynext-template="{name}"].template-enter-active {{
    transform: translateX(0);
    opacity: 1;
}}
""")
        elif trans == TransitionType.SLIDE_RIGHT:
            css_rules.append(f"""
[data-pynext-template="{name}"].template-exit {{
    transform: translateX(100%);
    opacity: 0;
}}
[data-pynext-template="{name}"].template-enter {{
    transform: translateX(-100%);
    opacity: 0;
}}
[data-pynext-template="{name}"].template-enter-active {{
    transform: translateX(0);
    opacity: 1;
}}
""")
        elif trans == TransitionType.SLIDE_UP:
            css_rules.append(f"""
[data-pynext-template="{name}"].template-exit {{
    transform: translateY(-100%);
    opacity: 0;
}}
[data-pynext-template="{name}"].template-enter {{
    transform: translateY(100%);
    opacity: 0;
}}
[data-pynext-template="{name}"].template-enter-active {{
    transform: translateY(0);
    opacity: 1;
}}
""")
        elif trans == TransitionType.SLIDE_DOWN:
            css_rules.append(f"""
[data-pynext-template="{name}"].template-exit {{
    transform: translateY(100%);
    opacity: 0;
}}
[data-pynext-template="{name}"].template-enter {{
    transform: translateY(-100%);
    opacity: 0;
}}
[data-pynext-template="{name}"].template-enter-active {{
    transform: translateY(0);
    opacity: 1;
}}
""")
        elif trans == TransitionType.SCALE:
            css_rules.append(f"""
[data-pynext-template="{name}"].template-exit {{
    transform: scale(0.9);
    opacity: 0;
}}
[data-pynext-template="{name}"].template-enter {{
    transform: scale(1.1);
    opacity: 0;
}}
[data-pynext-template="{name}"].template-enter-active {{
    transform: scale(1);
    opacity: 1;
}}
""")
        
        return "\n".join(css_rules)


def template(
    fn: Optional[Callable] = None,
    *,
    animate: bool = True,
    duration: int = 200,
    reset_scroll: bool = True,
    transition: Union[TransitionType, str] = TransitionType.FADE,
    easing: str = "ease-out",
) -> Union[Template, Callable[[Callable], Template]]:
    """
    Decorator to define a template.
    
    Templates are like layouts but they remount on every navigation.
    This is useful for:
    - Page transition animations
    - Resetting component state
    - Analytics tracking
    
    Args:
        fn: Template function (receives children kwarg)
        animate: Enable enter/exit CSS animations
        duration: Animation duration in milliseconds
        reset_scroll: Scroll to top on navigation
        transition: Type of transition animation
        easing: CSS easing function
    
    Returns:
        Template instance
    
    Examples:
        # Simple template
        @template
        def page_wrapper(children):
            return main(class_="page")[children]
        
        # With animation
        @template(animate=True, duration=300)
        def animated_wrapper(children):
            return div(class_="transition")[children]
        
        # Slide transition
        @template(transition="slide-left")
        def slide_wrapper(children):
            return div()[children]
        
        # No animation, keep scroll
        @template(animate=False, reset_scroll=False)
        def static_wrapper(children):
            return div()[children]
    """
    # Handle string transition type
    if isinstance(transition, str):
        try:
            transition = TransitionType(transition)
        except ValueError:
            transition = TransitionType.FADE
    
    def decorator(fn: Callable) -> Template:
        config = TemplateConfig(
            name=fn.__name__,
            animate=animate,
            duration=duration,
            reset_scroll=reset_scroll,
            transition=transition,
            easing=easing,
        )
        return Template(fn, config)
    
    if fn is not None:
        return decorator(fn)
    return decorator


# Convenience functions for common patterns

def fade_template(duration: int = 200) -> Callable[[Callable], Template]:
    """Create a fade transition template."""
    return template(transition=TransitionType.FADE, duration=duration)


def slide_template(
    direction: str = "left",
    duration: int = 300,
) -> Callable[[Callable], Template]:
    """Create a slide transition template."""
    trans_map = {
        "left": TransitionType.SLIDE_LEFT,
        "right": TransitionType.SLIDE_RIGHT,
        "up": TransitionType.SLIDE_UP,
        "down": TransitionType.SLIDE_DOWN,
    }
    return template(
        transition=trans_map.get(direction, TransitionType.SLIDE_LEFT),
        duration=duration,
    )


def scale_template(duration: int = 200) -> Callable[[Callable], Template]:
    """Create a scale transition template."""
    return template(transition=TransitionType.SCALE, duration=duration)


def static_template() -> Callable[[Callable], Template]:
    """Create a template with no animation."""
    return template(animate=False)

