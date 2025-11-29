/**
 * PyNext Dev Reload Client
 * 
 * Handles hot reloading during development.
 * Injected automatically by the dev server.
 * 
 * Features:
 * - WebSocket connection to dev server
 * - CSS hot swapping (instant, no flash)
 * - Hot reload (DOM diffing without full refresh)
 * - Full reload fallback
 * - Automatic reconnection
 * 
 * Size: ~2KB minified
 * 
 * @module pynext/dev-reload
 */

(function() {
  'use strict';
  
  // ============================================
  // Configuration
  // ============================================
  
  const CONFIG = {
    wsUrl: 'ws://' + location.host + '/__pynext/ws',
    reconnectDelay: 1000,
    maxReconnectAttempts: 10,
    heartbeatInterval: 30000,
  };
  
  // ============================================
  // State
  // ============================================
  
  let ws = null;
  let reconnectTimer = null;
  let heartbeatTimer = null;
  let reconnectAttempts = 0;
  
  // ============================================
  // Connection Overlay
  // ============================================
  
  /**
   * Show connection status overlay.
   * @param {string} message - Message to display
   * @param {string} type - 'info' | 'error' | 'success'
   */
  function showOverlay(message, type) {
    type = type || 'info';
    
    let overlay = document.getElementById('__pynext_dev_overlay');
    
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.id = '__pynext_dev_overlay';
      overlay.style.cssText = [
        'position: fixed',
        'top: 0',
        'left: 0',
        'right: 0',
        'padding: 10px 20px',
        'font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace',
        'font-size: 13px',
        'z-index: 999999',
        'text-align: center',
        'transition: background-color 0.2s',
      ].join(';');
      document.body.appendChild(overlay);
    }
    
    // Style based on type
    const styles = {
      info: { bg: '#1e293b', color: '#f1f5f9' },
      error: { bg: '#dc2626', color: '#ffffff' },
      success: { bg: '#16a34a', color: '#ffffff' },
    };
    
    const style = styles[type] || styles.info;
    overlay.style.backgroundColor = style.bg;
    overlay.style.color = style.color;
    overlay.textContent = message;
    overlay.style.display = 'block';
  }
  
  /**
   * Hide connection status overlay.
   */
  function hideOverlay() {
    const overlay = document.getElementById('__pynext_dev_overlay');
    if (overlay) {
      overlay.style.display = 'none';
    }
  }
  
  // ============================================
  // WebSocket Connection
  // ============================================
  
  /**
   * Connect to dev server via WebSocket.
   */
  function connect() {
    // Don't create multiple connections
    if (ws && ws.readyState === WebSocket.OPEN) {
      return;
    }
    
    // Clean up existing connection
    if (ws) {
      ws.close();
    }
    
    ws = new WebSocket(CONFIG.wsUrl);
    
    ws.onopen = function() {
      console.log('[PyNext] Dev mode active');
      reconnectAttempts = 0;
      hideOverlay();
      
      // Start heartbeat
      if (heartbeatTimer) clearInterval(heartbeatTimer);
      heartbeatTimer = setInterval(sendHeartbeat, CONFIG.heartbeatInterval);
    };
    
    ws.onmessage = function(event) {
      try {
        const data = JSON.parse(event.data);
        handleMessage(data);
      } catch (err) {
        console.error('[PyNext] Invalid message:', err);
      }
    };
    
    ws.onclose = function() {
      console.log('[PyNext] Connection closed');
      
      // Clear heartbeat
      if (heartbeatTimer) {
        clearInterval(heartbeatTimer);
        heartbeatTimer = null;
      }
      
      // Attempt reconnection
      if (reconnectAttempts < CONFIG.maxReconnectAttempts) {
        reconnectAttempts++;
        showOverlay(
          '[PyNext] Reconnecting... (' + reconnectAttempts + '/' + CONFIG.maxReconnectAttempts + ')',
          'info'
        );
        reconnectTimer = setTimeout(connect, CONFIG.reconnectDelay);
      } else {
        showOverlay('[PyNext] Connection lost. Refresh to reconnect.', 'error');
      }
    };
    
    ws.onerror = function(err) {
      console.error('[PyNext] WebSocket error:', err);
      ws.close();
    };
  }
  
  /**
   * Send heartbeat to keep connection alive.
   */
  function sendHeartbeat() {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'ping' }));
    }
  }
  
  // ============================================
  // Message Handling
  // ============================================
  
  /**
   * Handle incoming WebSocket message.
   * @param {Object} data - Parsed message data
   */
  function handleMessage(data) {
    // Handle pong (heartbeat response)
    if (data.type === 'pong') {
      return;
    }
    
    // Handle reload
    if (data.type === 'reload') {
      handleReload(data);
      return;
    }
    
    // Unknown message type
    console.log('[PyNext] Unknown message:', data);
  }
  
  /**
   * Handle reload message.
   * @param {Object} data - Reload message data
   */
  function handleReload(data) {
    console.log('[PyNext] ' + data.reload_type + ' reload: ' + data.path);
    
    const start = performance.now();
    
    switch (data.reload_type) {
      case 'css':
        reloadCSS();
        logTiming(start);
        break;
        
      case 'hot':
        hotReload().then(function() {
          logTiming(start);
        });
        break;
        
      case 'none':
        // No visual reload needed (e.g., API changes)
        console.log('[PyNext] Change detected (no reload needed)');
        break;
        
      case 'full':
      default:
        fullReload();
        // No timing log - page will refresh
    }
  }
  
  /**
   * Log reload timing.
   * @param {number} start - Start timestamp from performance.now()
   */
  function logTiming(start) {
    const elapsed = performance.now() - start;
    console.log('[PyNext] Reload completed in ' + elapsed.toFixed(1) + 'ms');
  }
  
  // ============================================
  // Reload Strategies
  // ============================================
  
  /**
   * CSS hot swap - instant stylesheet reload.
   * Updates all stylesheets without page flash.
   */
  function reloadCSS() {
    // Reload linked stylesheets
    const links = document.querySelectorAll('link[rel="stylesheet"]');
    links.forEach(function(link) {
      if (!link.href) return;
      
      const url = new URL(link.href);
      url.searchParams.set('_pynext_t', Date.now());
      link.href = url.toString();
    });
    
    // Reload inline styles with file reference
    const styles = document.querySelectorAll('style[data-pynext-file]');
    styles.forEach(function(style) {
      const file = style.getAttribute('data-pynext-file');
      if (!file) return;
      
      fetch(file + '?_t=' + Date.now())
        .then(function(r) { return r.text(); })
        .then(function(css) { style.textContent = css; })
        .catch(function(err) {
          console.error('[PyNext] Failed to reload style:', err);
        });
    });
    
    // Dispatch event
    window.dispatchEvent(new CustomEvent('pynext:reload', {
      detail: { type: 'css' }
    }));
  }
  
  /**
   * Hot reload - swap page content without full refresh.
   * Preserves JavaScript state, scroll position, form inputs.
   * @returns {Promise}
   */
  function hotReload() {
    return fetch(location.href, {
      cache: 'no-store',
      headers: {
        'X-PyNext-Hot-Reload': '1',
        'Cache-Control': 'no-cache',
      }
    })
    .then(function(response) {
      if (!response.ok) {
        throw new Error('Failed to fetch: ' + response.status);
      }
      return response.text();
    })
    .then(function(html) {
      const parser = new DOMParser();
      const newDoc = parser.parseFromString(html, 'text/html');
      
      // Swap body content
      if (window.morphdom) {
        // Use morphdom for minimal DOM changes
        morphdom(document.body, newDoc.body, {
          onBeforeElUpdated: function(fromEl, toEl) {
            // Preserve focus state
            if (fromEl === document.activeElement) {
              setTimeout(function() { toEl.focus(); }, 0);
            }
            // Preserve form values
            if (fromEl.tagName === 'INPUT' || fromEl.tagName === 'TEXTAREA') {
              if (fromEl.value !== fromEl.defaultValue) {
                toEl.value = fromEl.value;
              }
            }
            return true;
          }
        });
      } else {
        // Fallback: simple innerHTML swap
        document.body.innerHTML = newDoc.body.innerHTML;
      }
      
      // Update document title
      if (newDoc.title && newDoc.title !== document.title) {
        document.title = newDoc.title;
      }
      
      // Re-initialize PyNext runtime
      if (window.__pynext__ && typeof window.__pynext__.init === 'function') {
        window.__pynext__.init();
      }
      
      // Dispatch event
      window.dispatchEvent(new CustomEvent('pynext:reload', {
        detail: { type: 'hot' }
      }));
    })
    .catch(function(err) {
      console.error('[PyNext] Hot reload failed:', err);
      console.log('[PyNext] Falling back to full reload');
      fullReload();
    });
  }
  
  /**
   * Full page reload.
   */
  function fullReload() {
    location.reload();
  }
  
  // ============================================
  // Public API
  // ============================================
  
  /**
   * Expose dev utilities for debugging.
   */
  window.__pynext_dev__ = {
    // Manual reload triggers
    reload: fullReload,
    hotReload: hotReload,
    reloadCSS: reloadCSS,
    
    // Connection control
    reconnect: connect,
    disconnect: function() {
      if (ws) ws.close();
    },
    
    // Status
    isConnected: function() {
      return ws && ws.readyState === WebSocket.OPEN;
    },
    
    // Config
    config: CONFIG,
  };
  
  // ============================================
  // Initialize
  // ============================================
  
  // Connect when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', connect);
  } else {
    connect();
  }
  
})();

