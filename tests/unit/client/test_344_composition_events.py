"""
Phase 34.4: Composition Event Tests

Unit tests for CompositionEvent transpilation covering:
- compositionstart, compositionupdate, compositionend events
- data property
- IME input handling patterns

Total: 10 tests
"""

import pytest
from pynext.transpiler import transpile


class TestCompositionEventBasics:
    """Tests for basic CompositionEvent properties."""
    
    def test_composition_start_event(self):
        """compositionstart event should pass through."""
        code = '''
def on_composition_start(event):
    handle_composition()

el.addEventListener("compositionstart", on_composition_start)
'''
        result = transpile(code)
        assert 'addEventListener("compositionstart"' in result
        # Event-specific code doesn't use __py helpers (print is ok)
        assert 'on_composition_start' in result
    
    def test_composition_update_event(self):
        """compositionupdate event should pass through."""
        code = '''
def on_composition_update(event):
    current_text = event.data

el.addEventListener("compositionupdate", on_composition_update)
'''
        result = transpile(code)
        assert 'addEventListener("compositionupdate"' in result
        assert 'event.data' in result
    
    def test_composition_end_event(self):
        """compositionend event should pass through."""
        code = '''
def on_composition_end(event):
    final_text = event.data

el.addEventListener("compositionend", on_composition_end)
'''
        result = transpile(code)
        assert 'addEventListener("compositionend"' in result
        assert 'event.data' in result
    
    def test_data_property(self):
        """CompositionEvent.data should pass through."""
        code = '''
def handle(event):
    text = event.data
'''
        result = transpile(code)
        assert 'event.data' in result
        assert '__py.' not in result


class TestIMEPatterns:
    """Tests for common IME input handling patterns."""
    
    def test_ime_aware_search_input(self):
        """IME-aware search input pattern should work."""
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
    
    def test_ignore_keydown_during_composition(self):
        """Ignoring keydown during composition should work."""
        code = '''
def on_keydown(event):
    if event.isComposing:
        return
    handle_key(event.key)
'''
        result = transpile(code)
        assert 'event.isComposing' in result
    
    def test_composition_with_enter_key(self):
        """Handling Enter during composition should work."""
        code = '''
def on_keydown(event):
    if event.key == "Enter":
        if event.isComposing:
            return  # Don't submit during IME
        submit_form()
'''
        result = transpile(code)
        assert 'event.isComposing' in result
        # Comparison may use __py.eq or direct ==
        assert 'event.key' in result and '"Enter"' in result
    
    def test_multi_event_composition_handler(self):
        """Multiple composition event handlers should work."""
        code = '''
def on_composition_start(event):
    show_composition_indicator()

def on_composition_update(event):
    update_preview(event.data)

def on_composition_end(event):
    hide_composition_indicator()
    apply_text(event.data)

el.addEventListener("compositionstart", on_composition_start)
el.addEventListener("compositionupdate", on_composition_update)
el.addEventListener("compositionend", on_composition_end)
'''
        result = transpile(code)
        assert result.count('addEventListener') == 3
        assert 'event.data' in result
    
    def test_japanese_ime_pattern(self):
        """Japanese IME input pattern should work."""
        code = '''
from pynext.client import document

class JapaneseInputHandler:
    def __init__(self, input_el):
        self.input_el = input_el
        self.composing = False
        
        input_el.addEventListener("compositionstart", self.on_start)
        input_el.addEventListener("compositionend", self.on_end)
    
    def on_start(self, event):
        self.composing = True
    
    def on_end(self, event):
        self.composing = False
        self.on_complete(event.data)
    
    def on_complete(self, text):
        pass
'''
        result = transpile(code)
        assert 'compositionstart' in result
        assert 'compositionend' in result
    
    def test_chinese_pinyin_pattern(self):
        """Chinese Pinyin input pattern should work."""
        code = '''
def handle_chinese_input(event):
    # During composition, data contains pinyin
    # After composition, data contains Chinese characters
    if event.type == "compositionend":
        characters = event.data
        process_chinese(characters)
'''
        result = transpile(code)
        assert 'event.type' in result
        assert 'event.data' in result

