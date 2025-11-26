/**
 * PyNext UI Core - Shared utilities for UI components
 * Size target: ~1.5 KB minified
 */
(function(g) {
    'use strict';
    
    g.__pynext__ = g.__pynext__ || {};
    g.__pynext__.ui = g.__pynext__.ui || {};
    
    var ui = g.__pynext__.ui;
    
    // Focusable element selector
    var FOCUSABLE = 'a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"]),[contenteditable]';
    
    /**
     * Get focusable elements within container
     */
    ui.getFocusable = function(el) {
        return Array.from(el.querySelectorAll(FOCUSABLE)).filter(function(e) {
            return e.offsetParent !== null;
        });
    };
    
    /**
     * Trap focus within container
     */
    ui.trapFocus = function(container, e) {
        var focusable = ui.getFocusable(container);
        if (!focusable.length) return;
        
        var first = focusable[0];
        var last = focusable[focusable.length - 1];
        
        if (e.shiftKey && document.activeElement === first) {
            e.preventDefault();
            last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
            e.preventDefault();
            first.focus();
        }
    };
    
    /**
     * Toggle element visibility with optional animation
     */
    ui.toggle = function(el, show) {
        if (show) {
            el.removeAttribute('hidden');
            el.setAttribute('data-state', 'open');
        } else {
            el.setAttribute('hidden', '');
            el.setAttribute('data-state', 'closed');
        }
    };
    
    /**
     * Close on Escape key
     */
    ui.onEscape = function(el, callback) {
        el.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                e.preventDefault();
                callback(e);
            }
        });
    };
    
    /**
     * Close on click outside
     */
    ui.onClickOutside = function(el, callback, ignore) {
        document.addEventListener('click', function(e) {
            if (!el.contains(e.target)) {
                if (ignore && e.target.closest(ignore)) return;
                callback(e);
            }
        });
    };
    
    /**
     * Initialize component by selector
     */
    ui.init = function(selector, initFn) {
        document.querySelectorAll(selector).forEach(initFn);
    };
    
    /**
     * Delegate event handler
     */
    ui.on = function(event, selector, handler) {
        document.addEventListener(event, function(e) {
            var target = e.target.closest(selector);
            if (target) handler(e, target);
        });
    };
    
    /**
     * Generate unique ID
     */
    ui.uid = function() {
        return 'pynext-' + Math.random().toString(36).substr(2, 9);
    };
    
    // Mark core as loaded
    ui._coreLoaded = true;
    
})(typeof window !== 'undefined' ? window : this);

