"""
Calendar Component

A date picker calendar with single and range selection support.

Usage:
    from pynext.shadcn import Calendar
    
    # Single date selection
    Calendar(
        selected=date_signal,
        on_select=lambda d: date_signal.set(d)
    )
    
    # Range selection
    Calendar(
        mode="range",
        selected=date_range_signal,
        on_select=lambda r: date_range_signal.set(r)
    )
    
    # With date restrictions
    Calendar(
        selected=date_signal,
        disabled_dates=[datetime(2024, 12, 25)],  # Christmas
        min_date=datetime.now(),  # No past dates
        max_date=datetime(2025, 12, 31),  # Up to end of 2025
    )
"""

from typing import Any, Optional, List, Union, Callable, Literal
from datetime import datetime, date
from pynext.tw import cn
import calendar
import hashlib


# Calendar container styles
CALENDAR_BASE = "p-3"

# Header styles (month/year navigation)
CALENDAR_HEADER_BASE = "relative flex items-center justify-center pt-1"
CALENDAR_NAV_BUTTON_BASE = (
    "inline-flex h-7 w-7 items-center justify-center rounded-md border "
    "border-input bg-transparent opacity-50 hover:opacity-100 "
    "absolute"
)
CALENDAR_CAPTION_BASE = "text-sm font-medium"

# Week days header
CALENDAR_WEEKDAYS_BASE = "flex"
CALENDAR_WEEKDAY_BASE = (
    "text-muted-foreground rounded-md w-9 font-normal text-[0.8rem] text-center"
)

# Days grid
CALENDAR_DAYS_BASE = "w-full border-collapse space-y-1"
CALENDAR_WEEK_BASE = "flex w-full mt-2"

# Day button styles
CALENDAR_DAY_BASE = (
    "h-9 w-9 text-center text-sm p-0 relative "
    "inline-flex items-center justify-center rounded-md "
    "[&:has([aria-selected])]:bg-accent "
    "first:[&:has([aria-selected])]:rounded-l-md "
    "last:[&:has([aria-selected])]:rounded-r-md "
    "focus-within:relative focus-within:z-20"
)

CALENDAR_DAY_BUTTON_BASE = (
    "inline-flex h-9 w-9 items-center justify-center rounded-md text-sm "
    "font-normal ring-offset-background transition-colors "
    "hover:bg-accent hover:text-accent-foreground "
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring "
    "focus-visible:ring-offset-2"
)

# Day states
CALENDAR_DAY_SELECTED = "bg-primary text-primary-foreground hover:bg-primary hover:text-primary-foreground"
CALENDAR_DAY_TODAY = "bg-accent text-accent-foreground"
CALENDAR_DAY_OUTSIDE = "text-muted-foreground opacity-50"
CALENDAR_DAY_DISABLED = "text-muted-foreground opacity-50 cursor-not-allowed"
CALENDAR_DAY_RANGE_MIDDLE = "bg-accent/50"


# Default locale settings (English)
DEFAULT_WEEKDAY_NAMES = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]
DEFAULT_MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

# Common locale presets
LOCALES = {
    "en": {
        "weekdays": ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"],
        "months": ["January", "February", "March", "April", "May", "June",
                   "July", "August", "September", "October", "November", "December"],
        "start_week": 0,  # Sunday
    },
    "en-GB": {
        "weekdays": ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"],
        "months": ["January", "February", "March", "April", "May", "June",
                   "July", "August", "September", "October", "November", "December"],
        "start_week": 1,  # Monday
    },
    "es": {
        "weekdays": ["Lu", "Ma", "Mi", "Ju", "Vi", "Sá", "Do"],
        "months": ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                   "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"],
        "start_week": 1,
    },
    "fr": {
        "weekdays": ["Lu", "Ma", "Me", "Je", "Ve", "Sa", "Di"],
        "months": ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
                   "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"],
        "start_week": 1,
    },
    "de": {
        "weekdays": ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"],
        "months": ["Januar", "Februar", "März", "April", "Mai", "Juni",
                   "Juli", "August", "September", "Oktober", "November", "Dezember"],
        "start_week": 1,
    },
    "ja": {
        "weekdays": ["日", "月", "火", "水", "木", "金", "土"],
        "months": ["1月", "2月", "3月", "4月", "5月", "6月",
                   "7月", "8月", "9月", "10月", "11月", "12月"],
        "start_week": 0,
    },
    "zh": {
        "weekdays": ["日", "一", "二", "三", "四", "五", "六"],
        "months": ["一月", "二月", "三月", "四月", "五月", "六月",
                   "七月", "八月", "九月", "十月", "十一月", "十二月"],
        "start_week": 0,
    },
    "pt": {
        "weekdays": ["Do", "Se", "Te", "Qu", "Qu", "Se", "Sá"],
        "months": ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                   "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"],
        "start_week": 0,
    },
}


class Calendar:
    """
    A calendar for date selection.
    
    Attributes:
        mode: "single" for one date, "range" for date range
        selected: Currently selected date(s)
        on_select: Callback when date is selected
        default_month: Initial month to display
        disabled_dates: List of dates to disable
        min_date: Minimum selectable date
        max_date: Maximum selectable date
        show_outside_days: Show days from prev/next months
        locale: Locale for weekday/month names ("en", "es", "fr", "de", "ja", "zh", "pt", "en-GB")
        weekday_names: Custom weekday names (overrides locale)
        month_names: Custom month names (overrides locale)
        week_starts_on: Day week starts (0=Sunday, 1=Monday, overrides locale)
        class_: Additional CSS classes
    
    Example:
        # Default (English, Sunday start)
        Calendar(
            selected=selected_date,
            on_select=lambda d: selected_date.set(d),
        )
        
        # Spanish locale
        Calendar(
            selected=selected_date,
            locale="es",
        )
        
        # Custom weekday names
        Calendar(
            selected=selected_date,
            weekday_names=["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
        )
        
        # Monday start (European style)
        Calendar(
            selected=selected_date,
            week_starts_on=1,
        )
    """
    
    def __init__(
        self,
        mode: Literal["single", "range"] = "single",
        selected: Optional[Union[date, datetime, dict]] = None,
        on_select: Optional[Callable] = None,
        default_month: Optional[Union[date, datetime]] = None,
        disabled_dates: Optional[List[Union[date, datetime]]] = None,
        min_date: Optional[Union[date, datetime]] = None,
        max_date: Optional[Union[date, datetime]] = None,
        show_outside_days: bool = True,
        locale: Optional[str] = None,
        weekday_names: Optional[List[str]] = None,
        month_names: Optional[List[str]] = None,
        week_starts_on: Optional[int] = None,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.mode = mode
        self.selected = selected
        self.on_select = on_select
        self.default_month = default_month or datetime.now()
        self.disabled_dates = disabled_dates or []
        self.min_date = min_date
        self.max_date = max_date
        self.show_outside_days = show_outside_days
        self.extra_class = class_
        self.attrs = attrs
        
        # Handle localization
        locale_config = LOCALES.get(locale, LOCALES["en"]) if locale else LOCALES["en"]
        self.weekday_names = weekday_names or locale_config["weekdays"]
        self.month_names = month_names or locale_config["months"]
        self.week_starts_on = week_starts_on if week_starts_on is not None else locale_config["start_week"]
    
    def render(self) -> str:
        cal_id = hashlib.md5(str(id(self)).encode()).hexdigest()[:8]
        class_str = cn(CALENDAR_BASE, self.extra_class)
        
        # Get the month to display
        display_date = self.default_month
        if isinstance(display_date, datetime):
            display_date = display_date.date() if hasattr(display_date, 'date') else display_date
        
        year = display_date.year if hasattr(display_date, 'year') else datetime.now().year
        month = display_date.month if hasattr(display_date, 'month') else datetime.now().month
        
        # Build calendar structure
        header = self._render_header(year, month)
        weekdays = self._render_weekdays()
        days = self._render_days(year, month)
        
        # Selected date(s) as data attributes
        selected_attr = ""
        if self.selected:
            if self.mode == "single" and self.selected:
                d = self.selected
                if hasattr(d, 'isoformat'):
                    selected_attr = f'data-selected="{d.isoformat()}"'
            elif self.mode == "range" and isinstance(self.selected, dict):
                start = self.selected.get('start')
                end = self.selected.get('end')
                if start:
                    selected_attr += f' data-range-start="{start.isoformat()}"'
                if end:
                    selected_attr += f' data-range-end="{end.isoformat()}"'
        
        return f'''
<div data-pynext-calendar="{cal_id}"
     data-mode="{self.mode}"
     data-year="{year}"
     data-month="{month}"
     {selected_attr}
     class="{class_str}">
    {header}
    <table class="{cn(CALENDAR_DAYS_BASE)}" role="grid">
        {weekdays}
        {days}
    </table>
</div>
'''
    
    def _render_header(self, year: int, month: int) -> str:
        # Use localized month name (month is 1-indexed, list is 0-indexed)
        month_name = self.month_names[month - 1]
        
        nav_prev = f'''
<button type="button" 
        data-pynext-calendar-prev
        class="{cn(CALENDAR_NAV_BUTTON_BASE, 'left-1')}"
        aria-label="Previous month">
    <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
    </svg>
</button>
'''
        
        nav_next = f'''
<button type="button"
        data-pynext-calendar-next
        class="{cn(CALENDAR_NAV_BUTTON_BASE, 'right-1')}"
        aria-label="Next month">
    <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
    </svg>
</button>
'''
        
        return f'''
<div class="{cn(CALENDAR_HEADER_BASE)}">
    {nav_prev}
    <div class="{cn(CALENDAR_CAPTION_BASE)}" data-pynext-calendar-caption>
        {month_name} {year}
    </div>
    {nav_next}
</div>
'''
    
    def _render_weekdays(self) -> str:
        # Get localized weekday names, rotated based on week_starts_on
        # self.weekday_names is [Sun, Mon, Tue, Wed, Thu, Fri, Sat] for week_starts_on=0
        # Need to rotate if week_starts_on != 0
        if self.week_starts_on == 0:
            weekdays = self.weekday_names
        else:
            # Rotate the weekday names based on start day
            # If week_starts_on=1 (Monday), we want [Mon, Tue, ..., Sun]
            weekdays = self.weekday_names[self.week_starts_on:] + self.weekday_names[:self.week_starts_on]
        
        cells = "".join([
            f'<th scope="col" class="{cn(CALENDAR_WEEKDAY_BASE)}">{day}</th>'
            for day in weekdays
        ])
        
        return f'''
<thead>
    <tr class="{cn(CALENDAR_WEEKDAYS_BASE)}">
        {cells}
    </tr>
</thead>
'''
    
    def _render_days(self, year: int, month: int) -> str:
        # Get calendar for this month
        # Python's calendar module uses 0=Monday, 6=Sunday
        # We use 0=Sunday, 1=Monday, etc.
        # Convert: our 0 (Sun) -> Python's 6, our 1 (Mon) -> Python's 0
        python_first_weekday = (self.week_starts_on - 1) % 7 if self.week_starts_on > 0 else 6
        cal = calendar.Calendar(firstweekday=python_first_weekday)
        weeks = cal.monthdayscalendar(year, month)
        
        rows = []
        for week in weeks:
            cells = []
            for day in week:
                if day == 0:
                    # Outside day (from adjacent month)
                    cells.append(self._render_day_cell(None, outside=True))
                else:
                    current_date = date(year, month, day)
                    cells.append(self._render_day_cell(current_date))
            
            rows.append(f'<tr class="{cn(CALENDAR_WEEK_BASE)}">{" ".join(cells)}</tr>')
        
        return f'<tbody>{"".join(rows)}</tbody>'
    
    def _render_day_cell(self, d: Optional[date], outside: bool = False) -> str:
        if d is None or (outside and not self.show_outside_days):
            return f'<td class="{cn(CALENDAR_DAY_BASE)}"></td>'
        
        # Determine day state
        is_today = d == date.today()
        is_selected = self._is_selected(d)
        is_disabled = self._is_disabled(d)
        is_in_range = self._is_in_range(d)
        
        # Build classes
        day_classes = [CALENDAR_DAY_BUTTON_BASE]
        if is_today:
            day_classes.append(CALENDAR_DAY_TODAY)
        if is_selected:
            day_classes.append(CALENDAR_DAY_SELECTED)
        if is_disabled:
            day_classes.append(CALENDAR_DAY_DISABLED)
        if outside:
            day_classes.append(CALENDAR_DAY_OUTSIDE)
        if is_in_range and not is_selected:
            day_classes.append(CALENDAR_DAY_RANGE_MIDDLE)
        
        disabled_attr = 'disabled aria-disabled="true"' if is_disabled else ""
        selected_attr = 'aria-selected="true"' if is_selected else ""
        
        return f'''
<td class="{cn(CALENDAR_DAY_BASE)}">
    <button type="button"
            data-pynext-calendar-day
            data-date="{d.isoformat()}"
            class="{cn(*day_classes)}"
            {disabled_attr}
            {selected_attr}>
        {d.day}
    </button>
</td>
'''
    
    def _is_selected(self, d: date) -> bool:
        if not self.selected:
            return False
        
        if self.mode == "single":
            sel = self.selected
            if hasattr(sel, 'date'):
                sel = sel.date()
            return d == sel
        
        elif self.mode == "range" and isinstance(self.selected, dict):
            start = self.selected.get('start')
            end = self.selected.get('end')
            if hasattr(start, 'date'):
                start = start.date()
            if hasattr(end, 'date'):
                end = end.date()
            return d == start or d == end
        
        return False
    
    def _is_in_range(self, d: date) -> bool:
        if self.mode != "range" or not isinstance(self.selected, dict):
            return False
        
        start = self.selected.get('start')
        end = self.selected.get('end')
        
        if not start or not end:
            return False
        
        if hasattr(start, 'date'):
            start = start.date()
        if hasattr(end, 'date'):
            end = end.date()
        
        return start < d < end
    
    def _is_disabled(self, d: date) -> bool:
        # Check explicit disabled dates
        for disabled in self.disabled_dates:
            if hasattr(disabled, 'date'):
                disabled = disabled.date()
            if d == disabled:
                return True
        
        # Check min/max
        if self.min_date:
            min_d = self.min_date
            if hasattr(min_d, 'date'):
                min_d = min_d.date()
            if d < min_d:
                return True
        
        if self.max_date:
            max_d = self.max_date
            if hasattr(max_d, 'date'):
                max_d = max_d.date()
            if d > max_d:
                return True
        
        return False
    
    def __str__(self) -> str:
        return self.render()

