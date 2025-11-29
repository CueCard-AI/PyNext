"""
Build-time environment processing.

Handles:
- Validating env before build
- Inlining public vars into JS bundles
- Generating env.json for runtime mode

SolidJS Principle: All decisions at build time
AI-Friendly: Clear build vs runtime separation

Example:
    # Validate before build
    validate_env_for_build(Path.cwd(), "production")
    
    # Inline vars into JS
    process_js_bundle(js_path, env_vars)
    
    # Generate runtime config
    generate_env_json(Path.cwd(), Path(".pynext/public"), "production")
"""

from pathlib import Path
from typing import Dict, List, Optional
import json

from pynext.env.loader import load_env_files
from pynext.env.schema import load_schema
from pynext.env.client import get_public_vars, inline_env_in_js, generate_inline_script


def validate_env_for_build(
    root: Path,
    mode: str = "production",
    fail_on_warning: bool = False,
) -> bool:
    """
    Validate environment before build.
    
    Args:
        root: Project root directory
        mode: Build mode (production/development/test)
        fail_on_warning: If True, treat warnings as errors
    
    Returns:
        True if validation passed
    
    Raises:
        EnvironmentError: If schema exists and validation fails
    
    Example:
        # In build script
        validate_env_for_build(Path.cwd(), "production")
        # Raises if any required vars are missing
    """
    env_vars = load_env_files(root, mode)
    schema = load_schema(root)
    
    if schema:
        result = schema.validate(env_vars)
        
        if fail_on_warning and result.warnings:
            raise EnvironmentError(
                "Environment validation warnings (treated as errors):\n" +
                "\n".join(f"  - {w}" for w in result.warnings)
            )
        
        result.raise_if_invalid()
        
        # Print success message
        required = len(schema.get_required_vars())
        optional = len(schema.get_optional_vars())
        print(f"[PyNext] Environment validated: {required} required, {optional} optional vars")
        
        return True
    
    # No schema - just report var count
    print(f"[PyNext] Environment loaded ({len(env_vars)} vars, no schema)")
    return True


def process_js_bundle(
    js_path: Path,
    env_vars: Dict[str, str],
    output_path: Optional[Path] = None,
) -> None:
    """
    Inline public env vars into a JS bundle.
    
    Replaces process.env.VAR and import.meta.env.VAR
    with actual values.
    
    Args:
        js_path: Path to input JS file
        env_vars: All environment variables
        output_path: Output path (defaults to overwriting input)
    
    Example:
        # Input JS: const api = process.env.API_URL;
        # After: const api = "https://api.example.com";
        
        process_js_bundle(
            Path("dist/app.js"),
            {"PYNEXT_PUBLIC_API_URL": "https://api.example.com"}
        )
    """
    public_vars = get_public_vars(env_vars)
    
    if not public_vars:
        return  # Nothing to inline
    
    content = js_path.read_text(encoding="utf-8")
    processed = inline_env_in_js(content, public_vars)
    
    output = output_path or js_path
    output.write_text(processed, encoding="utf-8")


def process_all_js_bundles(
    build_dir: Path,
    env_vars: Dict[str, str],
    extensions: List[str] = None,
) -> int:
    """
    Process all JS files in build directory.
    
    Args:
        build_dir: Directory containing built JS files
        env_vars: All environment variables
        extensions: File extensions to process (default: [".js", ".mjs"])
    
    Returns:
        Number of files processed
    """
    extensions = extensions or [".js", ".mjs"]
    public_vars = get_public_vars(env_vars)
    
    if not public_vars:
        return 0
    
    count = 0
    for ext in extensions:
        for js_path in build_dir.rglob(f"*{ext}"):
            content = js_path.read_text(encoding="utf-8")
            
            # Check if file needs processing
            needs_processing = any(
                f"process.env.{key}" in content or
                f"import.meta.env.{key}" in content
                for key in public_vars
            )
            
            if needs_processing:
                processed = inline_env_in_js(content, public_vars)
                js_path.write_text(processed, encoding="utf-8")
                count += 1
    
    return count


def generate_env_json(
    root: Path,
    output_dir: Path,
    mode: str = "production",
) -> Path:
    """
    Generate env.json for runtime client access.
    
    Only includes PYNEXT_PUBLIC_* vars.
    
    Args:
        root: Project root directory
        output_dir: Directory to write env.json
        mode: Build mode
    
    Returns:
        Path to generated env.json
    
    Example:
        # Generates .pynext/public/env.json
        path = generate_env_json(
            Path.cwd(),
            Path(".pynext/public"),
            "production"
        )
    """
    env_vars = load_env_files(root, mode)
    public_vars = get_public_vars(env_vars)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "env.json"
    output_file.write_text(
        json.dumps(public_vars, indent=2, sort_keys=True),
        encoding="utf-8"
    )
    
    return output_file


def generate_env_types(
    root: Path,
    output_path: Optional[Path] = None,
) -> Optional[str]:
    """
    Generate TypeScript types for environment variables.
    
    Args:
        root: Project root directory
        output_path: Optional path to write types file
    
    Returns:
        TypeScript type definitions string
    
    Example:
        types = generate_env_types(Path.cwd())
        # Returns TypeScript interface for env vars
    """
    schema = load_schema(root)
    if not schema:
        return None
    
    lines = [
        "// Auto-generated from env.schema.py",
        "// Do not edit manually",
        "",
        "interface PyNextEnv {",
    ]
    
    for key, var in schema.vars.items():
        # Only public vars for client types
        if key.startswith("PYNEXT_PUBLIC_"):
            client_key = key.replace("PYNEXT_PUBLIC_", "")
            ts_type = _python_type_to_ts(var.type)
            optional = "?" if not var.required else ""
            
            if var.description:
                lines.append(f"  /** {var.description} */")
            lines.append(f"  {client_key}{optional}: {ts_type};")
    
    lines.append("}")
    lines.append("")
    lines.append("declare global {")
    lines.append("  interface Window {")
    lines.append("    __PYNEXT_ENV__: PyNextEnv;")
    lines.append("  }")
    lines.append("}")
    lines.append("")
    lines.append("export {};")
    
    content = "\n".join(lines)
    
    if output_path:
        output_path.write_text(content, encoding="utf-8")
    
    return content


def _python_type_to_ts(py_type) -> str:
    """Convert Python type to TypeScript type."""
    type_map = {
        str: "string",
        int: "number",
        float: "number",
        bool: "boolean",
        list: "string[]",
    }
    return type_map.get(py_type, "string")


def get_build_env_summary(root: Path, mode: str = "production") -> Dict:
    """
    Get summary of environment for build logging.
    
    Args:
        root: Project root directory
        mode: Build mode
    
    Returns:
        Dict with summary information
    """
    env_vars = load_env_files(root, mode)
    public_vars = get_public_vars(env_vars)
    schema = load_schema(root)
    
    return {
        "mode": mode,
        "total_vars": len(env_vars),
        "public_vars": len(public_vars),
        "has_schema": schema is not None,
        "required_vars": len(schema.get_required_vars()) if schema else 0,
        "optional_vars": len(schema.get_optional_vars()) if schema else 0,
        "public_var_names": list(public_vars.keys()),
    }


def inject_env_into_html(
    html_path: Path,
    env_vars: Dict[str, str],
    output_path: Optional[Path] = None,
    mode: str = "inline",
) -> None:
    """
    Inject environment variables into HTML file.
    
    Args:
        html_path: Path to HTML file
        env_vars: All environment variables
        output_path: Output path (defaults to overwriting input)
        mode: "inline" for build-time or "runtime" for fetch-based
    """
    from pynext.env.client import inject_env_into_html as inject
    
    public_vars = get_public_vars(env_vars)
    html = html_path.read_text(encoding="utf-8")
    
    processed = inject(html, public_vars, mode)
    
    output = output_path or html_path
    output.write_text(processed, encoding="utf-8")

