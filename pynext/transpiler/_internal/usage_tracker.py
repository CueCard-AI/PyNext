"""
PyNext Transpiler - Runtime Usage Tracking

=============================================================================
WHO: Transpiler developers, bundle size optimizers
=============================================================================

=============================================================================
WHAT THIS FILE DOES
=============================================================================

Tracks which runtime features are used during transpilation.
This information is used to:
1. Generate minimal import statements
2. Enable tree-shaking of unused code
3. Produce bundle size reports

=============================================================================
WHEN: During transpilation, as features are emitted
=============================================================================

=============================================================================
WHERE: Called by emitter.py when runtime helpers are used
=============================================================================

=============================================================================
WHY THIS EXISTS (Problem It Solves)
=============================================================================

Without usage tracking, we must include the entire runtime (~13KB).
With usage tracking, we can:
1. Only include used features
2. Generate per-file manifests
3. Enable smarter bundling

Example:
    # This code only uses 'at' and 'bool' from Layer 0
    items = [1, 2, 3]
    if items:
        last = items[-1]
    
    # Manifest: { "layer0": ["at", "bool"], "layer1": [], "stdlib": [] }
    # Bundle: Only ~500B instead of 13KB

=============================================================================
HOW IT WORKS
=============================================================================

1. During transpilation, call tracker.record("at") when emitting __py.at()
2. After transpilation, call tracker.get_manifest() for feature list
3. Use manifest to generate optimal imports or bundle

=============================================================================
LAYER CLASSIFICATION
=============================================================================

Layer 0 (Essential, ~500B):
    - at, slice, bool, eq, mod, floordiv, range, len

Layer 1 (Common, ~1KB):
    - str.*: split, replace, count, index, strip, etc.
    - list.*: remove, insert, index, sort, etc.
    - dict.*: get, pop, setdefault, update, etc.

Layer 2 (Extended, ~2KB):
    - errors: ValueError, TypeError, etc.
    - dunders: __add__, __eq__, etc.
    - generators: wrapGenerator, etc.

Layer 3 (Stdlib, varies):
    - json, math, re, random

=============================================================================
EXAMPLES
=============================================================================

```python
from pynext.transpiler._internal.usage_tracker import UsageTracker

tracker = UsageTracker()

# During transpilation:
tracker.record("at")           # items[-1]
tracker.record("bool")         # if items:
tracker.record("str.split")    # s.split()

# After transpilation:
manifest = tracker.get_manifest()
# {
#     "layer0": ["at", "bool"],
#     "layer1": ["str.split"],
#     "layer2": [],
#     "stdlib": []
# }

# Use manifest for imports:
if manifest["layer0"]:
    emit: import { at, bool } from '@pynext/runtime/core-minimal';
```
"""

from __future__ import annotations
from typing import Dict, Set, List, Optional, FrozenSet
from dataclasses import dataclass, field


# =============================================================================
# LAYER DEFINITIONS
# =============================================================================

# Layer 0: Essential functions (~500B)
LAYER_0_FEATURES: FrozenSet[str] = frozenset({
    "at", "slice", "bool", "eq", "mod", "floordiv", "range", "len",
    "contains", "in_", "iter",
})

# Layer 1: Common type methods (~1KB)
LAYER_1_STR_FEATURES: FrozenSet[str] = frozenset({
    "str.split", "str.rsplit", "str.replace", "str.count", "str.index",
    "str.rindex", "str.strip", "str.lstrip", "str.rstrip",
    "str.startswith", "str.endswith", "str.find", "str.rfind", "str.join",
    "str.title", "str.capitalize", "str.swapcase", "str.center",
    "str.ljust", "str.rjust", "str.zfill", "str.partition", "str.rpartition",
    "str.splitlines", "str.isdigit", "str.isalpha", "str.isalnum",
    "str.isspace", "str.isupper", "str.islower", "str.istitle",
    "str.isnumeric", "str.isdecimal", "str.isidentifier", "str.expandtabs",
    "str.encode",
})

LAYER_1_LIST_FEATURES: FrozenSet[str] = frozenset({
    "list.remove", "list.insert", "list.index", "list.count", "list.sort",
    "list.copy", "list.clear", "list.extend", "list.append", "list.pop",
    "list.reverse",
})

LAYER_1_DICT_FEATURES: FrozenSet[str] = frozenset({
    "dict.get", "dict.pop", "dict.setdefault", "dict.update", "dict.keys",
    "dict.values", "dict.items", "dict.clear", "dict.copy",
})

LAYER_1_SET_FEATURES: FrozenSet[str] = frozenset({
    "set.add", "set.remove", "set.discard", "set.pop", "set.clear",
    "set.copy", "set.update", "set.union", "set.intersection",
    "set.difference", "set.symmetric_difference",
})

LAYER_1_FEATURES: FrozenSet[str] = (
    LAYER_1_STR_FEATURES | LAYER_1_LIST_FEATURES | 
    LAYER_1_DICT_FEATURES | LAYER_1_SET_FEATURES
)

# Layer 2: Extended features (~2KB)
LAYER_2_ERROR_FEATURES: FrozenSet[str] = frozenset({
    "ValueError", "TypeError", "KeyError", "IndexError", "ZeroDivisionError",
    "RuntimeError", "AttributeError", "AssertionError", "NotImplementedError",
    "StopIteration", "StopAsyncIteration",
})

LAYER_2_DUNDER_FEATURES: FrozenSet[str] = frozenset({
    "dunders.add", "dunders.sub", "dunders.mul", "dunders.truediv",
    "dunders.floordiv", "dunders.mod", "dunders.pow",
    "dunders.eq", "dunders.ne", "dunders.lt", "dunders.le",
    "dunders.gt", "dunders.ge",
    "dunders.and", "dunders.or", "dunders.xor",
    "dunders.lshift", "dunders.rshift",
})

LAYER_2_GENERATOR_FEATURES: FrozenSet[str] = frozenset({
    "wrapGenerator", "wrapAsyncGenerator", "GeneratorExit",
})

LAYER_2_FEATURES: FrozenSet[str] = (
    LAYER_2_ERROR_FEATURES | LAYER_2_DUNDER_FEATURES | LAYER_2_GENERATOR_FEATURES
)

# Layer 3: Stdlib modules (varies)
STDLIB_MODULES: FrozenSet[str] = frozenset({
    "json", "math", "re", "random", "asyncio",
})


# =============================================================================
# USAGE TRACKER
# =============================================================================

@dataclass
class UsageManifest:
    """
    Manifest of runtime features used in transpiled code.
    
    Attributes:
        layer0: Essential functions used (at, slice, bool, etc.)
        layer1: Common type methods used (str.split, list.append, etc.)
        layer2: Extended features used (errors, dunders, generators)
        stdlib: Standard library modules used (json, math, etc.)
    """
    layer0: List[str] = field(default_factory=list)
    layer1: List[str] = field(default_factory=list)
    layer2: List[str] = field(default_factory=list)
    stdlib: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, List[str]]:
        """Convert to dictionary format."""
        return {
            "layer0": self.layer0,
            "layer1": self.layer1,
            "layer2": self.layer2,
            "stdlib": self.stdlib,
        }
    
    def is_empty(self) -> bool:
        """Check if no features are used."""
        return not (self.layer0 or self.layer1 or self.layer2 or self.stdlib)
    
    def total_features(self) -> int:
        """Get total number of features used."""
        return len(self.layer0) + len(self.layer1) + len(self.layer2) + len(self.stdlib)


class UsageTracker:
    """
    Tracks runtime feature usage during transpilation.
    
    Usage:
        tracker = UsageTracker()
        
        # During transpilation:
        tracker.record("at")           # Used __py.at()
        tracker.record("str.split")    # Used __py.str.split()
        tracker.record("json")         # Imported json
        
        # After transpilation:
        manifest = tracker.get_manifest()
        print(manifest.layer0)  # ["at"]
        print(manifest.layer1)  # ["str.split"]
        print(manifest.stdlib)  # ["json"]
    """
    
    def __init__(self):
        self._features: Set[str] = set()
    
    def record(self, feature: str) -> None:
        """
        Record that a runtime feature was used.
        
        Args:
            feature: Feature name (e.g., "at", "str.split", "json")
        """
        self._features.add(feature)
    
    def record_many(self, features: List[str]) -> None:
        """Record multiple features at once."""
        self._features.update(features)
    
    def has(self, feature: str) -> bool:
        """Check if a feature was used."""
        return feature in self._features
    
    def get_features(self) -> Set[str]:
        """Get all recorded features."""
        return self._features.copy()
    
    def get_manifest(self) -> UsageManifest:
        """
        Get a manifest of all used features, categorized by layer.
        
        Returns:
            UsageManifest with features grouped by layer
        """
        manifest = UsageManifest()
        
        for feature in self._features:
            if feature in LAYER_0_FEATURES:
                manifest.layer0.append(feature)
            elif feature in LAYER_1_FEATURES:
                manifest.layer1.append(feature)
            elif feature in LAYER_2_FEATURES:
                manifest.layer2.append(feature)
            elif feature in STDLIB_MODULES:
                manifest.stdlib.append(feature)
            elif "." in feature:
                # Type method like "str.split"
                prefix = feature.split(".")[0]
                if prefix in ("str", "list", "dict", "set"):
                    manifest.layer1.append(feature)
                elif prefix == "dunders":
                    manifest.layer2.append(feature)
        
        # Sort for deterministic output
        manifest.layer0.sort()
        manifest.layer1.sort()
        manifest.layer2.sort()
        manifest.stdlib.sort()
        
        return manifest
    
    def reset(self) -> None:
        """Reset all tracking."""
        self._features.clear()
    
    def merge(self, other: "UsageTracker") -> None:
        """Merge features from another tracker."""
        self._features.update(other._features)
    
    def generate_imports(self, runtime_path: str = "@pynext/runtime") -> List[str]:
        """
        Generate JavaScript import statements based on usage.
        
        This is the key method for bundle optimization. It generates minimal
        imports based on what features were actually used during transpilation.
        
        Args:
            runtime_path: Base path for runtime imports (default: "@pynext/runtime")
        
        Returns:
            List of JavaScript import statements
        
        Example:
            If only 'at' and 'bool' were used:
                ["import { at, bool } from '@pynext/runtime/core-minimal';"]
            
            If string methods were also used:
                [
                    "import { at, bool } from '@pynext/runtime/core-minimal';",
                    "import { split, replace } from '@pynext/runtime/types/string-core';",
                ]
        """
        manifest = self.get_manifest()
        imports = []
        
        # Layer 0: Core minimal functions
        if manifest.layer0:
            features = ", ".join(sorted(manifest.layer0))
            imports.append(f"import {{ {features} }} from '{runtime_path}/core-minimal';")
        
        # Layer 1: String methods (from string-core.js)
        str_methods = [f.split(".")[1] for f in manifest.layer1 if f.startswith("str.")]
        if str_methods:
            features = ", ".join(sorted(str_methods))
            imports.append(f"import {{ {features} }} from '{runtime_path}/types/string-core';")
        
        # Layer 1: List methods
        list_methods = [f.split(".")[1] for f in manifest.layer1 if f.startswith("list.")]
        if list_methods:
            features = ", ".join(sorted(list_methods))
            imports.append(f"import {{ {features} }} from '{runtime_path}/types/list';")
        
        # Layer 1: Dict methods
        dict_methods = [f.split(".")[1] for f in manifest.layer1 if f.startswith("dict.")]
        if dict_methods:
            features = ", ".join(sorted(dict_methods))
            imports.append(f"import {{ {features} }} from '{runtime_path}/types/dict';")
        
        # Layer 1: Set methods
        set_methods = [f.split(".")[1] for f in manifest.layer1 if f.startswith("set.")]
        if set_methods:
            features = ", ".join(sorted(set_methods))
            imports.append(f"import {{ {features} }} from '{runtime_path}/types/set';")
        
        # Layer 2: Errors (from errors-factory.js for minimal, errors.js for full)
        errors = [f for f in manifest.layer2 if f in LAYER_2_ERROR_FEATURES]
        if errors:
            features = ", ".join(sorted(errors))
            imports.append(f"import {{ {features} }} from '{runtime_path}/errors-factory';")
        
        # Layer 2: Dunders
        dunder_ops = [f.split(".")[1] for f in manifest.layer2 if f.startswith("dunders.")]
        if dunder_ops:
            # Import the dunders object
            imports.append(f"import {{ dunders }} from '{runtime_path}/dunders';")
        
        # Layer 3: Stdlib modules
        for module in manifest.stdlib:
            imports.append(f"import {{ {module} }} from '{runtime_path}/stdlib/{module}';")
        
        return imports
    
    def needs_full_runtime(self) -> bool:
        """
        Check if the full runtime is needed (vs minimal imports).
        
        Returns True if:
        - Many features are used (> 10)
        - Complex features like generators are used
        - Multiple layers are needed
        
        Returns:
            True if full runtime should be imported, False for minimal imports
        """
        manifest = self.get_manifest()
        
        # If generators are used, we need full runtime
        if any(f in LAYER_2_GENERATOR_FEATURES for f in manifest.layer2):
            return True
        
        # If many features, full runtime is more efficient
        if manifest.total_features() > 10:
            return True
        
        # If using most of layer 0, might as well get full runtime
        if len(manifest.layer0) >= 6:  # 6 out of 8 core functions
            return True
        
        return False


# =============================================================================
# GLOBAL TRACKER INSTANCE
# =============================================================================

_tracker: Optional[UsageTracker] = None


def get_usage_tracker() -> UsageTracker:
    """Get the global usage tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = UsageTracker()
    return _tracker


def reset_usage_tracker() -> None:
    """Reset the global usage tracker."""
    global _tracker
    if _tracker is not None:
        _tracker.reset()
    _tracker = None


def record_usage(feature: str) -> None:
    """Record a feature usage in the global tracker."""
    get_usage_tracker().record(feature)


def get_usage_manifest() -> UsageManifest:
    """Get the manifest from the global tracker."""
    return get_usage_tracker().get_manifest()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def classify_feature(feature: str) -> str:
    """
    Classify a feature into its layer.
    
    Args:
        feature: Feature name
    
    Returns:
        Layer name ("layer0", "layer1", "layer2", "stdlib", or "unknown")
    """
    if feature in LAYER_0_FEATURES:
        return "layer0"
    elif feature in LAYER_1_FEATURES:
        return "layer1"
    elif feature in LAYER_2_FEATURES:
        return "layer2"
    elif feature in STDLIB_MODULES:
        return "stdlib"
    else:
        return "unknown"


def get_layer_size_estimate(manifest: UsageManifest) -> int:
    """
    Estimate bundle size (gzipped bytes) based on manifest.
    
    Args:
        manifest: Usage manifest
    
    Returns:
        Estimated size in bytes
    """
    size = 0
    
    # Layer 0: ~500B base, but we count per-feature
    if manifest.layer0:
        size += 500  # Base
    
    # Layer 1: ~100B per method
    size += len(manifest.layer1) * 100
    
    # Layer 2: ~200B per feature
    size += len(manifest.layer2) * 200
    
    # Stdlib: ~500B per module
    size += len(manifest.stdlib) * 500
    
    return size

