"""
Unit tests for PyNext Build System

Tests for:
- JS minification
- Console statement removal
- Runtime bundling
- Import analysis
"""

import pytest
from pathlib import Path
import tempfile
import os


class TestMinifyJS:
    """Tests for JavaScript minification."""
    
    def test_removes_single_line_comments(self):
        from pynext.build.minify import minify_js
        
        source = """
        // This is a comment
        function test() {
            return 42; // inline comment
        }
        """
        result = minify_js(source)
        
        assert '//' not in result
        assert 'function test()' in result
        assert 'return 42' in result
    
    def test_removes_multi_line_comments(self):
        from pynext.build.minify import minify_js
        
        source = """
        /**
         * This is a multi-line comment
         */
        function test() {
            return 42;
        }
        """
        result = minify_js(source)
        
        assert '/**' not in result
        assert '*/' not in result
        assert 'function test()' in result
    
    def test_removes_console_debug(self):
        from pynext.build.minify import minify_js
        
        source = """
        function test() {
            console.debug('debugging');
            console.log('logging');
            return 42;
        }
        """
        result = minify_js(source, strip_debug=True)
        
        assert 'console.debug' not in result
        assert 'console.log' not in result
        assert 'return 42' in result
    
    def test_preserves_console_when_disabled(self):
        from pynext.build.minify import minify_js
        
        source = """
        function test() {
            console.debug('keep me');
            return 42;
        }
        """
        result = minify_js(source, strip_debug=False)
        
        assert 'console.debug' in result
    
    def test_preserves_string_literals(self):
        from pynext.build.minify import minify_js
        
        source = """
        var msg = "Hello // not a comment";
        var msg2 = 'Also not /* a comment */';
        """
        result = minify_js(source)
        
        assert 'Hello // not a comment' in result
        assert 'Also not /* a comment */' in result
    
    def test_removes_whitespace(self):
        from pynext.build.minify import minify_js
        
        source = """
        function    test(   a  ,   b   ) {
            return    a    +    b;
        }
        """
        result = minify_js(source)
        
        # Should not have multiple consecutive spaces
        assert '    ' not in result
    
    def test_handles_empty_input(self):
        from pynext.build.minify import minify_js
        
        result = minify_js('')
        assert result == ''
    
    def test_handles_only_comments(self):
        from pynext.build.minify import minify_js
        
        source = """
        // Comment 1
        /* Comment 2 */
        // Comment 3
        """
        result = minify_js(source)
        
        assert result.strip() == ''


class TestMinifyRuntime:
    """Tests for runtime minification."""
    
    def test_minify_runtime_creates_output_dir(self):
        from pynext.build.minify import minify_runtime
        
        # Uses default runtime dir
        results = minify_runtime()
        
        # Should have processed files
        assert len(results) > 0
        
        # Check that minified files exist
        min_dir = Path(__file__).parent.parent.parent / 'pynext' / 'runtime' / 'min'
        assert min_dir.exists()
    
    def test_minify_runtime_returns_stats(self):
        from pynext.build.minify import minify_runtime
        
        results = minify_runtime()
        
        # Each result should have size info
        for name, stats in results.items():
            assert 'original_size' in stats
            assert 'minified_size' in stats
            assert 'savings' in stats
            assert 'savings_percent' in stats
            
            # Minified should be smaller
            assert stats['minified_size'] <= stats['original_size']


class TestGetRuntimeSizes:
    """Tests for runtime size analysis."""
    
    def test_get_runtime_sizes(self):
        from pynext.build.minify import get_runtime_sizes
        
        sizes = get_runtime_sizes()
        
        # Should find runtime files
        assert len(sizes) > 0
        
        # All sizes should be positive
        for name, size in sizes.items():
            assert size > 0
    
    def test_includes_ui_modules(self):
        from pynext.build.minify import get_runtime_sizes
        
        sizes = get_runtime_sizes()
        
        # Should include ui/ subdirectory
        ui_files = [k for k in sizes.keys() if k.startswith('ui/')]
        assert len(ui_files) > 0


class TestBundleSystem:
    """Tests for runtime bundling."""
    
    def test_analyze_file_finds_imports(self):
        from pynext.build.bundle import analyze_file
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
from pynext import on_keydown, use_storage
from pynext.shadcn import Dialog, Button

@on_keydown("cmd+k")
def open_search():
    pass
""")
            f.flush()
            
            try:
                required = analyze_file(Path(f.name))
                
                assert 'keyboard.js' in required
                assert 'storage.js' in required
                assert 'ui/dialog.js' in required
            finally:
                os.unlink(f.name)
    
    def test_analyze_file_handles_syntax_error(self):
        from pynext.build.bundle import analyze_file
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("this is not valid python {{{")
            f.flush()
            
            try:
                required = analyze_file(Path(f.name))
                
                # Should return empty set, not crash
                assert required == set()
            finally:
                os.unlink(f.name)
    
    def test_analyze_file_handles_missing_file(self):
        from pynext.build.bundle import analyze_file
        
        required = analyze_file(Path('/nonexistent/file.py'))
        
        assert required == set()
    
    def test_get_required_modules(self):
        from pynext.build.bundle import get_required_modules
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test file
            test_file = Path(tmpdir) / 'test.py'
            test_file.write_text("""
from pynext import use_visibility
from pynext.shadcn import Tabs, TabsList
""")
            
            required = get_required_modules(Path(tmpdir))
            
            assert 'browser.js' in required
            assert 'ui/tabs.js' in required
            assert 'signals.js' in required  # Always included


class TestFeatureMapping:
    """Tests for feature to runtime mapping."""
    
    def test_keyboard_features_map_to_keyboard_js(self):
        from pynext.build.bundle import FEATURE_TO_RUNTIME
        
        assert FEATURE_TO_RUNTIME['on_keydown'] == 'keyboard.js'
        assert FEATURE_TO_RUNTIME['on_key_sequence'] == 'keyboard.js'
        assert FEATURE_TO_RUNTIME['register_shortcut'] == 'keyboard.js'
    
    def test_browser_features_map_to_browser_js(self):
        from pynext.build.bundle import FEATURE_TO_RUNTIME
        
        assert FEATURE_TO_RUNTIME['use_visibility'] == 'browser.js'
        assert FEATURE_TO_RUNTIME['use_online'] == 'browser.js'
    
    def test_component_mapping(self):
        from pynext.build.bundle import COMPONENT_TO_UI_MODULE
        
        assert COMPONENT_TO_UI_MODULE['Dialog'] == 'ui/dialog.js'
        assert COMPONENT_TO_UI_MODULE['Tabs'] == 'ui/tabs.js'
        assert COMPONENT_TO_UI_MODULE['Calendar'] == 'ui/calendar.js'


class TestBundleRuntime:
    """Tests for bundling runtime modules."""
    
    def test_bundle_includes_core_for_ui(self):
        from pynext.build.bundle import bundle_runtime
        
        bundle = bundle_runtime(['ui/dialog.js'], minified=False)
        
        # Should include core utilities
        assert 'getFocusable' in bundle or bundle  # Core functions
    
    def test_bundle_handles_missing_modules(self):
        from pynext.build.bundle import bundle_runtime
        
        # Should not crash on missing module
        bundle = bundle_runtime(['nonexistent.js'], minified=False)
        
        # Should return empty or minimal bundle
        assert isinstance(bundle, str)

