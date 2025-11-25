/**
 * Resource - Async data fetching primitive for PyNext
 * 
 * Client-side implementation that syncs with server-resolved resources
 * and provides reactive loading/error/data states.
 * 
 * API mirrors SolidJS's createResource:
 * - resource() - Get the data
 * - resource.loading - Is fetching?
 * - resource.error - Any error?
 * - resource.refetch() - Force refetch
 * - resource.mutate(value) - Optimistic update
 */

(function() {
  'use strict';

  // Resource states (matches Python enum)
  const ResourceState = {
    UNRESOLVED: 'unresolved',
    PENDING: 'pending',
    READY: 'ready',
    REFRESHING: 'refreshing',
    ERRORED: 'errored'
  };

  // Resource registry
  const resources = new Map();

  /**
   * Create a Resource for async data fetching.
   * 
   * @param {string} id - Unique resource ID
   * @param {Object} options - Resource options
   * @param {Function} options.fetcher - Async function to fetch data
   * @param {Function} options.source - Optional reactive source (signal getter)
   * @param {*} options.initialValue - Initial value before fetch
   * @returns {Function} Resource accessor with .loading, .error, .refetch, .mutate
   */
  function createResource(id, options = {}) {
    const {
      fetcher = null,
      source = null,
      initialValue = null,
      state: initialState = ResourceState.UNRESOLVED,
      data: initialData = null,
      error: initialError = null,
      fetchedAt = null
    } = options;

    // Internal state using signals
    const stateSignal = __pynext__.createSignal(id + '_state', initialState);
    const dataSignal = __pynext__.createSignal(id + '_data', initialData ?? initialValue);
    const errorSignal = __pynext__.createSignal(id + '_error', initialError);
    
    let latest = initialData ?? initialValue;
    let lastSourceValue = null;
    let fetchCount = 0;
    let lastFetchId = 0;
    let cachedFetchedAt = fetchedAt;

    /**
     * Get current source value if source is reactive
     */
    function getSourceValue() {
      if (!source) return null;
      if (typeof source === 'function') return source();
      return source;
    }

    /**
     * Perform the fetch operation
     */
    async function doFetch(refetch = false) {
      if (!fetcher) {
        console.warn(`Resource ${id} has no fetcher defined`);
        return dataSignal[0]();
      }

      const sourceValue = getSourceValue();

      // Check if cached (unless refetching)
      if (!refetch && stateSignal[0]() === ResourceState.READY) {
        if (sourceValue === lastSourceValue) {
          return dataSignal[0]();
        }
      }

      // Track this fetch
      fetchCount++;
      const myFetchId = fetchCount;
      lastFetchId = myFetchId;
      lastSourceValue = sourceValue;

      // Update state
      if (stateSignal[0]() === ResourceState.READY) {
        stateSignal[1](ResourceState.REFRESHING);
      } else {
        stateSignal[1](ResourceState.PENDING);
      }
      errorSignal[1](null);

      try {
        // Call fetcher with source if provided
        const result = sourceValue !== null 
          ? await fetcher(sourceValue)
          : await fetcher();

        // Only update if this is still the latest fetch
        if (myFetchId === lastFetchId) {
          dataSignal[1](result);
          latest = result;
          stateSignal[1](ResourceState.READY);
          cachedFetchedAt = Date.now();
        }

        return result;
      } catch (err) {
        // Only update if this is still the latest fetch
        if (myFetchId === lastFetchId) {
          errorSignal[1](err);
          stateSignal[1](ResourceState.ERRORED);
        }
        throw err;
      }
    }

    /**
     * The resource accessor function
     */
    function resource() {
      return dataSignal[0]();
    }

    // Attach properties
    Object.defineProperties(resource, {
      /**
       * Loading state signal
       */
      loading: {
        get() {
          const state = stateSignal[0]();
          return state === ResourceState.PENDING || state === ResourceState.REFRESHING;
        }
      },

      /**
       * Error signal
       */
      error: {
        get() {
          return errorSignal[0]();
        }
      },

      /**
       * Current state
       */
      state: {
        get() {
          return stateSignal[0]();
        }
      },

      /**
       * Last successful value (doesn't change during refresh)
       */
      latest: {
        get() {
          return latest;
        }
      }
    });

    /**
     * Force refetch
     */
    resource.refetch = function() {
      return doFetch(true);
    };

    /**
     * Optimistically update the resource
     */
    resource.mutate = function(value) {
      dataSignal[1](value);
      latest = value;
      stateSignal[1](ResourceState.READY);
      return value;
    };

    /**
     * Invalidate the cache
     */
    resource.invalidate = function() {
      cachedFetchedAt = null;
      stateSignal[1](ResourceState.UNRESOLVED);
    };

    /**
     * Fetch if not already fetched
     */
    resource.fetch = function() {
      return doFetch(false);
    };

    // Store in registry
    resources.set(id, resource);

    return resource;
  }

  /**
   * Hydrate a resource from server-provided data.
   * 
   * @param {string} id - Resource ID
   * @param {Object} data - Hydration data from server
   */
  function hydrateResource(id, data) {
    const existing = resources.get(id);
    
    if (existing) {
      // Update existing resource
      if (data.state === ResourceState.READY) {
        existing.mutate(data.data);
      }
      return existing;
    }

    // Create new resource with hydrated state
    return createResource(id, {
      state: data.state || ResourceState.UNRESOLVED,
      data: data.data,
      error: data.error,
      fetchedAt: data.fetchedAt
    });
  }

  /**
   * Get a resource by ID
   */
  function getResource(id) {
    return resources.get(id);
  }

  /**
   * Wait for all resources to be ready
   */
  async function waitForResources(resourceIds) {
    const pending = resourceIds
      .map(id => resources.get(id))
      .filter(r => r && (r.state === ResourceState.UNRESOLVED || r.state === ResourceState.PENDING));

    if (pending.length === 0) return;

    await Promise.all(pending.map(r => r.fetch()));
  }

  /**
   * Check if any resources are pending
   */
  function hasPendingResources() {
    for (const resource of resources.values()) {
      const state = resource.state;
      if (state === ResourceState.UNRESOLVED || state === ResourceState.PENDING) {
        return true;
      }
    }
    return false;
  }

  // Export to global PyNext namespace
  if (typeof window !== 'undefined') {
    window.__pynext__ = window.__pynext__ || {};
    window.__pynext__.ResourceState = ResourceState;
    window.__pynext__.createResource = createResource;
    window.__pynext__.hydrateResource = hydrateResource;
    window.__pynext__.getResource = getResource;
    window.__pynext__.waitForResources = waitForResources;
    window.__pynext__.hasPendingResources = hasPendingResources;
    window.__pynext__.resources = resources;
  }

  // Also export for module systems
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
      ResourceState,
      createResource,
      hydrateResource,
      getResource,
      waitForResources,
      hasPendingResources
    };
  }

})();

