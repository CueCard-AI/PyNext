"""
Path Resolution for PyNext.

Auto-detects project structure:
- src/pages/ (if exists) 
- pages/ (fallback)

SolidJS Principle: Zero configuration - just works
AI-Friendly: No config files, no setup steps

Example project structures:

    # Standard (detected automatically)
    my-app/
    ├── pages/
    ├── components/
    └── public/
    
    # With src (detected automatically)
    my-app/
    ├── src/
    │   ├── pages/
    │   └── components/
    └── public/
"""

from pathlib import Path
from typing import Tuple, List, Optional
from dataclasses import dataclass


@dataclass
class ProjectPaths:
    """
    Resolved project paths.
    
    All paths are absolute and resolved. Use these paths
    throughout the application for consistency.
    """
    pages: Path         # pages/ or src/pages/
    components: Path    # components/ or src/components/
    lib: Path          # lib/ or src/lib/
    public: Path       # public/ (always at root)
    root: Path         # Project root
    
    @property
    def uses_src(self) -> bool:
        """Check if using src/ structure."""
        return "src" in self.pages.parts
    
    @property
    def styles(self) -> Path:
        """Get styles directory."""
        if self.uses_src:
            return self.root / "src" / "styles"
        return self.root / "styles"
    
    @property
    def api(self) -> Path:
        """Get API routes directory."""
        return self.pages / "api"
    
    def relative(self, path: Path) -> Path:
        """Get path relative to project root."""
        try:
            return path.relative_to(self.root)
        except ValueError:
            return path
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "pages": str(self.pages),
            "components": str(self.components),
            "lib": str(self.lib),
            "public": str(self.public),
            "root": str(self.root),
            "uses_src": self.uses_src,
        }


def resolve_paths(root: Optional[Path] = None) -> ProjectPaths:
    """
    Resolve project paths, auto-detecting src/ structure.
    
    This function checks if the project uses a src/ directory
    structure and returns appropriate paths. It requires no
    configuration - just place your files and it works.
    
    Args:
        root: Project root (defaults to current working directory)
    
    Returns:
        ProjectPaths with resolved directories
    
    Example:
        paths = resolve_paths()
        print(paths.pages)      # /project/src/pages or /project/pages
        print(paths.uses_src)   # True or False
        
        # Use in imports
        from pynext.core.paths import resolve_paths
        paths = resolve_paths()
        for page in paths.pages.glob("**/page.py"):
            print(page)
    """
    root = Path(root or Path.cwd()).resolve()
    
    # Check for src/ structure (priority)
    src_pages = root / "src" / "pages"
    if src_pages.exists():
        return ProjectPaths(
            pages=src_pages,
            components=root / "src" / "components",
            lib=root / "src" / "lib",
            public=root / "public",
            root=root,
        )
    
    # Standard structure
    return ProjectPaths(
        pages=root / "pages",
        components=root / "components",
        lib=root / "lib",
        public=root / "public",
        root=root,
    )


def detect_structure(root: Optional[Path] = None) -> str:
    """
    Detect project structure type.
    
    Args:
        root: Project root
    
    Returns:
        "src" if using src/ structure, "standard" otherwise
    
    Example:
        structure = detect_structure()
        print(f"Using {structure} structure")
    """
    root = Path(root or Path.cwd()).resolve()
    
    if (root / "src" / "pages").exists():
        return "src"
    return "standard"


def get_watch_dirs(root: Optional[Path] = None) -> List[Path]:
    """
    Get directories to watch for hot reload.
    
    Returns all existing project directories that should be
    watched for changes during development.
    
    Args:
        root: Project root
    
    Returns:
        List of existing directories to watch
    
    Example:
        from watchfiles import watch
        
        dirs = get_watch_dirs()
        for changes in watch(*dirs):
            print("Files changed:", changes)
    """
    paths = resolve_paths(root)
    
    dirs = []
    for path in [paths.pages, paths.components, paths.lib, paths.public, paths.styles]:
        if path.exists():
            dirs.append(path)
    
    return dirs


def ensure_structure(
    root: Optional[Path] = None, 
    use_src: bool = False,
) -> ProjectPaths:
    """
    Create project directory structure.
    
    This function creates all necessary directories for a PyNext
    project. Use this when initializing a new project.
    
    Args:
        root: Project root
        use_src: Whether to use src/ structure
    
    Returns:
        ProjectPaths after creating directories
    
    Example:
        # Create standard structure
        paths = ensure_structure()
        
        # Create src/ structure
        paths = ensure_structure(use_src=True)
        
        # Create in specific directory
        paths = ensure_structure(Path("/path/to/project"))
    """
    root = Path(root or Path.cwd()).resolve()
    
    if use_src:
        (root / "src" / "pages").mkdir(parents=True, exist_ok=True)
        (root / "src" / "components").mkdir(parents=True, exist_ok=True)
        (root / "src" / "lib").mkdir(parents=True, exist_ok=True)
        (root / "src" / "styles").mkdir(parents=True, exist_ok=True)
    else:
        (root / "pages").mkdir(parents=True, exist_ok=True)
        (root / "components").mkdir(parents=True, exist_ok=True)
        (root / "lib").mkdir(parents=True, exist_ok=True)
        (root / "styles").mkdir(parents=True, exist_ok=True)
    
    (root / "public").mkdir(parents=True, exist_ok=True)
    
    return resolve_paths(root)


def find_project_root(start: Optional[Path] = None) -> Optional[Path]:
    """
    Find the project root by looking for marker files.
    
    Searches upward from the start directory looking for:
    - pynext.config.py
    - pyproject.toml with [tool.pynext]
    - pages/ directory
    
    Args:
        start: Directory to start searching from
    
    Returns:
        Project root path, or None if not found
    
    Example:
        root = find_project_root()
        if root:
            print(f"Found project at {root}")
        else:
            print("Not in a PyNext project")
    """
    current = Path(start or Path.cwd()).resolve()
    
    # Search up to filesystem root
    while current != current.parent:
        # Check for PyNext markers
        if (current / "pynext.config.py").exists():
            return current
        
        if (current / "pages").exists() and (current / "pages").is_dir():
            # Verify it looks like a pages directory
            if list((current / "pages").glob("**/page.py")):
                return current
        
        if (current / "src" / "pages").exists():
            return current
        
        # Check pyproject.toml for [tool.pynext]
        pyproject = current / "pyproject.toml"
        if pyproject.exists():
            try:
                content = pyproject.read_text()
                if "[tool.pynext]" in content:
                    return current
            except Exception:
                pass
        
        current = current.parent
    
    return None


def validate_structure(root: Optional[Path] = None) -> Tuple[bool, List[str]]:
    """
    Validate project structure.
    
    Checks that the project has required directories and files.
    
    Args:
        root: Project root
    
    Returns:
        Tuple of (is_valid, list of issues)
    
    Example:
        valid, issues = validate_structure()
        if not valid:
            for issue in issues:
                print(f"  - {issue}")
    """
    paths = resolve_paths(root)
    issues = []
    errors = 0  # Critical issues that make project invalid
    
    # Check required directories
    if not paths.pages.exists():
        issues.append(f"Missing pages directory: {paths.pages}")
        errors += 1
    
    # Check for at least one page
    if paths.pages.exists():
        pages = list(paths.pages.glob("**/page.py"))
        if not pages:
            issues.append("No page.py files found in pages directory")
            errors += 1
    
    # Check public directory (optional - just a warning, not a blocker)
    # We don't add to issues since it's truly optional
    
    return errors == 0, issues


def get_page_url(page_path: Path, paths: Optional[ProjectPaths] = None) -> str:
    """
    Convert a page file path to its URL.
    
    Args:
        page_path: Path to a page.py file
        paths: Project paths (auto-resolved if not provided)
    
    Returns:
        URL path like "/about" or "/blog/[slug]"
    
    Example:
        url = get_page_url(Path("pages/about/page.py"))
        print(url)  # "/about"
        
        url = get_page_url(Path("pages/blog/[slug]/page.py"))
        print(url)  # "/blog/[slug]"
    """
    if paths is None:
        paths = resolve_paths()
    
    try:
        # Get path relative to pages directory
        rel = page_path.relative_to(paths.pages)
    except ValueError:
        # Not under pages directory
        return "/" + str(page_path)
    
    # Remove page.py from the end
    parts = list(rel.parts)
    if parts and parts[-1] == "page.py":
        parts = parts[:-1]
    
    # Join to URL
    if not parts:
        return "/"
    
    return "/" + "/".join(parts)

