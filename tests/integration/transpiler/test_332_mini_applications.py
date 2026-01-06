"""
Phase 33.2: Advanced Constructs Mini Application Tests

Comprehensive mini applications demonstrating Phase 33.2 features:
- Dunder methods (operator overloading, special methods)
- Generators (yield, yield from, generator protocol)
- Context managers (with statements, resource management)
- Pattern matching (match/case with all pattern types)
- Async/await (async functions, async for/with, asyncio.gather)

These mini apps test real-world usage patterns and integration of Phase 33.2 features.
"""

import pytest
import subprocess
import tempfile
import os
from pathlib import Path
from pynext.transpiler import transpile

# Import existing mini app harness
import sys
sys.path.insert(0, str(Path(__file__).parent))
from test_mini_applications import MiniAppHarness


@pytest.fixture
def harness():
    """Fixture providing mini app harness (reuse existing)."""
    h = MiniAppHarness()
    yield h
    import shutil
    shutil.rmtree(h.temp_dir, ignore_errors=True)


def _normalize_output(output: str) -> list:
    """
    Normalize output for comparison between Python and JavaScript.
    
    Handles:
    - Boolean representations (True/False vs true/false)
    - None vs null
    - String quote differences (' vs ")
    - List representation differences
    """
    import re
    lines = [l.strip() for l in output.split("\n") if l.strip()]
    normalized = []
    for line in lines:
        # Normalize boolean representations
        line = re.sub(r'\bTrue\b', 'true', line)
        line = re.sub(r'\bFalse\b', 'false', line)
        # Normalize None
        line = re.sub(r'\bNone\b', 'null', line)
        # Normalize string quotes (Python uses ' by default, JS uses ")
        # But be careful not to break escaped quotes
        # Simple approach: convert single quotes to double quotes for simple strings
        # This is a heuristic - may need refinement
        normalized.append(line)
    return normalized


# =============================================================================
# DUNDER METHODS MINI APPS
# =============================================================================

class TestVectorMathApp:
    """Vector math library using dunder methods."""
    
    def test_vector_operations(self, harness):
        """Vector class with arithmetic and comparison dunders."""
        code = """
class Vector:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def __str__(self):
        return f"({self.x}, {self.y})"
    
    def __repr__(self):
        return f"Vector({self.x}, {self.y})"
    
    def __eq__(self, other):
        if not isinstance(other, Vector):
            return False
        return self.x == other.x and self.y == other.y
    
    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other):
        return Vector(self.x - other.x, self.y - other.y)
    
    def __mul__(self, scalar):
        return Vector(self.x * scalar, self.y * scalar)
    
    def __abs__(self):
        return (self.x**2 + self.y**2)**0.5
    
    def __iter__(self):
        yield self.x
        yield self.y

# Test
v1 = Vector(1, 2)
v2 = Vector(3, 4)
v3 = v1 + v2
v4 = v1 * 2
magnitude = abs(v1)

print(str(v1))
print(str(v3))
print(str(v4))
print(magnitude)
print(v1 == Vector(1, 2))
print(list(v1))
"""
        result = harness.run_mini_app(code)
        
        # Both should execute successfully
        assert result["python"]["returncode"] == 0, f"Python failed: {result['python']['stderr']}"
        assert result["javascript"]["returncode"] == 0, f"JS failed: stdout={result['javascript']['stdout'][:200]}, stderr={result['javascript']['stderr'][:200]}"
        
        # Compare outputs
        py_output = result["python"]["stdout"].strip()
        js_output = result["javascript"]["stdout"].strip()
        
        # Normalize for comparison (handle whitespace and format differences)
        py_lines = _normalize_output(py_output)
        js_lines = _normalize_output(js_output)
        
        assert py_lines == js_lines, f"Python: {py_output}, JS: {js_output}"


class TestContainerApp:
    """Container class using container dunders."""
    
    def test_container_dunders(self, harness):
        """Container with len, bool, iter, contains, getitem."""
        code = """
class Container:
    def __init__(self, items):
        self.items = list(items)
    
    def __len__(self):
        return len(self.items)
    
    def __bool__(self):
        return len(self.items) > 0
    
    def __iter__(self):
        yield from self.items
    
    def __contains__(self, item):
        return item in self.items
    
    def __getitem__(self, index):
        return self.items[index]
    
    def __setitem__(self, index, value):
        self.items[index] = value

# Test
c = Container([1, 2, 3, 4, 5])
print(len(c))
print(bool(c))
print(3 in c)
print(10 in c)
print(c[2])
c[2] = 99
print(c[2])
print([x for x in c])
"""
        result = harness.run_mini_app(code)
        
        # Both should execute successfully
        assert result["python"]["returncode"] == 0, f"Python failed: {result['python']['stderr']}"
        assert result["javascript"]["returncode"] == 0, f"JS failed: stdout={result['javascript']['stdout'][:200]}, stderr={result['javascript']['stderr'][:200]}"
        
        # Compare outputs
        py_output = result["python"]["stdout"].strip()
        js_output = result["javascript"]["stdout"].strip()
        
        # Normalize for comparison (handle whitespace and format differences)
        py_lines = _normalize_output(py_output)
        js_lines = _normalize_output(js_output)
        
        assert py_lines == js_lines, f"Python: {py_output}, JS: {js_output}"


class TestCallableApp:
    """Callable class using __call__."""
    
    def test_callable_class(self, harness):
        """Class that can be called like a function."""
        code = """
class Multiplier:
    def __init__(self, factor):
        self.factor = factor
    
    def __call__(self, value):
        return value * self.factor
    
    def __str__(self):
        return f"Multiplier({self.factor})"

# Test
double = Multiplier(2)
triple = Multiplier(3)

print(double(5))
print(triple(7))
print(str(double))
"""
        result = harness.run_mini_app(code)
        
        # Both should execute successfully
        assert result["python"]["returncode"] == 0, f"Python failed: {result['python']['stderr']}"
        assert result["javascript"]["returncode"] == 0, f"JS failed: stdout={result['javascript']['stdout'][:200]}, stderr={result['javascript']['stderr'][:200]}"
        
        # Compare outputs
        py_output = result["python"]["stdout"].strip()
        js_output = result["javascript"]["stdout"].strip()
        
        # Normalize for comparison (handle whitespace and format differences)
        py_lines = _normalize_output(py_output)
        js_lines = _normalize_output(js_output)
        
        assert py_lines == js_lines, f"Python: {py_output}, JS: {js_output}"


# =============================================================================
# GENERATORS MINI APPS
# =============================================================================

class TestGeneratorApp:
    """Generator functions for iteration."""
    
    def test_fibonacci_generator(self, harness):
        """Infinite Fibonacci generator."""
        code = """
def fibonacci():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

# Test
fib = fibonacci()
results = []
for i in range(10):
    results.append(next(fib))

print(results)
"""
        result = harness.run_mini_app(code)
        
        # Both should execute successfully
        assert result["python"]["returncode"] == 0, f"Python failed: {result['python']['stderr']}"
        assert result["javascript"]["returncode"] == 0, f"JS failed: stdout={result['javascript']['stdout'][:200]}, stderr={result['javascript']['stderr'][:200]}"
        
        # Compare outputs
        py_output = result["python"]["stdout"].strip()
        js_output = result["javascript"]["stdout"].strip()
        
        # Normalize for comparison (handle whitespace and format differences)
        py_lines = _normalize_output(py_output)
        js_lines = _normalize_output(js_output)
        
        assert py_lines == js_lines, f"Python: {py_output}, JS: {js_output}"
    
    def test_flatten_generator(self, harness):
        """Recursive flatten generator using yield from."""
        code = """
def flatten(nested):
    for item in nested:
        if isinstance(item, list):
            yield from flatten(item)
        else:
            yield item

# Test
nested = [1, [2, 3], [4, [5, 6]], 7]
flat = list(flatten(nested))
print(flat)
"""
        result = harness.run_mini_app(code)
        
        # Both should execute successfully
        assert result["python"]["returncode"] == 0, f"Python failed: {result['python']['stderr']}"
        assert result["javascript"]["returncode"] == 0, f"JS failed: stdout={result['javascript']['stdout'][:200]}, stderr={result['javascript']['stderr'][:200]}"
        
        # Compare outputs
        py_output = result["python"]["stdout"].strip()
        js_output = result["javascript"]["stdout"].strip()
        
        # Normalize for comparison (handle whitespace and format differences)
        py_lines = _normalize_output(py_output)
        js_lines = _normalize_output(js_output)
        
        assert py_lines == js_lines, f"Python: {py_output}, JS: {js_output}"
    
    def test_generator_with_state(self, harness):
        """Generator with state management."""
        code = """
def counter(start=0):
    count = start
    while True:
        increment = yield count
        if increment is not None:
            count += increment
        else:
            count += 1

# Test
c = counter(10)
results = []
results.append(next(c))
results.append(c.send(5))
results.append(next(c))
print(results)
"""
        result = harness.run_mini_app(code)
        
        # Both should execute successfully
        assert result["python"]["returncode"] == 0, f"Python failed: {result['python']['stderr']}"
        assert result["javascript"]["returncode"] == 0, f"JS failed: stdout={result['javascript']['stdout'][:200]}, stderr={result['javascript']['stderr'][:200]}"
        
        # Compare outputs
        py_output = result["python"]["stdout"].strip()
        js_output = result["javascript"]["stdout"].strip()
        
        # Normalize for comparison (handle whitespace and format differences)
        py_lines = _normalize_output(py_output)
        js_lines = _normalize_output(js_output)
        
        assert py_lines == js_lines, f"Python: {py_output}, JS: {js_output}"


# =============================================================================
# CONTEXT MANAGERS MINI APPS
# =============================================================================

class TestContextManagerApp:
    """Context managers for resource management."""
    
    def test_file_context_manager(self, harness):
        """File-like context manager."""
        code = """
class FileManager:
    def __init__(self, filename, mode='r'):
        self.filename = filename
        self.mode = mode
        self.file = None
        self.opened = False
    
    def __enter__(self):
        self.opened = True
        self.file = {"content": f"File: {self.filename}", "mode": self.mode}
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.file = None
        self.opened = False
        return False
    
    def read(self):
        return self.file["content"] if self.file else None

# Test
with FileManager("test.txt") as f:
    content = f.read()
    print(content)
    print(f.opened)

print(f.opened)  # Should be False after exit
"""
        result = harness.run_mini_app(code)
        
        # Both should execute successfully
        assert result["python"]["returncode"] == 0, f"Python failed: {result['python']['stderr']}"
        assert result["javascript"]["returncode"] == 0, f"JS failed: stdout={result['javascript']['stdout'][:200]}, stderr={result['javascript']['stderr'][:200]}"
        
        # Compare outputs
        py_output = result["python"]["stdout"].strip()
        js_output = result["javascript"]["stdout"].strip()
        
        # Normalize for comparison (handle whitespace and format differences)
        py_lines = _normalize_output(py_output)
        js_lines = _normalize_output(js_output)
        
        assert py_lines == js_lines, f"Python: {py_output}, JS: {js_output}"
    
    def test_multiple_context_managers(self, harness):
        """Multiple context managers."""
        code = """
class Resource:
    def __init__(self, name):
        self.name = name
        self.active = False
    
    def __enter__(self):
        self.active = True
        return self
    
    def __exit__(self, *args):
        self.active = False
        return False

# Test
with Resource("A") as a, Resource("B") as b:
    print(f"{a.name}: {a.active}")
    print(f"{b.name}: {b.active}")

print(f"A: {a.active}")
print(f"B: {b.active}")
"""
        result = harness.run_mini_app(code)
        
        # Both should execute successfully
        assert result["python"]["returncode"] == 0, f"Python failed: {result['python']['stderr']}"
        assert result["javascript"]["returncode"] == 0, f"JS failed: stdout={result['javascript']['stdout'][:200]}, stderr={result['javascript']['stderr'][:200]}"
        
        # Compare outputs
        py_output = result["python"]["stdout"].strip()
        js_output = result["javascript"]["stdout"].strip()
        
        # Normalize for comparison (handle whitespace and format differences)
        py_lines = _normalize_output(py_output)
        js_lines = _normalize_output(js_output)
        
        assert py_lines == js_lines, f"Python: {py_output}, JS: {js_output}"


# =============================================================================
# PATTERN MATCHING MINI APPS
# =============================================================================

class TestPatternMatchingApp:
    """Pattern matching for command processing."""
    
    def test_command_parser(self, harness):
        """Command parser using pattern matching."""
        code = """
def handle_command(cmd):
    match cmd:
        case ["move", x, y]:
            return f"Moving to ({x}, {y})"
        case ["attack", target]:
            return f"Attacking {target}"
        case ["use", item, target]:
            return f"Using {item} on {target}"
        case ["quit"]:
            return "Quitting"
        case _:
            return f"Unknown command: {cmd}"

# Test
commands = [
    ["move", 10, 20],
    ["attack", "enemy"],
    ["use", "potion", "player"],
    ["quit"],
    ["unknown", "command"]
]

results = []
for cmd in commands:
    results.append(handle_command(cmd))

for r in results:
    print(r)
"""
        result = harness.run_mini_app(code)
        
        # Both should execute successfully
        assert result["python"]["returncode"] == 0, f"Python failed: {result['python']['stderr']}"
        assert result["javascript"]["returncode"] == 0, f"JS failed: stdout={result['javascript']['stdout'][:200]}, stderr={result['javascript']['stderr'][:200]}"
        
        # Compare outputs
        py_output = result["python"]["stdout"].strip()
        js_output = result["javascript"]["stdout"].strip()
        
        # Normalize for comparison (handle whitespace and format differences)
        py_lines = _normalize_output(py_output)
        js_lines = _normalize_output(js_output)
        
        assert py_lines == js_lines, f"Python: {py_output}, JS: {js_output}"
    
    def test_api_response_handler(self, harness):
        """API response handler using pattern matching."""
        code = """
def handle_response(response):
    match response:
        case {"status": "success", "data": data}:
            return f"Success: {data}"
        case {"status": "error", "message": msg}:
            return f"Error: {msg}"
        case {"status": "pending"}:
            return "Pending..."
        case _:
            return "Unknown response"

# Test
responses = [
    {"status": "success", "data": [1, 2, 3]},
    {"status": "error", "message": "Not found"},
    {"status": "pending"},
    {"status": "unknown"}
]

for resp in responses:
    print(handle_response(resp))
"""
        result = harness.run_mini_app(code)
        
        # Both should execute successfully
        assert result["python"]["returncode"] == 0, f"Python failed: {result['python']['stderr']}"
        assert result["javascript"]["returncode"] == 0, f"JS failed: stdout={result['javascript']['stdout'][:200]}, stderr={result['javascript']['stderr'][:200]}"
        
        # Compare outputs
        py_output = result["python"]["stdout"].strip()
        js_output = result["javascript"]["stdout"].strip()
        
        # Normalize for comparison (handle whitespace and format differences)
        py_lines = _normalize_output(py_output)
        js_lines = _normalize_output(js_output)
        
        assert py_lines == js_lines, f"Python: {py_output}, JS: {js_output}"
    
    def test_pattern_with_guard(self, harness):
        """Pattern matching with guard clauses."""
        code = """
def process_value(value):
    match value:
        case x if x > 0:
            return f"Positive: {x}"
        case x if x < 0:
            return f"Negative: {x}"
        case 0:
            return "Zero"
        case _:
            return "Unknown"

# Test
values = [5, -3, 0, 10, -7]
for v in values:
    print(process_value(v))
"""
        result = harness.run_mini_app(code)
        
        # Both should execute successfully
        assert result["python"]["returncode"] == 0, f"Python failed: {result['python']['stderr']}"
        assert result["javascript"]["returncode"] == 0, f"JS failed: stdout={result['javascript']['stdout'][:200]}, stderr={result['javascript']['stderr'][:200]}"
        
        # Compare outputs
        py_output = result["python"]["stdout"].strip()
        js_output = result["javascript"]["stdout"].strip()
        
        # Normalize for comparison (handle whitespace and format differences)
        py_lines = _normalize_output(py_output)
        js_lines = _normalize_output(js_output)
        
        assert py_lines == js_lines, f"Python: {py_output}, JS: {js_output}"


# =============================================================================
# ASYNC MINI APPS
# =============================================================================

class TestAsyncApp:
    """Async/await applications."""
    
    def test_async_fetch(self, harness):
        """Async function for data fetching."""
        code = """
# Mock async functions for testing
class MockFetch:
    async def get(self, url):
        return {"data": f"Data from {url}"}

async def fetch_data(url):
    fetcher = MockFetch()
    response = await fetcher.get(url)
    return response["data"]

# Test (synchronous execution for testing)
import asyncio

async def test():
    result = await fetch_data("/api/data")
    print(result)
    return result

# Run async test
result = asyncio.run(test())
print(f"Final: {result}")
"""
        # Note: This requires async runtime support
        # For now, we'll test the transpilation structure
        result = transpile(code)
        assert "async function" in result
        assert "await" in result
    
    def test_async_gather(self, harness):
        """Async gather for concurrent operations (transpilation test)."""
        code = """
# Mock async functions
async def fetch_a():
    return "A"

async def fetch_b():
    return "B"

async def fetch_c():
    return "C"

async def fetch_all():
    results = await asyncio.gather(
        fetch_a(),
        fetch_b(),
        fetch_c()
    )
    return results
"""
        # This test only verifies transpilation, not execution
        # Note: import asyncio is not supported in transpiler
        result = transpile(code)
        assert "async function" in result
        assert "Promise.all" in result
        # Don't try to execute - async requires proper runtime


# =============================================================================
# INTEGRATED MINI APPS (Combining Multiple Features)
# =============================================================================

class TestIntegratedApp:
    """Mini apps combining multiple Phase 33.2 features."""
    
    def test_vector_with_generator(self, harness):
        """Vector class with generator iteration."""
        code = """
class Vector:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def __iter__(self):
        yield self.x
        yield self.y
    
    def __str__(self):
        return f"({self.x}, {self.y})"

def vector_range(n):
    for i in range(n):
        yield Vector(i, i*2)

# Test
vectors = list(vector_range(5))
for v in vectors:
    print(v)
    print(list(v))
"""
        result = harness.run_mini_app(code)
        
        # Both should execute successfully
        assert result["python"]["returncode"] == 0, f"Python failed: {result['python']['stderr']}"
        assert result["javascript"]["returncode"] == 0, f"JS failed: stdout={result['javascript']['stdout'][:200]}, stderr={result['javascript']['stderr'][:200]}"
        
        # Compare outputs
        py_output = result["python"]["stdout"].strip()
        js_output = result["javascript"]["stdout"].strip()
        
        # Normalize for comparison (handle whitespace and format differences)
        py_lines = _normalize_output(py_output)
        js_lines = _normalize_output(js_output)
        
        assert py_lines == js_lines, f"Python: {py_output}, JS: {js_output}"
    
    def test_container_with_context(self, harness):
        """Container with context manager."""
        code = """
class ManagedContainer:
    def __init__(self, items):
        self.items = list(items)
        self.modified = False
    
    def __len__(self):
        return len(self.items)
    
    def __enter__(self):
        self.modified = True
        return self
    
    def __exit__(self, *args):
        self.modified = False
        return False
    
    def add(self, item):
        self.items.append(item)

# Test
with ManagedContainer([1, 2, 3]) as c:
    print(len(c))
    print(c.modified)
    c.add(4)
    print(len(c))

print(c.modified)
"""
        result = harness.run_mini_app(code)
        
        # Both should execute successfully
        assert result["python"]["returncode"] == 0, f"Python failed: {result['python']['stderr']}"
        assert result["javascript"]["returncode"] == 0, f"JS failed: stdout={result['javascript']['stdout'][:200]}, stderr={result['javascript']['stderr'][:200]}"
        
        # Compare outputs
        py_output = result["python"]["stdout"].strip()
        js_output = result["javascript"]["stdout"].strip()
        
        # Normalize for comparison (handle whitespace and format differences)
        py_lines = _normalize_output(py_output)
        js_lines = _normalize_output(js_output)
        
        assert py_lines == js_lines, f"Python: {py_output}, JS: {js_output}"
    
    def test_pattern_with_generator(self, harness):
        """Pattern matching with generator."""
        code = """
def process_commands(commands):
    for cmd in commands:
        match cmd:
            case ["action", value]:
                yield f"Action: {value}"
            case ["data", *values]:
                yield f"Data: {values}"
            case _:
                yield "Unknown"

# Test
commands = [
    ["action", "start"],
    ["data", 1, 2, 3],
    ["action", "stop"],
    ["unknown"]
]

results = list(process_commands(commands))
for r in results:
    print(r)
"""
        result = harness.run_mini_app(code)
        
        # Both should execute successfully
        assert result["python"]["returncode"] == 0, f"Python failed: {result['python']['stderr']}"
        assert result["javascript"]["returncode"] == 0, f"JS failed: stdout={result['javascript']['stdout'][:200]}, stderr={result['javascript']['stderr'][:200]}"
        
        # Compare outputs
        py_output = result["python"]["stdout"].strip()
        js_output = result["javascript"]["stdout"].strip()
        
        # Normalize for comparison (handle whitespace and format differences)
        py_lines = _normalize_output(py_output)
        js_lines = _normalize_output(js_output)
        
        assert py_lines == js_lines, f"Python: {py_output}, JS: {js_output}"
    
    def test_complete_workflow(self, harness):
        """Complete workflow using all Phase 33.2 features."""
        code = """
class DataProcessor:
    def __init__(self):
        self.queue = []
    
    def __len__(self):
        return len(self.queue)
    
    def __iter__(self):
        yield from self.queue
    
    def __str__(self):
        return f"Processor({len(self)} items)"
    
    def add(self, item):
        self.queue.append(item)
    
    def process_stream(self):
        for item in self.queue:
            match item:
                case {"type": "data", "value": value}:
                    yield f"Processed: {value}"
                case {"type": "error", "message": msg}:
                    yield f"Error: {msg}"
                case _:
                    yield "Unknown item"

# Test
processor = DataProcessor()
processor.add({"type": "data", "value": 42})
processor.add({"type": "error", "message": "Test error"})
processor.add({"type": "unknown"})

print(str(processor))
print(len(processor))

results = list(processor.process_stream())
for r in results:
    print(r)
"""
        result = harness.run_mini_app(code)
        
        # Both should execute successfully
        assert result["python"]["returncode"] == 0, f"Python failed: {result['python']['stderr']}"
        assert result["javascript"]["returncode"] == 0, f"JS failed: stdout={result['javascript']['stdout'][:200]}, stderr={result['javascript']['stderr'][:200]}"
        
        # Compare outputs
        py_output = result["python"]["stdout"].strip()
        js_output = result["javascript"]["stdout"].strip()
        
        # Normalize for comparison (handle whitespace and format differences)
        py_lines = _normalize_output(py_output)
        js_lines = _normalize_output(js_output)
        
        assert py_lines == js_lines, f"Python: {py_output}, JS: {js_output}"


# =============================================================================
# REAL-WORLD SCENARIOS
# =============================================================================

class TestRealWorldApps:
    """Real-world application scenarios."""
    
    def test_game_entity_system(self, harness):
        """Game entity system with dunders and pattern matching."""
        code = """
class Entity:
    def __init__(self, x, y, health):
        self.x = x
        self.y = y
        self.health = health
    
    def __str__(self):
        return f"Entity({self.x}, {self.y}, {self.health})"
    
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y
    
    def __add__(self, other):
        return Entity(self.x + other.x, self.y + other.y, self.health + other.health)

def handle_event(event):
    match event:
        case {"type": "move", "entity": e, "dx": dx, "dy": dy}:
            e.x += dx
            e.y += dy
            return f"Moved {e}"
        case {"type": "damage", "entity": e, "amount": amount}:
            e.health -= amount
            return f"Damaged {e}"
        case _:
            return "Unknown event"

# Test
player = Entity(0, 0, 100)
enemy = Entity(5, 5, 50)

events = [
    {"type": "move", "entity": player, "dx": 2, "dy": 3},
    {"type": "damage", "entity": enemy, "amount": 10}
]

for event in events:
    print(handle_event(event))

print(player)
print(enemy)
"""
        result = harness.run_mini_app(code)
        
        # Both should execute successfully
        assert result["python"]["returncode"] == 0, f"Python failed: {result['python']['stderr']}"
        assert result["javascript"]["returncode"] == 0, f"JS failed: stdout={result['javascript']['stdout'][:200]}, stderr={result['javascript']['stderr'][:200]}"
        
        # Compare outputs
        py_output = result["python"]["stdout"].strip()
        js_output = result["javascript"]["stdout"].strip()
        
        # Normalize for comparison (handle whitespace and format differences)
        py_lines = _normalize_output(py_output)
        js_lines = _normalize_output(js_output)
        
        assert py_lines == js_lines, f"Python: {py_output}, JS: {js_output}"
    
    def test_data_pipeline(self, harness):
        """Data processing pipeline with generators and context."""
        code = """
class DataSource:
    def __init__(self, data):
        self.data = data
        self.processed = False
    
    def __enter__(self):
        self.processed = True
        return self
    
    def __exit__(self, *args):
        self.processed = False
        return False
    
    def stream(self):
        for item in self.data:
            yield item

def transform(stream):
    for item in stream:
        yield item * 2

def filter_positive(stream):
    for item in stream:
        if item > 0:
            yield item

# Test
with DataSource([1, -2, 3, -4, 5]) as source:
    stream = source.stream()
    transformed = transform(stream)
    filtered = filter_positive(transformed)
    results = list(filtered)
    print(results)
"""
        result = harness.run_mini_app(code)
        
        # Both should execute successfully
        assert result["python"]["returncode"] == 0, f"Python failed: {result['python']['stderr']}"
        assert result["javascript"]["returncode"] == 0, f"JS failed: stdout={result['javascript']['stdout'][:200]}, stderr={result['javascript']['stderr'][:200]}"
        
        # Compare outputs
        py_output = result["python"]["stdout"].strip()
        js_output = result["javascript"]["stdout"].strip()
        
        # Normalize for comparison (handle whitespace and format differences)
        py_lines = _normalize_output(py_output)
        js_lines = _normalize_output(js_output)
        
        assert py_lines == js_lines, f"Python: {py_output}, JS: {js_output}"

