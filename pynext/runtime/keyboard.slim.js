/**
 * PyNext Keyboard Runtime (Slim)
 * Keyboard shortcuts and key sequences
 */
(function(g) {
    'use strict';
    
    var isMac = /Mac|iPhone|iPad/.test(navigator.platform || '');
    var shortcuts = new Map();
    var sequences = new Map();
    var handlers = new Map();
    var seqBuffer = [];
    var seqTimeout = null;
    
    function register(config) {
        shortcuts.set(config.id, config);
    }
    
    function registerSeq(config) {
        sequences.set(config.id, config);
    }
    
    function registerHandler(id, fn) {
        handlers.set(id, fn);
    }
    
    function matches(e, s) {
        if (e.key.toLowerCase() !== s.key) return false;
        var m = s.modifiers || [];
        return (m.includes('meta') === e.metaKey) &&
               (m.includes('ctrl') === e.ctrlKey) &&
               (m.includes('alt') === e.altKey) &&
               (m.includes('shift') === e.shiftKey);
    }
    
    function checkContext(e, s) {
        var ctx = s.context || 'global';
        var tag = e.target.tagName;
        var isInput = tag === 'INPUT' || tag === 'TEXTAREA' || e.target.isContentEditable;
        
        if (ctx === 'global' && isInput) return false;
        if (ctx === 'dialog' && !e.target.closest('[role="dialog"]')) return false;
        return true;
    }
    
    function handleKeydown(e) {
        // Check shortcuts
        for (var [id, s] of shortcuts) {
            if (matches(e, s) && checkContext(e, s)) {
                if (s.preventDefault !== false) e.preventDefault();
                var h = handlers.get(s.handlerId);
                if (h) h(e);
                return;
            }
        }
        
        // Check sequences
        if (!e.metaKey && !e.ctrlKey && !e.altKey) {
            clearTimeout(seqTimeout);
            seqBuffer.push(e.key.toLowerCase());
            
            for (var [id, seq] of sequences) {
                var keys = seq.keys;
                var match = true;
                for (var i = 0; i < keys.length; i++) {
                    if (seqBuffer[seqBuffer.length - keys.length + i] !== keys[i]) {
                        match = false;
                        break;
                    }
                }
                if (match && seqBuffer.length >= keys.length) {
                    seqBuffer = [];
                    var h = handlers.get(seq.handlerId);
                    if (h) h(e);
                    return;
                }
            }
            
            seqTimeout = setTimeout(function() { seqBuffer = []; }, seq ? seq.timeout || 1000 : 1000);
        }
    }
    
    function hydrate(data) {
        if (!data) return;
        (data.shortcuts || []).forEach(function(s) { register(s); });
        (data.sequences || []).forEach(function(s) { registerSeq(s); });
    }
    
    document.addEventListener('keydown', handleKeydown);
    
    g.__pynext__ = g.__pynext__ || {};
    g.__pynext__.keyboard = {
        register: register,
        registerSeq: registerSeq,
        registerHandler: registerHandler,
        unregister: function(id) { shortcuts.delete(id); },
        unregisterSeq: function(id) { sequences.delete(id); },
        hydrate: hydrate,
        isMac: isMac
    };
    
    if (g.__PYNEXT_DATA__) hydrate(g.__PYNEXT_DATA__);
    
})(window);

