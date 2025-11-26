/**
 * PyNext Calendar & DatePicker Runtime
 * Size target: ~1.5 KB minified
 */
(function(g) {
    'use strict';
    
    var ui = g.__pynext__.ui;
    
    function initCalendars() {
        document.querySelectorAll('[data-pynext-calendar]').forEach(initCalendar);
    }
    
    function initCalendar(calendar) {
        // Navigation
        ui.on('click', '[data-pynext-calendar-prev]', function(e, btn) {
            if (!calendar.contains(btn)) return;
            navigateMonth(calendar, -1);
        });
        
        ui.on('click', '[data-pynext-calendar-next]', function(e, btn) {
            if (!calendar.contains(btn)) return;
            navigateMonth(calendar, 1);
        });
        
        // Day selection
        ui.on('click', '[data-pynext-calendar-day]', function(e, day) {
            if (!calendar.contains(day)) return;
            if (day.hasAttribute('disabled')) return;
            
            var date = day.dataset.pynextCalendarDay;
            var mode = calendar.dataset.pynextCalendarMode || 'single';
            
            if (mode === 'single') {
                calendar.querySelectorAll('[data-pynext-calendar-day]').forEach(function(d) {
                    d.setAttribute('data-selected', 'false');
                });
                day.setAttribute('data-selected', 'true');
                
                calendar.dispatchEvent(new CustomEvent('pynext:calendar-select', {
                    bubbles: true,
                    detail: { date: date }
                }));
            } else if (mode === 'range') {
                handleRangeSelect(calendar, day, date);
            }
        });
    }
    
    function handleRangeSelect(calendar, day, date) {
        var rangeStart = calendar.dataset.rangeStart;
        
        if (!rangeStart) {
            // First selection - set start
            calendar.querySelectorAll('[data-pynext-calendar-day]').forEach(function(d) {
                d.setAttribute('data-selected', 'false');
                d.setAttribute('data-range', 'false');
            });
            day.setAttribute('data-selected', 'true');
            calendar.dataset.rangeStart = date;
        } else {
            // Second selection - set end
            var start = new Date(rangeStart);
            var end = new Date(date);
            
            if (end < start) {
                var tmp = start;
                start = end;
                end = tmp;
            }
            
            calendar.querySelectorAll('[data-pynext-calendar-day]').forEach(function(d) {
                var dayDate = new Date(d.dataset.pynextCalendarDay);
                if (dayDate >= start && dayDate <= end) {
                    d.setAttribute('data-selected', 'true');
                    d.setAttribute('data-range', 'true');
                }
            });
            
            delete calendar.dataset.rangeStart;
            
            calendar.dispatchEvent(new CustomEvent('pynext:calendar-range', {
                bubbles: true,
                detail: { from: start.toISOString().split('T')[0], to: end.toISOString().split('T')[0] }
            }));
        }
    }
    
    function navigateMonth(calendar, direction) {
        var current = calendar.dataset.currentMonth;
        if (!current) current = new Date().toISOString().slice(0, 7);
        
        var date = new Date(current + '-01');
        date.setMonth(date.getMonth() + direction);
        
        var newMonth = date.toISOString().slice(0, 7);
        calendar.dataset.currentMonth = newMonth;
        
        calendar.dispatchEvent(new CustomEvent('pynext:calendar-navigate', {
            bubbles: true,
            detail: { month: newMonth }
        }));
    }
    
    // DatePicker
    function initDatePickers() {
        ui.on('click', '[data-pynext-datepicker-trigger]', function(e, trigger) {
            var picker = trigger.closest('[data-pynext-datepicker]');
            var popover = picker.querySelector('[data-pynext-datepicker-popover]');
            
            if (popover.hasAttribute('hidden')) {
                popover.removeAttribute('hidden');
                popover.setAttribute('data-state', 'open');
            } else {
                popover.setAttribute('hidden', '');
                popover.setAttribute('data-state', 'closed');
            }
        });
        
        // Close on select
        document.addEventListener('pynext:calendar-select', function(e) {
            var picker = e.target.closest('[data-pynext-datepicker]');
            if (picker) {
                var popover = picker.querySelector('[data-pynext-datepicker-popover]');
                var trigger = picker.querySelector('[data-pynext-datepicker-trigger]');
                
                if (popover) {
                    popover.setAttribute('hidden', '');
                    popover.setAttribute('data-state', 'closed');
                }
                
                if (trigger) trigger.textContent = e.detail.date;
            }
        });
    }
    
    initCalendars();
    initDatePickers();
    
})(window);

