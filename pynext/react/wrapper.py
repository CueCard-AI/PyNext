"""
React Component Wrapper

Enables using React components within PyNext applications by rendering
them as hydrated islands.

Usage:
    from pynext.react import use_react
    
    # Default export
    DatePicker = use_react("react-datepicker")
    
    # Named export
    Carousel = use_react("embla-carousel-react", "Carousel")
    
    # Use in component
    DatePicker(selected=date, on_change=lambda d: set_date(d))
"""

from typing import Any, Optional, Dict, List, Union, Callable
import json
import hashlib


class ReactComponent:
    """
    A wrapper that renders a React component as a PyNext island.
    
    This is the class returned by use_react(). When you call it
    with props, it creates an island that will be hydrated on the
    client with the actual React component.
    
    Attributes:
        package: npm package name
        export_name: Named export to use (None for default export)
        props: Props to pass to the React component
    """
    
    def __init__(
        self,
        package: str,
        export_name: Optional[str] = None,
    ):
        self.package = package
        self.export_name = export_name
    
    def __call__(self, **props: Any) -> "ReactIsland":
        """
        Create an island instance with the given props.
        
        Example:
            DatePicker = use_react("react-datepicker")
            DatePicker(selected=date, on_change=handle_change)
        """
        return ReactIsland(
            package=self.package,
            export_name=self.export_name,
            props=props
        )
    
    def __repr__(self) -> str:
        if self.export_name:
            return f"ReactComponent({self.package!r}, {self.export_name!r})"
        return f"ReactComponent({self.package!r})"


class ReactIsland:
    """
    A React component instance ready to be rendered.
    
    This renders as an island placeholder that the client-side
    JavaScript will hydrate with the actual React component.
    """
    
    def __init__(
        self,
        package: str,
        export_name: Optional[str],
        props: Dict[str, Any],
    ):
        self.package = package
        self.export_name = export_name
        self.props = props
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "ReactIsland":
        """Add children using bracket syntax."""
        if isinstance(children, tuple):
            self._children = list(children)
        else:
            self._children = [children]
        return self
    
    def _serialize_props(self) -> str:
        """
        Serialize props to JSON for client-side hydration.
        
        Handles special cases:
        - Callables are converted to handler IDs
        - Complex objects are serialized
        """
        serialized = {}
        handlers = {}
        
        for key, value in self.props.items():
            if callable(value):
                # Generate handler ID for callbacks
                handler_id = hashlib.md5(str(id(value)).encode()).hexdigest()[:8]
                handlers[key] = handler_id
                serialized[key] = f"__handler__{handler_id}"
            elif hasattr(value, 'value'):
                # Signal value - extract current value
                serialized[key] = value.value
            else:
                serialized[key] = value
        
        return json.dumps(serialized)
    
    def render(self) -> str:
        """
        Render the React island placeholder.
        
        The placeholder contains:
        - Package and export information
        - Serialized props
        - Children (if any)
        
        Client-side JavaScript will:
        1. Import the React component
        2. Deserialize props
        3. Render/hydrate the component
        """
        # Generate unique ID for this island
        island_id = hashlib.md5(
            f"{self.package}{self.export_name}{id(self)}".encode()
        ).hexdigest()[:8]
        
        # Render children
        children_html = ""
        for child in self._children:
            if hasattr(child, 'render'):
                children_html += child.render()
            else:
                children_html += str(child)
        
        # Build data attributes
        data_attrs = f'data-pynext-react-island="{island_id}"'
        data_attrs += f' data-package="{self.package}"'
        
        if self.export_name:
            data_attrs += f' data-export="{self.export_name}"'
        
        # Include serialized props
        props_json = self._serialize_props()
        
        # Render placeholder with loading state
        return f'''
<div {data_attrs}>
    <script type="application/json" data-props>{props_json}</script>
    <div data-react-root>{children_html}</div>
    <noscript>This component requires JavaScript to function.</noscript>
</div>
'''
    
    def __str__(self) -> str:
        return self.render()


def use_react(
    package: str,
    export_name: Optional[str] = None,
) -> ReactComponent:
    """
    Create a PyNext wrapper for a React component.
    
    This function returns a ReactComponent wrapper that can be used
    like a PyNext component but renders as a hydrated island using
    the actual React component.
    
    Args:
        package: The npm package name (e.g., "react-datepicker")
        export_name: The named export to use. If None, uses default export.
    
    Returns:
        A ReactComponent wrapper that can be called with props.
    
    Example:
        # Default export
        DatePicker = use_react("react-datepicker")
        
        # Named export  
        Carousel = use_react("embla-carousel-react", "Carousel")
        Dialog = use_react("@radix-ui/react-dialog", "Root")
        
        # Usage
        DatePicker(selected=date, on_change=set_date)
        Carousel(slides=images)
    
    Note:
        The React component must be installed via pynext.npm.txt:
        
        ```txt
        # pynext.npm.txt
        react-datepicker@^4.0.0
        embla-carousel-react@^8.0.0
        ```
        
        PyNext will automatically enable React compatibility mode
        when React components are detected.
    """
    return ReactComponent(package=package, export_name=export_name)

