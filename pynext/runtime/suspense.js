/**
 * Suspense Runtime for PyNext
 * 
 * Handles client-side Suspense boundaries:
 * - Shows fallback while resources load
 * - Replaces fallback when content ready
 * - Handles streaming replacements from server
 * - Coordinates with Resource loading states
 */

(function() {
  'use strict';

  // Suspense boundary states
  const SuspenseState = {
    PENDING: 'pending',
    RESOLVED: 'resolved',
    FALLBACK: 'fallback',
    TIMEOUT: 'timeout'
  };

  // Registry of Suspense boundaries
  const suspenseBoundaries = new Map();

  /**
   * Create a Suspense boundary.
   * 
   * @param {string} id - Unique boundary ID
   * @param {Object} options - Boundary options
   * @param {string[]} options.pendingResources - IDs of pending resources
   * @param {number|null} options.timeout - Timeout in ms
   */
  function createSuspense(id, options = {}) {
    const {
      pendingResources = [],
      timeout = null
    } = options;

    const boundary = {
      id,
      state: pendingResources.length > 0 ? SuspenseState.PENDING : SuspenseState.RESOLVED,
      pendingResources: new Set(pendingResources),
      timeout,
      element: null,
      timeoutId: null
    };

    suspenseBoundaries.set(id, boundary);

    // Find DOM element
    boundary.element = document.querySelector(`[data-suspense="${id}"]`);

    // Set up timeout if specified
    if (timeout && boundary.state === SuspenseState.PENDING) {
      boundary.timeoutId = setTimeout(() => {
        if (boundary.state === SuspenseState.PENDING) {
          boundary.state = SuspenseState.TIMEOUT;
          updateBoundaryDOM(boundary);
        }
      }, timeout);
    }

    // Watch for resource resolutions
    if (pendingResources.length > 0) {
      watchResources(boundary);
    }

    return boundary;
  }

  /**
   * Watch resources and resolve boundary when all complete.
   */
  function watchResources(boundary) {
    const checkResources = () => {
      const allResolved = [...boundary.pendingResources].every(resourceId => {
        const resource = __pynext__.getResource?.(resourceId);
        return resource && resource.state === 'ready';
      });

      if (allResolved) {
        resolveBoundary(boundary.id);
      }
    };

    // Check immediately
    checkResources();

    // Also set up polling (resources don't have native subscriptions yet)
    if (boundary.state === SuspenseState.PENDING) {
      const pollId = setInterval(() => {
        if (boundary.state !== SuspenseState.PENDING) {
          clearInterval(pollId);
          return;
        }
        checkResources();
      }, 100);
    }
  }

  /**
   * Mark a Suspense boundary as resolved.
   * 
   * @param {string} id - Boundary ID
   */
  function resolveBoundary(id) {
    const boundary = suspenseBoundaries.get(id);
    if (!boundary) return;

    // Clear timeout
    if (boundary.timeoutId) {
      clearTimeout(boundary.timeoutId);
      boundary.timeoutId = null;
    }

    boundary.state = SuspenseState.RESOLVED;
    updateBoundaryDOM(boundary);
  }

  /**
   * Update DOM to reflect boundary state.
   */
  function updateBoundaryDOM(boundary) {
    if (!boundary.element) {
      boundary.element = document.querySelector(`[data-suspense="${boundary.id}"]`);
    }

    if (boundary.element) {
      boundary.element.setAttribute('data-state', boundary.state);

      // If resolved, show template content
      if (boundary.state === SuspenseState.RESOLVED) {
        const template = boundary.element.querySelector('[data-suspense-content]');
        const fallback = boundary.element.querySelector('[data-suspense-fallback]');
        
        if (template && template.content) {
          // Replace with template content
          const content = template.content.cloneNode(true);
          boundary.element.innerHTML = '';
          boundary.element.appendChild(content);
          
          // Hydrate new content
          if (__pynext__.hydrateElement) {
            __pynext__.hydrateElement(boundary.element);
          }
        } else if (fallback) {
          fallback.style.display = 'none';
        }
      }
    }
  }

  /**
   * Replace a Suspense placeholder with new content.
   * 
   * Called by streaming scripts when server-side content resolves.
   * 
   * @param {string} id - Boundary ID
   * @param {string} html - New HTML content
   */
  function replaceSuspense(id, html) {
    const boundary = suspenseBoundaries.get(id);
    
    let element = boundary?.element;
    if (!element) {
      element = document.querySelector(`[data-suspense="${id}"]`);
    }

    if (element) {
      // Create temp container
      const temp = document.createElement('div');
      temp.innerHTML = html;

      // Replace placeholder with content
      while (temp.firstChild) {
        element.parentNode.insertBefore(temp.firstChild, element);
      }
      element.remove();

      // Update boundary state
      if (boundary) {
        boundary.state = SuspenseState.RESOLVED;
        boundary.element = null;
      }

      // Hydrate new content
      if (__pynext__.hydrate) {
        __pynext__.hydrate();
      }
    }
  }

  /**
   * Get a Suspense boundary by ID.
   */
  function getSuspense(id) {
    return suspenseBoundaries.get(id);
  }

  /**
   * Check if any Suspense boundaries are pending.
   */
  function hasPendingSuspense() {
    for (const boundary of suspenseBoundaries.values()) {
      if (boundary.state === SuspenseState.PENDING) {
        return true;
      }
    }
    return false;
  }

  /**
   * Wait for all Suspense boundaries to resolve.
   * 
   * @param {number} timeout - Maximum wait time in ms
   * @returns {Promise<boolean>} - True if all resolved, false if timeout
   */
  async function waitForSuspense(timeout = 10000) {
    const start = Date.now();

    while (hasPendingSuspense()) {
      if (Date.now() - start > timeout) {
        return false;
      }
      await new Promise(resolve => setTimeout(resolve, 50));
    }

    return true;
  }

  // ==========================================================================
  // Show/Switch/Match Components
  // ==========================================================================

  /**
   * Show component - conditional rendering.
   * 
   * @param {HTMLElement} element - Container element
   * @param {Function} condition - Condition function
   */
  function setupShow(element, condition) {
    const updateVisibility = () => {
      const shouldShow = typeof condition === 'function' ? condition() : condition;
      const content = element.querySelector('[data-show-content]');
      const fallback = element.querySelector('[data-show-fallback]');

      if (content) content.style.display = shouldShow ? '' : 'none';
      if (fallback) fallback.style.display = shouldShow ? 'none' : '';
    };

    // Initial update
    updateVisibility();

    // If condition uses signals, it will auto-update
    // For now, return the update function for manual calls
    return updateVisibility;
  }

  // ==========================================================================
  // Error Boundary Support
  // ==========================================================================

  /**
   * Set up error boundary handling.
   * 
   * @param {HTMLElement} element - Boundary element
   * @param {Function} onError - Error handler
   */
  function setupErrorBoundary(element, onError) {
    const handleError = (error) => {
      const fallback = element.querySelector('[data-error-fallback]');
      const content = element.querySelector('[data-error-content]');

      if (content) content.style.display = 'none';
      if (fallback) {
        fallback.style.display = '';
        // Render error message
        const messageEl = fallback.querySelector('[data-error-message]');
        if (messageEl) {
          messageEl.textContent = error.message || String(error);
        }
      }

      if (onError) onError(error);
    };

    // Catch errors in child scripts
    window.addEventListener('error', (event) => {
      if (element.contains(event.target)) {
        handleError(event.error);
      }
    });

    return handleError;
  }

  // ==========================================================================
  // Export to global PyNext namespace
  // ==========================================================================

  if (typeof window !== 'undefined') {
    window.__pynext__ = window.__pynext__ || {};
    
    // Suspense
    window.__pynext__.SuspenseState = SuspenseState;
    window.__pynext__.createSuspense = createSuspense;
    window.__pynext__.resolveBoundary = resolveBoundary;
    window.__pynext__.replaceSuspense = replaceSuspense;
    window.__pynext__.getSuspense = getSuspense;
    window.__pynext__.hasPendingSuspense = hasPendingSuspense;
    window.__pynext__.waitForSuspense = waitForSuspense;
    window.__pynext__.suspenseBoundaries = suspenseBoundaries;
    
    // Conditional rendering
    window.__pynext__.setupShow = setupShow;
    window.__pynext__.setupErrorBoundary = setupErrorBoundary;
  }

  // Module exports
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
      SuspenseState,
      createSuspense,
      resolveBoundary,
      replaceSuspense,
      getSuspense,
      hasPendingSuspense,
      waitForSuspense,
      setupShow,
      setupErrorBoundary
    };
  }

})();

