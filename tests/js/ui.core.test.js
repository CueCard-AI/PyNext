/**
 * Tests for PyNext UI Core Runtime
 */

const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

describe('UI Core Runtime', () => {
    let dom;
    let window;
    let document;
    
    beforeEach(() => {
        dom = new JSDOM('<!DOCTYPE html><html><body></body></html>', {
            runScripts: 'dangerously',
        });
        window = dom.window;
        document = window.document;
        
        // Load the runtime
        const code = fs.readFileSync(
            path.join(__dirname, '../../pynext/runtime/ui/core.js'),
            'utf8'
        );
        const script = document.createElement('script');
        script.textContent = code;
        document.body.appendChild(script);
    });
    
    afterEach(() => {
        dom.window.close();
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
        });
        
        test('excludes disabled inputs', () => {
            document.body.innerHTML = `
                <div id="container">
                    <input type="text" />
                    <input type="text" disabled />
                </div>
            `;
            const container = document.getElementById('container');
            
            const focusable = window.__pynext__.ui.getFocusable(container);
            
            expect(focusable).toHaveLength(1);
        });
        
        test('finds elements with tabindex', () => {
            document.body.innerHTML = `
                <div id="container">
                    <div tabindex="0">Focusable div</div>
                    <div tabindex="-1">Not focusable</div>
                </div>
            `;
            const container = document.getElementById('container');
            
            const focusable = window.__pynext__.ui.getFocusable(container);
            
            expect(focusable).toHaveLength(1);
        });
    });
    
    describe('toggle', () => {
        test('shows element', () => {
            const div = document.createElement('div');
            div.setAttribute('hidden', '');
            document.body.appendChild(div);
            
            window.__pynext__.ui.toggle(div, true);
            
            expect(div.hasAttribute('hidden')).toBe(false);
            expect(div.getAttribute('data-state')).toBe('open');
        });
        
        test('hides element', () => {
            const div = document.createElement('div');
            document.body.appendChild(div);
            
            window.__pynext__.ui.toggle(div, false);
            
            expect(div.hasAttribute('hidden')).toBe(true);
            expect(div.getAttribute('data-state')).toBe('closed');
        });
    });
    
    describe('onEscape', () => {
        test('calls callback on escape', () => {
            let called = false;
            const div = document.createElement('div');
            document.body.appendChild(div);
            
            window.__pynext__.ui.onEscape(div, () => {
                called = true;
            });
            
            const event = new window.KeyboardEvent('keydown', {
                key: 'Escape',
                bubbles: true,
            });
            div.dispatchEvent(event);
            
            expect(called).toBe(true);
        });
        
        test('ignores other keys', () => {
            let called = false;
            const div = document.createElement('div');
            document.body.appendChild(div);
            
            window.__pynext__.ui.onEscape(div, () => {
                called = true;
            });
            
            const event = new window.KeyboardEvent('keydown', {
                key: 'Enter',
                bubbles: true,
            });
            div.dispatchEvent(event);
            
            expect(called).toBe(false);
        });
    });
    
    describe('uid', () => {
        test('generates unique IDs', () => {
            const id1 = window.__pynext__.ui.uid();
            const id2 = window.__pynext__.ui.uid();
            
            expect(id1).not.toBe(id2);
            expect(id1).toMatch(/^pynext-[a-z0-9]+$/);
        });
    });
    
    describe('event delegation', () => {
        test('on() delegates events', () => {
            document.body.innerHTML = `
                <div id="container">
                    <button class="btn">Click me</button>
                </div>
            `;
            
            let clicked = false;
            window.__pynext__.ui.on('click', '.btn', () => {
                clicked = true;
            });
            
            const btn = document.querySelector('.btn');
            btn.click();
            
            expect(clicked).toBe(true);
        });
        
        test('on() passes target to handler', () => {
            document.body.innerHTML = `<button data-id="123">Click</button>`;
            
            let targetId = null;
            window.__pynext__.ui.on('click', 'button', (e, target) => {
                targetId = target.dataset.id;
            });
            
            document.querySelector('button').click();
            
            expect(targetId).toBe('123');
        });
    });
    
    describe('init', () => {
        test('initializes matching elements', () => {
            document.body.innerHTML = `
                <div data-component></div>
                <div data-component></div>
                <div></div>
            `;
            
            let count = 0;
            window.__pynext__.ui.init('[data-component]', () => {
                count++;
            });
            
            expect(count).toBe(2);
        });
    });
});

