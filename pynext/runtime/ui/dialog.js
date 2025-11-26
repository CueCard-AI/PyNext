/**
 * PyNext Dialog Component Runtime
 * Handles Dialog and AlertDialog
 * Size target: ~1 KB minified
 */
(function(g) {
    'use strict';
    
    var ui = g.__pynext__.ui;
    
    function initDialogs() {
        // Dialog triggers
        ui.on('click', '[data-pynext-dialog-trigger]', function(e, trigger) {
            var dialogId = trigger.dataset.pynextDialogTrigger;
            var dialog = document.querySelector('[data-pynext-dialog="' + dialogId + '"]');
            if (dialog) openDialog(dialog);
        });
        
        // Close buttons
        ui.on('click', '[data-pynext-dialog-close]', function(e, btn) {
            var dialog = btn.closest('[data-pynext-dialog]');
            if (dialog) closeDialog(dialog);
        });
        
        // Overlay click
        ui.on('click', '[data-pynext-dialog-overlay]', function(e, overlay) {
            var dialog = overlay.closest('[data-pynext-dialog]');
            if (dialog && dialog.dataset.pynextDialogCloseOnOverlay !== 'false') {
                closeDialog(dialog);
            }
        });
    }
    
    function openDialog(dialog) {
        var content = dialog.querySelector('[data-pynext-dialog-content]');
        
        dialog.removeAttribute('hidden');
        dialog.setAttribute('data-state', 'open');
        
        // Store previous focus
        dialog._prevFocus = document.activeElement;
        
        // Focus first focusable or content
        var focusable = ui.getFocusable(content);
        if (focusable.length) {
            focusable[0].focus();
        } else {
            content.focus();
        }
        
        // Focus trap
        content.addEventListener('keydown', function(e) {
            if (e.key === 'Tab') ui.trapFocus(content, e);
            if (e.key === 'Escape') closeDialog(dialog);
        });
        
        // Prevent body scroll
        document.body.style.overflow = 'hidden';
    }
    
    function closeDialog(dialog) {
        dialog.setAttribute('hidden', '');
        dialog.setAttribute('data-state', 'closed');
        
        // Restore focus
        if (dialog._prevFocus) {
            dialog._prevFocus.focus();
        }
        
        // Restore body scroll
        document.body.style.overflow = '';
    }
    
    // AlertDialog (same behavior, different semantics)
    function initAlertDialogs() {
        ui.on('click', '[data-pynext-alertdialog-trigger]', function(e, trigger) {
            var dialogId = trigger.dataset.pynextAlertdialogTrigger;
            var dialog = document.querySelector('[data-pynext-alertdialog="' + dialogId + '"]');
            if (dialog) openDialog(dialog);
        });
        
        ui.on('click', '[data-pynext-alertdialog-action]', function(e, btn) {
            var dialog = btn.closest('[data-pynext-alertdialog]');
            if (dialog) closeDialog(dialog);
        });
        
        ui.on('click', '[data-pynext-alertdialog-cancel]', function(e, btn) {
            var dialog = btn.closest('[data-pynext-alertdialog]');
            if (dialog) closeDialog(dialog);
        });
    }
    
    // Initialize
    initDialogs();
    initAlertDialogs();
    
    // Expose for dynamic content
    ui.dialog = { open: openDialog, close: closeDialog };
    
})(window);

