"""
MDX Components - Default and Custom Component Registry

Provides default components for MDX rendering and a
registry for custom components.

Usage:
    from pynext.mdx import register_components
    
    register_components({
        "Alert": Alert,
        "Callout": Callout,
    })
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union


# Global component registry
_component_registry: Dict[str, Callable] = {}


def register_components(components: Dict[str, Callable]):
    """
    Register custom components for use in MDX.
    
    Components are mapped from their JSX-like name to a
    Python callable that returns HTML.
    
    Args:
        components: Dict mapping names to components
        
    Example:
        register_components({
            "Alert": Alert,
            "CodeBlock": CodeBlock,
            "Callout": Callout,
        })
        
        # Then in MDX:
        # <Alert type="warning">Warning!</Alert>
    """
    _component_registry.update(components)


def get_component(name: str) -> Optional[Callable]:
    """
    Get a registered component by name.
    
    Args:
        name: Component name
        
    Returns:
        Component callable or None
    """
    return _component_registry.get(name)


def clear_components():
    """Clear all registered components."""
    _component_registry.clear()


class MDXProvider:
    """
    Context provider for MDX components.
    
    Wraps content and provides component overrides.
    
    Example:
        >>> with MDXProvider(components={"Alert": MyAlert}):
        ...     content = mdx("# Hello <Alert>!")
    """
    
    _stack: List[Dict[str, Callable]] = []
    
    def __init__(self, components: Optional[Dict[str, Callable]] = None):
        self.components = components or {}
    
    def __enter__(self):
        MDXProvider._stack.append(self.components)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        MDXProvider._stack.pop()
        return False
    
    @classmethod
    def get_current_components(cls) -> Dict[str, Callable]:
        """Get components from current context."""
        result = _component_registry.copy()
        for layer in cls._stack:
            result.update(layer)
        return result


# ============================================
# Default MDX Components
# ============================================

def Alert(
    type: str = "info",
    title: Optional[str] = None,
    children: Any = None,
) -> str:
    """
    Alert/callout component.
    
    Args:
        type: "info", "warning", "error", "success"
        title: Optional title
        children: Alert content
        
    Example:
        <Alert type="warning">Be careful!</Alert>
    """
    icons = {
        "info": "ℹ️",
        "warning": "⚠️",
        "error": "❌",
        "success": "✅",
    }
    
    icon = icons.get(type, "ℹ️")
    
    title_html = ""
    if title:
        title_html = f'<div class="mdx-alert-title">{icon} {title}</div>'
    
    content = children if isinstance(children, str) else "".join(str(c) for c in (children or []))
    
    return f'''
<div class="mdx-alert mdx-alert-{type}">
    {title_html}
    <div class="mdx-alert-content">{icon if not title else ""} {content}</div>
</div>
'''


def Callout(
    emoji: str = "💡",
    children: Any = None,
) -> str:
    """
    Simple callout with emoji.
    
    Args:
        emoji: Emoji to display
        children: Callout content
        
    Example:
        <Callout emoji="🔥">Hot tip!</Callout>
    """
    content = children if isinstance(children, str) else "".join(str(c) for c in (children or []))
    
    return f'''
<aside class="mdx-callout">
    <span class="mdx-callout-emoji">{emoji}</span>
    <div class="mdx-callout-content">{content}</div>
</aside>
'''


def CodeBlock(
    language: str = "text",
    filename: Optional[str] = None,
    highlight: Optional[str] = None,
    children: Any = None,
) -> str:
    """
    Enhanced code block with filename and line highlighting.
    
    Args:
        language: Programming language
        filename: Optional filename to display
        highlight: Lines to highlight (e.g., "1,3-5")
        children: Code content
        
    Example:
        <CodeBlock language="python" filename="app.py">
        def hello():
            print("Hello!")
        </CodeBlock>
    """
    code = children if isinstance(children, str) else "".join(str(c) for c in (children or []))
    
    header = ""
    if filename:
        header = f'<div class="mdx-code-header"><span class="mdx-code-filename">{filename}</span></div>'
    
    return f'''
<div class="mdx-code-block-wrapper" data-language="{language}">
    {header}
    <pre class="mdx-code-block language-{language}"><code>{code}</code></pre>
</div>
'''


def Tabs(
    children: Any = None,
) -> str:
    """
    Tab container component.
    
    Example:
        <Tabs>
            <Tab label="Python">Python code</Tab>
            <Tab label="JavaScript">JS code</Tab>
        </Tabs>
    """
    content = children if isinstance(children, str) else "".join(str(c) for c in (children or []))
    
    return f'''
<div class="mdx-tabs" data-tabs>
    {content}
</div>
'''


def Tab(
    label: str,
    children: Any = None,
) -> str:
    """
    Individual tab panel.
    
    Args:
        label: Tab label
        children: Tab content
    """
    content = children if isinstance(children, str) else "".join(str(c) for c in (children or []))
    
    return f'''
<div class="mdx-tab" data-tab-label="{label}">
    {content}
</div>
'''


def Steps(
    children: Any = None,
) -> str:
    """
    Numbered steps container.
    
    Example:
        <Steps>
            <Step>First step</Step>
            <Step>Second step</Step>
        </Steps>
    """
    content = children if isinstance(children, str) else "".join(str(c) for c in (children or []))
    
    return f'''
<ol class="mdx-steps">
    {content}
</ol>
'''


def Step(
    title: Optional[str] = None,
    children: Any = None,
) -> str:
    """
    Individual step.
    
    Args:
        title: Optional step title
        children: Step content
    """
    content = children if isinstance(children, str) else "".join(str(c) for c in (children or []))
    
    title_html = f'<strong class="mdx-step-title">{title}</strong>' if title else ""
    
    return f'''
<li class="mdx-step">
    {title_html}
    <div class="mdx-step-content">{content}</div>
</li>
'''


def Card(
    title: Optional[str] = None,
    href: Optional[str] = None,
    icon: Optional[str] = None,
    children: Any = None,
) -> str:
    """
    Card component for links or content.
    
    Args:
        title: Card title
        href: Optional link URL
        icon: Optional emoji icon
        children: Card content
        
    Example:
        <Card title="Getting Started" href="/docs" icon="🚀">
            Learn the basics
        </Card>
    """
    content = children if isinstance(children, str) else "".join(str(c) for c in (children or []))
    
    icon_html = f'<span class="mdx-card-icon">{icon}</span>' if icon else ""
    title_html = f'<h3 class="mdx-card-title">{icon_html}{title}</h3>' if title else ""
    
    wrapper_tag = "a" if href else "div"
    href_attr = f' href="{href}"' if href else ""
    
    return f'''
<{wrapper_tag}{href_attr} class="mdx-card">
    {title_html}
    <div class="mdx-card-content">{content}</div>
</{wrapper_tag}>
'''


def Cards(
    cols: int = 2,
    children: Any = None,
) -> str:
    """
    Card grid container.
    
    Args:
        cols: Number of columns
        children: Card components
    """
    content = children if isinstance(children, str) else "".join(str(c) for c in (children or []))
    
    return f'''
<div class="mdx-cards" style="--cols: {cols}">
    {content}
</div>
'''


def FileTree(
    children: Any = None,
) -> str:
    """
    File tree component.
    
    Example:
        <FileTree>
        - pages/
          - index.py
          - about.py
        - components/
          - Button.py
        </FileTree>
    """
    content = children if isinstance(children, str) else "".join(str(c) for c in (children or []))
    
    # Parse the tree structure
    lines = content.strip().split("\n")
    html_lines = []
    
    for line in lines:
        indent = len(line) - len(line.lstrip())
        text = line.strip().lstrip("- ")
        
        is_folder = text.endswith("/")
        icon = "📁" if is_folder else "📄"
        
        html_lines.append(
            f'<div class="mdx-file" style="padding-left: {indent * 12}px">'
            f'<span class="mdx-file-icon">{icon}</span>'
            f'<span class="mdx-file-name">{text}</span>'
            f'</div>'
        )
    
    return f'''
<div class="mdx-file-tree">
    {"".join(html_lines)}
</div>
'''


def Accordion(
    title: str,
    children: Any = None,
) -> str:
    """
    Collapsible accordion component.
    
    Args:
        title: Accordion header
        children: Collapsible content
    """
    content = children if isinstance(children, str) else "".join(str(c) for c in (children or []))
    
    return f'''
<details class="mdx-accordion">
    <summary class="mdx-accordion-title">{title}</summary>
    <div class="mdx-accordion-content">{content}</div>
</details>
'''


def YouTube(
    id: str,
    title: str = "YouTube Video",
) -> str:
    """
    Embedded YouTube video.
    
    Args:
        id: YouTube video ID
        title: Accessible title
    """
    return f'''
<div class="mdx-video-wrapper">
    <iframe
        src="https://www.youtube.com/embed/{id}"
        title="{title}"
        frameborder="0"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowfullscreen
        class="mdx-video"
    ></iframe>
</div>
'''


def Kbd(
    children: Any = None,
) -> str:
    """
    Keyboard key component.
    
    Example:
        Press <Kbd>Ctrl</Kbd> + <Kbd>C</Kbd> to copy
    """
    content = children if isinstance(children, str) else "".join(str(c) for c in (children or []))
    
    return f'<kbd class="mdx-kbd">{content}</kbd>'


# Default components to register
default_components = {
    "Alert": Alert,
    "Callout": Callout,
    "CodeBlock": CodeBlock,
    "Tabs": Tabs,
    "Tab": Tab,
    "Steps": Steps,
    "Step": Step,
    "Card": Card,
    "Cards": Cards,
    "FileTree": FileTree,
    "Accordion": Accordion,
    "YouTube": YouTube,
    "Kbd": Kbd,
}

# Register defaults
register_components(default_components)

