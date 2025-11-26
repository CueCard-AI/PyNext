"""
PyNext Tailwind Utilities

Type-safe Tailwind CSS class building and conditional class merging.

Example:
    from pynext.tw import tw, cn
    
    # Class builder
    div(class_=tw.flex.items_center.p(4).bg("blue-500"))
    
    # Conditional merging
    Button(class_=cn(
        "px-4 py-2 rounded",
        is_primary and "bg-blue-500",
        disabled and "opacity-50"
    ))
"""

from .builder import tw, TailwindBuilder
from .utils import cn, clsx

__all__ = ["tw", "cn", "clsx", "TailwindBuilder"]

