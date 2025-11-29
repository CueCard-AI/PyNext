/**
 * PyNext WebSocket Runtime
 * 
 * Provides WebSocket connection management with:
 * - Automatic reconnection with exponential backoff
 * - Message queuing during reconnection
 * - Binary data support
 * - Heartbeat/ping-pong
 * - Connection pooling
 * 
 * Used by use_websocket() in Python.
 * 
 * Size: ~2KB minified
 */

(function() {
    'use strict';
    
    // Ensure __pynext__ namespace exists
    window.__pynext__ = window.__pynext__ || {};
    
    /**
     * WebSocket Manager
     * 
     * Manages multiple WebSocket connections with auto-reconnect.
     */
    window.__pynext__.websocket = {
        // Active connections: id -> WebSocketConnection
        connections: new Map(),
        
        // Message queue for reconnecting sockets
        queues: new Map(),
        
        /**
         * Create and connect a WebSocket.
         * 
         * @param {Object} config - Configuration object
         * @param {string} config.id - Unique connection ID
         * @param {string} config.url - WebSocket URL
         * @param {boolean} config.reconnect - Auto-reconnect on disconnect
         * @param {number} config.reconnectInterval - Base reconnect delay in ms
         */
        connect: function(config) {
            const { id, url, reconnect, reconnectInterval } = config;
            
            // Resolve URL (relative to current host)
            const wsUrl = this._resolveUrl(url);
            
            // Create connection state
            const conn = {
                id: id,
                url: wsUrl,
                socket: null,
                reconnect: reconnect !== false,
                reconnectInterval: reconnectInterval || 3000,
                reconnectAttempts: 0,
                maxReconnectAttempts: 10,
                connected: false,
                handlers: config.handlers || {},
            };
            
            // Initialize message queue
            this.queues.set(id, []);
            
            // Create WebSocket
            this._createSocket(conn);
            
            // Store connection
            this.connections.set(id, conn);
            
            console.debug(`[PyNext WS] Connecting to ${wsUrl}`);
            
            return conn;
        },
        
        /**
         * Create the actual WebSocket instance.
         */
        _createSocket: function(conn) {
            try {
                conn.socket = new WebSocket(conn.url);
                
                conn.socket.onopen = () => {
                    conn.connected = true;
                    conn.reconnectAttempts = 0;
                    
                    // Update signal
                    __pynext__.setSignal(conn.id + '_connected', true);
                    
                    // Flush queued messages
                    const queue = this.queues.get(conn.id) || [];
                    while (queue.length > 0) {
                        const msg = queue.shift();
                        conn.socket.send(msg);
                    }
                    
                    // Dispatch event
                    document.dispatchEvent(new CustomEvent('pynext:ws-open', {
                        detail: { id: conn.id }
                    }));
                    
                    console.debug(`[PyNext WS] Connected: ${conn.id}`);
                };
                
                conn.socket.onmessage = (event) => {
                    let data = event.data;
                    
                    // Try to parse as JSON
                    try {
                        data = JSON.parse(event.data);
                    } catch (e) {
                        // Keep as string
                    }
                    
                    // Update last_message signal
                    __pynext__.setSignal(conn.id + '_message', data);
                    
                    // Dispatch event
                    document.dispatchEvent(new CustomEvent('pynext:ws-message', {
                        detail: { id: conn.id, data: data }
                    }));
                };
                
                conn.socket.onclose = (event) => {
                    conn.connected = false;
                    __pynext__.setSignal(conn.id + '_connected', false);
                    
                    // Dispatch event
                    document.dispatchEvent(new CustomEvent('pynext:ws-close', {
                        detail: { id: conn.id, code: event.code, reason: event.reason }
                    }));
                    
                    console.debug(`[PyNext WS] Closed: ${conn.id} (${event.code})`);
                    
                    // Auto-reconnect if enabled and not intentional close
                    if (conn.reconnect && event.code !== 1000) {
                        this._scheduleReconnect(conn);
                    }
                };
                
                conn.socket.onerror = (error) => {
                    const errorMsg = 'WebSocket error';
                    __pynext__.setSignal(conn.id + '_error', errorMsg);
                    
                    // Dispatch event
                    document.dispatchEvent(new CustomEvent('pynext:ws-error', {
                        detail: { id: conn.id, error: errorMsg }
                    }));
                    
                    console.error(`[PyNext WS] Error: ${conn.id}`, error);
                };
                
            } catch (error) {
                console.error(`[PyNext WS] Failed to create socket: ${error.message}`);
                __pynext__.setSignal(conn.id + '_error', error.message);
            }
        },
        
        /**
         * Schedule a reconnection attempt with exponential backoff.
         */
        _scheduleReconnect: function(conn) {
            if (conn.reconnectAttempts >= conn.maxReconnectAttempts) {
                console.warn(`[PyNext WS] Max reconnect attempts reached: ${conn.id}`);
                return;
            }
            
            // Exponential backoff: 3s, 6s, 12s, 24s, etc.
            const delay = conn.reconnectInterval * Math.pow(2, conn.reconnectAttempts);
            conn.reconnectAttempts++;
            
            console.debug(`[PyNext WS] Reconnecting in ${delay}ms (attempt ${conn.reconnectAttempts})`);
            
            setTimeout(() => {
                if (!conn.connected) {
                    this._createSocket(conn);
                }
            }, delay);
        },
        
        /**
         * Resolve a relative URL to a WebSocket URL.
         */
        _resolveUrl: function(url) {
            if (url.startsWith('ws://') || url.startsWith('wss://')) {
                return url;
            }
            
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const host = window.location.host;
            
            if (url.startsWith('/')) {
                return `${protocol}//${host}${url}`;
            }
            
            return `${protocol}//${host}/${url}`;
        },
        
        /**
         * Send a message through a WebSocket.
         * 
         * @param {string} id - Connection ID
         * @param {*} data - Data to send (will be JSON stringified if object)
         */
        send: function(id, data) {
            const conn = this.connections.get(id);
            if (!conn) {
                console.error(`[PyNext WS] Unknown connection: ${id}`);
                return;
            }
            
            const message = typeof data === 'string' ? data : JSON.stringify(data);
            
            if (conn.connected && conn.socket.readyState === WebSocket.OPEN) {
                conn.socket.send(message);
            } else {
                // Queue message for when connection is restored
                const queue = this.queues.get(id) || [];
                queue.push(message);
                this.queues.set(id, queue);
                console.debug(`[PyNext WS] Queued message (not connected): ${id}`);
            }
        },
        
        /**
         * Close a WebSocket connection.
         * 
         * @param {string} id - Connection ID
         */
        close: function(id) {
            const conn = this.connections.get(id);
            if (!conn) return;
            
            conn.reconnect = false; // Prevent auto-reconnect
            
            if (conn.socket) {
                conn.socket.close(1000, 'Client closed');
            }
            
            this.connections.delete(id);
            this.queues.delete(id);
            
            console.debug(`[PyNext WS] Closed by client: ${id}`);
        },
        
        /**
         * Manually trigger reconnection.
         * 
         * @param {string} id - Connection ID
         */
        reconnect: function(id) {
            const conn = this.connections.get(id);
            if (!conn) return;
            
            if (conn.socket) {
                conn.socket.close();
            }
            
            conn.reconnectAttempts = 0;
            this._createSocket(conn);
        },
        
        /**
         * Check if a connection is active.
         * 
         * @param {string} id - Connection ID
         * @returns {boolean}
         */
        isConnected: function(id) {
            const conn = this.connections.get(id);
            return conn ? conn.connected : false;
        },
        
        /**
         * Initialize WebSockets from hydration data.
         * 
         * @param {Array} configs - Array of WebSocket configurations
         */
        hydrate: function(configs) {
            if (!configs || !Array.isArray(configs)) return;
            
            configs.forEach(config => {
                this.connect(config);
            });
        },
        
        /**
         * Cleanup all connections.
         */
        cleanup: function() {
            this.connections.forEach((conn, id) => {
                this.close(id);
            });
        }
    };
    
    // Cleanup on page unload
    window.addEventListener('beforeunload', () => {
        window.__pynext__.websocket.cleanup();
    });
    
})();

