"""
Unit tests for Parallel Routes.

Tests:
- Slot component
- Parallel route scanning
- Slot context management
- Independent streaming
"""

import pytest
from pathlib import Path
from pynext.core.slot import (
    Slot,
    SlotGroup,
    SlotContext,
    get_slot_context,
    create_slot_context,
    set_slot_content,
    sidebar_slot,
    main_slot,
    modal_slot,
    get_slot_streaming_js,
    get_slot_css,
)
from pynext.router.parallel import (
    ParallelRoute,
    SlotConfig,
    SlotMatch,
    CompiledSlotHierarchy,
    ParallelRouteScanner,
    SlotRenderer,
    get_parallel_scanner,
    scan_parallel_routes,
)
from pynext.core.html import div


class TestSlotComponent:
    """Tests for the Slot component."""
    
    def test_slot_renders_placeholder(self):
        """Slot should render placeholder when no content."""
        slot = Slot("sidebar")
        html = slot.render()
        
        assert 'data-slot="sidebar"' in html
        assert 'data-slot-state="pending"' in html
    
    def test_slot_renders_loading(self):
        """Slot should render loading component when provided."""
        slot = Slot(
            "main",
            loading=lambda: div()["Loading main..."]
        )
        html = slot.render()
        
        assert "Loading main..." in html
        assert 'data-slot-state="loading"' in html
    
    def test_slot_renders_content_from_context(self):
        """Slot should render content from context."""
        ctx = create_slot_context()
        ctx.active_slots["sidebar"] = "<nav>Navigation</nav>"
        
        slot = Slot("sidebar")
        html = slot.render()
        
        assert "Navigation" in html
        assert 'data-slot-state="ready"' in html
    
    def test_slot_unique_id(self):
        """Each slot should have unique ID."""
        slot1 = Slot("test")
        slot2 = Slot("test")
        
        assert slot1.id != slot2.id


class TestSlotHelpers:
    """Tests for slot helper functions."""
    
    def test_sidebar_slot(self):
        """sidebar_slot should create sidebar slot."""
        slot = sidebar_slot()
        
        assert slot.name == "sidebar"
        assert "sidebar-slot" in slot.className
    
    def test_main_slot(self):
        """main_slot should create main slot."""
        slot = main_slot()
        
        assert slot.name == "main"
        assert "main-slot" in slot.className
    
    def test_modal_slot(self):
        """modal_slot should create modal slot."""
        slot = modal_slot()
        
        assert slot.name == "modal"
        assert "modal-slot" in slot.className


class TestSlotContext:
    """Tests for slot context."""
    
    def test_create_context(self):
        """Should create slot context."""
        ctx = create_slot_context()
        
        assert ctx.active_slots == {}
        assert ctx.pending_slots == []
    
    def test_set_slot_content(self):
        """set_slot_content should update context."""
        ctx = create_slot_context()
        ctx.pending_slots.append("sidebar")
        
        set_slot_content("sidebar", "<nav>Nav</nav>")
        
        assert ctx.active_slots["sidebar"] == "<nav>Nav</nav>"
        assert "sidebar" not in ctx.pending_slots


class TestSlotGroup:
    """Tests for SlotGroup component."""
    
    def test_slot_group_renders_children(self):
        """SlotGroup should render child slots."""
        group = SlotGroup()[
            Slot("header"),
            Slot("main"),
            Slot("footer"),
        ]
        
        html = group.render()
        
        assert 'data-slot="header"' in html
        assert 'data-slot="main"' in html
        assert 'data-slot="footer"' in html
    
    def test_slot_group_loading_state(self):
        """SlotGroup should show loading when children pending."""
        group = SlotGroup(
            loading=lambda: div()["Loading page..."]
        )[
            Slot("main"),
        ]
        
        html = group.render()
        
        assert "Loading page..." in html


class TestCompiledSlotHierarchy:
    """Tests for compiled slot hierarchy."""
    
    def test_hierarchy_creation(self):
        """Should create compiled hierarchy."""
        hierarchy = CompiledSlotHierarchy(
            layout_path="",
            slots={
                "sidebar": [],
                "main": [],
            },
            default_slots={},
            slot_configs={},
        )
        
        assert "sidebar" in hierarchy.slots
        assert "main" in hierarchy.slots
    
    def test_hierarchy_match_slots(self):
        """Hierarchy should match slots for path."""
        route = ParallelRoute(
            slot_name="main",
            path_pattern="/users/:id",
            handler=None,
            module_path="",
        )
        
        hierarchy = CompiledSlotHierarchy(
            layout_path="",
            slots={"main": [route]},
            default_slots={},
            slot_configs={},
        )
        
        matches = hierarchy.match_slots("/users/123")
        
        assert "main" in matches
        assert matches["main"].params.get("id") == "123"


class TestParallelRouteScanner:
    """Tests for parallel route scanner."""
    
    def test_scanner_creation(self):
        """Should create scanner."""
        scanner = ParallelRouteScanner()
        
        assert scanner._hierarchies == {}
    
    def test_scanner_singleton(self):
        """get_parallel_scanner should return singleton."""
        scanner1 = get_parallel_scanner()
        scanner2 = get_parallel_scanner()
        
        assert scanner1 is scanner2


class TestSlotConfig:
    """Tests for slot configuration."""
    
    def test_default_config(self):
        """SlotConfig should have defaults."""
        config = SlotConfig(name="test")
        
        assert config.name == "test"
        assert config.stream_independent is True
        assert config.cache_ttl == 0
    
    def test_custom_config(self):
        """SlotConfig should accept custom values."""
        config = SlotConfig(
            name="sidebar",
            cache_ttl=60,
            stream_independent=False,
        )
        
        assert config.cache_ttl == 60
        assert config.stream_independent is False


class TestSlotRuntime:
    """Tests for slot JavaScript runtime."""
    
    def test_runtime_content(self):
        """Slot runtime should have essential functions."""
        js = get_slot_streaming_js()
        
        assert "__pynext__.slots" in js
        assert "update" in js
        assert "setLoading" in js
        assert "setError" in js
    
    def test_css_content(self):
        """Slot CSS should have essential styles."""
        css = get_slot_css()
        
        assert ".pynext-slot" in css
        assert "data-slot-state" in css


class TestIndependentStreaming:
    """Tests for independent slot streaming."""
    
    def test_slots_stream_independently(self):
        """Each slot should be able to stream independently."""
        ctx = create_slot_context()
        
        # Create multiple pending slots
        slot1 = Slot("fast")
        slot2 = Slot("slow")
        
        slot1.render()
        slot2.render()
        
        # Fast slot resolves first
        set_slot_content("fast", "Fast content")
        
        assert "fast" in ctx.active_slots
        assert "slow" not in ctx.active_slots
        assert "slow" in ctx.pending_slots

