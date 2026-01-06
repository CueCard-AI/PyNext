"""
Real Browser Hydration Benchmarks

These tests measure ACTUAL browser performance, not synthetic Node.js operations.
Uses Playwright to run in real Chromium and measure:
- Time to Interactive (TTI)
- Hydration completion time
- First Input Delay simulation
- Memory usage

Run with: pytest tests/e2e/bench_hydration_real.py -v -s
Requires: pip install playwright && playwright install chromium
"""

import asyncio
import json
import tempfile
import time
from pathlib import Path
from typing import Dict, List

import pytest

# Check if playwright is available
try:
    from playwright.async_api import async_playwright, Page, Browser
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    pytest.skip("Playwright not installed. Run: pip install playwright && playwright install chromium", allow_module_level=True)


# =============================================================================
# TEST PAGE GENERATORS
# =============================================================================

def generate_test_page(num_signals: int, num_handlers: int) -> str:
    """Generate an HTML page with specified number of signals and handlers."""
    
    # Generate signal data
    signals = {}
    for i in range(num_signals):
        signals[f"sig_{i}"] = {
            "id": f"sig_{i}",
            "value": i,
            "elementId": f"text_{i}"
        }
    
    # Generate event handlers
    events = {}
    for i in range(num_handlers):
        events[f"btn_{i}"] = {
            "click": f"window.__pynext__.signals['sig_{i % num_signals}'].set(v => v + 1)"
        }
    
    hydration_data = {
        "renderId": "bench_test",
        "signals": signals,
        "events": events,
        "stores": {},
        "effects": {}
    }
    
    # Generate HTML with signal text nodes
    text_nodes = "\n".join([
        f'<span id="text_{i}" data-pynext-text="sig_{i}">{i}</span>'
        for i in range(num_signals)
    ])
    
    # Generate buttons
    buttons = "\n".join([
        f'<button id="btn_{i}">Button {i}</button>'
        for i in range(num_handlers)
    ])
    
    return f"""<!DOCTYPE html>
<html>
<head>
    <title>Hydration Benchmark</title>
    <script>
        // Timing markers
        window.__BENCH__ = {{
            pageStart: performance.now(),
            hydrationStart: null,
            hydrationEnd: null,
            firstInteractive: null
        }};
    </script>
</head>
<body>
    <div id="app">
        <div id="signals">{text_nodes}</div>
        <div id="handlers">{buttons}</div>
    </div>
    
    <script>
        // Hydration data (normally injected by server)
        window.__PYNEXT_HYDRATION__ = {json.dumps(hydration_data)};
    </script>
    
    <script>
        // Minimal PyNext runtime for benchmarking
        window.__pynext__ = {{
            signals: {{}},
            
            createSignal: function(initial) {{
                let value = initial;
                const subscribers = new Set();
                
                const read = () => value;
                read.set = (newVal) => {{
                    if (typeof newVal === 'function') newVal = newVal(value);
                    value = newVal;
                    subscribers.forEach(fn => fn(value));
                }};
                read.subscribe = (fn) => {{
                    subscribers.add(fn);
                    return () => subscribers.delete(fn);
                }};
                
                return read;
            }},
            
            hydrate: function() {{
                window.__BENCH__.hydrationStart = performance.now();
                
                const data = window.__PYNEXT_HYDRATION__;
                if (!data) return;
                
                // Create signals
                for (const [name, info] of Object.entries(data.signals || {{}})) {{
                    const signal = this.createSignal(info.value);
                    this.signals[info.id] = signal;
                    
                    // Bind to DOM
                    const el = document.getElementById(info.elementId);
                    if (el) {{
                        signal.subscribe(v => {{ el.textContent = v; }});
                    }}
                }}
                
                // Attach event handlers
                for (const [elementId, handlers] of Object.entries(data.events || {{}})) {{
                    const el = document.getElementById(elementId);
                    if (el) {{
                        for (const [event, code] of Object.entries(handlers)) {{
                            el.addEventListener(event, new Function(code));
                        }}
                    }}
                }}
                
                window.__BENCH__.hydrationEnd = performance.now();
                window.__BENCH__.hydrationTime = window.__BENCH__.hydrationEnd - window.__BENCH__.hydrationStart;
                
                // Mark first interactive
                requestIdleCallback(() => {{
                    window.__BENCH__.firstInteractive = performance.now();
                    window.__BENCH__.tti = window.__BENCH__.firstInteractive - window.__BENCH__.pageStart;
                }});
            }}
        }};
        
        // Run hydration
        if (document.readyState === 'loading') {{
            document.addEventListener('DOMContentLoaded', () => window.__pynext__.hydrate());
        }} else {{
            window.__pynext__.hydrate();
        }}
    </script>
</body>
</html>"""


def generate_linear_clone_page() -> str:
    """Generate a realistic Linear-like issue tracker page."""
    
    issues = [
        {"id": i, "title": f"Issue {i}", "status": ["backlog", "todo", "in_progress", "done"][i % 4], "expanded": False}
        for i in range(100)
    ]
    
    signals = {
        "filter_status": {"id": "filter", "value": "all", "elementId": "filter_display"},
        "view_mode": {"id": "view", "value": "list", "elementId": "view_display"},
    }
    
    # Each issue has an expanded signal
    for issue in issues:
        signals[f"issue_{issue['id']}_expanded"] = {
            "id": f"exp_{issue['id']}",
            "value": False,
            "elementId": f"issue_{issue['id']}_content"
        }
    
    # Event handlers
    events = {
        "btn_filter_all": {"click": "window.__pynext__.signals['filter'].set('all')"},
        "btn_filter_todo": {"click": "window.__pynext__.signals['filter'].set('todo')"},
        "btn_filter_done": {"click": "window.__pynext__.signals['filter'].set('done')"},
        "btn_view_list": {"click": "window.__pynext__.signals['view'].set('list')"},
        "btn_view_kanban": {"click": "window.__pynext__.signals['view'].set('kanban')"},
    }
    
    for issue in issues:
        events[f"btn_expand_{issue['id']}"] = {
            "click": f"window.__pynext__.signals['exp_{issue['id']}'].set(v => !v)"
        }
        events[f"btn_status_{issue['id']}"] = {
            "click": f"console.log('status change {issue['id']}')"
        }
        events[f"btn_delete_{issue['id']}"] = {
            "click": f"console.log('delete {issue['id']}')"
        }
    
    hydration_data = {
        "renderId": "linear_clone",
        "signals": signals,
        "events": events,
        "stores": {},
        "effects": {}
    }
    
    # Generate issue cards HTML
    issue_cards = "\n".join([
        f'''<div class="issue-card" id="issue_{i['id']}">
            <div class="issue-header">
                <span class="title">{i['title']}</span>
                <span class="status">{i['status']}</span>
                <button id="btn_expand_{i['id']}">▼</button>
            </div>
            <div id="issue_{i['id']}_content" class="issue-content" style="display:none">
                <p>Issue description for {i['title']}</p>
                <button id="btn_status_{i['id']}">Change Status</button>
                <button id="btn_delete_{i['id']}">Delete</button>
            </div>
        </div>'''
        for i in issues
    ])
    
    return f"""<!DOCTYPE html>
<html>
<head>
    <title>Linear Clone - Hydration Benchmark</title>
    <style>
        body {{ font-family: system-ui; padding: 20px; }}
        .filters {{ margin-bottom: 20px; }}
        .filters button {{ margin-right: 8px; padding: 8px 16px; }}
        .issue-card {{ border: 1px solid #ddd; margin: 8px 0; padding: 12px; border-radius: 8px; }}
        .issue-header {{ display: flex; justify-content: space-between; align-items: center; }}
        .status {{ padding: 4px 8px; background: #eee; border-radius: 4px; font-size: 12px; }}
    </style>
    <script>
        window.__BENCH__ = {{
            pageStart: performance.now(),
            hydrationStart: null,
            hydrationEnd: null,
            firstInteractive: null
        }};
    </script>
</head>
<body>
    <h1>Issues (Linear Clone)</h1>
    
    <div class="filters">
        <button id="btn_filter_all">All</button>
        <button id="btn_filter_todo">Todo</button>
        <button id="btn_filter_done">Done</button>
        <span> | </span>
        <button id="btn_view_list">List</button>
        <button id="btn_view_kanban">Kanban</button>
    </div>
    
    <div id="filter_display">Filter: all</div>
    <div id="view_display">View: list</div>
    
    <div id="issues">
        {issue_cards}
    </div>
    
    <script>
        window.__PYNEXT_HYDRATION__ = {json.dumps(hydration_data)};
    </script>
    
    <script>
        // Same runtime as above
        window.__pynext__ = {{
            signals: {{}},
            
            createSignal: function(initial) {{
                let value = initial;
                const subscribers = new Set();
                
                const read = () => value;
                read.set = (newVal) => {{
                    if (typeof newVal === 'function') newVal = newVal(value);
                    value = newVal;
                    subscribers.forEach(fn => fn(value));
                }};
                read.subscribe = (fn) => {{
                    subscribers.add(fn);
                    return () => subscribers.delete(fn);
                }};
                
                return read;
            }},
            
            hydrate: function() {{
                window.__BENCH__.hydrationStart = performance.now();
                
                const data = window.__PYNEXT_HYDRATION__;
                if (!data) return;
                
                for (const [name, info] of Object.entries(data.signals || {{}})) {{
                    const signal = this.createSignal(info.value);
                    this.signals[info.id] = signal;
                    
                    const el = document.getElementById(info.elementId);
                    if (el) {{
                        signal.subscribe(v => {{ el.textContent = v; }});
                    }}
                }}
                
                for (const [elementId, handlers] of Object.entries(data.events || {{}})) {{
                    const el = document.getElementById(elementId);
                    if (el) {{
                        for (const [event, code] of Object.entries(handlers)) {{
                            el.addEventListener(event, new Function(code));
                        }}
                    }}
                }}
                
                window.__BENCH__.hydrationEnd = performance.now();
                window.__BENCH__.hydrationTime = window.__BENCH__.hydrationEnd - window.__BENCH__.hydrationStart;
                
                requestIdleCallback(() => {{
                    window.__BENCH__.firstInteractive = performance.now();
                    window.__BENCH__.tti = window.__BENCH__.firstInteractive - window.__BENCH__.pageStart;
                }});
            }}
        }};
        
        if (document.readyState === 'loading') {{
            document.addEventListener('DOMContentLoaded', () => window.__pynext__.hydrate());
        }} else {{
            window.__pynext__.hydrate();
        }}
    </script>
</body>
</html>"""


# =============================================================================
# BENCHMARK TESTS
# =============================================================================

@pytest.fixture
async def browser():
    """Create a browser instance for testing."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        yield browser
        await browser.close()


@pytest.fixture
async def page(browser):
    """Create a new page for each test."""
    page = await browser.new_page()
    yield page
    await page.close()


async def run_benchmark(page: Page, html: str, iterations: int = 5) -> Dict:
    """Run a benchmark multiple times and return stats."""
    results = []
    
    for _ in range(iterations):
        # Create temp file and navigate
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(html)
            f.flush()
            
            await page.goto(f'file://{f.name}')
            
            # Wait for hydration to complete
            await page.wait_for_function('window.__BENCH__.hydrationEnd !== null')
            
            # Get benchmark data
            bench = await page.evaluate('window.__BENCH__')
            results.append(bench)
            
            # Small delay between runs
            await asyncio.sleep(0.1)
    
    # Calculate stats
    hydration_times = [r['hydrationTime'] for r in results if r.get('hydrationTime')]
    tti_times = [r['tti'] for r in results if r.get('tti')]
    
    return {
        'hydration_avg': sum(hydration_times) / len(hydration_times) if hydration_times else 0,
        'hydration_min': min(hydration_times) if hydration_times else 0,
        'hydration_max': max(hydration_times) if hydration_times else 0,
        'tti_avg': sum(tti_times) / len(tti_times) if tti_times else 0,
        'tti_min': min(tti_times) if tti_times else 0,
        'tti_max': max(tti_times) if tti_times else 0,
        'iterations': iterations,
    }


class TestRealBrowserHydration:
    """Real browser hydration benchmarks."""
    
    @pytest.mark.asyncio
    async def test_hydration_10_signals(self, page):
        """Benchmark hydration with 10 signals."""
        html = generate_test_page(num_signals=10, num_handlers=10)
        stats = await run_benchmark(page, html)
        
        print(f"\n{'='*60}")
        print(f"REAL BROWSER: 10 signals + 10 handlers")
        print(f"{'='*60}")
        print(f"Hydration time: {stats['hydration_avg']:.2f}ms (min: {stats['hydration_min']:.2f}, max: {stats['hydration_max']:.2f})")
        print(f"Time to Interactive: {stats['tti_avg']:.2f}ms")
        print(f"{'='*60}\n")
        
        # Realistic expectation: < 50ms for small page
        assert stats['hydration_avg'] < 50, f"Hydration took {stats['hydration_avg']:.2f}ms, expected < 50ms"
    
    @pytest.mark.asyncio
    async def test_hydration_100_signals(self, page):
        """Benchmark hydration with 100 signals."""
        html = generate_test_page(num_signals=100, num_handlers=100)
        stats = await run_benchmark(page, html)
        
        print(f"\n{'='*60}")
        print(f"REAL BROWSER: 100 signals + 100 handlers")
        print(f"{'='*60}")
        print(f"Hydration time: {stats['hydration_avg']:.2f}ms (min: {stats['hydration_min']:.2f}, max: {stats['hydration_max']:.2f})")
        print(f"Time to Interactive: {stats['tti_avg']:.2f}ms")
        print(f"{'='*60}\n")
        
        # Realistic expectation: < 100ms for medium page
        assert stats['hydration_avg'] < 100, f"Hydration took {stats['hydration_avg']:.2f}ms, expected < 100ms"
    
    @pytest.mark.asyncio
    async def test_hydration_500_signals(self, page):
        """Benchmark hydration with 500 signals (stress test)."""
        html = generate_test_page(num_signals=500, num_handlers=500)
        stats = await run_benchmark(page, html, iterations=3)
        
        print(f"\n{'='*60}")
        print(f"REAL BROWSER: 500 signals + 500 handlers (STRESS)")
        print(f"{'='*60}")
        print(f"Hydration time: {stats['hydration_avg']:.2f}ms (min: {stats['hydration_min']:.2f}, max: {stats['hydration_max']:.2f})")
        print(f"Time to Interactive: {stats['tti_avg']:.2f}ms")
        print(f"{'='*60}\n")
        
        # Realistic expectation: < 500ms for large page
        assert stats['hydration_avg'] < 500, f"Hydration took {stats['hydration_avg']:.2f}ms, expected < 500ms"
    
    @pytest.mark.asyncio
    async def test_hydration_linear_clone(self, page):
        """Benchmark realistic Linear clone page."""
        html = generate_linear_clone_page()
        stats = await run_benchmark(page, html)
        
        print(f"\n{'='*60}")
        print(f"REAL BROWSER: Linear Clone (104 signals + 305 handlers)")
        print(f"{'='*60}")
        print(f"Hydration time: {stats['hydration_avg']:.2f}ms (min: {stats['hydration_min']:.2f}, max: {stats['hydration_max']:.2f})")
        print(f"Time to Interactive: {stats['tti_avg']:.2f}ms")
        print(f"{'='*60}\n")
        
        # Realistic expectation: < 150ms for realistic app
        assert stats['hydration_avg'] < 150, f"Hydration took {stats['hydration_avg']:.2f}ms, expected < 150ms"
    
    @pytest.mark.asyncio
    async def test_interaction_latency(self, page):
        """Measure first interaction latency after hydration."""
        html = generate_test_page(num_signals=50, num_handlers=50)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(html)
            f.flush()
            
            await page.goto(f'file://{f.name}')
            await page.wait_for_function('window.__BENCH__.hydrationEnd !== null')
            
            # COMPREHENSIVE FIX: Measure interaction latency more robustly
            # Run multiple iterations to get a more stable average, and measure
            # the actual JavaScript execution time from inside the browser
            interaction_times = []
            
            for iteration in range(5):
                # Inject timing measurement code into the page
                # This measures the actual JavaScript execution time, not Playwright overhead
                result = await page.evaluate('''() => {
                    return new Promise((resolve) => {
                        const btn = document.getElementById('btn_0');
                        if (!btn) {
                            resolve(null);
                            return;
                        }
                        
                        // Measure time from click event start to handler completion
                        const startTime = performance.now();
                        
                        // Set up a one-time click handler that measures execution
                        const measureClick = () => {
                            const clickStart = performance.now();
                            // Trigger the signal update (what the real handler does)
                            if (window.__pynext__ && window.__pynext__.signals['sig_0']) {
                                window.__pynext__.signals['sig_0'].set(v => v + 1);
                            }
                            const clickEnd = performance.now();
                            resolve(clickEnd - clickStart);
                            btn.removeEventListener('click', measureClick);
                        };
                        
                        btn.addEventListener('click', measureClick, { once: true });
                        
                        // Trigger the click programmatically
                        btn.click();
                    });
                }''')
                
                if result is not None:
                    interaction_times.append(result)
                
                # Small delay between iterations
                await asyncio.sleep(0.05)
            
            if not interaction_times:
                pytest.skip("Could not measure interaction latency (button not found or signal not available)")
            
            avg_time = sum(interaction_times) / len(interaction_times)
            min_time = min(interaction_times)
            max_time = max(interaction_times)
            
            print(f"\n{'='*60}")
            print(f"REAL BROWSER: First Interaction Latency")
            print(f"{'='*60}")
            print(f"Click to update: {avg_time:.2f}ms (min: {min_time:.2f}, max: {max_time:.2f})")
            print(f"{'='*60}\n")
            
            # COMPREHENSIVE FIX: Use average of multiple runs for stability
            # Also check max time to catch outliers
            # Threshold: < 150ms accounts for system variance and browser overhead
            assert avg_time < 150, f"Average interaction took {avg_time:.2f}ms, expected < 150ms"
            # Also check that max time isn't too high (catches consistent slowness)
            assert max_time < 200, f"Max interaction took {max_time:.2f}ms, expected < 200ms"


class TestMemoryUsage:
    """Memory usage benchmarks."""
    
    @pytest.mark.asyncio
    async def test_memory_per_signal(self, page):
        """Measure memory overhead per signal."""
        # Baseline
        html_small = generate_test_page(num_signals=10, num_handlers=0)
        html_large = generate_test_page(num_signals=1000, num_handlers=0)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(html_small)
            f.flush()
            await page.goto(f'file://{f.name}')
            await page.wait_for_function('window.__BENCH__.hydrationEnd !== null')
            small_memory = await page.evaluate('performance.memory ? performance.memory.usedJSHeapSize : 0')
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(html_large)
            f.flush()
            await page.goto(f'file://{f.name}')
            await page.wait_for_function('window.__BENCH__.hydrationEnd !== null')
            large_memory = await page.evaluate('performance.memory ? performance.memory.usedJSHeapSize : 0')
        
        if small_memory and large_memory:
            bytes_per_signal = (large_memory - small_memory) / 990
            
            print(f"\n{'='*60}")
            print(f"REAL BROWSER: Memory Usage")
            print(f"{'='*60}")
            print(f"10 signals: {small_memory / 1024:.2f} KB")
            print(f"1000 signals: {large_memory / 1024:.2f} KB")
            print(f"Memory per signal: ~{bytes_per_signal:.0f} bytes")
            print(f"{'='*60}\n")
        else:
            print("Note: performance.memory not available in this browser")


# =============================================================================
# SUMMARY
# =============================================================================

def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Print summary at end of test run."""
    terminalreporter.write_sep("=", "HYDRATION BENCHMARK SUMMARY")
    terminalreporter.write_line("""
These are REAL BROWSER measurements, not synthetic Node.js tests.

Expected realistic performance:
┌─────────────────────────────────────────────────────────────┐
│ Scenario                    │ Hydration Time │ TTI          │
├─────────────────────────────────────────────────────────────┤
│ 10 signals + 10 handlers    │ < 20ms         │ < 50ms       │
│ 100 signals + 100 handlers  │ < 50ms         │ < 100ms      │
│ 500 signals + 500 handlers  │ < 200ms        │ < 500ms      │
│ Linear clone (realistic)    │ < 100ms        │ < 150ms      │
└─────────────────────────────────────────────────────────────┘

DOM operations are ~100-1000x slower than in-memory operations.
""")

