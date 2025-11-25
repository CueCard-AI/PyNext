"""
Dynamic route parsing and matching for file-based routing.

Supports patterns like:
- [id].py -> :id (single dynamic segment)
- [...slug].py -> *slug (catch-all)
- [[...slug]].py -> *slug? (optional catch-all)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class RoutePattern:
    """Parsed route pattern information."""
    
    # Original file path
    file_path: str
    
    # URL pattern for matching (e.g., "/users/:id")
    url_pattern: str
    
    # Regex pattern for matching
    regex: re.Pattern
    
    # Parameter names in order
    params: list[str]
    
    # Whether this is a catch-all route
    is_catch_all: bool = False
    
    # Whether this is an optional catch-all
    is_optional_catch_all: bool = False
    
    # Route priority (lower = higher priority)
    priority: int = 0


def parse_dynamic_segment(segment: str) -> tuple[str, Optional[str], bool, bool]:
    """
    Parse a single route segment.
    
    Returns: (url_segment, param_name, is_catch_all, is_optional)
    """
    # Optional catch-all: [[...slug]]
    if segment.startswith("[[...") and segment.endswith("]]"):
        param = segment[5:-2]  # Extract param name
        return f"(?P<{param}>.*)?", param, True, True
    
    # Catch-all: [...slug]
    if segment.startswith("[...") and segment.endswith("]"):
        param = segment[4:-1]  # Extract param name
        return f"(?P<{param}>.+)", param, True, False
    
    # Dynamic segment: [id]
    if segment.startswith("[") and segment.endswith("]"):
        param = segment[1:-1]  # Extract param name
        return f"(?P<{param}>[^/]+)", param, False, False
    
    # Static segment
    return re.escape(segment), None, False, False


def file_path_to_route(file_path: str, base_dir: str = "pages") -> RoutePattern:
    """
    Convert a file path to a route pattern.
    
    Examples:
        pages/index.py -> /
        pages/about.py -> /about
        pages/users/[id].py -> /users/:id
        pages/docs/[...slug].py -> /docs/*slug
    """
    # Remove base dir and .py extension
    if file_path.startswith(base_dir + "/"):
        file_path = file_path[len(base_dir) + 1:]
    if file_path.endswith(".py"):
        file_path = file_path[:-3]
    
    # Handle index files
    if file_path == "index" or file_path.endswith("/index"):
        if file_path == "index":
            file_path = ""
        else:
            file_path = file_path[:-6]  # Remove /index
    
    # Split into segments
    segments = file_path.split("/") if file_path else []
    
    url_parts = []
    regex_parts = ["^"]
    params = []
    is_catch_all = False
    is_optional_catch_all = False
    priority = 0
    
    for i, segment in enumerate(segments):
        if not segment:
            continue
            
        regex_segment, param, catch_all, optional = parse_dynamic_segment(segment)
        
        if param:
            params.append(param)
            url_parts.append(f":{param}" + ("*" if catch_all else ""))
            # Dynamic segments have lower priority than static
            priority += 10 if catch_all else 5
        else:
            url_parts.append(segment)
            priority += 1
        
        if catch_all:
            is_catch_all = True
            is_optional_catch_all = optional
            if optional:
                regex_parts.append(f"(?:/{regex_segment})?")
            else:
                regex_parts.append(f"/{regex_segment}")
        else:
            regex_parts.append(f"/{regex_segment}")
    
    # Build final patterns
    url_pattern = "/" + "/".join(url_parts) if url_parts else "/"
    regex_pattern = "".join(regex_parts) + "/?$"
    
    return RoutePattern(
        file_path=file_path,
        url_pattern=url_pattern,
        regex=re.compile(regex_pattern),
        params=params,
        is_catch_all=is_catch_all,
        is_optional_catch_all=is_optional_catch_all,
        priority=priority,
    )


def match_route(path: str, pattern: RoutePattern) -> Optional[dict[str, str]]:
    """
    Try to match a URL path against a route pattern.
    
    Returns matched parameters if successful, None otherwise.
    """
    match = pattern.regex.match(path)
    if not match:
        return None
    
    params = {}
    for param in pattern.params:
        value = match.group(param)
        if value is not None:
            # Handle catch-all (split into list)
            if pattern.is_catch_all and param == pattern.params[-1]:
                # Store as is - let the handler decide how to parse
                params[param] = value.strip("/") if value else ""
            else:
                params[param] = value
    
    return params


def sort_routes(routes: list[RoutePattern]) -> list[RoutePattern]:
    """
    Sort routes by priority for matching.
    
    More specific routes should match first:
    1. Static routes
    2. Dynamic routes
    3. Catch-all routes
    4. Optional catch-all routes
    """
    def sort_key(route: RoutePattern) -> tuple:
        # Count static segments for specificity
        static_count = len([s for s in route.url_pattern.split("/") if s and not s.startswith(":")])
        
        return (
            route.is_optional_catch_all,  # Optional catch-all last
            route.is_catch_all,           # Catch-all after regular
            -static_count,                # More static = higher priority
            route.priority,               # Then by calculated priority
            route.url_pattern,            # Finally alphabetically for consistency
        )
    
    return sorted(routes, key=sort_key)

