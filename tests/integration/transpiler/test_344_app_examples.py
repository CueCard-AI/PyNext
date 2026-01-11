"""
Phase 34.4: Mini-Application Example Tests

Integration tests verifying the cookbook examples transpile correctly.
These tests ensure all 8 mini-application patterns work as expected.

Total: 16 tests (2 per example)
"""

import pytest
from pynext.transpiler import transpile


class TestInfiniteScrollExample:
    """Tests for the infinite scroll example."""
    
    def test_infinite_scroll_transpiles(self):
        """Infinite scroll example should transpile correctly."""
        code = '''
from pynext.client import document, window

loading = False
page = 1

def on_scroll(event):
    global loading, page
    
    scroll_top = document.documentElement.scrollTop
    scroll_height = document.documentElement.scrollHeight
    client_height = document.documentElement.clientHeight
    
    if scroll_top + client_height >= scroll_height - 100:
        if not loading:
            loading = True
            page += 1

window.addEventListener("scroll", on_scroll, {"passive": True})
'''
        result = transpile(code)
        assert 'document.documentElement.scrollTop' in result
        assert 'document.documentElement.scrollHeight' in result
        assert 'addEventListener("scroll"' in result
        assert 'passive' in result
    
    def test_scroll_position_access(self):
        """Scroll position access should work."""
        code = '''
from pynext.client import document

scroll_top = document.documentElement.scrollTop
scroll_left = document.documentElement.scrollLeft
'''
        result = transpile(code)
        assert 'scrollTop' in result
        assert 'scrollLeft' in result


class TestKeyboardShortcutsExample:
    """Tests for the keyboard shortcuts example."""
    
    def test_keyboard_shortcuts_transpiles(self):
        """Keyboard shortcuts manager should transpile correctly."""
        code = '''
from pynext.client import document

shortcuts = {}

def on_keydown(event):
    parts = []
    if event.ctrlKey:
        parts.append("ctrl")
    if event.metaKey:
        parts.append("meta")
    if event.shiftKey:
        parts.append("shift")
    parts.append(event.key.lower())
    
    combo = "+".join(parts)
    
    if combo in shortcuts:
        event.preventDefault()
        shortcuts[combo]()

document.addEventListener("keydown", on_keydown)
'''
        result = transpile(code)
        assert 'event.ctrlKey' in result
        assert 'event.metaKey' in result
        assert 'event.shiftKey' in result
        assert 'event.key' in result
        assert 'event.preventDefault()' in result
    
    def test_skip_inputs_pattern(self):
        """Skipping inputs pattern should work."""
        code = '''
def on_keydown(event):
    if event.target.tagName in ["INPUT", "TEXTAREA"]:
        return
    handle_shortcut(event)
'''
        result = transpile(code)
        assert 'event.target.tagName' in result


class TestDragDropExample:
    """Tests for the drag-drop file upload example."""
    
    def test_drag_drop_transpiles(self):
        """Drag-drop file upload should transpile correctly."""
        code = '''
from pynext.client import document

def create_dropzone(element_id, on_files):
    dropzone = document.getElementById(element_id)
    
    def on_drag_enter(event):
        event.preventDefault()
        dropzone.classList.add("drag-over")
    
    def on_drag_over(event):
        event.preventDefault()
        event.dataTransfer.dropEffect = "copy"
    
    def on_drop(event):
        event.preventDefault()
        dropzone.classList.remove("drag-over")
        
        for file in event.dataTransfer.files:
            on_files(file)
    
    dropzone.addEventListener("dragenter", on_drag_enter)
    dropzone.addEventListener("dragover", on_drag_over)
    dropzone.addEventListener("drop", on_drop)
'''
        result = transpile(code)
        assert 'event.dataTransfer.dropEffect' in result
        assert 'event.dataTransfer.files' in result
        assert 'classList.add("drag-over")' in result
    
    def test_drop_effect_assignment(self):
        """Drop effect assignment should work."""
        code = '''
def on_drag_over(event):
    event.dataTransfer.dropEffect = "move"
'''
        result = transpile(code)
        assert 'dropEffect' in result


class TestTouchGesturesExample:
    """Tests for the touch gesture recognizer example."""
    
    def test_touch_gestures_transpiles(self):
        """Touch gesture recognizer should transpile correctly."""
        code = '''
class GestureRecognizer:
    def __init__(self, element):
        self.element = element
        self.start_x = 0
        self.start_y = 0
        self.start_time = 0
        
        element.addEventListener("touchstart", self.on_touch_start)
        element.addEventListener("touchend", self.on_touch_end)
        element.addEventListener("touchmove", self.on_touch_move, {"passive": False})
    
    def on_touch_start(self, event):
        if event.touches.length == 1:
            touch = event.touches[0]
            self.start_x = touch.clientX
            self.start_y = touch.clientY
            self.start_time = event.timeStamp
'''
        result = transpile(code)
        assert 'event.touches.length' in result
        assert 'touch.clientX' in result
        assert 'event.timeStamp' in result
    
    def test_changed_touches_access(self):
        """changedTouches access should work."""
        code = '''
def on_touch_end(event):
    touch = event.changedTouches[0]
    end_x = touch.clientX
'''
        result = transpile(code)
        assert 'event.changedTouches' in result


class TestCrossTabSyncExample:
    """Tests for the cross-tab state sync example."""
    
    def test_cross_tab_sync_transpiles(self):
        """Cross-tab sync should transpile correctly."""
        code = '''
from pynext.client import window

def sync_state_across_tabs(key, on_change):
    def on_storage(event):
        if event.key == key:
            if event.newValue:
                data = JSON.parse(event.newValue)
                on_change(data)
    
    window.addEventListener("storage", on_storage)
'''
        result = transpile(code)
        # Comparison may use __py.eq or direct ==
        assert 'event.key' in result and 'key' in result
        assert 'event.newValue' in result
        assert 'addEventListener("storage"' in result
    
    def test_storage_event_properties(self):
        """All storage event properties should work."""
        code = '''
def on_storage(event):
    key = event.key
    old = event.oldValue
    new = event.newValue
    url = event.url
    area = event.storageArea
'''
        result = transpile(code)
        assert 'event.oldValue' in result
        assert 'event.newValue' in result


class TestMediaPlayerExample:
    """Tests for the media player example."""
    
    def test_media_player_transpiles(self):
        """Media player should transpile correctly."""
        code = '''
from pynext.client import document

def create_media_player(video_id):
    video = document.getElementById(video_id)
    
    def on_timeupdate(event):
        current = video.currentTime
        duration = video.duration
        percent = (current / duration) * 100
    
    def on_play(event):
        play_btn.classList.add("playing")
    
    def on_pause(event):
        play_btn.classList.remove("playing")
    
    video.addEventListener("timeupdate", on_timeupdate)
    video.addEventListener("play", on_play)
    video.addEventListener("pause", on_pause)
'''
        result = transpile(code)
        assert 'video.currentTime' in result
        assert 'video.duration' in result
        assert 'addEventListener("timeupdate"' in result
    
    def test_media_properties(self):
        """Media element properties should work."""
        code = '''
def check_media(video):
    paused = video.paused
    volume = video.volume
    muted = video.muted
'''
        result = transpile(code)
        assert 'video.paused' in result
        assert 'video.volume' in result


class TestAbortControllerExample:
    """Tests for the AbortController cleanup example."""
    
    def test_abort_controller_transpiles(self):
        """AbortController cleanup should transpile correctly."""
        code = '''
from pynext.client import document, window

class Component:
    def __init__(self, element):
        self.element = element
        self.controller = AbortController()
    
    def mount(self):
        signal = self.controller.signal
        self.element.addEventListener("click", self.on_click, {"signal": signal})
        document.addEventListener("keydown", self.on_keydown, {"signal": signal})
        window.addEventListener("resize", self.on_resize, {"signal": signal})
    
    def unmount(self):
        self.controller.abort()
'''
        result = transpile(code)
        assert 'AbortController()' in result
        assert 'controller.signal' in result
        assert 'abort()' in result
    
    def test_signal_usage(self):
        """Signal usage in listener options should work."""
        code = '''
controller = AbortController()
el.addEventListener("click", handler, {"signal": controller.signal, "once": True})
'''
        result = transpile(code)
        assert 'signal' in result
        assert 'once' in result


class TestIMESearchExample:
    """Tests for the IME-aware search input example."""
    
    def test_ime_search_transpiles(self):
        """IME-aware search should transpile correctly."""
        code = '''
from pynext.client import document

def create_search_input(input_id, on_search):
    input_el = document.getElementById(input_id)
    is_composing = False
    
    def on_composition_start(event):
        nonlocal is_composing
        is_composing = True
    
    def on_composition_end(event):
        nonlocal is_composing
        is_composing = False
        on_search(input_el.value)
    
    def on_input(event):
        if not is_composing:
            on_search(input_el.value)
    
    input_el.addEventListener("compositionstart", on_composition_start)
    input_el.addEventListener("compositionend", on_composition_end)
    input_el.addEventListener("input", on_input)
'''
        result = transpile(code)
        assert 'compositionstart' in result
        assert 'compositionend' in result
        assert 'is_composing' in result or 'isComposing' in result
    
    def test_is_composing_check(self):
        """isComposing check should work."""
        code = '''
def on_keydown(event):
    if event.key == "Enter" and not event.isComposing:
        submit()
'''
        result = transpile(code)
        assert 'event.isComposing' in result

