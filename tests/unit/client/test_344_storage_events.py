"""
Phase 34.4: Storage Event Tests

Unit tests for StorageEvent transpilation covering:
- storage event listener
- key, oldValue, newValue properties
- Cross-tab communication patterns

Total: 10 tests
"""

import pytest
from pynext.transpiler import transpile


class TestStorageEventBasics:
    """Tests for basic StorageEvent properties."""
    
    def test_storage_event_listener(self):
        """storage event listener should pass through."""
        code = '''
from pynext.client import window

def on_storage(event):
    handle_storage_change()

window.addEventListener("storage", on_storage)
'''
        result = transpile(code)
        assert 'addEventListener("storage"' in result
        assert '__py.' not in result
    
    def test_key_property(self):
        """StorageEvent.key should pass through."""
        code = '''
def on_storage(event):
    key = event.key
'''
        result = transpile(code)
        assert 'event.key' in result
    
    def test_old_value_property(self):
        """StorageEvent.oldValue should pass through."""
        code = '''
def on_storage(event):
    old = event.oldValue
'''
        result = transpile(code)
        assert 'event.oldValue' in result
    
    def test_new_value_property(self):
        """StorageEvent.newValue should pass through."""
        code = '''
def on_storage(event):
    new = event.newValue
'''
        result = transpile(code)
        assert 'event.newValue' in result
    
    def test_url_property(self):
        """StorageEvent.url should pass through."""
        code = '''
def on_storage(event):
    source_url = event.url
'''
        result = transpile(code)
        assert 'event.url' in result
    
    def test_storage_area_property(self):
        """StorageEvent.storageArea should pass through."""
        code = '''
def on_storage(event):
    storage = event.storageArea
'''
        result = transpile(code)
        assert 'event.storageArea' in result


class TestCrossTabPatterns:
    """Tests for cross-tab communication patterns."""
    
    def test_sync_state_pattern(self):
        """Cross-tab state sync pattern should work."""
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
    
    def test_clear_storage_detection(self):
        """Detecting storage clear should work."""
        code = '''
def on_storage(event):
    if event.key is None:
        # Storage was cleared
        handle_storage_cleared()
'''
        result = transpile(code)
        assert 'event.key' in result
    
    def test_storage_area_check(self):
        """Checking storage area should work."""
        code = '''
def on_storage(event):
    if event.storageArea == localStorage:
        handle_local_storage_change(event)
    elif event.storageArea == sessionStorage:
        handle_session_storage_change(event)
'''
        result = transpile(code)
        assert 'event.storageArea' in result
    
    def test_filtered_storage_listener(self):
        """Filtered storage listener should work."""
        code = '''
from pynext.client import window

def create_storage_watcher(key_prefix, callback):
    def on_storage(event):
        if event.key and event.key.startswith(key_prefix):
            callback(event.key, event.oldValue, event.newValue)
    
    window.addEventListener("storage", on_storage)

# Watch for all "user:" prefixed keys
create_storage_watcher("user:", handle_user_change)
'''
        result = transpile(code)
        assert 'event.key' in result
        assert 'event.oldValue' in result
        assert 'event.newValue' in result

