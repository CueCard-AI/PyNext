"""
PyNext Linting - Island Rules

Rules for proper island usage:
    PNX004: Invalid prop type - prop not JSON-serializable for island
    PNX005: Server import in island - importing server-only code

Why These Rules:
    Islands are hydrated on the client. Their props must be
    serializable to JSON, and they cannot import server-only code.
"""

from __future__ import annotations

import ast
from typing import List, Set

from pynext.lint.rules.base import BaseLinter, LintError


# Imports that are server-only
SERVER_ONLY_IMPORTS = {
    "os",
    "subprocess",
    "socket",
    "sqlite3",
    "psycopg2",
    "pymongo",
    "sqlalchemy",
    "asyncpg",
    "aiofiles",
    "pathlib",  # File system access
    "shutil",
    "tempfile",
    "secrets",  # Server-side secrets
}

# Types that are not JSON-serializable
NON_SERIALIZABLE_TYPES = {
    "set",
    "frozenset",
    "bytes",
    "bytearray",
    "complex",
    "function",
    "lambda",
    "type",
    "module",
    "generator",
}


class IslandLinter(BaseLinter):
    """
    Lint island components in PyNext code.
    
    Checks for:
    - PNX004: Island props that aren't JSON-serializable
    - PNX005: Server-only imports in islands
    """
    
    def check(
        self,
        source: str,
        filename: str,
        enabled_rules: Set[str],
    ) -> List[LintError]:
        """Check source for island issues."""
        self.errors = []
        self.filename = filename
        self.source = source
        self.enabled_rules = enabled_rules
        
        tree = self.parse_source(source)
        if tree is None:
            return self.errors
        
        # Check if this file contains islands
        is_island_file = False
        island_functions: List[ast.FunctionDef] = []
        imports: List[ast.Import | ast.ImportFrom] = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check for @island decorator
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name) and decorator.id == "island":
                        is_island_file = True
                        island_functions.append(node)
                    elif isinstance(decorator, ast.Call):
                        if isinstance(decorator.func, ast.Name) and decorator.func.id == "island":
                            is_island_file = True
                            island_functions.append(node)
            
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.append(node)
        
        if not is_island_file:
            return self.errors
        
        # Check imports
        self._check_imports(imports)
        
        # Check island function parameters
        for func in island_functions:
            self._check_island_params(func)
        
        return self.errors
    
    def _check_imports(self, imports: List[ast.Import | ast.ImportFrom]) -> None:
        """Check for server-only imports."""
        for node in imports:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name.split(".")[0]
                    if module_name in SERVER_ONLY_IMPORTS:
                        self.add_error(
                            "PNX005",
                            f"Server-only import '{alias.name}' in island. "
                            f"Islands run on the client and cannot access server resources.",
                            node.lineno,
                            node.col_offset,
                            "error",
                        )
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module_name = node.module.split(".")[0]
                    if module_name in SERVER_ONLY_IMPORTS:
                        self.add_error(
                            "PNX005",
                            f"Server-only import from '{node.module}' in island. "
                            f"Islands run on the client and cannot access server resources.",
                            node.lineno,
                            node.col_offset,
                            "error",
                        )
    
    def _check_island_params(self, func: ast.FunctionDef) -> None:
        """Check that island parameters are JSON-serializable types."""
        for arg in func.args.args:
            # Check type annotation if present
            if arg.annotation:
                type_name = self._get_type_name(arg.annotation)
                if type_name and type_name.lower() in NON_SERIALIZABLE_TYPES:
                    self.add_error(
                        "PNX004",
                        f"Island prop '{arg.arg}' has non-serializable type '{type_name}'. "
                        f"Island props must be JSON-serializable (str, int, float, bool, list, dict, None).",
                        arg.lineno if hasattr(arg, "lineno") else func.lineno,
                        arg.col_offset if hasattr(arg, "col_offset") else func.col_offset,
                        "error",
                    )
        
        # Check defaults for non-serializable values
        defaults = func.args.defaults
        args_with_defaults = func.args.args[-len(defaults):] if defaults else []
        
        for arg, default in zip(args_with_defaults, defaults):
            if isinstance(default, ast.Set):
                self.add_error(
                    "PNX004",
                    f"Island prop '{arg.arg}' has default value of type 'set'. "
                    f"Use a list instead: [{', '.join(ast.unparse(e) for e in default.elts)}]",
                    default.lineno,
                    default.col_offset,
                    "error",
                    fix=f"[{', '.join(ast.unparse(e) for e in default.elts)}]",
                    fix_description="Convert set to list",
                )
            elif isinstance(default, ast.Lambda):
                self.add_error(
                    "PNX004",
                    f"Island prop '{arg.arg}' has function as default value. "
                    f"Functions cannot be serialized to JSON.",
                    default.lineno,
                    default.col_offset,
                    "error",
                )
    
    def _get_type_name(self, annotation: ast.expr) -> str | None:
        """Extract type name from annotation."""
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Subscript):
            # Handle generics like List[str]
            if isinstance(annotation.value, ast.Name):
                return annotation.value.id
        elif isinstance(annotation, ast.Constant):
            return str(annotation.value)
        return None
    
    @staticmethod
    def explain(rule_id: str) -> str:
        """Get detailed explanation for island rules."""
        explanations = {
            "PNX004": """
## PNX004: Invalid Prop Type for Island

An island component has a prop with a non-JSON-serializable type.

### Bad:
```python
@island
def Counter(on_change: Callable):  # Functions can't be serialized!
    count = Signal(0)
    return button(onclick=on_change)[count()]
```

```python
@island
def TagList(tags: set = {1, 2, 3}):  # Sets can't be serialized!
    return ul()[For(tags, lambda t: li()[t])]
```

### Good:
```python
@island
def Counter(initial: int = 0):  # Numbers are fine
    count = Signal(initial)
    return button(onclick=lambda: count.set(count() + 1))[count()]
```

```python
@island
def TagList(tags: list = [1, 2, 3]):  # Use list instead of set
    return ul()[For(tags, lambda t: li()[t])]
```

### Why This Matters:
- Island props are serialized to JSON in the HTML
- JSON only supports: string, number, boolean, null, array, object
- Sets, functions, and other Python types can't be serialized
- The island won't receive the correct props

### Serializable Types:
- ✅ str, int, float, bool, None
- ✅ list (becomes JSON array)
- ✅ dict (becomes JSON object)
- ❌ set, frozenset (use list)
- ❌ bytes, bytearray
- ❌ functions, lambdas
- ❌ classes, modules
""",
            "PNX005": """
## PNX005: Server Import in Island

An island imports a server-only module.

### Bad:
```python
import os  # Server-only!
import sqlite3  # Server-only!

@island
def UserWidget(user_id: int):
    # Can't access database from client!
    db = sqlite3.connect("app.db")
    ...
```

### Good:
```python
# No server imports in island files

@island
def UserWidget(user_id: int, user_name: str):
    # Props are passed from the server
    return div()[f"Hello, {user_name}!"]
```

### Why This Matters:
- Islands are hydrated and run on the client (browser)
- Browsers don't have access to file system, databases, etc.
- Server imports will fail or cause security issues
- Use server actions to communicate with the server

### Server-Only Modules:
- os, subprocess, socket
- sqlite3, psycopg2, pymongo, sqlalchemy
- pathlib, shutil, tempfile
- secrets (for server-side secrets)

### How to Fix:
- Move server logic to a server action
- Pass data as props from the server
- Use server actions for mutations
""",
        }
        return explanations.get(rule_id, f"No detailed explanation for {rule_id}")

