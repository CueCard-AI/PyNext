# Avatar

User profile image with fallback support.

## When to Use

Avatars are for:
- **User profiles** - Profile pictures
- **Comments** - Author images
- **Lists** - Team members
- **Navigation** - User menu trigger

## Installation

```bash
pynext ui add avatar
```

Or use directly:

```python
from pynext.shadcn import Avatar, AvatarImage, AvatarFallback
```

## Basic Usage

```python
Avatar()[
    AvatarImage(src="/avatar.jpg", alt="User"),
    AvatarFallback()["JD"]
]
```

**How it works:** `AvatarImage` shows the image. If it fails to load, `AvatarFallback` is displayed instead.

## Examples

### Simple Avatar

```python
Avatar()[
    AvatarImage(src="/profile.jpg"),
    AvatarFallback()["AB"]
]
```

### Fallback Only (No Image)

```python
Avatar()[
    AvatarFallback()["JD"]
]
```

### Sizes

```python
Avatar(class_="h-8 w-8")[...]   # Small
Avatar(class_="h-10 w-10")[...]  # Default
Avatar(class_="h-12 w-12")[...]  # Medium
Avatar(class_="h-16 w-16")[...]  # Large
Avatar(class_="h-24 w-24")[...]  # Extra Large
```

### Avatar Group

```python
def AvatarGroup(users, max_display=3):
    displayed = users[:max_display]
    remaining = len(users) - max_display
    
    return div(class_="flex -space-x-2")[
        [
            Avatar(class_="border-2 border-background")[
                AvatarImage(src=user["avatar"]),
                AvatarFallback()[user["initials"]]
            ]
            for user in displayed
        ],
        remaining > 0 and Avatar(class_="border-2 border-background")[
            AvatarFallback()[f"+{remaining}"]
        ]
    ]
```

### With Status Indicator

```python
div(class_="relative")[
    Avatar()[
        AvatarImage(src="/user.jpg"),
        AvatarFallback()["JD"]
    ],
    span(class_="absolute bottom-0 right-0 h-3 w-3 rounded-full bg-green-500 border-2 border-background")
]
```

### In a Card

```python
Card()[
    CardHeader(class_="flex flex-row items-center gap-4")[
        Avatar(class_="h-12 w-12")[
            AvatarImage(src="/team/jane.jpg"),
            AvatarFallback()["JD"]
        ],
        div()[
            CardTitle()["Jane Doe"],
            CardDescription()["Software Engineer"]
        ]
    ]
]
```

## Fallback Strategies

### Initials

```python
def get_initials(name: str) -> str:
    parts = name.split()
    return "".join(p[0].upper() for p in parts[:2])

Avatar()[
    AvatarImage(src=user.avatar_url),
    AvatarFallback()[get_initials(user.name)]
]
```

### Icon Fallback

```python
Avatar()[
    AvatarImage(src=user.avatar),
    AvatarFallback()["👤"]  # User icon
]
```

### Color-coded Fallback

```python
def avatar_color(name: str) -> str:
    colors = ["bg-red-500", "bg-blue-500", "bg-green-500", "bg-purple-500"]
    return colors[hash(name) % len(colors)]

Avatar()[
    AvatarImage(src=user.avatar),
    AvatarFallback(class_=avatar_color(user.name))[
        get_initials(user.name)
    ]
]
```

## Props Reference

### Avatar

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `class_` | str | `""` | Size and styling |

### AvatarImage

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `src` | str | Required | Image URL |
| `alt` | str | `""` | Alt text for accessibility |

### AvatarFallback

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `class_` | str | `""` | Fallback styling |

## Accessibility

- Always provide `alt` text on `AvatarImage`
- Fallback should be meaningful (initials, not empty)
- Status indicators need screen reader text

## Related Components

- [Card](./card.md) - Profile cards
- [DropdownMenu](./dropdown-menu.md) - User menu

