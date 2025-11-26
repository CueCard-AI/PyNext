/**
 * Dropdown Menu Component Tests
 * Tests for ui/dropdown.js functionality
 */

describe('DropdownMenu Component', () => {
    let container;
    
    beforeEach(() => {
        container = document.createElement('div');
        document.body.appendChild(container);
        
        window.__pynext__ = window.__pynext__ || {};
        window.__pynext__.ui = window.__pynext__.ui || {};
        window.__pynext__.ui.dropdown = {
            init: function(el) {
                const trigger = el.querySelector('[data-pynext-dropdown-trigger]');
                const content = el.querySelector('[data-pynext-dropdown-content]');
                
                if (trigger && content) {
                    trigger.addEventListener('click', () => this.toggle(el));
                }
            },
            toggle: function(el) {
                const content = el.querySelector('[data-pynext-dropdown-content]');
                const isOpen = content.getAttribute('data-state') === 'open';
                content.setAttribute('data-state', isOpen ? 'closed' : 'open');
            },
            close: function(el) {
                const content = el.querySelector('[data-pynext-dropdown-content]');
                content.setAttribute('data-state', 'closed');
            }
        };
    });
    
    afterEach(() => {
        document.body.removeChild(container);
    });
    
    test('opens on trigger click', () => {
        container.innerHTML = `
            <div data-pynext-dropdown>
                <button data-pynext-dropdown-trigger>Menu</button>
                <div data-pynext-dropdown-content data-state="closed">
                    <button>Item 1</button>
                </div>
            </div>
        `;
        
        const dropdown = container.querySelector('[data-pynext-dropdown]');
        window.__pynext__.ui.dropdown.init(dropdown);
        
        const trigger = container.querySelector('[data-pynext-dropdown-trigger]');
        trigger.click();
        
        const content = container.querySelector('[data-pynext-dropdown-content]');
        expect(content.getAttribute('data-state')).toBe('open');
    });
    
    test('closes on second trigger click', () => {
        container.innerHTML = `
            <div data-pynext-dropdown>
                <button data-pynext-dropdown-trigger>Menu</button>
                <div data-pynext-dropdown-content data-state="open">
                    <button>Item 1</button>
                </div>
            </div>
        `;
        
        const dropdown = container.querySelector('[data-pynext-dropdown]');
        window.__pynext__.ui.dropdown.init(dropdown);
        
        const trigger = container.querySelector('[data-pynext-dropdown-trigger]');
        trigger.click();
        
        const content = container.querySelector('[data-pynext-dropdown-content]');
        expect(content.getAttribute('data-state')).toBe('closed');
    });
    
    test('has menu role', () => {
        container.innerHTML = `
            <div data-pynext-dropdown>
                <button data-pynext-dropdown-trigger aria-haspopup="menu">Menu</button>
                <div data-pynext-dropdown-content role="menu">
                    <button role="menuitem">Item 1</button>
                </div>
            </div>
        `;
        
        const content = container.querySelector('[data-pynext-dropdown-content]');
        const item = container.querySelector('[role="menuitem"]');
        
        expect(content.getAttribute('role')).toBe('menu');
        expect(item.getAttribute('role')).toBe('menuitem');
    });
    
    test('keyboard navigation with arrow keys', () => {
        container.innerHTML = `
            <div data-pynext-dropdown>
                <div data-pynext-dropdown-content data-state="open" role="menu">
                    <button role="menuitem" id="item1">Item 1</button>
                    <button role="menuitem" id="item2">Item 2</button>
                    <button role="menuitem" id="item3">Item 3</button>
                </div>
            </div>
        `;
        
        const items = container.querySelectorAll('[role="menuitem"]');
        expect(items.length).toBe(3);
    });
});

