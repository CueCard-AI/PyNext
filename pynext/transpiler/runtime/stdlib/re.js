/**
 * PyNext Standard Library - re module
 * 
 * =============================================================================
 * WHAT THIS FILE DOES
 * =============================================================================
 * 
 * Provides Python re module equivalents in JavaScript.
 * Handles critical differences between Python and JavaScript regex.
 * 
 * =============================================================================
 * WHY THIS EXISTS
 * =============================================================================
 * 
 * Python re module differences from JavaScript:
 * - re.match() is anchored at start, JS String.match() is not
 * - re.sub() count parameter works differently
 * - Python regex returns Match objects with methods
 * - Python has re.IGNORECASE etc. flags as module constants
 * 
 * =============================================================================
 * CRITICAL DIFFERENCES
 * =============================================================================
 * 
 * | Python | JavaScript | Solution |
 * |--------|------------|----------|
 * | re.match(p, s) | Anchored at ^ | Prepend ^ to pattern |
 * | match.group(0) | Full match | Return m[0] |
 * | match.group(1) | First capture | Return m[1] |
 * | match.groups() | All captures | Return m.slice(1) |
 * | re.sub(p, r, s, count=1) | Replace N times | Loop N times |
 * 
 * =============================================================================
 * USAGE
 * =============================================================================
 * 
 * Python:
 *   import re
 *   m = re.match(r'\d+', '123abc')
 *   if m:
 *       print(m.group())  # '123'
 * 
 * Transpiled:
 *   const m = __py.re.match('\\d+', '123abc');
 *   if (m) {
 *       console.log(m.group());  // '123'
 *   }
 */

// =============================================================================
// FLAGS (Python re module constants)
// =============================================================================

export const IGNORECASE = 'i';
export const I = 'i';
export const MULTILINE = 'm';
export const M = 'm';
export const DOTALL = 's';
export const S = 's';
export const GLOBAL = 'g';
export const G = 'g';

// =============================================================================
// MATCH OBJECT
// =============================================================================

/**
 * Create a Match object that mimics Python's re.Match.
 * 
 * Supports:
 * - group(n) - Get group by index
 * - groups() - Get all captured groups
 * - start(n) / end(n) - Get positions of groups
 * - span(n) - Get (start, end) tuple
 * 
 * @param {RegExpMatchArray|null} m - JS regex match result
 * @param {string} string - Original string
 * @param {RegExp} pattern - Original regex pattern (for indices)
 * @returns {Object|null} Match object or null
 */
function createMatch(m, string, pattern = null) {
    if (!m) return null;
    
    // Calculate group positions by searching for each group in the matched string
    // This is a heuristic but works for most cases
    const groupPositions = [];
    const fullMatchStart = m.index;
    
    // Group 0 is always the full match
    groupPositions[0] = { start: fullMatchStart, end: fullMatchStart + m[0].length };
    
    // For captured groups, we need to find their positions
    // This uses the indices feature if available (ES2022+), otherwise estimates
    if (m.indices) {
        // Modern browsers with 'd' flag support
        for (let i = 1; i < m.length; i++) {
            if (m.indices[i]) {
                groupPositions[i] = { start: m.indices[i][0], end: m.indices[i][1] };
            } else {
                groupPositions[i] = { start: -1, end: -1 };  // Unmatched group
            }
        }
    } else {
        // Fallback: estimate positions by searching in the full match
        let searchStart = fullMatchStart;
        for (let i = 1; i < m.length; i++) {
            if (m[i] === undefined) {
                groupPositions[i] = { start: -1, end: -1 };
            } else {
                // Find this group within the string starting from where we left off
                const groupStart = string.indexOf(m[i], searchStart);
                if (groupStart >= 0 && groupStart < fullMatchStart + m[0].length) {
                    groupPositions[i] = { start: groupStart, end: groupStart + m[i].length };
                    searchStart = groupStart + m[i].length;
                } else {
                    // Fallback: position relative to match start
                    groupPositions[i] = { start: fullMatchStart, end: fullMatchStart + m[i].length };
                }
            }
        }
    }
    
    return {
        /**
         * Return the match or a captured group.
         * @param {number} i - Group index (0 = full match)
         * @returns {string|undefined}
         */
        group(i = 0) {
            return m[i];
        },
        
        /**
         * Return all captured groups (excluding full match).
         * @returns {Array<string>}
         */
        groups() {
            return m.slice(1);
        },
        
        /**
         * Return start index of match or group.
         * @param {number} group - Group index
         * @returns {number}
         */
        start(group = 0) {
            if (group >= groupPositions.length) {
                throw new Error(`no such group: ${group}`);
            }
            return groupPositions[group].start;
        },
        
        /**
         * Return end index of match or group.
         * @param {number} group - Group index
         * @returns {number}
         */
        end(group = 0) {
            if (group >= groupPositions.length) {
                throw new Error(`no such group: ${group}`);
            }
            return groupPositions[group].end;
        },
        
        /**
         * Return (start, end) tuple.
         * @param {number} group - Group index
         * @returns {[number, number]}
         */
        span(group = 0) {
            return [this.start(group), this.end(group)];
        },
        
        /** The original string */
        string: string,
        
        /** The regex pattern */
        re: pattern || m.input,
        
        /** Position where match starts */
        pos: 0,
        
        /** Position where match ends */
        endpos: string.length,
        
        /** Last matched group index */
        lastindex: m.length > 1 ? m.length - 1 : null,
        
        /** Last matched group (if named groups exist) */
        lastgroup: null
    };
}

// =============================================================================
// CORE FUNCTIONS
// =============================================================================

/**
 * Match pattern at the beginning of string.
 * 
 * CRITICAL: Python re.match() is anchored at start!
 * 
 * @param {string} pattern - Regex pattern
 * @param {string} string - String to match
 * @param {string} flags - Optional flags (i, m, s)
 * @returns {Object|null} Match object or null
 * 
 * @example
 * match('\\d+', '123abc')  // → Match object (group() = '123')
 * match('\\d+', 'abc123')  // → null (no match at start!)
 */
export function match(pattern, string, flags = '') {
    // Anchor at start to match Python behavior
    // Use 'd' flag for indices if supported (ES2022+)
    let re;
    let m;
    try {
        re = new RegExp('^' + pattern, flags + 'd');
        m = re.exec(string);
    } catch (e) {
        // Fallback without indices
        re = new RegExp('^' + pattern, flags);
        m = re.exec(string);
    }
    return createMatch(m, string, re);
}

/**
 * Search for pattern anywhere in string.
 * 
 * @param {string} pattern - Regex pattern
 * @param {string} string - String to search
 * @param {string} flags - Optional flags
 * @returns {Object|null} Match object or null
 * 
 * @example
 * search('\\d+', 'abc123def')  // → Match object (group() = '123')
 */
export function search(pattern, string, flags = '') {
    // Use 'd' flag for indices if supported (ES2022+)
    let re;
    let m;
    try {
        re = new RegExp(pattern, flags + 'd');
        m = re.exec(string);
    } catch (e) {
        // Fallback without indices
        re = new RegExp(pattern, flags);
        m = re.exec(string);
    }
    return createMatch(m, string, re);
}

/**
 * Find all non-overlapping matches.
 * 
 * @param {string} pattern - Regex pattern
 * @param {string} string - String to search
 * @param {string} flags - Optional flags
 * @returns {Array<string>} List of matches
 * 
 * @example
 * findall('\\d+', 'a1b2c3')  // → ['1', '2', '3']
 */
export function findall(pattern, string, flags = '') {
    const re = new RegExp(pattern, flags + 'g');
    return string.match(re) || [];
}

/**
 * Find all matches as Match objects (iterator).
 * 
 * @param {string} pattern - Regex pattern
 * @param {string} string - String to search
 * @param {string} flags - Optional flags
 * @returns {Array<Object>} List of Match objects
 */
export function finditer(pattern, string, flags = '') {
    const re = new RegExp(pattern, flags + 'g');
    const results = [];
    let m;
    while ((m = re.exec(string)) !== null) {
        results.push(createMatch(m, string));
    }
    return results;
}

/**
 * Replace occurrences of pattern with replacement.
 * 
 * @param {string} pattern - Regex pattern
 * @param {string|Function} repl - Replacement string or function
 * @param {string} string - String to modify
 * @param {number} count - Max replacements (0 = all)
 * @param {string} flags - Optional flags
 * @returns {string} Modified string
 * 
 * @example
 * sub('\\d', 'X', 'a1b2c3')      // → 'aXbXcX'
 * sub('\\d', 'X', 'a1b2c3', 2)   // → 'aXbXc3'
 */
export function sub(pattern, repl, string, count = 0, flags = '') {
    if (count === 0) {
        // Replace all
        const re = new RegExp(pattern, flags + 'g');
        return string.replace(re, repl);
    }
    
    // Replace limited count
    let result = string;
    let n = 0;
    while (n < count) {
        const re = new RegExp(pattern, flags);
        const newResult = result.replace(re, repl);
        if (newResult === result) break;  // No more matches
        result = newResult;
        n++;
    }
    return result;
}

/**
 * Replace and return (new_string, number_of_replacements).
 * 
 * @param {string} pattern - Regex pattern
 * @param {string|Function} repl - Replacement
 * @param {string} string - String to modify
 * @param {number} count - Max replacements (0 = all)
 * @param {string} flags - Optional flags
 * @returns {[string, number]} [new_string, num_replacements]
 */
export function subn(pattern, repl, string, count = 0, flags = '') {
    let numReplacements = 0;
    const replacer = typeof repl === 'function' 
        ? (...args) => { numReplacements++; return repl(...args); }
        : () => { numReplacements++; return repl; };
    
    if (count === 0) {
        const re = new RegExp(pattern, flags + 'g');
        const result = string.replace(re, replacer);
        return [result, numReplacements];
    }
    
    let result = string;
    while (numReplacements < count) {
        const re = new RegExp(pattern, flags);
        const newResult = result.replace(re, replacer);
        if (newResult === result) break;
        result = newResult;
    }
    return [result, numReplacements];
}

/**
 * Split string by pattern.
 * 
 * @param {string} pattern - Regex pattern
 * @param {string} string - String to split
 * @param {number} maxsplit - Max splits (0 = all)
 * @param {string} flags - Optional flags
 * @returns {Array<string>} List of parts
 * 
 * @example
 * split('\\s+', 'a b  c')   // → ['a', 'b', 'c']
 * split('\\s+', 'a b c', 1) // → ['a', 'b c']
 */
export function split(pattern, string, maxsplit = 0, flags = '') {
    const re = new RegExp(pattern, flags);
    
    if (maxsplit === 0) {
        return string.split(re);
    }
    
    // Limited splits
    const result = [];
    let remaining = string;
    let n = 0;
    
    while (n < maxsplit) {
        const m = remaining.match(re);
        if (!m) break;
        
        result.push(remaining.slice(0, m.index));
        remaining = remaining.slice(m.index + m[0].length);
        n++;
    }
    result.push(remaining);
    
    return result;
}

/**
 * Escape special regex characters in string.
 * 
 * @param {string} string - String to escape
 * @returns {string} Escaped string
 * 
 * @example
 * escape('hello.world')  // → 'hello\\.world'
 */
export function escape(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Compile a pattern into a regex object.
 * Returns an object with bound methods.
 * 
 * @param {string} pattern - Regex pattern
 * @param {string} flags - Optional flags
 * @returns {Object} Compiled pattern object
 */
export function compile(pattern, flags = '') {
    return {
        pattern: pattern,
        flags: flags,
        match: (string) => match(pattern, string, flags),
        search: (string) => search(pattern, string, flags),
        findall: (string) => findall(pattern, string, flags),
        finditer: (string) => finditer(pattern, string, flags),
        sub: (repl, string, count = 0) => sub(pattern, repl, string, count, flags),
        subn: (repl, string, count = 0) => subn(pattern, repl, string, count, flags),
        split: (string, maxsplit = 0) => split(pattern, string, maxsplit, flags)
    };
}

/**
 * Check if string matches pattern completely.
 * 
 * @param {string} pattern - Regex pattern
 * @param {string} string - String to match
 * @param {string} flags - Optional flags
 * @returns {Object|null} Match object or null
 */
export function fullmatch(pattern, string, flags = '') {
    // Anchor at both ends
    const re = new RegExp('^' + pattern + '$', flags);
    const m = string.match(re);
    return createMatch(m, string);
}
