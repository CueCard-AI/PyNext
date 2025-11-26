"""
PyNext Theme Module

Dark mode and theming support for PyNext applications.

Provides:
- Theme state management
- System preference detection
- Flash prevention
- Theme toggle components

Usage:
    from pynext.theme import use_theme, ThemeProvider, ThemeToggle
    
    theme = use_theme()
    
    # In layout
    ThemeProvider()[
        children
    ]
    
    # Toggle button
    ThemeToggle()
"""

from __future__ import annotations

from typing import Any, Callable, Optional
from dataclasses import dataclass

from pynext.core.client import (
    use_theme as _use_theme,
    use_storage,
    StorageSignal,
    ThemeState,
)


# Re-export core function
use_theme = _use_theme


# =============================================================================
# Theme Utilities
# =============================================================================

def get_flash_prevention_script(storage_key: str = "theme") -> str:
    """
    Get JavaScript to prevent theme flash on page load.
    
    Include this in the <head> of your HTML before any other scripts.
    
    Returns:
        JavaScript code as a string
    """
    return f"""
(function() {{
    try {{
        var mode = localStorage.getItem('{storage_key}');
        var prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        var isDark = mode === 'dark' || (mode === 'system' && prefersDark) || (!mode && prefersDark);
        if (isDark) {{
            document.documentElement.classList.add('dark');
            document.documentElement.style.colorScheme = 'dark';
        }}
    }} catch (e) {{}}
}})();
""".strip()


# =============================================================================
# Components
# =============================================================================

def ThemeProvider(
    default: str = "system",
    storage_key: str = "theme",
    children=None,
):
    """
    Component that provides theme management.
    
    Includes:
    - Flash prevention script
    - Theme hydration
    - System preference listening
    
    Usage:
        @layout
        def root_layout(children):
            return html()[
                head()[
                    # Flash prevention goes in head
                    ThemeScript(),
                ],
                body()[
                    ThemeProvider()[
                        children
                    ]
                ]
            ]
    """
    from pynext import div, script
    import json
    
    config = {
        "default": default,
        "storageKey": storage_key,
    }
    
    return div(data_pynext_theme_provider="true")[
        children,
        script()[f"""
            (function() {{
                const config = {json.dumps(config)};
                if (window.__pynext__?.theme?.hydrate) {{
                    window.__pynext__.theme.hydrate(config);
                }}
            }})();
        """],
    ]


def ThemeScript(storage_key: str = "theme"):
    """
    Flash prevention script for the <head>.
    
    Include this in your layout's head to prevent theme flash.
    
    Usage:
        head()[
            ThemeScript(),
            # other head elements
        ]
    """
    from pynext import script
    
    return script()[get_flash_prevention_script(storage_key)]


def ThemeToggle(
    class_: str = "",
    show_label: bool = False,
):
    """
    Button to toggle between light/dark/system themes.
    
    Usage:
        ThemeToggle()  # Just icon
        ThemeToggle(show_label=True)  # Icon + label
    """
    from pynext import button, span, div
    from pynext.tw import cn
    
    return button(
        type="button",
        class_=cn(
            "inline-flex items-center justify-center gap-2",
            "h-9 w-9 rounded-md",
            "hover:bg-accent hover:text-accent-foreground",
            "transition-colors",
            "w-auto px-3" if show_label else "",
            class_,
        ),
        onclick="__pynext__.theme.cycle()",
        aria_label="Toggle theme",
        data_pynext_theme_toggle="true",
    )[
        # Sun icon (shown in light mode)
        span(class_="dark:hidden")["☀️"],
        # Moon icon (shown in dark mode)  
        span(class_="hidden dark:inline")["🌙"],
        # Label
        show_label and span(class_="text-sm")[
            span(class_="dark:hidden")["Light"],
            span(class_="hidden dark:inline")["Dark"],
        ],
    ]


def ThemeSwitcher(class_: str = ""):
    """
    Dropdown for selecting theme mode (light/dark/system).
    
    More explicit than ThemeToggle - shows all three options.
    """
    from pynext import div, button, span
    from pynext.tw import cn
    from pynext.shadcn import (
        DropdownMenu, DropdownMenuTrigger, DropdownMenuContent,
        DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator,
        Button,
    )
    
    return DropdownMenu()[
        DropdownMenuTrigger()[
            Button(variant="ghost", size="icon")[
                span(class_="dark:hidden")["☀️"],
                span(class_="hidden dark:inline")["🌙"],
            ]
        ],
        DropdownMenuContent(align="end")[
            DropdownMenuLabel()["Theme"],
            DropdownMenuSeparator(),
            DropdownMenuItem(
                onclick="__pynext__.theme.setMode('light')",
            )["☀️ Light"],
            DropdownMenuItem(
                onclick="__pynext__.theme.setMode('dark')",
            )["🌙 Dark"],
            DropdownMenuItem(
                onclick="__pynext__.theme.setMode('system')",
            )["💻 System"],
        ],
    ]


def ColorSchemeSelect(
    class_: str = "",
    name: str = "theme",
):
    """
    Select input for theme in forms/settings.
    """
    from pynext import select, option, label, div
    from pynext.tw import cn
    
    return div(class_=cn("space-y-2", class_))[
        label(html_for=name, class_="text-sm font-medium")["Color Scheme"],
        select(
            id=name,
            name=name,
            class_=cn(
                "w-full h-10 rounded-md border border-input",
                "bg-background px-3 py-2 text-sm",
                "focus:outline-none focus:ring-2 focus:ring-ring",
            ),
            onchange="__pynext__.theme.setMode(this.value)",
        )[
            option(value="light")["Light"],
            option(value="dark")["Dark"],
            option(value="system")["System"],
        ],
    ]


# =============================================================================
# CSS Variables
# =============================================================================

def get_theme_css_variables(theme: str = "default") -> str:
    """
    Get CSS variables for a theme.
    
    Useful for generating custom themes.
    """
    themes = {
        "default": {
            # Light mode
            "light": {
                "--background": "0 0% 100%",
                "--foreground": "222.2 84% 4.9%",
                "--primary": "199 89% 48%",
                "--primary-foreground": "210 40% 98%",
            },
            # Dark mode
            "dark": {
                "--background": "222.2 84% 4.9%",
                "--foreground": "210 40% 98%",
                "--primary": "199 89% 48%",
                "--primary-foreground": "222.2 47.4% 11.2%",
            },
        },
    }
    
    if theme not in themes:
        theme = "default"
    
    lines = [":root {"]
    for var, value in themes[theme]["light"].items():
        lines.append(f"  {var}: {value};")
    lines.append("}")
    lines.append("")
    lines.append(".dark {")
    for var, value in themes[theme]["dark"].items():
        lines.append(f"  {var}: {value};")
    lines.append("}")
    
    return "\n".join(lines)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Core
    "use_theme",
    "get_flash_prevention_script",
    # Components
    "ThemeProvider",
    "ThemeScript",
    "ThemeToggle",
    "ThemeSwitcher",
    "ColorSchemeSelect",
    # Utilities
    "get_theme_css_variables",
    # Types
    "StorageSignal",
    "ThemeState",
]

