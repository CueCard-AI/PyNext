/**
 * PyNext Standard Library - Index
 * 
 * =============================================================================
 * WHO: Transpiled code, bundle optimizers
 * =============================================================================
 * 
 * =============================================================================
 * WHAT THIS FILE DOES
 * =============================================================================
 * 
 * Exports all standard library modules for the PyNext transpiler runtime.
 * Each module provides JavaScript implementations of Python stdlib functions.
 * 
 * =============================================================================
 * WHEN: Imported by core.js, or dynamically when individual modules are needed
 * =============================================================================
 * 
 * =============================================================================
 * WHERE: pynext/transpiler/runtime/stdlib/
 * =============================================================================
 * 
 * =============================================================================
 * WHY: Provides Python stdlib in JavaScript
 * =============================================================================
 * 
 * Python's stdlib doesn't exist in JavaScript. These modules implement
 * common functionality:
 * - json: JSON serialization (loads, dumps)
 * - math: Mathematical functions and constants
 * - re: Regular expression operations
 * - random: Random number generation
 * 
 * =============================================================================
 * HOW: Named exports and default export for different import styles
 * =============================================================================
 * 
 * Static import (current):
 *   import { json, math } from './stdlib/index.js';
 * 
 * Dynamic import (future optimization):
 *   const json = await import('./stdlib/json.js');
 * 
 * =============================================================================
 * SIZE OPTIMIZATION
 * =============================================================================
 * 
 * Each module is designed to be standalone for tree-shaking:
 * - json.js: ~200B gzipped
 * - math.js: ~800B gzipped
 * - re.js: ~500B gzipped
 * - random.js: ~600B gzipped
 * 
 * Apps that don't use a module won't include it in the final bundle.
 * 
 * =============================================================================
 * DYNAMIC IMPORT SUPPORT
 * =============================================================================
 * 
 * For apps that want to lazy-load stdlib modules, use the lazy loaders:
 * 
 *   const json = await loadJson();
 *   const math = await loadMath();
 * 
 * These return the same modules but defer loading until needed.
 */

// Static exports (for backward compatibility and tree-shaking)
import * as json from './json.js';
import * as math from './math.js';
import * as re from './re.js';
import * as random from './random.js';

export { json, math, re, random };

// Dynamic loaders (for lazy loading - future optimization)
export async function loadJson() { return import('./json.js'); }
export async function loadMath() { return import('./math.js'); }
export async function loadRe() { return import('./re.js'); }
export async function loadRandom() { return import('./random.js'); }

export default { json, math, re, random };
