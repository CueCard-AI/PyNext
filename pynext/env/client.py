"""
Client-side environment variable exposure.

Two approaches available:
1. Build-time inlining (default) - Zero runtime cost
2. Runtime injection - More flexible, tiny cost

Only PYNEXT_PUBLIC_* vars are exposed to client.

SolidJS Principle: Build-time when possible, explicit when not
AI-Friendly: Clear prefix, predictable behavior

Example:
    # In Python
    PYNEXT_PUBLIC_API_URL=https://api.example.com
    
    # In Browser (build-time)
    window.__PYNEXT_ENV__.API_URL  // "https://api.example.com"
    
    # Or using helper
    pynext.env.get('API_URL')  // "https://api.example.com"
"""

from typing import Dict
import json
import re


def get_public_vars(env_vars: Dict[str, str]) -> Dict[str, str]:
    """
    Extract PYNEXT_PUBLIC_* vars for client exposure.
    
    Strips the prefix for cleaner client access:
        PYNEXT_PUBLIC_API_URL -> API_URL
    
    Args:
        env_vars: Dict of all environment variables
    
    Returns:
        Dict of public vars with prefix stripped
    
    Example:
        vars = {
            "DATABASE_URL": "postgres://...",  # Private - excluded
            "PYNEXT_PUBLIC_API_URL": "https://api.example.com",
            "PYNEXT_PUBLIC_APP_NAME": "My App",
        }
        
        public = get_public_vars(vars)
        # Returns: {"API_URL": "https://api.example.com", "APP_NAME": "My App"}
    """
    return {
        k.replace("PYNEXT_PUBLIC_", ""): v
        for k, v in env_vars.items()
        if k.startswith("PYNEXT_PUBLIC_")
    }


def generate_inline_script(public_vars: Dict[str, str]) -> str:
    """
    Generate inline script for build-time injection.
    
    Used in HTML head - vars available immediately with zero runtime cost.
    
    Args:
        public_vars: Dict of public vars (already stripped of prefix)
    
    Returns:
        Script tag string to inject in HTML head
    
    Example:
        script = generate_inline_script({"API_URL": "https://api.example.com"})
        # Returns: <script>window.__PYNEXT_ENV__={"API_URL":"https://api.example.com"}</script>
    
    Benefits:
        - Zero runtime cost (no fetch, no async)
        - Available immediately on page load
        - Works without JavaScript enabled (values in HTML)
    """
    if not public_vars:
        return '<script>window.__PYNEXT_ENV__={}</script>'
    
    # Escape for safe HTML embedding
    json_str = json.dumps(public_vars, separators=(',', ':'))
    
    return f'<script>window.__PYNEXT_ENV__={json_str}</script>'


def generate_runtime_script() -> str:
    """
    Generate runtime loader script.
    
    Fetches vars from /_pynext/env.json endpoint.
    Used when vars might change without rebuild.
    
    Returns:
        Script tag string that fetches env vars at runtime
    
    Example:
        script = generate_runtime_script()
        # Inserts script that fetches /_pynext/env.json
    
    When to use:
        - Environment vars change frequently
        - Different values per deployment without rebuild
        - Dynamic configuration
    
    Trade-offs:
        - Small runtime cost (~1-5ms fetch)
        - Vars may not be immediately available
        - Requires JavaScript enabled
    """
    return '''<script>
(function(){
    'use strict';
    window.__PYNEXT_ENV__ = window.__PYNEXT_ENV__ || {};
    fetch('/_pynext/env.json')
        .then(function(r) { return r.json(); })
        .then(function(e) { window.__PYNEXT_ENV__ = e; })
        .catch(function() { /* Keep empty default */ });
})();
</script>'''


def inline_env_in_js(js_content: str, public_vars: Dict[str, str]) -> str:
    """
    Replace process.env.VAR references in JS with actual values.
    
    This is the build-time replacement approach.
    
    Args:
        js_content: JavaScript source code
        public_vars: Dict of public vars (already stripped of prefix)
    
    Returns:
        JavaScript with env references replaced by values
    
    Example:
        js = "const api = process.env.API_URL;"
        result = inline_env_in_js(js, {"API_URL": "https://api.example.com"})
        # Returns: 'const api = "https://api.example.com";'
    
    Replaces:
        process.env.KEY -> "value"
        import.meta.env.KEY -> "value"
    """
    for key, value in public_vars.items():
        # JSON encode the value for safe JS string
        json_value = json.dumps(value)
        
        # Replace process.env.KEY
        js_content = re.sub(
            rf'\bprocess\.env\.{re.escape(key)}\b',
            json_value,
            js_content
        )
        
        # Replace import.meta.env.KEY
        js_content = re.sub(
            rf'\bimport\.meta\.env\.{re.escape(key)}\b',
            json_value,
            js_content
        )
        
        # Replace window.__PYNEXT_ENV__.KEY
        js_content = re.sub(
            rf'\bwindow\.__PYNEXT_ENV__\.{re.escape(key)}\b',
            json_value,
            js_content
        )
    
    return js_content


def get_client_env_accessor() -> str:
    """
    Generate the client-side env accessor JavaScript.
    
    Provides type-safe access in browser:
        pynext.env.API_URL
        pynext.env.get('API_URL', 'default')
        pynext.env.has('API_URL')
    
    Returns:
        JavaScript code to include in page
    
    Example:
        accessor_js = get_client_env_accessor()
        # Include in page, then use:
        # pynext.env.API_URL
        # pynext.env.get('API_URL', 'fallback')
    """
    return '''
(function(g) {
    'use strict';
    
    g.__pynext__ = g.__pynext__ || {};
    
    /**
     * Client-side environment variable accessor.
     * 
     * Usage:
     *   pynext.env.API_URL           // Direct access
     *   pynext.env.get('KEY', 'default')  // With fallback
     *   pynext.env.has('KEY')        // Check existence
     *   pynext.env.all()             // Get all vars
     */
    var envAccessor = {
        /**
         * Get an environment variable with optional default.
         * @param {string} key - Variable name (without PYNEXT_PUBLIC_ prefix)
         * @param {*} defaultValue - Default if not set
         * @returns {*} Value or default
         */
        get: function(key, defaultValue) {
            var env = g.__PYNEXT_ENV__ || {};
            return env[key] !== undefined ? env[key] : defaultValue;
        },
        
        /**
         * Check if an environment variable exists.
         * @param {string} key - Variable name
         * @returns {boolean} True if set
         */
        has: function(key) {
            return (g.__PYNEXT_ENV__ || {})[key] !== undefined;
        },
        
        /**
         * Get all environment variables.
         * @returns {Object} Copy of all env vars
         */
        all: function() {
            return Object.assign({}, g.__PYNEXT_ENV__ || {});
        },
        
        /**
         * Get multiple environment variables.
         * @param {string[]} keys - Array of variable names
         * @returns {Object} Object with requested vars
         */
        pick: function(keys) {
            var env = g.__PYNEXT_ENV__ || {};
            var result = {};
            for (var i = 0; i < keys.length; i++) {
                var key = keys[i];
                if (env[key] !== undefined) {
                    result[key] = env[key];
                }
            }
            return result;
        }
    };
    
    // Use Proxy for direct property access if available
    if (typeof Proxy !== 'undefined') {
        g.__pynext__.env = new Proxy(envAccessor, {
            get: function(target, prop) {
                // Return methods as-is
                if (typeof target[prop] === 'function') {
                    return target[prop];
                }
                // Property access -> get value
                return target.get(prop);
            }
        });
    } else {
        // Fallback for older browsers
        g.__pynext__.env = envAccessor;
    }
    
})(typeof window !== 'undefined' ? window : this);
'''


def validate_public_var_name(name: str) -> bool:
    """
    Validate that a variable name is safe for client exposure.
    
    Args:
        name: Variable name (with or without prefix)
    
    Returns:
        True if valid for client exposure
    """
    # Remove prefix if present
    if name.startswith("PYNEXT_PUBLIC_"):
        name = name[14:]
    
    # Must be valid JS identifier
    return bool(re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', name))


def get_env_injection_point() -> str:
    """
    Get the recommended injection point comment for HTML templates.
    
    Returns:
        HTML comment to mark injection point
    """
    return "<!-- PYNEXT_ENV_INJECTION_POINT -->"


def inject_env_into_html(
    html: str,
    public_vars: Dict[str, str],
    mode: str = "inline",
) -> str:
    """
    Inject environment variables into HTML.
    
    Args:
        html: HTML content
        public_vars: Dict of public vars
        mode: "inline" for build-time or "runtime" for fetch-based
    
    Returns:
        HTML with env script injected
    """
    if mode == "runtime":
        script = generate_runtime_script()
    else:
        script = generate_inline_script(public_vars)
    
    # Try to inject after <head> or before </head>
    injection_point = get_env_injection_point()
    
    if injection_point in html:
        return html.replace(injection_point, script)
    elif "<head>" in html:
        return html.replace("<head>", f"<head>\n    {script}")
    elif "</head>" in html:
        return html.replace("</head>", f"    {script}\n</head>")
    else:
        # Prepend to document
        return script + "\n" + html

