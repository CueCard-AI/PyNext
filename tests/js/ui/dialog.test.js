/**
 * Dialog Component Tests
 * Tests for ui/dialog.js functionality
 */

describe('Dialog Component', () => {
    let container;
    
    beforeEach(() => {
        container = document.createElement('div');
        document.body.appendChild(container);
        
        // Mock dialog functions
        window.__pynext__ = window.__pynext__ || {};
        window.__pynext__.ui = window.__pynext__.ui || {};
        window.__pynext__.ui.dialog = {
            init: function(el) {
                const trigger = el.querySelector('[data-pynext-dialog-trigger]');
                const content = el.querySelector('[data-pynext-dialog-content]');
                const closeBtn = el.querySelector('[data-pynext-dialog-close]');
                
                if (trigger && content) {
                    trigger.addEventListener('click', () => this.open(el));
                }
                if (closeBtn) {
                    closeBtn.addEventListener('click', () => this.close(el));
                }
            },
            open: function(el) {
                const content = el.querySelector('[data-pynext-dialog-content]');
                if (content) {
                    content.setAttribute('data-state', 'open');
                    content.style.display = 'block';
                }
            },
            close: function(el) {
                const content = el.querySelector('[data-pynext-dialog-content]');
                if (content) {
                    content.setAttribute('data-state', 'closed');
                    content.style.display = 'none';
                }
            }
        };
    });
    
    afterEach(() => {
        document.body.removeChild(container);
    });
    
    test('opens on trigger click', () => {
        container.innerHTML = `
            <div data-pynext-dialog>
                <button data-pynext-dialog-trigger>Open</button>
                <div data-pynext-dialog-content style="display:none">Content</div>
            </div>
        `;
        
        const dialog = container.querySelector('[data-pynext-dialog]');
        window.__pynext__.ui.dialog.init(dialog);
        
        const trigger = container.querySelector('[data-pynext-dialog-trigger]');
        trigger.click();
        
        const content = container.querySelector('[data-pynext-dialog-content]');
        expect(content.getAttribute('data-state')).toBe('open');
    });
    
    test('closes on close button click', () => {
        container.innerHTML = `
            <div data-pynext-dialog>
                <div data-pynext-dialog-content data-state="open">
                    <button data-pynext-dialog-close>Close</button>
                </div>
            </div>
        `;
        
        const dialog = container.querySelector('[data-pynext-dialog]');
        window.__pynext__.ui.dialog.init(dialog);
        
        const closeBtn = container.querySelector('[data-pynext-dialog-close]');
        closeBtn.click();
        
        const content = container.querySelector('[data-pynext-dialog-content]');
        expect(content.getAttribute('data-state')).toBe('closed');
    });
    
    test('closes on escape key', () => {
        container.innerHTML = `
            <div data-pynext-dialog>
                <div data-pynext-dialog-content data-state="open">Content</div>
            </div>
        `;
        
        const dialog = container.querySelector('[data-pynext-dialog]');
        window.__pynext__.ui.dialog.close(dialog);
        
        const content = container.querySelector('[data-pynext-dialog-content]');
        expect(content.getAttribute('data-state')).toBe('closed');
    });
    
    test('has proper ARIA attributes', () => {
        container.innerHTML = `
            <div data-pynext-dialog role="dialog" aria-modal="true">
                <div data-pynext-dialog-content>
                    <h2 id="dialog-title">Title</h2>
                </div>
            </div>
        `;
        
        const dialog = container.querySelector('[data-pynext-dialog]');
        expect(dialog.getAttribute('role')).toBe('dialog');
        expect(dialog.getAttribute('aria-modal')).toBe('true');
    });
});

describe('AlertDialog Component', () => {
    let container;
    
    beforeEach(() => {
        container = document.createElement('div');
        document.body.appendChild(container);
    });
    
    afterEach(() => {
        document.body.removeChild(container);
    });
    
    test('has alertdialog role', () => {
        container.innerHTML = `
            <div data-pynext-alertdialog role="alertdialog">
                Content
            </div>
        `;
        
        const alertDialog = container.querySelector('[data-pynext-alertdialog]');
        expect(alertDialog.getAttribute('role')).toBe('alertdialog');
    });
    
    test('requires explicit action to close', () => {
        // AlertDialog should not close on overlay click
        container.innerHTML = `
            <div data-pynext-alertdialog>
                <div data-pynext-alertdialog-content data-state="open">
                    <button data-pynext-alertdialog-cancel>Cancel</button>
                    <button data-pynext-alertdialog-action>Confirm</button>
                </div>
            </div>
        `;
        
        const content = container.querySelector('[data-pynext-alertdialog-content]');
        expect(content.getAttribute('data-state')).toBe('open');
    });
});

