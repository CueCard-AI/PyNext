"""
JavaScript Minification for PyNext

Provides lightweight JS minification without external dependencies.
For production builds, we recommend using terser via npm, but this
module provides a pure-Python fallback.
"""

import re
import os
from pathlib import Path
from typing import Optional


def minify_js(source: str, *, strip_debug: bool = True) -> str:
    """
    Minify JavaScript source code.
    
    This is a lightweight minifier that:
    - Removes comments (single-line and multi-line)
    - Removes console.debug/console.log statements
    - Removes unnecessary whitespace
    - Preserves string literals
    
    For production, consider using terser for better results.
    
    Args:
        source: JavaScript source code
        strip_debug: Whether to remove console.debug statements
    
    Returns:
        Minified JavaScript
    """
    # Preserve strings by replacing them temporarily
    strings = []
    string_pattern = r'(["\'])(?:(?!\1|\\).|\\.)*\1'
    
    def save_string(match):
        strings.append(match.group(0))
        return f'__STRING_{len(strings) - 1}__'
    
    result = re.sub(string_pattern, save_string, source)
    
    # Remove single-line comments
    result = re.sub(r'//[^\n]*', '', result)
    
    # Remove multi-line comments
    result = re.sub(r'/\*[\s\S]*?\*/', '', result)
    
    # Remove console.debug/log statements (if enabled)
    if strip_debug:
        result = re.sub(r'console\.(debug|log)\([^)]*\);?', '', result)
    
    # Remove unnecessary whitespace
    # - Multiple spaces -> single space
    result = re.sub(r'[ \t]+', ' ', result)
    
    # - Newlines around braces and operators
    result = re.sub(r'\s*([{}\[\]();,:])\s*', r'\1', result)
    result = re.sub(r'\s*([=+\-*/<>!&|])\s*', r'\1', result)
    
    # - Multiple newlines -> single newline
    result = re.sub(r'\n+', '\n', result)
    
    # - Leading/trailing whitespace per line
    result = '\n'.join(line.strip() for line in result.split('\n') if line.strip())
    
    # Restore strings
    for i, s in enumerate(strings):
        result = result.replace(f'__STRING_{i}__', s)
    
    return result


def minify_runtime(
    runtime_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    strip_debug: bool = True,
) -> dict:
    """
    Minify all PyNext runtime JS files.
    
    Args:
        runtime_dir: Directory containing runtime JS files
        output_dir: Directory for minified output (defaults to runtime_dir/min)
        strip_debug: Whether to remove console.debug statements
    
    Returns:
        Dict mapping filename to {original_size, minified_size, savings}
    """
    if runtime_dir is None:
        runtime_dir = Path(__file__).parent.parent / 'runtime'
    
    if output_dir is None:
        output_dir = runtime_dir / 'min'
    
    output_dir.mkdir(exist_ok=True)
    
    results = {}
    
    # Process root runtime files
    for js_file in runtime_dir.glob('*.js'):
        result = _minify_file(js_file, output_dir / js_file.name, strip_debug)
        results[js_file.name] = result
    
    # Process ui/ subdirectory
    ui_dir = runtime_dir / 'ui'
    if ui_dir.exists():
        ui_output = output_dir / 'ui'
        ui_output.mkdir(exist_ok=True)
        
        for js_file in ui_dir.glob('*.js'):
            result = _minify_file(js_file, ui_output / js_file.name, strip_debug)
            results[f'ui/{js_file.name}'] = result
    
    return results


def _minify_file(input_path: Path, output_path: Path, strip_debug: bool) -> dict:
    """Minify a single file."""
    source = input_path.read_text()
    minified = minify_js(source, strip_debug=strip_debug)
    output_path.write_text(minified)
    
    original_size = len(source)
    minified_size = len(minified)
    
    return {
        'original_size': original_size,
        'minified_size': minified_size,
        'savings': original_size - minified_size,
        'savings_percent': round((1 - minified_size / original_size) * 100, 1) if original_size > 0 else 0,
    }


def get_runtime_sizes(runtime_dir: Optional[Path] = None) -> dict:
    """
    Get current sizes of all runtime files.
    
    Returns:
        Dict mapping filename to size in bytes
    """
    if runtime_dir is None:
        runtime_dir = Path(__file__).parent.parent / 'runtime'
    
    sizes = {}
    
    for js_file in runtime_dir.glob('*.js'):
        sizes[js_file.name] = js_file.stat().st_size
    
    ui_dir = runtime_dir / 'ui'
    if ui_dir.exists():
        for js_file in ui_dir.glob('*.js'):
            sizes[f'ui/{js_file.name}'] = js_file.stat().st_size
    
    return sizes

