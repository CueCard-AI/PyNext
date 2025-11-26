# Calendar

> **Like a wall calendar you can click — select dates visually**

A month-view calendar for selecting dates with full localization support.

---

## First Principles: What IS a Calendar Component?

### The Core Concept

A calendar is a **visual date picker** that shows dates in familiar month view:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         THE CALENDAR CONCEPT                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Text Input:                       Calendar:                                 │
│  ───────────                       ─────────                                 │
│                                                                              │
│  ┌─────────────────┐               ┌─────────────────────────┐              │
│  │ 2024-01-15      │               │  ◀  January 2024  ▶     │              │
│  └─────────────────┘               ├───┬───┬───┬───┬───┬───┬───┤            │
│                                    │ S │ M │ T │ W │ T │ F │ S │            │
│  User must know                    ├───┼───┼───┼───┼───┼───┼───┤            │
│  exact format!                     │   │ 1 │ 2 │ 3 │ 4 │ 5 │ 6 │            │
│                                    │ 7 │ 8 │ 9 │10 │11 │12 │13 │            │
│  Error-prone:                      │14 │[15]│16 │17 │18 │19 │20 │ ← Selected│
│  - "01/15/2024"                    │21 │22 │23 │24 │25 │26 │27 │            │
│  - "15/01/2024"                    │28 │29 │30 │31 │   │   │   │            │
│  - "Jan 15, 2024"                  └───┴───┴───┴───┴───┴───┴───┘            │
│                                                                              │
│                                    Click to select!                          │
│                                    No format confusion                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### When to Use Calendar vs Input

```
USE CALENDAR WHEN:                  USE DATE INPUT WHEN:
──────────────────                  ────────────────────

• Date is unknown to user           • Date is known exactly
• Relative selection needed         • Typing is faster
  ("next Friday")                   • Form autofill needed
• Date range selection              • Accessibility is critical
• Visual context helps              • Mobile keyboard preferred
  (see weekdays, holidays)
```

---

## How It Works

### Component Structure

```
Calendar                           ← Root container
├── CalendarHeader                 ← Navigation bar
│   ├── CalendarPrevMonth          ← Previous month button
│   ├── CalendarMonthYear          ← "January 2024"
│   └── CalendarNextMonth          ← Next month button
├── CalendarGrid                   ← The date grid
│   ├── CalendarWeekdays           ← S M T W T F S
│   └── CalendarDays               ← Date cells
│       └── CalendarDay            ← Individual date
└── (optional) CalendarFooter      ← Today button, etc.
```

### Selection Modes

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CALENDAR SELECTION MODES                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  SINGLE:                          RANGE:                                     │
│  ───────                          ──────                                     │
│                                                                              │
│  Click one date                   Click start → Click end                    │
│  ┌───┬───┬───┐                    ┌───┬───┬───┐                             │
│  │ 1 │ 2 │ 3 │                    │ 1 │ 2 │ 3 │                             │
│  │ 4 │[5]│ 6 │ ← Selected         │[4]│ 5 │ 6 │ ← Start                     │
│  │ 7 │ 8 │ 9 │                    │ 7 │[8]│ 9 │ ← End                       │
│  └───┴───┴───┘                    └───┴───┴───┘                             │
│                                   Days 4-8 highlighted                       │
│                                                                              │
│  MULTIPLE:                                                                   │
│  ─────────                                                                  │
│                                                                              │
│  Click to toggle                                                             │
│  ┌───┬───┬───┐                                                              │
│  │[1]│ 2 │[3]│ ← Multiple selected                                          │
│  │ 4 │[5]│ 6 │                                                              │
│  └───┴───┴───┘                                                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Installation

```bash
pynext ui add calendar
```

Or import directly:

```python
from pynext.shadcn import Calendar
```

---

## Step-by-Step Usage

### Step 1: Basic Calendar

```python
from pynext import Signal
from datetime import date

selected = Signal(date.today())

Calendar(
    selected=selected.value,
    on_select=selected.set
)
```

### Step 2: Date Range Selection

```python
from pynext import Signal

date_range = Signal({"from": None, "to": None})

Calendar(
    mode="range",
    selected=date_range.value,
    on_select=date_range.set
)

# date_range.value = {"from": date(2024, 1, 10), "to": date(2024, 1, 15)}
```

### Step 3: With Disabled Dates

```python
from datetime import date, timedelta

# Disable past dates
min_date = date.today()

# Disable specific dates
disabled_dates = [
    date(2024, 12, 25),  # Christmas
    date(2024, 1, 1),    # New Year
]

# Disable weekends
def is_weekend(d):
    return d.weekday() >= 5

Calendar(
    selected=selected.value,
    on_select=selected.set,
    min_date=min_date,
    disabled=disabled_dates,
    disabled_fn=is_weekend
)
```

### Step 4: Localization

```python
# Spanish calendar (Monday start, Spanish month names)
Calendar(
    locale="es",
    week_starts_on=1,  # Monday
    weekday_names=["Lu", "Ma", "Mi", "Ju", "Vi", "Sá", "Do"],
    month_names=[
        "Enero", "Febrero", "Marzo", "Abril",
        "Mayo", "Junio", "Julio", "Agosto",
        "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]
)

# Japanese calendar
Calendar(
    locale="ja",
    weekday_names=["日", "月", "火", "水", "木", "金", "土"],
    month_names=["1月", "2月", "3月", "4月", "5月", "6月",
                 "7月", "8月", "9月", "10月", "11月", "12月"]
)
```

---

## Common Patterns

### Pattern 1: Date Picker (with Popover)

```python
from pynext import Signal

selected = Signal(None)

Popover()[
    PopoverTrigger()[
        Button(variant="outline", class_="w-[240px] justify-start")[
            Icons.calendar(class_="mr-2 h-4 w-4"),
            selected.value.strftime("%b %d, %Y") if selected.value else "Pick a date"
        ]
    ],
    PopoverContent(class_="w-auto p-0")[
        Calendar(
            selected=selected.value,
            on_select=selected.set
        )
    ]
]
```

### Pattern 2: Date Range Picker

```python
date_range = Signal({"from": None, "to": None})

div(class_="grid gap-2")[
    Popover()[
        PopoverTrigger()[
            Button(variant="outline", class_="w-[300px] justify-start")[
                Icons.calendar(class_="mr-2 h-4 w-4"),
                format_date_range(date_range.value)
            ]
        ],
        PopoverContent(class_="w-auto p-0", align="start")[
            Calendar(
                mode="range",
                selected=date_range.value,
                on_select=date_range.set,
                number_of_months=2  # Show 2 months side by side
            )
        ]
    ]
]
```

### Pattern 3: Booking Calendar (with Availability)

```python
# Dates with availability data
availability = {
    date(2024, 1, 15): {"available": True, "slots": 3},
    date(2024, 1, 16): {"available": True, "slots": 1},
    date(2024, 1, 17): {"available": False, "slots": 0},
}

Calendar(
    selected=selected.value,
    on_select=selected.set,
    # Custom day rendering
    day_render=lambda d: div(class_="relative")[
        span()[d.day],
        availability.get(d, {}).get("available") and 
            span(class_="absolute bottom-0 left-1/2 w-1 h-1 bg-green-500 rounded-full")
    ],
    disabled_fn=lambda d: not availability.get(d, {}).get("available", True)
)
```

---

## API Reference

### Calendar

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `selected` | date/dict | `None` | Selected date(s) |
| `on_select` | callable | `None` | Called when selection changes |
| `mode` | str | `"single"` | `"single"`, `"range"`, `"multiple"` |
| `min_date` | date | `None` | Earliest selectable date |
| `max_date` | date | `None` | Latest selectable date |
| `disabled` | list | `[]` | Specific dates to disable |
| `disabled_fn` | callable | `None` | Function to determine if date disabled |
| `week_starts_on` | int | `0` | Start day (0=Sunday, 1=Monday) |
| `locale` | str | `"en"` | Locale for formatting |
| `weekday_names` | list | `None` | Custom weekday labels |
| `month_names` | list | `None` | Custom month labels |
| `number_of_months` | int | `1` | Number of months to display |

---

## Accessibility

| Feature | Implementation |
|---------|----------------|
| **ARIA Grid** | `role="grid"` with proper cell roles |
| **Arrow Keys** | Navigate between dates |
| **Page Up/Down** | Navigate months |
| **Home/End** | Jump to start/end of week |
| **Enter/Space** | Select focused date |

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Wrong month showing | Initial date not set | Pass `default_month` prop |
| Can't select past dates | `min_date` set | Remove or adjust min_date |
| Wrong week start | Default is Sunday | Set `week_starts_on=1` for Monday |
| Localization not working | Missing locale data | Provide custom `weekday_names` and `month_names` |

---

## Related Components

- **[DatePicker](./date-picker.md)** — Calendar in a popover
- **[Popover](./popover.md)** — For dropdown calendars
- **[Input](./input.md)** — For typed date entry
