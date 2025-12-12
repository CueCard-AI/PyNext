"""
Tests for JS Injector - Inject PyNext-Aware Tracking Code.

Tests cover:
- JSInjector initialization
- Script injection
- Already injected detection
- State retrieval
- Signal manipulation
- Manual snapshot triggering
- Hydration waiting
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from pynext.devtools.injector import (
    JSInjector,
    TRACKING_SCRIPT,
    CHECK_SCRIPT,
    GET_STATE_SCRIPT,
)


# ============================================
# JSInjector Initialization Tests
# ============================================

class TestJSInjectorInit:
    """Tests for JSInjector initialization."""
    
    def test_init(self):
        """Test injector initialization."""
        bridge = Mock()
        injector = JSInjector(bridge)
        
        assert injector._bridge is bridge
        assert injector.injected is False
    
    def test_injected_property(self):
        """Test injected property."""
        bridge = Mock()
        injector = JSInjector(bridge)
        
        assert injector.injected is False
        
        injector._injected = True
        assert injector.injected is True


# ============================================
# Injection Tests
# ============================================

class TestJSInjectorInject:
    """Tests for script injection."""
    
    @pytest.mark.asyncio
    async def test_inject_success(self):
        """Test successful injection."""
        bridge = AsyncMock()
        # execute_script: 1) check if injected (False), 2) run script, 3) verify (object)
        bridge.execute_script = AsyncMock(side_effect=[False, None, "object"])
        bridge.send_command = AsyncMock(return_value={"identifier": "1"})
        
        injector = JSInjector(bridge)
        result = await injector.inject()
        
        assert result is True
        assert injector.injected is True
    
    @pytest.mark.asyncio
    async def test_inject_already_injected(self):
        """Test injection when already injected."""
        bridge = AsyncMock()
        bridge.execute_script = AsyncMock(return_value=True)  # Already injected
        
        injector = JSInjector(bridge)
        result = await injector.inject()
        
        assert result is True
        assert injector.injected is True
        # Should only check, not inject
        assert bridge.execute_script.call_count == 1
    
    @pytest.mark.asyncio
    async def test_inject_force(self):
        """Test forced injection."""
        bridge = AsyncMock()
        bridge.execute_script = AsyncMock(return_value=None)
        
        injector = JSInjector(bridge)
        injector._injected = True  # Pretend already injected
        
        result = await injector.inject(force=True)
        
        assert result is True
        # Should inject even though already marked as injected
        bridge.execute_script.assert_called()
    
    @pytest.mark.asyncio
    async def test_inject_failure(self):
        """Test injection failure."""
        bridge = AsyncMock()
        bridge.execute_script = AsyncMock(side_effect=Exception("Script error"))
        
        injector = JSInjector(bridge)
        result = await injector.inject()
        
        assert result is False
        assert injector.injected is False
    
    @pytest.mark.asyncio
    async def test_is_already_injected(self):
        """Test checking if already injected."""
        bridge = AsyncMock()
        bridge.execute_script = AsyncMock(return_value=True)
        
        injector = JSInjector(bridge)
        result = await injector.is_already_injected()
        
        assert result is True
        bridge.execute_script.assert_called_with(CHECK_SCRIPT)
    
    @pytest.mark.asyncio
    async def test_is_already_injected_error(self):
        """Test is_already_injected handles errors."""
        bridge = AsyncMock()
        bridge.execute_script = AsyncMock(side_effect=Exception("Error"))
        
        injector = JSInjector(bridge)
        result = await injector.is_already_injected()
        
        assert result is False


# ============================================
# State Retrieval Tests
# ============================================

class TestJSInjectorState:
    """Tests for state retrieval."""
    
    @pytest.mark.asyncio
    async def test_get_state(self):
        """Test getting current state."""
        bridge = AsyncMock()
        bridge.execute_script = AsyncMock(return_value={
            "url": "http://localhost:3000",
            "signals": {"count": 5},
            "lastClick": None,
            "eventCount": 10,
        })
        
        injector = JSInjector(bridge)
        state = await injector.get_state()
        
        assert state is not None
        assert state["url"] == "http://localhost:3000"
        assert state["signals"]["count"] == 5
    
    @pytest.mark.asyncio
    async def test_get_state_error(self):
        """Test get_state handles errors."""
        bridge = AsyncMock()
        bridge.execute_script = AsyncMock(side_effect=Exception("Error"))
        
        injector = JSInjector(bridge)
        state = await injector.get_state()
        
        assert state is None


# ============================================
# Signal Manipulation Tests
# ============================================

class TestJSInjectorSignals:
    """Tests for signal manipulation."""
    
    @pytest.mark.asyncio
    async def test_get_signal_value(self):
        """Test getting signal value."""
        bridge = AsyncMock()
        bridge.execute_script = AsyncMock(return_value="kanban")
        
        injector = JSInjector(bridge)
        value = await injector.get_signal_value("view_mode")
        
        assert value == "kanban"
    
    @pytest.mark.asyncio
    async def test_get_signal_value_not_found(self):
        """Test getting non-existent signal."""
        bridge = AsyncMock()
        bridge.execute_script = AsyncMock(return_value=None)
        
        injector = JSInjector(bridge)
        value = await injector.get_signal_value("unknown")
        
        assert value is None
    
    @pytest.mark.asyncio
    async def test_get_signal_value_error(self):
        """Test get_signal_value handles errors."""
        bridge = AsyncMock()
        bridge.execute_script = AsyncMock(side_effect=Exception("Error"))
        
        injector = JSInjector(bridge)
        value = await injector.get_signal_value("count")
        
        assert value is None
    
    @pytest.mark.asyncio
    async def test_set_signal_value(self):
        """Test setting signal value."""
        bridge = AsyncMock()
        bridge.execute_script = AsyncMock(return_value=True)
        
        injector = JSInjector(bridge)
        result = await injector.set_signal_value("count", 10)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_set_signal_value_not_found(self):
        """Test setting non-existent signal."""
        bridge = AsyncMock()
        bridge.execute_script = AsyncMock(return_value=False)
        
        injector = JSInjector(bridge)
        result = await injector.set_signal_value("unknown", 5)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_set_signal_value_error(self):
        """Test set_signal_value handles errors."""
        bridge = AsyncMock()
        bridge.execute_script = AsyncMock(side_effect=Exception("Error"))
        
        injector = JSInjector(bridge)
        result = await injector.set_signal_value("count", 10)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_list_signals(self):
        """Test listing all signals."""
        bridge = AsyncMock()
        bridge.execute_script = AsyncMock(return_value=[
            {"id": "sig_1", "name": "count", "value": 5},
            {"id": "sig_2", "name": "view_mode", "value": "list"},
        ])
        
        injector = JSInjector(bridge)
        signals = await injector.list_signals()
        
        assert len(signals) == 2
        assert signals[0]["name"] == "count"
    
    @pytest.mark.asyncio
    async def test_list_signals_empty(self):
        """Test listing signals when none exist."""
        bridge = AsyncMock()
        bridge.execute_script = AsyncMock(return_value=[])
        
        injector = JSInjector(bridge)
        signals = await injector.list_signals()
        
        assert signals == []
    
    @pytest.mark.asyncio
    async def test_list_signals_error(self):
        """Test list_signals handles errors."""
        bridge = AsyncMock()
        bridge.execute_script = AsyncMock(side_effect=Exception("Error"))
        
        injector = JSInjector(bridge)
        signals = await injector.list_signals()
        
        assert signals == []


# ============================================
# Manual Snapshot Tests
# ============================================

class TestJSInjectorSnapshot:
    """Tests for manual snapshot triggering."""
    
    @pytest.mark.asyncio
    async def test_trigger_snapshot(self):
        """Test triggering manual snapshot."""
        bridge = AsyncMock()
        bridge.execute_script = AsyncMock(return_value=True)
        
        injector = JSInjector(bridge)
        result = await injector.trigger_snapshot("Testing modal")
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_trigger_snapshot_no_note(self):
        """Test triggering snapshot without note."""
        bridge = AsyncMock()
        bridge.execute_script = AsyncMock(return_value=True)
        
        injector = JSInjector(bridge)
        result = await injector.trigger_snapshot()
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_trigger_snapshot_error(self):
        """Test trigger_snapshot handles errors."""
        bridge = AsyncMock()
        bridge.execute_script = AsyncMock(side_effect=Exception("Error"))
        
        injector = JSInjector(bridge)
        result = await injector.trigger_snapshot("test")
        
        assert result is False


# ============================================
# Hydration Waiting Tests
# ============================================

class TestJSInjectorHydration:
    """Tests for hydration waiting."""
    
    @pytest.mark.asyncio
    async def test_wait_for_hydration_immediate(self):
        """Test hydration already complete."""
        bridge = AsyncMock()
        bridge.execute_script = AsyncMock(return_value=True)
        
        injector = JSInjector(bridge)
        result = await injector.wait_for_hydration(timeout=1.0)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_wait_for_hydration_delayed(self):
        """Test hydration completes after delay."""
        bridge = AsyncMock()
        
        call_count = 0
        async def mock_execute(script):
            nonlocal call_count
            call_count += 1
            return call_count >= 3  # Succeed on 3rd call
        
        bridge.execute_script = mock_execute
        
        injector = JSInjector(bridge)
        result = await injector.wait_for_hydration(timeout=5.0)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_wait_for_hydration_timeout(self):
        """Test hydration timeout."""
        bridge = AsyncMock()
        bridge.execute_script = AsyncMock(return_value=False)
        
        injector = JSInjector(bridge)
        result = await injector.wait_for_hydration(timeout=0.2)
        
        assert result is False


# ============================================
# Script Content Tests
# ============================================

class TestTrackingScript:
    """Tests for tracking script content."""
    
    def test_tracking_script_not_empty(self):
        """Test that tracking script is not empty."""
        assert len(TRACKING_SCRIPT) > 0
    
    def test_tracking_script_has_debug_object(self):
        """Test that script creates __pynext_debug__."""
        assert "__pynext_debug__" in TRACKING_SCRIPT
    
    def test_tracking_script_has_signal_tracking(self):
        """Test that script has signal tracking."""
        assert "reportSignal" in TRACKING_SCRIPT
    
    def test_tracking_script_has_click_tracking(self):
        """Test that script has click tracking."""
        assert "click" in TRACKING_SCRIPT.lower()
    
    def test_tracking_script_has_snapshot(self):
        """Test that script has snapshot function."""
        assert "snapshot" in TRACKING_SCRIPT
    
    def test_check_script_simple(self):
        """Test that check script is simple."""
        assert "__pynext_debug__" in CHECK_SCRIPT
        assert len(CHECK_SCRIPT) < 100
    
    def test_get_state_script_returns_state(self):
        """Test that get state script returns state object."""
        assert "getState" in GET_STATE_SCRIPT

