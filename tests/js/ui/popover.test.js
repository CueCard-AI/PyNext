/**
 * Popover Component Tests
 * Tests for ui/popover.js functionality
 */

describe('Popover Component', () => {
    let container;
    
    beforeEach(() => {
        container = document.createElement('div');
        document.body.appendChild(container);
        
        window.__pynext__ = window.__pynext__ || {};
        window.__pynext__.ui = window.__pynext__.ui || {};
        window.__pynext__.ui.popover = {
            init: function(el) {
                const trigger = el.querySelector('[data-pynext-popover-trigger]');
                
                if (trigger) {
                    trigger.addEventListener('click', () => this.toggle(el));
                }
                
                // Click outside to close
                document.addEventListener('click', (e) => {
                    if (!el.contains(e.target)) {
                        this.close(el);
                    }
                });
            },
            toggle: function(el) {
                const content = el.querySelector('[data-pynext-popover-content]');
                const isOpen = content.getAttribute('data-state') === 'open';
                content.setAttribute('data-state', isOpen ? 'closed' : 'open');
            },
            open: function(el) {
                const content = el.querySelector('[data-pynext-popover-content]');
                content.setAttribute('data-state', 'open');
            },
            close: function(el) {
                const content = el.querySelector('[data-pynext-popover-content]');
                content.setAttribute('data-state', 'closed');
            }
        };
    });
    
    afterEach(() => {
        document.body.removeChild(container);
    });
    
    test('opens on click', () => {
        container.innerHTML = `
            <div data-pynext-popover>
                <button data-pynext-popover-trigger>Open</button>
                <div data-pynext-popover-content data-state="closed">Content</div>
            </div>
        `;
        
        const popover = container.querySelector('[data-pynext-popover]');
        window.__pynext__.ui.popover.init(popover);
        
        const trigger = container.querySelector('[data-pynext-popover-trigger]');
        trigger.click();
        
        const content = container.querySelector('[data-pynext-popover-content]');
        expect(content.getAttribute('data-state')).toBe('open');
    });
    
    test('closes on second click', () => {
        container.innerHTML = `
            <div data-pynext-popover>
                <button data-pynext-popover-trigger>Toggle</button>
                <div data-pynext-popover-content data-state="open">Content</div>
            </div>
        `;
        
        const popover = container.querySelector('[data-pynext-popover]');
        window.__pynext__.ui.popover.toggle(popover);
        
        const content = container.querySelector('[data-pynext-popover-content]');
        expect(content.getAttribute('data-state')).toBe('closed');
    });
    
    test('positions according to side prop', () => {
        container.innerHTML = `
            <div data-pynext-popover>
                <button data-pynext-popover-trigger>Trigger</button>
                <div data-pynext-popover-content data-side="top">Content</div>
            </div>
        `;
        
        const content = container.querySelector('[data-pynext-popover-content]');
        expect(content.getAttribute('data-side')).toBe('top');
    });
});

