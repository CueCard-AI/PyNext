"""
Unit tests for PyNext server actions.

Tests @server_action decorator, action registry, and RPC handling.
"""

import pytest
from pynext.server.actions import (
    server_action,
    ActionRegistry,
    get_registry,
    handle_action_request,
)


class TestServerActionDecorator:
    """Tests for the @server_action decorator."""
    
    def test_decorator_registers_action(self):
        """@server_action registers the function."""
        registry = ActionRegistry()
        
        @server_action
        async def my_action(x: int) -> int:
            return x * 2
        
        # Action should have an ID
        assert hasattr(my_action, '_action_id')
    
    def test_action_has_unique_id(self):
        """Each action gets a unique ID."""
        @server_action
        async def action1():
            pass
        
        @server_action
        async def action2():
            pass
        
        assert action1._action_id != action2._action_id
    
    def test_sync_action(self):
        """Synchronous actions work."""
        @server_action
        def sync_action(a: int, b: int) -> int:
            return a + b
        
        # Should be wrapped but callable
        assert hasattr(sync_action, '_action_id')
    
    def test_async_action(self):
        """Async actions work."""
        @server_action
        async def async_action(x: int) -> int:
            return x * 2
        
        assert hasattr(async_action, '_action_id')


class TestActionRegistry:
    """Tests for ActionRegistry."""
    
    def test_create_registry(self):
        """Registry can be created."""
        registry = ActionRegistry()
        assert registry is not None
    
    def test_register_via_decorator(self):
        """Actions are registered via @server_action decorator."""
        @server_action
        async def my_registered_action():
            return "result"
        
        # Action should be registered in global registry
        registry = get_registry()
        action = registry.get(my_registered_action._action_id)
        
        assert action is not None
    
    def test_get_nonexistent_action(self):
        """Getting nonexistent action returns None."""
        registry = get_registry()
        
        result = registry.get("nonexistent_id_xyz")
        assert result is None
    
    def test_list_actions(self):
        """Registry can list all actions."""
        # Register some actions
        @server_action
        async def list_action1():
            pass
        
        @server_action
        async def list_action2():
            pass
        
        registry = get_registry()
        actions = registry.list_actions()
        
        # Should have at least these actions
        assert len(actions) >= 2


class TestHandleActionRequest:
    """Tests for action request handling."""
    
    @pytest.fixture(autouse=True)
    def setup_actions(self):
        """Set up test actions."""
        @server_action
        async def add(a: int, b: int) -> int:
            return a + b
        
        @server_action
        async def greet(name: str) -> str:
            return f"Hello, {name}!"
        
        @server_action
        async def failing_action():
            raise ValueError("Test error")
        
        self.add_id = add._action_id
        self.greet_id = greet._action_id
        self.failing_id = failing_action._action_id
    
    @pytest.mark.asyncio
    async def test_handle_valid_action(self):
        """Valid action request returns data."""
        request = {
            "actionId": self.add_id,
            "args": {"a": 2, "b": 3}
        }
        
        result = await handle_action_request(request)
        
        assert "data" in result
        assert result["data"] == 5
        assert result.get("error") is None
    
    @pytest.mark.asyncio
    async def test_handle_string_action(self):
        """Action with string argument."""
        request = {
            "actionId": self.greet_id,
            "args": {"name": "Alice"}
        }
        
        result = await handle_action_request(request)
        
        assert result["data"] == "Hello, Alice!"
    
    @pytest.mark.asyncio
    async def test_handle_nonexistent_action(self):
        """Nonexistent action returns error."""
        request = {
            "actionId": "nonexistent_action_id",
            "args": {}
        }
        
        result = await handle_action_request(request)
        
        assert result["data"] is None
        assert result["error"] is not None
        # Error message contains "unknown" or "not found"
        assert "unknown" in result["error"].lower() or "not found" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_handle_failing_action(self):
        """Failing action returns error."""
        request = {
            "actionId": self.failing_id,
            "args": {}
        }
        
        result = await handle_action_request(request)
        
        assert result["data"] is None
        assert result["error"] is not None
        assert "Test error" in result["error"]


class TestActionTyping:
    """Tests for action type handling."""
    
    def test_action_with_type_hints(self):
        """Action with type hints works."""
        @server_action
        async def typed_action(count: int, name: str, active: bool = True) -> dict:
            return {"count": count, "name": name, "active": active}
        
        assert hasattr(typed_action, '_action_id')
    
    def test_action_with_complex_types(self):
        """Action with complex types works."""
        from typing import List, Dict, Optional
        
        @server_action
        async def complex_action(
            items: List[str],
            metadata: Dict[str, int],
            optional: Optional[str] = None
        ) -> dict:
            return {
                "items": items,
                "metadata": metadata,
                "optional": optional
            }
        
        assert hasattr(complex_action, '_action_id')


class TestActionWithPythonPackages:
    """Tests for actions using Python packages."""
    
    @pytest.mark.asyncio
    async def test_action_uses_json(self):
        """Action can use json module."""
        @server_action
        async def json_action(data: dict) -> str:
            import json
            return json.dumps(data)
        
        request = {
            "actionId": json_action._action_id,
            "args": {"data": {"key": "value"}}
        }
        
        result = await handle_action_request(request)
        
        assert result["data"] == '{"key": "value"}'
    
    @pytest.mark.asyncio
    async def test_action_uses_datetime(self):
        """Action can use datetime module."""
        @server_action
        async def date_action() -> str:
            from datetime import datetime
            return datetime.now().strftime("%Y-%m-%d")
        
        request = {
            "actionId": date_action._action_id,
            "args": {}
        }
        
        result = await handle_action_request(request)
        
        assert result["data"] is not None
        assert "-" in result["data"]  # Date format


class TestGlobalRegistry:
    """Tests for the global registry."""
    
    def test_get_global_registry(self):
        """get_registry returns global registry."""
        registry = get_registry()
        
        assert isinstance(registry, ActionRegistry)
    
    def test_global_registry_singleton(self):
        """Global registry is a singleton."""
        registry1 = get_registry()
        registry2 = get_registry()
        
        assert registry1 is registry2

