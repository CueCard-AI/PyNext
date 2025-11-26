/**
 * PyNext Keyboard Runtime
 * 
 * Provides keyboard shortcut handling with:
 * - Single key shortcuts (cmd+k, ctrl+s, escape)
 * - Key sequences (g → d, g → s)
 * - Context awareness (skip in inputs, dialog-only, etc.)
 * - Platform detection (cmd on Mac, ctrl on Windows/Linux)
 * 
 * Size: ~2KB minified
 */

(function(global) {
    'use strict';

    // ==========================================================================
    // Platform Detection
    // ==========================================================================

    const isMac = typeof navigator !== 'undefined' && 
        /Mac|iPod|iPhone|iPad/.test(navigator.platform);

    // ==========================================================================
    // State
    // ==========================================================================

    /** @type {Map<string, Object>} Registered shortcuts */
    const shortcuts = new Map();

    /** @type {Map<string, Object>} Registered sequences */
    const sequences = new Map();

    /** @type {Map<string, Function>} Handler functions */
    const handlers = new Map();

    /** @type {string[]} Current sequence buffer */
    let sequenceBuffer = [];

    /** @type {number|null} Sequence timeout ID */
    let sequenceTimeout = null;

    /** @type {number} Sequence timeout duration (ms) */
    const SEQUENCE_TIMEOUT = 1000;

    // ==========================================================================
    // Shortcut Registration
    // ==========================================================================

    /**
     * Register a keyboard shortcut.
     * 
     * @param {Object} config - Shortcut configuration
     * @param {string} config.id - Unique ID
     * @param {string} config.key - Key to match (lowercase)
     * @param {string[]} config.modifiers - Required modifiers (meta, ctrl, alt, shift)
     * @param {string} config.handlerId - Handler function ID
     * @param {string} config.context - Context ("global", "input", "dialog")
     * @param {boolean} config.preventDefault - Whether to prevent default
     */
    function registerShortcut(config) {
        shortcuts.set(config.id, config);
        log(`Registered shortcut: ${formatShortcut(config)}`);
    }

    /**
     * Register a key sequence.
     * 
     * @param {Object} config - Sequence configuration
     * @param {string} config.id - Unique ID
     * @param {string[]} config.keys - Sequence of keys
     * @param {string} config.handlerId - Handler function ID
     * @param {number} config.timeout - Timeout between keys (ms)
     */
    function registerSequence(config) {
        sequences.set(config.id, config);
        log(`Registered sequence: ${config.keys.join(' → ')}`);
    }

    /**
     * Register a handler function.
     * 
     * @param {string} id - Handler ID
     * @param {Function} fn - Handler function
     */
    function registerHandler(id, fn) {
        handlers.set(id, fn);
    }

    /**
     * Unregister a shortcut.
     * 
     * @param {string} id - Shortcut ID
     */
    function unregisterShortcut(id) {
        shortcuts.delete(id);
    }

    /**
     * Unregister a sequence.
     * 
     * @param {string} id - Sequence ID
     */
    function unregisterSequence(id) {
        sequences.delete(id);
    }

    // ==========================================================================
    // Shortcut Matching
    // ==========================================================================

    /**
     * Check if an event matches a shortcut.
     * 
     * @param {KeyboardEvent} event
     * @param {Object} shortcut
     * @returns {boolean}
     */
    function matchesShortcut(event, shortcut) {
        // Check key
        if (event.key.toLowerCase() !== shortcut.key) {
            return false;
        }

        // Check modifiers
        const modifiers = shortcut.modifiers || [];
        
        // Meta/Cmd key
        const needsMeta = modifiers.includes('meta');
        if (needsMeta !== event.metaKey) return false;
        
        // Ctrl key
        const needsCtrl = modifiers.includes('ctrl');
        if (needsCtrl !== event.ctrlKey) return false;
        
        // Alt/Option key
        const needsAlt = modifiers.includes('alt');
        if (needsAlt !== event.altKey) return false;
        
        // Shift key
        const needsShift = modifiers.includes('shift');
        if (needsShift !== event.shiftKey) return false;
        
        return true;
    }

    /**
     * Check if current context allows this shortcut.
     * 
     * @param {KeyboardEvent} event
     * @param {Object} shortcut
     * @returns {boolean}
     */
    function checkContext(event, shortcut) {
        const target = event.target;
        const isInput = target.matches('input, textarea, select, [contenteditable="true"]');
        const isInDialog = target.closest('[data-pynext-dialog][data-state="open"], [role="dialog"]');
        
        switch (shortcut.context) {
            case 'global':
                // Skip in input fields unless it's a special key
                if (isInput && !isSpecialKey(shortcut.key)) {
                    return false;
                }
                return true;
                
            case 'input':
                // Only trigger in input fields
                return isInput;
                
            case 'dialog':
                // Only trigger in dialogs
                return !!isInDialog;
                
            case 'always':
                // Always trigger
                return true;
                
            default:
                return !isInput;
        }
    }

    /**
     * Check if a key is "special" (should work in inputs).
     * 
     * @param {string} key
     * @returns {boolean}
     */
    function isSpecialKey(key) {
        return ['escape', 'enter', 'tab'].includes(key.toLowerCase());
    }

    // ==========================================================================
    // Sequence Handling
    // ==========================================================================

    /**
     * Process a key for sequence matching.
     * 
     * @param {string} key - Key pressed
     * @returns {Object|null} Matched sequence or null
     */
    function processSequenceKey(key) {
        // Reset timeout
        if (sequenceTimeout) {
            clearTimeout(sequenceTimeout);
        }
        
        // Add to buffer
        sequenceBuffer.push(key.toLowerCase());
        
        // Set new timeout
        sequenceTimeout = setTimeout(() => {
            sequenceBuffer = [];
        }, SEQUENCE_TIMEOUT);
        
        // Check for matches
        const currentSequence = sequenceBuffer.join(' ');
        
        for (const [id, sequence] of sequences) {
            const targetSequence = sequence.keys.join(' ');
            
            if (currentSequence === targetSequence) {
                // Full match!
                sequenceBuffer = [];
                clearTimeout(sequenceTimeout);
                return sequence;
            }
            
            if (targetSequence.startsWith(currentSequence)) {
                // Partial match, keep buffering
                return null;
            }
        }
        
        // No match possible, reset
        sequenceBuffer = [];
        return null;
    }

    // ==========================================================================
    // Event Handler
    // ==========================================================================

    /**
     * Main keydown handler.
     * 
     * @param {KeyboardEvent} event
     */
    function handleKeyDown(event) {
        // Skip if in a context where keyboard shortcuts shouldn't fire
        // (e.g., composition for IME input)
        if (event.isComposing) return;
        
        // Check shortcuts first (they have modifiers)
        if (event.metaKey || event.ctrlKey || event.altKey) {
            for (const [id, shortcut] of shortcuts) {
                if (matchesShortcut(event, shortcut) && checkContext(event, shortcut)) {
                    const handler = handlers.get(shortcut.handlerId);
                    if (handler) {
                        if (shortcut.preventDefault) {
                            event.preventDefault();
                        }
                        try {
                            handler(event);
                        } catch (e) {
                            console.error(`Shortcut handler error (${id}):`, e);
                        }
                        return;
                    }
                }
            }
        }
        
        // Check sequences (no modifiers, single keys)
        if (!event.metaKey && !event.ctrlKey && !event.altKey) {
            // Skip if in input (unless escape)
            const target = event.target;
            const isInput = target.matches('input, textarea, select, [contenteditable="true"]');
            
            if (!isInput || event.key === 'Escape') {
                const matchedSequence = processSequenceKey(event.key);
                
                if (matchedSequence) {
                    const handler = handlers.get(matchedSequence.handlerId);
                    if (handler) {
                        event.preventDefault();
                        try {
                            handler(event);
                        } catch (e) {
                            console.error(`Sequence handler error (${matchedSequence.id}):`, e);
                        }
                    }
                }
            }
        }
        
        // Also check shortcuts without modifiers (like Escape, Enter)
        for (const [id, shortcut] of shortcuts) {
            if (!shortcut.modifiers || shortcut.modifiers.length === 0) {
                if (matchesShortcut(event, shortcut) && checkContext(event, shortcut)) {
                    const handler = handlers.get(shortcut.handlerId);
                    if (handler) {
                        if (shortcut.preventDefault) {
                            event.preventDefault();
                        }
                        try {
                            handler(event);
                        } catch (e) {
                            console.error(`Shortcut handler error (${id}):`, e);
                        }
                        return;
                    }
                }
            }
        }
    }

    // ==========================================================================
    // Utilities
    // ==========================================================================

    /**
     * Format a shortcut for display.
     * 
     * @param {Object} shortcut
     * @returns {string}
     */
    function formatShortcut(shortcut) {
        const parts = [];
        
        if (shortcut.modifiers) {
            if (shortcut.modifiers.includes('meta')) {
                parts.push(isMac ? '⌘' : 'Ctrl');
            }
            if (shortcut.modifiers.includes('ctrl')) {
                parts.push('Ctrl');
            }
            if (shortcut.modifiers.includes('alt')) {
                parts.push(isMac ? '⌥' : 'Alt');
            }
            if (shortcut.modifiers.includes('shift')) {
                parts.push('⇧');
            }
        }
        
        parts.push(shortcut.key.toUpperCase());
        
        return parts.join('+');
    }

    /**
     * Get all registered shortcuts for display.
     * 
     * @returns {Array<{combo: string, id: string}>}
     */
    function getRegisteredShortcuts() {
        return Array.from(shortcuts.values()).map(s => ({
            combo: formatShortcut(s),
            id: s.id,
            context: s.context,
        }));
    }

    /**
     * Get all registered sequences for display.
     * 
     * @returns {Array<{sequence: string, id: string}>}
     */
    function getRegisteredSequences() {
        return Array.from(sequences.values()).map(s => ({
            sequence: s.keys.join(' → '),
            id: s.id,
        }));
    }

    // ==========================================================================
    // Logging
    // ==========================================================================

    const DEBUG = typeof window !== 'undefined' && window.__PYNEXT_DEBUG__;

    function log(...args) {
        if (DEBUG) {
            console.log('[PyNext Keyboard]', ...args);
        }
    }

    // ==========================================================================
    // Initialization
    // ==========================================================================

    function init() {
        document.addEventListener('keydown', handleKeyDown);
        log('Keyboard runtime initialized');
        log('Platform:', isMac ? 'Mac' : 'Other');
    }

    /**
     * Initialize from hydration data.
     * 
     * @param {Object} data - Hydration data
     */
    function hydrate(data) {
        if (data.shortcuts) {
            data.shortcuts.forEach(registerShortcut);
        }
        if (data.sequences) {
            data.sequences.forEach(registerSequence);
        }
        log(`Hydrated ${shortcuts.size} shortcuts, ${sequences.size} sequences`);
    }

    // ==========================================================================
    // Export
    // ==========================================================================

    if (typeof window !== 'undefined') {
        window.__pynext__ = window.__pynext__ || {};
        
        // API
        window.__pynext__.keyboard = {
            registerShortcut,
            registerSequence,
            registerHandler,
            unregisterShortcut,
            unregisterSequence,
            getRegisteredShortcuts,
            getRegisteredSequences,
            formatShortcut,
            hydrate,
            isMac,
        };

        // Initialize on DOM ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', init);
        } else {
            init();
        }
    }

    // Module exports
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = {
            registerShortcut,
            registerSequence,
            registerHandler,
            unregisterShortcut,
            unregisterSequence,
            getRegisteredShortcuts,
            getRegisteredSequences,
            formatShortcut,
            hydrate,
        };
    }

})(typeof window !== 'undefined' ? window : global);

