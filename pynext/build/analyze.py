"""
PyNext Build - Bundle Analysis

=============================================================================
WHAT THIS FILE DOES
=============================================================================

Analyzes compiled bundles to provide insights into bundle composition,
size breakdown, and optimization opportunities.

    from pynext.build.analyze import analyze_bundle, print_report
    
    analysis = analyze_bundle(".pynext/build/")
    print_report(analysis)

=============================================================================
OUTPUT EXAMPLE
=============================================================================

    PyNext Bundle Analysis
    ═══════════════════════════════════════════════════════════════
    
    Total Size: 12.4 KB (4.1 KB gzipped)
    
    Breakdown:
    ├── Runtime (reactive.min.js)    2.3 KB (18.5%)  ████
    ├── Counter.js                   0.8 KB (6.5%)   ██
    ├── TodoList.js                  1.2 KB (9.7%)   ██
    └── Dashboard.js                 8.1 KB (65.3%)  █████████████
    
    Features Used:
    ✓ signals (all islands)
    ✓ effects (Counter, Dashboard)
    ✓ stores (Dashboard)
    ✗ memos (unused)
    ✗ forms (unused)
    
    Recommendations:
    • Dashboard.js is 65% of bundle - consider code splitting
    • Tree shaking could save 0.4 KB (remove unused: memos, forms)

=============================================================================
"""

from __future__ import annotations

import gzip
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Any


__all__ = [
    "analyze_bundle",
    "BundleAnalysis",
    "FileAnalysis",
    "print_report",
    "generate_report_json",
]


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class FileAnalysis:
    """
    Analysis of a single file in the bundle.
    
    Attributes:
        name: File name
        path: Full path
        size: Size in bytes
        gzip_size: Gzipped size in bytes
        features: Reactive features used
        imports: Other files imported
        exports: Exported identifiers
    """
    name: str
    path: str
    size: int
    gzip_size: int = 0
    features: Set[str] = field(default_factory=set)
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    
    @property
    def size_kb(self) -> float:
        """Size in KB."""
        return self.size / 1024
    
    @property
    def gzip_kb(self) -> float:
        """Gzipped size in KB."""
        return self.gzip_size / 1024


@dataclass
class BundleAnalysis:
    """
    Complete bundle analysis.
    
    Attributes:
        files: Individual file analyses
        total_size: Total bundle size in bytes
        total_gzip: Total gzipped size
        runtime_size: Size of runtime
        islands_size: Size of islands
        features_used: All features used across bundle
        features_unused: Available features not used
    """
    files: List[FileAnalysis] = field(default_factory=list)
    total_size: int = 0
    total_gzip: int = 0
    runtime_size: int = 0
    islands_size: int = 0
    features_used: Set[str] = field(default_factory=set)
    features_unused: Set[str] = field(default_factory=set)
    recommendations: List[str] = field(default_factory=list)
    
    @property
    def total_kb(self) -> float:
        """Total size in KB."""
        return self.total_size / 1024
    
    @property
    def gzip_kb(self) -> float:
        """Total gzipped size in KB."""
        return self.total_gzip / 1024
    
    @property
    def file_count(self) -> int:
        """Number of files in bundle."""
        return len(self.files)
    
    def get_largest_files(self, n: int = 5) -> List[FileAnalysis]:
        """Get the n largest files."""
        return sorted(self.files, key=lambda f: f.size, reverse=True)[:n]


# =============================================================================
# MAIN API
# =============================================================================

def analyze_bundle(build_dir: str | Path) -> BundleAnalysis:
    """
    Analyze a compiled bundle directory.
    
    Args:
        build_dir: Path to the build output directory
    
    Returns:
        BundleAnalysis with detailed breakdown
    
    Example:
        analysis = analyze_bundle(".pynext/build/")
        print(f"Total: {analysis.total_kb:.1f} KB")
    """
    build_path = Path(build_dir)
    
    if not build_path.exists():
        raise FileNotFoundError(f"Build directory not found: {build_path}")
    
    analysis = BundleAnalysis()
    all_features = {
        "signals", "effects", "memos", "stores", "batch",
        "show", "for", "switch", "portal", "dynamic",
        "error_boundary", "suspense", "forms",
    }
    
    # Analyze each JS file
    for js_file in build_path.glob("*.js"):
        file_analysis = _analyze_file(js_file)
        analysis.files.append(file_analysis)
        
        analysis.total_size += file_analysis.size
        analysis.total_gzip += file_analysis.gzip_size
        analysis.features_used.update(file_analysis.features)
        
        if file_analysis.name.startswith("reactive"):
            analysis.runtime_size += file_analysis.size
        else:
            analysis.islands_size += file_analysis.size
    
    # Calculate unused features
    analysis.features_unused = all_features - analysis.features_used
    
    # Generate recommendations
    analysis.recommendations = _generate_recommendations(analysis)
    
    return analysis


def _analyze_file(file_path: Path) -> FileAnalysis:
    """Analyze a single JavaScript file."""
    content = file_path.read_text(encoding="utf-8")
    size = len(content)
    
    # Calculate gzipped size
    gzip_size = len(gzip.compress(content.encode()))
    
    # Detect features
    features = _detect_features(content)
    
    # Find imports
    imports = _find_imports(content)
    
    # Find exports
    exports = _find_exports(content)
    
    return FileAnalysis(
        name=file_path.name,
        path=str(file_path),
        size=size,
        gzip_size=gzip_size,
        features=features,
        imports=imports,
        exports=exports,
    )


def _detect_features(code: str) -> Set[str]:
    """Detect which features are used in the code."""
    import re
    
    features = set()
    
    patterns = {
        "signals": r"\bcreateSignal\b",
        "effects": r"\bcreateEffect\b",
        "memos": r"\bcreateMemo\b",
        "stores": r"\bcreateStore\b",
        "batch": r"\bbatch\b",
        "show": r"\bShow\b",
        "for": r"\bFor\b|\bIndex\b",
        "switch": r"\bSwitch\b|\bMatch\b",
        "portal": r"\bPortal\b",
        "dynamic": r"\bDynamic\b",
        "error_boundary": r"\bErrorBoundary\b",
        "suspense": r"\bSuspense\b",
        "forms": r"\bcreateForm\b",
    }
    
    for feature, pattern in patterns.items():
        if re.search(pattern, code):
            features.add(feature)
    
    return features


def _find_imports(code: str) -> List[str]:
    """Find import statements."""
    import re
    
    imports = []
    
    # ES6 imports
    for match in re.finditer(r"import\s+.*?\s+from\s+['\"](.+?)['\"]", code):
        imports.append(match.group(1))
    
    # require() calls
    for match in re.finditer(r"require\(['\"](.+?)['\"]\)", code):
        imports.append(match.group(1))
    
    return imports


def _find_exports(code: str) -> List[str]:
    """Find exported identifiers."""
    import re
    
    exports = []
    
    # export { a, b, c }
    match = re.search(r"export\s*\{([^}]+)\}", code)
    if match:
        items = match.group(1).split(",")
        for item in items:
            item = item.strip()
            if " as " in item:
                item = item.split(" as ")[1].strip()
            exports.append(item)
    
    # export function foo / export const foo
    for match in re.finditer(r"export\s+(?:function|const|let|var)\s+(\w+)", code):
        exports.append(match.group(1))
    
    # export default
    if re.search(r"export\s+default", code):
        exports.append("default")
    
    return exports


def _generate_recommendations(analysis: BundleAnalysis) -> List[str]:
    """Generate optimization recommendations."""
    recs = []
    
    # Large file warning
    for file in analysis.files:
        percent = (file.size / analysis.total_size) * 100 if analysis.total_size > 0 else 0
        if percent > 50:
            recs.append(
                f"{file.name} is {percent:.0f}% of bundle - consider code splitting"
            )
    
    # Unused features
    if analysis.features_unused:
        estimated_savings = len(analysis.features_unused) * 0.2  # ~0.2KB per feature
        unused_list = ", ".join(sorted(analysis.features_unused))
        recs.append(
            f"Tree shaking could save ~{estimated_savings:.1f} KB (remove unused: {unused_list})"
        )
    
    # Large runtime
    if analysis.runtime_size > 5000:
        recs.append(
            f"Runtime is {analysis.runtime_size / 1024:.1f} KB - ensure tree shaking is enabled"
        )
    
    # Gzip recommendation
    if analysis.total_size > 10000:
        savings = analysis.total_size - analysis.total_gzip
        recs.append(
            f"Enable gzip compression to save {savings / 1024:.1f} KB"
        )
    
    return recs


# =============================================================================
# REPORTING
# =============================================================================

def print_report(analysis: BundleAnalysis) -> None:
    """
    Print a formatted bundle analysis report.
    
    Args:
        analysis: Bundle analysis to print
    
    Example:
        analysis = analyze_bundle(".pynext/build/")
        print_report(analysis)
    """
    print()
    print("PyNext Bundle Analysis")
    print("═" * 60)
    print()
    
    # Total size
    print(f"Total Size: {analysis.total_kb:.1f} KB ({analysis.gzip_kb:.1f} KB gzipped)")
    print()
    
    # Breakdown
    print("Breakdown:")
    
    sorted_files = sorted(analysis.files, key=lambda f: f.size, reverse=True)
    
    for i, file in enumerate(sorted_files):
        percent = (file.size / analysis.total_size) * 100 if analysis.total_size > 0 else 0
        bar_len = int(percent / 5)
        bar = "█" * bar_len
        
        prefix = "└──" if i == len(sorted_files) - 1 else "├──"
        
        print(f"{prefix} {file.name:<30} {file.size_kb:>5.1f} KB ({percent:>5.1f}%)  {bar}")
    
    print()
    
    # Features
    print("Features Used:")
    all_features = analysis.features_used | analysis.features_unused
    
    for feature in sorted(all_features):
        if feature in analysis.features_used:
            print(f"  ✓ {feature}")
        else:
            print(f"  ✗ {feature} (unused)")
    
    print()
    
    # Recommendations
    if analysis.recommendations:
        print("Recommendations:")
        for rec in analysis.recommendations:
            print(f"  • {rec}")
        print()


def generate_report_json(analysis: BundleAnalysis) -> str:
    """
    Generate JSON report.
    
    Args:
        analysis: Bundle analysis
    
    Returns:
        JSON string
    
    Example:
        json_report = generate_report_json(analysis)
        Path("report.json").write_text(json_report)
    """
    data = {
        "totalSize": analysis.total_size,
        "totalGzip": analysis.total_gzip,
        "runtimeSize": analysis.runtime_size,
        "islandsSize": analysis.islands_size,
        "files": [
            {
                "name": f.name,
                "size": f.size,
                "gzipSize": f.gzip_size,
                "features": list(f.features),
            }
            for f in analysis.files
        ],
        "featuresUsed": list(analysis.features_used),
        "featuresUnused": list(analysis.features_unused),
        "recommendations": analysis.recommendations,
    }
    
    return json.dumps(data, indent=2)


def generate_report_html(analysis: BundleAnalysis) -> str:
    """
    Generate HTML report with visualization.
    
    Args:
        analysis: Bundle analysis
    
    Returns:
        HTML string
    
    Example:
        html_report = generate_report_html(analysis)
        Path("report.html").write_text(html_report)
    """
    # Build file table rows
    rows = ""
    for file in sorted(analysis.files, key=lambda f: f.size, reverse=True):
        percent = (file.size / analysis.total_size) * 100 if analysis.total_size > 0 else 0
        rows += f"""
        <tr>
            <td>{file.name}</td>
            <td>{file.size_kb:.1f} KB</td>
            <td>{file.gzip_kb:.1f} KB</td>
            <td>
                <div class="bar" style="width: {percent}%"></div>
                <span>{percent:.1f}%</span>
            </td>
        </tr>
        """
    
    return f"""<!DOCTYPE html>
<html>
<head>
    <title>PyNext Bundle Analysis</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 900px;
            margin: 40px auto;
            padding: 20px;
            background: #0d1117;
            color: #c9d1d9;
        }}
        h1 {{ color: #58a6ff; }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin: 30px 0;
        }}
        .card {{
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 20px;
        }}
        .card h3 {{ margin: 0 0 10px 0; color: #8b949e; font-size: 14px; }}
        .card .value {{ font-size: 28px; font-weight: 600; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            text-align: left;
            padding: 12px;
            border-bottom: 1px solid #30363d;
        }}
        th {{ color: #8b949e; font-weight: 500; }}
        .bar {{
            background: #238636;
            height: 20px;
            border-radius: 4px;
            display: inline-block;
        }}
        .recommendations {{
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }}
        .recommendations li {{ margin: 10px 0; }}
    </style>
</head>
<body>
    <h1>PyNext Bundle Analysis</h1>
    
    <div class="summary">
        <div class="card">
            <h3>Total Size</h3>
            <div class="value">{analysis.total_kb:.1f} KB</div>
        </div>
        <div class="card">
            <h3>Gzipped</h3>
            <div class="value">{analysis.gzip_kb:.1f} KB</div>
        </div>
        <div class="card">
            <h3>Files</h3>
            <div class="value">{analysis.file_count}</div>
        </div>
    </div>
    
    <h2>File Breakdown</h2>
    <table>
        <tr>
            <th>File</th>
            <th>Size</th>
            <th>Gzipped</th>
            <th>% of Bundle</th>
        </tr>
        {rows}
    </table>
    
    <div class="recommendations">
        <h2>Recommendations</h2>
        <ul>
            {"".join(f"<li>{r}</li>" for r in analysis.recommendations) or "<li>No recommendations - bundle looks good!</li>"}
        </ul>
    </div>
</body>
</html>"""

