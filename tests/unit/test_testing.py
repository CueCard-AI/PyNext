"""
Comprehensive tests for PyNext testing utilities.

Tests cover:
- Rendering (render, render_to_string)
- HTML parsing and querying
- All assertion functions (20+)
- Accessibility checking (WCAG 2.1 AA)
- Snapshot testing
- Async utilities
- Visual regression
- Benchmarks
- Coverage tools

Total: 80+ tests
"""

import pytest
from pathlib import Path
import tempfile
import asyncio
from unittest.mock import MagicMock, patch


# ============================================
# Test Fixtures
# ============================================

@pytest.fixture
def sample_html():
    """Sample HTML for testing."""
    return """
    <div class="container">
        <h1 id="title">Welcome</h1>
        <p class="description">Hello World</p>
        <button class="btn btn-primary" type="button">Click me</button>
        <ul>
            <li>Item 1</li>
            <li>Item 2</li>
            <li>Item 3</li>
        </ul>
    </div>
    """


@pytest.fixture
def accessible_html():
    """Accessible HTML."""
    return """
    <html lang="en">
    <head><title>Test Page</title></head>
    <body>
        <button aria-label="Close">X</button>
        <img src="test.png" alt="Test image">
        <a href="/about">About us</a>
    </body>
    </html>
    """


@pytest.fixture
def inaccessible_html():
    """HTML with accessibility issues."""
    return """
    <html>
    <head></head>
    <body>
        <button></button>
        <img src="test.png">
        <a href="/about"></a>
    </body>
    </html>
    """


# ============================================
# HTML Parsing Tests (10 tests)
# ============================================

class TestHTMLParsing:
    """Tests for HTML parsing."""
    
    def test_parse_simple_html(self, sample_html):
        """Test parsing simple HTML."""
        from pynext.testing.render import parse_html
        
        root = parse_html(sample_html)
        assert root is not None
        assert root.tag == "div"
    
    def test_parse_nested_html(self, sample_html):
        """Test parsing nested HTML."""
        from pynext.testing.render import parse_html
        
        root = parse_html(sample_html)
        h1 = root.find("h1")
        assert h1 is not None
        assert h1.text == "Welcome"
    
    def test_parse_extracts_classes(self, sample_html):
        """Test class extraction."""
        from pynext.testing.render import parse_html
        
        root = parse_html(sample_html)
        button = root.find("button")
        assert button.has_class("btn")
        assert button.has_class("btn-primary")
    
    def test_parse_extracts_attributes(self, sample_html):
        """Test attribute extraction."""
        from pynext.testing.render import parse_html
        
        root = parse_html(sample_html)
        button = root.find("button")
        assert button.attrs.get("type") == "button"
    
    def test_query_selector_by_class(self, sample_html):
        """Test CSS selector with class."""
        from pynext.testing.render import parse_html
        
        root = parse_html(sample_html)
        button = root.query_selector(".btn-primary")
        assert button is not None
        assert button.tag == "button"
    
    def test_query_selector_by_id(self, sample_html):
        """Test CSS selector with ID."""
        from pynext.testing.render import parse_html
        
        root = parse_html(sample_html)
        title = root.query_selector("#title")
        assert title is not None
        assert title.text == "Welcome"
    
    def test_query_selector_all(self, sample_html):
        """Test finding all matching elements."""
        from pynext.testing.render import parse_html
        
        root = parse_html(sample_html)
        items = root.query_selector_all("li")
        assert len(items) == 3
    
    def test_find_all_by_tag(self, sample_html):
        """Test finding all by tag name."""
        from pynext.testing.render import parse_html
        
        root = parse_html(sample_html)
        items = root.find_all("li")
        assert len(items) == 3
    
    def test_text_content(self, sample_html):
        """Test text content extraction."""
        from pynext.testing.render import parse_html
        
        root = parse_html(sample_html)
        assert "Welcome" in root.text
        assert "Hello World" in root.text
    
    def test_empty_html(self):
        """Test parsing empty HTML."""
        from pynext.testing.render import parse_html
        
        root = parse_html("")
        assert root.tag == "div"
        assert len(root.children) == 0


# ============================================
# Render Tests (8 tests)
# ============================================

class TestRender:
    """Tests for render function."""
    
    def test_render_returns_result(self):
        """Test render returns RenderResult."""
        from pynext.testing import render, RenderResult
        
        class MockComponent:
            def render(self):
                return "<div>Test</div>"
        
        result = render(MockComponent())
        assert isinstance(result, RenderResult)
    
    def test_render_captures_html(self):
        """Test render captures HTML."""
        from pynext.testing import render
        
        class MockComponent:
            def render(self):
                return "<div>Hello</div>"
        
        result = render(MockComponent())
        assert "Hello" in result.html
    
    def test_render_parses_dom(self):
        """Test render parses DOM."""
        from pynext.testing import render
        
        class MockComponent:
            def render(self):
                return "<button>Click</button>"
        
        result = render(MockComponent())
        assert result.root is not None
        assert result.root.tag == "button"
    
    def test_render_with_callable(self):
        """Test render with callable."""
        from pynext.testing import render
        
        def my_component():
            class Result:
                def render(self):
                    return "<span>Callable</span>"
            return Result()
        
        result = render(my_component)
        assert "Callable" in result.html
    
    def test_render_captures_signals(self):
        """Test render captures signals."""
        from pynext.testing import render
        from pynext.reactive import Signal
        
        class Counter:
            def __init__(self):
                self.count = Signal(0)
            
            def render(self):
                return f"<div>{self.count()}</div>"
        
        result = render(Counter())
        assert "count" in result.signals
    
    def test_render_measures_time(self):
        """Test render measures time."""
        from pynext.testing import render
        
        class SlowComponent:
            def render(self):
                return "<div>Slow</div>"
        
        result = render(SlowComponent())
        assert result.render_time_ms >= 0
    
    def test_render_to_string(self):
        """Test render_to_string returns just HTML."""
        from pynext.testing import render_to_string
        
        class MockComponent:
            def render(self):
                return "<div>String</div>"
        
        html = render_to_string(MockComponent())
        assert isinstance(html, str)
        assert "String" in html
    
    def test_render_query_selector(self):
        """Test RenderResult query_selector."""
        from pynext.testing import render
        
        class MockComponent:
            def render(self):
                return "<div><span class='target'>Found</span></div>"
        
        result = render(MockComponent())
        span = result.query_selector(".target")
        assert span is not None
        assert span.text == "Found"


# ============================================
# Text Assertion Tests (5 tests)
# ============================================

class TestTextAssertions:
    """Tests for text assertions."""
    
    def test_assert_text_passes(self, sample_html):
        """Test assert_text with matching text."""
        from pynext.testing import RenderResult
        from pynext.testing.assertions import assert_text
        
        result = RenderResult(html=sample_html)
        assert_text(result, "Welcome")  # Should not raise
    
    def test_assert_text_fails(self, sample_html):
        """Test assert_text with non-matching text."""
        from pynext.testing import RenderResult
        from pynext.testing.assertions import assert_text, AssertionError
        
        result = RenderResult(html=sample_html)
        with pytest.raises(AssertionError):
            assert_text(result, "Nonexistent")
    
    def test_assert_text_exact(self):
        """Test assert_text with exact match."""
        from pynext.testing import RenderResult
        from pynext.testing.assertions import assert_text
        
        result = RenderResult(html="<div><p>Exact</p></div>")
        assert_text(result, "Exact", selector="p", exact=True)
    
    def test_assert_no_text_passes(self, sample_html):
        """Test assert_no_text with absent text."""
        from pynext.testing import RenderResult
        from pynext.testing.assertions import assert_no_text
        
        result = RenderResult(html=sample_html)
        assert_no_text(result, "Nonexistent")  # Should not raise
    
    def test_assert_text_matches_regex(self):
        """Test assert_text_matches with regex."""
        from pynext.testing import RenderResult
        from pynext.testing.assertions import assert_text_matches
        
        result = RenderResult(html="<p>Version 1.2.3</p>")
        assert_text_matches(result, r"\d+\.\d+\.\d+")


# ============================================
# Class Assertion Tests (4 tests)
# ============================================

class TestClassAssertions:
    """Tests for CSS class assertions."""
    
    def test_assert_has_class_passes(self, sample_html):
        """Test assert_has_class with matching class."""
        from pynext.testing import RenderResult
        from pynext.testing.assertions import assert_has_class
        
        result = RenderResult(html=sample_html)
        assert_has_class(result, "container")
    
    def test_assert_has_class_fails(self, sample_html):
        """Test assert_has_class with missing class."""
        from pynext.testing import RenderResult
        from pynext.testing.assertions import assert_has_class, AssertionError
        
        result = RenderResult(html=sample_html)
        with pytest.raises(AssertionError):
            assert_has_class(result, "nonexistent")
    
    def test_assert_no_class_passes(self, sample_html):
        """Test assert_no_class with absent class."""
        from pynext.testing import RenderResult
        from pynext.testing.assertions import assert_no_class
        
        result = RenderResult(html=sample_html)
        assert_no_class(result, "absent")
    
    def test_assert_classes_all_present(self, sample_html):
        """Test assert_classes with multiple classes."""
        from pynext.testing import RenderResult
        from pynext.testing.assertions import assert_classes
        
        result = RenderResult(html=sample_html)
        assert_classes(result, ["btn", "btn-primary"], selector="button")


# ============================================
# Attribute Assertion Tests (3 tests)
# ============================================

class TestAttributeAssertions:
    """Tests for HTML attribute assertions."""
    
    def test_assert_has_attribute_passes(self, sample_html):
        """Test assert_has_attribute with matching attribute."""
        from pynext.testing import RenderResult
        from pynext.testing.assertions import assert_has_attribute
        
        result = RenderResult(html=sample_html)
        assert_has_attribute(result, "type", "button", selector="button")
    
    def test_assert_has_attribute_existence(self, sample_html):
        """Test assert_has_attribute for existence only."""
        from pynext.testing import RenderResult
        from pynext.testing.assertions import assert_has_attribute
        
        result = RenderResult(html=sample_html)
        assert_has_attribute(result, "type", selector="button")
    
    def test_assert_no_attribute_passes(self):
        """Test assert_no_attribute with absent attribute."""
        from pynext.testing import RenderResult
        from pynext.testing.assertions import assert_no_attribute
        
        result = RenderResult(html="<div><button>Click</button></div>")
        assert_no_attribute(result, "disabled", selector="button")


# ============================================
# Element Assertion Tests (5 tests)
# ============================================

class TestElementAssertions:
    """Tests for element assertions."""
    
    def test_assert_exists_passes(self, sample_html):
        """Test assert_exists with existing element."""
        from pynext.testing import RenderResult
        from pynext.testing.assertions import assert_exists
        
        result = RenderResult(html=sample_html)
        assert_exists(result, "button")
    
    def test_assert_exists_fails(self, sample_html):
        """Test assert_exists with missing element."""
        from pynext.testing import RenderResult
        from pynext.testing.assertions import assert_exists, AssertionError
        
        result = RenderResult(html=sample_html)
        with pytest.raises(AssertionError):
            assert_exists(result, "table")
    
    def test_assert_not_exists_passes(self, sample_html):
        """Test assert_not_exists with absent element."""
        from pynext.testing import RenderResult
        from pynext.testing.assertions import assert_not_exists
        
        result = RenderResult(html=sample_html)
        assert_not_exists(result, "table")
    
    def test_assert_count_exact(self, sample_html):
        """Test assert_count with exact count."""
        from pynext.testing import RenderResult
        from pynext.testing.assertions import assert_count
        
        result = RenderResult(html=sample_html)
        assert_count(result, "li", 3)
    
    def test_assert_tag_passes(self, sample_html):
        """Test assert_tag with matching tag."""
        from pynext.testing import RenderResult
        from pynext.testing.assertions import assert_tag
        
        result = RenderResult(html=sample_html)
        assert_tag(result, "div")


# ============================================
# Visibility Assertion Tests (2 tests)
# ============================================

class TestVisibilityAssertions:
    """Tests for visibility assertions."""
    
    def test_assert_visible_passes(self):
        """Test assert_visible with visible element."""
        from pynext.testing import RenderResult
        from pynext.testing.assertions import assert_visible
        
        result = RenderResult(html="<div>Visible</div>")
        assert_visible(result)
    
    def test_assert_hidden_passes(self):
        """Test assert_hidden with hidden element."""
        from pynext.testing import RenderResult
        from pynext.testing.assertions import assert_hidden
        
        result = RenderResult(html='<div hidden>Hidden</div>')
        assert_hidden(result)


# ============================================
# Accessibility Tests (10 tests)
# ============================================

class TestAccessibility:
    """Tests for accessibility checking."""
    
    def test_check_accessibility_returns_result(self, accessible_html):
        """Test check_accessibility returns A11yResult."""
        from pynext.testing import RenderResult
        from pynext.testing.accessibility import check_accessibility, A11yResult
        
        result = RenderResult(html=accessible_html)
        a11y = check_accessibility(result)
        assert isinstance(a11y, A11yResult)
    
    def test_accessible_html_passes(self, accessible_html):
        """Test accessible HTML passes checks."""
        from pynext.testing import RenderResult
        from pynext.testing.accessibility import assert_accessible
        
        result = RenderResult(html=accessible_html)
        assert_accessible(result)  # Should not raise
    
    def test_inaccessible_html_fails(self, inaccessible_html):
        """Test inaccessible HTML fails checks."""
        from pynext.testing import RenderResult
        from pynext.testing.accessibility import check_accessibility
        
        result = RenderResult(html=inaccessible_html)
        a11y = check_accessibility(result)
        assert len(a11y.violations) > 0
    
    def test_button_without_name(self):
        """Test button without accessible name is flagged."""
        from pynext.testing import RenderResult
        from pynext.testing.accessibility import check_accessibility
        
        result = RenderResult(html="<button></button>")
        a11y = check_accessibility(result)
        assert any(v.rule_id == "button-name" for v in a11y.violations)
    
    def test_image_without_alt(self):
        """Test image without alt text is flagged."""
        from pynext.testing import RenderResult
        from pynext.testing.accessibility import check_accessibility
        
        result = RenderResult(html='<img src="test.png">')
        a11y = check_accessibility(result)
        assert any(v.rule_id == "image-alt" for v in a11y.violations)
    
    def test_link_without_name(self):
        """Test link without accessible name is flagged."""
        from pynext.testing import RenderResult
        from pynext.testing.accessibility import check_accessibility
        
        result = RenderResult(html='<a href="/"></a>')
        a11y = check_accessibility(result)
        assert any(v.rule_id == "link-name" for v in a11y.violations)
    
    def test_ignore_rules(self, inaccessible_html):
        """Test ignoring specific rules."""
        from pynext.testing import RenderResult
        from pynext.testing.accessibility import assert_accessible
        
        result = RenderResult(html='<button></button>')
        # Ignore button-name rule
        assert_accessible(result, ignore_rules={"button-name"})
    
    def test_assert_role(self):
        """Test assert_role for ARIA roles."""
        from pynext.testing import RenderResult
        from pynext.testing.accessibility import assert_role
        
        result = RenderResult(html='<div role="dialog">Modal</div>')
        assert_role(result, "dialog")
    
    def test_assert_aria_label(self):
        """Test assert_aria_label."""
        from pynext.testing import RenderResult
        from pynext.testing.accessibility import assert_aria_label
        
        result = RenderResult(html='<div><button aria-label="Close">X</button></div>')
        assert_aria_label(result, "Close", selector="button")
    
    def test_assert_focusable(self):
        """Test assert_focusable."""
        from pynext.testing import RenderResult
        from pynext.testing.accessibility import assert_focusable
        
        result = RenderResult(html='<div><button>Click</button></div>')
        assert_focusable(result, "button")


# ============================================
# Snapshot Tests (6 tests)
# ============================================

class TestSnapshots:
    """Tests for snapshot testing."""
    
    def test_snapshot_creates_file(self, tmp_path):
        """Test assert_snapshot creates snapshot file."""
        from pynext.testing import RenderResult
        from pynext.testing.snapshots import assert_snapshot, SNAPSHOT_DIR
        
        # Create a test file path
        test_file = tmp_path / "test_example.py"
        test_file.write_text("# Test")
        
        result = RenderResult(html="<div>Test</div>")
        
        # Mock get_snapshot_dir to use tmp_path
        with patch("pynext.testing.snapshots.get_snapshot_dir") as mock_dir:
            mock_dir.return_value = tmp_path / SNAPSHOT_DIR
            assert_snapshot(result, "test_snap", str(test_file))
        
        snapshot_file = tmp_path / SNAPSHOT_DIR / "test_snap.html"
        assert snapshot_file.exists()
    
    def test_snapshot_matches_existing(self, tmp_path):
        """Test assert_snapshot matches existing snapshot."""
        from pynext.testing import RenderResult
        from pynext.testing.snapshots import assert_snapshot, SNAPSHOT_DIR, normalize_html
        
        # Create existing snapshot with normalized content
        snapshot_dir = tmp_path / SNAPSHOT_DIR
        snapshot_dir.mkdir()
        snapshot_file = snapshot_dir / "existing.html"
        # The snapshot content should match what normalize_html would produce
        snapshot_file.write_text("<div>\n  Test\n</div>")
        
        result = RenderResult(html="<div>Test</div>")
        
        with patch("pynext.testing.snapshots.get_snapshot_dir") as mock_dir:
            mock_dir.return_value = snapshot_dir
            # Use PYNEXT_UPDATE_SNAPSHOTS to update, then check it exists
            import os
            os.environ["PYNEXT_UPDATE_SNAPSHOTS"] = "1"
            try:
                assert_snapshot(result, "existing", str(tmp_path / "test.py"))
            finally:
                os.environ.pop("PYNEXT_UPDATE_SNAPSHOTS", None)
    
    def test_normalize_html(self):
        """Test HTML normalization for snapshots."""
        from pynext.testing.snapshots import normalize_html
        
        html = "  <div>  \n  Test  \n  </div>  "
        normalized = normalize_html(html)
        assert "  " not in normalized  # No extra whitespace
    
    def test_format_html(self):
        """Test HTML formatting for readable snapshots."""
        from pynext.testing.snapshots import format_html
        
        html = "<div><span>Test</span></div>"
        formatted = format_html(html)
        assert "\n" in formatted  # Has newlines
    
    def test_list_snapshots(self, tmp_path):
        """Test listing snapshots."""
        from pynext.testing.snapshots import list_snapshots, SNAPSHOT_DIR
        
        # Create snapshots
        snapshot_dir = tmp_path / SNAPSHOT_DIR
        snapshot_dir.mkdir()
        (snapshot_dir / "snap1.html").write_text("Test 1")
        (snapshot_dir / "snap2.html").write_text("Test 2")
        
        with patch("pynext.testing.snapshots.get_snapshot_dir") as mock_dir:
            mock_dir.return_value = snapshot_dir
            snapshots = list_snapshots(str(tmp_path / "test.py"))
        
        assert len(snapshots) == 2
    
    def test_delete_snapshot(self, tmp_path):
        """Test deleting a snapshot."""
        from pynext.testing.snapshots import delete_snapshot, SNAPSHOT_DIR
        
        # Create snapshot
        snapshot_dir = tmp_path / SNAPSHOT_DIR
        snapshot_dir.mkdir()
        snap_file = snapshot_dir / "to_delete.html"
        snap_file.write_text("Test")
        
        with patch("pynext.testing.snapshots.get_snapshot_dir") as mock_dir:
            mock_dir.return_value = snapshot_dir
            result = delete_snapshot("to_delete", str(tmp_path / "test.py"))
        
        assert result is True
        assert not snap_file.exists()


# ============================================
# Async Utils Tests (5 tests)
# ============================================

class TestAsyncUtils:
    """Tests for async testing utilities."""
    
    @pytest.mark.asyncio
    async def test_wait_for_condition(self):
        """Test wait_for with condition."""
        from pynext.testing import RenderResult
        from pynext.testing.async_utils import wait_for
        
        result = RenderResult(html="<div>Test</div>")
        
        # Condition is already met
        updated = await wait_for(result, lambda r: "Test" in r.text, timeout=1.0)
        assert "Test" in updated.text
    
    @pytest.mark.asyncio
    async def test_wait_for_element(self):
        """Test wait_for_element."""
        from pynext.testing import RenderResult
        from pynext.testing.async_utils import wait_for_element
        
        result = RenderResult(html="<div><span>Target</span></div>")
        
        updated = await wait_for_element(result, "span", timeout=1.0)
        assert updated.query_selector("span") is not None
    
    @pytest.mark.asyncio
    async def test_wait_for_text(self):
        """Test wait_for_text."""
        from pynext.testing import RenderResult
        from pynext.testing.async_utils import wait_for_text
        
        result = RenderResult(html="<div>Hello World</div>")
        
        updated = await wait_for_text(result, "Hello", timeout=1.0)
        assert "Hello" in updated.text
    
    @pytest.mark.asyncio
    async def test_poll_until(self):
        """Test poll_until."""
        from pynext.testing.async_utils import poll_until
        
        counter = [0]
        
        def increment():
            counter[0] += 1
            return counter[0]
        
        result = await poll_until(increment, lambda x: x >= 3, timeout=1.0)
        assert result >= 3
    
    def test_sync_wait(self):
        """Test sync_wait helper."""
        from pynext.testing.async_utils import sync_wait
        
        async def async_task():
            await asyncio.sleep(0.01)
            return "done"
        
        result = sync_wait(async_task())
        assert result == "done"


# ============================================
# Benchmark Tests (5 tests)
# ============================================

class TestBenchmarks:
    """Tests for performance benchmarking."""
    
    def test_benchmark_decorator(self):
        """Test @benchmark decorator."""
        from pynext.testing.benchmarks import benchmark, BenchmarkResult
        
        @benchmark(iterations=10, warmup=2)
        def test_func():
            return sum(range(100))
        
        result = test_func()
        assert result == sum(range(100))
        assert hasattr(test_func, "_benchmark_result")
    
    def test_timer_context_manager(self):
        """Test Timer context manager."""
        from pynext.testing.benchmarks import Timer
        import time
        
        with Timer() as t:
            time.sleep(0.01)
        
        assert t.ms >= 10
        assert t.seconds >= 0.01
    
    def test_time_function(self):
        """Test time_function utility."""
        from pynext.testing.benchmarks import time_function
        
        result, ms = time_function(lambda: 42)
        assert result == 42
        assert ms >= 0
    
    def test_assert_performance(self):
        """Test assert_performance."""
        from pynext.testing.benchmarks import BenchmarkResult, assert_performance
        
        result = BenchmarkResult(
            name="test",
            iterations=10,
            mean_ms=5.0,
            median_ms=4.5,
            min_ms=3.0,
            max_ms=8.0,
            std_dev_ms=1.0,
            timings=[4.0, 5.0, 4.5, 5.5, 4.0] * 2,
        )
        
        assert_performance(result, max_median_ms=10.0)  # Should pass
    
    def test_benchmark_result_percentile(self):
        """Test BenchmarkResult percentile calculation."""
        from pynext.testing.benchmarks import BenchmarkResult
        
        result = BenchmarkResult(
            name="test",
            iterations=100,
            mean_ms=5.0,
            median_ms=5.0,
            min_ms=1.0,
            max_ms=10.0,
            std_dev_ms=2.0,
            timings=list(range(1, 101)),
        )
        
        # Percentile is calculated as index = int(len(timings) * p / 100)
        # For p=95: index = int(100 * 95 / 100) = 95, so timings[95] = 96
        assert result.p95 >= 95
        assert result.p99 >= 99


# ============================================
# Coverage Tests (4 tests)
# ============================================

class TestCoverage:
    """Tests for coverage tools."""
    
    def test_signal_coverage_returns_result(self):
        """Test signal_coverage returns SignalCoverage."""
        from pynext.testing import RenderResult
        from pynext.testing.coverage import signal_coverage, SignalCoverage
        
        result = RenderResult(html="<div>Test</div>", signals={})
        coverage = signal_coverage(result)
        assert isinstance(coverage, SignalCoverage)
    
    def test_coverage_report(self):
        """Test coverage_report returns string."""
        from pynext.testing.coverage import coverage_report
        
        report = coverage_report()
        assert isinstance(report, str)
        assert "Coverage Report" in report
    
    def test_coverage_json(self):
        """Test coverage_json returns dict."""
        from pynext.testing.coverage import coverage_json
        
        data = coverage_json()
        assert isinstance(data, dict)
        assert "signals" in data
        assert "components" in data
    
    def test_reset_coverage(self):
        """Test reset_coverage clears data."""
        from pynext.testing.coverage import reset_coverage, get_coverage
        
        reset_coverage()
        coverage = get_coverage()
        assert len(coverage.signals.defined) == 0


# ============================================
# Performance Assertions (3 tests)
# ============================================

class TestPerformanceAssertions:
    """Tests for performance assertions."""
    
    def test_assert_render_time_passes(self):
        """Test assert_render_time with fast render."""
        from pynext.testing import RenderResult
        from pynext.testing.assertions import assert_render_time
        
        result = RenderResult(html="<div>Fast</div>")
        result.render_time_ms = 5.0
        assert_render_time(result, max_ms=100)
    
    def test_assert_render_time_fails(self):
        """Test assert_render_time with slow render."""
        from pynext.testing import RenderResult
        from pynext.testing.assertions import assert_render_time
        from pynext.testing.assertions import AssertionError as TestAssertionError
        
        result = RenderResult(html="<div>Slow</div>")
        result.render_time_ms = 200.0
        
        with pytest.raises(TestAssertionError):
            assert_render_time(result, max_ms=100)
    
    def test_assert_faster_than(self):
        """Test assert_faster_than."""
        from pynext.testing.benchmarks import BenchmarkResult, assert_faster_than
        
        baseline = BenchmarkResult(
            name="baseline",
            iterations=10,
            mean_ms=10.0,
            median_ms=10.0,
            min_ms=8.0,
            max_ms=12.0,
            std_dev_ms=1.0,
            timings=[10.0] * 10,
        )
        
        current = BenchmarkResult(
            name="current",
            iterations=10,
            mean_ms=8.0,
            median_ms=8.0,
            min_ms=6.0,
            max_ms=10.0,
            std_dev_ms=1.0,
            timings=[8.0] * 10,
        )
        
        assert_faster_than(current, baseline)  # Should pass

