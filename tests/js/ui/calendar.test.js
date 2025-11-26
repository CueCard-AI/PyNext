/**
 * Calendar Component Tests
 * Tests for ui/calendar.js functionality
 */

describe('Calendar Component', () => {
    let container;
    
    beforeEach(() => {
        container = document.createElement('div');
        document.body.appendChild(container);
        
        window.__pynext__ = window.__pynext__ || {};
        window.__pynext__.ui = window.__pynext__.ui || {};
        window.__pynext__.ui.calendar = {
            init: function(el) {
                const prevBtn = el.querySelector('[data-pynext-calendar-prev]');
                const nextBtn = el.querySelector('[data-pynext-calendar-next]');
                const days = el.querySelectorAll('[data-pynext-calendar-day]');
                
                if (prevBtn) {
                    prevBtn.addEventListener('click', () => this.prevMonth(el));
                }
                if (nextBtn) {
                    nextBtn.addEventListener('click', () => this.nextMonth(el));
                }
                days.forEach(day => {
                    day.addEventListener('click', () => this.selectDay(el, day));
                });
            },
            getDate: function(el) {
                const year = parseInt(el.dataset.year);
                const month = parseInt(el.dataset.month);
                return new Date(year, month, 1);
            },
            setDate: function(el, date) {
                el.dataset.year = date.getFullYear();
                el.dataset.month = date.getMonth();
            },
            prevMonth: function(el) {
                const date = this.getDate(el);
                date.setMonth(date.getMonth() - 1);
                this.setDate(el, date);
            },
            nextMonth: function(el) {
                const date = this.getDate(el);
                date.setMonth(date.getMonth() + 1);
                this.setDate(el, date);
            },
            selectDay: function(el, day) {
                // Deselect others
                el.querySelectorAll('[data-pynext-calendar-day]').forEach(d => {
                    d.setAttribute('data-selected', 'false');
                });
                day.setAttribute('data-selected', 'true');
            }
        };
    });
    
    afterEach(() => {
        document.body.removeChild(container);
    });
    
    test('navigates to previous month', () => {
        container.innerHTML = `
            <div data-pynext-calendar data-year="2024" data-month="5">
                <button data-pynext-calendar-prev>←</button>
                <button data-pynext-calendar-next>→</button>
            </div>
        `;
        
        const calendar = container.querySelector('[data-pynext-calendar]');
        window.__pynext__.ui.calendar.prevMonth(calendar);
        
        expect(calendar.dataset.month).toBe('4');
    });
    
    test('navigates to next month', () => {
        container.innerHTML = `
            <div data-pynext-calendar data-year="2024" data-month="5">
                <button data-pynext-calendar-prev>←</button>
                <button data-pynext-calendar-next>→</button>
            </div>
        `;
        
        const calendar = container.querySelector('[data-pynext-calendar]');
        window.__pynext__.ui.calendar.nextMonth(calendar);
        
        expect(calendar.dataset.month).toBe('6');
    });
    
    test('handles year rollover (December to January)', () => {
        container.innerHTML = `
            <div data-pynext-calendar data-year="2024" data-month="11">
            </div>
        `;
        
        const calendar = container.querySelector('[data-pynext-calendar]');
        window.__pynext__.ui.calendar.nextMonth(calendar);
        
        expect(calendar.dataset.month).toBe('0');
        expect(calendar.dataset.year).toBe('2025');
    });
    
    test('handles year rollover (January to December)', () => {
        container.innerHTML = `
            <div data-pynext-calendar data-year="2024" data-month="0">
            </div>
        `;
        
        const calendar = container.querySelector('[data-pynext-calendar]');
        window.__pynext__.ui.calendar.prevMonth(calendar);
        
        expect(calendar.dataset.month).toBe('11');
        expect(calendar.dataset.year).toBe('2023');
    });
    
    test('selects day on click', () => {
        container.innerHTML = `
            <div data-pynext-calendar>
                <button data-pynext-calendar-day data-date="2024-06-15" data-selected="false">15</button>
                <button data-pynext-calendar-day data-date="2024-06-16" data-selected="false">16</button>
            </div>
        `;
        
        const calendar = container.querySelector('[data-pynext-calendar]');
        const day15 = container.querySelector('[data-date="2024-06-15"]');
        
        window.__pynext__.ui.calendar.selectDay(calendar, day15);
        
        expect(day15.getAttribute('data-selected')).toBe('true');
    });
    
    test('deselects other days on selection', () => {
        container.innerHTML = `
            <div data-pynext-calendar>
                <button data-pynext-calendar-day data-date="2024-06-15" data-selected="true">15</button>
                <button data-pynext-calendar-day data-date="2024-06-16" data-selected="false">16</button>
            </div>
        `;
        
        const calendar = container.querySelector('[data-pynext-calendar]');
        const day16 = container.querySelector('[data-date="2024-06-16"]');
        
        window.__pynext__.ui.calendar.selectDay(calendar, day16);
        
        const day15 = container.querySelector('[data-date="2024-06-15"]');
        expect(day15.getAttribute('data-selected')).toBe('false');
        expect(day16.getAttribute('data-selected')).toBe('true');
    });
    
    test('supports localization', () => {
        container.innerHTML = `
            <div data-pynext-calendar data-locale="es" data-week-starts-on="1">
                <div data-pynext-calendar-weekday>Lun</div>
                <div data-pynext-calendar-month>Junio</div>
            </div>
        `;
        
        const calendar = container.querySelector('[data-pynext-calendar]');
        expect(calendar.getAttribute('data-locale')).toBe('es');
        expect(calendar.getAttribute('data-week-starts-on')).toBe('1');
    });
});

