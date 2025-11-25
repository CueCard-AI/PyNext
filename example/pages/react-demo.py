"""
PyNext Example - React Components Demo

Demonstrates seamless integration between native PyNext components
and React npm packages via Preact (~4KB runtime).
"""

from pynext import (
    page, component, Signal, Store,
    div, h1, h2, h3, p, button, span, input_, a, section,
    ReactComponent,
)


@component
def NativeCounter():
    """
    Native PyNext counter - updates via direct DOM manipulation.
    No virtual DOM overhead, instant updates.
    """
    count = Signal(0)
    
    return div(class_="demo-card")[
        h3()["Native PyNext Counter"],
        p(class_="description")[
            "Pure PyNext component using signals. Updates are instant "
            "with direct DOM manipulation - no virtual DOM."
        ],
        div(class_="counter-display")[
            span(class_="count-label")["Count: "],
            span(class_="count-value")[count],
        ],
        div(class_="button-group")[
            button(
                class_="btn btn-primary",
                onclick=lambda: count.update(lambda x: x + 1)
            )["Increment"],
            button(
                class_="btn btn-secondary",
                onclick=lambda: count.update(lambda x: x - 1)
            )["Decrement"],
            button(
                class_="btn btn-outline",
                onclick=lambda: count.set(0)
            )["Reset"],
        ],
    ]


@component
def HybridDemo():
    """
    Demonstrates native PyNext + React components sharing state.
    
    The PyNext Signal is passed to React components as props,
    and React event handlers can update PyNext signals.
    """
    slider_value = Signal(50)
    
    return div(class_="demo-card")[
        h3()["Hybrid: PyNext + React (MUI Slider)"],
        p(class_="description")[
            "This demo shows a native PyNext display sharing state with a "
            "React Material UI Slider. When you drag the slider, both update!"
        ],
        
        # Native PyNext display - updates instantly
        div(class_="value-display")[
            span()["Value: "],
            span(class_="highlight")[slider_value],
            span()["%"],
        ],
        
        # Progress bar using native PyNext
        div(class_="progress-bar")[
            div(
                class_="progress-fill",
                style=f"width: {slider_value()}%"  # Note: This is SSR value
            )[""],
        ],
        
        # React MUI Slider component
        # The Signal is automatically converted to a prop value
        # and the component re-renders when the signal changes
        ReactComponent(
            package="@mui/material",
            component="Slider",
            props={
                "value": slider_value,          # PyNext Signal → React prop
                "onChange": slider_value.set,    # React callback → Signal update
                "min": 0,
                "max": 100,
                "valueLabelDisplay": "auto",
                "sx": {"color": "#6366f1"},
            }
        ),
        
        p(class_="note")[
            "Note: To see this in action, run: ",
            span(class_="code")["npm install @mui/material @emotion/react @emotion/styled"],
        ],
    ]


@component
def ReactButtonDemo():
    """Shows React buttons with PyNext signal integration."""
    theme = Signal("light")
    clicks = Signal(0)
    
    return div(class_="demo-card")[
        h3()["React MUI Buttons"],
        p(class_="description")[
            "React MUI buttons that interact with PyNext signals."
        ],
        
        div(class_="info")[
            span()["Theme: ", span(class_="highlight")[theme]],
            span()["  |  Clicks: ", span(class_="highlight")[clicks]],
        ],
        
        div(class_="button-group")[
            ReactComponent(
                package="@mui/material",
                component="Button",
                props={
                    "variant": "contained",
                    "color": "primary",
                    "onClick": clicks.set,  # Will increment
                },
                children="MUI Contained"
            ),
            ReactComponent(
                package="@mui/material",
                component="Button",
                props={
                    "variant": "outlined",
                    "color": "secondary",
                },
                children="MUI Outlined"
            ),
        ],
    ]


@page(
    title="React Components - PyNext",
    meta=[{"name": "description", "content": "React npm packages in PyNext via Preact"}]
)
def react_demo():
    """Page demonstrating React component integration."""
    
    return div(class_="container")[
        # Navigation
        div(class_="nav-back")[
            a(href="/")["← Back to Home"]
        ],
        
        # Header
        section(class_="header")[
            h1()["React Component Integration"],
            p(class_="subtitle")[
                "Use React npm packages in PyNext with optimal performance. "
                "React components run via Preact (~4KB) instead of React (~40KB)."
            ],
        ],
        
        # How it works
        section(class_="info-section")[
            h2()["How It Works"],
            div(class_="how-it-works")[
                div(class_="step")[
                    span(class_="step-num")["1"],
                    p()["Install React packages normally: ", span(class_="code")["npm install @mui/material"]],
                ],
                div(class_="step")[
                    span(class_="step-num")["2"],
                    p()["PyNext bundles them with React → Preact aliasing"],
                ],
                div(class_="step")[
                    span(class_="step-num")["3"],
                    p()["React components work seamlessly with PyNext signals"],
                ],
            ],
        ],
        
        # Performance comparison
        section(class_="info-section")[
            h2()["Performance Comparison"],
            div(class_="comparison")[
                div(class_="comparison-item good")[
                    span(class_="label")["PyNext + Preact"],
                    span(class_="value")["~9KB"],
                    span(class_="note")["(5KB runtime + 4KB Preact)"],
                ],
                div(class_="comparison-item bad")[
                    span(class_="label")["React"],
                    span(class_="value")["~42KB"],
                    span(class_="note")["(React + ReactDOM)"],
                ],
            ],
        ],
        
        # Demos
        section(class_="demos")[
            h2()["Live Demos"],
            div(class_="demo-grid")[
                NativeCounter(),
                HybridDemo(),
                ReactButtonDemo(),
            ],
        ],
        
        # Code example
        section(class_="code-section")[
            h2()["Usage Example"],
            div(class_="code-block")[
                """from pynext import page, Signal, div, span, ReactComponent

@page
def dashboard():
    value = Signal(50)
    
    return div()[
        # Native PyNext
        span()["Value: ", value],
        
        # React component with shared signal
        ReactComponent(
            package="@mui/material",
            component="Slider",
            props={
                "value": value,           # Signal as prop
                "onChange": value.set,     # Update signal from React
            }
        )
    ]"""
            ],
        ],
        
        DEMO_STYLES,
    ]


# Styles
from pynext.core.html import Element
style = Element("style")

DEMO_STYLES = style()["""
.container {
    max-width: 900px;
    margin: 0 auto;
    padding: 40px 20px;
    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
}

.nav-back {
    margin-bottom: 32px;
}

.nav-back a {
    color: #6366f1;
    text-decoration: none;
    font-weight: 500;
}

.header {
    text-align: center;
    margin-bottom: 48px;
}

.header h1 {
    font-size: 36px;
    margin: 0 0 16px 0;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.subtitle {
    font-size: 18px;
    color: #6b7280;
    max-width: 600px;
    margin: 0 auto;
}

.info-section {
    margin-bottom: 48px;
}

.info-section h2 {
    font-size: 24px;
    margin: 0 0 24px 0;
    color: #1f2937;
}

.how-it-works {
    display: flex;
    gap: 24px;
    flex-wrap: wrap;
}

.step {
    flex: 1;
    min-width: 200px;
    background: #f9fafb;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
}

.step-num {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    background: #6366f1;
    color: white;
    border-radius: 50%;
    font-weight: 700;
    margin-bottom: 12px;
}

.step p {
    margin: 0;
    color: #4b5563;
}

.comparison {
    display: flex;
    gap: 24px;
}

.comparison-item {
    flex: 1;
    padding: 24px;
    border-radius: 12px;
    text-align: center;
}

.comparison-item.good {
    background: #ecfdf5;
    border: 2px solid #10b981;
}

.comparison-item.bad {
    background: #fef2f2;
    border: 2px solid #ef4444;
}

.comparison-item .label {
    display: block;
    font-weight: 600;
    color: #1f2937;
    margin-bottom: 8px;
}

.comparison-item .value {
    display: block;
    font-size: 32px;
    font-weight: 700;
}

.comparison-item.good .value { color: #10b981; }
.comparison-item.bad .value { color: #ef4444; }

.comparison-item .note {
    display: block;
    font-size: 12px;
    color: #6b7280;
    margin-top: 4px;
}

.demos h2 {
    text-align: center;
}

.demo-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 24px;
    margin-top: 24px;
}

.demo-card {
    background: white;
    padding: 24px;
    border-radius: 12px;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    border: 1px solid #e5e7eb;
}

.demo-card h3 {
    margin: 0 0 12px 0;
    font-size: 18px;
    color: #1f2937;
}

.description {
    font-size: 14px;
    color: #6b7280;
    margin: 0 0 20px 0;
}

.counter-display {
    font-size: 24px;
    text-align: center;
    margin: 20px 0;
}

.count-value, .highlight {
    font-weight: 700;
    color: #6366f1;
}

.value-display {
    font-size: 24px;
    text-align: center;
    margin: 16px 0;
}

.progress-bar {
    height: 8px;
    background: #e5e7eb;
    border-radius: 4px;
    overflow: hidden;
    margin: 16px 0;
}

.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #6366f1, #8b5cf6);
    transition: width 0.2s;
}

.button-group {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    justify-content: center;
}

.btn {
    padding: 10px 20px;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
}

.btn-primary {
    background: #6366f1;
    color: white;
}

.btn-secondary {
    background: #10b981;
    color: white;
}

.btn-outline {
    background: white;
    border: 2px solid #e5e7eb;
    color: #4b5563;
}

.info {
    text-align: center;
    margin: 16px 0;
    color: #6b7280;
}

.note {
    font-size: 12px;
    color: #9ca3af;
    margin-top: 16px;
}

.code {
    background: #1f2937;
    color: #e5e7eb;
    padding: 2px 8px;
    border-radius: 4px;
    font-family: monospace;
    font-size: 13px;
}

.code-section h2 {
    margin-bottom: 16px;
}

.code-block {
    background: #1f2937;
    color: #e5e7eb;
    padding: 20px;
    border-radius: 12px;
    font-family: 'Fira Code', monospace;
    font-size: 14px;
    overflow-x: auto;
    white-space: pre;
    line-height: 1.6;
}

/* React component placeholder styles */
.pynext-react-root {
    min-height: 40px;
}
"""]

