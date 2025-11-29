"""
PyNext Testing - Async Utilities

Clean async testing without the complexity.
Simple functions that just work with async components.

Example:
    from pynext.testing import render, wait_for, assert_text
    
    async def test_user_profile():
        result = render(UserProfile, user_id=1)
        await wait_for(result, timeout=1.0)
        assert_text(result, "John Doe")

Why Async Testing Matters:
    - Components often fetch data
    - Loading states need testing
    - Race conditions must be caught
    - Error states need verification
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Callable, Optional, TypeVar, Union

from pynext.testing.render import RenderResult


T = TypeVar("T")


# =============================================================================
# Wait Functions
# =============================================================================

async def wait_for(
    result: RenderResult,
    condition: Optional[Callable[[RenderResult], bool]] = None,
    timeout: float = 5.0,
    interval: float = 0.05,
) -> RenderResult:
    """
    Wait for a condition to be true in rendered component.
    
    If no condition is provided, waits for any text content.
    
    Args:
        result: RenderResult from render()
        condition: Function that returns True when condition is met
        timeout: Maximum time to wait in seconds
        interval: Time between checks in seconds
        
    Returns:
        Updated RenderResult
        
    Raises:
        TimeoutError: If condition not met within timeout
        
    Example:
        # Wait for loading to complete
        result = render(DataLoader)
        await wait_for(result, lambda r: "Loading" not in r.text)
        
        # Wait for specific text
        await wait_for(result, lambda r: "Success" in r.text)
    """
    if condition is None:
        # Default: wait for any non-empty content
        condition = lambda r: bool(r.text.strip())
    
    start = time.monotonic()
    last_result = result
    
    while time.monotonic() - start < timeout:
        # Re-render to get latest state
        last_result = result.update()
        
        if condition(last_result):
            return last_result
        
        await asyncio.sleep(interval)
    
    raise TimeoutError(
        f"Condition not met within {timeout}s\n"
        f"Last HTML: {last_result.html[:200]}..."
    )


async def wait_for_element(
    result: RenderResult,
    selector: str,
    timeout: float = 5.0,
    interval: float = 0.05,
) -> RenderResult:
    """
    Wait for an element to appear.
    
    Args:
        result: RenderResult from render()
        selector: CSS selector for element to wait for
        timeout: Maximum time to wait in seconds
        interval: Time between checks in seconds
        
    Returns:
        Updated RenderResult
        
    Example:
        result = render(LazyModal)
        trigger_button.click()
        await wait_for_element(result, ".modal-content")
    """
    return await wait_for(
        result,
        condition=lambda r: r.query_selector(selector) is not None,
        timeout=timeout,
        interval=interval,
    )


async def wait_for_text(
    result: RenderResult,
    text: str,
    timeout: float = 5.0,
    interval: float = 0.05,
) -> RenderResult:
    """
    Wait for specific text to appear.
    
    Args:
        result: RenderResult from render()
        text: Text to wait for
        timeout: Maximum time to wait
        interval: Time between checks
        
    Returns:
        Updated RenderResult
        
    Example:
        result = render(Notification)
        await wait_for_text(result, "Message sent!")
    """
    return await wait_for(
        result,
        condition=lambda r: text in r.text,
        timeout=timeout,
        interval=interval,
    )


async def wait_for_removal(
    result: RenderResult,
    selector: str,
    timeout: float = 5.0,
    interval: float = 0.05,
) -> RenderResult:
    """
    Wait for an element to be removed.
    
    Args:
        result: RenderResult from render()
        selector: CSS selector for element to disappear
        timeout: Maximum time to wait
        interval: Time between checks
        
    Returns:
        Updated RenderResult
        
    Example:
        result = render(Toast)
        # Toast auto-dismisses after 3 seconds
        await wait_for_removal(result, ".toast", timeout=4.0)
    """
    return await wait_for(
        result,
        condition=lambda r: r.query_selector(selector) is None,
        timeout=timeout,
        interval=interval,
    )


# =============================================================================
# Act Function (Batched Updates)
# =============================================================================

async def act(func: Callable[[], T]) -> T:
    """
    Run a function and wait for all pending updates.
    
    Similar to React Testing Library's act(), this ensures
    all state updates are processed before continuing.
    
    Args:
        func: Function to execute (can be sync or async)
        
    Returns:
        Result of the function
        
    Example:
        result = render(Counter)
        
        async def click_button():
            result.signals["count"].set(result.signals["count"]() + 1)
        
        await act(click_button)
        assert_text(result, "Count: 1")
    """
    if asyncio.iscoroutinefunction(func):
        result = await func()
    else:
        result = func()
    
    # Give pending tasks a chance to run
    await asyncio.sleep(0)
    
    return result


# =============================================================================
# Async Fixtures
# =============================================================================

class AsyncRenderContext:
    """
    Context manager for async component testing.
    
    Handles setup and cleanup of async components.
    
    Example:
        async with AsyncRenderContext() as ctx:
            result = ctx.render(DataFetcher, endpoint="/api/users")
            await ctx.wait_for_load()
            assert_text(result, "User list")
    """
    
    def __init__(self):
        self.results: list[RenderResult] = []
        self.cleanup_tasks: list[Callable] = []
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Run cleanup tasks
        for cleanup in self.cleanup_tasks:
            try:
                if asyncio.iscoroutinefunction(cleanup):
                    await cleanup()
                else:
                    cleanup()
            except Exception:
                pass  # Ignore cleanup errors
        return False
    
    def render(self, component, *args, **kwargs) -> RenderResult:
        """Render a component and track it."""
        from pynext.testing.render import render
        result = render(component, *args, **kwargs)
        self.results.append(result)
        return result
    
    async def wait_for_all(self, timeout: float = 5.0) -> None:
        """Wait for all rendered components to be ready."""
        for result in self.results:
            try:
                await wait_for(result, timeout=timeout)
            except TimeoutError:
                pass  # Some components might not have async content
    
    def on_cleanup(self, func: Callable) -> None:
        """Register a cleanup function."""
        self.cleanup_tasks.append(func)


# =============================================================================
# Polling Utilities
# =============================================================================

async def poll_until(
    func: Callable[[], T],
    condition: Callable[[T], bool],
    timeout: float = 5.0,
    interval: float = 0.1,
) -> T:
    """
    Poll a function until condition is met.
    
    Generic polling utility for any async testing scenario.
    
    Args:
        func: Function to call repeatedly
        condition: Function that returns True when done
        timeout: Maximum time to poll
        interval: Time between polls
        
    Returns:
        Last result from func
        
    Example:
        # Wait for API mock to receive request
        result = await poll_until(
            lambda: mock_api.call_count,
            lambda count: count >= 1,
            timeout=2.0
        )
    """
    start = time.monotonic()
    last_result = None
    
    while time.monotonic() - start < timeout:
        if asyncio.iscoroutinefunction(func):
            last_result = await func()
        else:
            last_result = func()
        
        if condition(last_result):
            return last_result
        
        await asyncio.sleep(interval)
    
    raise TimeoutError(
        f"Condition not met within {timeout}s. "
        f"Last result: {last_result}"
    )


async def retry(
    func: Callable[[], T],
    max_attempts: int = 3,
    delay: float = 0.1,
    exceptions: tuple = (Exception,),
) -> T:
    """
    Retry a function on failure.
    
    Useful for flaky async operations in tests.
    
    Args:
        func: Function to retry
        max_attempts: Maximum number of attempts
        delay: Delay between attempts
        exceptions: Exception types to catch and retry
        
    Returns:
        Result of successful function call
        
    Example:
        result = await retry(
            lambda: fetch_data(),
            max_attempts=3,
            delay=0.5
        )
    """
    last_error = None
    
    for attempt in range(max_attempts):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func()
            else:
                return func()
        except exceptions as e:
            last_error = e
            if attempt < max_attempts - 1:
                await asyncio.sleep(delay)
    
    raise last_error


# =============================================================================
# Timeout Utilities
# =============================================================================

async def with_timeout(
    coro,
    timeout: float,
    message: str = "Operation timed out",
) -> Any:
    """
    Run a coroutine with a timeout.
    
    Args:
        coro: Coroutine to run
        timeout: Timeout in seconds
        message: Error message on timeout
        
    Returns:
        Result of the coroutine
        
    Example:
        result = await with_timeout(
            fetch_data(),
            timeout=5.0,
            message="Data fetch timed out"
        )
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        raise TimeoutError(message)


def sync_wait(coro, timeout: float = 5.0):
    """
    Run an async function synchronously.
    
    Useful for running async tests in sync test functions.
    
    Args:
        coro: Coroutine to run
        timeout: Maximum time to wait
        
    Returns:
        Result of the coroutine
        
    Example:
        def test_async_component():
            result = sync_wait(fetch_and_render())
            assert_text(result, "Expected")
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(
            asyncio.wait_for(coro, timeout=timeout)
        )
    finally:
        loop.close()

