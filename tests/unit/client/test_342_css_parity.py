"""
Phase 34.2: CSS Styling Integration Tests

Mini-application tests that verify Python-to-JavaScript parity
for CSS styling operations:
- Theme switching
- Responsive layouts
- Animations
- Dynamic styling
- UI Components (Card, Modal, Dropdown, Tabs, etc.)

Total: 40 tests
"""

import pytest
from pynext.transpiler import transpile


# =============================================================================
# Theme System Integration Tests (5 tests)
# =============================================================================

class TestThemeIntegration:
    """Integration tests for theme management."""
    
    def test_complete_theme_setup(self):
        """Complete theme setup should transpile correctly."""
        code = '''
from pynext.client import document, window
from pynext.client.css_vars import set_theme, toggle_theme

# Define themes
light_theme = {
    "bg": "#ffffff",
    "fg": "#1a1a1a",
    "primary": "#3b82f6",
    "secondary": "#64748b",
    "border": "#e2e8f0",
    "radius": "8px",
    "shadow": "0 2px 4px rgba(0,0,0,0.1)",
}

dark_theme = {
    "bg": "#0f172a",
    "fg": "#f1f5f9",
    "primary": "#60a5fa",
    "secondary": "#94a3b8",
    "border": "#334155",
    "radius": "8px",
    "shadow": "0 2px 4px rgba(0,0,0,0.3)",
}

# Apply based on system preference
is_dark = toggle_theme(light_theme, dark_theme)
'''
        result = transpile(code)
        assert "light_theme" in result
        assert "dark_theme" in result
        assert "toggle_theme" in result
    
    def test_theme_toggle_button(self):
        """Theme toggle button handler should work."""
        code = '''
from pynext.client import document
from pynext.client.css_vars import set_theme

light = {"bg": "#fff", "fg": "#000"}
dark = {"bg": "#000", "fg": "#fff"}
is_dark = False

def toggle():
    global is_dark
    is_dark = not is_dark
    if is_dark:
        set_theme(dark)
    else:
        set_theme(light)

btn = document.getElementById("theme-toggle")
btn.addEventListener("click", toggle)
'''
        result = transpile(code)
        assert "toggle" in result
        assert "set_theme" in result
        assert "addEventListener" in result
    
    def test_component_scoped_theme(self):
        """Scoped theming on component should work."""
        code = '''
from pynext.client import document
from pynext.client.css_vars import set_theme, set_css_var

# Global theme
set_theme({
    "primary": "#3b82f6",
    "radius": "8px",
})

# Override on specific card
card = document.getElementById("special-card")
set_css_var("primary", "#ef4444", element=card)
set_css_var("radius", "16px", element=card)
'''
        result = transpile(code)
        assert "special-card" in result
        assert "set_css_var" in result or "setProperty" in result
    
    def test_read_and_apply_theme(self):
        """Reading and applying theme variables should work."""
        code = '''
from pynext.client import window, document
from pynext.client.css_vars import get_css_var, set_css_var

# Read current primary color
current = get_css_var("primary")

# Calculate complementary color
# (would be done in real app)
complementary = current

# Apply to secondary
set_css_var("secondary", complementary)
'''
        result = transpile(code)
        assert "get_css_var" in result or "getPropertyValue" in result
        assert "set_css_var" in result or "setProperty" in result
    
    def test_system_theme_detection(self):
        """System theme detection and auto-switching."""
        code = '''
from pynext.client import window
from pynext.client.css_vars import set_theme

light = {"bg": "#ffffff"}
dark = {"bg": "#1a1a2e"}

def apply_system_theme():
    if window.matchMedia("(prefers-color-scheme: dark)").matches:
        set_theme(dark)
    else:
        set_theme(light)

# Initial application
apply_system_theme()

# Watch for changes
mql = window.matchMedia("(prefers-color-scheme: dark)")
mql.addEventListener("change", lambda e: apply_system_theme())
'''
        result = transpile(code)
        assert "matchMedia" in result
        assert "prefers-color-scheme" in result
        assert "addEventListener" in result


# =============================================================================
# Responsive Styling Integration Tests (3 tests)
# =============================================================================

class TestResponsiveIntegration:
    """Integration tests for responsive styling."""
    
    def test_responsive_layout_switch(self):
        """Responsive layout switching should work."""
        code = '''
from pynext.client import window, document
from pynext.client.style_utils import set_styles

def update_layout():
    container = document.getElementById("container")
    
    if window.matchMedia("(max-width: 768px)").matches:
        # Mobile layout
        set_styles(container, {
            "flexDirection": "column",
            "padding": "16px",
            "gap": "8px",
        })
    else:
        # Desktop layout
        set_styles(container, {
            "flexDirection": "row",
            "padding": "32px",
            "gap": "24px",
        })

update_layout()
window.matchMedia("(max-width: 768px)").addEventListener("change", update_layout)
'''
        result = transpile(code)
        assert "matchMedia" in result
        assert "flexDirection" in result
    
    def test_responsive_class_toggle(self):
        """Responsive class toggling should work."""
        code = '''
from pynext.client import window, document
from pynext.client.style_utils import toggle_class

nav = document.getElementById("nav")
is_mobile = window.matchMedia("(max-width: 768px)").matches

toggle_class(nav, "mobile-nav", is_mobile)
toggle_class(nav, "desktop-nav", not is_mobile)
'''
        result = transpile(code)
        assert "toggle_class" in result or "classList.toggle" in result
        assert "mobile-nav" in result
    
    def test_responsive_sidebar(self):
        """Responsive sidebar should work."""
        code = '''
from pynext.client import document, window
from pynext.client.style_utils import classes

def get_sidebar_classes():
    is_desktop = window.matchMedia("(min-width: 1024px)").matches
    return classes(
        "sidebar",
        ("expanded", is_desktop),
        ("collapsed", not is_desktop),
    )

sidebar = document.getElementById("sidebar")
sidebar.className = get_sidebar_classes()
'''
        result = transpile(code)
        assert "classes" in result
        assert "expanded" in result
        assert "collapsed" in result


# =============================================================================
# Animation Integration Tests (4 tests)
# =============================================================================

class TestAnimationIntegration:
    """Integration tests for animations."""
    
    def test_modal_open_animation(self):
        """Modal open animation should work."""
        code = '''
from pynext.client import document
from pynext.client.animation import fade_in, scale_in

async def open_modal():
    modal = document.getElementById("modal")
    overlay = document.getElementById("overlay")
    
    modal.style.display = "block"
    overlay.style.display = "block"
    
    # Animate in parallel
    await fade_in(overlay, duration=200)
    await scale_in(modal, duration=300)

open_modal()
'''
        result = transpile(code)
        assert "fade_in" in result
        assert "scale_in" in result
        assert "await" in result
    
    def test_notification_animation(self):
        """Notification slide in/out should work."""
        code = '''
from pynext.client import document
from pynext.client.animation import slide_in, slide_out

async def show_notification(message, duration=3000):
    # Create notification
    notif = document.createElement("div")
    notif.className = "notification"
    notif.textContent = message
    document.body.appendChild(notif)
    
    # Slide in
    await slide_in(notif, direction="right")
    
    # Wait
    # await sleep(duration)  # Would need async sleep
    
    # Slide out
    await slide_out(notif, direction="right")
    notif.remove()
'''
        result = transpile(code)
        assert "slide_in" in result
        assert "slide_out" in result
        assert "appendChild" in result
    
    def test_form_validation_shake(self):
        """Form validation shake animation should work."""
        code = '''
from pynext.client import document
from pynext.client.animation import shake
from pynext.client.style_utils import add_classes, remove_classes

async def validate_input(input_el):
    if not input_el.value:
        add_classes(input_el, "error", "border-red-500")
        await shake(input_el)
        return False
    else:
        remove_classes(input_el, "error", "border-red-500")
        return True
'''
        result = transpile(code)
        assert "shake" in result
        assert "add_classes" in result or "classList.add" in result
    
    def test_button_feedback_animation(self):
        """Button click feedback animation should work."""
        code = '''
from pynext.client import document
from pynext.client.animation import pulse

async def on_button_click(event):
    btn = event.target
    await pulse(btn, scale=1.1, duration=150)
    # Do action after animation
    print("Action completed")

btn = document.getElementById("action-btn")
btn.addEventListener("click", on_button_click)
'''
        result = transpile(code)
        assert "pulse" in result
        assert "addEventListener" in result


# =============================================================================
# Dynamic Styling Integration Tests (3 tests)
# =============================================================================

class TestDynamicStylingIntegration:
    """Integration tests for dynamic styling patterns."""
    
    def test_style_calculator(self):
        """Dynamic style calculation should work."""
        code = '''
from pynext.client import document
from pynext.client.styles import StylesProxy

el = document.getElementById("progress")
styles = StylesProxy(el)

progress = 75

# Set width based on progress
styles["width"] = f"{progress}%"

# Set color based on progress
if progress < 30:
    styles["background-color"] = "#ef4444"  # Red
elif progress < 70:
    styles["background-color"] = "#f59e0b"  # Yellow
else:
    styles["background-color"] = "#22c55e"  # Green
'''
        result = transpile(code)
        assert "StylesProxy" in result
        assert "width" in result
        assert "background-color" in result
    
    def test_conditional_classes_form(self):
        """Form with conditional classes should work."""
        code = '''
from pynext.client import document
from pynext.client.style_utils import classes

def get_input_classes(value, is_valid, is_focused):
    return classes(
        "input",
        "px-4",
        "py-2",
        "rounded-lg",
        ("ring-2", is_focused),
        ("ring-blue-500", is_focused and is_valid),
        ("ring-red-500", is_focused and not is_valid),
        {
            "border-green-500": is_valid and value,
            "border-red-500": not is_valid and value,
            "border-gray-300": not value,
        },
    )

input_el = document.getElementById("email")
input_el.className = get_input_classes("test@example.com", True, True)
'''
        result = transpile(code)
        assert "classes" in result
        assert "ring-blue-500" in result
    
    def test_style_composition(self):
        """Complex style composition should work."""
        code = '''
from pynext.client import document
from pynext.client.css_vars import set_css_var
from pynext.client.style_utils import set_styles

card = document.getElementById("card")

# Set base CSS variables
set_css_var("card-bg", "#ffffff")
set_css_var("card-shadow", "0 4px 6px rgba(0,0,0,0.1)")

# Apply inline styles for layout
set_styles(card, {
    "display": "flex",
    "flexDirection": "column",
    "padding": "var(--card-padding, 24px)",
    "backgroundColor": "var(--card-bg)",
    "boxShadow": "var(--card-shadow)",
    "borderRadius": "var(--radius, 8px)",
})

# Add classes for utilities
card.classList.add("transition-all", "hover:shadow-lg")
'''
        result = transpile(code)
        assert "set_css_var" in result or "setProperty" in result
        assert "set_styles" in result or "setProperty" in result
        assert "classList.add" in result


# =============================================================================
# Card Component Tests (4 tests)
# =============================================================================

class TestCardComponent:
    """Mini-app tests for a complete card component."""
    
    def test_interactive_card(self):
        """Card with hover effects and click handling."""
        code = '''
from pynext.client import document
from pynext.client.style_utils import classes, set_styles
from pynext.client.css_vars import set_css_var

def create_card(title, content, variant="default"):
    card = document.createElement("div")
    
    # Dynamic classes based on variant
    card.className = classes(
        "card",
        "rounded-lg",
        "shadow-md",
        "transition-all",
        "duration-300",
        {
            "bg-white": variant == "default",
            "bg-blue-50": variant == "primary",
            "bg-red-50": variant == "danger",
        },
    )
    
    # Set CSS variables for theming
    set_css_var("card-padding", "24px", element=card)
    
    # Inline styles
    set_styles(card, {
        "padding": "var(--card-padding)",
        "cursor": "pointer",
    })
    
    # Hover handlers
    def on_hover(e):
        card.style.transform = "translateY(-4px)"
        card.style.boxShadow = "0 8px 16px rgba(0,0,0,0.15)"
    
    def on_leave(e):
        card.style.transform = "translateY(0)"
        card.style.boxShadow = "0 2px 4px rgba(0,0,0,0.1)"
    
    card.addEventListener("mouseenter", on_hover)
    card.addEventListener("mouseleave", on_leave)
    
    return card
'''
        result = transpile(code)
        assert "classes" in result
        assert "set_css_var" in result or "setProperty" in result
        assert "translateY" in result
        assert "mouseenter" in result
    
    def test_card_skeleton_loading(self):
        """Card with skeleton loading state."""
        code = '''
from pynext.client import document
from pynext.client.style_utils import toggle_class, set_styles

def toggle_loading(card, is_loading):
    skeleton = card.querySelector(".skeleton")
    content = card.querySelector(".content")
    
    if is_loading:
        skeleton.style.display = "block"
        content.style.display = "none"
        # Add shimmer animation
        set_styles(skeleton, {
            "animation": "shimmer 1.5s infinite",
            "background": "linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%)",
            "backgroundSize": "200% 100%",
        })
    else:
        skeleton.style.display = "none"
        content.style.display = "block"
'''
        result = transpile(code)
        assert "skeleton" in result
        assert "shimmer" in result
        assert "linear-gradient" in result
    
    def test_expandable_card(self):
        """Card that expands on click."""
        code = '''
from pynext.client import document
from pynext.client.animation import scale_in

async def setup_expandable_card():
    card = document.getElementById("expandable-card")
    is_expanded = False
    
    async def toggle_expand(e):
        nonlocal is_expanded
        is_expanded = not is_expanded
        
        if is_expanded:
            card.style.height = "auto"
            card.style.maxHeight = "500px"
            await scale_in(card.querySelector(".details"))
        else:
            card.style.maxHeight = "100px"
    
    card.addEventListener("click", toggle_expand)
'''
        result = transpile(code)
        assert "expandable-card" in result
        assert "maxHeight" in result
        assert "scale_in" in result
    
    def test_card_selection(self):
        """Selectable card grid."""
        code = '''
from pynext.client import document
from pynext.client.style_utils import toggle_class, classes

selected_cards = []

def select_card(card_id):
    card = document.getElementById(card_id)
    
    if card_id in selected_cards:
        selected_cards.remove(card_id)
        toggle_class(card, "ring-2", False)
        toggle_class(card, "ring-blue-500", False)
        toggle_class(card, "bg-blue-50", False)
    else:
        selected_cards.append(card_id)
        toggle_class(card, "ring-2", True)
        toggle_class(card, "ring-blue-500", True)
        toggle_class(card, "bg-blue-50", True)
'''
        result = transpile(code)
        assert "toggle_class" in result or "classList.toggle" in result
        assert "ring-2" in result
        assert "ring-blue-500" in result


# =============================================================================
# Modal/Dialog Tests (4 tests)
# =============================================================================

class TestModalComponent:
    """Mini-app tests for modal/dialog component."""
    
    def test_complete_modal_flow(self):
        """Full modal with backdrop and animations."""
        code = '''
from pynext.client import document
from pynext.client.animation import fade_in, fade_out, scale_in, scale_out
from pynext.client.style_utils import set_styles

async def open_modal(modal_id):
    modal = document.getElementById(modal_id)
    backdrop = modal.querySelector(".backdrop")
    dialog = modal.querySelector(".dialog")
    
    # Show container
    modal.style.display = "flex"
    
    # Set backdrop styles
    set_styles(backdrop, {
        "position": "fixed",
        "inset": "0",
        "backgroundColor": "rgba(0,0,0,0.5)",
    })
    
    # Set dialog styles
    set_styles(dialog, {
        "position": "relative",
        "margin": "auto",
        "backgroundColor": "white",
        "borderRadius": "12px",
        "padding": "24px",
    })
    
    # Animate in
    await fade_in(backdrop, duration=200)
    await scale_in(dialog, duration=300)

async def close_modal(modal_id):
    modal = document.getElementById(modal_id)
    backdrop = modal.querySelector(".backdrop")
    dialog = modal.querySelector(".dialog")
    
    await scale_out(dialog, duration=200)
    await fade_out(backdrop, duration=150)
    modal.style.display = "none"
'''
        result = transpile(code)
        assert "fade_in" in result
        assert "scale_in" in result
        assert "scale_out" in result
        assert "backdrop" in result
    
    def test_modal_close_on_backdrop(self):
        """Modal closes when clicking backdrop."""
        code = '''
from pynext.client import document

def setup_modal_backdrop(modal_id):
    modal = document.getElementById(modal_id)
    backdrop = modal.querySelector(".backdrop")
    dialog = modal.querySelector(".dialog")
    
    def on_backdrop_click(e):
        if e.target == backdrop:
            modal.style.display = "none"
    
    backdrop.addEventListener("click", on_backdrop_click)
    
    # Prevent dialog click from closing
    def stop_propagation(e):
        e.stopPropagation()
    
    dialog.addEventListener("click", stop_propagation)
'''
        result = transpile(code)
        assert "stopPropagation" in result
        assert "e.target" in result
    
    def test_modal_focus_trap(self):
        """Modal with focus management."""
        code = '''
from pynext.client import document

def trap_focus(modal):
    focusable = modal.querySelectorAll(
        "button, [href], input, select, textarea, [tabindex]"
    )
    
    if focusable.length > 0:
        first = focusable.item(0)
        last = focusable.item(focusable.length - 1)
        
        first.focus()
        
        def on_keydown(e):
            if e.key == "Tab":
                if e.shiftKey:
                    if document.activeElement == first:
                        e.preventDefault()
                        last.focus()
                else:
                    if document.activeElement == last:
                        e.preventDefault()
                        first.focus()
        
        modal.addEventListener("keydown", on_keydown)
'''
        result = transpile(code)
        assert "querySelectorAll" in result
        assert "focus" in result
        assert "activeElement" in result
    
    def test_confirm_dialog(self):
        """Confirm dialog with action buttons."""
        code = '''
from pynext.client import document
from pynext.client.style_utils import classes

def create_confirm_dialog(title, message, on_confirm, on_cancel):
    dialog = document.createElement("div")
    dialog.className = "fixed inset-0 flex items-center justify-center"
    
    confirm_btn = document.createElement("button")
    confirm_btn.className = classes(
        "px-4", "py-2", "rounded-lg",
        "bg-blue-500", "text-white",
        "hover:bg-blue-600",
        "transition-colors",
    )
    confirm_btn.textContent = "Confirm"
    confirm_btn.addEventListener("click", on_confirm)
    
    cancel_btn = document.createElement("button")
    cancel_btn.className = classes(
        "px-4", "py-2", "rounded-lg",
        "bg-gray-200", "text-gray-800",
        "hover:bg-gray-300",
        "transition-colors",
    )
    cancel_btn.textContent = "Cancel"
    cancel_btn.addEventListener("click", on_cancel)
    
    return dialog
'''
        result = transpile(code)
        assert "classes" in result
        assert "Confirm" in result
        assert "Cancel" in result


# =============================================================================
# Dropdown/Menu Tests (3 tests)
# =============================================================================

class TestDropdownComponent:
    """Mini-app tests for dropdown menu component."""
    
    def test_dropdown_toggle(self):
        """Dropdown menu with toggle."""
        code = '''
from pynext.client import document
from pynext.client.animation import fade_in, fade_out
from pynext.client.style_utils import set_styles

async def setup_dropdown(trigger_id, menu_id):
    trigger = document.getElementById(trigger_id)
    menu = document.getElementById(menu_id)
    is_open = False
    
    # Initial hidden state
    menu.style.display = "none"
    set_styles(menu, {
        "position": "absolute",
        "top": "100%",
        "left": "0",
        "minWidth": "200px",
        "backgroundColor": "white",
        "borderRadius": "8px",
        "boxShadow": "0 4px 12px rgba(0,0,0,0.15)",
        "zIndex": "50",
    })
    
    async def toggle(e):
        nonlocal is_open
        is_open = not is_open
        
        if is_open:
            menu.style.display = "block"
            await fade_in(menu, duration=150)
        else:
            await fade_out(menu, duration=100)
            menu.style.display = "none"
    
    trigger.addEventListener("click", toggle)
'''
        result = transpile(code)
        assert "dropdown" in result or "trigger" in result
        assert "fade_in" in result
        assert "zIndex" in result
    
    def test_dropdown_close_outside(self):
        """Dropdown closes on outside click."""
        code = '''
from pynext.client import document

def setup_outside_click(menu_id):
    menu = document.getElementById(menu_id)
    
    def on_document_click(e):
        if not menu.contains(e.target):
            menu.style.display = "none"
    
    document.addEventListener("click", on_document_click)
'''
        result = transpile(code)
        assert "contains" in result
        assert "document.addEventListener" in result
    
    def test_dropdown_keyboard_nav(self):
        """Dropdown with keyboard navigation."""
        code = '''
from pynext.client import document
from pynext.client.style_utils import toggle_class

def setup_keyboard_nav(menu):
    items = menu.querySelectorAll("[role=menuitem]")
    current_index = -1
    
    def highlight(index):
        nonlocal current_index
        # Remove highlight from previous
        if current_index >= 0:
            toggle_class(items.item(current_index), "bg-gray-100", False)
        
        # Add highlight to current
        current_index = index
        toggle_class(items.item(current_index), "bg-gray-100", True)
        items.item(current_index).focus()
    
    def on_keydown(e):
        if e.key == "ArrowDown":
            e.preventDefault()
            next_idx = (current_index + 1) % items.length
            highlight(next_idx)
        elif e.key == "ArrowUp":
            e.preventDefault()
            prev_idx = (current_index - 1) % items.length
            highlight(prev_idx)
        elif e.key == "Enter":
            items.item(current_index).click()
    
    menu.addEventListener("keydown", on_keydown)
'''
        result = transpile(code)
        assert "ArrowDown" in result
        assert "ArrowUp" in result
        assert "menuitem" in result


# =============================================================================
# Tabs Component Tests (3 tests)
# =============================================================================

class TestTabsComponent:
    """Mini-app tests for tabs component."""
    
    def test_basic_tabs(self):
        """Basic tabs with content switching."""
        code = '''
from pynext.client import document
from pynext.client.style_utils import toggle_class

def setup_tabs(container_id):
    container = document.getElementById(container_id)
    tabs = container.querySelectorAll("[role=tab]")
    panels = container.querySelectorAll("[role=tabpanel]")
    
    def select_tab(index):
        # Deselect all tabs
        for i in range(tabs.length):
            toggle_class(tabs.item(i), "border-b-2", False)
            toggle_class(tabs.item(i), "border-blue-500", False)
            toggle_class(tabs.item(i), "text-blue-600", False)
            panels.item(i).style.display = "none"
        
        # Select current tab
        toggle_class(tabs.item(index), "border-b-2", True)
        toggle_class(tabs.item(index), "border-blue-500", True)
        toggle_class(tabs.item(index), "text-blue-600", True)
        panels.item(index).style.display = "block"
    
    # Attach click handlers
    for i in range(tabs.length):
        tabs.item(i).addEventListener("click", lambda e, idx=i: select_tab(idx))
    
    # Select first tab
    select_tab(0)
'''
        result = transpile(code)
        assert "role=tab" in result
        assert "toggle_class" in result or "classList.toggle" in result
        assert "border-blue-500" in result
    
    def test_animated_tab_indicator(self):
        """Tabs with sliding indicator."""
        code = '''
from pynext.client import document
from pynext.client.style_utils import set_styles

def setup_animated_tabs(container_id):
    container = document.getElementById(container_id)
    tabs = container.querySelectorAll("[role=tab]")
    indicator = container.querySelector(".tab-indicator")
    
    def move_indicator(tab):
        rect = tab.getBoundingClientRect()
        container_rect = container.getBoundingClientRect()
        
        set_styles(indicator, {
            "width": f"{rect.width}px",
            "transform": f"translateX({rect.left - container_rect.left}px)",
            "transition": "transform 0.3s ease, width 0.3s ease",
        })
    
    for i in range(tabs.length):
        tabs.item(i).addEventListener("click", lambda e: move_indicator(e.target))
'''
        result = transpile(code)
        assert "getBoundingClientRect" in result
        assert "translateX" in result
        assert "transition" in result
    
    def test_vertical_tabs(self):
        """Vertical tabs layout."""
        code = '''
from pynext.client import document
from pynext.client.style_utils import set_styles, toggle_class

def create_vertical_tabs():
    container = document.createElement("div")
    set_styles(container, {
        "display": "flex",
        "flexDirection": "row",
        "gap": "16px",
    })
    
    tab_list = document.createElement("div")
    set_styles(tab_list, {
        "display": "flex",
        "flexDirection": "column",
        "gap": "4px",
        "minWidth": "200px",
    })
    
    content = document.createElement("div")
    set_styles(content, {
        "flex": "1",
        "padding": "16px",
    })
    
    container.appendChild(tab_list)
    container.appendChild(content)
    
    return container
'''
        result = transpile(code)
        assert "flexDirection" in result
        assert "column" in result
        assert "appendChild" in result


# =============================================================================
# Form Styling Tests (4 tests)
# =============================================================================

class TestFormStyling:
    """Mini-app tests for form styling."""
    
    def test_input_focus_states(self):
        """Input with focus states."""
        code = '''
from pynext.client import document
from pynext.client.style_utils import toggle_class, set_styles

def setup_input(input_id):
    input_el = document.getElementById(input_id)
    label = input_el.previousElementSibling
    
    def on_focus(e):
        toggle_class(input_el, "ring-2", True)
        toggle_class(input_el, "ring-blue-500", True)
        toggle_class(input_el, "border-blue-500", True)
        # Float label
        set_styles(label, {
            "transform": "translateY(-24px) scale(0.85)",
            "color": "#3b82f6",
        })
    
    def on_blur(e):
        toggle_class(input_el, "ring-2", False)
        toggle_class(input_el, "ring-blue-500", False)
        toggle_class(input_el, "border-blue-500", False)
        # Reset label if empty
        if not input_el.value:
            set_styles(label, {
                "transform": "translateY(0) scale(1)",
                "color": "#6b7280",
            })
    
    input_el.addEventListener("focus", on_focus)
    input_el.addEventListener("blur", on_blur)
'''
        result = transpile(code)
        assert "ring-2" in result
        assert "translateY" in result
        assert "previousElementSibling" in result
    
    def test_validation_states(self):
        """Form with validation states."""
        code = '''
from pynext.client import document
from pynext.client.style_utils import classes, toggle_class
from pynext.client.animation import shake

async def validate_field(field_id, validator):
    field = document.getElementById(field_id)
    error_msg = field.nextElementSibling
    
    is_valid = validator(field.value)
    
    if not is_valid:
        toggle_class(field, "border-red-500", True)
        toggle_class(field, "bg-red-50", True)
        error_msg.style.display = "block"
        await shake(field)
    else:
        toggle_class(field, "border-red-500", False)
        toggle_class(field, "bg-red-50", False)
        toggle_class(field, "border-green-500", True)
        error_msg.style.display = "none"
    
    return is_valid
'''
        result = transpile(code)
        assert "border-red-500" in result
        assert "border-green-500" in result
        assert "shake" in result
    
    def test_multi_step_form(self):
        """Multi-step form with progress."""
        code = '''
from pynext.client import document
from pynext.client.style_utils import toggle_class, set_styles
from pynext.client.animation import slide_in, slide_out

async def show_step(step_num, direction="forward"):
    steps = document.querySelectorAll(".form-step")
    indicators = document.querySelectorAll(".step-indicator")
    
    # Hide all steps
    for i in range(steps.length):
        steps.item(i).style.display = "none"
        toggle_class(indicators.item(i), "bg-blue-500", i < step_num)
        toggle_class(indicators.item(i), "bg-gray-300", i >= step_num)
    
    # Show current step with animation
    current = steps.item(step_num)
    current.style.display = "block"
    
    if direction == "forward":
        await slide_in(current, direction="right")
    else:
        await slide_in(current, direction="left")
'''
        result = transpile(code)
        assert "form-step" in result
        assert "step-indicator" in result
        assert "slide_in" in result
    
    def test_file_upload_styling(self):
        """File upload with drag-drop styling."""
        code = '''
from pynext.client import document
from pynext.client.style_utils import toggle_class, set_styles

def setup_file_upload(zone_id):
    zone = document.getElementById(zone_id)
    
    def on_drag_enter(e):
        e.preventDefault()
        toggle_class(zone, "border-blue-500", True)
        toggle_class(zone, "bg-blue-50", True)
        toggle_class(zone, "border-dashed", True)
        set_styles(zone, {
            "borderWidth": "2px",
            "transform": "scale(1.02)",
        })
    
    def on_drag_leave(e):
        e.preventDefault()
        toggle_class(zone, "border-blue-500", False)
        toggle_class(zone, "bg-blue-50", False)
        set_styles(zone, {
            "borderWidth": "1px",
            "transform": "scale(1)",
        })
    
    def on_drop(e):
        e.preventDefault()
        on_drag_leave(e)
        toggle_class(zone, "border-green-500", True)
    
    zone.addEventListener("dragenter", on_drag_enter)
    zone.addEventListener("dragleave", on_drag_leave)
    zone.addEventListener("drop", on_drop)
'''
        result = transpile(code)
        assert "dragenter" in result
        assert "dragleave" in result
        assert "drop" in result
        assert "scale(1.02)" in result


# =============================================================================
# Toast/Notification Tests (3 tests)
# =============================================================================

class TestToastComponent:
    """Mini-app tests for toast notifications."""
    
    def test_toast_system(self):
        """Complete toast notification system."""
        code = '''
from pynext.client import document
from pynext.client.style_utils import classes, set_styles
from pynext.client.animation import slide_in, slide_out

toast_container = None

def init_toast_container():
    global toast_container
    toast_container = document.createElement("div")
    toast_container.id = "toast-container"
    set_styles(toast_container, {
        "position": "fixed",
        "bottom": "24px",
        "right": "24px",
        "display": "flex",
        "flexDirection": "column",
        "gap": "8px",
        "zIndex": "9999",
    })
    document.body.appendChild(toast_container)

async def show_toast(message, variant="info", duration=3000):
    toast = document.createElement("div")
    toast.className = classes(
        "px-4", "py-3", "rounded-lg", "shadow-lg",
        "flex", "items-center", "gap-3",
        {
            "bg-blue-500 text-white": variant == "info",
            "bg-green-500 text-white": variant == "success",
            "bg-red-500 text-white": variant == "error",
            "bg-yellow-500 text-black": variant == "warning",
        },
    )
    toast.textContent = message
    
    toast_container.appendChild(toast)
    await slide_in(toast, direction="right")
    
    # Auto dismiss (would need setTimeout)
'''
        result = transpile(code)
        assert "toast-container" in result
        assert "slide_in" in result
        assert "bg-green-500" in result
        assert "bg-red-500" in result
    
    def test_toast_with_actions(self):
        """Toast with action button."""
        code = '''
from pynext.client import document
from pynext.client.style_utils import set_styles

def create_action_toast(message, action_text, on_action):
    toast = document.createElement("div")
    set_styles(toast, {
        "display": "flex",
        "alignItems": "center",
        "justifyContent": "space-between",
        "gap": "16px",
        "padding": "12px 16px",
        "backgroundColor": "#1f2937",
        "color": "white",
        "borderRadius": "8px",
    })
    
    text = document.createElement("span")
    text.textContent = message
    
    action = document.createElement("button")
    action.textContent = action_text
    set_styles(action, {
        "color": "#60a5fa",
        "fontWeight": "600",
        "cursor": "pointer",
        "backgroundColor": "transparent",
        "border": "none",
    })
    action.addEventListener("click", on_action)
    
    toast.appendChild(text)
    toast.appendChild(action)
    
    return toast
'''
        result = transpile(code)
        assert "action" in result
        assert "#60a5fa" in result
        assert "justifyContent" in result
    
    def test_toast_progress(self):
        """Toast with progress indicator."""
        code = '''
from pynext.client import document
from pynext.client.style_utils import set_styles

def create_progress_toast(message, duration):
    toast = document.createElement("div")
    toast.style.position = "relative"
    toast.style.overflow = "hidden"
    
    progress = document.createElement("div")
    set_styles(progress, {
        "position": "absolute",
        "bottom": "0",
        "left": "0",
        "height": "3px",
        "backgroundColor": "rgba(255,255,255,0.5)",
        "width": "100%",
        "animation": f"shrink {duration}ms linear forwards",
    })
    
    toast.appendChild(progress)
    return toast
'''
        result = transpile(code)
        assert "progress" in result
        assert "shrink" in result
        assert "animation" in result


# =============================================================================
# Loading States Tests (2 tests)
# =============================================================================

class TestLoadingStates:
    """Mini-app tests for loading states."""
    
    def test_button_loading_state(self):
        """Button with loading spinner."""
        code = '''
from pynext.client import document
from pynext.client.style_utils import toggle_class, set_styles

def set_button_loading(btn, is_loading):
    spinner = btn.querySelector(".spinner")
    text = btn.querySelector(".text")
    
    if is_loading:
        btn.disabled = True
        toggle_class(btn, "opacity-75", True)
        toggle_class(btn, "cursor-wait", True)
        spinner.style.display = "inline-block"
        set_styles(spinner, {
            "animation": "spin 1s linear infinite",
        })
        text.textContent = "Loading..."
    else:
        btn.disabled = False
        toggle_class(btn, "opacity-75", False)
        toggle_class(btn, "cursor-wait", False)
        spinner.style.display = "none"
        text.textContent = "Submit"
'''
        result = transpile(code)
        assert "spinner" in result
        assert "cursor-wait" in result
        assert "spin 1s linear infinite" in result
    
    def test_skeleton_loader(self):
        """Skeleton content loader."""
        code = '''
from pynext.client import document
from pynext.client.style_utils import set_styles

def create_skeleton(width="100%", height="20px"):
    skeleton = document.createElement("div")
    set_styles(skeleton, {
        "width": width,
        "height": height,
        "borderRadius": "4px",
        "background": "linear-gradient(90deg, #e0e0e0 25%, #f0f0f0 50%, #e0e0e0 75%)",
        "backgroundSize": "200% 100%",
        "animation": "shimmer 1.5s ease-in-out infinite",
    })
    return skeleton

def create_card_skeleton():
    container = document.createElement("div")
    container.style.display = "flex"
    container.style.flexDirection = "column"
    container.style.gap = "12px"
    
    # Avatar
    container.appendChild(create_skeleton("48px", "48px"))
    # Title
    container.appendChild(create_skeleton("70%", "24px"))
    # Description lines
    container.appendChild(create_skeleton("100%", "16px"))
    container.appendChild(create_skeleton("90%", "16px"))
    
    return container
'''
        result = transpile(code)
        assert "skeleton" in result
        assert "shimmer" in result
        assert "linear-gradient" in result

