"""
Codebase Search for AI Code Generation.

Allows the AI to search the PyNext codebase and documentation
to find correct patterns and examples when fixing errors.

Features:
- Search documentation (.md files)
- Search source code (.py files)
- Get specific pattern examples
- Fuzzy matching for queries

Example:
    searcher = CodebaseSearch()
    
    # Search for Signal usage
    results = searcher.search("Signal state management")
    
    # Get specific pattern
    pattern = searcher.get_pattern("signals")
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set


# ============================================
# Search Result
# ============================================

@dataclass
class SearchResult:
    """
    A single search result.
    
    Attributes:
        file_path: Path to the file
        content: Relevant content snippet
        line_number: Starting line number
        score: Relevance score (0-1)
        context: Additional context around the match
    """
    file_path: str
    content: str
    line_number: int = 0
    score: float = 0.0
    context: str = ""
    
    def format(self) -> str:
        """Format for display."""
        lines = [
            f"**File:** {self.file_path}",
            f"**Line:** {self.line_number}" if self.line_number else "",
            "",
            "```python" if self.file_path.endswith(".py") else "```",
            self.content,
            "```",
        ]
        return "\n".join(line for line in lines if line)


# ============================================
# Built-in Pattern Examples
# ============================================

PATTERN_EXAMPLES: Dict[str, str] = {
    "signals": """# Signal - Reactive State
from pynext import Signal, Computed, Effect

# Create a signal (state)
count = Signal(0)

# Read the value (call like a function)
current_value = count()

# Update the value
count.set(count() + 1)

# Derived/computed value (auto-updates)
doubled = Computed(lambda: count() * 2)

# Side effects (runs when dependencies change)
Effect(lambda: print(f"Count changed to: {count()}"))
""",

    "elements": """# PyNext HTML Elements
from pynext import div, h1, p, button, span, input_, form, a, img, ul, li

# Basic element with children
div(class_="container")(
    h1("Hello World"),
    p("This is a paragraph"),
)

# Element with attributes
button(
    class_="btn btn-primary",
    type_="submit",
    on_click=handle_click
)("Click Me")

# Input element (note: input_ not input)
input_(
    type_="text",
    name="email",
    placeholder="Enter email",
    on_input=handle_input
)

# Link
a(href="/about", class_="link")("About Us")
""",

    "islands": """# Islands - Client-Side Interactivity
from pynext import Signal, div, button
from pynext.islands import island

@island  # This decorator makes it interactive on the client
def Counter():
    count = Signal(0)
    
    def increment():
        count.set(count() + 1)
    
    return div(class_="counter")(
        button(on_click=increment)(f"Count: {count()}")
    )

@island
def SearchBox():
    query = Signal("")
    results = Signal([])
    
    async def search():
        # Fetch results...
        results.set(await fetch_results(query()))
    
    return div(
        input_(
            type_="text",
            on_input=lambda e: query.set(e.target.value)
        ),
        button(on_click=search)("Search"),
        ul()(
            *[li(r) for r in results()]
        )
    )
""",

    "actions": """# Server Actions - Form Handling & Mutations
from pynext.actions import action, ActionError
from pynext import form, input_, button, div

@action
async def create_user(form_data: dict):
    # Validate
    email = form_data.get("email", "").strip()
    if not email:
        raise ActionError("Email is required", field="email")
    
    if "@" not in email:
        raise ActionError("Invalid email format", field="email")
    
    # Create user in database
    user = await db.users.create(email=email)
    
    # Return success
    return {"success": True, "user_id": user.id}

# Usage in a component
def SignupForm():
    return form(action=create_user)(
        input_(type_="email", name="email", placeholder="Email"),
        button(type_="submit")("Sign Up")
    )
""",

    "api": """# API Routes
from pynext.api import api, Request, Response

@api
async def GET(request: Request):
    # Get query parameters
    page = request.query_params.get("page", "1")
    
    # Fetch data
    items = await db.items.all()
    
    return Response.json({
        "items": items,
        "page": int(page)
    })

@api
async def POST(request: Request):
    # Parse JSON body
    data = await request.json()
    
    # Validate
    if not data.get("name"):
        return Response.json(
            {"error": "Name required"},
            status=400
        )
    
    # Create item
    item = await db.items.create(**data)
    
    return Response.json(
        {"created": item},
        status=201
    )

@api
async def DELETE(request: Request):
    item_id = request.path_params.get("id")
    await db.items.delete(id=item_id)
    return Response.json({"deleted": True})
""",

    "pages": """# Pages - File-based Routing
# pages/index.py -> /
# pages/about.py -> /about
# pages/blog/[slug].py -> /blog/:slug

from pynext import div, h1, p, a

# Basic page
def page():
    return div(class_="container")(
        h1("Welcome"),
        p("This is the home page"),
        a(href="/about")("About Us")
    )

# Page with dynamic params
# File: pages/blog/[slug].py
async def page(params):
    slug = params.get("slug")
    post = await db.posts.get(slug=slug)
    
    return div(
        h1(post.title),
        p(post.content)
    )
""",

    "layouts": """# Layouts - Shared UI Wrapper
# pages/layout.py wraps all pages in that directory

from pynext import div, header, nav, main, footer, a

def layout(children):
    return div(class_="min-h-screen flex flex-col")(
        header(class_="bg-gray-900 text-white")(
            nav(class_="container mx-auto p-4")(
                a(href="/", class_="font-bold")("MyApp"),
                a(href="/about", class_="ml-4")("About"),
            )
        ),
        main(class_="flex-1 container mx-auto p-4")(
            children  # Page content goes here
        ),
        footer(class_="bg-gray-100 p-4 text-center")(
            "© 2024 MyApp"
        )
    )
""",

    "database": """# Database - Table Definition & Queries
from pynext.db import Table, Column, types

class User(Table):
    id = Column(types.Integer, primary_key=True)
    email = Column(types.String, unique=True)
    name = Column(types.String)
    created_at = Column(types.DateTime, default="now()")

# Queries
users = await User.all()
user = await User.get(id=1)
user = await User.first(email="test@example.com")

# Create
new_user = await User.create(
    email="new@example.com",
    name="New User"
)

# Update
await User.update(id=1, name="Updated Name")

# Delete
await User.delete(id=1)

# Filtering
active_users = await User.where(active=True).all()
""",

    "live_queries": """# Live Queries - Real-time Data
from pynext.db.live import LiveQuery

# Create a live query that auto-updates
@island
def UserList():
    users = User.live().where(active=True).order_by("name")
    
    # users() returns current data
    # users.loading() returns loading state
    # users.error() returns any error
    
    if users.loading():
        return div("Loading...")
    
    if users.error():
        return div(f"Error: {users.error()}")
    
    return ul()(
        *[li(user.name) for user in users()]
    )
""",
}


# ============================================
# Codebase Search
# ============================================

class CodebaseSearch:
    """
    Search the PyNext codebase for patterns and examples.
    
    The searcher can:
    1. Search documentation files for explanations
    2. Search source code for implementation examples
    3. Return pre-built pattern examples
    
    Attributes:
        docs_path: Path to documentation
        source_path: Path to source code
        max_results: Maximum results to return
    """
    
    def __init__(
        self,
        docs_path: Optional[str] = None,
        source_path: Optional[str] = None,
        max_results: int = 5
    ):
        """
        Initialize the searcher.
        
        Args:
            docs_path: Path to docs (default: auto-detect)
            source_path: Path to source (default: auto-detect)
            max_results: Max results per search
        """
        self.max_results = max_results
        
        # Auto-detect paths
        base_path = self._find_project_root()
        self.docs_path = Path(docs_path) if docs_path else base_path / "docs"
        self.source_path = Path(source_path) if source_path else base_path / "pynext"
    
    def _find_project_root(self) -> Path:
        """Find the PyNext project root."""
        # Start from this file's location
        current = Path(__file__).parent
        
        # Walk up looking for pyproject.toml or setup.py
        while current != current.parent:
            if (current / "pyproject.toml").exists():
                return current
            if (current / "setup.py").exists():
                return current
            current = current.parent
        
        # Fallback to cwd
        return Path.cwd()
    
    def search(self, query: str) -> List[SearchResult]:
        """
        Search codebase for relevant content.
        
        Args:
            query: Search query
        
        Returns:
            List of SearchResult objects
        """
        results = []
        
        # First, check built-in patterns
        pattern_results = self._search_patterns(query)
        results.extend(pattern_results)
        
        # Then search docs
        if self.docs_path.exists():
            doc_results = self._search_docs(query)
            results.extend(doc_results)
        
        # Then search source
        if self.source_path.exists():
            source_results = self._search_source(query)
            results.extend(source_results)
        
        # Sort by score and limit
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:self.max_results]
    
    def _search_patterns(self, query: str) -> List[SearchResult]:
        """Search built-in patterns."""
        results = []
        query_lower = query.lower()
        
        # Keywords to pattern mapping
        keyword_mapping = {
            "signal": "signals",
            "state": "signals",
            "reactive": "signals",
            "element": "elements",
            "div": "elements",
            "button": "elements",
            "html": "elements",
            "island": "islands",
            "interactive": "islands",
            "client": "islands",
            "action": "actions",
            "form": "actions",
            "mutation": "actions",
            "api": "api",
            "route": "api",
            "endpoint": "api",
            "page": "pages",
            "routing": "pages",
            "layout": "layouts",
            "wrapper": "layouts",
            "database": "database",
            "table": "database",
            "query": "database",
            "live": "live_queries",
            "realtime": "live_queries",
        }
        
        # Find matching patterns
        matched_patterns: Set[str] = set()
        for keyword, pattern_name in keyword_mapping.items():
            if keyword in query_lower:
                matched_patterns.add(pattern_name)
        
        # Create results for matched patterns
        for pattern_name in matched_patterns:
            if pattern_name in PATTERN_EXAMPLES:
                results.append(SearchResult(
                    file_path=f"[Built-in Pattern: {pattern_name}]",
                    content=PATTERN_EXAMPLES[pattern_name],
                    score=1.5,  # Higher than doc results (max 1.0) for direct pattern matches
                ))
        
        return results
    
    def _search_docs(self, query: str) -> List[SearchResult]:
        """Search documentation files."""
        results = []
        query_words = set(query.lower().split())
        
        try:
            for md_file in self.docs_path.rglob("*.md"):
                try:
                    content = md_file.read_text(encoding="utf-8")
                    score = self._calculate_relevance(content, query_words)
                    
                    if score > 0.3:  # Minimum threshold
                        # Extract relevant section
                        snippet = self._extract_relevant_section(content, query_words)
                        
                        results.append(SearchResult(
                            file_path=str(md_file.relative_to(self.docs_path)),
                            content=snippet,
                            score=score,
                        ))
                except Exception:
                    continue
        except Exception:
            pass
        
        return results
    
    def _search_source(self, query: str) -> List[SearchResult]:
        """Search source code files."""
        results = []
        query_words = set(query.lower().split())
        
        try:
            for py_file in self.source_path.rglob("*.py"):
                # Skip test files and __pycache__
                if "test" in str(py_file) or "__pycache__" in str(py_file):
                    continue
                
                try:
                    content = py_file.read_text(encoding="utf-8")
                    score = self._calculate_relevance(content, query_words)
                    
                    if score > 0.2:  # Lower threshold for source
                        # Extract relevant code
                        snippet = self._extract_code_section(content, query_words)
                        
                        results.append(SearchResult(
                            file_path=str(py_file.relative_to(self.source_path)),
                            content=snippet,
                            score=score * 0.8,  # Slightly lower score for source
                        ))
                except Exception:
                    continue
        except Exception:
            pass
        
        return results
    
    def _calculate_relevance(self, content: str, query_words: Set[str]) -> float:
        """Calculate relevance score for content."""
        content_lower = content.lower()
        
        # Count matching words
        matches = sum(1 for word in query_words if word in content_lower)
        
        # Calculate score
        if not query_words:
            return 0.0
        
        return matches / len(query_words)
    
    def _extract_relevant_section(
        self,
        content: str,
        query_words: Set[str],
        max_lines: int = 30
    ) -> str:
        """Extract the most relevant section from content."""
        lines = content.split("\n")
        best_start = 0
        best_score = 0
        
        # Slide a window to find best section
        window_size = max_lines
        for i in range(len(lines) - window_size + 1):
            window = "\n".join(lines[i:i + window_size])
            score = self._calculate_relevance(window, query_words)
            
            if score > best_score:
                best_score = score
                best_start = i
        
        return "\n".join(lines[best_start:best_start + window_size])
    
    def _extract_code_section(
        self,
        content: str,
        query_words: Set[str],
        max_lines: int = 40
    ) -> str:
        """Extract relevant code section."""
        lines = content.split("\n")
        
        # Find lines containing query words
        relevant_lines = []
        for i, line in enumerate(lines):
            if any(word in line.lower() for word in query_words):
                # Get context around the line
                start = max(0, i - 5)
                end = min(len(lines), i + 15)
                relevant_lines.extend(range(start, end))
        
        if not relevant_lines:
            return content[:1000]  # Fallback to beginning
        
        # Get unique lines in order
        relevant_lines = sorted(set(relevant_lines))[:max_lines]
        return "\n".join(lines[i] for i in relevant_lines)
    
    def get_pattern(self, pattern_name: str) -> Optional[str]:
        """
        Get a specific pattern example.
        
        Args:
            pattern_name: Name of the pattern (signals, elements, etc.)
        
        Returns:
            Pattern example string or None if not found
        """
        return PATTERN_EXAMPLES.get(pattern_name)
    
    def get_all_patterns(self) -> Dict[str, str]:
        """Get all built-in pattern examples."""
        return PATTERN_EXAMPLES.copy()
    
    def format_results(self, results: List[SearchResult]) -> str:
        """
        Format search results for AI consumption.
        
        Args:
            results: List of SearchResult objects
        
        Returns:
            Formatted string with all results
        """
        if not results:
            return "No relevant results found."
        
        parts = []
        for i, result in enumerate(results, 1):
            parts.append(f"### Result {i} (Score: {result.score:.0%})")
            parts.append(result.format())
            parts.append("")
        
        return "\n".join(parts)


# ============================================
# Quick Search Functions
# ============================================

def search_codebase(query: str) -> str:
    """
    Quick search function.
    
    Args:
        query: Search query
    
    Returns:
        Formatted results string
    """
    searcher = CodebaseSearch()
    results = searcher.search(query)
    return searcher.format_results(results)


def get_pattern_example(pattern: str) -> str:
    """
    Get a specific pattern example.
    
    Args:
        pattern: Pattern name (signals, elements, islands, etc.)
    
    Returns:
        Pattern example or error message
    """
    searcher = CodebaseSearch()
    example = searcher.get_pattern(pattern)
    
    if example:
        return example
    
    available = ", ".join(PATTERN_EXAMPLES.keys())
    return f"Pattern '{pattern}' not found. Available: {available}"

