"""
PyNext Keyboard Module

High-level keyboard shortcut handling for PyNext applications.

Provides:
- Shortcut registration with decorators
- Key sequence support (g → d)
- Context-aware shortcuts
- Shortcut display/help components

Usage:
    from pynext.keyboard import on_keydown, on_key_sequence, ShortcutProvider
    
    @on_keydown("cmd+k")
    def open_search():
        search_open.set(True)
    
    @on_key_sequence("g d")
    def go_dashboard():
        navigate("/")
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass

from pynext.core.client import (
    on_keydown as _on_keydown,
    on_key_sequence as _on_key_sequence,
    register_shortcut as _register_shortcut,
    unregister_shortcut as _unregister_shortcut,
    KeyboardShortcut,
    KeySequence,
    _shortcuts,
    _sequences,
)


# Re-export core functions
on_keydown = _on_keydown
on_key_sequence = _on_key_sequence
register_shortcut = _register_shortcut
unregister_shortcut = _unregister_shortcut


# =============================================================================
# Shortcut Display
# =============================================================================

def format_shortcut(shortcut: KeyboardShortcut, platform: str = "auto") -> str:
    """
    Format a shortcut for display.
    
    Args:
        shortcut: The shortcut to format
        platform: "mac", "windows", or "auto" (detect)
    
    Returns:
        Human-readable shortcut string (e.g., "⌘K" or "Ctrl+K")
    """
    import sys
    
    is_mac = platform == "mac" or (platform == "auto" and sys.platform == "darwin")
    
    parts = []
    
    for mod in shortcut.modifiers:
        if mod == "meta":
            parts.append("⌘" if is_mac else "Ctrl")
        elif mod == "ctrl":
            parts.append("Ctrl")
        elif mod == "alt":
            parts.append("⌥" if is_mac else "Alt")
        elif mod == "shift":
            parts.append("⇧" if is_mac else "Shift")
    
    # Format key
    key = shortcut.key.upper()
    if key == "ESCAPE":
        key = "Esc"
    elif key == "ENTER":
        key = "↵" if is_mac else "Enter"
    elif key == "ARROWUP":
        key = "↑"
    elif key == "ARROWDOWN":
        key = "↓"
    elif key == "ARROWLEFT":
        key = "←"
    elif key == "ARROWRIGHT":
        key = "→"
    
    parts.append(key)
    
    return "+" .join(parts) if not is_mac else "".join(parts)


def format_sequence(sequence: KeySequence) -> str:
    """
    Format a key sequence for display.
    
    Returns:
        Human-readable sequence string (e.g., "G → D")
    """
    return " → ".join(k.upper() for k in sequence.keys)


def get_all_shortcuts() -> List[Dict[str, Any]]:
    """
    Get all registered shortcuts for display.
    
    Returns:
        List of shortcut info dictionaries
    """
    result = []
    
    for shortcut in _shortcuts.values():
        result.append({
            "id": shortcut.id,
            "display": format_shortcut(shortcut),
            "key": shortcut.key,
            "modifiers": shortcut.modifiers,
            "context": shortcut.context,
        })
    
    return result


def get_all_sequences() -> List[Dict[str, Any]]:
    """
    Get all registered sequences for display.
    
    Returns:
        List of sequence info dictionaries
    """
    result = []
    
    for sequence in _sequences.values():
        result.append({
            "id": sequence.id,
            "display": format_sequence(sequence),
            "keys": sequence.keys,
        })
    
    return result


# =============================================================================
# Components
# =============================================================================

def ShortcutProvider(children=None):
    """
    Component that provides keyboard shortcut handling.
    
    Automatically injects the keyboard runtime and hydration data.
    Include this in your root layout.
    
    Usage:
        @layout
        def root_layout(children):
            return html()[
                head()[...],
                body()[
                    ShortcutProvider()[
                        children
                    ]
                ]
            ]
    """
    from pynext import div, script
    from pynext.core.client import get_client_hydration_data
    import json
    
    hydration_data = get_client_hydration_data()
    
    return div(data_pynext_keyboard_provider="true")[
        children,
        script()[f"""
            (function() {{
                const data = {json.dumps(hydration_data)};
                if (window.__pynext__?.keyboard?.hydrate) {{
                    window.__pynext__.keyboard.hydrate(data);
                }}
            }})();
        """],
    ]


def ShortcutHint(
    shortcut: str,
    class_: str = "",
):
    """
    Component that displays a keyboard shortcut.
    
    Usage:
        ShortcutHint("cmd+k")  # Displays "⌘K" on Mac, "Ctrl+K" on Windows
    """
    from pynext import kbd, span
    from pynext.tw import cn
    
    # Parse the shortcut
    parts = shortcut.lower().split("+")
    key = parts[-1].upper()
    modifiers = parts[:-1]
    
    # Create display parts
    display_parts = []
    for mod in modifiers:
        if mod in ("cmd", "meta", "command"):
            display_parts.append("⌘")
        elif mod in ("ctrl", "control"):
            display_parts.append("Ctrl")
        elif mod in ("alt", "option"):
            display_parts.append("⌥")
        elif mod == "shift":
            display_parts.append("⇧")
    
    display_parts.append(key)
    
    return kbd(
        class_=cn(
            "inline-flex items-center gap-0.5 px-1.5 py-0.5",
            "text-xs font-mono bg-muted rounded border",
            class_,
        ),
        data_shortcut=shortcut,
    )[
        [span()[part] for part in display_parts]
    ]


def ShortcutsHelpDialog(
    trigger=None,
    class_: str = "",
):
    """
    Component that displays all registered shortcuts in a dialog.
    
    Usage:
        ShortcutsHelpDialog(
            trigger=Button()["?"]
        )
    """
    from pynext import div, h3, span
    from pynext.tw import cn
    from pynext.shadcn import (
        Dialog, DialogTrigger, DialogContent, DialogHeader, DialogTitle,
        Button,
    )
    
    shortcuts = get_all_shortcuts()
    sequences = get_all_sequences()
    
    # Group shortcuts by context
    by_context: Dict[str, list] = {}
    for s in shortcuts:
        ctx = s["context"].title()
        if ctx not in by_context:
            by_context[ctx] = []
        by_context[ctx].append(s)
    
    return Dialog()[
        DialogTrigger()[
            trigger or Button(variant="ghost", size="icon")["?"]
        ],
        DialogContent(class_=cn("max-w-lg", class_))[
            DialogHeader()[
                DialogTitle()["Keyboard Shortcuts"],
            ],
            div(class_="space-y-6 max-h-96 overflow-y-auto py-4")[
                # Shortcuts by context
                [
                    div()[
                        h3(class_="text-sm font-semibold mb-2 text-muted-foreground")[
                            context
                        ],
                        div(class_="space-y-2")[
                            [
                                div(class_="flex items-center justify-between")[
                                    span(class_="text-sm")[s["id"]],
                                    ShortcutHint(
                                        "+".join(s["modifiers"] + [s["key"]])
                                    ),
                                ]
                                for s in items
                            ]
                        ],
                    ]
                    for context, items in by_context.items()
                ],
                
                # Sequences
                sequences and div()[
                    h3(class_="text-sm font-semibold mb-2 text-muted-foreground")[
                        "Key Sequences"
                    ],
                    div(class_="space-y-2")[
                        [
                            div(class_="flex items-center justify-between")[
                                span(class_="text-sm")[seq["id"]],
                                span(class_="text-xs font-mono bg-muted px-2 py-0.5 rounded")[
                                    seq["display"]
                                ],
                            ]
                            for seq in sequences
                        ]
                    ],
                ],
            ],
        ],
    ]


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Decorators
    "on_keydown",
    "on_key_sequence",
    # Functions
    "register_shortcut",
    "unregister_shortcut",
    "format_shortcut",
    "format_sequence",
    "get_all_shortcuts",
    "get_all_sequences",
    # Components
    "ShortcutProvider",
    "ShortcutHint",
    "ShortcutsHelpDialog",
    # Types
    "KeyboardShortcut",
    "KeySequence",
]

