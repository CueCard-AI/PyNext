/**
 * Tests for PyNext Theme Runtime
 * Uses Jest's built-in jsdom environment
 */

const fs = require('fs');
const path = require('path');

describe('Theme Runtime', () => {
    beforeEach(() => {
        // Setup mock theme system
        window.__pynext__ = window.__pynext__ || {};
        
        let currentTheme = 'light';
        const subscribers = [];
        
        window.__pynext__.theme = {
            get: () => currentTheme,
            set: (theme) => {
                currentTheme = theme;
                document.documentElement.setAttribute('data-theme', theme);
                document.documentElement.classList.remove('light', 'dark');
                document.documentElement.classList.add(theme);
                localStorage.setItem('theme', theme);
                subscribers.forEach(fn => fn(theme));
            },
            toggle: () => {
                const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
                window.__pynext__.theme.set(newTheme);
            },
            subscribe: (fn) => {
                subscribers.push(fn);
                return () => {
                    const idx = subscribers.indexOf(fn);
                    if (idx > -1) subscribers.splice(idx, 1);
                };
            },
        };
    });
    
    afterEach(() => {
        document.documentElement.removeAttribute('data-theme');
        document.documentElement.classList.remove('light', 'dark');
        localStorage.clear();
    });
    
    describe('getTheme', () => {
        test('returns current theme', () => {
            expect(window.__pynext__.theme.get()).toBe('light');
        });
    });
    
    describe('setTheme', () => {
        test('updates document attribute', () => {
            window.__pynext__.theme.set('dark');
            expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
        });
        
        test('adds class to html element', () => {
            window.__pynext__.theme.set('dark');
            expect(document.documentElement.classList.contains('dark')).toBe(true);
        });
        
        test('persists to localStorage', () => {
            window.__pynext__.theme.set('dark');
            expect(localStorage.getItem('theme')).toBe('dark');
        });
    });
    
    describe('toggleTheme', () => {
        test('toggles from light to dark', () => {
            window.__pynext__.theme.set('light');
            window.__pynext__.theme.toggle();
            expect(window.__pynext__.theme.get()).toBe('dark');
        });
        
        test('toggles from dark to light', () => {
            window.__pynext__.theme.set('dark');
            window.__pynext__.theme.toggle();
            expect(window.__pynext__.theme.get()).toBe('light');
        });
    });
    
    describe('subscribe', () => {
        test('notifies subscribers on change', () => {
            const callback = jest.fn();
            window.__pynext__.theme.subscribe(callback);
            
            window.__pynext__.theme.set('dark');
            
            expect(callback).toHaveBeenCalledWith('dark');
        });
        
        test('can unsubscribe', () => {
            const callback = jest.fn();
            const unsubscribe = window.__pynext__.theme.subscribe(callback);
            
            unsubscribe();
            window.__pynext__.theme.set('dark');
            
            expect(callback).not.toHaveBeenCalled();
        });
    });
    
    describe('theme.js file structure', () => {
        let content;
        
        beforeAll(() => {
            content = fs.readFileSync(
                path.join(__dirname, '../../pynext/runtime/theme.js'),
                'utf8'
            );
        });
        
        test('has theme namespace', () => {
            expect(content).toContain('theme');
        });
        
        test('handles localStorage', () => {
            expect(content).toContain('localStorage');
        });
        
        test('sets colorScheme style', () => {
            expect(content).toContain('colorScheme');
        });
        
        test('handles matchMedia for system preference', () => {
            expect(content).toContain('matchMedia');
        });
    });
});
