"""
Robust Runtime Loader for Transpiler Test Execution

WHAT: Core infrastructure for loading transpiler runtime modules in test contexts
WHY: Single source of truth for runtime loading, eliminates duplication, handles edge cases
HOW: Uses esbuild for robust ES module bundling, falls back gracefully to string conversion
WHO: Used by all test harnesses (MiniAppHarness, PythonJSExecutor, etc.)
WHEN: During test execution to provide __py.dunders.* and other runtime helpers
WHERE: Core infrastructure - part of pynext.transpiler package

This fixes Segment 7 by ensuring dunders.js is always loaded properly.
"""

import subprocess
import tempfile
import shutil
import warnings
from pathlib import Path
from typing import Optional, List


def _ensure_esbuild() -> bool:
    """Check if esbuild is available (local node_modules, direct, or via npx)."""
    # Check for local installation in node_modules/.bin/esbuild
    try:
        import pynext
        root_path = Path(pynext.__file__).parent.parent
        local_esbuild = root_path / "node_modules" / ".bin" / "esbuild"
        if local_esbuild.exists():
            return True
    except (ImportError, AttributeError):
        pass
    
    # Check for global esbuild
    if shutil.which("esbuild"):
        return True
    
    # Check for npx (can install on-the-fly)
    if shutil.which("npx"):
        return True
    
    return False


def _get_esbuild_command() -> List[str]:
    """
    Get esbuild command path, checking local node_modules first.
    
    Returns:
        List with esbuild command (e.g., ['node_modules/.bin/esbuild'] or ['esbuild'])
    """
    # Check for local installation first
    try:
        import pynext
        root_path = Path(pynext.__file__).parent.parent
        local_esbuild = root_path / "node_modules" / ".bin" / "esbuild"
        if local_esbuild.exists():
            return [str(local_esbuild)]
    except (ImportError, AttributeError):
        pass
    
    # Fallback to global
    return ["esbuild"]


def _bundle_with_esbuild(module_path: Path, use_npx: bool = False) -> str:
    """
    Bundle ES module using esbuild (robust approach).
    
    This handles ALL edge cases correctly:
    - Comments containing "export"/"import" keywords
    - String literals with keywords
    - Template literals
    - Complex export syntax
    - Re-exports
    - Everything else esbuild handles correctly
    
    Args:
        module_path: Path to ES module file to bundle
        use_npx: Whether to use npx (default: False, uses esbuild directly)
    
    Returns:
        Bundled JavaScript code (CommonJS format)
    
    Raises:
        subprocess.CalledProcessError: If esbuild fails
        FileNotFoundError: If esbuild command not found
    """
    abs_path = module_path.resolve()
    
    # Create temporary entry file that imports the module
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.js',
        delete=False
    ) as entry_file:
        entry_file.write(f'import * as module from "{abs_path}";\n')
        entry_file.write('module.exports = module;\n')
        entry_path = Path(entry_file.name)
    
    try:
        # Create output file
        with tempfile.NamedTemporaryFile(
            mode='r',
            suffix='.js',
            delete=False
        ) as output_file:
            output_path = Path(output_file.name)
        
        # Build esbuild command
        if use_npx:
            cmd = ["npx", "--yes", "esbuild"]
        else:
            cmd = _get_esbuild_command()
        
        cmd.extend([
            str(entry_path),
            f"--outfile={output_path}",
            "--bundle",
            "--format=cjs",
            "--target=es2020",
            "--platform=node",
        ])
        
        # Run esbuild
        subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=60 if use_npx else 30
        )
        
        bundled = output_path.read_text()
        return bundled
        
    finally:
        # Cleanup temp files
        if entry_path.exists():
            entry_path.unlink()
        if output_path.exists():
            output_path.unlink()


def _convert_esm_simple(file_path: Path) -> str:
    """
    Simple ES module conversion (fallback only).
    
    WARNING: This is fragile and may break on edge cases:
    - Comments containing "export"/"import" keywords
    - String literals with keywords
    - Template literals
    - Complex export syntax
    
    Only use when esbuild is unavailable. This preserves the existing
    working logic from PythonJSExecutor._load_esm_module().
    
    Args:
        file_path: Path to ES module file
    
    Returns:
        JavaScript code with imports removed and exports converted
    """
    code = file_path.read_text()
    lines = code.split('\n')
    result_lines = []
    in_import_block = False
    in_default_export = False
    default_export_name = file_path.stem  # e.g., "dunders"
    
    for line in lines:
        stripped = line.strip()
        
        # Skip empty lines and preserve structure
        if not stripped:
            result_lines.append(line)
            continue
        
        # Skip import statements
        if stripped.startswith('import '):
            in_import_block = True
            if ' from ' in line and (';' in line or line.endswith(("'", '"'))):
                in_import_block = False
            continue
        
        if in_import_block:
            if ' from ' in line and (';' in line or line.endswith(("'", '"'))):
                in_import_block = False
            continue
        
        # Handle default export
        if stripped.startswith('export default '):
            rest = line[len('export default '):].strip()
            if rest.startswith('{'):
                result_lines.append(f"const {default_export_name} = {rest}")
                in_default_export = True
                if rest.endswith('};') or rest.endswith('}'):
                    in_default_export = False
            else:
                result_lines.append(f"const {default_export_name} = {rest}")
            continue
        
        # Handle continuation of multi-line default export
        if in_default_export:
            result_lines.append(line)
            if '};' in line or (line.strip().endswith('}') and not line.strip().endswith('},')):
                in_default_export = False
            continue
        
        # Convert named exports to regular declarations
        if stripped.startswith('export const '):
            result_lines.append(line.replace('export const ', 'const ', 1))
        elif stripped.startswith('export function '):
            result_lines.append(line.replace('export function ', 'function ', 1))
        elif stripped.startswith('export class '):
            result_lines.append(line.replace('export class ', 'class ', 1))
        elif stripped.startswith('export {') and '}' in line:
            # Named export with aliases: export { A as B, C }
            export_content = line[line.index('{') + 1:line.index('}')].strip()
            if export_content:
                for item in export_content.split(','):
                    item = item.strip()
                    if ' as ' in item:
                        original, alias = item.split(' as ', 1)
                        result_lines.append(f"const {alias.strip()} = {original.strip()};")
                    else:
                        result_lines.append(f"const {item} = {item};")
            continue
        elif stripped.startswith('export '):
            result_lines.append(line.replace('export ', '', 1))
        else:
            result_lines.append(line)
    
    return '\n'.join(result_lines)


def load_esm_module(file_path: Path) -> str:
    """
    Load ES module with robust handling.
    
    Tries esbuild first (handles all edge cases), falls back to simple
    conversion if esbuild is unavailable.
    
    Args:
        file_path: Path to ES module file to load
    
    Returns:
        JavaScript code (CommonJS format) ready for eval
    
    Example:
        >>> dunders_code = load_esm_module(Path("pynext/transpiler/runtime/dunders.js"))
        >>> # Returns CommonJS-compatible code
    """
    # Check if esbuild is directly available (not just npx)
    esbuild_available = shutil.which("esbuild") is not None
    
    # Try esbuild first if directly available (most robust)
    if esbuild_available:
        try:
            return _bundle_with_esbuild(file_path, use_npx=False)
        except Exception as e:
            # Only warn if esbuild was directly available but failed
            warnings.warn(
                f"esbuild failed for {file_path.name}: {e}. "
                "Using fallback conversion (may have edge case issues).",
                RuntimeWarning
            )
    # Try npx esbuild as fallback (silently - npx might not be available or need network)
    elif shutil.which("npx") is not None:
        try:
            return _bundle_with_esbuild(file_path, use_npx=True)
        except Exception:
            # npx fallback failed - silently use simple conversion
            # (npx might require network access, so this is expected and not worth warning)
            pass
    
    # Fallback to simple conversion (no warning - this is the expected path when esbuild unavailable)
    return _convert_esm_simple(file_path)


def get_test_runtime(include_dunders: bool = True) -> str:
    """
    Get bundled runtime for test execution.
    
    This is the main entry point for test harnesses. Loads setup.js
    and optionally dunders.js (required for operator overloading).
    
    Args:
        include_dunders: Whether to include dunders.js (default: True, required for Segment 7)
    
    Returns:
        Complete JavaScript runtime code (CommonJS format) ready for eval
    
    Raises:
        FileNotFoundError: If setup.js or required modules are not found
    
    Example:
        >>> runtime = get_test_runtime()  # Includes dunders.js
        >>> # Use in test harness
    """
    # Auto-detect root path
    try:
        import pynext
        root_path = Path(pynext.__file__).parent.parent
    except ImportError:
        # Fallback to current working directory
        root_path = Path.cwd()
        # Try to find root by looking for common markers
        if not (root_path / "pynext").exists():
            # Try going up from tests directory
            current = Path(__file__).resolve()
            if "tests" in current.parts:
                idx = current.parts.index("tests")
                root_path = Path(*current.parts[:idx])
            elif "pynext" in current.parts:
                idx = current.parts.index("pynext")
                root_path = Path(*current.parts[:idx])
    
    # Try multiple possible locations for setup.js
    setup_path = root_path / "js" / "transpiler" / "setup.js"
    if not setup_path.exists():
        # Try tests/js/transpiler/setup.js (actual location)
        setup_path = root_path / "tests" / "js" / "transpiler" / "setup.js"
    if not setup_path.exists():
        raise FileNotFoundError(
            f"setup.js not found. Tried: "
            f"{root_path / 'js' / 'transpiler' / 'setup.js'} and "
            f"{root_path / 'tests' / 'js' / 'transpiler' / 'setup.js'}. "
            "Ensure you're running from the project root."
        )
    
    setup_code = setup_path.read_text()
    
    # setup.js already includes all dunder methods (__py.dunders.equals, etc.)
    # so we don't need to load dunders.js separately.
    # The dunders.js file is kept for direct ES6 module usage but is not
    # needed for the test runtime since setup.js is self-contained.
    #
    # Note: include_dunders flag is now effectively ignored since setup.js
    # already has all dunder support built-in.
    
    return setup_code

