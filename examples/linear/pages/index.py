"""
Linear Clone - Home Page

Landing page for the Linear clone demo.
"""

from pynext import page, div, h1, h2, p, a, span
from pynext.core.html import Element


@page(title="Linear Clone - PyNext Demo")
def index():
    """
    Home page with navigation to features.
    """
    return div(
        class_="home-page",
        style="max-width: 800px; margin: 0 auto; padding: 48px 24px; text-align: center;",
    )[
        # Hero
        div(class_="hero", style="margin-bottom: 48px;")[
            h1(style="font-size: 48px; font-weight: 800; color: #111827; margin: 0 0 16px 0;")[
                "Linear Clone"
            ],
            p(style="font-size: 20px; color: #6b7280; margin: 0;")[
                "A project management demo built with PyNext"
            ],
        ],
        
        # Feature cards
        div(
            class_="features",
            style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 24px; text-align: left;",
        )[
            FeatureCard(
                title="Issue Tracking",
                description="Create, filter, and manage issues with server-side rendering and client-side interactivity.",
                link="/issues",
                icon="📝",
            ),
            FeatureCard(
                title="Kanban Board",
                description="Visualize your workflow with a drag-and-drop Kanban board.",
                link="/issues",
                icon="📊",
            ),
            FeatureCard(
                title="Full Hydration",
                description="Experience seamless server → client state transfer with PyNext's hydration system.",
                link="/issues",
                icon="⚡",
            ),
        ],
        
        # Tech stack
        div(class_="tech-stack", style="margin-top: 48px; padding-top: 48px; border-top: 1px solid #e5e7eb;")[
            h2(style="font-size: 20px; font-weight: 600; color: #374151; margin: 0 0 24px 0;")[
                "Built with PyNext"
            ],
            div(style="display: flex; gap: 32px; justify-content: center; flex-wrap: wrap;")[
                TechBadge("Python", "🐍"),
                TechBadge("Signals", "📡"),
                TechBadge("SSR + Hydration", "💧"),
                TechBadge("SolidJS Principles", "🚀"),
            ],
        ],
    ]


def FeatureCard(title: str, description: str, link: str, icon: str) -> Element:
    """A feature showcase card."""
    return a(
        href=link,
        style="display: block; text-decoration: none; padding: 24px; background: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); transition: transform 0.2s, box-shadow 0.2s;",
    )[
        div(style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;")[
            span(style="font-size: 24px;")[icon],
            h2(style="font-size: 18px; font-weight: 600; color: #111827; margin: 0;")[title],
        ],
        p(style="font-size: 14px; color: #6b7280; margin: 0; line-height: 1.5;")[description],
    ]


def TechBadge(label: str, icon: str) -> Element:
    """A technology badge."""
    return div(
        style="display: flex; align-items: center; gap: 8px; padding: 8px 16px; background: #f3f4f6; border-radius: 8px;",
    )[
        span(style="font-size: 16px;")[icon],
        span(style="font-size: 14px; font-weight: 500; color: #374151;")[label],
    ]

