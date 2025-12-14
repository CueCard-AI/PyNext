"""
Tests for PyNext Bundle Analysis (40 tests)

Tests bundle composition analysis and reporting.
"""

import pytest
import json
from pathlib import Path

from pynext.build.analyze import (
    analyze_bundle,
    BundleAnalysis,
    FileAnalysis,
    print_report,
    generate_report_json,
    generate_report_html,
)


# =============================================================================
# FILE ANALYSIS
# =============================================================================

class TestFileAnalysis:
    """Tests for individual file analysis."""
    
    def test_file_analysis_creation(self):
        """Create FileAnalysis."""
        analysis = FileAnalysis(
            name="counter.js",
            path="/build/counter.js",
            size=1024,
            gzip_size=512,
        )
        assert analysis.name == "counter.js"
        assert analysis.size == 1024
    
    def test_size_kb(self):
        """Size in KB."""
        analysis = FileAnalysis(name="x", path="/x", size=2048)
        assert analysis.size_kb == 2.0
    
    def test_gzip_kb(self):
        """Gzip size in KB."""
        analysis = FileAnalysis(name="x", path="/x", size=2048, gzip_size=1024)
        assert analysis.gzip_kb == 1.0
    
    def test_features_detected(self):
        """Features are tracked."""
        analysis = FileAnalysis(
            name="x.js",
            path="/x.js",
            size=100,
            features={"signals", "effects"},
        )
        assert "signals" in analysis.features


# =============================================================================
# BUNDLE ANALYSIS
# =============================================================================

class TestBundleAnalysis:
    """Tests for bundle analysis."""
    
    def test_analyze_empty_dir(self, tmp_path):
        """Analyze empty directory."""
        (tmp_path / "build").mkdir()
        analysis = analyze_bundle(tmp_path / "build")
        assert analysis.file_count == 0
    
    def test_analyze_single_file(self, tmp_path):
        """Analyze single JS file."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "counter.js").write_text("export function Counter() {}")
        
        analysis = analyze_bundle(build_dir)
        assert analysis.file_count == 1
    
    def test_analyze_multiple_files(self, tmp_path):
        """Analyze multiple files."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "a.js").write_text("export function A() {}")
        (build_dir / "b.js").write_text("export function B() {}")
        (build_dir / "c.js").write_text("export function C() {}")
        
        analysis = analyze_bundle(build_dir)
        assert analysis.file_count == 3
    
    def test_total_size(self, tmp_path):
        """Calculate total size."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "a.js").write_text("x" * 100)
        (build_dir / "b.js").write_text("x" * 200)
        
        analysis = analyze_bundle(build_dir)
        assert analysis.total_size == 300
    
    def test_gzip_size(self, tmp_path):
        """Calculate gzip size."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "a.js").write_text("x" * 1000)
        
        analysis = analyze_bundle(build_dir)
        # Gzip should be smaller
        assert analysis.total_gzip < analysis.total_size
    
    def test_runtime_size(self, tmp_path):
        """Identify runtime size."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "reactive.min.js").write_text("x" * 2000)
        (build_dir / "counter.js").write_text("x" * 500)
        
        analysis = analyze_bundle(build_dir)
        assert analysis.runtime_size == 2000
        assert analysis.islands_size == 500
    
    def test_features_detected(self, tmp_path):
        """Detect features in bundle."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "counter.js").write_text("""
            const count = createSignal(0);
            createEffect(() => console.log(count()));
        """)
        
        analysis = analyze_bundle(build_dir)
        assert "signals" in analysis.features_used
        assert "effects" in analysis.features_used
    
    def test_unused_features(self, tmp_path):
        """Identify unused features."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "counter.js").write_text("createSignal(0);")
        
        analysis = analyze_bundle(build_dir)
        assert "stores" in analysis.features_unused or "forms" in analysis.features_unused
    
    def test_largest_files(self, tmp_path):
        """Get largest files."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "small.js").write_text("x" * 100)
        (build_dir / "medium.js").write_text("x" * 500)
        (build_dir / "large.js").write_text("x" * 1000)
        
        analysis = analyze_bundle(build_dir)
        largest = analysis.get_largest_files(2)
        assert largest[0].name == "large.js"
        assert largest[1].name == "medium.js"
    
    def test_recommendations_large_file(self, tmp_path):
        """Recommend code splitting for large files."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "huge.js").write_text("x" * 10000)
        (build_dir / "tiny.js").write_text("x" * 100)
        
        analysis = analyze_bundle(build_dir)
        assert any("huge.js" in r for r in analysis.recommendations)


# =============================================================================
# REPORTING
# =============================================================================

class TestReporting:
    """Tests for report generation."""
    
    def test_generate_json_report(self, tmp_path):
        """Generate JSON report."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "counter.js").write_text("createSignal(0);")
        
        analysis = analyze_bundle(build_dir)
        report = generate_report_json(analysis)
        
        data = json.loads(report)
        assert "totalSize" in data
        assert "files" in data
    
    def test_generate_html_report(self, tmp_path):
        """Generate HTML report."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "counter.js").write_text("createSignal(0);")
        
        analysis = analyze_bundle(build_dir)
        html = generate_report_html(analysis)
        
        assert "<!DOCTYPE html>" in html
        assert "PyNext Bundle Analysis" in html
    
    def test_print_report(self, tmp_path, capsys):
        """Print formatted report."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "counter.js").write_text("x" * 100)
        
        analysis = analyze_bundle(build_dir)
        print_report(analysis)
        
        captured = capsys.readouterr()
        assert "PyNext Bundle Analysis" in captured.out


# =============================================================================
# EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Edge case handling."""
    
    def test_missing_directory(self, tmp_path):
        """Handle missing directory."""
        with pytest.raises(FileNotFoundError):
            analyze_bundle(tmp_path / "nonexistent")
    
    def test_non_js_files_ignored(self, tmp_path):
        """Ignore non-JS files."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "data.json").write_text("{}")
        (build_dir / "style.css").write_text("body {}")
        (build_dir / "code.js").write_text("const x = 1;")
        
        analysis = analyze_bundle(build_dir)
        assert analysis.file_count == 1
    
    def test_empty_js_file(self, tmp_path):
        """Handle empty JS files."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "empty.js").write_text("")
        
        analysis = analyze_bundle(build_dir)
        assert analysis.file_count == 1
        assert analysis.files[0].size == 0
    
    def test_unicode_content(self, tmp_path):
        """Handle Unicode in JS files."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "i18n.js").write_text('const msg = "Привет! 你好!";')
        
        analysis = analyze_bundle(build_dir)
        assert analysis.file_count == 1


# =============================================================================
# PROPERTIES
# =============================================================================

class TestProperties:
    """Tests for computed properties."""
    
    def test_total_kb(self):
        """Total size in KB."""
        analysis = BundleAnalysis(total_size=2048)
        assert analysis.total_kb == 2.0
    
    def test_gzip_kb(self):
        """Gzip size in KB."""
        analysis = BundleAnalysis(total_gzip=1024)
        assert analysis.gzip_kb == 1.0
    
    def test_file_count(self):
        """File count from list."""
        analysis = BundleAnalysis(files=[
            FileAnalysis("a.js", "/a.js", 100),
            FileAnalysis("b.js", "/b.js", 200),
        ])
        assert analysis.file_count == 2

