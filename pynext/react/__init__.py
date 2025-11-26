"""
PyNext React Integration

Provides escape hatch for using React components in PyNext applications.
Use this when you need complex React components that haven't been ported
to native PyNext yet.

Example:
    from pynext.react import use_react
    
    # Wrap a React component
    DatePicker = use_react("react-datepicker")
    Carousel = use_react("embla-carousel-react", "Carousel")
    
    # Use it in your PyNext code
    DatePicker(selected=date, on_change=set_date)
"""

from .wrapper import use_react, ReactComponent, ReactIsland

__all__ = ["use_react", "ReactComponent", "ReactIsland"]
