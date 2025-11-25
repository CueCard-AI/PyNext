"""
Intercepting Routes for PyNext.

Implements the (..) convention for route interception, commonly used
for modal patterns where navigation shows content in a modal while
preserving the background page.

SolidJS Principles Applied:
- Build-time interception map (pre-computed rules)
- Background stays static (no re-render)
- Modal content only hydrates
- URL is source of truth (no client state)

Performance Advantages over Next.js:
- Pre-computed interception rules
- Static background (zero JS)
- Minimal modal payload
- No client-side routing state
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, List, Any, Callable, Tuple
import re
from enum import Enum


class InterceptionType(Enum):
    """Types of route interception."""
    SOFT = "soft"       # (..) - one level up
    HARD = "hard"       # (...) - to root
    SIBLING = "sibling" # (.) - same level


@dataclass
class InterceptionRule:
    """A rule for intercepting a route."""
    source_pattern: str      # Pattern that triggers interception
    target_pattern: str      # Pattern being intercepted
    interception_type: InterceptionType
    interceptor_path: str    # Path to the interceptor page
    original_path: str       # Path to the original page
    slot_name: str = "modal" # Slot to render interceptor in


@dataclass
class InterceptionMatch:
    """Result of matching an interception."""
    rule: InterceptionRule
    source_params: Dict[str, str]
    target_params: Dict[str, str]
    is_intercepted: bool
    referrer: Optional[str] = None  # Where the user came from


@dataclass
class CompiledInterceptionMap:
    """
    Pre-compiled map of all interceptions.
    
    Built at compile time for O(1) lookup at runtime.
    """
    rules: List[InterceptionRule]
    # source_pattern -> rule
    source_index: Dict[str, InterceptionRule] = field(default_factory=dict)
    # target_pattern -> list of rules that intercept it
    target_index: Dict[str, List[InterceptionRule]] = field(default_factory=dict)
    
    def __post_init__(self):
        for rule in self.rules:
            self.source_index[rule.source_pattern] = rule
            if rule.target_pattern not in self.target_index:
                self.target_index[rule.target_pattern] = []
            self.target_index[rule.target_pattern].append(rule)
    
    def should_intercept(
        self,
        path: str,
        referrer: Optional[str] = None,
    ) -> Optional[InterceptionMatch]:
        """
        Check if a path should be intercepted.
        
        Args:
            path: The path being navigated to
            referrer: The path the user is navigating from
        
        Returns:
            InterceptionMatch if intercepted, None otherwise
        """
        # Try to match against target patterns
        for target_pattern, rules in self.target_index.items():
            params = self._match_pattern(path, target_pattern)
            if params is not None:
                # Check if any rule should intercept
                for rule in rules:
                    if self._should_apply_rule(rule, referrer):
                        return InterceptionMatch(
                            rule=rule,
                            source_params={},
                            target_params=params,
                            is_intercepted=True,
                            referrer=referrer,
                        )
        
        return None
    
    def get_original_route(self, path: str) -> Optional[str]:
        """Get the original (non-intercepted) route for a path."""
        for target_pattern, rules in self.target_index.items():
            if self._match_pattern(path, target_pattern) is not None:
                return rules[0].original_path if rules else None
        return None
    
    def _should_apply_rule(
        self,
        rule: InterceptionRule,
        referrer: Optional[str],
    ) -> bool:
        """Check if an interception rule should apply."""
        if referrer is None:
            # Direct navigation (e.g., page refresh) - don't intercept
            return False
        
        # For soft interception, check referrer is in allowed scope
        if rule.interception_type == InterceptionType.SOFT:
            # (..) - referrer should be "up one level"
            # This means interceptor's parent matches referrer's path
            interceptor_parent = str(Path(rule.interceptor_path).parent)
            return referrer.startswith(interceptor_parent) or referrer == interceptor_parent
        
        elif rule.interception_type == InterceptionType.HARD:
            # (...) - always intercept from anywhere
            return True
        
        elif rule.interception_type == InterceptionType.SIBLING:
            # (.) - referrer should be sibling
            interceptor_dir = str(Path(rule.interceptor_path).parent)
            referrer_dir = str(Path(referrer).parent) if referrer != "/" else "/"
            return interceptor_dir == referrer_dir
        
        return False
    
    def _match_pattern(self, path: str, pattern: str) -> Optional[Dict[str, str]]:
        """Match a path against a pattern."""
        # Convert pattern to regex
        # First, handle :param and *param placeholders
        regex = pattern
        
        # Convert :param to capture groups (before escaping)
        regex = re.sub(r':(\w+)', r'__PARAM_\1__', regex)
        
        # Convert *param to catch-all (before escaping)
        regex = re.sub(r'\*(\w+)', r'__CATCHALL_\1__', regex)
        
        # Escape special regex characters
        regex = re.escape(regex)
        
        # Convert placeholders to regex capture groups
        regex = re.sub(r'__PARAM_(\w+)__', r'(?P<\1>[^/]+)', regex)
        regex = re.sub(r'__CATCHALL_(\w+)__', r'(?P<\1>.+)', regex)
        
        regex = f"^{regex}$"
        
        match = re.match(regex, path)
        if match:
            return match.groupdict()
        return None


class InterceptionScanner:
    """
    Scans for intercepting routes using the (..) convention.
    
    Convention:
    - (.)folder - intercept from same level
    - (..)folder - intercept from one level up
    - (...)folder - intercept from root
    
    Example structure:
        pages/
        ├── photos/
        │   └── [id]/
        │       └── page.py           # Full page view
        ├── @modal/
        │   └── (..)photos/
        │       └── [id]/
        │           └── page.py       # Modal view
        └── layout.py
    
    When navigating from /gallery to /photos/123:
    - Shows /gallery in background
    - Shows photos/123 content in modal
    - URL is /photos/123
    """
    
    def __init__(self):
        self._rules: List[InterceptionRule] = []
        self._map: Optional[CompiledInterceptionMap] = None
    
    def scan(self, pages_dir: Path) -> CompiledInterceptionMap:
        """
        Scan pages directory for intercepting routes.
        
        Returns compiled interception map.
        """
        self._rules = []
        
        if not pages_dir.exists():
            return CompiledInterceptionMap(rules=[])
        
        # Find all interception folders
        for item in pages_dir.rglob("(*)"):
            if item.is_dir():
                self._process_interception_folder(item, pages_dir)
        
        # Also check inside @slot folders
        for slot_dir in pages_dir.rglob("@*"):
            if slot_dir.is_dir():
                for item in slot_dir.rglob("(*)"):
                    if item.is_dir():
                        self._process_interception_folder(item, pages_dir)
        
        self._map = CompiledInterceptionMap(rules=self._rules)
        return self._map
    
    def _process_interception_folder(
        self,
        intercept_dir: Path,
        pages_dir: Path,
    ) -> None:
        """Process an interception folder like (..)photos."""
        folder_name = intercept_dir.name
        
        # Parse interception type and target
        match = re.match(r'\((\.+)\)(.+)', folder_name)
        if not match:
            return
        
        dots = match.group(1)
        target_name = match.group(2)
        
        # Determine interception type
        if dots == ".":
            interception_type = InterceptionType.SIBLING
        elif dots == "..":
            interception_type = InterceptionType.SOFT
        elif dots == "...":
            interception_type = InterceptionType.HARD
        else:
            return
        
        # Find all page files in this interception folder
        for page_file in intercept_dir.rglob("page.py"):
            self._create_rule(
                page_file,
                intercept_dir,
                target_name,
                interception_type,
                pages_dir,
            )
    
    def _create_rule(
        self,
        page_file: Path,
        intercept_dir: Path,
        target_name: str,
        interception_type: InterceptionType,
        pages_dir: Path,
    ) -> None:
        """Create an interception rule."""
        # Calculate the target pattern
        rel_path = page_file.relative_to(intercept_dir)
        page_subpath = str(rel_path.parent)
        if page_subpath == ".":
            page_subpath = ""
        
        # Build target pattern
        if page_subpath:
            target_pattern = f"/{target_name}/{page_subpath}"
        else:
            target_pattern = f"/{target_name}"
        
        # Convert [param] to :param
        target_pattern = re.sub(r'\[(\w+)\]', r':\1', target_pattern)
        
        # Convert [...slug] to *slug
        target_pattern = re.sub(r'\[\.\.\.(\w+)\]', r'*\1', target_pattern)
        
        # Normalize slashes
        target_pattern = "/" + target_pattern.strip("/")
        
        # Find the original page for this route
        original_path = self._find_original_page(
            target_name,
            page_subpath,
            pages_dir,
        )
        
        # Calculate interceptor path
        interceptor_rel = page_file.relative_to(pages_dir)
        interceptor_path = "/" + str(interceptor_rel.parent).replace("\\", "/")
        
        # Determine slot name (if in @slot folder)
        slot_name = "modal"
        for parent in intercept_dir.parents:
            if parent.name.startswith("@"):
                slot_name = parent.name[1:]
                break
        
        rule = InterceptionRule(
            source_pattern="",  # Will be determined by referrer
            target_pattern=target_pattern,
            interception_type=interception_type,
            interceptor_path=str(page_file),
            original_path=original_path or target_pattern,
            slot_name=slot_name,
        )
        
        self._rules.append(rule)
    
    def _find_original_page(
        self,
        target_name: str,
        subpath: str,
        pages_dir: Path,
    ) -> Optional[str]:
        """Find the original (non-intercepted) page path."""
        # Try to find the actual page
        if subpath:
            candidate = pages_dir / target_name / subpath / "page.py"
        else:
            candidate = pages_dir / target_name / "page.py"
        
        if candidate.exists():
            return "/" + target_name + ("/" + subpath if subpath else "")
        
        # Try index.py
        if subpath:
            candidate = pages_dir / target_name / subpath / "index.py"
        else:
            candidate = pages_dir / target_name / "index.py"
        
        if candidate.exists():
            return "/" + target_name + ("/" + subpath if subpath else "")
        
        return None
    
    def get_map(self) -> Optional[CompiledInterceptionMap]:
        """Get the compiled interception map."""
        return self._map


# Global scanner
_interception_scanner = InterceptionScanner()


def get_interception_scanner() -> InterceptionScanner:
    """Get the global interception scanner."""
    return _interception_scanner


def scan_interceptions(pages_dir: Path) -> CompiledInterceptionMap:
    """Scan for intercepting routes."""
    return _interception_scanner.scan(pages_dir)


def get_interception_map() -> Optional[CompiledInterceptionMap]:
    """Get the compiled interception map."""
    return _interception_scanner.get_map()


def check_interception(
    path: str,
    referrer: Optional[str] = None,
) -> Optional[InterceptionMatch]:
    """
    Check if a path should be intercepted.
    
    Args:
        path: The path being navigated to
        referrer: The previous path (from Referer header or navigation)
    
    Returns:
        InterceptionMatch if path should be intercepted
    """
    interception_map = get_interception_map()
    if interception_map is None:
        return None
    
    return interception_map.should_intercept(path, referrer)

