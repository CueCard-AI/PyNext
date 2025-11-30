"""
MDX Parser - Markdown + JSX Parsing

Parses MDX content into an AST that can be compiled
to Python component trees.

The parser handles:
- Standard Markdown syntax
- JSX-like component syntax: <Component prop="value" />
- Code blocks with language hints
- Frontmatter (YAML header)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from enum import Enum, auto


class NodeType(Enum):
    """Types of nodes in the MDX AST."""
    DOCUMENT = auto()
    HEADING = auto()
    PARAGRAPH = auto()
    TEXT = auto()
    BOLD = auto()
    ITALIC = auto()
    CODE = auto()
    CODE_BLOCK = auto()
    LINK = auto()
    IMAGE = auto()
    LIST = auto()
    LIST_ITEM = auto()
    BLOCKQUOTE = auto()
    HORIZONTAL_RULE = auto()
    TABLE = auto()
    TABLE_ROW = auto()
    TABLE_CELL = auto()
    COMPONENT = auto()  # <Component />
    HTML = auto()       # Raw HTML
    FRONTMATTER = auto()


@dataclass
class MDXNode:
    """
    A node in the MDX AST.
    
    Attributes:
        type: Node type
        children: Child nodes
        content: Text content (for leaf nodes)
        props: Properties (for components, links, etc.)
        meta: Additional metadata
    """
    type: NodeType
    children: List["MDXNode"] = field(default_factory=list)
    content: str = ""
    props: Dict[str, Any] = field(default_factory=dict)
    meta: Dict[str, Any] = field(default_factory=dict)
    
    def add_child(self, child: "MDXNode"):
        """Add a child node."""
        self.children.append(child)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for debugging."""
        result = {"type": self.type.name}
        if self.content:
            result["content"] = self.content
        if self.props:
            result["props"] = self.props
        if self.children:
            result["children"] = [c.to_dict() for c in self.children]
        return result


class MDXParser:
    """
    Parser for MDX content.
    
    Converts MDX (Markdown + JSX) into an AST that can be
    compiled to Python components.
    
    Example:
        >>> parser = MDXParser()
        >>> ast = parser.parse('''
        ... # Hello
        ... 
        ... <Alert>Warning!</Alert>
        ... ''')
        >>> print(ast.children[0].type)
        NodeType.HEADING
    """
    
    # Regex patterns
    FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
    HEADING = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
    CODE_BLOCK = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)
    INLINE_CODE = re.compile(r"`([^`]+)`")
    BOLD = re.compile(r"\*\*(.+?)\*\*|__(.+?)__")
    ITALIC = re.compile(r"\*(.+?)\*|_(.+?)_")
    LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
    BLOCKQUOTE = re.compile(r"^>\s*(.+)$", re.MULTILINE)
    HORIZONTAL_RULE = re.compile(r"^(-{3,}|\*{3,}|_{3,})$", re.MULTILINE)
    UNORDERED_LIST = re.compile(r"^[\s]*[-*+]\s+(.+)$", re.MULTILINE)
    ORDERED_LIST = re.compile(r"^[\s]*\d+\.\s+(.+)$", re.MULTILINE)
    
    # Component pattern: <Component prop="value">children</Component> or <Component />
    COMPONENT_SELF_CLOSING = re.compile(
        r"<([A-Z][a-zA-Z0-9]*)"  # Component name (PascalCase)
        r"(\s+[^>]*)?"           # Optional props
        r"\s*/>"                 # Self-closing
    )
    COMPONENT_WITH_CHILDREN = re.compile(
        r"<([A-Z][a-zA-Z0-9]*)"  # Opening tag
        r"(\s+[^>]*)?"           # Optional props
        r">"                     # Close opening tag
        r"(.*?)"                 # Children
        r"</\1>"                 # Closing tag
        , re.DOTALL
    )
    
    # Prop pattern: name="value" or name={expression}
    PROP_PATTERN = re.compile(
        r'(\w+)='
        r'(?:"([^"]*)"|'  # String value
        r'\{([^}]*)\})'   # Expression value
    )
    
    def __init__(self):
        self._component_registry: Dict[str, Any] = {}
    
    def register_component(self, name: str, component: Any):
        """Register a component for use in MDX."""
        self._component_registry[name] = component
    
    def parse(self, content: str) -> MDXNode:
        """
        Parse MDX content into an AST.
        
        Args:
            content: MDX string
            
        Returns:
            Root MDXNode of the AST
        """
        root = MDXNode(type=NodeType.DOCUMENT)
        
        # Extract frontmatter
        content, frontmatter = self._extract_frontmatter(content)
        if frontmatter:
            root.meta["frontmatter"] = frontmatter
            root.add_child(MDXNode(
                type=NodeType.FRONTMATTER,
                props=frontmatter,
            ))
        
        # Parse blocks
        blocks = self._split_blocks(content)
        
        for block in blocks:
            node = self._parse_block(block)
            if node:
                root.add_child(node)
        
        return root
    
    def _extract_frontmatter(
        self,
        content: str,
    ) -> tuple[str, Optional[Dict]]:
        """Extract YAML frontmatter from content."""
        match = self.FRONTMATTER.match(content)
        if not match:
            return content, None
        
        yaml_content = match.group(1)
        remaining = content[match.end():]
        
        # Simple YAML parsing (key: value)
        frontmatter = {}
        for line in yaml_content.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                frontmatter[key.strip()] = value.strip().strip('"\'')
        
        return remaining, frontmatter
    
    def _split_blocks(self, content: str) -> List[str]:
        """Split content into blocks (paragraphs, code blocks, etc.)."""
        blocks = []
        current = []
        in_code_block = False
        
        for line in content.split("\n"):
            # Track code blocks
            if line.startswith("```"):
                if in_code_block:
                    current.append(line)
                    blocks.append("\n".join(current))
                    current = []
                    in_code_block = False
                else:
                    if current:
                        blocks.append("\n".join(current))
                        current = []
                    current.append(line)
                    in_code_block = True
                continue
            
            if in_code_block:
                current.append(line)
                continue
            
            # Empty line ends a block
            if not line.strip():
                if current:
                    blocks.append("\n".join(current))
                    current = []
                continue
            
            current.append(line)
        
        if current:
            blocks.append("\n".join(current))
        
        return blocks
    
    def _parse_block(self, block: str) -> Optional[MDXNode]:
        """Parse a single block."""
        block = block.strip()
        if not block:
            return None
        
        # Check for code block
        if block.startswith("```"):
            return self._parse_code_block(block)
        
        # Check for heading
        heading_match = self.HEADING.match(block)
        if heading_match:
            return self._parse_heading(heading_match)
        
        # Check for horizontal rule
        if self.HORIZONTAL_RULE.match(block):
            return MDXNode(type=NodeType.HORIZONTAL_RULE)
        
        # Check for blockquote
        if block.startswith(">"):
            return self._parse_blockquote(block)
        
        # Check for list
        if self._is_list(block):
            return self._parse_list(block)
        
        # Check for component
        component = self._parse_component(block)
        if component:
            return component
        
        # Default to paragraph
        return self._parse_paragraph(block)
    
    def _parse_heading(self, match: re.Match) -> MDXNode:
        """Parse a heading."""
        level = len(match.group(1))
        text = match.group(2)
        
        # Generate ID for anchor links
        heading_id = re.sub(r"[^\w\s-]", "", text.lower())
        heading_id = re.sub(r"\s+", "-", heading_id)
        
        node = MDXNode(
            type=NodeType.HEADING,
            props={"level": level, "id": heading_id},
        )
        
        # Parse inline content
        node.children = self._parse_inline(text)
        
        return node
    
    def _parse_code_block(self, block: str) -> MDXNode:
        """Parse a fenced code block."""
        match = self.CODE_BLOCK.match(block)
        if not match:
            return MDXNode(type=NodeType.CODE_BLOCK, content=block)
        
        language = match.group(1) or "text"
        code = match.group(2).strip()
        
        return MDXNode(
            type=NodeType.CODE_BLOCK,
            content=code,
            props={"language": language},
        )
    
    def _parse_blockquote(self, block: str) -> MDXNode:
        """Parse a blockquote."""
        lines = []
        for line in block.split("\n"):
            if line.startswith(">"):
                lines.append(line[1:].strip())
            else:
                lines.append(line)
        
        content = "\n".join(lines)
        
        node = MDXNode(type=NodeType.BLOCKQUOTE)
        node.children = self._parse_inline(content)
        
        return node
    
    def _is_list(self, block: str) -> bool:
        """Check if block is a list."""
        first_line = block.split("\n")[0].strip()
        return bool(
            self.UNORDERED_LIST.match(first_line) or
            self.ORDERED_LIST.match(first_line)
        )
    
    def _parse_list(self, block: str) -> MDXNode:
        """Parse a list."""
        first_line = block.split("\n")[0].strip()
        ordered = bool(self.ORDERED_LIST.match(first_line))
        
        node = MDXNode(
            type=NodeType.LIST,
            props={"ordered": ordered},
        )
        
        # Parse list items
        pattern = self.ORDERED_LIST if ordered else self.UNORDERED_LIST
        for match in pattern.finditer(block):
            item = MDXNode(type=NodeType.LIST_ITEM)
            item.children = self._parse_inline(match.group(1))
            node.add_child(item)
        
        return node
    
    def _parse_component(self, block: str) -> Optional[MDXNode]:
        """Parse a JSX-like component."""
        # Try self-closing first
        match = self.COMPONENT_SELF_CLOSING.match(block.strip())
        if match:
            return self._create_component_node(
                name=match.group(1),
                props_str=match.group(2) or "",
                children_str="",
            )
        
        # Try component with children
        match = self.COMPONENT_WITH_CHILDREN.match(block.strip())
        if match:
            return self._create_component_node(
                name=match.group(1),
                props_str=match.group(2) or "",
                children_str=match.group(3),
            )
        
        return None
    
    def _create_component_node(
        self,
        name: str,
        props_str: str,
        children_str: str,
    ) -> MDXNode:
        """Create a component node."""
        # Parse props
        props = {"component": name}
        for match in self.PROP_PATTERN.finditer(props_str):
            prop_name = match.group(1)
            value = match.group(2) or match.group(3)
            
            # Try to parse as Python literal
            try:
                props[prop_name] = eval(value)
            except:
                props[prop_name] = value
        
        node = MDXNode(
            type=NodeType.COMPONENT,
            props=props,
            content=children_str.strip(),
        )
        
        # Parse children as inline content if present
        if children_str.strip():
            node.children = self._parse_inline(children_str.strip())
        
        return node
    
    def _parse_paragraph(self, block: str) -> MDXNode:
        """Parse a paragraph."""
        # Check if it contains a component
        if "<" in block and ">" in block:
            # Split around components
            return self._parse_mixed_paragraph(block)
        
        node = MDXNode(type=NodeType.PARAGRAPH)
        node.children = self._parse_inline(block)
        return node
    
    def _parse_mixed_paragraph(self, block: str) -> MDXNode:
        """Parse paragraph with embedded components."""
        # This is a simplified version - could be enhanced
        node = MDXNode(type=NodeType.PARAGRAPH)
        
        # For now, treat components in paragraphs as inline
        # A more complete implementation would properly parse them
        node.children = self._parse_inline(block)
        
        return node
    
    def _parse_inline(self, text: str) -> List[MDXNode]:
        """Parse inline content (bold, italic, links, etc.)."""
        nodes = []
        remaining = text
        
        while remaining:
            # Find the earliest match
            earliest_match = None
            earliest_type = None
            earliest_pos = len(remaining)
            
            patterns = [
                (self.BOLD, NodeType.BOLD),
                (self.ITALIC, NodeType.ITALIC),
                (self.INLINE_CODE, NodeType.CODE),
                (self.LINK, NodeType.LINK),
                (self.IMAGE, NodeType.IMAGE),
            ]
            
            for pattern, node_type in patterns:
                match = pattern.search(remaining)
                if match and match.start() < earliest_pos:
                    earliest_match = match
                    earliest_type = node_type
                    earliest_pos = match.start()
            
            if not earliest_match:
                # No more matches - add remaining as text
                if remaining:
                    nodes.append(MDXNode(
                        type=NodeType.TEXT,
                        content=remaining,
                    ))
                break
            
            # Add text before match
            if earliest_pos > 0:
                nodes.append(MDXNode(
                    type=NodeType.TEXT,
                    content=remaining[:earliest_pos],
                ))
            
            # Add the matched element
            nodes.append(self._create_inline_node(
                earliest_type,
                earliest_match,
            ))
            
            remaining = remaining[earliest_match.end():]
        
        return nodes
    
    def _create_inline_node(
        self,
        node_type: NodeType,
        match: re.Match,
    ) -> MDXNode:
        """Create an inline node from a regex match."""
        if node_type == NodeType.BOLD:
            content = match.group(1) or match.group(2)
            return MDXNode(type=NodeType.BOLD, content=content)
        
        if node_type == NodeType.ITALIC:
            content = match.group(1) or match.group(2)
            return MDXNode(type=NodeType.ITALIC, content=content)
        
        if node_type == NodeType.CODE:
            return MDXNode(type=NodeType.CODE, content=match.group(1))
        
        if node_type == NodeType.LINK:
            return MDXNode(
                type=NodeType.LINK,
                content=match.group(1),
                props={"href": match.group(2)},
            )
        
        if node_type == NodeType.IMAGE:
            return MDXNode(
                type=NodeType.IMAGE,
                props={
                    "alt": match.group(1),
                    "src": match.group(2),
                },
            )
        
        return MDXNode(type=NodeType.TEXT, content=match.group(0))


def parse_mdx(content: str) -> MDXNode:
    """
    Parse MDX content into an AST.
    
    Convenience function for quick parsing.
    
    Args:
        content: MDX string
        
    Returns:
        Root MDXNode
        
    Example:
        >>> ast = parse_mdx("# Hello **World**")
        >>> ast.children[0].type
        NodeType.HEADING
    """
    parser = MDXParser()
    return parser.parse(content)

