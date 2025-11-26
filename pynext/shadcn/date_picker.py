"""
DatePicker Component

A date input with a calendar popover.

Usage:
    from pynext.shadcn import DatePicker, DateRangePicker
    
    # Single date picker
    DatePicker(
        value=date_signal,
        on_change=lambda d: date_signal.set(d),
        placeholder="Pick a date"
    )
    
    # Date range picker
    DateRangePicker(
        value=range_signal,
        on_change=lambda r: range_signal.set(r),
        placeholder="Select date range"
    )
    
    # With presets
    DatePicker(
        value=date_signal,
        on_change=set_date,
        presets=[
            ("Today", datetime.now()),
            ("Tomorrow", datetime.now() + timedelta(days=1)),
            ("Next Week", datetime.now() + timedelta(weeks=1)),
        ]
    )
"""

from typing import Any, Optional, List, Union, Callable, Tuple, Literal
from datetime import datetime, date, timedelta
from pynext.tw import cn
import hashlib


# DatePicker trigger button styles
DATEPICKER_TRIGGER_BASE = (
    "flex h-10 w-[280px] items-center justify-start rounded-md border "
    "border-input bg-background px-3 py-2 text-sm ring-offset-background "
    "placeholder:text-muted-foreground focus:outline-none focus:ring-2 "
    "focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed "
    "disabled:opacity-50"
)

DATEPICKER_PLACEHOLDER_CLASS = "text-muted-foreground"

# Popover content styles
DATEPICKER_CONTENT_BASE = (
    "w-auto p-0"
)

# Presets sidebar styles
DATEPICKER_PRESETS_BASE = (
    "flex flex-col space-y-1 p-2 border-r"
)


class DatePicker:
    """
    A date input with calendar popover.
    
    Attributes:
        value: Currently selected date
        on_change: Callback when date changes
        placeholder: Text when no date selected
        format: Date format string (default: "PPP" - e.g., "January 1, 2024")
        disabled: Whether the picker is disabled
        min_date: Minimum selectable date
        max_date: Maximum selectable date
        disabled_dates: List of dates to disable
        presets: Optional list of (label, date) tuples for quick selection
        class_: Additional CSS classes
    
    Example:
        DatePicker(
            value=selected,
            on_change=set_selected,
            placeholder="Select a date",
            presets=[
                ("Today", date.today()),
                ("Tomorrow", date.today() + timedelta(days=1)),
            ]
        )
    """
    
    def __init__(
        self,
        value: Optional[Union[date, datetime]] = None,
        on_change: Optional[Callable[[Union[date, datetime]], None]] = None,
        placeholder: str = "Pick a date",
        format: str = "PPP",
        disabled: bool = False,
        min_date: Optional[Union[date, datetime]] = None,
        max_date: Optional[Union[date, datetime]] = None,
        disabled_dates: Optional[List[Union[date, datetime]]] = None,
        presets: Optional[List[Tuple[str, Union[date, datetime]]]] = None,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.value = value
        self.on_change = on_change
        self.placeholder = placeholder
        self.format = format
        self.disabled = disabled
        self.min_date = min_date
        self.max_date = max_date
        self.disabled_dates = disabled_dates or []
        self.presets = presets
        self.extra_class = class_
        self.attrs = attrs
    
    def render(self) -> str:
        picker_id = hashlib.md5(str(id(self)).encode()).hexdigest()[:8]
        
        # Format the display value
        display_value = self._format_date(self.value) if self.value else ""
        placeholder_class = DATEPICKER_PLACEHOLDER_CLASS if not self.value else ""
        
        trigger_class = cn(DATEPICKER_TRIGGER_BASE, self.extra_class)
        disabled_attr = 'disabled' if self.disabled else ""
        
        # Calendar icon
        calendar_icon = '''
<svg class="mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
          d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
</svg>
'''
        
        # Value data attribute
        value_attr = ""
        if self.value:
            val = self.value
            if hasattr(val, 'isoformat'):
                value_attr = f'data-value="{val.isoformat()}"'
        
        # Build calendar (imported inline to avoid circular import)
        calendar_html = self._render_calendar()
        
        # Presets sidebar
        presets_html = ""
        if self.presets:
            presets_html = self._render_presets()
        
        content_class = cn(DATEPICKER_CONTENT_BASE, "flex" if self.presets else "")
        
        return f'''
<div data-pynext-datepicker="{picker_id}" {value_attr} style="position:relative;display:inline-block">
    <button type="button"
            data-pynext-datepicker-trigger
            class="{trigger_class}"
            {disabled_attr}
            aria-haspopup="dialog">
        {calendar_icon}
        <span class="{placeholder_class}">
            {display_value or self.placeholder}
        </span>
    </button>
    <div data-pynext-datepicker-content
         class="{content_class} rounded-md border bg-popover shadow-md"
         style="display:none;position:absolute;top:100%;left:0;margin-top:4px;z-index:50">
        {presets_html}
        {calendar_html}
    </div>
</div>
'''
    
    def _format_date(self, d: Union[date, datetime]) -> str:
        """Format date for display."""
        if hasattr(d, 'strftime'):
            # Simple format - can be enhanced with locale support
            return d.strftime("%B %d, %Y")
        return str(d)
    
    def _render_calendar(self) -> str:
        """Render the calendar component."""
        from .calendar import Calendar
        
        cal = Calendar(
            mode="single",
            selected=self.value,
            min_date=self.min_date,
            max_date=self.max_date,
            disabled_dates=self.disabled_dates,
        )
        return cal.render()
    
    def _render_presets(self) -> str:
        """Render preset buttons."""
        if not self.presets:
            return ""
        
        preset_buttons = []
        for label, preset_date in self.presets:
            val = preset_date.isoformat() if hasattr(preset_date, 'isoformat') else str(preset_date)
            preset_buttons.append(f'''
<button type="button"
        data-pynext-datepicker-preset
        data-preset-value="{val}"
        class="text-sm px-3 py-1.5 rounded-sm hover:bg-accent text-left">
    {label}
</button>
''')
        
        return f'''
<div class="{cn(DATEPICKER_PRESETS_BASE)}">
    {"".join(preset_buttons)}
</div>
'''
    
    def __str__(self) -> str:
        return self.render()


class DateRangePicker:
    """
    A date range picker with calendar popover.
    
    Attributes:
        value: Currently selected range {"start": date, "end": date}
        on_change: Callback when range changes
        placeholder: Text when no range selected
        disabled: Whether the picker is disabled
        min_date: Minimum selectable date
        max_date: Maximum selectable date
        presets: Optional list of (label, range) tuples for quick selection
        class_: Additional CSS classes
    
    Example:
        DateRangePicker(
            value=range_signal,
            on_change=set_range,
            presets=[
                ("Last 7 days", {
                    "start": date.today() - timedelta(days=7),
                    "end": date.today()
                }),
            ]
        )
    """
    
    def __init__(
        self,
        value: Optional[dict] = None,  # {"start": date, "end": date}
        on_change: Optional[Callable[[dict], None]] = None,
        placeholder: str = "Select date range",
        disabled: bool = False,
        min_date: Optional[Union[date, datetime]] = None,
        max_date: Optional[Union[date, datetime]] = None,
        presets: Optional[List[Tuple[str, dict]]] = None,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.value = value
        self.on_change = on_change
        self.placeholder = placeholder
        self.disabled = disabled
        self.min_date = min_date
        self.max_date = max_date
        self.presets = presets
        self.extra_class = class_
        self.attrs = attrs
    
    def render(self) -> str:
        picker_id = hashlib.md5(str(id(self)).encode()).hexdigest()[:8]
        
        # Format the display value
        display_value = self._format_range(self.value) if self.value else ""
        placeholder_class = DATEPICKER_PLACEHOLDER_CLASS if not self.value else ""
        
        trigger_class = cn(DATEPICKER_TRIGGER_BASE, "w-[300px]", self.extra_class)
        disabled_attr = 'disabled' if self.disabled else ""
        
        # Calendar icon
        calendar_icon = '''
<svg class="mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
          d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
</svg>
'''
        
        # Value data attributes
        value_attrs = ""
        if self.value:
            if self.value.get('start'):
                start = self.value['start']
                if hasattr(start, 'isoformat'):
                    value_attrs += f' data-start="{start.isoformat()}"'
            if self.value.get('end'):
                end = self.value['end']
                if hasattr(end, 'isoformat'):
                    value_attrs += f' data-end="{end.isoformat()}"'
        
        # Build calendar for range mode
        calendar_html = self._render_calendars()
        
        # Presets sidebar
        presets_html = ""
        if self.presets:
            presets_html = self._render_presets()
        
        content_class = cn(DATEPICKER_CONTENT_BASE, "flex" if self.presets else "")
        
        return f'''
<div data-pynext-daterangepicker="{picker_id}" {value_attrs} style="position:relative;display:inline-block">
    <button type="button"
            data-pynext-datepicker-trigger
            class="{trigger_class}"
            {disabled_attr}
            aria-haspopup="dialog">
        {calendar_icon}
        <span class="{placeholder_class}">
            {display_value or self.placeholder}
        </span>
    </button>
    <div data-pynext-datepicker-content
         class="{content_class} rounded-md border bg-popover shadow-md"
         style="display:none;position:absolute;top:100%;left:0;margin-top:4px;z-index:50">
        {presets_html}
        <div class="flex">
            {calendar_html}
        </div>
    </div>
</div>
'''
    
    def _format_range(self, r: dict) -> str:
        """Format date range for display."""
        if not r:
            return ""
        
        start = r.get('start')
        end = r.get('end')
        
        if start and end:
            start_str = start.strftime("%b %d, %Y") if hasattr(start, 'strftime') else str(start)
            end_str = end.strftime("%b %d, %Y") if hasattr(end, 'strftime') else str(end)
            return f"{start_str} - {end_str}"
        elif start:
            start_str = start.strftime("%b %d, %Y") if hasattr(start, 'strftime') else str(start)
            return f"{start_str} - ..."
        
        return ""
    
    def _render_calendars(self) -> str:
        """Render two calendars for range selection."""
        from .calendar import Calendar
        
        # Two calendars side by side
        cal1 = Calendar(
            mode="range",
            selected=self.value,
            min_date=self.min_date,
            max_date=self.max_date,
        )
        
        # Second calendar shows next month
        cal2 = Calendar(
            mode="range",
            selected=self.value,
            default_month=self._next_month(),
            min_date=self.min_date,
            max_date=self.max_date,
        )
        
        return f'''
<div class="p-0">
    {cal1.render()}
</div>
<div class="p-0 border-l">
    {cal2.render()}
</div>
'''
    
    def _next_month(self) -> datetime:
        """Get the first day of next month."""
        today = datetime.now()
        if today.month == 12:
            return datetime(today.year + 1, 1, 1)
        return datetime(today.year, today.month + 1, 1)
    
    def _render_presets(self) -> str:
        """Render preset buttons for common ranges."""
        if not self.presets:
            return ""
        
        preset_buttons = []
        for label, preset_range in self.presets:
            start = preset_range.get('start')
            end = preset_range.get('end')
            start_val = start.isoformat() if hasattr(start, 'isoformat') else str(start)
            end_val = end.isoformat() if hasattr(end, 'isoformat') else str(end)
            
            preset_buttons.append(f'''
<button type="button"
        data-pynext-daterange-preset
        data-preset-start="{start_val}"
        data-preset-end="{end_val}"
        class="text-sm px-3 py-1.5 rounded-sm hover:bg-accent text-left">
    {label}
</button>
''')
        
        return f'''
<div class="{cn(DATEPICKER_PRESETS_BASE)}">
    {"".join(preset_buttons)}
</div>
'''
    
    def __str__(self) -> str:
        return self.render()

