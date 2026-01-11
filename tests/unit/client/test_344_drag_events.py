"""
Phase 34.4: Drag Event Tests

Unit tests for DragEvent transpilation covering:
- DataTransfer properties (files, items, types)
- DataTransfer methods (setData, getData, clearData, setDragImage)
- effectAllowed and dropEffect
- Complete drag-drop patterns

Total: 25 tests
"""

import pytest
from pynext.transpiler import transpile


class TestDataTransferProperties:
    """Tests for DataTransfer property access."""
    
    def test_data_transfer_passthrough(self):
        """dataTransfer should pass through unchanged."""
        code = '''
def handle(event):
    dt = event.dataTransfer
'''
        result = transpile(code)
        assert 'event.dataTransfer' in result
        assert '__py.' not in result
    
    def test_files_property(self):
        """dataTransfer.files should pass through."""
        code = '''
def handle(event):
    files = event.dataTransfer.files
'''
        result = transpile(code)
        assert 'event.dataTransfer.files' in result
    
    def test_items_property(self):
        """dataTransfer.items should pass through."""
        code = '''
def handle(event):
    items = event.dataTransfer.items
'''
        result = transpile(code)
        assert 'event.dataTransfer.items' in result
    
    def test_types_property(self):
        """dataTransfer.types should pass through."""
        code = '''
def handle(event):
    types = event.dataTransfer.types
'''
        result = transpile(code)
        assert 'event.dataTransfer.types' in result


class TestDataTransferEffects:
    """Tests for drag effect properties."""
    
    def test_drop_effect_get(self):
        """dropEffect should pass through."""
        code = '''
def handle(event):
    effect = event.dataTransfer.dropEffect
'''
        result = transpile(code)
        assert 'event.dataTransfer.dropEffect' in result
    
    def test_drop_effect_set(self):
        """Setting dropEffect should pass through."""
        code = '''
def handle(event):
    event.dataTransfer.dropEffect = "move"
'''
        result = transpile(code)
        assert 'event.dataTransfer.dropEffect' in result
        assert '"move"' in result
    
    def test_effect_allowed_get(self):
        """effectAllowed should pass through."""
        code = '''
def handle(event):
    allowed = event.dataTransfer.effectAllowed
'''
        result = transpile(code)
        assert 'event.dataTransfer.effectAllowed' in result
    
    def test_effect_allowed_set(self):
        """Setting effectAllowed should pass through."""
        code = '''
def handle(event):
    event.dataTransfer.effectAllowed = "copyMove"
'''
        result = transpile(code)
        assert 'event.dataTransfer.effectAllowed' in result
        assert '"copyMove"' in result


class TestDataTransferMethods:
    """Tests for DataTransfer methods."""
    
    def test_set_data(self):
        """setData should pass through."""
        code = '''
def handle(event):
    event.dataTransfer.setData("text/plain", "hello")
'''
        result = transpile(code)
        assert 'setData("text/plain", "hello")' in result
        assert '__py.' not in result
    
    def test_get_data(self):
        """getData should pass through."""
        code = '''
def handle(event):
    data = event.dataTransfer.getData("text/plain")
'''
        result = transpile(code)
        assert 'getData("text/plain")' in result
    
    def test_clear_data(self):
        """clearData should pass through."""
        code = '''
def handle(event):
    event.dataTransfer.clearData()
'''
        result = transpile(code)
        assert 'clearData()' in result
    
    def test_clear_data_specific(self):
        """clearData with format should pass through."""
        code = '''
def handle(event):
    event.dataTransfer.clearData("text/plain")
'''
        result = transpile(code)
        assert 'clearData("text/plain")' in result
    
    def test_set_drag_image(self):
        """setDragImage should pass through."""
        code = '''
def handle(event):
    img = document.createElement("img")
    event.dataTransfer.setDragImage(img, 10, 10)
'''
        result = transpile(code)
        assert 'setDragImage' in result


class TestFileDrop:
    """Tests for file drop handling."""
    
    def test_files_length(self):
        """files.length should pass through."""
        code = '''
def handle(event):
    count = event.dataTransfer.files.length
'''
        result = transpile(code)
        assert 'event.dataTransfer.files.length' in result
    
    def test_files_iteration(self):
        """Iterating over files should work."""
        code = '''
def handle(event):
    for file in event.dataTransfer.files:
        upload(file)
'''
        result = transpile(code)
        assert 'event.dataTransfer.files' in result
    
    def test_files_index_access(self):
        """Accessing files by index should work."""
        code = '''
def handle(event):
    first_file = event.dataTransfer.files[0]
'''
        result = transpile(code)
        assert 'event.dataTransfer.files' in result


class TestDragEventPatterns:
    """Tests for complete drag-drop patterns."""
    
    def test_drag_start_handler(self):
        """Complete dragstart handler should work."""
        code = '''
def on_drag_start(event):
    event.dataTransfer.setData("text/plain", item_id)
    event.dataTransfer.effectAllowed = "move"
'''
        result = transpile(code)
        assert 'setData' in result
        assert 'effectAllowed' in result
        assert '__py.' not in result
    
    def test_drag_over_handler(self):
        """dragover handler should work."""
        code = '''
def on_drag_over(event):
    event.preventDefault()
    event.dataTransfer.dropEffect = "move"
'''
        result = transpile(code)
        assert 'event.preventDefault()' in result
        assert 'dropEffect' in result
    
    def test_drop_handler(self):
        """Complete drop handler should work."""
        code = '''
def on_drop(event):
    event.preventDefault()
    data = event.dataTransfer.getData("text/plain")
    move_item(data, event.target)
'''
        result = transpile(code)
        assert 'event.preventDefault()' in result
        assert 'getData("text/plain")' in result
        assert 'event.target' in result
    
    def test_file_drop_handler(self):
        """File drop handler should work."""
        code = '''
def on_drop(event):
    event.preventDefault()
    if event.dataTransfer.files.length > 0:
        for file in event.dataTransfer.files:
            upload_file(file)
'''
        result = transpile(code)
        assert 'event.dataTransfer.files.length' in result
        assert 'event.dataTransfer.files' in result
    
    def test_drag_leave_handler(self):
        """dragleave handler should work."""
        code = '''
def on_drag_leave(event):
    event.target.classList.remove("drag-over")
'''
        result = transpile(code)
        assert 'event.target' in result
        assert 'classList.remove' in result
    
    def test_html_text_data_formats(self):
        """Multiple data formats should work."""
        code = '''
def on_drag_start(event):
    event.dataTransfer.setData("text/plain", text_content)
    event.dataTransfer.setData("text/html", html_content)
'''
        result = transpile(code)
        assert 'text/plain' in result
        assert 'text/html' in result
    
    def test_check_data_types(self):
        """Checking available data types should work."""
        code = '''
def on_drop(event):
    if "text/html" in event.dataTransfer.types:
        html = event.dataTransfer.getData("text/html")
'''
        result = transpile(code)
        assert 'event.dataTransfer.types' in result

