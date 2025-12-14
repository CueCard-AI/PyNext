/**
 * Comprehensive tests for PyNext Router JavaScript Runtime
 * 
 * Tests cover:
 * 1. Route pattern compilation
 * 2. Route matching
 * 3. Navigation
 * 4. Hooks (useParams, useNavigate, etc.)
 * 5. Prefetching
 */

// Mock DOM environment
const { JSDOM } = require('jsdom');
const dom = new JSDOM('<!DOCTYPE html><html><body><div id="app"></div></body></html>', {
    url: 'http://localhost/',
    runScripts: 'dangerously',
});

global.window = dom.window;
global.document = dom.window.document;
global.history = dom.window.history;
global.location = dom.window.location;

// Load the router module
require('../../pynext/runtime/router.js');

const router = window.__pynext__.router;

describe('Router Module', () => {
    describe('Route Pattern Compilation', () => {
        test('compiles static path', () => {
            const { regex, paramNames } = router._compileRoutePattern('/about');
            
            expect(paramNames).toEqual([]);
            expect(regex.test('/about')).toBe(true);
            expect(regex.test('/other')).toBe(false);
        });

        test('compiles root path', () => {
            const { regex, paramNames } = router._compileRoutePattern('/');
            
            expect(paramNames).toEqual([]);
            expect(regex.test('/')).toBe(true);
            expect(regex.test('/other')).toBe(false);
        });

        test('compiles single param', () => {
            const { regex, paramNames } = router._compileRoutePattern('/users/:id');
            
            expect(paramNames).toEqual(['id']);
            expect(regex.test('/users/123')).toBe(true);
            expect(regex.test('/users/')).toBe(false);
        });

        test('compiles multiple params', () => {
            const { regex, paramNames } = router._compileRoutePattern('/users/:userId/posts/:postId');
            
            expect(paramNames).toEqual(['userId', 'postId']);
            expect(regex.test('/users/1/posts/2')).toBe(true);
        });

        test('compiles wildcard', () => {
            const { regex, paramNames } = router._compileRoutePattern('/files/*');
            
            expect(paramNames).toContain('*');
            expect(regex.test('/files/path/to/file.txt')).toBe(true);
        });

        test('escapes special regex chars', () => {
            const { regex } = router._compileRoutePattern('/api.v1/users');
            
            expect(regex.test('/api.v1/users')).toBe(true);
            expect(regex.test('/apixv1/users')).toBe(false);
        });
    });

    describe('Route Matching', () => {
        test('matches static route', () => {
            const compiled = router._compileRoutePattern('/about');
            const params = router._matchRoute('/about', compiled);
            
            expect(params).toEqual({});
        });

        test('returns null for non-match', () => {
            const compiled = router._compileRoutePattern('/about');
            const params = router._matchRoute('/contact', compiled);
            
            expect(params).toBeNull();
        });

        test('extracts single param', () => {
            const compiled = router._compileRoutePattern('/users/:id');
            const params = router._matchRoute('/users/123', compiled);
            
            expect(params).toEqual({ id: '123' });
        });

        test('extracts multiple params', () => {
            const compiled = router._compileRoutePattern('/users/:userId/posts/:postId');
            const params = router._matchRoute('/users/1/posts/2', compiled);
            
            expect(params).toEqual({ userId: '1', postId: '2' });
        });

        test('extracts wildcard param', () => {
            const compiled = router._compileRoutePattern('/files/*');
            const params = router._matchRoute('/files/path/to/file.txt', compiled);
            
            expect(params['*']).toBe('path/to/file.txt');
        });
    });

    describe('Hooks', () => {
        test('useNavigate returns function', () => {
            const navigate = router.useNavigate();
            
            expect(typeof navigate).toBe('function');
        });

        test('useParams returns object', () => {
            const params = router.useParams();
            
            expect(typeof params).toBe('object');
        });

        test('useSearchParams returns tuple', () => {
            const [params, setParams] = router.useSearchParams();
            
            expect(typeof params).toBe('object');
            expect(typeof setParams).toBe('function');
        });

        test('useLocation returns location object', () => {
            const location = router.useLocation();
            
            expect(location).toHaveProperty('pathname');
            expect(location).toHaveProperty('search');
            expect(location).toHaveProperty('hash');
        });

        test('useMatch returns null for no match', () => {
            // Current path is /
            const match = router.useMatch('/users/:id');
            
            expect(match).toBeNull();
        });
    });

    describe('Prefetching', () => {
        test('prefetch function exists', () => {
            expect(typeof router.prefetch).toBe('function');
        });

        test('prefetch does not throw', () => {
            expect(() => router.prefetch('/about')).not.toThrow();
        });

        test('prefetch with params', () => {
            expect(() => router.prefetch('/users/123')).not.toThrow();
        });
    });
});

describe('Route Pattern Edge Cases', () => {
    test('handles underscore in param name', () => {
        const { paramNames } = router._compileRoutePattern('/users/:user_id');
        expect(paramNames).toEqual(['user_id']);
    });

    test('handles camelCase param name', () => {
        const { paramNames } = router._compileRoutePattern('/users/:userId');
        expect(paramNames).toEqual(['userId']);
    });

    test('handles numbers in param name', () => {
        const { paramNames } = router._compileRoutePattern('/v1/:version2');
        expect(paramNames).toEqual(['version2']);
    });

    test('handles deeply nested path', () => {
        const { regex, paramNames } = router._compileRoutePattern('/a/:a/b/:b/c/:c');
        
        expect(paramNames).toEqual(['a', 'b', 'c']);
        expect(regex.test('/a/1/b/2/c/3')).toBe(true);
    });

    test('handles hyphen in static segment', () => {
        const { regex } = router._compileRoutePattern('/about-us');
        expect(regex.test('/about-us')).toBe(true);
    });

    test('handles dot in static segment', () => {
        const { regex } = router._compileRoutePattern('/api.json');
        expect(regex.test('/api.json')).toBe(true);
    });
});

describe('Route Matching Edge Cases', () => {
    test('param with hyphen value', () => {
        const compiled = router._compileRoutePattern('/articles/:slug');
        const params = router._matchRoute('/articles/my-article-title', compiled);
        
        expect(params).toEqual({ slug: 'my-article-title' });
    });

    test('param with dot value', () => {
        const compiled = router._compileRoutePattern('/files/:filename');
        const params = router._matchRoute('/files/document.pdf', compiled);
        
        expect(params).toEqual({ filename: 'document.pdf' });
    });

    test('param with uuid value', () => {
        const compiled = router._compileRoutePattern('/items/:id');
        const uuid = '550e8400-e29b-41d4-a716-446655440000';
        const params = router._matchRoute(`/items/${uuid}`, compiled);
        
        expect(params).toEqual({ id: uuid });
    });

    test('empty wildcard', () => {
        const compiled = router._compileRoutePattern('/files/*');
        const params = router._matchRoute('/files/', compiled);
        
        expect(params).not.toBeNull();
    });

    test('trailing slash does not match', () => {
        const compiled = router._compileRoutePattern('/about');
        const params = router._matchRoute('/about/', compiled);
        
        expect(params).toBeNull();
    });
});

describe('Module Exports', () => {
    test('router object exists on __pynext__', () => {
        expect(window.__pynext__.router).toBeDefined();
    });

    test('navigate function exported', () => {
        expect(typeof router.navigate).toBe('function');
    });

    test('init function exported', () => {
        expect(typeof router.init).toBe('function');
    });

    test('getPathname function exported', () => {
        expect(typeof router.getPathname).toBe('function');
    });

    test('getParams function exported', () => {
        expect(typeof router.getParams).toBe('function');
    });

    test('getQuery function exported', () => {
        expect(typeof router.getQuery).toBe('function');
    });
});

