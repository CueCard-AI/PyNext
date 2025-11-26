/**
 * PyNext UI Loader
 * Dynamically loads only the component modules needed for the page
 * Size target: ~0.5 KB minified
 */
(function(g) {
    'use strict';
    
    var loaded = {};
    var basePath = '/static/pynext/ui/';
    
    // Map data attributes to module names
    var componentMap = {
        'pynext-dialog': 'dialog',
        'pynext-alertdialog': 'dialog',
        'pynext-dropdown': 'dropdown',
        'pynext-tabs': 'tabs',
        'pynext-accordion': 'accordion',
        'pynext-switch': 'forms',
        'pynext-checkbox': 'forms',
        'pynext-toggle': 'forms',
        'pynext-toggle-group': 'forms',
        'pynext-radio-group': 'forms',
        'pynext-tooltip': 'tooltip',
        'pynext-popover': 'popover',
        'pynext-sheet': 'sheet',
        'pynext-combobox': 'combobox',
        'pynext-command': 'command',
        'pynext-calendar': 'calendar',
        'pynext-datepicker': 'calendar',
        'pynext-datatable': 'datatable',
        'pynext-file-upload': 'fileupload'
    };
    
    /**
     * Scan page for PyNext components and load required modules
     */
    function scan() {
        var needed = new Set();
        
        // Find all data-pynext-* attributes
        document.querySelectorAll('*').forEach(function(el) {
            Array.from(el.attributes).forEach(function(attr) {
                if (attr.name.startsWith('data-')) {
                    var key = attr.name.replace('data-', '');
                    if (componentMap[key]) {
                        needed.add(componentMap[key]);
                    }
                }
            });
        });
        
        // Load required modules
        needed.forEach(function(module) {
            load(module);
        });
    }
    
    /**
     * Load a component module
     */
    function load(name) {
        if (loaded[name]) return Promise.resolve();
        
        loaded[name] = true;
        
        return new Promise(function(resolve, reject) {
            var script = document.createElement('script');
            script.src = basePath + name + '.js';
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }
    
    /**
     * Configure the loader
     */
    function configure(options) {
        if (options.basePath) basePath = options.basePath;
    }
    
    // Ensure core is loaded first
    function ensureCore() {
        if (g.__pynext__ && g.__pynext__.ui && g.__pynext__.ui._coreLoaded) {
            return Promise.resolve();
        }
        return load('core');
    }
    
    // Auto-scan on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            ensureCore().then(scan);
        });
    } else {
        ensureCore().then(scan);
    }
    
    // Re-scan on dynamic content (HTMX, Turbo, etc.)
    document.addEventListener('turbo:load', scan);
    document.addEventListener('htmx:afterSettle', scan);
    
    // Expose API
    g.__pynext__ = g.__pynext__ || {};
    g.__pynext__.uiLoader = {
        load: load,
        scan: scan,
        configure: configure
    };
    
})(window);

