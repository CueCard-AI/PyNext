/**
 * Tests for PyNext Theme Runtime
 */

const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

describe('Theme Runtime', () => {
    let dom;
    let window;
    let document;
    
    beforeEach(() => {
        dom = new JSDOM('<!DOCTYPE html><html><body></body></html>', {
            runScripts: 'dangerously',
        });
        window = dom.window;
        document = window.document;
        
        // Mock matchMedia
        window.matchMedia = (query) => ({
            matches: query === '(prefers-color-scheme: dark)',
            media: query,
            onchange: null,
            addListener: () => {},
            removeListener: () => {},
            addEventListener: () => {},
            removeEventListener: () => {},
            dispatchEvent: () => true,
        });
        
        // Mock localStorage
        const storage = {};
        window.localStorage = {
            getItem: (key) => storage[key] || null,
            setItem: (key, value) => { storage[key] = String(value); },
            removeItem: (key) => { delete storage[key]; },
            clear: () => { Object.keys(storage).forEach(k => delete storage[k]); },
        };
        
        // Load the runtime
        const code = fs.readFileSync(
            path.join(__dirname, '../../pynext/runtime/theme.slim.js'),
            'utf8'
        );
        const script = document.createElement('script');
        script.textContent = code;
        document.body.appendChild(script);
    });
    
    afterEach(() => {
        dom.window.close();
    });
    
    describe('get/set', () => {
        test('returns system by default', () => {
            expect(window.__pynext__.theme.get()).toBe('system');
        });
        
        test('set stores theme', () => {
            window.__pynext__.theme.set('dark');
            expect(window.__pynext__.theme.get()).toBe('dark');
        });
        
        test('persists to localStorage', () => {
            window.__pynext__.theme.set('light');
            expect(window.localStorage.getItem('pynext-theme')).toBe('light');
        });
    });
    
    describe('toggle', () => {
        test('toggles dark to light', () => {
            window.__pynext__.theme.set('dark');
            window.__pynext__.theme.toggle();
            expect(window.__pynext__.theme.get()).toBe('light');
        });
        
        test('toggles light to dark', () => {
            window.__pynext__.theme.set('light');
            window.__pynext__.theme.toggle();
            expect(window.__pynext__.theme.get()).toBe('dark');
        });
    });
    
    describe('DOM updates', () => {
        test('adds dark class for dark theme', () => {
            window.__pynext__.theme.set('dark');
            expect(document.documentElement.classList.contains('dark')).toBe(true);
        });
        
        test('removes dark class for light theme', () => {
            window.__pynext__.theme.set('dark');
            window.__pynext__.theme.set('light');
            expect(document.documentElement.classList.contains('dark')).toBe(false);
        });
        
        test('sets data-theme attribute', () => {
            window.__pynext__.theme.set('dark');
            expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
        });
    });
    
    describe('subscribe', () => {
        test('notifies on theme change', () => {
            let notifications = [];
            
            window.__pynext__.theme.subscribe((theme, resolved) => {
                notifications.push({ theme, resolved });
            });
            
            window.__pynext__.theme.set('dark');
            
            expect(notifications).toHaveLength(1);
            expect(notifications[0].theme).toBe('dark');
        });
        
        test('returns unsubscribe function', () => {
            let count = 0;
            const unsubscribe = window.__pynext__.theme.subscribe(() => {
                count++;
            });
            
            window.__pynext__.theme.set('dark');
            expect(count).toBe(1);
            
            unsubscribe();
            
            window.__pynext__.theme.set('light');
            expect(count).toBe(1); // Still 1
        });
    });
    
    describe('flash prevention', () => {
        test('generates inline script', () => {
            const script = window.__pynext__.theme.getFlashPreventionScript();
            
            expect(script).toContain('localStorage');
            expect(script).toContain('pynext-theme');
            expect(script).toContain('prefers-color-scheme');
        });
    });
});

