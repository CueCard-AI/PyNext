"""
Root layout for the example application.

This layout wraps all pages and provides:
- Navigation
- Main content area
- Footer
"""

from pynext import layout, div, nav, main, footer, a, h1

@layout
def root_layout(children):
    """Root layout that wraps all pages."""
    return div(class_="app-layout")[
        # Navigation
        nav(class_="main-nav")[
            div(class_="nav-brand")[
                a(href="/")[h1()["PyNext"]]
            ],
            div(class_="nav-links")[
                a(href="/")["Home"],
                a(href="/about")["About"],
                a(href="/dashboard")["Dashboard"],
                a(href="/api-demo")["API Demo"],
            ]
        ],
        
        # Main content
        main(class_="main-content")[
            children
        ],
        
        # Footer
        footer(class_="main-footer")[
            div()["© 2024 PyNext Example App"],
            div()[
                a(href="https://github.com/yourusername/pynext", target="_blank")[
                    "GitHub"
                ]
            ]
        ]
    ]

