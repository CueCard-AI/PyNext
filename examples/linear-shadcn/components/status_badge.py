"""
Status Badge Component

A domain-specific component that displays issue status as a colored badge.

Usage:
    StatusBadge("todo")        # Blue "Todo" badge
    StatusBadge("done")        # Green "Done" badge
    StatusBadge(status=issue["status"])
"""

from typing import Literal, Optional, Any
from pynext.shadcn import Badge


# Status to display name
STATUS_LABELS = {
    "backlog": "Backlog",
    "todo": "Todo",
    "in_progress": "In Progress",
    "done": "Done",
    "cancelled": "Cancelled",
}

# Status to badge variant and custom colors
# We use custom colors because shadcn Badge variants don't cover all our statuses
STATUS_STYLES = {
    "backlog": {"bg": "bg-gray-500", "text": "text-white"},
    "todo": {"bg": "bg-blue-500", "text": "text-white"},
    "in_progress": {"bg": "bg-yellow-500", "text": "text-white"},
    "done": {"bg": "bg-green-500", "text": "text-white"},
    "cancelled": {"bg": "bg-red-500", "text": "text-white"},
}

# Inline style colors for dynamic updates via data-pynext-style-map
# These override Tailwind classes when items are dynamically updated in For loops
STATUS_COLORS = {
    "backlog": {"backgroundColor": "#6b7280"},      # gray-500
    "todo": {"backgroundColor": "#3b82f6"},         # blue-500
    "in_progress": {"backgroundColor": "#eab308"},  # yellow-500
    "done": {"backgroundColor": "#22c55e"},         # green-500
    "cancelled": {"backgroundColor": "#ef4444"},    # red-500
}

StatusType = Literal["backlog", "todo", "in_progress", "done", "cancelled"]


class StatusBadge:
    """
    Display an issue status as a styled badge.
    
    This is a DOMAIN component - it knows about your business logic.
    Python developers just pass a status, the component handles styling.
    
    Attributes:
        status: The status value - "backlog", "todo", "in_progress", "done", "cancelled"
        size: Badge size - "sm", "base"
    
    Example:
        # Simple usage
        StatusBadge("done")
        
        # From issue data
        StatusBadge(issue["status"])
        
        # In a card
        Row(justify="between")[
            Text(issue["title"]),
            StatusBadge(issue["status"])
        ]
    """
    
    def __init__(
        self,
        status: StatusType = "todo",
        size: Literal["sm", "base"] = "base",
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.status = status
        self.size = size
        self.extra_class = class_
        self.attrs = attrs
    
    def render(self) -> str:
        """Render the status badge."""
        import json
        label = STATUS_LABELS.get(self.status, self.status.replace("_", " ").title())
        styles = STATUS_STYLES.get(self.status, STATUS_STYLES["todo"])
        
        size_class = "text-xs px-2 py-0.5" if self.size == "sm" else "text-sm px-2.5 py-0.5"
        
        classes = [
            "inline-flex items-center rounded-full font-medium",
            size_class,
            styles["bg"],
            styles["text"],
        ]
        if self.extra_class:
            classes.append(self.extra_class)
        class_str = " ".join(classes)
        
        attrs_str = f'class="{class_str}"'
        
        # Handle data_pynext_field - add field map for value transformation
        if "data_pynext_field" in self.attrs:
            # JSON escape the field map for HTML attribute (text labels)
            field_map_json = json.dumps(STATUS_LABELS).replace('"', '&quot;')
            attrs_str += f' data-pynext-field-map="{field_map_json}"'
            
            # Also add style map for dynamic background color updates
            style_map_json = json.dumps(STATUS_COLORS).replace('"', '&quot;')
            attrs_str += f' data-pynext-style-map="{style_map_json}"'
        
        for key, value in self.attrs.items():
            if key == "class_":
                continue
            attr_name = key.rstrip("_").replace("_", "-")
            attrs_str += f' {attr_name}="{value}"'
        
        return f'<span {attrs_str}>{label}</span>'
    
    def __str__(self) -> str:
        return self.render()


