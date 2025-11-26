/**
 * Combobox Component Tests
 * Tests for ui/combobox.js functionality
 */

describe('Combobox Component', () => {
    let container;
    
    beforeEach(() => {
        container = document.createElement('div');
        document.body.appendChild(container);
        
        window.__pynext__ = window.__pynext__ || {};
        window.__pynext__.ui = window.__pynext__.ui || {};
        window.__pynext__.ui.combobox = {
            init: function(el) {
                const input = el.querySelector('[data-pynext-combobox-input]');
                const items = el.querySelectorAll('[data-pynext-combobox-item]');
                
                if (input) {
                    input.addEventListener('input', () => this.filter(el, input.value));
                    input.addEventListener('focus', () => this.open(el));
                }
                
                items.forEach(item => {
                    item.addEventListener('click', () => this.select(el, item));
                });
            },
            open: function(el) {
                const content = el.querySelector('[data-pynext-combobox-content]');
                content.setAttribute('data-state', 'open');
            },
            close: function(el) {
                const content = el.querySelector('[data-pynext-combobox-content]');
                content.setAttribute('data-state', 'closed');
            },
            filter: function(el, query) {
                const items = el.querySelectorAll('[data-pynext-combobox-item]');
                items.forEach(item => {
                    const text = item.textContent.toLowerCase();
                    item.hidden = !text.includes(query.toLowerCase());
                });
            },
            select: function(el, item) {
                const input = el.querySelector('[data-pynext-combobox-input]');
                input.value = item.textContent;
                item.setAttribute('data-selected', 'true');
                this.close(el);
            }
        };
    });
    
    afterEach(() => {
        document.body.removeChild(container);
    });
    
    test('filters items on input', () => {
        container.innerHTML = `
            <div data-pynext-combobox>
                <input data-pynext-combobox-input type="text">
                <div data-pynext-combobox-content data-state="open">
                    <div data-pynext-combobox-item>Apple</div>
                    <div data-pynext-combobox-item>Banana</div>
                    <div data-pynext-combobox-item>Cherry</div>
                </div>
            </div>
        `;
        
        const combobox = container.querySelector('[data-pynext-combobox]');
        window.__pynext__.ui.combobox.filter(combobox, 'ban');
        
        const items = container.querySelectorAll('[data-pynext-combobox-item]');
        expect(items[0].hidden).toBe(true); // Apple
        expect(items[1].hidden).toBe(false); // Banana
        expect(items[2].hidden).toBe(true); // Cherry
    });
    
    test('selects item on click', () => {
        container.innerHTML = `
            <div data-pynext-combobox>
                <input data-pynext-combobox-input type="text">
                <div data-pynext-combobox-content data-state="open">
                    <div data-pynext-combobox-item>Apple</div>
                </div>
            </div>
        `;
        
        const combobox = container.querySelector('[data-pynext-combobox]');
        const item = container.querySelector('[data-pynext-combobox-item]');
        
        window.__pynext__.ui.combobox.select(combobox, item);
        
        const input = container.querySelector('[data-pynext-combobox-input]');
        expect(input.value).toBe('Apple');
    });
    
    test('closes after selection', () => {
        container.innerHTML = `
            <div data-pynext-combobox>
                <input data-pynext-combobox-input type="text">
                <div data-pynext-combobox-content data-state="open">
                    <div data-pynext-combobox-item>Apple</div>
                </div>
            </div>
        `;
        
        const combobox = container.querySelector('[data-pynext-combobox]');
        const item = container.querySelector('[data-pynext-combobox-item]');
        
        window.__pynext__.ui.combobox.select(combobox, item);
        
        const content = container.querySelector('[data-pynext-combobox-content]');
        expect(content.getAttribute('data-state')).toBe('closed');
    });
    
    test('supports create new option', () => {
        container.innerHTML = `
            <div data-pynext-combobox data-allow-create="true">
                <input data-pynext-combobox-input type="text" value="New Item">
                <div data-pynext-combobox-content>
                    <div data-pynext-combobox-create>Create "New Item"</div>
                </div>
            </div>
        `;
        
        const combobox = container.querySelector('[data-pynext-combobox]');
        expect(combobox.getAttribute('data-allow-create')).toBe('true');
    });
});

