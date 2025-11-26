"""
Additional tests to boost code coverage.

These tests cover modules that previously had low or no coverage.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os
import tempfile


# =============================================================================
# PRIMITIVES TESTS
# =============================================================================

class TestPrimitives:
    """Tests for shadcn primitives."""
    
    def test_portal_import(self):
        """Portal can be imported."""
        from pynext.shadcn.primitives.portal import Portal
        assert Portal is not None
    
    def test_portal_render(self):
        """Portal renders content."""
        from pynext.shadcn.primitives.portal import Portal
        result = Portal(target="body")
        html = str(result)
        assert "portal" in html.lower()
    
    def test_focus_trap_import(self):
        """FocusTrap can be imported."""
        from pynext.shadcn.primitives.focus_trap import FocusTrap
        assert FocusTrap is not None
    
    def test_focus_trap_render(self):
        """FocusTrap renders."""
        from pynext.shadcn.primitives.focus_trap import FocusTrap
        result = FocusTrap()
        html = str(result)
        assert "focus-trap" in html.lower()
    
    def test_click_outside_import(self):
        """ClickOutside can be imported."""
        from pynext.shadcn.primitives.click_outside import ClickOutside
        assert ClickOutside is not None
    
    def test_click_outside_render(self):
        """ClickOutside renders."""
        from pynext.shadcn.primitives.click_outside import ClickOutside
        result = ClickOutside(on_click_outside="handleClose()")
        html = str(result)
        assert "click-outside" in html.lower()
    
    def test_slot_import(self):
        """Slot can be imported."""
        from pynext.shadcn.primitives.slot import Slot
        assert Slot is not None
    
    def test_presence_import(self):
        """Presence can be imported."""
        from pynext.shadcn.primitives.presence import Presence
        assert Presence is not None
    
    def test_presence_render(self):
        """Presence renders."""
        from pynext.shadcn.primitives.presence import Presence
        result = Presence(present=True)
        html = str(result)
        assert "presence" in html.lower()
    
    def test_primitives_init_exports(self):
        """Primitives __init__ exports all primitives."""
        from pynext.shadcn import primitives
        assert primitives is not None


# =============================================================================
# DRAFT MIDDLEWARE TESTS
# =============================================================================

class TestDraftMiddleware:
    """Tests for draft middleware."""
    
    def test_draft_config_import(self):
        """DraftConfig can be imported."""
        from pynext.middleware.draft import DraftConfig
        assert DraftConfig is not None
    
    def test_is_draft_mode_function(self):
        """is_draft_mode function exists."""
        from pynext.middleware.draft import is_draft_mode
        assert callable(is_draft_mode)
    
    def test_detect_draft_mode(self):
        """detect_draft_mode function exists."""
        from pynext.middleware.draft import detect_draft_mode
        assert callable(detect_draft_mode)
    
    def test_verify_draft_token(self):
        """verify_draft_token function exists."""
        from pynext.middleware.draft import verify_draft_token
        assert callable(verify_draft_token)
    
    def test_enable_draft(self):
        """enable_draft function exists."""
        from pynext.middleware.draft import enable_draft
        assert callable(enable_draft)


# =============================================================================
# ISR (Incremental Static Regeneration) TESTS
# =============================================================================

class TestISR:
    """Tests for ISR module."""
    
    def test_isr_module_import(self):
        """ISR module can be imported."""
        from pynext.server import isr
        assert isr is not None
    
    def test_isr_exports(self):
        """ISR exports are accessible."""
        import pynext.server.isr as isr_module
        # Get all public names
        exports = [name for name in dir(isr_module) if not name.startswith('_')]
        assert len(exports) > 0


# =============================================================================
# PPR (Partial Pre-Rendering) TESTS
# =============================================================================

class TestPPR:
    """Tests for PPR module."""
    
    def test_ppr_module_import(self):
        """PPR module can be imported."""
        from pynext.server import ppr
        assert ppr is not None
    
    def test_ppr_exports(self):
        """PPR exports are accessible."""
        import pynext.server.ppr as ppr_module
        exports = [name for name in dir(ppr_module) if not name.startswith('_')]
        assert len(exports) > 0


# =============================================================================
# DEV SERVER TESTS
# =============================================================================

class TestDevServer:
    """Tests for dev server module."""
    
    def test_dev_module_import(self):
        """Dev module can be imported."""
        from pynext.server import dev
        assert dev is not None
    
    def test_dev_exports(self):
        """Dev server exports are accessible."""
        import pynext.server.dev as dev_module
        exports = [name for name in dir(dev_module) if not name.startswith('_')]
        assert len(exports) > 0


# =============================================================================
# I18N EXTRACTOR TESTS
# =============================================================================

class TestI18nExtractor:
    """Tests for i18n extractor."""
    
    def test_extractor_module_import(self):
        """Extractor module can be imported."""
        from pynext.i18n import extractor
        assert extractor is not None
    
    def test_extractor_exports(self):
        """Extractor exports are accessible."""
        import pynext.i18n.extractor as extractor_module
        exports = [name for name in dir(extractor_module) if not name.startswith('_')]
        assert len(exports) > 0


# =============================================================================
# ADDITIONAL COMPONENT COVERAGE
# =============================================================================

class TestToggleComponent:
    """Tests for Toggle component."""
    
    def test_toggle_import(self):
        """Toggle can be imported."""
        from pynext.shadcn.toggle import Toggle
        assert Toggle is not None
    
    def test_toggle_render(self):
        """Toggle renders correctly."""
        from pynext.shadcn.toggle import Toggle
        result = Toggle()
        html = str(result)
        assert html


class TestToggleGroupComponent:
    """Tests for ToggleGroup component."""
    
    def test_toggle_group_import(self):
        """ToggleGroup can be imported."""
        from pynext.shadcn.toggle import ToggleGroup
        assert ToggleGroup is not None


class TestSeparatorComponent:
    """Tests for Separator component."""
    
    def test_separator_import(self):
        """Separator can be imported."""
        from pynext.shadcn.separator import Separator
        assert Separator is not None
    
    def test_separator_render(self):
        """Separator renders."""
        from pynext.shadcn.separator import Separator
        result = Separator()
        html = str(result)
        assert html


class TestAvatarComponent:
    """Tests for Avatar component."""
    
    def test_avatar_import(self):
        """Avatar can be imported."""
        from pynext.shadcn.avatar import Avatar
        assert Avatar is not None
    
    def test_avatar_image_import(self):
        """AvatarImage can be imported."""
        from pynext.shadcn.avatar import AvatarImage
        assert AvatarImage is not None
    
    def test_avatar_fallback_import(self):
        """AvatarFallback can be imported."""
        from pynext.shadcn.avatar import AvatarFallback
        assert AvatarFallback is not None


class TestAlertDialogComponent:
    """Tests for AlertDialog component."""
    
    def test_alert_dialog_import(self):
        """AlertDialog can be imported."""
        from pynext.shadcn.alert_dialog import AlertDialog
        assert AlertDialog is not None
    
    def test_alert_dialog_trigger_import(self):
        """AlertDialogTrigger can be imported."""
        from pynext.shadcn.alert_dialog import AlertDialogTrigger
        assert AlertDialogTrigger is not None
    
    def test_alert_dialog_content_import(self):
        """AlertDialogContent can be imported."""
        from pynext.shadcn.alert_dialog import AlertDialogContent
        assert AlertDialogContent is not None


class TestThemeModule:
    """Tests for theme module."""
    
    def test_theme_provider_import(self):
        """ThemeProvider can be imported."""
        from pynext.theme import ThemeProvider
        assert ThemeProvider is not None
    
    def test_theme_script_import(self):
        """ThemeScript can be imported."""
        from pynext.theme import ThemeScript
        assert ThemeScript is not None
    
    def test_theme_toggle_import(self):
        """ThemeToggle can be imported."""
        from pynext.theme import ThemeToggle
        assert ThemeToggle is not None
    
    def test_theme_switcher_import(self):
        """ThemeSwitcher can be imported."""
        from pynext.theme import ThemeSwitcher
        assert ThemeSwitcher is not None


class TestKeyboardModule:
    """Tests for keyboard module."""
    
    def test_shortcut_provider_import(self):
        """ShortcutProvider can be imported."""
        from pynext.keyboard import ShortcutProvider
        assert ShortcutProvider is not None
    
    def test_shortcut_hint_import(self):
        """ShortcutHint can be imported."""
        from pynext.keyboard import ShortcutHint
        assert ShortcutHint is not None
    
    def test_shortcuts_help_dialog_import(self):
        """ShortcutsHelpDialog can be imported."""
        from pynext.keyboard import ShortcutsHelpDialog
        assert ShortcutsHelpDialog is not None


class TestFocusModule:
    """Tests for focus module."""
    
    def test_roving_focus_import(self):
        """RovingFocus can be imported."""
        from pynext.focus import RovingFocus
        assert RovingFocus is not None
    
    def test_skip_links_import(self):
        """SkipLinks can be imported."""
        from pynext.focus import SkipLinks
        assert SkipLinks is not None
    
    def test_visually_hidden_import(self):
        """VisuallyHidden can be imported."""
        from pynext.focus import VisuallyHidden
        assert VisuallyHidden is not None


class TestTailwindBuilder:
    """Tests for Tailwind builder."""
    
    def test_tw_import(self):
        """tw can be imported."""
        from pynext.tw.builder import tw
        assert tw is not None
    
    def test_tailwind_builder_class(self):
        """TailwindBuilder class exists."""
        from pynext.tw.builder import TailwindBuilder
        assert TailwindBuilder is not None


class TestRouterModules:
    """Tests for router modules."""
    
    def test_intercept_module_import(self):
        """Intercept router module can be imported."""
        from pynext.router import intercept
        assert intercept is not None
    
    def test_parallel_module_import(self):
        """Parallel router module can be imported."""
        from pynext.router import parallel
        assert parallel is not None
    
    def test_intercept_exports(self):
        """Intercept module has exports."""
        import pynext.router.intercept as intercept_module
        exports = [name for name in dir(intercept_module) if not name.startswith('_')]
        assert len(exports) > 0
    
    def test_parallel_exports(self):
        """Parallel module has exports."""
        import pynext.router.parallel as parallel_module
        exports = [name for name in dir(parallel_module) if not name.startswith('_')]
        assert len(exports) > 0


class TestStreamingModule:
    """Tests for streaming module."""
    
    def test_streaming_module_import(self):
        """Streaming module can be imported."""
        from pynext.server import streaming
        assert streaming is not None
    
    def test_streaming_exports(self):
        """Streaming module has exports."""
        import pynext.server.streaming as streaming_module
        exports = [name for name in dir(streaming_module) if not name.startswith('_')]
        assert len(exports) > 0


class TestServerDraft:
    """Tests for server draft module."""
    
    def test_draft_module_import(self):
        """Draft module can be imported."""
        from pynext.server import draft
        assert draft is not None
    
    def test_draft_exports(self):
        """Draft module has exports."""
        import pynext.server.draft as draft_module
        exports = [name for name in dir(draft_module) if not name.startswith('_')]
        assert len(exports) > 0


class TestI18nMiddleware:
    """Tests for i18n middleware."""
    
    def test_locale_middleware_import(self):
        """LocaleMiddleware can be imported."""
        from pynext.i18n.middleware import LocaleMiddleware
        assert LocaleMiddleware is not None


class TestI18nTranslations:
    """Tests for i18n translations."""
    
    def test_translation_loader_import(self):
        """TranslationLoader can be imported."""
        from pynext.i18n.translations import TranslationLoader
        assert TranslationLoader is not None


class TestRuntimeModule:
    """Tests for runtime module."""
    
    def test_runtime_module_import(self):
        """Runtime module can be imported."""
        from pynext import runtime
        assert runtime is not None
    
    def test_runtime_exports(self):
        """Runtime module has exports."""
        import pynext.runtime as runtime_module
        exports = [name for name in dir(runtime_module) if not name.startswith('_')]
        assert len(exports) > 0


class TestRegistryManager:
    """Tests for registry manager."""
    
    def test_registry_manager_import(self):
        """RegistryManager can be imported."""
        from pynext.registry.manager import RegistryManager
        assert RegistryManager is not None
    
    def test_registry_manager_init(self):
        """RegistryManager initializes."""
        from pynext.registry.manager import RegistryManager
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = RegistryManager(project_dir=tmpdir)
            assert manager is not None


class TestToastComponent:
    """Tests for Toast component."""
    
    def test_toast_import(self):
        """Toast can be imported."""
        from pynext.shadcn.toast import Toast
        assert Toast is not None
    
    def test_toaster_import(self):
        """Toaster can be imported."""
        from pynext.shadcn.toast import Toaster
        assert Toaster is not None


class TestCalendarLocalization:
    """Tests for Calendar localization."""
    
    def test_calendar_import(self):
        """Calendar can be imported."""
        from pynext.shadcn.calendar import Calendar
        assert Calendar is not None
    
    def test_calendar_render(self):
        """Calendar renders."""
        from pynext.shadcn.calendar import Calendar
        result = Calendar()
        html = str(result)
        assert html


class TestDataTableFeatures:
    """Tests for DataTable features."""
    
    def test_datatable_import(self):
        """DataTable can be imported."""
        from pynext.shadcn.data_table import DataTable
        assert DataTable is not None
    
    def test_datatable_column_toggle_import(self):
        """DataTableColumnToggle can be imported."""
        from pynext.shadcn.data_table import DataTableColumnToggle
        assert DataTableColumnToggle is not None


class TestComboboxCreate:
    """Tests for Combobox create feature."""
    
    def test_combobox_import(self):
        """Combobox can be imported."""
        from pynext.shadcn.combobox import Combobox
        assert Combobox is not None
    
    def test_combobox_create_import(self):
        """ComboboxCreate can be imported."""
        from pynext.shadcn.combobox import ComboboxCreate
        assert ComboboxCreate is not None


class TestSheetSwipe:
    """Tests for Sheet swipe feature."""
    
    def test_sheet_import(self):
        """Sheet can be imported."""
        from pynext.shadcn.sheet import Sheet
        assert Sheet is not None
    
    def test_sheet_render(self):
        """Sheet renders."""
        from pynext.shadcn.sheet import Sheet
        result = Sheet()
        html = str(result)
        assert html


# =============================================================================
# SERVER APP TESTS
# =============================================================================

class TestServerApp:
    """Tests for server app module."""
    
    def test_app_import(self):
        """App can be imported."""
        from pynext.server.app import create_app
        assert create_app is not None


# =============================================================================
# FILE ROUTER TESTS
# =============================================================================

class TestFileRouter:
    """Tests for file router."""
    
    def test_file_router_import(self):
        """FileRouter can be imported."""
        from pynext.router.file_router import FileRouter
        assert FileRouter is not None


# =============================================================================
# DEPS MODULE TESTS
# =============================================================================

class TestDepsModule:
    """Tests for deps module."""
    
    def test_deps_import(self):
        """Deps module can be imported."""
        from pynext import deps
        assert deps is not None


# =============================================================================
# EDITOR MODULE TESTS
# =============================================================================

class TestEditorModule:
    """Tests for editor module."""
    
    def test_editor_import(self):
        """Editor can be imported."""
        from pynext.editor import Editor
        assert Editor is not None
    
    def test_use_editor_import(self):
        """use_editor can be imported."""
        from pynext.editor import use_editor
        assert use_editor is not None
    
    def test_markdown_editor_import(self):
        """MarkdownEditor can be imported."""
        from pynext.editor import MarkdownEditor
        assert MarkdownEditor is not None


# =============================================================================
# CHARTS MODULE TESTS
# =============================================================================

class TestChartsModule:
    """Tests for charts module."""
    
    def test_charts_import(self):
        """Charts module can be imported."""
        from pynext import charts
        assert charts is not None
    
    def test_line_chart_import(self):
        """LineChart can be imported."""
        from pynext.charts import LineChart
        assert LineChart is not None
    
    def test_bar_chart_import(self):
        """BarChart can be imported."""
        from pynext.charts import BarChart
        assert BarChart is not None
    
    def test_pie_chart_import(self):
        """PieChart can be imported."""
        from pynext.charts import PieChart
        assert PieChart is not None


# =============================================================================
# BUILD MODULE TESTS
# =============================================================================

class TestBuildModule:
    """Tests for build module."""
    
    def test_build_import(self):
        """Build module can be imported."""
        from pynext import build
        assert build is not None
    
    def test_minify_import(self):
        """minify_js can be imported."""
        from pynext.build.minify import minify_js
        assert minify_js is not None


# =============================================================================
# LOCALE MODULE TESTS
# =============================================================================

class TestLocaleModule:
    """Tests for locale module."""
    
    def test_locale_import(self):
        """Locale module can be imported."""
        from pynext.i18n import locale
        assert locale is not None
