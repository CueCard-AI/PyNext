"""
CSS Extractor - Collect CSS from Python Components

Scans Python files to find all css() and css_module() calls,
extracts the CSS content, and prepares it for bundling.

This enables build-time CSS extraction without runtime overhead.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from .scoper import CSSScoper, ScopedCSS


@dataclass
class ExtractedCSS:
    """
    CSS extracted from a source file.
    
    Attributes:
        source: Path to the source file
        component: Component name
        raw_css: Original CSS string
        scoped_css: Scoped CSS string
        classes: Mapping of original to scoped class names
        line_number: Line where CSS was defined
        is_external: Whether CSS came from external file
    """
    source: Path
    component: str
    raw_css: str
    scoped_css: str
    classes: Dict[str, str]
    line_number: int
    is_external: bool = False
    external_path: Optional[Path] = None


class CSSExtractor:
    """
    Extracts CSS from Python source files.
    
    Parses Python AST to find css() and css_module() calls,
    extracts the CSS content, and scopes it.
    
    Example:
        >>> extractor = CSSExtractor()
        >>> results = extractor.extract_file(Path("components/Button.py"))
        >>> for css in results:
        ...     print(css.component, css.scoped_css)
    """
    
    def __init__(self):
        self._cache: Dict[Path, List[ExtractedCSS]] = {}
    
    def extract_file(self, path: Path) -> List[ExtractedCSS]:
        """
        Extract all CSS from a Python file.
        
        Args:
            path: Path to Python file
            
        Returns:
            List of ExtractedCSS objects
        """
        if path in self._cache:
            return self._cache[path]
        
        if not path.exists():
            return []
        
        content = path.read_text(encoding="utf-8")
        results = self._extract_from_source(content, path)
        
        self._cache[path] = results
        return results
    
    def extract_directory(
        self,
        directory: Path,
        recursive: bool = True,
    ) -> List[ExtractedCSS]:
        """
        Extract CSS from all Python files in a directory.
        
        Args:
            directory: Directory to scan
            recursive: Whether to scan subdirectories
            
        Returns:
            List of all ExtractedCSS objects
        """
        results = []
        pattern = "**/*.py" if recursive else "*.py"
        
        for py_file in directory.glob(pattern):
            results.extend(self.extract_file(py_file))
        
        return results
    
    def _extract_from_source(
        self,
        source: str,
        path: Path,
    ) -> List[ExtractedCSS]:
        """Extract CSS from Python source code."""
        results = []
        
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return []
        
        # Find all css() and css_module() calls
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                result = self._process_call(node, source, path)
                if result:
                    results.append(result)
        
        return results
    
    def _process_call(
        self,
        node: ast.Call,
        source: str,
        path: Path,
    ) -> Optional[ExtractedCSS]:
        """Process a function call node."""
        # Get function name
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
        else:
            return None
        
        # Handle css() call
        if func_name == "css":
            return self._extract_inline_css(node, path)
        
        # Handle css_module() call
        if func_name == "css_module":
            return self._extract_module_css(node, path)
        
        return None
    
    def _extract_inline_css(
        self,
        node: ast.Call,
        path: Path,
    ) -> Optional[ExtractedCSS]:
        """Extract CSS from css() call."""
        if not node.args:
            return None
        
        # Get CSS string argument
        css_arg = node.args[0]
        if isinstance(css_arg, ast.Constant) and isinstance(css_arg.value, str):
            raw_css = css_arg.value
        elif isinstance(css_arg, ast.JoinedStr):
            # f-string - can't statically extract
            return None
        else:
            return None
        
        # Get component name
        component = self._get_component_name(node, path)
        
        # Scope the CSS
        scoper = CSSScoper(component)
        scoped = scoper.scope(raw_css)
        
        return ExtractedCSS(
            source=path,
            component=component,
            raw_css=raw_css,
            scoped_css=scoped.css,
            classes=scoped.all(),
            line_number=node.lineno,
            is_external=False,
        )
    
    def _extract_module_css(
        self,
        node: ast.Call,
        path: Path,
    ) -> Optional[ExtractedCSS]:
        """Extract CSS from css_module() call."""
        if not node.args:
            return None
        
        # Get path argument
        path_arg = node.args[0]
        if isinstance(path_arg, ast.Constant) and isinstance(path_arg.value, str):
            css_path_str = path_arg.value
        else:
            return None
        
        # Resolve CSS path
        if css_path_str.startswith("./") or css_path_str.startswith("../"):
            css_path = path.parent / css_path_str
        else:
            css_path = Path(css_path_str)
        
        css_path = css_path.resolve()
        
        if not css_path.exists():
            return None
        
        # Read CSS content
        raw_css = css_path.read_text(encoding="utf-8")
        
        # Get component name
        component = self._get_component_name_from_path(css_path)
        
        # Scope the CSS
        scoper = CSSScoper(component)
        scoped = scoper.scope(raw_css)
        
        return ExtractedCSS(
            source=path,
            component=component,
            raw_css=raw_css,
            scoped_css=scoped.css,
            classes=scoped.all(),
            line_number=node.lineno,
            is_external=True,
            external_path=css_path,
        )
    
    def _get_component_name(
        self,
        node: ast.Call,
        path: Path,
    ) -> str:
        """Get component name from call or file."""
        # Check for explicit component argument
        for kw in node.keywords:
            if kw.arg == "component":
                if isinstance(kw.value, ast.Constant):
                    return kw.value.value
        
        # Use filename
        name = path.stem
        if name in ("__init__", "__main__", "index"):
            name = path.parent.name
        
        return self._to_pascal_case(name)
    
    def _get_component_name_from_path(self, path: Path) -> str:
        """Get component name from CSS file path."""
        name = path.name
        if name.endswith(".module.css"):
            name = name[:-11]
        elif name.endswith(".css"):
            name = name[:-4]
        return self._to_pascal_case(name)
    
    def _to_pascal_case(self, name: str) -> str:
        """Convert to PascalCase."""
        words = name.replace("-", "_").split("_")
        return "".join(word.capitalize() for word in words if word)
    
    def clear_cache(self):
        """Clear the extraction cache."""
        self._cache.clear()


def extract_all_css(
    directory: Path,
    recursive: bool = True,
) -> List[ExtractedCSS]:
    """
    Convenience function to extract all CSS from a directory.
    
    Args:
        directory: Directory to scan
        recursive: Whether to scan subdirectories
        
    Returns:
        List of all ExtractedCSS objects
        
    Example:
        >>> css_list = extract_all_css(Path("components"))
        >>> for css in css_list:
        ...     print(f"{css.component}: {len(css.classes)} classes")
    """
    extractor = CSSExtractor()
    return extractor.extract_directory(directory, recursive)

