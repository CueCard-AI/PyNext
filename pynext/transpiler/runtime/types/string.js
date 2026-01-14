/**
 * PyNext Transpiler - Python String Methods for JavaScript
 * 
 * =============================================================================
 * WHAT THIS FILE DOES
 * =============================================================================
 * 
 * Provides JavaScript functions that implement Python string method semantics.
 * Used when Python string methods differ from JavaScript equivalents.
 * 
 * =============================================================================
 * WHY THIS EXISTS
 * =============================================================================
 * 
 * Python and JavaScript string methods have subtle but critical differences:
 * 
 * 1. split():     Python "a  b".split() → ["a", "b"], JS → ["a  b"]
 * 2. index():     Python throws ValueError, JS indexOf returns -1
 * 3. count():     Python counts overlapping, different from JS regex
 * 4. title():     Python "hello world".title() → "Hello World"
 * 5. capitalize(): Python only capitalizes first char, lowers rest
 * 6. center():    Python pads with custom fill character
 * 
 * =============================================================================
 * USAGE
 * =============================================================================
 * 
 * The transpiler emits calls to these functions:
 * 
 *   s.split()        → __py.str.split(s)
 *   s.index("x")     → __py.str.index(s, "x")
 *   s.title()        → __py.str.title(s)
 */

// =============================================================================
// CORE STRING METHODS (deduplicated - imported from string-core.js)
// =============================================================================
import {
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
} from './string-core.js';

// Re-export core methods for backward compatibility
export { split, replace, count, index, rindex, strip, lstrip, rstrip, startswith, endswith, find, rfind, join };

// =============================================================================
// RSPLIT - Split from right
// =============================================================================

/**
 * Python rsplit() - split from the right
 * 
 * @param {string} s - String to split
 * @param {string|null} sep - Separator
 * @param {number} maxsplit - Max splits from right
 * @returns {string[]} Array of parts
 */
export function rsplit(s, sep = null, maxsplit = -1) {
    if (maxsplit < 0) {
        return split(s, sep, -1);
    }
    
    if (sep === null) {
        const parts = split(s, null, -1);
        if (maxsplit >= parts.length - 1) return parts;
        const splitPoint = parts.length - maxsplit;
        const result = [parts.slice(0, splitPoint).join(' ')];
        result.push(...parts.slice(splitPoint));
        return result;
    }
    
    const parts = s.split(sep);
    if (maxsplit >= parts.length - 1) return parts;
    const splitPoint = parts.length - maxsplit;
    const result = [parts.slice(0, splitPoint).join(sep)];
    result.push(...parts.slice(splitPoint));
    return result;
}

// =============================================================================
// TITLE - Title case
// =============================================================================

/**
 * Python title() - title case
 * 
 * @param {string} s - String to convert
 * @returns {string} Title cased string
 * 
 * @example
 * title("hello world")  // → "Hello World"
 * title("it's a test")  // → "It'S A Test" (Python behavior)
 * 
 * Note: Python's title() capitalizes after ANY non-letter, including apostrophe
 * "it's" → "It'S" because ' is not a letter
 */
export function title(s) {
    // Browser-compatible version (no lookbehind)
    // Process character by character to match Python behavior
    let result = '';
    let capitalizeNext = true;
    
    for (const c of s) {
        if (/[a-zA-Z]/.test(c)) {
            result += capitalizeNext ? c.toUpperCase() : c.toLowerCase();
            capitalizeNext = false;
        } else {
            result += c;
            capitalizeNext = true;  // Next letter should be capitalized
        }
    }
    
    return result;
}

// =============================================================================
// CAPITALIZE - Capitalize first letter only
// =============================================================================

/**
 * Python capitalize() - capitalize first char, lowercase rest
 * 
 * @param {string} s - String to capitalize
 * @returns {string} Capitalized string
 */
export function capitalize(s) {
    if (s.length === 0) return s;
    return s[0].toUpperCase() + s.slice(1).toLowerCase();
}

// =============================================================================
// SWAPCASE - Swap upper/lower case
// =============================================================================

/**
 * Python swapcase() - swap case of each character
 */
export function swapcase(s) {
    return s.split('').map(c => {
        if (c === c.toUpperCase()) return c.toLowerCase();
        return c.toUpperCase();
    }).join('');
}

// =============================================================================
// CENTER / LJUST / RJUST - Padding with fill character
// =============================================================================

/**
 * Python center() - center string with fill character
 * 
 * @param {string} s - String to center
 * @param {number} width - Total width
 * @param {string} fillchar - Fill character (default space)
 * @returns {string} Centered string
 */
export function center(s, width, fillchar = ' ') {
    if (s.length >= width) return s;
    const totalPad = width - s.length;
    const leftPad = Math.floor(totalPad / 2);
    const rightPad = totalPad - leftPad;
    return fillchar.repeat(leftPad) + s + fillchar.repeat(rightPad);
}

/**
 * Python ljust() - left justify with fill character
 */
export function ljust(s, width, fillchar = ' ') {
    if (s.length >= width) return s;
    return s + fillchar.repeat(width - s.length);
}

/**
 * Python rjust() - right justify with fill character
 */
export function rjust(s, width, fillchar = ' ') {
    if (s.length >= width) return s;
    return fillchar.repeat(width - s.length) + s;
}

/**
 * Python zfill() - pad with zeros, handle sign
 */
export function zfill(s, width) {
    if (s.length >= width) return s;
    const sign = (s[0] === '+' || s[0] === '-') ? s[0] : '';
    const rest = sign ? s.slice(1) : s;
    return sign + rest.padStart(width - sign.length, '0');
}

// =============================================================================
// PARTITION / RPARTITION
// =============================================================================

/**
 * Python partition() - split into (before, sep, after)
 */
export function partition(s, sep) {
    const idx = s.indexOf(sep);
    if (idx === -1) return [s, '', ''];
    return [s.slice(0, idx), sep, s.slice(idx + sep.length)];
}

/**
 * Python rpartition() - split from right
 */
export function rpartition(s, sep) {
    const idx = s.lastIndexOf(sep);
    if (idx === -1) return ['', '', s];
    return [s.slice(0, idx), sep, s.slice(idx + sep.length)];
}

// =============================================================================
// SPLITLINES
// =============================================================================

/**
 * Python splitlines() - split on line boundaries
 * 
 * Python recognizes these line boundaries:
 * \n, \r, \r\n, \v (0x0b), \f (0x0c), \x1c, \x1d, \x1e, \x85, \u2028, \u2029
 * 
 * @param {string} s - String to split
 * @param {boolean} keepends - Keep line endings
 * @returns {string[]} Array of lines
 */
export function splitlines(s, keepends = false) {
    // Match all Python line boundaries
    const lineBreaks = /\r\n|\r|\n|\x0b|\x0c|\x1c|\x1d|\x1e|\x85|\u2028|\u2029/g;
    
    if (keepends) {
        // Browser-compatible version (no lookbehind)
        const result = [];
        let lastEnd = 0;
        let match;
        
        while ((match = lineBreaks.exec(s)) !== null) {
            result.push(s.slice(lastEnd, match.index + match[0].length));
            lastEnd = match.index + match[0].length;
        }
        
        if (lastEnd < s.length) {
            result.push(s.slice(lastEnd));
        }
        
        return result;
    }
    
    return s.split(lineBreaks);
}

// =============================================================================
// IS* METHODS - Character classification (Unicode-aware)
// =============================================================================

/**
 * Python isdigit() - all characters are digits
 * Note: Python's isdigit() includes superscripts and subscripts
 */
export function isdigit(s) {
    if (s.length === 0) return false;
    for (const c of s) {
        // Check if character is a digit (Unicode category Nd)
        // This is a simplified check - Python is more comprehensive
        if (!/\d/.test(c)) return false;
    }
    return true;
}

/**
 * Python isalpha() - all characters are alphabetic (Unicode-aware)
 * Includes accented characters, CJK, etc.
 */
export function isalpha(s) {
    if (s.length === 0) return false;
    for (const c of s) {
        // Check if it's a letter by seeing if case conversion changes it
        // or if it's in the basic letter ranges
        if (c.toLowerCase() === c.toUpperCase() && !/[a-zA-Z]/.test(c)) {
            // Character has no case and isn't ASCII letter
            // Check if it might be CJK or other script
            const code = c.charCodeAt(0);
            // CJK ranges and other alphabetic scripts
            if (!((code >= 0x4E00 && code <= 0x9FFF) ||  // CJK
                  (code >= 0x3040 && code <= 0x309F) ||  // Hiragana
                  (code >= 0x30A0 && code <= 0x30FF) ||  // Katakana
                  (code >= 0xAC00 && code <= 0xD7AF) ||  // Korean
                  (code >= 0x0600 && code <= 0x06FF) ||  // Arabic
                  (code >= 0x0400 && code <= 0x04FF) ||  // Cyrillic
                  (code >= 0x0370 && code <= 0x03FF) ||  // Greek
                  (code >= 0x0590 && code <= 0x05FF) ||  // Hebrew
                  (code >= 0x00C0 && code <= 0x00FF) ||  // Latin Extended
                  (code >= 0x0100 && code <= 0x017F) ||  // Latin Extended-A
                  (code >= 0x0180 && code <= 0x024F))) { // Latin Extended-B
                return false;
            }
        }
    }
    return true;
}

/**
 * Python isalnum() - all characters are alphanumeric (Unicode-aware)
 */
export function isalnum(s) {
    if (s.length === 0) return false;
    for (const c of s) {
        if (!isalpha(c) && !isdigit(c)) return false;
    }
    return true;
}

/**
 * Python isspace() - all characters are whitespace
 */
export function isspace(s) {
    return s.length > 0 && /^\s+$/.test(s);
}

/**
 * Python isupper() - all cased characters are uppercase (Unicode-aware)
 */
export function isupper(s) {
    if (s.length === 0) return false;
    let hasCased = false;
    for (const c of s) {
        const lower = c.toLowerCase();
        const upper = c.toUpperCase();
        if (lower !== upper) {
            // This is a cased character
            hasCased = true;
            if (c !== upper) return false;
        }
    }
    return hasCased;
}

/**
 * Python islower() - all cased characters are lowercase (Unicode-aware)
 */
export function islower(s) {
    if (s.length === 0) return false;
    let hasCased = false;
    for (const c of s) {
        const lower = c.toLowerCase();
        const upper = c.toUpperCase();
        if (lower !== upper) {
            // This is a cased character
            hasCased = true;
            if (c !== lower) return false;
        }
    }
    return hasCased;
}

/**
 * Python istitle() - string is titlecased
 */
export function istitle(s) {
    return s.length > 0 && s === title(s);
}

/**
 * Python isnumeric() - all characters are numeric
 * Broader than isdigit - includes fractions, subscripts, etc.
 */
export function isnumeric(s) {
    if (s.length === 0) return false;
    for (const c of s) {
        const code = c.charCodeAt(0);
        // Basic digits and some numeric characters
        if (!/\d/.test(c) && 
            !(code >= 0x2150 && code <= 0x218F) &&  // Number forms
            !(code >= 0x00B2 && code <= 0x00B3) &&  // Superscript 2,3
            code !== 0x00B9 &&                       // Superscript 1
            !(code >= 0x2070 && code <= 0x209F)) {  // Super/subscripts
            return false;
        }
    }
    return true;
}

/**
 * Python isdecimal() - all characters are decimal digits
 * Most restrictive - only 0-9 style digits
 */
export function isdecimal(s) {
    if (s.length === 0) return false;
    for (const c of s) {
        if (!/[0-9]/.test(c)) return false;
    }
    return true;
}

/**
 * Python isidentifier() - valid Python identifier
 */
export function isidentifier(s) {
    if (s.length === 0) return false;
    // Python identifiers can include unicode letters
    // Simplified: ASCII letters, digits, underscore
    // First char can't be digit
    const first = s[0];
    if (/[0-9]/.test(first)) return false;
    if (!isalpha(first) && first !== '_') return false;
    
    for (let i = 1; i < s.length; i++) {
        const c = s[i];
        if (!isalpha(c) && !isdigit(c) && c !== '_') return false;
    }
    return true;
}

// =============================================================================
// EXPANDTABS
// =============================================================================

/**
 * Python expandtabs() - replace tabs with spaces
 */
export function expandtabs(s, tabsize = 8) {
    let result = '';
    let col = 0;
    
    for (const c of s) {
        if (c === '\t') {
            const spaces = tabsize - (col % tabsize);
            result += ' '.repeat(spaces);
            col += spaces;
        } else if (c === '\n' || c === '\r') {
            result += c;
            col = 0;
        } else {
            result += c;
            col++;
        }
    }
    
    return result;
}

// =============================================================================
// ENCODE (basic)
// =============================================================================

/**
 * Python encode() - basic UTF-8 encoding
 * Returns Uint8Array (similar to Python bytes)
 */
export function encode(s, encoding = 'utf-8') {
    if (encoding !== 'utf-8' && encoding !== 'utf8') {
        throw new Error(`Unsupported encoding: ${encoding}`);
    }
    return new TextEncoder().encode(s);
}

// =============================================================================
// FORMAT (placeholder, main format is in core.js)
// =============================================================================

// Format is handled by __py.format in core.js

// =============================================================================
// EXPORT
// =============================================================================

export default {
    split,
    rsplit,
    index,
    rindex,
    count,
    title,
    capitalize,
    swapcase,
    center,
    ljust,
    rjust,
    zfill,
    strip,
    lstrip,
    rstrip,
    replace,
    partition,
    rpartition,
    splitlines,
    isdigit,
    isalpha,
    isalnum,
    isspace,
    isupper,
    islower,
    istitle,
    isnumeric,
    isdecimal,
    isidentifier,
    expandtabs,
    encode,
};
