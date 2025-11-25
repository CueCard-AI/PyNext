"""
Server actions for PyNext.

Provides the @server_action decorator for defining Python functions
that can be called from the client via RPC.
"""

from __future__ import annotations

import asyncio
import functools
import inspect
import json
import uuid
from typing import Any, Callable, Optional, TypeVar, Union

import orjson


T = TypeVar("T")


class ActionRegistry:
    """Registry of all server actions."""
    
    _instance: Optional["ActionRegistry"] = None
    
    def __new__(cls) -> "ActionRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._actions = {}
        return cls._instance
    
    def __init__(self):
        # Only initialize once
        if not hasattr(self, "_initialized"):
            self._actions: dict[str, "ServerAction"] = {}
            self._initialized = True
    
    def register(self, action: "ServerAction") -> None:
        """Register a server action."""
        self._actions[action._action_id] = action
    
    def get(self, action_id: str) -> Optional["ServerAction"]:
        """Get an action by ID."""
        return self._actions.get(action_id)
    
    def get_by_name(self, name: str) -> Optional["ServerAction"]:
        """Get an action by name."""
        for action in self._actions.values():
            if action._action_name == name:
                return action
        return None
    
    async def call(self, action_id: str, args: dict) -> Any:
        """Call an action by ID with given arguments."""
        action = self.get(action_id)
        if not action:
            raise ValueError(f"Unknown action: {action_id}")
        return await action.call(**args)
    
    def list_actions(self) -> list[dict]:
        """List all registered actions."""
        return [
            {
                "id": action._action_id,
                "name": action._action_name,
                "params": list(inspect.signature(action._fn).parameters.keys()),
            }
            for action in self._actions.values()
        ]


# Global registry instance
_registry = ActionRegistry()


class ServerAction:
    """
    A server action that can be called from the client.
    
    Server actions:
    - Execute on the server with full Python access
    - Can use any Python package
    - Are called via JSON-RPC from the client
    - Return JSON-serializable results
    """
    
    _is_server_action = True
    
    def __init__(
        self,
        fn: Callable,
        *,
        name: Optional[str] = None,
        validate: bool = True,
    ):
        self._fn = fn
        self._action_name = name or fn.__name__
        self._action_id = f"action_{uuid.uuid4().hex[:8]}"
        self._validate = validate
        self._is_async = asyncio.iscoroutinefunction(fn)
        
        # Preserve function metadata
        functools.update_wrapper(self, fn)
        
        # Register with global registry
        _registry.register(self)
    
    async def call(self, **kwargs) -> Any:
        """
        Execute the action with the given arguments.
        
        This is called by the RPC handler.
        """
        # Validate arguments if enabled
        if self._validate:
            sig = inspect.signature(self._fn)
            try:
                sig.bind(**kwargs)
            except TypeError as e:
                raise ValueError(f"Invalid arguments: {e}")
        
        # Execute the function
        if self._is_async:
            result = await self._fn(**kwargs)
        else:
            # Run sync function in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: self._fn(**kwargs))
        
        # Ensure result is JSON-serializable
        try:
            orjson.dumps(result)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Action result is not JSON-serializable: {e}")
        
        return result
    
    def __call__(self, *args, **kwargs) -> Any:
        """
        Direct call for server-side usage.
        
        When called from Python (not via RPC), executes directly.
        """
        if self._is_async:
            return self._fn(*args, **kwargs)
        return self._fn(*args, **kwargs)
    
    def get_client_code(self) -> str:
        """Generate JavaScript code for calling this action."""
        return f"__pynext__.callAction('{self._action_id}', event)"
    
    def __repr__(self) -> str:
        return f"ServerAction({self._action_name!r}, id={self._action_id!r})"


def server_action(
    fn: Optional[Callable] = None,
    *,
    name: Optional[str] = None,
    validate: bool = True,
) -> Union[ServerAction, Callable[[Callable], ServerAction]]:
    """
    Decorator to define a server action.
    
    Server actions are Python functions that can be called from the
    client via RPC. They have full access to Python packages and
    the server environment.
    
    Usage:
        @server_action
        async def save_data(data: dict) -> dict:
            # Can use any Python package
            import pandas as pd
            df = pd.DataFrame(data)
            df.to_csv("data.csv")
            return {"saved": True, "rows": len(df)}
    
        # With options:
        @server_action(name="custom_name", validate=True)
        def process_file(path: str) -> dict:
            return {"processed": True}
    """
    def decorator(fn: Callable) -> ServerAction:
        return ServerAction(fn, name=name, validate=validate)
    
    if fn is not None:
        return decorator(fn)
    return decorator


async def handle_action_request(request_data: dict) -> dict:
    """
    Handle an incoming action request.
    
    Expected format:
        {
            "actionId": "action_xxx",
            "args": {...}
        }
    
    Returns:
        {
            "data": <result>,
            "error": null
        }
        or
        {
            "data": null,
            "error": "error message"
        }
    """
    try:
        action_id = request_data.get("actionId")
        args = request_data.get("args", {})
        
        if not action_id:
            return {"data": None, "error": "Missing actionId"}
        
        result = await _registry.call(action_id, args)
        return {"data": result, "error": None}
        
    except ValueError as e:
        return {"data": None, "error": str(e)}
    except Exception as e:
        # Log the full error on server
        import traceback
        traceback.print_exc()
        return {"data": None, "error": f"Server error: {type(e).__name__}"}


def get_registry() -> ActionRegistry:
    """Get the global action registry."""
    return _registry

