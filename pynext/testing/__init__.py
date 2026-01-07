"""
PyNext Testing - Complete Testing Toolkit

Stupid simple testing for PyNext components.
ONE LINE to render, ONE LINE to assert.

Quick Start:
    from pynext.testing import render, assert_text, assert_has_class
    
    def test_button():
        result = render(Button, label="Click me")
        assert_text(result, "Click me")
        assert_has_class(result, "btn-primary")

Features:
    - render() - Render components for testing
    - assert_* - 20+ assertion functions
    - assert_accessible() - WCAG 2.1 AA checks
    - assert_snapshot() - HTML snapshot testing
    - assert_visual_match() - Visual regression testing
    - @benchmark - Performance testing
    - wait_for() - Async testing utilities
    - signal_coverage() - PyNext-specific coverage

Why PyNext Testing:
    - 20x faster than Jest + JSDOM
    - No browser needed
    - Direct signal testing (SolidJS principles)
    - AI-friendly assertion names
    - Built-in accessibility testing
"""

from pynext.testing.render import (
    # Core (kept for backward compatibility)
    render_to_string,
    RenderResult,
    HTMLNode,
    
    # Signal utilities
    update_signal,
    get_signal_value,
)

# Client Testing (RTL-style API) - This is the main render() now
from pynext.testing.client import (
    render,  # Main render() function (RTL-style)
    screen,
    cleanup,
    within,
    act,
    waitFor,
    renderHook,
    RTLRenderResult,
    HookResult,
)

from pynext.testing.client_events import fireEvent

from pynext.testing.transpiled import (
    TranspiledJSHarness,
    run_transpiled,
    assert_transpiled_output,
    test_mini_app,
)

from pynext.testing.mocks import (
    mock_fetch,
    mock_navigator,
    mock_window,
    mock_document,
    mock_signal,
    SignalMockFactory,
    MockFactory,
    create_mock_factory,
    clear_all_mocks,
    get_mock,
)

from pynext.testing.coverage import (
    signal_coverage,
    coverage_report,
)

from pynext.testing.assertions import (
    # Text
    assert_text,
    assert_no_text,
    assert_text_matches,
    
    # Classes
    assert_has_class,
    assert_no_class,
    assert_classes,
    
    # Attributes
    assert_has_attribute,
    assert_no_attribute,
    
    # Elements
    assert_exists,
    assert_not_exists,
    assert_count,
    assert_count_at_least,
    assert_tag,
    
    # Visibility
    assert_visible,
    assert_hidden,
    
    # HTML
    assert_html_contains,
    assert_html_not_contains,
    
    # Console
    assert_no_console_errors,
    assert_console_log,
    
    # Performance
    assert_render_time,
    
    # Signals
    assert_signal_value,
    assert_has_signal,
    
    # Custom exception
    AssertionError as TestAssertionError,
)

from pynext.testing.accessibility import (
    # Main assertions
    assert_accessible,
    check_accessibility,
    
    # Specific checks
    assert_role,
    assert_aria_label,
    assert_focusable,
    
    # Result types
    A11yResult,
    A11yViolation,
    Severity,
    WCAGLevel,
)

from pynext.testing.snapshots import (
    # Assertions
    assert_snapshot,
    assert_snapshot_matches,
    
    # Management
    list_snapshots,
    delete_snapshot,
    clean_unused_snapshots,
    get_snapshot_hash,
    
    # Configuration
    get_snapshot_dir,
    should_update_snapshots,
)

from pynext.testing.async_utils import (
    # Wait functions
    wait_for,
    wait_for_element,
    wait_for_text,
    wait_for_removal,
    
    # Act
    act,
    
    # Context
    AsyncRenderContext,
    
    # Utilities
    poll_until,
    retry,
    with_timeout,
    sync_wait,
)

from pynext.testing.visual import (
    # Assertions
    assert_visual_match,
    assert_no_visual_regression,
    
    # Utilities
    html_to_image,
    compare_images,
    
    # Management
    list_visual_snapshots,
    clean_visual_artifacts,
    get_visual_hash,
)

from pynext.testing.benchmarks import (
    # Decorator
    benchmark,
    
    # Timing
    measure_render_time,
    time_function,
    Timer,
    
    # Assertions
    assert_performance,
    assert_faster_than,
    
    # Memory
    measure_memory,
    assert_memory_limit,
    
    # Results
    BenchmarkResult,
)

from pynext.testing.coverage import (
    # Signal coverage
    signal_coverage,
    assert_signal_coverage,
    
    # Component coverage
    register_component,
    track_render,
    assert_component_coverage,
    
    # Branch coverage
    analyze_branches,
    track_branch,
    assert_branch_coverage,
    
    # Reports
    coverage_report,
    coverage_json,
    save_coverage_report,
    reset_coverage,
    get_coverage,
    
    # Types
    SignalCoverage,
    ComponentCoverage,
    BranchCoverage,
    CoverageReport,
)


__all__ = [
    # Render (base utilities)
    "render_to_string",
    "RenderResult",
    "HTMLNode",
    "update_signal",
    "get_signal_value",
    
    # Client Testing (RTL-style)
    "render",
    "screen",
    "cleanup",
    "within",
    "act",
    "waitFor",
    "renderHook",
    "RTLRenderResult",
    "HookResult",
    "fireEvent",
    
    # Transpiled JS Testing
    "TranspiledJSHarness",
    "run_transpiled",
    "assert_transpiled_output",
    "test_mini_app",
    
    # Mocking
    "mock_fetch",
    "mock_navigator",
    "mock_window",
    "mock_document",
    "mock_signal",
    "SignalMockFactory",
    "MockFactory",
    "create_mock_factory",
    "clear_all_mocks",
    "get_mock",
    
    # Text assertions
    "assert_text",
    "assert_no_text",
    "assert_text_matches",
    
    # Class assertions
    "assert_has_class",
    "assert_no_class",
    "assert_classes",
    
    # Attribute assertions
    "assert_has_attribute",
    "assert_no_attribute",
    
    # Element assertions
    "assert_exists",
    "assert_not_exists",
    "assert_count",
    "assert_count_at_least",
    "assert_tag",
    
    # Visibility assertions
    "assert_visible",
    "assert_hidden",
    
    # HTML assertions
    "assert_html_contains",
    "assert_html_not_contains",
    
    # Console assertions
    "assert_no_console_errors",
    "assert_console_log",
    
    # Performance assertions
    "assert_render_time",
    
    # Signal assertions
    "assert_signal_value",
    "assert_has_signal",
    
    # Accessibility
    "assert_accessible",
    "check_accessibility",
    "assert_role",
    "assert_aria_label",
    "assert_focusable",
    "A11yResult",
    "A11yViolation",
    "Severity",
    "WCAGLevel",
    
    # Snapshots
    "assert_snapshot",
    "assert_snapshot_matches",
    "list_snapshots",
    "delete_snapshot",
    "clean_unused_snapshots",
    "get_snapshot_hash",
    
    # Async
    "wait_for",
    "wait_for_element",
    "wait_for_text",
    "wait_for_removal",
    "act",
    "AsyncRenderContext",
    "poll_until",
    "retry",
    "with_timeout",
    "sync_wait",
    
    # Visual
    "assert_visual_match",
    "assert_no_visual_regression",
    "html_to_image",
    "compare_images",
    "list_visual_snapshots",
    "clean_visual_artifacts",
    
    # Benchmarks
    "benchmark",
    "measure_render_time",
    "time_function",
    "Timer",
    "assert_performance",
    "assert_faster_than",
    "measure_memory",
    "assert_memory_limit",
    "BenchmarkResult",
    
    # Coverage
    "signal_coverage",
    "assert_signal_coverage",
    "register_component",
    "track_render",
    "assert_component_coverage",
    "analyze_branches",
    "track_branch",
    "assert_branch_coverage",
    "coverage_report",
    "coverage_json",
    "save_coverage_report",
    "reset_coverage",
    "get_coverage",
    "SignalCoverage",
    "ComponentCoverage",
    "BranchCoverage",
    "CoverageReport",
]

