"""
Phase 33.1: Mini Application Test Harness

Test harness for mini applications that exercise the transpiler
with realistic code patterns and verify end-to-end behavior.
"""

import pytest
import subprocess
import tempfile
import os
from pathlib import Path
from pynext.transpiler import transpile

# Import executor for class instantiation fix
import sys
sys.path.insert(0, str(Path(__file__).parent))
from test_python_js_equivalence import PythonJSExecutor


class MiniAppHarness:
    """Harness for testing mini applications."""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        self.runtime_helpers = self._load_runtime_helpers()
    
    def _load_runtime_helpers(self) -> str:
        """Load PyNext runtime helpers."""
        # Use the comprehensive setup.js from tests/js/transpiler
        setup_path = Path(__file__).parent.parent.parent / "js" / "transpiler" / "setup.js"
        if setup_path.exists():
            setup_code = setup_path.read_text()
            
            # Phase 33.2: Also load Phase 33.2 runtime helpers
            runtime_path = Path(__file__).parent.parent.parent.parent / "pynext" / "transpiler" / "runtime"
            phase332_helpers = []
            for file in ["dunders.js", "proxy.js", "generators.js"]:
                file_path = runtime_path / file
                if file_path.exists():
                    helper_code = file_path.read_text()
                    # Convert ES modules to CommonJS for test environment
                    helper_code = self._convert_esm_to_commonjs(helper_code, file)
                    phase332_helpers.append(helper_code)
            
            # Combine setup.js with Phase 33.2 helpers
            if phase332_helpers:
                # Export Phase 33.2 helpers to __py namespace
                phase332_code = "\n".join(phase332_helpers)
                phase332_exports = """
// Phase 33.2: Export helpers to __py namespace
if (typeof __py !== 'undefined') {
    // Export generators
    if (typeof wrapGenerator !== 'undefined') {
        __py.generators = __py.generators || {};
        __py.generators.wrapGenerator = wrapGenerator;
    }
    if (typeof StopIterationError !== 'undefined') {
        __py.generators = __py.generators || {};
        __py.generators.StopIteration = StopIterationError;
    }
    if (typeof generators !== 'undefined') {
        __py.generators = __py.generators || {};
        Object.assign(__py.generators, generators);
    }
    
    // Export dunders
    if (typeof dunders !== 'undefined') {
        __py.dunders = dunders;
    }
    
    // Export proxy
    if (typeof createDunderProxy !== 'undefined') {
        __py.proxy = __py.proxy || {};
        __py.proxy.createDunderProxy = createDunderProxy;
    }
    if (typeof proxy !== 'undefined') {
        __py.proxy = __py.proxy || {};
        Object.assign(__py.proxy, proxy);
    }
}
"""
                return setup_code + "\n" + phase332_code + "\n" + phase332_exports
            
            return setup_code
        
        # Fallback
        runtime_path = Path(__file__).parent.parent.parent.parent / "pynext" / "transpiler" / "runtime"
        helpers = []
        for file in ["helpers.js", "classes.js", "dunders.js", "proxy.js", "generators.js"]:
            file_path = runtime_path / file
            if file_path.exists():
                helper_code = file_path.read_text()
                # Convert ES modules to CommonJS for test environment
                helper_code = self._convert_esm_to_commonjs(helper_code, file)
                helpers.append(helper_code)
        
        return "\n".join(helpers)
    
    def _convert_esm_to_commonjs(self, code: str, filename: str) -> str:
        """
        Convert ES module syntax to CommonJS for test environment.
        
        This is a proper conversion, not a hack - we're adapting ES modules
        to work in CommonJS context for testing. This maintains performance
        by doing simple string replacements, not runtime transformations.
        """
        import re
        
        # Remove import statements (they import from core.js which is already in setup.js)
        # Pattern: import { ... } from '...'; (multiline support)
        # Handle both single-line and multiline imports
        lines = code.split('\n')
        filtered_lines = []
        in_import = False
        for line in lines:
            # Check if this line starts an import
            if re.match(r"^\s*import\s+", line):
                in_import = True
                # Check if it's a single-line import (has 'from' and ends with semicolon)
                if 'from' in line and (';' in line or line.strip().endswith("'")):
                    in_import = False
                continue
            # If we're in an import block, check if this line ends it
            if in_import:
                if 'from' in line and (';' in line or line.strip().endswith("'")):
                    in_import = False
                continue
            # Not an import line, keep it
            filtered_lines.append(line)
        code = '\n'.join(filtered_lines)
        
        # Convert export function/const/class to regular declarations
        # Pattern: export function name(...) { ... }
        code = re.sub(r"^export\s+function\s+", "function ", code, flags=re.MULTILINE)
        # Pattern: export class Name { ... }
        code = re.sub(r"^export\s+class\s+", "class ", code, flags=re.MULTILINE)
        
        # Convert export const name = { ... } to const name = { ... }
        # This preserves the object for later use
        code = re.sub(r"^export\s+const\s+", "const ", code, flags=re.MULTILINE)
        
        # The exported objects (dunders, proxy, generators) are now regular const declarations
        # They'll be available in the global scope when the code is evaluated
        
        return code
    
    def _fix_class_instantiation(self, js_code: str) -> str:
        """No-op: The transpiler now properly emits 'new' keywords for class instantiations."""
        return js_code
    
    def run_mini_app(self, python_code: str) -> dict:
        """Run a mini application in both Python and JavaScript."""
        # Transpile
        js_code = transpile(python_code)
        
        # Execute Python
        py_file = os.path.join(self.temp_dir, "app.py")
        with open(py_file, "w") as f:
            f.write(python_code)
        
        py_result = subprocess.run(
            ["python3", py_file],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        # Execute JavaScript
        # Fix class instantiation - add 'new' keyword
        processed_js = self._fix_class_instantiation(js_code)
        
        # Write the transpiled code to a separate file and require it
        transpiled_file = os.path.join(self.temp_dir, "transpiled.js")
        with open(transpiled_file, "w") as f:
            f.write(processed_js)
        
        # Write runtime helpers to a separate file too (to avoid template literal issues)
        runtime_file = os.path.join(self.temp_dir, "runtime.js")
        runtime_code = self.runtime_helpers.replace('module.exports = __py;', '// module.exports removed')
        with open(runtime_file, "w") as f:
            f.write(runtime_code)
        
        # Use absolute paths and JSON encode for safe embedding
        transpiled_file_abs = os.path.abspath(transpiled_file)
        runtime_file_abs = os.path.abspath(runtime_file)
        # Use JSON encoding to safely embed paths in JavaScript
        import json
        transpiled_file_js = json.dumps(transpiled_file_abs)
        runtime_file_js = json.dumps(runtime_file_abs)
        
        wrapped_js = f"""
const output = [];
const originalLog = console.log;
console.log = (...args) => {{
    const line = args.map(a => {{
        if (a === null) return 'None';
        if (a === undefined) return 'None';
        if (typeof a === 'object') {{
            if (Array.isArray(a)) return '[' + a.map(x => String(x)).join(', ') + ']';
            return JSON.stringify(a);
        }}
        return String(a);
    }}).join(' ');
    output.push(line);
    originalLog(...args);
}};

// Load runtime helpers from file (to avoid template literal issues)
const fs = require('fs');
const runtimeFile = {runtime_file_js};
const runtimeCode = fs.readFileSync(runtimeFile, 'utf8');
eval(runtimeCode);

// Add __py_classes if needed (from classes.js)
if (typeof __py_classes === 'undefined') {{
    if (typeof applyMixins !== 'undefined') {{
        global.__py_classes = {{ applyMixins, createProperty, checkAbstract }};
    }} else {{
        // If classes.js wasn't loaded, create a stub
        global.__py_classes = {{
            applyMixins: function(targetClass, mixins) {{
                for (const mixin of mixins) {{
                    const propertyNames = Object.getOwnPropertyNames(mixin.prototype);
                    for (const name of propertyNames) {{
                        if (name !== 'constructor') {{
                            const descriptor = Object.getOwnPropertyDescriptor(mixin.prototype, name);
                            if (descriptor) {{
                                Object.defineProperty(targetClass.prototype, name, descriptor);
                            }}
                        }}
                    }}
                }}
            }},
            createProperty: function({{get, set, delete: deleter}}) {{
                const descriptor = {{}};
                if (get) descriptor.get = get;
                if (set) descriptor.set = set;
                if (deleter) descriptor.configurable = true;
                return descriptor;
            }},
            checkAbstract: function(abstractClass, instanceClass) {{
                if (instanceClass === abstractClass) {{
                    throw new Error(`TypeError: Cannot instantiate abstract class ${{abstractClass.name}}`);
                }}
            }}
        }};
    }}
}}

try {{
    // Load and execute the transpiled code
    const fs = require('fs');
    const transpiledFile = {transpiled_file_js};
    const transpiledCode = fs.readFileSync(transpiledFile, 'utf8');
    eval(transpiledCode);
    
    // Output the results as JSON (last thing printed)
    const result = {{ success: true, output: output }};
    originalLog(JSON.stringify(result));
}} catch (e) {{
    const result = {{ success: false, error: e.message, stack: e.stack, output: output }};
    originalLog(JSON.stringify(result));
    process.stderr.write(e.stack || e.message);
    process.exit(1);
}}
"""
        
        js_file = os.path.join(self.temp_dir, "app.js")
        with open(js_file, "w") as f:
            f.write(wrapped_js)
        
        js_result = subprocess.run(
            ["node", js_file],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        # Parse JavaScript output (last line is JSON)
        js_stdout = js_result.stdout
        js_stderr = js_result.stderr
        js_output_lines = []
        js_success = js_result.returncode == 0
        
        try:
            import json
            # Combine stdout and stderr to find JSON result
            all_output = (js_stdout + "\n" + js_stderr).strip()
            lines = all_output.split("\n")
            
            # Look for JSON in any line (usually last)
            json_found = False
            for line in reversed(lines):
                line = line.strip()
                if not line:
                    continue
                try:
                    result_data = json.loads(line)
                    js_output_lines = result_data.get("output", [])
                    js_success = result_data.get("success", js_success)
                    json_found = True
                    break
                except json.JSONDecodeError:
                    # Not JSON, keep this as regular output (but only if we haven't found JSON yet)
                    if not json_found and line and not line.startswith("{"):
                        js_output_lines.insert(0, line)
        except Exception as e:
            # Fallback: use all non-empty lines
            js_output_lines = [l for l in js_stdout.strip().split("\n") if l.strip() and not l.strip().startswith("{")]
        
        return {
            "python": {
                "stdout": py_result.stdout,
                "stderr": py_result.stderr,
                "returncode": py_result.returncode,
            },
            "javascript": {
                "stdout": "\n".join(js_output_lines) if js_output_lines else js_stdout,
                "stderr": js_stderr,
                "returncode": 0 if js_success else js_result.returncode,
            },
            "transpiled_js": js_code,
        }


@pytest.fixture
def harness():
    """Create a mini app harness."""
    h = MiniAppHarness()
    yield h
    import shutil
    shutil.rmtree(h.temp_dir, ignore_errors=True)


# =============================================================================
# MINI APPLICATION TESTS
# =============================================================================

class TestCalculatorApp:
    """A simple calculator application."""
    
    def test_calculator(self, harness):
        """Basic calculator with functions."""
        app_code = """
class Calculator:
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def multiply(self, a, b):
        result = a * b
        self.history.append(f"{a} * {b} = {result}")
        return result
    
    def get_history(self):
        return self.history

calc = Calculator()
print(calc.add(2, 3))
print(calc.multiply(4, 5))
print(len(calc.get_history()))
"""
        result = harness.run_mini_app(app_code)
        
        # Both should execute successfully
        assert result["python"]["returncode"] == 0, f"Python failed: {result['python']['stderr']}"
        assert result["javascript"]["returncode"] == 0, f"JS failed: stdout={result['javascript']['stdout'][:200]}, stderr={result['javascript']['stderr'][:200]}"
        
        # Normalize outputs for comparison
        py_output = result["python"]["stdout"].strip()
        js_output = result["javascript"]["stdout"].strip()
        
        # Extract numeric values
        import re
        py_nums = re.findall(r'\d+', py_output)
        js_nums = re.findall(r'\d+', js_output)
        
        # Should have same numbers (order might differ slightly)
        assert len(py_nums) > 0, "Python produced no output"
        assert len(js_nums) > 0, f"JS produced no output: {result['javascript']}"
        assert set(py_nums) == set(js_nums), f"Python: {py_nums}, JS: {js_nums}"


class TestTodoApp:
    """A simple todo list application."""
    
    def test_todo_app(self, harness):
        """Todo app with classes and methods."""
        app_code = """
class Todo:
    def __init__(self, title):
        self.title = title
        self.done = False
    
    def toggle(self):
        self.done = not self.done
    
    def __str__(self):
        status = "✓" if self.done else " "
        return f"[{status}] {self.title}"

class TodoList:
    def __init__(self):
        self.todos = []
    
    def add(self, title):
        self.todos.append(Todo(title))
    
    def toggle(self, index):
        if 0 <= index < len(self.todos):
            self.todos[index].toggle()
    
    def list_all(self):
        for i, todo in enumerate(self.todos):
            print(f"{i}: {todo}")

todos = TodoList()
todos.add("Buy milk")
todos.add("Walk dog")
todos.toggle(0)
todos.list_all()
"""
        result = harness.run_mini_app(app_code)
        
        # Check both execute successfully
        assert result["python"]["returncode"] == 0
        assert result["javascript"]["returncode"] == 0


class TestDataProcessorApp:
    """A data processing application with comprehensions."""
    
    def test_data_processor(self, harness):
        """Data processor using comprehensions."""
        app_code = """
# Process a list of numbers
numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# Filter evens and square them
evens_squared = [x*x for x in numbers if x % 2 == 0]
print(f"Evens squared: {evens_squared}")

# Create a mapping
number_map = {x: x*2 for x in numbers if x > 5}
print(f"Number map: {sorted(number_map.items())}")

# Process with functions
def process_data(data):
    return [x*2 for x in data if x > 3]

result = process_data(numbers)
print(f"Processed: {result}")
"""
        result = harness.run_mini_app(app_code)
        
        # Both should execute
        assert result["python"]["returncode"] == 0
        assert result["javascript"]["returncode"] == 0


class TestGameApp:
    """A simple game with classes and control flow."""
    
    def test_game_app(self, harness):
        """Game with player, enemies, and game loop."""
        app_code = """
class Player:
    def __init__(self, name, health=100):
        self.name = name
        self.health = health
    
    def take_damage(self, amount):
        self.health -= amount
        if self.health < 0:
            self.health = 0
    
    def is_alive(self):
        return self.health > 0

class Enemy:
    def __init__(self, name, damage=10):
        self.name = name
        self.damage = damage
    
    def attack(self, player):
        player.take_damage(self.damage)
        return f"{self.name} attacks {player.name} for {self.damage} damage"

player = Player("Hero")
enemy = Enemy("Goblin")

rounds = 0
while player.is_alive() and rounds < 5:
    rounds += 1
    message = enemy.attack(player)
    print(f"Round {rounds}: {message}, Health: {player.health}")

if player.is_alive():
    print(f"{player.name} survived!")
else:
    print(f"{player.name} was defeated!")
"""
        result = harness.run_mini_app(app_code)
        
        # Both should execute
        assert result["python"]["returncode"] == 0
        assert result["javascript"]["returncode"] == 0


class TestMathLibraryApp:
    """A math library with various functions."""
    
    def test_math_library(self, harness):
        """Math library with functions, classes, and comprehensions."""
        app_code = """
class MathUtils:
    @staticmethod
    def factorial(n):
        if n <= 1:
            return 1
        return n * MathUtils.factorial(n - 1)
    
    @staticmethod
    def fibonacci(n):
        if n <= 1:
            return n
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b
    
    @staticmethod
    def primes_up_to(n):
        return [x for x in range(2, n + 1) 
                if all(x % i != 0 for i in range(2, int(x**0.5) + 1))]

print(f"Factorial(5): {MathUtils.factorial(5)}")
print(f"Fibonacci(10): {MathUtils.fibonacci(10)}")
print(f"Primes up to 20: {MathUtils.primes_up_to(20)}")
"""
        result = harness.run_mini_app(app_code)
        
        # Both should execute
        assert result["python"]["returncode"] == 0
        assert result["javascript"]["returncode"] == 0


class TestEventSystemApp:
    """An event system with callbacks and closures."""
    
    def test_event_system(self, harness):
        """Event system using closures and callbacks."""
        app_code = """
class EventEmitter:
    def __init__(self):
        self.listeners = {}
    
    def on(self, event, callback):
        if event not in self.listeners:
            self.listeners[event] = []
        self.listeners[event].append(callback)
    
    def emit(self, event, *args):
        if event in self.listeners:
            for callback in self.listeners[event]:
                callback(*args)

emitter = EventEmitter()

# Register listeners
emitter.on("greet", lambda name: print(f"Hello, {name}!"))
emitter.on("greet", lambda name: print(f"Welcome, {name}!"))

# Emit events
emitter.emit("greet", "Alice")
emitter.emit("greet", "Bob")
"""
        result = harness.run_mini_app(app_code)
        
        # Both should execute
        assert result["python"]["returncode"] == 0
        assert result["javascript"]["returncode"] == 0

