# DatePicker

A date input with a calendar popover.

## Installation

```python
from pynext.shadcn import DatePicker, DateRangePicker
```

## Basic Usage

```python
DatePicker(
    value=selected_date,
    on_change=lambda d: selected_date.set(d),
    placeholder="Pick a date"
)
```

## Examples

### Single Date

```python
DatePicker(
    value=date_signal,
    on_change=set_date,
    placeholder="Select date"
)
```

### Date Range

```python
DateRangePicker(
    value={"start": start, "end": end},
    on_change=set_range,
    placeholder="Select date range"
)
```

### With Date Restrictions

```python
from datetime import datetime, timedelta

DatePicker(
    value=selected,
    on_change=set_date,
    min_date=datetime.now(),
    max_date=datetime.now() + timedelta(days=30),
    placeholder="Select within 30 days"
)
```

### With Presets

```python
from datetime import date, timedelta

DatePicker(
    value=selected,
    on_change=set_date,
    presets=[
        ("Today", date.today()),
        ("Tomorrow", date.today() + timedelta(days=1)),
        ("Next Week", date.today() + timedelta(weeks=1)),
        ("Next Month", date.today() + timedelta(days=30)),
    ]
)
```

### Date Range with Presets

```python
DateRangePicker(
    value=range_signal,
    on_change=set_range,
    presets=[
        ("Last 7 days", {
            "start": date.today() - timedelta(days=7),
            "end": date.today()
        }),
        ("Last 30 days", {
            "start": date.today() - timedelta(days=30),
            "end": date.today()
        }),
        ("This Month", {
            "start": date.today().replace(day=1),
            "end": date.today()
        }),
    ]
)
```

### Disabled State

```python
DatePicker(
    value=locked_date,
    disabled=True,
    placeholder="Date is locked"
)
```

## API Reference

### DatePicker

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `value` | `date` | `None` | Selected date |
| `on_change` | `Callable` | `None` | Change callback |
| `placeholder` | `str` | `"Pick a date"` | Placeholder text |
| `format` | `str` | `"PPP"` | Date format |
| `disabled` | `bool` | `False` | Disable picker |
| `min_date` | `date` | `None` | Minimum date |
| `max_date` | `date` | `None` | Maximum date |
| `disabled_dates` | `list` | `[]` | Disabled dates |
| `presets` | `list` | `None` | Quick select presets |

### DateRangePicker

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `value` | `dict` | `None` | `{"start": date, "end": date}` |
| `on_change` | `Callable` | `None` | Change callback |
| `placeholder` | `str` | `"Select range"` | Placeholder text |
| `disabled` | `bool` | `False` | Disable picker |
| `min_date` | `date` | `None` | Minimum date |
| `max_date` | `date` | `None` | Maximum date |
| `presets` | `list` | `None` | Quick select presets |

## Date Formatting

The `format` prop accepts standard Python strftime patterns:

- `%B %d, %Y` - "January 01, 2024"
- `%m/%d/%Y` - "01/01/2024"
- `%Y-%m-%d` - "2024-01-01"

## Integration with Forms

```python
@server_action
async def submit_form(form_data):
    event_date = form_data.get("event_date")
    # event_date is already a date object
    
form()[
    Label()["Event Date"],
    DatePicker(
        name="event_date",
        value=None,
        placeholder="Select event date"
    ),
    Button(type="submit")["Create Event"]
]
```

