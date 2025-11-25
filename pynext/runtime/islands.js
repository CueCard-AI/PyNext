/**
 * Islands Runtime for PyNext
 * 
 * Implements selective/partial hydration - only interactive parts
 * of the page get JavaScript while static content stays as HTML.
 * 
 * Strategies:
 * - load: Hydrate immediately on page load
 * - visible: Hydrate when island scrolls into view
 * - idle: Hydrate when browser is idle or user interacts
 * - media: Hydrate when media query matches
 * - none: Never hydrate (SSR only)
 */

(function() {
  'use strict';

  // ==========================================================================
  // Island Registry
  // ==========================================================================

  /**
   * Registry of all islands on the page.
   * @type {Map<string, IslandConfig>}
   */
  const islands = new Map();

  /**
   * Registry of island component factories.
   * @type {Map<string, Function>}
   */
  const componentFactories = new Map();

  /**
   * Islands that have been hydrated.
   * @type {Set<string>}
   */
  const hydratedIslands = new Set();

  /**
   * Intersection observer for visible strategy.
   * @type {IntersectionObserver|null}
   */
  let visibilityObserver = null;

  /**
   * Media query listeners.
   * @type {Map<string, MediaQueryList>}
   */
  const mediaQueryListeners = new Map();

  // ==========================================================================
  // Island Configuration
  // ==========================================================================

  /**
   * @typedef {Object} IslandConfig
   * @property {string} id - Unique island ID
   * @property {string} component - Component name
   * @property {string} strategy - Hydration strategy
   * @property {Object} props - Component props
   * @property {string[]} signals - Signal IDs used by this island
   * @property {string|null} mediaQuery - Media query for 'media' strategy
   */

  /**
   * Register an island for hydration.
   * 
   * @param {string} id - Island ID
   * @param {IslandConfig} config - Island configuration
   */
  function registerIsland(id, config) {
    islands.set(id, {
      id,
      component: config.component,
      strategy: config.strategy || 'load',
      props: config.props || {},
      signals: config.signals || [],
      mediaQuery: config.mediaQuery || null,
      element: null,
      hydrated: false
    });

    log(`Registered island: ${id} (${config.component}, strategy: ${config.strategy})`);
  }

  /**
   * Register a component factory for hydration.
   * 
   * @param {string} name - Component name
   * @param {Function} factory - Function that creates the component
   */
  function registerComponent(name, factory) {
    componentFactories.set(name, factory);
    log(`Registered component factory: ${name}`);
  }

  // ==========================================================================
  // Hydration Strategies
  // ==========================================================================

  /**
   * Hydrate all registered islands based on their strategies.
   */
  function hydrateIslands() {
    log(`Starting hydration for ${islands.size} islands`);

    islands.forEach((config, id) => {
      // Find the island element
      const element = document.querySelector(`[data-island="${id}"]`);
      if (!element) {
        warn(`Island element not found: ${id}`);
        return;
      }

      config.element = element;

      // Apply hydration strategy
      switch (config.strategy) {
        case 'load':
          hydrateIsland(id);
          break;

        case 'visible':
          observeVisibility(id, element);
          break;

        case 'idle':
          scheduleIdleHydration(id, element);
          break;

        case 'media':
          observeMediaQuery(id, config.mediaQuery);
          break;

        case 'none':
          // Never hydrate
          log(`Island ${id} marked as SSR-only, skipping hydration`);
          break;

        default:
          warn(`Unknown strategy for island ${id}: ${config.strategy}`);
          hydrateIsland(id);
      }
    });
  }

  /**
   * Hydrate a specific island.
   * 
   * @param {string} id - Island ID
   */
  function hydrateIsland(id) {
    if (hydratedIslands.has(id)) {
      return; // Already hydrated
    }

    const config = islands.get(id);
    if (!config) {
      warn(`Island not found: ${id}`);
      return;
    }

    const element = config.element || document.querySelector(`[data-island="${id}"]`);
    if (!element) {
      warn(`Island element not found: ${id}`);
      return;
    }

    const startTime = performance.now();
    log(`Hydrating island: ${id} (${config.component})`);

    try {
      // Get signals for this island
      const signalData = {};
      config.signals.forEach(signalId => {
        const signal = __pynext__.getSignal?.(signalId);
        if (signal) {
          signalData[signalId] = signal;
        }
      });

      // Create component if we have a factory
      const factory = componentFactories.get(config.component);
      if (factory) {
        const component = factory(config.props, signalData);
        // Mount component (implementation depends on component system)
        if (typeof component === 'function') {
          component(element);
        }
      }

      // Connect event handlers
      connectEventHandlers(element);

      // Connect signals to DOM
      connectSignals(element, signalData);

      // Mark as hydrated
      hydratedIslands.add(id);
      element.setAttribute('data-hydrated', 'true');
      element.removeAttribute('data-hydrate');

      const duration = performance.now() - startTime;
      log(`Hydrated island: ${id} in ${duration.toFixed(2)}ms`);

      // Dispatch event
      element.dispatchEvent(new CustomEvent('pynext:hydrated', {
        detail: { id, duration }
      }));

    } catch (error) {
      console.error(`Failed to hydrate island ${id}:`, error);
      element.setAttribute('data-hydration-error', error.message);
    }
  }

  // ==========================================================================
  // Visibility Strategy (IntersectionObserver)
  // ==========================================================================

  /**
   * Initialize visibility observer if needed.
   */
  function initVisibilityObserver() {
    if (visibilityObserver) return;

    visibilityObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const element = entry.target;
            const id = element.getAttribute('data-island');
            if (id && !hydratedIslands.has(id)) {
              hydrateIsland(id);
              visibilityObserver.unobserve(element);
            }
          }
        });
      },
      {
        rootMargin: '50px', // Start hydrating 50px before visible
        threshold: 0
      }
    );
  }

  /**
   * Observe an island for visibility.
   * 
   * @param {string} id - Island ID
   * @param {HTMLElement} element - Island element
   */
  function observeVisibility(id, element) {
    initVisibilityObserver();
    visibilityObserver.observe(element);
    log(`Observing visibility for island: ${id}`);
  }

  // ==========================================================================
  // Idle Strategy (requestIdleCallback + Interaction)
  // ==========================================================================

  /**
   * Schedule hydration for when browser is idle.
   * 
   * @param {string} id - Island ID
   * @param {HTMLElement} element - Island element
   */
  function scheduleIdleHydration(id, element) {
    // Hydrate on any user interaction
    const interactionHandler = () => {
      hydrateIsland(id);
      removeInteractionListeners();
    };

    const removeInteractionListeners = () => {
      element.removeEventListener('click', interactionHandler);
      element.removeEventListener('focus', interactionHandler, true);
      element.removeEventListener('mouseover', interactionHandler);
      element.removeEventListener('touchstart', interactionHandler);
    };

    element.addEventListener('click', interactionHandler);
    element.addEventListener('focus', interactionHandler, true);
    element.addEventListener('mouseover', interactionHandler, { once: true });
    element.addEventListener('touchstart', interactionHandler, { once: true });

    // Also hydrate when browser is idle
    if ('requestIdleCallback' in window) {
      requestIdleCallback(() => {
        if (!hydratedIslands.has(id)) {
          hydrateIsland(id);
          removeInteractionListeners();
        }
      }, { timeout: 2000 }); // Max 2 second delay
    } else {
      // Fallback for Safari
      setTimeout(() => {
        if (!hydratedIslands.has(id)) {
          hydrateIsland(id);
          removeInteractionListeners();
        }
      }, 200);
    }

    log(`Scheduled idle hydration for island: ${id}`);
  }

  // ==========================================================================
  // Media Query Strategy
  // ==========================================================================

  /**
   * Observe a media query for an island.
   * 
   * @param {string} id - Island ID
   * @param {string} query - Media query string
   */
  function observeMediaQuery(id, query) {
    if (!query) {
      warn(`No media query specified for island ${id}, hydrating immediately`);
      hydrateIsland(id);
      return;
    }

    const mediaQuery = window.matchMedia(query);
    
    const handler = (e) => {
      if (e.matches && !hydratedIslands.has(id)) {
        hydrateIsland(id);
        mediaQuery.removeEventListener('change', handler);
      }
    };

    if (mediaQuery.matches) {
      // Already matches, hydrate immediately
      hydrateIsland(id);
    } else {
      mediaQuery.addEventListener('change', handler);
      mediaQueryListeners.set(id, mediaQuery);
      log(`Observing media query for island ${id}: ${query}`);
    }
  }

  // ==========================================================================
  // DOM Connection
  // ==========================================================================

  /**
   * Connect event handlers within an island.
   * 
   * @param {HTMLElement} element - Island root element
   */
  function connectEventHandlers(element) {
    // Find all elements with data-event attributes
    const eventElements = element.querySelectorAll('[data-onclick], [data-onchange], [data-oninput], [data-onsubmit]');
    
    eventElements.forEach(el => {
      // onclick
      const onclickId = el.getAttribute('data-onclick');
      if (onclickId) {
        const handler = __pynext__.getHandler?.(onclickId);
        if (handler) {
          el.addEventListener('click', handler);
        }
      }

      // onchange
      const onchangeId = el.getAttribute('data-onchange');
      if (onchangeId) {
        const handler = __pynext__.getHandler?.(onchangeId);
        if (handler) {
          el.addEventListener('change', handler);
        }
      }

      // oninput
      const oninputId = el.getAttribute('data-oninput');
      if (oninputId) {
        const handler = __pynext__.getHandler?.(oninputId);
        if (handler) {
          el.addEventListener('input', handler);
        }
      }

      // onsubmit
      const onsubmitId = el.getAttribute('data-onsubmit');
      if (onsubmitId) {
        const handler = __pynext__.getHandler?.(onsubmitId);
        if (handler) {
          el.addEventListener('submit', handler);
        }
      }
    });
  }

  /**
   * Connect signals to DOM elements within an island.
   * 
   * @param {HTMLElement} element - Island root element
   * @param {Object} signals - Signal data
   */
  function connectSignals(element, signals) {
    // Find all elements with data-signal-bind
    const signalElements = element.querySelectorAll('[data-signal-bind]');
    
    signalElements.forEach(el => {
      const signalId = el.getAttribute('data-signal-bind');
      const signal = signals[signalId] || __pynext__.getSignal?.(signalId);
      
      if (signal) {
        // Subscribe to signal changes
        if (typeof signal.subscribe === 'function') {
          signal.subscribe(value => {
            updateElementWithSignal(el, value);
          });
        }

        // For input elements, also update signal on change
        if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.tagName === 'SELECT') {
          el.addEventListener('input', (e) => {
            if (typeof signal.set === 'function') {
              signal.set(e.target.value);
            }
          });
        }
      }
    });
  }

  /**
   * Update a DOM element with a signal value.
   * 
   * @param {HTMLElement} element - Element to update
   * @param {*} value - Signal value
   */
  function updateElementWithSignal(element, value) {
    const bindType = element.getAttribute('data-signal-type') || 'text';
    
    switch (bindType) {
      case 'text':
        element.textContent = String(value);
        break;
      case 'html':
        element.innerHTML = String(value);
        break;
      case 'value':
        element.value = value;
        break;
      case 'checked':
        element.checked = Boolean(value);
        break;
      case 'class':
        element.className = String(value);
        break;
      case 'style':
        Object.assign(element.style, value);
        break;
      case 'attr':
        const attrName = element.getAttribute('data-signal-attr');
        if (attrName) {
          element.setAttribute(attrName, String(value));
        }
        break;
    }
  }

  // ==========================================================================
  // Island Bundle Loading
  // ==========================================================================

  /**
   * Load an island's JavaScript bundle dynamically.
   * 
   * @param {string} componentName - Component name
   * @returns {Promise<Function>} Component factory
   */
  async function loadIslandBundle(componentName) {
    const bundleUrl = `/__pynext__/islands/${componentName}.js`;
    
    try {
      // Dynamic import
      const module = await import(bundleUrl);
      
      if (module.default) {
        registerComponent(componentName, module.default);
        return module.default;
      }
      
      throw new Error(`No default export in island bundle: ${componentName}`);
    } catch (error) {
      console.error(`Failed to load island bundle: ${componentName}`, error);
      throw error;
    }
  }

  /**
   * Prefetch island bundles for faster hydration.
   * 
   * @param {string[]} componentNames - Components to prefetch
   */
  function prefetchIslands(componentNames) {
    componentNames.forEach(name => {
      if (!componentFactories.has(name)) {
        const link = document.createElement('link');
        link.rel = 'modulepreload';
        link.href = `/__pynext__/islands/${name}.js`;
        document.head.appendChild(link);
      }
    });
  }

  // ==========================================================================
  // Utilities
  // ==========================================================================

  /**
   * Check if an island has been hydrated.
   * 
   * @param {string} id - Island ID
   * @returns {boolean}
   */
  function isHydrated(id) {
    return hydratedIslands.has(id);
  }

  /**
   * Get all island IDs.
   * 
   * @returns {string[]}
   */
  function getIslandIds() {
    return Array.from(islands.keys());
  }

  /**
   * Get hydration stats.
   * 
   * @returns {Object}
   */
  function getStats() {
    return {
      total: islands.size,
      hydrated: hydratedIslands.size,
      pending: islands.size - hydratedIslands.size,
      byStrategy: {
        load: Array.from(islands.values()).filter(i => i.strategy === 'load').length,
        visible: Array.from(islands.values()).filter(i => i.strategy === 'visible').length,
        idle: Array.from(islands.values()).filter(i => i.strategy === 'idle').length,
        media: Array.from(islands.values()).filter(i => i.strategy === 'media').length,
        none: Array.from(islands.values()).filter(i => i.strategy === 'none').length,
      }
    };
  }

  /**
   * Force hydrate all pending islands.
   * Useful for testing or when you need everything interactive immediately.
   */
  function hydrateAll() {
    islands.forEach((_, id) => {
      if (!hydratedIslands.has(id)) {
        hydrateIsland(id);
      }
    });
  }

  // ==========================================================================
  // Logging
  // ==========================================================================

  const DEBUG = window.__PYNEXT_DEBUG__ || false;

  function log(...args) {
    if (DEBUG) {
      console.log('[PyNext Islands]', ...args);
    }
  }

  function warn(...args) {
    console.warn('[PyNext Islands]', ...args);
  }

  // ==========================================================================
  // Export to Global
  // ==========================================================================

  if (typeof window !== 'undefined') {
    window.__pynext__ = window.__pynext__ || {};
    
    // Core API
    window.__pynext__.registerIsland = registerIsland;
    window.__pynext__.registerComponent = registerComponent;
    window.__pynext__.hydrateIslands = hydrateIslands;
    window.__pynext__.hydrateIsland = hydrateIsland;
    window.__pynext__.hydrateAll = hydrateAll;
    
    // Bundle loading
    window.__pynext__.loadIslandBundle = loadIslandBundle;
    window.__pynext__.prefetchIslands = prefetchIslands;
    
    // Queries
    window.__pynext__.isHydrated = isHydrated;
    window.__pynext__.getIslandIds = getIslandIds;
    window.__pynext__.getIslandStats = getStats;
    
    // Internal (for other modules)
    window.__pynext__._islands = islands;
    window.__pynext__._hydratedIslands = hydratedIslands;
  }

  // Module exports
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
      registerIsland,
      registerComponent,
      hydrateIslands,
      hydrateIsland,
      hydrateAll,
      loadIslandBundle,
      prefetchIslands,
      isHydrated,
      getIslandIds,
      getStats
    };
  }

})();

