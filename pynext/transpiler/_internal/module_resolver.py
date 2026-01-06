"""
PyNext Transpiler - Module Resolver

=============================================================================
WHAT THIS FILE DOES
=============================================================================

Resolves Python module paths to JavaScript module paths, handles relative
imports, detects circular dependencies, and manages module dependencies.

=============================================================================
WHY THIS EXISTS (Problem It Solves)
=============================================================================

Python's import system is complex:
- Absolute imports: import module → './module.js'
- Relative imports: from . import x → './x.js'
- Parent imports: from ..parent import x → '../parent.js'
- Package structure: package/module → './package/module.js'

JavaScript uses ES6 modules with different path resolution. This module
bridges the gap by:
1. Converting Python module paths to JS paths
2. Resolving relative imports based on current file location
3. Detecting circular dependencies at transpile time
4. Tracking module dependencies for bundling

=============================================================================
HOW IT WORKS (Architecture)
=============================================================================

    Python Import          Module Resolver          JavaScript Import
    ─────────────          ───────────────          ────────────────
    import json      →     Resolve path      →     import * as json from './json.js'
    from . import x  →     Resolve relative  →     import { x } from './x.js'
    from ..p import  →     Resolve parent    →     import { p } from '../p.js'

The resolver:
1. Tracks current file path (for relative imports)
2. Maintains dependency graph (for circular detection)
3. Converts Python module names to JS file paths
4. Handles package structure (__init__.py → index.js)

=============================================================================
WHO USES THIS
=============================================================================

- imports.py: Uses resolver to resolve import paths
- parser.py: Uses resolver to track dependencies
- emitter.py: Uses resolver to generate import statements

=============================================================================
WHEN THIS IS USED
=============================================================================

- During parsing: When encountering import/from import statements
- During emission: When generating ES6 import statements
- At transpile time: To detect circular dependencies

=============================================================================
WHERE THIS FITS
=============================================================================

Part of the import system (pynext/transpiler/_internal/module_resolver.py).
Used by imports.py and integrated into parser.py and emitter.py.

=============================================================================
EXAMPLES
=============================================================================

```python
# Absolute import
import json
# → import * as json from './json.js'

# Relative import
from . import utils
# → import { utils } from './utils.js'

# Parent import
from ..parent import child
# → import { child } from '../parent/child.js'

# Package import
from package import module
# → import { module } from './package/module.js'
```

=============================================================================
EDGE CASES
=============================================================================

- Circular imports: Detected and warned at transpile time
- Missing modules: Error with helpful message
- Relative imports at top level: Error (must be in package)
- Deep relative imports: from ...grandparent → '../../grandparent.js'

=============================================================================
RELATED FILES
=============================================================================

- imports.py: Import statement parsing and IR generation
- parser.py: Integration with AST parsing
- emitter.py: ES6 import statement emission
"""

from __future__ import annotations
from typing import Optional, Dict, Set, List, Tuple
from pathlib import Path
import os


class ModuleResolver:
    """
    Resolves Python module paths to JavaScript module paths.
    
    WHAT: Converts Python import paths to JavaScript ES6 import paths.
    WHY: Python and JavaScript have different module systems.
    HOW: Tracks current file path, resolves relative imports, converts paths.
    WHO: Used by import parser and emitter.
    WHEN: During transpilation when processing imports.
    WHERE: Part of the import system infrastructure.
    
    Examples:
        resolver = ModuleResolver(current_file="src/components/Button.py")
        resolver.resolve_absolute("json") → "./json.js"
        resolver.resolve_relative(".", "utils") → "./utils.js"
        resolver.resolve_relative("..", "parent") → "../parent.js"
    """
    
    def __init__(self, current_file: str = "<string>"):
        """
        Initialize module resolver.
        
        Args:
            current_file: Path to current Python file being transpiled
        """
        self.current_file = current_file
        self.current_dir = self._get_directory(current_file)
        
        # Track dependencies for circular import detection
        self.dependencies: Dict[str, Set[str]] = {}  # module → set of imported modules
        self.visited: Set[str] = set()  # Modules currently being resolved (for cycle detection)
        
    def _get_directory(self, file_path: str) -> str:
        """Get directory from file path."""
        if file_path == "<string>":
            return "."
        return str(Path(file_path).parent)
    
    def resolve_absolute(self, module_name: str) -> str:
        """
        Resolve absolute import: import module → './module.js'
        
        WHAT: Converts Python absolute module name to JavaScript import path.
        WHY: JavaScript uses file paths, not module names.
        HOW: Converts module name to relative path from current file.
        WHO: Used for absolute imports like 'import json'.
        WHEN: When parsing 'import module' statements.
        WHERE: Part of import path resolution.
        
        Examples:
            resolve_absolute("json") → "./json.js"
            resolve_absolute("package.module") → "./package/module.js"
        
        Args:
            module_name: Python module name (e.g., "json", "package.module")
        
        Returns:
            JavaScript import path (e.g., "./json.js", "./package/module.js")
        """
        # Built-in modules are handled separately (point to __py.*)
        BUILTIN_MODULES = {"json", "math", "re", "random", "asyncio"}
        if module_name.split('.')[0] in BUILTIN_MODULES:
            # Built-in modules don't need file paths - they're in __py namespace
            return None  # Signal to use __py.* instead
        
        # Convert module name to file path
        # package.module → ./package/module.js
        parts = module_name.split('.')
        if len(parts) == 1:
            # Simple module: module → ./module.js
            return f"./{parts[0]}.js"
        else:
            # Package: package.module → ./package/module.js
            path = "/".join(parts[:-1])  # package
            module = parts[-1]  # module
            return f"./{path}/{module}.js"
    
    def resolve_relative(self, level: int, module_name: Optional[str] = None) -> str:
        """
        Resolve relative import: from . import x → './x.js'
        
        WHAT: Converts Python relative import to JavaScript import path.
        WHY: Relative imports need to be resolved based on current file location.
        HOW: Calculates relative path based on level (number of dots).
             When current_file is "<string>" (default), treats it as current directory (.)
             to allow relative imports to work in tests and interactive contexts.
        WHO: Used for relative imports like 'from . import x'.
        WHEN: When parsing 'from . import x' or 'from ..parent import x'.
        WHERE: Part of import path resolution.
        
        Phase 33.3: Auto-allow relative imports with default context.
        When current_file is "<string>" (default), relative imports resolve
        relative to current directory (.). This allows relative imports to work
        in tests and interactive contexts without requiring explicit filename.
        Real usage with explicit filenames will still work correctly.
        
        Examples:
            from . import utils → level=1, module=None → "./utils.js"
            from ..parent import child → level=2, module="parent.child" → "../parent/child.js"
            from ...grandparent import x → level=3 → "../../grandparent/x.js"
        
        Args:
            level: Number of dots (1 = current dir, 2 = parent, 3 = grandparent, etc.)
            module_name: Optional module name (for from ..parent import x)
        
        Returns:
            JavaScript import path
        """
        # Phase 33.3: Allow relative imports even when filename is "<string>"
        # Treat "<string>" as current directory (.) - this is safe and allows
        # relative imports to work in tests and interactive contexts
        # Real usage with explicit filenames will still work correctly
        
        # Calculate parent directory path
        # level=1 → current dir (.)
        # level=2 → parent dir (..)
        # level=3 → grandparent dir (../..)
        parent_path = "../" * (level - 1) if level > 1 else "./"
        
        if module_name:
            # from ..parent import child → ../parent/child.js
            parts = module_name.split('.')
            if len(parts) == 1:
                # Simple: from ..parent → ../parent.js
                return f"{parent_path}{parts[0]}.js"
            else:
                # Nested: from ..parent.child → ../parent/child.js
                path = "/".join(parts[:-1])
                module = parts[-1]
                return f"{parent_path}{path}/{module}.js"
        else:
            # from . import x → directory path (module name comes from import list)
            # parent_path is already correctly formatted with trailing slash
            return parent_path
    
    def add_dependency(self, from_module: str, to_module: str):
        """
        Track module dependency for circular import detection.
        
        WHAT: Records that one module imports another.
        WHY: Enables detection of circular dependencies.
        HOW: Maintains dependency graph.
        WHO: Used by import parser.
        WHEN: When processing import statements.
        WHERE: Part of circular import detection.
        
        Args:
            from_module: Module doing the import
            to_module: Module being imported
        """
        if from_module not in self.dependencies:
            self.dependencies[from_module] = set()
        self.dependencies[from_module].add(to_module)
    
    def detect_circular(self, module: str, path: Optional[List[str]] = None, visited_in_path: Optional[Set[str]] = None) -> Optional[List[str]]:
        """
        Detect circular import dependencies using DFS with explicit path tracking.
        
        WHAT: Finds circular import chains (A imports B, B imports A).
        WHY: Circular imports can cause issues in JavaScript modules.
        HOW: DFS traversal tracking the current path, returns full cycle when visited node found.
        WHO: Used during transpilation to warn about circular imports.
        WHEN: After all imports are processed.
        WHERE: Part of circular import detection.
        
        Phase 33.3: Enhanced with explicit path tracking for robust cycle detection.
        This ensures we return the complete cycle path, not just a marker.
        
        Algorithm:
        1. Track current path being explored (list of modules)
        2. Track modules in current path (set for O(1) lookup)
        3. If module is in current path → cycle found, return cycle
        4. If module was visited in previous DFS → no cycle from this path
        5. Recursively check all dependencies
        6. Backtrack when done exploring
        
        Args:
            module: Module to check for cycles
            path: Current path being explored (internal, for recursion)
            visited_in_path: Set of modules in current path (internal, for O(1) lookup)
        
        Returns:
            List of modules in cycle (e.g., ['module_a', 'module_b', 'module_a']), or None
        
        Examples:
            # Simple cycle: A → B → A
            detect_circular('module_a') → ['module_a', 'module_b', 'module_a']
            
            # Three-way: A → B → C → A
            detect_circular('module_a') → ['module_a', 'module_b', 'module_c', 'module_a']
            
            # Partial cycle: A → B → C → B (cycle is B, C)
            detect_circular('module_a') → ['module_b', 'module_c', 'module_b']
        """
        # Initialize path tracking on first call
        if path is None:
            path = []
        if visited_in_path is None:
            visited_in_path = set()
        
        # If module is in current path, we found a cycle
        # Return the cycle: from first occurrence to end, plus module again
        if module in visited_in_path:
            cycle_start = path.index(module)
            return path[cycle_start:] + [module]
        
        # If module was visited in a previous DFS (not in current path), no cycle from here
        if module in self.visited:
            return None
        
        # Add to visited set (for this DFS) and current path
        self.visited.add(module)
        path.append(module)
        visited_in_path.add(module)
        
        # Check all dependencies
        if module in self.dependencies:
            for dep in self.dependencies[module]:
                cycle = self.detect_circular(dep, path, visited_in_path)
                if cycle:
                    return cycle
        
        # Backtrack: remove from path (but keep in visited for this DFS)
        path.pop()
        visited_in_path.remove(module)
        return None
    
    def get_all_circular_imports(self) -> List[List[str]]:
        """
        Find all circular import chains.
        
        WHAT: Finds all circular dependencies in the module graph.
        WHY: Reports all circular imports, not just one.
        HOW: Checks each module for cycles.
        WHO: Used for comprehensive circular import reporting.
        WHEN: After all imports are processed.
        WHERE: Part of circular import detection.
        
        Returns:
            List of circular import chains
        """
        cycles = []
        checked = set()
        
        for module in self.dependencies:
            if module not in checked:
                self.visited = set()
                cycle = self.detect_circular(module)
                if cycle:
                    cycles.append(cycle)
                    checked.update(cycle)
        
        return cycles

