"""
Route Groups - Organize routes without affecting URLs.

Example:
    pages/
    ├── (marketing)/
    │   ├── about/page.py    → /about
    │   └── pricing/page.py  → /pricing
    ├── (app)/
    │   └── dashboard/page.py → /dashboard

SolidJS Principle: Compile-time route resolution (O(1) lookup)
AI-Friendly: Single function to check, single function to strip
"""

import re
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass, field

# Simple regex - parentheses with alphanumeric/dash/underscore
_GROUP_PATTERN = re.compile(r"^\([\w-]+\)$")


def is_route_group(name: str) -> bool:
    """
    Check if folder name is a route group.
    
    Args:
        name: Folder name like "(marketing)" or "dashboard"
    
    Returns:
        True if it's a route group (wrapped in parentheses)
    
    Examples:
        >>> is_route_group("(marketing)")
        True
        >>> is_route_group("dashboard")
        False
        >>> is_route_group("(app-v2)")
        True
    """
    return bool(_GROUP_PATTERN.match(name))


def get_group_name(folder_name: str) -> Optional[str]:
    """
    Extract the group name from a route group folder.
    
    Args:
        folder_name: Folder name like "(marketing)"
    
    Returns:
        Group name without parentheses, or None if not a group
    
    Examples:
        >>> get_group_name("(marketing)")
        "marketing"
        >>> get_group_name("dashboard")
        None
    """
    if is_route_group(folder_name):
        return folder_name[1:-1]
    return None


def strip_groups(path: str) -> str:
    """
    Remove route groups from path to get URL.
    
    Args:
        path: File path like "pages/(app)/dashboard/page.py"
    
    Returns:
        URL path like "/dashboard"
    
    Examples:
        >>> strip_groups("pages/(marketing)/about/page.py")
        "/about"
        >>> strip_groups("pages/(app)/users/[id]/page.py")
        "/users/[id]"
        >>> strip_groups("pages/blog/page.py")
        "/blog"
    """
    parts = Path(path).parts
    result = []
    
    for part in parts:
        # Skip: route groups, "pages", "src", page files
        if is_route_group(part):
            continue
        if part in ("pages", "src", "page.py", "index.py"):
            continue
        result.append(part)
    
    return "/" + "/".join(result) if result else "/"


def get_groups_in_path(path: str) -> List[str]:
    """
    Get all route groups in a path.
    
    Args:
        path: File path like "pages/(app)/(admin)/users/page.py"
    
    Returns:
        List of group names like ["app", "admin"]
    """
    parts = Path(path).parts
    groups = []
    
    for part in parts:
        name = get_group_name(part)
        if name:
            groups.append(name)
    
    return groups


@dataclass
class RouteGroup:
    """A route group with its special files."""
    name: str                          # "marketing", "app"
    path: Path                         # Full path to group folder
    layout: Optional[Path] = None      # Group-specific layout
    template: Optional[Path] = None    # Group-specific template
    loading: Optional[Path] = None     # Group-specific loading
    error: Optional[Path] = None       # Group-specific error
    not_found: Optional[Path] = None   # Group-specific 404


@dataclass 
class GroupRegistry:
    """
    Registry of all route groups - built once at startup.
    
    SolidJS Principle: Immutable after construction
    """
    groups: Dict[str, RouteGroup] = field(default_factory=dict)
    url_to_groups: Dict[str, List[str]] = field(default_factory=dict)
    
    def get_group(self, name: str) -> Optional[RouteGroup]:
        """Get a route group by name."""
        return self.groups.get(name)
    
    def get_groups_for_url(self, url: str) -> List[RouteGroup]:
        """Get all route groups that apply to a URL."""
        group_names = self.url_to_groups.get(url, [])
        return [self.groups[name] for name in group_names if name in self.groups]
    
    def get_layouts(self, url: str) -> List[Path]:
        """
        Get layout chain for URL: [root, group1, group2, ...] or [root].
        
        Returns layouts in order from outermost to innermost.
        """
        layouts = []
        
        # Root layout first
        if "root" in self.groups and self.groups["root"].layout:
            layouts.append(self.groups["root"].layout)
        
        # Then group layouts in order
        for group in self.get_groups_for_url(url):
            if group.layout:
                layouts.append(group.layout)
        
        return layouts
    
    def get_templates(self, url: str) -> List[Path]:
        """Get template chain for URL (templates remount on navigation)."""
        templates = []
        
        # Root template first
        if "root" in self.groups and self.groups["root"].template:
            templates.append(self.groups["root"].template)
        
        # Then group templates
        for group in self.get_groups_for_url(url):
            if group.template:
                templates.append(group.template)
        
        return templates
    
    def get_loading(self, url: str) -> Optional[Path]:
        """Get the most specific loading.py for a URL."""
        # Check groups in reverse order (most specific first)
        for group in reversed(self.get_groups_for_url(url)):
            if group.loading:
                return group.loading
        
        # Fall back to root
        if "root" in self.groups and self.groups["root"].loading:
            return self.groups["root"].loading
        
        return None
    
    def get_error(self, url: str) -> Optional[Path]:
        """Get the most specific error.py for a URL."""
        for group in reversed(self.get_groups_for_url(url)):
            if group.error:
                return group.error
        
        if "root" in self.groups and self.groups["root"].error:
            return self.groups["root"].error
        
        return None


def scan_groups(pages_dir: Path) -> GroupRegistry:
    """
    Scan pages directory for route groups.
    
    Called once at startup. Returns immutable registry.
    
    Args:
        pages_dir: Path to pages directory
    
    Returns:
        GroupRegistry with all groups and URL mappings
    """
    registry = GroupRegistry()
    
    if not pages_dir.exists():
        return registry
    
    # Check for root special files first
    root_group = RouteGroup(name="root", path=pages_dir)
    _scan_special_files(pages_dir, root_group)
    if root_group.layout or root_group.template or root_group.loading or root_group.error:
        registry.groups["root"] = root_group
    
    # Find all (group) folders recursively
    _scan_groups_recursive(pages_dir, pages_dir, registry, [])
    
    return registry


def _scan_special_files(folder: Path, group: RouteGroup) -> None:
    """Scan a folder for special files and add them to the group."""
    special_files = {
        "layout.py": "layout",
        "template.py": "template",
        "loading.py": "loading",
        "error.py": "error",
        "not-found.py": "not_found",
        "not_found.py": "not_found",
    }
    
    for filename, attr in special_files.items():
        file_path = folder / filename
        if file_path.exists():
            setattr(group, attr, file_path)


def _scan_groups_recursive(
    current: Path,
    pages_dir: Path,
    registry: GroupRegistry,
    parent_groups: List[str],
) -> None:
    """Recursively scan for route groups."""
    if not current.is_dir():
        return
    
    for item in current.iterdir():
        if not item.is_dir():
            continue
        
        if is_route_group(item.name):
            # This is a route group
            name = item.name[1:-1]  # "(marketing)" -> "marketing"
            
            group = RouteGroup(name=name, path=item)
            _scan_special_files(item, group)
            
            registry.groups[name] = group
            
            # Build group chain for this level
            current_groups = parent_groups + [name]
            
            # Map all pages in this group
            for page in item.rglob("page.py"):
                url = strip_groups(str(page.relative_to(pages_dir.parent)))
                registry.url_to_groups[url] = current_groups.copy()
            
            # Recurse into the group
            _scan_groups_recursive(item, pages_dir, registry, current_groups)
        else:
            # Regular folder - continue scanning but don't add to group chain
            _scan_groups_recursive(item, pages_dir, registry, parent_groups)

