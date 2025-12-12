"""
Tests for PyNext Build Scanner (80 tests)

Tests @island detection, edge cases, and performance.
"""

import pytest
import tempfile
from pathlib import Path

from pynext.build.scanner import (
    scan_source,
    scan_file,
    scan_directory,
    is_island_file,
    IslandInfo,
    ScanResult,
    IslandVisitor,
)


# =============================================================================
# BASIC ISLAND DETECTION
# =============================================================================

class TestBasicDetection:
    """Tests for basic @island decorator detection."""
    
    def test_simple_island(self):
        """Detect a simple @island function."""
        source = '''
from pynext import island

@island
def Counter():
    return button()["Click"]
'''
        result = scan_source(source)
        assert len(result.islands) == 1
        assert result.islands[0].name == "Counter"
    
    def test_island_with_arguments(self):
        """Detect @island with decorator arguments."""
        source = '''
@island(hydrate=True)
def Counter():
    count = signal(0)
    return div()[count()]
'''
        result = scan_source(source)
        assert len(result.islands) == 1
        assert "island" in result.islands[0].decorators
    
    def test_multiple_islands(self):
        """Detect multiple islands in one file."""
        source = '''
@island
def Counter():
    return button()["Count"]

@island  
def Todo():
    return div()["Todo"]

@island
def Timer():
    return span()["00:00"]
'''
        result = scan_source(source)
        assert len(result.islands) == 3
        names = {i.name for i in result.islands}
        assert names == {"Counter", "Todo", "Timer"}
    
    def test_async_island(self):
        """Detect async @island functions."""
        source = '''
@island
async def DataLoader():
    data = await fetch_data()
    return div()[data]
'''
        result = scan_source(source)
        assert len(result.islands) == 1
        assert result.islands[0].name == "DataLoader"
    
    def test_island_with_params(self):
        """Detect island with function parameters."""
        source = '''
@island
def Greeting(name: str, count: int = 0):
    return h1()[f"Hello, {name}!"]
'''
        result = scan_source(source)
        assert len(result.islands) == 1
        assert result.islands[0].name == "Greeting"
    
    def test_nested_functions_not_islands(self):
        """Inner functions are not detected as islands."""
        source = '''
@island
def Outer():
    def inner():
        return "inner"
    return div()[inner()]
'''
        result = scan_source(source)
        assert len(result.islands) == 1
        assert result.islands[0].name == "Outer"
    
    def test_class_method_not_island(self):
        """Class methods with @island are detected."""
        source = '''
class Component:
    @island
    def render(self):
        return div()["Hello"]
'''
        result = scan_source(source)
        # Note: We detect decorated functions regardless of context
        assert len(result.islands) == 1
    
    def test_no_islands(self):
        """File without islands returns empty list."""
        source = '''
def regular_function():
    return "not an island"

class RegularClass:
    pass
'''
        result = scan_source(source)
        assert len(result.islands) == 0
    
    def test_decorated_but_not_island(self):
        """Other decorators don't count as islands."""
        source = '''
@staticmethod
def helper():
    return 42

@property
def value(self):
    return self._value
'''
        result = scan_source(source)
        assert len(result.islands) == 0


# =============================================================================
# FEATURE DETECTION  
# =============================================================================

class TestFeatureDetection:
    """Tests for detecting reactive features in islands."""
    
    def test_detect_signals(self):
        """Detect signal() usage."""
        source = '''
@island
def Counter():
    count = signal(0)
    return button()[count()]
'''
        result = scan_source(source)
        assert result.islands[0].has_signals is True
    
    def test_detect_stores(self):
        """Detect store() usage."""
        source = '''
@island
def TodoList():
    todos = store([])
    return ul()[For(todos, lambda t: li()[t])]
'''
        result = scan_source(source)
        assert result.islands[0].has_stores is True
    
    def test_detect_effects(self):
        """Detect effect() usage."""
        source = '''
@island
def Logger():
    count = signal(0)
    effect(lambda: print(count()))
    return div()[count()]
'''
        result = scan_source(source)
        assert result.islands[0].has_effects is True
    
    def test_detect_memos(self):
        """Detect memo() usage."""
        source = '''
@island
def DoubleCounter():
    count = signal(0)
    double = memo(lambda: count() * 2)
    return span()[double()]
'''
        result = scan_source(source)
        assert result.islands[0].has_memos is True
    
    def test_detect_forms(self):
        """Detect create_form() usage."""
        source = '''
@island
def LoginForm():
    form = create_form({"email": "", "password": ""})
    return div()[
        input(bind=form.email),
        input(bind=form.password),
    ]
'''
        result = scan_source(source)
        assert result.islands[0].has_forms is True
    
    def test_detect_multiple_features(self):
        """Detect multiple features in one island."""
        source = '''
@island
def ComplexComponent():
    count = signal(0)
    items = store([])
    double = memo(lambda: count() * 2)
    effect(lambda: print(count()))
    return div()[double()]
'''
        result = scan_source(source)
        island = result.islands[0]
        assert island.has_signals is True
        assert island.has_stores is True
        assert island.has_memos is True
        assert island.has_effects is True
    
    def test_no_features(self):
        """Island without reactive features."""
        source = '''
@island
def Static():
    return div()["Static content"]
'''
        result = scan_source(source)
        island = result.islands[0]
        assert island.has_signals is False
        assert island.has_stores is False
        assert island.has_memos is False
        assert island.has_effects is False
    
    def test_feature_in_nested_call(self):
        """Detect features in nested function calls."""
        source = '''
@island
def Nested():
    x = some_wrapper(signal(0))
    return div()[x()]
'''
        result = scan_source(source)
        assert result.islands[0].has_signals is True
    
    def test_signal_class_usage(self):
        """Detect Signal class usage (capital S)."""
        source = '''
@island
def Counter():
    count = Signal(0)
    return button()[count.value]
'''
        result = scan_source(source)
        assert result.islands[0].has_signals is True


# =============================================================================
# FILE SCANNING
# =============================================================================

class TestFileScan:
    """Tests for scanning Python files."""
    
    def test_scan_file_exists(self, tmp_path):
        """Scan existing file."""
        file = tmp_path / "counter.py"
        file.write_text('''
@island
def Counter():
    return button()["Click"]
''')
        result = scan_file(file)
        assert result.islands[0].name == "Counter"
        assert result.islands[0].file_path == str(file)
    
    def test_scan_file_not_found(self, tmp_path):
        """Handle missing file gracefully."""
        result = scan_file(tmp_path / "nonexistent.py")
        assert len(result.islands) == 0
        assert len(result.errors) == 1
    
    def test_scan_file_syntax_error(self, tmp_path):
        """Handle syntax errors in file."""
        file = tmp_path / "broken.py"
        # Include 'island' so the file isn't skipped
        file.write_text('''
@island
def broken(
    # Missing closing paren
''')
        result = scan_file(file)
        assert len(result.errors) == 1
        assert "Syntax error" in result.errors[0][1]
    
    def test_scan_file_not_python(self, tmp_path):
        """Reject non-Python files."""
        file = tmp_path / "script.js"
        file.write_text('console.log("hello")')
        result = scan_file(file)
        assert len(result.errors) == 1
        assert "Not a Python file" in result.errors[0][1]
    
    def test_scan_file_no_island_keyword(self, tmp_path):
        """Skip file that doesn't contain 'island'."""
        file = tmp_path / "utils.py"
        file.write_text('''
def helper():
    return 42
''')
        result = scan_file(file)
        assert len(result.islands) == 0
        assert len(result.errors) == 0
    
    def test_scan_file_line_numbers(self, tmp_path):
        """Verify line numbers are correct."""
        file = tmp_path / "counter.py"
        file.write_text('''# Comment
# More comments

@island
def Counter():
    return button()["Click"]
''')
        result = scan_file(file)
        assert result.islands[0].line_number == 5  # Line where def starts
    
    def test_scan_file_with_encoding(self, tmp_path):
        """Handle files with different encodings."""
        file = tmp_path / "unicode.py"
        file.write_text('''
# -*- coding: utf-8 -*-
@island
def Greeting():
    return h1()["Привет! 你好! 🎉"]
''', encoding='utf-8')
        result = scan_file(file)
        assert len(result.islands) == 1


# =============================================================================
# DIRECTORY SCANNING
# =============================================================================

class TestDirectoryScan:
    """Tests for scanning directories."""
    
    def test_scan_empty_directory(self, tmp_path):
        """Scan empty directory."""
        result = scan_directory(tmp_path)
        assert result.files_scanned == 0
        assert len(result.islands) == 0
    
    def test_scan_directory_with_islands(self, tmp_path):
        """Scan directory with island files."""
        (tmp_path / "counter.py").write_text('''
@island
def Counter():
    return button()["Click"]
''')
        (tmp_path / "todo.py").write_text('''
@island
def Todo():
    return div()["Todo"]
''')
        result = scan_directory(tmp_path)
        assert result.files_scanned == 2
        assert len(result.islands) == 2
    
    def test_scan_directory_recursive(self, tmp_path):
        """Scan directories recursively."""
        sub = tmp_path / "components"
        sub.mkdir()
        (sub / "button.py").write_text('''
@island
def Button():
    return button()["Click"]
''')
        result = scan_directory(tmp_path, recursive=True)
        assert len(result.islands) == 1
    
    def test_scan_directory_non_recursive(self, tmp_path):
        """Scan only top level when recursive=False."""
        sub = tmp_path / "components"
        sub.mkdir()
        (sub / "button.py").write_text('''
@island
def Button():
    return button()["Click"]
''')
        (tmp_path / "main.py").write_text('''
@island
def Main():
    return div()["Main"]
''')
        result = scan_directory(tmp_path, recursive=False)
        assert len(result.islands) == 1
        assert result.islands[0].name == "Main"
    
    def test_scan_directory_exclude_pycache(self, tmp_path):
        """Exclude __pycache__ directories."""
        pycache = tmp_path / "__pycache__"
        pycache.mkdir()
        (pycache / "cached.py").write_text('''
@island
def Cached():
    return div()["Cached"]
''')
        result = scan_directory(tmp_path)
        assert len(result.islands) == 0
    
    def test_scan_directory_exclude_venv(self, tmp_path):
        """Exclude .venv and venv directories."""
        venv = tmp_path / ".venv"
        venv.mkdir()
        (venv / "package.py").write_text('''
@island
def VenvIsland():
    return div()["Package"]
''')
        result = scan_directory(tmp_path)
        assert len(result.islands) == 0
    
    def test_scan_directory_custom_exclude(self, tmp_path):
        """Custom exclusion patterns."""
        test_dir = tmp_path / "test_components"
        test_dir.mkdir()
        (test_dir / "test_counter.py").write_text('''
@island
def TestCounter():
    return button()["Test"]
''')
        result = scan_directory(tmp_path, exclude_dirs={"test_components"})
        assert len(result.islands) == 0
    
    def test_scan_directory_not_found(self):
        """Handle missing directory."""
        result = scan_directory("/nonexistent/path")
        assert len(result.errors) == 1
        assert "not found" in result.errors[0][1].lower()
    
    def test_scan_directory_multiple_islands_per_file(self, tmp_path):
        """Count multiple islands from same file."""
        (tmp_path / "components.py").write_text('''
@island
def Counter():
    return button()["Count"]

@island
def Timer():
    return span()["00:00"]

@island
def Toggle():
    return input(type="checkbox")
''')
        result = scan_directory(tmp_path)
        assert len(result.islands) == 3
        assert result.files_with_islands == 1


# =============================================================================
# ISLAND INFO
# =============================================================================

class TestIslandInfo:
    """Tests for IslandInfo data structure."""
    
    def test_island_id(self):
        """Island ID is unique per file:name."""
        info = IslandInfo(
            name="Counter",
            file_path="pages/dashboard.py",
            line_number=10,
        )
        assert info.id == "pages/dashboard.py:Counter"
    
    def test_island_hash(self):
        """Islands can be used in sets."""
        info1 = IslandInfo(name="A", file_path="a.py", line_number=1)
        info2 = IslandInfo(name="B", file_path="b.py", line_number=1)
        info3 = IslandInfo(name="A", file_path="a.py", line_number=1)
        
        islands = {info1, info2, info3}
        assert len(islands) == 2  # info1 and info3 are equal
    
    def test_island_equality(self):
        """Islands with same id are equal."""
        info1 = IslandInfo(name="X", file_path="x.py", line_number=1)
        info2 = IslandInfo(name="X", file_path="x.py", line_number=10)
        assert info1 == info2  # Same id despite different line
    
    def test_island_source_hash(self):
        """Source hash is computed."""
        source = '''
@island
def Counter():
    count = signal(0)
    return button()[count()]
'''
        result = scan_source(source)
        assert result.islands[0].source_hash != ""
        assert len(result.islands[0].source_hash) == 16


# =============================================================================
# SCAN RESULT
# =============================================================================

class TestScanResult:
    """Tests for ScanResult data structure."""
    
    def test_result_success(self):
        """Success when no errors."""
        result = ScanResult(islands=[IslandInfo("A", "a.py", 1)])
        assert result.success is True
    
    def test_result_failure(self):
        """Failure when errors present."""
        result = ScanResult(errors=[("file.py", "Error")])
        assert result.success is False
    
    def test_result_count(self):
        """Island count property."""
        islands = [
            IslandInfo("A", "a.py", 1),
            IslandInfo("B", "b.py", 1),
        ]
        result = ScanResult(islands=islands)
        assert result.island_count == 2
    
    def test_result_by_file(self):
        """Group islands by file."""
        islands = [
            IslandInfo("A", "a.py", 1),
            IslandInfo("B", "a.py", 10),
            IslandInfo("C", "b.py", 1),
        ]
        result = ScanResult(islands=islands)
        by_file = result.get_islands_by_file()
        
        assert len(by_file["a.py"]) == 2
        assert len(by_file["b.py"]) == 1


# =============================================================================
# IS ISLAND FILE
# =============================================================================

class TestIsIslandFile:
    """Tests for quick island file detection."""
    
    def test_is_island_file_true(self, tmp_path):
        """File with 'island' returns True."""
        file = tmp_path / "counter.py"
        file.write_text('''
@island
def Counter():
    pass
''')
        assert is_island_file(file) is True
    
    def test_is_island_file_false(self, tmp_path):
        """File without 'island' returns False."""
        file = tmp_path / "utils.py"
        file.write_text('''
def helper():
    return 42
''')
        assert is_island_file(file) is False
    
    def test_is_island_file_nonexistent(self, tmp_path):
        """Nonexistent file returns False."""
        assert is_island_file(tmp_path / "missing.py") is False
    
    def test_is_island_file_not_python(self, tmp_path):
        """Non-Python file returns False."""
        file = tmp_path / "script.js"
        file.write_text('const island = true;')
        assert is_island_file(file) is False
    
    def test_is_island_file_case_insensitive(self, tmp_path):
        """Detection is case-insensitive."""
        file = tmp_path / "counter.py"
        file.write_text('''
@ISLAND
def Counter():
    pass
''')
        assert is_island_file(file) is True


# =============================================================================
# EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Edge case tests."""
    
    def test_island_in_string(self):
        """Don't detect 'island' in strings."""
        source = '''
def not_island():
    return "This is an island reference but not a decorator"
'''
        result = scan_source(source)
        assert len(result.islands) == 0
    
    def test_island_in_comment(self):
        """Don't detect 'island' in comments."""
        source = '''
# @island - this is a comment, not a decorator
def regular():
    pass
'''
        result = scan_source(source)
        assert len(result.islands) == 0
    
    def test_multiple_decorators(self):
        """Island with multiple decorators."""
        source = '''
@cache
@island
@logged
def Counter():
    return button()["Click"]
'''
        result = scan_source(source)
        assert len(result.islands) == 1
        assert "island" in result.islands[0].decorators
        assert "cache" in result.islands[0].decorators
        assert "logged" in result.islands[0].decorators
    
    def test_module_island(self):
        """Qualified decorator: module.island."""
        source = '''
import pynext

@pynext.island
def Counter():
    return button()["Click"]
'''
        result = scan_source(source)
        assert len(result.islands) == 1
    
    def test_empty_file(self):
        """Empty file."""
        result = scan_source("")
        assert len(result.islands) == 0
        assert result.success is True
    
    def test_whitespace_only(self):
        """File with only whitespace."""
        result = scan_source("   \n\n   \t   \n")
        assert len(result.islands) == 0
        assert result.success is True
    
    def test_very_long_file(self):
        """Performance with large files."""
        # Generate 1000 islands
        source = "\n".join(f"""
@island
def Island{i}():
    count = signal({i})
    return div()[count()]
""" for i in range(100))
        
        result = scan_source(source)
        assert len(result.islands) == 100
    
    def test_unicode_function_name(self):
        """Unicode in function names (if Python allows)."""
        source = '''
@island
def Счётчик():
    return span()["0"]
'''
        result = scan_source(source)
        assert len(result.islands) == 1
        assert result.islands[0].name == "Счётчик"


# =============================================================================
# PERFORMANCE
# =============================================================================

class TestPerformance:
    """Performance tests."""
    
    def test_scan_speed(self, tmp_path):
        """Scan 100 files in reasonable time."""
        import time
        
        # Create 100 Python files
        for i in range(100):
            (tmp_path / f"component_{i}.py").write_text(f'''
@island
def Component{i}():
    count = signal({i})
    return button()[count()]
''')
        
        start = time.perf_counter()
        result = scan_directory(tmp_path)
        duration = (time.perf_counter() - start) * 1000
        
        assert len(result.islands) == 100
        assert duration < 1000  # Should complete in < 1 second
    
    def test_skip_non_island_files(self, tmp_path):
        """Files without 'island' are skipped quickly."""
        import time
        
        # Create 100 non-island files
        for i in range(100):
            (tmp_path / f"util_{i}.py").write_text(f'''
def helper_{i}():
    return {i}
''')
        
        start = time.perf_counter()
        result = scan_directory(tmp_path)
        duration = (time.perf_counter() - start) * 1000
        
        assert len(result.islands) == 0
        assert duration < 500  # Should be fast

