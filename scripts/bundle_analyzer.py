#!/usr/bin/env python3
"""
PyNext Bundle Analyzer - Python Wrapper

=============================================================================
WHO: Developers, CI/CD pipelines, LLMs helping with PyNext
=============================================================================

=============================================================================
WHAT THIS FILE DOES
=============================================================================

Provides a Python interface to the bundle analyzer. You can:
1. Run it as a CLI tool
2. Import it as a module for programmatic use

=============================================================================
WHEN TO USE
=============================================================================

- Before committing: Check that bundle sizes haven't grown
- During CI: Automatically fail builds if bundles exceed limits
- When debugging: Identify which modules contribute to bundle size

=============================================================================
WHERE TO RUN
=============================================================================

From the project root:
    python scripts/bundle_analyzer.py
    python scripts/bundle_analyzer.py --real-apps
    python scripts/bundle_analyzer.py --json

=============================================================================
WHY THIS EXISTS
=============================================================================

Makes bundle analysis accessible without knowing Node.js commands.
Also enables programmatic access for build scripts and tests.

=============================================================================
HOW TO USE
=============================================================================

CLI:
    python scripts/bundle_analyzer.py              # Basic check
    python scripts/bundle_analyzer.py --real-apps  # Include real app sizes
    python scripts/bundle_analyzer.py --verbose    # Full breakdown
    python scripts/bundle_analyzer.py --json       # Output as JSON

Programmatic:
    from scripts.bundle_analyzer import analyze_bundles, analyze_real_apps
    
    report = analyze_bundles()
    if report.get('failed'):
        print("Bundle size limits exceeded!")
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# =============================================================================
# Configuration
# =============================================================================

PROJECT_ROOT = Path(__file__).parent.parent


# =============================================================================
# Core Functions
# =============================================================================

def run_node_analyzer(*args: str) -> Dict[str, Any]:
    """
    Run the Node.js bundle analyzer and return results.
    
    Args:
        *args: Arguments to pass to analyze-bundle.js
    
    Returns:
        Dictionary with analysis results
    
    Example:
        report = run_node_analyzer("--real-apps")
        print(report["totals"]["gzip"])
    """
    cmd = ["node", "scripts/analyze-bundle.js", "--json", *args]
    
    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
        
        if result.returncode != 0:
            # Try to parse any JSON in stderr for error details
            error_msg = result.stderr.strip() or "Unknown error"
            print(f"❌ Bundle analysis failed: {error_msg}", file=sys.stderr)
            return {"error": error_msg, "failed": True}
        
        # Parse JSON output
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            # If not JSON, the analyzer printed human-readable output
            # This happens when --json wasn't passed properly
            return {"raw_output": result.stdout, "failed": False}
        
    except subprocess.TimeoutExpired:
        return {"error": "Analysis timed out after 120 seconds", "failed": True}
    except FileNotFoundError:
        return {
            "error": "Node.js not found. Please run 'npm install' first.",
            "failed": True
        }


def analyze_bundles(verbose: bool = False) -> Dict[str, Any]:
    """
    Analyze bundle sizes for all runtime modules.
    
    Args:
        verbose: If True, include module-level breakdown
    
    Returns:
        Dictionary containing:
        - bundles: List of bundle info (name, gzip, limit, etc.)
        - totals: Aggregate sizes
        - failed: True if any bundle exceeds limits
        - warnings: Number of bundles near limits
    
    Example:
        report = analyze_bundles()
        for bundle in report.get("bundles", []):
            print(f"{bundle['name']}: {bundle['gzip']}B")
    """
    args = ["--verbose"] if verbose else []
    return run_node_analyzer(*args)


def analyze_real_apps() -> Dict[str, Any]:
    """
    Analyze bundle sizes for real transpiled Python apps.
    
    This is the most accurate measure of what end users will experience.
    It transpiles sample Python code to JavaScript and bundles it with
    the runtime to get real-world sizes.
    
    Returns:
        Dictionary containing both runtime bundle info AND real app sizes
    
    Example:
        report = analyze_real_apps()
        # Check if any real apps exceed limits
        if report.get("failed"):
            print("Some bundles exceed limits!")
    """
    return run_node_analyzer("--real-apps")


# =============================================================================
# Output Formatting
# =============================================================================

def format_size(bytes_val: int) -> str:
    """Format bytes as human-readable string."""
    if bytes_val >= 1024:
        return f"{bytes_val / 1024:.2f}KB"
    return f"{bytes_val}B"


def print_summary(report: Dict[str, Any]) -> None:
    """
    Print a human-readable summary of the analysis.
    
    Args:
        report: Analysis report from analyze_bundles() or analyze_real_apps()
    """
    if report.get("error"):
        print(f"❌ Error: {report['error']}")
        return
    
    if report.get("raw_output"):
        # Direct output from analyzer (not JSON)
        print(report["raw_output"])
        return
    
    print()
    print("📦 PyNext Bundle Size Analysis")
    print("=" * 60)
    
    bundles = report.get("bundles", [])
    if not bundles:
        print("  No bundles analyzed")
        return
    
    for bundle in bundles:
        # Determine status emoji
        if bundle.get("overLimit"):
            status = "❌"
        elif bundle.get("nearLimit"):
            status = "⚠️"
        else:
            status = "✅"
        
        gzip = bundle.get("gzip", 0)
        limit = bundle.get("limit", 0)
        usage = round((gzip / limit) * 100) if limit else 0
        
        name = bundle.get("name", "unknown")
        size_str = format_size(gzip)
        limit_str = format_size(limit)
        
        print(f"  {status} {name:25s} {size_str:>10s} / {limit_str:>10s} ({usage}%)")
    
    print("=" * 60)
    
    # Summary
    totals = report.get("totals", {})
    total_gzip = totals.get("gzip", 0)
    print(f"  Total: {format_size(total_gzip)}")
    
    if report.get("failed"):
        print()
        print("❌ FAILED: Some bundles exceed size limits!")
        print("   Review the bundles marked with ❌ and optimize.")
    elif report.get("warnings", 0) > 0:
        print()
        print(f"⚠️  WARNING: {report['warnings']} bundle(s) approaching limit")
    else:
        print()
        print("✅ All bundles within limits!")


# =============================================================================
# CLI
# =============================================================================

def main() -> int:
    """
    CLI entry point.
    
    Returns:
        Exit code (0 = success, 1 = failure)
    """
    parser = argparse.ArgumentParser(
        description="Analyze PyNext bundle sizes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/bundle_analyzer.py              # Basic check
  python scripts/bundle_analyzer.py --real-apps  # Include real app sizes
  python scripts/bundle_analyzer.py --verbose    # Full breakdown
  python scripts/bundle_analyzer.py --json       # Output as JSON

Programmatic Usage:
  from scripts.bundle_analyzer import analyze_bundles, analyze_real_apps
  
  report = analyze_bundles()
  print(f"Total: {report['totals']['gzip']} bytes")
        """,
    )
    
    parser.add_argument(
        "--real-apps",
        action="store_true",
        help="Include real app bundle analysis (transpile Python → bundle)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Include module-level breakdown",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON (for programmatic use)",
    )
    
    args = parser.parse_args()
    
    # Run analysis
    if args.real_apps:
        report = analyze_real_apps()
    else:
        report = analyze_bundles(verbose=args.verbose)
    
    # Output
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_summary(report)
    
    # Exit code
    return 1 if report.get("failed") else 0


if __name__ == "__main__":
    sys.exit(main())

