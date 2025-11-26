/**
 * PyNext Theme Runtime
 * 
 * Provides dark mode and theming support with:
 * - System preference detection
 * - Manual mode override
 * - localStorage persistence
 * - Flash prevention
 * - Signal integration
 * 
 * Size: ~1KB minified
 */

(function(global) {
    'use strict';

    // ==========================================================================
    // State
    // ==========================================================================

    /** @type {string} Current theme mode: "light", "dark", or "system" */
    let currentMode = 'system';

    /** @type {string} Storage key for persisting theme */
    let storageKey = 'theme';

    /** @type {Set<Function>} Theme change subscribers */
    const subscribers = new Set();

    /** @type {MediaQueryList} System dark mode query */
    let darkModeQuery = null;

    // ==========================================================================
    // Core Functions
    // ==========================================================================

    /**
     * Get the effective theme (resolving "system" to actual light/dark).
     * 
     * @returns {"light"|"dark"}
     */
    function getEffectiveTheme() {
        if (currentMode === 'system') {
            return getSystemPreference();
        }
        return currentMode;
    }

    /**
     * Get the system's preferred color scheme.
     * 
     * @returns {"light"|"dark"}
     */
    function getSystemPreference() {
        if (!darkModeQuery) {
            darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
        }
        return darkModeQuery.matches ? 'dark' : 'light';
    }

    /**
     * Apply theme to the document.
     * 
     * @param {"light"|"dark"} theme
     */
    function applyTheme(theme) {
        const root = document.documentElement;
        
        if (theme === 'dark') {
            root.classList.add('dark');
            root.style.colorScheme = 'dark';
        } else {
            root.classList.remove('dark');
            root.style.colorScheme = 'light';
        }
        
        // Update meta theme-color for mobile browsers
        const metaTheme = document.querySelector('meta[name="theme-color"]');
        if (metaTheme) {
            metaTheme.content = theme === 'dark' ? '#1a1a2e' : '#ffffff';
        }
        
        log(`Applied theme: ${theme}`);
    }

    /**
     * Set the theme mode.
     * 
     * @param {"light"|"dark"|"system"} mode
     */
    function setMode(mode) {
        if (!['light', 'dark', 'system'].includes(mode)) {
            console.warn(`Invalid theme mode: ${mode}`);
            return;
        }
        
        currentMode = mode;
        
        // Persist to storage
        try {
            localStorage.setItem(storageKey, mode);
        } catch (e) {
            // Storage might be unavailable
        }
        
        // Apply theme
        applyTheme(getEffectiveTheme());
        
        // Notify subscribers
        subscribers.forEach(fn => fn(mode, getEffectiveTheme()));
        
        // Update any signals
        updateThemeSignals(mode);
    }

    /**
     * Get the current theme mode.
     * 
     * @returns {"light"|"dark"|"system"}
     */
    function getMode() {
        return currentMode;
    }

    /**
     * Toggle between light and dark (skipping system).
     */
    function toggle() {
        const effective = getEffectiveTheme();
        setMode(effective === 'dark' ? 'light' : 'dark');
    }

    /**
     * Cycle through modes: light → dark → system → light.
     */
    function cycle() {
        const modes = ['light', 'dark', 'system'];
        const currentIndex = modes.indexOf(currentMode);
        const nextIndex = (currentIndex + 1) % modes.length;
        setMode(modes[nextIndex]);
    }

    // ==========================================================================
    // Signal Integration
    // ==========================================================================

    /**
     * Update any signals that track theme.
     * 
     * @param {string} mode
     */
    function updateThemeSignals(mode) {
        // Update storage signals
        if (window.__pynext__?.storage) {
            const themeSignal = window.__pynext__.storage.getStorageSignal('theme');
            if (themeSignal) {
                themeSignal.write(mode);
            }
        }
        
        // Update regular signals with 'theme' in their name
        if (window.__pynext__?.signals) {
            for (const [id, signal] of Object.entries(window.__pynext__.signals)) {
                if (id.includes('theme') && typeof signal.write === 'function') {
                    signal.write(mode);
                }
            }
        }
    }

    // ==========================================================================
    // System Preference Listener
    // ==========================================================================

    function setupSystemListener() {
        if (!darkModeQuery) {
            darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
        }
        
        darkModeQuery.addEventListener('change', (e) => {
            if (currentMode === 'system') {
                applyTheme(e.matches ? 'dark' : 'light');
                subscribers.forEach(fn => fn('system', e.matches ? 'dark' : 'light'));
            }
            log(`System preference changed: ${e.matches ? 'dark' : 'light'}`);
        });
    }

    // ==========================================================================
    // Subscription
    // ==========================================================================

    /**
     * Subscribe to theme changes.
     * 
     * @param {Function} fn - Callback (mode, effectiveTheme) => void
     * @returns {Function} Unsubscribe function
     */
    function subscribe(fn) {
        subscribers.add(fn);
        return () => subscribers.delete(fn);
    }

    // ==========================================================================
    // Flash Prevention
    // ==========================================================================

    /**
     * Generate a script tag that prevents theme flash.
     * Include this in <head> for best results.
     * 
     * @param {string} key - Storage key (default: "theme")
     * @returns {string} Script content
     */
    function getFlashPreventionScript(key = 'theme') {
        return `
(function() {
    try {
        var mode = localStorage.getItem('${key}');
        var prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        var isDark = mode === 'dark' || (mode === 'system' && prefersDark) || (!mode && prefersDark);
        if (isDark) {
            document.documentElement.classList.add('dark');
            document.documentElement.style.colorScheme = 'dark';
        }
    } catch (e) {}
})();
        `.trim();
    }

    // ==========================================================================
    // Logging
    // ==========================================================================

    const DEBUG = typeof window !== 'undefined' && window.__PYNEXT_DEBUG__;

    function log(...args) {
        if (DEBUG) {
            console.log('[PyNext Theme]', ...args);
        }
    }

    // ==========================================================================
    // Initialization
    // ==========================================================================

    function init(config = {}) {
        // Use custom storage key if provided
        if (config.storageKey) {
            storageKey = config.storageKey;
        }
        
        // Load persisted mode
        try {
            const stored = localStorage.getItem(storageKey);
            if (stored && ['light', 'dark', 'system'].includes(stored)) {
                currentMode = stored;
            }
        } catch (e) {
            // Storage might be unavailable
        }
        
        // Apply current theme
        applyTheme(getEffectiveTheme());
        
        // Listen for system changes
        setupSystemListener();
        
        log(`Theme runtime initialized: mode=${currentMode}, effective=${getEffectiveTheme()}`);
    }

    /**
     * Initialize from hydration data.
     * 
     * @param {Object} themeConfig
     */
    function hydrate(themeConfig) {
        if (!themeConfig) return;
        
        if (themeConfig.storageKey) {
            storageKey = themeConfig.storageKey;
        }
        
        init();
    }

    // ==========================================================================
    // Export
    // ==========================================================================

    if (typeof window !== 'undefined') {
        window.__pynext__ = window.__pynext__ || {};
        
        // API
        window.__pynext__.theme = {
            setMode,
            getMode,
            getEffectiveTheme,
            getSystemPreference,
            toggle,
            cycle,
            subscribe,
            applyTheme,
            getFlashPreventionScript,
            hydrate,
        };

        // Initialize on DOM ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => init());
        } else {
            init();
        }
    }

    // Module exports
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = {
            setMode,
            getMode,
            getEffectiveTheme,
            getSystemPreference,
            toggle,
            cycle,
            subscribe,
            applyTheme,
            getFlashPreventionScript,
            hydrate,
        };
    }

})(typeof window !== 'undefined' ? window : global);

