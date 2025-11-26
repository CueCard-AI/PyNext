/**
 * PyNext Popover Runtime
 * Size target: ~0.5 KB minified
 */
(function(g) {
    'use strict';
    
    var ui = g.__pynext__.ui;
    var activePopover = null;
    
    function initPopovers() {
        ui.on('click', '[data-pynext-popover-trigger]', function(e, trigger) {
            e.stopPropagation();
            var popover = trigger.closest('[data-pynext-popover]');
            var content = popover.querySelector('[data-pynext-popover-content]');
            
            if (activePopover && activePopover !== content) {
                closePopover(activePopover);
            }
            
            if (content.hasAttribute('hidden')) {
                openPopover(content);
            } else {
                closePopover(content);
            }
        });
        
        // Close on outside click
        document.addEventListener('click', function(e) {
            if (activePopover && !activePopover.contains(e.target)) {
                closePopover(activePopover);
            }
        });
        
        // Close on Escape
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && activePopover) {
                closePopover(activePopover);
            }
        });
    }
    
    function openPopover(content) {
        content.removeAttribute('hidden');
        content.setAttribute('data-state', 'open');
        activePopover = content;
        
        var focusable = ui.getFocusable(content);
        if (focusable.length) focusable[0].focus();
    }
    
    function closePopover(content) {
        content.setAttribute('hidden', '');
        content.setAttribute('data-state', 'closed');
        if (activePopover === content) activePopover = null;
    }
    
    initPopovers();
    ui.popover = { open: openPopover, close: closePopover };
    
})(window);

