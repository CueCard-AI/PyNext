"""
MDX Compiler - AST to Python Components

Compiles the MDX AST into Python component trees that
can be rendered as HTML.

The compiler:
1. Takes the parsed AST
2. Maps nodes to PyNext components
3. Returns a callable component tree
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union

from .parser import MDXNode, NodeType


# Type alias for rendered content
RenderedContent = Union[str, List[Any], Any]


@dataclass
class CompileOptions:
    """
    Options for MDX compilation.
    
    Attributes:
        components: Custom component overrides
        highlight_code: Whether to add syntax highlighting
        add_anchors: Whether to add anchor links to headings
        github_flavored: Whether to support GFM extensions
    """
    components: Dict[str, Callable] = field(default_factory=dict)
    highlight_code: bool = True
    add_anchors: bool = True
    github_flavored: bool = True


class MDXCompiler:
    """
    Compiles MDX AST to Python component trees.
    
    Example:
        >>> parser = MDXParser()
        >>> ast = parser.parse("# Hello **World**")
        >>> compiler = MDXCompiler()
        >>> component = compiler.compile(ast)
        >>> html = component()  # Renders to HTML
    """
    
    def __init__(self, options: Optional[CompileOptions] = None):
        self.options = options or CompileOptions()
        self._components: Dict[str, Callable] = {}
    
    def register_component(self, name: str, component: Callable):
        """Register a custom component."""
        self._components[name] = component
    
    def compile(self, ast: MDXNode) -> Callable[[], RenderedContent]:
        """
        Compile AST to a callable component.
        
        Args:
            ast: Parsed MDX AST
            
        Returns:
            Callable that renders the content
        """
        def render():
            return self._render_node(ast)
        
        # Attach metadata
        render.frontmatter = ast.meta.get("frontmatter", {})
        render.toc = self._extract_toc(ast)
        
        return render
    
    def _render_node(self, node: MDXNode) -> RenderedContent:
        """Render a single node."""
        handler = getattr(self, f"_render_{node.type.name.lower()}", None)
        if handler:
            return handler(node)
        return self._render_default(node)
    
    def _render_document(self, node: MDXNode) -> RenderedContent:
        """Render document root."""
        children = [
            self._render_node(child)
            for child in node.children
            if child.type != NodeType.FRONTMATTER
        ]
        
        return self._create_element("div", {"class": "mdx-content"}, children)
    
    def _render_heading(self, node: MDXNode) -> RenderedContent:
        """Render heading (h1-h6)."""
        level = node.props.get("level", 1)
        heading_id = node.props.get("id", "")
        
        children = [self._render_node(c) for c in node.children]
        
        # Add anchor link if enabled
        if self.options.add_anchors and heading_id:
            anchor = self._create_element(
                "a",
                {"href": f"#{heading_id}", "class": "anchor"},
                ["#"],
            )
            children.append(anchor)
        
        return self._create_element(
            f"h{level}",
            {"id": heading_id, "class": f"mdx-heading mdx-h{level}"},
            children,
        )
    
    def _render_paragraph(self, node: MDXNode) -> RenderedContent:
        """Render paragraph."""
        children = [self._render_node(c) for c in node.children]
        return self._create_element("p", {"class": "mdx-paragraph"}, children)
    
    def _render_text(self, node: MDXNode) -> str:
        """Render text node."""
        return self._escape_html(node.content)
    
    def _render_bold(self, node: MDXNode) -> RenderedContent:
        """Render bold text."""
        return self._create_element("strong", {}, [node.content])
    
    def _render_italic(self, node: MDXNode) -> RenderedContent:
        """Render italic text."""
        return self._create_element("em", {}, [node.content])
    
    def _render_code(self, node: MDXNode) -> RenderedContent:
        """Render inline code."""
        return self._create_element(
            "code",
            {"class": "mdx-inline-code"},
            [node.content],
        )
    
    def _render_code_block(self, node: MDXNode) -> RenderedContent:
        """Render code block with syntax highlighting."""
        language = node.props.get("language", "text")
        code = node.content
        
        # Apply syntax highlighting if enabled
        if self.options.highlight_code:
            code = self._highlight_code(code, language)
        else:
            code = self._escape_html(code)
        
        pre = self._create_element(
            "pre",
            {"class": f"mdx-code-block language-{language}"},
            [self._create_element("code", {}, [code], escape=False)],
        )
        
        return pre
    
    def _render_link(self, node: MDXNode) -> RenderedContent:
        """Render link."""
        href = node.props.get("href", "")
        text = node.content
        
        # External links open in new tab
        attrs = {"href": href, "class": "mdx-link"}
        if href.startswith("http"):
            attrs["target"] = "_blank"
            attrs["rel"] = "noopener noreferrer"
        
        return self._create_element("a", attrs, [text])
    
    def _render_image(self, node: MDXNode) -> RenderedContent:
        """Render image."""
        src = node.props.get("src", "")
        alt = node.props.get("alt", "")
        
        return self._create_element(
            "img",
            {"src": src, "alt": alt, "class": "mdx-image"},
            [],
        )
    
    def _render_list(self, node: MDXNode) -> RenderedContent:
        """Render ordered or unordered list."""
        tag = "ol" if node.props.get("ordered") else "ul"
        children = [self._render_node(c) for c in node.children]
        return self._create_element(tag, {"class": "mdx-list"}, children)
    
    def _render_list_item(self, node: MDXNode) -> RenderedContent:
        """Render list item."""
        children = [self._render_node(c) for c in node.children]
        return self._create_element("li", {"class": "mdx-list-item"}, children)
    
    def _render_blockquote(self, node: MDXNode) -> RenderedContent:
        """Render blockquote."""
        children = [self._render_node(c) for c in node.children]
        return self._create_element("blockquote", {"class": "mdx-blockquote"}, children)
    
    def _render_horizontal_rule(self, node: MDXNode) -> RenderedContent:
        """Render horizontal rule."""
        return self._create_element("hr", {"class": "mdx-hr"}, [])
    
    def _render_component(self, node: MDXNode) -> RenderedContent:
        """Render a custom component."""
        name = node.props.get("component", "div")
        
        # Check for registered component
        component = (
            self._components.get(name) or
            self.options.components.get(name)
        )
        
        if component:
            # Call the component with props
            props = {k: v for k, v in node.props.items() if k != "component"}
            
            # Add children
            if node.children:
                children = [self._render_node(c) for c in node.children]
                props["children"] = children
            elif node.content:
                props["children"] = node.content
            
            try:
                return component(**props)
            except Exception as e:
                return self._create_element(
                    "div",
                    {"class": "mdx-error"},
                    [f"Error rendering {name}: {e}"],
                )
        
        # Fallback: render as div with component name as class
        children = [self._render_node(c) for c in node.children]
        if node.content and not children:
            children = [node.content]
        
        props_str = " ".join(
            f'{k}="{v}"' for k, v in node.props.items()
            if k != "component"
        )
        
        return self._create_element(
            "div",
            {"class": f"mdx-component mdx-{name.lower()}", "data-component": name},
            children,
        )
    
    def _render_frontmatter(self, node: MDXNode) -> str:
        """Frontmatter is not rendered."""
        return ""
    
    def _render_default(self, node: MDXNode) -> RenderedContent:
        """Default rendering for unknown nodes."""
        if node.children:
            return self._create_element(
                "div",
                {},
                [self._render_node(c) for c in node.children],
            )
        return node.content
    
    def _create_element(
        self,
        tag: str,
        attrs: Dict[str, str],
        children: List[RenderedContent],
        escape: bool = True,
    ) -> str:
        """Create an HTML element."""
        # Build attribute string
        attr_parts = []
        for key, value in attrs.items():
            if value:
                attr_parts.append(f'{key}="{value}"')
        
        attr_str = " " + " ".join(attr_parts) if attr_parts else ""
        
        # Self-closing tags
        if tag in ("img", "br", "hr", "input", "meta", "link"):
            return f"<{tag}{attr_str} />"
        
        # Build children string
        children_str = ""
        for child in children:
            if isinstance(child, str):
                children_str += child
            elif isinstance(child, list):
                children_str += "".join(str(c) for c in child)
            else:
                children_str += str(child)
        
        return f"<{tag}{attr_str}>{children_str}</{tag}>"
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return (
            text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#x27;")
        )
    
    def _highlight_code(self, code: str, language: str) -> str:
        """
        Add syntax highlighting classes to code.
        
        This is a simple implementation - for full highlighting,
        integrate with Pygments or similar.
        """
        # Basic keyword highlighting for common languages
        keywords = {
            "python": [
                "def", "class", "import", "from", "return", "if", "else",
                "elif", "for", "while", "try", "except", "with", "as",
                "async", "await", "yield", "None", "True", "False",
            ],
            "javascript": [
                "function", "const", "let", "var", "return", "if", "else",
                "for", "while", "class", "extends", "import", "export",
                "async", "await", "null", "undefined", "true", "false",
            ],
            "typescript": [
                "function", "const", "let", "var", "return", "if", "else",
                "for", "while", "class", "extends", "import", "export",
                "async", "await", "null", "undefined", "true", "false",
                "interface", "type", "enum",
            ],
        }
        
        lang_keywords = keywords.get(language, [])
        escaped = self._escape_html(code)
        
        # Wrap keywords in spans
        for kw in lang_keywords:
            escaped = escaped.replace(
                f" {kw} ",
                f' <span class="keyword">{kw}</span> ',
            )
            escaped = escaped.replace(
                f" {kw}(",
                f' <span class="keyword">{kw}</span>(',
            )
        
        # Highlight strings
        import re
        escaped = re.sub(
            r'(".*?"|\'.*?\')',
            r'<span class="string">\1</span>',
            escaped,
        )
        
        # Highlight comments
        escaped = re.sub(
            r'(#.*)$',
            r'<span class="comment">\1</span>',
            escaped,
            flags=re.MULTILINE,
        )
        escaped = re.sub(
            r'(//.*)$',
            r'<span class="comment">\1</span>',
            escaped,
            flags=re.MULTILINE,
        )
        
        return escaped
    
    def _extract_toc(self, ast: MDXNode) -> List[Dict]:
        """Extract table of contents from AST."""
        toc = []
        
        for node in ast.children:
            if node.type == NodeType.HEADING:
                level = node.props.get("level", 1)
                heading_id = node.props.get("id", "")
                
                # Get text content
                text = ""
                for child in node.children:
                    if child.type == NodeType.TEXT:
                        text += child.content
                    elif hasattr(child, "content"):
                        text += child.content
                
                toc.append({
                    "level": level,
                    "id": heading_id,
                    "text": text,
                })
        
        return toc


def compile_mdx(
    ast: MDXNode,
    components: Optional[Dict[str, Callable]] = None,
) -> Callable[[], RenderedContent]:
    """
    Compile MDX AST to a callable component.
    
    Convenience function for quick compilation.
    
    Args:
        ast: Parsed MDX AST
        components: Optional component overrides
        
    Returns:
        Callable that renders the content
        
    Example:
        >>> ast = parse_mdx("# Hello")
        >>> render = compile_mdx(ast)
        >>> html = render()
    """
    options = CompileOptions(components=components or {})
    compiler = MDXCompiler(options)
    return compiler.compile(ast)

