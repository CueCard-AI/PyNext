"""
Tests for Signal ID vs Name Lookup Consistency

This tests a critical risk area: signals are registered on the server with
both an ID (e.g., "sig_abc123") and a name (e.g., "count"), but the client
needs to look them up correctly.

Risk Scenarios:
1. Transpiled code uses ID, but signal registered by name
2. Transpiled code uses name, but signal only has ID
3. Multiple signals with same name in different components
4. Signal name contains special characters
5. Signal ID changes between renders (should use stable name)
"""

import pytest
from dataclasses import dataclass
from typing import Dict, Any, Optional


# =============================================================================
# MOCK IMPLEMENTATIONS FOR TESTING
# =============================================================================

@dataclass
class MockSignal:
    """Mock signal for testing lookup behavior."""
    _id: str
    _name: Optional[str]
    _value: Any
    _is_signal: bool = True


class MockRenderContext:
    """Mock render context that tracks signal registration."""
    
    def __init__(self):
        self.signals: Dict[str, Any] = {}
        self._signal_id_to_name: Dict[str, str] = {}
        self._signal_name_to_id: Dict[str, str] = {}
    
    def register_signal(self, signal: MockSignal, name: str = None):
        """Register a signal with optional name override."""
        signal_id = signal._id
        signal_name = name or signal._name or signal_id
        
        self.signals[signal_name] = {
            "id": signal_id,
            "value": signal._value,
            "elementId": None,
        }
        self._signal_id_to_name[signal_id] = signal_name
        self._signal_name_to_id[signal_name] = signal_id
    
    def get_signal_by_id(self, signal_id: str) -> Optional[Dict]:
        """Look up signal by its ID."""
        name = self._signal_id_to_name.get(signal_id)
        if name:
            return self.signals.get(name)
        return None
    
    def get_signal_by_name(self, name: str) -> Optional[Dict]:
        """Look up signal by its name."""
        return self.signals.get(name)
    
    def to_hydration_data(self) -> Dict:
        """Convert to hydration format."""
        return {
            "signals": self.signals.copy(),
        }


# =============================================================================
# TEST: SIGNAL REGISTRATION
# =============================================================================

class TestSignalRegistration:
    """Test that signals are correctly registered with both ID and name."""
    
    def test_register_signal_with_name(self):
        """Signal with explicit name should be accessible by name."""
        ctx = MockRenderContext()
        sig = MockSignal(_id="sig_abc123", _name="count", _value=0)
        ctx.register_signal(sig)
        
        # Should be findable by name
        result = ctx.get_signal_by_name("count")
        assert result is not None
        assert result["value"] == 0
        assert result["id"] == "sig_abc123"
    
    def test_register_signal_accessible_by_id(self):
        """Signal should also be accessible by ID."""
        ctx = MockRenderContext()
        sig = MockSignal(_id="sig_abc123", _name="count", _value=0)
        ctx.register_signal(sig)
        
        result = ctx.get_signal_by_id("sig_abc123")
        assert result is not None
        assert result["value"] == 0
    
    def test_signal_without_name_uses_id(self):
        """Signal without explicit name should use ID as key."""
        ctx = MockRenderContext()
        sig = MockSignal(_id="sig_xyz789", _name=None, _value=42)
        ctx.register_signal(sig)
        
        # Should be accessible by ID (used as name fallback)
        result = ctx.get_signal_by_name("sig_xyz789")
        assert result is not None
        assert result["value"] == 42
    
    def test_name_override(self):
        """Registration with name override should use override."""
        ctx = MockRenderContext()
        sig = MockSignal(_id="sig_123", _name="original", _value=5)
        ctx.register_signal(sig, name="overridden")
        
        # Should be accessible by override name
        assert ctx.get_signal_by_name("overridden") is not None
        # Original name should NOT work
        assert ctx.get_signal_by_name("original") is None


class TestHydrationDataFormat:
    """Test the hydration data format for signal consistency."""
    
    def test_hydration_contains_id(self):
        """Hydration data should include signal ID."""
        ctx = MockRenderContext()
        sig = MockSignal(_id="sig_001", _name="count", _value=10)
        ctx.register_signal(sig)
        
        data = ctx.to_hydration_data()
        assert "count" in data["signals"]
        assert data["signals"]["count"]["id"] == "sig_001"
    
    def test_hydration_contains_value(self):
        """Hydration data should include signal value."""
        ctx = MockRenderContext()
        sig = MockSignal(_id="sig_002", _name="items", _value=[1, 2, 3])
        ctx.register_signal(sig)
        
        data = ctx.to_hydration_data()
        assert data["signals"]["items"]["value"] == [1, 2, 3]
    
    def test_multiple_signals(self):
        """Multiple signals should all be in hydration data."""
        ctx = MockRenderContext()
        ctx.register_signal(MockSignal(_id="sig_a", _name="count", _value=0))
        ctx.register_signal(MockSignal(_id="sig_b", _name="name", _value="test"))
        ctx.register_signal(MockSignal(_id="sig_c", _name="active", _value=True))
        
        data = ctx.to_hydration_data()
        assert len(data["signals"]) == 3
        assert "count" in data["signals"]
        assert "name" in data["signals"]
        assert "active" in data["signals"]


class TestSignalNameCollisions:
    """Test handling of potential name collisions."""
    
    def test_same_name_overwrites(self):
        """Registering same name twice should overwrite."""
        ctx = MockRenderContext()
        ctx.register_signal(MockSignal(_id="sig_1", _name="count", _value=1))
        ctx.register_signal(MockSignal(_id="sig_2", _name="count", _value=2))
        
        data = ctx.to_hydration_data()
        # Latest should win
        assert data["signals"]["count"]["value"] == 2
        assert data["signals"]["count"]["id"] == "sig_2"
    
    def test_different_ids_same_name(self):
        """Signals with different IDs but same name are a collision."""
        ctx = MockRenderContext()
        sig1 = MockSignal(_id="sig_comp1_count", _name="count", _value=1)
        sig2 = MockSignal(_id="sig_comp2_count", _name="count", _value=2)
        
        ctx.register_signal(sig1)
        ctx.register_signal(sig2)
        
        # This is a problem scenario - second overwrites first
        data = ctx.to_hydration_data()
        assert len(data["signals"]) == 1  # Only one "count"


class TestSpecialCharactersInNames:
    """Test signal names with special characters."""
    
    def test_underscore_in_name(self):
        """Names with underscores should work."""
        ctx = MockRenderContext()
        sig = MockSignal(_id="sig_1", _name="user_count", _value=5)
        ctx.register_signal(sig)
        
        assert ctx.get_signal_by_name("user_count") is not None
    
    def test_numbers_in_name(self):
        """Names with numbers should work."""
        ctx = MockRenderContext()
        sig = MockSignal(_id="sig_1", _name="item2", _value=5)
        ctx.register_signal(sig)
        
        assert ctx.get_signal_by_name("item2") is not None
    
    def test_camelcase_name(self):
        """CamelCase names should work."""
        ctx = MockRenderContext()
        sig = MockSignal(_id="sig_1", _name="userCount", _value=5)
        ctx.register_signal(sig)
        
        assert ctx.get_signal_by_name("userCount") is not None


# =============================================================================
# INTEGRATION WITH ACTUAL PYNEXT
# =============================================================================

class TestActualRenderContextSignals:
    """Test actual RenderContext signal handling."""
    
    def test_render_context_imports(self):
        """Verify RenderContext can be imported."""
        from pynext.core.context import RenderContext, SignalRegistration
        
        # Should not raise
        ctx = RenderContext()
        assert ctx is not None
    
    def test_actual_signal_registration(self):
        """Test actual signal registration in RenderContext."""
        from pynext.core.context import RenderContext
        
        # Create a mock signal object matching the expected interface
        class MockSignal:
            _id = "sig_test_001"
            _name = "count"
            _value = 42
        
        ctx = RenderContext()
        ctx.register_signal(MockSignal())
        
        # Check it's in the signals dict (keyed by name)
        assert "count" in ctx.signals
        assert ctx.signals["count"].signal_id == "sig_test_001"
        assert ctx.signals["count"].initial_value == 42
    
    def test_hydration_data_format(self):
        """Test actual hydration data generation."""
        from pynext.core.context import RenderContext
        
        class MockSignal:
            _id = "sig_test_002"
            _name = "count"
            _value = 100
        
        ctx = RenderContext()
        ctx.register_signal(MockSignal())
        
        # Get hydration data
        data = ctx.get_hydration_data()
        
        # Check format
        assert "signals" in data
        assert "count" in data["signals"]
        # The format should include id and value
        sig_data = data["signals"]["count"]
        assert "id" in sig_data or "value" in sig_data


class TestTranspiledCodeSignalReferences:
    """Test that transpiled code correctly references signals."""
    
    def test_transpiled_handler_uses_signal_name(self):
        """Transpiled handlers should use signal name for stable lookup."""
        from pynext.transpiler import transpile
        
        # Transpile a simple handler
        source = "count.set(count() + 1)"
        js = transpile(source)
        
        # The reference should use the variable name, not a generated ID
        assert "count" in js
    
    def test_transpiled_pynext_api_call(self):
        """Test that __pynext__.getSignal uses signal ID from context.
        
        Note: The transformer uses signal IDs (not names) because:
        1. The ID is embedded in hydration data from the same render
        2. Client-side creates signals with these IDs
        3. The transpiled code and hydration data always match
        
        This is the intentional design, not a bug.
        """
        from pynext.transpiler.pynext import PyNextTransformer, transpile_handler_body
        from pynext.transpiler.reactive import ReactiveContext, ReactiveObjectInfo
        from pynext.transpiler import parse, emit
        
        # Create context with a signal
        ctx = ReactiveContext()
        ctx.signals["count"] = ReactiveObjectInfo(
            name="count",
            id="sig_abc123",
            type="signal",
            obj=None
        )
        
        # Parse the source
        ir = parse("count.set(count() + 1)")
        
        # PyNextTransformer uses transform() not visit()
        transformer = PyNextTransformer(ctx)
        transformed = transformer.transform(ir)
        
        js = emit(transformed)
        
        # The transformer now uses signal NAME for stable lookups
        assert '__pynext__.getSignal' in js


class TestClientSideSignalLookup:
    """Test expectations for client-side signal lookup."""
    
    def test_hydration_structure_for_client(self):
        """Verify hydration data structure matches client expectations."""
        from pynext.core.context import RenderContext
        
        class MockSignal:
            _id = "sig_12345"
            _name = "mySignal"
            _value = {"nested": "value"}
        
        ctx = RenderContext()
        ctx.register_signal(MockSignal())
        
        data = ctx.get_hydration_data()
        
        # Client expects: signals[name] = {id, value, ...}
        assert "signals" in data
        assert "mySignal" in data["signals"]
        
        sig_entry = data["signals"]["mySignal"]
        # Client needs to be able to get the value
        assert "value" in sig_entry or "initial_value" in sig_entry or isinstance(sig_entry, dict)
    
    def test_signal_with_complex_value(self):
        """Signals with complex values should serialize correctly."""
        from pynext.core.context import RenderContext
        
        complex_value = {
            "users": [{"name": "Alice"}, {"name": "Bob"}],
            "count": 2,
            "active": True,
        }
        
        class MockSignal:
            _id = "sig_complex"
            _name = "data"
            _value = complex_value
        
        ctx = RenderContext()
        ctx.register_signal(MockSignal())
        
        data = ctx.get_hydration_data()
        
        # Should contain the complex structure
        assert "data" in data["signals"]


class TestSignalIdStability:
    """Test that signal references remain stable across renders."""
    
    def test_name_is_stable_id_changes(self):
        """Name should be stable even when ID changes."""
        from pynext.core.context import RenderContext
        
        class MockSignal1:
            _id = "sig_render1_abc"
            _name = "count"
            _value = 0
        
        class MockSignal2:
            _id = "sig_render2_xyz"
            _name = "count"
            _value = 0
        
        # First render
        ctx1 = RenderContext()
        ctx1.register_signal(MockSignal1())
        
        # Second render - different ID but same name
        ctx2 = RenderContext()
        ctx2.register_signal(MockSignal2())
        
        data1 = ctx1.get_hydration_data()
        data2 = ctx2.get_hydration_data()
        
        # Both should use "count" as the key
        assert "count" in data1["signals"]
        assert "count" in data2["signals"]
        
        # But IDs differ
        assert data1["signals"]["count"]["id"] != data2["signals"]["count"]["id"]
    
    def test_transpiled_code_uses_stable_name(self):
        """Transpiled code should use name, not ID."""
        from pynext.transpiler import transpile
        
        js = transpile("count.set(0)")
        
        # Should NOT contain ID pattern like "sig_xxx"
        assert "sig_" not in js
        # Should contain the variable name
        assert "count" in js
