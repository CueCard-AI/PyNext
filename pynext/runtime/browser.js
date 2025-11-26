/**
 * PyNext Browser APIs Runtime
 * 
 * Provides client-side infrastructure for browser-specific APIs:
 * - Tab visibility tracking (Page Visibility API)
 * - Network status detection (Navigator.onLine)
 * 
 * Used by use_visibility() and use_online() in Python.
 */

(function() {
    'use strict';
    
    // Ensure __pynext__ namespace exists
    window.__pynext__ = window.__pynext__ || {};
    
    /**
     * Browser API Manager
     * 
     * Tracks browser state and syncs with PyNext signals.
     */
    window.__pynext__.browser = {
        // Signal IDs for browser state
        visibilitySignalId: null,
        onlineSignalId: null,
        
        // Listener cleanup functions
        _cleanups: [],
        
        /**
         * Initialize visibility tracking.
         * 
         * Listens for the 'visibilitychange' event and updates
         * the associated signal when the tab becomes visible/hidden.
         * 
         * @param {string} signalId - ID of the signal to update
         */
        initVisibility: function(signalId) {
            this.visibilitySignalId = signalId;
            
            // Get initial state
            const isVisible = !document.hidden;
            __pynext__.setSignal(signalId, isVisible);
            
            // Create handler
            const handler = () => {
                const visible = !document.hidden;
                __pynext__.setSignal(signalId, visible);
                
                console.debug(`[PyNext Browser] Visibility changed: ${visible}`);
                
                // Dispatch custom event
                document.dispatchEvent(new CustomEvent('pynext:visibility-change', {
                    detail: { visible }
                }));
            };
            
            // Listen for visibility changes
            document.addEventListener('visibilitychange', handler);
            
            // Store cleanup
            this._cleanups.push(() => {
                document.removeEventListener('visibilitychange', handler);
            });
            
            console.debug(`[PyNext Browser] Visibility tracking initialized`);
        },
        
        /**
         * Initialize online status tracking.
         * 
         * Listens for 'online' and 'offline' events and updates
         * the associated signal when connectivity changes.
         * 
         * @param {string} signalId - ID of the signal to update
         */
        initOnline: function(signalId) {
            this.onlineSignalId = signalId;
            
            // Get initial state from navigator
            const isOnline = navigator.onLine;
            __pynext__.setSignal(signalId, isOnline);
            
            // Create handlers
            const onlineHandler = () => {
                __pynext__.setSignal(signalId, true);
                console.debug('[PyNext Browser] Network: online');
                
                document.dispatchEvent(new CustomEvent('pynext:online-change', {
                    detail: { online: true }
                }));
            };
            
            const offlineHandler = () => {
                __pynext__.setSignal(signalId, false);
                console.debug('[PyNext Browser] Network: offline');
                
                document.dispatchEvent(new CustomEvent('pynext:online-change', {
                    detail: { online: false }
                }));
            };
            
            // Listen for network changes
            window.addEventListener('online', onlineHandler);
            window.addEventListener('offline', offlineHandler);
            
            // Store cleanup
            this._cleanups.push(() => {
                window.removeEventListener('online', onlineHandler);
                window.removeEventListener('offline', offlineHandler);
            });
            
            console.debug(`[PyNext Browser] Online tracking initialized`);
        },
        
        /**
         * Get current visibility state.
         * 
         * @returns {boolean} True if tab is visible
         */
        isVisible: function() {
            return !document.hidden;
        },
        
        /**
         * Get current online state.
         * 
         * @returns {boolean} True if browser is online
         */
        isOnline: function() {
            return navigator.onLine;
        },
        
        /**
         * Initialize browser APIs from hydration data.
         * 
         * @param {Object} data - Hydration data containing visibility and online configs
         */
        hydrate: function(data) {
            if (data.visibility) {
                this.initVisibility(data.visibility.id);
            }
            
            if (data.online) {
                this.initOnline(data.online.id);
            }
        },
        
        /**
         * Cleanup all listeners.
         */
        cleanup: function() {
            this._cleanups.forEach(fn => fn());
            this._cleanups = [];
            this.visibilitySignalId = null;
            this.onlineSignalId = null;
        }
    };
    
    // Cleanup on page unload
    window.addEventListener('beforeunload', () => {
        window.__pynext__.browser.cleanup();
    });
    
})();

