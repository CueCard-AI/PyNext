# Calendar

A date picker calendar with single and range selection support.

## Installation

```python
from pynext.shadcn import Calendar
```

## Basic Usage

```python
from datetime import date

Calendar(
    selected=selected_date,
    on_select=lambda d: selected_date.set(d)
)
```

## Examples

### Single Date Selection

```python
Calendar(
    mode="single",
    selected=selected_date,
    on_select=handle_select
)
```

### Range Selection

```python
Calendar(
    mode="range",
    selected={"start": start_date, "end": end_date},
    on_select=lambda r: set_range(r)
)
```

### With Date Restrictions

```python
from datetime import datetime, timedelta

Calendar(
    selected=selected,
    min_date=datetime.now(),  # No past dates
    max_date=datetime.now() + timedelta(days=365),  # Up to 1 year
    disabled_dates=[
        datetime(2024, 12, 25),  # Christmas
        datetime(2025, 1, 1),    # New Year
    ]
)
```

### Hide Outside Days

```python
Calendar(
    selected=selected,
    show_outside_days=False  # Don't show days from adjacent months
)
```

### Custom Initial Month

```python
from datetime import datetime

Calendar(
    selected=None,
    default_month=datetime(2025, 6, 1)  # Start showing June 2025
)
```

### Localization

The calendar supports multiple locales for weekday and month names:

```python
# Spanish locale
Calendar(
    selected=selected_date,
    locale="es"  # Shows "Enero", "Febrero", "Lu", "Ma", etc.
)

# Week starts on Monday (European style)
Calendar(
    selected=selected_date,
    locale="en-GB"  # Mon-Sun order
)

# German locale
Calendar(
    selected=selected_date,
    locale="de"  # "Januar", "Mo", "Di", "Mi", etc.
)

# Japanese locale
Calendar(
    selected=selected_date,
    locale="ja"  # "1月", "日", "月", "火", etc.
)
```

**Supported Locales:**
- `en` (English, Sunday start) - default
- `en-GB` (English, Monday start)
- `es` (Spanish)
- `fr` (French)
- `de` (German)
- `ja` (Japanese)
- `zh` (Chinese)
- `pt` (Portuguese)

### Custom Weekday/Month Names

Override locale defaults with custom names:

```python
Calendar(
    selected=selected_date,
    weekday_names=["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
    month_names=["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                 "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
)

# Change only the start day
Calendar(
    selected=selected_date,
    week_starts_on=1  # 0=Sunday, 1=Monday, ..., 6=Saturday
)
```

## API Reference

### Calendar

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `mode` | `"single" \| "range"` | `"single"` | Selection mode |
| `selected` | `date \| dict` | `None` | Selected date(s) |
| `on_select` | `Callable` | `None` | Selection callback |
| `default_month` | `date` | Current | Initial month to display |
| `disabled_dates` | `list[date]` | `[]` | Dates to disable |
| `min_date` | `date` | `None` | Minimum selectable date |
| `max_date` | `date` | `None` | Maximum selectable date |
| `show_outside_days` | `bool` | `True` | Show adjacent month days |
| `locale` | `str` | `"en"` | Locale preset for weekday/month names |
| `weekday_names` | `list[str]` | From locale | Custom weekday abbreviations (7 items) |
| `month_names` | `list[str]` | From locale | Custom month names (12 items) |
| `week_starts_on` | `int` | From locale | First day of week (0=Sun, 1=Mon, etc.) |

## Events

```python
# Listen for selection
@on("pynext:calendar-select")
def handle_select(event):
    date = event.detail.date
    mode = event.detail.mode
    start = event.detail.start  # For range mode
    end = event.detail.end      # For range mode

# Listen for navigation
@on("pynext:calendar-navigate")
def handle_navigate(event):
    year = event.detail.year
    month = event.detail.month
```

## Styling

The calendar uses these key classes:

- `bg-primary text-primary-foreground` - Selected day
- `bg-accent text-accent-foreground` - Today
- `text-muted-foreground opacity-50` - Disabled/outside days

## Keyboard Navigation

- `←/→` - Navigate days
- `↑/↓` - Navigate weeks
- `Enter` - Select focused day

