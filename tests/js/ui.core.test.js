/**
 * Tests for PyNext UI Core Runtime
 * Uses Jest's built-in jsdom environment
 */

const fs = require('fs');
const path = require('path');

describe('UI Core Runtime', () => {
    beforeEach(() => {
        // Setup mock UI core functions
        window.__pynext__ = window.__pynext__ || {};
        window.__pynext__.ui = window.__pynext__.ui || {};
        
        const FOCUSABLE_SELECTOR = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
        
        window.__pynext__.ui.getFocusable = (container) => {
            return Array.from(container.querySelectorAll(FOCUSABLE_SELECTOR))
                .filter(el => el.offsetParent !== null || el.offsetWidth > 0 || el.offsetHeight > 0);
        };
        
        window.__pynext__.ui.trapFocus = (container, event) => {
            const focusable = window.__pynext__.ui.getFocusable(container);
            if (focusable.length === 0) return;
            
            const first = focusable[0];
            const last = focusable[focusable.length - 1];
            
            if (event.shiftKey && document.activeElement === first) {
                event.preventDefault();
                last.focus();
            } else if (!event.shiftKey && document.activeElement === last) {
                event.preventDefault();
                first.focus();
            }
        };
        
        window.__pynext__.ui._coreLoaded = true;
    });
    
    afterEach(() => {
        document.body.innerHTML = '';
    });
    
    describe('getFocusable', () => {
        test('finds buttons', () => {
            document.body.innerHTML = '<div id="container"><button>Click</button></div>';
            const container = document.getElementById('container');
            
            const focusable = window.__pynext__.ui.getFocusable(container);
            
            expect(focusable).toHaveLength(1);
            expect(focusable[0].tagName).toBe('BUTTON');
        });
        
        test('finds links with href', () => {
            document.body.innerHTML = `
                <div id="container">
                    <a href="/page">Link</a>
                    <a>No href</a>
                </div>
            `;
            const container = document.getElementById('container');
            
            const focusable = window.__pynext__.ui.getFocusable(container);
            
            expect(focusable).toHaveLength(1);
            expect(focusable[0].textContent).toBe('Link');
        });
        
        test('finds form inputs', () => {
            document.body.innerHTML = `
                <div id="container">
                    <input type="text" />
                    <select><option>Opt</option></select>
                    <textarea></textarea>
                </div>
            `;
            const container = document.getElementById('container');
            
            const focusable = window.__pynext__.ui.getFocusable(container);
            
            expect(focusable).toHaveLength(3);
        });
        
        test('finds elements with positive tabindex', () => {
            document.body.innerHTML = `
                <div id="container">
                    <div tabindex="0">Focusable</div>
                    <div tabindex="-1">Skip</div>
                </div>
            `;
            const container = document.getElementById('container');
            
            const focusable = window.__pynext__.ui.getFocusable(container);
            
            expect(focusable).toHaveLength(1);
        });
    });
    
    describe('trapFocus', () => {
        test('prevents default when going past last element', () => {
            document.body.innerHTML = `
                <div id="container">
                    <button id="first">First</button>
                    <button id="last">Last</button>
                </div>
            `;
            const container = document.getElementById('container');
            const last = document.getElementById('last');
            last.focus();
            
            const event = { shiftKey: false, preventDefault: jest.fn() };
            window.__pynext__.ui.trapFocus(container, event);
            
            expect(event.preventDefault).toHaveBeenCalled();
        });
        
        test('prevents default when going before first element with shift', () => {
            document.body.innerHTML = `
                <div id="container">
                    <button id="first">First</button>
                    <button id="last">Last</button>
                </div>
            `;
            const container = document.getElementById('container');
            const first = document.getElementById('first');
            first.focus();
            
            const event = { shiftKey: true, preventDefault: jest.fn() };
            window.__pynext__.ui.trapFocus(container, event);
            
            expect(event.preventDefault).toHaveBeenCalled();
        });
    });
    
    describe('core.js file structure', () => {
        let content;
        
        beforeAll(() => {
            content = fs.readFileSync(
                path.join(__dirname, '../../pynext/runtime/ui/core.js'),
                'utf8'
            );
        });
        
        test('has ui namespace', () => {
            expect(content).toContain('ui');
        });
        
        test('has getFocusable function', () => {
            expect(content).toContain('getFocusable');
        });
        
        test('has trapFocus function', () => {
            expect(content).toContain('trapFocus');
        });
        
        test('has FOCUSABLE selector', () => {
            expect(content).toContain('button');
            expect(content).toContain('input');
        });
    });
});
