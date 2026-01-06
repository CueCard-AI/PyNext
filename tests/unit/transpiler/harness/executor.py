"""
Phase 33.1: Transpiler Test Harness

Reusable harness for unit testing Python-to-JavaScript transpilation.
"""

import subprocess
import tempfile
import os
import json
import re
from pathlib import Path
from pynext.transpiler import transpile
from pynext.transpiler.runtime_loader import get_test_runtime


class MiniAppHarness:
    """Harness for testing mini applications as unit tests."""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        # Use shared runtime loader (fixes Segment 7 - includes dunders.js)
        self.runtime_helpers = get_test_runtime(include_dunders=True)
    
    def _fix_class_instantiation(self, js_code: str) -> str:
        """Fix class instantiation to add 'new' keyword."""
        processed_js = js_code
        class_names = []
        class_def_regex = re.compile(r'class\s+([A-Za-z_][A-Za-z0-9_]*)')
        for match in class_def_regex.finditer(js_code):
            class_names.append(match.group(1))
        
        for class_name in class_names:
            # Pattern 1: let/const/var name = ClassName(
            pattern1 = re.compile(r'(let|const|var)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*' + re.escape(class_name) + r'\s*\(')
            processed_js = pattern1.sub(r'\1 \2 = new ' + class_name + '(', processed_js)
            
            # Pattern 2: Standalone call at start of statement (after semicolon or newline)
            pattern2 = re.compile(r'([;\n])\s*' + re.escape(class_name) + r'\s*\(')
            processed_js = pattern2.sub(r'\1 new ' + class_name + '(', processed_js)
            
            # Pattern 3: Inside method calls: .method(ClassName( or .method(ClassName(
            # This handles cases like: this.todos.append(Todo(title))
            pattern3 = re.compile(r'(\w+\s*\([^)]*|\.\w+\s*\()([^,)]*)\b' + re.escape(class_name) + r'\s*\(')
            # More robust: find ClassName( that's not already prefixed with 'new'
            pattern3 = re.compile(r'(?<!new\s)\b' + re.escape(class_name) + r'\s*\(')
            processed_js = pattern3.sub('new ' + class_name + '(', processed_js)
        
        return processed_js
    
    def run_mini_app(self, python_code: str) -> dict:
        """Run a mini application in both Python and JavaScript."""
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
        processed_js = self._fix_class_instantiation(js_code)
        
        transpiled_file = os.path.join(self.temp_dir, "transpiled.js")
        with open(transpiled_file, "w") as f:
            f.write(processed_js)
        
        runtime_file = os.path.join(self.temp_dir, "runtime.js")
        runtime_code = self.runtime_helpers.replace('module.exports = __py;', '// module.exports removed')
        with open(runtime_file, "w") as f:
            f.write(runtime_code)
        
        transpiled_file_abs = os.path.abspath(transpiled_file)
        runtime_file_abs = os.path.abspath(runtime_file)
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

const fs = require('fs');
const runtimeFile = {runtime_file_js};
const runtimeCode = fs.readFileSync(runtimeFile, 'utf8');
eval(runtimeCode);

if (typeof __py_classes === 'undefined') {{
    if (typeof applyMixins !== 'undefined') {{
        global.__py_classes = {{ applyMixins, createProperty, checkAbstract }};
    }} else {{
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
    const fs = require('fs');
    const transpiledFile = {transpiled_file_js};
    const transpiledCode = fs.readFileSync(transpiledFile, 'utf8');
    eval(transpiledCode);
    
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
        
        # Parse JavaScript output
        js_stdout = js_result.stdout
        js_stderr = js_result.stderr
        js_output_lines = []
        js_success = js_result.returncode == 0
        
        try:
            all_output = (js_stdout + "\n" + js_stderr).strip()
            lines = all_output.split("\n")
            
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
                    if not json_found and line and not line.startswith("{"):
                        js_output_lines.insert(0, line)
        except Exception:
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

