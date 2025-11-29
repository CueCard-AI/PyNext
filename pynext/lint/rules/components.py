"""
PyNext Linting - Component Rules

Rules for proper component structure:
    PNX003: Missing component return - function doesn't return element

Why These Rules:
    Components must return HTML elements. A component
    that doesn't return anything renders nothing.
"""

from __future__ import annotations

import ast
from typing import List, Set

from pynext.lint.rules.base import BaseLinter, LintError


class ComponentLinter(BaseLinter):
    """
    Lint component structure in PyNext code.
    
    Checks for:
    - PNX003: Component function missing return statement
    """
    
    def check(
        self,
        source: str,
        filename: str,
        enabled_rules: Set[str],
    ) -> List[LintError]:
        """Check source for component issues."""
        self.errors = []
        self.filename = filename
        self.source = source
        self.enabled_rules = enabled_rules
        
        tree = self.parse_source(source)
        if tree is None:
            return self.errors
        
        # Find decorated functions and functions that look like components
        component_decorators = {"component", "page", "layout", "loading", "error", "not_found"}
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if it has a component decorator
                is_component = any(
                    (isinstance(d, ast.Name) and d.id in component_decorators) or
                    (isinstance(d, ast.Call) and isinstance(d.func, ast.Name) and d.func.id in component_decorators)
                    for d in node.decorator_list
                )
                
                # Also check if name suggests it's a component (PascalCase)
                if not is_component and node.name[0].isupper():
                    is_component = True
                
                if is_component:
                    self._check_component_return(node)
        
        return self.errors
    
    def _check_component_return(self, func: ast.FunctionDef) -> None:
        """Check that component has a return statement."""
        has_return = False
        returns_element = False
        
        for node in ast.walk(func):
            if isinstance(node, ast.Return):
                has_return = True
                
                if node.value is not None:
                    # Check if return value looks like an element
                    # Elements are usually function calls (div(), span(), etc.)
                    # or subscript expressions (div()["text"])
                    if isinstance(node.value, (ast.Call, ast.Subscript)):
                        returns_element = True
                    # Or it could be a variable that holds an element
                    elif isinstance(node.value, ast.Name):
                        returns_element = True  # Assume it's valid
        
        if not has_return:
            self.add_error(
                "PNX003",
                f"Component '{func.name}' doesn't return anything. "
                f"Add a return statement with an HTML element.",
                func.lineno,
                func.col_offset,
                "error",
                fix=f"    return div()['{func.name} content']",
                fix_description="Add a return statement",
            )
        elif not returns_element:
            # Has return but returns None or non-element
            self.add_error(
                "PNX003",
                f"Component '{func.name}' returns None or non-element. "
                f"Return an HTML element like div(), span(), etc.",
                func.lineno,
                func.col_offset,
                "error",
            )
    
    @staticmethod
    def explain(rule_id: str) -> str:
        """Get detailed explanation for PNX003."""
        if rule_id == "PNX003":
            return """
## PNX003: Missing Component Return

A component function doesn't return an HTML element.

### Bad:
```python
@component
def MyComponent():
    name = "Hello"
    # Oops! Forgot to return
```

```python
@component
def MyComponent():
    return None  # Returns nothing visible
```

### Good:
```python
@component
def MyComponent():
    name = "Hello"
    return div()[name]  # Returns an element
```

### Why This Matters:
- Components must return HTML elements
- Forgetting to return is a common mistake
- The component will render nothing
- Often leads to blank pages

### How to Fix:
- Add a return statement with an HTML element
- Common elements: div(), span(), p(), h1(), etc.
- You can return any PyNext element or component

### Example Fix:
```python
@component
def MyComponent():
    name = "Hello"
    return div(class_="greeting")[
        h1()["Welcome"],
        p()[name]
    ]
```
"""
        return f"No detailed explanation for {rule_id}"

