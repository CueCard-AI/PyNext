"""
MDX API - Main User-Facing Functions

Provides the primary mdx() function for creating
MDX content in Python files.

Usage:
    from pynext import mdx
    
    content = mdx('''
    # Hello World
    
    This is **markdown** with components!
    
    <Alert type="warning">Be careful!</Alert>
    ''')
    
    def page():
        return content
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from .parser import MDXParser, parse_mdx
from .compiler import MDXCompiler, CompileOptions, compile_mdx
from .components import MDXProvider, get_component
from .toc import TableOfContents, extract_toc
from .frontmatter import Frontmatter, extract_frontmatter


@dataclass
class MDXContent:
    """
    Compiled MDX content ready for rendering.
    
    Attributes:
        html: Rendered HTML string
        frontmatter: Extracted frontmatter metadata
        toc: Table of contents
        components: Components used in this content
    """
    html: str
    frontmatter: Frontmatter
    toc: TableOfContents
    components: List[str]
    
    def __str__(self) -> str:
        """Return HTML when used as string."""
        return self.html
    
    def __html__(self) -> str:
        """Support Jinja2 safe rendering."""
        return self.html
    
    def with_toc(
        self,
        position: str = "before",
        max_level: int = 3,
    ) -> str:
        """
        Return HTML with table of contents.
        
        Args:
            position: "before" or "after" content
            max_level: Maximum heading level in TOC
            
        Returns:
            HTML string with TOC
        """
        toc_html = self.toc.to_html(max_level=max_level)
        
        if position == "before":
            return f'{toc_html}\n{self.html}'
        return f'{self.html}\n{toc_html}'
    
    def meta_tags(self) -> str:
        """Get HTML meta tags from frontmatter."""
        return self.frontmatter.to_meta_tags()


def mdx(
    content: str,
    components: Optional[Dict[str, Callable]] = None,
    highlight_code: bool = True,
    add_anchors: bool = True,
) -> MDXContent:
    """
    Parse and compile MDX content.
    
    This is the primary function for using MDX in PyNext.
    It parses Markdown with component syntax and returns
    compiled HTML that can be rendered.
    
    Args:
        content: MDX string with Markdown and components
        components: Optional component overrides
        highlight_code: Whether to add syntax highlighting
        add_anchors: Whether to add anchor links to headings
        
    Returns:
        MDXContent with HTML and metadata
        
    Example:
        # In pages/blog/hello.py
        from pynext import mdx, page
        from components import Alert, CodeBlock
        
        content = mdx('''
        ---
        title: Hello World
        date: 2024-01-15
        ---
        
        # Hello World
        
        Welcome to my **blog post**!
        
        <Alert type="info">
            This is a custom component.
        </Alert>
        
        ## Code Example
        
        ```python
        def hello():
            print("Hello!")
        ```
        
        <CodeBlock language="python" filename="example.py">
        def main():
            hello()
        </CodeBlock>
        ''', components={
            "Alert": Alert,
            "CodeBlock": CodeBlock,
        })
        
        @page
        def blog_post():
            return article[
                content,  # Rendered HTML
            ]
    """
    # Extract frontmatter
    fm, body = extract_frontmatter(content)
    
    # Parse MDX
    parser = MDXParser()
    ast = parser.parse(body)
    
    # Get components from context and parameters
    all_components = MDXProvider.get_current_components()
    if components:
        all_components.update(components)
    
    # Compile to HTML
    options = CompileOptions(
        components=all_components,
        highlight_code=highlight_code,
        add_anchors=add_anchors,
    )
    compiler = MDXCompiler(options)
    render = compiler.compile(ast)
    
    # Extract TOC
    toc = extract_toc(body)
    
    # Find used components
    used_components = _find_components(ast)
    
    # Render HTML
    html = render()
    
    return MDXContent(
        html=html,
        frontmatter=fm,
        toc=toc,
        components=used_components,
    )


def mdx_file(
    path: Union[str, Path],
    components: Optional[Dict[str, Callable]] = None,
    **kwargs,
) -> MDXContent:
    """
    Load and compile MDX from a file.
    
    Resolves paths relative to the calling file.
    
    Args:
        path: Path to .mdx or .md file
        components: Optional component overrides
        **kwargs: Additional options for mdx()
        
    Returns:
        MDXContent with HTML and metadata
        
    Example:
        # In pages/blog/hello.py
        content = mdx_file("./hello.mdx")
        
        # Or with absolute path
        content = mdx_file("/content/posts/hello.mdx")
    """
    # Resolve path relative to caller
    caller_frame = inspect.stack()[1]
    caller_file = caller_frame.filename
    caller_dir = Path(caller_file).parent
    
    # Handle relative paths
    if isinstance(path, str):
        if path.startswith("./") or path.startswith("../"):
            file_path = caller_dir / path
        else:
            file_path = Path(path)
    else:
        file_path = path
    
    file_path = file_path.resolve()
    
    if not file_path.exists():
        raise FileNotFoundError(
            f"MDX file not found: {file_path}\n"
            f"Relative to: {caller_file}"
        )
    
    # Read content
    content = file_path.read_text(encoding="utf-8")
    
    return mdx(content, components=components, **kwargs)


def _find_components(ast) -> List[str]:
    """Find all component names used in AST."""
    from .parser import NodeType
    
    components = []
    
    def walk(node):
        if node.type == NodeType.COMPONENT:
            name = node.props.get("component")
            if name and name not in components:
                components.append(name)
        
        for child in node.children:
            walk(child)
    
    walk(ast)
    return components


# ============================================
# MDX Page Decorator
# ============================================

def mdx_page(
    path: Optional[Union[str, Path]] = None,
    layout: Optional[Callable] = None,
):
    """
    Decorator to create a page from MDX content.
    
    Automatically loads MDX from a file and renders it
    with an optional layout.
    
    Args:
        path: Path to MDX file (defaults to same name as .py file)
        layout: Optional layout component
        
    Example:
        # pages/blog/hello.py
        from pynext import mdx_page
        from layouts import BlogLayout
        
        @mdx_page(layout=BlogLayout)
        def page():
            pass  # Content loaded from hello.mdx
            
        # Or with explicit path
        @mdx_page(path="./content/hello.mdx")
        def page():
            pass
    """
    def decorator(func: Callable) -> Callable:
        # Resolve MDX path
        caller_frame = inspect.stack()[1]
        caller_file = Path(caller_frame.filename)
        
        if path is None:
            # Look for .mdx file with same name
            mdx_path = caller_file.with_suffix(".mdx")
            if not mdx_path.exists():
                mdx_path = caller_file.with_suffix(".md")
        elif isinstance(path, str):
            if path.startswith("./") or path.startswith("../"):
                mdx_path = caller_file.parent / path
            else:
                mdx_path = Path(path)
        else:
            mdx_path = path
        
        mdx_path = mdx_path.resolve()
        
        def wrapper(*args, **kwargs):
            # Load and compile MDX
            if not mdx_path.exists():
                return f"<div class='error'>MDX file not found: {mdx_path}</div>"
            
            content = mdx_file(mdx_path)
            
            # Apply layout if provided
            if layout:
                return layout(
                    title=content.frontmatter.title,
                    description=content.frontmatter.description,
                    children=content.html,
                    frontmatter=content.frontmatter,
                    toc=content.toc,
                )
            
            return str(content)
        
        # Copy function metadata
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        wrapper.mdx_path = mdx_path
        
        return wrapper
    
    return decorator


# ============================================
# MDX Renderer Component
# ============================================

def MDXRenderer(
    content: Union[str, MDXContent],
    components: Optional[Dict[str, Callable]] = None,
    class_: str = "",
) -> str:
    """
    Component for rendering MDX content.
    
    Can accept either raw MDX string or pre-compiled MDXContent.
    
    Args:
        content: MDX string or MDXContent object
        components: Optional component overrides
        class_: CSS class for wrapper
        
    Returns:
        HTML string
        
    Example:
        def page():
            return div[
                MDXRenderer('''
                # Hello
                
                <Alert>Hi!</Alert>
                '''),
            ]
    """
    if isinstance(content, str):
        compiled = mdx(content, components=components)
        html = compiled.html
    else:
        html = content.html
    
    class_attr = f' class="{class_}"' if class_ else ""
    return f"<div{class_attr}>{html}</div>"

