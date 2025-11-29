"""
PyNext Testing - Coverage Tools

Track code coverage with PyNext-specific metrics.
Goes beyond line coverage to measure signals, components, and branches.

Example:
    from pynext.testing import coverage_report, signal_coverage
    
    def test_counter():
        result = render(Counter)
        signal_coverage(result)  # Track which signals were used

Why PyNext-Specific Coverage:
    - Line coverage doesn't tell the whole story
    - Signal coverage shows reactivity testing
    - Component coverage shows UI coverage
    - Branch coverage shows edge cases
"""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from pynext.testing.render import RenderResult


# =============================================================================
# Coverage Data Structures
# =============================================================================

@dataclass
class SignalCoverage:
    """
    Coverage information for signals in a component.
    
    Tracks which signals were:
    - Defined
    - Read (accessed)
    - Written (set)
    """
    defined: Set[str] = field(default_factory=set)
    read: Set[str] = field(default_factory=set)
    written: Set[str] = field(default_factory=set)
    
    @property
    def coverage_ratio(self) -> float:
        """Ratio of used signals to defined signals."""
        if not self.defined:
            return 1.0
        used = self.read | self.written
        return len(used) / len(self.defined)
    
    @property
    def unused(self) -> Set[str]:
        """Signals that were defined but never used."""
        used = self.read | self.written
        return self.defined - used
    
    def __str__(self) -> str:
        return (
            f"Signal Coverage: {self.coverage_ratio:.0%}\n"
            f"  Defined: {sorted(self.defined)}\n"
            f"  Read:    {sorted(self.read)}\n"
            f"  Written: {sorted(self.written)}\n"
            f"  Unused:  {sorted(self.unused)}"
        )


@dataclass
class ComponentCoverage:
    """
    Coverage information for components.
    
    Tracks which components were:
    - Registered (in the codebase)
    - Rendered (in tests)
    - With all variants tested
    """
    registered: Set[str] = field(default_factory=set)
    rendered: Set[str] = field(default_factory=set)
    variants_tested: Dict[str, Set[str]] = field(default_factory=dict)
    
    @property
    def coverage_ratio(self) -> float:
        """Ratio of rendered components to registered components."""
        if not self.registered:
            return 1.0
        return len(self.rendered & self.registered) / len(self.registered)
    
    @property
    def untested(self) -> Set[str]:
        """Components that were never rendered."""
        return self.registered - self.rendered
    
    def __str__(self) -> str:
        return (
            f"Component Coverage: {self.coverage_ratio:.0%}\n"
            f"  Registered: {len(self.registered)}\n"
            f"  Rendered:   {len(self.rendered)}\n"
            f"  Untested:   {sorted(self.untested)}"
        )


@dataclass
class BranchCoverage:
    """
    Coverage for conditional branches in components.
    
    Tracks if all branches of Show/For/Match were tested.
    """
    total_branches: int = 0
    covered_branches: int = 0
    uncovered: List[str] = field(default_factory=list)
    
    @property
    def coverage_ratio(self) -> float:
        if self.total_branches == 0:
            return 1.0
        return self.covered_branches / self.total_branches
    
    def __str__(self) -> str:
        return (
            f"Branch Coverage: {self.coverage_ratio:.0%}\n"
            f"  Total:     {self.total_branches}\n"
            f"  Covered:   {self.covered_branches}\n"
            f"  Uncovered: {self.uncovered[:5]}..."
        )


@dataclass  
class CoverageReport:
    """
    Complete coverage report for a test session.
    """
    signals: SignalCoverage = field(default_factory=SignalCoverage)
    components: ComponentCoverage = field(default_factory=ComponentCoverage)
    branches: BranchCoverage = field(default_factory=BranchCoverage)
    
    def summary(self) -> str:
        """Generate a coverage summary."""
        return (
            f"╔══════════════════════════════════════════╗\n"
            f"║           Coverage Report                ║\n"
            f"╠══════════════════════════════════════════╣\n"
            f"║ Signals:    {self.signals.coverage_ratio:>6.1%}                     ║\n"
            f"║ Components: {self.components.coverage_ratio:>6.1%}                     ║\n"
            f"║ Branches:   {self.branches.coverage_ratio:>6.1%}                     ║\n"
            f"╚══════════════════════════════════════════╝"
        )


# =============================================================================
# Global Coverage Tracker
# =============================================================================

_coverage = CoverageReport()


def reset_coverage() -> None:
    """Reset coverage tracking."""
    global _coverage
    _coverage = CoverageReport()


def get_coverage() -> CoverageReport:
    """Get current coverage report."""
    return _coverage


# =============================================================================
# Signal Coverage
# =============================================================================

def signal_coverage(result: RenderResult) -> SignalCoverage:
    """
    Track signal coverage for a rendered component.
    
    Args:
        result: RenderResult from render()
        
    Returns:
        SignalCoverage with usage statistics
        
    Example:
        result = render(Counter)
        coverage = signal_coverage(result)
        assert coverage.coverage_ratio >= 0.8
    """
    coverage = SignalCoverage()
    
    # Get all defined signals
    for name, signal in result.signals.items():
        coverage.defined.add(name)
        
        # Check if signal was read during render
        # (This is a simplified check - real implementation would
        #  instrument the signal to track reads)
        if hasattr(signal, "_read_count") and signal._read_count > 0:
            coverage.read.add(name)
        else:
            # Assume read if value is in rendered HTML
            value = str(signal())
            if value in result.text:
                coverage.read.add(name)
    
    # Update global tracker
    _coverage.signals.defined |= coverage.defined
    _coverage.signals.read |= coverage.read
    _coverage.signals.written |= coverage.written
    
    return coverage


def assert_signal_coverage(
    result: RenderResult,
    min_ratio: float = 0.8,
) -> None:
    """
    Assert minimum signal coverage.
    
    Args:
        result: RenderResult to check
        min_ratio: Minimum coverage ratio (0-1)
        
    Example:
        result = render(Dashboard)
        assert_signal_coverage(result, min_ratio=0.9)
    """
    coverage = signal_coverage(result)
    
    if coverage.coverage_ratio < min_ratio:
        raise AssertionError(
            f"Signal coverage too low\n"
            f"  Required: {min_ratio:.0%}\n"
            f"  Actual:   {coverage.coverage_ratio:.0%}\n"
            f"  Unused:   {coverage.unused}"
        )


# =============================================================================
# Component Coverage
# =============================================================================

def register_component(name: str) -> None:
    """
    Register a component for coverage tracking.
    
    Called automatically by @component decorator if coverage is enabled.
    
    Args:
        name: Component name
    """
    _coverage.components.registered.add(name)


def track_render(name: str, variant: Optional[str] = None) -> None:
    """
    Track that a component was rendered.
    
    Called automatically by render() if coverage is enabled.
    
    Args:
        name: Component name
        variant: Optional variant that was tested
    """
    _coverage.components.rendered.add(name)
    
    if variant:
        if name not in _coverage.components.variants_tested:
            _coverage.components.variants_tested[name] = set()
        _coverage.components.variants_tested[name].add(variant)


def assert_component_coverage(min_ratio: float = 0.8) -> None:
    """
    Assert minimum component coverage.
    
    Args:
        min_ratio: Minimum ratio of tested components
        
    Example:
        # At end of test suite
        assert_component_coverage(min_ratio=0.9)
    """
    if _coverage.components.coverage_ratio < min_ratio:
        raise AssertionError(
            f"Component coverage too low\n"
            f"  Required:  {min_ratio:.0%}\n"
            f"  Actual:    {_coverage.components.coverage_ratio:.0%}\n"
            f"  Untested:  {_coverage.components.untested}"
        )


# =============================================================================
# Branch Coverage (Show/For/Match)
# =============================================================================

def analyze_branches(source_code: str) -> List[str]:
    """
    Analyze source code for conditional branches.
    
    Finds Show, For, and Match components that need branch testing.
    
    Args:
        source_code: Python source code
        
    Returns:
        List of branch identifiers
    """
    branches = []
    
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return branches
    
    class BranchFinder(ast.NodeVisitor):
        def visit_Call(self, node: ast.Call):
            # Look for Show(), For(), Match() calls
            if isinstance(node.func, ast.Name):
                name = node.func.id
                if name in ("Show", "For", "Match"):
                    branches.append(f"{name}:{node.lineno}")
            
            self.generic_visit(node)
    
    finder = BranchFinder()
    finder.visit(tree)
    
    return branches


def track_branch(branch_id: str) -> None:
    """Track that a branch was executed."""
    _coverage.branches.covered_branches += 1


def assert_branch_coverage(min_ratio: float = 0.8) -> None:
    """
    Assert minimum branch coverage.
    
    Args:
        min_ratio: Minimum ratio of covered branches
    """
    if _coverage.branches.coverage_ratio < min_ratio:
        raise AssertionError(
            f"Branch coverage too low\n"
            f"  Required: {min_ratio:.0%}\n"
            f"  Actual:   {_coverage.branches.coverage_ratio:.0%}"
        )


# =============================================================================
# Coverage Report Generation
# =============================================================================

def coverage_report() -> str:
    """
    Generate a full coverage report.
    
    Returns:
        Formatted coverage report string
        
    Example:
        # At end of test session
        print(coverage_report())
    """
    return _coverage.summary()


def coverage_json() -> Dict[str, Any]:
    """
    Export coverage data as JSON-compatible dict.
    
    Returns:
        Coverage data for CI/CD integration
    """
    return {
        "signals": {
            "defined": list(_coverage.signals.defined),
            "read": list(_coverage.signals.read),
            "written": list(_coverage.signals.written),
            "coverage_ratio": _coverage.signals.coverage_ratio,
        },
        "components": {
            "registered": list(_coverage.components.registered),
            "rendered": list(_coverage.components.rendered),
            "coverage_ratio": _coverage.components.coverage_ratio,
        },
        "branches": {
            "total": _coverage.branches.total_branches,
            "covered": _coverage.branches.covered_branches,
            "coverage_ratio": _coverage.branches.coverage_ratio,
        },
    }


def save_coverage_report(path: Path) -> None:
    """
    Save coverage report to file.
    
    Args:
        path: Output file path (.json or .html)
    """
    import json
    
    if path.suffix == ".json":
        path.write_text(json.dumps(coverage_json(), indent=2))
    elif path.suffix == ".html":
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>PyNext Coverage Report</title>
            <style>
                body {{ font-family: system-ui; padding: 2rem; }}
                .metric {{ display: inline-block; margin: 1rem; padding: 1rem; 
                          background: #f0f0f0; border-radius: 8px; }}
                .metric-value {{ font-size: 2rem; font-weight: bold; }}
                .metric-label {{ color: #666; }}
            </style>
        </head>
        <body>
            <h1>PyNext Coverage Report</h1>
            <div class="metric">
                <div class="metric-value">{_coverage.signals.coverage_ratio:.0%}</div>
                <div class="metric-label">Signal Coverage</div>
            </div>
            <div class="metric">
                <div class="metric-value">{_coverage.components.coverage_ratio:.0%}</div>
                <div class="metric-label">Component Coverage</div>
            </div>
            <div class="metric">
                <div class="metric-value">{_coverage.branches.coverage_ratio:.0%}</div>
                <div class="metric-label">Branch Coverage</div>
            </div>
            <h2>Details</h2>
            <pre>{_coverage.signals}</pre>
            <pre>{_coverage.components}</pre>
        </body>
        </html>
        """
        path.write_text(html)
    else:
        path.write_text(coverage_report())

