/**
 * PyNext Tooltip Runtime
 * Size target: ~0.5 KB minified
 */
(function(g) {
    'use strict';
    
    var ui = g.__pynext__.ui;
    var showTimeout = null;
    var hideTimeout = null;
    
    function initTooltips() {
        document.querySelectorAll('[data-pynext-tooltip]').forEach(function(tooltip) {
            var trigger = tooltip.querySelector('[data-pynext-tooltip-trigger]');
            var content = tooltip.querySelector('[data-pynext-tooltip-content]');
            var delay = parseInt(tooltip.dataset.pynextTooltipDelay) || 200;
            
            if (!trigger || !content) return;
            
            trigger.addEventListener('mouseenter', function() {
                clearTimeout(hideTimeout);
                showTimeout = setTimeout(function() {
                    content.removeAttribute('hidden');
                    content.setAttribute('data-state', 'open');
                }, delay);
            });
            
            trigger.addEventListener('mouseleave', function() {
                clearTimeout(showTimeout);
                hideTimeout = setTimeout(function() {
                    content.setAttribute('hidden', '');
                    content.setAttribute('data-state', 'closed');
                }, 100);
            });
            
            trigger.addEventListener('focus', function() {
                content.removeAttribute('hidden');
                content.setAttribute('data-state', 'open');
            });
            
            trigger.addEventListener('blur', function() {
                content.setAttribute('hidden', '');
                content.setAttribute('data-state', 'closed');
            });
            
            // Escape closes
            trigger.addEventListener('keydown', function(e) {
                if (e.key === 'Escape') {
                    content.setAttribute('hidden', '');
                    content.setAttribute('data-state', 'closed');
                }
            });
        });
    }
    
    initTooltips();
    
})(window);

