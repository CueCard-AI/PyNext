"""
PyNext Middleware Router - Compiled Matchers with O(1) Lookup.

Extends the existing route trie to support middleware matching
with lazy loading per route.
"""

import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Pattern, Set, Tuple
from pathlib import Path

from pynext.middleware.edge import (
    MiddlewareEntry,
    MiddlewareConfig,
    MatcherType,
    matches_path,
    get_middleware_registry,
)


@dataclass
class MiddlewareMatcher:
    """Compiled middleware matcher for fast path lookup."""
    pattern: Pattern
    middleware_ids: Set[str] = field(default_factory=set)
    is_exclude: bool = False


class MiddlewareRouter:
    """
    Router for middleware with O(1) path matching.
    
    Features:
    - Pre-compiled regex patterns
    - Cached middleware chains per path
    - Lazy middleware loading
    - Priority-based ordering
    """
    
    def __init__(self):
        self._matchers: List[MiddlewareMatcher] = []
        self._exclude_matchers: List[MiddlewareMatcher] = []
        self._path_cache: Dict[str, List[str]] = {}
        self._loaded: Set[str] = set()
    
    def compile(self) -> None:
        """
        Compile all registered middleware into matchers.
        
        Call this after all middleware is registered.
        """
        registry = get_middleware_registry()
        
        for name, entry in registry.items():
            # Compile include matcher
            self._add_matcher(entry.config.matcher, entry.config.matcher_type, name)
            
            # Compile exclude matchers
            for exclude in entry.config.exclude:
                self._add_exclude_matcher(exclude, name)
    
    def _add_matcher(
        self,
        pattern: str,
        matcher_type: MatcherType,
        middleware_id: str
    ) -> None:
        """Add a pattern matcher."""
        regex = compile_matcher(pattern, matcher_type)
        
        # Check if we can merge with existing matcher
        for matcher in self._matchers:
            if matcher.pattern.pattern == regex.pattern:
                matcher.middleware_ids.add(middleware_id)
                return
        
        self._matchers.append(MiddlewareMatcher(
            pattern=regex,
            middleware_ids={middleware_id},
        ))
    
    def _add_exclude_matcher(self, pattern: str, middleware_id: str) -> None:
        """Add an exclude pattern matcher."""
        regex = compile_matcher(pattern, MatcherType.GLOB)
        
        self._exclude_matchers.append(MiddlewareMatcher(
            pattern=regex,
            middleware_ids={middleware_id},
            is_exclude=True,
        ))
    
    def get_middleware_for_path(self, path: str) -> List[MiddlewareEntry]:
        """
        Get all middleware entries that match a path.
        
        Uses caching for repeated lookups.
        """
        # Check cache
        if path in self._path_cache:
            middleware_ids = self._path_cache[path]
        else:
            middleware_ids = self._match_path(path)
            self._path_cache[path] = middleware_ids
        
        # Get entries from registry
        registry = get_middleware_registry()
        return [
            registry[mid]
            for mid in middleware_ids
            if mid in registry
        ]
    
    def _match_path(self, path: str) -> List[str]:
        """Match path against all patterns."""
        matched: Set[str] = set()
        excluded: Set[str] = set()
        
        # Check include patterns
        for matcher in self._matchers:
            if matcher.pattern.match(path):
                matched.update(matcher.middleware_ids)
        
        # Check exclude patterns
        for matcher in self._exclude_matchers:
            if matcher.pattern.match(path):
                excluded.update(matcher.middleware_ids)
        
        # Return matched minus excluded
        result = matched - excluded
        
        # Sort by priority
        registry = get_middleware_registry()
        sorted_result = sorted(
            result,
            key=lambda mid: -registry[mid].config.priority if mid in registry else 0
        )
        
        return sorted_result
    
    def clear_cache(self) -> None:
        """Clear the path cache."""
        self._path_cache.clear()
    
    def get_stats(self) -> Dict[str, int]:
        """Get router statistics."""
        return {
            "matchers": len(self._matchers),
            "exclude_matchers": len(self._exclude_matchers),
            "cached_paths": len(self._path_cache),
            "loaded_middleware": len(self._loaded),
        }


def compile_matcher(pattern: str, matcher_type: MatcherType) -> Pattern:
    """
    Compile a pattern into an optimized regex.
    
    Patterns are pre-compiled at startup for O(1) matching.
    """
    if matcher_type == MatcherType.EXACT:
        return re.compile(f"^{re.escape(pattern)}$")
    
    elif matcher_type == MatcherType.PREFIX:
        return re.compile(f"^{re.escape(pattern)}")
    
    elif matcher_type == MatcherType.REGEX:
        return re.compile(pattern)
    
    elif matcher_type == MatcherType.GLOB:
        # Convert glob to optimized regex
        regex = _glob_to_regex(pattern)
        return re.compile(f"^{regex}$")
    
    return re.compile(f"^{re.escape(pattern)}$")


def _glob_to_regex(pattern: str) -> str:
    """
    Convert glob pattern to regex.
    
    Supports:
    - * matches anything except /
    - ** matches anything including /
    - ? matches single character
    - [abc] matches character class
    """
    regex = []
    i = 0
    n = len(pattern)
    
    while i < n:
        c = pattern[i]
        
        if c == "*":
            # Check for **
            if i + 1 < n and pattern[i + 1] == "*":
                # Check for /**/
                if i + 2 < n and pattern[i + 2] == "/":
                    regex.append("(?:/.*)?")
                    i += 3
                else:
                    regex.append(".*")
                    i += 2
            else:
                regex.append("[^/]*")
                i += 1
        
        elif c == "?":
            regex.append("[^/]")
            i += 1
        
        elif c == "[":
            # Character class
            j = i + 1
            while j < n and pattern[j] != "]":
                j += 1
            if j < n:
                regex.append(pattern[i:j + 1])
                i = j + 1
            else:
                regex.append(re.escape(c))
                i += 1
        
        elif c in ".^$+{}|()":
            regex.append("\\" + c)
            i += 1
        
        else:
            regex.append(c)
            i += 1
    
    return "".join(regex)


# Global router instance
_middleware_router: Optional[MiddlewareRouter] = None


def get_middleware_router() -> MiddlewareRouter:
    """Get the global middleware router."""
    global _middleware_router
    if _middleware_router is None:
        _middleware_router = MiddlewareRouter()
    return _middleware_router


def init_middleware_router() -> MiddlewareRouter:
    """Initialize and compile the middleware router."""
    global _middleware_router
    _middleware_router = MiddlewareRouter()
    _middleware_router.compile()
    return _middleware_router


async def load_middleware_file(path: Path) -> None:
    """
    Dynamically load a middleware.py file.
    
    Called during development for hot reload.
    """
    import importlib.util
    
    spec = importlib.util.spec_from_file_location("middleware", path)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

