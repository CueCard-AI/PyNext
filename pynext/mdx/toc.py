"""
Table of Contents - Auto-Generate from MDX

Extracts headings from MDX content and generates
a structured table of contents.

Usage:
    from pynext.mdx import extract_toc
    
    toc = extract_toc(mdx_content)
    for item in toc.items:
        print(f"{item.level}: {item.text}")
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TOCItem:
    """
    A single table of contents entry.
    
    Attributes:
        level: Heading level (1-6)
        id: Anchor ID for linking
        text: Heading text
        children: Nested headings
    """
    level: int
    id: str
    text: str
    children: List["TOCItem"] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "level": self.level,
            "id": self.id,
            "text": self.text,
            "children": [c.to_dict() for c in self.children],
        }


@dataclass
class TableOfContents:
    """
    Complete table of contents.
    
    Attributes:
        items: Top-level TOC items (with nested children)
        flat: Flat list of all items
    """
    items: List[TOCItem] = field(default_factory=list)
    flat: List[TOCItem] = field(default_factory=list)
    
    def __bool__(self) -> bool:
        """Check if TOC has items."""
        return bool(self.items)
    
    def __len__(self) -> int:
        """Get total number of items."""
        return len(self.flat)
    
    def __iter__(self):
        """Iterate over flat items."""
        return iter(self.flat)
    
    def to_html(
        self,
        max_level: int = 3,
        ordered: bool = False,
    ) -> str:
        """
        Render TOC as HTML.
        
        Args:
            max_level: Maximum heading level to include
            ordered: Use ordered list (ol) instead of unordered (ul)
            
        Returns:
            HTML string
        """
        if not self.items:
            return ""
        
        tag = "ol" if ordered else "ul"
        
        def render_item(item: TOCItem) -> str:
            if item.level > max_level:
                return ""
            
            children_html = ""
            if item.children:
                visible_children = [
                    render_item(c)
                    for c in item.children
                    if c.level <= max_level
                ]
                if visible_children:
                    children_html = f'<{tag} class="toc-children">{"".join(visible_children)}</{tag}>'
            
            return f'''
<li class="toc-item toc-level-{item.level}">
    <a href="#{item.id}" class="toc-link">{item.text}</a>
    {children_html}
</li>
'''
        
        items_html = "".join(render_item(item) for item in self.items)
        
        return f'''
<nav class="toc" aria-label="Table of contents">
    <{tag} class="toc-list">
        {items_html}
    </{tag}>
</nav>
'''
    
    def to_dict(self) -> List[dict]:
        """Convert to list of dictionaries."""
        return [item.to_dict() for item in self.items]


def extract_toc(content: str) -> TableOfContents:
    """
    Extract table of contents from Markdown/MDX content.
    
    Parses all headings and builds a nested structure.
    
    Args:
        content: Markdown/MDX string
        
    Returns:
        TableOfContents with nested items
        
    Example:
        >>> toc = extract_toc('''
        ... # Title
        ... ## Section 1
        ... ### Subsection
        ... ## Section 2
        ... ''')
        >>> len(toc)
        4
        >>> toc.items[0].text
        'Title'
    """
    # Find all headings
    heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
    
    flat_items: List[TOCItem] = []
    
    for match in heading_pattern.finditer(content):
        level = len(match.group(1))
        text = match.group(2).strip()
        
        # Generate ID
        heading_id = _generate_id(text)
        
        flat_items.append(TOCItem(
            level=level,
            id=heading_id,
            text=text,
        ))
    
    # Build nested structure
    nested_items = _build_nested(flat_items)
    
    return TableOfContents(
        items=nested_items,
        flat=flat_items,
    )


def _generate_id(text: str) -> str:
    """Generate a URL-safe ID from heading text."""
    # Remove special characters
    text = re.sub(r"[^\w\s-]", "", text.lower())
    # Replace spaces with hyphens
    text = re.sub(r"\s+", "-", text)
    return text


def _build_nested(items: List[TOCItem]) -> List[TOCItem]:
    """
    Build nested TOC structure from flat list.
    
    Lower-level headings become children of higher-level ones.
    """
    if not items:
        return []
    
    result: List[TOCItem] = []
    stack: List[TOCItem] = []
    
    for item in items:
        # Create a copy to avoid mutating the original
        current = TOCItem(
            level=item.level,
            id=item.id,
            text=item.text,
        )
        
        # Pop items from stack that are same level or higher
        while stack and stack[-1].level >= current.level:
            stack.pop()
        
        if stack:
            # Add as child of the last item in stack
            stack[-1].children.append(current)
        else:
            # Add as top-level item
            result.append(current)
        
        stack.append(current)
    
    return result


class TOCRenderer:
    """
    Customizable TOC renderer.
    
    Allows fine-grained control over TOC rendering.
    """
    
    def __init__(
        self,
        max_level: int = 3,
        ordered: bool = False,
        class_prefix: str = "toc",
    ):
        self.max_level = max_level
        self.ordered = ordered
        self.class_prefix = class_prefix
    
    def render(self, toc: TableOfContents) -> str:
        """Render TOC to HTML."""
        return toc.to_html(
            max_level=self.max_level,
            ordered=self.ordered,
        )
    
    def render_compact(self, toc: TableOfContents) -> str:
        """Render as simple list without nesting."""
        if not toc.flat:
            return ""
        
        items = [
            f'<li><a href="#{item.id}">{item.text}</a></li>'
            for item in toc.flat
            if item.level <= self.max_level
        ]
        
        tag = "ol" if self.ordered else "ul"
        return f'<{tag} class="{self.class_prefix}-compact">{"".join(items)}</{tag}>'

