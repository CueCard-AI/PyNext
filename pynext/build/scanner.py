"""
PyNext Build - Island Scanner

=============================================================================
WHAT THIS FILE DOES
=============================================================================

Scans Python source files to find @island decorated functions that need
to be compiled to JavaScript.

    from pynext.build.scanner import scan_directory, scan_file
    
    # Scan entire project
    islands = scan_directory("pages/")
    # Returns: [IslandInfo("Counter", "pages/dashboard.py", 10), ...]
    
    # Scan single file
    islands = scan_file("components/counter.py")

=============================================================================
WHY THIS EXISTS
=============================================================================

Before we can compile islands, we need to find them. This scanner:

1. Recursively walks directories looking for .py files
2. Parses each file's AST to find @island decorators
3. Returns structured information about each island

This is the first step in the build pipeline:

    SCAN → Cache Check → Compile → Tree Shake → Bundle

=============================================================================
WHO USES THIS
=============================================================================

1. Build system (reactive.py) - Finds all islands to compile
2. Dev server (watcher.py) - Checks if changed file contains islands
3. CLI - `pynext build` command

=============================================================================
PERFORMANCE
=============================================================================

Target: Scan 1000 Python files in < 100ms

Optimizations:
- Only parse files that could contain islands (has 'island' in text)
- Use Python's built-in AST (C-optimized)
- Parallel scanning for large projects

=============================================================================
"""

from __future__ import annotations

import ast
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Set, Dict, Any
import hashlib


__all__ = [
    "IslandInfo",
    "ScanResult",
    "scan_file",
    "scan_source",
    "scan_directory",
    "is_island_file",
]


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class IslandInfo:
    """
    Information about a discovered @island component.
    
    Attributes:
        name: Function name (e.g., "Counter")
        file_path: Path to the source file
        line_number: Line where the function starts
        decorators: List of all decorator names
        has_signals: True if the island uses signal()
        has_stores: True if the island uses store()
        has_effects: True if the island uses effect()
        source_hash: SHA256 hash of the function source
    
    Example:
        IslandInfo(
            name="Counter",
            file_path="pages/dashboard.py",
            line_number=10,
            decorators=["island"],
            has_signals=True,
            has_stores=False,
            has_effects=True,
            source_hash="abc123..."
        )
    """
    name: str
    file_path: str
    line_number: int
    decorators: List[str] = field(default_factory=list)
    has_signals: bool = False
    has_stores: bool = False
    has_effects: bool = False
    has_memos: bool = False
    has_forms: bool = False
    source_hash: str = ""
    
    @property
    def id(self) -> str:
        """Unique identifier for this island."""
        return f"{self.file_path}:{self.name}"
    
    def __hash__(self) -> int:
        return hash(self.id)
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, IslandInfo):
            return False
        return self.id == other.id


@dataclass
class ScanResult:
    """
    Result of scanning files for islands.
    
    Attributes:
        islands: List of discovered islands
        files_scanned: Number of files processed
        files_with_islands: Number of files containing islands
        errors: List of (file_path, error_message) for parse failures
        duration_ms: Time taken to scan
    """
    islands: List[IslandInfo] = field(default_factory=list)
    files_scanned: int = 0
    files_with_islands: int = 0
    errors: List[tuple] = field(default_factory=list)
    duration_ms: float = 0.0
    
    @property
    def island_count(self) -> int:
        """Total number of islands found."""
        return len(self.islands)
    
    @property
    def success(self) -> bool:
        """True if no errors occurred."""
        return len(self.errors) == 0
    
    def get_islands_by_file(self) -> Dict[str, List[IslandInfo]]:
        """Group islands by their source file."""
        result: Dict[str, List[IslandInfo]] = {}
        for island in self.islands:
            if island.file_path not in result:
                result[island.file_path] = []
            result[island.file_path].append(island)
        return result


# =============================================================================
# AST VISITOR
# =============================================================================

class IslandVisitor(ast.NodeVisitor):
    """
    AST visitor that finds @island decorated functions.
    
    Collects:
    - Function name and location
    - All decorators
    - Whether the function uses signals, stores, effects
    """
    
    def __init__(self, source: str, file_path: str = "<string>"):
        self.source = source
        self.file_path = file_path
        self.source_lines = source.splitlines()
        self.islands: List[IslandInfo] = []
        self._current_function: Optional[ast.FunctionDef] = None
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit a function definition."""
        # Check if this function has @island decorator
        decorator_names = self._get_decorator_names(node)
        
        if "island" in decorator_names:
            # Analyze the function body
            has_signals = self._uses_signals(node)
            has_stores = self._uses_stores(node)
            has_effects = self._uses_effects(node)
            has_memos = self._uses_memos(node)
            has_forms = self._uses_forms(node)
            
            # Calculate source hash
            source_hash = self._hash_function(node)
            
            island = IslandInfo(
                name=node.name,
                file_path=self.file_path,
                line_number=node.lineno,
                decorators=decorator_names,
                has_signals=has_signals,
                has_stores=has_stores,
                has_effects=has_effects,
                has_memos=has_memos,
                has_forms=has_forms,
                source_hash=source_hash,
            )
            self.islands.append(island)
        
        # Continue visiting child nodes
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit an async function definition (same logic as sync)."""
        # Check if this function has @island decorator
        decorator_names = self._get_decorator_names(node)
        
        if "island" in decorator_names:
            has_signals = self._uses_signals(node)
            has_stores = self._uses_stores(node)
            has_effects = self._uses_effects(node)
            has_memos = self._uses_memos(node)
            has_forms = self._uses_forms(node)
            source_hash = self._hash_function(node)
            
            island = IslandInfo(
                name=node.name,
                file_path=self.file_path,
                line_number=node.lineno,
                decorators=decorator_names,
                has_signals=has_signals,
                has_stores=has_stores,
                has_effects=has_effects,
                has_memos=has_memos,
                has_forms=has_forms,
                source_hash=source_hash,
            )
            self.islands.append(island)
        
        self.generic_visit(node)
    
    def _get_decorator_names(self, node: ast.FunctionDef) -> List[str]:
        """Extract decorator names from a function."""
        names = []
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                names.append(decorator.id)
            elif isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Name):
                    names.append(decorator.func.id)
                elif isinstance(decorator.func, ast.Attribute):
                    names.append(decorator.func.attr)
            elif isinstance(decorator, ast.Attribute):
                names.append(decorator.attr)
        return names
    
    def _uses_signals(self, node: ast.FunctionDef) -> bool:
        """Check if the function uses signal()."""
        return self._contains_call(node, {"signal", "Signal"})
    
    def _uses_stores(self, node: ast.FunctionDef) -> bool:
        """Check if the function uses store()."""
        return self._contains_call(node, {"store", "Store"})
    
    def _uses_effects(self, node: ast.FunctionDef) -> bool:
        """Check if the function uses effect()."""
        return self._contains_call(node, {"effect", "Effect"})
    
    def _uses_memos(self, node: ast.FunctionDef) -> bool:
        """Check if the function uses memo()."""
        return self._contains_call(node, {"memo", "Memo"})
    
    def _uses_forms(self, node: ast.FunctionDef) -> bool:
        """Check if the function uses create_form()."""
        return self._contains_call(node, {"create_form", "FormState"})
    
    def _contains_call(self, node: ast.AST, names: Set[str]) -> bool:
        """Check if the AST contains a call to any of the given names."""
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    if child.func.id in names:
                        return True
                elif isinstance(child.func, ast.Attribute):
                    if child.func.attr in names:
                        return True
        return False
    
    def _hash_function(self, node: ast.FunctionDef) -> str:
        """Calculate SHA256 hash of the function source."""
        # Get source lines for this function
        start_line = node.lineno - 1
        end_line = node.end_lineno if hasattr(node, "end_lineno") and node.end_lineno else start_line + 1
        
        func_lines = self.source_lines[start_line:end_line]
        func_source = "\n".join(func_lines)
        
        return hashlib.sha256(func_source.encode()).hexdigest()[:16]


# =============================================================================
# PUBLIC API
# =============================================================================

def scan_source(source: str, file_path: str = "<string>") -> ScanResult:
    """
    Scan Python source code for @island components.
    
    Args:
        source: Python source code as a string
        file_path: Path to use in error messages and IslandInfo
    
    Returns:
        ScanResult with discovered islands
    
    Example:
        source = '''
        @island
        def Counter():
            count = signal(0)
            return button()[count()]
        '''
        result = scan_source(source, "counter.py")
        assert result.islands[0].name == "Counter"
    """
    import time
    start = time.perf_counter()
    
    result = ScanResult()
    result.files_scanned = 1
    
    try:
        tree = ast.parse(source)
        visitor = IslandVisitor(source, file_path)
        visitor.visit(tree)
        
        result.islands = visitor.islands
        if result.islands:
            result.files_with_islands = 1
            
    except SyntaxError as e:
        result.errors.append((file_path, f"Syntax error: {e.msg} at line {e.lineno}"))
    except Exception as e:
        result.errors.append((file_path, f"Parse error: {str(e)}"))
    
    result.duration_ms = (time.perf_counter() - start) * 1000
    return result


def scan_file(file_path: str | Path) -> ScanResult:
    """
    Scan a Python file for @island components.
    
    Args:
        file_path: Path to the Python file
    
    Returns:
        ScanResult with discovered islands
    
    Example:
        result = scan_file("components/counter.py")
        for island in result.islands:
            print(f"Found: {island.name} at line {island.line_number}")
    """
    import time
    start = time.perf_counter()
    
    path = Path(file_path)
    result = ScanResult()
    result.files_scanned = 1
    
    if not path.exists():
        result.errors.append((str(path), "File not found"))
        result.duration_ms = (time.perf_counter() - start) * 1000
        return result
    
    if not path.suffix == ".py":
        result.errors.append((str(path), "Not a Python file"))
        result.duration_ms = (time.perf_counter() - start) * 1000
        return result
    
    try:
        source = path.read_text(encoding="utf-8")
        
        # Strip UTF-8 BOM if present (U+FEFF)
        if source.startswith('\ufeff'):
            source = source[1:]
        
        # Quick check: skip files that don't mention 'island'
        if "island" not in source.lower():
            result.duration_ms = (time.perf_counter() - start) * 1000
            return result
        
        tree = ast.parse(source)
        visitor = IslandVisitor(source, str(path))
        visitor.visit(tree)
        
        result.islands = visitor.islands
        if result.islands:
            result.files_with_islands = 1
            
    except SyntaxError as e:
        result.errors.append((str(path), f"Syntax error: {e.msg} at line {e.lineno}"))
    except UnicodeDecodeError as e:
        result.errors.append((str(path), f"Encoding error: {str(e)}"))
    except Exception as e:
        result.errors.append((str(path), f"Parse error: {str(e)}"))
    
    result.duration_ms = (time.perf_counter() - start) * 1000
    return result


def scan_directory(
    directory: str | Path,
    exclude_dirs: Optional[Set[str]] = None,
    recursive: bool = True,
) -> ScanResult:
    """
    Scan a directory for @island components in Python files.
    
    Args:
        directory: Path to the directory to scan
        exclude_dirs: Directory names to skip (default: __pycache__, .git, node_modules, .venv)
        recursive: Whether to scan subdirectories
    
    Returns:
        ScanResult with all discovered islands
    
    Example:
        result = scan_directory("pages/")
        print(f"Found {result.island_count} islands in {result.files_scanned} files")
    """
    import time
    start = time.perf_counter()
    
    if exclude_dirs is None:
        exclude_dirs = {"__pycache__", ".git", "node_modules", ".venv", ".pynext", "venv"}
    
    path = Path(directory)
    result = ScanResult()
    
    if not path.exists():
        result.errors.append((str(path), "Directory not found"))
        result.duration_ms = (time.perf_counter() - start) * 1000
        return result
    
    if not path.is_dir():
        result.errors.append((str(path), "Not a directory"))
        result.duration_ms = (time.perf_counter() - start) * 1000
        return result
    
    # Collect all Python files
    py_files: List[Path] = []
    
    if recursive:
        for root, dirs, files in os.walk(path):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file.endswith(".py"):
                    py_files.append(Path(root) / file)
    else:
        py_files = list(path.glob("*.py"))
    
    # Scan each file
    for py_file in py_files:
        file_result = scan_file(py_file)
        result.files_scanned += 1
        result.islands.extend(file_result.islands)
        result.errors.extend(file_result.errors)
        if file_result.islands:
            result.files_with_islands += 1
    
    result.duration_ms = (time.perf_counter() - start) * 1000
    return result


def is_island_file(file_path: str | Path) -> bool:
    """
    Quick check if a file might contain islands.
    
    This is a fast heuristic check that looks for 'island' in the file.
    Use scan_file() for accurate detection.
    
    Args:
        file_path: Path to the Python file
    
    Returns:
        True if the file might contain islands
    
    Example:
        if is_island_file("components/counter.py"):
            result = scan_file("components/counter.py")
    """
    path = Path(file_path)
    
    if not path.exists() or not path.suffix == ".py":
        return False
    
    try:
        content = path.read_text(encoding="utf-8")
        return "island" in content.lower()
    except Exception:
        return False

