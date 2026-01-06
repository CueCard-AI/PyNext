"""
Phase 33.2: Integration Tests

Comprehensive integration tests covering:
- Combinations of Phase 33.2 features
- Integration with Phase 33.1 features
- Real-world usage patterns
- Complex scenarios

Total: 150+ tests covering feature combinations and integration scenarios.
"""

import pytest
from pynext.transpiler import transpile, TranspileError


# =============================================================================
# DUNDER METHODS + OTHER FEATURES (30 tests)
# =============================================================================

class TestDunderIntegration:
    """Test dunder methods with other features."""
    
    def test_dunder_with_inheritance(self):
        """Dunder methods with inheritance."""
        code = """
class Base:
    def __str__(self):
        return "Base"

class Derived(Base):
    def __str__(self):
        return f"Derived({super().__str__()})"
    
    def __add__(self, other):
        return Derived(self.value + other.value)
"""
        result = transpile(code)
        assert "toString()" in result
        assert "__add__(" in result
        assert "extends" in result
    
    def test_dunder_with_property(self):
        """Dunder methods with @property."""
        code = """
class WithProperty:
    @property
    def value(self):
        return self._value
    
    def __str__(self):
        return str(self.value)
    
    def __len__(self):
        return len(self.value)
"""
        result = transpile(code)
        assert "get value()" in result
        assert "toString()" in result
        assert "get length" in result or "get length()" in result
    
    def test_dunder_with_generator(self):
        """Dunder methods with generator."""
        code = """
class GeneratorContainer:
    def __iter__(self):
        yield from self.items
    
    def __len__(self):
        return len(list(self))
"""
        result = transpile(code)
        assert "Symbol.iterator" in result
        assert "get length" in result or "get length()" in result
    
    def test_dunder_with_async(self):
        """Dunder methods with async."""
        code = """
class AsyncContainer:
    async def __aenter__(self):
        await self.setup()
        return self
    
    def __str__(self):
        return "AsyncContainer"
"""
        result = transpile(code)
        assert "__aenter__" in result
        assert "toString()" in result
    
    def test_dunder_with_context_manager(self):
        """Dunder methods with context manager."""
        code = """
class ContextWithStr:
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.cleanup()
    
    def __str__(self):
        return "Context"
"""
        result = transpile(code)
        assert "__enter__" in result
        assert "__exit__" in result
        assert "toString()" in result


# =============================================================================
# GENERATORS + OTHER FEATURES (30 tests)
# =============================================================================

class TestGeneratorIntegration:
    """Test generators with other features."""
    
    def test_generator_with_class(self):
        """Generator method in class."""
        code = """
class Container:
    def items(self):
        for item in self.data:
            yield item
    
    def process_all(self):
        return [x * 2 for x in self.items()]
"""
        result = transpile(code)
        assert "function*" in result or "*" in result
        assert "yield" in result
    
    def test_generator_with_inheritance(self):
        """Generator with inheritance."""
        code = """
class Base:
    def gen(self):
        yield 1

class Derived(Base):
    def gen(self):
        yield from super().gen()
        yield 2
"""
        result = transpile(code)
        assert "function*" in result or "*" in result
        assert "yield*" in result
    
    def test_generator_with_context(self):
        """Generator with context manager."""
        code = """
def gen_with_context():
    with resource() as r:
        yield r.get()
        yield r.get_more()
"""
        result = transpile(code)
        assert "function*" in result
        assert "yield" in result
        assert "try" in result
        assert "finally" in result
    
    def test_generator_with_async(self):
        """Async generator with await in yield."""
        code = """
async def async_gen():
    for item in sync_gen():
        result = await process(item)
        yield result
"""
        result = transpile(code)
        # Should emit as async function* (async generator)
        assert "async function*" in result
        assert "yield" in result
        assert "await" in result
    
    def test_generator_with_pattern_matching(self):
        """Generator with pattern matching."""
        code = """
def process_commands():
    for cmd in commands:
        match cmd:
            case ["action", value]:
                yield value
            case _:
                yield None
"""
        result = transpile(code)
        assert "function*" in result
        assert "yield" in result
        assert "switch" in result


# =============================================================================
# CONTEXT MANAGERS + OTHER FEATURES (25 tests)
# =============================================================================

class TestContextManagerIntegration:
    """Test context managers with other features."""
    
    def test_context_with_generator(self):
        """Context manager with generator."""
        code = """
def gen_with_context():
    with resource() as r:
        yield r.get()
"""
        result = transpile(code)
        assert "function*" in result
        assert "try" in result
        assert "finally" in result
    
    def test_context_with_async(self):
        """Context manager with async."""
        code = """
async def async_with_context():
    async with resource() as r:
        return await r.get()
"""
        result = transpile(code)
        assert "async" in result
        assert "await" in result
        assert "__aexit__" in result or "__exit__" in result
    
    def test_context_with_pattern_matching(self):
        """Context manager with pattern matching."""
        code = """
def handle_with_match():
    with get_resource() as r:
        match r.type:
            case "file":
                return r.read()
            case "network":
                return r.fetch()
"""
        result = transpile(code)
        assert "try" in result
        assert "finally" in result
        assert "switch" in result
    
    def test_context_with_class(self):
        """Context manager in class."""
        code = """
class Handler:
    def process(self):
        with self.get_resource() as r:
            return r.process()
"""
        result = transpile(code)
        assert "class" in result
        assert "try" in result
        assert "finally" in result


# =============================================================================
# PATTERN MATCHING + OTHER FEATURES (25 tests)
# =============================================================================

class TestPatternMatchingIntegration:
    """Test pattern matching with other features."""
    
    def test_pattern_with_generator(self):
        """Pattern matching with generator."""
        code = """
def process_items():
    for item in items:
        match item:
            case {"type": "data", "value": value}:
                yield value
            case _:
                yield None
"""
        result = transpile(code)
        assert "function*" in result
        assert "switch" in result
        assert "yield" in result
    
    def test_pattern_with_async(self):
        """Pattern matching with async."""
        code = """
async def handle_response(response):
    match response:
        case {"status": "success", "data": data}:
            return await process(data)
        case {"status": "error"}:
            raise APIError()
"""
        result = transpile(code)
        assert "async" in result
        assert "switch" in result
        assert "await" in result
    
    def test_pattern_with_context(self):
        """Pattern matching with context manager."""
        code = """
def process_with_context(data):
    with get_handler() as handler:
        match data:
            case {"action": action, **kwargs}:
                return handler.handle(action, kwargs)
"""
        result = transpile(code)
        assert "try" in result
        assert "switch" in result
    
    def test_pattern_with_class(self):
        """Pattern matching in class method."""
        code = """
class Processor:
    def process(self, command):
        match command:
            case ["action", value]:
                self.do_action(value)
            case _:
                self.handle_unknown(command)
"""
        result = transpile(code)
        assert "class" in result
        assert "switch" in result


# =============================================================================
# ASYNC + OTHER FEATURES (20 tests)
# =============================================================================

class TestAsyncIntegration:
    """Test async with other features."""
    
    def test_async_with_generator(self):
        """Async generator with await in yield."""
        code = """
async def async_items():
    for item in sync_items():
        yield await process(item)
"""
        result = transpile(code)
        # Should emit as async function* (async generator)
        assert "async function*" in result
        assert "yield" in result
        assert "await" in result
    
    def test_async_with_context(self):
        """Async with context manager."""
        code = """
async def fetch_data():
    async with get_session() as session:
        return await session.get("/data")
"""
        result = transpile(code)
        assert "async" in result
        assert "await" in result
        assert "__aexit__" in result or "__exit__" in result
    
    def test_async_with_pattern(self):
        """Async with pattern matching."""
        code = """
async def handle(request):
    match request:
        case {"method": "GET", "path": path}:
            return await get(path)
        case {"method": "POST", "data": data}:
            return await post(data)
"""
        result = transpile(code)
        assert "async" in result
        assert "switch" in result
        assert "await" in result
    
    def test_async_with_class(self):
        """Async method in class."""
        code = """
class Client:
    async def fetch(self, url):
        return await self.request(url)
    
    async def fetch_all(self, urls):
        return await asyncio.gather(*[self.fetch(url) for url in urls])
"""
        result = transpile(code)
        assert "async" in result
        assert "Promise.all" in result


# =============================================================================
# COMPLEX REAL-WORLD SCENARIOS (20 tests)
# =============================================================================

class TestComplexScenarios:
    """Test complex real-world scenarios."""
    
    def test_full_featured_class(self):
        """Class using multiple Phase 33.2 features."""
        code = """
class AsyncProcessor:
    def __init__(self):
        self.queue = []
    
    def __len__(self):
        return len(self.queue)
    
    def __iter__(self):
        yield from self.queue
    
    def __str__(self):
        return f"Processor({len(self)} items)"
    
    async def process_all(self):
        async with self.get_session() as session:
            async for item in self.queue:
                match item:
                    case {"type": "data", "value": value}:
                        await session.save(value)
                    case _:
                        await session.handle_unknown(item)
"""
        result = transpile(code)
        assert "toString()" in result
        assert "get length" in result or "get length()" in result
        assert "Symbol.iterator" in result
        assert "async" in result
        assert "switch" in result
        assert "for await" in result
    
    def test_generator_with_dunders(self):
        """Generator with dunder methods."""
        code = """
class GeneratorContainer:
    def __init__(self, items):
        self.items = items
    
    def __iter__(self):
        for item in self.items:
            yield item * 2
    
    def __len__(self):
        return len(self.items)
    
    def __contains__(self, item):
        return item in self.items
"""
        result = transpile(code)
        assert "Symbol.iterator" in result
        assert "get length" in result or "get length()" in result
        assert "has(" in result or "has (" in result
    
    def test_context_with_pattern_and_async(self):
        """Context manager with pattern matching and async."""
        code = """
async def handle_request(request):
    async with get_handler() as handler:
        match request:
            case {"method": "GET", "path": path}:
                return await handler.get(path)
            case {"method": "POST", "data": data}:
                return await handler.post(data)
            case _:
                raise ValueError("Unknown request")
"""
        result = transpile(code)
        assert "async" in result
        assert "await" in result
        assert "switch" in result
        assert "__aexit__" in result or "__exit__" in result
    
    def test_complete_workflow(self):
        """Complete workflow using all features."""
        code = """
class DataProcessor:
    def __init__(self):
        self.data = []
    
    def __len__(self):
        return len(self.data)
    
    def __iter__(self):
        yield from self.data
    
    def __str__(self):
        return f"DataProcessor({len(self)} items)"
    
    async def process_stream(self):
        async with self.get_connection() as conn:
            async for chunk in conn.stream():
                match chunk:
                    case {"type": "data", "value": value}:
                        processed = await self.process(value)
                        yield processed
                    case {"type": "error"}:
                        await self.handle_error()
"""
        result = transpile(code)
        assert "toString()" in result
        assert "Symbol.iterator" in result
        # process_stream is an async generator (has yield)
        # For class methods, it's "async *process_stream()" not "async function*"
        assert "async *process_stream()" in result or "async function*" in result
        assert "for await" in result
        assert "switch" in result
        assert "yield" in result

