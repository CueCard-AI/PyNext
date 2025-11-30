"""
Proxy Router - Path Matching and Rewriting

Matches incoming requests against proxy patterns
and rewrites paths for forwarding.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .config import ProxyConfig, ProxyRoute, get_proxy_config


@dataclass
class ProxyMatch:
    """
    Result of matching a request against proxy routes.
    
    Attributes:
        route: The matched route
        target_url: Full target URL (including rewritten path)
        original_path: Original request path
        rewritten_path: Path after rewriting
        headers: Headers to add
        groups: Captured groups from pattern matching
    """
    route: ProxyRoute
    target_url: str
    original_path: str
    rewritten_path: str
    headers: Dict[str, str]
    groups: Dict[str, str]


class ProxyRouter:
    """
    Routes requests to proxy targets.
    
    Handles pattern matching, path rewriting, and
    building target URLs.
    
    Example:
        >>> router = ProxyRouter()
        >>> match = router.match("/api/users/123")
        >>> if match:
        ...     print(match.target_url)
        https://users.example.com/123
    """
    
    def __init__(self, config: Optional[ProxyConfig] = None):
        self.config = config or get_proxy_config()
        self._pattern_cache: Dict[str, re.Pattern] = {}
    
    def match(
        self,
        path: str,
        is_dev: bool = False,
    ) -> Optional[ProxyMatch]:
        """
        Match a request path against proxy routes.
        
        Args:
            path: Request path (e.g., "/api/users/123")
            is_dev: Whether running in development mode
            
        Returns:
            ProxyMatch if matched, None otherwise
        """
        result = self.config.find_route(path, is_dev)
        if result is None:
            return None
        
        route, groups = result
        
        # Rewrite path
        rewritten_path = route.rewrite_path(path, groups)
        
        # Build target URL
        target_base = route.get_target()
        target_url = self._build_target_url(target_base, rewritten_path)
        
        # Collect headers
        headers = self.config.global_headers.copy()
        headers.update(route.get_headers())
        
        return ProxyMatch(
            route=route,
            target_url=target_url,
            original_path=path,
            rewritten_path=rewritten_path,
            headers=headers,
            groups=groups,
        )
    
    def _build_target_url(self, base: str, path: str) -> str:
        """Combine base URL with path."""
        # Remove trailing slash from base
        base = base.rstrip("/")
        
        # Ensure path starts with /
        if not path.startswith("/"):
            path = "/" + path
        
        return base + path
    
    def _compile_pattern(self, pattern: str) -> re.Pattern:
        """Compile glob pattern to regex."""
        if pattern in self._pattern_cache:
            return self._pattern_cache[pattern]
        
        regex = pattern
        regex = regex.replace(".", r"\.")
        regex = regex.replace("**", "__DOUBLE_STAR__")
        regex = regex.replace("*", "([^/]*)")
        regex = regex.replace("__DOUBLE_STAR__", "(.*)")
        regex = f"^{regex}$"
        
        compiled = re.compile(regex)
        self._pattern_cache[pattern] = compiled
        return compiled
    
    def get_all_routes(self) -> List[ProxyRoute]:
        """Get all configured routes."""
        return self.config.routes.copy()
    
    def clear_cache(self):
        """Clear pattern cache."""
        self._pattern_cache.clear()


def match_proxy(
    path: str,
    is_dev: bool = False,
) -> Optional[ProxyMatch]:
    """
    Match a path against global proxy config.
    
    Convenience function for quick matching.
    
    Args:
        path: Request path
        is_dev: Whether in development mode
        
    Returns:
        ProxyMatch if matched
    """
    router = ProxyRouter()
    return router.match(path, is_dev)


class PathRewriter:
    """
    Handles complex path rewriting patterns.
    
    Supports:
    - $1, $2, etc. for captured groups
    - Named captures: $name
    - Strip prefix: /api/v1/* -> /$1
    - Append path: /* -> /prefix/$1
    """
    
    def __init__(self, pattern: str, rewrite: str):
        self.pattern = pattern
        self.rewrite = rewrite
        self._regex = self._compile()
    
    def _compile(self) -> re.Pattern:
        """Compile pattern to regex with named groups."""
        regex = self.pattern
        
        # Replace ** with named group
        regex = re.sub(
            r"\*\*",
            r"(?P<rest>.*)",
            regex,
        )
        
        # Replace * with numbered groups
        group_num = [0]
        
        def replace_star(match):
            group_num[0] += 1
            return f"(?P<g{group_num[0]}>[^/]*)"
        
        regex = re.sub(r"(?<!\*)\*(?!\*)", replace_star, regex)
        regex = regex.replace(".", r"\.")
        
        return re.compile(f"^{regex}$")
    
    def rewrite(self, path: str) -> Optional[str]:
        """
        Rewrite path if it matches pattern.
        
        Returns rewritten path or None if no match.
        """
        match = self._regex.match(path)
        if not match:
            return None
        
        result = self.rewrite
        groups = match.groupdict()
        
        # Replace named groups
        for name, value in groups.items():
            result = result.replace(f"${name}", value)
        
        # Replace numbered groups
        for i, group in enumerate(match.groups(), 1):
            result = result.replace(f"${i}", group)
        
        return result

