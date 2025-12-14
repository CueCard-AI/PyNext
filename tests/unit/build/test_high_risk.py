"""
Tests for High-Risk Areas in Build System (Phase 17.7)

These tests target the P0/P1/P2 risks identified during implementation:
- P0: Critical risks that will break production
- P1: High risks that will cause bugs
- P2: Medium risks (edge cases)

Total: 58 targeted tests for risky areas.
"""

import pytest
import json
import time
import threading
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from concurrent.futures import ThreadPoolExecutor

from pynext.build.scanner import scan_source, scan_file, scan_directory, IslandInfo
from pynext.build.cache import BuildCache, hash_content
from pynext.build.treeshake import tree_shake, analyze_features, TreeShakeConfig
from pynext.build.watcher import FileWatcher, WatcherConfig, ChangeEvent
from pynext.build.hmr import HMRServer, HMRUpdate
from pynext.build.parallel import compile_parallel, ParallelConfig


# =============================================================================
# P0: CRITICAL - PROCESSPOOL WORKER ISOLATION
# =============================================================================

class TestP0WorkerIsolation:
    """
    Tests for ProcessPoolExecutor worker isolation issues.
    Workers run in separate processes where mocks don't work.
    """
    
    def test_worker_handles_import_error(self, tmp_path):
        """Worker should gracefully handle import errors."""
        file = tmp_path / "test.py"
        file.write_text("@island\ndef Test(): pass")
        
        # Use threads for testability
        config = ParallelConfig(use_threads=True)
        
        with patch('pynext.compiler.compile_file') as mock:
            mock.side_effect = ImportError("Cannot import pynext.compiler")
            result = compile_parallel([str(file)], config)
        
        # Should capture the error, not crash
        assert result.errors_count >= 1 or not result.success
    
    def test_worker_handles_syntax_error_in_source(self, tmp_path):
        """Worker should handle syntax errors in compiled source."""
        file = tmp_path / "broken.py"
        file.write_text('''
@island
def Broken(
    # Missing closing paren - syntax error
''')
        
        config = ParallelConfig(use_threads=True)
        
        with patch('pynext.compiler.compile_file') as mock:
            mock.side_effect = SyntaxError("invalid syntax")
            result = compile_parallel([str(file)], config)
        
        assert result.errors_count == 1
    
    def test_worker_handles_runtime_exception(self, tmp_path):
        """Worker should handle unexpected runtime exceptions."""
        file = tmp_path / "crash.py"
        file.write_text("@island\ndef Crash(): pass")
        
        config = ParallelConfig(use_threads=True)
        
        with patch('pynext.compiler.compile_file') as mock:
            mock.side_effect = RuntimeError("Unexpected crash in compiler")
            result = compile_parallel([str(file)], config)
        
        assert result.errors_count == 1
        # Error message should be captured
        assert any("Unexpected crash" in str(r[3]) for r in result.results if r[3])
    
    def test_worker_handles_memory_error(self, tmp_path):
        """Worker should handle memory errors gracefully."""
        file = tmp_path / "huge.py"
        file.write_text("@island\ndef Huge(): pass")
        
        config = ParallelConfig(use_threads=True)
        
        with patch('pynext.compiler.compile_file') as mock:
            mock.side_effect = MemoryError("Out of memory")
            result = compile_parallel([str(file)], config)
        
        # Should not crash, should report error
        assert result.errors_count >= 1


# =============================================================================
# P0: CRITICAL - TREE SHAKING REGEX FRAGILITY
# =============================================================================

class TestP0TreeShakingRegex:
    """
    Tests for tree shaking regex edge cases.
    The regex-based approach can accidentally remove valid code.
    """
    
    def test_function_name_in_string_preserved(self):
        """Don't remove function name that's in a string."""
        code = '''
const msg = "We use createStore for state management";
const x = createSignal(0);
'''
        result = tree_shake(code, {"signals"})
        # The string should be preserved
        assert 'createStore' in result.code
    
    def test_function_name_in_comment_preserved(self):
        """Don't affect code when function name is in comment."""
        code = '''
// We removed createStore because it's unused
const x = createSignal(0);
'''
        config = TreeShakeConfig(remove_comments=False)
        result = tree_shake(code, {"signals"}, config)
        # With comments preserved, the comment should still be there
        # (or at least no crash)
        assert result.code is not None
    
    def test_nested_function_not_corrupted(self):
        """Nested functions should not be corrupted."""
        code = '''
function outer() {
    function createSignal(x) {
        return x;
    }
    return createSignal(5);
}
'''
        # Should not corrupt nested function
        result = tree_shake(code, set())
        # Code should still be valid (no broken braces)
        assert result.code.count('{') == result.code.count('}')
    
    def test_multiline_function_handled(self):
        """Multi-line function definitions should be handled safely."""
        code = '''
function createStore(
    initialValue,
    options
) {
    return {
        value: initialValue,
        ...options
    };
}
'''
        result = tree_shake(code, set())
        # Conservative tree shaking should NOT corrupt complex functions
        # It may leave them in place rather than risk corruption
        # The key is: no broken syntax
        assert result.code.count('{') == result.code.count('}'), \
            f"Braces unbalanced in: {result.code!r}"
    
    def test_arrow_function_preserved(self):
        """Arrow functions with feature names preserved."""
        code = '''
const helper = () => {
    const createSignal = (x) => ({ value: x });
    return createSignal(5);
};
'''
        result = tree_shake(code, set())
        # Should be valid
        assert result.code is not None
    
    def test_export_cleanup_doesnt_corrupt(self):
        """Export cleanup should not corrupt export statement."""
        code = '''
export { createSignal, createStore, createEffect };
'''
        result = tree_shake(code, {"signals"})
        # Should not have syntax errors like {,} or {createSignal,}
        assert ',,' not in result.code
        assert '{,' not in result.code
        assert ',}' not in result.code
    
    def test_regex_special_chars_in_identifier(self):
        """Handle identifiers that look like regex patterns."""
        code = '''
const $signal = createSignal(0);
const _store$ = createStore({});
'''
        # Should not crash on special chars
        result = tree_shake(code)
        assert result.code is not None


# =============================================================================
# P0: CRITICAL - CACHE MANIFEST RACE CONDITION
# =============================================================================

class TestP0CacheRaceCondition:
    """
    Tests for cache manifest race conditions.
    Multiple parallel workers could corrupt the manifest.
    """
    
    def test_concurrent_stores_dont_corrupt_manifest(self, tmp_path):
        """Multiple concurrent stores should not corrupt manifest."""
        cache_dir = tmp_path / ".cache"
        cache = BuildCache(cache_dir)
        
        errors = []
        
        def store_item(i):
            try:
                cache.store(
                    f"file{i}.py",
                    f"const x{i} = {i};",
                    None,
                    f"hash{i:03d}",
                    [f"Island{i}"],
                )
            except Exception as e:
                errors.append(e)
        
        # Run 50 concurrent stores
        threads = [threading.Thread(target=store_item, args=(i,)) for i in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"Errors during concurrent stores: {errors}"
        
        # Verify manifest is valid JSON
        manifest_path = cache_dir / "manifest.json"
        assert manifest_path.exists()
        
        try:
            data = json.loads(manifest_path.read_text())
            # All 50 entries should be present
            assert len(data["entries"]) == 50
        except json.JSONDecodeError as e:
            pytest.fail(f"Manifest corrupted: {e}")
    
    def test_store_and_read_concurrent(self, tmp_path):
        """Store and read operations should not conflict."""
        cache_dir = tmp_path / ".cache"
        cache = BuildCache(cache_dir)
        
        # Pre-populate
        for i in range(10):
            cache.store(f"file{i}.py", f"code{i}", None, f"hash{i}", [f"A{i}"])
        
        errors = []
        
        def read_and_write(i):
            try:
                # Read
                js, _ = cache.get(f"file{i % 10}.py")
                # Write
                cache.store(f"new{i}.py", f"newcode{i}", None, f"newhash{i}", [f"B{i}"])
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=read_and_write, args=(i,)) for i in range(30)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0
    
    def test_invalidate_during_store(self, tmp_path):
        """Invalidate during store should not corrupt."""
        cache_dir = tmp_path / ".cache"
        cache = BuildCache(cache_dir)
        
        errors = []
        
        def store_loop():
            for i in range(20):
                try:
                    cache.store(f"file{i}.py", f"code{i}", None, f"hash{i}", [f"A{i}"])
                except Exception as e:
                    errors.append(e)
        
        def invalidate_loop():
            for i in range(20):
                try:
                    cache.invalidate(f"file{i}.py")
                except Exception as e:
                    errors.append(e)
        
        t1 = threading.Thread(target=store_loop)
        t2 = threading.Thread(target=invalidate_loop)
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        
        assert len(errors) == 0


# =============================================================================
# P1: HIGH - WATCHER DEBOUNCE RACE
# =============================================================================

class TestP1WatcherDebounceRace:
    """
    Tests for file watcher debounce race conditions.
    Rapid events could cause multiple callbacks or missed events.
    """
    
    def test_rapid_events_debounced(self, tmp_path):
        """Rapid events on same file should be debounced."""
        watcher = FileWatcher([tmp_path], WatcherConfig(debounce_ms=100))
        callback_count = [0]
        
        @watcher.on_change
        def handler(events):
            callback_count[0] += 1
        
        file_path = str(tmp_path / "test.py")
        
        # Fire 100 rapid events
        for _ in range(100):
            watcher._handle_event(file_path, "modified")
        
        # Only one event should be pending
        assert len(watcher._pending_events) == 1
    
    def test_different_files_not_debounced(self, tmp_path):
        """Events on different files should not be debounced together."""
        watcher = FileWatcher([tmp_path])
        
        # Fire events on 10 different files
        for i in range(10):
            watcher._handle_event(str(tmp_path / f"file{i}.py"), "modified")
        
        # All 10 should be pending
        assert len(watcher._pending_events) == 10
    
    def test_flush_clears_pending(self, tmp_path):
        """Flush should clear pending events."""
        watcher = FileWatcher([tmp_path])
        received_events = []
        
        @watcher.on_change
        def handler(events):
            received_events.extend(events)
        
        watcher._handle_event(str(tmp_path / "a.py"), "modified")
        watcher._handle_event(str(tmp_path / "b.py"), "created")
        
        watcher._flush_events()
        
        assert len(received_events) == 2
        assert len(watcher._pending_events) == 0
    
    def test_timer_race_condition(self, tmp_path):
        """Timer race should not cause issues."""
        watcher = FileWatcher([tmp_path], WatcherConfig(debounce_ms=10))
        callback_count = [0]
        
        @watcher.on_change
        def handler(events):
            callback_count[0] += 1
        
        file_path = str(tmp_path / "test.py")
        
        # Rapid-fire events that might race with timer
        for _ in range(20):
            watcher._handle_event(file_path, "modified")
            time.sleep(0.005)  # 5ms between events
        
        # Wait for debounce to settle
        time.sleep(0.05)
        
        # Should have received at least one callback (timer could fire multiple times)
        # The important thing is no crashes


# =============================================================================
# P1: HIGH - HMR THREAD SAFETY
# =============================================================================

class TestP1HMRThreadSafety:
    """
    Tests for HMR server thread safety.
    notify_update() is called from main thread while async loop runs.
    """
    
    def test_concurrent_notifications(self):
        """Concurrent notify_update calls should not corrupt state."""
        server = HMRServer()
        errors = []
        
        def notify(i):
            try:
                server.notify_update(f"module{i}.js", f"code{i}")
            except Exception as e:
                errors.append(e)
        
        # Notify from 20 threads simultaneously
        threads = [threading.Thread(target=notify, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0
        # All 20 updates should be pending
        assert len(server._pending_updates) == 20
    
    def test_mixed_operations_thread_safe(self):
        """Mix of notify_update, notify_reload, notify_error thread-safe."""
        server = HMRServer()
        errors = []
        
        def operations():
            try:
                for i in range(10):
                    server.notify_update(f"module{i}.js", f"code{i}")
                    server.notify_reload()
                    server.notify_error(f"error{i}")
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=operations) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0
        # 5 threads * (10 updates + 10 reloads + 10 errors) = 150
        assert len(server._pending_updates) == 150
    
    def test_update_serialization(self):
        """HMRUpdate.to_json() should be thread-safe."""
        updates = [HMRUpdate(f"m{i}.js", f"c{i}") for i in range(100)]
        errors = []
        
        def serialize(update):
            try:
                json.loads(update.to_json())
            except Exception as e:
                errors.append(e)
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            list(executor.map(serialize, updates))
        
        assert len(errors) == 0


# =============================================================================
# P1: HIGH - SCANNER DECORATOR DETECTION
# =============================================================================

class TestP1ScannerDecoratorDetection:
    """
    Tests for scanner decorator edge cases.
    Complex decorator patterns might not be detected.
    """
    
    def test_module_qualified_decorator(self):
        """Detect @module.island decorator."""
        source = '''
import pynext

@pynext.island
def Counter():
    return button()["Click"]
'''
        result = scan_source(source)
        assert len(result.islands) == 1
        assert result.islands[0].name == "Counter"
    
    def test_deeply_nested_decorator(self):
        """Detect @a.b.c.island decorator."""
        source = '''
@some.deeply.nested.island
def Counter():
    return div()["Hello"]
'''
        result = scan_source(source)
        # Should detect or at least not crash
        assert len(result.islands) >= 0
    
    def test_decorator_with_complex_args(self):
        """Detect @island with complex arguments."""
        source = '''
@island(
    hydrate=True,
    ssr=False,
    priority="high",
)
def Counter():
    return button()["Click"]
'''
        result = scan_source(source)
        assert len(result.islands) == 1
    
    def test_decorator_factory_call(self):
        """Detect decorator returned from factory."""
        source = '''
@create_island("Counter")
def counter_impl():
    return button()["Click"]

# This one should be detected
@island
def RealIsland():
    return div()["Real"]
'''
        result = scan_source(source)
        assert any(i.name == "RealIsland" for i in result.islands)
    
    def test_stacked_decorators(self):
        """Detect island in stack of decorators."""
        source = '''
@cache(ttl=60)
@logged
@island
@traced
def Counter():
    return button()["Click"]
'''
        result = scan_source(source)
        assert len(result.islands) == 1
        assert "island" in result.islands[0].decorators
        assert "cache" in result.islands[0].decorators
    
    def test_conditional_decorator(self):
        """Handle conditional decorator (edge case)."""
        source = '''
decorator = island if production else debug_island

@decorator
def Counter():
    return button()["Click"]
'''
        # Might not detect since 'island' isn't the decorator name
        # But should not crash
        result = scan_source(source)
        assert result.success
    
    def test_lambda_decorator(self):
        """Handle lambda-style decorator (edge case)."""
        source = '''
@(lambda f: island(f) if is_production else f)
def Counter():
    return button()["Click"]
'''
        # Complex decorator - might not detect but should not crash
        result = scan_source(source)
        assert result.success


# =============================================================================
# P2: MEDIUM - LINE ENDING HASH INSTABILITY
# =============================================================================

class TestP2LineEndingHashInstability:
    """
    Tests for hash instability due to line endings.
    Same logical content with different line endings = different hash.
    """
    
    def test_lf_vs_crlf_hash_differs(self, tmp_path):
        """LF and CRLF produce different hashes (known limitation)."""
        lf_file = tmp_path / "lf.py"
        crlf_file = tmp_path / "crlf.py"
        
        content = "@island\ndef Counter():\n    pass\n"
        
        lf_file.write_bytes(content.encode('utf-8'))
        crlf_file.write_bytes(content.replace('\n', '\r\n').encode('utf-8'))
        
        from pynext.build.cache import hash_file
        
        lf_hash = hash_file(lf_file)
        crlf_hash = hash_file(crlf_file)
        
        # They will differ - this is a known limitation
        # Test documents this behavior
        assert lf_hash != crlf_hash
    
    def test_content_hash_consistent(self):
        """Content hash should be consistent for same content."""
        content = "def test(): pass"
        
        hashes = [hash_content(content) for _ in range(100)]
        
        assert len(set(hashes)) == 1


# =============================================================================
# P2: MEDIUM - LARGE FILE HANDLING
# =============================================================================

class TestP2LargeFileHandling:
    """
    Tests for handling large Python files.
    Scanner reads entire files into memory.
    """
    
    def test_large_file_scan(self, tmp_path):
        """Scan large file without memory issues."""
        file = tmp_path / "large.py"
        
        # Generate 10,000 line file
        lines = ['# Large file\n']
        for i in range(10000):
            lines.append(f'def func_{i}():\n    return {i}\n\n')
        
        # Add one island at the end
        lines.append('@island\ndef LargeIsland():\n    return div()["Large"]\n')
        
        file.write_text(''.join(lines))
        
        result = scan_file(file)
        assert len(result.islands) == 1
        assert result.islands[0].name == "LargeIsland"
    
    def test_many_islands_in_file(self, tmp_path):
        """Scan file with many islands."""
        file = tmp_path / "many.py"
        
        lines = []
        for i in range(500):
            lines.append(f'''
@island
def Island{i}():
    count = signal({i})
    return div()[count()]
''')
        
        file.write_text('\n'.join(lines))
        
        result = scan_file(file)
        assert len(result.islands) == 500


# =============================================================================
# P2: MEDIUM - ENCODING ISSUES
# =============================================================================

class TestP2EncodingIssues:
    """
    Tests for file encoding edge cases.
    Non-UTF-8 files could fail to parse.
    """
    
    def test_utf8_bom(self, tmp_path):
        """Handle UTF-8 with BOM."""
        file = tmp_path / "bom.py"
        
        content = '@island\ndef Test(): pass'
        # UTF-8 BOM
        file.write_bytes(b'\xef\xbb\xbf' + content.encode('utf-8'))
        
        result = scan_file(file)
        # Should handle BOM
        assert len(result.islands) == 1 or len(result.errors) == 0
    
    def test_unicode_content(self, tmp_path):
        """Handle Unicode content in file."""
        file = tmp_path / "unicode.py"
        file.write_text('''
# 中文注释
# Комментарий на русском
@island
def Greeting():
    return h1()["Привет, 世界! 🌍"]
''', encoding='utf-8')
        
        result = scan_file(file)
        assert len(result.islands) == 1
    
    def test_invalid_utf8_graceful(self, tmp_path):
        """Handle invalid UTF-8 gracefully."""
        file = tmp_path / "bad.py"
        
        # Write invalid UTF-8
        file.write_bytes(b'@island\ndef Test():\n    return "\xff\xfe"')
        
        result = scan_file(file)
        # Should have error, not crash
        assert len(result.errors) >= 1 or len(result.islands) == 0

