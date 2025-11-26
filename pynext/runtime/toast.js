/**
 * PyNext Toast Runtime
 * 
 * Client-side JavaScript for toast notifications.
 * Handles showing, stacking, auto-dismiss, and animations.
 */

(function(global) {
    'use strict';

    const toasts = new Map(); // id -> { element, timer }
    let toasterElement = null;
    let toasterConfig = {
        position: 'bottom-right',
        maxVisible: 3,
        duration: 4000,
        closeButton: true,
        richColors: true,
        expand: true
    };

    // Toast variant styles (used when richColors is true)
    const VARIANT_CLASSES = {
        default: '',
        success: 'border-green-500 bg-green-50 dark:bg-green-950',
        error: 'border-red-500 bg-red-50 dark:bg-red-950',
        warning: 'border-yellow-500 bg-yellow-50 dark:bg-yellow-950',
        info: 'border-blue-500 bg-blue-50 dark:bg-blue-950'
    };

    // Icons for each variant
    const VARIANT_ICONS = {
        success: `<svg class="h-5 w-5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
        </svg>`,
        error: `<svg class="h-5 w-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
        </svg>`,
        warning: `<svg class="h-5 w-5 text-yellow-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
        </svg>`,
        info: `<svg class="h-5 w-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>`
    };

    /**
     * Initialize the toaster from the DOM element
     */
    function init() {
        toasterElement = document.querySelector('[data-pynext-toaster]');
        if (!toasterElement) return;

        // Read config from data attributes
        const dataset = toasterElement.dataset;
        toasterConfig = {
            position: dataset.position || 'bottom-right',
            maxVisible: parseInt(dataset.maxVisible) || 3,
            duration: parseInt(dataset.duration) || 4000,
            closeButton: dataset.closeButton !== 'false',
            richColors: dataset.richColors !== 'false',
            expand: dataset.expand !== 'false'
        };

        // Set up event delegation for close buttons
        toasterElement.addEventListener('click', (e) => {
            const closeBtn = e.target.closest('[data-pynext-toast-close]');
            if (closeBtn) {
                const toast = closeBtn.closest('[data-pynext-toast]');
                if (toast) {
                    dismiss(toast.dataset.pynextToast);
                }
            }

            const actionBtn = e.target.closest('[data-pynext-toast-action]');
            if (actionBtn) {
                const toast = actionBtn.closest('[data-pynext-toast]');
                if (toast) {
                    const id = toast.dataset.pynextToast;
                    const toastData = toasts.get(id);
                    if (toastData && toastData.onAction) {
                        toastData.onAction();
                    }
                    dismiss(id);
                }
            }
        });

        // Pause timers on hover
        if (toasterConfig.expand) {
            toasterElement.addEventListener('mouseenter', pauseAllTimers);
            toasterElement.addEventListener('mouseleave', resumeAllTimers);
        }
    }

    /**
     * Show a toast notification
     */
    function show(options) {
        if (!toasterElement) {
            console.warn('PyNext Toast: No Toaster element found. Add <Toaster /> to your layout.');
            return null;
        }

        const id = options.id || generateId();
        const message = options.message || '';
        const description = options.description || null;
        const variant = options.variant || 'default';
        const duration = options.duration !== undefined ? options.duration : toasterConfig.duration;
        const action = options.action || null;

        // Build toast HTML
        const toastHtml = buildToastHtml(id, message, description, variant, action);

        // Insert toast
        const wrapper = document.createElement('div');
        wrapper.innerHTML = toastHtml;
        const toastElement = wrapper.firstElementChild;

        // Determine insertion position based on toaster position
        if (toasterConfig.position.startsWith('top')) {
            toasterElement.appendChild(toastElement);
        } else {
            toasterElement.insertBefore(toastElement, toasterElement.firstChild);
        }

        // Set up auto-dismiss timer
        let timer = null;
        if (duration > 0) {
            timer = setTimeout(() => dismiss(id), duration);
        }

        // Store toast data
        toasts.set(id, {
            element: toastElement,
            timer,
            duration,
            remaining: duration,
            pausedAt: null,
            onAction: action?.callback
        });

        // Enforce max visible
        enforceMaxVisible();

        return id;
    }

    /**
     * Build the HTML for a toast
     */
    function buildToastHtml(id, message, description, variant, action) {
        const variantClass = toasterConfig.richColors ? (VARIANT_CLASSES[variant] || '') : '';
        const baseClass = `relative flex items-center justify-between w-full max-w-md p-4 
            bg-background border rounded-lg shadow-lg pointer-events-auto 
            animate-in slide-in-from-top-full fade-in-0 ${variantClass}`;

        const icon = VARIANT_ICONS[variant] || '';
        const iconHtml = icon ? `<div class="flex-shrink-0 mr-3">${icon}</div>` : '';

        const descriptionHtml = description 
            ? `<p class="text-sm text-muted-foreground mt-1">${escapeHtml(description)}</p>` 
            : '';

        const actionHtml = action 
            ? `<button data-pynext-toast-action class="ml-4 text-sm font-medium underline hover:no-underline">${escapeHtml(action.label)}</button>` 
            : '';

        const closeHtml = toasterConfig.closeButton 
            ? `<button data-pynext-toast-close class="ml-4 text-muted-foreground hover:text-foreground" aria-label="Close">
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
            </button>` 
            : '';

        return `
<div data-pynext-toast="${id}"
     data-variant="${variant}"
     class="${baseClass}"
     role="alert"
     aria-live="polite">
    ${iconHtml}
    <div class="flex-1">
        <p class="text-sm font-medium">${escapeHtml(message)}</p>
        ${descriptionHtml}
    </div>
    ${actionHtml}
    ${closeHtml}
</div>`;
    }

    /**
     * Dismiss a toast by ID
     */
    function dismiss(id) {
        const toastData = toasts.get(id);
        if (!toastData) return;

        const { element, timer } = toastData;

        // Clear timer
        if (timer) clearTimeout(timer);

        // Animate out
        element.classList.add('animate-out', 'fade-out-0', 'slide-out-to-right-full');
        
        // Remove after animation
        setTimeout(() => {
            element.remove();
            toasts.delete(id);
        }, 150);
    }

    /**
     * Dismiss all toasts
     */
    function dismissAll() {
        for (const id of toasts.keys()) {
            dismiss(id);
        }
    }

    /**
     * Pause all auto-dismiss timers
     */
    function pauseAllTimers() {
        for (const [id, data] of toasts) {
            if (data.timer) {
                clearTimeout(data.timer);
                data.timer = null;
                data.pausedAt = Date.now();
            }
        }
    }

    /**
     * Resume all paused timers
     */
    function resumeAllTimers() {
        for (const [id, data] of toasts) {
            if (data.pausedAt && data.remaining > 0) {
                // Calculate remaining time
                const elapsed = data.pausedAt - (Date.now() - data.remaining);
                const remaining = Math.max(data.remaining - (Date.now() - data.pausedAt), 0);
                
                if (remaining > 0) {
                    data.timer = setTimeout(() => dismiss(id), remaining);
                    data.remaining = remaining;
                }
                data.pausedAt = null;
            }
        }
    }

    /**
     * Enforce maximum visible toasts
     */
    function enforceMaxVisible() {
        const allToasts = Array.from(toasts.keys());
        const excess = allToasts.length - toasterConfig.maxVisible;
        
        if (excess > 0) {
            // Remove oldest toasts (first in the list)
            const toRemove = toasterConfig.position.startsWith('top') 
                ? allToasts.slice(0, excess)
                : allToasts.slice(-excess);
            
            for (const id of toRemove) {
                dismiss(id);
            }
        }
    }

    /**
     * Update a toast's content (for promise toasts)
     */
    function update(id, options) {
        const toastData = toasts.get(id);
        if (!toastData) return;

        const { element } = toastData;
        
        if (options.message) {
            const messageEl = element.querySelector('.text-sm.font-medium');
            if (messageEl) messageEl.textContent = options.message;
        }
        
        if (options.description !== undefined) {
            let descEl = element.querySelector('.text-muted-foreground');
            if (options.description) {
                if (descEl) {
                    descEl.textContent = options.description;
                } else {
                    const contentDiv = element.querySelector('.flex-1');
                    contentDiv.insertAdjacentHTML('beforeend', 
                        `<p class="text-sm text-muted-foreground mt-1">${escapeHtml(options.description)}</p>`
                    );
                }
            } else if (descEl) {
                descEl.remove();
            }
        }

        if (options.variant) {
            // Update variant classes
            const variantClass = VARIANT_CLASSES[options.variant] || '';
            element.dataset.variant = options.variant;
            // Remove old variant classes and add new
            Object.values(VARIANT_CLASSES).forEach(cls => {
                cls.split(' ').forEach(c => c && element.classList.remove(c));
            });
            variantClass.split(' ').forEach(c => c && element.classList.add(c));

            // Update icon
            const iconContainer = element.querySelector('.flex-shrink-0');
            if (iconContainer && VARIANT_ICONS[options.variant]) {
                iconContainer.innerHTML = VARIANT_ICONS[options.variant];
            }
        }
    }

    // Utility functions
    function generateId() {
        return 'toast_' + Math.random().toString(36).substr(2, 9);
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Expose API
    global.PyNextToast = {
        show,
        dismiss,
        dismissAll,
        update,
        
        // Convenience methods
        success: (message, options = {}) => show({ ...options, message, variant: 'success' }),
        error: (message, options = {}) => show({ ...options, message, variant: 'error' }),
        warning: (message, options = {}) => show({ ...options, message, variant: 'warning' }),
        info: (message, options = {}) => show({ ...options, message, variant: 'info' }),
        
        // Promise helper
        promise: async (promise, options = {}) => {
            const id = show({
                message: options.loading || 'Loading...',
                variant: 'default',
                duration: 0 // Don't auto-dismiss
            });

            try {
                const result = await promise;
                update(id, {
                    message: typeof options.success === 'function' 
                        ? options.success(result) 
                        : (options.success || 'Success'),
                    variant: 'success'
                });
                // Start dismiss timer
                setTimeout(() => dismiss(id), toasterConfig.duration);
                return result;
            } catch (error) {
                update(id, {
                    message: typeof options.error === 'function'
                        ? options.error(error)
                        : (options.error || 'Error'),
                    variant: 'error'
                });
                // Start dismiss timer
                setTimeout(() => dismiss(id), toasterConfig.duration);
                throw error;
            }
        }
    };

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Re-init on navigation
    document.addEventListener('turbo:load', init);
    document.addEventListener('htmx:afterSettle', init);

})(typeof window !== 'undefined' ? window : this);

