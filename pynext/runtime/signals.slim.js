/**
 * PyNext Signals Runtime (Slim)
 * 
 * Lightweight version of the signals runtime for production use.
 * Compatible with AST transpiler output.
 * 
 * Features:
 * - Signal creation and reactivity
 * - Effect system for derived values
 * - Memo for computed values
 * - Batched updates
 * - DOM text bindings
 * - Show/For control flow helpers
 * - Python runtime helpers (__py.dict.get, __py.bool, etc.)
 */
(function(g) {
    'use strict';
    
    var signals = new Map();
    var effects = [];
    var currentEffect = null;
    var batchDepth = 0;
    var batchQueue = new Set();

    // ==========================================================================
    // Python Runtime Helpers
    // These match the Python semantics that the transpiler generates
    // ==========================================================================
    var __py = {
        // Boolean conversion (Python's bool())
        bool: function(v) { return !!v; },
        
        // Length (Python's len())
        len: function(v) { 
            return v && v.length !== undefined ? v.length : Object.keys(v || {}).length; 
        },
        
        // Dict operations
        dict: {
            get: function(d, k, def) { 
                return d && d[k] !== undefined ? d[k] : (def !== undefined ? def : null); 
            },
            keys: function(d) { return Object.keys(d || {}); },
            values: function(d) { return Object.values(d || {}); },
            items: function(d) { return Object.entries(d || {}); }
        },
        
        // List operations
        list: {
            append: function(l, v) { l.push(v); return l; },
            filter: function(l, fn) { return l.filter(fn); },
            map: function(l, fn) { return l.map(fn); }
        },
        
        // Type conversions
        str: function(v) { return String(v); },
        int: function(v) { return parseInt(v, 10); },
        float: function(v) { return parseFloat(v); }
    };

    // ==========================================================================
    // Signal System
    // ==========================================================================
    
    function createSignal(id, value) {
        var subscribers = new Set();
        
        var signal = {
            id: id,
            _value: value,
            
            // Read the signal value (tracks dependencies)
            read: function() {
                if (currentEffect) subscribers.add(currentEffect);
                return signal._value;
            },
            
            // Alias for read() for backwards compatibility
            get: function() { return signal.read(); },
            
            // Set the signal value
            set: function(v) {
                if (typeof v === 'function') v = v(signal._value);
                if (signal._value === v) return;
                signal._value = v;
                updateDOM(id, v);
                
                if (batchDepth > 0) {
                    subscribers.forEach(function(e) { batchQueue.add(e); });
                } else {
                    subscribers.forEach(function(fn) { 
                        if (fn.execute) fn.execute(); else fn(); 
                    });
                }
            },
            
            // Alias for set()
            write: function(v) { signal.set(v); },
            
            // Subscribe to changes
            subscribe: function(fn) {
                var effect = { execute: fn, dependencies: new Set() };
                subscribers.add(effect);
                return function() { subscribers.delete(effect); };
            }
        };
        
        signals.set(id, signal);
        return signal;
    }
    
    function getSignal(id) { 
        return signals.get(id); 
    }
    
    function setSignal(id, v) { 
        var s = signals.get(id); 
        if (s) s.set(v); 
    }

    // ==========================================================================
    // Effect System
    // ==========================================================================
    
    function createEffect(fn) {
        var effect = {
            execute: function() {
                currentEffect = effect;
                try { fn(); } finally { currentEffect = null; }
            },
            dependencies: new Set()
        };
        effects.push(effect);
        effect.execute();
        return effect;
    }
    
    function createMemo(id, fn) {
        var signal = createSignal(id, undefined);
        createEffect(function() { signal.set(fn()); });
        return signal;
    }
    
    function batch(fn) {
        batchDepth++;
        try { fn(); } finally {
            batchDepth--;
            if (batchDepth === 0) {
                var q = Array.from(batchQueue);
                batchQueue.clear();
                q.forEach(function(e) { if (e.execute) e.execute(); else e(); });
            }
        }
    }

    // ==========================================================================
    // DOM Updates
    // ==========================================================================
    
    function updateDOM(id, v) {
        // Update text bindings
        var els = document.querySelectorAll('[data-pynext-text="' + id + '"]');
        els.forEach(function(el) { el.textContent = v; });
        
        // Legacy selector
        els = document.querySelectorAll('[data-signal="' + id + '"]');
        els.forEach(function(el) { el.textContent = v; });
    }

    // ==========================================================================
    // Control Flow Helpers
    // ==========================================================================
    
    function updateShow(id, visible) {
        var el = document.getElementById(id);
        if (el) {
            el.style.display = visible ? '' : 'none';
            el.setAttribute('data-condition', visible ? 'true' : 'false');
        }
    }
    
    function updateFor(id, items, renderFn) {
        var container = document.getElementById(id);
        if (!container) return;
        container.innerHTML = '';
        (items || []).forEach(function(item, idx) {
            var html = renderFn(item, idx);
            container.insertAdjacentHTML('beforeend', html);
        });
    }

    // ==========================================================================
    // Hydration
    // ==========================================================================
    
    function hydrate(data) {
        if (!data) return;
        
        // Hydrate signals
        if (data.signals) {
            Object.keys(data.signals).forEach(function(name) {
                var s = data.signals[name];
                createSignal(name, s.value);
                if (s.id && s.id !== name) {
                    signals.set(s.id, signals.get(name));
                }
            });
        }
        
        // Hydrate memos (they work like signals on the client)
        if (data.memos) {
            Object.keys(data.memos).forEach(function(name) {
                var m = data.memos[name];
                createSignal(name, m.value);
            });
        }
        
        // Attach event handlers
        if (data.events) {
            Object.keys(data.events).forEach(function(elId) {
                var el = document.getElementById(elId);
                if (!el) return;
                var handlers = data.events[elId];
                Object.keys(handlers).forEach(function(eventName) {
                    var handler = handlers[eventName];
                    var code = typeof handler === 'string' ? handler : (handler.code || '');
                    if (!code) return;
                    try {
                        var fn = new Function('event', code);
                        el.addEventListener(eventName, fn);
                    } catch (e) { console.error('Handler error:', e); }
                });
            });
        }
        
        // Set up reactive bindings (Show/For/Text/Attr/Class)
        if (data.bindings) {
            data.bindings.forEach(function(b) {
                var expr = b.update || b.updateExpr;
                var nodeId = b.nodeId || b.node_id;
                var type = b.type || b.bindingType;
                var deps = b.signals || b.signalDeps || [];
                
                if (!expr || deps.length === 0) return;
                
                createEffect(function() {
                    try {
                        // Use new Function instead of eval for consistency and strict mode compatibility
                        var result = (new Function('return ' + expr))();
                        if (type === 'show') {
                            updateShow(nodeId, result);
                        } else if (type === 'text') {
                            var el = document.getElementById(nodeId);
                            if (el) el.textContent = result != null ? result : '';
                        } else if (type === 'for') {
                            // For bindings are handled by the For component
                        } else if (type === 'attr') {
                            var el = document.getElementById(nodeId);
                            var attr = b.attr;
                            if (el && attr) el.setAttribute(attr, result);
                        } else if (type === 'class') {
                            var el = document.getElementById(nodeId);
                            if (el) el.className = result;
                        }
                    } catch (e) { console.error('Binding error:', nodeId, e); }
                });
            });
        }
    }

    // ==========================================================================
    // Global Exports
    // ==========================================================================
    
    // Initialize global namespace
    g.__pynext__ = g.__pynext__ || {};
    g.__pynext__.signals = g.__pynext__.signals || {};
    g.__pynext__.stores = g.__pynext__.stores || {};
    g.__pynext__.forms = g.__pynext__.forms || {};
    g.__pynext__.memos = g.__pynext__.memos || {};
    
    // Export functions - wrap to sync with internal Map
    g.__pynext__.createSignal = function(id, value) {
        var sig = createSignal(id, value);
        g.__pynext__.signals[id] = sig;
        return sig;
    };
    
    g.__pynext__.getSignal = function(id) {
        return signals.get(id) || g.__pynext__.signals[id];
    };
    
    g.__pynext__.setSignal = setSignal;
    g.__pynext__.createEffect = createEffect;
    g.__pynext__.createMemo = createMemo;
    g.__pynext__.batch = batch;
    g.__pynext__.updateShow = updateShow;
    g.__pynext__.updateFor = updateFor;
    
    g.__pynext__.hydrate = function(data) {
        hydrate(data);
        // Copy signals to global namespace for debugging/inspection
        signals.forEach(function(sig, id) { 
            g.__pynext__.signals[id] = sig; 
        });
    };
    
    // Python helpers
    g.__py = __py;
    
    // Auto-hydrate if data present
    if (g.__PYNEXT_DATA__) hydrate(g.__PYNEXT_DATA__);
    if (g.__PYNEXT_HYDRATION__) hydrate(g.__PYNEXT_HYDRATION__);
    
})(typeof window !== 'undefined' ? window : this);
