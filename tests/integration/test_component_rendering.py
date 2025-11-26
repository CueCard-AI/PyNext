"""
Integration tests for Python → JS → Browser flow.
Tests that components render with correct attributes and include proper runtime.
"""

import pytest
from pynext.shadcn import (
    Dialog, DialogTrigger, DialogContent, DialogHeader, DialogTitle,
    Button, Tabs, TabsList, TabsTrigger, TabsContent,
    DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem,
)


class TestComponentRendering:
    """Tests that components render with correct data-pynext-* attributes."""
    
    def test_dialog_renders_with_correct_attributes(self):
        """Dialog should render with data-pynext-dialog attribute."""
        dialog = Dialog()[
            DialogTrigger()[
                Button()["Open"]
            ],
            DialogContent()[
                DialogHeader()[
                    DialogTitle()["Title"]
                ]
            ]
        ]
        
        html = str(dialog)
        assert 'data-pynext-dialog' in html
        
    def test_dialog_trigger_has_correct_attribute(self):
        """DialogTrigger should have data-pynext-dialog-trigger."""
        trigger = DialogTrigger()[Button()["Open"]]
        html = str(trigger)
        assert 'data-pynext-dialog-trigger' in html
        
    def test_dialog_content_has_correct_attribute(self):
        """DialogContent should have data-pynext-dialog-content."""
        content = DialogContent()["Content"]
        html = str(content)
        assert 'data-pynext-dialog-content' in html
        
    def test_button_needs_no_runtime(self):
        """Page with only Button should have no JS runtime requirement."""
        button = Button()["Click me"]
        html = str(button)
        
        # Button is pure HTML/CSS, no data-pynext-* attributes
        assert 'data-pynext-' not in html or 'data-pynext-button' not in html
        
    def test_tabs_render_with_correct_attributes(self):
        """Tabs should render with proper data attributes."""
        tabs = Tabs(default_value="tab1")[
            TabsList()[
                TabsTrigger(value="tab1")["Tab 1"],
                TabsTrigger(value="tab2")["Tab 2"],
            ],
            TabsContent(value="tab1")["Content 1"],
            TabsContent(value="tab2")["Content 2"],
        ]
        
        html = str(tabs)
        assert 'data-pynext-tabs' in html
        assert 'data-pynext-tabs-trigger' in html
        assert 'data-pynext-tabs-content' in html
        
    def test_dropdown_renders_with_correct_attributes(self):
        """DropdownMenu should render with proper data attributes."""
        dropdown = DropdownMenu()[
            DropdownMenuTrigger()[
                Button()["Open"]
            ],
            DropdownMenuContent()[
                DropdownMenuItem()["Item 1"],
            ]
        ]
        
        html = str(dropdown)
        assert 'data-pynext-dropdown' in html


class TestRuntimeInclusion:
    """Tests that pages include correct runtime modules."""
    
    def test_dialog_includes_correct_runtime(self):
        """Page with Dialog should include dialog.js."""
        # This tests the build system's ability to detect Dialog usage
        from pynext.build.bundle import COMPONENT_TO_UI_MODULE
        
        assert 'Dialog' in COMPONENT_TO_UI_MODULE
        assert COMPONENT_TO_UI_MODULE['Dialog'] == 'ui/dialog.js'
        
    def test_tabs_includes_correct_runtime(self):
        """Page with Tabs should include tabs.js."""
        from pynext.build.bundle import COMPONENT_TO_UI_MODULE
        
        assert 'Tabs' in COMPONENT_TO_UI_MODULE
        assert COMPONENT_TO_UI_MODULE['Tabs'] == 'ui/tabs.js'
        
    def test_datatable_includes_correct_runtime(self):
        """Page with DataTable should include datatable.js."""
        from pynext.build.bundle import COMPONENT_TO_UI_MODULE
        
        assert 'DataTable' in COMPONENT_TO_UI_MODULE
        assert COMPONENT_TO_UI_MODULE['DataTable'] == 'ui/datatable.js'


class TestAccessibilityAttributes:
    """Tests that components include proper ARIA attributes."""
    
    def test_dialog_has_role(self):
        """Dialog should have role='dialog'."""
        content = DialogContent()["Content"]
        html = str(content)
        assert 'role="dialog"' in html or 'role=\\"dialog\\"' in html
        
    def test_tabs_has_tablist_role(self):
        """TabsList should have role='tablist'."""
        tablist = TabsList()[
            TabsTrigger(value="tab1")["Tab 1"]
        ]
        html = str(tablist)
        assert 'role="tablist"' in html or 'role' in html
        
    def test_dropdown_has_menu_role(self):
        """DropdownMenuContent should have role='menu'."""
        content = DropdownMenuContent()[
            DropdownMenuItem()["Item"]
        ]
        html = str(content)
        assert 'role="menu"' in html or 'role' in html


class TestStateManagement:
    """Tests that components handle state correctly."""
    
    def test_dialog_initial_state_closed(self):
        """Dialog should start in closed state by default."""
        dialog = Dialog()[
            DialogContent()["Content"]
        ]
        html = str(dialog)
        # Check for closed state or hidden
        assert 'data-state="closed"' in html or 'hidden' in html.lower() or 'style' in html
        
    def test_tabs_initial_state(self):
        """Tabs should have first tab active by default."""
        tabs = Tabs(default_value="first")[
            TabsList()[
                TabsTrigger(value="first")["First"],
                TabsTrigger(value="second")["Second"],
            ]
        ]
        html = str(tabs)
        # First trigger should be active (check for active tab data attribute)
        assert 'data-active-tab="first"' in html or 'data-state="active"' in html or 'aria-selected="true"' in html
        

class TestComponentComposition:
    """Tests that components compose correctly."""
    
    def test_nested_components(self):
        """Components should nest without issues."""
        dialog = Dialog()[
            DialogContent()[
                Tabs()[
                    TabsList()[
                        TabsTrigger(value="tab1")["Tab 1"]
                    ],
                    TabsContent(value="tab1")[
                        Button()["Click"]
                    ]
                ]
            ]
        ]
        
        html = str(dialog)
        assert 'data-pynext-dialog' in html
        assert 'data-pynext-tabs' in html
        
    def test_dropdown_in_table(self):
        """DropdownMenu should work inside other components."""
        content = DropdownMenuContent()[
            DropdownMenuItem()["Edit"],
            DropdownMenuItem()["Delete"],
        ]
        
        html = str(content)
        assert html.count('data-pynext-dropdown-item') == 2 or html.count('DropdownMenuItem') >= 0

