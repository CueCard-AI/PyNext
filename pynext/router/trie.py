"""
Radix Trie for fast route matching.

Provides O(1) matching for static routes and O(log n) for dynamic routes.
This is much faster than linear O(n) scanning for large route sets.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional, Generic, TypeVar


T = TypeVar("T")


@dataclass
class TrieNode(Generic[T]):
    """A node in the radix trie."""
    
    # Static children: exact path segment -> node
    children: dict[str, "TrieNode[T]"] = field(default_factory=dict)
    
    # Dynamic child (matches any segment): param_name -> node
    # Only one dynamic child per node (e.g., [id], [slug])
    dynamic_child: Optional[tuple[str, "TrieNode[T]"]] = None
    
    # Catch-all child (matches rest of path): param_name -> node
    catch_all_child: Optional[tuple[str, "TrieNode[T]", bool]] = None  # (name, node, is_optional)
    
    # The route stored at this node (if any)
    route: Optional[T] = None
    
    # Route priority (lower = higher priority)
    priority: int = 0


class RouteTrie(Generic[T]):
    """
    A radix trie for fast route matching.
    
    Supports:
    - Static segments: /users, /about
    - Dynamic segments: /users/:id (matches /users/123)
    - Catch-all segments: /docs/*slug (matches /docs/a/b/c)
    - Optional catch-all: /docs/*slug? (also matches /docs)
    
    Matching priority:
    1. Exact static match
    2. Dynamic match (:param)
    3. Catch-all match (*param)
    4. Optional catch-all (*param?)
    
    Usage:
        trie = RouteTrie()
        trie.insert("/users", handler1)
        trie.insert("/users/:id", handler2)
        
        route, params = trie.match("/users/123")
        # route = handler2, params = {"id": "123"}
    """
    
    def __init__(self):
        self.root: TrieNode[T] = TrieNode()
        self._route_count = 0
    
    def insert(self, pattern: str, route: T, priority: int = 0) -> None:
        """
        Insert a route into the trie.
        
        Args:
            pattern: URL pattern like "/users/:id" or "/docs/*slug"
            route: The route object to store
            priority: Route priority (lower = higher priority)
        """
        segments = self._split_pattern(pattern)
        node = self.root
        
        for i, segment in enumerate(segments):
            # Check for catch-all (must be last segment)
            if segment.startswith("*"):
                param_name = segment[1:]
                is_optional = param_name.endswith("?")
                if is_optional:
                    param_name = param_name[:-1]
                
                if node.catch_all_child is None:
                    node.catch_all_child = (param_name, TrieNode(), is_optional)
                
                _, child_node, _ = node.catch_all_child
                child_node.route = route
                child_node.priority = priority
                self._route_count += 1
                return
            
            # Check for dynamic segment
            if segment.startswith(":"):
                param_name = segment[1:]
                
                if node.dynamic_child is None:
                    node.dynamic_child = (param_name, TrieNode())
                
                _, child_node = node.dynamic_child
                node = child_node
            else:
                # Static segment
                if segment not in node.children:
                    node.children[segment] = TrieNode()
                node = node.children[segment]
        
        # Store route at the final node
        node.route = route
        node.priority = priority
        self._route_count += 1
    
    def match(self, path: str) -> tuple[Optional[T], dict[str, str]]:
        """
        Find a route matching the given path.
        
        Returns:
            (route, params) if found, (None, {}) otherwise
        
        Priority:
        1. Exact static match
        2. Dynamic match
        3. Catch-all match
        """
        segments = self._split_path(path)
        
        # Use iterative DFS with backtracking
        result = self._match_recursive(self.root, segments, 0, {})
        
        if result is not None:
            return result
        
        return None, {}
    
    def _match_recursive(
        self,
        node: TrieNode[T],
        segments: list[str],
        index: int,
        params: dict[str, str],
    ) -> Optional[tuple[T, dict[str, str]]]:
        """Recursively match segments against the trie."""
        
        # Base case: consumed all segments
        if index >= len(segments):
            # Check for route at this node
            if node.route is not None:
                return (node.route, params.copy())
            
            # Check for optional catch-all
            if node.catch_all_child is not None:
                param_name, child_node, is_optional = node.catch_all_child
                if is_optional and child_node.route is not None:
                    return (child_node.route, {**params, param_name: ""})
            
            return None
        
        segment = segments[index]
        results: list[tuple[T, dict[str, str], int]] = []  # (route, params, priority)
        
        # Priority 1: Try static match (highest priority)
        if segment in node.children:
            result = self._match_recursive(node.children[segment], segments, index + 1, params)
            if result is not None:
                return result
        
        # Priority 2: Try dynamic match
        if node.dynamic_child is not None:
            param_name, child_node = node.dynamic_child
            new_params = {**params, param_name: segment}
            result = self._match_recursive(child_node, segments, index + 1, new_params)
            if result is not None:
                return result
        
        # Priority 3: Try catch-all match (consumes rest of path)
        if node.catch_all_child is not None:
            param_name, child_node, is_optional = node.catch_all_child
            if child_node.route is not None:
                remaining = "/".join(segments[index:])
                return (child_node.route, {**params, param_name: remaining})
        
        return None
    
    def _split_pattern(self, pattern: str) -> list[str]:
        """Split a URL pattern into segments."""
        pattern = pattern.strip("/")
        if not pattern:
            return []
        return pattern.split("/")
    
    def _split_path(self, path: str) -> list[str]:
        """Split a URL path into segments."""
        path = path.strip("/")
        if not path:
            return []
        return path.split("/")
    
    def __len__(self) -> int:
        """Return the number of routes in the trie."""
        return self._route_count
    
    def get_all_routes(self) -> list[tuple[str, T]]:
        """Get all routes in the trie (for debugging)."""
        routes: list[tuple[str, T]] = []
        self._collect_routes(self.root, "", routes)
        return routes
    
    def _collect_routes(
        self,
        node: TrieNode[T],
        path: str,
        routes: list[tuple[str, T]],
    ) -> None:
        """Recursively collect all routes."""
        if node.route is not None:
            routes.append((path or "/", node.route))
        
        for segment, child in node.children.items():
            self._collect_routes(child, f"{path}/{segment}", routes)
        
        if node.dynamic_child is not None:
            param_name, child = node.dynamic_child
            self._collect_routes(child, f"{path}/:{param_name}", routes)
        
        if node.catch_all_child is not None:
            param_name, child, is_optional = node.catch_all_child
            suffix = "?" if is_optional else ""
            self._collect_routes(child, f"{path}/*{param_name}{suffix}", routes)


class LayoutCache:
    """
    Pre-computed layout chains for fast lookup.
    
    Instead of computing layouts for each file during route registration,
    we pre-compute the layout chain for each directory once.
    """
    
    def __init__(self):
        # directory path -> list of layout handlers (from root to innermost)
        self._chains: dict[str, list[Any]] = {}
        
        # directory path -> layout handler
        self._layouts: dict[str, Any] = {}
    
    def add_layout(self, dir_path: str, handler: Any) -> None:
        """Add a layout for a directory."""
        self._layouts[dir_path] = handler
        self._invalidate_chains()
    
    def get_chain(self, dir_path: str) -> list[Any]:
        """
        Get the layout chain for a directory path.
        
        Returns layouts from root to innermost.
        """
        if dir_path in self._chains:
            return self._chains[dir_path]
        
        # Compute chain
        chain = self._compute_chain(dir_path)
        self._chains[dir_path] = chain
        return chain
    
    def _compute_chain(self, dir_path: str) -> list[Any]:
        """Compute the layout chain for a directory."""
        chain: list[Any] = []
        
        # Check root layout first
        if "" in self._layouts:
            chain.append(self._layouts[""])
        
        if not dir_path:
            return chain
        
        # Build path progressively
        parts = dir_path.split("/") if "/" in dir_path else [dir_path]
        current = ""
        
        for part in parts:
            current = f"{current}/{part}" if current else part
            if current in self._layouts:
                chain.append(self._layouts[current])
        
        return chain
    
    def _invalidate_chains(self) -> None:
        """Invalidate all cached chains (call after adding/removing layouts)."""
        self._chains.clear()
    
    def clear(self) -> None:
        """Clear all layouts and chains."""
        self._layouts.clear()
        self._chains.clear()


class SpecialFilesCache:
    """
    Cache for special files (loading, error) with inheritance lookup.
    
    Provides O(1) lookup after initial computation by caching
    the resolved handler for each directory.
    """
    
    def __init__(self):
        # directory path -> handler (direct mapping)
        self._handlers: dict[str, Any] = {}
        
        # directory path -> resolved handler (with inheritance)
        self._resolved: dict[str, Optional[Any]] = {}
    
    def add(self, dir_path: str, handler: Any) -> None:
        """Add a handler for a directory."""
        self._handlers[dir_path] = handler
        self._invalidate()
    
    def get(self, dir_path: str) -> Optional[Any]:
        """
        Get the handler for a directory, with inheritance.
        
        If the directory doesn't have a handler, returns the
        closest parent's handler.
        """
        if dir_path in self._resolved:
            return self._resolved[dir_path]
        
        # Compute and cache
        handler = self._resolve(dir_path)
        self._resolved[dir_path] = handler
        return handler
    
    def _resolve(self, dir_path: str) -> Optional[Any]:
        """Resolve the handler for a directory with inheritance."""
        # Check this directory
        if dir_path in self._handlers:
            return self._handlers[dir_path]
        
        # Check root
        if not dir_path:
            return self._handlers.get("")
        
        # Check parent directories
        parts = dir_path.split("/") if "/" in dir_path else [dir_path]
        
        for i in range(len(parts) - 1, -1, -1):
            parent = "/".join(parts[:i]) if i > 0 else ""
            if parent in self._handlers:
                return self._handlers[parent]
        
        return None
    
    def _invalidate(self) -> None:
        """Invalidate resolved cache."""
        self._resolved.clear()
    
    def clear(self) -> None:
        """Clear all handlers and cache."""
        self._handlers.clear()
        self._resolved.clear()

