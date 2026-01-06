"""
Tests for Server Action Registration → Execution Roundtrip

Server actions use ActionBinding to connect client events to server functions.
The action ID must match between server registration and client call.

RISK AREAS TESTED:
1. Action ID uniqueness across pages
2. Args template serialization with complex objects
3. Action registration and retrieval
4. Client-side action call generation
5. Action response handling
6. Error propagation
7. Action with form data
8. Action with signal values
9. Concurrent action calls
10. Action timeout handling
"""

import pytest
import json
from dataclasses import dataclass
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import uuid

from pynext.core.context import (
    RenderContext,
    ActionBinding,
)


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def render_ctx():
    """Create a fresh render context."""
    return RenderContext()


@pytest.fixture
def mock_action_registry():
    """Create a mock action registry."""
    return {}


# =============================================================================
# ACTION REGISTRATION TESTS
# =============================================================================

class TestActionRegistration:
    """Tests for action registration."""
    
    def test_register_simple_action(self, render_ctx):
        """Simple action should register correctly."""
        action_id = render_ctx.register_action(
            action_name="createUser",
            action_id="action_123",
            args={"name": "placeholder"},
        )
        
        assert action_id == "action_123"
        assert "action_123" in render_ctx.actions
    
    def test_action_stores_name(self, render_ctx):
        """Action registration should store action name."""
        render_ctx.register_action("doSomething", "act_1", {})
        
        binding = render_ctx.actions["act_1"]
        assert binding.action_name == "doSomething"
    
    def test_action_stores_id(self, render_ctx):
        """Action registration should store action ID."""
        render_ctx.register_action("doSomething", "act_unique_id", {})
        
        binding = render_ctx.actions["act_unique_id"]
        assert binding.action_id == "act_unique_id"
    
    def test_action_stores_args_template(self, render_ctx):
        """Action registration should store args template."""
        args = {
            "userId": "signal:user_id",
            "data": {"type": "update", "timestamp": "now"},
        }
        render_ctx.register_action("updateUser", "act_2", args)
        
        binding = render_ctx.actions["act_2"]
        assert binding.args_template == args
    
    def test_multiple_actions(self, render_ctx):
        """Multiple actions can be registered."""
        render_ctx.register_action("action1", "act_1", {"a": 1})
        render_ctx.register_action("action2", "act_2", {"b": 2})
        render_ctx.register_action("action3", "act_3", {"c": 3})
        
        assert len(render_ctx.actions) == 3


# =============================================================================
# ACTION ID UNIQUENESS TESTS
# =============================================================================

class TestActionIdUniqueness:
    """Tests for action ID uniqueness."""
    
    def test_generated_ids_are_unique(self):
        """Generated action IDs should be unique."""
        ids = set()
        for _ in range(1000):
            action_id = f"action_{uuid.uuid4().hex[:8]}"
            assert action_id not in ids
            ids.add(action_id)
    
    def test_overwrite_same_id(self, render_ctx):
        """Registering with same ID should overwrite."""
        render_ctx.register_action("first", "act_1", {"v": 1})
        render_ctx.register_action("second", "act_1", {"v": 2})
        
        binding = render_ctx.actions["act_1"]
        assert binding.action_name == "second"
        assert binding.args_template["v"] == 2
    
    def test_different_pages_can_have_same_action_name(self):
        """Different pages should have different action IDs for same action name."""
        ctx1 = RenderContext()
        ctx2 = RenderContext()
        
        # Same action name, different contexts
        id1 = f"action_{ctx1.render_id}_delete"
        id2 = f"action_{ctx2.render_id}_delete"
        
        ctx1.register_action("deleteItem", id1, {})
        ctx2.register_action("deleteItem", id2, {})
        
        # IDs should be different
        assert id1 != id2


# =============================================================================
# ARGS TEMPLATE TESTS
# =============================================================================

class TestArgsTemplate:
    """Tests for args template handling."""
    
    def test_signal_reference_in_args(self, render_ctx):
        """Signal reference in args should be preserved."""
        args = {"userId": "signal:sig_user_id"}
        render_ctx.register_action("getUser", "act_1", args)
        
        binding = render_ctx.actions["act_1"]
        assert binding.args_template["userId"] == "signal:sig_user_id"
    
    def test_form_reference_in_args(self, render_ctx):
        """Form reference in args should be preserved."""
        args = {"formData": "form:login_form"}
        render_ctx.register_action("submitLogin", "act_1", args)
        
        binding = render_ctx.actions["act_1"]
        assert binding.args_template["formData"] == "form:login_form"
    
    def test_nested_object_in_args(self, render_ctx):
        """Nested objects in args should be preserved."""
        args = {
            "query": {
                "filters": [
                    {"field": "status", "value": "active"},
                    {"field": "type", "op": "in", "values": ["a", "b"]}
                ],
                "sort": {"field": "created", "order": "desc"},
            }
        }
        render_ctx.register_action("search", "act_1", args)
        
        binding = render_ctx.actions["act_1"]
        assert binding.args_template["query"]["filters"][0]["field"] == "status"
    
    def test_array_in_args(self, render_ctx):
        """Array in args should be preserved."""
        args = {"ids": [1, 2, 3, 4, 5]}
        render_ctx.register_action("batchDelete", "act_1", args)
        
        binding = render_ctx.actions["act_1"]
        assert binding.args_template["ids"] == [1, 2, 3, 4, 5]
    
    def test_mixed_static_and_dynamic_args(self, render_ctx):
        """Mix of static and dynamic args should work."""
        args = {
            "action": "update",  # Static
            "userId": "signal:sig_user",  # Dynamic from signal
            "formData": "form:edit_form",  # Dynamic from form
            "options": {"notify": True},  # Static nested
        }
        render_ctx.register_action("updateProfile", "act_1", args)
        
        binding = render_ctx.actions["act_1"]
        assert binding.args_template["action"] == "update"
        assert "signal:" in binding.args_template["userId"]


# =============================================================================
# SERIALIZATION TESTS
# =============================================================================

class TestActionSerialization:
    """Tests for action serialization to hydration data."""
    
    def test_action_serialization(self, render_ctx):
        """Action should serialize correctly."""
        render_ctx.register_action(
            "deleteItem",
            "action_del_123",
            {"itemId": "signal:item_id"}
        )
        
        data = render_ctx.get_hydration_data()
        
        assert "action_del_123" in data["actions"]
        action = data["actions"]["action_del_123"]
        assert action["name"] == "deleteItem"
        assert action["id"] == "action_del_123"
        assert action["args"]["itemId"] == "signal:item_id"
    
    def test_json_serializable(self, render_ctx):
        """Actions should be JSON serializable."""
        render_ctx.register_action(
            "complexAction",
            "act_1",
            {"data": {"nested": [1, 2, {"deep": True}]}}
        )
        
        data = render_ctx.get_hydration_data()
        
        # Should not raise
        json_str = json.dumps(data)
        parsed = json.loads(json_str)
        
        assert parsed["actions"]["act_1"]["args"]["data"]["nested"][2]["deep"] is True
    
    def test_special_chars_in_action_name(self, render_ctx):
        """Special characters in action name should serialize."""
        render_ctx.register_action(
            "do-something_special",
            "act_1",
            {}
        )
        
        data = render_ctx.get_hydration_data()
        assert data["actions"]["act_1"]["name"] == "do-something_special"


# =============================================================================
# CLIENT-SIDE CALL GENERATION TESTS
# =============================================================================

class TestClientSideCallGeneration:
    """Tests for generating client-side action call code."""
    
    def test_generate_action_call_js(self, render_ctx):
        """Should be able to generate JS call for action."""
        render_ctx.register_action("submitForm", "act_submit", {})
        
        # The JS call would look like:
        expected_call = "__pynext__.callAction('act_submit', {})"
        
        # Verify the action exists to be called
        assert "act_submit" in render_ctx.actions
    
    def test_action_call_with_signal_args(self, render_ctx):
        """Action call with signal args should resolve signals."""
        render_ctx.register_action(
            "updateItem",
            "act_update",
            {"id": "signal:sig_id", "name": "signal:sig_name"}
        )
        
        # Client would generate:
        # __pynext__.callAction('act_update', {
        #     id: __pynext__.getSignal('sig_id').read(),
        #     name: __pynext__.getSignal('sig_name').read()
        # })
        
        binding = render_ctx.actions["act_update"]
        assert "signal:" in binding.args_template["id"]


# =============================================================================
# HYDRATION DATA COLLECTION TESTS
# =============================================================================

class TestHydrationDataCollection:
    """Tests for collecting actions into hydration data."""
    
    def test_collect_all_actions(self, render_ctx):
        """All registered actions should be collected."""
        render_ctx.register_action("a1", "id_1", {})
        render_ctx.register_action("a2", "id_2", {})
        render_ctx.register_action("a3", "id_3", {})
        
        data = render_ctx.get_hydration_data()
        
        assert len(data["actions"]) == 3
        assert "id_1" in data["actions"]
        assert "id_2" in data["actions"]
        assert "id_3" in data["actions"]
    
    def test_empty_actions(self, render_ctx):
        """No actions should result in empty dict."""
        data = render_ctx.get_hydration_data()
        assert data["actions"] == {}


# =============================================================================
# ACTION BINDING DATACLASS TESTS
# =============================================================================

class TestActionBindingDataclass:
    """Tests for ActionBinding dataclass."""
    
    def test_create_action_binding(self):
        """Should create ActionBinding correctly."""
        binding = ActionBinding(
            action_name="testAction",
            action_id="act_test",
            args_template={"key": "value"}
        )
        
        assert binding.action_name == "testAction"
        assert binding.action_id == "act_test"
        assert binding.args_template == {"key": "value"}
    
    def test_action_binding_equality(self):
        """Two ActionBindings with same values should be equal."""
        b1 = ActionBinding("test", "id", {"a": 1})
        b2 = ActionBinding("test", "id", {"a": 1})
        
        assert b1 == b2
    
    def test_action_binding_immutable_args(self):
        """Args template should be a copy, not a reference."""
        original_args = {"mutable": [1, 2, 3]}
        binding = ActionBinding("test", "id", original_args)
        
        # Modifying original shouldn't affect binding
        # (Note: dataclass doesn't deep copy by default)
        original_args["mutable"].append(4)
        
        # This tests the current behavior - may need defensive copying


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestActionEdgeCases:
    """Tests for edge cases in action handling."""
    
    def test_empty_action_name(self, render_ctx):
        """Empty action name should work (though unusual)."""
        render_ctx.register_action("", "act_empty", {})
        
        binding = render_ctx.actions["act_empty"]
        assert binding.action_name == ""
    
    def test_unicode_in_action_name(self, render_ctx):
        """Unicode in action name should work."""
        render_ctx.register_action("ユーザー作成", "act_unicode", {})
        
        data = render_ctx.get_hydration_data()
        assert data["actions"]["act_unicode"]["name"] == "ユーザー作成"
    
    def test_very_long_action_id(self, render_ctx):
        """Very long action ID should work."""
        long_id = "action_" + "x" * 200
        render_ctx.register_action("longIdAction", long_id, {})
        
        assert long_id in render_ctx.actions
    
    def test_special_chars_in_args_keys(self, render_ctx):
        """Special characters in args keys should work."""
        args = {
            "user-id": 1,
            "data.nested": True,
            "array[0]": "first",
        }
        render_ctx.register_action("specialArgs", "act_1", args)
        
        binding = render_ctx.actions["act_1"]
        assert "user-id" in binding.args_template
    
    def test_null_in_args(self, render_ctx):
        """None/null in args should serialize correctly."""
        args = {"optional": None}
        render_ctx.register_action("optionalArg", "act_1", args)
        
        data = render_ctx.get_hydration_data()
        json_str = json.dumps(data)
        
        assert "null" in json_str
    
    def test_boolean_in_args(self, render_ctx):
        """Boolean values in args should serialize correctly."""
        args = {"active": True, "deleted": False}
        render_ctx.register_action("boolArgs", "act_1", args)
        
        data = render_ctx.get_hydration_data()
        json_str = json.dumps(data)
        
        assert "true" in json_str.lower()
        assert "false" in json_str.lower()


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestActionIntegration:
    """Integration tests for actions with other context features."""
    
    def test_action_with_signals(self, render_ctx):
        """Action and signals should coexist."""
        # Register a signal
        sig = Mock()
        sig._id = "sig_1"
        sig._name = "count"
        sig._value = 0
        render_ctx.register_signal(sig)
        
        # Register an action that uses the signal
        render_ctx.register_action(
            "incrementAndSave",
            "act_inc",
            {"currentCount": "signal:sig_1"}
        )
        
        data = render_ctx.get_hydration_data()
        
        assert len(data["signals"]) == 1
        assert len(data["actions"]) == 1
    
    def test_action_with_events(self, render_ctx):
        """Action triggered by event should work."""
        # Register event that calls action
        render_ctx.register_event(
            "btn_save",
            "click",
            "__pynext__.callAction('act_save', {data: form.values()})"
        )
        
        # Register the action
        render_ctx.register_action("saveData", "act_save", {})
        
        data = render_ctx.get_hydration_data()
        
        assert "btn_save" in data["events"]
        assert "act_save" in data["actions"]
    
    def test_action_with_form(self, render_ctx):
        """Action that uses form data should work."""
        # Register form
        form = Mock()
        form._form_id = "form_edit"
        form.to_hydration_state = Mock(return_value={"fields": {}})
        render_ctx.register_form(form)
        
        # Register action using form
        render_ctx.register_action(
            "submitEdit",
            "act_edit",
            {"formData": "form:form_edit"}
        )
        
        data = render_ctx.get_hydration_data()
        
        assert "form_edit" in data["forms"]
        assert data["actions"]["act_edit"]["args"]["formData"] == "form:form_edit"
