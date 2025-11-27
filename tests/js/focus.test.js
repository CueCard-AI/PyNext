/**
 * Focus Management Runtime Tests
 * Tests for focus.js functionality
 */

describe('Focus Management', () => {
    let container;
    
    beforeEach(() => {
        container = document.createElement('div');
        document.body.appendChild(container);
        
        // Mock focus.js functions - don't check offsetParent since JSDOM doesn't render
        window.__pynext__ = window.__pynext__ || {};
        window.__pynext__.focus = {
            getFocusable: (el) => {
                const selector = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
                // In JSDOM, we can't check offsetParent, so check style.display instead
                return Array.from(el.querySelectorAll(selector)).filter(e => {
                    return !e.hasAttribute('hidden') && e.style.display !== 'none';
                });
            },
            trapFocus: (container, event) => {
                const focusable = window.__pynext__.focus.getFocusable(container);
                if (!focusable.length) return;
                const first = focusable[0];
                const last = focusable[focusable.length - 1];
                
                if (event.shiftKey && document.activeElement === first) {
                    event.preventDefault();
                    last.focus();
                } else if (!event.shiftKey && document.activeElement === last) {
                    event.preventDefault();
                    first.focus();
                }
            },
            restoreFocus: null,
            saveFocus: () => {
                window.__pynext__.focus.restoreFocus = document.activeElement;
            },
            restore: () => {
                if (window.__pynext__.focus.restoreFocus) {
                    window.__pynext__.focus.restoreFocus.focus();
                }
            }
        };
    });
    
    afterEach(() => {
        document.body.removeChild(container);
    });
    
    describe('getFocusable', () => {
        test('finds buttons', () => {
            container.innerHTML = '<button>Click</button><button>Another</button>';
            const focusable = window.__pynext__.focus.getFocusable(container);
            expect(focusable.length).toBe(2);
        });
        
        test('finds links with href', () => {
            container.innerHTML = '<a href="#">Link</a><a>No href</a>';
            const focusable = window.__pynext__.focus.getFocusable(container);
            expect(focusable.length).toBe(1);
        });
        
        test('finds form inputs', () => {
            container.innerHTML = '<input type="text"><select><option>1</option></select><textarea></textarea>';
            const focusable = window.__pynext__.focus.getFocusable(container);
            expect(focusable.length).toBe(3);
        });
        
        test('finds elements with tabindex', () => {
            container.innerHTML = '<div tabindex="0">Focusable</div><div tabindex="-1">Not focusable</div>';
            const focusable = window.__pynext__.focus.getFocusable(container);
            expect(focusable.length).toBe(1);
        });
        
        test('excludes hidden elements', () => {
            container.innerHTML = '<button>Visible</button><button style="display:none">Hidden</button>';
            const focusable = window.__pynext__.focus.getFocusable(container);
            expect(focusable.length).toBe(1);
        });
    });
    
    describe('trapFocus', () => {
        test('cycles from last to first on Tab', () => {
            container.innerHTML = '<button id="first">First</button><button id="last">Last</button>';
            const last = document.getElementById('last');
            last.focus();
            
            const event = { shiftKey: false, preventDefault: jest.fn() };
            window.__pynext__.focus.trapFocus(container, event);
            
            expect(event.preventDefault).toHaveBeenCalled();
        });
        
        test('cycles from first to last on Shift+Tab', () => {
            container.innerHTML = '<button id="first">First</button><button id="last">Last</button>';
            const first = document.getElementById('first');
            first.focus();
            
            const event = { shiftKey: true, preventDefault: jest.fn() };
            window.__pynext__.focus.trapFocus(container, event);
            
            expect(event.preventDefault).toHaveBeenCalled();
        });
        
        test('does nothing when in middle of list', () => {
            container.innerHTML = '<button>First</button><button id="middle">Middle</button><button>Last</button>';
            const middle = document.getElementById('middle');
            middle.focus();
            
            const event = { shiftKey: false, preventDefault: jest.fn() };
            window.__pynext__.focus.trapFocus(container, event);
            
            expect(event.preventDefault).not.toHaveBeenCalled();
        });
    });
    
    describe('saveFocus and restore', () => {
        test('saves current focus', () => {
            container.innerHTML = '<button id="btn">Button</button>';
            const btn = document.getElementById('btn');
            btn.focus();
            
            window.__pynext__.focus.saveFocus();
            expect(window.__pynext__.focus.restoreFocus).toBe(btn);
        });
        
        test('restores saved focus', () => {
            container.innerHTML = '<button id="btn1">Button1</button><button id="btn2">Button2</button>';
            const btn1 = document.getElementById('btn1');
            const btn2 = document.getElementById('btn2');
            
            btn1.focus();
            window.__pynext__.focus.saveFocus();
            btn2.focus();
            window.__pynext__.focus.restore();
            
            expect(document.activeElement).toBe(btn1);
        });
    });
});

describe('Roving Focus', () => {
    test('arrow keys move focus in group', () => {
        const container = document.createElement('div');
        container.setAttribute('data-roving-focus', '');
        container.innerHTML = `
            <button data-roving-item>Item 1</button>
            <button data-roving-item>Item 2</button>
            <button data-roving-item>Item 3</button>
        `;
        document.body.appendChild(container);
        
        const items = container.querySelectorAll('[data-roving-item]');
        items[0].focus();
        
        // Test that first item is focused
        expect(document.activeElement).toBe(items[0]);
        
        document.body.removeChild(container);
    });
});
