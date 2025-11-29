"""
PyNext Linting - Route Rules

Rules for proper route file conventions:
    PNX006: Invalid route name - route file doesn't match convention
    PNX007: Missing page export - page.py missing page() function
    PNX010: Missing metadata - page without Metadata export

Why These Rules:
    PyNext uses file-based routing. Files must follow conventions
    for the router to discover them correctly.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import List, Set

from pynext.lint.rules.base import BaseLinter, LintError


# Valid route file patterns
VALID_ROUTE_FILES = {
    "page.py",
    "layout.py",
    "loading.py",
    "error.py",
    "not-found.py",
    "template.py",
    "middleware.py",
    "route.py",
}

# Pattern for dynamic route segments
DYNAMIC_SEGMENT = re.compile(r"^\[[\w.]+\]$")
CATCH_ALL_SEGMENT = re.compile(r"^\[\.\.\.[\w]+\]$")
OPTIONAL_CATCH_ALL = re.compile(r"^\[\[\.\.\.[\w]+\]\]$")


class RouteLinter(BaseLinter):
    """
    Lint route files in PyNext code.
    
    Checks for:
    - PNX006: Invalid route file naming
    - PNX007: Missing page() function in page.py
    - PNX010: Missing Metadata in page.py
    """
    
    def check(
        self,
        source: str,
        filename: str,
        enabled_rules: Set[str],
    ) -> List[LintError]:
        """Check source for route issues."""
        self.errors = []
        self.filename = filename
        self.source = source
        self.enabled_rules = enabled_rules
        
        # Get file name
        file_path = Path(filename)
        file_name = file_path.name
        
        # Only check files in pages/ or app/ directories
        is_route_file = self._is_route_file(file_path)
        if not is_route_file:
            return self.errors
        
        # Parse source
        tree = self.parse_source(source)
        if tree is None:
            return self.errors
        
        # PNX006: Check file naming
        if not self._is_valid_route_filename(file_path):
            self._check_route_naming(file_path)
        
        # For page.py files, check for required exports
        if file_name == "page.py":
            self._check_page_exports(tree)
            self._check_metadata_export(tree)
        
        # For layout.py, check for required exports
        if file_name == "layout.py":
            self._check_layout_exports(tree)
        
        return self.errors
    
    def _is_route_file(self, file_path: Path) -> bool:
        """Check if file is in a routing directory."""
        parts = file_path.parts
        return any(p in ("pages", "app", "src") for p in parts)
    
    def _is_valid_route_filename(self, file_path: Path) -> bool:
        """Check if filename follows conventions."""
        name = file_path.name
        
        # Standard route files
        if name in VALID_ROUTE_FILES:
            return True
        
        # API routes
        if name.startswith("api.") and name.endswith(".py"):
            return True
        
        # Dynamic segments in directory names are fine
        parent = file_path.parent.name
        if DYNAMIC_SEGMENT.match(parent) or CATCH_ALL_SEGMENT.match(parent):
            return True
        
        return False
    
    def _check_route_naming(self, file_path: Path) -> None:
        """Check route file naming convention."""
        name = file_path.name
        
        # Check for common mistakes
        if name.endswith("_page.py"):
            self.add_error(
                "PNX006",
                f"Route file '{name}' should be named 'page.py' (in a directory).",
                1,
                0,
                "warning",
                fix="Rename to page.py",
                fix_description="Use page.py in a directory instead",
            )
        
        elif name.endswith("Page.py"):
            self.add_error(
                "PNX006",
                f"Route file '{name}' uses PascalCase. Use 'page.py' instead.",
                1,
                0,
                "warning",
                fix="Rename to page.py",
                fix_description="Route files should be lowercase",
            )
        
        elif name.endswith(".route.py"):
            self.add_error(
                "PNX006",
                f"Route file '{name}' should be 'route.py' (for API routes).",
                1,
                0,
                "warning",
            )
    
    def _check_page_exports(self, tree: ast.AST) -> None:
        """Check that page.py exports a page() function."""
        has_page_function = False
        has_page_decorator = False
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name == "page":
                    has_page_function = True
                
                # Check for @page decorator
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name) and decorator.id == "page":
                        has_page_decorator = True
                    elif isinstance(decorator, ast.Call):
                        if isinstance(decorator.func, ast.Name) and decorator.func.id == "page":
                            has_page_decorator = True
        
        if not has_page_function and not has_page_decorator:
            self.add_error(
                "PNX007",
                "page.py is missing a page() function. "
                "Define a function named 'page' or use the @page decorator.",
                1,
                0,
                "error",
                fix="""
@page
def page():
    return div()["Page content"]
""",
                fix_description="Add a page() function",
            )
    
    def _check_layout_exports(self, tree: ast.AST) -> None:
        """Check that layout.py exports a layout() function."""
        has_layout_function = False
        has_layout_decorator = False
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name == "layout":
                    has_layout_function = True
                
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name) and decorator.id == "layout":
                        has_layout_decorator = True
        
        if not has_layout_function and not has_layout_decorator:
            self.add_error(
                "PNX007",
                "layout.py is missing a layout() function. "
                "Define a function named 'layout' or use the @layout decorator.",
                1,
                0,
                "error",
                fix="""
@layout
def layout(children):
    return div()[children]
""",
                fix_description="Add a layout() function",
            )
    
    def _check_metadata_export(self, tree: ast.AST) -> None:
        """Check for Metadata export in page files."""
        has_metadata = False
        
        for node in ast.walk(tree):
            # Check for Metadata assignment
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "metadata":
                        has_metadata = True
            
            # Check for generate_metadata function
            if isinstance(node, ast.FunctionDef):
                if node.name == "generate_metadata":
                    has_metadata = True
        
        if not has_metadata:
            self.add_error(
                "PNX010",
                "Page is missing Metadata. Add metadata for SEO.",
                1,
                0,
                "info",
                fix="""
metadata = Metadata(
    title="Page Title",
    description="Page description for SEO",
)
""",
                fix_description="Add Metadata export",
            )
    
    @staticmethod
    def explain(rule_id: str) -> str:
        """Get detailed explanation for route rules."""
        explanations = {
            "PNX006": """
## PNX006: Invalid Route Name

The route file doesn't follow PyNext naming conventions.

### PyNext Route File Conventions:

```
pages/
├── page.py              # Home page (/)
├── about/
│   └── page.py          # About page (/about)
├── blog/
│   ├── page.py          # Blog index (/blog)
│   ├── [slug]/
│   │   └── page.py      # Blog post (/blog/:slug)
│   └── [...catchall]/
│       └── page.py      # Catch-all (/blog/*)
├── layout.py            # Root layout
├── loading.py           # Loading state
├── error.py             # Error boundary
└── not-found.py         # 404 page
```

### Bad:
```
pages/
├── home_page.py         # ❌ Should be page.py in root
├── AboutPage.py         # ❌ PascalCase not allowed
└── blog.route.py        # ❌ Should be blog/page.py
```

### How to Fix:
- Use `page.py` for page components
- Use directories for route segments
- Use `[param]` for dynamic segments
- Use lowercase with hyphens for directories
""",
            "PNX007": """
## PNX007: Missing Page Export

The page.py file doesn't export a `page()` function.

### Bad:
```python
# pages/about/page.py

def AboutPage():  # Wrong name!
    return div()["About us"]
```

### Good:
```python
# pages/about/page.py

def page():  # Correct!
    return div()["About us"]
```

Or with decorator:
```python
# pages/about/page.py

@page
def my_about_page():
    return div()["About us"]
```

### Why This Matters:
- PyNext looks for a `page()` function or `@page` decorator
- Without it, the route won't be registered
- The page will return 404

### How to Fix:
- Name your function `page()`
- Or use the `@page` decorator on any function
""",
            "PNX010": """
## PNX010: Missing Metadata

The page doesn't define metadata for SEO.

### Bad:
```python
def page():
    return div()["My Page"]
    # No metadata defined!
```

### Good:
```python
from pynext import Metadata

metadata = Metadata(
    title="My Page - MySite",
    description="A description for search engines",
    keywords=["keyword1", "keyword2"],
)

def page():
    return div()["My Page"]
```

Or generate dynamically:
```python
def generate_metadata(params):
    return Metadata(
        title=f"Post: {params['slug']}",
        description="Dynamic description",
    )

def page():
    return div()["Post content"]
```

### Why This Matters:
- Search engines use metadata to index pages
- Social media uses it for previews
- Missing metadata hurts SEO

### What to Include:
- `title`: Page title (shown in browser tab)
- `description`: 150-160 character description
- `keywords`: Relevant keywords (optional)
- `og_image`: Social media preview image (optional)
""",
        }
        return explanations.get(rule_id, f"No detailed explanation for {rule_id}")

