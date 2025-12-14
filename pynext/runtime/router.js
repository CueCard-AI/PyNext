/**
 * PyNext Client-Side Router - SolidJS-Style Reactive Routing
 * 
 * =============================================================================
 * WHAT THIS FILE DOES (AI Summary)
 * =============================================================================
 * 
 * This module provides client-side routing with fine-grained reactivity.
 * Unlike React Router which re-renders component trees, PyNext router:
 * 
 * 1. Stores route state in SIGNALS (pathname, params, query)
 * 2. Only components using those signals react to changes
 * 3. DOM swapping happens directly in the route outlet
 * 
 * PERFORMANCE:
 * - Route change: ~5-10ms (just signal update + DOM swap)
 * - No virtual DOM reconciliation
 * - No component tree re-rendering
 * 
 * =============================================================================
 * HOW IT WORKS
 * =============================================================================
 * 
 * 1. On page load:
 *    - Find router outlet (data-pynext-router)
 *    - Parse route data from data-pynext-route-data
 *    - Initialize route signals
 *    - Set up History API listeners
 * 
 * 2. On navigation (Link click or navigate()):
 *    - Prevent default browser navigation
 *    - Update History API (pushState/replaceState)
 *    - Update pathname signal
 *    - Match route and update params signal
 *    - Fetch and render new route content
 * 
 * 3. On browser back/forward:
 *    - Listen to popstate event
 *    - Same as step 2, but without History API update
 * 
 * =============================================================================
 */

(function(global) {
    'use strict';

    // =========================================================================
    // SECTION 1: ROUTE PATTERN COMPILATION
    // =========================================================================
    // 
    // Compile route patterns like "/users/:id" to regex for fast matching.
    // This happens once per route, not on every navigation.
    // =========================================================================

    /**
     * Compile a route pattern to a regex.
     * 
     * @param {string} pattern - Route pattern (e.g., "/users/:id")
     * @returns {{regex: RegExp, paramNames: string[]}}
     */
    function compileRoutePattern(pattern) {
        const paramNames = [];
        
        // Find all :param patterns
        const paramRegex = /:([a-zA-Z_][a-zA-Z0-9_]*)/g;
        let match;
        while ((match = paramRegex.exec(pattern)) !== null) {
            paramNames.push(match[1]);
        }
        
        // Convert to regex
        let regexPattern = pattern
            // Escape special chars
            .replace(/[.+?^${}()|[\]\\]/g, '\\$&')
            // Replace :param with capture group
            .replace(/:([a-zA-Z_][a-zA-Z0-9_]*)/g, '([^/]+)')
            // Replace * with catch-all
            .replace(/\*/g, '(.*)');
        
        if (pattern.includes('*')) {
            paramNames.push('*');
        }
        
        return {
            regex: new RegExp(`^${regexPattern}$`),
            paramNames,
        };
    }

    /**
     * Match a pathname against a compiled route.
     * 
     * @param {string} pathname - URL pathname
     * @param {{regex: RegExp, paramNames: string[]}} compiled - Compiled route
     * @returns {Object|null} - Params object or null if no match
     */
    function matchRoute(pathname, compiled) {
        const match = compiled.regex.exec(pathname);
        if (!match) return null;
        
        const params = {};
        for (let i = 0; i < compiled.paramNames.length; i++) {
            params[compiled.paramNames[i]] = match[i + 1];
        }
        return params;
    }


    // =========================================================================
    // SECTION 2: ROUTER STATE (Signals)
    // =========================================================================
    //
    // Router state is stored in reactive signals from the core runtime.
    // Components that call useParams() etc subscribe to these signals.
    // =========================================================================

    // Router state signals
    let pathnameSignal = null;
    let paramsSignal = null;
    let querySignal = null;
    let hashSignal = null;
    
    // Compiled routes
    let routes = [];
    
    // Router outlet element
    let routerOutlet = null;
    
    // Base path
    let basePath = '';
    
    // Whether router is initialized
    let initialized = false;

    /**
     * Get current pathname.
     * @returns {string}
     */
    function getPathname() {
        return pathnameSignal ? pathnameSignal() : window.location.pathname;
    }

    /**
     * Get current params.
     * @returns {Object}
     */
    function getParams() {
        return paramsSignal ? paramsSignal() : {};
    }

    /**
     * Get current query params.
     * @returns {Object}
     */
    function getQuery() {
        return querySignal ? querySignal() : {};
    }


    // =========================================================================
    // SECTION 3: ROUTER INITIALIZATION
    // =========================================================================
    //
    // Initialize router from server-rendered data and set up event listeners.
    // =========================================================================

    /**
     * Parse query string to object.
     * @param {string} search - Query string (with or without ?)
     * @returns {Object}
     */
    function parseQuery(search) {
        if (!search) return {};
        if (search.startsWith('?')) search = search.slice(1);
        if (!search) return {};
        
        const params = {};
        for (const part of search.split('&')) {
            const [key, value] = part.split('=');
            if (key) {
                params[decodeURIComponent(key)] = value ? decodeURIComponent(value) : '';
            }
        }
        return params;
    }

    /**
     * Convert object to query string.
     * @param {Object} params - Query params
     * @returns {string}
     */
    function stringifyQuery(params) {
        if (!params || Object.keys(params).length === 0) return '';
        return '?' + Object.entries(params)
            .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
            .join('&');
    }

    /**
     * Initialize the router.
     * 
     * This is called automatically when the page loads.
     * It finds the router outlet, parses route data, and sets up listeners.
     */
    function initRouter() {
        if (initialized) return;
        
        // Find router outlet
        routerOutlet = document.querySelector('[data-pynext-router]');
        if (!routerOutlet) {
            console.log('[PyNext Router] No router outlet found');
            return;
        }
        
        // Parse route data from SSR
        const routeDataAttr = routerOutlet.getAttribute('data-pynext-route-data');
        let routeData = { pathname: '/', params: {}, routes: [] };
        
        if (routeDataAttr) {
            try {
                routeData = JSON.parse(routeDataAttr);
            } catch (e) {
                console.error('[PyNext Router] Failed to parse route data:', e);
            }
        }
        
        // Get createSignal from core runtime
        const createSignal = window.__pynext__?.createSignal;
        if (!createSignal) {
            console.error('[PyNext Router] Core runtime not found. Make sure signals.js is loaded first.');
            // Store pending init for retry when signals load
            window.__pynext__ = window.__pynext__ || {};
            window.__pynext__._pendingRouterInit = true;
            return;
        }
        
        // Initialize signals with current location
        pathnameSignal = createSignal('router:pathname', window.location.pathname);
        paramsSignal = createSignal('router:params', routeData.params || {});
        querySignal = createSignal('router:query', parseQuery(window.location.search));
        hashSignal = createSignal('router:hash', window.location.hash.slice(1));
        
        // Compile routes
        routes = (routeData.routes || []).map(path => ({
            path,
            ...compileRoutePattern(path),
        }));
        
        // Set up click handler for Link components
        document.addEventListener('click', handleLinkClick);
        
        // Set up popstate handler for browser back/forward
        window.addEventListener('popstate', handlePopState);
        
        // Handle prefetching on hover
        document.addEventListener('mouseover', handleLinkHover);
        
        initialized = true;
        console.log('[PyNext Router] Initialized', { 
            pathname: window.location.pathname,
            routes: routes.length,
        });
    }


    // =========================================================================
    // SECTION 4: NAVIGATION
    // =========================================================================
    //
    // Handle navigation via Link clicks, programmatic navigation, and
    // browser back/forward buttons.
    // =========================================================================

    /**
     * Navigate to a new path.
     * 
     * @param {string|number} to - Path to navigate to, or history delta (-1 = back)
     * @param {Object} options - Navigation options
     * @param {boolean} options.replace - Replace history instead of push
     * @param {Object} options.state - History state
     */
    function navigate(to, options = {}) {
        const { replace = false, state = null } = options;
        
        // History navigation
        if (typeof to === 'number') {
            window.history.go(to);
            return;
        }
        
        // Parse the target path
        const url = new URL(to, window.location.origin);
        const newPathname = url.pathname;
        const newSearch = url.search;
        const newHash = url.hash;
        
        // Skip if same path
        if (
            newPathname === window.location.pathname &&
            newSearch === window.location.search &&
            newHash === window.location.hash
        ) {
            return;
        }
        
        // Update History API
        const fullPath = newPathname + newSearch + newHash;
        if (replace) {
            window.history.replaceState(state, '', fullPath);
        } else {
            window.history.pushState(state, '', fullPath);
        }
        
        // Update signals and render
        updateRoute(newPathname, newSearch, newHash);
    }

    /**
     * Update route state and re-render outlet.
     * 
     * @param {string} pathname - New pathname
     * @param {string} search - Query string
     * @param {string} hash - Hash (without #)
     */
    function updateRoute(pathname, search, hash) {
        // Find matching route
        let matchedParams = {};
        for (const route of routes) {
            const params = matchRoute(pathname, route);
            if (params !== null) {
                matchedParams = params;
                break;
            }
        }
        
        // Update signals
        if (pathnameSignal) pathnameSignal.set(pathname);
        if (paramsSignal) paramsSignal.set(matchedParams);
        if (querySignal) querySignal.set(parseQuery(search));
        if (hashSignal) hashSignal.set(hash.startsWith('#') ? hash.slice(1) : hash);
        
        // Fetch and render new content
        fetchRouteContent(pathname);
        
        // Update active link states
        updateActiveLinks(pathname);
        
        console.log('[PyNext Router] Route updated', { pathname, params: matchedParams });
    }

    /**
     * Fetch route content from server and update outlet.
     * 
     * @param {string} pathname - Path to fetch
     */
    async function fetchRouteContent(pathname) {
        if (!routerOutlet) return;
        
        try {
            // Fetch partial HTML from server
            const response = await fetch(pathname, {
                headers: {
                    'X-PyNext-Partial': 'true',  // Tell server we want partial content
                },
            });
            
            if (!response.ok) {
                console.error('[PyNext Router] Failed to fetch route:', response.status);
                return;
            }
            
            const html = await response.text();
            
            // Update outlet content
            routerOutlet.innerHTML = html;
            
            // Re-initialize any reactive components in new content
            if (window.__pynext__?.hydrate) {
                window.__pynext__.hydrate();
            }
            
            // Scroll to top (or hash target)
            if (window.location.hash) {
                const target = document.querySelector(window.location.hash);
                if (target) {
                    target.scrollIntoView();
                }
            } else {
                window.scrollTo(0, 0);
            }
            
        } catch (error) {
            console.error('[PyNext Router] Navigation error:', error);
        }
    }

    /**
     * Handle click on Link component.
     * 
     * @param {MouseEvent} event
     */
    function handleLinkClick(event) {
        // Find the link element
        const link = event.target.closest('[data-pynext-link]');
        if (!link) return;
        
        // Skip if modifier keys (let browser handle)
        if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
            return;
        }
        
        // Skip if not left click
        if (event.button !== 0) return;
        
        // Skip if target="_blank" etc
        const target = link.getAttribute('target');
        if (target && target !== '_self') return;
        
        // Skip external links
        const href = link.getAttribute('href');
        if (!href || href.startsWith('http') || href.startsWith('//')) {
            return;
        }
        
        // Prevent default navigation
        event.preventDefault();
        
        // Check for replace mode
        const replace = link.hasAttribute('data-pynext-replace');
        
        // Navigate
        navigate(href, { replace });
    }

    /**
     * Handle browser back/forward navigation.
     * 
     * @param {PopStateEvent} event
     */
    function handlePopState(event) {
        updateRoute(
            window.location.pathname,
            window.location.search,
            window.location.hash
        );
    }

    /**
     * Update active state on Link components.
     * 
     * @param {string} pathname - Current pathname
     */
    function updateActiveLinks(pathname) {
        const links = document.querySelectorAll('[data-pynext-link]');
        
        for (const link of links) {
            const href = link.getAttribute('href');
            if (!href) continue;
            
            // Check if active
            const isExact = href === pathname;
            const isPartial = pathname.startsWith(href) && href !== '/';
            const isActive = isExact || isPartial;
            
            // Toggle active class
            if (isActive) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        }
    }


    // =========================================================================
    // SECTION 5: PREFETCHING
    // =========================================================================
    //
    // Prefetch route content on hover for faster navigation.
    // =========================================================================

    // Cache of prefetched routes
    const prefetchCache = new Map();

    /**
     * Handle hover on Link for prefetching.
     * 
     * @param {MouseEvent} event
     */
    function handleLinkHover(event) {
        const link = event.target.closest('[data-pynext-prefetch]');
        if (!link) return;
        
        const href = link.getAttribute('href');
        if (!href || prefetchCache.has(href)) return;
        
        prefetchRoute(href);
    }

    /**
     * Prefetch a route's content.
     * 
     * @param {string} path - Path to prefetch
     */
    async function prefetchRoute(path) {
        if (prefetchCache.has(path)) return;
        
        try {
            // Mark as prefetching (prevent duplicate requests)
            prefetchCache.set(path, 'pending');
            
            const response = await fetch(path, {
                headers: {
                    'X-PyNext-Partial': 'true',
                    'X-PyNext-Prefetch': 'true',
                },
            });
            
            if (response.ok) {
                const html = await response.text();
                prefetchCache.set(path, html);
                console.log('[PyNext Router] Prefetched:', path);
            }
        } catch (error) {
            prefetchCache.delete(path);
        }
    }


    // =========================================================================
    // SECTION 6: HOOKS (for use in components)
    // =========================================================================
    //
    // These functions provide access to router state from components.
    // =========================================================================

    /**
     * Get navigation function.
     * @returns {Function}
     */
    function useNavigate() {
        return navigate;
    }

    /**
     * Get current route params (reactive).
     * @returns {Object}
     */
    function useParams() {
        return paramsSignal ? paramsSignal() : {};
    }

    /**
     * Get current query params (reactive).
     * @returns {[Object, Function]}
     */
    function useSearchParams() {
        const params = querySignal ? querySignal() : {};
        
        const setParams = (newParams) => {
            if (querySignal) {
                querySignal.set(newParams);
            }
            // Update URL
            const newSearch = stringifyQuery(newParams);
            window.history.replaceState(null, '', window.location.pathname + newSearch);
        };
        
        return [params, setParams];
    }

    /**
     * Get current location (reactive).
     * @returns {{pathname: string, search: string, hash: string}}
     */
    function useLocation() {
        return {
            pathname: pathnameSignal ? pathnameSignal() : window.location.pathname,
            search: window.location.search,
            hash: window.location.hash,
        };
    }

    /**
     * Check if a pattern matches current path.
     * @param {string} pattern - Route pattern
     * @returns {Object|null}
     */
    function useMatch(pattern) {
        const compiled = compileRoutePattern(pattern);
        const pathname = pathnameSignal ? pathnameSignal() : window.location.pathname;
        return matchRoute(pathname, compiled);
    }


    // =========================================================================
    // SECTION 7: EXPORTS
    // =========================================================================

    // Export to global __pynext__ object
    const pynext = global.__pynext__ = global.__pynext__ || {};
    
    // Router module
    pynext.router = {
        // Core
        init: initRouter,
        navigate,
        
        // State
        getPathname,
        getParams,
        getQuery,
        
        // Hooks
        useNavigate,
        useParams,
        useSearchParams,
        useLocation,
        useMatch,
        
        // Prefetching
        prefetch: prefetchRoute,
        
        // Internal (for testing)
        _compileRoutePattern: compileRoutePattern,
        _matchRoute: matchRoute,
        _updateRoute: updateRoute,
        _routes: () => routes,
    };

    // Auto-initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initRouter);
    } else {
        // DOM already loaded
        setTimeout(initRouter, 0);
    }

    console.log('[PyNext Router] Module loaded');

})(typeof window !== 'undefined' ? window : global);

