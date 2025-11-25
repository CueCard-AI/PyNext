/**
 * Navigation & Transitions Runtime for PyNext
 * 
 * Implements SPA-style client-side navigation with:
 * - View Transitions API support
 * - Route prefetching
 * - History management
 * - Loading states
 * - Fallback for unsupported browsers
 */

(function() {
  'use strict';

  // ==========================================================================
  // Feature Detection
  // ==========================================================================

  const supportsViewTransitions = 'startViewTransition' in document;
  const DEBUG = window.__PYNEXT_DEBUG__ || false;

  // ==========================================================================
  // State
  // ==========================================================================

  /** @type {Map<string, string>} Route cache: URL -> HTML */
  const pageCache = new Map();

  /** @type {Set<string>} URLs currently being prefetched */
  const prefetchingUrls = new Set();

  /** @type {AbortController|null} Current navigation abort controller */
  let currentNavigation = null;

  /** @type {string} Current URL */
  let currentUrl = window.location.pathname;

  /** @type {Object} Navigation configuration */
  const config = {
    defaultTransition: 'fade',
    prefetchDelay: 50,
    cacheMaxSize: 20,
    showLoadingAfter: 150,
  };

  // ==========================================================================
  // Initialization
  // ==========================================================================

  /**
   * Initialize the navigation system.
   */
  function init() {
    log('Initializing navigation');
    log('View Transitions supported:', supportsViewTransitions);

    // Set up link interception
    setupLinkInterception();

    // Set up popstate handler for back/forward
    setupPopstateHandler();

    // Set up prefetching
    setupPrefetching();

    // Initialize from server data
    if (window.__PYNEXT_NAV__) {
      const navData = window.__PYNEXT_NAV__;
      currentUrl = navData.current || window.location.pathname;
      
      // Prefetch specified routes
      if (navData.prefetch) {
        navData.prefetch.forEach(url => prefetch(url));
      }
    }

    log('Navigation initialized');
  }

  // ==========================================================================
  // Link Interception
  // ==========================================================================

  /**
   * Set up click interception for navigation links.
   */
  function setupLinkInterception() {
    document.addEventListener('click', async (e) => {
      // Find closest link
      const link = e.target.closest('a[data-pynext-link], a[href^="/"]');
      if (!link) return;

      // Skip external links
      const href = link.getAttribute('href');
      if (!href || href.startsWith('http') || href.startsWith('//')) return;

      // Skip if modifier keys pressed
      if (e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return;

      // Skip if target is set
      if (link.target && link.target !== '_self') return;

      // Prevent default navigation
      e.preventDefault();

      // Get transition type
      const transition = link.getAttribute('data-transition') || config.defaultTransition;
      const replace = link.hasAttribute('data-replace');

      // Navigate
      await navigate(href, { transition, replace });
    });
  }

  // ==========================================================================
  // Navigation
  // ==========================================================================

  /**
   * Navigate to a URL.
   * 
   * @param {string} url - Destination URL
   * @param {Object} options - Navigation options
   * @returns {Promise<void>}
   */
  async function navigate(url, options = {}) {
    const {
      transition = config.defaultTransition,
      replace = false,
      scrollTo = { top: 0, behavior: 'instant' },
    } = options;

    // Abort any current navigation
    if (currentNavigation) {
      currentNavigation.abort();
    }

    // Create new abort controller
    currentNavigation = new AbortController();
    const signal = currentNavigation.signal;

    log(`Navigating to ${url} with transition: ${transition}`);

    // Emit start event
    emitNavigationEvent('start', currentUrl, url, transition);

    try {
      // Show loading indicator after delay
      const loadingTimeout = setTimeout(() => {
        if (!signal.aborted) {
          showLoading();
        }
      }, config.showLoadingAfter);

      // Fetch the new page
      const html = await fetchPage(url, signal);

      // Clear loading timeout
      clearTimeout(loadingTimeout);
      hideLoading();

      if (signal.aborted) return;

      // Perform transition
      if (supportsViewTransitions && transition !== 'none') {
        await performViewTransition(html, transition);
      } else {
        // Fallback: direct update
        updatePage(html);
      }

      // Update history
      if (replace) {
        history.replaceState({ url, transition }, '', url);
      } else {
        history.pushState({ url, transition }, '', url);
      }

      // Update current URL
      currentUrl = url;

      // Scroll to top
      if (scrollTo) {
        window.scrollTo(scrollTo);
      }

      // Re-initialize components
      reinitialize();

      // Emit complete event
      emitNavigationEvent('complete', currentUrl, url, transition);

    } catch (error) {
      hideLoading();

      if (error.name === 'AbortError') {
        emitNavigationEvent('abort', currentUrl, url, transition);
        return;
      }

      console.error('[PyNext Navigation] Error:', error);
      emitNavigationEvent('error', currentUrl, url, transition, error.message);

      // Fallback to full page navigation
      window.location.href = url;
    } finally {
      currentNavigation = null;
    }
  }

  /**
   * Go back in history with transition.
   * 
   * @param {Object} options - Navigation options
   */
  function back(options = {}) {
    const transition = options.transition || 'slide-right';
    
    // Store transition for popstate handler
    sessionStorage.setItem('__pynext_back_transition__', transition);
    
    history.back();
  }

  /**
   * Go forward in history with transition.
   * 
   * @param {Object} options - Navigation options
   */
  function forward(options = {}) {
    const transition = options.transition || 'slide-left';
    
    sessionStorage.setItem('__pynext_forward_transition__', transition);
    
    history.forward();
  }

  // ==========================================================================
  // Page Fetching
  // ==========================================================================

  /**
   * Fetch a page's HTML.
   * 
   * @param {string} url - URL to fetch
   * @param {AbortSignal} signal - Abort signal
   * @returns {Promise<string>} - Page HTML
   */
  async function fetchPage(url, signal) {
    // Check cache
    if (pageCache.has(url)) {
      log(`Cache hit: ${url}`);
      return pageCache.get(url);
    }

    log(`Fetching: ${url}`);

    const response = await fetch(url, {
      signal,
      headers: {
        'Accept': 'text/html',
        'X-PyNext-Navigation': 'true',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const html = await response.text();

    // Cache the response
    cacheResponse(url, html);

    return html;
  }

  /**
   * Cache a page response.
   * 
   * @param {string} url - URL
   * @param {string} html - HTML content
   */
  function cacheResponse(url, html) {
    // Evict oldest if cache is full
    if (pageCache.size >= config.cacheMaxSize) {
      const firstKey = pageCache.keys().next().value;
      pageCache.delete(firstKey);
    }

    pageCache.set(url, html);
  }

  // ==========================================================================
  // View Transitions
  // ==========================================================================

  /**
   * Perform a view transition.
   * 
   * @param {string} html - New page HTML
   * @param {string} transition - Transition type
   */
  async function performViewTransition(html, transition) {
    // Set transition type on document
    document.documentElement.setAttribute('data-transition', transition);

    const viewTransition = document.startViewTransition(() => {
      updatePage(html);
    });

    try {
      await viewTransition.finished;
    } finally {
      document.documentElement.removeAttribute('data-transition');
    }
  }

  /**
   * Update the page content.
   * 
   * @param {string} html - New HTML content
   */
  function updatePage(html) {
    // Parse the new HTML
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');

    // Update title
    const newTitle = doc.querySelector('title');
    if (newTitle) {
      document.title = newTitle.textContent;
    }

    // Update body content
    const newBody = doc.querySelector('body');
    if (newBody) {
      // Find main content area or use body
      const mainContent = document.querySelector('[data-page-content], main, #app, #root');
      const newMainContent = doc.querySelector('[data-page-content], main, #app, #root');

      if (mainContent && newMainContent) {
        mainContent.innerHTML = newMainContent.innerHTML;
      } else {
        document.body.innerHTML = newBody.innerHTML;
      }
    }

    // Execute any new scripts
    const scripts = doc.querySelectorAll('script:not([src])');
    scripts.forEach(script => {
      const newScript = document.createElement('script');
      newScript.textContent = script.textContent;
      document.body.appendChild(newScript);
      document.body.removeChild(newScript);
    });
  }

  // ==========================================================================
  // Popstate Handler (Back/Forward)
  // ==========================================================================

  /**
   * Set up popstate handler for browser back/forward.
   */
  function setupPopstateHandler() {
    window.addEventListener('popstate', async (e) => {
      const state = e.state || {};
      const url = state.url || window.location.pathname;

      // Get stored transition
      let transition = state.transition || config.defaultTransition;
      
      // Check for back/forward specific transitions
      const backTransition = sessionStorage.getItem('__pynext_back_transition__');
      const forwardTransition = sessionStorage.getItem('__pynext_forward_transition__');
      
      if (backTransition) {
        transition = backTransition;
        sessionStorage.removeItem('__pynext_back_transition__');
      } else if (forwardTransition) {
        transition = forwardTransition;
        sessionStorage.removeItem('__pynext_forward_transition__');
      }

      log(`Popstate: ${url} with transition: ${transition}`);

      // Fetch and display the page
      try {
        const html = await fetchPage(url, new AbortController().signal);

        if (supportsViewTransitions && transition !== 'none') {
          await performViewTransition(html, transition);
        } else {
          updatePage(html);
        }

        currentUrl = url;
        reinitialize();

      } catch (error) {
        console.error('[PyNext Navigation] Popstate error:', error);
        window.location.href = url;
      }
    });
  }

  // ==========================================================================
  // Prefetching
  // ==========================================================================

  /**
   * Set up prefetching for links.
   */
  function setupPrefetching() {
    // Hover prefetching
    let hoverTimeout = null;

    document.addEventListener('mouseenter', (e) => {
      const link = e.target.closest('a[data-prefetch="hover"], a[href^="/"]');
      if (!link) return;

      const href = link.getAttribute('href');
      if (!href || href.startsWith('http')) return;

      // Delay prefetch slightly
      hoverTimeout = setTimeout(() => {
        prefetch(href);
      }, config.prefetchDelay);
    }, true);

    document.addEventListener('mouseleave', (e) => {
      if (hoverTimeout) {
        clearTimeout(hoverTimeout);
        hoverTimeout = null;
      }
    }, true);

    // Viewport prefetching with IntersectionObserver
    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const link = entry.target;
            const href = link.getAttribute('href');
            if (href) {
              prefetch(href);
              observer.unobserve(link);
            }
          }
        });
      }, { rootMargin: '100px' });

      // Observe links with visible prefetch
      document.querySelectorAll('a[data-prefetch="visible"]').forEach(link => {
        observer.observe(link);
      });
    }

    // Idle prefetching
    if ('requestIdleCallback' in window) {
      document.querySelectorAll('a[data-prefetch="idle"]').forEach(link => {
        const href = link.getAttribute('href');
        if (href) {
          requestIdleCallback(() => prefetch(href));
        }
      });
    }
  }

  /**
   * Prefetch a URL.
   * 
   * @param {string} url - URL to prefetch
   */
  async function prefetch(url) {
    // Skip if already cached or prefetching
    if (pageCache.has(url) || prefetchingUrls.has(url)) {
      return;
    }

    // Skip current URL
    if (url === currentUrl) {
      return;
    }

    prefetchingUrls.add(url);
    log(`Prefetching: ${url}`);

    try {
      await fetchPage(url, new AbortController().signal);
    } catch (error) {
      // Silently ignore prefetch errors
      log(`Prefetch failed: ${url}`, error.message);
    } finally {
      prefetchingUrls.delete(url);
    }
  }

  // ==========================================================================
  // Loading Indicator
  // ==========================================================================

  /** @type {HTMLElement|null} */
  let loadingElement = null;

  /**
   * Show loading indicator.
   */
  function showLoading() {
    if (loadingElement) return;

    loadingElement = document.createElement('div');
    loadingElement.className = 'pynext-nav-loading';
    loadingElement.setAttribute('aria-hidden', 'true');
    document.body.appendChild(loadingElement);
  }

  /**
   * Hide loading indicator.
   */
  function hideLoading() {
    if (loadingElement) {
      loadingElement.remove();
      loadingElement = null;
    }
  }

  // ==========================================================================
  // Re-initialization
  // ==========================================================================

  /**
   * Re-initialize PyNext components after navigation.
   */
  function reinitialize() {
    // Hydrate signals
    if (window.__pynext__?.hydrateSignals) {
      window.__pynext__.hydrateSignals();
    }

    // Hydrate resources
    if (window.__pynext__?.hydrateResources) {
      window.__pynext__.hydrateResources();
    }

    // Initialize islands
    if (window.__pynext__?.hydrateAllIslands) {
      window.__pynext__.hydrateAllIslands();
    }

    // Initialize lazy components
    if (window.__pynext__?.initLazyLoading) {
      window.__pynext__.initLazyLoading();
    }

    // Set up prefetching for new links
    setupPrefetching();

    // Emit reinitialize event
    document.dispatchEvent(new CustomEvent('pynext:navigated'));
  }

  // ==========================================================================
  // Events
  // ==========================================================================

  /**
   * Emit a navigation event.
   * 
   * @param {string} type - Event type
   * @param {string} fromUrl - Source URL
   * @param {string} toUrl - Destination URL
   * @param {string} transition - Transition type
   * @param {string} error - Error message (optional)
   */
  function emitNavigationEvent(type, fromUrl, toUrl, transition, error = null) {
    const event = new CustomEvent(`pynext:navigation:${type}`, {
      detail: { fromUrl, toUrl, transition, error, timestamp: Date.now() }
    });
    document.dispatchEvent(event);
    log(`Event: navigation:${type}`, { fromUrl, toUrl, transition });
  }

  // ==========================================================================
  // Utilities
  // ==========================================================================

  function log(...args) {
    if (DEBUG) {
      console.log('[PyNext Nav]', ...args);
    }
  }

  /**
   * Get navigation stats.
   * 
   * @returns {Object}
   */
  function getStats() {
    return {
      currentUrl,
      cachedPages: pageCache.size,
      prefetching: prefetchingUrls.size,
      supportsViewTransitions,
    };
  }

  /**
   * Clear the page cache.
   */
  function clearCache() {
    pageCache.clear();
    log('Cache cleared');
  }

  // ==========================================================================
  // Export
  // ==========================================================================

  if (typeof window !== 'undefined') {
    window.__pynext__ = window.__pynext__ || {};

    // Core navigation
    window.__pynext__.navigate = navigate;
    window.__pynext__.back = back;
    window.__pynext__.forward = forward;

    // Prefetching
    window.__pynext__.prefetch = prefetch;

    // Cache management
    window.__pynext__.clearNavigationCache = clearCache;
    window.__pynext__.getNavigationStats = getStats;

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', init);
    } else {
      init();
    }
  }

  // Module exports
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
      navigate,
      back,
      forward,
      prefetch,
      clearCache,
      getStats,
    };
  }

})();

