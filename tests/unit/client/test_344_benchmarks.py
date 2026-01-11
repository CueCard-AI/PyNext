"""
Phase 34.4: Event Transpilation Benchmarks

Performance tests for event-related transpilation covering:
- Transpilation speed for event handlers
- Output size verification
- No runtime helper overhead

Total: 10 tests
"""

import pytest
import time
from pynext.transpiler import transpile


class TestTranspilationSpeed:
    """Tests for transpilation performance."""
    
    def test_simple_handler_speed(self):
        """Simple event handler should transpile fast."""
        code = '''
def on_click(event):
    event.preventDefault()
    x = event.clientX
    y = event.clientY
'''
        start = time.perf_counter()
        for _ in range(100):
            transpile(code)
        elapsed = time.perf_counter() - start
        
        # 100 transpilations should complete in under 2 seconds
        assert elapsed < 2.0, f"Took {elapsed}s for 100 transpilations"
    
    def test_complex_handler_speed(self):
        """Complex event handler should still transpile fast."""
        code = '''
def handle_keyboard(event):
    if event.ctrlKey or event.metaKey:
        if event.key == "s":
            event.preventDefault()
            save()
        elif event.key == "z":
            event.preventDefault()
            if event.shiftKey:
                redo()
            else:
                undo()
        elif event.key == "c":
            copy()
        elif event.key == "v":
            paste()
'''
        start = time.perf_counter()
        for _ in range(50):
            transpile(code)
        elapsed = time.perf_counter() - start
        
        # 50 complex transpilations should complete in under 2 seconds
        assert elapsed < 2.0, f"Took {elapsed}s for 50 transpilations"


class TestOutputSize:
    """Tests for minimal output size."""
    
    def test_no_runtime_helpers(self):
        """Event code should not include __py.* helpers."""
        code = '''
def on_click(event):
    x = event.clientX
    y = event.clientY
    event.preventDefault()
    event.stopPropagation()
'''
        result = transpile(code)
        
        # Event property access should not use runtime helpers
        assert 'event.clientX' in result
        assert 'event.clientY' in result
        assert '__py.' not in result
    
    def test_minimal_output_overhead(self):
        """Output should be close to handwritten JS."""
        code = '''
def handle(event):
    event.preventDefault()
'''
        result = transpile(code)
        
        # Output should be simple - just function and call
        lines = [l for l in result.strip().split('\n') if l.strip()]
        # Should be around 3-4 lines (function def, body, close)
        assert len(lines) < 10, f"Output too verbose: {len(lines)} lines"


class TestPassthroughVerification:
    """Tests verifying passthrough behavior."""
    
    def test_all_mouse_properties_passthrough(self):
        """All mouse properties should pass through."""
        properties = [
            'clientX', 'clientY', 'pageX', 'pageY',
            'screenX', 'screenY', 'offsetX', 'offsetY',
            'button', 'buttons', 'altKey', 'ctrlKey',
            'shiftKey', 'metaKey', 'relatedTarget'
        ]
        for prop in properties:
            code = f'''
def handle(event):
    x = event.{prop}
'''
            result = transpile(code)
            assert f'event.{prop}' in result, f"Property {prop} not passed through"
            assert '__py.' not in result, f"Property {prop} uses runtime helper"
    
    def test_all_keyboard_properties_passthrough(self):
        """All keyboard properties should pass through."""
        properties = [
            'key', 'code', 'repeat', 'isComposing',
            'location', 'altKey', 'ctrlKey', 'shiftKey', 'metaKey'
        ]
        for prop in properties:
            code = f'''
def handle(event):
    x = event.{prop}
'''
            result = transpile(code)
            assert f'event.{prop}' in result, f"Property {prop} not passed through"
    
    def test_all_event_methods_passthrough(self):
        """All event methods should pass through."""
        methods = [
            'preventDefault()',
            'stopPropagation()',
            'stopImmediatePropagation()',
            'composedPath()',
        ]
        for method in methods:
            code = f'''
def handle(event):
    event.{method}
'''
            result = transpile(code)
            assert f'event.{method}' in result, f"Method {method} not passed through"


class TestRealWorldPatterns:
    """Tests for real-world event patterns."""
    
    def test_form_submit_pattern(self):
        """Real form submit pattern should work efficiently."""
        code = '''
def on_submit(event):
    event.preventDefault()
    form = event.target
    data = FormData(form)
    submit(data)
'''
        result = transpile(code)
        assert 'event.preventDefault()' in result
        assert 'event.target' in result
        assert '__py.' not in result
    
    def test_drag_drop_pattern(self):
        """Real drag-drop pattern should work efficiently."""
        code = '''
def on_drag_start(event):
    event.dataTransfer.setData("text/plain", item.id)
    event.dataTransfer.effectAllowed = "move"

def on_drop(event):
    event.preventDefault()
    id = event.dataTransfer.getData("text/plain")
    move(id, event.target)
'''
        result = transpile(code)
        assert 'event.dataTransfer.setData' in result
        assert 'event.dataTransfer.getData' in result
        assert '__py.' not in result
    
    def test_keyboard_shortcuts_pattern(self):
        """Real keyboard shortcuts pattern should work efficiently."""
        code = '''
def on_keydown(event):
    if event.ctrlKey and event.key == "s":
        event.preventDefault()
        save()
    elif event.ctrlKey and event.key == "z":
        event.preventDefault()
        undo()
'''
        result = transpile(code)
        assert 'event.ctrlKey' in result
        assert 'event.key' in result
        assert 'event.preventDefault()' in result
        # Truthiness/comparison may use __py helpers

