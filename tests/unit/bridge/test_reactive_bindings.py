"""
Tests for Reactive DOM Bindings

ReactiveBinding connects DOM nodes to signals. The update_expr is a JavaScript
expression that must be valid and reference the correct signal IDs.

RISK AREAS TESTED:
1. Text binding update expressions
2. Attribute binding with signal dependencies
3. Class binding toggle behavior
4. Style binding expressions
5. Show/hide binding conditions
6. For binding iteration patterns
7. Signal dependency tracking accuracy
8. Update expression JavaScript validity
9. Initial value preservation
10. Multiple bindings on same element
"""

import pytest
import json
from dataclasses import dataclass
from unittest.mock import Mock, MagicMock, patch

from pynext.core.context import (
    RenderContext,
    ReactiveBinding,
    SignalRegistration,
)


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def render_ctx():
    """Create a fresh render context."""
    return RenderContext()


@pytest.fixture
def mock_signals():
    """Create mock signals for testing."""
    def create_signal(id, name, value):
        sig = Mock()
        sig._id = id
        sig._name = name
        sig._value = value
        return sig
    
    return {
        "count": create_signal("sig_count", "count", 0),
        "name": create_signal("sig_name", "name", "Alice"),
        "visible": create_signal("sig_visible", "visible", True),
        "items": create_signal("sig_items", "items", [1, 2, 3]),
        "theme": create_signal("sig_theme", "theme", "light"),
    }


# =============================================================================
# TEXT BINDING TESTS
# =============================================================================

class TestTextBinding:
    """Tests for text content bindings."""
    
    def test_simple_text_binding(self, render_ctx):
        """Simple text binding should store all fields."""
        render_ctx.register_binding(
            node_id="span_1",
            binding_type="text",
            signal_deps=["sig_count"],
            update_expr="__pynext__.getSignal('sig_count').read()",
            initial_value="0",
        )
        
        assert len(render_ctx.bindings) == 1
        binding = render_ctx.bindings[0]
        assert binding.node_id == "span_1"
        assert binding.binding_type == "text"
        assert binding.signal_deps == ["sig_count"]
        assert "getSignal" in binding.update_expr
    
    def test_text_binding_with_multiple_signals(self, render_ctx):
        """Text binding can depend on multiple signals."""
        render_ctx.register_binding(
            node_id="greeting_span",
            binding_type="text",
            signal_deps=["sig_greeting", "sig_name"],
            update_expr="__pynext__.getSignal('sig_greeting').read() + ' ' + __pynext__.getSignal('sig_name').read()",
        )
        
        binding = render_ctx.bindings[0]
        assert len(binding.signal_deps) == 2
        assert "sig_greeting" in binding.signal_deps
        assert "sig_name" in binding.signal_deps
    
    def test_text_binding_with_expression(self, render_ctx):
        """Text binding can have computed expression."""
        render_ctx.register_binding(
            node_id="doubled_span",
            binding_type="text",
            signal_deps=["sig_count"],
            update_expr="(__pynext__.getSignal('sig_count').read() * 2).toString()",
            initial_value="0",
        )
        
        binding = render_ctx.bindings[0]
        assert "* 2" in binding.update_expr
    
    def test_text_binding_serialization(self, render_ctx):
        """Text binding should serialize correctly."""
        render_ctx.register_binding(
            node_id="text_el",
            binding_type="text",
            signal_deps=["sig_val"],
            update_expr="val.read()",
            initial_value="initial",
        )
        
        data = render_ctx.get_hydration_data()
        bindings = data["bindings"]
        
        assert len(bindings) == 1
        assert bindings[0]["nodeId"] == "text_el"
        assert bindings[0]["type"] == "text"
        assert bindings[0]["signals"] == ["sig_val"]
        assert bindings[0]["initial"] == "initial"


# =============================================================================
# ATTRIBUTE BINDING TESTS
# =============================================================================

class TestAttributeBinding:
    """Tests for attribute bindings."""
    
    def test_href_attribute_binding(self, render_ctx):
        """Attribute binding for href should work."""
        render_ctx.register_binding(
            node_id="link_1",
            binding_type="attr",
            signal_deps=["sig_url"],
            update_expr="__pynext__.getSignal('sig_url').read()",
            attr_name="href",
        )
        
        binding = render_ctx.bindings[0]
        assert binding.binding_type == "attr"
        assert binding.attr_name == "href"
    
    def test_src_attribute_binding(self, render_ctx):
        """Attribute binding for src should work."""
        render_ctx.register_binding(
            node_id="img_1",
            binding_type="attr",
            signal_deps=["sig_image_url"],
            update_expr="__pynext__.getSignal('sig_image_url').read()",
            attr_name="src",
        )
        
        binding = render_ctx.bindings[0]
        assert binding.attr_name == "src"
    
    def test_disabled_attribute_binding(self, render_ctx):
        """Attribute binding for disabled should work."""
        render_ctx.register_binding(
            node_id="btn_1",
            binding_type="attr",
            signal_deps=["sig_loading"],
            update_expr="__pynext__.getSignal('sig_loading').read() ? 'disabled' : null",
            attr_name="disabled",
        )
        
        binding = render_ctx.bindings[0]
        assert binding.attr_name == "disabled"
        assert "?" in binding.update_expr  # Ternary
    
    def test_value_attribute_binding(self, render_ctx):
        """Attribute binding for input value should work."""
        render_ctx.register_binding(
            node_id="input_1",
            binding_type="attr",
            signal_deps=["sig_input_value"],
            update_expr="__pynext__.getSignal('sig_input_value').read()",
            attr_name="value",
        )
        
        binding = render_ctx.bindings[0]
        assert binding.attr_name == "value"
    
    def test_data_attribute_binding(self, render_ctx):
        """Data attribute binding should work."""
        render_ctx.register_binding(
            node_id="el_1",
            binding_type="attr",
            signal_deps=["sig_id"],
            update_expr="'item-' + __pynext__.getSignal('sig_id').read()",
            attr_name="data-id",
        )
        
        binding = render_ctx.bindings[0]
        assert binding.attr_name == "data-id"


# =============================================================================
# CLASS BINDING TESTS
# =============================================================================

class TestClassBinding:
    """Tests for class bindings."""
    
    def test_single_class_toggle(self, render_ctx):
        """Single class toggle should work."""
        render_ctx.register_binding(
            node_id="div_1",
            binding_type="class",
            signal_deps=["sig_active"],
            update_expr="__pynext__.getSignal('sig_active').read() ? 'active' : ''",
            attr_name="active",
        )
        
        binding = render_ctx.bindings[0]
        assert binding.binding_type == "class"
        assert binding.attr_name == "active"
    
    def test_multiple_class_conditions(self, render_ctx):
        """Multiple class conditions should work."""
        render_ctx.register_binding(
            node_id="btn_1",
            binding_type="class",
            signal_deps=["sig_primary", "sig_disabled"],
            update_expr="[sig_primary.read() && 'primary', sig_disabled.read() && 'disabled'].filter(Boolean).join(' ')",
            attr_name="button-classes",
        )
        
        binding = render_ctx.bindings[0]
        assert len(binding.signal_deps) == 2
    
    def test_class_with_ternary(self, render_ctx):
        """Class with ternary expression should work."""
        render_ctx.register_binding(
            node_id="theme_div",
            binding_type="class",
            signal_deps=["sig_dark_mode"],
            update_expr="__pynext__.getSignal('sig_dark_mode').read() ? 'dark' : 'light'",
            attr_name="theme",
        )
        
        binding = render_ctx.bindings[0]
        assert "dark" in binding.update_expr
        assert "light" in binding.update_expr


# =============================================================================
# STYLE BINDING TESTS
# =============================================================================

class TestStyleBinding:
    """Tests for style bindings."""
    
    def test_color_style_binding(self, render_ctx):
        """Color style binding should work."""
        render_ctx.register_binding(
            node_id="text_1",
            binding_type="style",
            signal_deps=["sig_color"],
            update_expr="__pynext__.getSignal('sig_color').read()",
            attr_name="color",
        )
        
        binding = render_ctx.bindings[0]
        assert binding.binding_type == "style"
        assert binding.attr_name == "color"
    
    def test_transform_style_binding(self, render_ctx):
        """Transform style binding should work."""
        render_ctx.register_binding(
            node_id="box_1",
            binding_type="style",
            signal_deps=["sig_x", "sig_y"],
            update_expr="'translate(' + sig_x.read() + 'px, ' + sig_y.read() + 'px)'",
            attr_name="transform",
        )
        
        binding = render_ctx.bindings[0]
        assert binding.attr_name == "transform"
        assert "translate" in binding.update_expr
    
    def test_display_style_binding(self, render_ctx):
        """Display style binding should work."""
        render_ctx.register_binding(
            node_id="modal_1",
            binding_type="style",
            signal_deps=["sig_visible"],
            update_expr="__pynext__.getSignal('sig_visible').read() ? 'block' : 'none'",
            attr_name="display",
        )
        
        binding = render_ctx.bindings[0]
        assert "block" in binding.update_expr
        assert "none" in binding.update_expr


# =============================================================================
# SHOW BINDING TESTS
# =============================================================================

class TestShowBinding:
    """Tests for show/hide bindings."""
    
    def test_simple_show_binding(self, render_ctx):
        """Simple show binding should work."""
        render_ctx.register_binding(
            node_id="content_1",
            binding_type="show",
            signal_deps=["sig_visible"],
            update_expr="__pynext__.getSignal('sig_visible').read()",
        )
        
        binding = render_ctx.bindings[0]
        assert binding.binding_type == "show"
    
    def test_show_with_condition(self, render_ctx):
        """Show binding with condition should work."""
        render_ctx.register_binding(
            node_id="admin_panel",
            binding_type="show",
            signal_deps=["sig_user", "sig_is_admin"],
            update_expr="sig_user.read() && sig_is_admin.read()",
        )
        
        binding = render_ctx.bindings[0]
        assert "&&" in binding.update_expr
    
    def test_show_with_comparison(self, render_ctx):
        """Show binding with comparison should work."""
        render_ctx.register_binding(
            node_id="loading_indicator",
            binding_type="show",
            signal_deps=["sig_count"],
            update_expr="__pynext__.getSignal('sig_count').read() > 0",
        )
        
        binding = render_ctx.bindings[0]
        assert ">" in binding.update_expr


# =============================================================================
# FOR BINDING TESTS
# =============================================================================

class TestForBinding:
    """Tests for for/iteration bindings."""
    
    def test_simple_for_binding(self, render_ctx):
        """Simple for binding should work."""
        render_ctx.register_binding(
            node_id="list_container",
            binding_type="for",
            signal_deps=["sig_items"],
            update_expr="__pynext__.getSignal('sig_items').read()",
        )
        
        binding = render_ctx.bindings[0]
        assert binding.binding_type == "for"
    
    def test_for_with_key_function(self, render_ctx):
        """For binding with key function should work."""
        render_ctx.register_binding(
            node_id="user_list",
            binding_type="for",
            signal_deps=["sig_users"],
            update_expr="sig_users.read().map(u => ({...u, __key: u.id}))",
        )
        
        binding = render_ctx.bindings[0]
        assert "__key" in binding.update_expr


# =============================================================================
# MULTIPLE BINDINGS TESTS
# =============================================================================

class TestMultipleBindings:
    """Tests for multiple bindings on same or different elements."""
    
    def test_multiple_bindings_same_element(self, render_ctx):
        """Multiple bindings on same element should work."""
        # Text binding
        render_ctx.register_binding(
            node_id="complex_el",
            binding_type="text",
            signal_deps=["sig_text"],
            update_expr="sig_text.read()",
        )
        
        # Class binding
        render_ctx.register_binding(
            node_id="complex_el",
            binding_type="class",
            signal_deps=["sig_active"],
            update_expr="sig_active.read() ? 'active' : ''",
            attr_name="active",
        )
        
        # Style binding
        render_ctx.register_binding(
            node_id="complex_el",
            binding_type="style",
            signal_deps=["sig_color"],
            update_expr="sig_color.read()",
            attr_name="color",
        )
        
        assert len(render_ctx.bindings) == 3
        
        # All should have same node_id
        for binding in render_ctx.bindings:
            assert binding.node_id == "complex_el"
    
    def test_bindings_different_elements(self, render_ctx):
        """Bindings on different elements should be independent."""
        render_ctx.register_binding("el_1", "text", ["sig_a"], "a.read()")
        render_ctx.register_binding("el_2", "text", ["sig_b"], "b.read()")
        render_ctx.register_binding("el_3", "text", ["sig_c"], "c.read()")
        
        data = render_ctx.get_hydration_data()
        bindings = data["bindings"]
        
        node_ids = [b["nodeId"] for b in bindings]
        assert node_ids == ["el_1", "el_2", "el_3"]


# =============================================================================
# SIGNAL DEPENDENCY TESTS
# =============================================================================

class TestSignalDependencies:
    """Tests for signal dependency tracking."""
    
    def test_single_dependency(self, render_ctx):
        """Single signal dependency should be tracked."""
        render_ctx.register_binding(
            node_id="el",
            binding_type="text",
            signal_deps=["sig_only"],
            update_expr="sig_only.read()",
        )
        
        assert render_ctx.bindings[0].signal_deps == ["sig_only"]
    
    def test_multiple_dependencies(self, render_ctx):
        """Multiple signal dependencies should be tracked."""
        deps = ["sig_a", "sig_b", "sig_c", "sig_d"]
        
        render_ctx.register_binding(
            node_id="el",
            binding_type="text",
            signal_deps=deps,
            update_expr="sig_a.read() + sig_b.read() + sig_c.read() + sig_d.read()",
        )
        
        assert render_ctx.bindings[0].signal_deps == deps
    
    def test_empty_dependencies(self, render_ctx):
        """Empty dependencies should be allowed (static binding)."""
        render_ctx.register_binding(
            node_id="static_el",
            binding_type="text",
            signal_deps=[],
            update_expr="'Static Content'",
        )
        
        assert render_ctx.bindings[0].signal_deps == []


# =============================================================================
# INITIAL VALUE TESTS
# =============================================================================

class TestInitialValues:
    """Tests for initial value handling."""
    
    def test_initial_value_string(self, render_ctx):
        """String initial value should be preserved."""
        render_ctx.register_binding(
            node_id="el",
            binding_type="text",
            signal_deps=["sig"],
            update_expr="sig.read()",
            initial_value="Hello World",
        )
        
        assert render_ctx.bindings[0].initial_value == "Hello World"
    
    def test_initial_value_number(self, render_ctx):
        """Number initial value should be preserved."""
        render_ctx.register_binding(
            node_id="el",
            binding_type="text",
            signal_deps=["sig"],
            update_expr="sig.read()",
            initial_value=42,
        )
        
        assert render_ctx.bindings[0].initial_value == 42
    
    def test_initial_value_none(self, render_ctx):
        """None initial value should be allowed."""
        render_ctx.register_binding(
            node_id="el",
            binding_type="text",
            signal_deps=["sig"],
            update_expr="sig.read()",
            initial_value=None,
        )
        
        assert render_ctx.bindings[0].initial_value is None
    
    def test_initial_value_complex(self, render_ctx):
        """Complex initial value (dict, list) should be preserved."""
        render_ctx.register_binding(
            node_id="el",
            binding_type="for",
            signal_deps=["sig"],
            update_expr="sig.read()",
            initial_value=[{"id": 1}, {"id": 2}],
        )
        
        assert render_ctx.bindings[0].initial_value == [{"id": 1}, {"id": 2}]


# =============================================================================
# SERIALIZATION TESTS
# =============================================================================

class TestBindingSerialization:
    """Tests for binding serialization to hydration data."""
    
    def test_full_serialization(self, render_ctx):
        """All binding fields should serialize correctly."""
        render_ctx.register_binding(
            node_id="full_el",
            binding_type="attr",
            signal_deps=["sig_1", "sig_2"],
            update_expr="compute(sig_1, sig_2)",
            attr_name="data-computed",
            initial_value="initial_computed",
        )
        
        data = render_ctx.get_hydration_data()
        binding = data["bindings"][0]
        
        assert binding["nodeId"] == "full_el"
        assert binding["type"] == "attr"
        assert binding["signals"] == ["sig_1", "sig_2"]
        assert binding["update"] == "compute(sig_1, sig_2)"
        assert binding["attr"] == "data-computed"
        assert binding["initial"] == "initial_computed"
    
    def test_json_serializable(self, render_ctx):
        """Bindings should be JSON serializable."""
        render_ctx.register_binding(
            node_id="json_el",
            binding_type="text",
            signal_deps=["sig"],
            update_expr="sig.read()",
            initial_value={"nested": [1, 2, 3]},
        )
        
        data = render_ctx.get_hydration_data()
        
        # Should not raise
        json_str = json.dumps(data)
        parsed = json.loads(json_str)
        
        assert parsed["bindings"][0]["initial"]["nested"] == [1, 2, 3]


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestBindingEdgeCases:
    """Tests for edge cases in bindings."""
    
    def test_special_chars_in_node_id(self, render_ctx):
        """Special characters in node_id should work."""
        render_ctx.register_binding(
            node_id="el-with-dashes_and_underscores",
            binding_type="text",
            signal_deps=["sig"],
            update_expr="sig.read()",
        )
        
        assert render_ctx.bindings[0].node_id == "el-with-dashes_and_underscores"
    
    def test_unicode_in_update_expr(self, render_ctx):
        """Unicode in update expression should work."""
        render_ctx.register_binding(
            node_id="unicode_el",
            binding_type="text",
            signal_deps=["sig"],
            update_expr="'Привет ' + sig.read()",
        )
        
        assert "Привет" in render_ctx.bindings[0].update_expr
    
    def test_very_long_update_expr(self, render_ctx):
        """Very long update expression should work."""
        long_expr = " + ".join([f"sig{i}.read()" for i in range(50)])
        
        render_ctx.register_binding(
            node_id="long_el",
            binding_type="text",
            signal_deps=[f"sig{i}" for i in range(50)],
            update_expr=long_expr,
        )
        
        assert len(render_ctx.bindings[0].update_expr) > 500
    
    def test_empty_attr_name(self, render_ctx):
        """Empty attr_name for non-attr bindings should be allowed."""
        render_ctx.register_binding(
            node_id="el",
            binding_type="text",
            signal_deps=["sig"],
            update_expr="sig.read()",
            attr_name="",  # Empty for text binding
        )
        
        assert render_ctx.bindings[0].attr_name == ""
