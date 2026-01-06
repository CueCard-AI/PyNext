"""
Linear Clone App (Shadcn Version)

A clean issue tracker built with PyNext's Shadcn component library.

This demonstrates how Python developers can build beautiful UIs
without writing any CSS - just using semantic Python components.

Run with:
    cd examples/linear-shadcn
    pynext dev --port 3001
"""

from pynext import PyNextApp
from pynext.core.html import html, head, body, title, meta, link, div


# Create the app
app = PyNextApp(
    name="Linear Clone (Shadcn)",
    description="Issue tracker built with PyNext Shadcn components",
)


def layout(children):
    """
    Root layout for the app.
    
    Includes Tailwind CSS for shadcn component styling.
    """
    return html()[
        head()[
            title()["Linear Clone - Shadcn"],
            meta(charset="utf-8"),
            meta(name="viewport", content="width=device-width, initial-scale=1"),
            # Tailwind CSS (required for shadcn)
            link(
                href="https://cdn.jsdelivr.net/npm/tailwindcss@3.4.1/dist/tailwind.min.css",
                rel="stylesheet"
            ),
            # CSS variables for shadcn theming
            """
            <style>
                :root {
                    --background: 0 0% 100%;
                    --foreground: 222.2 84% 4.9%;
                    --card: 0 0% 100%;
                    --card-foreground: 222.2 84% 4.9%;
                    --popover: 0 0% 100%;
                    --popover-foreground: 222.2 84% 4.9%;
                    --primary: 221.2 83.2% 53.3%;
                    --primary-foreground: 210 40% 98%;
                    --secondary: 210 40% 96%;
                    --secondary-foreground: 222.2 47.4% 11.2%;
                    --muted: 210 40% 96%;
                    --muted-foreground: 215.4 16.3% 46.9%;
                    --accent: 210 40% 96%;
                    --accent-foreground: 222.2 47.4% 11.2%;
                    --destructive: 0 84.2% 60.2%;
                    --destructive-foreground: 210 40% 98%;
                    --border: 214.3 31.8% 91.4%;
                    --input: 214.3 31.8% 91.4%;
                    --ring: 221.2 83.2% 53.3%;
                    --radius: 0.5rem;
                }
                
                body {
                    background: hsl(var(--background));
                    color: hsl(var(--foreground));
                    font-family: system-ui, -apple-system, sans-serif;
                }
            </style>
            """
        ],
        body()[
            div(id="__pynext")[
                children
            ],
        ],
    ]


# Export for PyNext
__all__ = ["app", "layout"]


