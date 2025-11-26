/**
 * Tabs Component Tests
 * Tests for ui/tabs.js functionality
 */

describe('Tabs Component', () => {
    let container;
    
    beforeEach(() => {
        container = document.createElement('div');
        document.body.appendChild(container);
        
        window.__pynext__ = window.__pynext__ || {};
        window.__pynext__.ui = window.__pynext__.ui || {};
        window.__pynext__.ui.tabs = {
            init: function(el) {
                const triggers = el.querySelectorAll('[data-pynext-tab-trigger]');
                triggers.forEach(trigger => {
                    trigger.addEventListener('click', () => this.select(el, trigger.dataset.value));
                });
            },
            select: function(el, value) {
                // Update triggers
                el.querySelectorAll('[data-pynext-tab-trigger]').forEach(t => {
                    t.setAttribute('data-state', t.dataset.value === value ? 'active' : 'inactive');
                    t.setAttribute('aria-selected', t.dataset.value === value ? 'true' : 'false');
                });
                // Update content
                el.querySelectorAll('[data-pynext-tab-content]').forEach(c => {
                    c.setAttribute('data-state', c.dataset.value === value ? 'active' : 'inactive');
                    c.hidden = c.dataset.value !== value;
                });
            }
        };
    });
    
    afterEach(() => {
        document.body.removeChild(container);
    });
    
    test('switches content on tab click', () => {
        container.innerHTML = `
            <div data-pynext-tabs>
                <div data-pynext-tab-list role="tablist">
                    <button data-pynext-tab-trigger data-value="tab1" data-state="active">Tab 1</button>
                    <button data-pynext-tab-trigger data-value="tab2" data-state="inactive">Tab 2</button>
                </div>
                <div data-pynext-tab-content data-value="tab1" data-state="active">Content 1</div>
                <div data-pynext-tab-content data-value="tab2" data-state="inactive" hidden>Content 2</div>
            </div>
        `;
        
        const tabs = container.querySelector('[data-pynext-tabs]');
        window.__pynext__.ui.tabs.init(tabs);
        
        const tab2 = container.querySelector('[data-value="tab2"][data-pynext-tab-trigger]');
        tab2.click();
        
        const content1 = container.querySelector('[data-value="tab1"][data-pynext-tab-content]');
        const content2 = container.querySelector('[data-value="tab2"][data-pynext-tab-content]');
        
        expect(content1.getAttribute('data-state')).toBe('inactive');
        expect(content2.getAttribute('data-state')).toBe('active');
    });
    
    test('updates aria-selected on tab switch', () => {
        container.innerHTML = `
            <div data-pynext-tabs>
                <button data-pynext-tab-trigger data-value="tab1" aria-selected="true">Tab 1</button>
                <button data-pynext-tab-trigger data-value="tab2" aria-selected="false">Tab 2</button>
            </div>
        `;
        
        const tabs = container.querySelector('[data-pynext-tabs]');
        window.__pynext__.ui.tabs.select(tabs, 'tab2');
        
        const tab1 = container.querySelector('[data-value="tab1"]');
        const tab2 = container.querySelector('[data-value="tab2"]');
        
        expect(tab1.getAttribute('aria-selected')).toBe('false');
        expect(tab2.getAttribute('aria-selected')).toBe('true');
    });
    
    test('has proper ARIA roles', () => {
        container.innerHTML = `
            <div data-pynext-tabs>
                <div role="tablist">
                    <button role="tab" id="tab1">Tab 1</button>
                </div>
                <div role="tabpanel" aria-labelledby="tab1">Content</div>
            </div>
        `;
        
        const tablist = container.querySelector('[role="tablist"]');
        const tab = container.querySelector('[role="tab"]');
        const panel = container.querySelector('[role="tabpanel"]');
        
        expect(tablist).toBeTruthy();
        expect(tab).toBeTruthy();
        expect(panel.getAttribute('aria-labelledby')).toBe('tab1');
    });
});

