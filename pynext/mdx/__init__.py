"""
PyNext MDX - Markdown with Components

Write documentation and blogs mixing Markdown with
interactive Python components. Zero runtime parsing.

Usage:
    from pynext import mdx
    
    content = mdx('''
    # Hello World
    
    This is **markdown** with components!
    
    <Alert type="warning">Important!</Alert>
    
    ```python
    def hello():
        print("Hello!")
    ```
    ''')
    
    def page():
        return content

Features:
- Build-time compilation (no runtime parsing)
- Component embedding with <Component /> syntax
- Automatic syntax highlighting
- Table of contents generation
- Frontmatter support
"""

from .parser import MDXParser, parse_mdx
from .compiler import MDXCompiler, compile_mdx
from .components import (
    register_components,
    get_component,
    MDXProvider,
    default_components,
)
from .toc import TableOfContents, extract_toc
from .frontmatter import Frontmatter, extract_frontmatter

# Main API function
from .api import mdx, mdx_file

__all__ = [
    # Main API
    "mdx",
    "mdx_file",
    # Parser
    "MDXParser",
    "parse_mdx",
    # Compiler
    "MDXCompiler",
    "compile_mdx",
    # Components
    "register_components",
    "get_component",
    "MDXProvider",
    "default_components",
    # TOC
    "TableOfContents",
    "extract_toc",
    # Frontmatter
    "Frontmatter",
    "extract_frontmatter",
]

