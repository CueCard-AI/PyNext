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
    // Tooltip
    // =========================================================================

    let tooltipShowTimer = null;
    let tooltipHideTimer = null;
    let activeTooltip = null;

    function initTooltips() {
        document.addEventListener('mouseenter', (e) => {
            const trigger = e.target.closest('[data-pynext-tooltip-trigger]');
            if (!trigger) return;

            const tooltip = trigger.closest('[data-pynext-tooltip]');
            if (!tooltip) return;

            clearTimeout(tooltipHideTimer);
            
            const delay = parseInt(tooltip.dataset.delay) || 700;
            
            tooltipShowTimer = setTimeout(() => {
                showTooltip(tooltip);
            }, delay);
        }, true);

        document.addEventListener('mouseleave', (e) => {
            const trigger = e.target.closest('[data-pynext-tooltip-trigger]');
            if (!trigger) return;

            const tooltip = trigger.closest('[data-pynext-tooltip]');
            if (!tooltip) return;

            clearTimeout(tooltipShowTimer);
            
            tooltipHideTimer = setTimeout(() => {
                hideTooltip(tooltip);
            }, 100);
        }, true);

        // Also show on focus for keyboard users
        document.addEventListener('focusin', (e) => {
            const trigger = e.target.closest('[data-pynext-tooltip-trigger]');
            if (!trigger) return;

            const tooltip = trigger.closest('[data-pynext-tooltip]');
            if (tooltip) showTooltip(tooltip);
        });

        document.addEventListener('focusout', (e) => {
            const trigger = e.target.closest('[data-pynext-tooltip-trigger]');
            if (!trigger) return;

            const tooltip = trigger.closest('[data-pynext-tooltip]');
            if (tooltip) hideTooltip(tooltip);
        });

        // Hide on Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && activeTooltip) {
                hideTooltip(activeTooltip);
            }
        });
    }

    function showTooltip(tooltip) {
        const content = tooltip.querySelector('[data-pynext-tooltip-content]');
        if (!content) return;

        tooltip.dataset.state = 'open';
        content.dataset.state = 'open';
        content.style.display = '';
        activeTooltip = tooltip;
    }

    function hideTooltip(tooltip) {
        const content = tooltip.querySelector('[data-pynext-tooltip-content]');
        if (!content) return;

        tooltip.dataset.state = 'closed';
        content.dataset.state = 'closed';
        
        setTimeout(() => {
            if (content.dataset.state === 'closed') {
                content.style.display = 'none';
            }
        }, 100);

        if (activeTooltip === tooltip) {
            activeTooltip = null;
        }
    }

    // =========================================================================
    // Popover
    // =========================================================================

    let activePopover = null;

    function initPopovers() {
        // Open/close on trigger click
        document.addEventListener('click', (e) => {
            const trigger = e.target.closest('[data-pynext-popover-trigger]');
            if (trigger) {
                const popover = trigger.closest('[data-pynext-popover]');
                if (popover) {
                    e.stopPropagation();
                    if (popover.dataset.state === 'open') {
                        closePopover(popover);
                    } else {
                        // Close any other open popovers
                        if (activePopover && activePopover !== popover) {
                            closePopover(activePopover);
                        }
                        openPopover(popover);
                    }
                }
                return;
            }

            // Close button inside popover
            const closeBtn = e.target.closest('[data-pynext-popover-close]');
            if (closeBtn) {
                const popover = closeBtn.closest('[data-pynext-popover]');
                if (popover) {
                    closePopover(popover);
                }
                return;
            }

            // Click outside to close
            if (activePopover) {
                const content = activePopover.querySelector('[data-pynext-popover-content]');
                if (content && content.dataset.closeOnOutsideClick !== 'false') {
                    if (!e.target.closest('[data-pynext-popover-content]')) {
                        closePopover(activePopover);
                    }
                }
            }
        });

        // Close on Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && activePopover) {
                const content = activePopover.querySelector('[data-pynext-popover-content]');
                if (content && content.dataset.closeOnEscape !== 'false') {
                    closePopover(activePopover);
                }
            }
        });
    }

    function openPopover(popover) {
        popover.dataset.state = 'open';
        const content = popover.querySelector('[data-pynext-popover-content]');
        
        if (content) {
            content.dataset.state = 'open';
            content.style.display = '';
            
            // Focus first focusable element if focus trap is enabled
            if (content.dataset.pynextFocusTrap === 'true') {
                const focusable = getFocusableElements(content);
                if (focusable.length > 0) {
                    setTimeout(() => focusable[0].focus(), 50);
                }
            }
        }
        
        activePopover = popover;
    }

    function closePopover(popover) {
        popover.dataset.state = 'closed';
        const content = popover.querySelector('[data-pynext-popover-content]');
        
        if (content) {
            content.dataset.state = 'closed';
            setTimeout(() => {
                if (content.dataset.state === 'closed') {
                    content.style.display = 'none';
                }
            }, 150);
        }
        
        if (activePopover === popover) {
            activePopover = null;
        }
    }

    // =========================================================================
    // Sheet / Drawer
    // =========================================================================

    // Sheet swipe state
    let sheetTouchStart = null;
    let sheetTouchCurrent = null;
    const SWIPE_THRESHOLD = 100; // Minimum distance to trigger close
    const SWIPE_VELOCITY_THRESHOLD = 0.5; // Minimum velocity (px/ms)

    function initSheets() {
        // Open sheet on trigger click
        document.addEventListener('click', (e) => {
            const trigger = e.target.closest('[data-pynext-sheet-trigger]');
            if (trigger) {
                const sheet = trigger.closest('[data-pynext-sheet]');
                if (sheet) {
                    openSheet(sheet);
                }
            }

            // Close on close button or overlay click
            const closeBtn = e.target.closest('[data-pynext-sheet-close]');
            if (closeBtn) {
                const sheet = closeBtn.closest('[data-pynext-sheet]');
                if (sheet) {
                    closeSheet(sheet);
                }
            }

            const overlay = e.target.closest('[data-pynext-sheet-overlay]');
            if (overlay) {
                const sheet = overlay.closest('[data-pynext-sheet]');
                if (sheet) {
                    closeSheet(sheet);
                }
            }
        });

        // Close on Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const openSheet = document.querySelector('[data-pynext-sheet][data-state="open"]');
                if (openSheet) {
                    closeSheet(openSheet);
                }
            }
        });

        // Swipe to close (mobile)
        document.addEventListener('touchstart', (e) => {
            const content = e.target.closest('[data-pynext-sheet-content]');
            if (!content) return;
            
            sheetTouchStart = {
                x: e.touches[0].clientX,
                y: e.touches[0].clientY,
                time: Date.now()
            };
            sheetTouchCurrent = sheetTouchStart;
        }, { passive: true });

        document.addEventListener('touchmove', (e) => {
            if (!sheetTouchStart) return;
            
            const content = e.target.closest('[data-pynext-sheet-content]');
            if (!content) return;

            sheetTouchCurrent = {
                x: e.touches[0].clientX,
                y: e.touches[0].clientY,
                time: Date.now()
            };

            // Calculate drag distance based on sheet side
            const side = content.dataset.side || 'right';
            const deltaX = sheetTouchCurrent.x - sheetTouchStart.x;
            const deltaY = sheetTouchCurrent.y - sheetTouchStart.y;

            // Apply visual feedback (translate) during drag
            let translate = 0;
            if (side === 'right' && deltaX > 0) {
                translate = Math.min(deltaX, content.offsetWidth);
                content.style.transform = `translateX(${translate}px)`;
            } else if (side === 'left' && deltaX < 0) {
                translate = Math.max(deltaX, -content.offsetWidth);
                content.style.transform = `translateX(${translate}px)`;
            } else if (side === 'bottom' && deltaY > 0) {
                translate = Math.min(deltaY, content.offsetHeight);
                content.style.transform = `translateY(${translate}px)`;
            } else if (side === 'top' && deltaY < 0) {
                translate = Math.max(deltaY, -content.offsetHeight);
                content.style.transform = `translateY(${translate}px)`;
            }
        }, { passive: true });

        document.addEventListener('touchend', (e) => {
            if (!sheetTouchStart || !sheetTouchCurrent) {
                sheetTouchStart = null;
                sheetTouchCurrent = null;
                return;
            }

            const content = e.target.closest('[data-pynext-sheet-content]');
            if (!content) {
                sheetTouchStart = null;
                sheetTouchCurrent = null;
                return;
            }

            const sheet = content.closest('[data-pynext-sheet]');
            const side = content.dataset.side || 'right';
            
            const deltaX = sheetTouchCurrent.x - sheetTouchStart.x;
            const deltaY = sheetTouchCurrent.y - sheetTouchStart.y;
            const deltaTime = sheetTouchCurrent.time - sheetTouchStart.time;
            
            // Calculate velocity
            const velocityX = Math.abs(deltaX) / deltaTime;
            const velocityY = Math.abs(deltaY) / deltaTime;

            // Determine if swipe should close
            let shouldClose = false;
            
            if (side === 'right') {
                shouldClose = deltaX > SWIPE_THRESHOLD || (deltaX > 50 && velocityX > SWIPE_VELOCITY_THRESHOLD);
            } else if (side === 'left') {
                shouldClose = deltaX < -SWIPE_THRESHOLD || (deltaX < -50 && velocityX > SWIPE_VELOCITY_THRESHOLD);
            } else if (side === 'bottom') {
                shouldClose = deltaY > SWIPE_THRESHOLD || (deltaY > 50 && velocityY > SWIPE_VELOCITY_THRESHOLD);
            } else if (side === 'top') {
                shouldClose = deltaY < -SWIPE_THRESHOLD || (deltaY < -50 && velocityY > SWIPE_VELOCITY_THRESHOLD);
            }

            // Reset transform
            content.style.transform = '';

            if (shouldClose && sheet) {
                closeSheet(sheet);
            }

            sheetTouchStart = null;
            sheetTouchCurrent = null;
        }, { passive: true });
    }

    function openSheet(sheet) {
        sheet.dataset.state = 'open';
        const content = sheet.querySelector('[data-pynext-sheet-content]');
        const overlay = sheet.querySelector('[data-pynext-sheet-overlay]');
        
        if (overlay) {
            overlay.dataset.state = 'open';
            overlay.style.display = '';
        }
        if (content) {
            content.dataset.state = 'open';
            content.style.display = '';
            
            // Focus first focusable element
            const focusable = getFocusableElements(content);
            if (focusable.length > 0) {
                setTimeout(() => focusable[0].focus(), 50);
            }
        }

        document.body.style.overflow = 'hidden';
    }

    function closeSheet(sheet) {
        sheet.dataset.state = 'closed';
        const content = sheet.querySelector('[data-pynext-sheet-content]');
        const overlay = sheet.querySelector('[data-pynext-sheet-overlay]');
        
        if (content) content.dataset.state = 'closed';
        if (overlay) overlay.dataset.state = 'closed';

        document.body.style.overflow = '';

        setTimeout(() => {
            if (content) content.style.display = 'none';
            if (overlay) overlay.style.display = 'none';
        }, 300);
    }

    // =========================================================================
    // Combobox
    // =========================================================================

    let activeCombobox = null;
    let highlightedIndex = -1;

    function initComboboxes() {
        // Open/close on trigger click
        document.addEventListener('click', (e) => {
            const trigger = e.target.closest('[data-pynext-combobox-trigger]');
            if (trigger) {
                e.stopPropagation();
                const combobox = trigger.closest('[data-pynext-combobox]');
                if (combobox) {
                    if (combobox.dataset.state === 'open') {
                        closeCombobox(combobox);
                    } else {
                        if (activeCombobox && activeCombobox !== combobox) {
                            closeCombobox(activeCombobox);
                        }
                        openCombobox(combobox);
                    }
                }
                return;
            }

            // Item selection
            const item = e.target.closest('[data-pynext-combobox-item]');
            if (item && !item.hasAttribute('data-disabled')) {
                const combobox = item.closest('[data-pynext-combobox]');
                if (combobox) {
                    selectComboboxItem(combobox, item);
                }
                return;
            }

            // Create new item
            const createOption = e.target.closest('[data-pynext-combobox-create]');
            if (createOption) {
                const combobox = createOption.closest('[data-pynext-combobox]');
                if (combobox) {
                    const input = combobox.querySelector('[data-pynext-combobox-input]');
                    const query = input ? input.value.trim() : '';
                    
                    if (query) {
                        // Dispatch create event
                        combobox.dispatchEvent(new CustomEvent('pynext:combobox:create', {
                            bubbles: true,
                            detail: { query }
                        }));
                        
                        // Clear input and close
                        if (input) input.value = '';
                        closeCombobox(combobox);
                    }
                }
                return;
            }

            // Click outside to close
            if (activeCombobox && !e.target.closest('[data-pynext-combobox-content]')) {
                closeCombobox(activeCombobox);
            }
        });

        // Search input handling
        document.addEventListener('input', (e) => {
            const input = e.target.closest('[data-pynext-combobox-input]');
            if (input) {
                const combobox = input.closest('[data-pynext-combobox]');
                if (combobox) {
                    filterComboboxItems(combobox, input.value);
                }
            }
        });

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (!activeCombobox) return;

            const items = getVisibleComboboxItems(activeCombobox);
            
            switch (e.key) {
                case 'ArrowDown':
                    e.preventDefault();
                    highlightedIndex = Math.min(highlightedIndex + 1, items.length - 1);
                    updateComboboxHighlight(items);
                    break;
                case 'ArrowUp':
                    e.preventDefault();
                    highlightedIndex = Math.max(highlightedIndex - 1, 0);
                    updateComboboxHighlight(items);
                    break;
                case 'Enter':
                    e.preventDefault();
                    if (highlightedIndex >= 0 && items[highlightedIndex]) {
                        selectComboboxItem(activeCombobox, items[highlightedIndex]);
                    } else {
                        // Check if create option is visible
                        const createOption = activeCombobox.querySelector('[data-pynext-combobox-create]');
                        if (createOption && createOption.style.display !== 'none') {
                            const input = activeCombobox.querySelector('[data-pynext-combobox-input]');
                            const query = input ? input.value.trim() : '';
                            
                            if (query) {
                                activeCombobox.dispatchEvent(new CustomEvent('pynext:combobox:create', {
                                    bubbles: true,
                                    detail: { query }
                                }));
                                if (input) input.value = '';
                                closeCombobox(activeCombobox);
                            }
                        }
                    }
                    break;
                case 'Escape':
                    e.preventDefault();
                    closeCombobox(activeCombobox);
                    break;
            }
        });
    }

    function openCombobox(combobox) {
        combobox.dataset.state = 'open';
        const content = combobox.querySelector('[data-pynext-combobox-content]');
        const trigger = combobox.querySelector('[data-pynext-combobox-trigger]');
        
        if (content) {
            content.dataset.state = 'open';
            content.style.display = '';
        }
        if (trigger) {
            trigger.setAttribute('aria-expanded', 'true');
        }

        // Focus search input
        const input = combobox.querySelector('[data-pynext-combobox-input]');
        if (input) {
            setTimeout(() => input.focus(), 50);
        }

        activeCombobox = combobox;
        highlightedIndex = -1;

        // Update selected state
        updateComboboxSelectedState(combobox);
    }

    function closeCombobox(combobox) {
        combobox.dataset.state = 'closed';
        const content = combobox.querySelector('[data-pynext-combobox-content]');
        const trigger = combobox.querySelector('[data-pynext-combobox-trigger]');
        
        if (content) {
            content.dataset.state = 'closed';
            setTimeout(() => {
                if (content.dataset.state === 'closed') {
                    content.style.display = 'none';
                }
            }, 150);
        }
        if (trigger) {
            trigger.setAttribute('aria-expanded', 'false');
        }

        // Clear search
        const input = combobox.querySelector('[data-pynext-combobox-input]');
        if (input) {
            input.value = '';
            filterComboboxItems(combobox, '');
        }

        if (activeCombobox === combobox) {
            activeCombobox = null;
        }
        highlightedIndex = -1;
    }

    function selectComboboxItem(combobox, item) {
        const value = item.dataset.value;
        const isMultiple = combobox.hasAttribute('data-multiple');
        
        if (isMultiple) {
            // Toggle selection for multi-select
            const current = combobox.dataset.value ? combobox.dataset.value.split(',') : [];
            const idx = current.indexOf(value);
            if (idx >= 0) {
                current.splice(idx, 1);
            } else {
                current.push(value);
            }
            combobox.dataset.value = current.join(',');
        } else {
            combobox.dataset.value = value;
            closeCombobox(combobox);
        }

        updateComboboxSelectedState(combobox);
        
        // Dispatch change event
        combobox.dispatchEvent(new CustomEvent('pynext:combobox-change', {
            bubbles: true,
            detail: { value: combobox.dataset.value }
        }));
    }

    function filterComboboxItems(combobox, query) {
        const items = combobox.querySelectorAll('[data-pynext-combobox-item]');
        const empty = combobox.querySelector('[data-pynext-combobox-empty]');
        const createOption = combobox.querySelector('[data-pynext-combobox-create]');
        const createQuerySpan = combobox.querySelector('[data-pynext-combobox-create-query]');
        let hasVisible = false;

        const normalizedQuery = query.toLowerCase();
        const trimmedQuery = query.trim();

        items.forEach(item => {
            const text = item.textContent.toLowerCase();
            const matches = text.includes(normalizedQuery);
            item.style.display = matches ? '' : 'none';
            if (matches) hasVisible = true;
        });

        // Show/hide empty message
        if (empty) {
            empty.style.display = hasVisible ? 'none' : '';
        }

        // Handle create option (only if allow_create is set and there's a query)
        if (createOption) {
            const allowCreate = combobox.hasAttribute('data-allow-create');
            const shouldShowCreate = allowCreate && !hasVisible && trimmedQuery.length > 0;
            
            createOption.style.display = shouldShowCreate ? '' : 'none';
            
            // Update the query text
            if (createQuerySpan) {
                createQuerySpan.textContent = `"${trimmedQuery}"`;
            }
            
            // Hide empty when showing create
            if (shouldShowCreate && empty) {
                empty.style.display = 'none';
            }
        }

        highlightedIndex = -1;
    }

    function getVisibleComboboxItems(combobox) {
        return Array.from(combobox.querySelectorAll('[data-pynext-combobox-item]'))
            .filter(item => item.style.display !== 'none' && !item.hasAttribute('data-disabled'));
    }

    function updateComboboxHighlight(items) {
        items.forEach((item, i) => {
            if (i === highlightedIndex) {
                item.dataset.highlighted = 'true';
                item.scrollIntoView({ block: 'nearest' });
            } else {
                delete item.dataset.highlighted;
            }
        });
    }

    function updateComboboxSelectedState(combobox) {
        const selectedValues = combobox.dataset.value ? combobox.dataset.value.split(',') : [];
        const items = combobox.querySelectorAll('[data-pynext-combobox-item]');
        
        items.forEach(item => {
            const isSelected = selectedValues.includes(item.dataset.value);
            const checkIcon = item.querySelector('[data-pynext-combobox-check]');
            if (checkIcon) {
                checkIcon.dataset.selected = isSelected;
                checkIcon.style.opacity = isSelected ? '1' : '0';
            }
        });
    }

    // =========================================================================
    // Command / Command Dialog
    // =========================================================================

    let activeCommand = null;
    let commandHighlightedIndex = -1;

    function initCommands() {
        // Handle command dialogs (⌘K to open)
        document.addEventListener('keydown', (e) => {
            if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
                e.preventDefault();
                const dialog = document.querySelector('[data-pynext-command-dialog]');
                if (dialog) {
                    if (dialog.dataset.state === 'open') {
                        closeCommandDialog(dialog);
                    } else {
                        openCommandDialog(dialog);
                    }
                }
            }

            // Navigation in command list
            if (activeCommand) {
                const items = getVisibleCommandItems(activeCommand);
                
                switch (e.key) {
                    case 'ArrowDown':
                        e.preventDefault();
                        commandHighlightedIndex = Math.min(commandHighlightedIndex + 1, items.length - 1);
                        updateCommandHighlight(items);
                        break;
                    case 'ArrowUp':
                        e.preventDefault();
                        commandHighlightedIndex = Math.max(commandHighlightedIndex - 1, 0);
                        updateCommandHighlight(items);
                        break;
                    case 'Enter':
                        e.preventDefault();
                        if (commandHighlightedIndex >= 0 && items[commandHighlightedIndex]) {
                            selectCommandItem(activeCommand, items[commandHighlightedIndex]);
                        }
                        break;
                    case 'Escape':
                        e.preventDefault();
                        const dialog = activeCommand.closest('[data-pynext-command-dialog]');
                        if (dialog) {
                            closeCommandDialog(dialog);
                        }
                        break;
                }
            }
        });

        // Search input handling
        document.addEventListener('input', (e) => {
            const input = e.target.closest('[data-pynext-command-input]');
            if (input) {
                const command = input.closest('[data-pynext-command]');
                if (command) {
                    filterCommandItems(command, input.value);
                }
            }
        });

        // Item selection
        document.addEventListener('click', (e) => {
            const item = e.target.closest('[data-pynext-command-item]');
            if (item && !item.hasAttribute('data-disabled')) {
                const command = item.closest('[data-pynext-command]');
                if (command) {
                    selectCommandItem(command, item);
                }
            }
        });
    }

    function openCommandDialog(dialog) {
        dialog.dataset.state = 'open';
        const overlay = dialog.querySelector('[data-pynext-command-dialog-overlay]');
        const content = dialog.querySelector('[data-pynext-command]');
        
        if (overlay) overlay.style.display = '';
        if (content) {
            content.parentElement.style.display = '';
            const input = content.querySelector('[data-pynext-command-input]');
            if (input) setTimeout(() => input.focus(), 50);
        }
        
        activeCommand = content;
        commandHighlightedIndex = -1;
        document.body.style.overflow = 'hidden';
    }

    function closeCommandDialog(dialog) {
        dialog.dataset.state = 'closed';
        const overlay = dialog.querySelector('[data-pynext-command-dialog-overlay]');
        const content = dialog.querySelector('[data-pynext-command]');
        
        setTimeout(() => {
            if (overlay) overlay.style.display = 'none';
            if (content) content.parentElement.style.display = 'none';
        }, 150);
        
        // Clear search
        const input = dialog.querySelector('[data-pynext-command-input]');
        if (input) {
            input.value = '';
            if (content) filterCommandItems(content, '');
        }
        
        activeCommand = null;
        commandHighlightedIndex = -1;
        document.body.style.overflow = '';
    }

    function filterCommandItems(command, query) {
        const items = command.querySelectorAll('[data-pynext-command-item]');
        const empty = command.querySelector('[data-pynext-command-empty]');
        let hasVisible = false;

        query = query.toLowerCase();

        items.forEach(item => {
            const value = (item.dataset.value || '').toLowerCase();
            const text = item.textContent.toLowerCase();
            const matches = value.includes(query) || text.includes(query);
            item.style.display = matches ? '' : 'none';
            if (matches) hasVisible = true;
        });

        // Show/hide empty state
        if (empty) {
            empty.style.display = hasVisible ? 'none' : '';
        }

        // Hide empty groups
        command.querySelectorAll('[data-pynext-command-group]').forEach(group => {
            const visibleItems = group.querySelectorAll('[data-pynext-command-item]:not([style*="display: none"])');
            group.style.display = visibleItems.length > 0 ? '' : 'none';
        });

        commandHighlightedIndex = -1;
    }

    function getVisibleCommandItems(command) {
        return Array.from(command.querySelectorAll('[data-pynext-command-item]'))
            .filter(item => item.style.display !== 'none' && !item.hasAttribute('data-disabled'));
    }

    function updateCommandHighlight(items) {
        items.forEach((item, i) => {
            if (i === commandHighlightedIndex) {
                item.dataset.selected = 'true';
                item.scrollIntoView({ block: 'nearest' });
            } else {
                delete item.dataset.selected;
            }
        });
    }

    function selectCommandItem(command, item) {
        const value = item.dataset.value;
        command.dataset.value = value;
        
        // Dispatch event
        command.dispatchEvent(new CustomEvent('pynext:command-select', {
            bubbles: true,
            detail: { value }
        }));

        // Close dialog if in one
        const dialog = command.closest('[data-pynext-command-dialog]');
        if (dialog) {
            closeCommandDialog(dialog);
        }
    }

    // =========================================================================
    // Calendar
    // =========================================================================

    function initCalendars() {
        document.addEventListener('click', (e) => {
            // Day selection
            const dayBtn = e.target.closest('[data-pynext-calendar-day]');
            if (dayBtn && !dayBtn.hasAttribute('disabled')) {
                const calendar = dayBtn.closest('[data-pynext-calendar]');
                if (calendar) {
                    selectCalendarDate(calendar, dayBtn.dataset.date);
                }
                return;
            }

            // Previous month
            const prevBtn = e.target.closest('[data-pynext-calendar-prev]');
            if (prevBtn) {
                const calendar = prevBtn.closest('[data-pynext-calendar]');
                if (calendar) navigateCalendar(calendar, -1);
                return;
            }

            // Next month
            const nextBtn = e.target.closest('[data-pynext-calendar-next]');
            if (nextBtn) {
                const calendar = nextBtn.closest('[data-pynext-calendar]');
                if (calendar) navigateCalendar(calendar, 1);
                return;
            }
        });
    }

    function selectCalendarDate(calendar, dateStr) {
        const mode = calendar.dataset.mode || 'single';
        
        if (mode === 'single') {
            calendar.dataset.selected = dateStr;
            
            // Update visual state
            calendar.querySelectorAll('[data-pynext-calendar-day]').forEach(btn => {
                const isSelected = btn.dataset.date === dateStr;
                btn.setAttribute('aria-selected', isSelected);
                if (isSelected) {
                    btn.classList.add('bg-primary', 'text-primary-foreground');
                } else {
                    btn.classList.remove('bg-primary', 'text-primary-foreground');
                }
            });
        } else if (mode === 'range') {
            // Handle range selection
            const start = calendar.dataset.rangeStart;
            const end = calendar.dataset.rangeEnd;
            
            if (!start || (start && end)) {
                // Start new range
                calendar.dataset.rangeStart = dateStr;
                delete calendar.dataset.rangeEnd;
            } else {
                // Complete range
                if (dateStr < start) {
                    calendar.dataset.rangeEnd = start;
                    calendar.dataset.rangeStart = dateStr;
                } else {
                    calendar.dataset.rangeEnd = dateStr;
                }
            }
        }
        
        calendar.dispatchEvent(new CustomEvent('pynext:calendar-select', {
            bubbles: true,
            detail: { 
                date: dateStr,
                mode,
                start: calendar.dataset.rangeStart,
                end: calendar.dataset.rangeEnd
            }
        }));
    }

    function navigateCalendar(calendar, delta) {
        let year = parseInt(calendar.dataset.year);
        let month = parseInt(calendar.dataset.month);
        
        month += delta;
        if (month > 12) { month = 1; year++; }
        if (month < 1) { month = 12; year--; }
        
        calendar.dataset.year = year;
        calendar.dataset.month = month;
        
        calendar.dispatchEvent(new CustomEvent('pynext:calendar-navigate', {
            bubbles: true,
            detail: { year, month }
        }));
    }

    // =========================================================================
    // DatePicker
    // =========================================================================

    let activeDatePicker = null;

    function initDatePickers() {
        document.addEventListener('click', (e) => {
            // Open/close on trigger click
            const trigger = e.target.closest('[data-pynext-datepicker-trigger]');
            if (trigger) {
                const picker = trigger.closest('[data-pynext-datepicker], [data-pynext-daterangepicker]');
                if (picker) {
                    e.stopPropagation();
                    if (activeDatePicker === picker) {
                        closeDatePicker(picker);
                    } else {
                        if (activeDatePicker) closeDatePicker(activeDatePicker);
                        openDatePicker(picker);
                    }
                }
                return;
            }

            // Preset selection
            const preset = e.target.closest('[data-pynext-datepicker-preset], [data-pynext-daterange-preset]');
            if (preset) {
                const picker = preset.closest('[data-pynext-datepicker], [data-pynext-daterangepicker]');
                if (picker) {
                    const value = preset.dataset.presetValue;
                    const start = preset.dataset.presetStart;
                    const end = preset.dataset.presetEnd;
                    
                    if (value) {
                        picker.dataset.value = value;
                    } else if (start && end) {
                        picker.dataset.start = start;
                        picker.dataset.end = end;
                    }
                    
                    closeDatePicker(picker);
                    picker.dispatchEvent(new CustomEvent('pynext:datepicker-change', {
                        bubbles: true,
                        detail: { value, start, end }
                    }));
                }
                return;
            }

            // Click outside to close
            if (activeDatePicker && !e.target.closest('[data-pynext-datepicker-content]')) {
                closeDatePicker(activeDatePicker);
            }
        });

        // Listen for calendar selection
        document.addEventListener('pynext:calendar-select', (e) => {
            const picker = e.target.closest('[data-pynext-datepicker], [data-pynext-daterangepicker]');
            if (picker) {
                if (picker.hasAttribute('data-pynext-datepicker')) {
                    picker.dataset.value = e.detail.date;
                    closeDatePicker(picker);
                } else if (e.detail.start && e.detail.end) {
                    picker.dataset.start = e.detail.start;
                    picker.dataset.end = e.detail.end;
                    closeDatePicker(picker);
                }
                
                picker.dispatchEvent(new CustomEvent('pynext:datepicker-change', {
                    bubbles: true,
                    detail: e.detail
                }));
            }
        });
    }

    function openDatePicker(picker) {
        const content = picker.querySelector('[data-pynext-datepicker-content]');
        if (content) content.style.display = '';
        activeDatePicker = picker;
    }

    function closeDatePicker(picker) {
        const content = picker.querySelector('[data-pynext-datepicker-content]');
        if (content) content.style.display = 'none';
        if (activeDatePicker === picker) activeDatePicker = null;
    }

    // =========================================================================
    // DataTable
    // =========================================================================

    function initDataTables() {
        document.addEventListener('click', (e) => {
            // Sort column
            const sortBtn = e.target.closest('[data-pynext-datatable-sort]');
            if (sortBtn) {
                const table = sortBtn.closest('[data-pynext-datatable]');
                if (table) {
                    const column = sortBtn.dataset.pynextDatatableSort;
                    const currentDir = table.dataset.sortDirection || 'asc';
                    const newDir = table.dataset.sortColumn === column && currentDir === 'asc' ? 'desc' : 'asc';
                    
                    table.dataset.sortColumn = column;
                    table.dataset.sortDirection = newDir;
                    
                    table.dispatchEvent(new CustomEvent('pynext:datatable-sort', {
                        bubbles: true,
                        detail: { column, direction: newDir }
                    }));
                }
                return;
            }

            // Pagination
            const pageBtn = e.target.closest('[data-pynext-datatable-first], [data-pynext-datatable-prev], [data-pynext-datatable-next], [data-pynext-datatable-last]');
            if (pageBtn && !pageBtn.hasAttribute('disabled')) {
                const table = pageBtn.closest('[data-pynext-datatable]');
                if (table) {
                    const currentPage = parseInt(table.dataset.page) || 1;
                    let newPage = currentPage;
                    
                    if (pageBtn.hasAttribute('data-pynext-datatable-first')) newPage = 1;
                    else if (pageBtn.hasAttribute('data-pynext-datatable-prev')) newPage = currentPage - 1;
                    else if (pageBtn.hasAttribute('data-pynext-datatable-next')) newPage = currentPage + 1;
                    else if (pageBtn.hasAttribute('data-pynext-datatable-last')) {
                        // Would need total pages info
                    }
                    
                    table.dataset.page = newPage;
                    table.dispatchEvent(new CustomEvent('pynext:datatable-page', {
                        bubbles: true,
                        detail: { page: newPage }
                    }));
                }
                return;
            }

            // Row selection
            const selectAll = e.target.closest('[data-pynext-datatable-select-all]');
            if (selectAll) {
                const table = selectAll.closest('[data-pynext-datatable]');
                if (table) {
                    const checkboxes = table.querySelectorAll('[data-pynext-datatable-select-row]');
                    checkboxes.forEach(cb => cb.checked = selectAll.checked);
                    
                    table.dispatchEvent(new CustomEvent('pynext:datatable-select', {
                        bubbles: true,
                        detail: { all: selectAll.checked }
                    }));
                }
                return;
            }

            const selectRow = e.target.closest('[data-pynext-datatable-select-row]');
            if (selectRow) {
                const table = selectRow.closest('[data-pynext-datatable]');
                const row = selectRow.closest('tr');
                if (table && row) {
                    row.dataset.state = selectRow.checked ? 'selected' : '';
                    
                    table.dispatchEvent(new CustomEvent('pynext:datatable-select', {
                        bubbles: true,
                        detail: { 
                            rowIndex: parseInt(selectRow.dataset.pynextDatatableSelectRow),
                            selected: selectRow.checked
                        }
                    }));
                }
                return;
            }
        });

        // Column visibility toggle
        document.addEventListener('click', (e) => {
            // Toggle trigger
            const trigger = e.target.closest('[data-pynext-column-toggle-trigger]');
            if (trigger) {
                const toggle = trigger.closest('[data-pynext-column-toggle]');
                if (toggle) {
                    const content = toggle.querySelector('[data-pynext-column-toggle-content]');
                    if (content) {
                        const isOpen = content.style.display !== 'none';
                        content.style.display = isOpen ? 'none' : '';
                        trigger.setAttribute('aria-expanded', !isOpen);
                    }
                }
                return;
            }

            // Toggle item click
            const item = e.target.closest('[data-pynext-column-toggle-item]');
            if (item) {
                const accessor = item.dataset.pynextColumnToggleItem;
                const currentVisible = item.dataset.visible === 'true';
                const newVisible = !currentVisible;
                
                item.dataset.visible = newVisible;
                item.setAttribute('aria-checked', newVisible);
                
                // Update checkmark icon
                const checkIcon = newVisible 
                    ? '<svg class="mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>'
                    : '<span class="mr-2 h-4 w-4"></span>';
                item.querySelector('svg, span').outerHTML = checkIcon;
                
                const toggle = item.closest('[data-pynext-column-toggle]');
                if (toggle) {
                    toggle.dispatchEvent(new CustomEvent('pynext:column-visibility', {
                        bubbles: true,
                        detail: { accessor, visible: newVisible }
                    }));
                }
                return;
            }

            // Close on click outside
            document.querySelectorAll('[data-pynext-column-toggle-content]').forEach(content => {
                if (!e.target.closest('[data-pynext-column-toggle]')) {
                    content.style.display = 'none';
                }
            });
        });

        // Column resize
        initColumnResize();
    }

    // Column resize implementation
    let resizeState = null;

    function initColumnResize() {
        document.addEventListener('mousedown', (e) => {
            const handle = e.target.closest('[data-pynext-resize-handle]');
            if (!handle) return;

            const th = handle.closest('th');
            if (!th) return;

            e.preventDefault();
            
            const minWidth = parseInt(th.dataset.minWidth) || 50;
            const maxWidth = parseInt(th.dataset.maxWidth) || 500;
            const startX = e.clientX;
            const startWidth = th.offsetWidth;

            resizeState = { th, minWidth, maxWidth, startX, startWidth };
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
        });

        document.addEventListener('mousemove', (e) => {
            if (!resizeState) return;

            const { th, minWidth, maxWidth, startX, startWidth } = resizeState;
            const delta = e.clientX - startX;
            const newWidth = Math.min(maxWidth, Math.max(minWidth, startWidth + delta));
            
            th.style.width = `${newWidth}px`;
        });

        document.addEventListener('mouseup', () => {
            if (!resizeState) return;

            const { th } = resizeState;
            const table = th.closest('[data-pynext-datatable]');
            
            if (table) {
                table.dispatchEvent(new CustomEvent('pynext:column-resize', {
                    bubbles: true,
                    detail: { 
                        accessor: th.dataset.resizableCol,
                        width: th.style.width
                    }
                }));
            }

            resizeState = null;
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        });

        // Touch support for mobile
        document.addEventListener('touchstart', (e) => {
            const handle = e.target.closest('[data-pynext-resize-handle]');
            if (!handle) return;

            const th = handle.closest('th');
            if (!th) return;

            const minWidth = parseInt(th.dataset.minWidth) || 50;
            const maxWidth = parseInt(th.dataset.maxWidth) || 500;
            const startX = e.touches[0].clientX;
            const startWidth = th.offsetWidth;

            resizeState = { th, minWidth, maxWidth, startX, startWidth };
        }, { passive: true });

        document.addEventListener('touchmove', (e) => {
            if (!resizeState) return;

            const { th, minWidth, maxWidth, startX, startWidth } = resizeState;
            const delta = e.touches[0].clientX - startX;
            const newWidth = Math.min(maxWidth, Math.max(minWidth, startWidth + delta));
            
            th.style.width = `${newWidth}px`;
        }, { passive: true });

        document.addEventListener('touchend', () => {
            if (!resizeState) return;

            const { th } = resizeState;
            const table = th.closest('[data-pynext-datatable]');
            
            if (table) {
                table.dispatchEvent(new CustomEvent('pynext:column-resize', {
                    bubbles: true,
                    detail: { 
                        accessor: th.dataset.resizableCol,
                        width: th.style.width
                    }
                }));
            }

            resizeState = null;
        }, { passive: true });
    }

    // =========================================================================
    // FileUpload
    // =========================================================================

    function initFileUploads() {
        document.querySelectorAll('[data-pynext-file-upload]').forEach(upload => {
            const dropzone = upload.querySelector('[data-pynext-dropzone]');
            const input = upload.querySelector('[data-pynext-file-input]');
            
            if (!dropzone || !input) return;

            // Configure input from upload data attributes
            if (upload.dataset.accept) input.accept = upload.dataset.accept;
            if (upload.dataset.multiple) input.multiple = true;

            // Drag events
            ['dragenter', 'dragover'].forEach(event => {
                dropzone.addEventListener(event, (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    dropzone.dataset.dragActive = 'true';
                });
            });

            ['dragleave', 'drop'].forEach(event => {
                dropzone.addEventListener(event, (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    dropzone.dataset.dragActive = 'false';
                });
            });

            dropzone.addEventListener('drop', (e) => {
                const files = Array.from(e.dataTransfer.files);
                handleFiles(upload, files);
            });

            // File input change
            input.addEventListener('change', () => {
                const files = Array.from(input.files);
                handleFiles(upload, files);
            });
        });

        // Remove file
        document.addEventListener('click', (e) => {
            const removeBtn = e.target.closest('[data-pynext-file-remove]');
            if (removeBtn) {
                const item = removeBtn.closest('[data-pynext-file-item]');
                if (item) {
                    item.remove();
                    const upload = e.target.closest('[data-pynext-file-upload]');
                    if (upload) {
                        upload.dispatchEvent(new CustomEvent('pynext:file-remove', {
                            bubbles: true,
                            detail: { item }
                        }));
                    }
                }
            }
        });
    }

    function handleFiles(upload, files) {
        const maxSize = parseInt(upload.dataset.maxSize) || Infinity;
        const maxFiles = parseInt(upload.dataset.maxFiles) || Infinity;
        
        // Validate files
        const validFiles = files.filter(file => {
            if (file.size > maxSize) {
                console.warn(`File ${file.name} exceeds max size`);
                return false;
            }
            return true;
        }).slice(0, maxFiles);
        
        // Dispatch event
        upload.dispatchEvent(new CustomEvent('pynext:file-select', {
            bubbles: true,
            detail: { files: validFiles }
        }));
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
        initTooltips();
        initPopovers();
        initSheets();
        initComboboxes();
        initCommands();
        initCalendars();
        initDatePickers();
        initDataTables();
        initFileUploads();
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

