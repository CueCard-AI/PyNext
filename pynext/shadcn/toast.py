"""
Toast Component (Sonner-style)

Non-blocking notifications that appear temporarily.
Supports stacking, auto-dismiss, and action buttons.

Usage:
    from pynext.shadcn import Toaster, toast
    
    # Add Toaster to your layout (once)
    @layout
    def root_layout(children):
        return html()[
            body()[
                children,
                Toaster(),  # Add at the end of body
            ]
        ]
    
    # Show toasts from anywhere
    toast("Event has been created")
    toast.success("Profile saved successfully")
    toast.error("Something went wrong")
    toast.warning("Please check your input")
    toast.info("New update available")
    
    # With options
    toast("Custom toast", description="More details here", duration=5000)
    
    # With action button
    toast("File deleted", action=("Undo", undo_action))
    
    # Promise toast (loading → success/error)
    toast.promise(
        save_data(),
        loading="Saving...",
        success="Saved!",
        error="Failed to save"
    )
"""

from typing import Any, Optional, List, Union, Literal, Callable, Tuple
from pynext.tw import cn
import json
import uuid


# Toast container styles
TOASTER_BASE = (
    "fixed z-[100] flex flex-col gap-2 p-4 pointer-events-none"
)

TOASTER_POSITIONS = {
    "top-left": "top-0 left-0",
    "top-center": "top-0 left-1/2 -translate-x-1/2",
    "top-right": "top-0 right-0",
    "bottom-left": "bottom-0 left-0",
    "bottom-center": "bottom-0 left-1/2 -translate-x-1/2",
    "bottom-right": "bottom-0 right-0",
}

# Individual toast styles
TOAST_BASE = (
    "relative flex items-center justify-between w-full max-w-md p-4 "
    "bg-background border rounded-lg shadow-lg pointer-events-auto "
    "animate-in slide-in-from-top-full fade-in-0 "
    "data-[swipe=end]:animate-out data-[swipe=end]:slide-out-to-right-full "
    "data-[swipe=end]:fade-out-0"
)

TOAST_VARIANTS = {
    "default": "",
    "success": "border-green-500 bg-green-50 dark:bg-green-950",
    "error": "border-red-500 bg-red-50 dark:bg-red-950",
    "warning": "border-yellow-500 bg-yellow-50 dark:bg-yellow-950",
    "info": "border-blue-500 bg-blue-50 dark:bg-blue-950",
}

TOAST_ICONS = {
    "success": '''<svg class="h-5 w-5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
    </svg>''',
    "error": '''<svg class="h-5 w-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
    </svg>''',
    "warning": '''<svg class="h-5 w-5 text-yellow-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
    </svg>''',
    "info": '''<svg class="h-5 w-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
    </svg>''',
}


class Toaster:
    """
    Container for toast notifications. Add once to your layout.
    
    Attributes:
        position: Where toasts appear on screen
        max_visible: Maximum number of visible toasts
        duration: Default auto-dismiss time in ms
        close_button: Whether to show close button
        rich_colors: Use colored backgrounds for variants
        expand: Expand toasts on hover
        class_: Additional CSS classes
    
    Example:
        Toaster(position="bottom-right", duration=5000)
    """
    
    def __init__(
        self,
        position: Literal[
            "top-left", "top-center", "top-right",
            "bottom-left", "bottom-center", "bottom-right"
        ] = "bottom-right",
        max_visible: int = 3,
        duration: int = 4000,
        close_button: bool = True,
        rich_colors: bool = True,
        expand: bool = True,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.position = position
        self.max_visible = max_visible
        self.duration = duration
        self.close_button = close_button
        self.rich_colors = rich_colors
        self.expand = expand
        self.extra_class = class_
        self.attrs = attrs
    
    def render(self) -> str:
        position_class = TOASTER_POSITIONS.get(self.position, "bottom-right")
        class_str = cn(TOASTER_BASE, position_class, self.extra_class)
        
        return f'''
<div data-pynext-toaster
     data-position="{self.position}"
     data-max-visible="{self.max_visible}"
     data-duration="{self.duration}"
     data-close-button="{str(self.close_button).lower()}"
     data-rich-colors="{str(self.rich_colors).lower()}"
     data-expand="{str(self.expand).lower()}"
     class="{class_str}"
     role="region"
     aria-label="Notifications">
</div>
'''
    
    def __str__(self) -> str:
        return self.render()


class Toast:
    """
    Individual toast component (usually created by toast() function).
    
    Attributes:
        title: Main message
        description: Secondary text
        variant: "default", "success", "error", "warning", "info"
        duration: Auto-dismiss time (0 for persistent)
        action: Tuple of (label, callback) for action button
        dismissible: Whether user can dismiss
    """
    
    def __init__(
        self,
        title: str,
        description: Optional[str] = None,
        variant: Literal["default", "success", "error", "warning", "info"] = "default",
        duration: int = 4000,
        action: Optional[Tuple[str, Callable]] = None,
        dismissible: bool = True,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.title = title
        self.description = description
        self.variant = variant
        self.duration = duration
        self.action = action
        self.dismissible = dismissible
        self.extra_class = class_
        self.attrs = attrs
        self.id = str(uuid.uuid4())[:8]
    
    def render(self) -> str:
        variant_class = TOAST_VARIANTS.get(self.variant, "")
        class_str = cn(TOAST_BASE, variant_class, self.extra_class)
        
        # Icon
        icon_html = ""
        if self.variant in TOAST_ICONS:
            icon_html = f'<div class="flex-shrink-0 mr-3">{TOAST_ICONS[self.variant]}</div>'
        
        # Description
        description_html = ""
        if self.description:
            description_html = f'<p class="text-sm text-muted-foreground mt-1">{self.description}</p>'
        
        # Action button
        action_html = ""
        if self.action:
            label, _ = self.action
            action_html = f'''
<button data-pynext-toast-action class="ml-4 text-sm font-medium underline hover:no-underline">
    {label}
</button>
'''
        
        # Close button
        close_html = ""
        if self.dismissible:
            close_html = '''
<button data-pynext-toast-close class="ml-4 text-muted-foreground hover:text-foreground" aria-label="Close">
    <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
    </svg>
</button>
'''
        
        return f'''
<div data-pynext-toast="{self.id}"
     data-variant="{self.variant}"
     data-duration="{self.duration}"
     class="{class_str}"
     role="alert"
     aria-live="polite">
    {icon_html}
    <div class="flex-1">
        <p class="text-sm font-medium">{self.title}</p>
        {description_html}
    </div>
    {action_html}
    {close_html}
</div>
'''
    
    def __str__(self) -> str:
        return self.render()


class ToastAPI:
    """
    Global toast API for showing notifications.
    
    Usage:
        from pynext.shadcn import toast
        
        toast("Hello!")
        toast.success("Saved")
        toast.error("Failed")
    """
    
    def __call__(
        self,
        message: str,
        description: Optional[str] = None,
        duration: int = 4000,
        action: Optional[Tuple[str, Callable]] = None,
        **kwargs: Any
    ) -> str:
        """Show a default toast."""
        return self._create_toast(message, description, "default", duration, action, **kwargs)
    
    def success(
        self,
        message: str,
        description: Optional[str] = None,
        duration: int = 4000,
        **kwargs: Any
    ) -> str:
        """Show a success toast."""
        return self._create_toast(message, description, "success", duration, **kwargs)
    
    def error(
        self,
        message: str,
        description: Optional[str] = None,
        duration: int = 4000,
        **kwargs: Any
    ) -> str:
        """Show an error toast."""
        return self._create_toast(message, description, "error", duration, **kwargs)
    
    def warning(
        self,
        message: str,
        description: Optional[str] = None,
        duration: int = 4000,
        **kwargs: Any
    ) -> str:
        """Show a warning toast."""
        return self._create_toast(message, description, "warning", duration, **kwargs)
    
    def info(
        self,
        message: str,
        description: Optional[str] = None,
        duration: int = 4000,
        **kwargs: Any
    ) -> str:
        """Show an info toast."""
        return self._create_toast(message, description, "info", duration, **kwargs)
    
    def promise(
        self,
        promise: Any,
        loading: str = "Loading...",
        success: str = "Success",
        error: str = "Error",
        **kwargs: Any
    ) -> str:
        """
        Show a toast that updates based on promise state.
        
        Example:
            toast.promise(
                save_data(),
                loading="Saving...",
                success="Saved!",
                error="Failed to save"
            )
        """
        toast_id = str(uuid.uuid4())[:8]
        # This creates a script that the toast.js runtime will handle
        return f'''
<script>
    window.__PYNEXT_TOAST_PROMISE__ = window.__PYNEXT_TOAST_PROMISE__ || [];
    window.__PYNEXT_TOAST_PROMISE__.push({{
        id: "{toast_id}",
        loading: {json.dumps(loading)},
        success: {json.dumps(success)},
        error: {json.dumps(error)}
    }});
</script>
'''
    
    def dismiss(self, toast_id: Optional[str] = None) -> str:
        """
        Dismiss a toast by ID, or all toasts if no ID provided.
        """
        if toast_id:
            return f'<script>window.PyNextToast?.dismiss("{toast_id}")</script>'
        return '<script>window.PyNextToast?.dismissAll()</script>'
    
    def _create_toast(
        self,
        message: str,
        description: Optional[str],
        variant: str,
        duration: int,
        action: Optional[Tuple[str, Callable]] = None,
        **kwargs: Any
    ) -> str:
        """Internal: Create a toast via client-side script."""
        toast_id = str(uuid.uuid4())[:8]
        
        toast_data = {
            "id": toast_id,
            "message": message,
            "description": description,
            "variant": variant,
            "duration": duration,
        }
        
        if action:
            label, _ = action
            toast_data["action"] = {"label": label}
        
        return f'''
<script>
    window.PyNextToast?.show({json.dumps(toast_data)});
</script>
'''


# Global toast instance
toast = ToastAPI()

