"""
PyNext Client - Client-Side Utilities

WHAT THIS MODULE DOES:
Provides client-side utilities including type checking, Promise utilities,
and scheduling APIs for use in transpiled JavaScript code.

WHY THIS EXISTS:
Client-side code needs access to these utilities in a Pythonic way.
This module provides the Python interface that transpiles to JavaScript.

HOW IT WORKS:
- Python imports are transpiled to JavaScript ES6 imports
- Runtime code is imported from pynext/runtime/ modules
- Type checking, Promise, and scheduling APIs are available

WHO USES THIS:
- Client-side Python code
- Code decorated with @client
- Transpiled JavaScript code

WHEN TO USE:
- Type checking: from pynext.client import typed
- Promise utilities: from pynext.client import Promise
- Scheduling: from pynext.client import queue_microtask, request_animation_frame

EXAMPLES:
    from pynext.client import client, typed, Promise
    
    @typed
    @client
    async def fetch_data():
        results = await Promise.all([fetch(url1), fetch(url2)])
        return results
"""

from pynext.client.typed import typed, enable_type_checking, is_type_checking_enabled

# Promise and scheduling will be available after transpilation
# These are exported for type hints and documentation

__all__ = [
    "typed",
    "enable_type_checking",
    "is_type_checking_enabled",
    # Promise and scheduling are available in transpiled code
    # but not directly importable in Python (they're JS-only)
]

