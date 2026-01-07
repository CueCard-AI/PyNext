"""
PyNext Client - Runtime Type Checking

WHAT THIS FILE DOES:
Provides @typed decorator for runtime type checking of client functions.
Validates function arguments and return values at runtime in development mode.

WHY THIS EXISTS:
Type checking catches bugs early. Runtime validation ensures types are correct
even when compile-time checking isn't available or when dealing with dynamic data.

HOW IT WORKS:
- @typed decorator wraps functions with type validation
- In dev mode: Emits runtime checks using __py.type_check.validate()
- In production: Stripped by transpiler (no-op)
- Uses enable_type_checking() to globally enable/disable

WHO USES THIS:
- Client functions that need type validation
- Functions with complex type signatures
- Functions that receive data from external sources

WHEN TO USE:
- Client functions: @typed @client
- Functions with type hints: @typed
- When you want runtime safety without TypeScript

EXAMPLES:
    from pynext.client import client, typed
    
    @typed
    @client
    def greet(name: str, times: int = 1) -> str:
        return (f"Hello, {name}! " * times).strip()
    
    # In dev mode: Validates types at runtime
    greet("John", 2)  # OK
    greet("John", "2")  # TypeError: times must be int, got str
"""

from __future__ import annotations

import functools
import inspect
from typing import Any, Callable, Dict, Optional, Union, get_type_hints, get_origin, get_args

# Global flag for type checking
_TYPE_CHECKING_ENABLED = True


def enable_type_checking(enable: bool = True) -> None:
    """
    Enable or disable runtime type checking globally.
    
    Args:
        enable: If True, enable type checking; if False, disable
        
    Example:
        enable_type_checking(False)  # Disable type checking
        enable_type_checking(True)   # Re-enable
    """
    global _TYPE_CHECKING_ENABLED
    _TYPE_CHECKING_ENABLED = enable


def is_type_checking_enabled() -> bool:
    """Check if type checking is currently enabled."""
    return _TYPE_CHECKING_ENABLED


def _validate_type(value: Any, expected_type: Any) -> bool:
    """
    Validate that a value matches the expected type.
    
    Args:
        value: Value to validate
        expected_type: Expected type (from type hints)
        
    Returns:
        True if value matches type, False otherwise
    """
    # Handle None
    if expected_type is None or expected_type is type(None):
        return value is None
    
    # Handle Optional[T] (Union[T, None])
    origin = get_origin(expected_type)
    if origin is Union:
        args = get_args(expected_type)
        if type(None) in args:
            # Optional type - check if None or other type
            non_none_args = [arg for arg in args if arg is not type(None)]
            if value is None:
                return True
            if non_none_args:
                return any(_validate_type(value, arg) for arg in non_none_args)
    
    # Handle Union types
    if origin is Union:
        args = get_args(expected_type)
        return any(_validate_type(value, arg) for arg in args)
    
    # Handle List[T], Dict[K, V], Set[T]
    if origin is list:
        if not isinstance(value, list):
            return False
        args = get_args(expected_type)
        if args:
            item_type = args[0]
            return all(_validate_type(item, item_type) for item in value)
        return True
    
    if origin is dict:
        if not isinstance(value, dict):
            return False
        args = get_args(expected_type)
        if len(args) >= 2:
            key_type, value_type = args[0], args[1]
            return all(
                _validate_type(k, key_type) and _validate_type(v, value_type)
                for k, v in value.items()
            )
        return True
    
    if origin is set:
        if not isinstance(value, set):
            return False
        args = get_args(expected_type)
        if args:
            item_type = args[0]
            return all(_validate_type(item, item_type) for item in value)
        return True
    
    # Handle tuple
    if origin is tuple:
        if not isinstance(value, tuple):
            return False
        args = get_args(expected_type)
        if args:
            if len(args) == 2 and args[1] is ...:
                # Tuple[T, ...]
                item_type = args[0]
                return all(_validate_type(item, item_type) for item in value)
            else:
                # Tuple[T1, T2, ...]
                if len(value) != len(args):
                    return False
                return all(_validate_type(v, t) for v, t in zip(value, args))
        return True
    
    # Handle Callable
    if origin is Callable or expected_type is Callable:
        return callable(value)
    
    # Handle basic types
    if expected_type is Any:
        return True
    
    # Handle class types
    if isinstance(expected_type, type):
        return isinstance(value, expected_type)
    
    # Handle string type names (for forward references)
    if isinstance(expected_type, str):
        # Would need to resolve forward reference
        # For now, just return True
        return True
    
    return False


def typed(func: Optional[Callable] = None, *, enabled: bool = True) -> Callable:
    """
    Decorator for runtime type checking.
    
    Validates function arguments and return values at runtime.
    In production builds, this decorator is stripped by the transpiler.
    
    Args:
        func: Function to wrap
        enabled: Whether type checking is enabled for this function
        
    Returns:
        Wrapped function with type checking
        
    Example:
        @typed
        @client
        def calculate_total(items: list[dict], tax_rate: float = 0.1) -> float:
            subtotal = sum(item["price"] * item["quantity"] for item in items)
            return subtotal * (1 + tax_rate)
    """
    def decorator(fn: Callable) -> Callable:
        # Get type hints
        try:
            hints = get_type_hints(fn, include_extras=True)
        except Exception:
            # If we can't get hints, just return the function
            return fn
        
        sig = inspect.signature(fn)
        
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            # Check if type checking is enabled
            if not _TYPE_CHECKING_ENABLED or not enabled:
                return fn(*args, **kwargs)
            
            # Bind arguments
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            
            # Validate arguments
            for param_name, param in sig.parameters.items():
                if param_name in bound.arguments:
                    value = bound.arguments[param_name]
                    param_type = hints.get(param_name)
                    
                    if param_type is not None:
                        # Special handling for **kwargs
                        if param.kind == inspect.Parameter.VAR_KEYWORD:
                            # param_type should be something like Dict[str, int]
                            # Extract the value type from the dict annotation
                            origin = get_origin(param_type)
                            if origin is dict:
                                args = get_args(param_type)
                                if len(args) >= 2:
                                    # args[0] is key type (usually str), args[1] is value type
                                    value_type = args[1]
                                    for kwarg_value in value.values():
                                        if not _validate_type(kwarg_value, value_type):
                                            raise TypeError(
                                                f"Keyword argument value must be {value_type.__name__}, "
                                                f"got {type(kwarg_value).__name__}"
                                            )
                        else:
                            # Normal parameter validation
                            if not _validate_type(value, param_type):
                                raise TypeError(
                                    f"{param_name} must be {param_type}, got {type(value).__name__}"
                                )
            
            # Call function
            result = fn(*args, **kwargs)
            
            # Validate return type
            return_type = hints.get("return")
            if return_type is not None and return_type is not inspect.Signature.empty:
                if not _validate_type(result, return_type):
                    raise TypeError(
                        f"Return value must be {return_type}, got {type(result).__name__}"
                    )
            
            return result
        
        # Mark as typed for transpiler
        wrapper._pynext_typed = True
        wrapper._pynext_type_check_enabled = enabled
        
        return wrapper
    
    if func is None:
        return decorator
    else:
        return decorator(func)

