/**
 * PyNext UI Runtime
 * 
 * Client-side JavaScript for ShadCN component interactivity.
 * Handles dialogs, dropdowns, tabs, accordions, and other interactive components.
 */

(function() {
    'use strict';

    // =========================================================================
    // Utility Functions
    // =========================================================================

    /**
     * Get focusable elements within a container
     */
    function getFocusableElements(container) {
        const selector = [
            'a[href]',
            'area[href]',
            'input:not([disabled])',
            'select:not([disabled])',
            'textarea:not([disabled])',
            'button:not([disabled])',
            'iframe',
            '[tabindex]:not([tabindex="-1"])',
            '[contenteditable]'
        ].join(', ');
        return container.querySelectorAll(selector);
    }

    /**
     * Trap focus within an element
     */
    function trapFocus(container, event) {
        const focusable = getFocusableElements(container);
        if (focusable.length === 0) return;

        const first = focusable[0];
        const last = focusable[focusable.length - 1];

        if (event.shiftKey && document.activeElement === first) {
            event.preventDefault();
            last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
            event.preventDefault();
            first.focus();
        }
    }

    // =========================================================================
    // Portal
    // =========================================================================

    function initPortals() {
        document.querySelectorAll('[data-pynext-portal]').forEach(portal => {
            const target = portal.dataset.pynextPortal || 'body';
            const targetEl = document.querySelector(target);
            if (targetEl && portal.parentNode !== targetEl) {
                targetEl.appendChild(portal);
            }
        });
    }

    // =========================================================================
    // Focus Trap
    // =========================================================================

    function initFocusTraps() {
        document.querySelectorAll('[data-pynext-focus-trap="true"]').forEach(trap => {
            trap.addEventListener('keydown', (e) => {
                if (e.key === 'Tab') {
                    trapFocus(trap, e);
                }
            });

            // Auto-focus first element if specified
            if (trap.dataset.pynextFocusTrapAutofocus === 'true') {
                const focusable = getFocusableElements(trap);
                if (focusable.length > 0) {
                    focusable[0].focus();
                }
            }
        });
    }

    // =========================================================================
    // Click Outside
    // =========================================================================

    function initClickOutside() {
        document.addEventListener('click', (e) => {
            document.querySelectorAll('[data-pynext-click-outside="true"]').forEach(el => {
                if (!el.contains(e.target)) {
                    // Check ignore selector
                    const ignoreSelector = el.dataset.pynextClickOutsideIgnore;
                    if (ignoreSelector && e.target.closest(ignoreSelector)) {
                        return;
                    }
                    
                    // Dispatch custom event
                    el.dispatchEvent(new CustomEvent('pynext:clickoutside', {
                        bubbles: true,
                        detail: { target: e.target }
                    }));
                }
            });
        });
    }

    // =========================================================================
    // Dialog
    // =========================================================================

    function initDialogs() {
        // Open dialog on trigger click
        document.addEventListener('click', (e) => {
            const trigger = e.target.closest('[data-pynext-dialog-trigger]');
            if (trigger) {
                const dialog = trigger.closest('[data-pynext-dialog]');
                if (dialog) {
                    openDialog(dialog);
                }
            }

            // Close dialog on close button or overlay click
            const closeBtn = e.target.closest('[data-pynext-dialog-close]');
            if (closeBtn) {
                const dialog = closeBtn.closest('[data-pynext-dialog]');
                if (dialog) {
                    closeDialog(dialog);
                }
            }

            const overlay = e.target.closest('[data-pynext-dialog-overlay]');
            if (overlay) {
                const dialog = overlay.closest('[data-pynext-dialog]');
                if (dialog) {
                    closeDialog(dialog);
                }
            }
        });

        // Close on Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const openDialog = document.querySelector('[data-pynext-dialog][data-state="open"]');
                if (openDialog) {
                    closeDialog(openDialog);
                }
            }
        });
    }

    function openDialog(dialog) {
        dialog.dataset.state = 'open';
        const content = dialog.querySelector('[data-pynext-dialog-content]');
        const overlay = dialog.querySelector('[data-pynext-dialog-overlay]');
        
        if (content) {
            content.dataset.state = 'open';
            content.style.display = '';
            
            // Focus first focusable element
            const focusable = getFocusableElements(content);
            if (focusable.length > 0) {
                setTimeout(() => focusable[0].focus(), 50);
            }
        }
        if (overlay) {
            overlay.dataset.state = 'open';
            overlay.style.display = '';
        }

        // Prevent body scroll
        document.body.style.overflow = 'hidden';
    }

    function closeDialog(dialog) {
        dialog.dataset.state = 'closed';
        const content = dialog.querySelector('[data-pynext-dialog-content]');
        const overlay = dialog.querySelector('[data-pynext-dialog-overlay]');
        
        if (content) content.dataset.state = 'closed';
        if (overlay) overlay.dataset.state = 'closed';

        // Restore body scroll
        document.body.style.overflow = '';

        // Hide after animation
        setTimeout(() => {
            if (content) content.style.display = 'none';
            if (overlay) overlay.style.display = 'none';
        }, 200);
    }

    // =========================================================================
    // AlertDialog (similar to Dialog but requires action)
    // =========================================================================

    function initAlertDialogs() {
        document.addEventListener('click', (e) => {
            const trigger = e.target.closest('[data-pynext-alert-dialog-trigger]');
            if (trigger) {
                const dialog = trigger.closest('[data-pynext-alert-dialog]');
                if (dialog) {
                    openAlertDialog(dialog);
                }
            }

            const cancel = e.target.closest('[data-pynext-alert-dialog-cancel]');
            if (cancel) {
                const dialog = cancel.closest('[data-pynext-alert-dialog]');
                if (dialog) {
                    closeAlertDialog(dialog);
                }
            }

            const action = e.target.closest('[data-pynext-alert-dialog-action]');
            if (action) {
                const dialog = action.closest('[data-pynext-alert-dialog]');
                if (dialog) {
                    closeAlertDialog(dialog);
                }
            }
        });
    }

    function openAlertDialog(dialog) {
        dialog.dataset.state = 'open';
        const content = dialog.querySelector('[data-pynext-alert-dialog-content]');
        const overlay = dialog.querySelector('[data-pynext-alert-dialog-overlay]');
        
        if (content) {
            content.dataset.state = 'open';
            content.style.display = '';
        }
        if (overlay) {
            overlay.dataset.state = 'open';
            overlay.style.display = '';
        }

        document.body.style.overflow = 'hidden';
    }

    function closeAlertDialog(dialog) {
        dialog.dataset.state = 'closed';
        const content = dialog.querySelector('[data-pynext-alert-dialog-content]');
        const overlay = dialog.querySelector('[data-pynext-alert-dialog-overlay]');
        
        if (content) content.dataset.state = 'closed';
        if (overlay) overlay.dataset.state = 'closed';

        document.body.style.overflow = '';

        setTimeout(() => {
            if (content) content.style.display = 'none';
            if (overlay) overlay.style.display = 'none';
        }, 200);
    }

    // =========================================================================
    // Dropdown Menu
    // =========================================================================

    let activeDropdown = null;

    function initDropdownMenus() {
        document.addEventListener('click', (e) => {
            const trigger = e.target.closest('[data-pynext-dropdown-trigger]');
            if (trigger) {
                e.stopPropagation();
                const menu = trigger.closest('[data-pynext-dropdown-menu]');
                if (menu) {
                    if (menu.dataset.state === 'open') {
                        closeDropdown(menu);
                    } else {
                        closeAllDropdowns();
                        openDropdown(menu);
                    }
                }
                return;
            }

            // Close on outside click
            if (activeDropdown && !e.target.closest('[data-pynext-dropdown-content]')) {
                closeDropdown(activeDropdown);
            }
        });

        // Close on Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && activeDropdown) {
                closeDropdown(activeDropdown);
            }
        });
    }

    function openDropdown(menu) {
        menu.dataset.state = 'open';
        const content = menu.querySelector('[data-pynext-dropdown-content]');
        if (content) {
            content.dataset.state = 'open';
            content.style.display = '';
        }
        activeDropdown = menu;
    }

    function closeDropdown(menu) {
        menu.dataset.state = 'closed';
        const content = menu.querySelector('[data-pynext-dropdown-content]');
        if (content) {
            content.dataset.state = 'closed';
            setTimeout(() => {
                content.style.display = 'none';
            }, 100);
        }
        if (activeDropdown === menu) {
            activeDropdown = null;
        }
    }

    function closeAllDropdowns() {
        document.querySelectorAll('[data-pynext-dropdown-menu][data-state="open"]').forEach(menu => {
            closeDropdown(menu);
        });
    }

    // =========================================================================
    // Tabs
    // =========================================================================

    function initTabs() {
        document.addEventListener('click', (e) => {
            const trigger = e.target.closest('[data-pynext-tabs-trigger]');
            if (trigger) {
                const tabs = trigger.closest('[data-pynext-tabs]');
                if (tabs) {
                    const value = trigger.dataset.value;
                    activateTab(tabs, value);
                }
            }
        });

        // Initialize default tab states
        document.querySelectorAll('[data-pynext-tabs]').forEach(tabs => {
            const activeValue = tabs.dataset.activeTab;
            if (activeValue) {
                activateTab(tabs, activeValue);
            }
        });
    }

    function activateTab(tabs, value) {
        // Update triggers
        tabs.querySelectorAll('[data-pynext-tabs-trigger]').forEach(trigger => {
            trigger.dataset.state = trigger.dataset.value === value ? 'active' : 'inactive';
            trigger.setAttribute('aria-selected', trigger.dataset.value === value);
        });

        // Update content panels
        tabs.querySelectorAll('[data-pynext-tabs-content]').forEach(content => {
            if (content.dataset.value === value) {
                content.style.display = '';
                content.dataset.state = 'active';
            } else {
                content.style.display = 'none';
                content.dataset.state = 'inactive';
            }
        });

        tabs.dataset.activeTab = value;
    }

    // =========================================================================
    // Accordion
    // =========================================================================

    function initAccordions() {
        document.addEventListener('click', (e) => {
            const trigger = e.target.closest('[data-pynext-accordion-trigger]');
            if (trigger) {
                const item = trigger.closest('[data-pynext-accordion-item]');
                const accordion = trigger.closest('[data-pynext-accordion]');
                
                if (item && accordion) {
                    toggleAccordionItem(accordion, item);
                }
            }
        });
    }

    function toggleAccordionItem(accordion, item) {
        const content = item.querySelector('[data-pynext-accordion-content]');
        const trigger = item.querySelector('[data-pynext-accordion-trigger]');
        const isOpen = item.dataset.state === 'open';
        const isSingle = accordion.dataset.type === 'single';
        const isCollapsible = accordion.hasAttribute('data-collapsible');

        // For single type, close other items
        if (isSingle && !isOpen) {
            accordion.querySelectorAll('[data-pynext-accordion-item]').forEach(otherItem => {
                if (otherItem !== item) {
                    closeAccordionItem(otherItem);
                }
            });
        }

        // Toggle current item
        if (isOpen) {
            if (isSingle && !isCollapsible) {
                // Can't close if single and not collapsible
                return;
            }
            closeAccordionItem(item);
        } else {
            openAccordionItem(item);
        }
    }

    function openAccordionItem(item) {
        item.dataset.state = 'open';
        const content = item.querySelector('[data-pynext-accordion-content]');
        const trigger = item.querySelector('[data-pynext-accordion-trigger]');
        
        if (content) {
            content.dataset.state = 'open';
            content.style.display = '';
        }
        if (trigger) {
            trigger.dataset.state = 'open';
            trigger.setAttribute('aria-expanded', 'true');
        }
    }

    function closeAccordionItem(item) {
        item.dataset.state = 'closed';
        const content = item.querySelector('[data-pynext-accordion-content]');
        const trigger = item.querySelector('[data-pynext-accordion-trigger]');
        
        if (content) {
            content.dataset.state = 'closed';
            content.style.display = 'none';
        }
        if (trigger) {
            trigger.dataset.state = 'closed';
            trigger.setAttribute('aria-expanded', 'false');
        }
    }

    // =========================================================================
    // Toggle / Switch / Checkbox / RadioGroup
    // =========================================================================

    function initFormControls() {
        // Toggle
        document.addEventListener('click', (e) => {
            const toggle = e.target.closest('[data-pynext-toggle]');
            if (toggle && !toggle.disabled) {
                const isPressed = toggle.dataset.state === 'on';
                toggle.dataset.state = isPressed ? 'off' : 'on';
                toggle.setAttribute('aria-pressed', !isPressed);
            }
        });

        // Switch
        document.addEventListener('click', (e) => {
            const switchEl = e.target.closest('[data-pynext-switch]');
            if (switchEl && !switchEl.disabled) {
                const isChecked = switchEl.dataset.state === 'checked';
                const newState = isChecked ? 'unchecked' : 'checked';
                switchEl.dataset.state = newState;
                switchEl.setAttribute('aria-checked', !isChecked);
                
                const thumb = switchEl.querySelector('span');
                if (thumb) thumb.dataset.state = newState;
            }
        });

        // Checkbox
        document.addEventListener('click', (e) => {
            const checkbox = e.target.closest('[data-pynext-checkbox]');
            if (checkbox && !checkbox.disabled) {
                const currentState = checkbox.dataset.state;
                let newState;
                
                if (currentState === 'checked') {
                    newState = 'unchecked';
                } else {
                    newState = 'checked';
                }
                
                checkbox.dataset.state = newState;
                checkbox.setAttribute('aria-checked', newState === 'checked');
                
                // Show/hide icons
                const checkIcon = checkbox.querySelector('[data-checkbox-icon]');
                const indeterminateIcon = checkbox.querySelector('[data-checkbox-indeterminate]');
                
                if (checkIcon) checkIcon.style.display = newState === 'checked' ? '' : 'none';
                if (indeterminateIcon) indeterminateIcon.style.display = 'none';
            }
        });

        // RadioGroup
        document.addEventListener('click', (e) => {
            const radioItem = e.target.closest('[data-pynext-radio-item]');
            if (radioItem && !radioItem.hasAttribute('disabled')) {
                const group = radioItem.closest('[data-pynext-radio-group]');
                if (group) {
                    const value = radioItem.dataset.value;
                    
                    // Update all items in the group
                    group.querySelectorAll('[data-pynext-radio-item]').forEach(item => {
                        const isSelected = item.dataset.value === value;
                        item.dataset.state = isSelected ? 'checked' : 'unchecked';
                        item.setAttribute('aria-checked', isSelected);
                        
                        const indicator = item.querySelector('[data-radio-indicator]');
                        if (indicator) {
                            indicator.style.display = isSelected ? '' : 'none';
                        }
                    });
                    
                    group.dataset.value = value;
                }
            }
        });
    }

    // =========================================================================
    // Avatar
    // =========================================================================

    function initAvatars() {
        document.querySelectorAll('[data-pynext-avatar-image]').forEach(img => {
            const fallback = img.parentElement.querySelector('[data-pynext-avatar-fallback]');
            
            img.addEventListener('load', () => {
                img.style.display = '';
                if (fallback) fallback.style.display = 'none';
            });
            
            img.addEventListener('error', () => {
                img.style.display = 'none';
                if (fallback) fallback.style.display = '';
            });

            // Check if already loaded/errored
            if (img.complete) {
                if (img.naturalHeight === 0) {
                    img.style.display = 'none';
                    if (fallback) fallback.style.display = '';
                } else {
                    if (fallback) fallback.style.display = 'none';
                }
            }
        });
    }

    // =========================================================================
    // Initialize
    // =========================================================================

    function init() {
        initPortals();
        initFocusTraps();
        initClickOutside();
        initDialogs();
        initAlertDialogs();
        initDropdownMenus();
        initTabs();
        initAccordions();
        initFormControls();
        initAvatars();
    }

    // Run on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Also run on Turbo/HTMX navigations
    document.addEventListener('turbo:load', init);
    document.addEventListener('htmx:afterSettle', init);

    // Expose for manual initialization
    window.PyNextUI = { init };

})();

