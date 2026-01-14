/**
 * PyNext Transpiler Runtime - Complete Bundle Entry Point
 * 
 * =============================================================================
 * WHAT THIS FILE DOES
 * =============================================================================
 * 
 * Exports all transpiler runtime modules as a unified entry point.
 * Used for bundle analysis to measure the total size of a "full" PyNext app
 * that uses all Python-to-JavaScript semantics features.
 * 
 * =============================================================================
 * WHY THIS EXISTS
 * =============================================================================
 * 
 * Bundle analysis tools (esbuild, rollup) need an entry point that imports
 * all modules to accurately measure:
 * 
 * 1. Total bundle size (minified + gzipped)
 * 2. Per-module contribution to bundle
 * 3. Tree-shaking effectiveness
 * 
 * =============================================================================
 * SIZE BUDGET
 * =============================================================================
 * 
 * Target: < 8KB gzipped for full runtime
 * 
 * Individual targets:
 * - core.js: < 2KB (essential Python semantics)
 * - dunders.js: < 1KB (operator overloading)
 * - errors.js: < 1KB (exception classes)
 * - types/*: < 2KB (string/list/dict/set methods)
 * - stdlib/*: < 2KB (json/math/re/random)
 * 
 * =============================================================================
 * USAGE
 * =============================================================================
 * 
 * This file is NOT meant to be imported directly in production code.
 * Production code should import only what it needs:
 * 
 *   // Good: Import only what you use
 *   import { at, slice, bool } from './core.js';
 * 
 *   // Bad: Import everything (defeats tree-shaking)
 *   import * as runtime from './index.js';
 * 
 * This file is used by:
 * - scripts/analyze-bundle.js (bundle size CI checks)
 * - Tests that need the complete runtime
 */

// =============================================================================
// Core Python Semantics
// =============================================================================

export * from './core.js';

// =============================================================================
// Dunder Method Helpers
// =============================================================================

export * from './dunders.js';

// =============================================================================
// Python Exception Classes
// =============================================================================

export * from './errors.js';

// =============================================================================
// Built-in Functions
// =============================================================================

export * from './builtins.js';

// =============================================================================
// Generator Support
// =============================================================================

export * from './generators.js';

// =============================================================================
// Async/Await Support
// =============================================================================

export * from './async.js';

// =============================================================================
// Class Helpers
// =============================================================================

export * from './classes.js';

// =============================================================================
// Decorator Support
// =============================================================================

export * from './decorators.js';

// =============================================================================
// Proxy Wrappers
// =============================================================================

export * from './proxy.js';

// =============================================================================
// Type Method Helpers (str, list, dict, set)
// =============================================================================

export * from './types/index.js';

// =============================================================================
// Standard Library (json, math, re, random)
// =============================================================================

export * as stdlib from './stdlib/index.js';

