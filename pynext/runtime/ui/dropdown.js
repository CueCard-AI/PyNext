/**
 * PyNext Dropdown Menu Runtime
 * Size target: ~0.8 KB minified
 */
(function(g) {
    'use strict';
    
    var ui = g.__pynext__.ui;
    var activeDropdown = null;
    
    function initDropdowns() {
        // Trigger click
        ui.on('click', '[data-pynext-dropdown-trigger]', function(e, trigger) {
            e.stopPropagation();
            var dropdown = trigger.closest('[data-pynext-dropdown]');
            var content = dropdown.querySelector('[data-pynext-dropdown-content]');
            
            if (activeDropdown && activeDropdown !== content) {
                closeDropdown(activeDropdown);
            }
            
            if (content.hasAttribute('hidden')) {
                openDropdown(content, trigger);
            } else {
                closeDropdown(content);
            }
        });
        
        // Item click
        ui.on('click', '[data-pynext-dropdown-item]', function(e, item) {
            if (item.hasAttribute('disabled')) {
                e.preventDefault();
                return;
            }
            var dropdown = item.closest('[data-pynext-dropdown-content]');
            if (dropdown) closeDropdown(dropdown);
        });
        
        // Close on outside click
        document.addEventListener('click', function() {
            if (activeDropdown) closeDropdown(activeDropdown);
        });
        
        // Keyboard navigation
        document.addEventListener('keydown', function(e) {
            if (!activeDropdown) return;
            
            var items = activeDropdown.querySelectorAll('[data-pynext-dropdown-item]:not([disabled])');
            var current = Array.from(items).indexOf(document.activeElement);
            
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                var next = current < items.length - 1 ? current + 1 : 0;
                items[next].focus();
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                var prev = current > 0 ? current - 1 : items.length - 1;
                items[prev].focus();
            } else if (e.key === 'Escape') {
                closeDropdown(activeDropdown);
            }
        });
    }
    
    function openDropdown(content, trigger) {
        content.removeAttribute('hidden');
        content.setAttribute('data-state', 'open');
        activeDropdown = content;
        
        // Focus first item
        var firstItem = content.querySelector('[data-pynext-dropdown-item]:not([disabled])');
        if (firstItem) firstItem.focus();
    }
    
    function closeDropdown(content) {
        content.setAttribute('hidden', '');
        content.setAttribute('data-state', 'closed');
        if (activeDropdown === content) activeDropdown = null;
    }
    
    initDropdowns();
    ui.dropdown = { open: openDropdown, close: closeDropdown };
    
})(window);

