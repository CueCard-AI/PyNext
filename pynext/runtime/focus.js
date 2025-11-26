/**
 * PyNext Focus Runtime
 * 
 * Provides focus management with:
 * - Focus trapping (for modals/dialogs)
 * - Focus restoration (when closing modals)
 * - Roving focus (for lists/menus)
 * - Skip links
 * - Focus ring management
 * 
 * Size: ~1.5KB minified
 */

(function(global) {
    'use strict';

    // ==========================================================================
    // State
    // ==========================================================================

    /** @type {HTMLElement[]} Stack of previously focused elements for restoration */
    const focusStack = [];

    /** @type {Set<HTMLElement>} Currently active focus traps */
    const activeFocusTraps = new Set();

    /** @type {Map<string, Object>} Roving focus configurations */
    const rovingConfigs = new Map();

    // ==========================================================================
    // Focus Trap
    // ==========================================================================

    /**
     * Get all focusable elements within a container.
     * 
     * @param {HTMLElement} container
     * @returns {HTMLElement[]}
     */
    function getFocusableElements(container) {
        const selector = [
            'a[href]:not([disabled])',
            'button:not([disabled])',
            'input:not([disabled])',
            'select:not([disabled])',
            'textarea:not([disabled])',
            '[tabindex]:not([tabindex="-1"]):not([disabled])',
            '[contenteditable="true"]',
        ].join(', ');
        
        return Array.from(container.querySelectorAll(selector))
            .filter(el => {
                // Filter out invisible elements
                const style = window.getComputedStyle(el);
                return style.display !== 'none' && 
                       style.visibility !== 'hidden' &&
                       el.offsetParent !== null;
            });
    }

    /**
     * Create a focus trap for a container.
     * 
     * @param {HTMLElement} container - Element to trap focus within
     * @param {Object} options
     * @param {boolean} options.autoFocus - Auto-focus first element
     * @param {boolean} options.restoreFocus - Restore focus on release
     * @returns {Object} Trap controller
     */
    function createFocusTrap(container, options = {}) {
        const { autoFocus = true, restoreFocus = true } = options;
        
        // Store currently focused element
        if (restoreFocus && document.activeElement) {
            focusStack.push(document.activeElement);
        }
        
        // Keydown handler for trapping
        function handleKeyDown(event) {
            if (event.key !== 'Tab') return;
            
            const focusable = getFocusableElements(container);
            if (focusable.length === 0) return;
            
            const first = focusable[0];
            const last = focusable[focusable.length - 1];
            
            if (event.shiftKey) {
                // Shift+Tab: going backwards
                if (document.activeElement === first) {
                    event.preventDefault();
                    last.focus();
                }
            } else {
                // Tab: going forwards
                if (document.activeElement === last) {
                    event.preventDefault();
                    first.focus();
                }
            }
        }
        
        // Activate trap
        container.addEventListener('keydown', handleKeyDown);
        activeFocusTraps.add(container);
        
        // Auto-focus
        if (autoFocus) {
            const focusable = getFocusableElements(container);
            if (focusable.length > 0) {
                // Small delay for animations
                requestAnimationFrame(() => focusable[0].focus());
            }
        }
        
        log(`Focus trap activated: ${container.id || 'anonymous'}`);
        
        // Return controller
        return {
            release: () => {
                container.removeEventListener('keydown', handleKeyDown);
                activeFocusTraps.delete(container);
                
                // Restore focus
                if (restoreFocus && focusStack.length > 0) {
                    const previousElement = focusStack.pop();
                    if (previousElement && document.body.contains(previousElement)) {
                        previousElement.focus();
                    }
                }
                
                log(`Focus trap released: ${container.id || 'anonymous'}`);
            },
            
            focusFirst: () => {
                const focusable = getFocusableElements(container);
                if (focusable.length > 0) focusable[0].focus();
            },
            
            focusLast: () => {
                const focusable = getFocusableElements(container);
                if (focusable.length > 0) focusable[focusable.length - 1].focus();
            },
        };
    }

    /**
     * Initialize focus traps from data attributes.
     */
    function initFocusTraps() {
        document.querySelectorAll('[data-pynext-focus-trap="true"]').forEach(container => {
            const autoFocus = container.dataset.focusTrapAutofocus !== 'false';
            createFocusTrap(container, { autoFocus, restoreFocus: true });
        });
    }

    // ==========================================================================
    // Focus Restoration
    // ==========================================================================

    /**
     * Push current focus to stack for later restoration.
     */
    function pushFocus() {
        if (document.activeElement && document.activeElement !== document.body) {
            focusStack.push(document.activeElement);
            log('Focus pushed to stack');
        }
    }

    /**
     * Restore focus from stack.
     */
    function popFocus() {
        if (focusStack.length > 0) {
            const element = focusStack.pop();
            if (element && document.body.contains(element)) {
                element.focus();
                log('Focus restored from stack');
            }
        }
    }

    /**
     * Create a focus restoration scope.
     * 
     * @returns {Function} Function to restore focus
     */
    function useFocusRestore() {
        const previousElement = document.activeElement;
        
        return () => {
            if (previousElement && document.body.contains(previousElement)) {
                previousElement.focus();
            }
        };
    }

    // ==========================================================================
    // Roving Focus
    // ==========================================================================

    /**
     * Initialize roving focus for a container.
     * 
     * Allows arrow key navigation within a group of elements.
     * 
     * @param {HTMLElement} container
     * @param {Object} options
     * @param {string} options.selector - Selector for focusable items
     * @param {string} options.orientation - "horizontal", "vertical", or "both"
     * @param {boolean} options.loop - Whether to loop at ends
     */
    function createRovingFocus(container, options = {}) {
        const {
            selector = '[data-roving-item]',
            orientation = 'vertical',
            loop = true,
        } = options;
        
        let currentIndex = 0;
        
        function getItems() {
            return Array.from(container.querySelectorAll(selector));
        }
        
        function focusItem(index) {
            const items = getItems();
            if (items.length === 0) return;
            
            // Handle bounds
            if (loop) {
                index = (index + items.length) % items.length;
            } else {
                index = Math.max(0, Math.min(index, items.length - 1));
            }
            
            // Update tabindex
            items.forEach((item, i) => {
                item.setAttribute('tabindex', i === index ? '0' : '-1');
            });
            
            // Focus
            items[index].focus();
            currentIndex = index;
        }
        
        function handleKeyDown(event) {
            const items = getItems();
            if (items.length === 0) return;
            
            let handled = false;
            
            switch (event.key) {
                case 'ArrowDown':
                    if (orientation === 'vertical' || orientation === 'both') {
                        focusItem(currentIndex + 1);
                        handled = true;
                    }
                    break;
                    
                case 'ArrowUp':
                    if (orientation === 'vertical' || orientation === 'both') {
                        focusItem(currentIndex - 1);
                        handled = true;
                    }
                    break;
                    
                case 'ArrowRight':
                    if (orientation === 'horizontal' || orientation === 'both') {
                        focusItem(currentIndex + 1);
                        handled = true;
                    }
                    break;
                    
                case 'ArrowLeft':
                    if (orientation === 'horizontal' || orientation === 'both') {
                        focusItem(currentIndex - 1);
                        handled = true;
                    }
                    break;
                    
                case 'Home':
                    focusItem(0);
                    handled = true;
                    break;
                    
                case 'End':
                    focusItem(items.length - 1);
                    handled = true;
                    break;
            }
            
            if (handled) {
                event.preventDefault();
            }
        }
        
        // Initialize
        container.addEventListener('keydown', handleKeyDown);
        
        // Set initial tabindex
        const items = getItems();
        items.forEach((item, i) => {
            item.setAttribute('tabindex', i === 0 ? '0' : '-1');
        });
        
        const id = container.id || `roving_${Date.now()}`;
        rovingConfigs.set(id, { container, options, cleanup: () => {
            container.removeEventListener('keydown', handleKeyDown);
            rovingConfigs.delete(id);
        }});
        
        log(`Roving focus initialized: ${id} (${orientation})`);
        
        return {
            focusItem,
            destroy: () => {
                container.removeEventListener('keydown', handleKeyDown);
                rovingConfigs.delete(id);
            },
        };
    }

    /**
     * Initialize roving focus from data attributes.
     */
    function initRovingFocus() {
        document.querySelectorAll('[data-roving-group]').forEach(container => {
            const orientation = container.dataset.rovingOrientation || 'vertical';
            const loop = container.dataset.rovingLoop !== 'false';
            const selector = container.dataset.rovingSelector || '[data-roving-item]';
            
            createRovingFocus(container, { orientation, loop, selector });
        });
    }

    // ==========================================================================
    // Skip Links
    // ==========================================================================

    /**
     * Initialize skip links.
     */
    function initSkipLinks() {
        document.querySelectorAll('[data-skip-link]').forEach(link => {
            const targetId = link.dataset.skipLink;
            
            link.addEventListener('click', (event) => {
                event.preventDefault();
                const target = document.getElementById(targetId);
                if (target) {
                    target.setAttribute('tabindex', '-1');
                    target.focus();
                    target.removeAttribute('tabindex');
                }
            });
        });
    }

    // ==========================================================================
    // Focus Visible
    // ==========================================================================

    /**
     * Initialize focus-visible polyfill-like behavior.
     * Adds data-focus-visible attribute when using keyboard.
     */
    function initFocusVisible() {
        let hadKeyboardEvent = false;
        
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Tab') {
                hadKeyboardEvent = true;
            }
        });
        
        document.addEventListener('mousedown', () => {
            hadKeyboardEvent = false;
        });
        
        document.addEventListener('focusin', (event) => {
            if (hadKeyboardEvent) {
                event.target.setAttribute('data-focus-visible', '');
            }
        });
        
        document.addEventListener('focusout', (event) => {
            event.target.removeAttribute('data-focus-visible');
        });
    }

    // ==========================================================================
    // Logging
    // ==========================================================================

    const DEBUG = typeof window !== 'undefined' && window.__PYNEXT_DEBUG__;

    function log(...args) {
        if (DEBUG) {
            console.log('[PyNext Focus]', ...args);
        }
    }

    // ==========================================================================
    // Initialization
    // ==========================================================================

    function init() {
        initFocusTraps();
        initRovingFocus();
        initSkipLinks();
        initFocusVisible();
        log('Focus runtime initialized');
    }

    /**
     * Re-initialize after dynamic content changes.
     */
    function refresh() {
        initFocusTraps();
        initRovingFocus();
    }

    // ==========================================================================
    // Export
    // ==========================================================================

    if (typeof window !== 'undefined') {
        window.__pynext__ = window.__pynext__ || {};
        
        // API
        window.__pynext__.focus = {
            // Focus trap
            createFocusTrap,
            getFocusableElements,
            
            // Focus restoration
            pushFocus,
            popFocus,
            useFocusRestore,
            
            // Roving focus
            createRovingFocus,
            
            // Utilities
            refresh,
        };

        // Initialize on DOM ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', init);
        } else {
            init();
        }
        
        // Also re-init after navigation
        document.addEventListener('pynext:navigated', refresh);
    }

    // Module exports
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = {
            createFocusTrap,
            getFocusableElements,
            pushFocus,
            popFocus,
            useFocusRestore,
            createRovingFocus,
            refresh,
        };
    }

})(typeof window !== 'undefined' ? window : global);

