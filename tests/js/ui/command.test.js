/**
 * Command Palette Component Tests
 * Tests for ui/command.js functionality
 */

describe('Command Component', () => {
    let container;
    
    beforeEach(() => {
        container = document.createElement('div');
        document.body.appendChild(container);
        
        window.__pynext__ = window.__pynext__ || {};
        window.__pynext__.ui = window.__pynext__.ui || {};
        window.__pynext__.ui.command = {
            init: function(el) {
                const input = el.querySelector('[data-pynext-command-input]');
                
                if (input) {
                    input.addEventListener('input', () => this.filter(el, input.value));
                }
                
                // Global shortcut
                document.addEventListener('keydown', (e) => {
                    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
                        e.preventDefault();
                        this.toggle(el);
                    }
                    if (e.key === 'Escape') {
                        this.close(el);
                    }
                });
            },
            toggle: function(el) {
                const dialog = el.querySelector('[data-pynext-command-dialog]');
                const isOpen = dialog.getAttribute('data-state') === 'open';
                dialog.setAttribute('data-state', isOpen ? 'closed' : 'open');
            },
            open: function(el) {
                const dialog = el.querySelector('[data-pynext-command-dialog]');
                dialog.setAttribute('data-state', 'open');
                const input = el.querySelector('[data-pynext-command-input]');
                if (input) input.focus();
            },
            close: function(el) {
                const dialog = el.querySelector('[data-pynext-command-dialog]');
                dialog.setAttribute('data-state', 'closed');
            },
            filter: function(el, query) {
                const items = el.querySelectorAll('[data-pynext-command-item]');
                const groups = el.querySelectorAll('[data-pynext-command-group]');
                
                items.forEach(item => {
                    const text = item.textContent.toLowerCase();
                    const keywords = item.dataset.keywords?.toLowerCase() || '';
                    const matches = text.includes(query.toLowerCase()) || keywords.includes(query.toLowerCase());
                    item.hidden = !matches;
                });
                
                // Hide empty groups
                groups.forEach(group => {
                    const visibleItems = group.querySelectorAll('[data-pynext-command-item]:not([hidden])');
                    group.hidden = visibleItems.length === 0;
                });
            }
        };
    });
    
    afterEach(() => {
        document.body.removeChild(container);
    });
    
    test('opens on Cmd+K', () => {
        container.innerHTML = `
            <div data-pynext-command>
                <div data-pynext-command-dialog data-state="closed">
                    <input data-pynext-command-input placeholder="Search...">
                </div>
            </div>
        `;
        
        const command = container.querySelector('[data-pynext-command]');
        window.__pynext__.ui.command.open(command);
        
        const dialog = container.querySelector('[data-pynext-command-dialog]');
        expect(dialog.getAttribute('data-state')).toBe('open');
    });
    
    test('filters items on input', () => {
        container.innerHTML = `
            <div data-pynext-command>
                <input data-pynext-command-input>
                <div data-pynext-command-item>Open File</div>
                <div data-pynext-command-item>Save File</div>
                <div data-pynext-command-item>Close Tab</div>
            </div>
        `;
        
        const command = container.querySelector('[data-pynext-command]');
        window.__pynext__.ui.command.filter(command, 'file');
        
        const items = container.querySelectorAll('[data-pynext-command-item]');
        expect(items[0].hidden).toBe(false); // Open File
        expect(items[1].hidden).toBe(false); // Save File
        expect(items[2].hidden).toBe(true);  // Close Tab
    });
    
    test('filters by keywords', () => {
        container.innerHTML = `
            <div data-pynext-command>
                <input data-pynext-command-input>
                <div data-pynext-command-item data-keywords="git version control">Commit Changes</div>
                <div data-pynext-command-item>Open File</div>
            </div>
        `;
        
        const command = container.querySelector('[data-pynext-command]');
        window.__pynext__.ui.command.filter(command, 'git');
        
        const items = container.querySelectorAll('[data-pynext-command-item]');
        expect(items[0].hidden).toBe(false); // Commit Changes (has git keyword)
        expect(items[1].hidden).toBe(true);  // Open File
    });
    
    test('hides empty groups', () => {
        container.innerHTML = `
            <div data-pynext-command>
                <div data-pynext-command-group data-heading="Files">
                    <div data-pynext-command-item>Open File</div>
                </div>
                <div data-pynext-command-group data-heading="Git">
                    <div data-pynext-command-item>Commit</div>
                </div>
            </div>
        `;
        
        const command = container.querySelector('[data-pynext-command]');
        window.__pynext__.ui.command.filter(command, 'file');
        
        const groups = container.querySelectorAll('[data-pynext-command-group]');
        expect(groups[0].hidden).toBe(false); // Files group
        expect(groups[1].hidden).toBe(true);  // Git group (no matches)
    });
    
    test('closes on Escape', () => {
        container.innerHTML = `
            <div data-pynext-command>
                <div data-pynext-command-dialog data-state="open">Content</div>
            </div>
        `;
        
        const command = container.querySelector('[data-pynext-command]');
        window.__pynext__.ui.command.close(command);
        
        const dialog = container.querySelector('[data-pynext-command-dialog]');
        expect(dialog.getAttribute('data-state')).toBe('closed');
    });
});

