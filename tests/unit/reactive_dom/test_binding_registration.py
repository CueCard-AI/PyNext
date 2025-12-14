"""
Tests for reactive binding registration in RenderContext.

Tests cover:
- ReactiveBinding dataclass
- Context register_binding method
- Binding in hydration data
- Different binding types
"""

import pytest
from pynext.core.context import RenderContext, ReactiveBinding, set_context, clear_context


class TestReactiveBindingDataclass:
    """Tests for ReactiveBinding dataclass."""
    
    def test_binding_creation(self):
        """Create a ReactiveBinding."""
        binding = ReactiveBinding(
            node_id="el_123",
            binding_type="text",
            signal_deps=["sig_1"],
            update_expr="__pynext__.getSignal('sig_1').read()",
        )
        assert binding.node_id == "el_123"
        assert binding.binding_type == "text"
    
    def test_binding_with_attr_name(self):
        """Binding with attribute name."""
        binding = ReactiveBinding(
            node_id="el_123",
            binding_type="attr",
            signal_deps=["sig_1"],
            update_expr="expr",
            attr_name="class",
        )
        assert binding.attr_name == "class"
    
    def test_binding_with_initial_value(self):
        """Binding with initial value."""
        binding = ReactiveBinding(
            node_id="el_123",
            binding_type="show",
            signal_deps=["sig_1"],
            update_expr="expr",
            initial_value=True,
        )
        assert binding.initial_value == True
    
    def test_binding_multiple_deps(self):
        """Binding with multiple signal dependencies."""
        binding = ReactiveBinding(
            node_id="el_123",
            binding_type="text",
            signal_deps=["sig_1", "sig_2", "sig_3"],
            update_expr="expr",
        )
        assert len(binding.signal_deps) == 3


class TestContextRegisterBinding:
    """Tests for context.register_binding method."""
    
    def setup_method(self):
        """Set up render context."""
        self.ctx = RenderContext()
    
    def test_register_adds_binding(self):
        """register_binding adds to bindings list."""
        self.ctx.register_binding(
            node_id="el_123",
            binding_type="text",
            signal_deps=["sig_1"],
            update_expr="expr",
        )
        assert len(self.ctx.bindings) == 1
    
    def test_register_multiple_bindings(self):
        """Register multiple bindings."""
        self.ctx.register_binding("el_1", "text", ["sig_1"], "expr1")
        self.ctx.register_binding("el_2", "show", ["sig_2"], "expr2")
        self.ctx.register_binding("el_3", "class", ["sig_3"], "expr3")
        
        assert len(self.ctx.bindings) == 3
    
    def test_binding_has_correct_type(self):
        """Registered binding has correct type."""
        self.ctx.register_binding("el_123", "show", ["sig_1"], "expr")
        
        binding = self.ctx.bindings[0]
        assert binding.binding_type == "show"
    
    def test_binding_has_correct_deps(self):
        """Registered binding has correct dependencies."""
        self.ctx.register_binding("el_123", "text", ["sig_1", "sig_2"], "expr")
        
        binding = self.ctx.bindings[0]
        assert "sig_1" in binding.signal_deps
        assert "sig_2" in binding.signal_deps


class TestBindingTypes:
    """Tests for different binding types."""
    
    def setup_method(self):
        """Set up render context."""
        self.ctx = RenderContext()
    
    def test_text_binding(self):
        """Register text binding."""
        self.ctx.register_binding("el_123", "text", ["sig_1"], "read()")
        assert self.ctx.bindings[0].binding_type == "text"
    
    def test_attr_binding(self):
        """Register attr binding."""
        self.ctx.register_binding("el_123", "attr", ["sig_1"], "read()", attr_name="href")
        
        binding = self.ctx.bindings[0]
        assert binding.binding_type == "attr"
        assert binding.attr_name == "href"
    
    def test_class_binding(self):
        """Register class binding."""
        self.ctx.register_binding("el_123", "class", ["sig_1"], "read()")
        assert self.ctx.bindings[0].binding_type == "class"
    
    def test_style_binding(self):
        """Register style binding."""
        self.ctx.register_binding("el_123", "style", ["sig_1"], "read()")
        assert self.ctx.bindings[0].binding_type == "style"
    
    def test_show_binding(self):
        """Register show binding."""
        self.ctx.register_binding("el_123", "show", ["sig_1"], "read()", initial_value=True)
        
        binding = self.ctx.bindings[0]
        assert binding.binding_type == "show"
        assert binding.initial_value == True
    
    def test_for_binding(self):
        """Register for binding."""
        self.ctx.register_binding(
            "el_123", "for", ["sig_1"], "read()",
            initial_value={"count": 3, "keys": [1, 2, 3]}
        )
        
        binding = self.ctx.bindings[0]
        assert binding.binding_type == "for"


class TestBindingInHydration:
    """Tests for bindings in hydration data."""
    
    def setup_method(self):
        """Set up render context."""
        self.ctx = RenderContext()
    
    def test_bindings_in_hydration_data(self):
        """Bindings appear in hydration data."""
        self.ctx.register_binding("el_1", "text", ["sig_1"], "expr")
        
        data = self.ctx.get_hydration_data()
        assert "bindings" in data
        assert len(data["bindings"]) == 1
    
    def test_binding_structure_in_hydration(self):
        """Binding has correct structure in hydration."""
        self.ctx.register_binding(
            "el_123", "show", ["sig_1", "sig_2"],
            "__pynext__.getSignal('sig_1').read()",
            initial_value=True
        )
        
        data = self.ctx.get_hydration_data()
        binding = data["bindings"][0]
        
        assert binding["nodeId"] == "el_123"
        assert binding["type"] == "show"
        assert "sig_1" in binding["signals"]
        assert "sig_2" in binding["signals"]
        assert binding["initial"] == True
    
    def test_multiple_bindings_in_hydration(self):
        """Multiple bindings all appear in hydration."""
        self.ctx.register_binding("el_1", "text", ["s1"], "e1")
        self.ctx.register_binding("el_2", "show", ["s2"], "e2")
        self.ctx.register_binding("el_3", "class", ["s3"], "e3")
        
        data = self.ctx.get_hydration_data()
        assert len(data["bindings"]) == 3
    
    def test_attr_name_in_hydration(self):
        """Attr name appears in hydration for attr bindings."""
        self.ctx.register_binding("el_1", "class", ["s1"], "e1", attr_name="class")
        
        data = self.ctx.get_hydration_data()
        assert data["bindings"][0]["attr"] == "class"


class TestBindingEdgeCases:
    """Edge cases for binding registration."""
    
    def setup_method(self):
        """Set up render context."""
        self.ctx = RenderContext()
    
    def test_empty_signal_deps(self):
        """Binding with empty signal deps."""
        self.ctx.register_binding("el_1", "text", [], "expr")
        
        binding = self.ctx.bindings[0]
        assert binding.signal_deps == []
    
    def test_long_update_expr(self):
        """Binding with long update expression."""
        long_expr = "Boolean(__pynext__.getSignal('sig_1').read() && __pynext__.getSignal('sig_2').read())"
        self.ctx.register_binding("el_1", "show", ["sig_1", "sig_2"], long_expr)
        
        binding = self.ctx.bindings[0]
        assert binding.update_expr == long_expr
    
    def test_complex_initial_value(self):
        """Binding with complex initial value."""
        self.ctx.register_binding(
            "el_1", "for", ["sig_1"], "expr",
            initial_value={
                "count": 5,
                "keys": [1, 2, 3, 4, 5],
                "template": "<div>Item</div>"
            }
        )
        
        binding = self.ctx.bindings[0]
        assert binding.initial_value["count"] == 5
        assert len(binding.initial_value["keys"]) == 5


class TestBindingContextIntegration:
    """Integration tests for bindings with context."""
    
    def test_set_and_get_context(self):
        """Set context and access bindings."""
        ctx = RenderContext()
        set_context(ctx)
        
        from pynext.core.context import get_context
        retrieved = get_context()
        assert retrieved is ctx
        
        clear_context()
    
    def test_bindings_persist_in_context(self):
        """Bindings persist in context through set/get."""
        ctx = RenderContext()
        ctx.register_binding("el_1", "text", ["s1"], "e1")
        
        set_context(ctx)
        
        from pynext.core.context import get_context
        retrieved = get_context()
        assert len(retrieved.bindings) == 1
        
        clear_context()

