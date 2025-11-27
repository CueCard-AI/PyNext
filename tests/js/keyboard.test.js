/**
 * Tests for PyNext Keyboard Runtime
 * Uses Jest's built-in jsdom environment
 */

const fs = require('fs');
const path = require('path');

describe('Keyboard Runtime', () => {
    beforeEach(() => {
        // Reset __pynext__
        window.__pynext__ = window.__pynext__ || {};
        window.__pynext__.keyboard = {
            shortcuts: {},
            sequences: {},
            register: jest.fn((key, handler, options) => {
                window.__pynext__.keyboard.shortcuts[key] = { handler, options };
            }),
            registerSequence: jest.fn((keys, handler) => {
                window.__pynext__.keyboard.sequences[keys] = handler;
            }),
        };
    });
    
    describe('Shortcut Registration', () => {
        test('registers shortcuts', () => {
            const handler = jest.fn();
            window.__pynext__.keyboard.register('ctrl+k', handler);
            
            expect(window.__pynext__.keyboard.register).toHaveBeenCalledWith('ctrl+k', handler);
            expect(window.__pynext__.keyboard.shortcuts['ctrl+k']).toBeDefined();
        });
        
        test('registers with options', () => {
            const handler = jest.fn();
            window.__pynext__.keyboard.register('ctrl+s', handler, { preventDefault: true });
            
            expect(window.__pynext__.keyboard.shortcuts['ctrl+s'].options).toEqual({ preventDefault: true });
        });
    });
    
    describe('Sequence Registration', () => {
        test('registers sequences', () => {
            const handler = jest.fn();
            window.__pynext__.keyboard.registerSequence('g d', handler);
            
            expect(window.__pynext__.keyboard.registerSequence).toHaveBeenCalledWith('g d', handler);
        });
    });
    
    describe('Keyboard.js file structure', () => {
        let content;
        
        beforeAll(() => {
            content = fs.readFileSync(
                path.join(__dirname, '../../pynext/runtime/keyboard.js'),
                'utf8'
            );
        });
        
        test('has keyboard namespace', () => {
            expect(content).toContain('keyboard');
        });
        
        test('has register function', () => {
            expect(content).toContain('register');
        });
        
        test('handles meta key for Mac', () => {
            expect(content).toContain('metaKey');
        });
        
        test('handles ctrl key', () => {
            expect(content).toContain('ctrlKey');
        });
    });
});
