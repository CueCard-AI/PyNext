"""
Browser Parity Harness for Runtime Tests

WHAT: Infrastructure for testing transpiled Python code in real browsers
WHY: Ensures transpiled code actually runs correctly, not just looks correct
HOW: Uses Playwright to inject and execute transpiled JS in browser context
WHO: Used by all browser-based parity tests (34.1, 34.2, 34.3, 34.4)
WHEN: During E2E testing phase to verify browser behavior
WHERE: tests/e2e/browser_parity_harness.py

This harness enables testing that transpiled Python code produces
semantically equivalent results when executed in a real browser environment.
"""

import pytest
from typing import Dict, Any, Optional, List

# Check if playwright is available
try:
    from playwright.sync_api import Page, sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

from pynext.transpiler import transpile
from pynext.transpiler.runtime_loader import get_test_runtime


class BrowserParityHarness:
    """
    Execute transpiled Python code in a real browser.
    
    This harness:
    1. Transpiles Python code to JavaScript
    2. Injects the PyNext runtime into the browser page
    3. Executes the transpiled code
    4. Captures console output and errors
    5. Returns structured results for assertion
    
    Example:
        harness = BrowserParityHarness(page)
        result = harness.execute('''
            from pynext.client import document
            el = document.createElement("div")
            el.textContent = "Hello"
            print(el.textContent)
        ''')
        assert result["success"]
        assert "Hello" in result["output"]
    """
    
    def __init__(self, page: Page):
        """
        Initialize harness with a Playwright page.
        
        Args:
            page: Playwright Page object to execute code in
        """
        self.page = page
        self._runtime: Optional[str] = None
        self._setup_page()
    
    def _setup_page(self) -> None:
        """Navigate to blank page and prepare for execution."""
        self.page.goto("about:blank")
    
    @property
    def runtime(self) -> str:
        """
        Get PyNext runtime for browser injection.
        
        Lazy-loads and caches the runtime for efficiency.
        """
        if self._runtime is None:
            self._runtime = get_test_runtime(include_dunders=True)
        return self._runtime
    
    def execute(
        self,
        python_code: str,
        *,
        include_dom_helpers: bool = True,
        timeout: int = 5000
    ) -> Dict[str, Any]:
        """
        Transpile Python code and execute in browser.
        
        Args:
            python_code: Python code to transpile and execute
            include_dom_helpers: Whether to include DOM helper shims (default: True)
            timeout: Execution timeout in milliseconds (default: 5000)
        
        Returns:
            Dictionary with:
                - success: bool - Whether execution succeeded without errors
                - output: List[str] - Console.log output lines
                - error: Optional[str] - Error message if failed
                - result: Any - Last expression result (if applicable)
        """
        # Transpile Python to JavaScript
        try:
            js_code = transpile(python_code)
        except Exception as e:
            return {
                "success": False,
                "output": [],
                "error": f"Transpilation error: {str(e)}",
                "result": None
            }
        
        return self.execute_js(js_code, include_dom_helpers=include_dom_helpers, timeout=timeout)
    
    def execute_js(
        self,
        js_code: str,
        *,
        include_dom_helpers: bool = True,
        timeout: int = 5000
    ) -> Dict[str, Any]:
        """
        Execute JavaScript code directly in browser.
        
        This is useful when you want to test raw JS or already-transpiled code.
        
        Args:
            js_code: JavaScript code to execute
            include_dom_helpers: Whether to include DOM helper shims (default: True)
            timeout: Execution timeout in milliseconds (default: 5000)
        
        Returns:
            Same structure as execute()
        """
        # Build the DOM helpers if requested
        dom_helpers = ""
        if include_dom_helpers:
            dom_helpers = """
                // Make print() work like Python
                function print(...args) {
                    console.log(...args);
                }
            """
        
        # Escape JS code for template literal embedding
        js_code_escaped = js_code.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')
        
        # Build wrapper that captures output
        wrapper = f"""
        () => {{
            // Shim Node.js globals for browser compatibility
            if (typeof global === 'undefined') {{
                window.global = window;
            }}
            if (typeof module === 'undefined') {{
                window.module = {{ exports: {{}} }};
            }}
            if (typeof exports === 'undefined') {{
                window.exports = {{}};
            }}
            
            // Capture console output
            const output = [];
            const originalLog = console.log;
            console.log = (...args) => {{
                const line = args.map(v => {{
                    if (v === null) return 'None';
                    if (v === undefined) return 'None';
                    if (typeof v === 'object') {{
                        try {{
                            return JSON.stringify(v);
                        }} catch {{
                            return String(v);
                        }}
                    }}
                    return String(v);
                }}).join(' ');
                output.push(line);
                originalLog(...args);
            }};
            
            // Inject runtime
            {self.runtime}
            
            // Inject DOM helpers
            {dom_helpers}
            
            // Execute transpiled code
            try {{
                const code = `{js_code_escaped}`;
                const result = eval(code);
                return {{ success: true, output, result }};
            }} catch (e) {{
                return {{ success: false, output, error: e.message, stack: e.stack }};
            }} finally {{
                console.log = originalLog;
            }}
        }}
        """
        
        try:
            result = self.page.evaluate(wrapper)
            return {
                "success": result.get("success", False),
                "output": result.get("output", []),
                "error": result.get("error"),
                "result": result.get("result")
            }
        except Exception as e:
            return {
                "success": False,
                "output": [],
                "error": f"Browser execution error: {str(e)}",
                "result": None
            }
    
    def execute_and_compare(
        self,
        python_code: str,
        expected_output: List[str],
        *,
        strict: bool = False
    ) -> bool:
        """
        Execute code and compare output to expected.
        
        Args:
            python_code: Python code to transpile and execute
            expected_output: Expected console output lines
            strict: If True, require exact match; if False, allow substring matching
        
        Returns:
            True if output matches expected
        """
        result = self.execute(python_code)
        
        if not result["success"]:
            return False
        
        output = result["output"]
        
        if len(output) != len(expected_output):
            return False
        
        for actual, expected in zip(output, expected_output):
            if strict:
                if actual != expected:
                    return False
            else:
                # Substring matching - expected should be in actual
                if expected not in actual:
                    return False
        
        return True
    
    def get_element_property(
        self,
        selector: str,
        property_name: str
    ) -> Any:
        """
        Get a property value from a DOM element.
        
        Useful for verifying DOM state after code execution.
        
        Args:
            selector: CSS selector to find element
            property_name: Property name to retrieve
        
        Returns:
            Property value, or None if element not found
        """
        result = self.page.evaluate(f'''
            () => {{
                const el = document.querySelector({repr(selector)});
                if (!el) return null;
                return el[{repr(property_name)}];
            }}
        ''')
        return result
    
    def reset_page(self) -> None:
        """Reset page to blank state for next test."""
        self._setup_page()


# =============================================================================
# Pytest Fixtures
# =============================================================================

@pytest.fixture(scope="function")
def browser_parity_harness():
    """
    Create a BrowserParityHarness for each test.
    
    Usage:
        def test_something(browser_parity_harness):
            harness = browser_parity_harness
            result = harness.execute('print("hello")')
            assert result["success"]
    """
    if not PLAYWRIGHT_AVAILABLE:
        pytest.skip("Playwright not installed")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        harness = BrowserParityHarness(page)
        yield harness
        page.close()
        browser.close()


@pytest.fixture(scope="function")
def browser_page_for_parity():
    """
    Create a raw browser page for parity tests.
    
    Use this when you need more control than BrowserParityHarness provides.
    """
    if not PLAYWRIGHT_AVAILABLE:
        pytest.skip("Playwright not installed")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        yield page
        page.close()
        browser.close()


# =============================================================================
# Helper Functions
# =============================================================================

def compare_parity_results(
    python_output: str,
    js_output: List[str],
    *,
    normalize_whitespace: bool = True
) -> bool:
    """
    Compare Python execution output with JavaScript execution output.
    
    Args:
        python_output: stdout from Python execution
        js_output: output list from JS execution
        normalize_whitespace: Whether to normalize whitespace differences
    
    Returns:
        True if outputs are semantically equivalent
    """
    py_lines = [line.strip() for line in python_output.strip().split('\n') if line.strip()]
    js_lines = [line.strip() for line in js_output if line.strip()]
    
    if len(py_lines) != len(js_lines):
        return False
    
    for py_line, js_line in zip(py_lines, js_lines):
        if normalize_whitespace:
            # Normalize comma spacing, bracket spacing, etc.
            import re
            py_normalized = re.sub(r',\s+', ',', py_line)
            py_normalized = re.sub(r'\s+', ' ', py_normalized)
            js_normalized = re.sub(r',\s+', ',', js_line)
            js_normalized = re.sub(r'\s+', ' ', js_normalized)
            
            if py_normalized != js_normalized:
                return False
        else:
            if py_line != js_line:
                return False
    
    return True

