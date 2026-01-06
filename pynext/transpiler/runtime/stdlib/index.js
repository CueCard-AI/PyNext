/**
 * PyNext Standard Library - Index
 * 
 * =============================================================================
 * WHAT THIS FILE DOES
 * =============================================================================
 * 
 * Exports all standard library modules for the PyNext transpiler runtime.
 * Each module provides JavaScript implementations of Python stdlib functions.
 * 
 * =============================================================================
 * WHO USES THIS
 * =============================================================================
 * 
 * - core.js imports this to expose stdlib under __py namespace
 * - Transpiled code calls __py.json.*, __py.re.*, etc.
 * 
 * =============================================================================
 * MODULES
 * =============================================================================
 * 
 * - json: loads, dumps
 * - math: Mathematical functions and constants
 * - re: Regular expression operations
 * - random: Random number generation
 */

import * as json from './json.js';
import * as math from './math.js';
import * as re from './re.js';
import * as random from './random.js';

export { json, math, re, random };
export default { json, math, re, random };
