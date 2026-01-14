/**
 * PyNext Runtime - String Methods (Extended)
 * 
 * =============================================================================
 * WHO: Transpiled code using less common string operations
 * =============================================================================
 * 
 * =============================================================================
 * WHAT: Extended Python string methods (~1KB gzipped)
 * =============================================================================
 * 
 * This file contains string methods used by <20% of Python code.
 * Most apps won't need these, so they're separated for tree-shaking.
 * 
 * Methods included:
 * - title, capitalize, swapcase: Case transformation
 * - center, ljust, rjust, zfill: Padding and alignment
 * - partition, rpartition: Split into 3 parts
 * - splitlines: Split on line boundaries
 * - is* methods: Character type checking
 * - expandtabs: Tab expansion
 * 
 * =============================================================================
 * WHEN: Loaded only when transpiled code uses these methods
 * =============================================================================
 * 
 * =============================================================================
 * WHERE: Part of Layer 1 (Extended) - lazy loaded
 * =============================================================================
 * 
 * =============================================================================
 * WHY: Keep bundle small for common cases
 * =============================================================================
 * 
 * Most web apps only use split, replace, strip - the core methods.
 * By separating extended methods, we avoid bloating the bundle.
 * 
 * =============================================================================
 * SIZE BUDGET: < 1.2KB gzipped
 * =============================================================================
 */

// =============================================================================
// CASE TRANSFORMATION
// =============================================================================

/**
 * Python title() - "hello world" → "Hello World"
 */
export function title(s) {
    return s.replace(/\b\w/g, c => c.toUpperCase());
}

/**
 * Python capitalize() - "hello WORLD" → "Hello world"
 */
export function capitalize(s) {
    if (s.length === 0) return s;
    return s[0].toUpperCase() + s.slice(1).toLowerCase();
}

/**
 * Python swapcase() - "Hello" → "hELLO"
 */
export function swapcase(s) {
    return s.split('').map(c => {
        if (c === c.toLowerCase()) return c.toUpperCase();
        return c.toLowerCase();
    }).join('');
}

// =============================================================================
// PADDING AND ALIGNMENT
// =============================================================================

/**
 * Python center() - center align with fill character
 */
export function center(s, width, fillchar = ' ') {
    if (s.length >= width) return s;
    const total = width - s.length;
    const left = Math.floor(total / 2);
    const right = total - left;
    return fillchar.repeat(left) + s + fillchar.repeat(right);
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
 * Python zfill() - pad with zeros, preserve sign
 */
export function zfill(s, width) {
    if (s.length >= width) return s;
    
    const hasSign = s[0] === '+' || s[0] === '-';
    if (hasSign) {
        return s[0] + '0'.repeat(width - s.length) + s.slice(1);
    }
    return '0'.repeat(width - s.length) + s;
}

// =============================================================================
// PARTITION
// =============================================================================

/**
 * Python partition() - split into (before, sep, after)
 */
export function partition(s, sep) {
    const idx = s.indexOf(sep);
    if (idx === -1) {
        return [s, '', ''];
    }
    return [s.slice(0, idx), sep, s.slice(idx + sep.length)];
}

/**
 * Python rpartition() - split from right into (before, sep, after)
 */
export function rpartition(s, sep) {
    const idx = s.lastIndexOf(sep);
    if (idx === -1) {
        return ['', '', s];
    }
    return [s.slice(0, idx), sep, s.slice(idx + sep.length)];
}

// =============================================================================
// RSPLIT
// =============================================================================

/**
 * Python rsplit() - split from right
 */
export function rsplit(s, sep = null, maxsplit = -1) {
    if (s === '') {
        return sep === null ? [] : [''];
    }
    
    if (sep === null) {
        const trimmed = s.trim();
        if (trimmed === '') return [];
        
        if (maxsplit < 0) {
            return trimmed.split(/\s+/);
        }
        
        // Split from right with maxsplit
        const parts = trimmed.split(/\s+/);
        if (parts.length <= maxsplit + 1) {
            return parts;
        }
        const splitPoint = parts.length - maxsplit;
        return [parts.slice(0, splitPoint).join(' '), ...parts.slice(splitPoint)];
    }
    
    if (maxsplit < 0) {
        return s.split(sep);
    }
    
    const parts = s.split(sep);
    if (parts.length <= maxsplit + 1) {
        return parts;
    }
    const splitPoint = parts.length - maxsplit;
    return [parts.slice(0, splitPoint).join(sep), ...parts.slice(splitPoint)];
}

// =============================================================================
// SPLITLINES
// =============================================================================

/**
 * Python splitlines() - split on line boundaries
 */
export function splitlines(s, keepends = false) {
    const lineEndings = /\r\n|\r|\n|\v|\f|\x1c|\x1d|\x1e|\x85|\u2028|\u2029/g;
    
    if (keepends) {
        const result = [];
        let lastIndex = 0;
        let match;
        
        while ((match = lineEndings.exec(s)) !== null) {
            result.push(s.slice(lastIndex, match.index + match[0].length));
            lastIndex = match.index + match[0].length;
        }
        
        if (lastIndex < s.length) {
            result.push(s.slice(lastIndex));
        }
        
        return result;
    }
    
    return s.split(lineEndings);
}

// =============================================================================
// IS* METHODS
// =============================================================================

/**
 * Python isdigit() - all characters are digits
 */
export function isdigit(s) {
    if (s.length === 0) return false;
    return /^[0-9]+$/.test(s);
}

/**
 * Python isalpha() - all characters are alphabetic
 */
export function isalpha(s) {
    if (s.length === 0) return false;
    return /^[a-zA-Z]+$/.test(s);
}

/**
 * Python isalnum() - all characters are alphanumeric
 */
export function isalnum(s) {
    if (s.length === 0) return false;
    return /^[a-zA-Z0-9]+$/.test(s);
}

/**
 * Python isspace() - all characters are whitespace
 */
export function isspace(s) {
    if (s.length === 0) return false;
    return /^\s+$/.test(s);
}

/**
 * Python isupper() - all cased characters are uppercase
 */
export function isupper(s) {
    if (s.length === 0) return false;
    const hasUpper = /[A-Z]/.test(s);
    const hasLower = /[a-z]/.test(s);
    return hasUpper && !hasLower;
}

/**
 * Python islower() - all cased characters are lowercase
 */
export function islower(s) {
    if (s.length === 0) return false;
    const hasUpper = /[A-Z]/.test(s);
    const hasLower = /[a-z]/.test(s);
    return hasLower && !hasUpper;
}

/**
 * Python istitle() - string is titlecased
 */
export function istitle(s) {
    if (s.length === 0) return false;
    
    const words = s.split(/\s+/);
    if (words.length === 0) return false;
    
    for (const word of words) {
        if (word.length === 0) continue;
        
        // First letter should be uppercase (if it's a letter)
        const first = word[0];
        if (/[a-zA-Z]/.test(first)) {
            if (first !== first.toUpperCase()) return false;
            
            // Rest should be lowercase (if they're letters)
            for (let i = 1; i < word.length; i++) {
                const c = word[i];
                if (/[a-zA-Z]/.test(c) && c !== c.toLowerCase()) {
                    return false;
                }
            }
        }
    }
    
    // Must have at least one cased character
    return /[a-zA-Z]/.test(s);
}

/**
 * Python isnumeric() - all characters are numeric
 */
export function isnumeric(s) {
    if (s.length === 0) return false;
    // Includes digits and Unicode numeric characters
    return /^[\d\u00B2\u00B3\u00B9\u00BC-\u00BE\u0660-\u0669\u06F0-\u06F9\u2150-\u2189]+$/.test(s);
}

/**
 * Python isdecimal() - all characters are decimal digits
 */
export function isdecimal(s) {
    if (s.length === 0) return false;
    return /^[0-9]+$/.test(s);
}

/**
 * Python isidentifier() - valid Python identifier
 */
export function isidentifier(s) {
    if (s.length === 0) return false;
    
    const first = s[0];
    if (/[0-9]/.test(first)) return false;
    if (!/[a-zA-Z]/.test(first) && first !== '_') return false;
    
    for (let i = 1; i < s.length; i++) {
        const c = s[i];
        if (!/[a-zA-Z0-9_]/.test(c)) return false;
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
// ENCODE
// =============================================================================

/**
 * Python encode() - basic UTF-8 encoding
 */
export function encode(s, encoding = 'utf-8') {
    if (encoding !== 'utf-8' && encoding !== 'utf8') {
        throw new Error(`Unsupported encoding: ${encoding}`);
    }
    return new TextEncoder().encode(s);
}

// =============================================================================
// EXPORT
// =============================================================================

export default {
    title,
    capitalize,
    swapcase,
    center,
    ljust,
    rjust,
    zfill,
    partition,
    rpartition,
    rsplit,
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

