# HTML API Reference

PyNext provides a Pythonic API for building HTML elements. This guide covers all available elements, attributes, and patterns.

## Table of Contents

- [Element Syntax](#element-syntax)
- [All HTML Elements](#all-html-elements)
- [Attributes](#attributes)
- [Event Handlers](#event-handlers)
- [Children](#children)
- [Conditional Rendering](#conditional-rendering)
- [List Rendering](#list-rendering)
- [Forms and Inputs](#forms-and-inputs)
- [Special Patterns](#special-patterns)
- [Raw HTML](#raw-html)
- [Best Practices](#best-practices)
- [API Reference](#api-reference)

---

## Element Syntax

### Basic Pattern

```python
element(attributes)[children]
```

### Examples

```python
from pynext import div, h1, p, span, button

# Element only
div()

# With attributes
div(class_="container", id="main")

# With children
div()["Hello World"]

# With both
div(class_="card")[
    h1()["Title"],
    p()["Description"]
]
```

### Anatomy

```python
div(class_="box", id="my-box")[     # Tag + Attributes
    h1()["Hello"],                   # Child element
    p()[                             # Child element with nested children
        "Welcome ",                  # Text child
        span(class_="name")["User"]  # Element child
    ]
]
```

---

## All HTML Elements

### Document Metadata

```python
from pynext import html, head, title, base, link, meta, style

# Document structure (usually handled by framework)
html(lang="en")[
    head()[
        title()["My App"],
        meta(charset="utf-8"),
        meta(name="viewport", content="width=device-width, initial-scale=1"),
        link(rel="stylesheet", href="/styles.css"),
        style()[".custom { color: red; }"]
    ],
    body()[...]
]
```

### Content Sectioning

```python
from pynext import (
    body, article, section, nav, aside, 
    header, footer, main, address
)

# Page structure
body()[
    header(class_="site-header")[
        nav()["Navigation"]
    ],
    main()[
        article()[
            section()["Content section"]
        ],
        aside()["Sidebar"]
    ],
    footer()["Footer content"],
    address()["Contact info"]
]
```

### Text Content

```python
from pynext import (
    div, p, h1, h2, h3, h4, h5, h6,
    blockquote, pre, code, hr, br,
    ul, ol, li, dl, dt, dd,
    figure, figcaption
)

# Headings
h1()["Main Heading"]
h2()["Subheading"]
h3()["Section Heading"]

# Paragraphs and blocks
p()["Paragraph text"]
blockquote()["Quoted text"]
pre()[code()["code block"]]

# Lists
ul()[
    li()["Item 1"],
    li()["Item 2"],
    li()["Item 3"]
]

ol(start="1")[
    li()["First"],
    li()["Second"]
]

# Description list
dl()[
    dt()["Term"],
    dd()["Definition"]
]

# Figure with caption
figure()[
    img(src="/chart.png", alt="Chart"),
    figcaption()["Figure 1: Sales data"]
]

# Line break and horizontal rule
p()["Line 1", br(), "Line 2"]
hr()
```

### Inline Text Semantics

```python
from pynext import (
    a, span, strong, em, b, i, u, s,
    small, mark, sub, sup, code, kbd,
    abbr, time, q, cite, dfn, var
)

# Links
a(href="/about")["About Us"]
a(href="https://example.com", target="_blank")["External Link"]

# Text formatting
strong()["Bold text"]
em()["Italic text"]
mark()["Highlighted text"]
small()["Small text"]
s()["Strikethrough"]
code()["inline code"]
kbd()["Ctrl+C"]

# Subscript and superscript
p()["H", sub()["2"], "O"]     # H₂O
p()["E=mc", sup()["2"]]       # E=mc²

# Semantic inline elements
abbr(title="HyperText Markup Language")["HTML"]
time(datetime="2024-03-15")["March 15, 2024"]
q()["A quoted phrase"]
cite()["Book Title"]
dfn()["Definition term"]
var()["x"]
```

### Images and Multimedia

```python
from pynext import (
    img, audio, video, source, track,
    picture, canvas, svg, iframe
)

# Images
img(src="/photo.jpg", alt="Description", width="400", height="300")

# Responsive image
picture()[
    source(media="(min-width: 800px)", srcset="/large.jpg"),
    source(media="(min-width: 400px)", srcset="/medium.jpg"),
    img(src="/small.jpg", alt="Responsive image")
]

# Video
video(controls=True, width="640")[
    source(src="/video.mp4", type="video/mp4"),
    source(src="/video.webm", type="video/webm"),
    "Your browser does not support video."
]

# Audio
audio(controls=True)[
    source(src="/audio.mp3", type="audio/mp3"),
    "Your browser does not support audio."
]

# Canvas (for JS drawing)
canvas(id="myCanvas", width="400", height="300")

# Iframe
iframe(src="https://example.com", width="100%", height="400")
```

### Tables

```python
from pynext import (
    table, caption, thead, tbody, tfoot,
    tr, th, td, colgroup, col
)

# Basic table
table(class_="data-table")[
    caption()["Monthly Sales"],
    thead()[
        tr()[
            th()["Month"],
            th()["Sales"],
            th()["Growth"]
        ]
    ],
    tbody()[
        tr()[
            td()["January"],
            td()["$10,000"],
            td()["+5%"]
        ],
        tr()[
            td()["February"],
            td()["$12,000"],
            td()["+20%"]
        ]
    ],
    tfoot()[
        tr()[
            td()["Total"],
            td(colspan="2")["$22,000"]
        ]
    ]
]

# Column styling
table()[
    colgroup()[
        col(style="width: 50%"),
        col(style="width: 25%"),
        col(style="width: 25%")
    ],
    # ... rows
]
```

### Forms

```python
from pynext import (
    form, input_, button, select, option, optgroup,
    textarea, label, fieldset, legend, datalist,
    output, progress, meter
)

# Complete form example
form(action="/submit", method="post")[
    fieldset()[
        legend()["Personal Information"],
        
        div()[
            label(for_="name")["Name:"],
            input_(type="text", id="name", name="name", required=True)
        ],
        
        div()[
            label(for_="email")["Email:"],
            input_(type="email", id="email", name="email", required=True)
        ],
        
        div()[
            label(for_="age")["Age:"],
            input_(type="number", id="age", name="age", min="0", max="120")
        ]
    ],
    
    fieldset()[
        legend()["Preferences"],
        
        div()[
            label(for_="country")["Country:"],
            select(id="country", name="country")[
                option(value="")["Select..."],
                optgroup(label="North America")[
                    option(value="us")["United States"],
                    option(value="ca")["Canada"]
                ],
                optgroup(label="Europe")[
                    option(value="uk")["United Kingdom"],
                    option(value="de")["Germany"]
                ]
            ]
        ],
        
        div()[
            label(for_="bio")["Bio:"],
            textarea(id="bio", name="bio", rows="4", cols="50")
        ]
    ],
    
    button(type="submit")["Submit"]
]

# Progress and meter
progress(value="70", max="100")["70%"]
meter(value="0.6", min="0", max="1", low="0.3", high="0.7")["60%"]
```

### Interactive Elements

```python
from pynext import details, summary, dialog, menu

# Collapsible content
details()[
    summary()["Click to expand"],
    p()["Hidden content here..."]
]

# Dialog (modal)
dialog(id="myDialog", open=True)[
    h2()["Dialog Title"],
    p()["Dialog content..."],
    button(onclick="closeDialog()")["Close"]
]
```

### Scripting

```python
from pynext import script, noscript, template, slot

# Inline script
script()["""
    console.log('Hello from PyNext!');
"""]

# External script
script(src="/app.js", defer=True)

# No-script fallback
noscript()[
    p()["Please enable JavaScript to use this app."]
]

# Template for client-side cloning
template(id="card-template")[
    div(class_="card")[
        h3(class_="title")[""],
        p(class_="content")[""]
    ]
]
```

---

## Attributes

### Standard Attributes

```python
from pynext import div

# Common attributes
div(
    id="unique-id",
    class_="container flex",    # Note: class_ (underscore) for Python reserved word
    style="color: red;",
    title="Tooltip text",
    hidden=True,
    tabindex="0",
    role="button",
    aria_label="Click me"       # aria-label becomes aria_label
)
```

### Reserved Words

Python reserved words use trailing underscores:

| HTML Attribute | Python Parameter |
|----------------|------------------|
| `class` | `class_` |
| `for` | `for_` |
| `type` | `type_` (or `type` works in most cases) |

```python
# Using reserved words
div(class_="container")
label(for_="email-input")["Email"]
input_(type="email", id="email-input")
```

### Boolean Attributes

```python
# Boolean attributes - use True/False
input_(type="checkbox", checked=True)
input_(type="text", disabled=True)
input_(type="text", readonly=True)
input_(type="text", required=True)
button(type="submit", disabled=False)  # Won't render disabled
select(multiple=True)
video(autoplay=True, loop=True, muted=True)
details(open=True)
```

### Data Attributes

```python
# data-* attributes use data_ prefix
div(
    data_id="123",
    data_user_name="Alice",     # data-user-name
    data_config='{"key": "value"}'
)

# Renders as:
# <div data-id="123" data-user-name="Alice" data-config='{"key": "value"}'></div>
```

### ARIA Attributes

```python
# aria-* attributes use aria_ prefix
button(
    aria_label="Close dialog",
    aria_expanded="false",
    aria_haspopup="true",
    aria_controls="menu-1"
)

# Role attribute
div(
    role="button",
    tabindex="0",
    aria_pressed="false"
)
```

### Hyphenated Attributes

For attributes with hyphens, use underscores:

```python
# Underscores convert to hyphens in output
div(
    x_data="{open: false}",     # x-data (Alpine.js)
    hx_get="/api/data",         # hx-get (htmx)
    hx_trigger="click"          # hx-trigger (htmx)
)
```

---

## Event Handlers

### Basic Events

```python
from pynext import button, input_, div

# Click handler
button(onclick=lambda: print("Clicked!"))["Click Me"]

# With event object
button(onclick=lambda e: handle_click(e))["Click"]

# Input events
input_(
    type="text",
    onchange=lambda e: update_value(e.target.value),
    oninput=lambda e: live_update(e.target.value),
    onfocus=lambda: set_focused(True),
    onblur=lambda: set_focused(False)
)

# Form events
form(onsubmit=lambda e: handle_submit(e))
```

### Server Actions

```python
from pynext import server_action, button

@server_action
async def save_data(data: dict) -> dict:
    return {"saved": True}

# Server action as handler
button(onclick=save_data)["Save"]

# With arguments
button(onclick=lambda: save_data({"id": 123}))["Save Item"]
```

### Signal Updates

```python
from pynext import Signal, button, input_

count = Signal(0)
name = Signal("")

# Update signal on click
button(onclick=lambda: count.update(lambda x: x + 1))["Increment"]
button(onclick=lambda: count.set(0))["Reset"]

# Update signal on input
input_(
    type="text",
    value=name,
    oninput=lambda e: name.set(e.target.value)
)
```

### All Event Types

```python
# Mouse events
div(
    onclick=handler,
    ondblclick=handler,
    onmousedown=handler,
    onmouseup=handler,
    onmouseover=handler,
    onmouseout=handler,
    onmousemove=handler,
    oncontextmenu=handler
)

# Keyboard events
input_(
    onkeydown=handler,
    onkeyup=handler,
    onkeypress=handler  # Deprecated, use onkeydown
)

# Form events
form(
    onsubmit=handler,
    onreset=handler
)

input_(
    onchange=handler,
    oninput=handler,
    onfocus=handler,
    onblur=handler,
    onselect=handler
)

# Drag events
div(
    draggable=True,
    ondragstart=handler,
    ondrag=handler,
    ondragend=handler,
    ondragenter=handler,
    ondragover=handler,
    ondragleave=handler,
    ondrop=handler
)

# Touch events (mobile)
div(
    ontouchstart=handler,
    ontouchmove=handler,
    ontouchend=handler,
    ontouchcancel=handler
)

# Scroll and resize
div(
    onscroll=handler
)
# window.onresize handled in JS

# Media events
video(
    onplay=handler,
    onpause=handler,
    onended=handler,
    ontimeupdate=handler,
    onvolumechange=handler
)
```

---

## Children

### Text Children

```python
from pynext import p, span

# Simple text
p()["Hello World"]

# Multiple text nodes
p()["Hello ", "World"]

# Mixed content
p()[
    "Welcome, ",
    span(class_="name")["Alice"],
    "!"
]
```

### Element Children

```python
from pynext import div, h1, p

# Nested elements
div()[
    h1()["Title"],
    p()["First paragraph"],
    p()["Second paragraph"]
]

# Deeply nested
div(class_="card")[
    div(class_="card-header")[
        h2()["Header"]
    ],
    div(class_="card-body")[
        p()["Content here"]
    ],
    div(class_="card-footer")[
        button()["Action"]
    ]
]
```

### Signal Children

```python
from pynext import Signal, div, span

count = Signal(0)
name = Signal("World")

# Signal as child - auto-updates
div()[
    span()["Count: ", count],
    p()["Hello, ", name, "!"]
]
```

### Computed Children

```python
from pynext import Signal, Computed, div

price = Signal(100)
quantity = Signal(2)
total = Computed(lambda: price() * quantity())

div()[
    p()["Price: $", price],
    p()["Quantity: ", quantity],
    p()["Total: $", total]  # Updates when price or quantity changes
]
```

### Empty Children

```python
from pynext import div, br, hr, img

# Self-closing elements (no children)
br()
hr()
img(src="/photo.jpg", alt="Photo")

# Explicitly empty
div()  # <div></div>
div()[]  # Same
```

---

## Conditional Rendering

### Using Python Conditionals

```python
from pynext import div, p

is_logged_in = True
is_admin = False

div()[
    # if/else
    p()["Welcome back!"] if is_logged_in else p()["Please log in"],
    
    # if only (None is ignored)
    is_admin and p()["Admin panel"],
    
    # Ternary with elements
    div(class_="admin" if is_admin else "user")[
        "Content"
    ]
]
```

### With Signals

```python
from pynext import Signal, div, p, button

show_details = Signal(False)
loading = Signal(False)
error = Signal(None)
data = Signal(None)

div()[
    # Toggle visibility
    button(onclick=lambda: show_details.update(lambda x: not x))[
        "Toggle Details"
    ],
    show_details() and div(class_="details")[
        p()["Detailed information here"]
    ],
    
    # Loading state
    loading() and div(class_="loading")["Loading..."],
    
    # Error state
    error() and div(class_="error")[f"Error: {error()}"],
    
    # Success state
    data() and div(class_="data")[
        p()[f"Data: {data()}"]
    ]
]
```

### Helper Function

```python
from pynext import Signal, div

def when(condition, element):
    """Render element only when condition is true."""
    return element if condition() if callable(condition) else condition else None

show = Signal(True)

div()[
    when(show, p()["Visible content"]),
    when(lambda: show() and some_other_condition(), p()["Also visible"])
]
```

### Switch/Match Pattern

```python
from pynext import Signal, div, p

status = Signal("loading")

def render_status(s):
    match s:
        case "loading":
            return div(class_="loading")["Loading..."]
        case "error":
            return div(class_="error")["Something went wrong"]
        case "success":
            return div(class_="success")["Done!"]
        case _:
            return div()["Unknown status"]

div()[
    render_status(status())
]
```

---

## List Rendering

### Basic List

```python
from pynext import ul, li

items = ["Apple", "Banana", "Cherry"]

ul()[
    [li()[item] for item in items]
]
```

### With Index

```python
from pynext import ol, li

items = ["First", "Second", "Third"]

ol()[
    [li()[f"{i+1}. {item}"] for i, item in enumerate(items)]
]
```

### Object List

```python
from pynext import div, h3, p

users = [
    {"id": 1, "name": "Alice", "role": "Admin"},
    {"id": 2, "name": "Bob", "role": "User"},
    {"id": 3, "name": "Charlie", "role": "User"}
]

div(class_="user-list")[
    [
        div(class_="user-card", key=user["id"])[
            h3()[user["name"]],
            p()[f"Role: {user['role']}"]
        ]
        for user in users
    ]
]
```

### Reactive Lists

```python
from pynext import Signal, Store, ul, li, button

todos = Signal([
    {"id": 1, "text": "Learn PyNext"},
    {"id": 2, "text": "Build an app"}
])

def add_todo():
    new_id = max(t["id"] for t in todos()) + 1 if todos() else 1
    todos.update(lambda t: t + [{"id": new_id, "text": "New todo"}])

def remove_todo(todo_id):
    todos.update(lambda t: [todo for todo in t if todo["id"] != todo_id])

div()[
    button(onclick=add_todo)["Add Todo"],
    
    ul()[
        [
            li(key=todo["id"])[
                span()[todo["text"]],
                button(onclick=lambda tid=todo["id"]: remove_todo(tid))["×"]
            ]
            for todo in todos()
        ]
    ]
]
```

### Keys for Performance

Always use `key` for dynamic lists:

```python
# Good - with keys
ul()[
    [li(key=item["id"])[item["name"]] for item in items]
]

# Avoid - without keys (less efficient updates)
ul()[
    [li()[item["name"]] for item in items]
]
```

### Filtered Lists

```python
from pynext import Signal, div, input_, ul, li

search = Signal("")
items = ["Apple", "Apricot", "Banana", "Blueberry", "Cherry"]

div()[
    input_(
        type="text",
        placeholder="Search...",
        oninput=lambda e: search.set(e.target.value)
    ),
    
    ul()[
        [
            li()[item]
            for item in items
            if search().lower() in item.lower()
        ]
    ]
]
```

### Grouped Lists

```python
from pynext import div, h3, ul, li
from itertools import groupby

items = [
    {"name": "Apple", "category": "Fruit"},
    {"name": "Banana", "category": "Fruit"},
    {"name": "Carrot", "category": "Vegetable"},
    {"name": "Broccoli", "category": "Vegetable"}
]

# Group by category
sorted_items = sorted(items, key=lambda x: x["category"])
grouped = groupby(sorted_items, key=lambda x: x["category"])

div()[
    [
        div(class_="group")[
            h3()[category],
            ul()[
                [li()[item["name"]] for item in list(group)]
            ]
        ]
        for category, group in grouped
    ]
]
```

---

## Forms and Inputs

### Text Inputs

```python
from pynext import Signal, input_, textarea

name = Signal("")
bio = Signal("")

# Text input
input_(
    type="text",
    value=name,
    placeholder="Enter your name",
    oninput=lambda e: name.set(e.target.value)
)

# Textarea
textarea(
    rows="4",
    cols="50",
    placeholder="Tell us about yourself",
    oninput=lambda e: bio.set(e.target.value)
)[bio()]
```

### Input Types

```python
from pynext import input_

# Text variants
input_(type="text", placeholder="Text")
input_(type="email", placeholder="email@example.com")
input_(type="password", placeholder="Password")
input_(type="url", placeholder="https://...")
input_(type="tel", placeholder="+1 234 567 8900")
input_(type="search", placeholder="Search...")

# Numbers
input_(type="number", min="0", max="100", step="1")
input_(type="range", min="0", max="100", value="50")

# Date/Time
input_(type="date")
input_(type="time")
input_(type="datetime-local")
input_(type="month")
input_(type="week")

# Other
input_(type="color", value="#ff0000")
input_(type="file", accept="image/*")
input_(type="hidden", name="csrf_token", value="abc123")
```

### Checkboxes and Radios

```python
from pynext import Signal, div, input_, label

# Single checkbox
agreed = Signal(False)

div()[
    input_(
        type="checkbox",
        id="agree",
        checked=agreed,
        onchange=lambda e: agreed.set(e.target.checked)
    ),
    label(for_="agree")["I agree to the terms"]
]

# Checkbox group
selected = Signal(set())

def toggle_option(value):
    selected.update(lambda s: s ^ {value})

div()[
    [
        div()[
            input_(
                type="checkbox",
                id=f"opt-{opt}",
                checked=opt in selected(),
                onchange=lambda e, o=opt: toggle_option(o)
            ),
            label(for_=f"opt-{opt}")[opt]
        ]
        for opt in ["Option A", "Option B", "Option C"]
    ]
]

# Radio group
choice = Signal("option1")

div()[
    [
        div()[
            input_(
                type="radio",
                name="choice",
                id=f"radio-{opt}",
                value=opt,
                checked=choice() == opt,
                onchange=lambda e: choice.set(e.target.value)
            ),
            label(for_=f"radio-{opt}")[opt.replace("option", "Option ")]
        ]
        for opt in ["option1", "option2", "option3"]
    ]
]
```

### Select Dropdowns

```python
from pynext import Signal, select, option, optgroup

country = Signal("")

select(
    value=country,
    onchange=lambda e: country.set(e.target.value)
)[
    option(value="")["Select a country..."],
    optgroup(label="North America")[
        option(value="us")["United States"],
        option(value="ca")["Canada"],
        option(value="mx")["Mexico"]
    ],
    optgroup(label="Europe")[
        option(value="uk")["United Kingdom"],
        option(value="de")["Germany"],
        option(value="fr")["France"]
    ]
]

# Multiple select
selected_countries = Signal([])

select(
    multiple=True,
    size="5",
    onchange=lambda e: selected_countries.set(
        [opt.value for opt in e.target.selectedOptions]
    )
)[
    option(value="us")["United States"],
    option(value="uk")["United Kingdom"],
    option(value="de")["Germany"]
]
```

### Complete Form Example

```python
from pynext import Signal, server_action, form, div, label, input_, select, option, textarea, button

# Form state
form_data = Signal({
    "name": "",
    "email": "",
    "subject": "general",
    "message": ""
})

errors = Signal({})
submitting = Signal(False)

@server_action
async def submit_form(data: dict) -> dict:
    # Validate and save
    return {"success": True}

def update_field(field, value):
    form_data.update(lambda d: {**d, field: value})

async def handle_submit(e):
    e.preventDefault()
    submitting.set(True)
    
    try:
        result = await submit_form(form_data())
        if result["success"]:
            # Reset form
            form_data.set({"name": "", "email": "", "subject": "general", "message": ""})
    finally:
        submitting.set(False)

form(onsubmit=handle_submit)[
    div(class_="form-group")[
        label(for_="name")["Name *"],
        input_(
            type="text",
            id="name",
            required=True,
            value=form_data()["name"],
            oninput=lambda e: update_field("name", e.target.value)
        ),
        errors().get("name") and span(class_="error")[errors()["name"]]
    ],
    
    div(class_="form-group")[
        label(for_="email")["Email *"],
        input_(
            type="email",
            id="email",
            required=True,
            value=form_data()["email"],
            oninput=lambda e: update_field("email", e.target.value)
        )
    ],
    
    div(class_="form-group")[
        label(for_="subject")["Subject"],
        select(
            id="subject",
            value=form_data()["subject"],
            onchange=lambda e: update_field("subject", e.target.value)
        )[
            option(value="general")["General Inquiry"],
            option(value="support")["Technical Support"],
            option(value="sales")["Sales"]
        ]
    ],
    
    div(class_="form-group")[
        label(for_="message")["Message *"],
        textarea(
            id="message",
            rows="5",
            required=True,
            oninput=lambda e: update_field("message", e.target.value)
        )[form_data()["message"]]
    ],
    
    button(type="submit", disabled=submitting())[
        "Sending..." if submitting() else "Send Message"
    ]
]
```

---

## Special Patterns

### Fragments

Group elements without a wrapper:

```python
from pynext import Fragment, h1, p

# Fragment returns multiple elements
def Header():
    return Fragment()[
        h1()["Title"],
        p()["Subtitle"]
    ]

# Or simply return a list
def Header():
    return [
        h1()["Title"],
        p()["Subtitle"]
    ]
```

### Dynamic Tag Names

```python
from pynext import create_element

def heading(level, text):
    return create_element(f"h{level}")()[text]

heading(1, "Main Title")  # <h1>Main Title</h1>
heading(2, "Subtitle")    # <h2>Subtitle</h2>
```

### Spread Attributes

```python
from pynext import div, button

# Spread attributes from dict
attrs = {
    "class_": "btn btn-primary",
    "id": "submit-btn",
    "disabled": False
}

button(**attrs)["Submit"]

# Merge with additional attrs
button(**attrs, type="submit")["Submit"]
```

### Class Utilities

```python
from pynext import div

# Conditional classes
def class_names(*classes, **conditional):
    result = list(classes)
    for cls, condition in conditional.items():
        if condition:
            result.append(cls)
    return " ".join(result)

is_active = True
is_disabled = False

div(class_=class_names(
    "button",
    active=is_active,
    disabled=is_disabled
))
# class="button active"
```

### Style Object

```python
from pynext import div

def style_string(**styles):
    return "; ".join(f"{k.replace('_', '-')}: {v}" for k, v in styles.items())

div(style=style_string(
    background_color="blue",
    padding="1rem",
    border_radius="8px"
))
# style="background-color: blue; padding: 1rem; border-radius: 8px"
```

---

## Raw HTML

### Inserting Raw HTML

For trusted HTML content:

```python
from pynext import div, raw_html

# Render HTML string (be careful with user input!)
markdown_html = "<p><strong>Bold</strong> and <em>italic</em></p>"

div(class_="content")[
    raw_html(markdown_html)
]
```

### Safety Warning

```python
# NEVER do this with user input!
user_input = "<script>alert('XSS!')</script>"
raw_html(user_input)  # DANGEROUS!

# Always sanitize first
from bleach import clean
safe_html = clean(user_input, tags=["p", "b", "i", "em", "strong"])
raw_html(safe_html)  # Safe
```

---

## Best Practices

### 1. Component Organization

```python
# Good: Small, focused components
@component
def UserAvatar(user):
    return img(src=user["avatar"], alt=user["name"], class_="avatar")

@component
def UserCard(user):
    return div(class_="user-card")[
        UserAvatar(user),
        h3()[user["name"]],
        p()[user["bio"]]
    ]

# Avoid: Monolithic components
@component
def EverythingComponent():
    # 200 lines of HTML...
    pass
```

### 2. Semantic HTML

```python
# Good: Semantic elements
article()[
    header()[h1()["Article Title"]],
    section()[p()["Content..."]],
    footer()[small()["Published 2024"]]
]

# Avoid: div soup
div()[
    div()[div()["Article Title"]],
    div()[div()["Content..."]],
    div()[div()["Published 2024"]]
]
```

### 3. Accessible Elements

```python
# Good: Accessible
button(
    onclick=handler,
    aria_label="Close dialog"
)["×"]

img(src="/photo.jpg", alt="Team photo from company retreat")

# Avoid: Inaccessible
div(onclick=handler)["×"]  # Use button for interactive
img(src="/photo.jpg")       # Missing alt
```

### 4. Keys for Lists

```python
# Good: With keys
ul()[
    [li(key=item.id)[item.name] for item in items]
]

# Avoid: Without keys
ul()[
    [li()[item.name] for item in items]
]
```

### 5. Event Handler Patterns

```python
# Good: Named handlers
def handle_click():
    count.update(lambda x: x + 1)

button(onclick=handle_click)["Click"]

# Good: Inline for simple operations
button(onclick=lambda: visible.set(True))["Show"]

# Avoid: Complex inline logic
button(onclick=lambda: (
    validate() and save() and notify() and redirect()
))["Submit"]
```

---

## API Reference

### Element Factory

```python
# Import elements
from pynext import div, span, button, ...

# Create element
element = div(class_="container")[
    "content"
]

# Render to HTML string
html = element.render()
```

### Core Elements

All standard HTML elements are available:

```python
from pynext import (
    # Document
    html, head, body, title, meta, link, script, style,
    
    # Sections
    header, footer, main, nav, aside, section, article, address,
    
    # Content
    div, span, p, h1, h2, h3, h4, h5, h6,
    ul, ol, li, dl, dt, dd,
    pre, code, blockquote, hr, br,
    
    # Text
    a, strong, em, b, i, u, s, mark, small,
    sub, sup, abbr, cite, q, dfn, time, kbd, var,
    
    # Media
    img, picture, source, video, audio, track,
    canvas, svg, iframe, figure, figcaption,
    
    # Tables
    table, caption, thead, tbody, tfoot, tr, th, td, colgroup, col,
    
    # Forms
    form, input_, button, select, option, optgroup,
    textarea, label, fieldset, legend, datalist,
    output, progress, meter,
    
    # Interactive
    details, summary, dialog, menu,
    
    # Special
    template, slot, noscript
)
```

### Utilities

```python
from pynext import raw_html, Fragment, create_element

# Raw HTML (use carefully!)
raw_html("<strong>Bold</strong>")

# Fragment (no wrapper element)
Fragment()[child1, child2]

# Dynamic element
create_element("custom-element")(attr="value")["content"]
```

---

## Next Steps

- [Getting Started](GETTING_STARTED.md) - Tutorial walkthrough
- [Routing](ROUTING.md) - File-based routing system
- [State Management](STATE_MANAGEMENT.md) - Signals and reactivity
- [Server Actions](SERVER_ACTIONS.md) - Server-side functions

