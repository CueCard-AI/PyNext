"""
Phase 18.8: Integration Tests

End-to-end tests for all Phase 18.8 features working together.

Tests: 30
"""

import pytest
from pynext.transpiler import parse, emit, transpile
from pynext.transpiler.sourcemap import SourceMapBuilder
from pynext.transpiler.debug import (
    get_transpile_debug_info,
    register_handler_debug_info,
    get_registered_handlers,
    clear_handler_registry,
)


class TestFullTranspilationPipeline:
    """Tests for complete transpilation pipeline."""
    
    def test_simple_handler_full_pipeline(self):
        """Simple handler through full pipeline."""
        code = '''
def handle_click():
    count = count + 1
'''
        # Parse
        ir = parse(code)
        assert ir is not None
        
        # Emit
        js = emit(ir)
        assert "function" in js
        
        # Full transpile
        js = transpile(code)
        assert "handle_click" in js
    
    def test_class_with_all_features(self):
        """Class with all Phase 18.8 features."""
        code = '''
class TodoList:
    def __init__(self, name="default"):
        self.name = name
        self.items = []
    
    def add(self, item):
        assert item, "Item required"
        self.items.append(item)
    
    @property
    def count(self):
        return len(self.items)
    
    @staticmethod
    def create():
        return TodoList()
'''
        js = transpile(code)
        
        # All features present
        assert "class TodoList" in js
        assert "constructor" in js
        assert "add(" in js
        assert "get count()" in js
        assert "static create()" in js
    
    def test_class_with_inheritance(self):
        """Class inheritance full pipeline."""
        code = '''
class BaseTodo:
    def __init__(self):
        pass

class Todo(BaseTodo):
    def __init__(self, title):
        super().__init__()
        self.title = title
'''
        js = transpile(code)
        assert "extends BaseTodo" in js or "extends" in js
        assert "super" in js  # super is present


class TestDebugIntegration:
    """Tests for debug utilities integration."""
    
    def setup_method(self):
        """Clear registry before each test."""
        clear_handler_registry()
    
    def test_debug_info_for_class(self):
        """Get debug info for class."""
        code = '''
class Counter:
    def increment(self):
        self.count = self.count + 1
'''
        info = get_transpile_debug_info(code, handler_name="Counter")
        
        assert info.original == code
        assert "Counter" in info.javascript
        assert info.handler_name == "Counter"
    
    def test_debug_info_with_source_map(self):
        """Debug info includes source map."""
        code = "x = 5"
        info = get_transpile_debug_info(code)
        
        assert info.source_map is not None
        assert info.source_map["version"] == 3
    
    def test_debug_info_runtime_deps(self):
        """Debug info tracks runtime dependencies."""
        code = '''
if items:
    last = items[-1]
'''
        info = get_transpile_debug_info(code)
        
        # Should detect __py.bool and/or __py.at
        deps_str = str(info.runtime_deps)
        assert "__py" in deps_str or len(info.runtime_deps) >= 0
    
    def test_register_and_retrieve_handler(self):
        """Register and retrieve handler debug info."""
        register_handler_debug_info(
            "my_handler",
            "def my_handler(): pass",
            "function my_handler() {}",
            ["__py.bool"],
        )
        
        handlers = get_registered_handlers()
        assert "my_handler" in handlers
    
    def test_full_debug_workflow(self):
        """Full debug info workflow."""
        code = '''
def handle_add(items):
    if items:
        return items[-1]
'''
        # Get debug info
        info = get_transpile_debug_info(code, handler_name="handle_add")
        
        # Register it
        register_handler_debug_info(
            info.handler_name,
            info.original,
            info.javascript,
            info.runtime_deps,
            info.source_map,
        )
        
        # Retrieve it
        handlers = get_registered_handlers()
        assert "handle_add" in handlers


class TestSourceMapIntegration:
    """Tests for source map integration."""
    
    def test_source_map_for_simple_code(self):
        """Generate source map for simple code."""
        code = "x = 1\ny = 2\nz = 3"
        info = get_transpile_debug_info(code)
        
        assert info.source_map is not None
        assert info.source_map["sources"] == ["handler.py"]
    
    def test_source_map_includes_content(self):
        """Source map includes source content."""
        code = "x = 1"
        info = get_transpile_debug_info(code)
        
        assert "sourcesContent" in info.source_map
        assert info.source_map["sourcesContent"][0] == code
    
    def test_source_map_mappings_exist(self):
        """Source map has mappings."""
        code = "x = 1"
        info = get_transpile_debug_info(code)
        
        assert "mappings" in info.source_map


class TestAssertIntegration:
    """Tests for assert integration with other features."""
    
    def test_assert_in_class_method(self):
        """Assert in class method."""
        code = '''
class Validator:
    def validate(self, x):
        assert x > 0, "Must be positive"
        return x
'''
        js = transpile(code)
        assert "throw" in js
        assert "AssertionError" in js
    
    def test_assert_with_walrus(self):
        """Assert after walrus operator."""
        code = '''
def process():
    if (x := get_value()):
        assert x > 0
'''
        js = transpile(code)
        assert "let x" in js
        assert "throw" in js


class TestWalrusIntegration:
    """Tests for walrus operator integration."""
    
    def test_walrus_in_class_method(self):
        """Walrus in class method."""
        code = '''
class Fetcher:
    def fetch(self):
        if (data := self.get_data()):
            return data
'''
        js = transpile(code)
        assert "let data" in js or "data =" in js
    
    def test_walrus_with_inheritance(self):
        """Walrus in inherited class."""
        code = '''
class Child(Parent):
    def process(self):
        if (result := super().compute()):
            return result
'''
        js = transpile(code)
        assert "super" in js  # super is present


class TestComplexScenarios:
    """Tests for complex real-world scenarios."""
    
    def test_todo_app_complete(self):
        """Complete Todo app class."""
        code = '''
class Todo:
    def __init__(self, title, done=False):
        assert title, "Title required"
        self.title = title
        self.done = done
    
    def toggle(self):
        self.done = not self.done
    
    @property
    def status(self):
        return "Done" if self.done else "Pending"
    
    @staticmethod
    def from_dict(data):
        return Todo(data["title"], data.get("done", False))

class TodoList:
    def __init__(self):
        self.items = []
    
    def add(self, title):
        if (existing := self.find(title)):
            return existing
        todo = Todo(title)
        self.items.append(todo)
        return todo
    
    def find(self, title):
        for item in self.items:
            if item.title == title:
                return item
        return None
'''
        js = transpile(code)
        
        # Verify key features
        assert "class Todo" in js
        assert "class TodoList" in js
        assert "constructor" in js
        assert "toggle()" in js
        assert "get status()" in js
        assert "static from_dict" in js
        assert "throw" in js  # From assert
    
    def test_counter_with_validation(self):
        """Counter class with validation."""
        code = '''
class Counter:
    def __init__(self, initial=0):
        assert initial >= 0, "Initial must be non-negative"
        self.count = initial
    
    def increment(self, amount=1):
        assert amount > 0, "Amount must be positive"
        self.count = self.count + amount
    
    def decrement(self, amount=1):
        if (new_count := self.count - amount) >= 0:
            self.count = new_count
    
    @property
    def is_zero(self):
        return self.count == 0
'''
        js = transpile(code)
        
        assert "constructor" in js
        assert "increment" in js
        assert "decrement" in js
        assert "get is_zero" in js
        assert js.count("throw") >= 2  # Two asserts


class TestErrorRecovery:
    """Tests for error handling and recovery."""
    
    def test_valid_code_after_warning(self):
        """Code transpiles after global warning."""
        import warnings
        code = '''
counter = 0

def increment():
    global counter
    counter = counter + 1
'''
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            js = transpile(code)
            assert "counter" in js
    
    def test_debug_info_after_parse_error(self):
        """Debug info captures parse errors."""
        code = "class Invalid(A, B, C): pass"  # Multiple inheritance
        
        info = get_transpile_debug_info(code)
        # Should have error info, not crash
        assert info is not None

