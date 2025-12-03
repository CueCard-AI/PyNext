/**
 * PyNext Live Queries - Client Runtime
 * 
 * Handles client-side live query subscriptions:
 * - Automatic transport selection (SSE/WebSocket)
 * - Reconnection with exponential backoff
 * - State synchronization
 * - Optimistic updates
 * 
 * Used by Model.live() in Python.
 * 
 * Size: ~3KB minified
 */

(function() {
    'use strict';
    
    // Ensure __pynext__ namespace exists
    window.__pynext__ = window.__pynext__ || {};
    
    /**
     * Live Query Manager
     * 
     * Manages live query subscriptions on the client.
     */
    window.__pynext__.live = {
        // Active subscriptions: query_id -> Subscription
        subscriptions: new Map(),
        
        // Transport connection
        transport: null,
        transportType: null,
        
        // Connection state
        connected: false,
        connecting: false,
        reconnectAttempts: 0,
        maxReconnectAttempts: 10,
        
        // Configuration
        config: {
            sseEndpoint: '/_pynext/live/sse',
            wsEndpoint: '/_pynext/live/ws',
            reconnectDelay: 1000,
            batchDelay: 50,
        },
        
        /**
         * Initialize live queries from hydration data.
         * 
         * Called automatically on page load.
         * 
         * @param {Array} queries - Array of query configurations
         */
        hydrate: function(queries) {
            if (!queries || !Array.isArray(queries)) return;
            
            queries.forEach(query => {
                this.subscribe(query);
            });
        },
        
        /**
         * Subscribe to a live query.
         * 
         * @param {Object} config - Query configuration
         * @param {string} config.id - Unique query ID
         * @param {string} config.table - Table name
         * @param {Array} config.data - Initial data
         * @param {string} config.transport - Preferred transport (auto/sse/websocket)
         * @returns {Object} Subscription handle
         */
        subscribe: function(config) {
            const { id, table, data, transport } = config;
            
            // Create subscription
            const subscription = {
                id: id,
                table: table,
                data: data || [],
                dataById: this._buildIndex(data || []),
                loading: false,
                error: null,
                callbacks: [],
            };
            
            this.subscriptions.set(id, subscription);
            
            // Ensure connected
            this._ensureConnected(transport || 'auto');
            
            // Send subscribe message
            this._sendSubscribe(id, config);
            
            console.debug(`[PyNext Live] Subscribed: ${id} (${table})`);
            
            return {
                // Get current data
                get: () => subscription.data,
                
                // Check loading state
                isLoading: () => subscription.loading,
                
                // Get error if any
                getError: () => subscription.error,
                
                // Add callback for updates
                onUpdate: (callback) => {
                    subscription.callbacks.push(callback);
                    return () => {
                        const idx = subscription.callbacks.indexOf(callback);
                        if (idx >= 0) subscription.callbacks.splice(idx, 1);
                    };
                },
                
                // Manual refresh
                refresh: () => this._requestRefresh(id),
                
                // Unsubscribe
                unsubscribe: () => this.unsubscribe(id),
            };
        },
        
        /**
         * Unsubscribe from a live query.
         * 
         * @param {string} queryId - Query ID
         */
        unsubscribe: function(queryId) {
            if (!this.subscriptions.has(queryId)) return;
            
            // Send unsubscribe message
            this._sendUnsubscribe(queryId);
            
            // Remove subscription
            this.subscriptions.delete(queryId);
            
            console.debug(`[PyNext Live] Unsubscribed: ${queryId}`);
        },
        
        /**
         * Ensure transport connection is established.
         */
        _ensureConnected: function(preferredTransport) {
            if (this.connected || this.connecting) return;
            
            this.connecting = true;
            
            // Select transport
            const transport = this._selectTransport(preferredTransport);
            this.transportType = transport;
            
            if (transport === 'websocket') {
                this._connectWebSocket();
            } else {
                this._connectSSE();
            }
        },
        
        /**
         * Select the best transport.
         * 
         * Auto-selection strategy:
         * 1. If preferred is explicit, use it
         * 2. If Phase 5 websocket.js has existing connections, reuse WebSocket
         * 3. Default to SSE for simplicity (unidirectional, simpler)
         */
        _selectTransport: function(preferred) {
            if (preferred === 'websocket') return 'websocket';
            if (preferred === 'sse') return 'sse';
            
            // Auto-select: prefer existing WebSocket connection from Phase 5
            // This enables connection reuse and reduces overhead
            if (window.__pynext__.websocket && 
                window.__pynext__.websocket.connections.size > 0) {
                console.debug('[PyNext Live] Reusing existing WebSocket connection');
                return 'websocket';
            }
            
            // Default to SSE for simplicity (unidirectional, widely supported)
            return 'sse';
        },
        
        /**
         * Connect via Server-Sent Events.
         */
        _connectSSE: function() {
            const url = this.config.sseEndpoint;
            
            console.debug(`[PyNext Live] Connecting via SSE: ${url}`);
            
            const eventSource = new EventSource(url);
            this.transport = eventSource;
            
            eventSource.onopen = () => {
                this.connected = true;
                this.connecting = false;
                this.reconnectAttempts = 0;
                console.debug('[PyNext Live] SSE connected');
            };
            
            eventSource.onerror = (error) => {
                console.warn('[PyNext Live] SSE error:', error);
                this.connected = false;
                this.connecting = false;
                
                // Attempt reconnection
                if (this.subscriptions.size > 0) {
                    this._scheduleReconnect();
                }
            };
            
            // Handle different event types
            eventSource.addEventListener('data', (event) => {
                this._handleMessage(JSON.parse(event.data));
            });
            
            eventSource.addEventListener('sync', (event) => {
                this._handleSync(JSON.parse(event.data));
            });
            
            eventSource.addEventListener('error', (event) => {
                const data = JSON.parse(event.data);
                this._handleError(data);
            });
        },
        
        /**
         * Connect via WebSocket.
         * 
         * INTEGRATION: Uses the existing __pynext__.websocket infrastructure
         * from Phase 5 (use_websocket hook) when available, otherwise falls
         * back to a direct WebSocket connection.
         */
        _connectWebSocket: function() {
            const wsUrl = this.config.wsEndpoint;
            const connectionId = 'live_query_ws';
            
            console.debug(`[PyNext Live] Connecting via WebSocket: ${wsUrl}`);
            
            // Check if we can use the existing websocket.js infrastructure
            if (window.__pynext__.websocket) {
                // Use existing Phase 5 WebSocket infrastructure
                console.debug('[PyNext Live] Using existing websocket.js infrastructure');
                
                const ws = window.__pynext__.websocket;
                
                // Connect using existing infrastructure
                ws.connect({
                    id: connectionId,
                    url: wsUrl,
                    reconnect: true,
                    reconnectInterval: this.config.reconnectDelay,
                });
                
                // Store reference
                this.transport = ws.connections.get(connectionId);
                this._wsConnectionId = connectionId;
                
                // Listen for connection events via signals
                const checkConnected = () => {
                    if (ws.isConnected(connectionId)) {
                        this.connected = true;
                        this.connecting = false;
                        this.reconnectAttempts = 0;
                        console.debug('[PyNext Live] WebSocket connected (via websocket.js)');
                        
                        // Re-subscribe to all queries
                        this.subscriptions.forEach((sub, id) => {
                            this._sendSubscribe(id, { table: sub.table });
                        });
                    }
                };
                
                // Check immediately and on interval until connected
                checkConnected();
                const connectCheck = setInterval(() => {
                    if (ws.isConnected(connectionId)) {
                        clearInterval(connectCheck);
                        checkConnected();
                    }
                }, 100);
                
                // Listen for messages via custom event
                document.addEventListener('pynext:ws-message', (event) => {
                    if (event.detail.id === connectionId) {
                        this._handleMessage(event.detail.data);
                    }
                });
                
                // Listen for close events
                document.addEventListener('pynext:ws-close', (event) => {
                    if (event.detail.id === connectionId) {
                        console.debug(`[PyNext Live] WebSocket closed: ${event.detail.code}`);
                        this.connected = false;
                        this.connecting = false;
                    }
                });
                
                return;
            }
            
            // Fallback: Direct WebSocket connection
            console.debug('[PyNext Live] Using direct WebSocket connection');
            
            const fullUrl = this._resolveWSUrl(wsUrl);
            const socket = new WebSocket(fullUrl);
            this.transport = socket;
            
            socket.onopen = () => {
                this.connected = true;
                this.connecting = false;
                this.reconnectAttempts = 0;
                console.debug('[PyNext Live] WebSocket connected');
                
                // Re-subscribe to all queries
                this.subscriptions.forEach((sub, id) => {
                    this._sendSubscribe(id, { table: sub.table });
                });
            };
            
            socket.onclose = (event) => {
                console.debug(`[PyNext Live] WebSocket closed: ${event.code}`);
                this.connected = false;
                this.connecting = false;
                
                if (event.code !== 1000 && this.subscriptions.size > 0) {
                    this._scheduleReconnect();
                }
            };
            
            socket.onerror = (error) => {
                console.warn('[PyNext Live] WebSocket error:', error);
            };
            
            socket.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    this._handleMessage(message);
                } catch (e) {
                    console.error('[PyNext Live] Invalid message:', e);
                }
            };
        },
        
        /**
         * Handle incoming message.
         */
        _handleMessage: function(message) {
            const { type, query_id, data } = message;
            
            if (type === 'data') {
                this._applyChange(query_id, data);
            } else if (type === 'sync') {
                this._handleSync(message);
            } else if (type === 'error') {
                this._handleError(message);
            } else if (type === 'pong') {
                // Heartbeat response, ignore
            }
        },
        
        /**
         * Apply a change to a subscription.
         */
        _applyChange: function(queryId, change) {
            const subscription = this.subscriptions.get(queryId);
            if (!subscription) return;
            
            const { type, row_id, old_data, new_data } = change;
            
            let changed = false;
            
            if (type === 'INSERT' && new_data) {
                // Add new row
                if (!subscription.dataById[new_data.id]) {
                    subscription.data.push(new_data);
                    subscription.dataById[new_data.id] = new_data;
                    changed = true;
                }
            } else if (type === 'UPDATE' && new_data) {
                // Update existing row
                const idx = subscription.data.findIndex(r => r.id === row_id);
                if (idx >= 0) {
                    subscription.data[idx] = new_data;
                    subscription.dataById[row_id] = new_data;
                    changed = true;
                }
            } else if (type === 'DELETE') {
                // Remove row
                const idx = subscription.data.findIndex(r => r.id === row_id);
                if (idx >= 0) {
                    subscription.data.splice(idx, 1);
                    delete subscription.dataById[row_id];
                    changed = true;
                }
            }
            
            if (changed) {
                // Update signal if exists
                if (window.__pynext__.setSignal) {
                    window.__pynext__.setSignal(queryId, subscription.data);
                }
                
                // Notify callbacks
                subscription.callbacks.forEach(cb => {
                    try { cb(subscription.data, change); } catch (e) {}
                });
            }
        },
        
        /**
         * Handle full sync message.
         */
        _handleSync: function(message) {
            const { query_id, data } = message;
            
            const subscription = this.subscriptions.get(query_id);
            if (!subscription) return;
            
            const rows = data.rows || [];
            subscription.data = rows;
            subscription.dataById = this._buildIndex(rows);
            subscription.loading = false;
            
            // Update signal
            if (window.__pynext__.setSignal) {
                window.__pynext__.setSignal(query_id, rows);
                window.__pynext__.setSignal(query_id + '_loading', false);
            }
            
            // Notify callbacks
            subscription.callbacks.forEach(cb => {
                try { cb(rows, { type: 'sync' }); } catch (e) {}
            });
            
            console.debug(`[PyNext Live] Synced ${query_id}: ${rows.length} rows`);
        },
        
        /**
         * Handle error message.
         */
        _handleError: function(message) {
            const { query_id, data } = message;
            const error = data?.error || 'Unknown error';
            
            if (query_id) {
                const subscription = this.subscriptions.get(query_id);
                if (subscription) {
                    subscription.error = error;
                    subscription.loading = false;
                    
                    if (window.__pynext__.setSignal) {
                        window.__pynext__.setSignal(query_id + '_error', error);
                        window.__pynext__.setSignal(query_id + '_loading', false);
                    }
                }
            }
            
            console.error(`[PyNext Live] Error: ${error}`);
        },
        
        /**
         * Send subscribe message.
         */
        _sendSubscribe: function(queryId, config) {
            this._send({
                type: 'subscribe',
                query_id: queryId,
                data: {
                    table: config.table,
                    where: config.where,
                    orderBy: config.orderBy,
                    limit: config.limit,
                },
            });
        },
        
        /**
         * Send unsubscribe message.
         */
        _sendUnsubscribe: function(queryId) {
            this._send({
                type: 'unsubscribe',
                query_id: queryId,
            });
        },
        
        /**
         * Request a refresh.
         */
        _requestRefresh: function(queryId) {
            const subscription = this.subscriptions.get(queryId);
            if (!subscription) return;
            
            subscription.loading = true;
            
            if (window.__pynext__.setSignal) {
                window.__pynext__.setSignal(queryId + '_loading', true);
            }
            
            // For SSE, we need to make a separate request
            if (this.transportType === 'sse') {
                fetch(`/_pynext/live/refresh?query_id=${queryId}`, {
                    method: 'POST',
                }).catch(e => console.error('[PyNext Live] Refresh failed:', e));
            } else {
                this._send({ type: 'refresh', query_id: queryId });
            }
        },
        
        /**
         * Send message through transport.
         * 
         * Uses Phase 5 websocket.js infrastructure when available.
         */
        _send: function(message) {
            if (!this.connected) {
                console.debug('[PyNext Live] Not connected, queuing message');
                return;
            }
            
            if (this.transportType === 'websocket') {
                // Use websocket.js if available
                if (window.__pynext__.websocket && this._wsConnectionId) {
                    window.__pynext__.websocket.send(this._wsConnectionId, message);
                } else if (this.transport) {
                    this.transport.send(JSON.stringify(message));
                }
            }
            // SSE is one-way, subscribes happen via initial connection
        },
        
        /**
         * Schedule reconnection with exponential backoff.
         */
        _scheduleReconnect: function() {
            if (this.reconnectAttempts >= this.maxReconnectAttempts) {
                console.warn('[PyNext Live] Max reconnect attempts reached');
                return;
            }
            
            const delay = this.config.reconnectDelay * Math.pow(2, this.reconnectAttempts);
            this.reconnectAttempts++;
            
            console.debug(`[PyNext Live] Reconnecting in ${delay}ms`);
            
            setTimeout(() => {
                if (!this.connected && this.subscriptions.size > 0) {
                    this._ensureConnected(this.transportType);
                }
            }, delay);
        },
        
        /**
         * Build index of data by ID.
         */
        _buildIndex: function(data) {
            const index = {};
            data.forEach(row => {
                if (row.id) index[row.id] = row;
            });
            return index;
        },
        
        /**
         * Resolve WebSocket URL.
         */
        _resolveWSUrl: function(path) {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            return `${protocol}//${window.location.host}${path}`;
        },
        
        /**
         * Disconnect and cleanup.
         * 
         * Uses Phase 5 websocket.js infrastructure when available.
         */
        disconnect: function() {
            if (this.transportType === 'sse') {
                if (this.transport) {
                    this.transport.close();
                    this.transport = null;
                }
            } else if (this.transportType === 'websocket') {
                // Use websocket.js if available
                if (window.__pynext__.websocket && this._wsConnectionId) {
                    window.__pynext__.websocket.close(this._wsConnectionId);
                    this._wsConnectionId = null;
                } else if (this.transport && this.transport.readyState === WebSocket.OPEN) {
                    this.transport.close();
                }
                this.transport = null;
            }
            
            this.connected = false;
            this.connecting = false;
            this.subscriptions.clear();
            
            console.debug('[PyNext Live] Disconnected');
        },
    };
    
    // Auto-disconnect on page unload
    window.addEventListener('beforeunload', () => {
        window.__pynext__.live.disconnect();
    });
    
})();

