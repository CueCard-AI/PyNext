/**
 * Tests for PyNext Keyboard Runtime
 */

const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

describe('Keyboard Runtime', () => {
    let dom;
    let window;
    let document;
    
    beforeEach(() => {
        dom = new JSDOM('<!DOCTYPE html><html><body></body></html>', {
            runScripts: 'dangerously',
        });
        window = dom.window;
        document = window.document;
        
        // Mock navigator
        Object.defineProperty(window.navigator, 'platform', {
            value: 'MacIntel',
            writable: true,
        });
        
        // Load the runtime
        const code = fs.readFileSync(
            path.join(__dirname, '../../pynext/runtime/keyboard.slim.js'),
            'utf8'
        );
        const script = document.createElement('script');
        script.textContent = code;
        document.body.appendChild(script);
    });
    
    afterEach(() => {
        dom.window.close();
    });
    
    function pressKey(key, options = {}) {
        const event = new window.KeyboardEvent('keydown', {
            key: key,
            metaKey: options.meta || false,
            ctrlKey: options.ctrl || false,
            altKey: options.alt || false,
            shiftKey: options.shift || false,
            bubbles: true,
        });
        (options.target || document).dispatchEvent(event);
        return event;
    }
    
    describe('register', () => {
        test('registers shortcut', () => {
            let called = false;
            
            window.__pynext__.keyboard.registerHandler('handler1', () => {
                called = true;
            });
            
            window.__pynext__.keyboard.register({
                id: 'shortcut1',
                key: 'k',
                modifiers: ['meta'],
                handlerId: 'handler1',
            });
            
            pressKey('k', { meta: true });
            expect(called).toBe(true);
        });
        
        test('does not fire without modifier', () => {
            let called = false;
            
            window.__pynext__.keyboard.registerHandler('handler2', () => {
                called = true;
            });
            
            window.__pynext__.keyboard.register({
                id: 'shortcut2',
                key: 's',
                modifiers: ['meta'],
                handlerId: 'handler2',
            });
            
            pressKey('s'); // No meta key
            expect(called).toBe(false);
        });
        
        test('matches ctrl modifier', () => {
            let called = false;
            
            window.__pynext__.keyboard.registerHandler('handler3', () => {
                called = true;
            });
            
            window.__pynext__.keyboard.register({
                id: 'shortcut3',
                key: 'z',
                modifiers: ['ctrl'],
                handlerId: 'handler3',
            });
            
            pressKey('z', { ctrl: true });
            expect(called).toBe(true);
        });
        
        test('matches multiple modifiers', () => {
            let called = false;
            
            window.__pynext__.keyboard.registerHandler('handler4', () => {
                called = true;
            });
            
            window.__pynext__.keyboard.register({
                id: 'shortcut4',
                key: 'k',
                modifiers: ['meta', 'shift'],
                handlerId: 'handler4',
            });
            
            pressKey('k', { meta: true, shift: true });
            expect(called).toBe(true);
        });
    });
    
    describe('unregister', () => {
        test('unregisters shortcut', () => {
            let count = 0;
            
            window.__pynext__.keyboard.registerHandler('handler5', () => {
                count++;
            });
            
            window.__pynext__.keyboard.register({
                id: 'shortcut5',
                key: 'x',
                modifiers: ['meta'],
                handlerId: 'handler5',
            });
            
            pressKey('x', { meta: true });
            expect(count).toBe(1);
            
            window.__pynext__.keyboard.unregister('shortcut5');
            
            pressKey('x', { meta: true });
            expect(count).toBe(1); // Still 1, not 2
        });
    });
    
    describe('context handling', () => {
        test('skips input elements by default', () => {
            let called = false;
            
            window.__pynext__.keyboard.registerHandler('handler6', () => {
                called = true;
            });
            
            window.__pynext__.keyboard.register({
                id: 'shortcut6',
                key: 'k',
                modifiers: ['meta'],
                handlerId: 'handler6',
                context: 'global',
            });
            
            const input = document.createElement('input');
            document.body.appendChild(input);
            
            pressKey('k', { meta: true, target: input });
            expect(called).toBe(false);
        });
    });
    
    describe('sequences', () => {
        test('fires on sequence completion', async () => {
            let called = false;
            
            window.__pynext__.keyboard.registerHandler('seqHandler', () => {
                called = true;
            });
            
            window.__pynext__.keyboard.registerSeq({
                id: 'seq1',
                keys: ['g', 'd'],
                handlerId: 'seqHandler',
            });
            
            pressKey('g');
            pressKey('d');
            
            expect(called).toBe(true);
        });
        
        test('resets on wrong key', () => {
            let called = false;
            
            window.__pynext__.keyboard.registerHandler('seqHandler2', () => {
                called = true;
            });
            
            window.__pynext__.keyboard.registerSeq({
                id: 'seq2',
                keys: ['a', 'b', 'c'],
                handlerId: 'seqHandler2',
            });
            
            pressKey('a');
            pressKey('x'); // Wrong key
            pressKey('c');
            
            expect(called).toBe(false);
        });
    });
    
    describe('hydrate', () => {
        test('hydrates from data object', () => {
            let called = false;
            
            window.__pynext__.keyboard.registerHandler('h1', () => {
                called = true;
            });
            
            window.__pynext__.keyboard.hydrate({
                shortcuts: [{
                    id: 's1',
                    key: 'p',
                    modifiers: ['meta'],
                    handlerId: 'h1',
                }]
            });
            
            pressKey('p', { meta: true });
            expect(called).toBe(true);
        });
    });
    
    describe('platform detection', () => {
        test('detects Mac', () => {
            expect(window.__pynext__.keyboard.isMac).toBe(true);
        });
    });
});

