"""
Tests for Phase 33.5: asyncio.sleep Transpilation

Tests the transpilation of Python's asyncio.sleep() to JavaScript's __py.sleep().

Run with: pytest tests/unit/transpiler/test_335_asyncio_sleep.py -v
"""

import pytest
from pynext.transpiler import transpile


class TestAsyncioSleepBasic:
    """Tests for basic asyncio.sleep transpilation."""
    
    def test_asyncio_sleep_basic(self):
        """Test basic asyncio.sleep transpilation."""
        code = '''
import asyncio

async def wait():
    await asyncio.sleep(1)
'''
        result = transpile(code)
        assert "__py.sleep" in result
        assert "1" in result
    
    def test_asyncio_sleep_with_float(self):
        """Test asyncio.sleep with fractional seconds."""
        code = '''
import asyncio

async def wait():
    await asyncio.sleep(0.5)
'''
        result = transpile(code)
        assert "__py.sleep" in result
        assert "0.5" in result
    
    def test_asyncio_sleep_with_zero(self):
        """Test asyncio.sleep(0) for yielding to event loop."""
        code = '''
import asyncio

async def yield_control():
    await asyncio.sleep(0)
'''
        result = transpile(code)
        assert "__py.sleep(0)" in result or "__py.sleep( 0)" in result
    
    def test_asyncio_sleep_with_variable(self):
        """Test asyncio.sleep with a variable."""
        code = '''
import asyncio

async def wait(seconds):
    await asyncio.sleep(seconds)
'''
        result = transpile(code)
        assert "__py.sleep" in result
        assert "seconds" in result
    
    def test_asyncio_sleep_with_expression(self):
        """Test asyncio.sleep with an expression."""
        code = '''
import asyncio

async def wait():
    await asyncio.sleep(2 * 0.5)
'''
        result = transpile(code)
        assert "__py.sleep" in result


class TestAsyncioSleepImportPatterns:
    """Tests for different import patterns of asyncio.sleep."""
    
    def test_import_asyncio_module(self):
        """Test with 'import asyncio' pattern."""
        code = '''
import asyncio

async def wait():
    await asyncio.sleep(1)
'''
        result = transpile(code)
        assert "__py.sleep" in result
    
    def test_from_asyncio_import_sleep(self):
        """Test with 'from asyncio import sleep' pattern."""
        code = '''
from asyncio import sleep

async def wait():
    await sleep(1)
'''
        result = transpile(code)
        # Either direct __py.sleep or via __py.asyncio.sleep is valid
        assert "__py.sleep" in result or "__py.asyncio.sleep" in result
    
    def test_from_asyncio_import_sleep_alias(self):
        """Test with aliased import."""
        code = '''
from asyncio import sleep as async_sleep

async def wait():
    await async_sleep(1)
'''
        result = transpile(code)
        # The alias should be tracked - either direct __py.sleep or via __py.asyncio.sleep
        assert "__py.sleep" in result or "__py.asyncio.sleep" in result


class TestAsyncioSleepInContext:
    """Tests for asyncio.sleep in various contexts."""
    
    def test_asyncio_sleep_in_loop(self):
        """Test asyncio.sleep in a loop."""
        code = '''
import asyncio

async def poll():
    for i in range(10):
        await asyncio.sleep(1)
        check_status()
'''
        result = transpile(code)
        assert "__py.sleep" in result
    
    def test_asyncio_sleep_multiple_calls(self):
        """Test multiple asyncio.sleep calls."""
        code = '''
import asyncio

async def steps():
    await asyncio.sleep(1)
    step1()
    await asyncio.sleep(2)
    step2()
    await asyncio.sleep(3)
'''
        result = transpile(code)
        assert result.count("__py.sleep") == 3
    
    def test_asyncio_sleep_in_try_except(self):
        """Test asyncio.sleep in try/except block."""
        code = '''
import asyncio

async def safe_wait():
    try:
        await asyncio.sleep(1)
    except Exception:
        pass
'''
        result = transpile(code)
        assert "__py.sleep" in result
    
    def test_asyncio_sleep_in_nested_async(self):
        """Test asyncio.sleep in nested async function."""
        code = '''
import asyncio

async def outer():
    async def inner():
        await asyncio.sleep(0.1)
    await inner()
'''
        result = transpile(code)
        assert "__py.sleep" in result


class TestAsyncioSleepWithGather:
    """Tests for asyncio.sleep used with asyncio.gather."""
    
    def test_asyncio_sleep_with_gather(self):
        """Test asyncio.sleep combined with asyncio.gather."""
        code = '''
import asyncio

async def main():
    await asyncio.gather(
        asyncio.sleep(1),
        asyncio.sleep(2)
    )
'''
        result = transpile(code)
        assert "__py.sleep" in result
        assert "Promise.all" in result
    
    def test_asyncio_sleep_parallel(self):
        """Test multiple parallel sleeps."""
        code = '''
import asyncio

async def parallel():
    tasks = [asyncio.sleep(i) for i in range(5)]
    await asyncio.gather(*tasks)
'''
        result = transpile(code)
        assert "__py.sleep" in result


class TestAsyncioSleepEdgeCases:
    """Tests for edge cases in asyncio.sleep handling."""
    
    def test_asyncio_sleep_no_args(self):
        """Test asyncio.sleep() with no arguments defaults to 0."""
        code = '''
import asyncio

async def wait():
    await asyncio.sleep()
'''
        result = transpile(code)
        assert "__py.sleep(0)" in result or "__py.sleep()" in result
    
    def test_asyncio_sleep_named_argument(self):
        """Test asyncio.sleep with named argument."""
        code = '''
import asyncio

async def wait():
    await asyncio.sleep(delay=1)
'''
        result = transpile(code)
        # Named argument should still work
        assert "__py.sleep" in result
    
    def test_asyncio_sleep_large_value(self):
        """Test asyncio.sleep with large value."""
        code = '''
import asyncio

async def long_wait():
    await asyncio.sleep(3600)  # 1 hour
'''
        result = transpile(code)
        assert "__py.sleep" in result
        assert "3600" in result

