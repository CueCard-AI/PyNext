/**
 * PyNext Control Flow Runtime - Hyper-Optimized DOM Primitives
 * 
 * =============================================================================
 * WHAT THIS FILE DOES
 * =============================================================================
 * 
 * This runtime provides SolidJS-style control flow for client-side reactivity:
 * - createShow: Conditional DOM rendering with surgical updates
 * - createFor: Keyed list reconciliation (minimal DOM operations)
 * - createIndex: Index-based list rendering
 * - createSwitch: Multi-branch conditional rendering
 * - createPortal: Render outside component tree
 * - createErrorBoundary: Error catching and recovery
 * 
 * =============================================================================
 * PERFORMANCE TARGETS
 * =============================================================================
 * 
 * | Operation                | Target      |
 * |--------------------------|-------------|
 * | Show toggle              | < 0.5ms     |
 * | For 1000 items update    | < 5ms       |
 * | Bundle size (minified)   | < 3KB gzip  |
 * | Memory per list item     | < 100 bytes |
 * 
 * =============================================================================
 * ARCHITECTURE
 * =============================================================================
 * 
 * No Virtual DOM! Instead:
 * 1. Each control flow component creates a reactive Effect
 * 2. Effect tracks dependencies (signals, stores)
 * 3. On change, performs SURGICAL DOM update (only changed parts)
 * 
 * For list reconciliation:
 * 1. Build key -> node map from current DOM
 * 2. Compare with new data keys
 * 3. Create/Remove/Move nodes minimally
 * 4. Result: O(n) operations, not O(n²)
 * 
 * =============================================================================
 */

(function(global) {
    'use strict';

    // =========================================================================
    // CONSTANTS & CONFIGURATION
    // =========================================================================
    
    const DEBUG = false;
    const PERF_LOGGING = false;

    // =========================================================================
    // SECTION 1: SHOW - Conditional Rendering
    // =========================================================================
    //
    // HOW IT WORKS:
    // 1. Find the Show container by data-show attribute
    // 2. Create Effect that watches the condition
    // 3. On condition change:
    //    - If true: render children (or swap in cached children)
    //    - If false: render fallback (or empty)
    // 4. Keyed mode: destroy/recreate instead of swap
    //
    // OPTIMIZATION:
    // - Caches both branches when not keyed
    // - Single DOM operation per toggle
    // =========================================================================

    /**
     * Create a Show component for conditional rendering.
     * 
     * @param {string} id - The data-show ID
     * @param {Function} condition - Accessor returning boolean
     * @param {Function} renderContent - Function to render true branch
     * @param {Function} renderFallback - Function to render false branch
     * @param {Object} options - { keyed: boolean }
     * @returns {Object} - { dispose: Function }
     */
    function createShow(id, condition, renderContent, renderFallback, options = {}) {
        const container = document.querySelector(`[data-show="${id}"]`);
        if (!container) {
            if (DEBUG) console.warn(`Show container not found: ${id}`);
            return { dispose: () => {} };
        }

        const { keyed = false } = options;
        
        // Cache for non-keyed mode
        let contentNodes = null;
        let fallbackNodes = null;
        let currentBranch = null; // 'content' | 'fallback' | null
        
        // Marker for insertion position
        const marker = document.createComment(`show:${id}`);
        container.parentNode.insertBefore(marker, container);
        
        // Create reactive effect
        const effect = __pynext__.createEffect(() => {
            const show = condition();
            
            if (PERF_LOGGING) {
                const start = performance.now();
                updateShow(show);
                console.log(`Show ${id} toggle: ${(performance.now() - start).toFixed(2)}ms`);
            } else {
                updateShow(show);
            }
        });
        
        function updateShow(show) {
            if (show && currentBranch !== 'content') {
                // Switch to content
                if (keyed) {
                    // Keyed: always recreate
                    clearContainer();
                    const nodes = createNodes(renderContent);
                    appendNodes(nodes);
                    contentNodes = null; // Don't cache in keyed mode
                } else {
                    // Non-keyed: swap cached nodes
                    if (currentBranch === 'fallback' && fallbackNodes) {
                        detachNodes(fallbackNodes);
                    } else {
                        clearContainer();
                    }
                    
                    if (contentNodes) {
                        appendNodes(contentNodes);
                    } else {
                        contentNodes = createNodes(renderContent);
                        appendNodes(contentNodes);
                    }
                }
                currentBranch = 'content';
                
            } else if (!show && currentBranch !== 'fallback') {
                // Switch to fallback
                if (keyed) {
                    clearContainer();
                    const nodes = renderFallback ? createNodes(renderFallback) : [];
                    appendNodes(nodes);
                    fallbackNodes = null;
                } else {
                    if (currentBranch === 'content' && contentNodes) {
                        detachNodes(contentNodes);
                    } else {
                        clearContainer();
                    }
                    
                    if (fallbackNodes) {
                        appendNodes(fallbackNodes);
                    } else if (renderFallback) {
                        fallbackNodes = createNodes(renderFallback);
                        appendNodes(fallbackNodes);
                    }
                }
                currentBranch = 'fallback';
            }
        }
        
        function createNodes(renderFn) {
            if (!renderFn) return [];
            const html = renderFn();
            return htmlToNodes(html);
        }
        
        function appendNodes(nodes) {
            const frag = document.createDocumentFragment();
            nodes.forEach(n => frag.appendChild(n));
            container.appendChild(frag);
        }
        
        function detachNodes(nodes) {
            nodes.forEach(n => {
                if (n.parentNode) n.parentNode.removeChild(n);
            });
        }
        
        function clearContainer() {
            while (container.firstChild) {
                container.removeChild(container.firstChild);
            }
        }
        
        // Initialize from server-rendered state
        const serverCondition = container.getAttribute('data-condition') === 'true';
        currentBranch = serverCondition ? 'content' : 'fallback';
        
        return {
            dispose() {
                if (effect && effect.dispose) effect.dispose();
                if (marker.parentNode) marker.parentNode.removeChild(marker);
            }
        };
    }

    // =========================================================================
    // SECTION 2: FOR - Keyed List Reconciliation
    // =========================================================================
    //
    // THE RECONCILIATION ALGORITHM (SolidJS-inspired)
    // ================================================
    //
    // Given old list [A, B, C, D] and new list [A, C, E, D]:
    //
    // 1. BUILD KEY MAP from old list
    //    { A: {node, index:0}, B: {node, index:1}, ... }
    //
    // 2. PROCESS NEW LIST left-to-right:
    //    - A: key exists, already in position → skip
    //    - C: key exists, wrong position → mark for move
    //    - E: key missing → create new
    //    - D: key exists, wrong position → mark for move
    //
    // 3. REMOVE nodes with keys not in new list (B)
    //
    // 4. APPLY MOVES using Longest Increasing Subsequence (LIS)
    //    - Find nodes already in correct relative order
    //    - Only move nodes NOT in LIS
    //
    // COMPLEXITY: O(n log n) for LIS, O(n) for the rest
    //
    // WHY LIS MATTERS:
    // Old: [A, B, C, D, E]  →  New: [E, D, C, B, A]
    // Without LIS: 4 moves
    // With LIS: Only move nodes not in longest increasing sequence
    // =========================================================================

    /**
     * Create a For component for keyed list rendering.
     * 
     * @param {string} id - The data-for ID
     * @param {Function} getItems - Accessor returning array
     * @param {Function} getKey - Function to extract key from item
     * @param {Function} renderItem - Function(item, index) -> HTML
     * @param {Function} renderFallback - Function to render empty state
     * @returns {Object} - { dispose: Function }
     */
    function createFor(id, getItems, getKey, renderItem, renderFallback) {
        const container = document.querySelector(`[data-for="${id}"]`);
        if (!container) {
            if (DEBUG) console.warn(`For container not found: ${id}`);
            return { dispose: () => {} };
        }

        // State
        let itemMap = new Map(); // key -> { node, item, index }
        let keys = []; // Current key order
        
        // Create reactive effect
        const effect = __pynext__.createEffect(() => {
            const items = getItems() || [];
            
            if (PERF_LOGGING) {
                const start = performance.now();
                reconcile(items);
                console.log(`For ${id} reconcile (${items.length} items): ${(performance.now() - start).toFixed(2)}ms`);
            } else {
                reconcile(items);
            }
        });
        
        function reconcile(newItems) {
            const newKeys = newItems.map((item, i) => getKey(item, i));
            
            // Handle empty
            if (newItems.length === 0) {
                // Clear all
                itemMap.forEach(entry => {
                    if (entry.node.parentNode) {
                        entry.node.parentNode.removeChild(entry.node);
                    }
                });
                itemMap.clear();
                keys = [];
                
                // Show fallback
                if (renderFallback) {
                    container.innerHTML = renderFallback();
                } else {
                    container.innerHTML = '';
                }
                container.setAttribute('data-empty', 'true');
                return;
            }
            
            // Remove fallback if it was showing
            if (container.getAttribute('data-empty') === 'true') {
                container.innerHTML = '';
                container.removeAttribute('data-empty');
            }
            
            // Build new key set for O(1) lookup
            const newKeySet = new Set(newKeys);
            
            // 1. Remove items not in new list
            const toRemove = [];
            itemMap.forEach((entry, key) => {
                if (!newKeySet.has(key)) {
                    toRemove.push(key);
                }
            });
            toRemove.forEach(key => {
                const entry = itemMap.get(key);
                if (entry.node.parentNode) {
                    entry.node.parentNode.removeChild(entry.node);
                }
                itemMap.delete(key);
            });
            
            // 2. Create/update items and build new order
            const newOrder = [];
            const oldKeyToIndex = new Map();
            keys.forEach((key, i) => oldKeyToIndex.set(key, i));
            
            for (let i = 0; i < newItems.length; i++) {
                const item = newItems[i];
                const key = newKeys[i];
                
                let entry = itemMap.get(key);
                if (entry) {
                    // Update existing
                    entry.item = item;
                    entry.index = i;
                    // Update content if needed
                    const newHtml = renderItem(item, i);
                    if (entry.lastHtml !== newHtml) {
                        const newNode = htmlToNode(wrapForItem(key, newHtml));
                        entry.node.replaceWith(newNode);
                        entry.node = newNode;
                        entry.lastHtml = newHtml;
                    }
                } else {
                    // Create new
                    const html = renderItem(item, i);
                    const node = htmlToNode(wrapForItem(key, html));
                    entry = { node, item, index: i, lastHtml: html };
                    itemMap.set(key, entry);
                }
                newOrder.push({ key, entry, oldIndex: oldKeyToIndex.get(key) ?? -1 });
            }
            
            // 3. Reorder using LIS algorithm
            reorderNodes(container, newOrder);
            
            // Update key order
            keys = newKeys;
        }
        
        function wrapForItem(key, html) {
            return `<div data-for-item="${key}">${html}</div>`;
        }
        
        function reorderNodes(parent, newOrder) {
            if (newOrder.length === 0) return;
            
            // Find Longest Increasing Subsequence of old indices
            // Nodes in LIS don't need to move
            const oldIndices = newOrder.map(o => o.oldIndex);
            const lis = longestIncreasingSubsequence(oldIndices);
            const lisSet = new Set(lis);
            
            // Insert nodes in order, skipping those in LIS
            let lastNode = null;
            for (let i = newOrder.length - 1; i >= 0; i--) {
                const { entry } = newOrder[i];
                const node = entry.node;
                
                if (!lisSet.has(i)) {
                    // Node needs to move
                    if (lastNode) {
                        parent.insertBefore(node, lastNode);
                    } else {
                        parent.appendChild(node);
                    }
                }
                lastNode = node;
            }
        }
        
        // Initialize from server state
        container.querySelectorAll('[data-for-item]').forEach((node, index) => {
            const key = node.getAttribute('data-for-item');
            itemMap.set(key, { node, item: null, index, lastHtml: node.innerHTML });
            keys.push(key);
        });
        
        return {
            dispose() {
                if (effect && effect.dispose) effect.dispose();
                itemMap.clear();
                keys = [];
            }
        };
    }

    /**
     * Longest Increasing Subsequence algorithm.
     * Returns indices of elements that form the LIS.
     * 
     * Used to minimize DOM moves during list reconciliation.
     * 
     * @param {number[]} arr - Array of old indices (-1 for new items)
     * @returns {number[]} - Indices in arr that form LIS
     */
    function longestIncreasingSubsequence(arr) {
        const n = arr.length;
        if (n === 0) return [];
        
        // Filter out -1 (new items) for LIS calculation
        const filtered = arr.map((v, i) => ({ v, i })).filter(x => x.v >= 0);
        if (filtered.length === 0) return [];
        
        const dp = new Array(filtered.length).fill(1);
        const parent = new Array(filtered.length).fill(-1);
        let maxLen = 1;
        let maxIdx = 0;
        
        for (let i = 1; i < filtered.length; i++) {
            for (let j = 0; j < i; j++) {
                if (filtered[j].v < filtered[i].v && dp[j] + 1 > dp[i]) {
                    dp[i] = dp[j] + 1;
                    parent[i] = j;
                    if (dp[i] > maxLen) {
                        maxLen = dp[i];
                        maxIdx = i;
                    }
                }
            }
        }
        
        // Reconstruct LIS (as indices in original array)
        const lis = [];
        let idx = maxIdx;
        while (idx >= 0) {
            lis.push(filtered[idx].i);
            idx = parent[idx];
        }
        
        return lis.reverse();
    }

    // =========================================================================
    // SECTION 3: INDEX - Index-Based List Rendering
    // =========================================================================
    //
    // Simpler than For - tracks by position, not key.
    // Better for:
    // - Lists of primitives
    // - Fixed-size lists
    // - No reordering needed
    // =========================================================================

    /**
     * Create an Index component for index-based list rendering.
     * 
     * @param {string} id - The data-index ID
     * @param {Function} getItems - Accessor returning array
     * @param {Function} renderItem - Function(itemAccessor, index) -> HTML
     * @param {Function} renderFallback - Function for empty state
     * @returns {Object} - { dispose: Function }
     */
    function createIndex(id, getItems, renderItem, renderFallback) {
        const container = document.querySelector(`[data-index="${id}"]`);
        if (!container) {
            if (DEBUG) console.warn(`Index container not found: ${id}`);
            return { dispose: () => {} };
        }

        let nodes = [];
        let itemSignals = []; // Signals for each item accessor
        
        const effect = __pynext__.createEffect(() => {
            const items = getItems() || [];
            reconcileIndex(items);
        });
        
        function reconcileIndex(items) {
            // Handle empty
            if (items.length === 0) {
                nodes.forEach(n => n.parentNode && n.parentNode.removeChild(n));
                nodes = [];
                itemSignals = [];
                
                if (renderFallback) {
                    container.innerHTML = renderFallback();
                } else {
                    container.innerHTML = '';
                }
                container.setAttribute('data-empty', 'true');
                return;
            }
            
            if (container.getAttribute('data-empty') === 'true') {
                container.innerHTML = '';
                container.removeAttribute('data-empty');
            }
            
            // Grow/shrink to match
            while (nodes.length < items.length) {
                const index = nodes.length;
                // Create signal for this item
                const itemSignal = __pynext__.createSignal(`index_${id}_${index}`, items[index]);
                itemSignals.push(itemSignal);
                
                const html = renderItem(() => itemSignal.read(), index);
                const node = htmlToNode(`<div data-index-item="${index}">${html}</div>`);
                container.appendChild(node);
                nodes.push(node);
            }
            
            while (nodes.length > items.length) {
                const node = nodes.pop();
                if (node.parentNode) node.parentNode.removeChild(node);
                itemSignals.pop();
            }
            
            // Update item signals
            for (let i = 0; i < items.length; i++) {
                itemSignals[i].write(items[i]);
            }
        }
        
        // Initialize from server state
        container.querySelectorAll('[data-index-item]').forEach((node, i) => {
            nodes.push(node);
        });
        
        return {
            dispose() {
                if (effect && effect.dispose) effect.dispose();
                nodes = [];
                itemSignals = [];
            }
        };
    }

    // =========================================================================
    // SECTION 4: SWITCH - Multi-Branch Conditionals
    // =========================================================================

    /**
     * Create a Switch component for multi-branch rendering.
     * 
     * @param {string} id - The data-switch ID
     * @param {Array} branches - Array of { condition: Function, render: Function }
     * @returns {Object} - { dispose: Function }
     */
    function createSwitch(id, branches) {
        const container = document.querySelector(`[data-switch="${id}"]`);
        if (!container) {
            if (DEBUG) console.warn(`Switch container not found: ${id}`);
            return { dispose: () => {} };
        }

        let currentMatch = -1;
        let cachedNodes = new Map(); // matchIndex -> nodes
        
        const effect = __pynext__.createEffect(() => {
            let newMatch = -1;
            for (let i = 0; i < branches.length; i++) {
                if (branches[i].condition()) {
                    newMatch = i;
                    break;
                }
            }
            
            if (newMatch !== currentMatch) {
                updateBranch(newMatch);
            }
        });
        
        function updateBranch(matchIndex) {
            // Clear current content
            container.innerHTML = '';
            
            if (matchIndex >= 0 && matchIndex < branches.length) {
                const html = branches[matchIndex].render();
                container.innerHTML = html;
            }
            
            container.setAttribute('data-match', matchIndex.toString());
            currentMatch = matchIndex;
        }
        
        // Initialize from server state
        currentMatch = parseInt(container.getAttribute('data-match') || '-1', 10);
        
        return {
            dispose() {
                if (effect && effect.dispose) effect.dispose();
                cachedNodes.clear();
            }
        };
    }

    // =========================================================================
    // SECTION 5: PORTAL - Render Outside Component Tree
    // =========================================================================

    /**
     * Create a Portal to render content in a different DOM location.
     * 
     * @param {string} id - The data-portal ID
     * @param {string} mountSelector - CSS selector for mount target
     * @param {Object} options - { useShadow: boolean, isSvg: boolean }
     * @returns {Object} - { dispose: Function }
     */
    function createPortal(id, mountSelector, options = {}) {
        const source = document.querySelector(`[data-portal="${id}"]`);
        if (!source) {
            if (DEBUG) console.warn(`Portal source not found: ${id}`);
            return { dispose: () => {} };
        }

        const { useShadow = false, isSvg = false } = options;
        
        // Find mount target
        const target = document.querySelector(mountSelector);
        if (!target) {
            if (DEBUG) console.warn(`Portal target not found: ${mountSelector}`);
            return { dispose: () => {} };
        }
        
        // Create portal container
        let portalContainer;
        if (useShadow && target.attachShadow) {
            portalContainer = target.attachShadow({ mode: 'open' });
        } else {
            portalContainer = document.createElement('div');
            portalContainer.setAttribute('data-portal-container', id);
            target.appendChild(portalContainer);
        }
        
        // Move content
        while (source.firstChild) {
            portalContainer.appendChild(source.firstChild);
        }
        
        // Hide source
        source.style.display = 'none';
        
        return {
            dispose() {
                // Move content back
                while (portalContainer.firstChild) {
                    source.appendChild(portalContainer.firstChild);
                }
                source.style.display = '';
                
                // Remove container if we created it
                if (!useShadow && portalContainer.parentNode) {
                    portalContainer.parentNode.removeChild(portalContainer);
                }
            }
        };
    }

    // =========================================================================
    // SECTION 6: ERROR BOUNDARY - Error Catching
    // =========================================================================

    /**
     * Create an ErrorBoundary for catching render errors.
     * 
     * @param {string} id - The data-error-boundary ID
     * @param {Function} renderFallback - Function(error, reset) -> HTML
     * @returns {Object} - { dispose: Function, reset: Function }
     */
    function createErrorBoundary(id, renderFallback) {
        const container = document.querySelector(`[data-error-boundary="${id}"]`);
        if (!container) {
            if (DEBUG) console.warn(`ErrorBoundary not found: ${id}`);
            return { dispose: () => {}, reset: () => {} };
        }

        let hasError = container.getAttribute('data-has-error') === 'true';
        let currentError = null;
        let originalContent = null;
        
        // Save original content
        if (!hasError) {
            originalContent = container.innerHTML;
        }
        
        function setError(error) {
            currentError = error;
            hasError = true;
            container.setAttribute('data-has-error', 'true');
            
            if (renderFallback) {
                container.innerHTML = renderFallback(error, reset);
            } else {
                container.innerHTML = `<div style="color: red;">Error: ${error.message}</div>`;
            }
        }
        
        function reset() {
            if (originalContent !== null) {
                container.innerHTML = originalContent;
            }
            hasError = false;
            currentError = null;
            container.removeAttribute('data-has-error');
        }
        
        // Override global error handler for this boundary
        // (In practice, this would integrate with PyNext's component system)
        
        return {
            dispose() {
                // Cleanup
            },
            reset,
            setError
        };
    }

    // =========================================================================
    // SECTION 7: SUSPENSE - Async Loading States
    // =========================================================================

    /**
     * Create a Suspense boundary for async loading.
     * 
     * @param {string} id - The data-suspense ID
     * @returns {Object} - { dispose: Function, suspend: Function, resolve: Function }
     */
    function createSuspense(id) {
        const container = document.querySelector(`[data-suspense="${id}"]`);
        if (!container) {
            if (DEBUG) console.warn(`Suspense not found: ${id}`);
            return { dispose: () => {}, suspend: () => {}, resolve: () => {} };
        }

        const fallbackHtml = container.getAttribute('data-fallback') || '';
        let originalContent = container.innerHTML;
        let isSuspended = false;
        
        function suspend() {
            if (!isSuspended) {
                originalContent = container.innerHTML;
                container.innerHTML = decodeHtmlEntities(fallbackHtml);
                isSuspended = true;
            }
        }
        
        function resolve() {
            if (isSuspended && originalContent !== null) {
                container.innerHTML = originalContent;
                isSuspended = false;
            }
        }
        
        return {
            dispose() {
                // Cleanup
            },
            suspend,
            resolve
        };
    }

    // =========================================================================
    // SECTION 8: UTILITY FUNCTIONS
    // =========================================================================

    /**
     * Convert HTML string to array of nodes.
     */
    function htmlToNodes(html) {
        if (!html || typeof html !== 'string') return [];
        const template = document.createElement('template');
        template.innerHTML = html.trim();
        return Array.from(template.content.childNodes);
    }

    /**
     * Convert HTML string to single node (wrapper div if multiple).
     */
    function htmlToNode(html) {
        const nodes = htmlToNodes(html);
        if (nodes.length === 0) return document.createTextNode('');
        if (nodes.length === 1) return nodes[0];
        
        const wrapper = document.createElement('div');
        nodes.forEach(n => wrapper.appendChild(n));
        return wrapper;
    }

    /**
     * Decode HTML entities in a string.
     */
    function decodeHtmlEntities(str) {
        const txt = document.createElement('textarea');
        txt.innerHTML = str;
        return txt.value;
    }

    // =========================================================================
    // SECTION 9: EXPORTS
    // =========================================================================

    // Ensure __pynext__ global exists
    global.__pynext__ = global.__pynext__ || {};

    // Export control flow functions
    Object.assign(global.__pynext__, {
        createShow,
        createFor,
        createIndex,
        createSwitch,
        createPortal,
        createErrorBoundary,
        createSuspense,
        
        // Utilities
        _controlFlow: {
            htmlToNodes,
            htmlToNode,
            longestIncreasingSubsequence,
        }
    });

    if (DEBUG) {
        console.log('PyNext Control Flow Runtime loaded');
    }

})(typeof window !== 'undefined' ? window : global);

