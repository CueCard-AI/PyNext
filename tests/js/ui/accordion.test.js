/**
 * Accordion Component Tests
 * Tests for ui/accordion.js functionality
 */

describe('Accordion Component', () => {
    let container;
    
    beforeEach(() => {
        container = document.createElement('div');
        document.body.appendChild(container);
        
        window.__pynext__ = window.__pynext__ || {};
        window.__pynext__.ui = window.__pynext__.ui || {};
        window.__pynext__.ui.accordion = {
            init: function(el) {
                const items = el.querySelectorAll('[data-pynext-accordion-item]');
                items.forEach(item => {
                    const trigger = item.querySelector('[data-pynext-accordion-trigger]');
                    if (trigger) {
                        trigger.addEventListener('click', () => this.toggle(el, item));
                    }
                });
            },
            toggle: function(el, item) {
                const content = item.querySelector('[data-pynext-accordion-content]');
                const trigger = item.querySelector('[data-pynext-accordion-trigger]');
                const isOpen = content.getAttribute('data-state') === 'open';
                
                // If single mode, close others
                if (el.getAttribute('data-type') !== 'multiple') {
                    el.querySelectorAll('[data-pynext-accordion-content]').forEach(c => {
                        c.setAttribute('data-state', 'closed');
                    });
                    el.querySelectorAll('[data-pynext-accordion-trigger]').forEach(t => {
                        t.setAttribute('aria-expanded', 'false');
                    });
                }
                
                content.setAttribute('data-state', isOpen ? 'closed' : 'open');
                trigger.setAttribute('aria-expanded', isOpen ? 'false' : 'true');
            }
        };
    });
    
    afterEach(() => {
        document.body.removeChild(container);
    });
    
    test('expands on trigger click', () => {
        container.innerHTML = `
            <div data-pynext-accordion>
                <div data-pynext-accordion-item>
                    <button data-pynext-accordion-trigger aria-expanded="false">Title</button>
                    <div data-pynext-accordion-content data-state="closed">Content</div>
                </div>
            </div>
        `;
        
        const accordion = container.querySelector('[data-pynext-accordion]');
        window.__pynext__.ui.accordion.init(accordion);
        
        const trigger = container.querySelector('[data-pynext-accordion-trigger]');
        trigger.click();
        
        const content = container.querySelector('[data-pynext-accordion-content]');
        expect(content.getAttribute('data-state')).toBe('open');
        expect(trigger.getAttribute('aria-expanded')).toBe('true');
    });
    
    test('collapses on second click', () => {
        container.innerHTML = `
            <div data-pynext-accordion>
                <div data-pynext-accordion-item>
                    <button data-pynext-accordion-trigger aria-expanded="true">Title</button>
                    <div data-pynext-accordion-content data-state="open">Content</div>
                </div>
            </div>
        `;
        
        const accordion = container.querySelector('[data-pynext-accordion]');
        const item = container.querySelector('[data-pynext-accordion-item]');
        
        window.__pynext__.ui.accordion.toggle(accordion, item);
        
        const content = container.querySelector('[data-pynext-accordion-content]');
        expect(content.getAttribute('data-state')).toBe('closed');
    });
    
    test('single mode closes others', () => {
        container.innerHTML = `
            <div data-pynext-accordion data-type="single">
                <div data-pynext-accordion-item id="item1">
                    <button data-pynext-accordion-trigger>Item 1</button>
                    <div data-pynext-accordion-content data-state="open">Content 1</div>
                </div>
                <div data-pynext-accordion-item id="item2">
                    <button data-pynext-accordion-trigger>Item 2</button>
                    <div data-pynext-accordion-content data-state="closed">Content 2</div>
                </div>
            </div>
        `;
        
        const accordion = container.querySelector('[data-pynext-accordion]');
        const item2 = container.querySelector('#item2');
        
        window.__pynext__.ui.accordion.toggle(accordion, item2);
        
        const content1 = container.querySelector('#item1 [data-pynext-accordion-content]');
        const content2 = container.querySelector('#item2 [data-pynext-accordion-content]');
        
        expect(content1.getAttribute('data-state')).toBe('closed');
        expect(content2.getAttribute('data-state')).toBe('open');
    });
    
    test('multiple mode keeps others open', () => {
        container.innerHTML = `
            <div data-pynext-accordion data-type="multiple">
                <div data-pynext-accordion-item id="item1">
                    <button data-pynext-accordion-trigger>Item 1</button>
                    <div data-pynext-accordion-content data-state="open">Content 1</div>
                </div>
                <div data-pynext-accordion-item id="item2">
                    <button data-pynext-accordion-trigger>Item 2</button>
                    <div data-pynext-accordion-content data-state="closed">Content 2</div>
                </div>
            </div>
        `;
        
        const accordion = container.querySelector('[data-pynext-accordion]');
        const item2 = container.querySelector('#item2');
        
        window.__pynext__.ui.accordion.toggle(accordion, item2);
        
        const content1 = container.querySelector('#item1 [data-pynext-accordion-content]');
        const content2 = container.querySelector('#item2 [data-pynext-accordion-content]');
        
        expect(content1.getAttribute('data-state')).toBe('open');
        expect(content2.getAttribute('data-state')).toBe('open');
    });
});

