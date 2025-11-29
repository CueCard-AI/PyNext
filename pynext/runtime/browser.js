/**
 * PyNext Browser APIs Runtime
 * 
 * Provides client-side infrastructure for browser-specific APIs:
 * - Tab visibility tracking (Page Visibility API)
 * - Network status detection (Navigator.onLine)
 * - Media queries (matchMedia)
 * - Geolocation (navigator.geolocation)
 * - Clipboard (navigator.clipboard)
 * - Window size (resize events)
 * - Scroll position (scroll events)
 * - Intersection Observer (viewport visibility)
 * 
 * Used by use_visibility(), use_online(), use_media_query(), etc. in Python.
 * 
 * Size: ~3KB minified
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
        
        // Media query listeners
        mediaQueries: new Map(),
        
        // Geolocation watch ID
        geolocationWatchId: null,
        
        // Intersection observers
        intersectionObservers: new Map(),
        
        // RAF IDs for throttling
        _scrollRAF: null,
        _resizeRAF: null,
        
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
         * Initialize media query tracking.
         * 
         * Uses matchMedia to track CSS media query state.
         * 
         * @param {string} signalId - ID of the signal to update
         * @param {string} query - CSS media query string
         */
        initMediaQuery: function(signalId, query) {
            const mql = window.matchMedia(query);
            
            // Set initial state
            __pynext__.setSignal(signalId, mql.matches);
            
            // Create handler
            const handler = (e) => {
                __pynext__.setSignal(signalId, e.matches);
                
                console.debug(`[PyNext Browser] Media query "${query}": ${e.matches}`);
                
                document.dispatchEvent(new CustomEvent('pynext:media-query-change', {
                    detail: { id: signalId, query, matches: e.matches }
                }));
            };
            
            // Listen for changes
            mql.addEventListener('change', handler);
            
            // Store for cleanup
            this.mediaQueries.set(signalId, { mql, handler });
            
            this._cleanups.push(() => {
                mql.removeEventListener('change', handler);
                this.mediaQueries.delete(signalId);
            });
            
            console.debug(`[PyNext Browser] Media query initialized: "${query}"`);
        },
        
        /**
         * Initialize geolocation tracking.
         * 
         * @param {Object} config - Geolocation configuration
         */
        initGeolocation: function(config) {
            const { id, watch, options } = config;
            
            // Set loading state
            __pynext__.setSignal(id + '_loading', true);
            __pynext__.setSignal(id + '_error', null);
            
            // Success callback
            const success = (position) => {
                __pynext__.setSignal(id + '_loading', false);
                __pynext__.setSignal(id + '_latitude', position.coords.latitude);
                __pynext__.setSignal(id + '_longitude', position.coords.longitude);
                __pynext__.setSignal(id + '_accuracy', position.coords.accuracy);
                __pynext__.setSignal(id + '_altitude', position.coords.altitude);
                __pynext__.setSignal(id + '_heading', position.coords.heading);
                __pynext__.setSignal(id + '_speed', position.coords.speed);
                __pynext__.setSignal(id + '_permission', 'granted');
                
                console.debug(`[PyNext Browser] Geolocation: ${position.coords.latitude}, ${position.coords.longitude}`);
                
                document.dispatchEvent(new CustomEvent('pynext:geolocation-update', {
                    detail: { id, coords: position.coords }
                }));
            };
            
            // Error callback
            const error = (err) => {
                __pynext__.setSignal(id + '_loading', false);
                __pynext__.setSignal(id + '_error', err.message);
                
                if (err.code === 1) {
                    __pynext__.setSignal(id + '_permission', 'denied');
                }
                
                console.warn(`[PyNext Browser] Geolocation error: ${err.message}`);
                
                document.dispatchEvent(new CustomEvent('pynext:geolocation-error', {
                    detail: { id, error: err.message, code: err.code }
                }));
            };
            
            // Start tracking
            if (watch) {
                this.geolocationWatchId = navigator.geolocation.watchPosition(success, error, options);
                
                this._cleanups.push(() => {
                    if (this.geolocationWatchId !== null) {
                        navigator.geolocation.clearWatch(this.geolocationWatchId);
                        this.geolocationWatchId = null;
                    }
                });
            } else {
                navigator.geolocation.getCurrentPosition(success, error, options);
            }
            
            console.debug(`[PyNext Browser] Geolocation initialized (watch: ${watch})`);
        },
        
        /**
         * Refresh geolocation.
         * 
         * @param {string} id - Signal ID
         */
        refreshGeolocation: function(id) {
            __pynext__.setSignal(id + '_loading', true);
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    __pynext__.setSignal(id + '_loading', false);
                    __pynext__.setSignal(id + '_latitude', position.coords.latitude);
                    __pynext__.setSignal(id + '_longitude', position.coords.longitude);
                },
                (err) => {
                    __pynext__.setSignal(id + '_loading', false);
                    __pynext__.setSignal(id + '_error', err.message);
                }
            );
        },
        
        /**
         * Stop watching geolocation.
         * 
         * @param {string} id - Signal ID
         */
        stopGeolocation: function(id) {
            if (this.geolocationWatchId !== null) {
                navigator.geolocation.clearWatch(this.geolocationWatchId);
                this.geolocationWatchId = null;
                console.debug(`[PyNext Browser] Geolocation stopped`);
            }
        },
        
        /**
         * Initialize clipboard tracking.
         * 
         * @param {string} signalId - Signal ID
         */
        initClipboard: function(signalId) {
            // Check if clipboard API is supported
            const supported = !!navigator.clipboard;
            __pynext__.setSignal(signalId + '_supported', supported);
            __pynext__.setSignal(signalId + '_copied', false);
            __pynext__.setSignal(signalId + '_text', null);
            
            console.debug(`[PyNext Browser] Clipboard initialized (supported: ${supported})`);
        },
        
        /**
         * Copy text to clipboard.
         * 
         * @param {string} signalId - Signal ID
         * @param {string} text - Text to copy
         */
        clipboardCopy: function(signalId, text) {
            navigator.clipboard.writeText(text).then(() => {
                __pynext__.setSignal(signalId + '_copied', true);
                
                // Reset copied flag after 2 seconds
                setTimeout(() => {
                    __pynext__.setSignal(signalId + '_copied', false);
                }, 2000);
                
                console.debug(`[PyNext Browser] Copied to clipboard`);
                
                document.dispatchEvent(new CustomEvent('pynext:clipboard-copy', {
                    detail: { id: signalId, text }
                }));
            }).catch(err => {
                console.error(`[PyNext Browser] Clipboard copy failed: ${err.message}`);
            });
        },
        
        /**
         * Read text from clipboard.
         * 
         * @param {string} signalId - Signal ID
         */
        clipboardRead: function(signalId) {
            navigator.clipboard.readText().then((text) => {
                __pynext__.setSignal(signalId + '_text', text);
                
                console.debug(`[PyNext Browser] Read from clipboard`);
                
                document.dispatchEvent(new CustomEvent('pynext:clipboard-read', {
                    detail: { id: signalId, text }
                }));
            }).catch(err => {
                console.error(`[PyNext Browser] Clipboard read failed: ${err.message}`);
            });
        },
        
        /**
         * Initialize window size tracking.
         * 
         * Uses requestAnimationFrame for throttling.
         * 
         * @param {string} signalId - Signal ID
         */
        initWindowSize: function(signalId) {
            // Set initial values
            __pynext__.setSignal(signalId + '_width', window.innerWidth);
            __pynext__.setSignal(signalId + '_height', window.innerHeight);
            
            // Create handler with RAF throttling
            const handler = () => {
                if (this._resizeRAF) return;
                
                this._resizeRAF = requestAnimationFrame(() => {
                    __pynext__.setSignal(signalId + '_width', window.innerWidth);
                    __pynext__.setSignal(signalId + '_height', window.innerHeight);
                    
                    document.dispatchEvent(new CustomEvent('pynext:window-resize', {
                        detail: { width: window.innerWidth, height: window.innerHeight }
                    }));
                    
                    this._resizeRAF = null;
                });
            };
            
            window.addEventListener('resize', handler);
            
            this._cleanups.push(() => {
                window.removeEventListener('resize', handler);
                if (this._resizeRAF) {
                    cancelAnimationFrame(this._resizeRAF);
                    this._resizeRAF = null;
                }
            });
            
            console.debug(`[PyNext Browser] Window size tracking initialized`);
        },
        
        /**
         * Initialize scroll position tracking.
         * 
         * Uses requestAnimationFrame for throttling (60fps max).
         * 
         * @param {string} signalId - Signal ID
         */
        initScrollPosition: function(signalId) {
            // Calculate initial values
            const updateScroll = () => {
                const x = window.scrollX || window.pageXOffset;
                const y = window.scrollY || window.pageYOffset;
                
                // Calculate progress (0.0 to 1.0)
                const docHeight = document.documentElement.scrollHeight - window.innerHeight;
                const progress = docHeight > 0 ? Math.min(y / docHeight, 1) : 0;
                
                __pynext__.setSignal(signalId + '_x', x);
                __pynext__.setSignal(signalId + '_y', y);
                __pynext__.setSignal(signalId + '_progress', progress);
            };
            
            // Set initial values
            updateScroll();
            
            // Create handler with RAF throttling
            const handler = () => {
                if (this._scrollRAF) return;
                
                this._scrollRAF = requestAnimationFrame(() => {
                    updateScroll();
                    
                    document.dispatchEvent(new CustomEvent('pynext:scroll', {
                        detail: { 
                            x: window.scrollX, 
                            y: window.scrollY,
                            progress: __pynext__.getSignal(signalId + '_progress')
                        }
                    }));
                    
                    this._scrollRAF = null;
                });
            };
            
            window.addEventListener('scroll', handler, { passive: true });
            
            this._cleanups.push(() => {
                window.removeEventListener('scroll', handler);
                if (this._scrollRAF) {
                    cancelAnimationFrame(this._scrollRAF);
                    this._scrollRAF = null;
                }
            });
            
            console.debug(`[PyNext Browser] Scroll position tracking initialized`);
        },
        
        /**
         * Initialize intersection observer.
         * 
         * @param {Object} config - Intersection config
         */
        initIntersection: function(config) {
            const { id, elementId, options } = config;
            
            // Set initial state
            __pynext__.setSignal(id, false);
            __pynext__.setSignal(id + '_ratio', 0);
            
            // Wait for DOM
            const setup = () => {
                const element = document.getElementById(elementId);
                if (!element) {
                    console.warn(`[PyNext Browser] Element not found: ${elementId}`);
                    return;
                }
                
                const observer = new IntersectionObserver((entries) => {
                    entries.forEach(entry => {
                        __pynext__.setSignal(id, entry.isIntersecting);
                        __pynext__.setSignal(id + '_ratio', entry.intersectionRatio);
                        
                        document.dispatchEvent(new CustomEvent('pynext:intersection', {
                            detail: { 
                                id, 
                                elementId, 
                                isIntersecting: entry.isIntersecting,
                                ratio: entry.intersectionRatio
                            }
                        }));
                    });
                }, {
                    threshold: options?.threshold || 0,
                    rootMargin: options?.rootMargin || '0px',
                });
                
                observer.observe(element);
                
                // Store for cleanup
                this.intersectionObservers.set(id, observer);
                
                this._cleanups.push(() => {
                    observer.disconnect();
                    this.intersectionObservers.delete(id);
                });
                
                console.debug(`[PyNext Browser] Intersection observer initialized: ${elementId}`);
            };
            
            // Setup after DOM ready
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', setup);
            } else {
                // Small delay to ensure element exists
                setTimeout(setup, 0);
            }
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
         * @param {Object} data - Hydration data
         */
        hydrate: function(data) {
            if (data.visibility) {
                this.initVisibility(data.visibility.id);
            }
            
            if (data.online) {
                this.initOnline(data.online.id);
            }
            
            if (data.mediaQueries) {
                data.mediaQueries.forEach(mq => {
                    this.initMediaQuery(mq.id, mq.query);
                });
            }
            
            if (data.geolocation) {
                this.initGeolocation(data.geolocation);
            }
            
            if (data.clipboard) {
                this.initClipboard(data.clipboard.id);
            }
            
            if (data.windowSize) {
                this.initWindowSize(data.windowSize.id);
            }
            
            if (data.scrollPosition) {
                this.initScrollPosition(data.scrollPosition.id);
            }
            
            if (data.intersections) {
                data.intersections.forEach(int => {
                    this.initIntersection(int);
                });
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
            this.mediaQueries.clear();
            this.intersectionObservers.clear();
        }
    };
    
    // Cleanup on page unload
    window.addEventListener('beforeunload', () => {
        window.__pynext__.browser.cleanup();
    });
    
})();

