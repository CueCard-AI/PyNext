"""
JS Injector - Inject PyNext-Aware Tracking Code.

This module injects JavaScript into the page that hooks into PyNext's
reactive system to report signal changes, component events, and user
interactions to the debug system.

What Gets Injected:
    - Signal read/write interceptors
    - Click event listeners with element info
    - Manual snapshot trigger (Ctrl+Shift+S)
    - Keyboard shortcut handlers
    - Component lifecycle tracking

Why Inject?
    CDP can see console messages and network, but it can't see internal
    PyNext state like signal values or which component triggered an update.
    We inject code that hooks into PyNext's runtime to expose this info.

How It Works:
    1. Wait for page to load
    2. Inject tracking script via CDP Runtime.evaluate
    3. Script patches __pynext__ object to intercept operations
    4. Events are reported via console.log with special prefix
    5. EventCapture parses these messages into structured events

Example:
    injector = JSInjector(bridge)
    await injector.inject()
    
    # Now signal changes will appear as:
    # [PyNext] SIGNAL: view_mode = kanban (was: list)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pynext.devtools.bridge import CDPBridge


# JavaScript code to inject into the page
TRACKING_SCRIPT = """
(function() {
    'use strict';
    
    // Prevent double injection
    if (window.__pynext_debug__) {
        console.log('[PyNext] DEBUG: Already injected');
        return;
    }
    
    console.log('[PyNext] DEBUG: Injecting AI debug hooks...');
    
    // Debug state
    window.__pynext_debug__ = {
        enabled: true,
        signals: {},        // signal_id -> { name, value, component, line }
        lastClick: null,    // Last clicked element info
        eventCount: 0,      // Number of events sent
        _sessionActive: false,
        _sessionIntent: '',
        
        // Session management - start recording session
        session_start: function(intent) {
            if (this._sessionActive) {
                console.log('[PyNext] SESSION_START: (already active)');
                return;
            }
            this._sessionActive = true;
            this._sessionIntent = intent || 'debug session';
            console.log('[PyNext] SESSION_START: ' + this._sessionIntent);
            this.eventCount++;
        },
        
        // Session management - end recording session
        session_end: function(outcome) {
            if (!this._sessionActive) {
                console.log('[PyNext] SESSION_END: (no active session)');
                return;
            }
            this._sessionActive = false;
            const result = outcome || 'completed';
            console.log('[PyNext] SESSION_END: ' + result);
            this.eventCount++;
        },
        
        // Add note during session
        note: function(text) {
            console.log('[PyNext] NOTE: ' + (text || 'note'));
            this.eventCount++;
        },
        
        // Manual snapshot function
        snapshot: function(note) {
            console.log('[PyNext] SNAPSHOT: ' + (note || 'manual'));
            this.eventCount++;
        },
        
        // Check session status
        status: function() {
            console.log('[PyNext] STATUS: session=' + this._sessionActive + 
                        ', events=' + this.eventCount +
                        ', intent=' + this._sessionIntent);
        },
        
        // Report signal change
        reportSignal: function(name, newValue, oldValue) {
            const msg = name + ' = ' + JSON.stringify(newValue) + 
                        ' (was: ' + JSON.stringify(oldValue) + ')';
            console.log('[PyNext] SIGNAL: ' + msg);
            this.eventCount++;
        },
        
        // Report effect execution
        reportEffect: function(id, deps) {
            console.log('[PyNext] EFFECT: ' + id + ' deps=[' + deps.join(',') + ']');
            this.eventCount++;
        },
        
        // Report component mount
        reportMount: function(componentName, elementId) {
            console.log('[PyNext] MOUNT: ' + componentName + ' -> #' + elementId);
            this.eventCount++;
        },
        
        // Report click
        reportClick: function(element, x, y) {
            const info = this.getElementInfo(element);
            this.lastClick = { element: info, x: x, y: y };
            console.log('[PyNext] CLICK: ' + info.selector + ' at (' + x + ',' + y + ')');
            this.eventCount++;
        },
        
        // Get element info for reporting
        getElementInfo: function(el) {
            if (!el) return { tagName: 'unknown', selector: 'unknown' };
            
            const tag = el.tagName.toLowerCase();
            const id = el.id;
            const classes = Array.from(el.classList || []).join('.');
            
            let selector = tag;
            if (id) {
                selector = '#' + id;
            } else if (classes) {
                selector = tag + '.' + classes;
            }
            
            // Try to find PyNext data attributes
            const pynextId = el.getAttribute('data-pynext-id') || 
                            el.getAttribute('id') || '';
            const pynextBind = el.getAttribute('data-pynext-bind') || '';
            
            return {
                tagName: tag,
                id: id || '',
                classes: Array.from(el.classList || []),
                selector: selector,
                pynextId: pynextId,
                pynextBind: pynextBind,
                textContent: (el.textContent || '').substring(0, 50),
            };
        },
        
        // Get all signal states
        getSignalStates: function() {
            const states = {};
            if (window.__pynext__ && window.__pynext__.signals) {
                for (const [id, signal] of Object.entries(window.__pynext__.signals)) {
                    try {
                        states[id] = {
                            value: signal.read ? signal.read() : signal._value,
                            name: signal._name || id,
                        };
                    } catch (e) {
                        states[id] = { value: '(error)', name: id };
                    }
                }
            }
            return states;
        },
        
        // Get current page state for AI
        getState: function() {
            return {
                url: window.location.href,
                title: document.title,
                signals: this.getSignalStates(),
                lastClick: this.lastClick,
                eventCount: this.eventCount,
            };
        },
    };
    
    // Alias for easier typing in console
    window.pynext_debug = window.__pynext_debug__;
    
    // Patch __pynext__.createSignal if available
    function patchSignals() {
        if (!window.__pynext__) {
            return false;
        }
        
        const pynext = window.__pynext__;
        
        // Patch getSignal to track reads
        if (pynext.getSignal && !pynext._getSignal_original) {
            pynext._getSignal_original = pynext.getSignal;
            pynext.getSignal = function(id) {
                const signal = pynext._getSignal_original(id);
                if (signal && !signal._debug_patched) {
                    signal._debug_patched = true;
                    
                    // Store signal info
                    window.__pynext_debug__.signals[id] = {
                        name: signal._name || id,
                        component: signal._component || '',
                        line: signal._line || 0,
                    };
                    
                    // Patch set method
                    if (signal.set && !signal._set_original) {
                        signal._set_original = signal.set;
                        signal.set = function(newValue) {
                            const oldValue = signal._value;
                            const result = signal._set_original(newValue);
                            window.__pynext_debug__.reportSignal(
                                signal._name || id,
                                newValue,
                                oldValue
                            );
                            return result;
                        };
                    }
                    
                    // Patch update method
                    if (signal.update && !signal._update_original) {
                        signal._update_original = signal.update;
                        signal.update = function(fn) {
                            const oldValue = signal._value;
                            const result = signal._update_original(fn);
                            const newValue = signal._value;
                            window.__pynext_debug__.reportSignal(
                                signal._name || id,
                                newValue,
                                oldValue
                            );
                            return result;
                        };
                    }
                }
                return signal;
            };
        }
        
        return true;
    }
    
    // Set up click tracking
    function setupClickTracking() {
        document.addEventListener('click', function(e) {
            const target = e.target;
            window.__pynext_debug__.reportClick(target, e.clientX, e.clientY);
        }, true);  // Capture phase to get all clicks
    }
    
    // Set up keyboard shortcuts
    function setupKeyboardShortcuts() {
        document.addEventListener('keydown', function(e) {
            // Ctrl+Shift+S for manual snapshot
            if (e.ctrlKey && e.shiftKey && e.key === 'S') {
                e.preventDefault();
                const note = prompt('Snapshot note (optional):') || '';
                window.__pynext_debug__.snapshot(note);
            }
        });
    }
    
    // Initialize
    function init() {
        setupClickTracking();
        setupKeyboardShortcuts();
        
        // Try to patch signals immediately
        if (!patchSignals()) {
            // Wait for __pynext__ to be available
            let attempts = 0;
            const interval = setInterval(function() {
                if (patchSignals() || attempts++ > 50) {
                    clearInterval(interval);
                }
            }, 100);
        }
        
        console.log('[PyNext] DEBUG: AI debug hooks ready');
        console.log('[PyNext] HYDRATION: complete');
    }
    
    // Add pynext_debug alias (easier to type than __pynext_debug__)
    window.pynext_debug = window.__pynext_debug__;
    
    // Add session recording API
    const debug = window.__pynext_debug__;
    
    debug._session = null;
    debug._sessionNotes = [];
    debug._frameCount = 0;
    
    debug.session_start = function(intent) {
        if (debug._session) {
            console.warn('[PyNext Debug] Session already active. Call session_end() first.');
            return false;
        }
        debug._session = {
            id: 'rec_' + Date.now(),
            intent: intent || '',
            startTime: Date.now(),
        };
        debug._sessionNotes = [];
        debug._frameCount = 0;
        console.log('%c[PyNext Debug] Session started: ' + intent, 'color: #4CAF50; font-weight: bold');
        console.log('[PyNext] SESSION_START: ' + intent);
        return true;
    };
    
    debug.session_end = function(outcome) {
        if (!debug._session) {
            console.warn('[PyNext Debug] No active session.');
            return null;
        }
        debug._session.outcome = outcome || '';
        debug._session.endTime = Date.now();
        console.log('%c[PyNext Debug] Session ended: ' + outcome, 'color: #f44336; font-weight: bold');
        console.log('[PyNext] SESSION_END: ' + JSON.stringify({
            id: debug._session.id,
            intent: debug._session.intent,
            outcome: outcome,
            duration: debug._session.endTime - debug._session.startTime,
            noteCount: debug._sessionNotes.length,
        }));
        const session = debug._session;
        debug._session = null;
        return session;
    };
    
    debug.note = function(text) {
        if (!debug._session) {
            console.warn('[PyNext Debug] No active session. Call session_start() first.');
            return false;
        }
        const note = { ts: Date.now() - debug._session.startTime, text: text };
        debug._sessionNotes.push(note);
        console.log('%c[PyNext Debug] Note: ' + text, 'color: #2196F3');
        console.log('[PyNext] NOTE: ' + text);
        return true;
    };
    
    debug.status = function() {
        if (!debug._session) {
            console.log('[PyNext Debug] No active session.');
            return { active: false };
        }
        return {
            active: true,
            id: debug._session.id,
            intent: debug._session.intent,
            elapsed: Date.now() - debug._session.startTime,
            notes: debug._sessionNotes.length,
        };
    };
    
    debug.inspect = function() {
        console.log('%c[PyNext Debug] Inspect mode: Hover over elements to see info, click to select', 'color: #2196F3; font-weight: bold');
        console.log('Note: Full inspect mode requires CDP connection. For now, hover info shown in console.');
        
        const handler = function(e) {
            const el = e.target;
            const info = debug.getElementInfo(el);
            info.handlers = {
                onclick: el.onclick !== null,
                oninput: el.oninput !== null,
            };
            info.hydrated = el.onclick !== null || el.oninput !== null || !el.hasAttribute('data-pynext-bind');
            console.log('[PyNext Debug] Element:', info);
        };
        
        document.addEventListener('mouseover', handler);
        
        const clickHandler = function(e) {
            e.preventDefault();
            e.stopPropagation();
            const el = e.target;
            const info = debug.getElementInfo(el);
            info.handlers = {
                onclick: el.onclick !== null,
                oninput: el.oninput !== null,
            };
            console.log('%c[PyNext Debug] Selected:', 'color: #4CAF50; font-weight: bold', info);
            console.log('[PyNext] ELEMENT_SELECT: ' + JSON.stringify(info));
            document.removeEventListener('mouseover', handler);
            document.removeEventListener('click', clickHandler, true);
        };
        
        document.addEventListener('click', clickHandler, true);
    };
    
    // Drawing state
    debug._drawOverlay = null;
    debug._drawCanvas = null;
    debug._drawCtx = null;
    debug._drawToolbar = null;
    debug._drawTool = 'circle';
    debug._drawColor = '#ff0000';
    debug._drawAnnotations = [];
    debug._drawIsDrawing = false;
    debug._drawStartPos = null;
    debug._drawCurrentPoints = [];
    
    debug.draw = function(tool) {
        if (debug._drawOverlay) {
            console.warn('[PyNext Debug] Draw mode already active. Press ESC to exit.');
            return;
        }
        
        debug._drawTool = tool || 'circle';
        debug._createDrawOverlay();
        console.log('%c[PyNext Debug] Draw mode active. Tool: ' + debug._drawTool, 'color: #ff9800; font-weight: bold');
        console.log('Press ESC or click Done to exit draw mode.');
    };
    
    debug.disableDraw = function() {
        if (!debug._drawOverlay) return;
        
        // Remove event listeners
        document.removeEventListener('keydown', debug._drawKeyHandler);
        
        // Remove overlay
        debug._drawOverlay.remove();
        debug._drawOverlay = null;
        debug._drawCanvas = null;
        debug._drawCtx = null;
        debug._drawToolbar = null;
        
        console.log('%c[PyNext Debug] Draw mode exited. ' + debug._drawAnnotations.length + ' annotations captured.', 'color: #4CAF50');
    };
    
    debug._createDrawOverlay = function() {
        // Create overlay container
        const overlay = document.createElement('div');
        overlay.id = 'pynext-draw-overlay';
        overlay.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:999999;cursor:crosshair;';
        
        // Create canvas
        const canvas = document.createElement('canvas');
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        canvas.style.cssText = 'position:absolute;top:0;left:0;width:100%;height:100%;';
        overlay.appendChild(canvas);
        
        // Create toolbar
        const toolbar = document.createElement('div');
        toolbar.style.cssText = 'position:absolute;top:10px;left:50%;transform:translateX(-50%);background:#333;padding:8px 16px;border-radius:8px;display:flex;gap:8px;align-items:center;box-shadow:0 4px 12px rgba(0,0,0,0.3);';
        
        // Tool buttons
        const tools = [
            { id: 'circle', label: '⭕', title: 'Circle' },
            { id: 'arrow', label: '➡️', title: 'Arrow' },
            { id: 'freehand', label: '✏️', title: 'Freehand' },
            { id: 'text', label: '💬', title: 'Text' },
        ];
        
        tools.forEach(t => {
            const btn = document.createElement('button');
            btn.textContent = t.label;
            btn.title = t.title;
            btn.style.cssText = 'padding:6px 12px;border:none;border-radius:4px;cursor:pointer;font-size:16px;background:' + (debug._drawTool === t.id ? '#666' : '#444') + ';color:#fff;';
            btn.onclick = function() {
                debug._drawTool = t.id;
                toolbar.querySelectorAll('button').forEach(b => b.style.background = '#444');
                btn.style.background = '#666';
            };
            toolbar.appendChild(btn);
        });
        
        // Separator
        const sep = document.createElement('div');
        sep.style.cssText = 'width:1px;height:24px;background:#555;margin:0 4px;';
        toolbar.appendChild(sep);
        
        // Color buttons
        const colors = ['#ff0000', '#00ff00', '#0066ff', '#ffff00'];
        colors.forEach(c => {
            const btn = document.createElement('button');
            btn.style.cssText = 'width:24px;height:24px;border:2px solid ' + (debug._drawColor === c ? '#fff' : '#333') + ';border-radius:50%;cursor:pointer;background:' + c + ';';
            btn.onclick = function() {
                debug._drawColor = c;
                toolbar.querySelectorAll('button').forEach(b => {
                    if (b.style.borderRadius === '50%') b.style.borderColor = '#333';
                });
                btn.style.borderColor = '#fff';
            };
            toolbar.appendChild(btn);
        });
        
        // Separator
        const sep2 = document.createElement('div');
        sep2.style.cssText = 'width:1px;height:24px;background:#555;margin:0 4px;';
        toolbar.appendChild(sep2);
        
        // Done button
        const doneBtn = document.createElement('button');
        doneBtn.textContent = '✓ Done';
        doneBtn.style.cssText = 'padding:6px 16px;border:none;border-radius:4px;cursor:pointer;font-size:14px;background:#4CAF50;color:#fff;font-weight:bold;';
        doneBtn.onclick = function() {
            debug.disableDraw();
        };
        toolbar.appendChild(doneBtn);
        
        overlay.appendChild(toolbar);
        document.body.appendChild(overlay);
        
        debug._drawOverlay = overlay;
        debug._drawCanvas = canvas;
        debug._drawCtx = canvas.getContext('2d');
        debug._drawToolbar = toolbar;
        
        // Set up drawing context
        debug._drawCtx.strokeStyle = debug._drawColor;
        debug._drawCtx.lineWidth = 3;
        debug._drawCtx.lineCap = 'round';
        debug._drawCtx.lineJoin = 'round';
        
        // Mouse events
        canvas.addEventListener('mousedown', debug._drawMouseDown);
        canvas.addEventListener('mousemove', debug._drawMouseMove);
        canvas.addEventListener('mouseup', debug._drawMouseUp);
        
        // Keyboard events
        debug._drawKeyHandler = function(e) {
            if (e.key === 'Escape') {
                debug.disableDraw();
            }
        };
        document.addEventListener('keydown', debug._drawKeyHandler);
    };
    
    debug._drawMouseDown = function(e) {
        debug._drawIsDrawing = true;
        debug._drawStartPos = { x: e.clientX, y: e.clientY };
        debug._drawCurrentPoints = [{ x: e.clientX, y: e.clientY }];
        debug._drawCtx.strokeStyle = debug._drawColor;
        
        if (debug._drawTool === 'text') {
            const text = prompt('Enter annotation text:');
            if (text) {
                debug._drawCtx.font = '16px Arial';
                debug._drawCtx.fillStyle = debug._drawColor;
                debug._drawCtx.fillText(text, e.clientX, e.clientY);
                debug._emitDrawing('text', { position: debug._drawStartPos, text: text });
            }
            debug._drawIsDrawing = false;
        }
    };
    
    debug._drawMouseMove = function(e) {
        if (!debug._drawIsDrawing) return;
        
        const ctx = debug._drawCtx;
        const start = debug._drawStartPos;
        const current = { x: e.clientX, y: e.clientY };
        
        if (debug._drawTool === 'freehand') {
            debug._drawCurrentPoints.push(current);
            ctx.beginPath();
            ctx.moveTo(debug._drawCurrentPoints[debug._drawCurrentPoints.length - 2].x, 
                       debug._drawCurrentPoints[debug._drawCurrentPoints.length - 2].y);
            ctx.lineTo(current.x, current.y);
            ctx.stroke();
        } else {
            // Preview for circle/arrow - redraw canvas
            ctx.clearRect(0, 0, debug._drawCanvas.width, debug._drawCanvas.height);
            debug._redrawAnnotations();
            
            ctx.strokeStyle = debug._drawColor;
            ctx.lineWidth = 3;
            
            if (debug._drawTool === 'circle') {
                const radius = Math.sqrt(Math.pow(current.x - start.x, 2) + Math.pow(current.y - start.y, 2));
                ctx.beginPath();
                ctx.arc(start.x, start.y, radius, 0, 2 * Math.PI);
                ctx.stroke();
            } else if (debug._drawTool === 'arrow') {
                debug._drawArrow(ctx, start.x, start.y, current.x, current.y);
            }
        }
    };
    
    debug._drawMouseUp = function(e) {
        if (!debug._drawIsDrawing) return;
        debug._drawIsDrawing = false;
        
        const start = debug._drawStartPos;
        const end = { x: e.clientX, y: e.clientY };
        
        if (debug._drawTool === 'circle') {
            const radius = Math.sqrt(Math.pow(end.x - start.x, 2) + Math.pow(end.y - start.y, 2));
            debug._emitDrawing('circle', { center: start, radius: Math.round(radius) });
        } else if (debug._drawTool === 'arrow') {
            debug._emitDrawing('arrow', { from: start, to: end });
        } else if (debug._drawTool === 'freehand') {
            debug._emitDrawing('freehand', { points: debug._drawCurrentPoints });
        }
    };
    
    debug._drawArrow = function(ctx, fromX, fromY, toX, toY) {
        const headlen = 15;
        const dx = toX - fromX;
        const dy = toY - fromY;
        const angle = Math.atan2(dy, dx);
        
        ctx.beginPath();
        ctx.moveTo(fromX, fromY);
        ctx.lineTo(toX, toY);
        ctx.lineTo(toX - headlen * Math.cos(angle - Math.PI / 6), toY - headlen * Math.sin(angle - Math.PI / 6));
        ctx.moveTo(toX, toY);
        ctx.lineTo(toX - headlen * Math.cos(angle + Math.PI / 6), toY - headlen * Math.sin(angle + Math.PI / 6));
        ctx.stroke();
    };
    
    debug._redrawAnnotations = function() {
        // Redraw all saved annotations (for preview during drawing)
        const ctx = debug._drawCtx;
        debug._drawAnnotations.forEach(a => {
            ctx.strokeStyle = a.color;
            ctx.lineWidth = 3;
            if (a.type === 'circle') {
                ctx.beginPath();
                ctx.arc(a.data.center.x, a.data.center.y, a.data.radius, 0, 2 * Math.PI);
                ctx.stroke();
            } else if (a.type === 'arrow') {
                debug._drawArrow(ctx, a.data.from.x, a.data.from.y, a.data.to.x, a.data.to.y);
            } else if (a.type === 'freehand' && a.data.points.length > 1) {
                ctx.beginPath();
                ctx.moveTo(a.data.points[0].x, a.data.points[0].y);
                for (let i = 1; i < a.data.points.length; i++) {
                    ctx.lineTo(a.data.points[i].x, a.data.points[i].y);
                }
                ctx.stroke();
            } else if (a.type === 'text') {
                ctx.font = '16px Arial';
                ctx.fillStyle = a.color;
                ctx.fillText(a.data.text, a.data.position.x, a.data.position.y);
            }
        });
    };
    
    debug._emitDrawing = function(type, data) {
        const annotation = {
            type: type,
            color: debug._drawColor,
            data: data,
            ts: debug._session ? Date.now() - debug._session.startTime : 0,
        };
        debug._drawAnnotations.push(annotation);
        console.log('[PyNext] DRAWING: ' + JSON.stringify(annotation));
    };
    
    // Run when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    console.log('[PyNext] pynext_debug API available. Try: pynext_debug.session_start("test")');
})();
"""

# Minimal script for checking if already injected
CHECK_SCRIPT = "typeof window.__pynext_debug__ !== 'undefined'"

# Script to get current state
GET_STATE_SCRIPT = """
(function() {
    if (window.__pynext_debug__ && window.__pynext_debug__.getState) {
        return window.__pynext_debug__.getState();
    }
    return null;
})();
"""

# Script to trigger manual snapshot
TRIGGER_SNAPSHOT_SCRIPT = """
(function(note) {
    if (window.__pynext_debug__) {
        window.__pynext_debug__.snapshot(note);
        return true;
    }
    return false;
})({note});
"""


class JSInjector:
    """
    Injects PyNext-aware tracking JavaScript into the page.
    
    This class handles:
    - Checking if already injected
    - Injecting the tracking script
    - Getting current debug state
    - Triggering manual snapshots
    
    The injected script:
    - Patches __pynext__ to intercept signal changes
    - Sets up click event listeners
    - Provides manual snapshot via Ctrl+Shift+S
    - Reports events via console.log with [PyNext] prefix
    
    Example:
        injector = JSInjector(bridge)
        
        # Inject on page load
        await injector.inject()
        
        # Get current state
        state = await injector.get_state()
        print(f"Current URL: {state['url']}")
        print(f"Signals: {state['signals']}")
        
        # Trigger manual snapshot
        await injector.trigger_snapshot("Checking modal position")
    """
    
    def __init__(self, bridge: "CDPBridge"):
        """
        Initialize the JS injector.
        
        Args:
            bridge: CDPBridge instance for browser communication
        """
        self._bridge = bridge
        self._injected = False
    
    @property
    def injected(self) -> bool:
        """Check if tracking script has been injected."""
        return self._injected
    
    async def is_already_injected(self) -> bool:
        """
        Check if the tracking script is already in the page.
        
        Returns:
            True if __pynext_debug__ exists
        """
        try:
            result = await self._bridge.execute_script(CHECK_SCRIPT)
            return result is True
        except Exception:
            return False
    
    async def inject(self, force: bool = False) -> bool:
        """
        Inject the tracking script into the page.
        
        Uses Page.addScriptToEvaluateOnNewDocument to persist across navigations,
        plus Runtime.evaluate for the current page.
        
        Args:
            force: Inject even if already injected
        
        Returns:
            True if injection succeeded
        """
        if not force and await self.is_already_injected():
            self._injected = True
            return True
        
        try:
            # Add script to evaluate on every new document (persists across navigation)
            print("[PyNext AI Debug] Adding script for new documents...")
            add_result = await self._bridge.send_command(
                "Page.addScriptToEvaluateOnNewDocument",
                {"source": TRACKING_SCRIPT}
            )
            print(f"[PyNext AI Debug] addScriptToEvaluateOnNewDocument result: {add_result}")
            
            # Also run on current page immediately
            print("[PyNext AI Debug] Executing script on current page...")
            await self._bridge.execute_script(TRACKING_SCRIPT)
            print("[PyNext AI Debug] Script executed successfully")
            
            # Verify injection worked
            check_result = await self._bridge.execute_script("typeof window.pynext_debug")
            print(f"[PyNext AI Debug] Verification - pynext_debug type: {check_result}")
            
            if check_result != "object":
                print("[PyNext AI Debug] WARNING: pynext_debug not available after injection!")
            
            self._injected = True
            return True
        except Exception as e:
            import traceback
            print(f"[PyNext AI Debug] Injection failed: {e}")
            traceback.print_exc()
            return False
    
    async def get_state(self) -> dict | None:
        """
        Get current debug state from the page.
        
        Returns:
            Dict with url, signals, lastClick, eventCount or None
        """
        try:
            return await self._bridge.execute_script(GET_STATE_SCRIPT)
        except Exception:
            return None
    
    async def trigger_snapshot(self, note: str = "") -> bool:
        """
        Trigger a manual snapshot from Python.
        
        Args:
            note: Optional note for the snapshot
        
        Returns:
            True if triggered successfully
        """
        try:
            import json
            script = TRIGGER_SNAPSHOT_SCRIPT.replace("{note}", json.dumps(note))
            result = await self._bridge.execute_script(script)
            return result is True
        except Exception:
            return False
    
    async def get_signal_value(self, signal_id: str) -> any:
        """
        Get the current value of a signal.
        
        Args:
            signal_id: Signal ID (e.g., "sig_124" or "view_mode")
        
        Returns:
            Current signal value or None
        """
        script = f"""
        (function() {{
            if (window.__pynext__ && window.__pynext__.signals) {{
                const signal = window.__pynext__.signals[{repr(signal_id)}];
                if (signal) {{
                    return signal.read ? signal.read() : signal._value;
                }}
            }}
            return null;
        }})();
        """
        try:
            return await self._bridge.execute_script(script)
        except Exception:
            return None
    
    async def set_signal_value(self, signal_id: str, value: any) -> bool:
        """
        Set a signal value for testing.
        
        Args:
            signal_id: Signal ID
            value: New value (must be JSON-serializable)
        
        Returns:
            True if set successfully
        """
        import json
        script = f"""
        (function() {{
            if (window.__pynext__ && window.__pynext__.signals) {{
                const signal = window.__pynext__.signals[{repr(signal_id)}];
                if (signal && signal.set) {{
                    signal.set({json.dumps(value)});
                    return true;
                }}
            }}
            return false;
        }})();
        """
        try:
            result = await self._bridge.execute_script(script)
            return result is True
        except Exception:
            return False
    
    async def list_signals(self) -> list[dict]:
        """
        List all registered signals.
        
        Returns:
            List of signal info dicts
        """
        script = """
        (function() {
            const signals = [];
            if (window.__pynext__ && window.__pynext__.signals) {
                for (const [id, signal] of Object.entries(window.__pynext__.signals)) {
                    signals.push({
                        id: id,
                        name: signal._name || id,
                        value: signal.read ? signal.read() : signal._value,
                    });
                }
            }
            return signals;
        })();
        """
        try:
            return await self._bridge.execute_script(script) or []
        except Exception:
            return []
    
    async def wait_for_hydration(self, timeout: float = 10.0) -> bool:
        """
        Wait for PyNext hydration to complete.
        
        Args:
            timeout: Max seconds to wait
        
        Returns:
            True if hydrated within timeout
        """
        import asyncio
        
        check_script = """
        (function() {
            return window.__pynext__ && 
                   window.__pynext__.hydrated === true;
        })();
        """
        
        start = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start < timeout:
            try:
                result = await self._bridge.execute_script(check_script)
                if result is True:
                    return True
            except Exception:
                pass
            await asyncio.sleep(0.1)
        
        return False

