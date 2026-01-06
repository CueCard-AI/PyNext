"""
PyNext Transpiler CLI - Command-line Interface for Transpilation

=============================================================================
WHAT THIS FILE DOES
=============================================================================

This module provides CLI commands for transpiling Python handlers to
JavaScript. It's useful for:

1. Debugging - See what JavaScript is generated from Python
2. Inspection - Check if handlers can be transpiled
3. Development - Export JS for testing in browser

=============================================================================
USAGE EXAMPLES
=============================================================================

    # Transpile a file and print to terminal
    pynext transpile pages/issues.py --print

    # Transpile with Python source as comments
    pynext transpile pages/issues.py --print --annotate

    # Transpile to a file
    pynext transpile pages/issues.py --output handlers.js

    # Show runtime dependencies
    pynext transpile pages/issues.py --deps

    # Transpile all handlers in project
    pynext transpile --all --output-dir ./debug-js/

=============================================================================
"""

from __future__ import annotations

import ast
import importlib.util
import os
import re
import sys
import textwrap
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

import click

from .reactive import (
    ReactiveContext,
    analyze_handler,
    get_handler_source,
    get_handler_name,
    create_context,
)
from .hydration import (
    transpile_for_hydration,
    HydrationOptions,
    generate_debug_output,
    get_runtime_dependencies,
    transpile_handlers_batch,
)
from .errors import TranspileError


# =============================================================================
# CLI GROUP
# =============================================================================

@click.group()
def transpiler_cli():
    """PyNext Transpiler CLI commands."""
    pass


# =============================================================================
# MAIN TRANSPILE COMMAND
# =============================================================================

@click.command("transpile")
@click.argument("file", required=False, type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option("--output-dir", type=click.Path(), help="Output directory for --all")
@click.option("--print", "print_", is_flag=True, help="Print to terminal")
@click.option("--annotate", is_flag=True, help="Include Python source as comments")
@click.option("--deps", is_flag=True, help="Show runtime dependencies")
@click.option("--all", "all_", is_flag=True, help="Transpile all handlers in project")
@click.option("--debug", is_flag=True, help="Show detailed debug output")
@click.option("--handler", "-h", multiple=True, help="Specific handler name(s) to transpile")
def transpile_cmd(
    file: Optional[str],
    output: Optional[str],
    output_dir: Optional[str],
    print_: bool,
    annotate: bool,
    deps: bool,
    all_: bool,
    debug: bool,
    handler: tuple,
):
    """
    Transpile Python handlers to JavaScript.
    
    Examples:
    
        # Transpile a file and print
        pynext transpile pages/issues.py --print
        
        # Transpile with source comments
        pynext transpile pages/issues.py --print --annotate
        
        # Show what runtime functions are used
        pynext transpile pages/issues.py --deps
        
        # Transpile specific handlers
        pynext transpile pages/issues.py -h handle_add_issue -h handle_delete
    """
    if all_:
        _transpile_all(output_dir, annotate)
        return
    
    if not file:
        click.echo("Error: FILE argument required (use --all for all handlers)", err=True)
        raise SystemExit(1)
    
    # Load the module
    try:
        handlers = _load_handlers_from_file(file)
    except Exception as e:
        click.echo(f"Error loading {file}: {e}", err=True)
        raise SystemExit(1)
    
    if not handlers:
        click.echo(f"No handlers found in {file}", err=True)
        raise SystemExit(1)
    
    # Filter to specific handlers if requested
    if handler:
        handlers = {name: func for name, func in handlers.items() if name in handler}
        if not handlers:
            click.echo(f"Handlers not found: {', '.join(handler)}", err=True)
            raise SystemExit(1)
    
    # Options
    options = HydrationOptions(
        wrap_in_function=True,
        include_comments=annotate,
    )
    
    # Process each handler
    results = []
    all_deps: Set[str] = set()
    
    for name, func in handlers.items():
        if debug:
            click.echo(generate_debug_output(func))
            continue
        
        try:
            ctx = analyze_handler(func)
            js = transpile_for_hydration(func, ctx, options)
            results.append((name, js, None))
            
            if deps:
                all_deps.update(get_runtime_dependencies(func, ctx))
        
        except Exception as e:
            results.append((name, "", str(e)))
    
    if debug:
        return
    
    # Output results
    if deps:
        click.echo("\n─── Runtime Dependencies ───\n")
        for dep in sorted(all_deps):
            click.echo(f"  {dep}")
        click.echo()
        return
    
    # Build output
    output_lines = [
        "// ═══════════════════════════════════════════════════════════════════════════",
        f"// Transpiled from: {file}",
        f"// Handlers: {', '.join(name for name, _, _ in results)}",
        "// Generated by: pynext transpile",
        "// ═══════════════════════════════════════════════════════════════════════════",
        "",
    ]
    
    for name, js, error in results:
        if error:
            output_lines.extend([
                f"// ERROR: {name}",
                f"// {error}",
                "",
            ])
        else:
            output_lines.append(js)
            output_lines.append("")
    
    output_text = "\n".join(output_lines)
    
    if print_ or not output:
        click.echo(output_text)
    
    if output:
        Path(output).write_text(output_text)
        click.echo(f"Wrote {output}")


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _load_handlers_from_file(file_path: str) -> Dict[str, Callable]:
    """
    Load Python file and extract handler functions.
    
    A handler is any function that:
    1. Starts with "handle_" or "on_"
    2. Has a closure with reactive objects
    """
    path = Path(file_path)
    
    # Load the module
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {file_path}")
    
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module
    
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        raise ImportError(f"Error executing {file_path}: {e}")
    
    # Find handlers
    handlers = {}
    
    for name in dir(module):
        if name.startswith("_"):
            continue
        
        obj = getattr(module, name)
        
        # Check if it's a handler function
        if callable(obj) and (
            name.startswith("handle_") or
            name.startswith("on_") or
            _has_reactive_closure(obj)
        ):
            handlers[name] = obj
    
    return handlers


def _has_reactive_closure(func: Callable) -> bool:
    """Check if function has reactive objects in closure."""
    closure = getattr(func, "__closure__", None) or ()
    
    for cell in closure:
        try:
            value = cell.cell_contents
            if hasattr(value, "__pynext_type__"):
                return True
        except (ValueError, AttributeError):
            pass
    
    return False


def _transpile_all(output_dir: Optional[str], annotate: bool):
    """Transpile all handlers in the project."""
    # Find all Python files in pages/ directory
    pages_dir = Path("pages")
    
    if not pages_dir.exists():
        click.echo("No pages/ directory found", err=True)
        raise SystemExit(1)
    
    output_path = Path(output_dir) if output_dir else Path(".pynext/debug")
    output_path.mkdir(parents=True, exist_ok=True)
    
    options = HydrationOptions(
        wrap_in_function=True,
        include_comments=annotate,
    )
    
    for py_file in pages_dir.rglob("*.py"):
        if py_file.name.startswith("_"):
            continue
        
        try:
            handlers = _load_handlers_from_file(str(py_file))
            
            if not handlers:
                continue
            
            # Transpile all handlers
            output_lines = [
                "// ═══════════════════════════════════════════════════════════════════════════",
                f"// Transpiled from: {py_file}",
                f"// Handlers: {', '.join(handlers.keys())}",
                "// ═══════════════════════════════════════════════════════════════════════════",
                "",
            ]
            
            for name, func in handlers.items():
                try:
                    ctx = analyze_handler(func)
                    js = transpile_for_hydration(func, ctx, options)
                    output_lines.append(js)
                    output_lines.append("")
                except Exception as e:
                    output_lines.extend([
                        f"// ERROR: {name}",
                        f"// {e}",
                        "",
                    ])
            
            # Write output
            output_file = output_path / f"{py_file.stem}.handlers.js"
            output_file.write_text("\n".join(output_lines))
            click.echo(f"Wrote {output_file}")
        
        except Exception as e:
            click.echo(f"Error processing {py_file}: {e}", err=True)


# =============================================================================
# CHECK COMMAND
# =============================================================================

@click.command("check")
@click.argument("file", type=click.Path(exists=True))
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
def check_cmd(file: str, verbose: bool):
    """
    Check if handlers in a file can be transpiled.
    
    Example:
        pynext check pages/issues.py
    """
    try:
        handlers = _load_handlers_from_file(file)
    except Exception as e:
        click.echo(f"Error loading {file}: {e}", err=True)
        raise SystemExit(1)
    
    if not handlers:
        click.echo(f"No handlers found in {file}")
        return
    
    passed = 0
    failed = 0
    
    for name, func in handlers.items():
        try:
            ctx = analyze_handler(func)
            transpile_for_hydration(func, ctx)
            passed += 1
            click.echo(f"✓ {name}")
            
            if verbose:
                deps = get_runtime_dependencies(func, ctx)
                for dep in sorted(deps):
                    click.echo(f"    uses {dep}")
        
        except Exception as e:
            failed += 1
            click.echo(f"✗ {name}: {e}")
    
    click.echo()
    click.echo(f"Passed: {passed}, Failed: {failed}")
    
    if failed > 0:
        raise SystemExit(1)


# =============================================================================
# DEPS COMMAND
# =============================================================================

@click.command("deps")
@click.argument("file", type=click.Path(exists=True))
def deps_cmd(file: str):
    """
    Show runtime dependencies for handlers.
    
    Example:
        pynext deps pages/issues.py
    """
    try:
        handlers = _load_handlers_from_file(file)
    except Exception as e:
        click.echo(f"Error loading {file}: {e}", err=True)
        raise SystemExit(1)
    
    all_deps: Set[str] = set()
    
    for name, func in handlers.items():
        try:
            ctx = analyze_handler(func)
            deps = get_runtime_dependencies(func, ctx)
            all_deps.update(deps)
        except Exception:
            pass
    
    click.echo("\nRuntime dependencies:\n")
    
    pynext_deps = sorted(d for d in all_deps if d.startswith("__pynext__"))
    py_deps = sorted(d for d in all_deps if d.startswith("__py"))
    
    if pynext_deps:
        click.echo("  PyNext Runtime:")
        for dep in pynext_deps:
            click.echo(f"    {dep}")
    
    if py_deps:
        click.echo("\n  Python Runtime:")
        for dep in py_deps:
            click.echo(f"    {dep}")
    
    click.echo()


# =============================================================================
# REGISTER COMMANDS
# =============================================================================

transpiler_cli.add_command(transpile_cmd)
transpiler_cli.add_command(check_cmd)
transpiler_cli.add_command(deps_cmd)


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    """Main entry point for CLI."""
    transpiler_cli()


if __name__ == "__main__":
    main()
