/**
 * PyNext Transpiler - Type Methods Index
 * 
 * =============================================================================
 * WHAT THIS FILE DOES
 * =============================================================================
 * 
 * Exports all Python type method helpers as a unified namespace.
 * This allows the runtime to access type methods via:
 * 
 *   __py.str.split(s)
 *   __py.list.remove(items, x)
 *   __py.dict.pop(d, "key")
 *   __py.set.remove(s, x)
 * 
 * =============================================================================
 * USAGE
 * =============================================================================
 * 
 * Import in core.js or directly:
 * 
 *   import { str, list, dict, set } from './types/index.js';
 */

import str from './string.js';
import list from './list.js';
import dict from './dict.js';
import set from './set.js';

export { str, list, dict, set };

export default { str, list, dict, set };
