"""
Context Builder - Builds optimal prompts for AI generation.

Assembles the best possible context from:
- Retrieved documentation
- Code examples
- Pattern templates
- API signatures

Fits everything within token budget for the AI prompt.

Example:
    builder = ContextBuilder(retriever, patterns)
    
    # Build context for a task
    context = builder.build_context(
        task="Create a real-time chat component",
        max_tokens=8000,
    )
    
    # Build context for a specific file
    file_context = builder.build_file_context(
        file_type="island",
        requirements={"purpose": "Chat widget", "features": ["messages", "typing"]},
    )
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import re


@dataclass
class ContextSection:
    """A section of context for the prompt."""
    title: str
    content: str
    priority: int  # Higher = more important
    estimated_tokens: int


class ContextBuilder:
    """
    Builds optimal context for AI code generation.
    
    Strategy:
    1. Identify what the task needs
    2. Retrieve relevant documentation
    3. Get similar code examples
    4. Include API signatures
    5. Add pattern templates
    6. Prioritize by relevance
    7. Fit within token budget
    """
    
    # Approximate chars per token (conservative estimate)
    CHARS_PER_TOKEN = 4
    
    def __init__(
        self,
        retriever: Any,  # SemanticRetriever
        patterns: Any,  # PatternLibrary
    ):
        """
        Initialize context builder.
        
        Args:
            retriever: SemanticRetriever for searching
            patterns: PatternLibrary for templates
        """
        self.retriever = retriever
        self.patterns = patterns
    
    def build_context(
        self,
        task: str,
        max_tokens: int = 8000,
        include_patterns: bool = True,
        include_examples: bool = True,
        include_api: bool = True,
    ) -> str:
        """
        Build optimal context for a generation task.
        
        Args:
            task: The generation task description
            max_tokens: Maximum tokens for context
            include_patterns: Include pattern templates
            include_examples: Include code examples
            include_api: Include API signatures
        
        Returns:
            Formatted context string
        """
        sections: List[ContextSection] = []
        
        # Always include PyNext overview
        sections.append(self._get_pynext_overview())
        
        # Search for relevant content
        if self.retriever:
            # Documentation
            doc_results = self.retriever.search(
                task,
                top_k=5,
                filters={"chunk_type": "docs"},
            )
            if doc_results:
                sections.append(self._format_docs_section(doc_results))
            
            # Examples
            if include_examples:
                example_results = self.retriever.search(
                    task,
                    top_k=3,
                    filters={"chunk_type": "example"},
                )
                if example_results:
                    sections.append(self._format_examples_section(example_results))
            
            # API signatures
            if include_api:
                api_results = self.retriever.search(
                    task,
                    top_k=5,
                    filters={"chunk_type": "api"},
                )
                if api_results:
                    sections.append(self._format_api_section(api_results))
        
        # Patterns
        if include_patterns and self.patterns:
            relevant_patterns = self.patterns.get_patterns_for(task)
            if relevant_patterns:
                sections.append(self._format_patterns_section(relevant_patterns))
        
        # Sort by priority and fit within budget
        sections.sort(key=lambda s: s.priority, reverse=True)
        
        return self._assemble_context(sections, max_tokens)
    
    def build_file_context(
        self,
        file_type: str,
        requirements: Dict[str, Any],
        existing_files: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Build context for generating a specific file.
        
        Args:
            file_type: Type of file (page, component, api, etc.)
            requirements: File requirements
            existing_files: Already generated files for imports
        
        Returns:
            Formatted context for the specific file
        """
        sections: List[ContextSection] = []
        
        # PyNext overview (condensed)
        sections.append(self._get_pynext_overview(condensed=True))
        
        # File type specific patterns
        type_patterns = self._get_patterns_for_type(file_type)
        if type_patterns:
            sections.append(self._format_patterns_section(
                type_patterns,
                title=f"Patterns for {file_type}",
            ))
        
        # Existing files context (for imports)
        if existing_files:
            sections.append(self._format_existing_files(existing_files))
        
        # Requirements
        sections.append(self._format_requirements(requirements))
        
        return self._assemble_context(sections, max_tokens=4000)
    
    def _get_pynext_overview(self, condensed: bool = False) -> ContextSection:
        """Get PyNext framework overview."""
        if condensed:
            content = """## PyNext Quick Reference

### HTML Elements
```python
from pynext import div, h1, p, button, span, input_, form, a, ul, li

div(class_="container")(child1, child2)  # Note: class_ not class
button(on_click=handler)("Click")        # Events: on_click, on_input, etc.
input_(type_="text", name="field")       # Note: input_ not input
```

### Signals (Reactive State)
```python
from pynext import Signal, Computed, Effect

count = Signal(0)      # Create state
value = count()        # Read (call like function)
count.set(value + 1)   # Write with .set()
```

### Islands (Client Interactivity)
```python
from pynext.islands import island

@island  # Decorator makes it interactive
def MyComponent():
    state = Signal(0)
    return button(on_click=lambda: state.set(state() + 1))(state())
```

### Server Actions
```python
from pynext.actions import action, ActionError

@action
async def my_action(form_data: dict):
    if not form_data.get("field"):
        raise ActionError("Required", field="field")
    return {"success": True}
```
"""
        else:
            content = """## PyNext Framework Overview

PyNext is a Python web framework with:
- Fine-grained reactivity (SolidJS principles)
- Python syntax for HTML elements
- File-based routing
- Server-side rendering with islands architecture

### HTML Elements
```python
from pynext import div, h1, p, button, span, input_, form, a, img, ul, li

# Basic usage - attributes in first call, children in second
div(class_="container mx-auto p-4")(
    h1(class_="text-2xl font-bold")("Title"),
    p("Paragraph content"),
)

# Important: Use class_ (not class), input_ (not input)
button(class_="btn", on_click=handler)("Click Me")
input_(type_="text", name="email", placeholder="Email")
```

### Signals (Reactive State)
```python
from pynext import Signal, Computed, Effect

# Create reactive state
count = Signal(0)

# Read value - call like a function
current = count()

# Write value - use .set()
count.set(count() + 1)

# Computed - auto-updates when dependencies change
doubled = Computed(lambda: count() * 2)

# Effect - runs when dependencies change
Effect(lambda: print(f"Count: {count()}"))
```

### Islands (Client Interactivity)
```python
from pynext.islands import island

@island  # This decorator makes component interactive on client
def Counter():
    count = Signal(0)
    
    return div(class_="flex items-center gap-2")(
        button(on_click=lambda: count.set(count() - 1))("-"),
        span(count()),
        button(on_click=lambda: count.set(count() + 1))("+"),
    )
```

### Server Actions (Form Handling)
```python
from pynext.actions import action, ActionError

@action
async def create_item(form_data: dict):
    name = form_data.get("name", "").strip()
    if not name:
        raise ActionError("Name is required", field="name")
    
    # Save to database
    item = await Item.create(name=name)
    return {"success": True, "id": item.id}
```

### API Routes
```python
from pynext.api import api, Request, Response

@api
async def GET(request: Request):
    items = await Item.all()
    return Response.json([i.to_dict() for i in items])

@api
async def POST(request: Request):
    data = await request.json()
    item = await Item.create(**data)
    return Response.json(item.to_dict(), status=201)
```

### Database Models
```python
from pynext.db import Table, Column, types

class User(Table):
    id = Column(types.Integer, primary_key=True)
    email = Column(types.String, unique=True)
    name = Column(types.String)

# Queries
users = await User.all()
user = await User.get(id=1)
user = await User.create(email="...", name="...")
```
"""
        
        return ContextSection(
            title="PyNext Overview",
            content=content,
            priority=100,  # Always include
            estimated_tokens=len(content) // self.CHARS_PER_TOKEN,
        )
    
    def _format_docs_section(self, results: List[Any]) -> ContextSection:
        """Format documentation results."""
        content_parts = ["## Relevant Documentation\n"]
        
        for result in results[:3]:
            source = result.chunk.source.split("/")[-1] if "/" in result.chunk.source else result.chunk.source
            header = result.chunk.metadata.get("header", "")
            content_parts.append(f"### {header} (from {source})\n")
            content_parts.append(result.chunk.content[:1500])
            content_parts.append("\n")
        
        content = "\n".join(content_parts)
        
        return ContextSection(
            title="Documentation",
            content=content,
            priority=80,
            estimated_tokens=len(content) // self.CHARS_PER_TOKEN,
        )
    
    def _format_examples_section(self, results: List[Any]) -> ContextSection:
        """Format code examples."""
        content_parts = ["## Code Examples\n"]
        
        for result in results[:3]:
            context = result.chunk.metadata.get("context", "")
            content_parts.append(f"### Example: {context}\n")
            content_parts.append("```python")
            content_parts.append(result.chunk.content[:1000])
            content_parts.append("```\n")
        
        content = "\n".join(content_parts)
        
        return ContextSection(
            title="Examples",
            content=content,
            priority=70,
            estimated_tokens=len(content) // self.CHARS_PER_TOKEN,
        )
    
    def _format_api_section(self, results: List[Any]) -> ContextSection:
        """Format API signatures."""
        content_parts = ["## API Reference\n"]
        
        for result in results[:5]:
            name = result.chunk.metadata.get("name", "")
            content_parts.append(f"### {name}\n")
            content_parts.append("```python")
            content_parts.append(result.chunk.content)
            content_parts.append("```\n")
        
        content = "\n".join(content_parts)
        
        return ContextSection(
            title="API",
            content=content,
            priority=60,
            estimated_tokens=len(content) // self.CHARS_PER_TOKEN,
        )
    
    def _format_patterns_section(
        self,
        patterns: List[Any],
        title: str = "Relevant Patterns",
    ) -> ContextSection:
        """Format patterns."""
        content_parts = [f"## {title}\n"]
        
        for pattern in patterns[:3]:
            content_parts.append(f"### Pattern: {pattern.name}\n")
            content_parts.append(f"*{pattern.description}*\n")
            content_parts.append("```python")
            content_parts.append(pattern.code_template[:1500])
            content_parts.append("```\n")
        
        content = "\n".join(content_parts)
        
        return ContextSection(
            title="Patterns",
            content=content,
            priority=90,  # Patterns are very useful
            estimated_tokens=len(content) // self.CHARS_PER_TOKEN,
        )
    
    def _format_existing_files(self, files: Dict[str, str]) -> ContextSection:
        """Format existing files for import context."""
        content_parts = ["## Already Generated Files\n"]
        content_parts.append("Use these for imports and consistency:\n")
        
        for path, code in list(files.items())[:5]:
            content_parts.append(f"### {path}\n")
            content_parts.append("```python")
            # Just show imports and function signatures
            lines = code.split("\n")
            relevant_lines = []
            for line in lines[:30]:
                if line.startswith("import ") or line.startswith("from "):
                    relevant_lines.append(line)
                elif line.startswith("def ") or line.startswith("async def "):
                    relevant_lines.append(line)
                elif line.startswith("class "):
                    relevant_lines.append(line)
            content_parts.append("\n".join(relevant_lines))
            content_parts.append("```\n")
        
        content = "\n".join(content_parts)
        
        return ContextSection(
            title="Existing Files",
            content=content,
            priority=85,  # Important for consistency
            estimated_tokens=len(content) // self.CHARS_PER_TOKEN,
        )
    
    def _format_requirements(self, requirements: Dict[str, Any]) -> ContextSection:
        """Format requirements."""
        content_parts = ["## Requirements\n"]
        
        for key, value in requirements.items():
            content_parts.append(f"- **{key}**: {value}")
        
        content = "\n".join(content_parts)
        
        return ContextSection(
            title="Requirements",
            content=content,
            priority=95,  # Very important
            estimated_tokens=len(content) // self.CHARS_PER_TOKEN,
        )
    
    def _get_patterns_for_type(self, file_type: str) -> List[Any]:
        """Get patterns for a specific file type."""
        if not self.patterns:
            return []
        
        type_mapping = {
            "page": ["basic_page", "page_with_data"],
            "component": ["static_component"],
            "island": ["island_component", "signal_state"],
            "api": ["api_crud"],
            "action": ["server_action"],
            "model": ["database_model"],
            "layout": ["app_layout"],
            "middleware": ["auth_middleware"],
        }
        
        pattern_names = type_mapping.get(file_type, [])
        return [self.patterns.get(name) for name in pattern_names if self.patterns.get(name)]
    
    def _assemble_context(
        self,
        sections: List[ContextSection],
        max_tokens: int,
    ) -> str:
        """Assemble sections within token budget."""
        result_parts = []
        total_tokens = 0
        
        for section in sections:
            if total_tokens + section.estimated_tokens <= max_tokens:
                result_parts.append(section.content)
                total_tokens += section.estimated_tokens
            elif total_tokens < max_tokens:
                # Add truncated version
                remaining = max_tokens - total_tokens
                truncated_chars = remaining * self.CHARS_PER_TOKEN
                truncated = section.content[:truncated_chars]
                result_parts.append(truncated + "\n...(truncated)")
                break
        
        return "\n\n".join(result_parts)
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        return len(text) // self.CHARS_PER_TOKEN

