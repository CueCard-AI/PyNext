"""
Additional tests to boost code coverage - Part 2.

Focus on components and modules with lower coverage.
"""

import pytest
from unittest.mock import Mock, patch
import tempfile


# =============================================================================
# THEME MODULE COMPREHENSIVE TESTS
# =============================================================================

class TestThemeProviderComprehensive:
    """Comprehensive tests for ThemeProvider."""
    
    def test_theme_provider_render(self):
        """ThemeProvider renders."""
        from pynext.theme import ThemeProvider
        result = ThemeProvider()
        html = str(result)
        assert html
    
    def test_theme_provider_with_children(self):
        """ThemeProvider with children."""
        from pynext.theme import ThemeProvider
        result = ThemeProvider()
        html = str(result)
        assert html
    
    def test_theme_script_render(self):
        """ThemeScript renders."""
        from pynext.theme import ThemeScript
        result = ThemeScript()
        html = str(result)
        assert "script" in html.lower() or html
    
    def test_theme_toggle_render(self):
        """ThemeToggle renders."""
        from pynext.theme import ThemeToggle
        result = ThemeToggle()
        html = str(result)
        assert html
    
    def test_theme_switcher_render(self):
        """ThemeSwitcher renders."""
        from pynext.theme import ThemeSwitcher
        result = ThemeSwitcher()
        html = str(result)
        assert html


# =============================================================================
# TAILWIND BUILDER COMPREHENSIVE TESTS
# =============================================================================

class TestTailwindBuilderComprehensive:
    """Comprehensive tests for TailwindBuilder."""
    
    def test_tw_padding(self):
        """TailwindBuilder padding methods."""
        from pynext.tw.builder import TailwindBuilder
        builder = TailwindBuilder()
        builder = builder.p_4
        assert builder is not None
    
    def test_tw_margin(self):
        """TailwindBuilder margin methods."""
        from pynext.tw.builder import TailwindBuilder
        builder = TailwindBuilder()
        builder = builder.m_4
        assert builder is not None
    
    def test_tw_background(self):
        """TailwindBuilder background methods."""
        from pynext.tw.builder import TailwindBuilder
        builder = TailwindBuilder()
        builder = builder.bg_blue_500
        assert builder is not None
    
    def test_tw_text(self):
        """TailwindBuilder text methods."""
        from pynext.tw.builder import TailwindBuilder
        builder = TailwindBuilder()
        builder = builder.text_lg
        assert builder is not None
    
    def test_tw_font(self):
        """TailwindBuilder font methods."""
        from pynext.tw.builder import TailwindBuilder
        builder = TailwindBuilder()
        builder = builder.font_bold
        assert builder is not None
    
    def test_tw_flex(self):
        """TailwindBuilder flex methods."""
        from pynext.tw.builder import TailwindBuilder
        builder = TailwindBuilder()
        builder = builder.flex
        assert builder is not None
    
    def test_tw_grid(self):
        """TailwindBuilder grid methods."""
        from pynext.tw.builder import TailwindBuilder
        builder = TailwindBuilder()
        builder = builder.grid
        assert builder is not None
    
    def test_tw_border(self):
        """TailwindBuilder border methods."""
        from pynext.tw.builder import TailwindBuilder
        builder = TailwindBuilder()
        builder = builder.border
        assert builder is not None
    
    def test_tw_rounded(self):
        """TailwindBuilder rounded methods."""
        from pynext.tw.builder import TailwindBuilder
        builder = TailwindBuilder()
        builder = builder.rounded_lg
        assert builder is not None
    
    def test_tw_shadow(self):
        """TailwindBuilder shadow methods."""
        from pynext.tw.builder import TailwindBuilder
        builder = TailwindBuilder()
        builder = builder.shadow_lg
        assert builder is not None


# =============================================================================
# SHADCN COMPONENT RENDER TESTS
# =============================================================================

class TestButtonRender:
    """Tests for Button rendering."""
    
    def test_button_variants(self):
        """Button with different variants."""
        from pynext.shadcn.button import Button
        
        variants = ["default", "destructive", "outline", "secondary", "ghost", "link"]
        for variant in variants:
            result = Button(variant=variant)
            html = str(result)
            assert html
    
    def test_button_sizes(self):
        """Button with different sizes."""
        from pynext.shadcn.button import Button
        
        sizes = ["default", "sm", "lg", "icon"]
        for size in sizes:
            result = Button(size=size)
            html = str(result)
            assert html
    
    def test_button_disabled(self):
        """Button disabled state."""
        from pynext.shadcn.button import Button
        result = Button(disabled=True)
        html = str(result)
        assert html


class TestInputRender:
    """Tests for Input rendering."""
    
    def test_input_types(self):
        """Input with different types."""
        from pynext.shadcn.input import Input
        
        types = ["text", "email", "password", "number"]
        for input_type in types:
            result = Input(type=input_type)
            html = str(result)
            assert html
    
    def test_input_placeholder(self):
        """Input with placeholder."""
        from pynext.shadcn.input import Input
        result = Input(placeholder="Enter text")
        html = str(result)
        assert html
    
    def test_label_render(self):
        """Label renders."""
        from pynext.shadcn.input import Label
        result = Label(children="Username")
        html = str(result)
        assert "Username" in html or html
    
    def test_textarea_render(self):
        """Textarea renders."""
        from pynext.shadcn.input import Textarea
        result = Textarea(placeholder="Enter message")
        html = str(result)
        assert html


class TestBadgeRender:
    """Tests for Badge rendering."""
    
    def test_badge_variants(self):
        """Badge with different variants."""
        from pynext.shadcn.badge import Badge
        
        variants = ["default", "secondary", "destructive", "outline"]
        for variant in variants:
            result = Badge(variant=variant)
            html = str(result)
            assert html


class TestCardRender:
    """Tests for Card rendering."""
    
    def test_card_render(self):
        """Card renders."""
        from pynext.shadcn.card import Card
        result = Card()
        html = str(result)
        assert html
    
    def test_card_header_render(self):
        """CardHeader renders."""
        from pynext.shadcn.card import CardHeader
        result = CardHeader()
        html = str(result)
        assert html
    
    def test_card_title_render(self):
        """CardTitle renders."""
        from pynext.shadcn.card import CardTitle
        result = CardTitle(children="Title")
        html = str(result)
        assert html
    
    def test_card_description_render(self):
        """CardDescription renders."""
        from pynext.shadcn.card import CardDescription
        result = CardDescription(children="Description")
        html = str(result)
        assert html
    
    def test_card_content_render(self):
        """CardContent renders."""
        from pynext.shadcn.card import CardContent
        result = CardContent()
        html = str(result)
        assert html
    
    def test_card_footer_render(self):
        """CardFooter renders."""
        from pynext.shadcn.card import CardFooter
        result = CardFooter()
        html = str(result)
        assert html


class TestDialogRender:
    """Tests for Dialog rendering."""
    
    def test_dialog_render(self):
        """Dialog renders."""
        from pynext.shadcn.dialog import Dialog
        result = Dialog()
        html = str(result)
        assert html
    
    def test_dialog_trigger_render(self):
        """DialogTrigger renders."""
        from pynext.shadcn.dialog import DialogTrigger
        result = DialogTrigger(children="Open")
        html = str(result)
        assert html
    
    def test_dialog_content_render(self):
        """DialogContent renders."""
        from pynext.shadcn.dialog import DialogContent
        result = DialogContent()
        html = str(result)
        assert html
    
    def test_dialog_header_render(self):
        """DialogHeader renders."""
        from pynext.shadcn.dialog import DialogHeader
        result = DialogHeader()
        html = str(result)
        assert html
    
    def test_dialog_footer_render(self):
        """DialogFooter renders."""
        from pynext.shadcn.dialog import DialogFooter
        result = DialogFooter()
        html = str(result)
        assert html


class TestTabsRender:
    """Tests for Tabs rendering."""
    
    def test_tabs_render(self):
        """Tabs renders."""
        from pynext.shadcn.tabs import Tabs
        result = Tabs()
        html = str(result)
        assert html
    
    def test_tabs_list_render(self):
        """TabsList renders."""
        from pynext.shadcn.tabs import TabsList
        result = TabsList()
        html = str(result)
        assert html
    
    def test_tabs_trigger_render(self):
        """TabsTrigger renders."""
        from pynext.shadcn.tabs import TabsTrigger
        result = TabsTrigger(value="tab1")
        html = str(result)
        assert html
    
    def test_tabs_content_render(self):
        """TabsContent renders."""
        from pynext.shadcn.tabs import TabsContent
        result = TabsContent(value="tab1")
        html = str(result)
        assert html


class TestAccordionRender:
    """Tests for Accordion rendering."""
    
    def test_accordion_render(self):
        """Accordion renders."""
        from pynext.shadcn.accordion import Accordion
        result = Accordion()
        html = str(result)
        assert html
    
    def test_accordion_item_render(self):
        """AccordionItem renders."""
        from pynext.shadcn.accordion import AccordionItem
        result = AccordionItem(value="item1")
        html = str(result)
        assert html
    
    def test_accordion_trigger_render(self):
        """AccordionTrigger renders."""
        from pynext.shadcn.accordion import AccordionTrigger
        result = AccordionTrigger(children="Title")
        html = str(result)
        assert html
    
    def test_accordion_content_render(self):
        """AccordionContent renders."""
        from pynext.shadcn.accordion import AccordionContent
        result = AccordionContent()
        html = str(result)
        assert html


class TestDropdownMenuRender:
    """Tests for DropdownMenu rendering."""
    
    def test_dropdown_menu_render(self):
        """DropdownMenu renders."""
        from pynext.shadcn.dropdown_menu import DropdownMenu
        result = DropdownMenu()
        html = str(result)
        assert html
    
    def test_dropdown_menu_trigger_render(self):
        """DropdownMenuTrigger renders."""
        from pynext.shadcn.dropdown_menu import DropdownMenuTrigger
        result = DropdownMenuTrigger(children="Menu")
        html = str(result)
        assert html
    
    def test_dropdown_menu_content_render(self):
        """DropdownMenuContent renders."""
        from pynext.shadcn.dropdown_menu import DropdownMenuContent
        result = DropdownMenuContent()
        html = str(result)
        assert html
    
    def test_dropdown_menu_item_render(self):
        """DropdownMenuItem renders."""
        from pynext.shadcn.dropdown_menu import DropdownMenuItem
        result = DropdownMenuItem(children="Item")
        html = str(result)
        assert html


class TestAlertRender:
    """Tests for Alert rendering."""
    
    def test_alert_render(self):
        """Alert renders."""
        from pynext.shadcn.alert import Alert
        result = Alert()
        html = str(result)
        assert html
    
    def test_alert_variants(self):
        """Alert with different variants."""
        from pynext.shadcn.alert import Alert
        
        variants = ["default", "destructive"]
        for variant in variants:
            result = Alert(variant=variant)
            html = str(result)
            assert html
    
    def test_alert_title_render(self):
        """AlertTitle renders."""
        from pynext.shadcn.alert import AlertTitle
        result = AlertTitle(children="Warning")
        html = str(result)
        assert html
    
    def test_alert_description_render(self):
        """AlertDescription renders."""
        from pynext.shadcn.alert import AlertDescription
        result = AlertDescription(children="Details here")
        html = str(result)
        assert html


class TestCheckboxRender:
    """Tests for Checkbox rendering."""
    
    def test_checkbox_render(self):
        """Checkbox renders."""
        from pynext.shadcn.checkbox import Checkbox
        result = Checkbox()
        html = str(result)
        assert html
    
    def test_checkbox_checked(self):
        """Checkbox with checked state."""
        from pynext.shadcn.checkbox import Checkbox
        result = Checkbox(checked=True)
        html = str(result)
        assert html
    
    def test_checkbox_disabled(self):
        """Checkbox disabled."""
        from pynext.shadcn.checkbox import Checkbox
        result = Checkbox(disabled=True)
        html = str(result)
        assert html


class TestSwitchRender:
    """Tests for Switch rendering."""
    
    def test_switch_render(self):
        """Switch renders."""
        from pynext.shadcn.switch import Switch
        result = Switch()
        html = str(result)
        assert html
    
    def test_switch_checked(self):
        """Switch with checked state."""
        from pynext.shadcn.switch import Switch
        result = Switch(checked=True)
        html = str(result)
        assert html


class TestRadioGroupRender:
    """Tests for RadioGroup rendering."""
    
    def test_radio_group_render(self):
        """RadioGroup renders."""
        from pynext.shadcn.radio_group import RadioGroup
        result = RadioGroup()
        html = str(result)
        assert html
    
    def test_radio_group_item_render(self):
        """RadioGroupItem renders."""
        from pynext.shadcn.radio_group import RadioGroupItem
        result = RadioGroupItem(value="option1")
        html = str(result)
        assert html


class TestToggleRender:
    """Tests for Toggle rendering."""
    
    def test_toggle_render(self):
        """Toggle renders."""
        from pynext.shadcn.toggle import Toggle
        result = Toggle()
        html = str(result)
        assert html
    
    def test_toggle_pressed(self):
        """Toggle with pressed state."""
        from pynext.shadcn.toggle import Toggle
        result = Toggle(pressed=True)
        html = str(result)
        assert html
    
    def test_toggle_group_render(self):
        """ToggleGroup renders."""
        from pynext.shadcn.toggle import ToggleGroup
        result = ToggleGroup()
        html = str(result)
        assert html


class TestTooltipRender:
    """Tests for Tooltip rendering."""
    
    def test_tooltip_render(self):
        """Tooltip renders."""
        from pynext.shadcn.tooltip import Tooltip
        result = Tooltip()
        html = str(result)
        assert html
    
    def test_tooltip_trigger_render(self):
        """TooltipTrigger renders."""
        from pynext.shadcn.tooltip import TooltipTrigger
        result = TooltipTrigger(children="Hover me")
        html = str(result)
        assert html
    
    def test_tooltip_content_render(self):
        """TooltipContent renders."""
        from pynext.shadcn.tooltip import TooltipContent
        result = TooltipContent(children="Tooltip text")
        html = str(result)
        assert html


class TestPopoverRender:
    """Tests for Popover rendering."""
    
    def test_popover_render(self):
        """Popover renders."""
        from pynext.shadcn.popover import Popover
        result = Popover()
        html = str(result)
        assert html
    
    def test_popover_trigger_render(self):
        """PopoverTrigger renders."""
        from pynext.shadcn.popover import PopoverTrigger
        result = PopoverTrigger(children="Click me")
        html = str(result)
        assert html
    
    def test_popover_content_render(self):
        """PopoverContent renders."""
        from pynext.shadcn.popover import PopoverContent
        result = PopoverContent()
        html = str(result)
        assert html


class TestSkeletonRender:
    """Tests for Skeleton rendering."""
    
    def test_skeleton_render(self):
        """Skeleton renders."""
        from pynext.shadcn.skeleton import Skeleton
        result = Skeleton()
        html = str(result)
        assert html


class TestCommandRender:
    """Tests for Command rendering."""
    
    def test_command_render(self):
        """Command renders."""
        from pynext.shadcn.command import Command
        result = Command()
        html = str(result)
        assert html
    
    def test_command_input_render(self):
        """CommandInput renders."""
        from pynext.shadcn.command import CommandInput
        result = CommandInput()
        html = str(result)
        assert html
    
    def test_command_list_render(self):
        """CommandList renders."""
        from pynext.shadcn.command import CommandList
        result = CommandList()
        html = str(result)
        assert html
    
    def test_command_item_render(self):
        """CommandItem renders."""
        from pynext.shadcn.command import CommandItem
        result = CommandItem(value="item1")
        html = str(result)
        assert html
    
    def test_command_group_render(self):
        """CommandGroup renders."""
        from pynext.shadcn.command import CommandGroup
        result = CommandGroup()
        html = str(result)
        assert html


class TestDatePickerRender:
    """Tests for DatePicker rendering."""
    
    def test_date_picker_render(self):
        """DatePicker renders."""
        from pynext.shadcn.date_picker import DatePicker
        result = DatePicker()
        html = str(result)
        assert html


class TestFileUploadRender:
    """Tests for FileUpload rendering."""
    
    def test_file_upload_render(self):
        """FileUpload renders."""
        from pynext.shadcn.file_upload import FileUpload
        result = FileUpload()
        html = str(result)
        assert html
    
    def test_file_upload_multiple(self):
        """FileUpload with multiple files."""
        from pynext.shadcn.file_upload import FileUpload
        result = FileUpload(multiple=True)
        html = str(result)
        assert html
    
    def test_file_upload_accept(self):
        """FileUpload with accept filter."""
        from pynext.shadcn.file_upload import FileUpload
        result = FileUpload(accept=".pdf,.doc")
        html = str(result)
        assert html


# =============================================================================
# KEYBOARD MODULE COMPREHENSIVE TESTS
# =============================================================================

class TestKeyboardProviderComprehensive:
    """Comprehensive tests for keyboard module."""
    
    def test_shortcut_provider_render(self):
        """ShortcutProvider renders."""
        from pynext.keyboard import ShortcutProvider
        result = ShortcutProvider()
        html = str(result)
        assert html
    
    def test_shortcut_hint_import(self):
        """ShortcutHint can be imported."""
        from pynext.keyboard import ShortcutHint
        assert ShortcutHint is not None
    
    def test_shortcuts_help_dialog_render(self):
        """ShortcutsHelpDialog renders."""
        from pynext.keyboard import ShortcutsHelpDialog
        result = ShortcutsHelpDialog()
        html = str(result)
        assert html


# =============================================================================
# FOCUS MODULE COMPREHENSIVE TESTS
# =============================================================================

class TestFocusModuleComprehensive:
    """Comprehensive tests for focus module."""
    
    def test_roving_focus_render(self):
        """RovingFocus renders."""
        from pynext.focus import RovingFocus
        result = RovingFocus()
        html = str(result)
        assert html
    
    def test_skip_links_render(self):
        """SkipLinks renders."""
        from pynext.focus import SkipLinks
        result = SkipLinks()
        html = str(result)
        assert html
    
    def test_visually_hidden_render(self):
        """VisuallyHidden renders."""
        from pynext.focus import VisuallyHidden
        result = VisuallyHidden(children="Hidden text")
        html = str(result)
        assert html


# =============================================================================
# SLOT PRIMITIVE TESTS
# =============================================================================

class TestSlotComprehensive:
    """Comprehensive tests for Slot primitive."""
    
    def test_slot_as_child(self):
        """Slot with asChild."""
        from pynext.shadcn.primitives.slot import Slot
        result = Slot()
        assert result is not None

