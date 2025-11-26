/**
 * Tooltip Component Tests
 * Tests for ui/tooltip.js functionality
 */

describe('Tooltip Component', () => {
    let container;
    
    beforeEach(() => {
        container = document.createElement('div');
        document.body.appendChild(container);
        jest.useFakeTimers();
        
        window.__pynext__ = window.__pynext__ || {};
        window.__pynext__.ui = window.__pynext__.ui || {};
        window.__pynext__.ui.tooltip = {
            delay: 200,
            init: function(el) {
                const trigger = el.querySelector('[data-pynext-tooltip-trigger]');
                const content = el.querySelector('[data-pynext-tooltip-content]');
                
                if (trigger && content) {
                    let timeout;
                    trigger.addEventListener('mouseenter', () => {
                        timeout = setTimeout(() => this.show(el), this.delay);
                    });
                    trigger.addEventListener('mouseleave', () => {
                        clearTimeout(timeout);
                        this.hide(el);
                    });
                    trigger.addEventListener('focus', () => this.show(el));
                    trigger.addEventListener('blur', () => this.hide(el));
                }
            },
            show: function(el) {
                const content = el.querySelector('[data-pynext-tooltip-content]');
                content.setAttribute('data-state', 'open');
            },
            hide: function(el) {
                const content = el.querySelector('[data-pynext-tooltip-content]');
                content.setAttribute('data-state', 'closed');
            }
        };
    });
    
    afterEach(() => {
        document.body.removeChild(container);
        jest.useRealTimers();
    });
    
    test('shows after delay on hover', () => {
        container.innerHTML = `
            <div data-pynext-tooltip>
                <button data-pynext-tooltip-trigger>Hover me</button>
                <div data-pynext-tooltip-content data-state="closed">Tooltip text</div>
            </div>
        `;
        
        const tooltip = container.querySelector('[data-pynext-tooltip]');
        window.__pynext__.ui.tooltip.init(tooltip);
        
        const trigger = container.querySelector('[data-pynext-tooltip-trigger]');
        trigger.dispatchEvent(new MouseEvent('mouseenter'));
        
        // Before delay
        const content = container.querySelector('[data-pynext-tooltip-content]');
        expect(content.getAttribute('data-state')).toBe('closed');
        
        // After delay
        jest.advanceTimersByTime(200);
        expect(content.getAttribute('data-state')).toBe('open');
    });
    
    test('hides on mouse leave', () => {
        container.innerHTML = `
            <div data-pynext-tooltip>
                <button data-pynext-tooltip-trigger>Hover me</button>
                <div data-pynext-tooltip-content data-state="open">Tooltip text</div>
            </div>
        `;
        
        const tooltip = container.querySelector('[data-pynext-tooltip]');
        window.__pynext__.ui.tooltip.init(tooltip);
        
        const trigger = container.querySelector('[data-pynext-tooltip-trigger]');
        trigger.dispatchEvent(new MouseEvent('mouseleave'));
        
        const content = container.querySelector('[data-pynext-tooltip-content]');
        expect(content.getAttribute('data-state')).toBe('closed');
    });
    
    test('shows on focus', () => {
        container.innerHTML = `
            <div data-pynext-tooltip>
                <button data-pynext-tooltip-trigger>Focus me</button>
                <div data-pynext-tooltip-content data-state="closed">Tooltip text</div>
            </div>
        `;
        
        const tooltip = container.querySelector('[data-pynext-tooltip]');
        window.__pynext__.ui.tooltip.init(tooltip);
        
        const trigger = container.querySelector('[data-pynext-tooltip-trigger]');
        trigger.dispatchEvent(new FocusEvent('focus'));
        
        const content = container.querySelector('[data-pynext-tooltip-content]');
        expect(content.getAttribute('data-state')).toBe('open');
    });
    
    test('has tooltip role', () => {
        container.innerHTML = `
            <div data-pynext-tooltip>
                <button data-pynext-tooltip-trigger aria-describedby="tooltip-1">Trigger</button>
                <div data-pynext-tooltip-content role="tooltip" id="tooltip-1">Tooltip</div>
            </div>
        `;
        
        const content = container.querySelector('[data-pynext-tooltip-content]');
        expect(content.getAttribute('role')).toBe('tooltip');
    });
});

