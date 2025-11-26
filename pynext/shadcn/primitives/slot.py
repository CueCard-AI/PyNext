"""
Slot Primitive

Enables the "asChild" pattern where a component merges its props
onto its child instead of wrapping it in another element.

Usage:
    # Normal button (wraps in <button>)
    Button()["Click me"]
    # → <button class="...">Click me</button>
    
    # With asChild, button styling on a link
    Button(as_child=True)[
        a(href="/page")["Go to page"]
    ]
    # → <a href="/page" class="...">Go to page</a>
"""

from typing import Any, Optional, List, Union, Dict
from pynext.core.component import Component


class Slot(Component):
    """
    Merges props onto its single child element.
    
    This enables the polymorphic component pattern where a component
    can render as a different element while keeping its styles and
    behavior. This is the PyNext equivalent of Radix UI's Slot.
    
    Attributes:
        props: Props to merge onto the child element.
    
    Example:
        # Button that renders as a link
        Slot(props={"class_": "btn btn-primary", "disabled": False})[
            a(href="/dashboard")["Dashboard"]
        ]
        # → <a href="/dashboard" class="btn btn-primary">Dashboard</a>
    """
    
    def __init__(self, props: Optional[Dict[str, Any]] = None, **attrs: Any):
        self.props = props or {}
        self.props.update(attrs)
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "Slot":
        """Add children using bracket syntax: Slot()[child]"""
        if isinstance(children, tuple):
            self._children = list(children)
        else:
            self._children = [children]
        return self
    
    def render(self) -> str:
        """
        Render by merging props onto the child.
        
        If there's no child or multiple children, renders a fragment.
        """
        if not self._children:
            return ""
        
        if len(self._children) == 1:
            child = self._children[0]
            
            # If child is a component with merge_props capability
            if hasattr(child, 'merge_props'):
                return child.merge_props(self.props).render()
            
            # If child is a string, just return it
            if isinstance(child, str):
                return child
            
            # If child has render, try to inject props
            if hasattr(child, 'render'):
                # For HTML elements, we can modify their attrs
                if hasattr(child, 'attrs'):
                    # Merge class_ specially
                    if 'class_' in self.props and 'class_' in child.attrs:
                        child.attrs['class_'] = f"{child.attrs['class_']} {self.props['class_']}"
                        props_without_class = {k: v for k, v in self.props.items() if k != 'class_'}
                        child.attrs.update(props_without_class)
                    else:
                        child.attrs.update(self.props)
                return child.render()
            
            return str(child)
        
        # Multiple children: render as fragment
        result = ""
        for child in self._children:
            if hasattr(child, 'render'):
                result += child.render()
            else:
                result += str(child)
        return result
    
    def __str__(self) -> str:
        return self.render()


def merge_props(base: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two prop dictionaries with special handling for class_.
    
    - class_ values are concatenated
    - style values are merged (if dicts) or concatenated (if strings)
    - Other values use override
    
    Example:
        merge_props(
            {"class_": "btn", "disabled": False},
            {"class_": "btn-primary", "disabled": True}
        )
        # → {"class_": "btn btn-primary", "disabled": True}
    """
    result = base.copy()
    
    for key, value in overrides.items():
        if key == "class_" and key in result:
            # Concatenate class names
            result[key] = f"{result[key]} {value}"
        elif key == "style" and key in result:
            # Merge styles
            if isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = {**result[key], **value}
            elif isinstance(result[key], str) and isinstance(value, str):
                result[key] = f"{result[key]}; {value}"
            else:
                result[key] = value
        else:
            result[key] = value
    
    return result

