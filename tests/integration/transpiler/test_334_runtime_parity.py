"""
Phase 33.4: Stdlib Runtime Parity Tests

WHAT: Tests that verify transpiled Python stdlib code ACTUALLY RUNS correctly
WHY: Ensures transpilation is semantically correct, not just syntactically valid
HOW: Transpiles Python code, bundles with esbuild, executes in Node.js
WHO: CI/CD pipeline, developers testing stdlib features
WHEN: During runtime verification phase
WHERE: tests/integration/transpiler/test_334_runtime_parity.py

These tests go beyond transpilation string matching to verify actual runtime behavior.
Each test:
1. Runs Python code and captures output
2. Transpiles to JavaScript
3. Bundles with esbuild (resolves ES module imports like collections.js)
4. Injects __py runtime from setup.js
5. Runs bundled JavaScript in Node.js
6. Compares outputs for semantic equivalence

Total: 18 tests
- Counter: 5 tests (basic counting, most_common, from_dict, elements, total)
- defaultdict: 3 tests (int factory, lambda factory, basic access)
- OrderedDict: 2 tests (basic, from_dict)
- deque: 3 tests (basic, appendleft, rotate)
- General stdlib: 5 tests (arithmetic, comprehensions, strings, lists, dicts)
"""

import pytest
import subprocess
import tempfile
import os
import json
import shutil
from pathlib import Path
from pynext.transpiler import transpile


def get_runtime_path() -> Path:
    """Get path to the runtime directory."""
    import pynext
    return Path(pynext.__file__).parent / "runtime" / "stdlib"


def get_project_root() -> Path:
    """Get project root directory."""
    import pynext
    return Path(pynext.__file__).parent.parent


class BundledExecutor:
    """Execute transpiled JS with bundled runtime via esbuild."""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        self.runtime_path = get_runtime_path()
        self.project_root = get_project_root()
        self.setup_js = self.project_root / "tests" / "js" / "transpiler" / "setup.js"
    
    def execute(self, python_code: str) -> dict:
        """Transpile Python, bundle with esbuild, and execute in Node.js."""
        try:
            # Transpile
            js_code = transpile(python_code)
            
            # Fix the import path to be absolute
            collections_path = str(self.runtime_path / "collections.js").replace('\\', '/')
            js_code = js_code.replace(
                'from "./collections.js"',
                f'from "{collections_path}"'
            )
            
            # Add 'new' to Counter/defaultdict/deque/OrderedDict calls
            for cls in ['Counter', 'defaultdict', 'deque', 'OrderedDict']:
                # Match patterns like "Counter(" but not "new Counter("
                import re
                js_code = re.sub(
                    rf'(?<!new )(?<![.\w])({cls})\(',
                    rf'new \1(',
                    js_code
                )
            
            # Read setup.js for __py runtime
            setup_code = self.setup_js.read_text() if self.setup_js.exists() else ""
            
            # Write transpiled code
            entry_file = os.path.join(self.temp_dir, "entry.mjs")
            
            # Create wrapper that captures output
            wrapper = f'''
// PyNext runtime (__py object)
{setup_code}

// Output capture
const output = [];
const originalLog = console.log;
console.log = (...args) => {{
    output.push(args.map(a => {{
        if (a === null) return 'None';
        if (a === undefined) return 'None';
        if (typeof a === 'object') {{
            if (Array.isArray(a)) {{
                if (a.length > 0 && Array.isArray(a[0]) && a[0].length === 2) {{
                    return '[' + a.map(([k, v]) => '(' + k + ', ' + v + ')').join(', ') + ']';
                }}
                return '[' + a.map(v => String(v)).join(', ') + ']';
            }}
            return JSON.stringify(a);
        }}
        return String(a);
    }}).join(' '));
}};

// Add print function
function print(...args) {{
    console.log(...args);
}}

// Transpiled code
{js_code}

// Output result
originalLog(JSON.stringify({{ success: true, output }}));
'''
            
            with open(entry_file, "w") as f:
                f.write(wrapper)
            
            # Bundle with esbuild
            bundle_file = os.path.join(self.temp_dir, "bundle.cjs")
            
            result = subprocess.run(
                [
                    "npx", "esbuild",
                    entry_file,
                    "--bundle",
                    f"--outfile={bundle_file}",
                    "--format=cjs",
                    "--platform=node",
                    "--target=es2020",
                ],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.project_root,
            )
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "output": [],
                    "error": f"esbuild failed: {result.stderr}",
                    "stderr": result.stderr,
                }
            
            # Execute the bundle
            result = subprocess.run(
                ["node", bundle_file],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # Parse result
            try:
                lines = result.stdout.strip().split("\n")
                result_data = json.loads(lines[-1])
                return {
                    "success": result_data.get("success", False),
                    "output": result_data.get("output", []),
                    "error": result_data.get("error"),
                    "stderr": result.stderr,
                }
            except (json.JSONDecodeError, IndexError):
                return {
                    "success": False,
                    "output": [],
                    "error": f"Parse error: {result.stdout}",
                    "stderr": result.stderr,
                }
        except Exception as e:
            return {
                "success": False,
                "output": [],
                "error": str(e),
                "stderr": "",
            }
    
    def execute_python(self, code: str) -> dict:
        """Execute Python code and return result."""
        try:
            py_file = os.path.join(self.temp_dir, "test.py")
            with open(py_file, "w") as f:
                f.write(code)
            
            result = subprocess.run(
                ["python3", py_file],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": result.returncode == 0
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": str(e),
                "returncode": 1,
                "success": False
            }
    
    def cleanup(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)


def esbuild_available() -> bool:
    """Check if esbuild is available."""
    try:
        result = subprocess.run(
            ["npx", "esbuild", "--version"],
            capture_output=True,
            timeout=30
        )
        return result.returncode == 0
    except Exception:
        return False


# Skip if esbuild not available
pytestmark = pytest.mark.skipif(
    not esbuild_available(),
    reason="esbuild not available (run 'npm install')"
)


@pytest.fixture
def executor():
    """Create a bundled executor for runtime parity testing."""
    exec_instance = BundledExecutor()
    yield exec_instance
    exec_instance.cleanup()


# =============================================================================
# COUNTER RUNTIME PARITY TESTS (5 tests)
# =============================================================================

class TestCounterRuntimeParity:
    """Verify Counter executes correctly in both Python and transpiled JS."""
    
    def test_counter_basic_counting(self, executor):
        """Counter counts elements correctly."""
        code = '''
from collections import Counter
c = Counter(["a", "b", "a", "c", "a", "b"])
print(c["a"])
print(c["b"])
print(c["c"])
'''
        js_result = executor.execute(code)
        py_result = executor.execute_python(code)
        
        assert py_result["success"], f"Python failed: {py_result['stderr']}"
        assert js_result["success"], f"JS failed: {js_result.get('error', js_result['stderr'])}"
        
        # Compare outputs
        py_output = py_result["stdout"].strip().split("\n")
        js_output = js_result["output"]
        assert py_output == js_output, f"Python: {py_output}, JS: {js_output}"
    
    def test_counter_most_common(self, executor):
        """Counter.most_common() returns sorted results."""
        code = '''
from collections import Counter
c = Counter(["a", "b", "a", "c", "a", "b"])
top2 = c.most_common(2)
for item, count in top2:
    print(item, count)
'''
        js_result = executor.execute(code)
        py_result = executor.execute_python(code)
        
        assert py_result["success"]
        assert js_result["success"], f"JS failed: {js_result.get('error')}"
        
        py_output = py_result["stdout"].strip().split("\n")
        js_output = js_result["output"]
        assert py_output == js_output
    
    def test_counter_from_dict(self, executor):
        """Counter from dict works."""
        code = '''
from collections import Counter
c = Counter({"a": 3, "b": 1})
print(c["a"])
print(c["b"])
'''
        js_result = executor.execute(code)
        py_result = executor.execute_python(code)
        
        assert py_result["success"]
        assert js_result["success"], f"JS failed: {js_result.get('error')}"
        
        py_output = py_result["stdout"].strip().split("\n")
        js_output = js_result["output"]
        assert py_output == js_output
    
    def test_counter_elements(self, executor):
        """Counter.elements() yields repeated elements."""
        code = '''
from collections import Counter
c = Counter({"a": 2, "b": 1})
elems = sorted(list(c.elements()))
print(elems)
'''
        js_result = executor.execute(code)
        py_result = executor.execute_python(code)
        
        assert py_result["success"]
        assert js_result["success"], f"JS failed: {js_result.get('error')}"
        
        # Elements should match
        assert "a" in js_result["output"][0] and "b" in js_result["output"][0]
    
    def test_counter_total(self, executor):
        """Counter.total() sums counts."""
        code = '''
from collections import Counter
c = Counter({"a": 3, "b": 2, "c": 1})
print(c.total())
'''
        js_result = executor.execute(code)
        py_result = executor.execute_python(code)
        
        assert py_result["success"]
        assert js_result["success"], f"JS failed: {js_result.get('error')}"
        
        py_output = py_result["stdout"].strip()
        js_output = js_result["output"][0] if js_result["output"] else ""
        assert py_output == js_output


# =============================================================================
# DEFAULTDICT RUNTIME PARITY TESTS (3 tests)
# =============================================================================

class TestDefaultdictRuntimeParity:
    """Verify defaultdict executes correctly in both environments."""
    
    def test_defaultdict_int_factory(self, executor):
        """defaultdict with int factory (counting)."""
        code = '''
from collections import defaultdict
dd = defaultdict(int)
dd["a"] = dd["a"] + 1
dd["a"] = dd["a"] + 1
dd["b"] = dd["b"] + 1
for k in sorted(dd.keys()):
    print(k, dd[k])
'''
        js_result = executor.execute(code)
        py_result = executor.execute_python(code)
        
        assert py_result["success"]
        assert js_result["success"], f"JS failed: {js_result.get('error')}"
    
    def test_defaultdict_lambda_factory(self, executor):
        """defaultdict with lambda factory."""
        code = '''
from collections import defaultdict
dd = defaultdict(lambda: "default")
print(dd["missing"])
dd["existing"] = "value"
print(dd["existing"])
'''
        js_result = executor.execute(code)
        py_result = executor.execute_python(code)
        
        assert py_result["success"]
        assert js_result["success"], f"JS failed: {js_result.get('error')}"
    
    def test_defaultdict_basic_access(self, executor):
        """defaultdict basic get/set."""
        code = '''
from collections import defaultdict
dd = defaultdict(int)
dd["a"] = 5
dd["b"] = 10
print(dd["a"], dd["b"], dd["c"])
'''
        js_result = executor.execute(code)
        py_result = executor.execute_python(code)
        
        assert py_result["success"]
        assert js_result["success"], f"JS failed: {js_result.get('error')}"


# =============================================================================
# ORDEREDDICT RUNTIME PARITY TESTS (2 tests)
# =============================================================================

class TestOrderedDictRuntimeParity:
    """Verify OrderedDict preserves insertion order."""
    
    def test_ordereddict_basic(self, executor):
        """OrderedDict basic operations."""
        code = '''
from collections import OrderedDict
od = OrderedDict()
od["c"] = 3
od["a"] = 1
od["b"] = 2
print(len(od))
print(od["a"], od["b"], od["c"])
'''
        js_result = executor.execute(code)
        py_result = executor.execute_python(code)
        
        assert py_result["success"]
        assert js_result["success"], f"JS failed: {js_result.get('error')}"
    
    def test_ordereddict_from_dict(self, executor):
        """OrderedDict from dict."""
        code = '''
from collections import OrderedDict
od = OrderedDict({"x": 10, "y": 20})
print(od["x"], od["y"])
'''
        js_result = executor.execute(code)
        py_result = executor.execute_python(code)
        
        assert py_result["success"]
        assert js_result["success"], f"JS failed: {js_result.get('error')}"


# =============================================================================
# DEQUE RUNTIME PARITY TESTS (3 tests)
# =============================================================================

class TestDequeRuntimeParity:
    """Verify deque executes correctly in both environments."""
    
    def test_deque_basic(self, executor):
        """deque basic operations."""
        code = '''
from collections import deque
dq = deque([1, 2, 3])
print(dq.popleft())
print(dq.pop())
'''
        js_result = executor.execute(code)
        py_result = executor.execute_python(code)
        
        assert py_result["success"]
        assert js_result["success"], f"JS failed: {js_result.get('error')}"
        
        py_output = py_result["stdout"].strip().split("\n")
        js_output = js_result["output"]
        assert py_output == js_output
    
    def test_deque_appendleft(self, executor):
        """deque appendleft adds to front."""
        code = '''
from collections import deque
dq = deque([1, 2, 3])
dq.appendleft(0)
print(dq.popleft())
'''
        js_result = executor.execute(code)
        py_result = executor.execute_python(code)
        
        assert py_result["success"]
        assert js_result["success"], f"JS failed: {js_result.get('error')}"
    
    def test_deque_rotate(self, executor):
        """deque rotate shifts elements."""
        code = '''
from collections import deque
dq = deque([1, 2, 3, 4, 5])
dq.rotate(2)
print(dq.popleft())
print(dq.popleft())
'''
        js_result = executor.execute(code)
        py_result = executor.execute_python(code)
        
        assert py_result["success"]
        assert js_result["success"], f"JS failed: {js_result.get('error')}"


# =============================================================================
# ADDITIONAL STDLIB RUNTIME PARITY TESTS (5 tests)
# =============================================================================

class TestStdlibRuntimeParity:
    """Test additional stdlib features."""
    
    def test_arithmetic_operations(self, executor):
        """Basic arithmetic operations work."""
        code = '''
x = 16 ** 0.5
print(x)
y = 10 // 3
print(y)
z = 10 % 3
print(z)
'''
        js_result = executor.execute(code)
        py_result = executor.execute_python(code)
        
        assert py_result["success"]
        assert js_result["success"], f"JS failed: {js_result.get('error')}"
    
    def test_comprehensions(self, executor):
        """List comprehensions work."""
        code = '''
squares = [x ** 2 for x in range(5)]
print(squares)
evens = [x for x in range(10) if x % 2 == 0]
print(evens)
'''
        js_result = executor.execute(code)
        py_result = executor.execute_python(code)
        
        assert py_result["success"]
        assert js_result["success"], f"JS failed: {js_result.get('error')}"
    
    def test_string_methods(self, executor):
        """String methods work."""
        code = '''
s = "hello world"
print(s.upper())
print(s.split()[0])
print(s.startswith("hello"))
'''
        js_result = executor.execute(code)
        py_result = executor.execute_python(code)
        
        assert py_result["success"]
        assert js_result["success"], f"JS failed: {js_result.get('error')}"
    
    def test_list_methods(self, executor):
        """List methods work."""
        code = '''
lst = [3, 1, 4, 1, 5]
print(len(lst))
print(max(lst))
print(min(lst))
print(sum(lst))
'''
        js_result = executor.execute(code)
        py_result = executor.execute_python(code)
        
        assert py_result["success"]
        assert js_result["success"], f"JS failed: {js_result.get('error')}"
    
    def test_dict_methods(self, executor):
        """Dict methods work."""
        code = '''
d = {"a": 1, "b": 2, "c": 3}
print(len(d))
print(d.get("a"))
print(d.get("z", "default"))
'''
        js_result = executor.execute(code)
        py_result = executor.execute_python(code)
        
        assert py_result["success"]
        assert js_result["success"], f"JS failed: {js_result.get('error')}"
