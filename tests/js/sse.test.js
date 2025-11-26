/**
 * SSE Runtime Tests
 * Tests for sse.js functionality (Server-Sent Events)
 */

describe('SSE Management', () => {
    let mockEventSource;
    let eventSourceInstances;
    
    beforeEach(() => {
        eventSourceInstances = [];
        
        // Mock EventSource
        mockEventSource = jest.fn().mockImplementation((url) => {
            const instance = {
                url,
                readyState: 0, // CONNECTING
                CONNECTING: 0,
                OPEN: 1,
                CLOSED: 2,
                onopen: null,
                onmessage: null,
                onerror: null,
                _listeners: {},
                addEventListener: jest.fn((event, handler) => {
                    if (!instance._listeners[event]) {
                        instance._listeners[event] = [];
                    }
                    instance._listeners[event].push(handler);
                }),
                removeEventListener: jest.fn((event, handler) => {
                    if (instance._listeners[event]) {
                        instance._listeners[event] = instance._listeners[event].filter(h => h !== handler);
                    }
                }),
                close: jest.fn(() => {
                    instance.readyState = 2;
                }),
                // Helper to simulate events
                _emit: (event, data) => {
                    if (instance._listeners[event]) {
                        instance._listeners[event].forEach(h => h(data));
                    }
                    if (event === 'open' && instance.onopen) instance.onopen(data);
                    if (event === 'message' && instance.onmessage) instance.onmessage(data);
                    if (event === 'error' && instance.onerror) instance.onerror(data);
                }
            };
            eventSourceInstances.push(instance);
            return instance;
        });
        
        global.EventSource = mockEventSource;
        
        // Mock SSE module
        window.__pynext__ = window.__pynext__ || {};
        window.__pynext__.sse = {
            connections: new Map(),
            
            connect: function(url, options = {}) {
                const es = new EventSource(url);
                const connection = {
                    es,
                    url,
                    reconnectAttempts: 0,
                    maxReconnects: options.maxReconnects || 5,
                    reconnectDelay: options.reconnectDelay || 1000,
                    handlers: new Map(),
                    
                    on: function(event, handler) {
                        if (!this.handlers.has(event)) {
                            this.handlers.set(event, []);
                        }
                        this.handlers.get(event).push(handler);
                        es.addEventListener(event, handler);
                        return () => {
                            es.removeEventListener(event, handler);
                            const handlers = this.handlers.get(event);
                            if (handlers) {
                                this.handlers.set(event, handlers.filter(h => h !== handler));
                            }
                        };
                    },
                    
                    close: function() {
                        es.close();
                        window.__pynext__.sse.connections.delete(url);
                    }
                };
                
                this.connections.set(url, connection);
                return connection;
            },
            
            disconnect: function(url) {
                const conn = this.connections.get(url);
                if (conn) {
                    conn.close();
                }
            },
            
            disconnectAll: function() {
                this.connections.forEach(conn => conn.close());
                this.connections.clear();
            }
        };
    });
    
    afterEach(() => {
        eventSourceInstances = [];
    });
    
    describe('connect', () => {
        test('creates EventSource with URL', () => {
            window.__pynext__.sse.connect('/api/events');
            expect(mockEventSource).toHaveBeenCalledWith('/api/events');
        });
        
        test('stores connection in map', () => {
            const conn = window.__pynext__.sse.connect('/api/events');
            expect(window.__pynext__.sse.connections.get('/api/events')).toBe(conn);
        });
        
        test('returns connection object with methods', () => {
            const conn = window.__pynext__.sse.connect('/api/events');
            expect(conn.on).toBeDefined();
            expect(conn.close).toBeDefined();
        });
    });
    
    describe('event handling', () => {
        test('registers event handler', () => {
            const conn = window.__pynext__.sse.connect('/api/events');
            const handler = jest.fn();
            conn.on('update', handler);
            
            expect(eventSourceInstances[0].addEventListener).toHaveBeenCalledWith('update', handler);
        });
        
        test('handler receives events', () => {
            const conn = window.__pynext__.sse.connect('/api/events');
            const handler = jest.fn();
            conn.on('message', handler);
            
            // Simulate event
            eventSourceInstances[0]._emit('message', { data: 'test data' });
            
            expect(handler).toHaveBeenCalledWith({ data: 'test data' });
        });
        
        test('unsubscribe removes handler', () => {
            const conn = window.__pynext__.sse.connect('/api/events');
            const handler = jest.fn();
            const unsubscribe = conn.on('update', handler);
            
            unsubscribe();
            
            expect(eventSourceInstances[0].removeEventListener).toHaveBeenCalledWith('update', handler);
        });
    });
    
    describe('disconnect', () => {
        test('closes EventSource', () => {
            window.__pynext__.sse.connect('/api/events');
            window.__pynext__.sse.disconnect('/api/events');
            
            expect(eventSourceInstances[0].close).toHaveBeenCalled();
        });
        
        test('removes from connections map', () => {
            window.__pynext__.sse.connect('/api/events');
            window.__pynext__.sse.disconnect('/api/events');
            
            expect(window.__pynext__.sse.connections.has('/api/events')).toBe(false);
        });
    });
    
    describe('disconnectAll', () => {
        test('closes all connections', () => {
            window.__pynext__.sse.connect('/api/events1');
            window.__pynext__.sse.connect('/api/events2');
            window.__pynext__.sse.disconnectAll();
            
            expect(eventSourceInstances[0].close).toHaveBeenCalled();
            expect(eventSourceInstances[1].close).toHaveBeenCalled();
        });
        
        test('clears connections map', () => {
            window.__pynext__.sse.connect('/api/events1');
            window.__pynext__.sse.connect('/api/events2');
            window.__pynext__.sse.disconnectAll();
            
            expect(window.__pynext__.sse.connections.size).toBe(0);
        });
    });
    
    describe('reconnection', () => {
        test('connection has reconnect settings', () => {
            const conn = window.__pynext__.sse.connect('/api/events', {
                maxReconnects: 3,
                reconnectDelay: 2000
            });
            
            expect(conn.maxReconnects).toBe(3);
            expect(conn.reconnectDelay).toBe(2000);
        });
        
        test('uses default reconnect settings', () => {
            const conn = window.__pynext__.sse.connect('/api/events');
            
            expect(conn.maxReconnects).toBe(5);
            expect(conn.reconnectDelay).toBe(1000);
        });
    });
});

describe('SSE Event Parsing', () => {
    test('parses JSON data', () => {
        const data = '{"type": "update", "payload": {"count": 42}}';
        const parsed = JSON.parse(data);
        expect(parsed.type).toBe('update');
        expect(parsed.payload.count).toBe(42);
    });
    
    test('handles plain text data', () => {
        const data = 'Hello, World!';
        expect(data).toBe('Hello, World!');
    });
});

