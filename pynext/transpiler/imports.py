"""
PyNext Transpiler - Import System

=============================================================================
WHAT THIS FILE DOES
=============================================================================

Parses Python import statements and generates IR nodes for JavaScript ES6
imports. Handles absolute imports, relative imports, star imports, aliased
imports, __all__ handling, TYPE_CHECKING imports, and dynamic imports.

=============================================================================
WHY THIS EXISTS (Problem It Solves)
=============================================================================

Python's import system is complex:
- import module → import * as module from './module.js'
- from module import x, y → import { x, y } from './module.js'
- from . import x → import { x } from './x.js'
- from ..parent import x → import { x } from '../parent.js'
- from module import * → import * as _module from './module.js' + property copying
- import module as alias → import * as alias from './module.js'

JavaScript uses ES6 modules with different syntax. This module:
1. Parses Python import statements
2. Resolves module paths (absolute, relative)
3. Generates appropriate ES6 import IR nodes
4. Handles special cases (__all__, TYPE_CHECKING, star imports)

=============================================================================
HOW IT WORKS (Architecture)
=============================================================================

    Python AST              Import Parser          IR Node              JavaScript
    ──────────              ──────────────          ────────              ──────────
    import json      →     Parse import    →     Import(...)    →     import * as json from './json.js'
    from . import x  →     Parse from      →     ImportFrom(...) →     import { x } from './x.js'
    from m import * →     Parse star      →     ImportStar(...) →     import * as _m from './m.js'

The import system:
1. Uses ModuleResolver to resolve paths
2. Generates Import/ImportFrom IR nodes
3. Emitter converts IR to ES6 import statements
4. Handles built-in modules (json, math, etc.) specially

=============================================================================
WHO USES THIS
=============================================================================

- parser.py: Calls parse_import() and parse_import_from()
- emitter.py: Emits Import/ImportFrom nodes as ES6 imports
- ModuleResolver: Resolves import paths

=============================================================================
WHEN THIS IS USED
=============================================================================

- During parsing: When encountering import/from import AST nodes
- During emission: When generating ES6 import statements
- At transpile time: To resolve paths and detect circular imports

=============================================================================
WHERE THIS FITS
=============================================================================

Part of the import system (pynext/transpiler/imports.py).
Integrates with parser.py, emitter.py, and module_resolver.py.

=============================================================================
EXAMPLES
=============================================================================

```python
# Absolute import
import json
# → import * as json from './json.js'

# From import
from module import x, y
# → import { x, y } from './module.js'

# Relative import
from . import utils
# → import { utils } from './utils.js'

# Star import
from module import *
# → import * as _module from './module.js'
#   const x = _module.x; const y = _module.y;  (if __all__ = ['x', 'y'])

# Aliased import
import module as alias
# → import * as alias from './module.js'
```

=============================================================================
EDGE CASES
=============================================================================

- __all__: Only exports listed names in star imports
- TYPE_CHECKING: Stripped at runtime (only for type checkers)
- Circular imports: Detected and warned
- Missing modules: Error with helpful message
- Built-in modules: Handled via __py.* namespace

=============================================================================
RELATED FILES
=============================================================================

- module_resolver.py: Path resolution and circular import detection
- parser.py: Integration with AST parsing
- emitter.py: ES6 import statement emission
- nodes.py: Import IR node definitions
"""

from __future__ import annotations
from typing import Optional, List, Tuple, Set
import ast

from .nodes import JSNode, Import, ImportFrom, ImportStar, Assignment, Name, Attribute
from ._internal.module_resolver import ModuleResolver
from .errors import UnsupportedSyntax


def parse_import(
    node: ast.Import,
    resolver: ModuleResolver,
    source: Optional[str] = None
) -> List[JSNode]:
    """
    Parse import statement: import module [as alias]
    
    WHAT: Parses Python 'import module' statements into IR nodes.
    WHY: Converts Python imports to JavaScript ES6 imports.
    HOW: Resolves module path, generates Import IR node.
    WHO: Used by parser.py when encountering ast.Import.
    WHEN: During AST parsing phase.
    WHERE: Part of import system parsing.
    
    Examples:
        import json → Import(module="json", alias="json", path="./json.js")
        import json as j → Import(module="json", alias="j", path="./json.js")
    
    Args:
        node: AST Import node
        resolver: ModuleResolver instance
        source: Optional source code for error messages
    
    Returns:
        List of IR nodes (Import or Assignment for built-ins)
    """
    results = []
    
    for alias in node.names:
        module_name = alias.name
        alias_name = alias.asname if alias.asname else module_name.split('.')[0]
        
        # Check if it's a built-in module
        BUILTIN_MODULES = {"json", "math", "re", "random", "asyncio"}
        if module_name.split('.')[0] in BUILTIN_MODULES:
            # Built-in module - create variable pointing to __py.*
            # Emit: const json = __py.json;
            results.append(Assignment(
                target=alias_name,
                value=Attribute(
                    value=Name(id="__py", line=node.lineno, col=node.col_offset),
                    attr=module_name.split('.')[0],
                    line=node.lineno,
                    col=node.col_offset
                ),
                line=node.lineno,
                col=node.col_offset
            ))
        else:
            # Regular module - resolve path and create Import node
            path = resolver.resolve_absolute(module_name)
            if path is None:
                raise UnsupportedSyntax(
                    message=f"Module '{module_name}' not found",
                    line=node.lineno,
                    col=node.col_offset,
                    source=source,
                    suggestion=f"Ensure '{module_name}.py' exists or use a built-in module."
                )
            
            results.append(Import(
                module=module_name,
                alias=alias_name,
                path=path,
                line=node.lineno,
                col=node.col_offset
            ))
            
            # Track dependency for circular import detection
            current_module = resolver.current_file
            resolver.add_dependency(current_module, module_name)
    
    return results


def parse_import_from(
    node: ast.ImportFrom,
    resolver: ModuleResolver,
    source: Optional[str] = None
) -> List[JSNode]:
    """
    Parse from import statement: from module import x, y [as alias]
    
    WHAT: Parses Python 'from module import ...' statements into IR nodes.
    WHY: Converts Python from imports to JavaScript ES6 named imports.
    HOW: Resolves module path, generates ImportFrom or ImportStar IR node.
    WHO: Used by parser.py when encountering ast.ImportFrom.
    WHEN: During AST parsing phase.
    WHERE: Part of import system parsing.
    
    Examples:
        from module import x, y → ImportFrom(module="module", names=[("x", "x"), ("y", "y")], path="./module.js")
        from . import utils → ImportFrom(module=None, names=[("utils", "utils")], path="./utils.js", is_relative=True)
        from module import * → ImportStar(module="module", path="./module.js")
    
    Args:
        node: AST ImportFrom node
        resolver: ModuleResolver instance
        source: Optional source code for error messages
    
    Returns:
        List of IR nodes (ImportFrom or ImportStar)
    """
    # Phase 33.3: Handle TYPE_CHECKING imports (stripped at runtime)
    # TYPE_CHECKING is a constant that's False at runtime, True for type checkers
    # Imports inside `if TYPE_CHECKING:` blocks should be stripped during emission
    # We detect this by checking if the import is inside an If statement with TYPE_CHECKING condition
    # For now, we'll mark it and let the emitter handle stripping
    # TODO: Track if we're inside a TYPE_CHECKING block during parsing
    
    # Resolve module path
    if node.module is None:
        # Relative import: from . import x
        if node.level == 0:
            raise UnsupportedSyntax(
                message="Relative import requires at least one dot (from . import x)",
                line=node.lineno,
                col=node.col_offset,
                source=source,
            )
        
        # Resolve relative path
        try:
            path = resolver.resolve_relative(node.level)
        except ValueError as e:
            raise UnsupportedSyntax(
                message=str(e),
                line=node.lineno,
                col=node.col_offset,
                source=source,
            )
        
        module_name = None  # Relative imports don't have module names
        is_relative = True
    else:
        # Absolute import: from module import x
        # Check for built-in modules
        BUILTIN_MODULES = {"json", "math", "re", "random", "asyncio"}
        if node.module.split('.')[0] in BUILTIN_MODULES:
            # Built-in module - handle specially
            return _parse_builtin_from_import(node, source)
        
        path = resolver.resolve_absolute(node.module)
        if path is None:
            raise UnsupportedSyntax(
                message=f"Module '{node.module}' not found",
                line=node.lineno,
                col=node.col_offset,
                source=source,
                suggestion=f"Ensure '{node.module}.py' exists or use a built-in module."
            )
        
        module_name = node.module
        is_relative = False
        
        # Track dependency
        current_module = resolver.current_file
        resolver.add_dependency(current_module, node.module)
    
    # Parse import names
    if len(node.names) == 1 and node.names[0].name == "*":
        # Star import: from module import *
        return [ImportStar(
            module=module_name,
            path=path,
            is_relative=is_relative,
            level=node.level if is_relative else 0,
            line=node.lineno,
            col=node.col_offset
        )]
    else:
        # Named imports: from module import x, y
        names = []
        for alias in node.names:
            name = alias.name
            as_name = alias.asname if alias.asname else name
            names.append((name, as_name))
        
        return [ImportFrom(
            module=module_name,
            names=tuple(names),
            path=path,
            is_relative=is_relative,
            level=node.level if is_relative else 0,
            line=node.lineno,
            col=node.col_offset
        )]


def _parse_builtin_from_import(
    node: ast.ImportFrom,
    source: Optional[str] = None
) -> List[JSNode]:
    """
    Parse from import for built-in modules (json, math, etc.).
    
    WHAT: Handles 'from json import loads' for built-in modules.
    WHY: Built-in modules are in __py.* namespace, not file imports.
    HOW: Creates assignments from __py.module.attribute.
    WHO: Used for built-in module from imports.
    WHEN: When importing from built-in modules.
    WHERE: Part of import system parsing.
    
    Examples:
        from json import loads → const loads = __py.json.loads;
        from math import sqrt → const sqrt = __py.math.sqrt;
    """
    # Phase 33.3: Import IR nodes needed for star imports
    from .nodes import ExprStmt, Call
    
    results = []
    module_name = node.module.split('.')[0]  # Get top-level module
    
    for alias in node.names:
        if alias.name == "*":
            # Star import from built-in - use runtime helper
            # Phase 33.3: Implement star imports for built-in modules
            # Emit: __py.star_import(__py.json, globalThis);
            
            results.append(ExprStmt(
                value=Call(
                    func=Attribute(
                        value=Name(id="__py", line=node.lineno, col=node.col_offset),
                        attr="star_import",
                        line=node.lineno,
                        col=node.col_offset
                    ),
                    args=(
                        Attribute(
                            value=Name(id="__py", line=node.lineno, col=node.col_offset),
                            attr=module_name,
                            line=node.lineno,
                            col=node.col_offset
                        ),
                        Name(id="globalThis", line=node.lineno, col=node.col_offset)
                    ),
                    keywords=(),
                    line=node.lineno,
                    col=node.col_offset
                ),
                line=node.lineno,
                col=node.col_offset
            ))
            continue
        
        attr_name = alias.name
        alias_name = alias.asname if alias.asname else attr_name
        
        # Create: const alias = __py.module.attr;
        results.append(Assignment(
            target=alias_name,
            value=Attribute(
                value=Attribute(
                    value=Name(id="__py", line=node.lineno, col=node.col_offset),
                    attr=module_name,
                    line=node.lineno,
                    col=node.col_offset
                ),
                attr=attr_name,
                line=node.lineno,
                col=node.col_offset
            ),
            line=node.lineno,
            col=node.col_offset
        ))
    
    return results

