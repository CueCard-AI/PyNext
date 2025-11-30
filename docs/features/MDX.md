# MDX Support

Markdown with embedded Python components. Build-time compilation.

## The Problem

Documentation and blogs need rich content mixing prose with interactive elements. Traditional MDX requires complex webpack config and runtime parsing.

**Next.js**: Complex MDX setup, runtime JavaScript parsing, webpack plugins.

**PyNext**: Build-time compilation, zero runtime parsing, native Python components.

## Quick Start

```python
from pynext import mdx
from components import Alert, CodeBlock

content = mdx("""
---
title: Getting Started
date: 2024-01-15
---

# Welcome to PyNext

This is **markdown** with embedded components!

<Alert type="info">
    PyNext compiles MDX at build-time, not runtime.
</Alert>

## Code Example

```python
def hello():
    print("Hello, World!")
```

<CodeBlock language="python" filename="example.py">
def main():
    hello()
</CodeBlock>
""")

@page
def docs():
    return article[
        content,  # Renders as HTML
    ]
```

## How It Works

### First Principles

MDX is Markdown + JSX. PyNext parses both syntaxes at **build-time**:

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   MDX        │ →  │   Parse      │ →  │   Compile    │ →  │   HTML       │
│   String     │    │   AST        │    │   Components │    │   Output     │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

1. **Frontmatter**: Extract YAML metadata
2. **Markdown**: Parse headings, paragraphs, lists, etc.
3. **Components**: Recognize `<Component />` syntax
4. **Compile**: Convert AST to HTML with registered components

### Why Build-Time?

- **Zero parsing JS**: Browser receives pure HTML
- **Faster page loads**: No markdown parsing in browser
- **Type safety**: Component props validated at build
- **SEO friendly**: Content fully rendered for crawlers

## API Reference

### mdx()

Parse and compile MDX content.

```python
from pynext import mdx

content = mdx("""
# Hello World

This is **markdown**.

<Alert>Important!</Alert>
""", components={
    "Alert": MyAlertComponent,
})

# Access parts
content.html           # Rendered HTML
content.frontmatter    # Frontmatter object
content.toc            # Table of contents
content.components     # List of used component names

# Use as string
str(content)           # HTML string

# With table of contents
content.with_toc(position="before", max_level=2)
```

**Parameters:**
- `content` (str): MDX string
- `components` (dict, optional): Component name → callable mapping
- `highlight_code` (bool): Enable syntax highlighting (default: True)
- `add_anchors` (bool): Add anchor links to headings (default: True)

### mdx_file()

Load MDX from a file.

```python
from pynext import mdx_file

content = mdx_file("./README.mdx")
content = mdx_file("/absolute/path/to/doc.mdx")
```

### Frontmatter

Access document metadata:

```python
from pynext.mdx import extract_frontmatter

fm, body = extract_frontmatter("""
---
title: My Post
date: 2024-01-15
author: Jane Doe
tags: [python, web]
draft: false
---

# Content here
""")

fm.title        # "My Post"
fm.date         # datetime object
fm.author       # "Jane Doe"
fm.tags         # ["python", "web"]
fm.draft        # False
fm["custom"]    # Access any field

# Generate meta tags
fm.to_meta_tags()  # HTML <meta> tags
```

### Table of Contents

Extract and render TOC:

```python
from pynext.mdx import extract_toc

toc = extract_toc("""
# Title
## Section 1
### Subsection
## Section 2
""")

len(toc)         # 4 items total
toc.items        # Nested structure
toc.flat         # Flat list

# Render as HTML
toc.to_html(max_level=2, ordered=False)

# Convert to dict
toc.to_dict()    # For JSON serialization
```

## Built-in Components

### Alert

```python
<Alert type="info">Informational message</Alert>
<Alert type="warning">Warning message</Alert>
<Alert type="error">Error message</Alert>
<Alert type="success">Success message</Alert>

<Alert type="warning" title="Important">
    Content with title
</Alert>
```

### Callout

```python
<Callout emoji="💡">
    Pro tip: Use callouts for tips!
</Callout>
```

### CodeBlock

```python
<CodeBlock language="python" filename="app.py" highlight="2,4-6">
def hello():
    print("Hello!")

def main():
    hello()
</CodeBlock>
```

### Tabs

```python
<Tabs>
    <Tab label="Python">
        Python code here
    </Tab>
    <Tab label="JavaScript">
        JavaScript code here
    </Tab>
</Tabs>
```

### Steps

```python
<Steps>
    <Step title="Install">pip install pynext</Step>
    <Step title="Create Project">pynext init my-app</Step>
    <Step title="Run">pynext dev</Step>
</Steps>
```

### Cards

```python
<Cards cols={3}>
    <Card title="Getting Started" href="/docs" icon="🚀">
        Learn the basics of PyNext
    </Card>
    <Card title="Components" href="/components" icon="🧩">
        Browse available components
    </Card>
</Cards>
```

### FileTree

```python
<FileTree>
- pages/
  - index.py
  - about.py
- components/
  - Button.py
  - Card.py
</FileTree>
```

### Accordion

```python
<Accordion title="Click to expand">
    Hidden content revealed on click
</Accordion>
```

### YouTube

```python
<YouTube id="dQw4w9WgXcQ" title="Video Title" />
```

### Kbd

```python
Press <Kbd>Ctrl</Kbd> + <Kbd>C</Kbd> to copy
```

## Custom Components

### Register Globally

```python
# mdx-components.py
from pynext.mdx import register_components

def CustomAlert(type="info", children=None):
    return f'<div class="alert alert-{type}">{children}</div>'

def InteractiveDemo(children=None):
    return f'''
    <div class="demo" data-interactive="true">
        {children}
    </div>
    '''

register_components({
    "Alert": CustomAlert,
    "Demo": InteractiveDemo,
})
```

### Per-File Components

```python
content = mdx("""
<MyComponent prop="value" />
""", components={
    "MyComponent": my_component_function,
})
```

### With MDXProvider

```python
from pynext.mdx import MDXProvider

def special_alert(**kwargs):
    return "<div class='special'>...</div>"

with MDXProvider(components={"Alert": special_alert}):
    content = mdx("<Alert>Uses special!</Alert>")
```

## Patterns

### Blog Post Page

```python
# pages/blog/[slug].py
from pynext import page, mdx_file
from layouts import BlogLayout
from pathlib import Path

@page
def blog_post(slug: str):
    content = mdx_file(f"./content/posts/{slug}.mdx")
    
    return BlogLayout(
        title=content.frontmatter.title,
        date=content.frontmatter.date,
        toc=content.toc,
    )[
        content,
    ]
```

### Documentation Site

```python
# pages/docs/[...path].py
from pynext import page, mdx_file

@page
def docs(path: list[str]):
    doc_path = "/".join(path)
    content = mdx_file(f"./docs/{doc_path}.mdx")
    
    return div(class_="docs-layout")[
        aside(class_="sidebar")[
            content.toc.to_html(max_level=3),
        ],
        main(class_="content")[
            content,
        ],
    ]
```

### MDX with Islands

```python
from pynext import mdx, island

@island
def Counter():
    count = Signal(0)
    return button(onclick=lambda: count.set(count.get() + 1))[
        f"Count: {count.get()}"
    ]

content = mdx("""
# Interactive Demo

Click the button below:

<Counter />
""", components={"Counter": Counter})
```

## Syntax Highlighting

Built-in support for common languages:

```python
# Highlighted automatically
```python
def hello():
    print("Hello!")
```

```javascript
function hello() {
    console.log("Hello!");
}
```

```typescript
const hello = (): void => {
    console.log("Hello!");
}
```
```

## Performance

| Metric | Next.js MDX | PyNext MDX |
|--------|-------------|------------|
| Parse location | Runtime | Build-time |
| JS bundle | ~50KB MDX runtime | 0KB |
| First paint | After JS loads | Immediate |
| SEO | Requires hydration | Full content indexed |

## Migration from Next.js

### Before (Next.js)

```jsx
// pages/blog/[slug].tsx
import { MDXRemote } from 'next-mdx-remote';
import { serialize } from 'next-mdx-remote/serialize';

export async function getStaticProps({ params }) {
  const source = await getPostContent(params.slug);
  const mdxSource = await serialize(source);
  return { props: { mdxSource } };
}

export default function Post({ mdxSource }) {
  return <MDXRemote {...mdxSource} components={components} />;
}
```

### After (PyNext)

```python
# pages/blog/[slug].py
from pynext import page, mdx_file

@page
def blog_post(slug: str):
    content = mdx_file(f"./content/{slug}.mdx")
    return article[content]
```

## Troubleshooting

### Component Not Rendering

```python
# Missing registration
<MyComponent />  # Shows as div with class="mdx-component"

# Fix: Register the component
register_components({"MyComponent": my_component})
```

### Frontmatter Not Parsing

```yaml
---
title: My Post
date: 2024-01-15   # Must be YYYY-MM-DD
tags: [a, b, c]    # Inline list syntax
---
```

### Code Block Not Highlighting

Ensure language is specified:
```
```python  # Highlighted
def hello(): pass
```

```
def hello(): pass  # Not highlighted (no language)
```
```

