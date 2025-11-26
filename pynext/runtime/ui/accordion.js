/**
 * PyNext Accordion Runtime
 * Size target: ~0.5 KB minified
 */
(function(g) {
    'use strict';
    
    var ui = g.__pynext__.ui;
    
    function initAccordions() {
        ui.on('click', '[data-pynext-accordion-trigger]', function(e, trigger) {
            var item = trigger.closest('[data-pynext-accordion-item]');
            var accordion = item.closest('[data-pynext-accordion]');
            var content = item.querySelector('[data-pynext-accordion-content]');
            var isOpen = !content.hasAttribute('hidden');
            var type = accordion.dataset.pynextAccordion || 'single';
            
            // Close others if single mode
            if (type === 'single' && !isOpen) {
                accordion.querySelectorAll('[data-pynext-accordion-content]').forEach(function(c) {
                    c.setAttribute('hidden', '');
                    c.setAttribute('data-state', 'closed');
                });
                accordion.querySelectorAll('[data-pynext-accordion-trigger]').forEach(function(t) {
                    t.setAttribute('data-state', 'closed');
                    t.setAttribute('aria-expanded', 'false');
                });
            }
            
            // Toggle current
            if (isOpen) {
                content.setAttribute('hidden', '');
                content.setAttribute('data-state', 'closed');
                trigger.setAttribute('data-state', 'closed');
                trigger.setAttribute('aria-expanded', 'false');
            } else {
                content.removeAttribute('hidden');
                content.setAttribute('data-state', 'open');
                trigger.setAttribute('data-state', 'open');
                trigger.setAttribute('aria-expanded', 'true');
            }
        });
    }
    
    initAccordions();
    
})(window);

