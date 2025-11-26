/**
 * PyNext SSE (Server-Sent Events) Runtime
 * 
 * Provides the client-side infrastructure for SSE connections.
 * Used by use_event_source() in Python.
 */

(function() {
    'use strict';
    
    // Ensure __pynext__ namespace exists
    window.__pynext__ = window.__pynext__ || {};
    
    /**
     * SSE Connection Manager
     * 
     * Manages multiple SSE connections with automatic reconnection,
     * event handling, and connection state tracking.
     */
    window.__pynext__.sse = {
        // Active connections: { id: EventSource }
        connections: {},
        
        // Connection configs: { id: config }
        configs: {},
        
        // Connection states: { id: 'connecting' | 'open' | 'closed' }
        states: {},
        
        /**
         * Connect to an SSE endpoint.
         * 
         * @param {Object} config - Connection configuration
         * @param {string} config.id - Unique connection ID
         * @param {string} config.url - SSE endpoint URL
         * @param {Object} config.handlers - Event name -> handler function mapping
         * @param {Object} config.options - Connection options
         */
        connect: function(config) {
            const { id, url, handlers, options } = config;
            
            // Store config for reconnection
            this.configs[id] = config;
            this.states[id] = 'connecting';
            
            // Create EventSource connection
            const es = new EventSource(url);
            this.connections[id] = es;
            
            // Handle connection open
            es.onopen = () => {
                this.states[id] = 'open';
                console.debug(`[PyNext SSE] Connected to ${url}`);
                
                // Dispatch custom event
                document.dispatchEvent(new CustomEvent('pynext:sse-open', {
                    detail: { id, url }
                }));
            };
            
            // Handle errors (includes disconnection)
            es.onerror = (error) => {
                console.warn(`[PyNext SSE] Error on ${url}:`, error);
                
                const wasOpen = this.states[id] === 'open';
                this.states[id] = 'closed';
                
                // Close the current connection
                es.close();
                delete this.connections[id];
                
                // Dispatch error event
                document.dispatchEvent(new CustomEvent('pynext:sse-error', {
                    detail: { id, url, wasOpen }
                }));
                
                // Attempt reconnection if enabled
                if (options.reconnect !== false) {
                    const delay = options.reconnectDelay || 1000;
                    console.debug(`[PyNext SSE] Reconnecting in ${delay}ms...`);
                    
                    setTimeout(() => {
                        // Only reconnect if not manually closed
                        if (this.configs[id]) {
                            this.connect(config);
                        }
                    }, delay);
                }
            };
            
            // Register event handlers
            Object.entries(handlers).forEach(([eventName, handler]) => {
                es.addEventListener(eventName, (event) => {
                    try {
                        // Parse JSON data
                        const data = JSON.parse(event.data);
                        
                        // Execute handler
                        if (typeof handler === 'function') {
                            handler(data);
                        } else if (typeof handler === 'string') {
                            // Handler is a JS string to evaluate
                            const fn = new Function('data', handler);
                            fn(data);
                        }
                    } catch (error) {
                        console.error(`[PyNext SSE] Handler error for ${eventName}:`, error);
                    }
                });
            });
            
            // Also listen for generic 'message' events
            es.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    
                    // Dispatch to 'message' handler if defined
                    if (handlers.message) {
                        if (typeof handlers.message === 'function') {
                            handlers.message(data);
                        }
                    }
                } catch (error) {
                    // Data might not be JSON
                    console.debug('[PyNext SSE] Non-JSON message:', event.data);
                }
            };
            
            return id;
        },
        
        /**
         * Close an SSE connection.
         * 
         * @param {string} id - Connection ID
         */
        close: function(id) {
            const es = this.connections[id];
            
            if (es) {
                es.close();
                delete this.connections[id];
                delete this.configs[id];  // Prevent reconnection
                this.states[id] = 'closed';
                
                console.debug(`[PyNext SSE] Closed connection ${id}`);
                
                document.dispatchEvent(new CustomEvent('pynext:sse-close', {
                    detail: { id }
                }));
            }
        },
        
        /**
         * Manually reconnect to an SSE endpoint.
         * 
         * @param {string} id - Connection ID
         */
        reconnect: function(id) {
            const config = this.configs[id];
            
            if (config) {
                // Close existing connection if any
                this.close(id);
                
                // Restore config (close removes it)
                this.configs[id] = config;
                
                // Reconnect
                this.connect(config);
            } else {
                console.warn(`[PyNext SSE] No config found for ${id}`);
            }
        },
        
        /**
         * Check if a connection is active.
         * 
         * @param {string} id - Connection ID
         * @returns {boolean}
         */
        isConnected: function(id) {
            return this.states[id] === 'open';
        },
        
        /**
         * Get connection state.
         * 
         * @param {string} id - Connection ID
         * @returns {'connecting' | 'open' | 'closed' | undefined}
         */
        getState: function(id) {
            return this.states[id];
        },
        
        /**
         * Close all connections.
         */
        closeAll: function() {
            Object.keys(this.connections).forEach(id => {
                this.close(id);
            });
        },
        
        /**
         * Initialize SSE connections from hydration data.
         * 
         * @param {Array} connections - Array of connection configs
         */
        hydrate: function(connections) {
            if (!connections || !Array.isArray(connections)) return;
            
            connections.forEach(config => {
                this.connect(config);
            });
        }
    };
    
    // Close all connections when page unloads
    window.addEventListener('beforeunload', () => {
        window.__pynext__.sse.closeAll();
    });
    
})();

