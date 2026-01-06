"""
Linear Clone Home Page (Shadcn Version)

Redirects to the issues page.
"""

from pynext import page
from pynext.core.html import a, Element
from pynext.shadcn import Column, Text, Heading, Button, Card, CardContent


@page(title="Linear Clone - Shadcn")
def index() -> Element:
    """Home page - welcome screen."""
    return Column(gap="lg", align="center", padding="xl", class_="min-h-screen")[
        Card(class_="max-w-md w-full")[
            CardContent(class_="p-6")[
                Column(gap="md", align="center")[
                    Heading(level=1)["Linear Clone"],
                    Text(
                        "A clean issue tracker built with PyNext and Shadcn components.",
                        color="muted",
                        as_element="p"
                    ),
                    a(href="/issues")[
                        Button(size="lg")["View Issues →"]
                    ],
                ],
            ],
        ],
    ]


