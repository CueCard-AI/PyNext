"""
Phase 34.4: Events Mini-Application Parity Tests

Integration tests verifying Python-to-JavaScript parity for event handling.
These tests ensure complete applications using events work correctly.

Total: 40 tests
"""

import pytest
from pynext.transpiler import transpile


# =============================================================================
# Click Handler Mini-App Tests (6 tests)
# =============================================================================

class TestClickHandlerMiniApp:
    """Integration tests for click handling mini-apps."""
    
    def test_button_click_counter(self):
        """Complete click counter should work."""
        code = '''
from pynext.client import document

count = 0

def on_click(event):
    global count
    count += 1
    event.target.textContent = f"Clicked {count} times"

button = document.getElementById("counter")
button.addEventListener("click", on_click)
'''
        result = transpile(code)
        assert 'addEventListener("click"' in result
        assert 'event.target.textContent' in result
        assert '__py.' not in result or 'global' in result.lower() or '__py.globals' in result
    
    def test_toggle_visibility(self):
        """Toggle visibility on click should work."""
        code = '''
from pynext.client import document

def toggle(event):
    content = document.getElementById("content")
    if content.style.display == "none":
        content.style.display = "block"
    else:
        content.style.display = "none"

button = document.getElementById("toggle-btn")
button.addEventListener("click", toggle)
'''
        result = transpile(code)
        assert 'addEventListener("click"' in result
        assert 'style.display' in result
    
    def test_multiple_buttons(self):
        """Handling multiple buttons should work."""
        code = '''
from pynext.client import document

def handle_nav(event):
    section = event.target.dataset.section
    show_section(section)

for btn in document.querySelectorAll(".nav-btn"):
    btn.addEventListener("click", handle_nav)
'''
        result = transpile(code)
        assert 'querySelectorAll' in result
        assert 'addEventListener' in result
        assert 'event.target.dataset.section' in result
    
    def test_ctrl_click_handler(self):
        """Ctrl+click handling should work."""
        code = '''
from pynext.client import document

def on_click(event):
    if event.ctrlKey or event.metaKey:
        open_in_new_tab(event.target.href)
    else:
        navigate(event.target.href)

link = document.querySelector("a.smart-link")
link.addEventListener("click", on_click)
'''
        result = transpile(code)
        assert 'event.ctrlKey' in result
        assert 'event.metaKey' in result
        assert 'event.target.href' in result
    
    def test_context_menu(self):
        """Context menu handling should work."""
        code = '''
from pynext.client import document

def on_context_menu(event):
    event.preventDefault()
    show_custom_menu(event.clientX, event.clientY)

el = document.getElementById("app")
el.addEventListener("contextmenu", on_context_menu)
'''
        result = transpile(code)
        assert 'addEventListener("contextmenu"' in result
        assert 'event.preventDefault()' in result
        assert 'event.clientX' in result
    
    def test_double_click(self):
        """Double click handling should work."""
        code = '''
from pynext.client import document

def on_dblclick(event):
    edit_item(event.target)

item = document.querySelector(".editable")
item.addEventListener("dblclick", on_dblclick)
'''
        result = transpile(code)
        assert 'addEventListener("dblclick"' in result


# =============================================================================
# Keyboard Shortcuts Mini-App Tests (6 tests)
# =============================================================================

class TestKeyboardShortcutsMiniApp:
    """Integration tests for keyboard shortcut mini-apps."""
    
    def test_save_shortcut(self):
        """Ctrl+S save shortcut should work."""
        code = '''
from pynext.client import document

def on_keydown(event):
    if (event.ctrlKey or event.metaKey) and event.key == "s":
        event.preventDefault()
        save_document()

document.addEventListener("keydown", on_keydown)
'''
        result = transpile(code)
        assert 'event.ctrlKey' in result
        assert 'event.metaKey' in result
        # Comparison may use __py.eq
        assert 'event.key' in result and '"s"' in result
        assert 'event.preventDefault()' in result
    
    def test_undo_redo(self):
        """Undo/redo shortcuts should work."""
        code = '''
from pynext.client import document

def on_keydown(event):
    if event.ctrlKey or event.metaKey:
        if event.key == "z":
            event.preventDefault()
            if event.shiftKey:
                redo()
            else:
                undo()

document.addEventListener("keydown", on_keydown)
'''
        result = transpile(code)
        assert 'event.shiftKey' in result
        # Comparison may use __py.eq
        assert 'event.key' in result and '"z"' in result
    
    def test_escape_close(self):
        """Escape key close modal should work."""
        code = '''
from pynext.client import document

def on_keydown(event):
    if event.key == "Escape":
        close_modal()
        event.stopPropagation()

document.addEventListener("keydown", on_keydown)
'''
        result = transpile(code)
        # Comparison may use __py.eq
        assert 'event.key' in result and '"Escape"' in result
        assert 'event.stopPropagation()' in result
    
    def test_arrow_navigation(self):
        """Arrow key navigation should work."""
        code = '''
from pynext.client import document

def on_keydown(event):
    if event.key == "ArrowUp":
        select_previous()
    elif event.key == "ArrowDown":
        select_next()
    elif event.key == "Enter":
        activate_selected()

list_el = document.getElementById("list")
list_el.addEventListener("keydown", on_keydown)
'''
        result = transpile(code)
        assert 'ArrowUp' in result
        assert 'ArrowDown' in result
        assert 'Enter' in result
    
    def test_game_controls(self):
        """WASD game controls should work."""
        code = '''
from pynext.client import document

def on_keydown(event):
    if event.code == "KeyW":
        move_forward()
    elif event.code == "KeyA":
        move_left()
    elif event.code == "KeyS":
        move_backward()
    elif event.code == "KeyD":
        move_right()

document.addEventListener("keydown", on_keydown)
'''
        result = transpile(code)
        # Comparison may use __py.eq
        assert 'event.code' in result and '"KeyW"' in result
        assert '"KeyA"' in result
    
    def test_search_focus(self):
        """Search focus shortcut should work."""
        code = '''
from pynext.client import document

def on_keydown(event):
    if event.key == "/" and not event.target.matches("input, textarea"):
        event.preventDefault()
        document.getElementById("search").focus()

document.addEventListener("keydown", on_keydown)
'''
        result = transpile(code)
        # Comparison may use __py.eq
        assert 'event.key' in result and '"/"' in result
        assert 'event.target.matches' in result


# =============================================================================
# Form Handling Mini-App Tests (6 tests)
# =============================================================================

class TestFormHandlingMiniApp:
    """Integration tests for form handling mini-apps."""
    
    def test_form_submit(self):
        """Form submission handling should work."""
        code = '''
from pynext.client import document

def on_submit(event):
    event.preventDefault()
    form = event.target
    data = FormData(form)
    submit_async(data)

form = document.getElementById("signup-form")
form.addEventListener("submit", on_submit)
'''
        result = transpile(code)
        assert 'event.preventDefault()' in result
        assert 'event.target' in result
        assert 'addEventListener("submit"' in result
    
    def test_input_validation(self):
        """Input validation on change should work."""
        code = '''
from pynext.client import document

def on_input(event):
    value = event.target.value
    if len(value) < 3:
        show_error("Too short")
    else:
        clear_error()

input_el = document.getElementById("username")
input_el.addEventListener("input", on_input)
'''
        result = transpile(code)
        assert 'event.target.value' in result
        assert 'addEventListener("input"' in result
    
    def test_focus_blur_styling(self):
        """Focus/blur styling should work."""
        code = '''
from pynext.client import document

def on_focus(event):
    event.target.classList.add("focused")
    event.target.parentElement.classList.add("field-focused")

def on_blur(event):
    event.target.classList.remove("focused")
    event.target.parentElement.classList.remove("field-focused")
    validate(event.target)

for field in document.querySelectorAll("input"):
    field.addEventListener("focus", on_focus)
    field.addEventListener("blur", on_blur)
'''
        result = transpile(code)
        assert 'classList.add("focused")' in result
        assert 'classList.remove("focused")' in result
    
    def test_checkbox_toggle(self):
        """Checkbox toggle should work."""
        code = '''
from pynext.client import document

def on_change(event):
    if event.target.checked:
        enable_feature()
    else:
        disable_feature()

checkbox = document.getElementById("feature-toggle")
checkbox.addEventListener("change", on_change)
'''
        result = transpile(code)
        assert 'event.target.checked' in result
    
    def test_select_change(self):
        """Select change should work."""
        code = '''
from pynext.client import document

def on_change(event):
    selected = event.target.value
    update_display(selected)

select = document.getElementById("theme-select")
select.addEventListener("change", on_change)
'''
        result = transpile(code)
        assert 'event.target.value' in result
        assert 'addEventListener("change"' in result
    
    def test_enter_submit(self):
        """Enter key form submit should work."""
        code = '''
from pynext.client import document

def on_keydown(event):
    if event.key == "Enter" and not event.shiftKey:
        event.preventDefault()
        submit_form()

textarea = document.getElementById("message")
textarea.addEventListener("keydown", on_keydown)
'''
        result = transpile(code)
        # Comparison may use __py.eq
        assert 'event.key' in result and '"Enter"' in result
        assert 'event.shiftKey' in result


# =============================================================================
# Drag and Drop Mini-App Tests (6 tests)
# =============================================================================

class TestDragDropMiniApp:
    """Integration tests for drag-drop mini-apps."""
    
    def test_sortable_list(self):
        """Sortable list should work."""
        code = '''
from pynext.client import document

def on_drag_start(event):
    event.dataTransfer.setData("text/plain", event.target.id)
    event.dataTransfer.effectAllowed = "move"

def on_drag_over(event):
    event.preventDefault()

def on_drop(event):
    event.preventDefault()
    id = event.dataTransfer.getData("text/plain")
    item = document.getElementById(id)
    event.target.appendChild(item)

for item in document.querySelectorAll(".sortable-item"):
    item.addEventListener("dragstart", on_drag_start)
    item.addEventListener("dragover", on_drag_over)
    item.addEventListener("drop", on_drop)
'''
        result = transpile(code)
        assert 'setData' in result
        assert 'getData' in result
        assert 'effectAllowed' in result
    
    def test_file_drop_zone(self):
        """File drop zone should work."""
        code = '''
from pynext.client import document

def on_drag_over(event):
    event.preventDefault()
    event.dataTransfer.dropEffect = "copy"
    dropzone.classList.add("drag-over")

def on_drag_leave(event):
    dropzone.classList.remove("drag-over")

def on_drop(event):
    event.preventDefault()
    dropzone.classList.remove("drag-over")
    
    for file in event.dataTransfer.files:
        upload_file(file)

dropzone = document.getElementById("dropzone")
dropzone.addEventListener("dragover", on_drag_over)
dropzone.addEventListener("dragleave", on_drag_leave)
dropzone.addEventListener("drop", on_drop)
'''
        result = transpile(code)
        assert 'event.dataTransfer.files' in result
        assert 'dropEffect' in result
    
    def test_kanban_board(self):
        """Kanban board should work."""
        code = '''
from pynext.client import document

dragged_card = None

def on_drag_start(event):
    global dragged_card
    dragged_card = event.target
    event.dataTransfer.effectAllowed = "move"

def on_drop(event):
    event.preventDefault()
    column = event.target.closest(".column")
    if column and dragged_card:
        column.querySelector(".cards").appendChild(dragged_card)

for card in document.querySelectorAll(".card"):
    card.draggable = True
    card.addEventListener("dragstart", on_drag_start)

for column in document.querySelectorAll(".column"):
    column.addEventListener("drop", on_drop)
    column.addEventListener("dragover", lambda e: e.preventDefault())
'''
        result = transpile(code)
        assert 'event.target.closest' in result
    
    def test_drag_image_custom(self):
        """Custom drag image should work."""
        code = '''
from pynext.client import document

def on_drag_start(event):
    ghost = document.createElement("div")
    ghost.textContent = "Dragging..."
    ghost.className = "drag-ghost"
    document.body.appendChild(ghost)
    event.dataTransfer.setDragImage(ghost, 0, 0)
'''
        result = transpile(code)
        assert 'setDragImage' in result
    
    def test_drag_data_html(self):
        """HTML drag data should work."""
        code = '''
def on_drag_start(event):
    event.dataTransfer.setData("text/plain", text)
    event.dataTransfer.setData("text/html", html)
'''
        result = transpile(code)
        assert 'text/plain' in result
        assert 'text/html' in result
    
    def test_drop_effect_feedback(self):
        """Drop effect feedback should work."""
        code = '''
def on_drag_over(event):
    event.preventDefault()
    if event.ctrlKey:
        event.dataTransfer.dropEffect = "copy"
    else:
        event.dataTransfer.dropEffect = "move"
'''
        result = transpile(code)
        assert 'event.ctrlKey' in result
        assert 'dropEffect' in result


# =============================================================================
# Touch Gesture Mini-App Tests (6 tests)
# =============================================================================

class TestTouchGestureMiniApp:
    """Integration tests for touch gesture mini-apps."""
    
    def test_swipe_detection(self):
        """Swipe detection should work."""
        code = '''
from pynext.client import document

start_x = 0
start_y = 0

def on_touch_start(event):
    global start_x, start_y
    touch = event.touches[0]
    start_x = touch.clientX
    start_y = touch.clientY

def on_touch_end(event):
    touch = event.changedTouches[0]
    dx = touch.clientX - start_x
    dy = touch.clientY - start_y
    
    if abs(dx) > 50:
        if dx > 0:
            swipe_right()
        else:
            swipe_left()

el = document.getElementById("swipeable")
el.addEventListener("touchstart", on_touch_start)
el.addEventListener("touchend", on_touch_end)
'''
        result = transpile(code)
        assert 'event.touches[0]' in result or 'event.touches' in result
        assert 'event.changedTouches' in result
    
    def test_pinch_zoom(self):
        """Pinch to zoom should work."""
        code = '''
def on_touch_move(event):
    if event.touches.length == 2:
        t1 = event.touches[0]
        t2 = event.touches[1]
        distance = calc_distance(t1.clientX, t1.clientY, t2.clientX, t2.clientY)
        scale = distance / initial_distance
        apply_zoom(scale)
'''
        result = transpile(code)
        # Comparison may use __py.eq
        assert 'event.touches.length' in result and '2' in result
        assert 't1.clientX' in result
    
    def test_touch_drag(self):
        """Touch drag should work."""
        code = '''
def on_touch_move(event):
    if event.touches.length == 1:
        event.preventDefault()
        touch = event.touches[0]
        move_element(touch.pageX, touch.pageY)
'''
        result = transpile(code)
        assert 'event.preventDefault()' in result
        assert 'touch.pageX' in result
    
    def test_touch_hold(self):
        """Touch hold detection should work."""
        code = '''
from pynext.client import document

hold_timer = None

def on_touch_start(event):
    global hold_timer
    hold_timer = setTimeout(lambda: show_context_menu(event.touches[0]), 500)

def on_touch_end(event):
    global hold_timer
    if hold_timer:
        clearTimeout(hold_timer)
        hold_timer = None
'''
        result = transpile(code)
        assert 'event.touches[0]' in result or 'event.touches' in result
    
    def test_multi_touch_tracking(self):
        """Multi-touch tracking should work."""
        code = '''
touches_map = {}

def on_touch_start(event):
    for touch in event.changedTouches:
        touches_map[touch.identifier] = {
            "x": touch.clientX,
            "y": touch.clientY
        }

def on_touch_move(event):
    for touch in event.changedTouches:
        if touch.identifier in touches_map:
            update_touch(touch.identifier, touch.clientX, touch.clientY)
'''
        result = transpile(code)
        assert 'touch.identifier' in result
        assert 'event.changedTouches' in result
    
    def test_prevent_scroll(self):
        """Preventing scroll on touch should work."""
        code = '''
def on_touch_move(event):
    event.preventDefault()

el.addEventListener("touchmove", on_touch_move, {"passive": False})
'''
        result = transpile(code)
        assert 'event.preventDefault()' in result
        assert 'passive' in result


# =============================================================================
# Custom Events Mini-App Tests (5 tests)
# =============================================================================

class TestCustomEventsMiniApp:
    """Integration tests for custom event mini-apps."""
    
    def test_component_communication(self):
        """Component communication should work."""
        code = '''
from pynext.client import document

def notify_parent(data):
    event = CustomEvent("child-updated", {
        "bubbles": True,
        "detail": data
    })
    el.dispatchEvent(event)

def on_child_updated(event):
    update_parent(event.detail)

parent.addEventListener("child-updated", on_child_updated)
'''
        result = transpile(code)
        assert 'CustomEvent' in result
        assert 'dispatchEvent' in result
        assert 'event.detail' in result
    
    def test_app_lifecycle_events(self):
        """App lifecycle events should work."""
        code = '''
from pynext.client import document

def emit_ready():
    document.dispatchEvent(CustomEvent("app-ready"))

def emit_data_loaded(data):
    document.dispatchEvent(CustomEvent("data-loaded", {"detail": data}))

document.addEventListener("app-ready", on_app_ready)
document.addEventListener("data-loaded", on_data_loaded)
'''
        result = transpile(code)
        assert 'document.dispatchEvent' in result
        assert 'document.addEventListener' in result
    
    def test_event_bus_pattern(self):
        """Event bus pattern should work."""
        code = '''
from pynext.client import document

class EventBus:
    def emit(self, name, data):
        event = CustomEvent(name, {"detail": data, "bubbles": True})
        document.dispatchEvent(event)
    
    def on(self, name, handler):
        document.addEventListener(name, handler)
    
    def off(self, name, handler):
        document.removeEventListener(name, handler)
'''
        result = transpile(code)
        assert 'CustomEvent' in result
        assert 'addEventListener' in result
        assert 'removeEventListener' in result
    
    def test_state_change_notification(self):
        """State change notification should work."""
        code = '''
from pynext.client import document

def set_state(key, value):
    state[key] = value
    event = CustomEvent("state-change", {
        "detail": {"key": key, "value": value}
    })
    document.dispatchEvent(event)

def on_state_change(event):
    key = event.detail["key"]
    value = event.detail["value"]
    update_ui(key, value)
'''
        result = transpile(code)
        assert 'event.detail' in result
    
    def test_cross_component_sync(self):
        """Cross-component sync should work."""
        code = '''
from pynext.client import document

def sync_selection(selected_id):
    event = CustomEvent("selection-changed", {
        "bubbles": True,
        "composed": True,
        "detail": {"id": selected_id}
    })
    document.dispatchEvent(event)
'''
        result = transpile(code)
        assert 'composed' in result
        assert 'bubbles' in result


# =============================================================================
# Event Delegation Mini-App Tests (5 tests)
# =============================================================================

class TestEventDelegationMiniApp:
    """Integration tests for event delegation mini-apps."""
    
    def test_list_item_delegation(self):
        """List item click delegation should work."""
        code = '''
from pynext.client import document

def on_list_click(event):
    item = event.target.closest("li")
    if item:
        select_item(item.dataset.id)

list_el = document.getElementById("list")
list_el.addEventListener("click", on_list_click)
'''
        result = transpile(code)
        assert 'event.target.closest' in result
        assert 'item.dataset.id' in result
    
    def test_table_row_delegation(self):
        """Table row click delegation should work."""
        code = '''
from pynext.client import document

def on_table_click(event):
    row = event.target.closest("tr")
    if row and row.dataset.id:
        show_details(row.dataset.id)

table = document.getElementById("data-table")
table.addEventListener("click", on_table_click)
'''
        result = transpile(code)
        assert 'closest("tr")' in result
    
    def test_button_action_delegation(self):
        """Button action delegation should work."""
        code = '''
from pynext.client import document

def on_click(event):
    button = event.target.closest("button[data-action]")
    if button:
        action = button.dataset.action
        if action == "edit":
            edit_item(button.dataset.id)
        elif action == "delete":
            delete_item(button.dataset.id)

container = document.getElementById("items")
container.addEventListener("click", on_click)
'''
        result = transpile(code)
        assert 'button.dataset.action' in result
    
    def test_stop_at_boundary(self):
        """Stopping at delegation boundary should work."""
        code = '''
def on_click(event):
    target = event.target
    while target and target != event.currentTarget:
        if target.matches(".interactive"):
            handle_interactive(target)
            return
        target = target.parentElement
'''
        result = transpile(code)
        assert 'event.target' in result
        assert 'event.currentTarget' in result
        assert 'target.matches' in result
    
    def test_dynamic_content(self):
        """Delegation for dynamic content should work."""
        code = '''
from pynext.client import document

# Single listener handles all items, even dynamically added
def on_container_click(event):
    item = event.target.closest(".dynamic-item")
    if item:
        handle_item_click(item)

container = document.getElementById("dynamic-container")
container.addEventListener("click", on_container_click)
'''
        result = transpile(code)
        assert 'closest(".dynamic-item")' in result

