# DatePicker

> **Like a calendar popup — click to open and select a date**

A button that opens a calendar popup for selecting dates.

---

## First Principles: What IS a DatePicker?

### The Core Concept

A DatePicker is a **Calendar inside a Popover**, triggered by a button:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         THE DATEPICKER CONCEPT                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  CLOSED STATE:                                                               │
│  ─────────────                                                              │
│  ┌─────────────────────────────┐                                            │
│  │ 📅  Pick a date...         ▼│                                            │
│  └─────────────────────────────┘                                            │
│                                                                              │
│  OPEN STATE (after click):                                                   │
│  ─────────────────────────────                                              │
│  ┌─────────────────────────────┐                                            │
│  │ 📅  January 15, 2024       ▼│                                            │
│  └─────────────────────────────┘                                            │
│         │                                                                    │
│         ▼                                                                    │
│  ┌─────────────────────────────┐                                            │
│  │  ◀  January 2024  ▶         │                                            │
│  ├───┬───┬───┬───┬───┬───┬───┤                                            │
│  │ S │ M │ T │ W │ T │ F │ S │                                            │
│  ├───┼───┼───┼───┼───┼───┼───┤                                            │
│  │   │ 1 │ 2 │ 3 │ 4 │ 5 │ 6 │                                            │
│  │ 7 │ 8 │ 9 │10 │11 │12 │13 │                                            │
│  │14 │[15]│16 │17 │18 │19 │20 │  ← Selected                                │
│  │21 │22 │23 │24 │25 │26 │27 │                                            │
│  │28 │29 │30 │31 │   │   │   │                                            │
│  └─────────────────────────────┘                                            │
│                                                                              │
│  DatePicker = Button + Popover + Calendar                                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DatePicker vs Calendar

```
CALENDAR:                           DATEPICKER:
─────────                           ───────────
• Always visible                    • Hidden until clicked
• Embedded in page                  • Opens in popover
• Good for booking UI               • Good for forms
• Takes up space                    • Saves space
```

---

## Installation

```bash
pynext ui add date-picker
```

Or import directly:

```python
from pynext.shadcn import DatePicker
# Or build from primitives:
from pynext.shadcn import Popover, PopoverTrigger, PopoverContent, Calendar, Button
```

---

## Step-by-Step Usage

### Step 1: Basic DatePicker

```python
from pynext import Signal
from datetime import date

selected = Signal(None)

DatePicker(
    value=selected.value,
    on_change=selected.set,
    placeholder="Pick a date"
)
```

### Step 2: Build from Primitives

```python
from pynext import Signal
from datetime import date

selected = Signal(None)

Popover()[
    PopoverTrigger()[
        Button(variant="outline", class_="w-[240px] justify-start text-left font-normal")[
            Icons.calendar(class_="mr-2 h-4 w-4"),
            selected.value.strftime("%B %d, %Y") if selected.value else "Pick a date"
        ]
    ],
    PopoverContent(class_="w-auto p-0", align="start")[
        Calendar(
            mode="single",
            selected=selected.value,
            on_select=selected.set
        )
    ]
]
```

### Step 3: Date Range Picker

```python
from pynext import Signal

date_range = Signal({"from": None, "to": None})

Popover()[
    PopoverTrigger()[
        Button(variant="outline", class_="w-[300px] justify-start")[
            Icons.calendar(class_="mr-2 h-4 w-4"),
            format_range(date_range.value)
        ]
    ],
    PopoverContent(class_="w-auto p-0", align="start")[
        Calendar(
            mode="range",
            selected=date_range.value,
            on_select=date_range.set,
            number_of_months=2
        )
    ]
]

def format_range(range):
    if range["from"] and range["to"]:
        return f"{range['from'].strftime('%b %d')} - {range['to'].strftime('%b %d, %Y')}"
    elif range["from"]:
        return f"{range['from'].strftime('%b %d, %Y')} - ..."
    return "Select date range"
```

---

## Common Patterns

### Pattern 1: Form Field

```python
div(class_="space-y-2")[
    Label(html_for="dob")["Date of Birth"],
    DatePicker(
        id="dob",
        name="date_of_birth",
        value=dob.value,
        on_change=dob.set,
        max_date=date.today(),  # No future dates
        placeholder="Select your birthday"
    )
]
```

### Pattern 2: With Presets

```python
from datetime import date, timedelta

Popover()[
    PopoverTrigger()[
        Button(variant="outline")[
            Icons.calendar(class_="mr-2 h-4 w-4"),
            selected.value.strftime("%b %d, %Y") if selected.value else "Pick a date"
        ]
    ],
    PopoverContent(class_="flex w-auto p-0")[
        # Preset buttons
        div(class_="flex flex-col gap-1 p-2 border-r")[
            Button(
                variant="ghost",
                class_="justify-start",
                on_click=lambda: selected.set(date.today())
            )["Today"],
            Button(
                variant="ghost",
                class_="justify-start",
                on_click=lambda: selected.set(date.today() + timedelta(days=1))
            )["Tomorrow"],
            Button(
                variant="ghost",
                class_="justify-start",
                on_click=lambda: selected.set(date.today() + timedelta(weeks=1))
            )["In a week"],
        ],
        # Calendar
        Calendar(
            selected=selected.value,
            on_select=selected.set
        )
    ]
]
```

### Pattern 3: Booking Dates

```python
div(class_="flex gap-2")[
    div(class_="space-y-2")[
        Label()["Check-in"],
        DatePicker(
            value=check_in.value,
            on_change=check_in.set,
            min_date=date.today(),
            max_date=check_out.value,
            placeholder="Arrival"
        )
    ],
    div(class_="space-y-2")[
        Label()["Check-out"],
        DatePicker(
            value=check_out.value,
            on_change=check_out.set,
            min_date=check_in.value or date.today(),
            placeholder="Departure"
        )
    ]
]
```

---

## API Reference

### DatePicker

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `value` | date | `None` | Selected date |
| `on_change` | callable | `None` | Called when date changes |
| `placeholder` | str | `"Pick a date"` | Button text when empty |
| `min_date` | date | `None` | Earliest selectable date |
| `max_date` | date | `None` | Latest selectable date |
| `disabled` | bool | `False` | Disable the picker |
| `format` | str | `"%B %d, %Y"` | Date display format |

---

## Accessibility

| Feature | Implementation |
|---------|----------------|
| **Keyboard** | Full calendar keyboard nav |
| **Screen Reader** | Announces selected date |
| **Focus** | Returns to button after selection |

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Calendar not closing | Missing on_select handler | Add handler that closes popover |
| Wrong date format | Default format | Use `format` prop |
| Can't select past dates | `min_date` set | Remove or adjust constraint |

---

## Related Components

- **[Calendar](./calendar.md)** — The underlying calendar
- **[Popover](./popover.md)** — The container
- **[Input](./input.md)** — For typed date entry
