/**
 * Lazy Loading Runtime for PyNext
 * 
 * Handles client-side lazy component loading:
 * - Dynamic chunk loading
 * - Prefetching strategies
 * - Loading state management
 * - Integration with navigation
 */

(function() {
  'use strict';

  // ==========================================================================
  // Constants
  // ==========================================================================

  const LoadingState = {
    IDLE: 'idle',
    LOADING: 'loading',
    LOADED: 'loaded',
    ERROR: 'error'
  };

  const PrefetchStrategy = {
    HOVER: 'hover',
    VISIBLE: 'visible',
    IDLE: 'idle',
    NONE: 'none'
  };

  // ==========================================================================
  // Lazy Component Registry
  // ==========================================================================

  /**
   * Registry of lazy components and their loading state.
   * @type {Map<string, LazyEntry>}
   */
  const lazyComponents = new Map();

  /**
   * Cache of loaded chunks.
   * @type {Map<string, Promise>}
   */
  const loadedChunks = new Map();

  /**
   * Prefetch queue for managing concurrent loads.
   * @type {Set<string>}
   */
  const prefetchQueue = new Set();

  /**
   * Maximum concurrent prefetches.
   */
  const MAX_CONCURRENT_PREFETCH = 2;

  /**
   * Currently prefetching count.
   */
  let currentPrefetches = 0;

  // ==========================================================================
  // Lazy Component Registration
  // ==========================================================================

  /**
   * @typedef {Object} LazyEntry
   * @property {string} id - Component ID
   * @property {string} chunk - Chunk URL
   * @property {Object} props - Component props
   * @property {string} state - Loading state
   * @property {boolean} preload - Whether to preload
   * @property {HTMLElement|null} element - DOM element
   * @property {Function|null} component - Loaded component
   * @property {Error|null} error - Loading error
   */

  /**
   * Register a lazy component.
   * 
   * @param {string} id - Component ID
   * @param {Object} config - Component configuration
   */
  function registerLazy(id, config) {
    const entry = {
      id,
      chunk: config.chunk,
      props: config.props || {},
      state: LoadingState.IDLE,
      preload: config.preload || false,
      element: null,
      component: null,
      error: null
    };

    lazyComponents.set(id, entry);
    log(`Registered lazy component: ${id}`);

    // Preload if configured
    if (entry.preload) {
      prefetchChunk(entry.chunk);
    }
  }

  // ==========================================================================
  // Chunk Loading
  // ==========================================================================

  /**
   * Load a JavaScript chunk.
   * 
   * @param {string} chunkUrl - URL of the chunk to load
   * @returns {Promise<any>} - Loaded module
   */
  async function loadChunk(chunkUrl) {
    // Check cache
    if (loadedChunks.has(chunkUrl)) {
      return loadedChunks.get(chunkUrl);
    }

    // Create loading promise
    const loadPromise = (async () => {
      const startTime = performance.now();
      log(`Loading chunk: ${chunkUrl}`);

      try {
        // Dynamic import
        const module = await import(chunkUrl);
        
        const duration = performance.now() - startTime;
        log(`Loaded chunk: ${chunkUrl} in ${duration.toFixed(2)}ms`);

        return module;
      } catch (error) {
        console.error(`Failed to load chunk: ${chunkUrl}`, error);
        loadedChunks.delete(chunkUrl); // Remove from cache on error
        throw error;
      }
    })();

    // Cache the promise
    loadedChunks.set(chunkUrl, loadPromise);

    return loadPromise;
  }

  /**
   * Prefetch a chunk without blocking.
   * 
   * @param {string} chunkUrl - URL of the chunk to prefetch
   */
  function prefetchChunk(chunkUrl) {
    // Already loaded or loading
    if (loadedChunks.has(chunkUrl)) {
      return;
    }

    // Already in queue
    if (prefetchQueue.has(chunkUrl)) {
      return;
    }

    // Add to queue
    prefetchQueue.add(chunkUrl);
    processPrefetchQueue();
  }

  /**
   * Process the prefetch queue.
   */
  function processPrefetchQueue() {
    if (currentPrefetches >= MAX_CONCURRENT_PREFETCH) {
      return;
    }

    for (const chunkUrl of prefetchQueue) {
      if (currentPrefetches >= MAX_CONCURRENT_PREFETCH) {
        break;
      }

      prefetchQueue.delete(chunkUrl);
      currentPrefetches++;

      // Use link preload for better browser integration
      const link = document.createElement('link');
      link.rel = 'modulepreload';
      link.href = chunkUrl;
      link.onload = () => {
        currentPrefetches--;
        processPrefetchQueue();
      };
      link.onerror = () => {
        currentPrefetches--;
        processPrefetchQueue();
      };
      document.head.appendChild(link);

      log(`Prefetching: ${chunkUrl}`);
    }
  }

  // ==========================================================================
  // Lazy Component Hydration
  // ==========================================================================

  /**
   * Load and hydrate a lazy component.
   * 
   * @param {string} id - Component ID
   */
  async function hydrateLazy(id) {
    const entry = lazyComponents.get(id);
    if (!entry) {
      warn(`Unknown lazy component: ${id}`);
      return;
    }

    if (entry.state === LoadingState.LOADED) {
      return; // Already loaded
    }

    // Find element
    const element = entry.element || document.querySelector(`[data-lazy="${id}"]`);
    if (!element) {
      warn(`Element not found for lazy component: ${id}`);
      return;
    }
    entry.element = element;

    // Update state
    entry.state = LoadingState.LOADING;
    element.setAttribute('data-state', LoadingState.LOADING);

    try {
      // Load the chunk
      const module = await loadChunk(entry.chunk);

      // Get the component from the module
      const Component = module.default || module;
      entry.component = Component;

      // Render the component
      if (typeof Component === 'function') {
        const result = Component(entry.props);
        
        // Replace fallback with rendered content
        const fallback = element.querySelector('[data-lazy-fallback]');
        if (fallback) {
          const temp = document.createElement('div');
          temp.innerHTML = typeof result === 'string' ? result : result.toString();
          
          while (temp.firstChild) {
            element.insertBefore(temp.firstChild, fallback);
          }
          fallback.remove();
        }
      }

      // Update state
      entry.state = LoadingState.LOADED;
      element.setAttribute('data-state', LoadingState.LOADED);
      element.setAttribute('data-hydrated', 'true');

      log(`Hydrated lazy component: ${id}`);

      // Dispatch event
      element.dispatchEvent(new CustomEvent('pynext:lazy-loaded', {
        detail: { id }
      }));

    } catch (error) {
      entry.state = LoadingState.ERROR;
      entry.error = error;
      element.setAttribute('data-state', LoadingState.ERROR);

      console.error(`Failed to hydrate lazy component ${id}:`, error);

      // Show error fallback
      const fallback = element.querySelector('[data-lazy-fallback]');
      if (fallback) {
        fallback.innerHTML = `<div class="lazy-error">Failed to load component</div>`;
      }
    }
  }

  /**
   * Initialize lazy loading for all registered components.
   */
  function initLazyLoading() {
    log('Initializing lazy loading');

    // Find all lazy elements
    const lazyElements = document.querySelectorAll('[data-lazy]');
    
    lazyElements.forEach(element => {
      const id = element.getAttribute('data-lazy');
      const entry = lazyComponents.get(id);
      
      if (entry) {
        entry.element = element;
        
        // Set up loading trigger based on state
        if (entry.preload) {
          // Load immediately
          hydrateLazy(id);
        } else {
          // Load on visibility or interaction
          observeLazyElement(id, element);
        }
      }
    });

    // Set up prefetching for links
    setupLinkPrefetching();
  }

  // ==========================================================================
  // Visibility Observer
  // ==========================================================================

  /**
   * IntersectionObserver for lazy loading.
   * @type {IntersectionObserver|null}
   */
  let lazyObserver = null;

  /**
   * Initialize the lazy observer.
   */
  function initLazyObserver() {
    if (lazyObserver) return;

    lazyObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const element = entry.target;
            const id = element.getAttribute('data-lazy');
            
            if (id) {
              hydrateLazy(id);
              lazyObserver.unobserve(element);
            }
          }
        });
      },
      {
        rootMargin: '100px', // Start loading 100px before visible
        threshold: 0
      }
    );
  }

  /**
   * Observe a lazy element for visibility.
   * 
   * @param {string} id - Component ID
   * @param {HTMLElement} element - Element to observe
   */
  function observeLazyElement(id, element) {
    initLazyObserver();
    
    // Also load on interaction
    element.addEventListener('click', () => hydrateLazy(id), { once: true });
    element.addEventListener('mouseenter', () => hydrateLazy(id), { once: true });
    
    // Observe for visibility
    lazyObserver.observe(element);
  }

  // ==========================================================================
  // Link Prefetching
  // ==========================================================================

  /**
   * Set up prefetching for links.
   */
  function setupLinkPrefetching() {
    // Hover prefetching
    document.addEventListener('mouseenter', (e) => {
      const link = e.target.closest('a[data-prefetch="hover"]');
      if (link) {
        const href = link.getAttribute('href');
        prefetchRoute(href);
      }
    }, true);

    // Visibility prefetching
    const visibleLinks = document.querySelectorAll('a[data-prefetch="visible"]');
    if (visibleLinks.length > 0 && 'IntersectionObserver' in window) {
      const linkObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const href = entry.target.getAttribute('href');
            prefetchRoute(href);
            linkObserver.unobserve(entry.target);
          }
        });
      });

      visibleLinks.forEach(link => linkObserver.observe(link));
    }

    // Idle prefetching
    if ('requestIdleCallback' in window) {
      const idleLinks = document.querySelectorAll('a[data-prefetch="idle"]');
      idleLinks.forEach(link => {
        requestIdleCallback(() => {
          const href = link.getAttribute('href');
          prefetchRoute(href);
        });
      });
    }
  }

  /**
   * Prefetch a route's code.
   * 
   * @param {string} route - Route to prefetch
   */
  function prefetchRoute(route) {
    if (!route) return;

    // Convert route to chunk name
    const chunkName = route.replace(/^\//, '').replace(/\//g, '-') || 'index';
    const chunkUrl = `/__pynext__/chunks/${chunkName}.js`;

    prefetchChunk(chunkUrl);
  }

  // ==========================================================================
  // Navigation Integration
  // ==========================================================================

  /**
   * Load a route's chunk before navigation.
   * 
   * @param {string} route - Route to navigate to
   * @returns {Promise<void>}
   */
  async function preloadRoute(route) {
    const chunkName = route.replace(/^\//, '').replace(/\//g, '-') || 'index';
    const chunkUrl = `/__pynext__/chunks/${chunkName}.js`;

    await loadChunk(chunkUrl);
  }

  // ==========================================================================
  // Utilities
  // ==========================================================================

  /**
   * Get loading stats.
   * 
   * @returns {Object}
   */
  function getStats() {
    const stats = {
      total: lazyComponents.size,
      idle: 0,
      loading: 0,
      loaded: 0,
      error: 0,
      chunks: loadedChunks.size,
      prefetchQueue: prefetchQueue.size
    };

    lazyComponents.forEach(entry => {
      stats[entry.state]++;
    });

    return stats;
  }

  /**
   * Force load all lazy components.
   */
  async function loadAll() {
    const promises = [];
    
    lazyComponents.forEach((entry, id) => {
      if (entry.state === LoadingState.IDLE) {
        promises.push(hydrateLazy(id));
      }
    });

    await Promise.all(promises);
  }

  // ==========================================================================
  // Logging
  // ==========================================================================

  const DEBUG = window.__PYNEXT_DEBUG__ || false;

  function log(...args) {
    if (DEBUG) {
      console.log('[PyNext Lazy]', ...args);
    }
  }

  function warn(...args) {
    console.warn('[PyNext Lazy]', ...args);
  }

  // ==========================================================================
  // Export to Global
  // ==========================================================================

  if (typeof window !== 'undefined') {
    window.__pynext__ = window.__pynext__ || {};

    // Core API
    window.__pynext__.registerLazy = registerLazy;
    window.__pynext__.initLazyLoading = initLazyLoading;
    window.__pynext__.hydrateLazy = hydrateLazy;
    window.__pynext__.loadAll = loadAll;

    // Chunk loading
    window.__pynext__.loadChunk = loadChunk;
    window.__pynext__.prefetchChunk = prefetchChunk;
    window.__pynext__.prefetchRoute = prefetchRoute;
    window.__pynext__.preloadRoute = preloadRoute;

    // Stats
    window.__pynext__.getLazyStats = getStats;

    // Internal
    window.__pynext__._lazyComponents = lazyComponents;
    window.__pynext__._loadedChunks = loadedChunks;
  }

  // Module exports
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
      registerLazy,
      initLazyLoading,
      hydrateLazy,
      loadAll,
      loadChunk,
      prefetchChunk,
      prefetchRoute,
      preloadRoute,
      getStats
    };
  }

})();

