/**
 * PyNext Runtime - String Methods (Core)
 * 
 * =============================================================================
 * WHO: Transpiled code using common string operations
 * =============================================================================
 * 
 * =============================================================================
 * WHAT: Most-used Python string methods (~500B gzipped)
 * =============================================================================
 * 
 * This file contains the string methods used by 80%+ of Python code.
 * Less common methods are in string-extended.js for smaller bundles.
 * 
 * Methods included:
 * - split(s, sep, maxsplit): Python's whitespace-aware split
 * - replace(s, old, new, count): Python's replace with count
 * - count(s, sub, start, end): Count substring occurrences
 * - index(s, sub, start, end): Find index or throw ValueError
 * - strip/lstrip/rstrip: Whitespace and character stripping
 * - startswith/endswith: Prefix/suffix checking
 * 
 * =============================================================================
 * WHEN: Loaded when transpiled code uses these string methods
 * =============================================================================
 * 
 * =============================================================================
 * WHERE: Part of Layer 1 (Common Type Methods)
 * =============================================================================
 * 
 * =============================================================================
 * WHY: Python string methods differ from JavaScript
 * =============================================================================
 * 
 * Key differences:
 * - split(): Python "a  b".split() → ["a", "b"], JS → ["a  b"]
 * - index(): Python throws ValueError, JS indexOf returns -1
 * - count(): Python counts non-overlapping, includes start/end bounds
 * 
 * =============================================================================
 * SIZE BUDGET: < 600 bytes gzipped
 * =============================================================================
 */

import { ValueError } from '../errors-factory.js';

// =============================================================================
// SPLIT - Critical: no-arg splits on whitespace
// =============================================================================

/**
 * Python split() with whitespace handling
 * 
 * @param {string} s - String to split
 * @param {string|null} sep - Separator (null = any whitespace)
 * @param {number} maxsplit - Max splits (-1 = no limit)
 * @returns {string[]} Array of parts
 */
export function split(s, sep = null, maxsplit = -1) {
    if (s === '') {
        return sep === null ? [] : [''];
    }
    
    if (sep === null) {
        const trimmed = s.trim();
        if (trimmed === '') return [];
        
        if (maxsplit < 0) {
            return trimmed.split(/\s+/);
        }
        
        const result = [];
        let remaining = s.trimStart();
        let count = 0;
        
        while (count < maxsplit && remaining.length > 0) {
            const match = remaining.match(/^\S+/);
            if (!match) break;
            
            result.push(match[0]);
            remaining = remaining.slice(match[0].length);
            
            const wsMatch = remaining.match(/^\s+/);
            if (wsMatch) {
                remaining = remaining.slice(wsMatch[0].length);
            }
            count++;
        }
        
        if (remaining.length > 0) {
            result.push(remaining);
        }
        
        return result;
    }
    
    if (maxsplit < 0) {
        return s.split(sep);
    }
    
    const parts = s.split(sep);
    if (parts.length <= maxsplit + 1) {
        return parts;
    }
    return [...parts.slice(0, maxsplit), parts.slice(maxsplit).join(sep)];
}

// =============================================================================
// REPLACE
// =============================================================================

/**
 * Python replace() with count parameter
 */
export function replace(s, old, new_, count = -1) {
    if (count === 0) return s;
    if (count < 0) return s.split(old).join(new_);
    
    let result = s;
    let replaced = 0;
    let start = 0;
    
    while (replaced < count) {
        const idx = result.indexOf(old, start);
        if (idx === -1) break;
        result = result.slice(0, idx) + new_ + result.slice(idx + old.length);
        start = idx + new_.length;
        replaced++;
    }
    
    return result;
}

// =============================================================================
// COUNT
// =============================================================================

/**
 * Python count() - count non-overlapping occurrences
 */
export function count(s, sub, start = 0, end = null) {
    if (end === null) end = s.length;
    if (start < 0) start = Math.max(0, s.length + start);
    if (end < 0) end = Math.max(0, s.length + end);
    
    const slice = s.slice(start, end);
    if (sub === '') return slice.length + 1;
    
    let n = 0;
    let pos = 0;
    while ((pos = slice.indexOf(sub, pos)) !== -1) {
        n++;
        pos += sub.length;
    }
    return n;
}

// =============================================================================
// INDEX / RINDEX
// =============================================================================

/**
 * Python index() - throws ValueError if not found
 */
export function index(s, sub, start = 0, end = null) {
    if (end === null) end = s.length;
    if (start < 0) start = Math.max(0, s.length + start);
    if (end < 0) end = Math.max(0, s.length + end);
    
    const slice = s.slice(start, end);
    const idx = slice.indexOf(sub);
    
    if (idx === -1) {
        throw new ValueError("substring not found");
    }
    return start + idx;
}

/**
 * Python rindex() - throws ValueError if not found
 */
export function rindex(s, sub, start = 0, end = null) {
    if (end === null) end = s.length;
    if (start < 0) start = Math.max(0, s.length + start);
    if (end < 0) end = Math.max(0, s.length + end);
    
    const slice = s.slice(start, end);
    const idx = slice.lastIndexOf(sub);
    
    if (idx === -1) {
        throw new ValueError("substring not found");
    }
    return start + idx;
}

// =============================================================================
// STRIP / LSTRIP / RSTRIP
// =============================================================================

/**
 * Python strip() - removes whitespace or specific chars
 */
export function strip(s, chars = null) {
    if (chars === null) return s.trim();
    const pattern = new RegExp(`^[${escapeRegex(chars)}]+|[${escapeRegex(chars)}]+$`, 'g');
    return s.replace(pattern, '');
}

/**
 * Python lstrip() - removes leading whitespace or chars
 */
export function lstrip(s, chars = null) {
    if (chars === null) return s.trimStart();
    const pattern = new RegExp(`^[${escapeRegex(chars)}]+`);
    return s.replace(pattern, '');
}

/**
 * Python rstrip() - removes trailing whitespace or chars
 */
export function rstrip(s, chars = null) {
    if (chars === null) return s.trimEnd();
    const pattern = new RegExp(`[${escapeRegex(chars)}]+$`);
    return s.replace(pattern, '');
}

function escapeRegex(s) {
    return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// =============================================================================
// STARTSWITH / ENDSWITH
// =============================================================================

/**
 * Python startswith() - supports tuple of prefixes
 */
export function startswith(s, prefix, start = 0, end = null) {
    if (end === null) end = s.length;
    const slice = s.slice(start, end);
    
    if (Array.isArray(prefix)) {
        return prefix.some(p => slice.startsWith(p));
    }
    return slice.startsWith(prefix);
}

/**
 * Python endswith() - supports tuple of suffixes
 */
export function endswith(s, suffix, start = 0, end = null) {
    if (end === null) end = s.length;
    const slice = s.slice(start, end);
    
    if (Array.isArray(suffix)) {
        return suffix.some(p => slice.endsWith(p));
    }
    return slice.endsWith(suffix);
}

// =============================================================================
// FIND / RFIND (like index but returns -1 instead of throwing)
// =============================================================================

/**
 * Python find() - returns -1 if not found
 */
export function find(s, sub, start = 0, end = null) {
    if (end === null) end = s.length;
    if (start < 0) start = Math.max(0, s.length + start);
    if (end < 0) end = Math.max(0, s.length + end);
    
    const slice = s.slice(start, end);
    const idx = slice.indexOf(sub);
    return idx === -1 ? -1 : start + idx;
}

/**
 * Python rfind() - returns -1 if not found
 */
export function rfind(s, sub, start = 0, end = null) {
    if (end === null) end = s.length;
    if (start < 0) start = Math.max(0, s.length + start);
    if (end < 0) end = Math.max(0, s.length + end);
    
    const slice = s.slice(start, end);
    const idx = slice.lastIndexOf(sub);
    return idx === -1 ? -1 : start + idx;
}

// =============================================================================
// JOIN
// =============================================================================

/**
 * Python join() - s.join(iterable)
 */
export function join(sep, iterable) {
    return Array.from(iterable).join(sep);
}

// =============================================================================
// EXPORT
// =============================================================================

export default {
    split,
    replace,
    count,
    index,
    rindex,
    strip,
    lstrip,
    rstrip,
    startswith,
    endswith,
    find,
    rfind,
    join,
};

