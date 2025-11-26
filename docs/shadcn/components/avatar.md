# Avatar

> **Like a profile picture placeholder — shows who someone is**

A visual representation of a user, typically showing their photo or initials.

---

## First Principles: What IS an Avatar?

### The Core Concept

An avatar is a **visual identity marker** for a user:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         THE AVATAR CONCEPT                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Three states of an avatar:                                                  │
│                                                                              │
│  1. WITH IMAGE:        2. IMAGE LOADING:     3. NO IMAGE (FALLBACK):        │
│     ┌─────────┐           ┌─────────┐           ┌─────────┐                │
│     │  ┌───┐  │           │ ░░░░░░░ │           │         │                │
│     │  │ 😊 │  │           │ ░░░░░░░ │           │   JD    │                │
│     │  └───┘  │           │ ░░░░░░░ │           │         │                │
│     └─────────┘           └─────────┘           └─────────┘                │
│     User's photo          Skeleton              Initials                    │
│                                                                              │
│  The avatar ALWAYS shows something — no empty broken images                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Why Avatars Are Everywhere

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AVATAR USE CASES                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  COMMENTS:                         TEAM LISTS:                               │
│  ─────────                         ───────────                               │
│  ┌──┐ John: Great work!            ┌──┐ ┌──┐ ┌──┐ ┌──┐ +3                  │
│  └──┘                              └──┘ └──┘ └──┘ └──┘                      │
│  ┌──┐ Jane: I agree                                                         │
│  └──┘                              NAVIGATION:                               │
│                                    ───────────                               │
│  MESSAGES:                         Logo  Nav  Nav  Nav  ┌──┐                │
│  ─────────                                              └──┘ Profile        │
│  ┌──┐ Sarah  3 new messages                                                 │
│  └──┘                                                                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Installation

```bash
pynext ui add avatar
```

Or import directly:

```python
from pynext.shadcn import Avatar, AvatarImage, AvatarFallback
```

---

## Step-by-Step Usage

### Step 1: Basic Avatar

```python
Avatar()[
    AvatarImage(src="https://example.com/avatar.jpg", alt="@username"),
    AvatarFallback()["JD"]  # Shown if image fails
]
```

### Step 2: Different Sizes

```python
# Small
Avatar(class_="h-6 w-6")[
    AvatarImage(src=user.avatar),
    AvatarFallback(class_="text-xs")[user.initials]
]

# Medium (default)
Avatar()[
    AvatarImage(src=user.avatar),
    AvatarFallback()[user.initials]
]

# Large
Avatar(class_="h-16 w-16")[
    AvatarImage(src=user.avatar),
    AvatarFallback(class_="text-xl")[user.initials]
]
```

### Step 3: Styled Fallback

```python
Avatar()[
    AvatarImage(src=user.avatar),
    AvatarFallback(class_="bg-primary text-primary-foreground")[
        user.initials
    ]
]
```

---

## Common Patterns

### Pattern 1: User Menu Trigger

```python
DropdownMenu()[
    DropdownMenuTrigger()[
        Avatar(class_="cursor-pointer")[
            AvatarImage(src=user.avatar),
            AvatarFallback()[user.initials]
        ]
    ],
    DropdownMenuContent(align="end")[
        DropdownMenuLabel()[user.name],
        DropdownMenuSeparator(),
        DropdownMenuItem()["Profile"],
        DropdownMenuItem()["Settings"],
        DropdownMenuItem()["Logout"],
    ]
]
```

### Pattern 2: Avatar Stack (Team)

```python
div(class_="flex -space-x-2")[
    [
        Avatar(class_="border-2 border-background", key=m.id)[
            AvatarImage(src=m.avatar),
            AvatarFallback()[m.initials]
        ]
        for m in team_members[:4]
    ],
    len(team_members) > 4 and Avatar(class_="border-2 border-background")[
        AvatarFallback(class_="bg-muted")[
            f"+{len(team_members) - 4}"
        ]
    ]
]
```

### Pattern 3: With Online Status

```python
div(class_="relative inline-block")[
    Avatar()[
        AvatarImage(src=user.avatar),
        AvatarFallback()[user.initials]
    ],
    span(
        class_=f"absolute bottom-0 right-0 h-3 w-3 rounded-full border-2 border-background {'bg-green-500' if user.is_online else 'bg-gray-400'}"
    )
]
```

### Pattern 4: Comment Thread

```python
div(class_="flex gap-4")[
    Avatar()[
        AvatarImage(src=comment.author.avatar),
        AvatarFallback()[comment.author.initials]
    ],
    div(class_="flex-1")[
        div(class_="flex items-center gap-2")[
            span(class_="font-medium")[comment.author.name],
            span(class_="text-sm text-muted-foreground")[comment.time_ago]
        ],
        p(class_="mt-1")[comment.text]
    ]
]
```

---

## API Reference

### Avatar

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `class_` | str | `""` | Size and style classes |

### AvatarImage

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `src` | str | Required | Image URL |
| `alt` | str | `""` | Alt text for accessibility |

### AvatarFallback

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `delay_ms` | int | `600` | Delay before showing fallback |

---

## Accessibility

| Feature | Implementation |
|---------|----------------|
| **Alt Text** | Always provide meaningful alt text |
| **Fallback** | Provides content when image unavailable |
| **Color Contrast** | Ensure initials are readable |

---

## Troubleshooting

### Image not loading, shows fallback immediately

**Problem:** Avatar always shows fallback even with valid image URL.

**Cause:** Image URL is incorrect or CORS blocked.

**Solution:**

```python
# Check the URL is accessible
AvatarImage(
    src="/static/images/user.jpg",  # Relative URLs often work better
    alt="User"
)

# Or use a CDN with CORS headers
AvatarImage(
    src="https://cdn.example.com/user.jpg",
    alt="User"
)
```

### Fallback flashes before image loads

**Problem:** Fallback text briefly appears, then image loads.

**Cause:** Default delay is short (600ms).

**Solution:** Increase the delay:

```python
AvatarFallback(delay_ms=1500)["JD"]
```

### Avatar not circular

**Problem:** Avatar appears square.

**Solution:** Ensure proper classes:

```python
Avatar(class_="rounded-full")[  # Add rounded-full
    AvatarImage(src=url, alt="User"),
    AvatarFallback()["JD"]
]
```

### Initials too large/small for avatar size

**Problem:** Fallback text doesn't fit the avatar size.

**Solution:** Adjust text size based on avatar size:

```python
# Small avatar
Avatar(class_="h-8 w-8")[
    AvatarFallback(class_="text-xs")["JD"]
]

# Large avatar
Avatar(class_="h-16 w-16")[
    AvatarFallback(class_="text-lg")["JD"]
]
```

### Multiple avatars overlap incorrectly

**Problem:** Stacked avatars don't overlap properly.

**Solution:** Use negative margins and proper z-index:

```python
Div(class_="flex -space-x-2")[
    Avatar(class_="ring-2 ring-background z-30")[...],
    Avatar(class_="ring-2 ring-background z-20")[...],
    Avatar(class_="ring-2 ring-background z-10")[...],
]
```

---

## Related Components

- **[Badge](./badge.md)** — For status indicators
- **[DropdownMenu](./dropdown-menu.md)** — For user menus
