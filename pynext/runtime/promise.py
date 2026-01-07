"""
PyNext Runtime - Promise Utilities (Python implementation)

This module provides Promise utility functions for Python async code.
The JavaScript equivalent is in promise.js.

These utilities wrap asyncio functionality to provide a Promise-like API
that mirrors the JavaScript Promise utilities.
"""

import asyncio
from typing import Any, Callable, List, TypeVar, Union, Tuple

T = TypeVar('T')


class AggregateError(Exception):
    """Error for Promise.any when all promises reject."""
    
    def __init__(self, errors: List[Exception], message: str = "All promises were rejected"):
        super().__init__(message)
        self.errors = errors


async def Promise_all(promises: List) -> List:
    """
    Wait for all promises (awaitables) to resolve.
    
    Returns list of results in the same order as input.
    Raises if any promise rejects.
    """
    if not promises:
        return []
    
    return await asyncio.gather(*promises)


async def Promise_allSettled(promises: List) -> List[dict]:
    """
    Wait for all promises to settle (resolve or reject).
    
    Returns list of result dicts with 'status' and 'value' or 'reason'.
    """
    if not promises:
        return []
    
    results = []
    for coro in promises:
        try:
            value = await coro
            results.append({"status": "fulfilled", "value": value})
        except Exception as e:
            results.append({"status": "rejected", "reason": e})
    
    return results


async def Promise_race(promises: List) -> Any:
    """
    Return the result of the first promise to complete.
    
    If first to complete rejects, the rejection is propagated.
    """
    if not promises:
        # Wait forever if empty (mirrors JS behavior)
        await asyncio.sleep(float('inf'))
    
    done, pending = await asyncio.wait(
        [asyncio.ensure_future(p) for p in promises],
        return_when=asyncio.FIRST_COMPLETED
    )
    
    # Cancel pending tasks
    for task in pending:
        task.cancel()
    
    # Return result of first completed
    first = done.pop()
    return first.result()


async def Promise_any(promises: List) -> Any:
    """
    Return the result of the first promise to successfully resolve.
    
    Ignores rejections until all reject, then raises AggregateError.
    """
    if not promises:
        raise AggregateError([], "No promises provided")
    
    errors = []
    tasks = [asyncio.ensure_future(p) for p in promises]
    pending = set(tasks)
    
    while pending:
        done, pending = await asyncio.wait(
            pending,
            return_when=asyncio.FIRST_COMPLETED
        )
        
        for task in done:
            try:
                result = task.result()
                # Cancel remaining tasks
                for p in pending:
                    p.cancel()
                return result
            except Exception as e:
                errors.append(e)
    
    raise AggregateError(errors)


def Promise_withResolvers() -> Tuple[asyncio.Future, Callable, Callable]:
    """
    Create a promise with external resolve/reject functions.
    
    Returns (promise, resolve, reject) tuple.
    """
    loop = asyncio.get_event_loop()
    future = loop.create_future()
    
    def resolve(value):
        if not future.done():
            future.set_result(value)
    
    def reject(error):
        if not future.done():
            future.set_exception(error)
    
    return future, resolve, reject


__all__ = [
    'AggregateError',
    'Promise_all',
    'Promise_allSettled',
    'Promise_race',
    'Promise_any',
    'Promise_withResolvers',
]

