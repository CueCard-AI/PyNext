/**
 * PyNext React Bridge
 * 
 * Provides seamless integration between PyNext signals and React components
 * rendered via Preact for optimal performance.
 */

(function(global) {
    'use strict';

    // Check if Preact is available
    let preact = null;
    let preactHooks = null;

    /**
     * Initialize the React bridge with Preact
     */
    async function initReactBridge() {
        // Try to load Preact from the bundled runtime
        try {
            const preactModule = await import('/_pynext/npm/preact-runtime.bundle.js');
            preact = preactModule;
            preactHooks = preactModule;
            console.log('[PyNext] React bridge initialized with Preact');
            return true;
        } catch (e) {
            console.warn('[PyNext] Preact not loaded - React components disabled:', e);
            return false;
        }
    }

    /**
     * Create a wrapper component that subscribes to PyNext signals
     */
    function createSignalWrapper(Component, signalBindings, callbackBindings, staticProps) {
        return function SignalWrapper(props) {
            const [, forceUpdate] = preactHooks.useState({});
            
            // Subscribe to all bound signals
            preactHooks.useEffect(() => {
                const unsubscribes = [];
                
                for (const [propName, signalId] of Object.entries(signalBindings)) {
                    const signal = __pynext__.getSignal(signalId);
                    if (signal) {
                        const unsub = signal.subscribe(() => {
                            forceUpdate({});
                        });
                        unsubscribes.push(unsub);
                    }
                }
                
                return () => {
                    unsubscribes.forEach(fn => fn());
                };
            }, []);
            
            // Build current props from signals
            const currentProps = { ...staticProps };
            
            // Add signal values as props
            for (const [propName, signalId] of Object.entries(signalBindings)) {
                const signal = __pynext__.getSignal(signalId);
                if (signal) {
                    currentProps[propName] = signal.read();
                }
            }
            
            // Add callback bindings
            for (const [propName, callbackCode] of Object.entries(callbackBindings)) {
                currentProps[propName] = (value) => {
                    // Handle different callback patterns
                    if (callbackCode.includes('.set')) {
                        const signalId = callbackCode.match(/'([^']+)'/)?.[1];
                        const signal = __pynext__.getSignal(signalId);
                        if (signal) {
                            // Handle event objects (e.g., from MUI)
                            const actualValue = value?.target?.value ?? value?.target?.checked ?? value;
                            signal.write(actualValue);
                        }
                    } else if (callbackCode.includes('.update')) {
                        const signalId = callbackCode.match(/'([^']+)'/)?.[1];
                        const signal = __pynext__.getSignal(signalId);
                        if (signal) {
                            signal.update(v => value);
                        }
                    }
                };
            }
            
            // Merge with passed props
            const finalProps = { ...currentProps, ...props };
            
            return preact.createElement(Component, finalProps);
        };
    }

    /**
     * Mount a React component into a container
     */
    async function mountReact(elementId, packageName, componentName, props, signalBindings, callbackBindings) {
        if (!preact) {
            const initialized = await initReactBridge();
            if (!initialized) return null;
        }

        const container = document.getElementById(elementId);
        if (!container) {
            console.error(`[PyNext] Container not found: ${elementId}`);
            return null;
        }

        try {
            // Dynamically import the package
            const safeName = packageName.replace(/\//g, '_').replace(/@/g, '').replace(/-/g, '_');
            const moduleUrl = `/_pynext/npm/${safeName}.bundle.js`;
            const module = await import(moduleUrl);
            
            // Get the component
            const Component = module[componentName] || module.default?.[componentName];
            if (!Component) {
                console.error(`[PyNext] Component not found: ${componentName} in ${packageName}`);
                return null;
            }

            // Create wrapper if there are signal bindings
            let RenderComponent = Component;
            if (Object.keys(signalBindings).length > 0 || Object.keys(callbackBindings).length > 0) {
                RenderComponent = createSignalWrapper(Component, signalBindings, callbackBindings, props);
            }

            // Get children if any
            const children = container.innerHTML.trim() 
                ? preact.createElement('div', { 
                    dangerouslySetInnerHTML: { __html: container.innerHTML }
                  })
                : null;

            // Render the component
            const element = preact.createElement(RenderComponent, props, children);
            preact.render(element, container);

            console.log(`[PyNext] Mounted React component: ${componentName}`);
            return { container, Component: RenderComponent };
        } catch (e) {
            console.error(`[PyNext] Failed to mount React component:`, e);
            return null;
        }
    }

    /**
     * Hydrate all React components on the page
     */
    async function hydrateReact() {
        if (!preact) {
            const initialized = await initReactBridge();
            if (!initialized) {
                console.log('[PyNext] Skipping React hydration - Preact not available');
                return;
            }
        }

        // Find all React component placeholders
        const components = document.querySelectorAll('[data-react-component]');
        console.log(`[PyNext] Found ${components.length} React components to hydrate`);

        // Get hydration data from window
        const hydrationData = window.__PYNEXT_HYDRATION__?.reactComponents || [];
        
        for (const container of components) {
            const elementId = container.id;
            const packageName = container.dataset.reactPackage;
            const componentName = container.dataset.reactComponent;
            
            // Parse props from data attribute
            let props = {};
            try {
                props = JSON.parse(container.dataset.reactProps || '{}');
            } catch (e) {
                console.warn(`[PyNext] Failed to parse props for ${elementId}`);
            }

            // Find signal/callback bindings from hydration data
            const componentData = hydrationData.find(c => c.id === elementId) || {};
            const signalBindings = componentData.signalBindings || {};
            const callbackBindings = componentData.callbackBindings || {};

            await mountReact(elementId, packageName, componentName, props, signalBindings, callbackBindings);
        }

        // Handle React islands
        const islands = document.querySelectorAll('[data-react-island]');
        for (const island of islands) {
            console.log(`[PyNext] Hydrating React island: ${island.id}`);
            // Islands are handled by hydrating their children
        }
    }

    /**
     * Unmount a React component
     */
    function unmountReact(elementId) {
        if (!preact) return;
        
        const container = document.getElementById(elementId);
        if (container) {
            preact.render(null, container);
        }
    }

    // ============================================
    // Extend PyNext global
    // ============================================

    const reactBridge = {
        init: initReactBridge,
        mount: mountReact,
        hydrate: hydrateReact,
        unmount: unmountReact,
        isReady: () => preact !== null,
    };

    // Add to global __pynext__ object
    if (global.__pynext__) {
        global.__pynext__.react = reactBridge;
    } else {
        // If main runtime not loaded yet, queue it
        global.__pynext_react_bridge__ = reactBridge;
    }

})(typeof window !== 'undefined' ? window : global);

