"""
Priority Icon Component

A domain-specific component that displays priority as an emoji icon.

Usage:
    PriorityIcon("high")    # 🟠
    PriorityIcon("urgent")  # 🔴
    PriorityIcon(priority=issue["priority"])
"""

from typing import Literal, Optional, Any


# Priority to icon mapping
PRIORITY_ICONS = {
    "low": "🟢",
    "medium": "🟡", 
    "high": "🟠",
    "urgent": "🔴",
}

PriorityLevel = Literal["low", "medium", "high", "urgent"]


class PriorityIcon:
    """
    Display an issue priority as a colored circle emoji.
    
    This is a DOMAIN component - it knows about your business logic.
    Python developers don't need to know about colors or styling.
    
    Attributes:
        priority: The priority level - "low", "medium", "high", or "urgent"
        size: Font size - "sm", "base", "lg"
    
    Example:
        # In a list of issues
        Row(gap="sm")[
            PriorityIcon(issue["priority"]),
            Text(issue["title"])
        ]
    """
    
    SIZE_CLASSES = {
        "sm": "text-sm",
        "base": "text-base",
        "lg": "text-lg",
    }
    
    def __init__(
        self,
        priority: PriorityLevel = "medium",
        size: Literal["sm", "base", "lg"] = "base",
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.priority = priority
        self.size = size
        self.extra_class = class_
        self.attrs = attrs
    
    def render(self) -> str:
        """Render the priority icon."""
        import json
        icon = PRIORITY_ICONS.get(self.priority, "⚪")
        size_class = self.SIZE_CLASSES.get(self.size, "text-base")
        
        classes = [size_class]
        if self.extra_class:
            classes.append(self.extra_class)
        class_str = " ".join(classes)
        
        attrs_str = f'class="{class_str}" title="Priority: {self.priority}"'
        
        # Handle data_pynext_field - add field map for value transformation
        if "data_pynext_field" in self.attrs:
            # JSON escape the field map for HTML attribute
            field_map_json = json.dumps(PRIORITY_ICONS).replace('"', '&quot;')
            attrs_str += f' data-pynext-field-map="{field_map_json}"'
        
        for key, value in self.attrs.items():
            if key == "class_":
                continue
            attr_name = key.rstrip("_").replace("_", "-")
            attrs_str += f' {attr_name}="{value}"'
        
        return f'<span {attrs_str}>{icon}</span>'
    
    def __str__(self) -> str:
        return self.render()


