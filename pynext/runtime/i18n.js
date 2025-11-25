/**
 * PyNext i18n Client-Side Runtime
 * 
 * Provides:
 * - Lazy locale loading
 * - Direct DOM text updates (no re-render)
 * - Locale persistence
 * - Automatic detection
 * 
 * SolidJS Principles Applied:
 * - Fine-grained updates (only text nodes change)
 * - Lazy loading (load translations on demand)
 * - Minimal JavaScript
 */

(function() {
    'use strict';
    
    // Initialize __pynext__ if not exists
    window.__pynext__ = window.__pynext__ || {};
    
    /**
     * i18n module
     */
    const i18n = {
        // Current locale
        _locale: 'en',
        
        // Available locales
        _locales: ['en'],
        
        // Loaded translations: { locale: { key: value } }
        _translations: {},
        
        // Subscribers for locale changes
        _subscribers: [],
        
        // Loading promises
        _loading: {},
        
        // Configuration
        _config: {
            cookieName: 'PYNEXT_LOCALE',
            translationsPath: '/locales',
            fallbackLocale: 'en',
            detectLocale: true,
        },
        
        /**
         * Initialize i18n with server data
         */
        init(config) {
            if (config.locale) this._locale = config.locale;
            if (config.locales) this._locales = config.locales;
            if (config.translations) this._translations = config.translations;
            if (config.config) Object.assign(this._config, config.config);
            
            // Set html lang attribute
            document.documentElement.lang = this._locale;
            
            // Setup mutation observer for dynamic content
            this._setupMutationObserver();
        },
        
        /**
         * Get current locale
         */
        get locale() {
            return this._locale;
        },
        
        /**
         * Get available locales
         */
        get locales() {
            return this._locales;
        },
        
        /**
         * Set locale and update DOM
         */
        async setLocale(locale) {
            if (!this._locales.includes(locale)) {
                console.warn(`Unknown locale: ${locale}`);
                return false;
            }
            
            // Load translations if not loaded
            if (!this._translations[locale]) {
                await this.loadLocale(locale);
            }
            
            const oldLocale = this._locale;
            this._locale = locale;
            
            // Update DOM
            this._updateDOM();
            
            // Update html lang
            document.documentElement.lang = locale;
            
            // Persist to cookie
            this._setCookie(locale);
            
            // Notify subscribers
            this._notifySubscribers(locale, oldLocale);
            
            // Dispatch event
            window.dispatchEvent(new CustomEvent('pynext:locale-change', {
                detail: { locale, oldLocale }
            }));
            
            return true;
        },
        
        /**
         * Load translations for a locale
         */
        async loadLocale(locale, namespace = 'common') {
            const key = `${locale}:${namespace}`;
            
            // Return existing promise if loading
            if (this._loading[key]) {
                return this._loading[key];
            }
            
            // Return if already loaded
            if (this._translations[locale]) {
                return this._translations[locale];
            }
            
            // Start loading
            this._loading[key] = this._fetchTranslations(locale, namespace);
            
            try {
                const translations = await this._loading[key];
                
                if (!this._translations[locale]) {
                    this._translations[locale] = {};
                }
                Object.assign(this._translations[locale], translations);
                
                return translations;
            } finally {
                delete this._loading[key];
            }
        },
        
        /**
         * Fetch translations from server
         */
        async _fetchTranslations(locale, namespace) {
            const url = `${this._config.translationsPath}/${locale}/${namespace}.json`;
            
            try {
                const response = await fetch(url);
                if (!response.ok) {
                    throw new Error(`Failed to load ${url}`);
                }
                return await response.json();
            } catch (error) {
                console.warn(`Failed to load translations for ${locale}:`, error);
                return {};
            }
        },
        
        /**
         * Translate a key
         */
        t(key, params = null) {
            // Try current locale
            let value = this._translations[this._locale]?.[key];
            
            // Try fallback locale
            if (value === undefined && this._config.fallbackLocale) {
                value = this._translations[this._config.fallbackLocale]?.[key];
            }
            
            // Return key if not found
            if (value === undefined) {
                return key;
            }
            
            // Interpolate parameters
            if (params) {
                for (const [k, v] of Object.entries(params)) {
                    value = value.replace(new RegExp(`\\{${k}\\}`, 'g'), v);
                }
            }
            
            return value;
        },
        
        /**
         * Translate with plural support
         */
        tp(key, count, params = null) {
            const pluralKey = this._getPluralKey(key, count);
            return this.t(pluralKey, { ...params, count });
        },
        
        /**
         * Get plural form key
         */
        _getPluralKey(key, count) {
            if (count === 0) return `${key}.zero`;
            if (count === 1) return `${key}.one`;
            if (count === 2) return `${key}.two`;
            if (count > 2 && count < 5) return `${key}.few`;
            return `${key}.other`;
        },
        
        /**
         * Update all data-i18n elements in DOM
         */
        _updateDOM() {
            const elements = document.querySelectorAll('[data-i18n]');
            
            elements.forEach(el => {
                const key = el.dataset.i18n;
                const params = el.dataset.i18nParams 
                    ? JSON.parse(el.dataset.i18nParams) 
                    : null;
                
                // Direct text update - no re-render!
                el.textContent = this.t(key, params);
            });
            
            // Update data-i18n-attr elements (for attributes)
            const attrElements = document.querySelectorAll('[data-i18n-attr]');
            
            attrElements.forEach(el => {
                const config = JSON.parse(el.dataset.i18nAttr);
                for (const [attr, key] of Object.entries(config)) {
                    el.setAttribute(attr, this.t(key));
                }
            });
        },
        
        /**
         * Setup mutation observer for dynamic content
         */
        _setupMutationObserver() {
            const observer = new MutationObserver(mutations => {
                for (const mutation of mutations) {
                    for (const node of mutation.addedNodes) {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            this._processNewElement(node);
                        }
                    }
                }
            });
            
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        },
        
        /**
         * Process newly added element for i18n
         */
        _processNewElement(element) {
            // Check the element itself
            if (element.dataset?.i18n) {
                const key = element.dataset.i18n;
                const params = element.dataset.i18nParams 
                    ? JSON.parse(element.dataset.i18nParams) 
                    : null;
                element.textContent = this.t(key, params);
            }
            
            // Check descendants
            const descendants = element.querySelectorAll('[data-i18n]');
            descendants.forEach(el => {
                const key = el.dataset.i18n;
                const params = el.dataset.i18nParams 
                    ? JSON.parse(el.dataset.i18nParams) 
                    : null;
                el.textContent = this.t(key, params);
            });
        },
        
        /**
         * Subscribe to locale changes
         */
        subscribe(callback) {
            this._subscribers.push(callback);
            
            // Return unsubscribe function
            return () => {
                const index = this._subscribers.indexOf(callback);
                if (index > -1) {
                    this._subscribers.splice(index, 1);
                }
            };
        },
        
        /**
         * Notify subscribers of locale change
         */
        _notifySubscribers(newLocale, oldLocale) {
            for (const callback of this._subscribers) {
                try {
                    callback(newLocale, oldLocale);
                } catch (error) {
                    console.error('Error in locale change subscriber:', error);
                }
            }
        },
        
        /**
         * Set locale cookie
         */
        _setCookie(locale) {
            document.cookie = `${this._config.cookieName}=${locale}; path=/; max-age=31536000; SameSite=Lax`;
        },
        
        /**
         * Get locale from cookie
         */
        _getCookie() {
            const match = document.cookie.match(
                new RegExp(`${this._config.cookieName}=([^;]+)`)
            );
            return match ? match[1] : null;
        },
        
        /**
         * Detect user's preferred locale
         */
        detectLocale() {
            // Check cookie first
            const cookieLocale = this._getCookie();
            if (cookieLocale && this._locales.includes(cookieLocale)) {
                return cookieLocale;
            }
            
            // Check navigator.language
            const browserLocale = navigator.language?.split('-')[0];
            if (browserLocale && this._locales.includes(browserLocale)) {
                return browserLocale;
            }
            
            // Return default
            return this._config.fallbackLocale || this._locales[0];
        }
    };
    
    // Expose on window.__pynext__
    window.__pynext__.i18n = i18n;
    
    // Also expose globally for convenience
    window.t = (key, params) => i18n.t(key, params);
    window.setLocale = (locale) => i18n.setLocale(locale);
    
})();

