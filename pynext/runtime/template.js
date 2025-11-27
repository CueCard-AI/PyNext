/**
 * Template Runtime - Handles template transitions.
 * 
 * Templates remount on every navigation, unlike layouts which persist.
 * This enables page transition animations and state reset.
 * 
 * SolidJS Principle: Single DOM operation (innerHTML replace)
 * Size: ~2KB minified
 */
(function(g) {
    'use strict';
    
    /**
     * Get template configuration from element data attributes.
     * 
     * @param {HTMLElement} el - Template element
     * @returns {Object} Configuration object
     */
    function getConfig(el) {
        return {
            name: el.dataset.pynextTemplate,
            animate: el.dataset.animate === 'true',
            duration: parseInt(el.dataset.duration) || 200,
            resetScroll: el.dataset.resetScroll === 'true',
            transition: el.dataset.transition || 'fade',
            easing: el.dataset.easing || 'ease-out',
        };
    }
    
    /**
     * Sleep for specified milliseconds.
     * 
     * @param {number} ms - Milliseconds to sleep
     * @returns {Promise} Resolves after delay
     */
    function sleep(ms) {
        return new Promise(function(resolve) {
            setTimeout(resolve, ms);
        });
    }
    
    /**
     * Apply exit animation to element.
     * 
     * @param {HTMLElement} el - Element to animate
     * @param {Object} config - Template configuration
     * @returns {Promise} Resolves when animation completes
     */
    async function animateExit(el, config) {
        if (!config.animate) return;
        
        var duration = config.duration / 2; // Half duration for exit
        
        // Set transition
        el.style.transition = 'opacity ' + duration + 'ms ' + config.easing + 
                             ', transform ' + duration + 'ms ' + config.easing;
        
        // Add exit class
        el.classList.add('template-exit');
        
        // Apply exit styles based on transition type
        switch (config.transition) {
            case 'fade':
                el.style.opacity = '0';
                break;
            case 'slide-left':
                el.style.transform = 'translateX(-100%)';
                el.style.opacity = '0';
                break;
            case 'slide-right':
                el.style.transform = 'translateX(100%)';
                el.style.opacity = '0';
                break;
            case 'slide-up':
                el.style.transform = 'translateY(-100%)';
                el.style.opacity = '0';
                break;
            case 'slide-down':
                el.style.transform = 'translateY(100%)';
                el.style.opacity = '0';
                break;
            case 'scale':
                el.style.transform = 'scale(0.9)';
                el.style.opacity = '0';
                break;
        }
        
        await sleep(duration);
    }
    
    /**
     * Apply enter animation to element.
     * 
     * @param {HTMLElement} el - Element to animate
     * @param {Object} config - Template configuration
     * @returns {Promise} Resolves when animation completes
     */
    async function animateEnter(el, config) {
        if (!config.animate) return;
        
        var duration = config.duration / 2;
        
        // Set initial enter state
        el.classList.add('template-enter');
        
        switch (config.transition) {
            case 'fade':
                el.style.opacity = '0';
                break;
            case 'slide-left':
                el.style.transform = 'translateX(100%)';
                el.style.opacity = '0';
                break;
            case 'slide-right':
                el.style.transform = 'translateX(-100%)';
                el.style.opacity = '0';
                break;
            case 'slide-up':
                el.style.transform = 'translateY(100%)';
                el.style.opacity = '0';
                break;
            case 'slide-down':
                el.style.transform = 'translateY(-100%)';
                el.style.opacity = '0';
                break;
            case 'scale':
                el.style.transform = 'scale(1.1)';
                el.style.opacity = '0';
                break;
        }
        
        // Force reflow
        el.offsetHeight;
        
        // Set transition
        el.style.transition = 'opacity ' + duration + 'ms ' + config.easing + 
                             ', transform ' + duration + 'ms ' + config.easing;
        
        // Animate to final state
        el.classList.remove('template-enter');
        el.classList.add('template-enter-active');
        el.style.opacity = '1';
        el.style.transform = '';
        
        await sleep(duration);
        
        // Cleanup
        el.classList.remove('template-enter-active');
        el.style.transition = '';
        el.style.opacity = '';
        el.style.transform = '';
    }
    
    /**
     * Transition to new template content.
     * 
     * @param {string} selector - Template selector
     * @param {string} newContent - New HTML content
     * @returns {Promise} Resolves when transition completes
     */
    async function transition(selector, newContent) {
        var el = document.querySelector(selector);
        if (!el) {
            console.warn('[PyNext Template] Element not found:', selector);
            return;
        }
        
        var config = getConfig(el);
        
        // Exit animation
        await animateExit(el, config);
        
        // Replace content
        el.innerHTML = newContent;
        
        // Enter animation
        await animateEnter(el, config);
        
        // Reset scroll if configured
        if (config.resetScroll) {
            window.scrollTo(0, 0);
        }
        
        // Re-hydrate new content
        if (g.__pynext__ && g.__pynext__.hydrate) {
            g.__pynext__.hydrate();
        }
        
        // Dispatch event for external listeners
        el.dispatchEvent(new CustomEvent('pynext:template-transition', {
            bubbles: true,
            detail: { name: config.name }
        }));
    }
    
    /**
     * Transition by template name.
     * 
     * @param {string} name - Template name
     * @param {string} newContent - New HTML content
     * @returns {Promise}
     */
    async function transitionByName(name, newContent) {
        return transition('[data-pynext-template="' + name + '"]', newContent);
    }
    
    /**
     * Get all template elements on the page.
     * 
     * @returns {HTMLElement[]} Array of template elements
     */
    function getTemplates() {
        return Array.from(document.querySelectorAll('[data-pynext-template]'));
    }
    
    /**
     * Get template configuration by name.
     * 
     * @param {string} name - Template name
     * @returns {Object|null} Configuration or null
     */
    function getTemplateConfig(name) {
        var el = document.querySelector('[data-pynext-template="' + name + '"]');
        return el ? getConfig(el) : null;
    }
    
    /**
     * Initialize templates on page load.
     * Sets up any necessary event listeners.
     */
    function init() {
        // Templates are already rendered by server
        // This is called to set up any client-side behavior
        
        var templates = getTemplates();
        templates.forEach(function(el) {
            // Mark as initialized
            el.dataset.pynextTemplateInit = 'true';
        });
    }
    
    // Export API
    g.__pynext__ = g.__pynext__ || {};
    g.__pynext__.template = {
        transition: transition,
        transitionByName: transitionByName,
        getTemplates: getTemplates,
        getConfig: getTemplateConfig,
        animateExit: animateExit,
        animateEnter: animateEnter,
    };
    
    // Auto-init on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // Re-init on Turbo/HTMX navigation
    document.addEventListener('turbo:load', init);
    document.addEventListener('htmx:afterSettle', init);
    
})(typeof window !== 'undefined' ? window : this);

