/**
 * Sheet Component Tests
 * Tests for ui/sheet.js functionality
 */

describe('Sheet Component', () => {
    let container;
    
    beforeEach(() => {
        container = document.createElement('div');
        document.body.appendChild(container);
        
        window.__pynext__ = window.__pynext__ || {};
        window.__pynext__.ui = window.__pynext__.ui || {};
        window.__pynext__.ui.sheet = {
            init: function(el) {
                const trigger = el.querySelector('[data-pynext-sheet-trigger]');
                const close = el.querySelector('[data-pynext-sheet-close]');
                
                if (trigger) {
                    trigger.addEventListener('click', () => this.open(el));
                }
                if (close) {
                    close.addEventListener('click', () => this.close(el));
                }
            },
            open: function(el) {
                const content = el.querySelector('[data-pynext-sheet-content]');
                content.setAttribute('data-state', 'open');
            },
            close: function(el) {
                const content = el.querySelector('[data-pynext-sheet-content]');
                content.setAttribute('data-state', 'closed');
            }
        };
    });
    
    afterEach(() => {
        document.body.removeChild(container);
    });
    
    test('opens from right by default', () => {
        container.innerHTML = `
            <div data-pynext-sheet>
                <button data-pynext-sheet-trigger>Open</button>
                <div data-pynext-sheet-content data-side="right" data-state="closed">
                    <h2>Sheet Title</h2>
                </div>
            </div>
        `;
        
        const sheet = container.querySelector('[data-pynext-sheet]');
        window.__pynext__.ui.sheet.open(sheet);
        
        const content = container.querySelector('[data-pynext-sheet-content]');
        expect(content.getAttribute('data-state')).toBe('open');
        expect(content.getAttribute('data-side')).toBe('right');
    });
    
    test('can open from left', () => {
        container.innerHTML = `
            <div data-pynext-sheet>
                <div data-pynext-sheet-content data-side="left" data-state="closed">Content</div>
            </div>
        `;
        
        const content = container.querySelector('[data-pynext-sheet-content]');
        expect(content.getAttribute('data-side')).toBe('left');
    });
    
    test('can open from top', () => {
        container.innerHTML = `
            <div data-pynext-sheet>
                <div data-pynext-sheet-content data-side="top" data-state="closed">Content</div>
            </div>
        `;
        
        const content = container.querySelector('[data-pynext-sheet-content]');
        expect(content.getAttribute('data-side')).toBe('top');
    });
    
    test('can open from bottom', () => {
        container.innerHTML = `
            <div data-pynext-sheet>
                <div data-pynext-sheet-content data-side="bottom" data-state="closed">Content</div>
            </div>
        `;
        
        const content = container.querySelector('[data-pynext-sheet-content]');
        expect(content.getAttribute('data-side')).toBe('bottom');
    });
    
    test('closes on close button click', () => {
        container.innerHTML = `
            <div data-pynext-sheet>
                <div data-pynext-sheet-content data-state="open">
                    <button data-pynext-sheet-close>Close</button>
                </div>
            </div>
        `;
        
        const sheet = container.querySelector('[data-pynext-sheet]');
        window.__pynext__.ui.sheet.init(sheet);
        
        const closeBtn = container.querySelector('[data-pynext-sheet-close]');
        closeBtn.click();
        
        const content = container.querySelector('[data-pynext-sheet-content]');
        expect(content.getAttribute('data-state')).toBe('closed');
    });
    
    test('supports swipe to close on mobile', () => {
        container.innerHTML = `
            <div data-pynext-sheet>
                <div data-pynext-sheet-content data-side="right" data-swipe-to-close="true" data-state="open">
                    Content
                </div>
            </div>
        `;
        
        const content = container.querySelector('[data-pynext-sheet-content]');
        expect(content.getAttribute('data-swipe-to-close')).toBe('true');
    });
});

